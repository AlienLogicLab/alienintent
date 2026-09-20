"""Executable offline proof for PY-04's real coordinator path."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, StopReason
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import EXPLICIT_HUMAN_OFF
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem
from alienintent.execution_coordination.ports.worker_provider import WorkerOutcome
from .domain.test_contract import valid_contract


@dataclass
class MemoryWorkManagement:
    items: list[ReadyWorkItem]
    reads: int = 0
    projected: list[tuple[str, str]] | None = None

    def __post_init__(self) -> None:
        self.projected = []

    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]:
        self.reads += 1
        return tuple(self.items)

    def propose_release(self, item: ReadyWorkItem) -> None:
        assert self.projected is not None
        self.projected.append((item.identity, "released"))

    def project_execution_state(self, identity: str, state: str) -> None:
        assert self.projected is not None
        self.projected.append((identity, state))


class ScriptedWorker:
    def __init__(self, artifact_store: LocalArtifactStore, outcomes: dict[str, list[str]]) -> None:
        self.artifact_store = artifact_store
        self.outcomes = outcomes
        self.dispatched: list[str] = []
        self.observed: dict[str, WorkerOutcome] = {}

    def start(self, invocation: object, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome:
        identity = getattr(invocation, "work_identity")
        self.dispatched.append(identity)
        outcome = self.outcomes[identity].pop(0)
        if outcome == "success":
            result = WorkerOutcome.success(self.artifact_store.write(f"artifact:{identity}".encode()))
        else:
            result = WorkerOutcome(kind=outcome)
        self.observed[getattr(invocation, "correlation_id")] = result
        return result

    def read_back(self, invocation: object) -> WorkerOutcome | None:
        return self.observed.get(getattr(invocation, "correlation_id"))


def _item(identity: str, fifo: int, priority: int | None, dependencies: tuple[str, ...] = ()) -> ReadyWorkItem:
    contract = valid_contract(
        identity=identity,
        dependencies=dependencies,
        release_policy="automatic-on",
        budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)),
        required_evidence=("artifact-verified",),
    )
    return ReadyWorkItem(identity, fifo, "repo", "offline", priority, dependencies, contract, contract.content_digest, "ready")


def test_start_consumes_five_items_in_priority_fifo_order_and_refills_dependencies(tmp_path: Path) -> None:
    """Removing event-driven refill or priority selection leaves this backlog incomplete or reordered."""
    items = [_item("blocked", 0, 1, ("first",)), _item("first", 1, 1), _item("second", 2, 1), _item("third", 3, 2), _item("last", 4, None)]
    work = MemoryWorkManagement(items)
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {item.identity: ["success"] for item in items})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.stop_reason is StopReason.EXHAUSTED
    assert worker.dispatched == ["first", "blocked", "second", "third", "last"]
    assert all(coordinator.state(item.identity).stage is LifecycleStage.DONE for item in items)
    assert work.reads == 1


def test_restart_resumes_without_duplicate_dispatch_and_verify_requires_fresh_digest_readback(tmp_path: Path) -> None:
    """Dropping persisted lifecycle/custody state would dispatch first again or admit VERIFY without proof."""
    item = _item("only", 1, 1)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    first_worker = ScriptedWorker(artifacts, {"only": ["success"]})
    path = tmp_path / "run.sqlite"
    first = FactoryCoordinator(SQLiteOperationalStore(path), work, first_worker, artifacts, "offline")

    first.start(limit=1)
    resumed_worker = ScriptedWorker(artifacts, {"only": ["success"]})
    resumed = FactoryCoordinator(SQLiteOperationalStore(path), work, resumed_worker, artifacts, "offline")
    summary = resumed.start()

    assert first_worker.dispatched == ["only"]
    assert resumed_worker.dispatched == []
    assert summary.stop_reason is StopReason.EXHAUSTED
    candidate = artifacts.write(b"independent artifact")
    assert verify_in_fresh_process(candidate).verify_admissible


def test_automatic_off_requires_explicit_release_and_authority_block_is_distinct(tmp_path: Path) -> None:
    """Bypassing release admission would dispatch automatic-off work; collapsing block into failure loses its reason."""
    item = _item("held", 1, 1)
    contract = replace(item.contract, release_policy=EXPLICIT_HUMAN_OFF)
    item = replace(item, automatic_release=False, contract=contract, readiness_digest=contract.content_digest)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"held": ["authority-block"]})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline")

    assert coordinator.start().stop_reason is StopReason.AWAITING_RELEASE
    summary = coordinator.release_and_start("held")

    assert summary.stop_reason is StopReason.AUTHORITY_BLOCKED
    assert worker.dispatched == ["held"]


def test_missing_capability_is_rejected_before_worker_dispatch(tmp_path: Path) -> None:
    """Removing release admission would let an ineligible worker run despite its missing grant."""
    item = _item("needs-grant", 1, 1)
    contract = replace(item.contract, required_capabilities=("unavailable",))
    item = replace(item, contract=contract, readiness_digest=contract.content_digest)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"needs-grant": ["success"]})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline")

    assert coordinator.start().stop_reason is StopReason.AUTHORITY_BLOCKED
    assert worker.dispatched == []


def test_existing_mutating_reservation_reports_capacity_unavailable_without_dispatch(tmp_path: Path) -> None:
    """Releasing or ignoring an unresolved reservation could duplicate a mutating invocation after restart."""
    item = _item("held-by-recovery", 1, 1)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"held-by-recovery": ["success"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    store.acquire("offline", "repository", "repo", "crashed-owner")
    coordinator = FactoryCoordinator(store, work, worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.stop_reason is StopReason.CAPACITY_UNAVAILABLE
    assert worker.dispatched == []
    assert work.reads == 1


def test_result_is_durably_correlated_and_read_back_before_capacity_release(tmp_path: Path) -> None:
    """Releasing capacity before persisting the worker result can lose a mutation and admit a duplicate."""
    item = _item("correlated", 1, 1)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"correlated": ["success"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    coordinator = FactoryCoordinator(store, work, worker, artifacts, "offline")

    coordinator.start()

    _, state = store.read_state("offline", "factory:correlated")
    assert state["correlation"] == "launch:correlated:0"
    assert state["outcome"] == "success"
    assert store.recovery_reservations("offline") == ()


def test_rework_outcome_returns_to_implement_then_reverifies_before_done(tmp_path: Path) -> None:
    """Treating rework as terminal failure would strand an authorized item instead of refilling its released slot."""
    item = _item("rework", 1, 1)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"rework": ["rework", "success"]})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline")

    summary = coordinator.start()

    assert summary.stop_reason is StopReason.EXHAUSTED
    assert worker.dispatched == ["rework", "rework"]
    assert coordinator.state("rework").stage is LifecycleStage.DONE


def test_content_addressed_artifact_changes_identity_when_contents_change(tmp_path: Path) -> None:
    """Reusing a candidate identity after mutation would make custody evidence refer to mutable contents."""
    artifacts = LocalArtifactStore(tmp_path / "artifacts")

    first = artifacts.write(b"first")
    changed = artifacts.write(b"changed")

    assert first.identity != changed.identity
    assert verify_in_fresh_process(first).content_digest == first.content_digest
    assert verify_in_fresh_process(changed).content_digest == changed.content_digest


def test_restart_reconciles_an_uncertain_launch_before_releasing_its_reservation(tmp_path: Path) -> None:
    """Stopping forever after an uncertain launch loses a known worker outcome and prevents safe refill."""
    item = _item("crashed", 1, 1)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"crashed": ["success"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    candidate = artifacts.write(b"artifact:crashed")
    store.acquire("offline", "repository", "repo", "launch:crashed:0")
    store.commit_with_effect("offline", "factory:crashed", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": [], "candidate": None}, "launch:crashed:0", {"correlation": "launch:crashed:0", "work": "crashed"})
    store.claim_effect("offline", "launch:crashed:0")
    store.confirm_effect("offline", "launch:crashed:0", "outcome:success")
    worker.observed["launch:crashed:0"] = WorkerOutcome.success(candidate)

    summary = FactoryCoordinator(store, work, worker, artifacts, "offline").start()

    assert summary.stop_reason is StopReason.EXHAUSTED
    assert worker.dispatched == []
    assert FactoryCoordinator(store, work, worker, artifacts, "offline").state("crashed").stage is LifecycleStage.DONE
    assert store.recovery_reservations("offline") == ()


def test_explicit_release_survives_restart_as_the_same_release_boundary(tmp_path: Path) -> None:
    """Keeping AUTO-OFF release only in memory makes a restart silently forget a valid authorization."""
    item = _item("durable-release", 1, 1)
    contract = replace(item.contract, release_policy=EXPLICIT_HUMAN_OFF)
    item = replace(item, automatic_release=False, contract=contract, readiness_digest=contract.content_digest)
    work = MemoryWorkManagement([item])
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"durable-release": ["authority-block", "authority-block"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    first = FactoryCoordinator(store, work, worker, artifacts, "offline")

    assert first.release_and_start("durable-release").stop_reason is StopReason.AUTHORITY_BLOCKED
    restarted = FactoryCoordinator(store, work, worker, artifacts, "offline")

    assert restarted.start().stop_reason is StopReason.AUTHORITY_BLOCKED
    assert store.read_state("offline", "release:durable-release")[1]["identity"] == "durable-release"
