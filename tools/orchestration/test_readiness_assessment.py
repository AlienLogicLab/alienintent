"""Tests for the Agent Ready CLI adapter behind the `ReadinessAssessment` port shape.

Founder (2026-09-22): "Invoke Agent Ready through its supported CLI or MCP behind the canonical
ReadinessAssessment port. Producer identity/version/schema provenance must be recorded where
currently available. If provenance support is incomplete, preserve the limitation explicitly; do
not fake it."

This adapter is programme tooling, not the SF-REQ-015 product port: it exists so the post-Wave-1
programme never again produces a contract-shaped surrogate (the Wave 1 authoritative-capability
substitution). It consumes the product only through `agent-ready assess ... --json`, preserves the
raw result verbatim, and records what produced it. Execution failure is never a disposition.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from readiness_assessment import (AGENT_READY_DISPOSITIONS, AgentReadyCliAdapter,  # noqa: E402
                                  FILTERED_ENV)

NATIVE = {"disposition": "HOLD", "governing_intent": "x", "summary": "x",
          "owner_clarifications": [], "implementation_unknowns": [],
          "independent_decision_centers": [], "semantic_split_recommendation": [],
          "verification_assessment": "x", "expected_rework_locality": "HIGH",
          "material_risks": ["m"], "next_action": "x", "rationale": "x",
          "provider_evidence": {"provider": "codex", "version": "codex-cli 0.155.1",
                                "compatibility": "COMPATIBLE_UNVERIFIED",
                                "capability_probe": "PASSED"}}

PIP_SHOW = "Name: agent-ready\nVersion: 0.1.0rc1\nEditable project location: /x/agent-ready\n"


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _runner(cap, assess=None, pip=None, git=None):
    """Fake subprocess boundary: routes by argv shape, captures the assess call."""
    assess = assess or _Proc(0, json.dumps(NATIVE))
    pip = pip or _Proc(0, PIP_SHOW)
    git = git or _Proc(0, "abc1234\n")

    def run(argv, **kw):
        if "assess" in argv:
            cap["argv"] = argv
            cap["env"] = kw.get("env")
            cap["text"] = Path(argv[argv.index("assess") + 1]).read_text()
            return assess
        if "pip" in argv:
            return pip
        if argv[0] == "git":
            return git
        raise AssertionError(f"unexpected call {argv}")
    return run


def _adapter(cap, **kw):
    return AgentReadyCliAdapter("/venv/bin/agent-ready", runner=_runner(cap, **kw))


def test_the_product_is_invoked_through_its_public_cli_in_json_mode(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "leak")
    cap = {}
    _adapter(cap).assess("the work unit text", provider="codex", work_unit_id="WO-1")
    argv = cap["argv"]
    assert argv[0] == "/venv/bin/agent-ready"
    assert argv[1] == "assess"
    assert argv[argv.index("--provider") + 1] == "codex"
    assert "--json" in argv
    assert cap["text"] == "the work unit text"
    assert all(k not in cap["env"] for k in FILTERED_ENV)


def test_a_successful_result_is_preserved_verbatim_with_producer_provenance():
    cap = {}
    rec = _adapter(cap).assess("t", provider="codex", work_unit_id="WO-1")
    assert rec["outcome"] == "ASSESSED"
    assert rec["disposition"] == "HOLD"
    assert rec["assessment"] == NATIVE
    p = rec["provenance"]
    assert p["producer"] == "agent-ready-cli"
    assert p["native_agent_ready"] is True
    assert p["input_sha256"] == hashlib.sha256(b"t").hexdigest()
    assert p["provider"] == "codex"
    assert p["provider_evidence"] == NATIVE["provider_evidence"]
    assert p["invocation"] == cap["argv"]
    assert p["exit_code"] == 0


def test_version_provenance_comes_from_the_installed_package_not_the_model():
    rec = _adapter({}).assess("t", provider="codex", work_unit_id="WO-1")
    p = rec["provenance"]
    assert p["agent_ready_version"] == "0.1.0rc1"
    assert p["agent_ready_checkout_commit"] == "abc1234"
    # Agent Ready v0.1 exposes no product/schema version on its results (agent-ready#1).
    assert "no schema version identifier" in p["contract_version"]
    assert "not exposed" in p["model"]


def test_unavailable_version_provenance_is_unknown_never_fabricated():
    rec = _adapter({}, pip=_Proc(1, "", "no pip"), git=_Proc(128, "", "not a repo")).assess(
        "t", provider="codex", work_unit_id="WO-1")
    assert rec["provenance"]["agent_ready_version"] == "UNKNOWN"
    assert rec["provenance"]["agent_ready_checkout_commit"] == "UNKNOWN"


def test_a_nonzero_exit_is_an_execution_failure_not_a_disposition():
    rec = _adapter({}, assess=_Proc(1, "", "Assessment failed; provider error")).assess(
        "t", provider="codex", work_unit_id="WO-1")
    assert rec["outcome"] == "EXECUTION_FAILURE"
    assert "disposition" not in rec
    assert "provider error" in rec["failure"]["stderr"]
    assert rec["provenance"]["exit_code"] == 1


@pytest.mark.parametrize("bad", [
    {**NATIVE, "disposition": "BLOCKED"},                       # bootstrap-assessor enum
    {k: v for k, v in NATIVE.items() if k != "rationale"},      # missing contract field
    {**NATIVE, "invocation": "codex exec"},                     # runner-asserted field
    "not json at all",
])
def test_output_without_agent_readys_shape_is_an_execution_failure(bad):
    """A compatible-looking result is not enough; an incompatible one is disproof."""
    out = bad if isinstance(bad, str) else json.dumps(bad)
    rec = _adapter({}, assess=_Proc(0, out)).assess("t", provider="codex", work_unit_id="WO-1")
    assert rec["outcome"] == "EXECUTION_FAILURE"
    assert "disposition" not in rec


def test_only_agent_ready_dispositions_are_recognised():
    assert AGENT_READY_DISPOSITIONS == ("READY", "CLARIFY", "SPLIT", "HOLD")


def test_an_unsupported_provider_is_refused_before_any_invocation():
    cap = {}
    with pytest.raises(ValueError):
        _adapter(cap).assess("t", provider="gemini", work_unit_id="WO-1")
    assert "argv" not in cap


def test_the_record_is_written_beside_the_wave2_evidence(tmp_path):
    rec = _adapter({}).assess("t", provider="codex", work_unit_id="WO-1")
    out = AgentReadyCliAdapter.write_record(rec, root=tmp_path)
    assert out.parent == tmp_path / "docs/evidence/wave2-readiness-assessments"
    assert out.name.startswith("WO-1.") and out.name.endswith(".assessment.json")
    assert json.loads(out.read_text())["assessment"] == NATIVE
