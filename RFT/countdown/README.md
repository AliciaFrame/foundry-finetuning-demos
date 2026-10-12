# Countdown RFT

This demo teaches reinforcement fine-tuning with an arithmetic Countdown task.
The model must use every supplied number exactly once and emit a structured
expression and result. Correctness can be checked automatically, making the
task a compact introduction to RFT.

Originally contributed by Jayesh Tanna. The optional endpoint-grader example
was contributed by Dave Voutila.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.template .env
```

Configure the endpoint in `.env`:

```env
AZURE_API_KEY="YOUR_AZURE_OPENAI_API_KEY_HERE"
AZURE_API_ENDPOINT="https://<resource>.openai.azure.com/openai/v1/"
```

Open `demo_with_python_grader.ipynb` for the preferred inline-grader path.
The older `demo.ipynb` demonstrates a model-based grader. Both notebooks cover
data preparation, base-model evaluation, RFT submission, and checkpoint
evaluation.

The [`endpoint-grader/`](endpoint-grader/) directory contains an optional Azure
Function implementation for environments that require a hosted grader.

## Results

The archived run did not preserve a reliable final base-versus-checkpoint
table. Treat this sample as unverified until you rerun the held-out evaluation
and record the exact model, checkpoint, grader threshold, date, cost, and pass
rate.

RFT model, region, grader, and API support changes over time. Check current
Microsoft Foundry documentation before submitting a paid run.
