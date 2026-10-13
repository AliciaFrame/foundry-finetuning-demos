import ast
import importlib.util
import json
import re
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DEMOS = {
    "SFT": {
        "distilling-sarcasm",
        "bug-detection",
        "nl-to-python-distillation",
        "image-breed-classification",
        "video-action-recognition",
        "trace-distillation",
    },
    "RFT": {"countdown", "math-reasoning", "zava-agentic-rft"},
}

EXPECTED_JSONL_COUNTS = {
    "SFT/bug-detection/data/training_data.jsonl": 224,
    "SFT/bug-detection/data/validation_data.jsonl": 20,
    "SFT/nl-to-python-distillation/training_data.jsonl": 1576,
    "SFT/nl-to-python-distillation/validation_data.jsonl": 83,
    "RFT/math-reasoning/training_rft.jsonl": 100,
    "RFT/math-reasoning/validation_rft.jsonl": 10,
    "RFT/zava-agentic-rft/rft/data/zava_v1_train.jsonl": 343,
    "RFT/zava-agentic-rft/rft/data/zava_v1_val.jsonl": 57,
}


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_expected_demo_structure():
    for method, demos in EXPECTED_DEMOS.items():
        actual = {path.name for path in (ROOT / method).iterdir() if path.is_dir()}
        assert actual == demos
        for demo in demos:
            folder = ROOT / method / demo
            assert (folder / "README.md").exists()
            assert (folder / "requirements.txt").exists()
            assert any(folder.glob("*.ipynb")) or any(folder.glob("notebooks/*.ipynb"))


def test_jsonl_is_valid_and_complete():
    for relative, expected_count in EXPECTED_JSONL_COUNTS.items():
        path = ROOT / relative
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(rows) == expected_count


def test_math_rft_answers_are_well_formed():
    demo = ROOT / "RFT/math-reasoning"
    for path in [demo / "training_rft.jsonl", demo / "validation_rft.jsonl"]:
        for line in path.read_text(encoding="utf-8").splitlines():
            answer = json.loads(line)["answer"]
            depth = 0
            for char in answer:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    assert depth >= 0, f"Unmatched closing brace in {answer!r}"
            assert depth == 0, f"Unmatched opening brace in {answer!r}"
            assert not answer.rstrip().endswith(("\\", "{"))


def test_notebooks_are_clean():
    for path in ROOT.rglob("*.ipynb"):
        notebook = nbformat.read(path, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                assert cell.execution_count is None
                assert not cell.outputs


def test_no_sensitive_identifiers():
    forbidden = [
        re.compile(r"ftjob-[a-z0-9-]+", re.IGNORECASE),
        re.compile(r"/subscriptions/[0-9a-f-]{36}", re.IGNORECASE),
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}", re.IGNORECASE),
        re.compile(r"cont-learning-faos-resource", re.IGNORECASE),
        re.compile(r"zava-rft-tools\.azurewebsites\.net", re.IGNORECASE),
        re.compile(r"(?:opt|cand)_[0-9a-f]{32}", re.IGNORECASE),
        re.compile(r"C:\\Users\\", re.IGNORECASE),
        re.compile(
            r"AZURE_SUBSCRIPTION_ID.{0,100}[0-9a-f]{8}-"
            r"[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            re.IGNORECASE,
        ),
    ]
    extensions = {".py", ".md", ".json", ".jsonl", ".ipynb", ".txt", ".csv", ".bicep"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if path == Path(__file__):
            continue
        assert re.search(r"(?:opt|cand)_[0-9a-f]{32}", path.name) is None
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden:
            assert pattern.search(text) is None, f"{pattern.pattern} found in {path}"


def test_zava_notebook_has_standalone_artifacts():
    demo = ROOT / "RFT/zava-agentic-rft"
    required = [
        demo / "agent/README.md",
        demo / "agent/eval.yaml",
        demo / "agent/eval.jsonl",
        demo / "agent/optimize_hosted_agent.py",
        demo / "agent/.agent_configs/baseline/metadata.yaml",
        demo / "agent/.agent_configs/baseline/instructions.md",
        demo / "agent/.agent_configs/baseline/tools.json",
        demo / "results/optimize-2026-05-05/o4-mini/candidate_v1_systemprompt.txt",
        demo / "results/optimize-2026-05-05/o4-mini/opt_historical.json",
        demo / "results/baseline-2026-05-05/o4-mini/opt_historical.json",
        demo
        / "results/baseline-2026-05-05/o4-mini-cand-v1/"
        "opt_historical.json",
        demo
        / "results/baseline-2026-05-05/o4-mini-rft-zavav1pt70-cand-v1/"
        "summary.json",
    ]
    assert all(path.exists() for path in required)

    notebook = (demo / "notebooks/e2e_demo.ipynb").read_text(encoding="utf-8")
    assert 'ROOT / \\"faos-agent\\"' not in notebook
    assert 'ROOT / \\"agent\\" / \\"spec.yaml\\"' not in notebook
    assert "cognitiveservices.azure.com/api/projects" not in notebook
    assert "RUN_FAOS" not in notebook
    assert 'LIVE_EVALS = env_flag(\\"LIVE_EVALS\\")' in notebook
    assert 'SUBMIT_RFT = env_flag(\\"SUBMIT_RFT\\")' in notebook

    parsed = json.loads(notebook)
    for cell in parsed["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))


def test_zava_optimizer_assets_use_current_schema():
    agent = ROOT / "RFT/zava-agentic-rft/agent"
    rows = [
        json.loads(line)
        for line in (agent / "eval.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 26
    for row in rows:
        assert isinstance(row["query"], str) and row["query"]
        assert isinstance(row["criteria"], list) and row["criteria"]
        assert "prompt" not in row
        assert "groundTruth" not in row

    tools = json.loads(
        (agent / ".agent_configs/baseline/tools.json").read_text(encoding="utf-8")
    )
    names = {item["function"]["name"] for item in tools}
    assert names == {
        "get_order_details",
        "get_fulfillment_status",
        "check_resolution_policy",
        "check_inventory",
        "calculate_resolution",
        "submit_resolution",
    }


def test_zava_grader_smoke():
    grader = _load_module(ROOT / "RFT/zava-agentic-rft/rft/grader.py")
    item = {
        "expected_resolution": (
            "Refund $89.99 for defective keyboard. Gold tier, within 45-day "
            "window. Defective items have $0 restocking fee."
        )
    }
    perfect = {
        "output_text": (
            "Refund approved for $89.99; defective item, no restocking fee. "
            "Gold tier, within the 45-day window."
        ),
        "output_tools": [{"function": {"name": "get_order", "arguments": "{}"}}],
    }
    bad = {"output_text": "No.", "output_tools": []}
    assert grader.grade(perfect, item) > grader.grade(bad, item)
    assert 0 <= grader.grade(perfect, item) <= 1


def test_zava_tool_service_smoke():
    service = _load_module(
        ROOT / "RFT/zava-agentic-rft/tool-service/function_app.py"
    )
    order = json.loads(service.get_order("ORD-001"))
    missing = json.loads(service.get_order("ORD-999"))
    assert order["order_id"] == "ORD-001"
    assert order["customer"]["email"].endswith("@example.com")
    assert "error" in missing


def test_countdown_grader_smoke():
    grader = _load_module(ROOT / "RFT/countdown/endpoint-grader/grader.py")
    item = {"nums": [1, 2, 3, 4], "target": 10}
    perfect = {"output_json": {"expression": "1+2+3+4", "result": 10}}
    invalid = {"output_json": {"expression": "1+2", "result": 3}}
    assert grader.grade(perfect, item) == 5
    assert grader.grade(invalid, item) == 0
    for expression in ["1+2+3//4", "1+2+3%4", "1+2+3**4"]:
        forbidden = {"output_json": {"expression": expression, "result": 7}}
        assert grader.grade(forbidden, item) == 0


def test_trace_export_converts_genai_parts():
    exporter = _load_module(
        ROOT / "SFT/trace-distillation/scripts/export_app_insights_traces.py"
    )
    input_messages = [
        {"role": "system", "parts": [{"type": "text", "content": "instructions"}]},
        {"role": "user", "parts": [{"type": "text", "content": "Find order 1"}]},
        {
            "role": "assistant",
            "parts": [
                {
                    "type": "tool_call",
                    "id": "call-1",
                    "name": "get_order",
                    "arguments": {"order_id": "1"},
                }
            ],
        },
        {
            "role": "tool",
            "parts": [
                {
                    "type": "tool_call_response",
                    "id": "call-1",
                    "response": "{\"status\":\"delivered\"}",
                }
            ],
        },
    ]
    output_messages = [
        {
            "role": "assistant",
            "parts": [{"type": "text", "content": "Order 1 was delivered."}],
        }
    ]

    messages = exporter.conversation_from_span(
        json.dumps(input_messages), json.dumps(output_messages)
    )

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert messages[1]["tool_calls"][0]["function"]["arguments"] == '{"order_id":"1"}'
    assert messages[2]["tool_call_id"] == "call-1"


def test_countdown_data_is_locally_generated():
    demo = ROOT / "RFT/countdown"
    for path in [demo / "demo.ipynb", demo / "demo_with_python_grader.ipynb"]:
        notebook = path.read_text(encoding="utf-8")
        assert "predibase/countdown" not in notebook
        assert re.search(r'eval(?:run)?_[0-9a-f]{20,}', notebook) is None
        assert "ast.FloorDiv" not in notebook
        assert "ast.Mod" not in notebook
        assert "ast.Pow" not in notebook
        assert "wait_for_eval_runs" in notebook

    def can_reach(numbers, target):
        @lru_cache(maxsize=None)
        def solve(state):
            if len(state) == 1:
                return state[0] == target
            for left_index in range(len(state)):
                for right_index in range(left_index + 1, len(state)):
                    left, right = state[left_index], state[right_index]
                    rest = [
                        value
                        for index, value in enumerate(state)
                        if index not in {left_index, right_index}
                    ]
                    candidates = {
                        left + right,
                        left - right,
                        right - left,
                        left * right,
                    }
                    if right:
                        candidates.add(left / right)
                    if left:
                        candidates.add(right / left)
                    for candidate in candidates:
                        next_state = tuple(sorted([*rest, candidate]))
                        if solve(next_state):
                            return True
            return False

        return solve(tuple(sorted(Fraction(number) for number in numbers)))

    splits = []
    for name in ["countdown_train_raw.jsonl", "countdown_valid_raw.jsonl"]:
        rows = [
            json.loads(line)
            for line in (demo / "data" / name).read_text(encoding="utf-8").splitlines()
        ]
        keys = set()
        for row in rows:
            numbers = json.loads(row["nums"])
            target = Fraction(int(row["target"]))
            assert can_reach(numbers, target), row
            keys.add((row["target"], tuple(sorted(numbers))))
        assert len(keys) == len(rows)
        splits.append(keys)
    assert splits[0].isdisjoint(splits[1])


def test_notebook_execution_repairs_are_present():
    countdown_upload = (
        ROOT / "RFT/countdown/scripts/io_utils.py"
    ).read_text(encoding="utf-8")
    assert 'processed.status == "processed"' in countdown_upload
    assert "client.files.retrieve(uploaded.id)" in countdown_upload
    assert "client.files.list()" not in countdown_upload

    image = (
        ROOT
        / "SFT/image-breed-classification/images_classification_vlm.ipynb"
    ).read_text(encoding="utf-8")
    assert "maurice-fp/stanford-dogs" in image
    assert 'comparison_df[\\\"id\\\"].astype(str)' in image
    assert "uploaded_file.status not in" in image
    assert "REUSE_IMAGE_JOB_ID" in image
    assert "DefaultAzureCredential" in image
    assert 'breed.lower() in text.lower()' in image
    assert 'selected_breeds = sorted(dataset_df[\\\"breed\\\"]' in image
    assert "dog-breed-demo" in image

    latency = (
        ROOT / "SFT/image-breed-classification/latency_base_ft_models.ipynb"
    ).read_text(encoding="utf-8")
    assert "DOG_IMAGES_PER_BREED" in latency
    assert 'FT_DEPLOYMENT = os.getenv(\\"AZURE_OPENAI_FT_DEPLOYMENT_NAME\\")' in latency

    video = (
        ROOT
        / "SFT/video-action-recognition/"
        "fine-tune-aoai-gpt4-1-action-detection.ipynb"
    ).read_text(encoding="utf-8")
    assert "sayakpaul/ucf101-subset" in video
    assert 'filter=\\\"data\\\"' in video
    assert 'f\\\"Bearer {token}\\\"' in video
    assert "uploaded.status == \\\"processed\\\"" in video

    sarcasm = (
        ROOT / "SFT/distilling-sarcasm/sarcasm.ipynb"
    ).read_text(encoding="utf-8")
    assert "SARCASM_BASE_MODELS" in sarcasm
    assert "SARCASM_STUDENT_MODEL" in sarcasm
    assert "status={status}" not in sarcasm
    assert "Fine-tuned deployment failed" in sarcasm

    trace = (
        ROOT / "SFT/trace-distillation/notebook.ipynb"
    ).read_text(encoding="utf-8")
    assert "SupervisedFineTuningDataGenerationJobInputs" in trace
    assert "begin_create_generation_job" in trace
    assert "TRACE_INPUT_FILE" in trace
    assert "REUSE_TRACE_JOB_ID" in trace
    assert "DefaultAzureCredential" in trace
    assert "FILE_PROCESSING_TIMEOUT" in trace
    assert "Deployment failed" in trace
    assert "was not inferenceable" in trace

    for countdown_path in [
        ROOT / "RFT/countdown/demo.ipynb",
        ROOT / "RFT/countdown/demo_with_python_grader.ipynb",
    ]:
        countdown = countdown_path.read_text(encoding="utf-8")
        assert "REUSE_COUNTDOWN_JOB_ID" in countdown
        assert "DefaultAzureCredential" in countdown

    math = (
        ROOT / "RFT/math-reasoning/rft_math_reasoning.ipynb"
    ).read_text(encoding="utf-8")
    assert "get_bearer_token_provider" in math
    assert "REUSE_RFT_JOB_ID" in math

    nl_to_python = (
        ROOT
        / "SFT/nl-to-python-distillation/Text_to_Python_Fine_Tuning.ipynb"
    ).read_text(encoding="utf-8")
    assert 'grader_name.startswith(\\"correctness-\\")' in nl_to_python
    assert 'grader_name.startswith(\\"conciseness-\\")' in nl_to_python
    assert "Evaluation completed without a full score set" in nl_to_python


def test_all_notebook_python_cells_parse():
    for path in ROOT.rglob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "\n".join(
                line
                for line in "".join(cell["source"]).splitlines()
                if not line.lstrip().startswith(("%", "!", "pip install "))
            )
            try:
                ast.parse(source)
            except SyntaxError as error:
                raise AssertionError(
                    f"Invalid Python in {path.relative_to(ROOT)} cell {index}"
                ) from error


def test_local_markdown_links():
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean_target = target.split("#", 1)[0]
            if not clean_target:
                continue
            assert (path.parent / clean_target).resolve().exists(), (
                f"Broken link {target!r} in {path.relative_to(ROOT)}"
            )
