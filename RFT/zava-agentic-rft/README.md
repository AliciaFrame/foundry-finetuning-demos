# Zava Agentic RFT

An end-to-end agentic reinforcement fine-tuning example for a fictional
post-purchase resolution desk. The model calls `get_order`, selects the correct
resolution, calculates exact amounts, and explains the applicable policy.

## What the notebook does

1. Evaluates the base `o4-mini` deployment on 57 held-out scenarios.
2. Uploads 343 training rows and 57 validation rows.
3. Submits a fresh tool-using RFT job with a Python partial-credit grader.
4. Monitors training to completion.
5. Deploys the fine-tuned model.
6. Evaluates it with the same prompt, tool, scenarios, and grader used for the
   baseline.

The grader rewards action correctness, amount correctness, policy reasoning,
and use of the `get_order` tool. The serialized grader is tested in isolation
before submission so its sandbox dependencies are explicit.

## Result

The end-to-end run trained on 343 scenarios, validated on 57 scenarios, and
evaluated the base and fine-tuned deployments on all 57 held-out scenarios
with the same prompt, tool, and grader.

| Model | Mean reward | Pass rate at 0.8 |
|---|---:|---:|
| Base `o4-mini` | 0.647 | 37% |
| Fine-tuned `o4-mini` | 0.846 | 77% |

The fine-tuned model improved mean reward by 0.199 and pass rate by 40
percentage points on this evaluation. The scenarios and grader are compact
instructional assets; use a larger independent set before selecting a model
for production.

## Contents

| Path | Purpose |
|---|---|
| `notebooks/e2e_demo.ipynb` | Complete baseline, training, deployment, and evaluation walkthrough |
| `rft/data/` | 343 fictional training scenarios and 57 held-out scenarios |
| `rft/grader.py` | Four-dimensional partial-credit grader |
| `rft/calibrate.py` | Base-model grader calibration |
| `rft/submit.py` | Command-line RFT submission |
| `rft/monitor.py` | Training-event monitor |
| `tool-service/` | Azure Function/FastAPI implementation of `get_order` |
| `agent/` | Optional current Agent Optimizer inputs for the hosted-agent prompt |

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
az login
```

Deploy `tool-service` and configure:

```powershell
$env:AZURE_AI_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"
$env:ZAVA_TOOL_BASE_URL = "https://<function-app>.azurewebsites.net"
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "<resource-group>"
$env:AZURE_AOAI_ACCOUNT = "<resource-name>"
$env:RFT_BASE_MODEL = "o4-mini"
$env:RFT_DEPLOYMENT = "zava-rft"
```

Run [`notebooks/e2e_demo.ipynb`](notebooks/e2e_demo.ipynb).

`ZAVA_RFT_JOB_ID` can resume a job created by an interrupted notebook
execution. Evaluation progress is cached under the ignored `run/` directory so
a transient tool or authentication failure does not discard completed rows.

The optional [`agent/`](agent/) folder follows the current Agent Optimizer
workflow. Agent Optimizer is a limited preview and is not required for the RFT
notebook.

## Privacy

All checked-in customers, orders, products, and scenarios are fictional. Do
not replace them with production records without consent, redaction,
retention, and access-control review.
