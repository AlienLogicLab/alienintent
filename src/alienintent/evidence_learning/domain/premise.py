"""Neutral platform-isolation premise values; missing evidence is InfeasibleProof, never denial."""
from dataclasses import dataclass
from enum import StrEnum

from alienintent.evidence_learning.domain.refs import Ref


class IsolationObservable(StrEnum):
    """SF-REQ-014-AC-03 observables. Credential denial is deliberately not one of them."""
    POSITIVE_TARGET_ACCESS = "POSITIVE_TARGET_ACCESS"
    PROFILE_SCOPING = "PROFILE_SCOPING"
    OUT_OF_SCOPE_REJECTION = "OUT_OF_SCOPE_REJECTION"
    OUTSIDE_STATE_READBACK = "OUTSIDE_STATE_READBACK"


ISOLATION_OBSERVABLES = frozenset(IsolationObservable)
RETURN_TO_AUTHORITY = "return the premise to source authority"


@dataclass(frozen=True)
class PremiseObservation:
    observable: IsolationObservable
    target: str
    predicate: str
    observed: str
    satisfied: bool
    source_ref: Ref


@dataclass(frozen=True)
class RetainedPremiseEvidence:
    """What the outer boundary read under one pinned mapping: doctor state, observations, gaps."""
    premise_id: str
    mapping_ref: Ref | None
    target: str
    doctor_passed: bool
    doctor_ref: Ref | None
    observations: tuple[PremiseObservation, ...]
    unavailable: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "unavailable", tuple(self.unavailable))


@dataclass(frozen=True)
class PlatformIsolationPremise:
    premise_id: str
    target: str
    observations: tuple[PremiseObservation, ...]
    doctor_ref: Ref
    mapping_ref: Ref


@dataclass(frozen=True)
class InfeasibleProof:
    premise_id: str
    reason_code: str
    missing: tuple[str, ...]
    evidence_refs: tuple[Ref, ...] = ()
    required_action: str = RETURN_TO_AUTHORITY


def evaluate_isolation_premise(premise_id: str, target: str, requested: frozenset[str],
                               evidence: RetainedPremiseEvidence) -> PlatformIsolationPremise | InfeasibleProof:
    refs = tuple(dict.fromkeys(((evidence.mapping_ref,) if evidence.mapping_ref else ())
                               + tuple(o.source_ref for o in evidence.observations)))
    if evidence.mapping_ref is None:
        return InfeasibleProof(premise_id, "MAPPING_UNAVAILABLE", ("predicate-mapping",) + evidence.unavailable, refs)
    if evidence.premise_id != premise_id:
        return InfeasibleProof(premise_id, "PREMISE_MISMATCH", (evidence.premise_id,), refs)
    unachievable = sorted(set(requested) - {o.value for o in ISOLATION_OBSERVABLES})
    if unachievable:
        return InfeasibleProof(premise_id, "UNACHIEVABLE_PREMISE", tuple(unachievable), refs)
    omitted = sorted(o.value for o in ISOLATION_OBSERVABLES if o.value not in requested)
    if omitted:
        return InfeasibleProof(premise_id, "INCOMPLETE_PREMISE_REQUEST", tuple(omitted), refs)
    if not evidence.doctor_passed or evidence.doctor_ref is None:
        return InfeasibleProof(premise_id, "DOCTOR_EVIDENCE_UNAVAILABLE", ("installation-doctor",) + evidence.unavailable, refs)
    mismatched = sorted({o.target for o in evidence.observations if o.target != target} | ({evidence.target} - {target}))
    if mismatched:
        return InfeasibleProof(premise_id, "TARGET_MISMATCH", tuple(mismatched), refs)
    missing = sorted(o.value for o in ISOLATION_OBSERVABLES
                     if not any(obs.observable == o for obs in evidence.observations))
    if missing or evidence.unavailable:
        return InfeasibleProof(premise_id, "MISSING_PREMISE", tuple(missing) + evidence.unavailable, refs)
    unsatisfied = sorted({o.observable.value for o in evidence.observations if o.satisfied is not True})
    if unsatisfied:
        return InfeasibleProof(premise_id, "UNSATISFIED_PREMISE", tuple(unsatisfied), refs)
    return PlatformIsolationPremise(premise_id, target, evidence.observations, evidence.doctor_ref, evidence.mapping_ref)
