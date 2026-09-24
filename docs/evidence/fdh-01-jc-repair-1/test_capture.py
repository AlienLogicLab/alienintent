"""Offline parser check against retained producer CLI output; never invokes a provider."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/orchestration"))
from factory_director_host import codex_usage


def test_captured_codex_output_records_explicit_model_limitation():
    text = Path(__file__).with_name("codex-capture.jsonl").read_text()
    events = [json.loads(line) for line in text.splitlines()]
    assert [event["type"] for event in events] == [
        "thread.started", "turn.started", "item.completed", "turn.completed"
    ]
    assert "model" not in text.lower()
    observed = codex_usage(text)
    assert observed["measured"] is True
    assert observed["observed_models"] is None
    assert observed["model_evidence"] == "NOT_EXPOSED_BY_PROVIDER"
    assert observed["input_tokens"] == events[-1]["usage"]["input_tokens"]
    assert observed["output_tokens"] == events[-1]["usage"]["output_tokens"]
    assert observed["cost_usd"] is None
