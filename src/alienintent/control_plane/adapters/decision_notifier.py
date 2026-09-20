"""Offline and Work Management projection notifiers."""

from __future__ import annotations

from collections.abc import Callable

from alienintent.control_plane.ports.decision_notifier import DeliveryHealth, DecisionNotifier
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired


class NoOpDecisionNotifier(DecisionNotifier):
    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        return DeliveryHealth(True, "offline notification intentionally suppressed")


class WorkManagementDecisionNotifier(DecisionNotifier):
    """Adapter around the PY-05 attributable-comment projection callback."""

    def __init__(self, comment: Callable[[HumanDecisionRequired], str]) -> None:
        self._comment = comment

    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        try:
            receipt = self._comment(escalation)
        except Exception:
            return DeliveryHealth(False, "decision notification projection unavailable")
        return DeliveryHealth(bool(receipt), "confirmed" if receipt else "decision notification projection unconfirmed")
