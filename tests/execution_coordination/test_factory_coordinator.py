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
            outcome = provider.WorkerOutcome.accept(invocation.candidate, receipts=("feature-regressions:sha256:" + "a" * 64,)) if step == "accept" else (
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


# --- WO-220611 (B3P): SWF-21 release preconditions and attributable budget at the canonical call site ---

DENIAL = "Implementation is **not** authorized by this Issue. Release remains an explicit authority step."


def _git(checkout: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", *args], cwd=checkout, env=env, check=True, capture_output=True, text=True).stdout.strip()


def _release_repository(tmp_path: Path) -> dict[str, str]:
    """A real repository: ``baseline`` is on ``main``; ``diverged`` is a commit ``main`` cannot reach."""
    checkout = tmp_path / "target"
    checkout.mkdir()
    _git(checkout, "init", "--quiet", "--initial-branch=main")
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "baseline")
    baseline = _git(checkout, "rev-parse", "HEAD")
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "release point")
    _git(checkout, "checkout", "--quiet", "-b", "side", baseline)
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "diverged")
    diverged = _git(checkout, "rev-parse", "HEAD")
    _git(checkout, "checkout", "--quiet", "main")
    return {"checkout": str(checkout), "baseline": baseline, "diverged": diverged}


def _gated(tmp_path: Path, item, *, record: dict | None, allocation=None, outcomes: list[str] | None = None, verdicts=None):
    coordinator_module, custody, _, _ = _api()
    from alienintent.execution_coordination.adapters.release_admission import GitRevisionResolver, StoredReleaseAuthorizations
    from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
    from alienintent.execution_coordination.domain.release import ReleaseAuthorization

    repository = _release_repository(tmp_path)
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    records = StoredReleaseAuthorizations(store, "offline")
    if record is not None:
        values = {"identity": item.identity, "record_ref": f"issue:{item.identity}:release-record", "authorizes_implement": True,
                  "baseline": "baseline", "text": "IMPLEMENT is authorized."} | record
        values["baseline"] = repository.get(values["baseline"], values["baseline"])
        records.record(ReleaseAuthorization(**values))
    release_gate = ReleasePreconditionGate(records, GitRevisionResolver({"repo": Path(repository["checkout"])}), "main")
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {item.identity: outcomes or ["success"]}, verdicts=verdicts)
    coordinator = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([item]), worker, artifacts, "offline",
                                                        release_gate=release_gate, allocation=allocation)
    return coordinator, worker


def _custom_item(identity: str, **changes):
    _, _, ports, _ = _api()
    values = dict(identity=identity, release_policy="automatic-on", satisfied_requirement_ids=("SF-REQ-001",),
                  budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)), required_evidence=("artifact-verified",))
    contract = valid_contract(**(values | changes))
    return ports.ReadyWorkItem(identity, 0, "repo", "offline", 1, (), contract, contract.content_digest, "ready", True)


def test_complete_release_record_admits_and_launches_exactly_one_producer(tmp_path: Path) -> None:
    coordinator, worker = _gated(tmp_path, _item("released", 0, 1), record={})
    summary = coordinator.start()
    assert worker.dispatched == ["released"]
    assert summary.dispatched == ("released",)
    assert coordinator.state("released").stage is LifecycleStage.DONE


@pytest.mark.parametrize(("record", "check"), [
    (None, "implementation-authorized"),
    ({"authorizes_implement": False}, "implementation-authorized"),
    ({"baseline": None}, "baseline-named"),
    ({"baseline": "main"}, "baseline-named"),
    ({"baseline": "0" * 40}, "baseline-resolves"),
    ({"baseline": "b" * 40}, "baseline-resolves"),
    ({"baseline": "diverged"}, "baseline-reachable"),
])
def test_failed_release_precondition_refuses_before_any_worker_launch(tmp_path: Path, record, check) -> None:
    coordinator, worker = _gated(tmp_path, _item("gated", 0, 1), record=record)
    summary = coordinator.start()
    assert worker.invocations == []
    assert summary.dispatched == ()
    assert summary.authority_blocked == ("gated",)
    projected = coordinator.state("gated")
    assert projected.stage is LifecycleStage.IMPLEMENT
    assert projected.record["correlation"] == "release"
    assert projected.record["hold_reason"] == f"release-precondition:{check}"


def test_unsuperseded_denial_wording_refuses_an_otherwise_valid_release(tmp_path: Path) -> None:
    coordinator, worker = _gated(tmp_path, _custom_item("denied", intent=DENIAL), record={})
    summary = coordinator.start()
    assert worker.invocations == [] and summary.authority_blocked == ("denied",)
    assert coordinator.state("denied").record["hold_reason"] == "release-precondition:authority-wording-consistent"


def test_explicit_superseding_record_admits_despite_earlier_denial_wording(tmp_path: Path) -> None:
    coordinator, worker = _gated(tmp_path, _custom_item("superseded", intent=DENIAL), record={"superseding_record": "issue:superseded:superseding-record"})
    coordinator.start()
    assert worker.dispatched == ["superseded"]


def test_attributable_allocation_replaces_the_synthesized_budget(tmp_path: Path) -> None:
    from alienintent.execution_coordination.application.release_admission import BiuLimitAllocation

    for identity, limits, launched in (
        ("exhausted", {"exhausted": {"attempts": 0}}, False),
        ("unallocated", {"someone-else": {"attempts": 3}}, False),
        ("allocated", {"allocated": {"attempts": 2}}, True),
    ):
        root = tmp_path / identity
        root.mkdir()
        coordinator, worker = _gated(root, _item(identity, 0, 1), record={}, allocation=BiuLimitAllocation(limits))
        summary = coordinator.start()
        assert worker.dispatched == ([identity] if launched else [])
        if not launched:
            assert worker.invocations == [] and summary.authority_blocked == (identity,)
            # Refused by the existing admit_release budget check, after every precondition passed.
            assert coordinator.state(identity).record["correlation"] == "release"
            assert "hold_reason" not in coordinator.state(identity).record


@pytest.mark.parametrize(("allocated", "producer_launches"), [(1, 1), (2, 2)])
def test_allocation_counts_durable_rejections_as_consumed_attempts(tmp_path: Path, allocated: int, producer_launches: int) -> None:
    from alienintent.execution_coordination.application.release_admission import BiuLimitAllocation

    _, _, _, provider = _api()
    item = _custom_item("reworked", budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",), maximum_attempts=3))
    coordinator, worker = _gated(tmp_path, item, record={}, allocation=BiuLimitAllocation({"reworked": {"attempts": allocated}}),
                                 outcomes=["success", "success"])
    scripted_start = worker.start

    def start(invocation, context, grants, budget):
        if invocation.role != provider.VERIFIER:
            return scripted_start(invocation, context, grants, budget)
        # A receipted verifier rejection: the only verdict that returns work to IMPLEMENT.
        worker.invocations.append((invocation.work_identity, invocation.role, invocation.correlation_id))
        outcome = provider.WorkerOutcome.reject(invocation.candidate, ("finding",), receipts=("feature-regressions:sha256:" + "a" * 64,))
        worker.observed[invocation.correlation_id] = outcome
        return outcome

    worker.start = start
    summary = coordinator.start()
    # Each receipted rejection consumes one allocated attempt; re-admission after rework
    # is refused once the allocation is exhausted, and not before.
    assert worker.dispatched == ["reworked"] * producer_launches
    assert summary.authority_blocked == ("reworked",)
    assert coordinator.state("reworked").record["correlation"] == "release"
    assert coordinator.state("reworked").record["rejections"] == allocated


# --- READY-SELECTION-RELEASE-GATE-WIP-ADMISSION: configurable WIP admission and cycle counts ---------------------

RECEIPT = "feature-regressions:sha256:" + "a" * 64


class WipWorker(ScriptedWorker):
    """A verifier step ``reject`` is a receipted rejection (the one verdict that reworks); ``observe`` runs before
    every invocation, while the coordinator has recorded the launch and holds its reservations."""

    def __init__(self, artifacts, outcomes, *, observe=None, **options) -> None:
        super().__init__(artifacts, outcomes, **options)
        self.observe = observe
        self.cancelled: list[str] = []

    def cancel(self, identity: str, reason: str) -> None:
        self.cancelled.append(identity)

    def start(self, invocation, context, grants, budget):
        _, _, _, provider = _api()
        if self.observe is not None:
            self.observe(invocation)
        steps = self.verdicts.get(invocation.work_identity)
        if invocation.role != provider.VERIFIER or not steps or steps[0] != "reject":
            return super().start(invocation, context, grants, budget)
        steps.pop(0)
        self.invocations.append((invocation.work_identity, invocation.role, invocation.correlation_id))
        outcome = provider.WorkerOutcome.reject(invocation.candidate, ("finding",), receipts=(RECEIPT,))
        self.observed[invocation.correlation_id] = outcome
        if self.durable:
            path = self._path(invocation.correlation_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"kind": outcome.kind, "candidate": outcome.candidate.__dict__,
                                        "findings": list(outcome.findings), "receipts": list(outcome.receipts)}))
        return outcome


class Limit:
    """An injected WIP limit that counts how often it is read."""

    def __init__(self, value: int | None) -> None:
        self.value, self.reads = value, 0

    def __call__(self) -> int | None:
        self.reads += 1
        return self.value


def _attempts(identity: str, fifo: int, priority: int, maximum_attempts: int = 3, *, automatic: bool = True):
    item = _custom_item(identity, budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",),
                                                             maximum_attempts=maximum_attempts))
    if not automatic:
        contract = replace(item.contract, release_policy=EXPLICIT_HUMAN_OFF)
        item = replace(item, contract=contract, readiness_digest=contract.content_digest, automatic_release=False)
    return replace(item, fifo=fifo, priority=priority)


def _wip(tmp_path: Path, items, outcomes, limit, *, verdicts=None, observe=None, store=None, durable: bool = False):
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    store = store if store is not None else SQLiteOperationalStore(tmp_path / "run.sqlite")
    worker = WipWorker(artifacts, outcomes, verdicts=verdicts, observe=observe, durable=durable)
    return coordinator_module.FactoryCoordinator(store, MemoryWorkManagement(list(items)), worker, artifacts, "offline",
                                                 wip_limit=limit), worker, store


def _slots(store) -> dict[str, int]:
    return {r.key: r.fence for r in store.recovery_reservations("offline") if r.scope == "wip" and r.owner == f"work:{r.key}"}


def test_check1_a_slot_is_a_work_item_kept_from_producer_through_verifier_and_rework(tmp_path: Path) -> None:
    """Limit 1: A keeps one slot PRODUCER -> VERIFIER -> rejected -> PRODUCER; B, released while A is in flight and
    ranked before A, is refused and the run continues A to DONE; the next run admits B."""
    from alienintent.execution_coordination.domain.release import ReleaseSource
    _, _, _, provider = _api()
    a, b = _attempts("A", 1, 2), _attempts("B", 0, 0, automatic=False)
    seen: list[tuple[str, str, dict[str, int]]] = []

    def observe(invocation) -> None:
        seen.append((invocation.work_identity, invocation.role, _slots(store)))
        if invocation.work_identity == "A" and len(seen) == 1:  # the Founder releases B while A is in IMPLEMENT
            store.commit("offline", "release:B", 0, {"identity": "B", "source": ReleaseSource.EXPLICIT_HUMAN})

    coordinator, worker, store = _wip(tmp_path, [b, a], {"A": ["success", "success"], "B": ["success"]}, Limit(1),
                                      verdicts={"A": ["reject", "accept"]}, observe=observe)
    summary = coordinator.start()
    assert summary.stop_reason.value == "capacity-unavailable"
    assert worker.dispatched == ["A", "A"] and summary.dispatched == ("A", "A")
    assert [(identity, role) for identity, role, _ in seen] == [
        ("A", provider.PRODUCER), ("A", provider.VERIFIER), ("A", provider.PRODUCER), ("A", provider.VERIFIER),
        ("A", provider.CLOSURE)]
    assert {tuple(slots) for _, _, slots in seen} == {("A",)} and len({slots["A"] for _, _, slots in seen}) == 1
    assert coordinator.state("A").stage is LifecycleStage.DONE and "B" not in [i for i, _, _ in worker.invocations]
    assert _slots(store) == {}
    second = coordinator.start()
    assert worker.dispatched == ["A", "A", "B"] and second.dispatched == ("B",)
    assert coordinator.state("B").stage is LifecycleStage.DONE and _slots(store) == {}


def test_check3_the_limit_is_n_and_a_changed_file_is_seen_at_the_next_admission(tmp_path: Path) -> None:
    """Limit 3 from the shared file: three admitted (held at authority-block), the fourth refused; raising the file's
    wipLimit to 4 admits it at the next admission."""
    from functools import partial
    from alienintent.composition.work_registry import wip_limit
    host = tmp_path / "factory-director-host.json"
    host.write_text(json.dumps({"wipLimit": 3}))
    items = [_item(f"n{index}", index, index) for index in range(1, 5)]
    outcomes = {"n1": ["authority-block"], "n2": ["authority-block"], "n3": ["authority-block"], "n4": ["success"]}
    coordinator, worker, store = _wip(tmp_path, items, outcomes, partial(wip_limit, host))
    summary = coordinator.start()
    assert summary.stop_reason.value == "capacity-unavailable" and worker.dispatched == ["n1", "n2", "n3"]
    assert set(_slots(store)) == {"n1", "n2", "n3"}
    host.write_text(json.dumps({"wipLimit": 4}))
    summary = coordinator.start()
    assert worker.dispatched == ["n1", "n2", "n3", "n4"] and summary.dispatched == ("n4",)
    assert coordinator.state("n4").stage is LifecycleStage.DONE and set(_slots(store)) == {"n1", "n2", "n3"}


def test_check4_lowering_the_limit_stops_admission_but_never_held_work(tmp_path: Path) -> None:
    """Three held slots, limit lowered to 1: W is refused while the three continue to DONE; the next run, with fewer
    than 1 slot held, admits W. The limit is read only for W's admission, never for work holding its slot."""
    items = [_item("W", 0, 0), _item("x", 1, 1), _item("y", 2, 2), _item("z", 3, 3)]
    limit = Limit(1)
    coordinator, worker, store = _wip(tmp_path, items, {key: ["success"] for key in "Wxyz"}, limit)
    for key in "xyz":  # admitted under the earlier limit 3
        store.acquire_within("offline", "wip", key, f"work:{key}", 3)
    summary = coordinator.start()
    assert summary.stop_reason.value == "capacity-unavailable" and limit.reads == 1
    assert worker.dispatched == ["x", "y", "z"] and _slots(store) == {}
    assert all(coordinator.state(key).stage is LifecycleStage.DONE for key in "xyz")
    assert coordinator.start().dispatched == ("W",) and limit.reads == 2 and _slots(store) == {}


@pytest.mark.parametrize("document", [None, {"wipLimit": 0}, {"wipLimit": -1}, {"wipLimit": "2"}, {"wipLimit": 2.0},
                                      {"wipLimit": True}, {}, [1], "not json"])
def test_check5_an_unavailable_limit_admits_nothing_new_and_is_reread_each_time(tmp_path: Path, document) -> None:
    from functools import partial
    from alienintent.composition.work_registry import wip_limit
    host = tmp_path / "factory-director-host.json"
    if document is not None:
        host.write_text(document if isinstance(document, str) else json.dumps(document))
    coordinator, worker, store = _wip(tmp_path, [_item("fresh", 0, 0), _item("held", 1, 1)],
                                      {"fresh": ["success"], "held": ["success"]}, partial(wip_limit, host))
    store.acquire_within("offline", "wip", "held", "work:held", 1)
    summary = coordinator.start()
    assert summary.stop_reason.value == "wip-limit-unavailable"
    assert worker.dispatched == ["held"] and coordinator.state("held").stage is LifecycleStage.DONE
    with pytest.raises(KeyError):
        coordinator.state("fresh")  # nothing was recorded for the work item that was not admitted
    host.write_text(json.dumps({"wipLimit": 1}))
    assert coordinator.start().dispatched == ("fresh",) and _slots(store) == {}


def test_check6_retries_reworks_and_resumable_results_keep_the_slot_until_done(tmp_path: Path) -> None:
    """missing-terminal-result, ineligible and a VERIFY rejection all keep H's one slot; it is admitted once."""
    _, _, _, provider = _api()
    seen: list[dict[str, int]] = []
    limit = Limit(1)
    coordinator, worker, store = _wip(
        tmp_path, [_attempts("H", 0, 1)],
        {"H": [provider.MISSING_TERMINAL_RESULT, "ineligible", "success", "success"]}, limit,
        verdicts={"H": ["reject", "accept"]}, observe=lambda invocation: seen.append(_slots(store)))
    coordinator.start()
    assert worker.dispatched == ["H"] * 4 and len(seen) == 7
    assert all(slots == seen[0] and list(slots) == ["H"] for slots in seen) and limit.reads == 1
    assert coordinator.state("H").stage is LifecycleStage.DONE and _slots(store) == {}


def test_check6_final_outcomes_release_the_slot_and_authority_holds_keep_it(tmp_path: Path) -> None:
    from alienintent.execution_coordination.domain.escalation import DecisionRecord, DecisionRecorded, DecisionSubmission
    items = [_item("failed", 0, 1), _item("timed", 1, 2), _attempts("exhausted", 2, 3, maximum_attempts=1),
             _item("operator", 3, 4), _item("decided", 4, 5)]
    outcomes = {"failed": ["failure"], "timed": ["timeout"], "exhausted": ["success"],
                "operator": ["authority-block"], "decided": ["authority-block"]}
    coordinator, worker, store = _wip(tmp_path, items, outcomes, Limit(5), verdicts={"exhausted": ["reject"]})
    summary = coordinator.start()
    assert worker.dispatched == ["failed", "timed", "exhausted", "operator", "decided"]
    assert coordinator.state("exhausted").record["hold_reason"] == "attempt-budget-exhausted"
    assert set(_slots(store)) == {"operator", "decided"} and summary.authority_blocked == ("operator", "decided")
    version, _ = store.read_state("offline", "factory:operator")
    coordinator.cancel("operator", "morty", "SWF-21", version, "stop", "cancel-operator")
    assert set(_slots(store)) == {"decided"}
    submission = DecisionSubmission("morty", "SWF-21", "decided", 0, 0, "cancel-decided", "cancel")
    coordinator.record_decision(DecisionRecord(submission, DecisionRecorded("decided", 0, "cancel-decided", "morty")))
    assert coordinator.state("decided").outcome == "cancelled-by-decision" and _slots(store) == {}


def test_check6_an_authority_block_keeps_its_slot_across_restart_and_an_authorize_decision(tmp_path: Path) -> None:
    """V is held at VERIFY by an authority block: restart keeps the slot and launches nothing; the authorize decision
    resumes V at VERIFY still holding the same slot, and DONE releases it."""
    from alienintent.control_plane.application.decision_inbox import DecisionInbox
    from alienintent.execution_coordination.domain.escalation import DecisionSubmission
    _, _, _, provider = _api()
    coordinator, worker, store = _wip(tmp_path, [_item("V", 0, 1)], {"V": ["success"]}, Limit(1),
                                      verdicts={"V": ["unattested"]})
    assert coordinator.start().authority_blocked == ("V",)
    held = _slots(store)
    assert list(held) == ["V"] and coordinator.state("V").stage is LifecycleStage.VERIFY
    seen: list[tuple[str, dict[str, int]]] = []
    restarted_store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    restarted, restarted_worker, _ = _wip(tmp_path, [_item("V", 0, 1)], {}, Limit(None), verdicts={"V": ["accept"]},
                                          store=restarted_store,
                                          observe=lambda invocation: seen.append((invocation.role, _slots(restarted_store))))
    assert restarted.start().stop_reason.value == "dependencies-or-authority-blocked"
    assert restarted_worker.invocations == [] and _slots(restarted_store) == held
    inbox = DecisionInbox(restarted_store, restarted, "offline")
    request = inbox.show("V")
    inbox.submit(DecisionSubmission("morty", "SWF-21", "V", request.biu_version, request.biu_version, "authorize-V", "authorize"))
    assert seen[0] == (provider.VERIFIER, held)
    assert restarted.state("V").stage is LifecycleStage.DONE and _slots(restarted_store) == {}


def test_check6_restart_frees_completed_slots_and_keeps_active_ones(tmp_path: Path) -> None:
    """The Founder's restart confirmation. A crash between the recorded result and the WIP release (DONE, and the final
    outcome `failure`) is completed by the next start; authority-block, blocked-by-authority and a work item no longer
    in the READY snapshot keep their slots; nothing is admitted twice."""
    coordinator_module, _, _, _ = _api()

    class CrashBeforeWipRelease(SQLiteOperationalStore):
        crash = {"failed", "done"}

        def release(self, profile, scope, key, owner, fence):
            if scope == "wip" and key in self.crash:
                self.crash.discard(key)
                raise RuntimeError(f"crash before releasing {key}")
            return super().release(profile, scope, key, owner, fence)

    blocked, gone, failed, done = _item("blocked", 0, 1), _item("gone", 1, 2), _item("failed", 2, 3), _item("done", 3, 4)
    dependent = _item("dependent", 4, 5)
    outcomes = {"blocked": ["authority-block"], "gone": ["authority-block"], "failed": ["failure"], "done": ["success"]}
    store = CrashBeforeWipRelease(tmp_path / "run.sqlite")
    first, worker, _ = _wip(tmp_path, [blocked, gone, failed], outcomes, Limit(10), store=store, durable=True)
    with pytest.raises(RuntimeError, match="crash before releasing failed"):
        first.start()
    assert first.state("failed").outcome == "failure" and "failed" in _slots(store)
    # A work item admitted earlier, then blocked by an authority hold on a work item it now depends on.
    store.acquire_within("offline", "wip", "dependent", "work:dependent", 10)
    state = coordinator_module.ExecutionState.for_contract(dependent.contract)
    store.commit("offline", "factory:dependent", 0, coordinator_module.FactoryCoordinator._encode(state)
                 | {"outcome": "blocked-by-authority", "blocked_by": "blocked"})
    second, _, _ = _wip(tmp_path, [blocked, gone, failed, done], outcomes, Limit(10), store=store, durable=True)
    with pytest.raises(RuntimeError, match="crash before releasing done"):
        second.start()  # its recovery has already completed the release of `failed`
    assert second.state("done").stage is LifecycleStage.DONE
    held = _slots(store)
    assert set(held) == {"blocked", "gone", "dependent", "done"}
    assert any(r.scope == "repository" for r in store.recovery_reservations("offline"))

    restarted_store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    snapshot = [blocked, failed, done, dependent, _item("new", 5, 6)]  # `gone` has left the READY view
    limit = Limit(3)
    restarted, restarted_worker, _ = _wip(tmp_path, snapshot, {"new": ["success"]}, limit, store=restarted_store,
                                          durable=True)
    summary = restarted.start()
    kept = {key: fence for key, fence in held.items() if key != "done"}
    assert _slots(restarted_store) == kept  # same fences: kept, never re-admitted
    assert restarted_store.recovery_reservations("offline") == tuple(
        r for r in restarted_store.recovery_reservations("offline") if r.scope == "wip")
    assert summary.stop_reason.value == "capacity-unavailable" and restarted_worker.invocations == []
    assert limit.reads == 1  # only `new` asked for admission
    limit.value = 4
    assert restarted.start().dispatched == ("new",) and _slots(restarted_store) == kept


def test_check8_cycle_counts_change_only_with_recorded_transitions(tmp_path: Path) -> None:
    """Admission and the first launch make IMPLEMENT 1 (recorded with the launch); retried launches change nothing;
    two reworks give IMPLEMENT 3 and VERIFY 2; a restart that reconciles the duplicate outcome changes nothing."""
    _, _, _, provider = _api()

    class ReleaseFailsOnceStore(SQLiteOperationalStore):
        fail = True

        def release(self, profile, scope, key, owner, fence):
            if self.fail and scope == "repository":
                self.fail = False
                raise RuntimeError("crash before repository release")
            return super().release(profile, scope, key, owner, fence)

    seen: list[tuple[str, int | None, int | None]] = []

    def observe(invocation) -> None:
        state = coordinator.state("C")
        seen.append((invocation.role, state.implement_cycles, state.verify_cycles))

    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    coordinator, worker, _ = _wip(
        tmp_path, [_attempts("C", 0, 1)],
        {"C": [provider.MISSING_TERMINAL_RESULT, "ineligible", "success", "success", "success"]}, Limit(1),
        verdicts={"C": ["reject", "reject", "accept"]}, observe=observe, store=store, durable=True)
    coordinator.start()
    assert seen == [(provider.PRODUCER, 1, 0), (provider.PRODUCER, 1, 0), (provider.PRODUCER, 1, 0),
                    (provider.VERIFIER, 1, 1), (provider.PRODUCER, 2, 1), (provider.VERIFIER, 2, 2),
                    (provider.PRODUCER, 3, 2), (provider.VERIFIER, 3, 3), (provider.CLOSURE, 3, 3)]
    done = coordinator.state("C")
    assert (done.stage, done.implement_cycles, done.verify_cycles) == (LifecycleStage.DONE, 3, 3)

    (tmp_path / "again").mkdir()
    crashing = ReleaseFailsOnceStore(tmp_path / "again" / "run.sqlite")
    first, _, _ = _wip(tmp_path / "again", [_attempts("D", 0, 1)], {"D": ["success"]}, Limit(1), store=crashing,
                       durable=True)
    with pytest.raises(RuntimeError, match="before repository release"):
        first.start()
    before = first.state("D")
    restarted, restarted_worker, _ = _wip(tmp_path / "again", [_attempts("D", 0, 1)], {"D": ["success"]}, Limit(1),
                                          store=SQLiteOperationalStore(tmp_path / "again" / "run.sqlite"), durable=True)
    restarted.start()
    after = restarted.state("D")
    assert (before.stage, before.implement_cycles, before.verify_cycles) == (LifecycleStage.VERIFY, 1, 1)
    assert after.stage is LifecycleStage.DONE and (after.implement_cycles, after.verify_cycles) == (1, 1)
    assert restarted_worker.dispatched == []


def test_check8_a_release_gate_refusal_leaves_implement_at_zero(tmp_path: Path) -> None:
    coordinator, worker = _gated(tmp_path, _item("gated", 0, 1), record=None)
    coordinator.start()
    state = coordinator.state("gated")
    assert worker.invocations == [] and (state.implement_cycles, state.verify_cycles) == (0, 0)


def test_check8_older_records_decode_only_what_their_history_proves(tmp_path: Path) -> None:
    """Counts are derived from retained `rejections`, `findings`, `producer_correlation` and a stage past IMPLEMENT;
    a record without launch evidence is unknown, stays unknown through transitions and is never re-derived."""
    coordinator_module, _, _, _ = _api()
    decode = coordinator_module.FactoryCoordinator.decode
    base = {"version": 3, "accepted": False, "closure": [], "candidate": None}

    def counts(**raw):
        state = decode(base | raw)
        return state.implement_cycles, state.verify_cycles

    assert counts(stage="VERIFY") == (1, 1)
    assert counts(stage="IMPLEMENT", producer_correlation="launch:x:0") == (1, 0)
    assert counts(stage="IMPLEMENT", rejections=2, findings=[{}, {}]) == (3, 2)
    assert counts(stage="DONE", rejections=1, findings=[{}], accepted=True) == (2, 2)
    assert counts(stage="IMPLEMENT", findings=[{"source": "verifier"}]) == (1, 0)
    assert counts(stage="IMPLEMENT", correlation="release", outcome="authority-block") == (None, None)
    assert counts(stage="IMPLEMENT", role="PRODUCER") == (None, None)  # `role` proves nothing
    assert counts(stage="VERIFY", implement_cycles=None, verify_cycles=None) == (None, None)  # recorded unknown
    assert counts(stage="IMPLEMENT", implement_cycles=0, verify_cycles=0, rejections=4) == (0, 0)

    # An older record with no launch evidence runs to DONE: unknown stays unknown, through the first launch too.
    item = _item("legacy", 0, 1)
    coordinator, worker, store = _wip(tmp_path, [item], {"legacy": ["success"]}, Limit(1))
    store.commit("offline", "factory:legacy", 0, base | {"version": 0, "stage": "IMPLEMENT", "correlation": "release",
                                                         "outcome": "decision-recorded"})
    coordinator.start()
    state = coordinator.state("legacy")
    assert state.stage is LifecycleStage.DONE and (state.implement_cycles, state.verify_cycles) == (None, None)
    assert state.record["implement_cycles"] is None and state.record["producer_correlation"]


# --- RECORD-COMPLETED-WORK check 4: a dependency recorded complete ----------------------------------------------------


def _dependent(tmp_path: Path, reader, dependency_stage: str | None = None):
    """Work item B depends on hand-built A, which is not in the READY snapshot; A's coordinator record, if any, is at
    `dependency_stage`; `reader` is the injected reader of recorded completions."""
    coordinator_module, custody, _, _ = _api()
    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {"B": ["success"]})
    store = SQLiteOperationalStore(tmp_path / "run.sqlite")
    if dependency_stage is not None:
        store.commit("offline", "factory:A", 0, {"stage": dependency_stage, "version": 0, "accepted": False,
                                                 "closure": [], "candidate": None})
    coordinator = coordinator_module.FactoryCoordinator(store, MemoryWorkManagement([_item("B", 0, 1, ("A",))]),
                                                        worker, artifacts, "offline", recorded_completion=reader)
    return coordinator, worker, store


@pytest.mark.parametrize("recorded,stage,admitted", [
    (True, None, True),  # recorded complete, no coordinator record
    (False, None, False),  # the reader refuses: a bare or imported DONE row, a retired row, CAPTURE
    (True, "IMPLEMENT", False),  # the row says DONE while the coordinator records active work
    (True, "VERIFY", False),
    (False, "DONE", True),  # a coordinator record at DONE still counts, whatever the row says
])
def test_a_dependency_counts_by_its_coordinator_record_first_then_the_recorded_completion(
        tmp_path: Path, recorded, stage, admitted) -> None:
    asked = []
    coordinator, worker, _ = _dependent(tmp_path, lambda identity: asked.append(identity) or recorded, stage)
    summary = coordinator.start()
    assert worker.dispatched == (["B"] if admitted else [])
    assert summary.stop_reason.value == ("eligible-backlog-exhausted" if admitted else
                                         "dependencies-or-authority-blocked")
    assert set(asked) <= ({"A"} if stage is None else set())  # the reader is asked only without a coordinator record


def test_guard_account_names_a_conflicting_dependency_dependencies_incomplete(tmp_path: Path) -> None:
    """The same decision through `guard_account`: recorded complete with no coordinator record is eligible; the row
    still recorded complete once the coordinator records active work is `dependencies-incomplete`."""
    coordinator, worker, store = _dependent(tmp_path, lambda identity: True)
    record = {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": [], "candidate": None}
    store.commit("offline", "factory:B", 0, record)
    assert coordinator.guard_account("B")["reason"] == "eligible"
    store.commit("offline", "factory:A", 0, record)
    assert coordinator.guard_account("B")["reason"] == "dependencies-incomplete"


def test_without_the_reader_a_dependency_without_a_coordinator_record_never_counts(tmp_path: Path) -> None:
    coordinator, worker, _ = _dependent(tmp_path, None)
    assert coordinator.start().stop_reason.value == "dependencies-or-authority-blocked" and worker.dispatched == []
