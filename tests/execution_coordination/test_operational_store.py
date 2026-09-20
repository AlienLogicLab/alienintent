"""Conformance cases for every OperationalStore adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import os
import sqlite3
import subprocess
import sys

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.effect_execution import EffectExecutor
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore,
    ReservationRejected,
    SchemaIncompatible,
    StaleFence,
    StoreUnavailable,
    VersionConflict,
)


@dataclass(frozen=True)
class StoreAdapter:
    name: str
    create: Callable[[Path], OperationalStore]


ADAPTERS = (StoreAdapter("sqlite", lambda root: SQLiteOperationalStore(root / "operational.sqlite")),)


@pytest.fixture(params=ADAPTERS, ids=lambda adapter: adapter.name)
def store_adapter(request: pytest.FixtureRequest) -> StoreAdapter:
    """Adapter composition for the port conformance suite."""
    return request.param


@pytest.fixture
def store(tmp_path: Path, store_adapter: StoreAdapter) -> OperationalStore:
    return store_adapter.create(tmp_path)


def test_duplicate_receipt_returns_original_without_second_domain_change(store: OperationalStore) -> None:
    """Removing receipt uniqueness would apply one event twice."""
    first = store.receive("alpha", "event-1", "digest-a", "job-1", 0, {"state": "queued"})
    duplicate = store.receive("alpha", "event-1", "digest-b", "job-1", 0, {"state": "changed"})

    assert duplicate == first
    assert store.read_state("alpha", "job-1") == (1, {"state": "queued"})


def test_redelivery_after_custody_reports_recovery_work_without_bypassing_outbox(store: OperationalStore) -> None:
    """Completing custody without the effect intent would permanently lose external work."""
    receipt = store.record_receipt("alpha", "event-1", "digest", "job-1")

    assert store.receive("alpha", "event-1", "digest", "job-1", 0, {"state": "queued"}) == receipt
    assert receipt.status == "received"
    assert store.recovery_receipts("alpha") == (receipt,)

    assert store.apply_receipt("alpha", "event-1", 0, {"state": "queued"}, "effect-1", {"kind": "publish"}) == 1
    assert store.read_state("alpha", "job-1") == (1, {"state": "queued"})
    assert store.pending_effects("alpha")[0].identity == "effect-1"


def test_recovery_lists_custody_taken_receipts(store: OperationalStore) -> None:
    """Omitting received receipts would leave a restart unable to finish accepted work."""
    store.record_receipt("alpha", "event-1", "digest", "job-1")

    assert store.recovery_receipts("alpha") == (store.record_receipt("alpha", "event-1", "digest", "job-1"),)


def test_expected_version_rejects_reordered_write(store: OperationalStore) -> None:
    """Removing the version guard would roll a later state backward."""
    store.commit("alpha", "job-1", 0, {"state": "one"})
    with pytest.raises(VersionConflict):
        store.commit("alpha", "job-1", 0, {"state": "stale"})

    assert store.read_state("alpha", "job-1") == (1, {"state": "one"})


def test_reservations_are_profile_scoped_and_stale_fences_cannot_release(store: OperationalStore) -> None:
    """Dropping profile keys or fence checks could release another owner's resource."""
    alpha = store.acquire("alpha", "repository", "repo-x", "owner-a")
    beta = store.acquire("beta", "repository", "repo-x", "owner-b")
    with pytest.raises(ReservationRejected):
        store.acquire("alpha", "repository", "repo-x", "owner-c")
    store.release("alpha", "repository", "repo-x", "owner-a", alpha.fence)
    successor = store.acquire("alpha", "repository", "repo-x", "owner-c")
    with pytest.raises(StaleFence):
        store.release("alpha", "repository", "repo-x", "owner-a", alpha.fence)

    assert alpha.fence == 1
    assert beta.fence == 1
    assert successor.fence == 2


def test_unresolved_effect_blocks_conflicting_mutation_until_reconciled(store: OperationalStore) -> None:
    """Treating an uncertain effect as retryable would duplicate external work."""
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    store.mark_effect_unknown("alpha", "effect-1")
    with pytest.raises(ReservationRejected):
        store.commit("alpha", "job-1", 1, {"state": "next"})
    store.confirm_effect("alpha", "effect-1", "receipt-1")

    assert store.commit("alpha", "job-1", 1, {"state": "next"}) == 2


def test_unresolved_effect_also_blocks_receipt_and_new_effect_paths(store: OperationalStore) -> None:
    """Removing the common mutation guard lets uncertain effects be bypassed."""
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    store.mark_effect_unknown("alpha", "effect-1")

    with pytest.raises(ReservationRejected):
        store.receive("alpha", "event-2", "digest", "job-1", 1, {"state": "receipt-bypass"})
    with pytest.raises(ReservationRejected):
        store.commit_with_effect("alpha", "job-1", 1, {"state": "effect-bypass"}, "effect-2", {"kind": "publish"})


def test_restart_recovers_pending_effects_and_unknown_outcomes(store: OperationalStore, store_adapter: StoreAdapter, tmp_path: Path) -> None:
    """Keeping recovery only in memory would lose a pending or unknown effect on restart."""
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    store.mark_effect_unknown("alpha", "effect-1")
    restarted = store_adapter.create(tmp_path)

    assert restarted.pending_effects("alpha") == ()
    assert restarted.unresolved_effects("alpha")[0].identity == "effect-1"


def test_runtime_sqlite_lock_is_a_port_unavailable_outcome(tmp_path: Path) -> None:
    """Leaking sqlite errors forces a port caller to import the adapter vendor."""
    path = tmp_path / "operational.sqlite"
    store = SQLiteOperationalStore(path)
    store.commit("alpha", "job-1", 0, {"state": "one"})
    lock = sqlite3.connect(path, timeout=0)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        with pytest.raises(StoreUnavailable):
            store.commit("alpha", "job-1", 1, {"state": "two"})
    finally:
        lock.rollback()
        lock.close()


def test_preflight_connection_failure_is_a_port_unavailable_outcome(tmp_path: Path) -> None:
    """Leaking a preflight connection error would expose SQLite beyond the adapter."""
    directory = tmp_path / "not-a-database"
    directory.mkdir()

    with pytest.raises(StoreUnavailable):
        SQLiteOperationalStore.preflight(directory)


def test_process_termination_preserves_owner_for_recovery(tmp_path: Path) -> None:
    """Dropping reservations at restart would let a second owner duplicate work."""
    path = tmp_path / "owner.sqlite"
    child = subprocess.run(
        [sys.executable, "-c", "\n".join((
            "import os, signal, sys",
            "from pathlib import Path",
            "from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore",
            "store = SQLiteOperationalStore(Path(sys.argv[1]))",
            "store.acquire('alpha', 'repository', 'repo-1', 'owner-1')",
            "os.kill(os.getpid(), signal.SIGKILL)",
        )), str(path)],
        check=False,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
    )

    assert child.returncode == -9
    assert SQLiteOperationalStore(path).recovery_reservations("alpha")[0].owner == "owner-1"


def test_process_termination_after_durable_effect_intent_recovers_without_execution(tmp_path: Path) -> None:
    """Moving intent persistence after an external boundary would lose restart recovery."""
    path = tmp_path / "killed.sqlite"
    child = subprocess.run(
        [sys.executable, "-c", "\n".join((
            "from pathlib import Path",
            "from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore",
            f"store = SQLiteOperationalStore(Path({str(path)!r}))",
            "store.commit_with_effect('alpha', 'job-1', 0, {'state': 'prepared'}, 'effect-1', {'kind': 'publish'})",
            "raise SystemExit(9)",
        ))],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
    )

    assert child.returncode == 9
    assert SQLiteOperationalStore(path).pending_effects("alpha")[0].identity == "effect-1"


def test_newer_schema_fails_closed_without_reset(tmp_path: Path) -> None:
    """Silently recreating a newer database would destroy operational state."""
    path = tmp_path / "newer.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE operational_schema (version INTEGER NOT NULL)")
    connection.execute("INSERT INTO operational_schema VALUES (999)")
    connection.commit()
    connection.close()

    with pytest.raises(SchemaIncompatible):
        SQLiteOperationalStore(path)


def test_v1_schema_is_preflighted_then_migrated_with_durable_evidence(tmp_path: Path) -> None:
    """Removing migration preflight or its ledger would make upgrades unauditable."""
    path = tmp_path / "v1.sqlite"
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE operational_schema (version INTEGER NOT NULL);
        INSERT INTO operational_schema VALUES (1);
        CREATE TABLE aggregates (profile TEXT NOT NULL, identity TEXT NOT NULL, version INTEGER NOT NULL, state TEXT NOT NULL, PRIMARY KEY(profile, identity));
        CREATE TABLE receipts (profile TEXT NOT NULL, event_id TEXT NOT NULL, digest TEXT NOT NULL, aggregate TEXT NOT NULL, version INTEGER NOT NULL, PRIMARY KEY(profile, event_id));
        CREATE TABLE reservations (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, owner TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
        CREATE TABLE fences (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
        CREATE TABLE effects (profile TEXT NOT NULL, identity TEXT NOT NULL, aggregate TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, receipt TEXT, PRIMARY KEY(profile, identity));
    """)
    connection.close()

    assert SQLiteOperationalStore.preflight(path).migration == (1, 2)
    SQLiteOperationalStore(path)
    with sqlite3.connect(path) as migrated:
        assert migrated.execute("SELECT version FROM operational_schema").fetchone() == (2,)
        assert migrated.execute("SELECT from_version, to_version, reversible FROM schema_migrations").fetchone() == (1, 2, 0)


def test_outbox_executor_marks_unknown_before_send_and_confirms_readback(tmp_path: Path) -> None:
    """Moving uncertainty handling after send would permit a blind duplicate retry."""
    store = SQLiteOperationalStore(tmp_path / "effects.sqlite")
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    calls: list[str] = []

    def send(effect: object) -> str:
        calls.append("effect-1")
        return "receipt-1"

    executor = EffectExecutor(store, send)
    assert executor.execute("alpha", "effect-1") == "receipt-1"
    assert calls == ["effect-1"]
    assert store.pending_effects("alpha") == ()
    assert store.unresolved_effects("alpha") == ()


def test_outbox_reconciliation_requires_readback_before_unblocking(tmp_path: Path) -> None:
    """Confirming an unknown outcome without read-back could admit conflicting work."""
    store = SQLiteOperationalStore(tmp_path / "reconcile.sqlite")
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    store.claim_effect("alpha", "effect-1")
    executor = EffectExecutor(store, lambda effect: "unused")

    assert executor.reconcile("alpha", "effect-1", lambda effect: None) is False
    with pytest.raises(ReservationRejected):
        store.commit("alpha", "job-1", 1, {"state": "blocked"})
    assert executor.reconcile("alpha", "effect-1", lambda effect: "receipt-1") is True
    assert store.commit("alpha", "job-1", 1, {"state": "unblocked"}) == 2


def test_real_sigkill_boundaries_recover_without_repeating_effect(tmp_path: Path) -> None:
    """Each durable boundary is process-killed; restart derives safe state from SQLite alone."""
    path = tmp_path / "crash.sqlite"
    marker = tmp_path / "effect-count"
    source_root = Path(__file__).resolve().parents[2] / "src"
    script = "\n".join((
        "import os, signal, sys",
        "from pathlib import Path",
        "from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore",
        "from alienintent.execution_coordination.application.effect_execution import EffectExecutor",
        "path, marker, boundary = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]",
        "store = SQLiteOperationalStore(path)",
        "store.acquire('alpha', 'repository', 'repo-1', 'owner-1')",
        "if boundary == 'before-receipt': os.kill(os.getpid(), signal.SIGKILL)",
        "receipt = store.record_receipt('alpha', 'event-1', 'digest', 'job-1')",
        "if boundary == 'after-receipt': os.kill(os.getpid(), signal.SIGKILL)",
        "store.apply_receipt('alpha', receipt.identity, 0, {'state': 'prepared'}, 'effect-1', {'kind': 'publish'})",
        "if boundary == 'after-domain': os.kill(os.getpid(), signal.SIGKILL)",
        "def send(effect): marker.write_text(str(int(marker.read_text()) + 1) if marker.exists() else '1'); return 'confirmed'",
        "EffectExecutor(store, send).execute('alpha', 'effect-1') if boundary != 'after-effect' else (store.claim_effect('alpha', 'effect-1'), send(store.unresolved_effects('alpha')[0]), os.kill(os.getpid(), signal.SIGKILL))",
    ))
    for boundary in ("before-receipt", "after-receipt", "after-domain", "after-effect"):
        path.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        child = subprocess.run([sys.executable, "-c", script, str(path), str(marker), boundary], check=False, env={**os.environ, "PYTHONPATH": str(source_root)})
        assert child.returncode == -9
        restarted = SQLiteOperationalStore(path)
        assert restarted.recovery_reservations("alpha")[0].owner == "owner-1"
        def send(effect: object) -> str:
            marker.write_text(str(int(marker.read_text()) + 1) if marker.exists() else "1")
            return "confirmed"
        if boundary == "before-receipt":
            assert restarted.read_state("alpha", "job-1") == (0, {})
        elif boundary == "after-receipt":
            assert restarted.read_state("alpha", "job-1") == (0, {})
            restarted.apply_receipt("alpha", "event-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
            EffectExecutor(restarted, send).execute("alpha", "effect-1")
            assert marker.read_text() == "1"
        elif boundary == "after-domain":
            assert restarted.pending_effects("alpha")[0].identity == "effect-1"
            assert not marker.exists()
            EffectExecutor(restarted, send).execute("alpha", "effect-1")
            assert marker.read_text() == "1"
        else:
            assert restarted.unresolved_effects("alpha")[0].identity == "effect-1"
            assert marker.read_text() == "1"
            with pytest.raises(ReservationRejected):
                EffectExecutor(restarted, send).execute("alpha", "effect-1")
            assert EffectExecutor(restarted, send).reconcile("alpha", "effect-1", lambda effect: "confirmed") is True
            assert marker.read_text() == "1"
