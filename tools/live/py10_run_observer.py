#!/usr/bin/env python3
"""Observe the live run's durable state while it happens, without touching it.

Scope §4 requires an ordering trace, refill events and reservations. Those are
facts about a run in progress, so they are sampled from the operational store
as the factory writes it — not reconstructed afterwards from the outcome.

The observer reads. Its one write is a deliberate contention probe: once, while
the factory holds the repository reservation, it tries to acquire the same
resource and records the refusal. That turns "WIP was 1" from an absence of
contention into an observed exclusion. The probe rolls back on refusal and
never holds the slot.

    python3 tools/live/py10_run_observer.py --state <dir> --until <file>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_sandbox import Redactor, document  # noqa: E402

SAMPLE_SECONDS = 0.05


def _read(database: Path) -> dict:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        reservations = [
            {"scope": row["scope"], "key": row["resource_key"], "owner": row["owner"], "fence": row["fence"]}
            for row in connection.execute("SELECT scope, resource_key, owner, fence FROM reservations ORDER BY scope, resource_key")
        ]
        aggregates = {}
        for row in connection.execute("SELECT identity, version, state FROM aggregates ORDER BY identity"):
            state = json.loads(row["state"])
            aggregates[row["identity"]] = {
                "revision": row["version"], "stage": state.get("stage"), "outcome": state.get("outcome"),
                "accepted": state.get("accepted"), "candidate": (state.get("candidate") or {}).get("locator"),
                "open_decisions": sorted(state.get("open", {})) if "open" in state else None,
            }
        effects = [
            {"identity": row["identity"], "aggregate": row["aggregate"], "status": row["status"]}
            for row in connection.execute("SELECT identity, aggregate, status FROM effects ORDER BY identity")
        ]
        fences = [
            {"scope": row["scope"], "key": row["resource_key"], "fence": row["fence"]}
            for row in connection.execute("SELECT scope, resource_key, fence FROM fences ORDER BY scope, resource_key")
        ]
        return {"reservations": reservations, "aggregates": aggregates, "effects": effects, "fences": fences}
    finally:
        connection.close()


def contention_probe(database: Path, profile: str, scope: str, key: str) -> dict:
    """Try to take the slot the factory is holding, and record the refusal."""
    connection = sqlite3.connect(database, isolation_level=None, timeout=5)
    try:
        connection.execute("BEGIN IMMEDIATE")
        held = connection.execute(
            "SELECT owner, fence FROM reservations WHERE profile=? AND scope=? AND resource_key=?",
            (profile, scope, key),
        ).fetchone()
        connection.execute("ROLLBACK")
        return {
            "probe": "independent acquisition of the held repository slot",
            "refused": held is not None,
            "held_by": held[0] if held else None,
            "fence": held[1] if held else None,
            "rule": "SQLiteOperationalStore.acquire raises ReservationRejected while a reservation row exists",
        }
    finally:
        connection.close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Observe the live run's durable state")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--until", type=Path, required=True, help="stop when this file appears")
    parser.add_argument("--timeline", type=Path, required=True)
    arguments = parser.parse_args(argv)

    record = document()
    redact = Redactor(record)
    profile, repository = str(record["profile"]), str(record["repository"])
    database = arguments.state / "state.sqlite"
    arguments.timeline.parent.mkdir(parents=True, exist_ok=True)

    previous: dict | None = None
    probed = False
    with arguments.timeline.open("w", encoding="utf-8") as sink:
        while not arguments.until.exists():
            if not database.exists():
                time.sleep(SAMPLE_SECONDS)
                continue
            try:
                observed = _read(database)
            except sqlite3.Error:
                time.sleep(SAMPLE_SECONDS)
                continue
            if observed != previous:
                entry = {"at": time.time(), "observed": observed}
                if observed["reservations"] and not probed:
                    probed = True
                    entry["contention_probe"] = contention_probe(database, profile, "repository", repository)
                sink.write(json.dumps(redact(entry), sort_keys=True) + "\n")
                sink.flush()
                previous = observed
            time.sleep(SAMPLE_SECONDS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
