"""Domain values for a durable, decision-ready authority escalation."""

from __future__ import annotations

from dataclasses import dataclass


class DecisionConflict(ValueError):
    """An idempotency key was re-used with a different decision."""


class SupersededDecision(ValueError):
    """A decision targets a version that is no longer current."""


@dataclass(frozen=True)
class HumanDecisionRequired:
    profile: str
    project: str
    work_item: str
    biu_version: int
    decision: str
    reason: str
    options: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    recommendation: str
    affected_requirements: tuple[str, ...]
    affected_architecture: tuple[str, ...]
    cost_of_waiting: str
    authorizations: tuple[str, ...]

    def __post_init__(self) -> None:
        values = (self.profile, self.project, self.work_item, self.decision, self.reason, self.recommendation, self.cost_of_waiting)
        sequences = (self.options, self.tradeoffs, self.affected_requirements, self.affected_architecture, self.authorizations)
        if self.biu_version < 0 or any(not value for value in values) or any(not group or any(not entry for entry in group) for group in sequences):
            raise ValueError("human decision escalation requires complete decision-ready context")


@dataclass(frozen=True)
class DecisionSubmission:
    actor: str
    authority_reference: str
    work_item: str
    biu_version: int
    expected_version: int
    idempotency_key: str
    choice: str

    def __post_init__(self) -> None:
        if self.biu_version < 0 or self.expected_version < 0 or any(not value for value in (self.actor, self.authority_reference, self.work_item, self.idempotency_key, self.choice)):
            raise ValueError("decision submission requires attribution, version and idempotency")


@dataclass(frozen=True)
class DecisionRecorded:
    work_item: str
    biu_version: int
    idempotency_key: str
    actor: str


@dataclass(frozen=True)
class DecisionRecord:
    submission: DecisionSubmission
    event: DecisionRecorded
