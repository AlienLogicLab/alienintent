"""`work release` (PLAN-AUTHORITY-INHERITANCE acceptance checks 4 and 5): the control plane releases a plan-derived
item with no Founder words and no manual card change, or refuses with its named code writing nothing.

Every case runs the composed WorkRegistry over the fixture project of test_work_registry (PlanBoard): a local clone,
the `readiness` store and evidence folder, a fixture Agent Ready and a recorded board that keeps each card's Status
and Priority. Plans, labels and quotes are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json

import pytest

from alienintent.context_assembly.application.inherited_release import (
    ASSESSMENT_MISSING, NOT_PLAN_DERIVED, NOT_RELEASABLE, OWNER_DECISION_REQUIRED)
from alienintent.context_assembly.domain.work_context import PRODUCER, ContextPackage
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH
from tests.composition.test_work_registry import PLAN_SCOPE, PlanBoard, plan_text
from tests.context_assembly.test_work_identity_service import commit_file


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


def test_an_item_prepared_under_an_older_plan_revision_is_revalidated_and_released_under_the_tip(fx):
    """PLAN-TIP-AUTHORITY-RUNTIME-FIX: the plan at main's tip is the live authority, with no approval step. An item
    prepared under an older revision is released when it is inside the tip's scope, and its release evidence records
    the exact tip commit and digest it was released under and the digest it was prepared from."""
    older = fx.approve()
    item = fx.derived("PD-OLD", older)
    tip = commit_file(fx.clone, "main", PLAN_PATH, plan_text(note=" revision 2"))  # no approval of revision 2
    live = "sha256:" + sha256(plan_text(note=" revision 2")).hexdigest()

    result = fx.loaded().release.release(item.id)

    assert result.answer is None, result
    release, _, _ = state(fx, item.id)
    assert release.text.startswith(f"inherited from plan authority {live}") and f"revalidated from {older}" in release.text
    package_evidence = json.loads(fx.registry.assessment.consumer.repository.get(
        ref_from_document(result.evidence_ref), frozenset({"private"})).value)
    assert package_evidence["plan"] == {"commit": tip, "content_digest": live, "prepared_from": older}


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
    if case == "older-plan":  # a later approved revision at the tip no longer grants the item's obligation
        fx.approve(plan_text(dict(PLAN_SCOPE, obligations=[
            dict(PLAN_SCOPE["obligations"][0], label="OTHER")])))
    before = state(fx, item.id)

    result = fx.loaded().release.release(item.id)

    assert result.answer == {"released": NOT_RELEASABLE, "held": ASSESSMENT_MISSING, "explicit": NOT_PLAN_DERIVED,
                             "older-plan": OWNER_DECISION_REQUIRED}[case]
    assert state(fx, item.id) == before and fx.github.fields == {}
    assert len(owner_decisions(fx, item.id)) == (1 if case == "older-plan" else 0)
    if case == "older-plan":
        assert "obligation FIXTURE is not in the approved plan" in result.detail
        fx.loaded().release.release(item.id)  # a rerun keeps the one durable owner-decision item
        [decision] = owner_decisions(fx, item.id)
        assert (decision.origin.kind, decision.origin.event_identity) == ("JUDGMENT", OWNER_DECISION_REQUIRED)


def test_a_release_records_and_checks_one_and_the_same_tip(fx):
    """The tip moves while a release runs (a landing): the release checks the item against the tip it records, never
    a second read. Here the second read would be a tip that drops the obligation; the release, made under the first,
    records that first tip."""
    digest = fx.approve()
    item = fx.derived("PD-RACE", digest)
    first = commit_file(fx.clone, "main", PLAN_PATH, plan_text(note=" revision 2"))  # still grants FIXTURE
    dropped = commit_file(fx.clone, "side", PLAN_PATH, plan_text(dict(PLAN_SCOPE, obligations=[
        dict(PLAN_SCOPE["obligations"][0], label="OTHER")])))
    registry = fx.loaded()
    tips = iter([first])
    registry.plan_approval.tip = lambda: next(tips, dropped)  # every read after the first sees the moved tip

    result = registry.release.release(item.id)

    assert result.answer is None, result
    evidence = json.loads(fx.registry.assessment.consumer.repository.get(
        ref_from_document(result.evidence_ref), frozenset({"private"})).value)
    assert evidence["plan"]["commit"] == first
