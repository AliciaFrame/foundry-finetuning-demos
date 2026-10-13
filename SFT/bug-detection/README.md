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

The original published percentages were not accompanied by the evaluation rows
that produced them, and the checked-in notebook evaluates ten examples. They
are therefore not reproducible from this repository and have been removed.
Run the notebook to produce a fresh base, fine-tuned, and teacher comparison;
record the denominator, model versions, date, and current pricing with any
result you publish.

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
