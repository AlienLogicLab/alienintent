"""Policy evaluation separates evidence definitions, observations and verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VerdictKind(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


@dataclass(frozen=True)
class EvidenceDefinition:
    required_ids: frozenset[str]


@dataclass(frozen=True)
class Observation:
    evidence_id: str
    trusted: bool
    satisfied: bool


@dataclass(frozen=True)
class Verdict:
    kind: VerdictKind
    reason: str


def evaluate_verdict(definition: EvidenceDefinition, observations: tuple[Observation, ...], *, worker_claimed_success: bool) -> Verdict:
    proven = {item.evidence_id for item in observations if item.trusted and item.satisfied}
    missing = definition.required_ids - proven
    if missing:
        return Verdict(VerdictKind.REJECT, "required trusted evidence is missing")
    return Verdict(VerdictKind.ACCEPT, "policy accepted required trusted evidence")
