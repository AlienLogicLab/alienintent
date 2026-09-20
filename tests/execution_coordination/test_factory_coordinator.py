"""Executable proof for the PY-04 offline factory loop."""

from __future__ import annotations

from dataclasses import dataclass, replace
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import EXPLICIT_HUMAN_OFF
from .domain.test_contract import valid_contract


def _api():
    coordinator = importlib.import_module("alienintent.execution_coordination.application.factory_coordinator")
    custody = importlib.import_module("alienintent.execution_coordination.application.local_artifact_custody")
    ports = importlib.import_module("alienintent.execution_coordination.ports.work_management")
    worker = importlib.import_module("alienintent.execution_coordination.ports.worker_provider")
    return coordinator, custody, ports, worker


@dataclass
class MemoryWorkManagement:
    items: list[object]
    reads: int = 0
    projected: list[tuple[str, str]] | None = None

    def __post_init__(self) -> None:
        self.projected = []

    def import_ready_snapshot(self):
        self.reads += 1
        return tuple(self.items)

    def propose_release(self, item) -> None:
        self.projected.append((item.identity, "released"))

    def project_execution_state(self, identity: str, state: str) -> None:
        self.projected.append((identity, str(state)))


class ScriptedWorker:
    def __init__(self, artifacts, outcomes: dict[str, list[str]], *, durable: bool = False) -> None:
        self.artifacts, self.outcomes, self.durable = artifacts, outcomes, durable
        self.dispatched: list[str] = []
        self.observed: dict[str, object] = {}

    def _path(self, correlation: str) -> Path:
        return self.artifacts.root / "outcomes" / correlation.replace(":", "_")

    def start(self, invocation, context, grants, budget):
        _, _, _, provider = _api()
        identity = invocation.work_identity
        self.dispatched.append(identity)
        kind = self.outcomes[identity].pop(0)
        outcome = provider.WorkerOutcome.success(self.artifacts.write(f"artifact:{identity}".encode())) if kind == "success" else provider.WorkerOutcome(kind)
        self.observed[invocation.correlation_id] = outcome
        if self.durable:
            path = self._path(invocation.correlation_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            candidate = outcome.candidate
            path.write_text(json.dumps({"kind": outcome.kind, "candidate": None if candidate is None else candidate.__dict__}))
        return outcome

    def read_back(self, invocation):
        if not self.durable:
            return self.observed.get(invocation.correlation_id)
        path = self._path(invocation.correlation_id)
        if not path.exists():
            return None
        _, custody, _, provider = _api()
        record = json.loads(path.read_text())
        if record["kind"] != "success":
            return provider.WorkerOutcome(record["kind"])
        candidate = record["candidate"]
        return provider.WorkerOutcome.success(custody.candidate_from_record(candidate))


def _item(identity: str, fifo: int, priority: int | None, dependencies: tuple[str, ...] = (), *, automatic: bool = True):
    _, _, ports, _ = _api()
    contract = valid_contract(identity=identity, dependencies=dependencies, release_policy="automatic-on" if automatic else EXPLICIT_HUMAN_OFF, budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)), required_evidence=("artifact-verified",))
    return ports.ReadyWorkItem(identity, fifo, "repo", "offline", priority, dependencies, contract, contract.content_digest, "ready", automatic)


def _coordinator(tmp_path: Path, items, outcomes):
    coordinator, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, outcomes)
    return coordinator.FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement(items), worker, artifacts, "offline"), worker, artifacts


def test_loop_drains_priority_backlog_and_skips_failure_and_timeout(tmp_path: Path) -> None:
    coordinator, worker, _ = _coordinator(tmp_path, [_item("bad", 0, 1), _item("slow", 1, 2), _item("good", 2, 3)], {"bad": ["failure"], "slow": ["timeout"], "good": ["success"]})
    summary = coordinator.start()
    assert worker.dispatched == ["bad", "slow", "good"]
    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    assert coordinator.state("good").stage is LifecycleStage.DONE
    assert coordinator.state("bad").stage is LifecycleStage.IMPLEMENT
    assert coordinator.state("bad").outcome == "failure"
    assert coordinator.state("slow").outcome == "timeout"


def test_custody_transfer_binds_verifier_copy_and_rejects_tampering(tmp_path: Path) -> None:
    _, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    candidate = artifacts.write(b"candidate")
    verified = custody.verify_in_fresh_process(candidate, artifacts.verifier_root)
    assert Path(verified.locator).is_relative_to(artifacts.verifier_root)
    Path(candidate.locator).chmod(0o644)
    Path(candidate.locator).write_bytes(b"replacement")
    assert Path(verified.locator).read_bytes() == b"candidate"
    with pytest.raises(ValueError, match="read-back"):
        custody.verify_in_fresh_process(replace(candidate, content_digest="sha256:" + "0" * 64, identity=candidate.identity.replace(candidate.content_digest, "sha256:" + "0" * 64)), artifacts.verifier_root)
    assert Path(verified.locator).read_bytes() == b"candidate"


def test_existing_verifier_copy_is_retained_when_producer_artifact_changes(tmp_path: Path) -> None:
    _, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    candidate = artifacts.write(b"candidate")
    verified = custody.verify_in_fresh_process(candidate, artifacts.verifier_root)
    Path(candidate.locator).write_bytes(b"replacement")
    assert custody.verify_in_fresh_process(candidate, artifacts.verifier_root).verify_admissible
    assert Path(verified.locator).read_bytes() == b"candidate"


def test_wip_refusal_and_explicit_release_are_reported(tmp_path: Path) -> None:
    coordinator_module, custody, _, _ = _api()
    held = _item("held", 1, 1, automatic=False)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    worker = ScriptedWorker(artifacts, {"held": ["success"]})
    coordinator = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([held]), worker, artifacts, "offline")
    assert coordinator.start().stop_reason.value == "awaiting-explicit-release"
    store.acquire("offline", "repository", "repo", "other")
    assert coordinator.release_and_start("held").stop_reason.value == "capacity-unavailable"


def test_success_requires_policy_evidence_and_readback(tmp_path: Path) -> None:
    coordinator, worker, _ = _coordinator(tmp_path, [_item("evidence", 1, 1)], {"evidence": ["success"]})
    item = coordinator._work.items[0]
    contract = replace(item.contract, required_evidence=("missing",))
    coordinator._work.items[0] = replace(item, contract=contract, readiness_digest=contract.content_digest)
    with pytest.raises(ValueError, match="ACCEPT requires"):
        coordinator.start()


def test_real_process_restart_reconciles_durable_outcome(tmp_path: Path) -> None:
    coordinator_module, custody, _, _ = _api()
    item = _item("crashed", 1, 1)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    class CrashWorker(ScriptedWorker):
        def start(self, *args):
            super().start(*args)
            raise RuntimeError("crash")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    with pytest.raises(RuntimeError, match="crash"):
        coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([item]), CrashWorker(artifacts, {"crashed": ["success"]}, durable=True), artifacts, "offline").start()
    script = """from pathlib import Path\nfrom tests.execution_coordination.test_factory_coordinator import _item, MemoryWorkManagement, ScriptedWorker\nfrom alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore\nfrom alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator\nfrom alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore\np=Path(__import__('sys').argv[1]); a=LocalArtifactStore(p/'producer',p/'verifier'); w=ScriptedWorker(a, {'crashed':['success']}, durable=True); s=FactoryCoordinator(SQLiteOperationalStore(p/'run.sqlite'),MemoryWorkManagement([_item('crashed',1,1)]),w,a,'offline').start(); assert s.stop_reason.value=='eligible-backlog-exhausted'; assert not w.dispatched\n"""
    completed = subprocess.run([sys.executable, "-c", script, str(tmp_path)], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": f"{Path.cwd() / 'src'}:{Path.cwd()}"})
    assert completed.returncode == 0, completed.stderr


def test_recovery_accepts_an_effect_already_confirmed_before_producer_crash(tmp_path: Path) -> None:
    coordinator_module, custody, _, provider = _api()
    item = _item("confirmed", 1, 1)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    correlation = "launch:confirmed:0"
    reservation = store.acquire("offline", "repository", "repo", correlation)
    state = coordinator_module.ExecutionState.for_contract(item.contract)
    store.commit_with_effect("offline", "factory:confirmed", 0, coordinator_module.FactoryCoordinator._encode(state), correlation, {"correlation": correlation})
    store.claim_effect("offline", correlation)
    store.confirm_effect("offline", correlation, "outcome:success")
    worker = ScriptedWorker(artifacts, {"confirmed": ["success"]}, durable=True)
    worker.start(provider.WorkerInvocation("confirmed", correlation), item.contract, frozenset(), item.contract.budget_policy)
    summary = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([item]), worker, artifacts, "offline").start()
    assert summary.stop_reason.value == "eligible-backlog-exhausted"
    assert store.recovery_reservations("offline") == ()
