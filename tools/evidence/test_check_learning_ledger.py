"""Tests for the Learning Ledger contract checker.

The checker exists because Phase 2's first ledger reported ownership_gaps=0 while several of
its own records said, in their own text, that no corresponding capability exists. Founder
decision POSTW1-DECIDE-002A: discovering an ownership gap was never prohibited, and authority,
enforcement strength, proven-red status and effectiveness evidence are four separate dimensions
that must not be collapsed into one "owner" column.

Every check here must be demonstrated to fail against a mutated ledger (SWF-24: a check that
cannot fail is not evidence). `test_every_check_has_a_negative_control` enforces that.
"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from check_learning_ledger import CHECKS, check_ledger  # noqa: E402


def _clean_record(**over):
    rec = {
        "learning_id": "LRN-001",
        "failure_class": "example-class",
        "originating_BIUs": ["PY-01"],
        "recurrence_count": 2,
        "first_occurrence": "2026-09-20T00:00:00Z",
        "last_occurrence": "2026-09-21T00:00:00Z",
        "evidence_refs": ["docs/evidence/wave1-closure-manifest.md"],
        "existing_owner": "SF-REQ-002",
        "owner_fit": "CANONICAL",
        "enforcement_level": "DETERMINISTIC_GATE",
        "mechanizable": "yes — assert the thing",
        "proven_red": "yes",
        "later_consumption": "consumed by PY-08",
        "effectiveness_evidence": "FACT: the gate refused two defective releases.",
        "recommended_disposition": "ALREADY_GRADUATED",
    }
    rec.update(over)
    return rec


def _ledger(*records):
    gaps = sum(1 for r in records if r.get("recommended_disposition") == "NEW_CAPABILITY_GAP")
    return {"records": list(records),
            "summary": {"lessons": len(records), "ownership_gaps": gaps}}


def test_a_clean_ledger_passes():
    ok, failures = check_ledger(_ledger(_clean_record()))
    assert ok, failures


# --- the four dimensions must be separately recorded --------------------------------


def test_a_record_without_an_explicit_owner_fit_is_rejected():
    """Authority and enforcement were collapsed into one column; that is what hid the gaps."""
    rec = _clean_record()
    del rec["owner_fit"]
    ok, failures = check_ledger(_ledger(rec))
    assert not ok
    assert any("owner_fit" in f for f in failures)


def test_an_unknown_owner_fit_value_is_rejected():
    ok, failures = check_ledger(_ledger(_clean_record(owner_fit="SORT_OF")))
    assert not ok


# --- the force-fit detector ----------------------------------------------------------


def test_an_owner_claimed_canonical_with_no_enforcement_and_no_effectiveness_is_rejected():
    """The exact shape of the force-fit: a requirement named as clean owner, while nothing
    enforces it and nothing shows it ever worked."""
    ok, failures = check_ledger(_ledger(_clean_record(
        owner_fit="CANONICAL", enforcement_level="DOCUMENTED_ONLY",
        effectiveness_evidence="none", proven_red="UNKNOWN",
        recommended_disposition="STRENGTHEN_EXISTING_OWNER")))
    assert not ok
    assert any("force-fit" in f.lower() or "adjacent" in f.lower() for f in failures)


def test_the_same_record_passes_once_the_owner_is_declared_adjacent():
    """Declaring the fit honestly is the repair — not deleting the lesson."""
    ok, failures = check_ledger(_ledger(_clean_record(
        owner_fit="ADJACENT", enforcement_level="DOCUMENTED_ONLY",
        effectiveness_evidence="none", proven_red="UNKNOWN",
        recommended_disposition="NEW_CAPABILITY_GAP")))
    assert ok, failures


# --- graduation requires evidence, not an owner --------------------------------------


def test_already_graduated_without_effectiveness_evidence_is_rejected():
    ok, failures = check_ledger(_ledger(_clean_record(
        recommended_disposition="ALREADY_GRADUATED", effectiveness_evidence="none")))
    assert not ok
    assert any("ALREADY_GRADUATED" in f for f in failures)


def test_already_graduated_requires_an_enforcing_owner():
    """LRN-018: a practice exercised twice by its own authors is not a graduated mechanism."""
    ok, failures = check_ledger(_ledger(_clean_record(
        recommended_disposition="ALREADY_GRADUATED", owner_fit="ADJACENT")))
    assert not ok


# --- the summary must not contradict the records --------------------------------------


def test_a_declared_gap_count_that_disagrees_with_the_records_is_rejected():
    led = _ledger(_clean_record(owner_fit="NONE", enforcement_level="NONE",
                                effectiveness_evidence="none", proven_red="UNKNOWN",
                                recommended_disposition="NEW_CAPABILITY_GAP"))
    led["summary"]["ownership_gaps"] = 0          # record says gap, summary says zero
    ok, failures = check_ledger(led)
    assert not ok
    assert any("ownership_gaps" in f for f in failures)


# --- SWF-24: no check may be incapable of failing --------------------------------------


def test_every_check_has_a_negative_control():
    """Each named check must reject at least one mutation of an otherwise clean ledger."""
    base = _ledger(_clean_record())
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        mutated = mutate(copy.deepcopy(base))
        ok, failures = check_ledger(mutated)
        if ok or not any(name in f for f in failures):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS), "every check needs a negative control"


def _drop_owner_fit(led):
    del led["records"][0]["owner_fit"]
    return led


def _force_fit(led):
    led["records"][0].update(owner_fit="CANONICAL", enforcement_level="DOCUMENTED_ONLY",
                             effectiveness_evidence="none", proven_red="UNKNOWN",
                             recommended_disposition="STRENGTHEN_EXISTING_OWNER")
    return led


def _graduate_without_evidence(led):
    led["records"][0].update(recommended_disposition="ALREADY_GRADUATED",
                             effectiveness_evidence="none")
    return led


def _miscount_gaps(led):
    led["records"][0].update(owner_fit="NONE", enforcement_level="NONE",
                             effectiveness_evidence="none", proven_red="UNKNOWN",
                             recommended_disposition="NEW_CAPABILITY_GAP")
    led["summary"]["ownership_gaps"] = 0
    return led


def _bad_dimension_value(led):
    led["records"][0]["proven_red"] = "sort of"
    return led


NEGATIVE_CONTROLS = {
    "owner_fit_declared": _drop_owner_fit,
    "no_force_fit": _force_fit,
    "graduation_needs_evidence": _graduate_without_evidence,
    "gap_count_matches_records": _miscount_gaps,
    "dimension_values_valid": _bad_dimension_value,
}


# --- defects found by running the checker against the real ledger ---------------------


def test_effectiveness_evidence_that_begins_with_none_counts_as_absent():
    """Real shape from the ledger: "none - no durable runtime implementation of the SWF-32
    counter is established." An exact-match test for "none" reads that as evidence present."""
    ok, failures = check_ledger(_ledger(_clean_record(
        recommended_disposition="ALREADY_GRADUATED",
        effectiveness_evidence="none - no durable runtime implementation is established.")))
    assert not ok
    assert any("graduation_needs_evidence" in f for f in failures)


def test_a_canonical_owner_may_have_no_enforcement_if_its_coverage_is_cited():
    """Codex's dispute, which is correct: explicit ownership survives absent implementation.
    SWF-32 amended SF-REQ-009 to own execution-cycle semantics; nothing implements it yet.
    That is owned-but-unbuilt, not force-fitted - provided the coverage is cited, not asserted."""
    ok, failures = check_ledger(_ledger(_clean_record(
        owner_fit="CANONICAL", enforcement_level="DOCUMENTED_ONLY",
        effectiveness_evidence="none - not yet implemented", proven_red="UNKNOWN",
        owner_fit_basis="SWF-32 amends SF-REQ-009 to own execution_cycle semantics",
        recommended_disposition="STRENGTHEN_EXISTING_OWNER")))
    assert ok, failures


def test_a_canonical_owner_with_no_enforcement_and_no_cited_coverage_is_still_refused():
    """Without a citation the claim is indistinguishable from the force-fit it replaced."""
    ok, failures = check_ledger(_ledger(_clean_record(
        owner_fit="CANONICAL", enforcement_level="DOCUMENTED_ONLY",
        effectiveness_evidence="none - not yet implemented", proven_red="UNKNOWN",
        recommended_disposition="STRENGTHEN_EXISTING_OWNER")))
    assert not ok
    assert any("owner_fit_basis" in f for f in failures)
