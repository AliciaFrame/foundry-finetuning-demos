"""Score a deployed (RFT or base) o4-mini deployment with the actual training-time RFT grader.

Why this exists
---------------
During RFT training, every `eval_interval` steps the platform measures
`full_valid_mean_reward` by:
1. Running the model against each row in val.jsonl as an agentic rollout
   (with the get_order tool available and max_episode_steps=5)
2. Scoring the {output_text, output_tools} with the Python grader
3. Averaging across all 57 examples

That signal is what told us "step 115 hit 0.5844, the highest checkpoint."
But it only exists *during* training. The pre-release May 2026 optimizer run
used a different evaluator and agent-layer execution path, so its score was
not comparable with the training reward.

This script reproduces the validation-time signal against any deployment
so we can ask:
- Does deployed-s115 actually score the same as training-step-115?
- How does base o4-mini (no RFT) score? (Should reproduce ~0.303.)
- How do s100 and s110 compare to s115 on the same metric?

It calls the model directly (not through the historical hosted-agent wrapper) and
runs an agentic rollout: model -> tool call -> POST to lab tool endpoint
-> feed result back -> final answer. Same shape as RFT training.

Output: rft/results/rl-rubric-eval/<deployment>.json with per-example
scores, mean, and per-dimension breakdown.

Usage:
  python grade_with_rl_rubric.py --deployment o4-mini-rft-zavav1pt70
  python grade_with_rl_rubric.py --deployment o4-mini --base    # base model
  python grade_with_rl_rubric.py --deployment o4-mini-rft-s100 --max 10  # quick smoke test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from openai import OpenAI
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from grader import grade  # noqa: E402

VAL_FILE = HERE / "data" / "zava_v1_val.jsonl"
RESULTS_DIR = HERE / "results" / "rl-rubric-eval"
TOOL_ENDPOINT = os.environ.get("ZAVA_TOOL_ENDPOINT", "")
MAX_EPISODE_STEPS = 5

GET_ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order",
        "description": "Look up a customer order by order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to look up."},
            },
            "required": ["order_id"],
        },
    },
}


def make_client() -> OpenAI:
    """Build OpenAI client pointed at the Foundry resource's AOAI-compat endpoint."""
    endpoint = os.environ["RFT_RESOURCE_ENDPOINT"].rstrip("/")
    base = f"{endpoint}/openai/v1/"
    cred = DefaultAzureCredential()
    token = cred.get_token("https://ai.azure.com/.default").token
    return OpenAI(base_url=base, api_key=token)


def load_val() -> list[dict]:
    rows = []
    with VAL_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def override_system_prompt(rows: list[dict], system_text: str) -> list[dict]:
    """Replace the developer/system role message in every row with a custom prompt.

    Used to measure how a non-trained baseline (e.g., rich Zava prompt + base
    model) scores on the RL-rubric, instead of the cand-v1 prompt baked into
    val.jsonl. We keep the role tag from the original message (developer or
    system) so the deployment receives the message in the same format.
    """
    out = []
    for row in rows:
        new_row = dict(row)
        new_msgs = []
        replaced = False
        for m in row.get("messages", []):
            if m.get("role") in ("developer", "system") and not replaced:
                new_msgs.append({"role": m["role"], "content": system_text})
                replaced = True
            else:
                new_msgs.append(m)
        if not replaced:
            new_msgs.insert(0, {"role": "developer", "content": system_text})
        new_row["messages"] = new_msgs
        out.append(new_row)
    return out


def call_tool(name: str, arguments: str) -> str:
    """Dispatch a tool call against the lab's hosted endpoint. Returns the tool's text output."""
    if name != "get_order":
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON arguments"})
    try:
        r = requests.post(TOOL_ENDPOINT, json={"arguments": args}, timeout=30)
        r.raise_for_status()
        body = r.json()
        return body.get("output", json.dumps(body))
    except Exception as e:
        return json.dumps({"error": f"Tool call failed: {e}"})


def rollout(client: OpenAI, deployment: str, initial_messages: list[dict]) -> tuple[str, list]:
    """Run an agentic rollout (max MAX_EPISODE_STEPS turns). Returns (final_text, output_tools).

    output_tools mirrors the grader's expectation:
      [{"function": {"name": "...", "arguments": "..."}}, ...]
    """
    msgs = list(initial_messages)
    output_tools = []
    final_text = ""

    for step in range(MAX_EPISODE_STEPS):
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=deployment,
                    messages=msgs,
                    tools=[GET_ORDER_TOOL],
                    tool_choice="auto",
                    reasoning_effort="medium",
                )
                break
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        msg = resp.choices[0].message
        text = msg.content or ""
        tool_calls = msg.tool_calls or []

        if text and not tool_calls:
            # Final answer reached
            final_text = text
            break

        # Append assistant turn (preserve tool_calls for the model's history)
        assistant_turn = {"role": "assistant", "content": text or None}
        if tool_calls:
            assistant_turn["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls
            ]
        msgs.append(assistant_turn)

        if not tool_calls:
            # No tool call and no text — bail
            final_text = text
            break

        # Execute each tool call, append results
        for tc in tool_calls:
            output_tools.append({
                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
            })
            tool_output = call_tool(tc.function.name, tc.function.arguments)
            msgs.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_output,
            })
        # Loop: model now has tool results, will produce more turns
    else:
        # Hit max steps without final text — use last assistant text we saw
        final_text = msgs[-1].get("content", "") if msgs else ""
        if not isinstance(final_text, str):
            final_text = ""

    return final_text, output_tools


def score_one(client: OpenAI, deployment: str, item: dict) -> dict:
    msgs = item.get("messages", [])
    expected = item.get("expected_resolution", "")
    text, tools_out = rollout(client, deployment, msgs)
    sample = {"output_text": text, "output_tools": tools_out}
    s = grade(sample, item)
    return {
        "score": s,
        "output_text": text[:300],
        "output_tools_count": len(tools_out),
        "tool_names": [t["function"]["name"] for t in tools_out],
        "expected": expected[:200],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deployment", required=True, help="Azure deployment name to score")
    ap.add_argument("--max", type=int, default=None, help="Limit to N examples (smoke test)")
    ap.add_argument("--workers", type=int, default=8, help="Parallel rollouts (model endpoint can handle this)")
    ap.add_argument("--label", default=None, help="Output filename label (default = deployment)")
    ap.add_argument(
        "--system-prompt-file",
        default=None,
        help="Override the developer/system message in every row with the contents of this file. "
             "Used to measure baselines that don't use the cand-v1 prompt baked into val.jsonl.",
    )
    args = ap.parse_args()
    if not TOOL_ENDPOINT:
        raise SystemExit("Set ZAVA_TOOL_ENDPOINT to the deployed /tool/get_order URL")

    rows = load_val()
    if args.system_prompt_file:
        prompt_text = Path(args.system_prompt_file).read_text(encoding="utf-8")
        rows = override_system_prompt(rows, prompt_text)
        print(f"Overrode dev prompt in all rows from {args.system_prompt_file} ({len(prompt_text)} chars)")
    if args.max:
        rows = rows[:args.max]
    print(f"Scoring {len(rows)} examples against deployment '{args.deployment}' with {args.workers} workers")

    client = make_client()
    results = [None] * len(rows)
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(score_one, client, args.deployment, r): i for i, r in enumerate(rows)}
        done = 0
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                results[i] = fut.result()
            except Exception as e:
                print(f"  [{i}] FAILED: {type(e).__name__}: {str(e)[:200]}")
                results[i] = {"score": 0.0, "error": str(e)}
            done += 1
            if done % 5 == 0 or done == len(rows):
                elapsed = time.time() - start
                avg_so_far = sum(r["score"] for r in results if r) / done
                print(f"  {done}/{len(rows)}  avg={avg_so_far:.4f}  elapsed={elapsed:.0f}s", flush=True)

    elapsed = time.time() - start
    scores = [r["score"] for r in results if r]
    mean = sum(scores) / len(scores) if scores else 0.0
    pass_rate = sum(1 for s in scores if s >= 0.7) / len(scores) if scores else 0.0

    out = {
        "deployment": args.deployment,
        "n_examples": len(rows),
        "mean_score": round(mean, 4),
        "pass_rate_at_0.7": round(pass_rate, 4),
        "elapsed_sec": round(elapsed, 1),
        "per_example": results,
    }

    label = args.label or args.deployment
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{label}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\n=== RFT-RUBRIC EVAL: {args.deployment} ===")
    print(f"  examples:    {len(rows)}")
    print(f"  mean score:  {mean:.4f}")
    print(f"  pass>=0.7:   {pass_rate:.2%}")
    print(f"  elapsed:     {elapsed:.0f}s")
    print(f"  saved to:    {out_path}")


if __name__ == "__main__":
    main()
