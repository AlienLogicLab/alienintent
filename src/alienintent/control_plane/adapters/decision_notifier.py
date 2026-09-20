"""Offline and Work Management projection notifiers."""

from __future__ import annotations

from alienintent.control_plane.ports.decision_notifier import DeliveryHealth, DecisionNotifier
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.ports.work_management import WorkManagement


class NoOpDecisionNotifier(DecisionNotifier):
    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        return DeliveryHealth(True, "offline notification intentionally suppressed")


class WorkManagementDecisionNotifier(DecisionNotifier):
    """Adapter around the PY-05 attributable-comment projection callback."""

    def __init__(self, work: WorkManagement) -> None:
        self._work = work

    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        try:
            receipt = self._work.project_decision_request(escalation)
        except Exception:
            return DeliveryHealth(False, "decision notification projection unavailable")
        return DeliveryHealth(receipt.confirmed, receipt.detail)
