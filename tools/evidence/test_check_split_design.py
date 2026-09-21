"""Tests for the BIU split/replan design contract checker.

Phase 5's strong invariant:

    Splitting may change decomposition, but it must conserve authorized intent and
    proof obligations.

Conservation is the checkable part. Every original requirement, acceptance criterion,
verification obligation and evidence obligation must map to a destination; nothing may
silently disappear. "Nothing silently disappears" is exactly the kind of claim that a
checker can enforce and prose cannot.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_split_design import CHECKS, REQUIRED_SECTIONS, check_design  # noqa: E402

DESTINATIONS = ("child_a", "child_b", "retained_integration_parent")


def _obligation(**over):
    o = {"obligation_id": "AC-1", "kind": "acceptance_criterion",
         "origin_biu": "PY-10", "maps_to": ["child_a"], "rationale": "transport is child A's"}
    o.update(over)
    return o


def _design(obligations=None, sections=None, **over):
    d = {"sections": {s: f"defined: {s}" for s in (sections or REQUIRED_SECTIONS)},
         "identity_grammar": "^[A-Z]{2,3}-[0-9]{2,6}[A-Z]?$",
         "strong_invariant_asserted": True,
         "conservation_mapping": obligations if obligations is not None else
             [_obligation(obligation_id=f"O-{i}", kind=k)
              for i, k in enumerate(("requirement", "acceptance_criterion",
                                     "verification_obligation", "evidence_obligation"))],
         "original_biu_lifecycle": "retained_integration_parent"}
    d.update(over)
    return d


def test_a_clean_design_passes():
    ok, f = check_design(_design())
    assert ok, f


def test_a_missing_required_section_is_rejected():
    ok, f = check_design(_design(sections=[s for s in REQUIRED_SECTIONS if s != "closure"]))
    assert not ok
    assert any("required_sections" in x for x in f)


def test_an_obligation_that_maps_nowhere_is_rejected():
    """Nothing silently disappears."""
    ok, f = check_design(_design([_obligation(maps_to=[])]))
    assert not ok
    assert any("conservation" in x for x in f)


def test_an_obligation_mapped_to_none_is_rejected():
    ok, f = check_design(_design([_obligation(maps_to=["none - dropped"])]))
    assert not ok
    assert any("conservation" in x for x in f)


def test_an_unknown_destination_is_rejected():
    ok, f = check_design(_design([_obligation(maps_to=["somewhere_else"])]))
    assert not ok
    assert any("valid_destinations" in x for x in f)


def test_all_four_obligation_kinds_must_be_represented():
    """The plan names four kinds; a mapping covering only one conserves little."""
    ok, f = check_design(_design([_obligation(obligation_id="R-1", kind="requirement")]))
    assert not ok
    assert any("all_obligation_kinds" in x for x in f)


def test_a_complete_mapping_over_all_kinds_passes():
    obs = [_obligation(obligation_id=f"O-{i}", kind=k)
           for i, k in enumerate(("requirement", "acceptance_criterion",
                                  "verification_obligation", "evidence_obligation"))]
    ok, f = check_design(_design(obs))
    assert ok, f


def test_an_absent_identity_grammar_is_rejected():
    """Identity allocation must not rest on ad hoc regex assumptions."""
    ok, f = check_design(_design(identity_grammar="none"))
    assert not ok
    assert any("identity_grammar" in x for x in f)


def test_a_grammar_that_cannot_express_the_one_real_split_identifier_is_rejected():
    """PY-09B is the only split allocation Wave 1 made. A grammar that rejects it is wrong."""
    ok, f = check_design(_design(identity_grammar="^[A-Z]{2}-[0-9]{2}$"))
    assert not ok
    assert any("identity_grammar" in x for x in f)


def test_an_unasserted_strong_invariant_is_rejected():
    ok, f = check_design(_design(strong_invariant_asserted=False))
    assert not ok
    assert any("strong_invariant" in x for x in f)


def test_an_undefined_original_biu_lifecycle_is_rejected():
    ok, f = check_design(_design(original_biu_lifecycle="none"))
    assert not ok
    assert any("original_lifecycle" in x for x in f)


NEGATIVE_CONTROLS = {
    "required_sections": lambda d: d["sections"].pop("closure"),
    "conservation": lambda d: d["conservation_mapping"][0].__setitem__("maps_to", []),
    "valid_destinations": lambda d: d["conservation_mapping"][0].__setitem__("maps_to", ["nope"]),
    "all_obligation_kinds": lambda d: d.__setitem__("conservation_mapping", [_obligation()]),
    "identity_grammar": lambda d: d.__setitem__("identity_grammar", "none"),
    "strong_invariant": lambda d: d.__setitem__("strong_invariant_asserted", False),
    "original_lifecycle": lambda d: d.__setitem__("original_biu_lifecycle", "none"),
}


def test_every_check_has_a_negative_control():
    obs = [_obligation(obligation_id=f"O-{i}", kind=k)
           for i, k in enumerate(("requirement", "acceptance_criterion",
                                  "verification_obligation", "evidence_obligation"))]
    base = _design(obs)
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(base)
        mutate(d)
        ok, f = check_design(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
