"""Removing role, revision or authority validation must break these assertions."""
from dataclasses import replace

import pytest

from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.evidence_learning.domain.records import Outcome, Verdict, record_ref
from tests.evidence_learning.support import definition, observation, external_ref, header


def test_authority_rejects_observation_promotion(tmp_path):
    from tests.evidence_learning.support import profile
    p = profile(tmp_path)
    forged = replace(definition(), issuer="fixture-worker")
    with pytest.raises(EvidenceHold, match="DEFINITION_AUTHORITY"):
        p.service.admit(forged, 0)
    assert p.service.read().version == 0
    assert p.service.admit(definition(), 0).version == 1


def test_kind_gate_refuses_an_observation_used_as_definition(tmp_path):
    from tests.evidence_learning.support import seeded
    p, dref, oref = seeded(tmp_path)
    forged = replace(observation(), header=header("forged"), definition_ref=oref)
    with pytest.raises(EvidenceHold, match="LINK_KIND"):
        p.service.admit(forged, 2)
    assert p.service.read().version == 2


def test_revision_gate_refuses_stale_evidence(tmp_path):
    from tests.evidence_learning.support import seeded
    p, dref, oref = seeded(tmp_path)
    new = replace(definition("2"), header=replace(definition("2").header, preceding_refs=(dref,)))
    # Both exact revisions were authorized externally, before ingestion.
    p.service.admit(new, 2)
    with pytest.raises(EvidenceHold, match="STALE_DEFINITION"):
        p.service.admit(replace(observation(), header=header("stale")), 3)


def test_missing_evaluator_policy_or_observation_ref_cannot_mint_verdict(tmp_path):
    from tests.evidence_learning.support import seeded
    p, dref, oref = seeded(tmp_path)
    v = Verdict(header("verdict"), dref, (oref,), "fixture-verifier", external_ref("evaluator-authority"), external_ref("policy"), Outcome.ACCEPT, "observed")
    for bad in [replace(v, evaluator="fixture-worker"), replace(v, policy_ref=external_ref("wrong-policy")),
                replace(v, observation_refs=(external_ref("missing"),))]:
        with pytest.raises(EvidenceHold):
            p.service.admit(bad, 2)
    assert p.service.read().version == 2


def test_conflict_preserves_both_observations_and_definition(tmp_path):
    from tests.evidence_learning.support import seeded
    p, dref, oref = seeded(tmp_path)
    false = replace(observation(value=False), header=header("competing-result"))
    fref = p.service.admit(false, 2).ref
    state = p.service.read()
    assert state.held_definitions == (dref,)
    assert state.refs == (dref, oref, fref)
    assert p.repository.get(dref, p.access_scope) == definition()
    assert p.repository.get(oref, p.access_scope).value is True
    assert p.repository.get(fref, p.access_scope).value is False
