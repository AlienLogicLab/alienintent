"""`work approve-plan` (PLAN-AUTHORITY-INHERITANCE acceptance check 3): the Founder's approval of one exact
canonical-plan revision, on the composed WorkRegistry over a temporary project with a local clone. Plans and quotes
are TEST DATA.
"""
from __future__ import annotations

from hashlib import sha256

import pytest

from alienintent.context_assembly.application.plan_approval import CURRENT, PLAN_NOT_ON_MAIN, PLAN_SCOPE_INVALID
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, parse_scope
from tests.composition.test_work_registry import PLAN_QUOTE, PlanBoard, plan_text
from tests.context_assembly.test_work_authorization import dump
from tests.context_assembly.test_work_identity_service import commit_file


@pytest.fixture
def fx(tmp_path) -> PlanBoard:
    return PlanBoard(tmp_path / "fx")


def written(fx: PlanBoard) -> tuple:
    """Everything the command could write: the `readiness` database and the evidence folder."""
    objects = fx.root / "evidence" / "objects"
    return dump(fx.root / "readiness.sqlite"), sorted(p.name for p in objects.iterdir()) if objects.is_dir() else []


def test_an_approval_records_the_exact_revision_and_becomes_current(fx):
    data = plan_text()
    commit = commit_file(fx.clone, "main", PLAN_PATH, data)
    result = fx.registry.plan_approval.approve(commit, PLAN_QUOTE)
    assert (result.answer, result.repeated, result.content_digest) == (None, False,
                                                                       "sha256:" + sha256(data).hexdigest())
    current = fx.loaded().plan_approval.current()  # read back by another process
    assert (current.commit, current.content_digest, current.quote, current.approver) == (
        commit, result.content_digest, PLAN_QUOTE, "Founder")
    assert current.scope == parse_scope(data.decode()) and current.record_ref == result.evidence_ref["revision_digest"]

    before = written(fx)
    again = fx.registry.plan_approval.approve(commit, PLAN_QUOTE)
    assert (again.answer, again.repeated, again.evidence_ref) == (None, True, result.evidence_ref)
    assert written(fx) == before


def test_re_approving_an_older_revision_makes_it_current_again(fx):
    first = fx.approve()
    second = fx.approve(plan_text(note=" revision 2"))
    assert fx.registry.plan_approval.current().content_digest == second
    commit = commit_file(fx.clone, "main", PLAN_PATH, plan_text())
    assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).repeated is True
    assert fx.registry.plan_approval.current().content_digest == first
    _, current = fx.registry.store.read_state("registry", CURRENT)
    assert current["content_digest"] == first


@pytest.mark.parametrize("case", ["side-branch", "bad-block", "empty-quote"])
def test_each_refusal_writes_nothing(fx, case):
    before = written(fx)
    if case == "side-branch":
        commit = commit_file(fx.clone, "side", PLAN_PATH, plan_text())
        assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).answer == PLAN_NOT_ON_MAIN
    elif case == "bad-block":
        commit = commit_file(fx.clone, "main", PLAN_PATH, b"# plan\n\n```json alienintent-plan-authority\n{}\n```\n")
        assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).answer == PLAN_SCOPE_INVALID
    else:
        with pytest.raises(ValueError):
            fx.registry.plan_approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text()), " ")
    assert written(fx) == before and fx.registry.plan_approval.current() is None
