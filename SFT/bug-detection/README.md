# SFT Bug Detection Demo

**Technique**: Supervised Fine-Tuning (SFT) — Distillation
**Use Case**: Teaching GPT-4.1-mini to identify bugs in code, explain them, and suggest fixes
**Base Model**: GPT-4.1-mini
**Teacher Model**: GPT-5.4 (used for data generation and as evaluation judge)
**Dataset**: 224 training / 20 validation examples across 10 bug categories

## What You'll Learn

1. **Baseline evaluation** — Measure the base model's bug detection ability before training
2. **Fine-tuning** — Submit an SFT job with optimal hyperparameters (2 epochs, lr=0.8)
3. **Evaluation** — Compare the fine-tuned model against both the base model and the teacher
4. **ROI analysis** — Compare quality and token pricing for the student and teacher

## Results

The end-to-end run produced this ten-example result:

| Model | Mean combined score | Pass rate at 7 |
|---|---:|---:|
| GPT-4.1-mini base | 8.33 | 80% (8/10) |
| GPT-4.1-mini fine-tuned | 8.63 | 80% (8/10) |
| GPT-5.4 teacher/judge | 8.80 | 80% (8/10) |

The fine-tuned model improved mean score by 0.30 but did **not** improve pass
rate. Ten rows are enough to validate the workflow, not to establish a robust
quality claim.

## Prerequisites

- Azure AI Foundry project with fine-tuning access
- Python 3.9+
- `pip install -r requirements.txt`
- Copy `.env.template` to `.env` and fill in your Azure credentials

## Files

| File | Description |
|------|-------------|
| `Bug_Detection_Fine_Tuning.ipynb` | Main notebook — run cells sequentially |
| `requirements.txt` | Python dependencies |
| `.env.template` | Environment variable template |

Training and validation data are bundled in [`data/`](data/): 224 training
rows and 20 validation rows.

## Bug Categories Covered

The dataset covers 10 types of bugs across Python, JavaScript, Java, and C++:

1. Off-by-one errors
2. Null/undefined reference
3. Type mismatches
4. Resource leaks
5. Race conditions
6. Buffer overflows
7. Integer overflow
8. Logic errors
9. Unhandled exceptions
10. Security vulnerabilities (SQL injection, XSS)
