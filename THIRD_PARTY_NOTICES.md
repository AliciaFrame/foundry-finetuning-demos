# Third-Party Notices

This repository curates examples originally developed in the MIT-licensed
[`microsoft-foundry/fine-tuning`](https://github.com/microsoft-foundry/fine-tuning)
repository. The original Azure AI Foundry MIT notice is retained in
[`LICENSE`](LICENSE).

## Demo attribution

| Demo | Primary contributor(s) | Source |
|---|---|---|
| Distilling sarcasm | Dave Voutila | `microsoft-foundry/fine-tuning`, based on the Azure AI Foundry Build 2025 distillation demo |
| Bug detection | Alicia Frame | `microsoft-foundry/fine-tuning` |
| NL-to-Python distillation | Alicia Frame | `microsoft-foundry/fine-tuning` |
| Image breed classification | `alevretmicrosoft` | `microsoft-foundry/fine-tuning` |
| Video action recognition | Andreas Kopp | `microsoft-foundry/fine-tuning` |
| Trace distillation | Alicia Frame | `microsoft-foundry/fine-tuning` |
| Countdown RFT | Jayesh Tanna; endpoint-grader material by Dave Voutila | `microsoft-foundry/fine-tuning` |
| Math reasoning RFT | Jayesh Tanna | `microsoft-foundry/fine-tuning` |
| Zava agentic RFT | Alicia Frame | `AliciaFrame/continuous-learning-FAOS` and `AliciaFrame/Zava-Ignite-RL-Lab` |

## Dataset and asset terms

- **OpenR1-Math-220k** is licensed under Apache License 2.0. The included
  subset retains that license in
  [`RFT/math-reasoning/DATA_LICENSE`](RFT/math-reasoning/DATA_LICENSE).
- **Countdown** rows in this repository are generated locally by
  [`generate_data.py`](RFT/countdown/scripts/generate_data.py); no rows from the
  unlicensed `predibase/countdown` dataset are redistributed.
- **Stanford Dogs** images are not redistributed. The image demo can download
  them from the `maurice-fp/stanford-dogs` Hugging Face mirror; the underlying
  Stanford Dogs/ImageNet image terms still apply.
- **UCF101** videos and extracted frames are not redistributed. The video demo
  can download the Apache-2.0 `sayakpaul/ucf101-subset` package for smoke
  testing. Users must still cite the UCF101 dataset authors.
- Synthetic Zava customers, orders, products, and results are fictional.

Third-party package licenses continue to apply to installed dependencies.
