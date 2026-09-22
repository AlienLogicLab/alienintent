"""Tests for the Wave 2 Agent-Ready assessment set checker (Phase 13).

The rules the plan states, reduced to decidable ones:

- every BIU assessed, disposition from the canonical four
- no disposition coerced to READY -- a BIU with an open authority gap cannot be READY
- every non-READY outcome follows the Phase 4 handling matrix: implementation not allowed, a
  next action, and a reassessment trigger
- assessment execution failure is not a disposition (LRN-008: a verifier exited success with no
  verdict and became DURABLE_RESULT_MISSING rather than ACCEPT)
- explicit provider/model provenance on every assessment
- SPLIT_RECOMMENDED must reference the Phase 5 split/replan process
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_agent_ready_set import CHECKS, check_set  # noqa: E402


def _a(**over):
    a = {"biu_id": "WO-220101", "disposition": "READY", "open_authority_gaps": [],
         "provider": "codex", "model": "gpt-6-astra", "baseline_sha": "01af974",
         "assessed_at": "2026-09-21T22:00:00Z", "terminal_result_valid": True,
         "implementation_allowed": True, "next_action": "release under SF-REQ-002 admission",
         "reassessment_trigger": "not applicable while READY"}
    a.update(over)
    return a


def _doc(assessments=None, required=("WO-220101",), failures=None):
    return {"assessments": assessments if assessments is not None else [_a()],
            "required_bius": list(required),
            "execution_failures": failures if failures is not None else []}


def test_a_clean_set_passes():
    ok, f = check_set(_doc())
    assert ok, f


def test_an_unassessed_biu_is_rejected():
    ok, f = check_set(_doc(required=("WO-220101", "WO-220102")))
    assert not ok
    assert any("every_biu_assessed" in x for x in f)


def test_an_invalid_disposition_is_rejected():
    ok, f = check_set(_doc([_a(disposition="PROBABLY_FINE")]))
    assert not ok
    assert any("canonical_disposition" in x for x in f)


def test_a_biu_with_an_open_authority_gap_cannot_be_ready():
    """No disposition coerced to READY."""
    ok, f = check_set(_doc([_a(open_authority_gaps=["R1-GAP-MONITOR-HOST"])]))
    assert not ok
    assert any("no_coercion_to_ready" in x for x in f)


def test_the_same_biu_blocked_passes():
    ok, f = check_set(_doc([_a(disposition="HOLD",
                               open_authority_gaps=["R1-GAP-MONITOR-HOST"],
                               implementation_allowed=False,
                               next_action="await Founder disposition",
                               reassessment_trigger="gap resolved")]))
    assert ok, f


def test_a_non_ready_disposition_permitting_implementation_is_rejected():
    ok, f = check_set(_doc([_a(disposition="HOLD", implementation_allowed=True,
                               next_action="x", reassessment_trigger="y")]))
    assert not ok
    assert any("matrix_conformance" in x for x in f)


def test_a_non_ready_disposition_without_a_reassessment_trigger_is_rejected():
    ok, f = check_set(_doc([_a(disposition="CLARIFY", implementation_allowed=False,
                               next_action="ask", reassessment_trigger="none")]))
    assert not ok
    assert any("matrix_conformance" in x for x in f)


def test_an_execution_failure_recorded_as_a_disposition_is_rejected():
    """LRN-008: a provider failure is not a readiness verdict."""
    ok, f = check_set(_doc([_a(disposition="PROVIDER_FAILURE")]))
    assert not ok
    assert any("canonical_disposition" in x for x in f)


def test_an_execution_failure_recorded_separately_passes():
    ok, f = check_set(_doc(failures=[{"biu_id": "WO-220101", "mode": "timeout",
                                      "is_disposition": False, "next_action": "reassess"}]))
    assert ok, f


def test_an_assessment_without_provider_provenance_is_rejected():
    ok, f = check_set(_doc([_a(provider="", model="")]))
    assert not ok
    assert any("provider_provenance" in x for x in f)


def test_an_unvalidated_terminal_result_is_rejected():
    ok, f = check_set(_doc([_a(terminal_result_valid=False)]))
    assert not ok
    assert any("terminal_result_validated" in x for x in f)


def test_legacy_split_recommended_under_declared_vocabulary_must_reference_the_split_process():
    d = _doc([_a(disposition="SPLIT_RECOMMENDED", implementation_allowed=False,
                 next_action="split", reassessment_trigger="after split")])
    d["assessor_vocabulary"] = "alienintent-bootstrap-assessor"
    ok, f = check_set(d)
    assert not ok
    assert any("split_invokes_process" in x for x in f)


def test_split_referencing_the_process_passes():
    ok, f = check_set(_doc([_a(disposition="SPLIT", implementation_allowed=False,
                               next_action="split", reassessment_trigger="after split",
                               split_process_ref="docs/evidence/wave1-biu-split-replan-design.json")]))
    assert ok, f


NEGATIVE_CONTROLS = {
    "every_biu_assessed": lambda d: d["required_bius"].append("WO-999999"),
    "canonical_disposition": lambda d: d["assessments"][0].__setitem__("disposition", "NOPE"),
    "no_coercion_to_ready": lambda d: d["assessments"][0].__setitem__("open_authority_gaps", ["G"]),
    "matrix_conformance": lambda d: d["assessments"][0].update(
        disposition="HOLD", implementation_allowed=True),
    "provider_provenance": lambda d: d["assessments"][0].__setitem__("provider", ""),
    "terminal_result_validated": lambda d: d["assessments"][0].__setitem__("terminal_result_valid", False),
    "split_invokes_process": lambda d: d["assessments"][0].update(
        disposition="SPLIT", implementation_allowed=False),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_doc())
        mutate(d)
        ok, f = check_set(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


# --- Founder decision 2026-09-22: Agent Ready dispositions are exactly READY/CLARIFY/SPLIT/HOLD


def test_the_canonical_disposition_set_is_agent_readys_four():
    from check_agent_ready_set import AGENT_READY_DISPOSITIONS
    assert AGENT_READY_DISPOSITIONS == ("READY", "CLARIFY", "SPLIT", "HOLD")


def test_an_undeclared_artifact_is_held_to_agent_ready_vocabulary():
    """BLOCKED is not an Agent Ready disposition. An artifact that does not declare the
    legacy bootstrap-assessor vocabulary is held to the canonical four."""
    ok, f = check_set(_doc([_a(disposition="BLOCKED", implementation_allowed=False,
                               next_action="await prerequisite", reassessment_trigger="x")]))
    assert not ok
    assert any("canonical_disposition" in x for x in f)


def test_hold_is_accepted_as_the_canonical_prerequisite_disposition():
    ok, f = check_set(_doc([_a(disposition="HOLD", implementation_allowed=False,
                               next_action="obtain prerequisite", reassessment_trigger="x")]))
    assert ok, f


def test_a_historical_artifact_may_declare_the_legacy_bootstrap_assessor_vocabulary():
    """Historical records remain historical: the Wave 2 programme assessments were produced by
    the AlienIntent bootstrap assessor and are validated under the vocabulary they declare."""
    d = _doc([_a(disposition="BLOCKED", implementation_allowed=False,
                 next_action="await prerequisite", reassessment_trigger="x")])
    d["assessor_vocabulary"] = "alienintent-bootstrap-assessor"
    ok, f = check_set(d)
    assert ok, f


def test_an_agent_ready_declared_artifact_rejects_legacy_names():
    d = _doc([_a(disposition="NEEDS_CLARIFICATION", implementation_allowed=False,
                 next_action="ask", reassessment_trigger="x")])
    d["assessor_vocabulary"] = "agent-ready"
    ok, f = check_set(d)
    assert not ok


def test_split_under_agent_ready_vocabulary_must_invoke_the_split_process():
    ok, f = check_set(_doc([_a(disposition="SPLIT", implementation_allowed=False,
                               next_action="split", reassessment_trigger="after split")]))
    assert not ok
    assert any("split_invokes_process" in x for x in f)
