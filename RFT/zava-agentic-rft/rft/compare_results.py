"""Aggregate all rubric results into a single comparison table.

Reads:
- results/strict-deterministic-2026-05-05/<variant>/strict-eval.json
- results/baseline-2026-05-05/<variant>/summary.json (Row 1)
- results/rich-2026-05-05/<variant>/summary.json (Row 2)
- rft/results/rl-rubric-eval/<deployment>.json (Row 4 — direct RFT-grader rollout)

Variants searched (in order, missing skipped):
- o4-mini                 (rich Zava prompt baseline)
- o4-mini-cand-v1         (historical optimizer candidate v1)
- o4-mini-cand-v1-append  (rich + historical optimizer postscript)
- o4-mini-rft-s100-cand-v1
- o4-mini-rft-s110-cand-v1
- o4-mini-rft-zavav1pt70-cand-v1  (RFT s115 deployed, default RFT model)

Run after RFT model is deployed and rubrics re-run, OR right now to
print the existing comparison.

Usage:
  python rft/compare_results.py
"""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
RL_RUBRIC = REPO / "rft" / "results" / "rl-rubric-eval"

VARIANTS = [
    ("baseline (rich Zava)",  "o4-mini",                          "o4-mini"),
    ("candidate v1",          "o4-mini-cand-v1",                  None),
    ("v1-append",             "o4-mini-cand-v1-append",           None),
    ("RFT s100 (cand-v1)",    "o4-mini-rft-s100-cand-v1",         "o4-mini-rft-s100"),
    ("RFT s110 (cand-v1)",    "o4-mini-rft-s110-cand-v1",         "o4-mini-rft-s110"),
    ("RFT s115 (cand-v1) ★",  "o4-mini-rft-zavav1pt70-cand-v1",   "o4-mini-rft-zavav1pt70"),
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_summary(path: Path) -> tuple[str, str]:
    """Return (score, pass) strings from a baseline/rich summary.json."""
    d = load_json(path)
    if not d:
        return ("—", "—")
    results = d.get("results", [])
    if not results:
        return ("—", "—")
    r = results[0]
    score = r.get("score")
    pas = r.get("pass")
    s_str = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
    p_str = f"{pas*100:.0f}%" if isinstance(pas, (int, float)) else "—"
    return (s_str, p_str)


def parse_strict(path: Path) -> tuple[str, str, str]:
    """Return (avg_score, pass_rate, billed_tokens) strings."""
    d = load_json(path)
    if not d:
        return ("—", "—", "—")
    s = d.get("avgScore")
    p = d.get("passRate")
    usage = d.get("usage_summary", {}) or {}
    tok = usage.get("total_billed_tokens")
    s_str = f"{s:.2f}" if isinstance(s, (int, float)) else "—"
    p_str = f"{p*100:.0f}%" if isinstance(p, (int, float)) else "—"
    t_str = f"{tok/1000:.0f}K" if isinstance(tok, (int, float)) else "—"
    return (s_str, p_str, t_str)


def parse_rl_rubric(deployment: str | None) -> str:
    """Return 'mean/pass%' string from rft/results/rl-rubric-eval/<deployment>.json."""
    if not deployment:
        return "—"
    path = RL_RUBRIC / f"{deployment}.json"
    d = load_json(path)
    if not d:
        return "—"
    m = d.get("mean_score")
    p = d.get("pass_rate_at_0.7")
    s_str = f"{m:.2f}" if isinstance(m, (int, float)) else "—"
    p_str = f"{p*100:.0f}%" if isinstance(p, (int, float)) else "—"
    return f"{s_str}/{p_str}"


def _get_row1_or_2(variant_dir: Path) -> str:
    """Return 'score/pass%' from either summary.json or an opt_*.json baseline."""
    summary = variant_dir / "summary.json"
    if summary.exists():
        s, p = parse_summary(summary)
        return f"{s}/{p}"

    if not variant_dir.exists():
        return "—"

    opt_files = list(variant_dir.glob("opt_*.json"))
    if not opt_files:
        return "—"

    d = load_json(opt_files[0])
    base = d.get("baseline") or {}
    if isinstance(base, dict):
        s = base.get("avgScore")
        p = base.get("passRate")
        s_str = f"{s:.2f}" if isinstance(s, (int, float)) else "—"
        p_str = f"{p*100:.0f}%" if isinstance(p, (int, float)) else "—"
        return f"{s_str}/{p_str}"
    return "—"


def main():
    headers = ("Variant", "Row 1 task_adh", "Row 2 8-builtins",
               "Row 3 strict", "RL-rubric (training)", "Tokens (Row 3)")
    print(f"{headers[0]:<24} {headers[1]:>16} {headers[2]:>20} "
          f"{headers[3]:>16} {headers[4]:>22} {headers[5]:>16}")
    print("-" * 122)

    for label, variant, deployment in VARIANTS:
        row1 = _get_row1_or_2(RESULTS / "baseline-2026-05-05" / variant)
        row2 = _get_row1_or_2(RESULTS / "rich-2026-05-05" / variant)
        row3_path = RESULTS / "strict-deterministic-2026-05-05" / variant / "strict-eval.json"
        s3, p3, tok = parse_strict(row3_path)
        row3 = f"{s3}/{p3}"
        rlr = parse_rl_rubric(deployment)

        print(f"{label:<24} {row1:>16} {row2:>20} {row3:>16} {rlr:>22} {tok:>16}")

    print("\nLegend: score / passRate.")
    print("  Row 1: task_adherence (historical optimizer LLM judge)")
    print("  Row 2: 8 builtins (historical optimizer LLM judge)")
    print("  Row 3: strict deterministic grader (must_contain/must_not_contain phrase lists)")
    print("  RL-rubric: rft/grader.py rolled out directly against the deployment")
    print("             (same scorer as RFT training; pass>=0.7)")
    print("  Tokens: total billed (input + output incl reasoning) on Row 3.")


if __name__ == "__main__":
    main()
