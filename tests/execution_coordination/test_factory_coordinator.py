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

    def project_execution_state(self, identity: str, state: str, revision: int = 0) -> None:
        self.projected.append((identity, str(state)))


class ScriptedWorker:
    """Worker-port double: producers follow ``outcomes``; verifier and closure roles are scripted too.

    A verifier accepts the exact candidate it is given unless ``verdicts`` names
    another step; closure reports receipts for the required closure actions
    unless ``closures`` names what was actually performed. ``dispatched`` counts
    producer dispatches; ``invocations`` records every role invocation.
    """

    def __init__(self, artifacts, outcomes: dict[str, list[str]], *, durable: bool = False, verdicts: dict[str, list[str]] | None = None, closures: dict[str, tuple[str, ...]] | None = None) -> None:
        self.artifacts, self.outcomes, self.durable = artifacts, outcomes, durable
        self.verdicts, self.closures = verdicts or {}, closures or {}
        self.dispatched: list[str] = []
        self.invocations: list[tuple[str, str, str]] = []
        self.observed: dict[str, object] = {}

    def _path(self, correlation: str) -> Path:
        return self.artifacts.root / "outcomes" / correlation.replace(":", "_")

    def start(self, invocation, context, grants, budget):
        _, _, _, provider = _api()
        identity = invocation.work_identity
        self.invocations.append((identity, invocation.role, invocation.correlation_id))
        if invocation.role == provider.VERIFIER:
            steps = self.verdicts.get(identity)
            step = steps.pop(0) if steps else "accept"
            outcome = provider.WorkerOutcome.accept(invocation.candidate) if step == "accept" else (
                provider.WorkerOutcome.reject(invocation.candidate, (f"{identity}: rejected under {invocation.correlation_id}",)) if step == "reject" else provider.WorkerOutcome(step))
        elif invocation.role == provider.CLOSURE:
            performed = self.closures.get(identity, context.required_closure_actions)
            outcome = provider.WorkerOutcome.closed(invocation.candidate, tuple(performed))
        else:
            self.dispatched.append(identity)
            kind = self.outcomes[identity].pop(0)
            outcome = provider.WorkerOutcome.success(self.artifacts.write(f"artifact:{identity}".encode())) if kind == "success" else provider.WorkerOutcome(kind)
        self.observed[invocation.correlation_id] = outcome
        if self.durable:
            path = self._path(invocation.correlation_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            candidate = outcome.candidate
            path.write_text(json.dumps({"kind": outcome.kind, "candidate": None if candidate is None else candidate.__dict__, "findings": list(outcome.findings), "receipts": list(outcome.receipts)}))
        return outcome

    def read_back(self, invocation):
        if not self.durable:
            return self.observed.get(invocation.correlation_id)
        path = self._path(invocation.correlation_id)
        if not path.exists():
            return None
        _, custody, _, provider = _api()
        record = json.loads(path.read_text())
        candidate = None if record["candidate"] is None else replace(custody.candidate_from_record(record["candidate"]), independent_read_back_proven=record["candidate"]["independent_read_back_proven"])
        return provider.WorkerOutcome(record["kind"], candidate, findings=tuple(record.get("findings", ())), receipts=tuple(record.get("receipts", ())))


def _item(identity: str, fifo: int, priority: int | None, dependencies: tuple[str, ...] = (), *, automatic: bool = True, requirement: str = "SF-REQ-001"):
    _, _, ports, _ = _api()
    contract = valid_contract(identity=identity, dependencies=dependencies, satisfied_requirement_ids=(requirement,),
                              release_policy="automatic-on" if automatic else EXPLICIT_HUMAN_OFF,
                              budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)),
                              required_evidence=("artifact-verified",))
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
    assert summary.stop_reason.value == "eligible-backlog-exhausted"
    assert coordinator.state("good").stage is LifecycleStage.DONE
    assert coordinator.state("bad").stage is LifecycleStage.IMPLEMENT
    assert coordinator.state("bad").outcome == "failure"
    assert coordinator.state("slow").outcome == "timeout"


def test_projection_type_error_does_not_retry_without_the_execution_revision(tmp_path: Path) -> None:
    coordinator_module, custody, ports, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")

    class TypeErrorProjectionWork(MemoryWorkManagement):
        def __init__(self, items):
            super().__init__(items)
            self.revisions: list[int] = []

        def project_execution_state(self, identity: str, state: str, revision: int = 0):
            self.revisions.append(revision)
            if revision == 4:
                raise TypeError("provider implementation fault")
            return ports.ProjectionReceipt(identity, revision, True, "confirmed")

    work = TypeErrorProjectionWork([_item("revisioned", 0, 1)])
    coordinator = coordinator_module.FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "run.sqlite"), work,
        ScriptedWorker(artifacts, {"revisioned": ["success"]}), artifacts, "offline",
    )

    with pytest.raises(TypeError, match="provider implementation fault"):
        coordinator.start()
    # VERIFY (1) and ACCEPT (3) project first; the fault at DONE (4) is not retried.
    assert work.revisions == [1, 3, 4]


def test_unavailable_projection_does_not_change_internal_execution_truth(tmp_path: Path) -> None:
    coordinator_module, custody, ports, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")

    class UnavailableProjectionWork(MemoryWorkManagement):
        def project_execution_state(self, identity: str, state: str, revision: int = 0):
            return ports.ProjectionReceipt(identity, revision, False, "projection provider unavailable")

    coordinator = coordinator_module.FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "run.sqlite"), UnavailableProjectionWork([_item("projected", 0, 1)]),
        ScriptedWorker(artifacts, {"projected": ["success"]}), artifacts, "offline",
    )

    coordinator.start()
    assert coordinator.state("projected").stage is LifecycleStage.DONE


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


def test_independent_verifier_retrieves_artifact_after_producer_process_exits(tmp_path: Path) -> None:
    """SWF-12 conditions 4, 5, 6 and 9 use distinct producer/verifier processes."""
    _, custody, _, _ = _api()
    producer_root, verifier_root = tmp_path / "producer", tmp_path / "verifier"
    writer = (
        "from pathlib import Path; import json,sys; "
        "from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore; "
        "print(json.dumps(LocalArtifactStore(Path(sys.argv[1]), Path(sys.argv[2])).write(b'process-artifact').__dict__))"
    )
    produced = subprocess.run(
        [sys.executable, "-c", writer, str(producer_root), str(verifier_root)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": f"{Path.cwd() / 'src'}:{Path.cwd()}"},
        check=True,
    )
    candidate = custody.candidate_from_record(json.loads(produced.stdout))

    verified = custody.verify_in_fresh_process(candidate, verifier_root)

    assert Path(verified.locator).read_bytes() == b"process-artifact"
    assert verified.verify_admissible


def test_wip_refusal_and_explicit_release_are_reported(tmp_path: Path) -> None:
    coordinator_module, custody, _, _ = _api()
    held = _item("held", 1, 1, automatic=False)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    worker = ScriptedWorker(artifacts, {"held": ["success"]})
    coordinator = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([held]), worker, artifacts, "offline")
    assert coordinator.start().stop_reason.value == "dependencies-or-authority-blocked"
    store.acquire("offline", "repository", "repo", "other")
    assert coordinator.release_and_start("held").stop_reason.value == "capacity-unavailable"


def test_success_requires_policy_evidence_and_readback(tmp_path: Path) -> None:
    """A REVIEW verdict without trusted required evidence reworks; it never accepts."""
    coordinator, worker, _ = _coordinator(tmp_path, [_item("evidence", 1, 1)], {"evidence": ["success"]})
    item = coordinator._work.items[0]
    contract = replace(item.contract, required_evidence=("missing",))
    coordinator._work.items[0] = replace(item, contract=contract, readiness_digest=contract.content_digest)
    coordinator.start()
    state = coordinator.state("evidence")
    assert state.stage is LifecycleStage.IMPLEMENT and not state.accepted and state.candidate is None
    assert state.outcome == "failure" and state.record["hold_reason"] == "attempt-budget-exhausted"
    assert [entry["source"] for entry in state.record["findings"]] == ["review"]
    assert worker.dispatched == ["evidence"]


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


def test_recovery_does_not_reapply_an_already_recorded_outcome(tmp_path: Path) -> None:
    """A crash after result read-back leaves only reservation release to recover."""
    coordinator_module, custody, _, _ = _api()
    item = _item("recorded", 1, 1)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")

    class ReleaseFailsOnceStore(SQLiteOperationalStore):
        fail_release = True

        def release(self, *args):
            if self.fail_release:
                self.fail_release = False
                raise RuntimeError("simulated crash before reservation release")
            return super().release(*args)

    first_store = ReleaseFailsOnceStore(tmp_path / "run.sqlite")
    with pytest.raises(RuntimeError, match="before reservation release"):
        coordinator_module.FactoryCoordinator(
            first_store,
            MemoryWorkManagement([item]),
            ScriptedWorker(artifacts, {"recorded": ["success"]}, durable=True),
            artifacts,
            "offline",
        ).start()

    resumed_worker = ScriptedWorker(artifacts, {"recorded": ["success"]}, durable=True)
    summary = coordinator_module.FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "run.sqlite"),
        MemoryWorkManagement([item]),
        resumed_worker,
        artifacts,
        "offline",
    ).start()
    assert summary.stop_reason.value == "eligible-backlog-exhausted"
    assert resumed_worker.dispatched == []


def test_all_scripted_outcomes_drain_independent_work_and_remain_distinct(tmp_path: Path) -> None:
    """Scope item 5: every declared fixture outcome is executable together."""
    items = [_item("failed", 0, 1), _item("timed", 1, 2), _item("reworked", 2, 3), _item("blocked", 3, 4), _item("good", 4, 5)]
    coordinator, worker, _ = _coordinator(tmp_path, items, {"failed": ["failure"], "timed": ["timeout"], "reworked": ["rework", "success"], "blocked": ["authority-block"], "good": ["success"]})
    summary = coordinator.start()
    assert worker.dispatched == ["failed", "timed", "reworked", "reworked", "blocked", "good"]
    assert coordinator.state("failed").outcome == "failure"
    assert coordinator.state("timed").outcome == "timeout"
    assert coordinator.state("blocked").outcome == "authority-block"
    assert coordinator.state("reworked").stage is LifecycleStage.DONE
    assert coordinator.state("good").stage is LifecycleStage.DONE
    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    (tmp_path / "terminal").mkdir()
    terminal, _, _ = _coordinator(tmp_path / "terminal", [_item("failed-only", 0, 1), _item("timed-only", 1, 2)], {"failed-only": ["failure"], "timed-only": ["timeout"]})
    assert terminal.start().stop_reason.value == "eligible-backlog-exhausted"


def test_explicit_release_runs_the_same_boundary_as_automatic_release(tmp_path: Path) -> None:
    (tmp_path / "automatic").mkdir()
    (tmp_path / "explicit").mkdir()
    automatic, worker, _ = _coordinator(tmp_path / "automatic", [_item("auto", 1, 1)], {"auto": ["success"]})
    assert automatic.start().stop_reason.value == "eligible-backlog-exhausted"
    held = _item("held", 1, 1, automatic=False)
    explicit, explicit_worker, _ = _coordinator(tmp_path / "explicit", [held], {"held": ["success"]})
    assert explicit.start().stop_reason.value == "dependencies-or-authority-blocked"
    assert explicit.release_and_start("held").stop_reason.value == "eligible-backlog-exhausted"
    assert worker.dispatched == ["auto"]
    assert explicit_worker.dispatched == ["held"]


def test_content_addressed_path_rejects_mutation_under_the_same_digest(tmp_path: Path) -> None:
    _, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    candidate = artifacts.write(b"original")
    Path(candidate.locator).chmod(0o644)
    Path(candidate.locator).write_bytes(b"mutated")
    with pytest.raises(ValueError, match="immutable"):
        artifacts.write(b"original")


def test_start_drains_five_items_in_priority_fifo_order_and_refills_dependencies(tmp_path: Path) -> None:
    """AC 1-3: a single event drains the ordered ready view to exhaustion."""
    items = [
        _item("blocked", 0, 1, ("first",)),
        _item("equal", 2, 1),
        _item("first", 1, 1),
        _item("later", 3, 2),
        _item("none-later", 5, None),
        _item("none", 4, None),
    ]
    coordinator, worker, _ = _coordinator(
        tmp_path,
        items,
        {item.identity: ["success"] for item in items},
    )

    summary = coordinator.start()

    assert summary.stop_reason.value == "eligible-backlog-exhausted"
    assert worker.dispatched == ["first", "blocked", "equal", "later", "none", "none-later"]
    assert summary.dispatched == tuple(worker.dispatched)
    assert all(coordinator.state(item.identity).stage is LifecycleStage.DONE for item in items)


def test_summary_excludes_a_missing_capability_rejection_from_dispatched(tmp_path: Path) -> None:
    """A rejected release is reported as blocked, not as a worker dispatch."""
    needs_network = _item("needs-network", 0, 1)
    contract = replace(needs_network.contract, required_capabilities=("network",))
    needs_network = replace(needs_network, contract=contract, readiness_digest=contract.content_digest)
    plain = _item("plain", 1, 2)
    coordinator, worker, _ = _coordinator(
        tmp_path,
        [needs_network, plain],
        {"needs-network": ["success"], "plain": ["success"]},
    )

    summary = coordinator.start()

    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    assert worker.dispatched == ["plain"]
    assert summary.dispatched == ("plain",)


def test_no_events_after_startup_do_not_reimport_the_ready_view(tmp_path: Path) -> None:
    """AC 11: blocked work does not turn the startup reconcile into polling."""
    blocked = _item("dependency", 1, 1, ("missing",))
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    work = MemoryWorkManagement([blocked])
    coordinator = coordinator_module.FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "run.sqlite"),
        work,
        ScriptedWorker(artifacts, {"dependency": ["success"]}),
        artifacts,
        "offline",
    )

    assert coordinator.start().stop_reason.value == "dependencies-or-authority-blocked"
    assert work.reads == 1


def test_a_drain_that_iterates_never_reimports_the_ready_view(tmp_path: Path) -> None:
    """AC 11: dispatching work still uses only the startup READY snapshot."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    items = [_item("a", 0, 1), _item("b", 1, 2), _item("c", 2, 3)]
    work = MemoryWorkManagement(items)
    worker = ScriptedWorker(artifacts, {item.identity: ["success"] for item in items})

    summary = coordinator_module.FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "run.sqlite"), work, worker, artifacts, "offline"
    ).start()

    assert worker.dispatched == ["a", "b", "c"]
    assert summary.stop_reason.value == "eligible-backlog-exhausted"
    assert work.reads == 1


def test_wip_refusal_is_enforced_during_an_active_invocation(tmp_path: Path) -> None:
    """AC 4: a competing admission hits the reservation guard, not recovery."""
    coordinator_module, custody, _, _ = _api()
    primary, contender = _item("primary", 0, 1), _item("contender", 1, 2)
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")

    class ContendingWorker(ScriptedWorker):
        contender_result = None

        def start(self, *args):
            self.contender_result = competing._run(contender)
            return super().start(*args)

    worker = ContendingWorker(artifacts, {"primary": ["success"]})
    competing = coordinator_module.FactoryCoordinator(
        store, MemoryWorkManagement([contender]), worker, artifacts, "offline"
    )
    primary_coordinator = coordinator_module.FactoryCoordinator(
        store, MemoryWorkManagement([primary]), worker, artifacts, "offline"
    )

    assert primary_coordinator.start().stop_reason.value == "eligible-backlog-exhausted"
    assert worker.contender_result is coordinator_module.StopReason.CAPACITY_UNAVAILABLE
    assert worker.dispatched == ["primary"]


def test_offline_profile_composes_the_py03_sqlite_store_and_drains(tmp_path: Path) -> None:
    """Scope item 7: the offline composition root wires the persisted store."""
    from alienintent.composition.offline_profile import OfflineProfile

    _, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {"wired": ["success"]})
    profile = OfflineProfile(
        tmp_path / "run.sqlite",
        MemoryWorkManagement([_item("wired", 1, 1)]),
        worker,
        tmp_path / "producer",
        tmp_path / "verifier",
    )

    assert isinstance(profile.coordinator._store, SQLiteOperationalStore)
    assert profile.coordinator.start().stop_reason.value == "eligible-backlog-exhausted"
    assert worker.dispatched == ["wired"]


def test_offline_profile_can_disable_automatic_release(tmp_path: Path) -> None:
    """AC 6: profile policy, rather than the imported view, controls auto-release."""
    from alienintent.composition.offline_profile import OfflineProfile

    _, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {"held": ["success"]})
    profile = OfflineProfile(
        tmp_path / "run.sqlite",
        MemoryWorkManagement([_item("held", 1, 1, automatic=False)]),
        worker,
        tmp_path / "producer",
        tmp_path / "verifier",
        automatic_release=False,
    )

    assert profile.coordinator.start().stop_reason.value == "dependencies-or-authority-blocked"
    assert worker.dispatched == []
    assert profile.coordinator.release_and_start("held").stop_reason.value == "eligible-backlog-exhausted"
    assert worker.dispatched == ["held"]


def test_profile_policy_alone_withholds_automatic_release(tmp_path: Path) -> None:
    """AC 6 / FD-03: the profile switch, not the imported view, gates release."""
    from alienintent.composition.offline_profile import OfflineProfile

    _, custody, _, _ = _api()
    item = _item("auto", 1, 1)
    for name, automatic_release, expected_dispatched in (
        ("off", False, []),
        ("on", True, ["auto"]),
    ):
        root = tmp_path / name
        root.mkdir()
        artifacts = custody.LocalArtifactStore(root / "producer", root / "verifier")
        worker = ScriptedWorker(artifacts, {"auto": ["success"]})
        profile = OfflineProfile(
            root / "run.sqlite",
            MemoryWorkManagement([item]),
            worker,
            root / "producer",
            root / "verifier",
            automatic_release=automatic_release,
        )

        profile.coordinator.start()

        assert worker.dispatched == expected_dispatched


def test_declared_priority_outranks_insertion_order(tmp_path: Path) -> None:
    """AC 2 / BR3: priority, not arrival order, decides which item runs first."""
    items = [_item("last", 0, 9), _item("middle", 1, 5), _item("urgent", 2, 1)]
    coordinator, worker, _ = _coordinator(tmp_path, items, {item.identity: ["success"] for item in items})
    summary = coordinator.start()
    assert worker.dispatched == ["urgent", "middle", "last"]
    assert summary.dispatched == tuple(worker.dispatched)


def test_loop_accepts_only_the_independently_retrieved_verifier_copy(tmp_path: Path) -> None:
    """BR6 / AC 9: the coordinator itself performs fresh-process read-back."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {"custodied": ["success"]})
    coordinator = coordinator_module.FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement([_item("custodied", 0, 1)]), worker, artifacts, "offline")
    coordinator.start()
    candidate = coordinator.state("custodied").candidate
    assert candidate is not None and candidate.independent_read_back_proven
    assert Path(candidate.locator).is_relative_to(artifacts.verifier_root)
    assert not Path(candidate.locator).is_relative_to(artifacts.root)


def test_run_summary_reports_capacity_unavailable_from_the_loop(tmp_path: Path) -> None:
    """BR4: a refill refused by WIP is never reported as exhaustion."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")

    class SeizesCapacityBeforeRefill(MemoryWorkManagement):
        def propose_release(self, item) -> None:
            super().propose_release(item)
            if item.identity == "second":
                store.acquire("offline", "repository", "repo", "concurrent-holder")

    worker = ScriptedWorker(artifacts, {"first": ["success"], "second": ["success"]})
    summary = coordinator_module.FactoryCoordinator(store, SeizesCapacityBeforeRefill([_item("first", 0, 1), _item("second", 1, 2)]), worker, artifacts, "offline").start()
    assert worker.dispatched == ["first"]
    assert summary.dispatched == ("first",)
    assert summary.stop_reason.value == "capacity-unavailable"


def test_reconcile_parks_an_unreadable_outcome_without_stopping_unrelated_work(tmp_path: Path) -> None:
    """PY-07 FD-05: an unreadable outcome blocks only its scoped authority closure."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    ready, stale = _item("ready", 0, 1), replace(_item("stale", 1, 2), repository="other")
    correlation = "launch:stale:0"
    store.acquire("offline", "repository", "other", correlation)
    state = coordinator_module.ExecutionState.for_contract(stale.contract)
    store.commit_with_effect("offline", "factory:stale", 0, coordinator_module.FactoryCoordinator._encode(state), correlation, {"correlation": correlation})
    store.claim_effect("offline", correlation)
    worker = ScriptedWorker(artifacts, {"ready": ["success"], "stale": ["success"]})
    coordinator = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([ready, stale]), worker, artifacts, "offline")
    summary = coordinator.start()
    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    assert summary.dispatched == ("ready",)
    assert worker.dispatched == ["ready"]
    assert store.recovery_reservations("offline") == ()
    assert coordinator.state("stale").outcome == "authority-block"


def test_recovery_refuses_a_result_that_does_not_read_back(tmp_path: Path) -> None:
    """BR6: a correlated result is retained until its durable read-back succeeds."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    item = _item("unconfirmed", 0, 1)
    correlation = "launch:unconfirmed:0"

    class LosesTheWrite(SQLiteOperationalStore):
        drop_next_commit = True

        def commit(self, profile, aggregate, version, payload):
            if self.drop_next_commit and aggregate == "factory:unconfirmed":
                self.drop_next_commit = False
                return None
            return super().commit(profile, aggregate, version, payload)

    store = LosesTheWrite(tmp_path / "run.sqlite")
    store.acquire("offline", "repository", "repo", correlation)
    state = coordinator_module.ExecutionState.for_contract(item.contract)
    store.commit_with_effect("offline", "factory:unconfirmed", 0, coordinator_module.FactoryCoordinator._encode(state), correlation, {"correlation": correlation})
    store.claim_effect("offline", correlation)
    worker = ScriptedWorker(artifacts, {"unconfirmed": ["success"]}, durable=True)
    worker.start(_api()[3].WorkerInvocation("unconfirmed", correlation), item.contract, frozenset(), item.contract.budget_policy)
    summary = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([item]), worker, artifacts, "offline").start()
    assert summary.stop_reason.value == "capacity-unavailable"
    assert store.recovery_reservations("offline") != ()


def test_scheduler_finishes_focused_requirement_before_equal_priority_peer(tmp_path: Path) -> None:
    items = [
        _item("A1", 1, 1, requirement="SF-REQ-A"),
        _item("B1", 2, 1, requirement="SF-REQ-B"),
        _item("A2", 3, 1, dependencies=("A1",), requirement="SF-REQ-A"),
        _item("B2", 4, 1, dependencies=("B1",), requirement="SF-REQ-B"),
    ]
    coordinator, worker, _ = _coordinator(
        tmp_path, items,
        {"A1": ["success"], "A2": ["success"], "B1": ["success"], "B2": ["success"]},
    )
    coordinator.start()
    assert worker.dispatched == ["A1", "A2", "B1", "B2"]


def test_scheduler_borrows_work_when_focused_requirement_is_blocked(tmp_path: Path) -> None:
    items = [
        _item("A1", 1, 1, dependencies=("missing"), requirement="SF-REQ-A"),
        _item("B1", 2, 1, requirement="SF-REQ-B"),
    ]
    coordinator, worker, _ = _coordinator(tmp_path, items, {"A1": ["success"], "B1": ["success"]})
    coordinator._set_requirement_focus("SF-REQ-A", 1)
    coordinator.start()
    assert worker.dispatched == ["B1"]
    assert coordinator._requirement_focus() == ("SF-REQ-A", 1)


def test_scheduler_focus_survives_restart_and_prevents_equal_priority_hopping(tmp_path: Path) -> None:
    first_items = [
        _item("A1", 1, 1, requirement="SF-REQ-A"),
        _item("B1", 2, 1, requirement="SF-REQ-B"),
    ]
    coordinator, worker, artifacts = _coordinator(
        tmp_path, first_items, {"A1": ["success"], "B1": ["success"]},
    )
    coordinator._set_requirement_focus("SF-REQ-A", 1)

    # Reconstruct the coordinator over the same durable store with a later
    # snapshot where A's next child arrived after B.
    store = coordinator._store
    _, _, ports, _ = _api()
    later = [
        _item("B1", 2, 1, requirement="SF-REQ-B"),
        _item("A2", 5, 1, requirement="SF-REQ-A"),
    ]
    restarted_worker = ScriptedWorker(artifacts, {"A2": ["success"], "B1": ["success"]})
    restarted = __import__("alienintent.execution_coordination.application.factory_coordinator", fromlist=["FactoryCoordinator"]).FactoryCoordinator(
        store, MemoryWorkManagement(later), restarted_worker, artifacts, "offline"
    )
    restarted.start()
    assert restarted_worker.dispatched[0] == "A2"


def test_higher_priority_requirement_preempts_existing_focus(tmp_path: Path) -> None:
    items = [
        _item("A1", 1, 1, requirement="SF-REQ-A"),
        _item("B0", 2, 0, requirement="SF-REQ-B"),
    ]
    coordinator, worker, _ = _coordinator(tmp_path, items, {"A1": ["success"], "B0": ["success"]})
    coordinator._set_requirement_focus("SF-REQ-A", 1)
    coordinator.start()
    assert worker.dispatched[0] == "B0"
    assert coordinator._requirement_focus() == ("SF-REQ-B", 0)
