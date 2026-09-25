"""Executable PY-07 proofs for authority escalation and durable re-admission."""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

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
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
from alienintent.control_plane.adapters.decision_notifier import WorkManagementDecisionNotifier
from alienintent.control_plane.adapters.decision_notifier import NoOpDecisionNotifier
from alienintent.execution_coordination.ports.operational_store import Effect, ReservationRejected
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
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
            outcome = WorkerOutcome.authority_block(replace(self.escalation, work_item=invocation.work_identity))
            self.observed[invocation.correlation_id] = outcome
            # The coordinator admits only an outcome it can durably read back.
            path = self._path(invocation.correlation_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"kind": outcome.kind, "candidate": None}))
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
    class FailingProjection:
        def project_decision_request(self, escalation: HumanDecisionRequired):
            raise RuntimeError("fixture delivery failure")

    item = _item("blocked", 0, 1)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = EscalatingWorker(artifacts, {"blocked": ["authority-block"]}, _escalation())
    notifier = WorkManagementDecisionNotifier(FailingProjection())
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "operational.sqlite"), MemoryWorkManagement([item]), worker, artifacts, "offline", notifier=notifier)

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.delivery_health["blocked"].delivered is False


def test_admission_authority_block_opens_a_decidable_request_and_resumes(tmp_path: Path) -> None:
    """Scope §2: admission refusal is a durable, recoverable authority escalation."""
    item = _item("needs-authority", 0, 1)
    contract = replace(item.contract, required_capabilities=("network",))
    item = replace(item, contract=contract, readiness_digest=contract.content_digest)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    worker = ScriptedWorker(artifacts, {"needs-authority": ["success"]})
    coordinator = FactoryCoordinator(store, MemoryWorkManagement([item]), worker, artifacts, "offline")

    assert coordinator.start().authority_blocked == ("needs-authority",)
    inbox = DecisionInbox(store, coordinator, "offline")
    request = inbox.show("needs-authority")
    assert isinstance(request, HumanDecisionRequired)
    assert request.work_item == "needs-authority"
    assert request.options == ("authorize", "defer")

    inbox.submit(DecisionSubmission("morty", "SWF-21", "needs-authority", request.biu_version, request.biu_version, "grant-network", "authorize"))

    assert coordinator.state("needs-authority").stage is LifecycleStage.DONE


def test_bare_worker_authority_block_is_escalated_scoped_and_decidable(tmp_path: Path) -> None:
    """The production provider shape carries only an authority-block outcome."""
    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",)), _item("independent", 2, 3)]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    worker = ScriptedWorker(artifacts, {"blocked": ["authority-block", "success"], "dependent": ["success"], "independent": ["success"]})
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert coordinator.state("dependent").outcome == "blocked-by-authority"
    request = DecisionInbox(store, coordinator, "offline").show("blocked")
    assert isinstance(request, HumanDecisionRequired)
    DecisionInbox(store, coordinator, "offline").submit(
        DecisionSubmission("morty", "SWF-21", "blocked", request.biu_version, request.biu_version, "bare-worker-authorize", "authorize")
    )
    assert coordinator.state("blocked").stage is LifecycleStage.DONE
    assert coordinator.state("dependent").stage is LifecycleStage.DONE


def test_recovery_reconstructs_a_bare_worker_authority_escalation(tmp_path: Path) -> None:
    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",))]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    correlation = "launch:blocked:0"
    store.acquire("offline", "repository", "repo", correlation)
    state = FactoryCoordinator._encode(ExecutionState.for_contract(items[0].contract))
    store.commit_with_effect("offline", "factory:blocked", 0, state, correlation, {"correlation": correlation, "work": "blocked"})
    worker = ScriptedWorker(artifacts, {"blocked": ["authority-block", "success"], "dependent": ["success"]}, durable=True)
    worker.start(WorkerInvocation("blocked", correlation), items[0].contract, frozenset(), items[0].contract.budget_policy)
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    coordinator.start()

    request = DecisionInbox(store, coordinator, "offline").show("blocked")
    assert isinstance(request, HumanDecisionRequired)
    assert coordinator.state("dependent").outcome == "blocked-by-authority"
    DecisionInbox(store, coordinator, "offline").submit(
        DecisionSubmission("morty", "SWF-21", "blocked", request.biu_version, request.biu_version, "recover-bare-authorize", "authorize")
    )
    assert coordinator.state("blocked").stage is LifecycleStage.DONE
    assert coordinator.state("dependent").stage is LifecycleStage.DONE


def test_recovery_reconstructs_an_authority_escalation_recorded_before_a_crash(tmp_path: Path) -> None:
    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",))]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    correlation = "launch:blocked:0"
    store.acquire("offline", "repository", "repo", correlation)
    state = ExecutionState.for_contract(items[0].contract)
    store.commit_with_effect("offline", "factory:blocked", 0, FactoryCoordinator._encode(state), correlation, {"correlation": correlation, "work": "blocked"})
    store.claim_effect("offline", correlation)
    worker = ScriptedWorker(artifacts, {"blocked": ["authority-block", "success"], "dependent": ["success"]}, durable=True)
    worker.start(WorkerInvocation("blocked", correlation), items[0].contract, frozenset(), items[0].contract.budget_policy)
    store.confirm_effect("offline", correlation, "outcome:authority-block")
    interrupted = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")
    assert interrupted._record_result(items[0], state, correlation, "authority-block")
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    coordinator.start()

    assert isinstance(DecisionInbox(store, coordinator, "offline").show("blocked"), HumanDecisionRequired)
    assert coordinator.state("dependent").outcome == "blocked-by-authority"


def test_defer_keeps_an_admission_escalation_open_for_later_authorization(tmp_path: Path) -> None:
    item = _item("needs-authority", 0, 1)
    contract = replace(item.contract, required_capabilities=("network",))
    item = replace(item, contract=contract, readiness_digest=contract.content_digest)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    coordinator = FactoryCoordinator(store, MemoryWorkManagement([item]), ScriptedWorker(artifacts, {"needs-authority": ["success"]}), artifacts, "offline")
    coordinator.start()
    inbox = DecisionInbox(store, coordinator, "offline")
    request = inbox.show("needs-authority")
    assert isinstance(request, HumanDecisionRequired)

    deferred = inbox.submit(DecisionSubmission("morty", "SWF-21", "needs-authority", 0, 0, "defer-admission", "defer"))

    assert deferred.submission.choice == "defer"
    assert inbox.show("needs-authority") == request
    inbox.submit(DecisionSubmission("morty", "SWF-21", "needs-authority", 0, 0, "authorize-admission", "authorize"))
    assert coordinator.state("needs-authority").stage is LifecycleStage.DONE


def test_defer_keeps_a_real_unknown_effect_open_for_later_authorization(tmp_path: Path) -> None:
    item = _item("blocked", 0, 1)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    correlation = "launch:blocked:0"
    store.acquire("offline", "repository", "repo", correlation)
    state = FactoryCoordinator._encode(ExecutionState.for_contract(item.contract))
    store.commit_with_effect("offline", "factory:blocked", 0, state, correlation, {"correlation": correlation, "work": "blocked"})
    store.claim_effect("offline", correlation)
    coordinator = FactoryCoordinator(store, MemoryWorkManagement([item]), ScriptedWorker(artifacts, {"blocked": ["success"]}), artifacts, "offline")
    coordinator.start()
    inbox = DecisionInbox(store, coordinator, "offline")
    request = inbox.show("blocked")
    assert isinstance(request, HumanDecisionRequired)

    inbox.submit(DecisionSubmission("morty", "SWF-21", "blocked", 0, 0, "defer-unknown", "defer"))

    assert inbox.show("blocked") == request
    inbox.submit(DecisionSubmission("morty", "SWF-21", "blocked", 0, 0, "authorize-unknown", "authorize"))
    assert coordinator.state("blocked").stage is LifecycleStage.DONE


def test_cancelled_escalation_and_its_closure_stay_terminal_when_another_decision_re_admits_the_loop(tmp_path: Path) -> None:
    """A later decision must not revive cancellation or strand its closure."""
    items = [
        _item("blocked", 0, 1),
        _item("dependent", 1, 2, ("blocked",)),
        _item("other", 2, 3),
    ]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    worker = EscalatingWorker(
        artifacts,
        {"blocked": ["authority-block", "success"], "dependent": ["success"], "other": ["authority-block", "success"]},
        _escalation(),
    )
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")
    coordinator.start()
    inbox = DecisionInbox(store, coordinator, "offline")
    blocked = inbox.show("blocked")
    other = inbox.show("other")
    assert isinstance(blocked, HumanDecisionRequired)
    assert isinstance(other, HumanDecisionRequired)

    inbox.submit(
        DecisionSubmission("morty", "SWF-21", "blocked", blocked.biu_version, blocked.biu_version, "cancel-worker", "cancel")
    )
    inbox.submit(
        DecisionSubmission("morty", "SWF-21", "other", other.biu_version, other.biu_version, "reconcile-other", "reconcile")
    )

    assert coordinator.state("blocked").outcome == "cancelled-by-decision"
    assert coordinator.state("dependent").outcome == "cancelled-by-decision"
    assert coordinator.state("other").stage is LifecycleStage.DONE
    assert worker.dispatched == ["blocked", "other", "other"]


def test_noop_notifier_leaves_the_decision_inbox_usable(tmp_path: Path) -> None:
    item = _item("blocked", 0, 1)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    coordinator = FactoryCoordinator(store, MemoryWorkManagement([item]), EscalatingWorker(artifacts, {"blocked": ["authority-block"]}, _escalation()), artifacts, "offline", notifier=NoOpDecisionNotifier())

    coordinator.start()

    assert DecisionInbox(store, coordinator, "offline").show("blocked") == _escalation()
    assert coordinator.delivery_health["blocked"].delivered is True


def test_work_management_notifier_projects_a_recorded_decision_fixture() -> None:
    projected: list[HumanDecisionRequired] = []

    class RecordedProjection:
        def project_decision_request(self, escalation: HumanDecisionRequired):
            from alienintent.execution_coordination.ports.work_management import ProjectionReceipt
            projected.append(escalation)
            return ProjectionReceipt(escalation.work_item, escalation.biu_version, True, "recorded-fixture comment read back")

    notifier = WorkManagementDecisionNotifier(RecordedProjection())

    assert notifier.notify(_escalation()).delivered
    assert projected == [_escalation()]


def test_decision_inbox_is_implemented_in_the_control_plane_application() -> None:
    assert DecisionInbox.__module__ == "alienintent.control_plane.application.decision_inbox"


def test_retry_applies_a_decision_persisted_before_an_interrupted_re_admission(tmp_path: Path) -> None:
    class InterruptedDecisionProjectionStore(SQLiteOperationalStore):
        fail_work_projection = True

        def commit(self, profile, aggregate, expected_version, state):
            if aggregate == "decision:blocked" and self.fail_work_projection:
                self.fail_work_projection = False
                raise RuntimeError("simulated interruption between decision writes")
            return super().commit(profile, aggregate, expected_version, state)

    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = InterruptedDecisionProjectionStore(tmp_path / "operational.sqlite")
    worker = EscalatingWorker(artifacts, {"blocked": ["authority-block", "success"]}, _escalation())
    coordinator = FactoryCoordinator(store, MemoryWorkManagement([_item("blocked", 0, 1)]), worker, artifacts, "offline")
    coordinator.start()
    command = DecisionSubmission("morty", "SWF-21", "blocked", 0, 0, "interrupted-decision", "reconcile")

    with pytest.raises(RuntimeError, match="simulated interruption between decision writes"):
        DecisionInbox(store, coordinator, "offline").submit(command)

    recovered = DecisionInbox(store, coordinator, "offline")
    assert recovered.submit(command).submission == command
    assert recovered.show("blocked").submission == command
    assert coordinator.state("blocked").stage is LifecycleStage.DONE


def test_unresolved_effect_is_decidable_and_re_admits_its_scoped_closure(tmp_path: Path) -> None:
    class UnknownEffectStore(SQLiteOperationalStore):
        unresolved = True

        def unresolved_effects(self, profile: str):
            if self.unresolved:
                return (Effect("unknown-launch", "factory:blocked", {"work": "blocked"}),)
            return ()

    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",)), _item("independent", 2, 3)]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = UnknownEffectStore(tmp_path / "operational.sqlite")
    store.unresolved = True
    assert store.unresolved_effects("offline")
    coordinator = FactoryCoordinator(
        store, MemoryWorkManagement(items),
        ScriptedWorker(artifacts, {"blocked": ["success", "success"], "dependent": ["success"], "independent": ["success"]}),
        artifacts, "offline",
    )

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.state("dependent").outcome == "blocked-by-authority"
    assert coordinator.state("independent").stage is LifecycleStage.DONE
    assert store.recovery_reservations("offline") == ()
    inbox = DecisionInbox(store, coordinator, "offline")
    request = inbox.show("blocked")
    assert isinstance(request, HumanDecisionRequired)
    assert "unknown" in request.reason

    store.unresolved = False
    inbox.submit(DecisionSubmission("morty", "SWF-21", "blocked", request.biu_version, request.biu_version, "reconcile-unknown", "authorize"))

    assert coordinator.state("blocked").stage is LifecycleStage.DONE
    assert coordinator.state("dependent").stage is LifecycleStage.DONE


def test_real_unknown_effect_recovers_as_a_scoped_decidable_authority_block(tmp_path: Path) -> None:
    """FD-05: a real unknown effect parks its closure without stopping unrelated work."""
    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",)), _item("independent", 2, 3)]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    correlation = "launch:blocked:0"
    store.acquire("offline", "repository", "repo", correlation)
    state = FactoryCoordinator._encode(ExecutionState.for_contract(items[0].contract))
    store.commit_with_effect("offline", "factory:blocked", 0, state, correlation, {"correlation": correlation, "work": "blocked"})
    store.claim_effect("offline", correlation)
    assert store.unresolved_effects("offline")
    worker = ScriptedWorker(artifacts, {"blocked": ["success"], "dependent": ["success"], "independent": ["success"]})
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert summary.dispatched == ("independent",)
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.state("dependent").outcome == "blocked-by-authority"
    assert coordinator.state("independent").stage is LifecycleStage.DONE
    assert store.recovery_reservations("offline") == ()
    request = DecisionInbox(store, coordinator, "offline").show("blocked")
    assert isinstance(request, HumanDecisionRequired)
    version, blocked = store.read_state("offline", "factory:blocked")
    with pytest.raises(ReservationRejected, match="unresolved effect"):
        store.commit("offline", "factory:blocked", version, blocked)

    DecisionInbox(store, coordinator, "offline").submit(
        DecisionSubmission("morty", "SWF-21", "blocked", request.biu_version, request.biu_version, "reconcile-real-unknown", "authorize")
    )

    assert coordinator.state("blocked").stage is LifecycleStage.DONE
    assert coordinator.state("dependent").stage is LifecycleStage.DONE


def test_lost_effect_confirmation_parks_the_running_item_without_stopping_the_factory(tmp_path: Path) -> None:
    """FD-05: uncertainty during a live run uses the same scoped escalation path."""
    class LostConfirmationStore(SQLiteOperationalStore):
        lose_confirmation = True

        def confirm_effect(self, profile: str, effect_id: str, receipt: str) -> None:
            if self.lose_confirmation:
                self.lose_confirmation = False
                raise ReservationRejected("durable confirmation lost")
            super().confirm_effect(profile, effect_id, receipt)

    class RetainingWorker(ScriptedWorker):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.finalized: list[tuple[str, bool]] = []

        def finalize(self, invocation, retain: bool) -> None:
            self.finalized.append((invocation.correlation_id, retain))

    items = [_item("blocked", 0, 1), _item("dependent", 1, 2, ("blocked",)), _item("independent", 2, 3)]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = LostConfirmationStore(tmp_path / "operational.sqlite")
    worker = RetainingWorker(artifacts, {"blocked": ["success", "success"], "dependent": ["success"], "independent": ["success"]})
    coordinator = FactoryCoordinator(store, MemoryWorkManagement(items), worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.authority_blocked == ("blocked",)
    assert summary.dispatched == ("independent",)
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.state("independent").stage is LifecycleStage.DONE
    assert store.recovery_reservations("offline") == ()
    assert worker.finalized[0] == ("launch:blocked:0", True)


def test_recorded_decision_re_admits_after_a_real_process_restart(tmp_path: Path) -> None:
    """AC 8: a fresh process reads the decision and resumes through normal guards."""
    items = [_item("blocked", 0, 1)]
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "operational.sqlite")
    coordinator = FactoryCoordinator(
        store, MemoryWorkManagement(items),
        EscalatingWorker(artifacts, {"blocked": ["authority-block"]}, _escalation()), artifacts, "offline",
    )
    coordinator.start()
    script = """from pathlib import Path
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.escalation import DecisionSubmission
from tests.execution_coordination.test_decision_inbox import _item
from tests.execution_coordination.test_factory_coordinator import MemoryWorkManagement, ScriptedWorker
p=Path(__import__('sys').argv[1]); a=LocalArtifactStore(p/'producer', p/'verifier'); c=FactoryCoordinator(SQLiteOperationalStore(p/'operational.sqlite'), MemoryWorkManagement([_item('blocked', 0, 1)]), ScriptedWorker(a, {'blocked':['success']}, durable=True), a, 'offline'); inbox=DecisionInbox(c._store, c, 'offline'); request=inbox.show('blocked'); inbox.submit(DecisionSubmission('morty','SWF-21','blocked',request.biu_version,request.biu_version,'restart-decision','reconcile')); assert c.state('blocked').stage.value == 'DONE'; assert inbox.show('blocked').event.idempotency_key == 'restart-decision'
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": f"{Path.cwd() / 'src'}:{Path.cwd()}"},
    )

    assert completed.returncode == 0, completed.stderr
