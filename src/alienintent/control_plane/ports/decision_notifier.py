"""Non-authoritative notification boundary for human decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired


@dataclass(frozen=True)
class DeliveryHealth:
    delivered: bool
    detail: str


class DecisionNotifier(Protocol):
    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth: ...
