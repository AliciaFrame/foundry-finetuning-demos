"""Monitor a Zava RFT job — stream events, surface first-step eval pass rate.

Reads job ID from rft/results/job.json (saved by submit.py).

Behavior:
  * Streams events as they appear (`fine_tuning.jobs.list_events`)
  * Highlights metric events (especially the first eval step)
  * If first eval step's pass rate is 0% or 100%, prints a CANCEL recommendation
    (per SKILL.md: a job with no learning signal is wasted compute)
  * Loops until terminal state or until --max-minutes runs out

Usage:
  python monitor.py                  # continuous (until terminal or 12h)
  python monitor.py --max-minutes 30 # bounded
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
JOB_FILE = HERE / "results" / "job.json"

TERMINAL = {"succeeded", "failed", "cancelled"}


def make_client() -> OpenAI:
    base = os.environ["AZURE_AI_PROJECT_ENDPOINT"].rstrip("/") + "/openai/v1/"
    cred = DefaultAzureCredential()
    token = cred.get_token("https://ai.azure.com/.default").token
    return OpenAI(base_url=base, api_key=token)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-id", help="Override job ID (otherwise from rft/results/job.json)")
    ap.add_argument("--max-minutes", type=int, default=720)
    ap.add_argument("--poll-seconds", type=int, default=20)
    args = ap.parse_args()

    job_id = args.job_id
    if not job_id:
        if not JOB_FILE.exists():
            sys.exit(f"No job ID provided and {JOB_FILE} not found. Run submit.py first.")
        job_id = json.loads(JOB_FILE.read_text())["id"]
    print(f"Monitoring job: {job_id}")

    client = make_client()
    client_made_at = time.time()
    seen_event_ids: set[str] = set()
    deadline = time.time() + args.max_minutes * 60
    first_eval_seen = False

    while time.time() < deadline:
        # Refresh token every 30 minutes (Azure tokens expire after ~60 min)
        if time.time() - client_made_at > 30 * 60:
            try:
                client = make_client()
                client_made_at = time.time()
                print(f"  [token refreshed]", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"  token refresh error: {exc!r}", flush=True)

        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
        except Exception as exc:  # noqa: BLE001
            err_str = str(exc)
            if "401" in err_str or "audience" in err_str or "expired" in err_str:
                print(f"  401, refreshing token...", flush=True)
                try:
                    client = make_client()
                    client_made_at = time.time()
                except Exception as e2:  # noqa: BLE001
                    print(f"  token refresh failed: {e2!r}", flush=True)
            else:
                print(f"  retrieve error: {exc!r}", flush=True)
            time.sleep(args.poll_seconds)
            continue

        try:
            events_page = client.fine_tuning.jobs.list_events(job_id, limit=50)
            events = list(reversed(events_page.data))
        except Exception as exc:  # noqa: BLE001
            print(f"  events error: {exc!r}", flush=True)
            events = []

        for ev in events:
            ev_id = getattr(ev, "id", None) or f"{ev.created_at}:{ev.message[:40]}"
            if ev_id in seen_event_ids:
                continue
            seen_event_ids.add(ev_id)
            ts = time.strftime("%H:%M:%S", time.localtime(ev.created_at))
            level = getattr(ev, "level", "info")
            msg = getattr(ev, "message", "")
            data = getattr(ev, "data", None)

            print(f"[{ts}] {level.upper():5} {msg}", flush=True)

            if data:
                try:
                    data_dict = data if isinstance(data, dict) else dict(data)
                except Exception:  # noqa: BLE001
                    data_dict = {}
                if data_dict:
                    interesting = {k: v for k, v in data_dict.items() if k in (
                        "step", "train_mean_reward", "valid_mean_reward",
                        "full_valid_mean_reward", "full_valid_pass_rate",
                        "valid_pass_rate", "completion_tokens_mean",
                        "reasoning_tokens_mean", "train_pass_rate",
                    )}
                    if interesting:
                        print(f"          metrics: {json.dumps(interesting, default=str)}", flush=True)
                        pr = interesting.get("full_valid_pass_rate") or interesting.get("valid_pass_rate")
                        if not first_eval_seen and pr is not None:
                            first_eval_seen = True
                            pr_f = float(pr)
                            if pr_f <= 0.001:
                                print("\n⚠️  FIRST EVAL PASS RATE = 0% — model is failing every example.", flush=True)
                                print("    Per SKILL.md, this means no learning signal (only negative reward).", flush=True)
                                print("    Recommend: cancel and lower pass_threshold OR widen the dataset.", flush=True)
                                print(f"    To cancel: python -c \"from openai import OpenAI; from azure.identity import DefaultAzureCredential as C; import os; b=os.environ['AZURE_AI_PROJECT_ENDPOINT'].rstrip('/')+'/openai/v1/'; t=C().get_token('https://cognitiveservices.azure.com/.default').token; OpenAI(base_url=b,api_key=t).fine_tuning.jobs.cancel('{job_id}')\"", flush=True)
                            elif pr_f >= 0.999:
                                print("\n⚠️  FIRST EVAL PASS RATE = 100% — task is too easy.", flush=True)
                                print("    Per SKILL.md, this means no learning signal (only positive reward).", flush=True)
                                print("    Recommend: cancel and raise pass_threshold OR add harder tasks.", flush=True)
                                print(f"    To cancel: see commands in monitor.py output above.", flush=True)
                            else:
                                print(f"\n✅ FIRST EVAL PASS RATE = {pr_f:.0%} — good learning signal (25-50% fail target)", flush=True)

        if job.status in TERMINAL:
            print(f"\n=== Job terminal: status={job.status} ===", flush=True)
            print(json.dumps({
                "id": job.id, "status": job.status,
                "fine_tuned_model": getattr(job, "fine_tuned_model", None),
                "trained_tokens": getattr(job, "trained_tokens", None),
                "error": getattr(job, "error", None),
            }, indent=2, default=str), flush=True)
            return

        time.sleep(args.poll_seconds)

    print(f"\n--max-minutes {args.max_minutes} exhausted; job still {job.status}", flush=True)


if __name__ == "__main__":
    main()
