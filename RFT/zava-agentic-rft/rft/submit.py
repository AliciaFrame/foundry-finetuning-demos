"""Submit a Zava RFT job to Microsoft Foundry.

Configuration:
  - Base model:        o4-mini (RFT-eligible, GA per Skills/SKILL.md)
  - System prompt:     fixed prompt included in the bundled data
  - Training/val data: 343 train + 57 val (from Zava-Ignite-RL-Lab rft_v7)
  - Tool endpoint:     ZAVA_TOOL_BASE_URL environment variable
  - Grader:            grader.py (Python, 4-dimensional partial credit)
  - Pass threshold:    settable via --pass-threshold (default 0.80)
  - Hyperparameters:   match Zava lab notebook defaults (epochs=3, lr=1.0, compute=1.5,
                       reasoning=medium, eval_interval=5, eval_samples=10)

Check current model and regional support for agentic RFT before submission.

Usage:
  python submit.py --pass-threshold 0.85 --suffix v1-prompt-rft

After submission, the job ID is saved to rft/results/job.json and a monitor
loop streams events until the FIRST eval step is reached. If first-step
pass rate is 0% or 100%, the script offers to cancel.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from grader import get_grader_source  # noqa: E402

TOOL_URL = os.environ.get("ZAVA_TOOL_BASE_URL", "").rstrip("/")
TRAIN_FILE = HERE / "data" / "zava_v1_train.jsonl"
VAL_FILE = HERE / "data" / "zava_v1_val.jsonl"


def make_client() -> OpenAI:
    base = os.environ["AZURE_AI_PROJECT_ENDPOINT"].rstrip("/") + "/openai/v1/"
    cred = DefaultAzureCredential()
    # /v1/ project endpoints want audience https://ai.azure.com
    token = cred.get_token("https://ai.azure.com/.default").token
    print(f"Using base_url: {base}")
    return OpenAI(base_url=base, api_key=token)


def upload(client: OpenAI, path: Path) -> str:
    print(f"Uploading {path.name} ({path.stat().st_size:,} bytes)...")
    with path.open("rb") as f:
        result = client.files.create(file=f, purpose="fine-tune")
    print(f"  ID: {result.id} — waiting for processing...")
    for _ in range(30):
        info = client.files.retrieve(result.id)
        if info.status == "processed":
            print(f"  Ready.")
            return result.id
        time.sleep(5)
    raise RuntimeError(f"File {result.id} did not process in time (status={info.status})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass-threshold", type=float, default=0.80)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1.0)
    ap.add_argument("--compute-multiplier", type=float, default=1.5)
    ap.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default="medium")
    ap.add_argument("--eval-interval", type=int, default=5)
    ap.add_argument("--eval-samples", type=int, default=10)
    ap.add_argument("--max-episode-steps", type=int, default=5)
    ap.add_argument(
        "--training-type",
        choices=["Standard", "GlobalStandard", "Developer"],
        default="GlobalStandard",
        help=(
            "Compute tier for the training job. GlobalStandard (default) uses "
            "global capacity (cheaper, faster queue, weights copied outside the "
            "resource region). Standard keeps weights in-region. Developer "
            "(preview) uses idle capacity with no SLA."
        ),
    )
    ap.add_argument("--model", default="o4-mini")
    ap.add_argument("--suffix", default="zavav1")
    args = ap.parse_args()

    if not TRAIN_FILE.exists() or not VAL_FILE.exists():
        sys.exit("Bundled training or validation data is missing; restore rft/data/")
    if not TOOL_URL:
        sys.exit("Set ZAVA_TOOL_BASE_URL to the deployed tool-service URL")

    client = make_client()
    train_id = upload(client, TRAIN_FILE)
    val_id = upload(client, VAL_FILE)

    grader_source = get_grader_source()

    method = {
        "type": "reinforcement",
        "reinforcement": {
            "grader": {
                "type": "python",
                "name": "zava_grader",
                "source": grader_source,
                "pass_threshold": args.pass_threshold,
            },
            "tools": [{
                "name": "get_order",
                "server_url": f"{TOOL_URL}/tool/get_order",
                "headers": {},
            }],
            "max_episode_steps": args.max_episode_steps,
            "hyperparameters": {
                "n_epochs": args.epochs,
                "learning_rate_multiplier": args.lr,
                "compute_multiplier": args.compute_multiplier,
                "reasoning_effort": args.reasoning_effort,
                "eval_interval": args.eval_interval,
                "eval_samples": args.eval_samples,
            },
        },
    }

    print("\nSubmitting RFT job:")
    print(f"  model:               {args.model}")
    print(f"  pass_threshold:      {args.pass_threshold}")
    print(f"  epochs:              {args.epochs}")
    print(f"  lr_multiplier:       {args.lr}")
    print(f"  compute_multiplier:  {args.compute_multiplier}")
    print(f"  reasoning_effort:    {args.reasoning_effort}")
    print(f"  eval_interval:       {args.eval_interval}")
    print(f"  eval_samples:        {args.eval_samples}")
    print(f"  max_episode_steps:   {args.max_episode_steps}")
    print(f"  suffix:              {args.suffix}")
    print(f"  training_type:       {args.training_type}")

    job = client.fine_tuning.jobs.create(
        model=args.model,
        training_file=train_id,
        validation_file=val_id,
        suffix=args.suffix,
        method=method,
        extra_body={"trainingType": args.training_type},
    )

    print("\n=== JOB SUBMITTED ===")
    print(f"  ID:     {job.id}")
    print(f"  Status: {job.status}")
    print(f"  Model:  {job.model}")

    info = {
        "id": job.id,
        "status": job.status,
        "model": job.model,
        "training_file_id": train_id,
        "validation_file_id": val_id,
        "training_type": args.training_type,
        "method": method,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    out = HERE / "results" / "job.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(info, indent=2, default=str))
    print(f"  Saved: {out}")
    print(f"\nNext: python monitor.py")


if __name__ == "__main__":
    main()
