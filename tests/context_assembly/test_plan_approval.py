"""`work approve-plan` (PLAN-AUTHORITY-INHERITANCE acceptance check 3) and the live plan authority
(PLAN-TIP-AUTHORITY-RUNTIME-FIX, Founder 2026-10-10: the canonical plan at the tip of canonical main is the live
authority root; an approval is a record, never an activation switch), on the composed WorkRegistry over a temporary
project with a local clone. Plans and quotes are TEST DATA.
"""
from __future__ import annotations

from hashlib import sha256
import subprocess

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
    """The approval is recorded once and becomes the current approval record (`plan-authority:current`); the live
    authority is the same revision because it is main's tip, not because it was approved."""
    data = plan_text()
    commit = commit_file(fx.clone, "main", PLAN_PATH, data)
    result = fx.registry.plan_approval.approve(commit, PLAN_QUOTE)
    assert (result.answer, result.repeated, result.content_digest) == (None, False,
                                                                       "sha256:" + sha256(data).hexdigest())
    _, recorded = fx.loaded().store.read_state("registry", CURRENT)  # read back by another process
    assert (recorded["content_digest"], recorded["record_ref"]) == (result.content_digest, result.evidence_ref)
    current = fx.loaded().plan_approval.current()
    assert (current.commit, current.content_digest) == (commit, result.content_digest)
    assert current.scope == parse_scope(data.decode())
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


def test_the_live_authority_is_the_plan_at_the_tip_of_main_with_no_approval(fx):
    """No `approve-plan` is needed: the plan at main's tip is the authority (read back by another process), and when
    the tip moves the authority moves with it, whatever was approved before. Reading it writes nothing."""
    first_data = plan_text()
    first = commit_file(fx.clone, "main", PLAN_PATH, first_data)
    before = written(fx)
    current = fx.loaded().plan_approval.current()
    assert (current.commit, current.content_digest, current.plan_path) == (
        first, "sha256:" + sha256(first_data).hexdigest(), PLAN_PATH)
    assert current.scope == parse_scope(first_data.decode()) and written(fx) == before
    fx.registry.plan_approval.approve(first, PLAN_QUOTE)  # an approval of the old revision does not pin it
    second_data = plan_text(note=" revision 2")
    second = commit_file(fx.clone, "main", PLAN_PATH, second_data)
    current = fx.loaded().plan_approval.current()
    assert (current.commit, current.content_digest) == (second, "sha256:" + sha256(second_data).hexdigest())
    commit_file(fx.clone, "main", PLAN_PATH, b"# plan\n\n```json alienintent-plan-authority\n{}\n```\n")
    assert fx.loaded().plan_approval.current() is None  # no authority from a tip whose block is invalid


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
    assert written(fx) == before
    assert (fx.registry.plan_approval.current() is None) is (case != "empty-quote")  # the tip's plan, if valid


def test_a_tag_named_like_the_branch_never_becomes_the_authority(fx):
    """Only the branch `refs/heads/main` is read: a tag `main` pointing at a side-branch plan is ignored."""
    tip = commit_file(fx.clone, "main", PLAN_PATH, plan_text())
    side = commit_file(fx.clone, "side", PLAN_PATH, plan_text(note=" side"))
    subprocess.run(["git", "tag", "main", side], cwd=fx.clone, check=True, capture_output=True)
    assert fx.loaded().plan_approval.current().commit == tip
