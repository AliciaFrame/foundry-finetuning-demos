import os, json
from azure.identity import DefaultAzureCredential
from openai import OpenAI
endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
base = endpoint.rstrip("/") + "/openai/v1/"
token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
client = OpenAI(base_url=base, api_key=token)
job_id = os.environ["RFT_JOB_ID"]

job = client.fine_tuning.jobs.retrieve(job_id)
print("Full job dict (selected fields):")
print(json.dumps({
    "id": job.id,
    "status": job.status,
    "model": job.model,
    "fine_tuned_model": getattr(job, "fine_tuned_model", None),
    "trained_tokens": getattr(job, "trained_tokens", None),
    "result_files": getattr(job, "result_files", None),
    "estimated_finish": getattr(job, "estimated_finish", None),
    "method": str(getattr(job, "method", None))[:200],
}, indent=2, default=str))

# Try the checkpoints endpoint (if exposed)
try:
    cps = client.fine_tuning.jobs.checkpoints.list(job_id, limit=20)
    print("\n=== CHECKPOINTS ===")
    for cp in cps.data:
        print(f"  {cp.id}  step={getattr(cp, 'step_number', None)}  metrics={getattr(cp, 'metrics', None)}  model={getattr(cp, 'fine_tuned_model_checkpoint', None)}")
except Exception as exc:
    print(f"\nCheckpoints API error: {exc!r}")
