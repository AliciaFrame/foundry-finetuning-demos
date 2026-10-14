# Zava Agent Optimizer Assets

This directory contains the current Microsoft Foundry Agent Optimizer inputs
for the Zava hosted-agent experiment. The optimizer is a limited preview; it
requires allow-listed access and is not recommended for production workloads.

## Contents

- `.agent_configs/baseline/`: current baseline configuration loaded by
  `azure-ai-agentserver-optimization`.
- `eval.yaml`: standalone `azd ai agent optimize` configuration.
- `eval.jsonl`: 26 fictional evaluation tasks in the current
  `query` + `criteria` schema.
- `optimize_hosted_agent.py`: supported Python SDK path for a registered
  Foundry dataset and evaluator.
- `zava_tools.py` and `data/zava_db.json`: deterministic fictional tool
  implementations and records for a hosted agent.

## Preferred standalone `azd` workflow

The deployed hosted agent must already call
`azure.ai.agentserver.optimization.load_config()` and use the returned model,
instructions, skills, and tool descriptions. This folder does not deploy or
mutate an existing agent.

1. Install or upgrade the Foundry extension:

   ```powershell
   azd ext install microsoft.foundry
   azd ext upgrade microsoft.foundry
   ```

2. Authenticate and select the Foundry project:

   ```powershell
   az login
   azd auth login
   azd ai project set "<project-endpoint>"
   azd ai project show
   ```

3. Edit the deployment names in `eval.yaml`, then run from this directory:

   ```powershell
   azd ai agent optimize --agent "<deployed-agent-name>" --config eval.yaml
   ```

   Because this is a standalone folder rather than an `azd` deployment
   project, run interactively and select
   `.agent_configs/baseline/instructions.md` when prompted for the baseline
   instruction.

4. Save the operation ID and monitor it explicitly:

   ```powershell
   azd ai agent optimize status "<operation-id>" --watch
   ```

For a standalone run, review and promote the candidate in the Foundry portal.
`azd ai agent optimize apply` requires an `azure.yaml` hosted-agent project.

## Python SDK workflow

The Python script targets an existing deployed hosted agent and expects the
dataset to be registered in the Foundry project:

```powershell
Copy-Item ..\.env.example .env
python optimize_hosted_agent.py
```

Required environment variables are `FOUNDRY_PROJECT_ENDPOINT`,
`FOUNDRY_AGENT_NAME`, and `DATASET_NAME`. The script supports resuming with
`OPTIMIZATION_JOB_ID`; it does not deploy or apply a candidate.

## Safety

Optimization invokes the agent for every task and candidate. If the deployed
agent calls stateful or paid tools, point it at a test endpoint or mock those
tools before starting a run. The bundled Zava records are fictional.

## Current documentation

- [Agent optimizer overview](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
- [Optimize a hosted agent](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-hosted-agent?pivots=azd)
- [Make a hosted agent optimizer-ready](https://learn.microsoft.com/azure/foundry/agents/how-to/make-agent-optimizer-ready)
- [Configure optimizer targets](https://learn.microsoft.com/azure/foundry/agents/how-to/optimize-agent-targets)
