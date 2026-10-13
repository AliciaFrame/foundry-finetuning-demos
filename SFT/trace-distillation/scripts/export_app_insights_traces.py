"""Export hosted-agent conversations directly from Application Insights."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

def _message_from_parts(message: dict[str, Any]) -> dict[str, Any] | None:
    role = message.get("role")
    if role == "system":
        return None

    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    tool_call_id: str | None = None
    tool_response: str | None = None

    for part in message.get("parts") or []:
        part_type = part.get("type")
        if part_type == "text":
            text_parts.append(str(part.get("content") or ""))
        elif part_type == "tool_call":
            arguments = part.get("arguments") or {}
            tool_calls.append(
                {
                    "id": part.get("id"),
                    "type": "function",
                    "function": {
                        "name": part.get("name"),
                        "arguments": json.dumps(arguments, separators=(",", ":")),
                    },
                }
            )
        elif part_type == "tool_call_response":
            tool_call_id = part.get("id")
            tool_response = str(part.get("response") or "")

    if role == "tool":
        if not tool_call_id:
            return None
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": tool_response or "",
        }

    converted: dict[str, Any] = {"role": role}
    if tool_calls:
        converted["tool_calls"] = tool_calls
    if text_parts:
        converted["content"] = "\n".join(text_parts)
    elif not tool_calls:
        converted["content"] = ""
    return converted


def conversation_from_span(input_json: str, output_json: str) -> list[dict[str, Any]]:
    """Convert OpenTelemetry GenAI message parts to OpenAI chat messages."""
    input_messages = json.loads(input_json)
    output_messages = json.loads(output_json)
    messages = [
        converted
        for message in [*input_messages, *output_messages]
        if (converted := _message_from_parts(message)) is not None
    ]
    return messages


def export_app_insights_traces(
    *,
    resource_id: str,
    agent_name: str,
    agent_version: str,
    hours: int,
    max_samples: int,
    output_path: str | Path,
) -> Path:
    """Query complete hosted-agent conversations and write raw JSONL."""
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import LogsQueryClient, LogsQueryStatus

    escaped_name = agent_name.replace("'", "''")
    escaped_version = agent_version.replace("'", "''")
    query = f"""
dependencies
| where name startswith "chat "
| where tostring(customDimensions["gen_ai.agent.name"]) == '{escaped_name}'
| where tostring(customDimensions["gen_ai.agent.version"]) == '{escaped_version}'
| extend input=tostring(customDimensions["gen_ai.input.messages"])
| extend output=tostring(customDimensions["gen_ai.output.messages"])
| where isnotempty(input) and isnotempty(output)
| summarize arg_max(timestamp, input, output) by operation_Id
| top {max(1, int(max_samples))} by timestamp desc
| project operation_Id, input, output
"""

    client = LogsQueryClient(DefaultAzureCredential())
    response = client.query_resource(
        resource_id,
        query,
        timespan=timedelta(hours=max(1, int(hours))),
    )
    if response.status == LogsQueryStatus.PARTIAL:
        raise RuntimeError(f"Application Insights query was partial: {response.partial_error}")
    if not response.tables:
        raise RuntimeError("Application Insights returned no trace table.")

    table = response.tables[0]
    columns = [
        column if isinstance(column, str) else column.name for column in table.columns
    ]
    records: list[dict[str, Any]] = []
    for values in table.rows:
        row = dict(zip(columns, values))
        messages = conversation_from_span(row["input"], row["output"])
        if any(message.get("tool_calls") for message in messages):
            records.append({"messages": messages})

    if not records:
        raise RuntimeError(
            "No complete tool-using conversations were found in Application Insights."
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
