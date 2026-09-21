"""Tests for the final Wave 1 retrospective checker.

Two things this enforces that prose cannot. The reconciliation rule -- existing owner first,
amendment preferred, a new requirement only with proof that no owner covers the semantics, and
Priority/Wave never invented. And the causality constraint: the two first-pass acceptances were
tested in Phase 2 as RAW-100 and not promoted (n=2, confounded), so no claim above HYPOTHESIS
may be made about their cause.
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_retrospective import CHECKS, check_retrospective  # noqa: E402


def _rec(**over):
    r = {"proposed_change": "extend SF-REQ-013 to own split/replan",
         "existing_owner": "SF-REQ-013", "change_type": "AMENDMENT",
         "ownership_proof": "SF-REQ-013 lowers requirements into BIUs; the transaction is adjacent",
         "priority_or_wave_invented": False}
    r.update(over)
    return r


def _retro(recs=None, **over):
    d = {"yield": {"biu_count": 11, "token_usage": "UNKNOWN", "cost": "UNKNOWN"},
         "learning": {"propagated": 3}, "methodology": {"verification_first": "assessed"},
         "architecture": {"identity": "assessed"},
         "recommendations": recs if recs is not None else [_rec()],
         "causality_claim": "HYPOTHESIS: verification-first may have contributed; confounded with provider substitution",
         "unresolved_founder_decisions": ["POSTW1-DECIDE-004A"]}
    d.update(over)
    return d


def test_a_clean_retrospective_passes():
    ok, f = check_retrospective(_retro())
    assert ok, f


def test_a_recommendation_without_an_existing_owner_is_rejected():
    ok, f = check_retrospective(_retro([_rec(existing_owner="none", ownership_proof="none")]))
    assert not ok
    assert any("existing_owner_first" in x for x in f)


def test_a_new_requirement_without_an_ownership_proof_is_rejected():
    ok, f = check_retrospective(_retro([_rec(change_type="NEW_REQUIREMENT",
                                             existing_owner="none", ownership_proof="none")]))
    assert not ok
    assert any("new_requirement_needs_proof" in x for x in f)


def test_a_new_requirement_with_a_proof_passes():
    ok, f = check_retrospective(_retro([_rec(change_type="NEW_REQUIREMENT", existing_owner="none",
        ownership_proof="no SF-REQ covers this; each candidate was read and none states it")]))
    assert ok, f


def test_inventing_priority_or_wave_is_rejected():
    ok, f = check_retrospective(_retro([_rec(priority_or_wave_invented=True)]))
    assert not ok
    assert any("never_invent_priority_or_wave" in x for x in f)


def test_unknown_telemetry_reported_as_a_number_is_rejected():
    """SF-REQ-030: UNKNOWN is never silently converted to zero."""
    r = _retro()
    r["yield"]["token_usage"] = 0
    ok, f = check_retrospective(r)
    assert not ok
    assert any("unknown_preserved" in x for x in f)


def test_a_causal_claim_about_the_first_pass_acceptances_is_rejected():
    ok, f = check_retrospective(_retro(
        causality_claim="verification-first sequencing caused both first-pass acceptances"))
    assert not ok
    assert any("no_unproven_causality" in x for x in f)


def test_a_hypothesis_labelled_claim_passes():
    ok, f = check_retrospective(_retro(
        causality_claim="HYPOTHESIS: bounded scope may have contributed; n=2 and confounded"))
    assert ok, f


def test_a_missing_required_section_is_rejected():
    r = _retro()
    del r["architecture"]
    ok, f = check_retrospective(r)
    assert not ok
    assert any("required_sections" in x for x in f)


NEGATIVE_CONTROLS = {
    "required_sections": lambda d: d.pop("architecture"),
    "existing_owner_first": lambda d: d["recommendations"][0].update(
        existing_owner="none", ownership_proof="none", change_type="AMENDMENT"),
    "new_requirement_needs_proof": lambda d: d["recommendations"][0].update(
        change_type="NEW_REQUIREMENT", existing_owner="SF-REQ-013", ownership_proof="none"),
    "never_invent_priority_or_wave": lambda d: d["recommendations"][0].__setitem__(
        "priority_or_wave_invented", True),
    "unknown_preserved": lambda d: d["yield"].__setitem__("cost", 0),
    "no_unproven_causality": lambda d: d.__setitem__(
        "causality_claim", "the provider substitution caused both first-pass acceptances"),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_retro())
        mutate(d)
        ok, f = check_retrospective(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
