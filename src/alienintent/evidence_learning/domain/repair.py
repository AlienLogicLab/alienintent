"""Repair preservation (014-repair-preservation): prior proof is replayed or authorizedly replaced."""
from dataclasses import dataclass
from enum import StrEnum

from alienintent.evidence_learning.domain.proof_plan import PlanHold, PredicateKind, ProofPlan

RETURN_TO_REPAIR = "replay every preserved prior obligation, or obtain authorized supersession with passing replacement proof"


class ReplayStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class RepairAccepted:
    prior_plan_digest: str
    current_plan_digest: str
    preserved: tuple[str, ...]
    superseded: tuple[str, ...]


_REASONS = {None: "PRIOR_PROOF_DROPPED", ReplayStatus.SKIPPED: "PRIOR_PROOF_SKIPPED",
            ReplayStatus.FAILED: "PRIOR_PROOF_FAILED"}


def evaluate_repair(prior: ProofPlan, current: ProofPlan, replay: dict[str, ReplayStatus]) -> RepairAccepted | PlanHold:
    if current.requirement_id != prior.requirement_id:
        return PlanHold("REVISION_MISMATCH", (current.requirement_id,), required_action=RETURN_TO_REPAIR)
    replacements = {s.prior_obligation_id: s for s in current.superseded}
    preserved, superseded = [], []
    for old in prior.obligations:
        kept = current.obligation(old.obligation_id)
        if old.obligation_id in replacements:
            replacement = replacements[old.obligation_id].replacement_obligation_id
            if current.obligation(replacement) is None or replay.get(replacement) is not ReplayStatus.PASSED:
                return PlanHold("REPLACEMENT_PROOF_MISSING", (old.obligation_id, replacement), required_action=RETURN_TO_REPAIR)
            superseded.append(old.obligation_id)
        elif kept is None or kept.revision != old.revision:
            return PlanHold("PRIOR_OBLIGATION_DROPPED", (old.obligation_id,), required_action=RETURN_TO_REPAIR)
        elif old.predicate.kind is PredicateKind.JUDGMENT:
            preserved.append(old.obligation_id)  # Same reviewer, inputs and decision record; not replayed.
        elif replay.get(old.obligation_id) is not ReplayStatus.PASSED:
            reason = _REASONS.get(replay.get(old.obligation_id), "PRIOR_PROOF_FAILED")
            return PlanHold(reason, (old.obligation_id,), required_action=RETURN_TO_REPAIR)
        else:
            preserved.append(old.obligation_id)
    return RepairAccepted(prior.digest, current.digest, tuple(preserved), tuple(superseded))
