"""Zava 4-dim Python grader — a Foundry **custom code-based evaluator**.

Conforms to the Foundry custom-evaluator contract:
  https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/custom-evaluators

  def grade(sample: dict, item: dict) -> float

Returns a score in [0.0, 1.0]. Higher is better.

The same source string is also submitted to the OpenAI RFT API as the reward
function — so train and eval signals stay aligned (preventing reward hacking,
see the Zava-Ignite-RL-Lab references on `reward-hacking-prevention`).

Dimensions (weights):
  - Action correctness (0.4): refund / deny / store credit / replacement / exchange / cancel
  - Amount correctness (0.3): all expected $XX.XX strings appear in the response
  - Policy reasoning (0.2): cited terms like "window", "restocking", "defective", etc.
  - Tool usage (0.1): the model called `get_order`
"""
from __future__ import annotations

import inspect
import re


def grade(sample, item):
    output_text = sample.get("output_text", "") or ""
    output_tools = sample.get("output_tools", []) or []
    expected = item.get("expected_resolution", "")
    if not expected:
        return 0.5

    score = 0.0
    exp_lower = expected.lower()
    out_lower = output_text.lower()

    # 1. Action correctness (0.4)
    actions = {
        "refund":       ["refund"],
        "denied":       ["denied", "deny", "not eligible", "cannot", "expired"],
        "store credit": ["store credit", "store_credit"],
        "replacement":  ["replacement", "replace"],
        "exchange":     ["exchange", "swap"],
        "cancel":       ["cancel", "cancellation"],
    }
    for action, keywords in actions.items():
        if any(k in exp_lower for k in keywords):
            if any(k in out_lower for k in keywords):
                score += 0.4
            break

    # 2. Amount correctness (0.3) — all expected $XX.XX strings must appear
    exp_amounts = re.findall(r"\$(\d+\.\d{2})", expected)
    if exp_amounts:
        out_amounts = re.findall(r"\$(\d+\.\d{2})", output_text)
        hits = sum(1 for a in exp_amounts if a in out_amounts)
        score += 0.3 * (hits / len(exp_amounts))
    else:
        score += 0.15

    # 3. Policy reasoning (0.2)
    policy_terms = ["window", "restocking", "defective", "sale", "platinum", "gold",
                    "standard", "late", "shipping credit", "personal care", "eligible"]
    exp_terms = [t for t in policy_terms if t in exp_lower]
    if exp_terms:
        hits = sum(1 for t in exp_terms if t in out_lower)
        score += 0.2 * (hits / len(exp_terms))

    # 4. Tool usage (0.1)
    if output_tools:
        tool_names = [t.get("function", {}).get("name", "") for t in output_tools]
        if "get_order" in tool_names:
            score += 0.1

    return round(min(score, 1.0), 3)


def get_grader_source() -> str:
    """Return the literal Python source that defines grade(sample, item).

    This is the artifact uploaded to the OpenAI RFT API as the reward grader,
    and the same string you'd register as a Foundry custom code-based evaluator.
    """
    return "import re\n\n" + inspect.getsource(grade)


# Backwards-compatible alias — older callers (rft/submit.py, notebook §6) imported
# GRADER_SOURCE as a module-level string. Now resolved lazily from `grade()`'s source.
GRADER_SOURCE = get_grader_source()


if __name__ == "__main__":
    # Smoke test
    item = {"expected_resolution": "Refund $89.99 for defective keyboard. Gold tier, within 45-day window. Defective items have $0 restocking fee."}
    perfect = {
        "output_text": "Refund approved for $89.99 — defective item, no restocking fee. Gold tier, within 45-day window.",
        "output_tools": [{"function": {"name": "get_order", "arguments": "{}"}}],
    }
    bad = {"output_text": "Sorry, we cannot process this return.", "output_tools": []}
    print(f"perfect: {grade(perfect, item):.3f}")
    print(f"bad:     {grade(bad, item):.3f}")
