"""Tests for the bootstrap retirement matrix checker.

Exit gate: no temporary mechanism quietly becomes permanent, and no known protection
disappears before its replacement is operational. "Retire by replacement, not by date" is the
rule this enforces mechanically -- a RETIRE_CANDIDATE must either have its replacement
implemented or state plainly what protection is not lost.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_retirement_matrix import CHECKS, REQUIRED_MECHANISMS, check_matrix  # noqa: E402


def _mech(**over):
    m = {"mechanism": "SWF-29 liveness reconciliation",
         "purpose": "reconcile launch gaps without retrying completed effects",
         "demonstrated_failure_prevented": "suppressed re-emission during PY-09 quota exhaustion",
         "authority": "SWF-29", "stated_expiry_condition": "SF-REQ-056 operational",
         "replacement_requirement": "SF-REQ-056 or equivalent",
         "replacement_implemented": False, "bootstrap_still_operating": True,
         "recommended_disposition": "KEEP_UNTIL_REPLACED",
         "evidence": ["docs/decisions/2026-09-20-liveness-reconciliation.md"]}
    m.update(over)
    return m


def _matrix(mechs=None, plan=None):
    mechs = mechs if mechs is not None else [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    non_retained = [m["mechanism"] for m in mechs
                    if m["recommended_disposition"] != "KEEP_UNTIL_REPLACED"]
    return {"mechanisms": mechs,
            "transition_plan": plan if plan is not None else
                [{"step": i + 1, "mechanism": n, "depends_on": []}
                 for i, n in enumerate(non_retained)]}


def test_a_clean_matrix_passes():
    ok, f = check_matrix(_matrix())
    assert ok, f


def test_a_missing_field_is_rejected():
    m = _mech()
    del m["stated_expiry_condition"]
    ok, f = check_matrix(_matrix([m] + [_mech(mechanism=n) for n in REQUIRED_MECHANISMS[1:]]))
    assert not ok
    assert any("required_fields" in x for x in f)


def test_an_unlisted_required_mechanism_is_rejected():
    ok, f = check_matrix(_matrix([_mech(mechanism=n) for n in REQUIRED_MECHANISMS[1:]]))
    assert not ok
    assert any("all_mechanisms_covered" in x for x in f)


def test_an_invalid_disposition_is_rejected():
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0]["recommended_disposition"] = "PROBABLY_FINE"
    ok, f = check_matrix(_matrix(ms))
    assert not ok
    assert any("valid_disposition" in x for x in f)


def test_retire_candidate_without_replacement_or_a_no_loss_statement_is_rejected():
    """Retire by replacement, not by date."""
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0].update(recommended_disposition="RETIRE_CANDIDATE", replacement_implemented=False)
    ok, f = check_matrix(_matrix(ms))
    assert not ok
    assert any("retire_by_replacement" in x for x in f)


def test_retire_candidate_passes_when_the_replacement_is_implemented():
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0].update(recommended_disposition="RETIRE_CANDIDATE", replacement_implemented=True)
    ok, f = check_matrix(_matrix(ms))
    assert ok, f


def test_retire_candidate_passes_when_no_protection_is_lost_is_stated():
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0].update(recommended_disposition="RETIRE_CANDIDATE", replacement_implemented=False,
                 protection_not_lost="the queue it served is drained and Wave 1 is closed")
    ok, f = check_matrix(_matrix(ms))
    assert ok, f


def test_revert_temporary_change_without_a_stated_expiry_is_rejected():
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0].update(recommended_disposition="REVERT_TEMPORARY_CHANGE",
                 stated_expiry_condition="none")
    ok, f = check_matrix(_matrix(ms))
    assert not ok
    assert any("revert_needs_expiry" in x for x in f)


def test_a_non_retained_mechanism_missing_from_the_transition_plan_is_rejected():
    ms = [_mech(mechanism=n) for n in REQUIRED_MECHANISMS]
    ms[0].update(recommended_disposition="RETIRE_CANDIDATE", replacement_implemented=True)
    ok, f = check_matrix(_matrix(ms, plan=[]))
    assert not ok
    assert any("transition_plan_complete" in x for x in f)


NEGATIVE_CONTROLS = {
    "required_fields": lambda m: m["mechanisms"][0].pop("stated_expiry_condition"),
    "all_mechanisms_covered": lambda m: m["mechanisms"].pop(0),
    "valid_disposition": lambda m: m["mechanisms"][0].__setitem__("recommended_disposition", "MEH"),
    "retire_by_replacement": lambda m: m["mechanisms"][0].update(
        recommended_disposition="RETIRE_CANDIDATE", replacement_implemented=False),
    "revert_needs_expiry": lambda m: m["mechanisms"][1].update(
        recommended_disposition="REVERT_TEMPORARY_CHANGE", stated_expiry_condition="none"),
    "transition_plan_complete": lambda m: (
        m["mechanisms"][0].update(recommended_disposition="RETIRE_CANDIDATE",
                                  replacement_implemented=True),
        m.__setitem__("transition_plan", [])),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        m = copy.deepcopy(_matrix())
        mutate(m)
        ok, f = check_matrix(m)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
