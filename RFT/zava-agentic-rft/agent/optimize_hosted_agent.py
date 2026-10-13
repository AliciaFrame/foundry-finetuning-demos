"""Run the current Microsoft Foundry optimizer against a deployed Zava agent.

The Azure Developer CLI flow in README.md is preferred for local JSONL data.
This SDK path is useful when the evaluation dataset and evaluator are already
registered in the Foundry project.
"""

import os
import time
from pathlib import Path

from azure.ai.agentserver.optimization import load_config, load_skills_from_dir
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentOptimizationBaselineAgentConfiguration,
    AgentOptimizationCandidateExpand,
    AgentOptimizationCandidateSearchConfiguration,
    AgentOptimizationConfiguration,
    AgentOptimizationEvaluationConfiguration,
    AgentOptimizationEvaluator,
    AgentOptimizationFoundryAgentTargetConfiguration,
    AgentOptimizationJob,
    AgentOptimizationModelConfiguration,
    AgentOptimizationSkill,
    AgentOptimizationSpace,
    AgentOptimizationTargetCompletionDatasetReferenceDataSource,
    AgentOptimizationTargetCompletionEvaluationSet,
    EvaluationModelConfiguration,
    JobStatus,
    TargetAttribute,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


AGENT_DIR = Path(__file__).resolve().parent


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Set {name} before running optimization.")
    return value


def build_job() -> AgentOptimizationJob:
    config = load_config(config_dir=AGENT_DIR / ".agent_configs")
    if config is None:
        raise RuntimeError("Could not load .agent_configs/baseline/metadata.yaml.")

    configured_skills = list(config.skills or [])
    if config.skills_dir:
        configured_skills.extend(load_skills_from_dir(Path(config.skills_dir)))

    target_attributes = [TargetAttribute.INSTRUCTIONS]
    skills = [
        AgentOptimizationSkill(
            name=skill.name,
            description=skill.description,
            body=skill.body or None,
        )
        for skill in configured_skills
    ]
    if skills:
        target_attributes.append(TargetAttribute.SKILLS)
    if config.tool_definitions:
        target_attributes.append(TargetAttribute.TOOLS)

    baseline = AgentOptimizationBaselineAgentConfiguration(
        system_prompt=config.instructions,
        current_model=config.model,
        skills=skills or None,
        tools=config.tool_definitions or None,
    )
    return AgentOptimizationJob(
        target_configuration=AgentOptimizationFoundryAgentTargetConfiguration(
            name=required_env("FOUNDRY_AGENT_NAME")
        ),
        optimization_model_configuration=AgentOptimizationModelConfiguration(
            model=os.environ.get("OPTIMIZATION_MODEL", "gpt-5.1")
        ),
        optimization_configuration=AgentOptimizationConfiguration(
            evaluation_configuration=AgentOptimizationEvaluationConfiguration(
                training_set=AgentOptimizationTargetCompletionEvaluationSet(
                    source=AgentOptimizationTargetCompletionDatasetReferenceDataSource(
                        name=required_env("DATASET_NAME"),
                        version=os.environ.get("DATASET_VERSION", "1"),
                    )
                ),
                evaluators=[
                    AgentOptimizationEvaluator(
                        name=os.environ.get(
                            "EVALUATOR_NAME", "builtin.task_adherence"
                        )
                    )
                ],
                evaluation_model=EvaluationModelConfiguration(
                    model=os.environ.get("EVAL_MODEL", "gpt-4.1-mini")
                ),
            ),
            candidate_search_configuration=(
                AgentOptimizationCandidateSearchConfiguration(
                    max_candidates=int(os.environ.get("MAX_CANDIDATES", "2"))
                )
            ),
            baseline_agent_configuration=baseline,
            agent_optimization_space=AgentOptimizationSpace(
                target_attributes=target_attributes
            ),
        ),
    )


def main() -> None:
    load_dotenv(override=False)
    poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "10"))
    terminal = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=required_env("FOUNDRY_PROJECT_ENDPOINT"),
            credential=credential,
        ) as project_client,
    ):
        existing_job_id = os.environ.get("OPTIMIZATION_JOB_ID")
        if existing_job_id:
            job_id = existing_job_id
        else:
            poller = project_client.agents.begin_create_optimization_job(
                job=build_job(),
                polling=False,
            )
            job_id = poller.details.get("job_id")
            if not isinstance(job_id, str):
                raise RuntimeError("The create operation returned no job ID.")

        print(f"Optimization job ID: {job_id}")
        job = project_client.agents.get_optimization_job(job_id=job_id)
        while job.status not in terminal:
            print(f"status={job.status}")
            time.sleep(poll_interval)
            job = project_client.agents.get_optimization_job(job_id=job_id)

        if job.status != JobStatus.SUCCEEDED or job.result is None:
            message = job.error.message if job.error else job.status
            raise RuntimeError(f"Optimization job failed: {message}")

        summary = job.result.candidate_summary
        if summary:
            print(f"Baseline: {summary.baseline_id} ({summary.baseline_score})")
            print(f"Best: {summary.best_id} ({summary.best_score})")

        for candidate in project_client.agents.list_optimization_candidates(
            job_id=job_id,
            expand=[AgentOptimizationCandidateExpand.MUTATIONS],
        ):
            score = (
                candidate.evaluation.score
                if candidate.evaluation is not None
                else None
            )
            print(
                f"{candidate.name}: id={candidate.candidate_id} "
                f"status={candidate.status} score={score}"
            )


if __name__ == "__main__":
    main()
