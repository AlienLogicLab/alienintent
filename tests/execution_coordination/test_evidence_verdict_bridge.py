"""Acceptance uses exact authorized inputs and the unchanged execution policy."""
from dataclasses import replace

import pytest

from alienintent.evidence_learning.domain.records import Outcome, Verdict, record_ref
from alienintent.evidence_learning.domain.refs import EvidenceHold
from tests.evidence_learning.support import definition, external_ref, header, observation, profile, seeded


def evaluate(p, dref, refs, **overrides):
    args = dict(header=header("verdict"), definition_ref=dref, observation_refs=refs,
                evaluator="fixture-verifier", authority_ref=external_ref("evaluator-authority"),
                policy_ref=external_ref("policy"), worker_claimed_success=True)
    args.update(overrides)
    return p.verdict.evaluate(**args)


def test_authorized_exact_evidence_bridges_and_retains_all_three_roles(tmp_path):
    p, dref, oref = seeded(tmp_path)
    v = evaluate(p, dref, (oref,))
    assert isinstance(v, Verdict)
    assert v.outcome is Outcome.ACCEPT
    assert v.definition_ref == dref and v.observation_refs == (oref,)
    assert v.reason == "policy accepted required trusted evidence"
    vref = p.service.admit(v, 2).ref
    assert p.repository.get(vref, p.access_scope) == v
    assert [type(r).__name__ for r in p.service.read().records] == ["Definition", "Observation", "Verdict"]


def test_worker_claim_unknown_false_or_numeric_one_cannot_authorize_pass(tmp_path):
    for i, changes in enumerate([{"observer": "fixture-worker"}, {"value": None, "uncertainty": "not measured"}, {"value": False}, {"value": 1}]):
        root = tmp_path / str(i)
        root.mkdir()
        p = profile(root)
        dref = p.service.admit(definition(), 0).ref
        oref = p.service.admit(observation(**changes), 1).ref
        assert evaluate(p, dref, (oref,)).outcome is Outcome.REJECT


def test_conflicting_or_stale_inputs_hold_even_if_caller_selects_only_success(tmp_path):
    p, dref, oref = seeded(tmp_path)
    p.service.admit(replace(observation(value=False), header=header("conflict")), 2)
    with pytest.raises(EvidenceHold, match="CONFLICTING_OBSERVATIONS"):
        evaluate(p, dref, (oref,))
    new = replace(definition("2"), header=replace(definition("2").header, preceding_refs=(dref,)))
    p.service.admit(new, 3)
    with pytest.raises(EvidenceHold, match="STALE_DEFINITION"):
        evaluate(p, dref, (oref,))


def test_bridge_rejects_wrong_roles_unknown_authority_and_missing_objects(tmp_path):
    p, dref, oref = seeded(tmp_path)
    for refs, overrides in [((dref,), {}), ((oref,), {"evaluator": "worker"}),
                            ((oref,), {"policy_ref": external_ref("unknown-policy")}), ((), {})]:
        with pytest.raises(EvidenceHold):
            evaluate(p, dref, refs, **overrides)
    (tmp_path / "evidence" / oref.locator).unlink()
    with pytest.raises(EvidenceHold, match="MISSING_OBJECT"):
        evaluate(p, dref, (oref,))


@pytest.mark.parametrize("changes", [{"value": False}, {"value": None, "uncertainty": "not measured"}, {"observer": "fixture-worker"}])
def test_direct_accept_admission_cannot_bypass_execution_policy(tmp_path, changes):
    p = profile(tmp_path)
    dref = p.service.admit(definition(), 0).ref
    oref = p.service.admit(observation(**changes), 1).ref
    evaluated = evaluate(p, dref, (oref,))
    assert evaluated.outcome is Outcome.REJECT
    with pytest.raises(EvidenceHold, match="VERDICT_POLICY_MISMATCH"):
        p.service.admit(replace(evaluated, outcome=Outcome.ACCEPT), 2)
    assert p.service.read().version == 2


def test_verdict_evaluated_before_conflict_cannot_be_newly_admitted_after_it(tmp_path):
    p, dref, oref = seeded(tmp_path)
    earlier = evaluate(p, dref, (oref,))
    p.service.admit(replace(observation(value=False), header=header("conflict")), 2)
    with pytest.raises(EvidenceHold, match="CONFLICTING_OBSERVATIONS"):
        p.service.admit(earlier, 3)
    assert p.service.read().version == 3


def test_previously_admitted_verdict_remains_historical_when_new_conflict_arrives(tmp_path):
    p, dref, oref = seeded(tmp_path)
    vref = p.service.admit(evaluate(p, dref, (oref,)), 2).ref
    p.service.admit(replace(observation(value=False), header=header("conflict")), 3)
    reopened = profile(tmp_path)
    state = reopened.service.read()
    assert vref in state.refs
    assert state.held_definitions == (dref,)
    with pytest.raises(EvidenceHold, match="CONFLICTING_OBSERVATIONS"):
        evaluate(reopened, dref, (oref,))
