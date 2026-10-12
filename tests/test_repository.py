import importlib.util
import json
import re
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DEMOS = {
    "SFT": {
        "distilling-sarcasm",
        "bug-detection",
        "nl-to-python-distillation",
        "image-breed-classification",
        "chart-analysis",
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
        demo / "agent/spec.yaml",
        demo / "results/optimize-2026-05-05/o4-mini/candidate_v1_systemprompt.txt",
        demo
        /         "results/optimize-2026-05-05/o4-mini/opt_historical.json",
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
    assert '"LIVE_EVALS = False' in notebook
    assert '"RUN_FAOS   = False' in notebook
    assert '"SUBMIT_RFT = False' in notebook


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
