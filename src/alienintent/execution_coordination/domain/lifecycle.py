"""Version-guarded execution lifecycle after explicit release."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from .custody import CandidateRef
from .contract import BiuContract
from .verdict import Verdict, VerdictKind


class LifecycleStage(StrEnum):
    IMPLEMENT = "IMPLEMENT"
    VERIFY = "VERIFY"
    REVIEW = "REVIEW"
    ACCEPT = "ACCEPT"
    DONE = "DONE"


class LifecycleError(ValueError):
    pass


class VersionConflictError(LifecycleError):
    pass


class AuthorityBlocked(LifecycleError):
    pass


class Cancelled(LifecycleError):
    pass


@dataclass(frozen=True)
class ExecutionState:
    stage: LifecycleStage = LifecycleStage.IMPLEMENT
    version: int = 0
    candidate: CandidateRef | None = None
    accepted: bool = False
    completed_closure_actions: frozenset[str] = frozenset()
    contract: BiuContract | None = None
    # Cycle counts recorded with the transitions; None is unknown and stays unknown.
    implement_cycles: int | None = None
    verify_cycles: int | None = None

    @classmethod
    def for_contract(cls, contract: BiuContract) -> ExecutionState:
        return cls(contract=contract, implement_cycles=0, verify_cycles=0)


def _plus_one(count: int | None) -> int | None:
    return None if count is None else count + 1


def transition(state: ExecutionState, expected_version: int, action: str, *, candidate: CandidateRef | None = None, verdict: Verdict | None = None, completed_closure_actions: frozenset[str] = frozenset()) -> ExecutionState:
    if state.version != expected_version:
        raise VersionConflictError("expected version does not match current execution state")
    if action == "authority-block":
        raise AuthorityBlocked("execution is blocked by authority")
    if action == "cancel":
        raise Cancelled("execution was cancelled")
    if action == "rework":
        if state.stage not in {LifecycleStage.VERIFY, LifecycleStage.REVIEW, LifecycleStage.ACCEPT}:
            raise LifecycleError("rework is not permitted from this stage")
        return replace(
            state,
            stage=LifecycleStage.IMPLEMENT,
            version=state.version + 1,
            candidate=None,
            accepted=False,
            completed_closure_actions=frozenset(),
            implement_cycles=_plus_one(state.implement_cycles),
        )
    if action == "verify" and state.stage is LifecycleStage.IMPLEMENT:
        if candidate is None or not candidate.verify_admissible:
            raise LifecycleError("VERIFY requires a CandidateRef with independent read-back")
        return replace(state, stage=LifecycleStage.VERIFY, version=state.version + 1, candidate=candidate,
                       verify_cycles=_plus_one(state.verify_cycles))
    if action == "review" and state.stage is LifecycleStage.VERIFY:
        return replace(state, stage=LifecycleStage.REVIEW, version=state.version + 1)
    if action == "accept" and state.stage is LifecycleStage.REVIEW:
        if verdict is None or verdict.kind is not VerdictKind.ACCEPT:
            raise LifecycleError("ACCEPT requires an admissible policy verdict")
        return replace(state, stage=LifecycleStage.ACCEPT, version=state.version + 1, accepted=True)
    if action == "close" and state.stage is LifecycleStage.ACCEPT:
        if state.contract is None:
            raise LifecycleError("DONE requires a bound execution contract")
        if not set(state.contract.required_closure_actions).issubset(completed_closure_actions):
            raise LifecycleError("DONE requires all required closure actions")
        return replace(state, stage=LifecycleStage.DONE, version=state.version + 1, completed_closure_actions=completed_closure_actions)
    raise LifecycleError("transition is not permitted by lifecycle semantics")
