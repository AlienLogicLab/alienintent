"""`work release` (PLAN-AUTHORITY-INHERITANCE acceptance checks 4 and 5): the control plane releases a plan-derived
item with no Founder words and no manual card change, or refuses with its named code writing nothing.

Every case runs the composed WorkRegistry over the fixture project of test_work_registry (PlanBoard): a local clone,
the `readiness` store and evidence folder, a fixture Agent Ready and a recorded board that keeps each card's Status
and Priority. Plans, labels and quotes are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest

from alienintent.context_assembly.application.inherited_release import (
    ASSESSMENT_MISSING, NOT_PLAN_DERIVED, NOT_RELEASABLE, OWNER_DECISION_REQUIRED)
from alienintent.context_assembly.domain.work_context import PRODUCER, ContextPackage
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from tests.composition.test_work_registry import PlanBoard, plan_text


@pytest.fixture
def fx(tmp_path) -> PlanBoard:
    return PlanBoard(tmp_path / "fx")


def state(fx: PlanBoard, identity: str) -> tuple:
    """What a release writes for the item: its release record, its approval_ref and its card's fields."""
    item = fx.registry.identities.find(identity)
    return (fx.registry.assessment.authorizations.release_authorization(identity), item.approval_ref,
            fx.github.fields.get(item.card_id) if item.card_id else None)


def owner_decisions(fx: PlanBoard, identity: str) -> list:
    return [i for i in fx.registry._attention.list_pending() if i.origin.work_ref == identity]


def test_a_plan_derived_item_is_released_its_card_reads_back_ready_p0_and_its_producer_context_assembles(fx):
    digest = fx.approve()
    item = fx.derived("PD-OK", digest)

    result = fx.loaded().release.release(item.id)

    assert result.answer is None and result.priority == "P0"
    release, approval, fields = state(fx, item.id)
    assert release.text.startswith(f"inherited from plan authority {digest}") and release.authorizes_implement
    assert approval is not None and approval.revision_digest == release.record_ref
    assert (fields["Status"], fields["Priority"]) == ("READY", "P0")
    store, correlation = fx.registry.store, f"launch:{item.id}:0"
    store.acquire_within("registry", "wip", item.id, f"work:{item.id}", 10)
    store.acquire("registry", "repository", f"repository-{item.label}", correlation)
    package = fx.registry.context.assemble(item.id, PRODUCER, correlation, None)
    assert isinstance(package, ContextPackage), package
    assert package.fields["release_record"]["evidence"]["approver"] == "plan-authority:" + digest


@pytest.mark.parametrize("case", ["released", "held", "explicit", "older-plan"])
def test_each_refusal_answers_its_code_and_writes_nothing(fx, case):
    digest = fx.approve()
    if case == "held":
        fx.answer.write_text("HOLD")
    item = fx.derived("PD-NO", digest, **({"release_policy": "explicit-human-off", "authority_issuer": "Founder"}
                                          if case == "explicit" else {}))
    if case == "released":  # a Founder release already recorded
        fx.registry.assessment.authorizations.record(ReleaseAuthorization(
            item.id, "sha256:" + "e" * 64, True, item.pointer.commit, "IMPLEMENT is authorized."))
    if case == "older-plan":  # the item was issued under the first digest; a second revision is approved after it
        fx.approve(plan_text(note=" revision 2"))
    before = state(fx, item.id)

    result = fx.loaded().release.release(item.id)

    assert result.answer == {"released": NOT_RELEASABLE, "held": ASSESSMENT_MISSING, "explicit": NOT_PLAN_DERIVED,
                             "older-plan": OWNER_DECISION_REQUIRED}[case]
    assert state(fx, item.id) == before and fx.github.fields == {}
    assert len(owner_decisions(fx, item.id)) == (1 if case == "older-plan" else 0)
    if case == "older-plan":
        assert "authority_issuer: not the approved plan authority" in result.detail
        fx.loaded().release.release(item.id)  # a rerun keeps the one durable owner-decision item
        [decision] = owner_decisions(fx, item.id)
        assert (decision.origin.kind, decision.origin.event_identity) == ("JUDGMENT", OWNER_DECISION_REQUIRED)
