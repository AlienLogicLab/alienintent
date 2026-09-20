from __future__ import annotations

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.lifecycle import (
    AuthorityBlocked,
    Cancelled,
    ExecutionState,
    LifecycleError,
    LifecycleStage,
    transition,
)
from alienintent.execution_coordination.domain.release import ReleaseConflict, ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.domain.scheduling import Capacity, ScheduledItem, select_admissible
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, VerdictKind, evaluate_verdict
from .test_contract import valid_contract


def test_release_is_idempotent_and_rejects_changed_payload_or_missing_guards() -> None:
    contract = valid_contract(budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)))
    request = ReleaseRequest("release-1", contract, contract.content_digest, frozenset(), frozenset({"python"}), {"attempts": 1}, "Founder")
    accepted = admit_release({}, request)

    assert admit_release(accepted.releases, request).identity == "release-1"
    with pytest.raises(ReleaseConflict):
        admit_release(accepted.releases, ReleaseRequest("release-1", contract, contract.content_digest, frozenset(), frozenset(), {"attempts": 1}, "Founder"))
    with pytest.raises(ValueError, match="capability"):
        admit_release({}, ReleaseRequest("release-2", contract, contract.content_digest, frozenset(), frozenset(), {"attempts": 1}, "Founder"))
    with pytest.raises(ValueError, match="stale readiness"):
        admit_release({}, ReleaseRequest("release-3", contract, "sha256:stale", frozenset(), frozenset({"python"}), {"attempts": 1}, "Founder"))
    dependency_contract = valid_contract(dependencies=("PY-01",))
    with pytest.raises(ValueError, match="unsatisfied dependency"):
        admit_release({}, ReleaseRequest("release-4", dependency_contract, dependency_contract.content_digest, frozenset(), frozenset({"python"}), {"attempts": 1}, "Founder"))
    with pytest.raises(ValueError, match="budget"):
        admit_release({}, ReleaseRequest("release-5", contract, contract.content_digest, frozenset(), frozenset({"python"}), {}, "Founder"))
    with pytest.raises(ValueError, match="budget"):
        admit_release({}, ReleaseRequest("release-6", contract, contract.content_digest, frozenset(), frozenset({"python"}), {"attempts": 0}, "Founder"))
    timed = valid_contract(budget_policy=BudgetPolicy(hard_wall_clock_seconds=60))
    with pytest.raises(ValueError, match="budget"):
        admit_release({}, ReleaseRequest("release-timed", timed, timed.content_digest, frozenset(), frozenset({"python"}), {}, "Founder"))
    automatic = valid_contract(release_policy="automatic-on")
    with pytest.raises(ValueError, match="policy"):
        admit_release({}, ReleaseRequest("release-7", automatic, automatic.content_digest, frozenset(), frozenset({"python"}), {"attempts": 1}, "Founder"))
    assert admit_release({}, ReleaseRequest("release-8", automatic, automatic.content_digest, frozenset(), frozenset({"python"}), {"attempts": 1}, "policy-v1", ReleaseSource.AUTOMATIC_POLICY)).identity == "release-8"


def test_lifecycle_requires_readback_and_policy_verdict_then_rework_invalidates_acceptance() -> None:
    candidate = CandidateRef.archive("sha256:" + "a" * 64, "archive://x").with_independent_read_back()
    state = transition(ExecutionState.for_contract(valid_contract()), 0, "verify", candidate=candidate)
    state = transition(state, 1, "review")
    verdict = evaluate_verdict(EvidenceDefinition(frozenset({"tests"})), (Observation("tests", True, True),), worker_claimed_success=True)
    state = transition(state, 2, "accept", verdict=verdict)
    reworked = transition(state, 3, "rework")

    assert reworked.stage is LifecycleStage.IMPLEMENT
    assert not reworked.accepted
    with pytest.raises(LifecycleError):
        transition(ExecutionState(), 0, "verify")
    with pytest.raises(AuthorityBlocked):
        transition(ExecutionState(), 0, "authority-block")
    with pytest.raises(Cancelled):
        transition(ExecutionState(), 0, "cancel")
    with pytest.raises(LifecycleError):
        transition(state, 99, "close")
    with pytest.raises(LifecycleError, match="closure"):
        transition(state, 3, "close")
    assert transition(state, 3, "close", completed_closure_actions=frozenset({"publish candidate"})).stage is LifecycleStage.DONE


def test_scheduling_honours_priority_fifo_and_capacity_without_blocking_independent_work() -> None:
    items = (
        ScheduledItem("blocked", 0, "repo", "profile", 1, False),
        ScheduledItem("later", 2, "repo", "profile", 2, True),
        ScheduledItem("first", 1, "repo", "profile", 1, True),
    )
    selected = select_admissible(items, (), Capacity(global_limit=3, profile_mutating_limit=3, repository_mutating_limit=3))

    assert [item.identity for item in selected] == ["first", "later"]


def test_verifier_counts_globally_but_not_against_mutating_repository_slot() -> None:
    verifier = ScheduledItem("verify", 1, "repo", "profile", None, True, mutating=False)
    producer = ScheduledItem("implement", 2, "repo", "profile", None, True)
    assert [item.identity for item in select_admissible((verifier, producer), (), Capacity(global_limit=2, profile_mutating_limit=1))] == ["verify", "implement"]
    assert select_admissible((verifier, producer), (), Capacity(global_limit=1, profile_mutating_limit=1)) == (verifier,)


def test_worker_claim_without_required_trusted_evidence_cannot_accept() -> None:
    verdict = evaluate_verdict(EvidenceDefinition(frozenset({"tests"})), (), worker_claimed_success=True)
    assert verdict.kind is VerdictKind.REJECT
