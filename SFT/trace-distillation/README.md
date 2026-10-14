# Trace Distillation

Fine-tune a smaller model to reproduce the first-turn tool-calling behavior of
a Microsoft Foundry hosted agent.

The notebook:

1. Exports live GenAI spans from Application Insights or Foundry Data
   Generation.
2. Converts traces into valid tool-use fine-tuning rows.
3. Splits the rows into training, validation, and test sets.
4. Evaluates the base student.
5. Trains and deploys the student model.
6. Evaluates the fine-tuned deployment on the same held-out rows.

## Result

The live run exported 14 tool-using conversations and split them into 11
training, 1 validation, and 2 test rows.

| Model | Structural score | Pass rate |
|---|---:|---:|
| Base `gpt-4.1-mini` | 10.0/10 | 100% |
| Fine-tuned `gpt-4.1-mini` | 10.0/10 | 100% |

The full live pipeline completed successfully, but the two-row test set was
too small and too easy to demonstrate quality lift. The evaluator compares the
ordered first-turn tool calls and arguments; it does not execute tools or
score the complete multi-turn trajectory.

## Prerequisites

- A Microsoft Foundry project with a deployed hosted agent and Application
  Insights.
- A student model that supports supervised fine-tuning.
- Azure CLI authentication.
- Python 3.11+.

Install dependencies:

```powershell
pip install -r requirements.txt
```

Configure the project and deployment:

```powershell
$env:AZURE_AI_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"
$env:OPENAI_BASE_URL = "https://<resource>.services.ai.azure.com/openai/v1"
$env:AZURE_OPENAI_API_KEY = "<key>"
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "<resource-group>"
$env:AZURE_ACCOUNT_NAME = "<resource-name>"
$env:FOUNDRY_AGENT_NAME = "<agent-name>"
$env:FOUNDRY_AGENT_VERSION = "<agent-version>"
```

Choose one trace source:

1. Set `TRACE_INPUT_FILE` to a reviewed JSONL export.
2. Set `APPLICATIONINSIGHTS_RESOURCE_ID` to query Application Insights
   directly with Azure RBAC.
3. Leave both unset to use the Foundry Data Generation API.

Then run [`notebook.ipynb`](notebook.ipynb).

## Files

| File | Purpose |
|---|---|
| `notebook.ipynb` | End-to-end trace export, SFT, deployment, and evaluation |
| `scripts/export_app_insights_traces.py` | Direct RBAC-authenticated Application Insights exporter |
| `fixtures/push_prompts.py` | Generates agent traffic when trace history is empty |
| `fixtures/sample_agent_traces.jsonl` | Sanitized synthetic traces for local pipeline testing |
| `fixtures/zava_system_prompt.md` | Example system prompt |
| `fixtures/zava_tools.json` | Example OpenAI-format tool catalog |

## Why traces need transformation

Current trace exports can contain overlapping snapshots, incomplete
conversations, literal `"null"` content, adjacent assistant tool-call turns,
and missing system prompts or tool definitions. The notebook normalizes these
cases before upload and validates the resulting message sequence.

## Privacy

Agent traces may contain prompts, tool arguments, tool outputs, identifiers,
and customer data. Obtain consent, apply redaction and retention controls, and
review every generated row before upload. Never commit production traces. The
direct Application Insights exporter does not apply the Data Generation
service's private-content redaction.
