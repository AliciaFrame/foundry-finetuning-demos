# Foundry Fine-Tuning Demos

Curated, runnable examples for supervised fine-tuning (SFT) and reinforcement
fine-tuning (RFT) on Microsoft Foundry.

The collection is organized by training method. Each demo includes its own
setup, data instructions, reported results, limitations, and attribution.
Cloud runs create billable resources; review the cost notes before submitting
training jobs or deploying models.

## SFT demos

| Demo | Level | What it teaches | Historical result |
|---|---|---|---|
| [Distilling sarcasm](SFT/distilling-sarcasm/) | Beginner | Teacher/student selection and behavioral distillation | `27%` to `83.84%` pass rate |
| [Bug detection](SFT/bug-detection/) | Beginner | Text SFT with a deterministic task | Approximately `80%` to `90%` pass rate in the tracked run |
| [NL-to-Python distillation](SFT/nl-to-python-distillation/) | Intermediate | Synthetic data generation and code distillation | Historical artifacts require a clean rerun |
| [Image breed classification](SFT/image-breed-classification/) | Intermediate | Vision SFT versus zero-shot and CNN baselines | `73.67%` to `82.67%` accuracy |
| [Chart analysis](SFT/chart-analysis/) | Intermediate | Visual question answering with ChartQA | Rerun required to publish a numeric comparison |
| [Video action recognition](SFT/video-action-recognition/) | Advanced | Video-frame SFT and evaluation | FT run reported `99%`; base comparison must be rerun |
| [Trace distillation](SFT/trace-distillation/) | Advanced | Turning agent traces into tool-use SFT data | `60%` to `100%` pass rate in the original experiment |

## RFT demos

| Demo | Level | What it teaches | Historical result |
|---|---|---|---|
| [Countdown](RFT/countdown/) | Beginner | Structured outputs and deterministic or endpoint graders | Mechanics sample; rerun required |
| [Math reasoning](RFT/math-reasoning/) | Intermediate | Final-answer verification with OpenR1-Math | Rerun required |
| [Zava agentic RFT](RFT/zava-agentic-rft/) | Advanced | Tool-use RFT, grader calibration, checkpoints, and independent evaluation | Mean reward `0.61` to `0.80` with prompt held fixed |

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
