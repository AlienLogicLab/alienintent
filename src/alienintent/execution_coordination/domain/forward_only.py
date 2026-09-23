"""Small, deterministic controls for forward-only factory operation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from alienintent.execution_coordination.ports.operational_store import OperationalStore


class AuthorityQuestion(StrEnum):
    MACHINERY_REPAIR = "machinery-repair"
    TEST_REPAIR = "test-repair"
    COMPATIBILITY_REPAIR = "compatibility-repair"
    PRODUCT_INTENT = "product-intent"
    MATERIAL_ARCHITECTURE = "material-architecture"
    SECURITY_RISK_ACCEPTANCE = "security-risk-acceptance"
    BUDGET_LIMIT = "budget-limit"
    EXTERNAL_COMMITMENT = "external-commitment"
    LIVE_OPERATION = "live-operation"


class AuthorityRoute(StrEnum):
    DELEGATED_ENGINEERING = "delegated-engineering"
    FOUNDER_DECISION = "founder-decision"


def route_authority(question: AuthorityQuestion) -> AuthorityRoute:
    """Route already-decided engineering work without manufacturing escalation."""
    if question in {
        AuthorityQuestion.MACHINERY_REPAIR,
        AuthorityQuestion.TEST_REPAIR,
        AuthorityQuestion.COMPATIBILITY_REPAIR,
    }:
        return AuthorityRoute.DELEGATED_ENGINEERING
    return AuthorityRoute.FOUNDER_DECISION


class RecheckDisposition(StrEnum):
    REUSE = "reuse"
    TARGETED_RECHECK = "targeted-recheck"
    FULL_VALIDATION = "full-validation"


@dataclass(frozen=True)
class InvalidationAssessment:
    disposition: RecheckDisposition
    evidence_to_reuse: str
    affected_boundaries: tuple[str, ...] = ()


def assess_invalidation(*, completed_evidence: str, declared_boundaries: tuple[str, ...], changed_boundaries: tuple[str, ...], impact_bounded: bool = True) -> InvalidationAssessment:
    """Recheck only declared assumptions that a change actually intersects."""
    if not completed_evidence or not declared_boundaries:
        raise ValueError("completed evidence and declared boundaries are required")
    if not impact_bounded:
        return InvalidationAssessment(RecheckDisposition.FULL_VALIDATION, completed_evidence)
    affected = tuple(
        boundary for boundary in declared_boundaries
        if any(_intersects(boundary, changed) for changed in changed_boundaries)
    )
    return InvalidationAssessment(
        RecheckDisposition.TARGETED_RECHECK if affected else RecheckDisposition.REUSE,
        completed_evidence,
        affected,
    )


def _intersects(declared: str, changed: str) -> bool:
    return declared == changed or declared.startswith(f"{changed}/") or changed.startswith(f"{declared}/")


class LessonDisposition(StrEnum):
    MECHANICAL_ENFORCEMENT = "MECHANICAL_ENFORCEMENT"
    DETERMINISTIC_PREFLIGHT = "DETERMINISTIC_PREFLIGHT"
    JUDGMENT_ONLY = "JUDGMENT_ONLY"


@dataclass(frozen=True)
class LessonClosure:
    failure_class: str
    disposition: LessonDisposition | None
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.failure_class or self.disposition is None:
            raise ValueError("a general lesson requires exactly one disposition")
        if not self.evidence or any(not item for item in self.evidence):
            raise ValueError("a general lesson requires evidence")
        if self.disposition is LessonDisposition.MECHANICAL_ENFORCEMENT:
            if not any(item.startswith("enforcement:") for item in self.evidence):
                raise ValueError("mechanical enforcement requires an enforcing mechanism")
            if not any(item.startswith("proven-red:") for item in self.evidence):
                raise ValueError("mechanical enforcement requires proven-red evidence")
        if self.disposition is LessonDisposition.DETERMINISTIC_PREFLIGHT and not any(item.startswith("preflight:") for item in self.evidence):
            raise ValueError("deterministic preflight requires check evidence")
        if self.disposition is LessonDisposition.DETERMINISTIC_PREFLIGHT and not any(item.startswith("proven-red:") for item in self.evidence):
            raise ValueError("deterministic preflight requires proven-red evidence")
        if self.disposition is LessonDisposition.JUDGMENT_ONLY and not any(item.startswith("judgment-owner:") for item in self.evidence):
            raise ValueError("judgment-only closure requires a judgment owner")
        if self.disposition is LessonDisposition.JUDGMENT_ONLY and not any(item.startswith("judgment-rationale:") for item in self.evidence):
            raise ValueError("judgment-only closure requires a mechanization rationale")


@dataclass(frozen=True)
class FailureClassRecurrence:
    status: str
    failure_class: str
    enforcement_evidence: tuple[str, ...]


class FailureClassRegister:
    """Keeps a repeated mechanized class visible as a control regression."""

    def __init__(self) -> None:
        self._closed: dict[str, LessonClosure] = {}

    def close(self, closure: LessonClosure) -> None:
        self._closed[closure.failure_class] = closure

    def record_recurrence(self, failure_class: str, evidence: str) -> FailureClassRecurrence:
        if not failure_class or not evidence:
            raise ValueError("recurrence requires a failure class and evidence")
        closure = self._closed.get(failure_class)
        if closure and closure.disposition in {LessonDisposition.MECHANICAL_ENFORCEMENT, LessonDisposition.DETERMINISTIC_PREFLIGHT}:
            return FailureClassRecurrence("REGRESSION", failure_class, closure.evidence)
        return FailureClassRecurrence("NEW_LESSON", failure_class, (evidence,))


class FailureClassLedger:
    """Durable closure and recurrence records backed by the existing state store."""

    def __init__(self, store: OperationalStore, profile: str) -> None:
        self._store = store
        self._profile = profile

    def close(self, closure: LessonClosure) -> None:
        aggregate = self._aggregate(closure.failure_class)
        version, prior = self._store.read_state(self._profile, aggregate)
        if prior:
            same_closure = (
                prior.get("failure_class") == closure.failure_class
                and prior.get("disposition") == closure.disposition
                and prior.get("evidence") == list(closure.evidence)
            )
            if same_closure:
                return
            raise ValueError("changing a closed failure class requires explicit supersession")
        self._store.commit(self._profile, aggregate, version, {
            "failure_class": closure.failure_class,
            "disposition": closure.disposition,
            "evidence": list(closure.evidence),
            "recurrences": list(prior.get("recurrences", [])),
        })

    def record_recurrence(self, failure_class: str, evidence: str) -> FailureClassRecurrence:
        aggregate = self._aggregate(failure_class)
        version, raw = self._store.read_state(self._profile, aggregate)
        if not raw:
            return FailureClassRecurrence("NEW_LESSON", failure_class, (evidence,))
        closure = LessonClosure(
            str(raw["failure_class"]),
            LessonDisposition(str(raw["disposition"])),
            tuple(str(item) for item in raw["evidence"]),
        )
        register = FailureClassRegister()
        register.close(closure)
        recurrence = register.record_recurrence(failure_class, evidence)
        self._store.commit(self._profile, aggregate, version, raw | {
            "recurrences": [*raw.get("recurrences", []), {"evidence": evidence, "status": recurrence.status}],
        })
        return recurrence

    @staticmethod
    def _aggregate(failure_class: str) -> str:
        return f"failure-class:{failure_class}"
