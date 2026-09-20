"""SQLite implementation of the operational store using explicit transactions."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Mapping

from alienintent.execution_coordination.ports.operational_store import (
    Effect, OperationalStore, Receipt, Reservation, ReservationRejected, SchemaIncompatible,
    StaleFence, StoreUnavailable, VersionConflict,
)


SCHEMA_VERSION = 1


class SQLiteOperationalStore(OperationalStore):
    """Durable operational state; evidence and external adapters remain outside it."""

    def __init__(self, path: Path) -> None:
        self.path = path
        try:
            self._initialize()
        except sqlite3.Error as error:
            raise StoreUnavailable(str(error)) from error

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='operational_schema'").fetchone()
            if exists:
                version = connection.execute("SELECT version FROM operational_schema").fetchone()[0]
                if version > SCHEMA_VERSION:
                    raise SchemaIncompatible(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
                if version != SCHEMA_VERSION:
                    raise SchemaIncompatible(f"database schema {version} requires an explicit migration")
                return
            connection.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE operational_schema (version INTEGER NOT NULL);
                CREATE TABLE aggregates (profile TEXT NOT NULL, identity TEXT NOT NULL, version INTEGER NOT NULL, state TEXT NOT NULL, PRIMARY KEY(profile, identity));
                CREATE TABLE receipts (profile TEXT NOT NULL, event_id TEXT NOT NULL, digest TEXT NOT NULL, aggregate TEXT NOT NULL, version INTEGER NOT NULL, PRIMARY KEY(profile, event_id));
                CREATE TABLE reservations (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, owner TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
                CREATE TABLE fences (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
                CREATE TABLE effects (profile TEXT NOT NULL, identity TEXT NOT NULL, aggregate TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, receipt TEXT, PRIMARY KEY(profile, identity));
                INSERT INTO operational_schema VALUES (1);
                COMMIT;
            """)

    def receive(self, profile: str, event_id: str, digest: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> Receipt:
        with self._transaction() as connection:
            prior = connection.execute("SELECT aggregate, version FROM receipts WHERE profile=? AND event_id=?", (profile, event_id)).fetchone()
            if prior:
                return Receipt(event_id, prior["aggregate"], prior["version"])
            self._ensure_unblocked(connection, profile, aggregate)
            version = self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute("INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", (profile, event_id, digest, aggregate, version))
            return Receipt(event_id, aggregate, version)

    def commit(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> int:
        with self._transaction() as connection:
            self._ensure_unblocked(connection, profile, aggregate)
            return self._commit(connection, profile, aggregate, expected_version, state)

    def _ensure_unblocked(self, connection: sqlite3.Connection, profile: str, aggregate: str) -> None:
        if connection.execute("SELECT 1 FROM effects WHERE profile=? AND aggregate=? AND status='unknown'", (profile, aggregate)).fetchone():
            raise ReservationRejected("unresolved effect blocks conflicting mutation")

    def _commit(self, connection: sqlite3.Connection, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> int:
        current = connection.execute("SELECT version FROM aggregates WHERE profile=? AND identity=?", (profile, aggregate)).fetchone()
        actual = current["version"] if current else 0
        if actual != expected_version:
            raise VersionConflict(f"expected version {expected_version}, found {actual}")
        version = actual + 1
        connection.execute("INSERT INTO aggregates VALUES (?, ?, ?, ?) ON CONFLICT(profile, identity) DO UPDATE SET version=excluded.version, state=excluded.state", (profile, aggregate, version, json.dumps(state, sort_keys=True)))
        return version

    def read_state(self, profile: str, aggregate: str) -> tuple[int, dict[str, object]]:
        with self._connect() as connection:
            row = connection.execute("SELECT version, state FROM aggregates WHERE profile=? AND identity=?", (profile, aggregate)).fetchone()
            if not row:
                return (0, {})
            return (row["version"], json.loads(row["state"]))

    def commit_with_effect(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int:
        with self._transaction() as connection:
            self._ensure_unblocked(connection, profile, aggregate)
            version = self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute("INSERT INTO effects VALUES (?, ?, ?, ?, 'pending', NULL)", (profile, effect_id, aggregate, json.dumps(payload, sort_keys=True)))
            return version

    def mark_effect_unknown(self, profile: str, effect_id: str) -> None:
        self._set_effect(profile, effect_id, "unknown", None)

    def confirm_effect(self, profile: str, effect_id: str, receipt: str) -> None:
        self._set_effect(profile, effect_id, "confirmed", receipt)

    def _set_effect(self, profile: str, effect_id: str, status: str, receipt: str | None) -> None:
        with self._transaction() as connection:
            changed = connection.execute("UPDATE effects SET status=?, receipt=? WHERE profile=? AND identity=? AND status IN ('pending', 'unknown')", (status, receipt, profile, effect_id)).rowcount
            if changed != 1:
                raise ReservationRejected("effect is not pending reconciliation")

    def _effects(self, profile: str, status: str) -> tuple[Effect, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT identity, aggregate, payload FROM effects WHERE profile=? AND status=? ORDER BY identity", (profile, status)).fetchall()
            return tuple(Effect(row["identity"], row["aggregate"], json.loads(row["payload"])) for row in rows)

    def pending_effects(self, profile: str) -> tuple[Effect, ...]:
        return self._effects(profile, "pending")

    def unresolved_effects(self, profile: str) -> tuple[Effect, ...]:
        return self._effects(profile, "unknown")

    def acquire(self, profile: str, scope: str, key: str, owner: str) -> Reservation:
        with self._transaction() as connection:
            if connection.execute("SELECT 1 FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key)).fetchone():
                raise ReservationRejected("resource already reserved")
            prior = connection.execute("SELECT fence FROM fences WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key)).fetchone()
            fence = (prior["fence"] if prior else 0) + 1
            connection.execute("INSERT INTO fences VALUES (?, ?, ?, ?) ON CONFLICT(profile, scope, resource_key) DO UPDATE SET fence=excluded.fence", (profile, scope, key, fence))
            connection.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?)", (profile, scope, key, owner, fence))
            return Reservation(scope, key, owner, fence)

    def release(self, profile: str, scope: str, key: str, owner: str, fence: int) -> None:
        with self._transaction() as connection:
            row = connection.execute("SELECT owner, fence FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key)).fetchone()
            if not row or row["owner"] != owner or row["fence"] != fence:
                raise StaleFence("reservation owner or fence is stale")
            connection.execute("DELETE FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key))

    def recovery_reservations(self, profile: str) -> tuple[Reservation, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT scope, resource_key, owner, fence FROM reservations WHERE profile=? ORDER BY scope, resource_key", (profile,)).fetchall()
            return tuple(Reservation(row["scope"], row["resource_key"], row["owner"], row["fence"]) for row in rows)

    class _Transaction:
        def __init__(self, store: "SQLiteOperationalStore") -> None:
            self.connection = store._connect()
        def __enter__(self) -> sqlite3.Connection:
            self.connection.execute("BEGIN IMMEDIATE")
            return self.connection
        def __exit__(self, kind: object, value: object, trace: object) -> None:
            self.connection.execute("ROLLBACK" if kind else "COMMIT")
            self.connection.close()

    def _transaction(self) -> "SQLiteOperationalStore._Transaction":
        return self._Transaction(self)
