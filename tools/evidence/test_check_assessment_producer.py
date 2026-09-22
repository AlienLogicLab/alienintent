"""Tests for the readiness-assessment producer-identity checker.

Wave 1's PY-01..PY-10 readiness assessments were not produced by the Agent Ready product. A
coordinator ran raw Codex (later Claude) prompts shaped to Agent Ready's contract, and the
resulting artifacts carried a `provider_evidence` block that *copied Agent Ready's host-measured
vocabulary* (`compatibility`, `capability_probe`) as asserted text. Nothing checked who produced
them; the release gate read only `disposition`.

The invariant this enforces, from the Founder (2026-09-22):

    A compatible output shape is not evidence that the authoritative capability produced the
    result.

So every retained assessment must be covered by a provenance manifest that declares its
producer, and the declaration must be consistent with what a native Agent Ready result actually
looks like: an MCP envelope, or a CLI object with exactly the twelve contract fields plus, at
most, Agent Ready's own four-key Codex-only `provider_evidence`, and a disposition from
`READY / CLARIFY / SPLIT / HOLD`. Anything carrying an `invocation`, `adapter`, `model`,
`provider_failover` or `permission_denials`, or a `claude` provider, or a bootstrap-assessor
disposition, was not produced by Agent Ready — whatever it says about itself.

Proven red against the real shapes: a real surrogate (PY-02) and a real native (PG-01) artifact.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_assessment_producer import (CHECKS, check_manifest,  # noqa: E402
                                       looks_native_agent_ready)

REPO = Path(__file__).resolve().parents[2]
REAL_SURROGATE = json.loads((REPO / "docs/work-units/python/PY-02.assessment.json").read_text())
REAL_NATIVE = json.loads(
    (REPO / "docs/work-units/pre-python-gate/assessments/PG-01.assessment.json").read_text())

_CONTRACT = {"disposition": "READY", "governing_intent": "x", "summary": "x",
             "owner_clarifications": [], "implementation_unknowns": [],
             "independent_decision_centers": [], "semantic_split_recommendation": [],
             "verification_assessment": "x", "expected_rework_locality": "HIGH",
             "material_risks": [], "next_action": "x", "rationale": "x"}


# --- shape recognition, proven against real artifacts -----------------------------------


def test_the_real_pre_python_gate_artifact_looks_native():
    assert looks_native_agent_ready(REAL_NATIVE) is True


def test_the_real_wave1_surrogate_artifact_does_not_look_native():
    """PY-02 asserts compatibility=COMPATIBLE_UNVERIFIED and capability_probe=PASSED, the
    words Agent Ready generates host-side. It also carries `invocation`. Shape is not proof."""
    assert looks_native_agent_ready(REAL_SURROGATE) is False


def test_a_bare_cli_object_with_exactly_the_contract_fields_looks_native():
    assert looks_native_agent_ready(dict(_CONTRACT)) is True


def test_agent_readys_own_codex_provider_evidence_is_accepted():
    a = dict(_CONTRACT)
    a["provider_evidence"] = {"provider": "codex", "version": "codex-cli 0.153.4",
                              "compatibility": "SUPPORTED", "capability_probe": "REVIEWED_VERSION"}
    assert looks_native_agent_ready(a) is True


def test_a_claude_provider_evidence_is_not_native():
    a = dict(_CONTRACT)
    a["provider_evidence"] = {"provider": "claude", "version": "x", "compatibility": "SUPPORTED",
                              "capability_probe": "PASSED"}
    assert looks_native_agent_ready(a) is False


def test_a_bootstrap_assessor_disposition_is_not_native():
    a = dict(_CONTRACT)
    a["disposition"] = "BLOCKED"
    assert looks_native_agent_ready(a) is False


# --- manifest checks ---------------------------------------------------------------------


def _manifest(entries):
    return {"entries": entries}


def _entry(**over):
    e = {"path": "docs/work-units/python/PY-02.assessment.json", "producer": "surrogate",
         "engine": "codex exec (bootstrap assessor)", "native_agent_ready": False}
    e.update(over)
    return e


def test_a_clean_manifest_passes():
    ok, f = check_manifest(_manifest([_entry(artifact=REAL_SURROGATE),
                                      _entry(path="pg", producer="agent-ready-mcp",
                                             engine="agent-ready MCP assess_work_unit",
                                             native_agent_ready=True, artifact=REAL_NATIVE)]))
    assert ok, f


def test_a_surrogate_declared_native_is_rejected():
    """The exact misrepresentation this checker exists to refuse."""
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready-cli", native_agent_ready=True,
                                             artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_a_native_declared_surrogate_is_flagged():
    """Mislabelling in the other direction hides a real Agent Ready execution."""
    ok, f = check_manifest(_manifest([_entry(path="pg", producer="surrogate",
                                             native_agent_ready=False, artifact=REAL_NATIVE)]))
    assert not ok
    assert any("declared_surrogate_must_not_look_native" in x for x in f)


def test_any_agent_ready_producer_label_is_held_to_native_shape():
    """Found live: a generator labelled two artifacts "agent-ready (…)" with native_agent_ready
    False and a non-native shape, and the checker let it through because only the exact producer
    names counted as native declarations. A label that names Agent Ready is a native claim."""
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready (CLI or MCP-unwrapped; method UNKNOWN)",
                                             native_agent_ready=False, artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_a_declared_native_partial_record_is_held_to_provenance_not_full_shape():
    """PG-00 is a receipt excerpt of a native MCP assessment: its own record_kind says the full
    response stayed in session evidence. A partial record cannot show the full contract shape,
    but it must still carry Agent Ready's own 4-key codex provider_evidence and an Agent Ready
    disposition, or the native claim fails."""
    excerpt = {"disposition": "READY", "owner_clarifications": [], "summary": "x",
               "record_kind": "Receipt excerpt",
               "provider_evidence": {"provider": "codex", "version": "codex-cli 0.154.0",
                                     "compatibility": "COMPATIBLE_UNVERIFIED",
                                     "capability_probe": "PASSED"}}
    ok, f = check_manifest(_manifest([_entry(path="pg00", producer="agent-ready-mcp",
                                             native_agent_ready=True, partial_record=True,
                                             artifact=excerpt)]))
    assert ok, f


def test_a_partial_record_claim_does_not_launder_surrogate_provenance():
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready-cli", native_agent_ready=True,
                                             partial_record=True, artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_an_entry_without_a_producer_is_rejected():
    e = _entry(artifact=REAL_SURROGATE)
    del e["producer"]
    ok, f = check_manifest(_manifest([e]))
    assert not ok
    assert any("producer_declared" in x for x in f)


def test_an_assessment_file_missing_from_the_manifest_is_rejected(tmp_path):
    """Coverage: every retained assessment must be accounted for, or an undeclared surrogate
    can sit beside declared ones."""
    ok, f = check_manifest(_manifest([]), expected_paths=["docs/work-units/python/PY-02.assessment.json"])
    assert not ok
    assert any("every_assessment_covered" in x for x in f)


NEGATIVE_CONTROLS = {
    "producer_declared": lambda m: m["entries"][0].pop("producer"),
    "declared_native_must_look_native": lambda m: m["entries"][0].update(
        producer="agent-ready-cli", native_agent_ready=True),
    "declared_surrogate_must_not_look_native": lambda m: m["entries"][1].update(
        producer="surrogate", native_agent_ready=False),
    "every_assessment_covered": lambda m: m["entries"].clear(),
}


def test_every_check_has_a_negative_control():
    base = _manifest([_entry(artifact=REAL_SURROGATE),
                      _entry(path="pg", producer="agent-ready-mcp", native_agent_ready=True,
                             artifact=REAL_NATIVE)])
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        m = copy.deepcopy(base)
        mutate(m)
        ok, f = check_manifest(m, expected_paths=["docs/work-units/python/PY-02.assessment.json"])
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
