"""Tests for the Wave 2 Design Contract checker.

Required discipline from the program plan:

    Do not let implementation agents make material design decisions.
    Design must be explicit enough that implementation becomes local execution rather than
    architecture invention.

That is the checkable claim. A contract that defers a material decision to implementation, or
that leaves a design field hollow, has not made implementation local -- it has moved the
architecture into the implementer's head, which is exactly what Wave 1's unexecuted-composition
and specification-mismatch defects cost.
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_design_contracts import (CHECKS, CONTRACT_FIELDS, KNOWN_CONTEXTS,  # noqa: E402
                                    check_contracts)


def _contract(**over):
    c = {f: f"defined: {f}" for f in CONTRACT_FIELDS}
    c.update({"requirement_id": "SF-REQ-013", "bounded_context": "execution_coordination",
              "deferred_to_implementation": [],
              "deterministic_enforcement_opportunities": ["extend tests/test_architecture_fitness.py"]})
    c.update(over)
    return c


def _doc(contracts=None, required=("SF-REQ-013",)):
    return {"contracts": contracts if contracts is not None else [_contract()],
            "required_requirements": list(required)}


def test_a_clean_contract_set_passes():
    ok, f = check_contracts(_doc())
    assert ok, f


def test_a_missing_contract_field_is_rejected():
    c = _contract()
    del c["recovery"]
    ok, f = check_contracts(_doc([c]))
    assert not ok
    assert any("contract_fields_complete" in x for x in f)


def test_a_hollow_contract_field_is_rejected():
    ok, f = check_contracts(_doc([_contract(failure_modes="none")]))
    assert not ok
    assert any("contract_fields_complete" in x for x in f)


def test_a_material_decision_deferred_to_implementation_is_rejected():
    """The plan's central discipline."""
    ok, f = check_contracts(_doc([_contract(
        deferred_to_implementation=["choice of persistence engine"])]))
    assert not ok
    assert any("no_material_decision_deferred" in x for x in f)


def test_an_explicitly_local_choice_is_allowed():
    """Bounded implementation freedom is not architecture invention."""
    ok, f = check_contracts(_doc([_contract(
        deferred_to_implementation=[],
        implementation_local_freedom=["variable naming", "internal helper decomposition"])]))
    assert ok, f


def test_an_unknown_bounded_context_without_justification_is_rejected():
    ok, f = check_contracts(_doc([_contract(bounded_context="brand_new_thing")]))
    assert not ok
    assert any("bounded_context_known" in x for x in f)


def test_a_new_bounded_context_with_justification_passes():
    ok, f = check_contracts(_doc([_contract(
        bounded_context="brand_new_thing",
        new_context_justification="no existing context owns requirement compilation IR")]))
    assert ok, f


def test_a_requirement_without_a_contract_is_rejected():
    ok, f = check_contracts(_doc([], required=("SF-REQ-013",)))
    assert not ok
    assert any("every_requirement_covered" in x for x in f)


def test_a_contract_with_no_deterministic_enforcement_opportunity_is_rejected():
    """Phase 3 promoted seven gates into existing layers; a design that names none has not
    looked."""
    ok, f = check_contracts(_doc([_contract(deterministic_enforcement_opportunities=[])]))
    assert not ok
    assert any("enforcement_opportunity_named" in x for x in f)


NEGATIVE_CONTROLS = {
    "contract_fields_complete": lambda d: d["contracts"][0].pop("recovery"),
    "no_material_decision_deferred": lambda d: d["contracts"][0].__setitem__(
        "deferred_to_implementation", ["persistence engine choice"]),
    "bounded_context_known": lambda d: d["contracts"][0].__setitem__(
        "bounded_context", "invented_context"),
    "every_requirement_covered": lambda d: d["contracts"].clear(),
    "enforcement_opportunity_named": lambda d: d["contracts"][0].__setitem__(
        "deterministic_enforcement_opportunities", []),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_doc())
        mutate(d)
        ok, f = check_contracts(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


def test_known_contexts_match_the_repository():
    """Guard against the contract set drifting from the codebase it governs."""
    assert "execution_coordination" in KNOWN_CONTEXTS
    assert "control_plane" in KNOWN_CONTEXTS
