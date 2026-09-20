"""Executable offline proof for PY-04's real coordinator path."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
import subprocess
import sys
import json

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, StopReason
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.composition.offline_profile import OfflineProfile
from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
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
        self.projected.append((identity, str(state)))


class ScriptedWorker:
    def __init__(self, artifact_store: LocalArtifactStore, outcomes: dict[str, list[str]]) -> None:
        self.artifact_store, self.outcomes = artifact_store, outcomes
        self.dispatched: list[str] = []
        self.observed: dict[str, WorkerOutcome] = {}

    def start(self, invocation: object, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome:
        identity = getattr(invocation, "work_identity")
        self.dispatched.append(identity)
        kind = self.outcomes[identity].pop(0)
        outcome = WorkerOutcome.success(self.artifact_store.write(f"artifact:{identity}".encode())) if kind == "success" else WorkerOutcome(kind)
        self.observed[getattr(invocation, "correlation_id")] = outcome
        return outcome

    def read_back(self, invocation: object) -> WorkerOutcome | None:
        return self.observed.get(getattr(invocation, "correlation_id"))


class CrashAfterLaunchWorker(ScriptedWorker):
    def start(self, invocation: object, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome:
        outcome = super().start(invocation, context, grants, budget)
        raise RuntimeError("simulated producer death after durable worker outcome")


class DurableScriptedWorker(ScriptedWorker):
    """Test double whose observable outcomes outlive a producer process."""
    def _outcome_path(self, correlation: str) -> Path:
        return self.artifact_store._root / "outcomes" / correlation.replace(":", "_")

    def start(self, invocation: object, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome:
        outcome = super().start(invocation, context, grants, budget)
        path = self._outcome_path(getattr(invocation, "correlation_id"))
        path.parent.mkdir(parents=True, exist_ok=True)
        candidate = outcome.candidate
        path.write_text(json.dumps({"kind": outcome.kind, "candidate": None if candidate is None else {"kind": candidate.kind, "identity": candidate.identity, "digest": candidate.content_digest, "locator": candidate.locator, "provenance": candidate.provenance}}))
        return outcome

    def read_back(self, invocation: object) -> WorkerOutcome | None:
        path = self._outcome_path(getattr(invocation, "correlation_id"))
        if not path.exists():
            return None
        record = json.loads(path.read_text())
        if record["kind"] != "success":
            return WorkerOutcome(record["kind"])
        candidate = record["candidate"]
        assert isinstance(candidate, dict)
        return WorkerOutcome.success(CandidateRef(CandidateKind(candidate["kind"]), candidate["identity"], candidate["digest"], candidate["locator"], candidate["provenance"]))


class CrashAfterDurableLaunchWorker(DurableScriptedWorker):
    def start(self, invocation: object, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome:
        super().start(invocation, context, grants, budget)
        raise RuntimeError("simulated producer death after durable worker outcome")


def _item(identity: str, fifo: int, priority: int | None, dependencies: tuple[str, ...] = ()) -> ReadyWorkItem:
    contract = valid_contract(identity=identity, dependencies=dependencies, release_policy="automatic-on", budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)), required_evidence=("artifact-verified",))
    return ReadyWorkItem(identity, fifo, "repo", "offline", priority, dependencies, contract, contract.content_digest, "ready")


def test_start_consumes_five_items_in_priority_fifo_order_and_refills_dependencies(tmp_path: Path) -> None:
    items = [_item("blocked", 0, 1, ("first",)), _item("first", 1, 1), _item("second", 2, 1), _item("third", 3, 2), _item("last", 4, None)]
    work, artifacts = MemoryWorkManagement(items), LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {item.identity: ["success"] for item in items})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline")
    summary = coordinator.start()
    assert summary.stop_reason is StopReason.EXHAUSTED
    assert worker.dispatched == ["first", "blocked", "second", "third", "last"]
    assert all(coordinator.state(item.identity).stage is LifecycleStage.DONE for item in items)
    assert work.reads == 1


def test_real_process_restart_recovers_actual_crashed_launch_without_duplicate_dispatch(tmp_path: Path) -> None:
    item, artifacts = _item("crashed", 1, 1), LocalArtifactStore(tmp_path / "artifacts")
    store, work = SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement([item])
    first_worker = CrashAfterDurableLaunchWorker(artifacts, {"crashed": ["success"]})
    with pytest.raises(RuntimeError, match="producer death"):
        FactoryCoordinator(store, work, first_worker, artifacts, "offline").start()
    # A distinct Python process proves the persisted state, reservation, and outcome are sufficient.
    script = """from pathlib import Path\nfrom tests.execution_coordination.test_factory_coordinator import _item, MemoryWorkManagement, DurableScriptedWorker\nfrom alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore\nfrom alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator\nfrom alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore\np=Path(__import__('sys').argv[1]); item=_item('crashed',1,1); a=LocalArtifactStore(p/'artifacts'); w=DurableScriptedWorker(a, {'crashed':['success']}); s=FactoryCoordinator(SQLiteOperationalStore(p/'run.sqlite'), MemoryWorkManagement([item]), w, a, 'offline').start(); assert s.stop_reason.value == 'eligible-backlog-exhausted'; assert not w.dispatched\n"""
    completed = subprocess.run([sys.executable, "-c", script, str(tmp_path)], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(Path.cwd() / "src")})
    assert completed.returncode == 0, completed.stderr
    assert store.recovery_reservations("offline") == ()


def test_recovery_refuses_a_mutated_durable_candidate(tmp_path: Path) -> None:
    item, artifacts = _item("tampered", 1, 1), LocalArtifactStore(tmp_path / "artifacts")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    with pytest.raises(RuntimeError):
        FactoryCoordinator(store, MemoryWorkManagement([item]), CrashAfterDurableLaunchWorker(artifacts, {"tampered": ["success"]}), artifacts, "offline").start()
    record = next((tmp_path / "artifacts" / "outcomes").iterdir())
    original = json.loads(record.read_text())
    Path(original["candidate"]["locator"]).chmod(0o644)
    Path(original["candidate"]["locator"]).write_bytes(b"substituted")
    resumed = DurableScriptedWorker(artifacts, {"tampered": ["success"]})
    with pytest.raises(ValueError, match="read-back"):
        FactoryCoordinator(store, MemoryWorkManagement([item]), resumed, artifacts, "offline").start()
    assert store.recovery_reservations("offline")


def test_verify_refuses_artifact_until_fresh_readback_and_policy_refuses_missing_evidence(tmp_path: Path) -> None:
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    candidate = artifacts.write(b"artifact")
    with pytest.raises(ValueError, match="read-back"):
        verify_in_fresh_process(replace(candidate, content_digest="sha256:" + "0" * 64, identity=candidate.identity.replace(candidate.content_digest, "sha256:" + "0" * 64)))
    item = _item("evidence", 1, 1)
    contract = replace(item.contract, required_evidence=("missing",))
    item = replace(item, contract=contract, readiness_digest=contract.content_digest)
    worker = ScriptedWorker(artifacts, {"evidence": ["success"]})
    with pytest.raises(ValueError, match="ACCEPT requires"):
        FactoryCoordinator(SQLiteOperationalStore(tmp_path / "evidence.sqlite"), MemoryWorkManagement([item]), worker, artifacts, "offline").start()


def test_custody_survives_writer_process_and_mutation_gets_new_identity(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    writer = "from pathlib import Path; from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore; import sys; print(LocalArtifactStore(Path(sys.argv[1])).write(b'first').identity)"
    written = subprocess.run([sys.executable, "-c", writer, str(root)], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}, check=True).stdout.strip()
    artifacts = LocalArtifactStore(root)
    first = CandidateRef.local_artifact(written.rsplit("@", 1)[1], str(root / written.rsplit("@", 1)[1].removeprefix("sha256:")))
    changed = artifacts.write(b"changed")
    assert first.identity != changed.identity
    assert verify_in_fresh_process(first).verify_admissible


def test_explicit_release_and_capacity_stop_are_distinct(tmp_path: Path) -> None:
    item = _item("held", 1, 1)
    contract = replace(item.contract, release_policy=EXPLICIT_HUMAN_OFF)
    item = replace(item, automatic_release=False, contract=contract, readiness_digest=contract.content_digest)
    artifacts, work = LocalArtifactStore(tmp_path / "artifacts"), MemoryWorkManagement([item])
    worker = ScriptedWorker(artifacts, {"held": ["authority-block"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    coordinator = FactoryCoordinator(store, work, worker, artifacts, "offline")
    assert coordinator.start().stop_reason is StopReason.AWAITING_RELEASE
    assert coordinator.release_and_start("held").stop_reason is StopReason.AUTHORITY_BLOCKED
    store.acquire("offline", "repository", "repo", "unrecoverable")
    assert FactoryCoordinator(store, work, worker, artifacts, "offline").start().stop_reason is StopReason.CAPACITY_UNAVAILABLE


def test_authority_block_skips_only_that_item_and_refills_independent_work(tmp_path: Path) -> None:
    blocked, ready = _item("blocked", 1, 1), _item("ready", 2, 2)
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"blocked": ["authority-block"], "ready": ["success"]})
    summary = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement([blocked, ready]), worker, artifacts, "offline").start()
    assert worker.dispatched == ["blocked", "ready"]
    assert summary.stop_reason is StopReason.AUTHORITY_BLOCKED


def test_no_events_after_startup_do_not_reimport_the_ready_view(tmp_path: Path) -> None:
    item = _item("dependency", 1, 1, ("missing",))
    work = MemoryWorkManagement([item])
    summary = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), work, ScriptedWorker(LocalArtifactStore(tmp_path / "artifacts"), {"dependency": ["success"]}), LocalArtifactStore(tmp_path / "artifacts"), "offline").start()
    assert summary.stop_reason is StopReason.BLOCKED
    assert work.reads == 1


def test_rework_returns_to_implement_then_reverifies_before_done(tmp_path: Path) -> None:
    item, artifacts = _item("rework", 1, 1), LocalArtifactStore(tmp_path / "artifacts")
    worker = ScriptedWorker(artifacts, {"rework": ["rework", "success"]})
    coordinator = FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement([item]), worker, artifacts, "offline")
    assert coordinator.start().stop_reason is StopReason.EXHAUSTED
    assert worker.dispatched == ["rework", "rework"]
    assert coordinator.state("rework").stage is LifecycleStage.DONE


def test_offline_profile_composes_the_py03_sqlite_store(tmp_path: Path) -> None:
    profile = OfflineProfile(tmp_path / "run.sqlite", MemoryWorkManagement([]), ScriptedWorker(LocalArtifactStore(tmp_path / "artifacts"), {}), tmp_path / "artifacts")
    assert isinstance(profile.coordinator._store, SQLiteOperationalStore)
