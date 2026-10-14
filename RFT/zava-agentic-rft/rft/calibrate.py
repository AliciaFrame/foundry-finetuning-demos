"""Calibrate the Zava RFT pass threshold.

Runs N random validation scenarios through:
  o4-mini (deployed in our Foundry project)
  + the system prompt bundled with the RFT dataset
  + the `get_order` endpoint configured by ZAVA_TOOL_BASE_URL

Then scores with the same Python grader we'll use during RFT, and prints the
pass rate at thresholds 0.5–0.95. Goal: choose a threshold that yields
25-50% failure rate on the base model — that's the sweet spot for RFT signal
(too easy: no learning; too hard: sparse positive reward).

Usage:
  python calibrate.py                     # 30 examples (default)
  python calibrate.py --n 57              # full val set
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import requests
from openai import OpenAI
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from grader import grade as run_grader  # noqa: E402

VAL_FILE = HERE / "data" / "zava_v1_val.jsonl"
TOOL_URL = os.environ.get("ZAVA_TOOL_BASE_URL", "").rstrip("/")
MODEL = os.environ.get("RFT_BASE_MODEL", "o4-mini")

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_order",
        "description": "Look up order details including items, prices, dates, loyalty tier, and delivery status.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The order ID (e.g., ORD-003)"}},
            "required": ["order_id"],
        },
    },
}]


def make_client() -> OpenAI:
    base = os.environ["AZURE_AI_PROJECT_ENDPOINT"].rstrip("/") + "/openai/v1/"
    cred = DefaultAzureCredential()
    token = cred.get_token("https://ai.azure.com/.default").token
    return OpenAI(base_url=base, api_key=token)


def call_tool(name: str, args: dict) -> str:
    url = f"{TOOL_URL}/tool/{name}"
    payload = {"arguments": json.dumps(args), "call_id": "c", "id": "f", "trace_id": "t"}
    for attempt in range(5):
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            body = response.json()
            return body.get("output", json.dumps(body))
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Tool request retry loop exited unexpectedly")


def run_agent(client: OpenAI, messages: list[dict], model: str = MODEL, max_turns: int = 8):
    convo = list(messages)
    tools_called: list[dict] = []
    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model=model, messages=convo, tools=TOOLS, max_completion_tokens=8192,
        )
        msg = resp.choices[0].message
        am: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            am["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
            tools_called.extend(am["tool_calls"])
        convo.append(am)
        if not msg.tool_calls:
            return msg.content or "", tools_called
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = call_tool(tc.function.name, args)
            convo.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return "", tools_called


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="Number of val examples to run (default 30)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    if not TOOL_URL:
        raise SystemExit("Set ZAVA_TOOL_BASE_URL to the deployed tool-service URL")

    val = [json.loads(line) for line in VAL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    random.seed(args.seed)
    sampled = random.sample(val, min(args.n, len(val)))
    print(f"Calibrating on {len(sampled)} of {len(val)} val examples (seed {args.seed})", flush=True)
    print(f"Base model: {MODEL}", flush=True)

    client = make_client()
    scores: list[float] = []
    started = time.time()
    for i, ex in enumerate(sampled, 1):
        msgs = ex["messages"]
        expected = ex.get("expected_resolution", "")
        t0 = time.time()
        try:
            output, tools_called = run_agent(client, msgs)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i:2d}/{len(sampled)}] ERROR  {exc!r}", flush=True)
            scores.append(0.0)
            continue
        sample = {"output_text": output, "output_tools": tools_called}
        score = run_grader(sample, ex)
        scores.append(score)
        dur = time.time() - t0
        status = "PASS" if score >= 0.8 else "fail"
        print(f"  [{i:2d}/{len(sampled)}] score={score:.3f} {status} ({dur:.1f}s) tools={len(tools_called)}", flush=True)

    avg = sum(scores) / len(scores)
    print(f"\n=== Calibration ({len(scores)} examples, {time.time()-started:.0f}s) ===")
    print(f"Avg score: {avg:.3f}")
    print()
    print(f"  {'Threshold':>10} {'Pass':>10} {'Fail':>10} {'Quality':>20}")
    for thr in (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95):
        passrate = sum(1 for s in scores if s >= thr) / len(scores)
        failrate = 1 - passrate
        if 0.25 <= failrate <= 0.50:
            q = "GOOD signal (25-50%)"
        elif failrate < 0.25:
            q = "too easy"
        else:
            q = "too hard"
        print(f"  {thr:>10.2f} {passrate:>9.0%} {failrate:>9.0%} {q:>20}")

    out_path = HERE / "results" / "calibration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "model": MODEL,
        "n": len(scores),
        "seed": args.seed,
        "avg_score": avg,
        "scores": scores,
    }, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
