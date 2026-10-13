# Foundry Fine-Tuning Demos

Curated, runnable examples for supervised fine-tuning (SFT) and reinforcement
fine-tuning (RFT) on Microsoft Foundry.

The collection is organized by training method. Each demo includes its own
setup, data instructions, reported results, limitations, and attribution.
Cloud runs create billable resources; review the cost notes before submitting
training jobs or deploying models.

See [Notebook execution status](EXECUTION_STATUS.md) for the current
end-to-end validation matrix and its blockers.

## SFT demos

| Demo | Level | What it teaches | Historical result |
|---|---|---|---|
| [Distilling sarcasm](SFT/distilling-sarcasm/) | Beginner | Teacher/student selection and behavioral distillation | 2026 smoke: pass `70%` to `80%`, mean `5.2` to `5.0` (n=10; inconclusive) |
| [Bug detection](SFT/bug-detection/) | Beginner | Text SFT with a deterministic task | 2026 smoke: mean `8.33` to `8.63`; pass rate unchanged at `80%` (n=10) |
| [NL-to-Python distillation](SFT/nl-to-python-distillation/) | Intermediate | Synthetic data generation and code distillation | 2026 smoke: combined `8.25` to `8.75` (n=2; pipeline evidence only) |
| [Image breed classification](SFT/image-breed-classification/) | Intermediate | Vision SFT versus zero-shot and CNN baselines | 2026 smoke: base and FT both `3/3`; historical full run `73.67%` to `82.67%` |
| [Chart analysis](SFT/chart-analysis/) | Intermediate | Visual question answering with ChartQA | 2026 smoke: base `17/20`; FT `16/20`; no improvement |
| [Video action recognition](SFT/video-action-recognition/) | Advanced | Video-frame SFT and evaluation | Live preprocessing verified; training blocked by people/face content policy |
| [Trace distillation](SFT/trace-distillation/) | Advanced | Turning agent traces into tool-use SFT data | 2026 fixture smoke: `75%` to `100%` pass (n=4) |

## RFT demos

| Demo | Level | What it teaches | Historical result |
|---|---|---|---|
| [Countdown](RFT/countdown/) | Beginner | Structured outputs and deterministic or endpoint graders | Python-grader training passed; deployment blocked by quota |
| [Math reasoning](RFT/math-reasoning/) | Intermediate | Final-answer verification with OpenR1-Math | Matching completed job reused; deployment and live inference passed |
| [Zava agentic RFT](RFT/zava-agentic-rft/) | Advanced | Current Agent Optimizer assets, tool-use RFT, grader calibration, checkpoints, and independent evaluation | Mean reward `0.61` to `0.80` with prompt held fixed |

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
