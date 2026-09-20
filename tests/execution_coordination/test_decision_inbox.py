"""Executable PY-07 proofs for authority escalation and durable re-admission."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.escalation import (
    DecisionConflict,
    DecisionSubmission,
    HumanDecisionRequired,
    SupersededDecision,
)
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.control_plane.adapters.decision_notifier import WorkManagementDecisionNotifier
from tests.execution_coordination.test_factory_coordinator import MemoryWorkManagement, ScriptedWorker, _item


class EscalatingWorker(ScriptedWorker):
    def __init__(self, artifacts: LocalArtifactStore, outcomes: dict[str, list[str]], escalation: HumanDecisionRequired) -> None:
        super().__init__(artifacts, outcomes, durable=True)
        self.escalation = escalation

    def start(self, invocation, context, grants, budget):
        if self.outcomes[invocation.work_identity][0] == "authority-block":
            self.outcomes[invocation.work_identity].pop(0)
            from alienintent.execution_coordination.ports.worker_provider import WorkerOutcome
            self.dispatched.append(invocation.work_identity)
            outcome = WorkerOutcome.authority_block(self.escalation)
            self.observed[invocation.correlation_id] = outcome
            return outcome
        return super().start(invocation, context, grants, budget)


def _escalation(version: int = 0) -> HumanDecisionRequired:
    return HumanDecisionRequired(
        profile="offline",
        project="AlienLogicLab/alienintent",
        work_item="blocked",
        biu_version=version,
        decision="Approve the external reconciliation strategy",
        reason="The external effect outcome is unknown.",
        options=("reconcile", "cancel"),
        tradeoffs=("reconcile preserves completed external work",),
        recommendation="reconcile",
        affected_requirements=("SF-REQ-006",),
        affected_architecture=("FD-05",),
        cost_of_waiting="repository capacity remains unavailable to conflicting work",
        authorizations=("reconcile authorizes one read-back", "cancel authorizes cancellation"),
    )


def test_authority_decision_is_durable_scoped_and_re_admits_through_the_loop(tmp_path: Path) -> None:
    """PY-07 AC 1-9: an escalation blocks its closure, not the factory, then resumes once."""
    items = [
        _item("blocked", 0, 1),
        _item("dependent", 1, 2, ("blocked",)),
        _item("independent", 2, 3),
    ]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    worker = EscalatingWorker(artifacts, {"blocked": ["authority-block", "success"], "dependent": ["success"], "independent": ["success"]}, _escalation())
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    first = coordinator.start()

    assert first.dispatched == ("blocked", "independent")
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.state("dependent").outcome == "blocked-by-authority"
    assert coordinator.state("independent").stage is LifecycleStage.DONE
    assert store.recovery_reservations("offline") == ()
    inbox = DecisionInbox(store, coordinator, "offline")
    open_decision = inbox.list_open()
    assert open_decision == (_escalation(),)
    assert inbox.show("blocked") == _escalation()
    command = DecisionSubmission("morty", "SWF-21", "blocked", 0, 0, "decision-1", "reconcile")

    recorded = inbox.submit(command)

    assert recorded.event.work_item == "blocked"
    assert inbox.submit(command) == recorded
    with pytest.raises(DecisionConflict):
        inbox.submit(replace(command, choice="cancel"))
    with pytest.raises(SupersededDecision):
        inbox.submit(replace(command, idempotency_key="stale", biu_version=1))
    assert coordinator.state("blocked").stage is LifecycleStage.DONE
    assert coordinator.state("dependent").stage is LifecycleStage.DONE
    restarted = DecisionInbox(SQLiteOperationalStore(tmp_path / "operational.sqlite"), coordinator, "offline")
    assert restarted.show("blocked") == recorded
    assert restarted.list_open() == ()


def test_notification_failure_is_delivery_health_not_an_execution_failure(tmp_path: Path) -> None:
    """PY-07 AC 9: the notifier is an adapter and cannot change execution truth."""
    item = _item("blocked", 0, 1)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = EscalatingWorker(artifacts, {"blocked": ["authority-block"]}, _escalation())
    notifier = WorkManagementDecisionNotifier(lambda _: (_ for _ in ()).throw(RuntimeError("fixture delivery failure")))
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "operational.sqlite"), MemoryWorkManagement([item]), worker, artifacts, "offline", notifier=notifier)

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.delivery_health["blocked"].delivered is False
