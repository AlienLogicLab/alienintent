"""Tests for the Gap Trap Promotion Backlog contract checker.

Phase 3 promotes recurring known failure classes out of REVIEW cognition and into mechanical
enforcement. The risk this checker guards is over-promotion: a promotion that cannot be shown
to fail is a prose reminder wearing a gate's clothing, and it would consume the review budget
it was meant to free.

Lesson carried from Phase 2, where three of my own checks passed on synthetic data and failed
to discriminate on real data: absence is written as "none — <why>", not as the bare word, and
every check here must be exercised by a negative control.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_gap_trap_backlog import CHECKS, check_backlog  # noqa: E402

KNOWN = {"LRN-001", "LRN-002", "LRN-010"}
LAYERS = {"architecture_fitness", "python_unit_integration", "evidence_consistency"}


def _candidate(**over):
    c = {
        "learning_id": "LRN-001",
        "failure_class": "EVIDENCE_PROOF_DEFECT",
        "cheapest_enforcement_layer": "architecture_fitness",
        "deterministic_rule": "every assertion must fail against its violation fixture",
        "violation_fixture": "tests/fixtures/fitness/non_discriminating_assertion.py",
        "proven_red_method": "revert the assertion and observe the suite fail",
        "advisory_or_blocking": "BLOCKING",
        "canonical_owner": "SF-REQ-050",
        "expected_cognitive_work_removed": "reviewers re-reading assertions to judge whether they can fail",
        "effectiveness_metric": "count of non-discriminating assertions reaching REVIEW, expected 0",
    }
    c.update(over)
    return c


def _backlog(*cands):
    return {"candidates": list(cands), "summary": {"promotions": len(cands)}}


def _check(b):
    return check_backlog(b, known_ids=KNOWN, known_layers=LAYERS)


def test_a_clean_backlog_passes():
    ok, failures = _check(_backlog(_candidate()))
    assert ok, failures


def test_a_missing_required_field_is_rejected():
    c = _candidate()
    del c["proven_red_method"]
    ok, failures = _check(_backlog(c))
    assert not ok
    assert any("required_fields" in f for f in failures)


def test_a_candidate_not_traceable_to_a_ledger_lesson_is_rejected():
    """Phase 3 promotes Wave 1 lessons; it does not invent new ones."""
    ok, failures = _check(_backlog(_candidate(learning_id="LRN-999")))
    assert not ok
    assert any("traceable_to_ledger" in f for f in failures)


def test_an_unknown_enforcement_layer_is_rejected_unless_declared_new():
    ok, failures = _check(_backlog(_candidate(cheapest_enforcement_layer="magic_gate")))
    assert not ok
    assert any("enforcement_layer_known" in f for f in failures)


def test_a_new_layer_is_allowed_when_explicitly_declared_and_justified():
    ok, failures = _check(_backlog(_candidate(
        cheapest_enforcement_layer="NEW:state_machine_invariant",
        new_layer_justification="no existing layer observes lifecycle transitions")))
    assert ok, failures


def test_a_new_layer_without_justification_is_rejected():
    ok, failures = _check(_backlog(_candidate(
        cheapest_enforcement_layer="NEW:state_machine_invariant")))
    assert not ok


def test_blocking_without_a_proven_red_method_is_rejected():
    """A gate that was never shown to fail must not block the factory."""
    ok, failures = _check(_backlog(_candidate(
        advisory_or_blocking="BLOCKING", proven_red_method="none — not yet designed")))
    assert not ok
    assert any("blocking_needs_proven_red" in f for f in failures)


def test_the_same_candidate_is_allowed_as_advisory():
    ok, failures = _check(_backlog(_candidate(
        advisory_or_blocking="ADVISORY", proven_red_method="none — not yet designed",
        violation_fixture="none — not yet designed")))
    assert ok, failures


def test_blocking_without_a_violation_fixture_is_rejected():
    ok, failures = _check(_backlog(_candidate(violation_fixture="none")))
    assert not ok


def test_a_promotion_that_removes_no_cognitive_work_is_rejected():
    """If no reviewer work disappears, the promotion adds a gate and buys nothing."""
    ok, failures = _check(_backlog(_candidate(
        expected_cognitive_work_removed="none — unchanged")))
    assert not ok
    assert any("removes_cognitive_work" in f for f in failures)


def test_an_unknown_advisory_or_blocking_value_is_rejected():
    ok, failures = _check(_backlog(_candidate(advisory_or_blocking="maybe")))
    assert not ok


def test_a_summary_count_that_disagrees_with_the_candidates_is_rejected():
    b = _backlog(_candidate())
    b["summary"]["promotions"] = 7
    ok, failures = _check(b)
    assert not ok
    assert any("summary_matches_candidates" in f for f in failures)


# --- SWF-24: no check may be incapable of failing -------------------------------------


def _drop_field(b):
    del b["candidates"][0]["proven_red_method"]
    return b


def _unknown_lesson(b):
    b["candidates"][0]["learning_id"] = "LRN-999"
    return b


def _unknown_layer(b):
    b["candidates"][0]["cheapest_enforcement_layer"] = "magic_gate"
    return b


def _blocking_unproven(b):
    b["candidates"][0]["proven_red_method"] = "none — not yet designed"
    return b


def _no_work_removed(b):
    b["candidates"][0]["expected_cognitive_work_removed"] = "none"
    return b


def _bad_enum(b):
    b["candidates"][0]["advisory_or_blocking"] = "maybe"
    return b


def _bad_count(b):
    b["summary"]["promotions"] = 7
    return b


NEGATIVE_CONTROLS = {
    "required_fields": _drop_field,
    "traceable_to_ledger": _unknown_lesson,
    "enforcement_layer_known": _unknown_layer,
    "blocking_needs_proven_red": _blocking_unproven,
    "removes_cognitive_work": _no_work_removed,
    "valid_enum_values": _bad_enum,
    "summary_matches_candidates": _bad_count,
}


def test_every_check_has_a_negative_control():
    base = _backlog(_candidate())
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        ok, failures = _check(mutate(copy.deepcopy(base)))
        if ok or not any(name in f for f in failures):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


def test_absence_written_as_none_with_an_explanation_is_still_absence():
    """The Phase 2 defect, carried forward as a guard: "none — <why>" is not evidence."""
    ok, failures = _check(_backlog(_candidate(
        expected_cognitive_work_removed="none — nothing changes for reviewers")))
    assert not ok
