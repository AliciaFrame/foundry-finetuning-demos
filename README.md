# Foundry Fine-Tuning Demos

Curated, runnable examples for supervised fine-tuning (SFT) and reinforcement
fine-tuning (RFT) on Microsoft Foundry.

The collection is organized by training method. Each demo includes its own
setup, data instructions, reported results, limitations, and attribution.
Cloud runs create billable resources; review the cost notes before submitting
training jobs or deploying models.

## SFT demos

| Demo | Level | What it teaches | Result |
|---|---|---|---|
| [Distilling sarcasm](SFT/distilling-sarcasm/) | Beginner | Teacher/student selection and behavioral distillation | Pass rate `70%` to `80%`; mean `5.2` to `5.0` (n=10; inconclusive) |
| [Bug detection](SFT/bug-detection/) | Beginner | Text SFT with a deterministic task | Mean `8.33` to `8.63`; pass rate unchanged at `80%` (n=10) |
| [NL-to-Python distillation](SFT/nl-to-python-distillation/) | Intermediate | Synthetic data generation and code distillation | Combined score `8.25` to `8.75` (n=2; pipeline evidence only) |
| [Image breed classification](SFT/image-breed-classification/) | Intermediate | Vision SFT versus zero-shot and CNN baselines | Base and fine-tuned models both `3/3` on the compact run |
| [Video action recognition](SFT/video-action-recognition/) | Advanced | Video-frame SFT and evaluation | Accuracy `26.7%` to `33.3%` (n=30); fine-tuned predictions collapsed to one class |
| [Trace distillation](SFT/trace-distillation/) | Advanced | Turning agent traces into tool-use SFT data | Base and fine-tuned models both passed `100%` (n=2) |

## RFT demos

| Demo | Level | What it teaches | Result |
|---|---|---|---|
| [Countdown](RFT/countdown/) | Beginner | Structured outputs and deterministic or endpoint graders | Pass rate `100%` to `95%` (n=20; no quality improvement) |
| [Math reasoning](RFT/math-reasoning/) | Intermediate | Final-answer verification with OpenR1-Math | Base and fine-tuned models both scored `60%` (6/10) |
| [Zava agentic RFT](RFT/zava-agentic-rft/) | Advanced | Current Agent Optimizer assets, tool-use RFT, grader calibration, checkpoints, and independent evaluation | Mean reward `0.647` to `0.846`; pass rate `37%` to `77%` (n=57) |

## Repository principles

- Baseline before training.
- Validate datasets before upload.
- Calibrate RFT graders so the base model has useful score variance.
- Evaluate retained checkpoints, not only the final checkpoint.
- Keep independent promotion evaluation separate from the training reward.
- Record model versions, dates, costs, and limitations with every result.
- Never commit credentials, customer traces, or account-specific endpoints.

The companion
[Foundry fine-tuning skill](https://github.com/AliciaFrame/foundry-finetuning-skill)
contains reusable validators, submission scripts, and detailed methodology.

## Licensing

Unless a file or dataset says otherwise, code and documentation are available
under the [MIT License](LICENSE). Third-party datasets and assets retain their
original terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
