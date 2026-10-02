from __future__ import annotations

from dataclasses import replace

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
from alienintent.execution_coordination.domain.release import (
    BaselineEvidence,
    ReleaseAuthorization,
    ReleaseConflict,
    ReleasePreconditionRefused,
    ReleaseRequest,
    ReleaseSource,
    admit_release,
    admit_release_preconditions,
    release_wording,
)
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


BASELINE = "a" * 40
DENIAL = "Implementation is **not** authorized by this Issue. Release remains an explicit authority step."


def _authorization(**overrides) -> ReleaseAuthorization:
    values = dict(identity="WO-1", record_ref="issue#1:comment:1", authorizes_implement=True, baseline=BASELINE,
                  text=f"IMPLEMENT is authorized against baseline `{BASELINE}`.")
    return ReleaseAuthorization(**(values | overrides))


def _refused(authorization, evidence=BaselineEvidence("main", True, True), wording=()) -> str:
    with pytest.raises(ReleasePreconditionRefused) as refused:
        admit_release_preconditions("WO-1", authorization, evidence, wording)
    assert isinstance(refused.value, ValueError)
    return refused.value.check


def test_release_preconditions_admit_only_a_complete_consistent_record() -> None:
    admit_release_preconditions("WO-1", _authorization(), BaselineEvidence("main", True, True), ("ordinary intent",))


@pytest.mark.parametrize(("authorization", "check"), [
    (None, "implementation-authorized"),
    (_authorization(record_ref=""), "implementation-authorized"),
    (_authorization(identity="WO-2"), "implementation-authorized"),
    (_authorization(authorizes_implement=False), "implementation-authorized"),
    (_authorization(baseline=None), "baseline-named"),
    (_authorization(baseline="main"), "baseline-named"),
    (_authorization(baseline="abc1234"), "baseline-named"),
])
def test_release_preconditions_refuse_missing_record_or_inexact_baseline(authorization, check) -> None:
    assert _refused(authorization) == check


def test_release_preconditions_refuse_unresolvable_or_unreachable_baseline() -> None:
    assert _refused(_authorization(), BaselineEvidence("main", False, False)) == "baseline-resolves"
    assert _refused(_authorization(), None) == "baseline-resolves"
    # The null revision never names a real commit, whatever a resolver answers.
    assert _refused(_authorization(baseline="0" * 40), BaselineEvidence("main", True, True)) == "baseline-resolves"
    assert _refused(_authorization(), BaselineEvidence("main", True, False)) == "baseline-reachable"


def test_release_preconditions_refuse_unsuperseded_denial_wording() -> None:
    assert _refused(_authorization(), wording=("fine", DENIAL)) == "authority-wording-consistent"
    assert _refused(_authorization(), wording=("implementation is unauthorized here",)) == "authority-wording-consistent"
    for denial in ("Implementation is not yet authorized.", "IMPLEMENT is not authorized", "Implementation not currently authorized",
                   "Release is refused pending review.", "release denied"):
        assert _refused(_authorization(), wording=(denial,)) == "authority-wording-consistent", denial
    # A record cannot supersede wording by naming itself.
    assert _refused(_authorization(superseding_record="issue#1:comment:1"), wording=(DENIAL,)) == "authority-wording-consistent"
    admit_release_preconditions("WO-1", _authorization(), BaselineEvidence("main", True, True),
                                ("READY does not itself authorize IMPLEMENT.", "Release rule: candidate compilation and READY are not release."))
    assert _refused(_authorization(text=DENIAL, superseding_record="issue#1:comment:2")) == "authority-wording-consistent"
    admit_release_preconditions("WO-1", _authorization(superseding_record="issue#1:comment:2"),
                                BaselineEvidence("main", True, True), (DENIAL,))


READINESS = "readiness/2232453f-9855-46cd-b155-34c11d88e43c/1/raw"
METADATA = {"wave": "6", "upstream_status": "READY", "source_version": "v1", "contract_location": "docs/p.md"}
# The fixed sequence: readiness evidence, metadata values, then the contract's string and string-tuple entries in
# canonical payload order (budget_policy, a mapping, carries none; empty dependencies add none).
WORDING = [READINESS, "6", "READY", "v1", "docs/p.md", "PY-02", "1", "Build a deterministic execution kernel",
           "SF-REQ-010", "pure-domain", "execution-coordination", "adapters", "python", "no automatic retry",
           "tests pass", "unit tests", "test output", "network", "independent read-back", "explicit-human-off",
           "Founder", "SWF-15", "AlienLogicLab/alienintent", "main@8a82e563", "publish candidate", "authority conflict"]


def test_release_wording_is_the_gate_wording_in_its_fixed_order() -> None:
    from alienintent.execution_coordination.application.release_admission import _wording
    from alienintent.execution_coordination.ports.work_management import ReadyWorkItem

    contract = valid_contract()
    assert list(release_wording(contract, READINESS, METADATA)) == WORDING
    assert list(release_wording(contract, READINESS, {})) == [READINESS, *WORDING[5:]]
    item = ReadyWorkItem("PY-02", 0, "repo", "profile", 1, (), contract, contract.content_digest, READINESS,
                         metadata=METADATA)
    assert list(_wording(item)) == WORDING
    assert list(_wording(replace(item, metadata=None))) == [READINESS, *WORDING[5:]]


def test_release_wording_carries_denials_from_each_branch() -> None:
    contract = valid_contract()
    admit_release_preconditions("WO-1", _authorization(), BaselineEvidence("main", True, True),
                                release_wording(contract, READINESS, METADATA))
    for wording in (release_wording(contract, DENIAL, METADATA),
                    release_wording(contract, READINESS, METADATA | {"wave": "release denied"}),
                    release_wording(valid_contract(intent=DENIAL), READINESS, METADATA),
                    release_wording(valid_contract(non_goals=("network", DENIAL)), READINESS, METADATA)):
        assert _refused(_authorization(), wording=wording) == "authority-wording-consistent"


def test_exhausted_attributable_budget_is_refused_by_the_existing_budget_check() -> None:
    contract = valid_contract(budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)))
    with pytest.raises(ValueError, match="budget"):
        admit_release({}, ReleaseRequest("exhausted", contract, contract.content_digest, frozenset(), frozenset({"python"}), {"attempts": 0}, "allocation"))
    assert admit_release({}, ReleaseRequest("allocated", contract, contract.content_digest, frozenset(), frozenset({"python"}), {"attempts": 3}, "allocation")).identity == "allocated"


def test_lifecycle_requires_readback_and_policy_verdict_then_rework_invalidates_acceptance() -> None:
    candidate = CandidateRef.archive("sha256:" + "a" * 64, "archive://x").with_independent_read_back()
    state = transition(ExecutionState.for_contract(valid_contract()), 0, "verify", candidate=candidate)
    state = transition(state, 1, "review")
    verdict = evaluate_verdict(EvidenceDefinition(frozenset({"tests"})), (Observation("tests", True, True),), worker_claimed_success=True)
    state = transition(state, 2, "accept", verdict=verdict)
    accepted = state
    reworked = transition(accepted, 3, "rework")

    assert reworked.stage is LifecycleStage.IMPLEMENT
    assert not reworked.accepted
    state = transition(reworked, 4, "verify", candidate=candidate)
    state = transition(state, 5, "review")
    state = transition(state, 6, "accept", verdict=verdict)
    assert transition(state, 7, "close", completed_closure_actions=frozenset({"publish candidate"})).stage is LifecycleStage.DONE
    with pytest.raises(LifecycleError):
        transition(ExecutionState(), 0, "verify")
    with pytest.raises(AuthorityBlocked):
        transition(ExecutionState(), 0, "authority-block")
    with pytest.raises(Cancelled):
        transition(ExecutionState(), 0, "cancel")
    with pytest.raises(LifecycleError):
        transition(state, 99, "close")
    with pytest.raises(LifecycleError, match="closure"):
        transition(accepted, 3, "close")
    assert transition(accepted, 3, "close", completed_closure_actions=frozenset({"publish candidate"})).stage is LifecycleStage.DONE


def test_scheduling_honours_priority_fifo_and_capacity_without_blocking_independent_work() -> None:
    items = (
        ScheduledItem("blocked", 0, "repo", "profile", 1, False),
        ScheduledItem("later", 2, "repo", "profile", 2, True),
        ScheduledItem("first", 1, "repo", "profile", 1, True),
    )
    selected = select_admissible(items, (), Capacity(global_limit=3, profile_mutating_limit=3, repository_mutating_limit=3))

    assert [item.identity for item in selected] == ["first", "later"]


def test_scheduling_honours_fifo_for_admissible_equal_and_absent_priorities() -> None:
    items = (
        ScheduledItem("equal-later", 2, "repo-a", "profile-a", 1, True),
        ScheduledItem("absent-later", 4, "repo-b", "profile-b", None, True),
        ScheduledItem("equal-first", 1, "repo-c", "profile-c", 1, True),
        ScheduledItem("absent-first", 3, "repo-d", "profile-d", None, True),
    )

    selected = select_admissible(items, (), Capacity(global_limit=4, profile_mutating_limit=1))

    assert [item.identity for item in selected] == ["equal-first", "equal-later", "absent-first", "absent-later"]


def test_scheduling_withholds_mutating_work_at_profile_and_repository_limits() -> None:
    active = (
        ScheduledItem("profile-active", 0, "repo-a", "profile-a", None, True),
        ScheduledItem("repository-active", 0, "repo-b", "profile-b", None, True),
    )
    items = (
        ScheduledItem("profile-blocked", 1, "repo-c", "profile-a", None, True),
        ScheduledItem("repository-blocked", 2, "repo-b", "profile-c", None, True),
        ScheduledItem("independent", 3, "repo-d", "profile-d", None, True),
    )

    selected = select_admissible(items, active, Capacity(global_limit=5, profile_mutating_limit=1, repository_mutating_limit=1))

    assert [item.identity for item in selected] == ["independent"]


def test_verifier_counts_globally_but_not_against_mutating_repository_slot() -> None:
    verifier = ScheduledItem("verify", 1, "repo", "profile", None, True, mutating=False)
    producer = ScheduledItem("implement", 2, "repo", "profile", None, True)
    assert [item.identity for item in select_admissible((verifier, producer), (), Capacity(global_limit=2, profile_mutating_limit=1))] == ["verify", "implement"]
    assert select_admissible((verifier, producer), (), Capacity(global_limit=1, profile_mutating_limit=1)) == (verifier,)


def test_worker_claim_without_required_trusted_evidence_cannot_accept() -> None:
    verdict = evaluate_verdict(EvidenceDefinition(frozenset({"tests"})), (), worker_claimed_success=True)
    assert verdict.kind is VerdictKind.REJECT


def test_untrusted_observation_cannot_satisfy_required_evidence() -> None:
    verdict = evaluate_verdict(
        EvidenceDefinition(frozenset({"tests"})),
        (Observation("tests", satisfied=True, trusted=False),),
        worker_claimed_success=True,
    )
    assert verdict.kind is VerdictKind.REJECT
