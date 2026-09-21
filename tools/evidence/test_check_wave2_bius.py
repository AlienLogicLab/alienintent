"""Tests for the Wave 2 candidate BIU set checker.

The learned decomposition rules the plan names, reduced to the ones a machine can decide:

- no unowned substrate: every capability a BIU needs is owned by some BIU
- requirement conservation: every requirement in the plan appears in some BIU
- no impossible acceptance criteria: a criterion no evidence could satisfy is a defect
  (PY-09B binding rule 6 demanded proof the platform could not give; SWF-34 undid it)
- proof harness established early: a BIU whose verification obligations are empty while it
  carries acceptance criteria has deferred its proof
- capstones integrate rather than invent: a capstone may not introduce a dependency that exists
  nowhere else in the set
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_wave2_bius import BIU_FIELDS, CHECKS, check_bius  # noqa: E402


def _biu(**over):
    b = {f: f"defined: {f}" for f in BIU_FIELDS}
    b.update({"biu_id": "W2-PY-01", "requirement_links": ["SF-REQ-011"],
              "dependencies": [], "is_capstone": False,
              "needs_capabilities": [], "provides_capabilities": ["requirement_ir"],
              "acceptance_criteria": ["an IR document is produced from a requirement set"],
              "verification_obligations": ["fixture: malformed requirement yields typed error"],
              "evidence_obligations": ["trajectory record emitted"]})
    b.update(over)
    return b


def _doc(bius=None, required=("SF-REQ-011",)):
    return {"bius": bius if bius is not None else [_biu()],
            "required_requirements": list(required)}


def test_a_clean_biu_set_passes():
    ok, f = check_bius(_doc())
    assert ok, f


def test_a_missing_biu_field_is_rejected():
    b = _biu()
    del b["stop_condition"]
    ok, f = check_bius(_doc([b]))
    assert not ok
    assert any("biu_fields_complete" in x for x in f)


def test_a_needed_capability_nobody_provides_is_rejected():
    """No unowned substrate."""
    ok, f = check_bius(_doc([_biu(needs_capabilities=["live_transport"])]))
    assert not ok
    assert any("no_unowned_substrate" in x for x in f)


def test_a_needed_capability_another_biu_provides_passes():
    a = _biu(biu_id="W2-PY-01", provides_capabilities=["live_transport"])
    b = _biu(biu_id="W2-PY-02", needs_capabilities=["live_transport"],
             provides_capabilities=["capstone_proof"], dependencies=["W2-PY-01"])
    ok, f = check_bius(_doc([a, b]))
    assert ok, f


def test_a_requirement_with_no_biu_is_rejected():
    """Requirement conservation."""
    ok, f = check_bius(_doc(required=("SF-REQ-011", "SF-REQ-012")))
    assert not ok
    assert any("requirement_conservation" in x for x in f)


def test_an_impossible_acceptance_criterion_is_rejected():
    ok, f = check_bius(_doc([_biu(
        acceptance_criteria=["prove the token cannot access any other project"])]))
    assert not ok
    assert any("no_impossible_acceptance" in x for x in f)


def test_acceptance_criteria_with_no_verification_obligation_is_rejected():
    """Proof harness established early."""
    ok, f = check_bius(_doc([_biu(verification_obligations=[])]))
    assert not ok
    assert any("proof_harness_early" in x for x in f)


def test_a_capstone_inventing_a_dependency_is_rejected():
    a = _biu(biu_id="W2-PY-01", provides_capabilities=["requirement_ir"])
    cap = _biu(biu_id="W2-PY-09", is_capstone=True, dependencies=["W2-PY-01"],
               needs_capabilities=["requirement_ir", "brand_new_thing"],
               provides_capabilities=["brand_new_thing"])
    ok, f = check_bius(_doc([a, cap]))
    assert not ok
    assert any("capstone_integrates" in x for x in f)


NEGATIVE_CONTROLS = {
    "biu_fields_complete": lambda d: d["bius"][0].pop("stop_condition"),
    "no_unowned_substrate": lambda d: d["bius"][0].__setitem__("needs_capabilities", ["ghost"]),
    "requirement_conservation": lambda d: d["required_requirements"].append("SF-REQ-999"),
    "no_impossible_acceptance": lambda d: d["bius"][0].__setitem__(
        "acceptance_criteria", ["prove no other project can ever be reached"]),
    "proof_harness_early": lambda d: d["bius"][0].__setitem__("verification_obligations", []),
    "capstone_integrates": lambda d: d["bius"][0].update(
        is_capstone=True, needs_capabilities=["solo"], provides_capabilities=["solo"]),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_doc())
        mutate(d)
        ok, f = check_bius(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
