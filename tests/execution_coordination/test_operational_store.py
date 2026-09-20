"""Conformance cases for every OperationalStore adapter."""

from __future__ import annotations

from pathlib import Path
import os
import sqlite3
import subprocess
import sys

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore,
    ReservationRejected,
    SchemaIncompatible,
    StaleFence,
    VersionConflict,
)


@pytest.fixture
def store(tmp_path: Path) -> OperationalStore:
    return SQLiteOperationalStore(tmp_path / "operational.sqlite")


def test_duplicate_receipt_returns_original_without_second_domain_change(store: SQLiteOperationalStore) -> None:
    """Removing receipt uniqueness would apply one event twice."""
    first = store.receive("alpha", "event-1", "digest-a", "job-1", 0, {"state": "queued"})
    duplicate = store.receive("alpha", "event-1", "digest-b", "job-1", 0, {"state": "changed"})

    assert duplicate == first
    assert store.read_state("alpha", "job-1") == (1, {"state": "queued"})


def test_expected_version_rejects_reordered_write(store: SQLiteOperationalStore) -> None:
    """Removing the version guard would roll a later state backward."""
    store.commit("alpha", "job-1", 0, {"state": "one"})
    with pytest.raises(VersionConflict):
        store.commit("alpha", "job-1", 0, {"state": "stale"})

    assert store.read_state("alpha", "job-1") == (1, {"state": "one"})


def test_reservations_are_profile_scoped_and_stale_fences_cannot_release(store: SQLiteOperationalStore) -> None:
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


def test_unresolved_effect_blocks_conflicting_mutation_until_reconciled(store: SQLiteOperationalStore) -> None:
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


def test_restart_recovers_pending_effects_and_unknown_outcomes(store: SQLiteOperationalStore, tmp_path: Path) -> None:
    """Keeping recovery only in memory would lose a pending or unknown effect on restart."""
    store.commit_with_effect("alpha", "job-1", 0, {"state": "prepared"}, "effect-1", {"kind": "publish"})
    store.mark_effect_unknown("alpha", "effect-1")
    restarted = SQLiteOperationalStore(tmp_path / "operational.sqlite")

    assert restarted.pending_effects("alpha") == ()
    assert restarted.unresolved_effects("alpha")[0].identity == "effect-1"


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
