# Zava Agentic RFT

An end-to-end agentic reinforcement fine-tuning example for a fictional
post-purchase resolution desk. The model must call `get_order`, select the
correct action, calculate exact amounts, and cite policy.

## Result

The same 57-row validation set and Python grader were used for all three
stages:

| Stage | Prompt | Model | Mean reward | Pass at 0.7 |
|---|---|---|---:|---:|
| Raw base | Rich Zava prompt | `o4-mini` | 0.30 | 9% |
| Prompt optimized | Historical FAOS candidate v1 | `o4-mini` | 0.61 | 44% |
| RFT checkpoint | Candidate v1 | RFT step 115 | **0.80** | **75%** |

The RFT-only comparison holds the prompt fixed: `0.61` to `0.80`. Offline
replay over all 57 rows preserved the training checkpoint ordering
(`step 115 > step 110 > step 100 > base`). These results were recorded in May
2026 with a pre-release FAOS API and should be treated as an experiment
receipt, not a timeless model or current-service claim.

## Contents

- `notebooks/e2e_demo.ipynb`: narrative walkthrough. Outputs are stripped;
  committed JSON files contain the evidence.
- `rft/grader.py`: four-dimensional partial-credit grader.
- `rft/calibrate.py`: calibrates the pass threshold on the base model.
- `rft/submit.py`: uploads data and submits an RFT job.
- `rft/grade_with_rl_rubric.py`: independently replays a deployment.
- `rft/data/`: 343 fictional training scenarios and 57 held-out scenarios.
- `rft/results/`: sanitized historical result artifacts.
- `agent/`: current Agent Optimizer baseline, evaluation data, `azd`
  configuration, Python SDK client, and fictional tool implementation.
- `results/`: sanitized historical FAOS and comparison artifacts consumed by
  the notebook. These are evidence, not current API examples.
- `tool-service/`: self-contained Azure Function/FastAPI implementation for
  the fictional `get_order` tool.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

The notebook defaults to artifact-only mode and can reproduce the historical
tables without Azure credentials. It no longer submits agent-optimization jobs:
the old direct FAOS HTTP endpoint has been retired from the example.

For a new optimization run, follow [`agent/README.md`](agent/README.md). The
preferred path is the current `azd ai agent optimize` workflow with
`agent/eval.yaml` and `.agent_configs/baseline/`. A supported Python SDK client
is also included for projects where the dataset and evaluator are registered.
Agent Optimizer is a limited preview that requires allow-listed access and is
not recommended for production workloads.

To rerun the RFT portion, authenticate with `az login`, fill in `.env`, deploy
`tool-service`, and set `ZAVA_TOOL_ENDPOINT` to its `/tool/get_order` URL.

```powershell
python rft/calibrate.py --n 30
python rft/submit.py --pass-threshold 0.8
python rft/monitor.py
```

RFT and agentic tool support vary by model, region, and service version. Check
current Foundry availability before incurring training cost. The original run
took approximately six hours and cost roughly USD 200.

## Privacy

All checked-in people, orders, and results are fictional. Do not substitute
production customer records or traces without consent, redaction, retention,
and access-control review.
