"""SQLite implementation of the operational store using explicit transactions."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
import math
from collections.abc import Callable
from pathlib import Path
import sqlite3
from typing import Mapping

from alienintent.execution_coordination.ports.operational_store import (
    Effect, OperationalStore, Receipt, Reservation, ReservationRejected, SchemaIncompatible, SchemaPreflight,
    StaleFence, StoreUnavailable, VersionConflict,
)


from alienintent.execution_coordination.ports.fenced_store import (
    ConsumerReceipt, EffectConfirmation, FencedOperationalStore, GuardVector,
)

SCHEMA_VERSION = 2
_FENCED = "__fenced__:"


def _encoded(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ReservationRejected("guarded data must be finite JSON") from error


def _key(kind: str, identity: str) -> str:
    return _FENCED + _encoded([kind, identity])


def _locks(reservations: tuple[Reservation, ...]) -> list[list[object]]:
    return [[r.scope, r.key, r.owner, r.fence] for r in sorted(reservations, key=lambda r: (r.scope, r.key))]


def _vector(vector: GuardVector) -> dict[str, object]:
    return {"versions": [list(p) for p in vector.versions], "authority": vector.authority,
            "epoch": vector.epoch, "invocation": vector.invocation}



class SQLiteOperationalStore(FencedOperationalStore):
    """Durable operational state; evidence and external adapters remain outside it."""

    def __init__(self, path: Path, *, clock: Callable[[], float] | None = None) -> None:
        self.path = path
        self._clock = clock
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
            preflight = self._preflight(connection)
            if preflight.current_version == SCHEMA_VERSION:
                return
            if preflight.migration:
                self._migrate(connection, *preflight.migration)
                return
            connection.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE operational_schema (version INTEGER NOT NULL);
                CREATE TABLE aggregates (profile TEXT NOT NULL, identity TEXT NOT NULL, version INTEGER NOT NULL, state TEXT NOT NULL, PRIMARY KEY(profile, identity));
                CREATE TABLE receipts (profile TEXT NOT NULL, event_id TEXT NOT NULL, digest TEXT NOT NULL, aggregate TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, PRIMARY KEY(profile, event_id));
                CREATE TABLE reservations (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, owner TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
                CREATE TABLE fences (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
                CREATE TABLE effects (profile TEXT NOT NULL, identity TEXT NOT NULL, aggregate TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, receipt TEXT, PRIMARY KEY(profile, identity));
                CREATE TABLE schema_migrations (from_version INTEGER NOT NULL, to_version INTEGER NOT NULL, reversible INTEGER NOT NULL, PRIMARY KEY(from_version, to_version));
                INSERT INTO operational_schema VALUES (2);
                COMMIT;
            """)

    @classmethod
    def preflight(cls, path: Path) -> SchemaPreflight:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(path)
            return cls._preflight(connection)
        except sqlite3.Error as error:
            raise StoreUnavailable(str(error)) from error
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _preflight(connection: sqlite3.Connection) -> SchemaPreflight:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='operational_schema'").fetchone()
        if not exists:
            return SchemaPreflight(None, None)
        version = connection.execute("SELECT version FROM operational_schema").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise SchemaIncompatible(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
        if version == SCHEMA_VERSION:
            return SchemaPreflight(version, None)
        if version == 1:
            return SchemaPreflight(version, (1, 2))
        raise SchemaIncompatible(f"database schema {version} has no safe migration to {SCHEMA_VERSION}")

    @staticmethod
    def _migrate(connection: sqlite3.Connection, from_version: int, to_version: int) -> None:
        if (from_version, to_version) != (1, 2):
            raise SchemaIncompatible(f"database schema {from_version} has no safe migration to {to_version}")
        connection.executescript("""
            BEGIN IMMEDIATE;
            ALTER TABLE receipts ADD COLUMN status TEXT NOT NULL DEFAULT 'applied';
            CREATE TABLE schema_migrations (from_version INTEGER NOT NULL, to_version INTEGER NOT NULL, reversible INTEGER NOT NULL, PRIMARY KEY(from_version, to_version));
            INSERT INTO schema_migrations VALUES (1, 2, 0);
            UPDATE operational_schema SET version=2;
            COMMIT;
        """)

    def receive(self, profile: str, event_id: str, digest: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> Receipt:
        with self._transaction() as connection:
            prior = connection.execute("SELECT aggregate, version, status FROM receipts WHERE profile=? AND event_id=?", (profile, event_id)).fetchone()
            if prior:
                return Receipt(event_id, prior["aggregate"], prior["version"], prior["status"])
            self._ensure_unblocked(connection, profile, aggregate)
            version = self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute("INSERT INTO receipts VALUES (?, ?, ?, ?, ?, 'applied')", (profile, event_id, digest, aggregate, version))
            return Receipt(event_id, aggregate, version, "applied")

    def receipt(self, profile: str, event_id: str) -> Receipt | None:
        with self._read() as connection:
            row = connection.execute("SELECT aggregate, version, status FROM receipts WHERE profile=? AND event_id=?", (profile, event_id)).fetchone()
            return None if row is None else Receipt(event_id, row["aggregate"], row["version"], row["status"])

    def record_receipt(self, profile: str, event_id: str, digest: str, aggregate: str) -> Receipt:
        return self.record_receipt_if_new(profile, event_id, digest, aggregate)[0]

    def record_receipt_if_new(self, profile: str, event_id: str, digest: str, aggregate: str) -> tuple[Receipt, bool]:
        with self._transaction() as connection:
            prior = connection.execute("SELECT aggregate, version, status FROM receipts WHERE profile=? AND event_id=?", (profile, event_id)).fetchone()
            if prior:
                return Receipt(event_id, prior["aggregate"], prior["version"], prior["status"]), False
            connection.execute("INSERT INTO receipts VALUES (?, ?, ?, ?, 0, 'received')", (profile, event_id, digest, aggregate))
            return Receipt(event_id, aggregate, 0, "received"), True

    def apply_receipt(self, profile: str, event_id: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int:
        with self._transaction() as connection:
            receipt = connection.execute("SELECT aggregate, status FROM receipts WHERE profile=? AND event_id=?", (profile, event_id)).fetchone()
            if not receipt or receipt["status"] != "received":
                raise ReservationRejected("receipt is not awaiting domain application")
            aggregate = receipt["aggregate"]
            self._ensure_unblocked(connection, profile, aggregate)
            version = self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute("INSERT INTO effects VALUES (?, ?, ?, ?, 'pending', NULL)", (profile, effect_id, aggregate, json.dumps(payload, sort_keys=True)))
            connection.execute("UPDATE receipts SET version=?, status='applied' WHERE profile=? AND event_id=?", (version, profile, event_id))
            return version

    def commit(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> int:
        with self._transaction() as connection:
            self._ensure_unblocked(connection, profile, aggregate)
            return self._commit(connection, profile, aggregate, expected_version, state)

    def _ensure_legacy(self, connection: sqlite3.Connection, profile: str, aggregate: str) -> None:
        if aggregate.startswith(_FENCED) or self._guard_record(connection, profile, "lane", aggregate) is not None:
            raise ReservationRejected("adopted lane requires guarded operations")

    def _ensure_legacy_effect(self, connection: sqlite3.Connection, profile: str, effect_id: str) -> None:
        row = connection.execute("SELECT aggregate FROM effects WHERE profile=? AND identity=?", (profile, effect_id)).fetchone()
        if row:
            self._ensure_legacy(connection, profile, row["aggregate"])

    def _ensure_unblocked(self, connection: sqlite3.Connection, profile: str, aggregate: str) -> None:
        self._ensure_legacy(connection, profile, aggregate)
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
        with self._read() as connection:
            row = connection.execute("SELECT version, state FROM aggregates WHERE profile=? AND identity=?", (profile, aggregate)).fetchone()
            if not row:
                return (0, {})
            return (row["version"], json.loads(row["state"]))

    def list_states(self, profile: str, prefix: str = "") -> tuple[tuple[str, int, dict[str, object]], ...]:
        """Read durable execution state without changing schema or semantics."""
        with self._read() as connection:
            rows = connection.execute(
                "SELECT identity, version, state FROM aggregates WHERE profile=? AND identity LIKE ? ORDER BY identity",
                (profile, f"{prefix}%"),
            ).fetchall()
            return tuple((row["identity"], row["version"], json.loads(row["state"])) for row in rows)

    def commit_with_effect(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int:
        with self._transaction() as connection:
            self._ensure_unblocked(connection, profile, aggregate)
            version = self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute("INSERT INTO effects VALUES (?, ?, ?, ?, 'pending', NULL)", (profile, effect_id, aggregate, json.dumps(payload, sort_keys=True)))
            return version

    def mark_effect_unknown(self, profile: str, effect_id: str) -> None:
        self.claim_effect(profile, effect_id)

    def park_unknown_effect(self, profile: str, effect_id: str, expected_version: int, state: Mapping[str, object]) -> int:
        """Atomically preserve an unknown effect and record its authority block.

        An unknown effect normally rejects mutations to its aggregate. Parking
        bypasses that guard only for the atomic recording of the authority
        block; the effect remains unknown until an attributable decision
        explicitly authorizes resumption.
        """
        with self._transaction() as connection:
            self._ensure_legacy_effect(connection, profile, effect_id)
            effect = connection.execute(
                "SELECT aggregate FROM effects WHERE profile=? AND identity=? AND status='unknown'",
                (profile, effect_id),
            ).fetchone()
            if not effect:
                raise ReservationRejected("effect is not awaiting authority reconciliation")
            version = self._commit(connection, profile, effect["aggregate"], expected_version, state)
            return version

    def authorize_unknown_effect(self, profile: str, effect_id: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> bool:
        """Atomically persist an authorize decision and lift its FD-05 guard."""
        with self._transaction() as connection:
            self._ensure_legacy_effect(connection, profile, effect_id)
            effect = connection.execute(
                "SELECT aggregate FROM effects WHERE profile=? AND identity=? AND status='unknown'",
                (profile, effect_id),
            ).fetchone()
            if not effect:
                return False
            if effect["aggregate"] != aggregate:
                raise ReservationRejected("unknown effect does not match decision aggregate")
            self._commit(connection, profile, aggregate, expected_version, state)
            connection.execute(
                "UPDATE effects SET status='authority-authorized' WHERE profile=? AND identity=?",
                (profile, effect_id),
            )
            return True

    def claim_effect(self, profile: str, effect_id: str) -> Effect:
        with self._transaction() as connection:
            self._ensure_legacy_effect(connection, profile, effect_id)
            row = connection.execute("SELECT identity, aggregate, payload FROM effects WHERE profile=? AND identity=? AND status='pending'", (profile, effect_id)).fetchone()
            if not row:
                raise ReservationRejected("effect is not pending execution")
            connection.execute("UPDATE effects SET status='unknown' WHERE profile=? AND identity=?", (profile, effect_id))
            return Effect(row["identity"], row["aggregate"], json.loads(row["payload"]))

    def confirm_effect(self, profile: str, effect_id: str, receipt: str) -> None:
        self._set_effect(profile, effect_id, "confirmed", receipt)

    def _set_effect(self, profile: str, effect_id: str, status: str, receipt: str | None) -> None:
        with self._transaction() as connection:
            self._ensure_legacy_effect(connection, profile, effect_id)
            changed = connection.execute("UPDATE effects SET status=?, receipt=? WHERE profile=? AND identity=? AND status IN ('pending', 'unknown')", (status, receipt, profile, effect_id)).rowcount
            if changed != 1:
                raise ReservationRejected("effect is not pending reconciliation")

    def _effects(self, profile: str, status: str) -> tuple[Effect, ...]:
        with self._read() as connection:
            rows = connection.execute("SELECT identity, aggregate, payload FROM effects WHERE profile=? AND status=? ORDER BY identity", (profile, status)).fetchall()
            return tuple(Effect(row["identity"], row["aggregate"], json.loads(row["payload"])) for row in rows)

    def pending_effects(self, profile: str) -> tuple[Effect, ...]:
        return self._effects(profile, "pending")

    def unresolved_effects(self, profile: str) -> tuple[Effect, ...]:
        return self._effects(profile, "unknown")

    def recovery_receipts(self, profile: str) -> tuple[Receipt, ...]:
        with self._read() as connection:
            rows = connection.execute("SELECT event_id, aggregate, version, status FROM receipts WHERE profile=? AND status='received' ORDER BY event_id", (profile,)).fetchall()
            return tuple(Receipt(row["event_id"], row["aggregate"], row["version"], row["status"]) for row in rows)

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
            self._ensure_releasable(connection, profile, Reservation(scope, key, owner, fence))
            connection.execute("DELETE FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key))

    def recovery_reservations(self, profile: str) -> tuple[Reservation, ...]:
        with self._read() as connection:
            rows = connection.execute("SELECT scope, resource_key, owner, fence FROM reservations WHERE profile=? ORDER BY scope, resource_key", (profile,)).fetchall()
            return tuple(Reservation(row["scope"], row["resource_key"], row["owner"], row["fence"]) for row in rows)

    def _guard_record(self, connection: sqlite3.Connection, profile: str, kind: str, identity: str) -> dict[str, object] | None:
        row = connection.execute("SELECT state FROM aggregates WHERE profile=? AND identity=?", (profile, _key(kind, identity))).fetchone()
        if row is None:
            return None
        record = json.loads(row["state"])
        if type(record.get("schema_version")) is not int or record["schema_version"] != 1:
            raise SchemaIncompatible("unsupported guarded record schema")
        return record

    def _save_guard_record(self, connection: sqlite3.Connection, profile: str, kind: str, identity: str, record: Mapping[str, object]) -> None:
        self._commit(connection, profile, _key(kind, identity), 0, {"schema_version": 1, **record})

    def _validate_fences(self, connection: sqlite3.Connection, profile: str, reservations: tuple[Reservation, ...]) -> None:
        if not reservations or len({(r.scope, r.key) for r in reservations}) != len(reservations):
            raise ReservationRejected("nonempty distinct reservations required")
        for reservation in reservations:
            row = connection.execute("SELECT owner, fence FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, reservation.scope, reservation.key)).fetchone()
            if not row or row["owner"] != reservation.owner or row["fence"] != reservation.fence:
                raise StaleFence("reservation owner or fence is stale")

    def _validate_vector(self, connection: sqlite3.Connection, profile: str, vector: GuardVector) -> None:
        for identity, expected in vector.versions:
            if identity.startswith(_FENCED):
                raise ReservationRejected("reserved vector identity")
            row = connection.execute("SELECT version FROM aggregates WHERE profile=? AND identity=?", (profile, identity)).fetchone()
            actual = row["version"] if row else 0
            if actual != expected:
                raise VersionConflict(f"guard vector {identity}: expected {expected}, found {actual}")
        row = connection.execute("SELECT state FROM aggregates WHERE profile=? AND identity=?", (profile, vector.authority)).fetchone()
        if row is None:
            raise ReservationRejected("missing authority")
        authority = json.loads(row["state"])
        if (type(authority.get("schema_version")) is not int or authority["schema_version"] != 1
                or authority.get("active") is not True or type(authority.get("epoch")) is not int
                or authority["epoch"] != vector.epoch or authority.get("invocation") != vector.invocation):
            raise ReservationRejected("inactive or mismatched epoch/authority")
        expiry = authority.get("expires_at")
        now = self._clock() if self._clock is not None else None
        if (type(expiry) not in (int, float) or not math.isfinite(expiry)
                or type(now) not in (int, float) or not math.isfinite(now)):
            raise ReservationRejected("finite authority expiry and injected clock required")
        if now >= expiry:
            raise ReservationRejected("authority expired")

    def acquire_many(self, profile: str, resources: tuple[tuple[str, str], ...], owner: str) -> tuple[Reservation, ...]:
        """Sorted acquisition in one transaction; failure rolls back this attempt only."""
        if (not profile or not owner or not resources or len(set(resources)) != len(resources)
                or any(len(r) != 2 or not all(isinstance(v, str) and v for v in r) for r in resources)):
            raise ReservationRejected("invalid reservation batch")
        result = []
        with self._transaction() as connection:
            for scope, key in sorted(resources):
                if connection.execute("SELECT 1 FROM reservations WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key)).fetchone():
                    raise ReservationRejected("resource already reserved")
                prior = connection.execute("SELECT fence FROM fences WHERE profile=? AND scope=? AND resource_key=?", (profile, scope, key)).fetchone()
                fence = (prior["fence"] if prior else 0) + 1
                connection.execute("INSERT INTO fences VALUES (?, ?, ?, ?) ON CONFLICT(profile, scope, resource_key) DO UPDATE SET fence=excluded.fence", (profile, scope, key, fence))
                connection.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?)", (profile, scope, key, owner, fence))
                result.append(Reservation(scope, key, owner, fence))
        return tuple(result)

    def commit_guarded(self, profile: str, aggregate: str, expected_version: int, expected_vector: GuardVector,
                       reservations: tuple[Reservation, ...], state: Mapping[str, object], effect_id: str,
                       payload: Mapping[str, object]) -> int:
        """Atomically admit intent and adopt its lane; the reservation spans readback."""
        # Snapshot inputs before acquiring the write lock; caller mutation cannot change admission.
        state = json.loads(_encoded(dict(state)))
        payload = json.loads(_encoded(dict(payload)))
        reservations = tuple(reservations)
        if (not profile or not aggregate or not effect_id or aggregate.startswith(_FENCED)
                or aggregate == expected_vector.authority or dict(expected_vector.versions).get(aggregate) != expected_version
                or any(r.owner != expected_vector.invocation for r in reservations)):
            raise ReservationRejected("intent identity/vector/owner mismatch")
        with self._transaction() as connection:
            self._validate_fences(connection, profile, reservations)
            self._validate_vector(connection, profile, expected_vector)
            if connection.execute("SELECT 1 FROM effects WHERE profile=? AND identity=?", (profile, effect_id)).fetchone():
                raise ReservationRejected("effect identity already used")
            if connection.execute("SELECT 1 FROM effects WHERE profile=? AND aggregate=? AND status!='confirmed'", (profile, aggregate)).fetchone():
                raise ReservationRejected("lane has unresolved effects")
            lane = self._guard_record(connection, profile, "lane", aggregate)
            resources = [[r.scope, r.key] for r in sorted(reservations, key=lambda r: (r.scope, r.key))]
            if lane is not None and lane["resources"] != resources:
                raise ReservationRejected("adopted lane reservation set cannot change")
            version = self._commit(connection, profile, aggregate, expected_version, state)
            post = replace(expected_vector, versions=tuple((key, version if key == aggregate else value) for key, value in expected_vector.versions))
            if lane is None:
                self._save_guard_record(connection, profile, "lane", aggregate, {"resources": resources})
            self._save_guard_record(connection, profile, "intent", effect_id,
                                    {"aggregate": aggregate, "vector": _vector(post), "reservations": _locks(reservations),
                                     "payload_digest": "sha256:" + sha256(_encoded(payload).encode()).hexdigest()})
            connection.execute("INSERT INTO effects VALUES (?, ?, ?, ?, 'pending', NULL)", (profile, effect_id, aggregate, _encoded(payload)))
            return version

    def _bound_intent(self, connection: sqlite3.Connection, profile: str, effect_id: str,
                      reservations: tuple[Reservation, ...], vector: GuardVector | None = None) -> tuple[sqlite3.Row, dict[str, object]]:
        self._validate_fences(connection, profile, reservations)
        record = self._guard_record(connection, profile, "intent", effect_id)
        row = connection.execute("SELECT * FROM effects WHERE profile=? AND identity=?", (profile, effect_id)).fetchone()
        if record is None or row is None or row["aggregate"] != record["aggregate"]:
            raise ReservationRejected("missing guarded intent")
        if record["reservations"] != _locks(reservations):
            raise StaleFence("intent reservations do not match")
        if "sha256:" + sha256(_encoded(json.loads(row["payload"])).encode()).hexdigest() != record["payload_digest"]:
            raise ReservationRejected("intent payload changed")
        if vector is not None:
            self._validate_vector(connection, profile, vector)
            if record["vector"] != _vector(vector):
                raise ReservationRejected("intent vector cannot be replaced or weakened")
        return row, record

    def claim_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], expected_vector: GuardVector) -> Effect:
        with self._transaction() as connection:
            row, _ = self._bound_intent(connection, profile, effect_id, reservations, expected_vector)
            if row["status"] != "pending":
                raise ReservationRejected("guarded effect is not pending")
            connection.execute("UPDATE effects SET status='unknown' WHERE profile=? AND identity=?", (profile, effect_id))
            return Effect(effect_id, row["aggregate"], json.loads(row["payload"]))

    @staticmethod
    def _consumer_receipt(record: dict[str, object]) -> ConsumerReceipt:
        return ConsumerReceipt(record["effect_id"], record["invocation"], "sha256:" + sha256(_encoded(record).encode()).hexdigest())

    def consume_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], expected_vector: GuardVector) -> ConsumerReceipt:
        """The local effect IS durable journal delivery, not an arbitrary remote send.

        Admission and the journal outcome commit together on the same database.
        Remote consumers need their own equivalent fence/idempotency contract.
        """
        with self._transaction() as connection:
            row, intent = self._bound_intent(connection, profile, effect_id, reservations, expected_vector)
            prior = self._guard_record(connection, profile, "consumer", effect_id)
            if prior is not None:
                return self._consumer_receipt(prior)
            if row["status"] != "unknown":
                raise ReservationRejected("consumer requires claimed effect")
            record = {"schema_version": 1, "profile": profile, "aggregate": row["aggregate"],
                      "vector": intent["vector"], "effect_id": effect_id, "invocation": expected_vector.invocation,
                      "reservations": intent["reservations"], "payload_digest": intent["payload_digest"],
                      "outcome": {"status": "accepted", "payload": json.loads(row["payload"])}}
            self._save_guard_record(connection, profile, "consumer", effect_id, record)
            return self._consumer_receipt(record)

    def readback_guarded(self, profile: str, effect_id: str) -> ConsumerReceipt | None:
        with self._read() as connection:
            record = self._guard_record(connection, profile, "consumer", effect_id)
            return None if record is None else self._consumer_receipt(record)

    def confirm_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], receipt: ConsumerReceipt) -> EffectConfirmation:
        with self._transaction() as connection:
            row, intent = self._bound_intent(connection, profile, effect_id, reservations)
            record = self._guard_record(connection, profile, "consumer", effect_id)
            if (record is None or receipt != self._consumer_receipt(record) or receipt.effect_id != effect_id
                    or record["profile"] != profile or record["aggregate"] != row["aggregate"]
                    or record["vector"] != intent["vector"] or record["invocation"] != intent["vector"]["invocation"]
                    or record["reservations"] != intent["reservations"] or record["payload_digest"] != intent["payload_digest"]):
                raise ReservationRejected("receipt is not a correlated durable consumer outcome")
            if row["status"] not in ("unknown", "confirmed"):
                raise ReservationRejected("effect was not claimed")
            if row["status"] == "confirmed" and row["receipt"] != receipt.digest:
                raise ReservationRejected("confirmation receipt changed")
            connection.execute("UPDATE effects SET status='confirmed', receipt=? WHERE profile=? AND identity=?", (receipt.digest, profile, effect_id))
            return EffectConfirmation(effect_id, receipt)

    def _ensure_releasable(self, connection: sqlite3.Connection, profile: str, reservation: Reservation) -> None:
        rows = connection.execute("SELECT identity FROM effects WHERE profile=? AND status!='confirmed'", (profile,)).fetchall()
        for row in rows:
            record = self._guard_record(connection, profile, "intent", row["identity"])
            if record is not None and _locks((reservation,))[0] in record["reservations"]:
                raise ReservationRejected("guarded effect retains reservation until correlated completion")

    class _Transaction:
        def __init__(self, store: "SQLiteOperationalStore") -> None:
            self.store = store
            self.connection: sqlite3.Connection | None = None
        def __enter__(self) -> sqlite3.Connection:
            try:
                self.connection = self.store._connect()
                self.connection.execute("BEGIN IMMEDIATE")
                return self.connection
            except sqlite3.Error as error:
                if self.connection is not None:
                    self.connection.close()
                raise StoreUnavailable(str(error)) from error
        def __exit__(self, kind: object, value: object, trace: object) -> None:
            assert self.connection is not None
            try:
                self.connection.execute("ROLLBACK" if kind else "COMMIT")
            except sqlite3.Error as error:
                raise StoreUnavailable(str(error)) from error
            finally:
                self.connection.close()
            if isinstance(value, sqlite3.Error):
                raise StoreUnavailable(str(value)) from value

    class _Read:
        def __init__(self, store: "SQLiteOperationalStore") -> None:
            self.store = store
            self.connection: sqlite3.Connection | None = None
        def __enter__(self) -> sqlite3.Connection:
            try:
                self.connection = self.store._connect()
                return self.connection
            except sqlite3.Error as error:
                raise StoreUnavailable(str(error)) from error
        def __exit__(self, kind: object, value: object, trace: object) -> None:
            assert self.connection is not None
            self.connection.close()
            if isinstance(value, sqlite3.Error):
                raise StoreUnavailable(str(value)) from value

    def _transaction(self) -> "SQLiteOperationalStore._Transaction":
        return self._Transaction(self)

    def _read(self) -> "SQLiteOperationalStore._Read":
        return self._Read(self)
