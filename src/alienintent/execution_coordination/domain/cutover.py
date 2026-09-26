"""One-writer cutover values: writer authority, Node state inventory, quiescence and rollback overlay.

The Node state shape is read exactly as `src/runtime/dispatcher.mjs` persists it; nothing here writes a
live Node state file. Ambiguity never picks a writer: it holds both dispatch paths (FX-E2, WO-220503).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Mapping

NODE = "NODE"
PYTHON = "PYTHON"
WRITERS = (NODE, PYTHON)
ACTIVE = "ACTIVE"
HELD = "HELD"
PENDING_INTENTS = ("pendingSignal", "pendingStatus", "pendingOperatorEvent")
IN_FLIGHT_LIFECYCLES = ("ALLOCATING", "LAUNCHING", "RUNNING")
RESERVATION_SCOPE = "cutover-lane"
MIGRATED_OWNER = "node-migrated:"


class WriterRejected(RuntimeError):
    """A dispatch was refused because its writer is not the single approved writer at the current epoch."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class CutoverHold(RuntimeError):
    """A cutover or rollback step cannot proceed safely; durable state is retained unchanged."""

    def __init__(self, code: str, reasons: tuple[str, ...] = ()) -> None:
        super().__init__(code if not reasons else f"{code}: {', '.join(reasons)}")
        self.code = code
        self.reasons = reasons


@dataclass(frozen=True)
class WriterAuthority:
    scope: str
    writer: str | None
    state: str
    epoch: int
    checkpoint: str | None = None
    reason: str = ""

    def to_record(self) -> dict[str, object]:
        return {"schema_version": 1, "scope": self.scope, "writer": self.writer, "state": self.state,
                "epoch": self.epoch, "checkpoint": self.checkpoint, "reason": self.reason}

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> "WriterAuthority":
        if record.get("schema_version") != 1 or record.get("state") not in (ACTIVE, HELD):
            raise CutoverHold("WRITER_RECORD_INVALID")
        writer = record.get("writer")
        if (record["state"] == ACTIVE) != (writer in WRITERS) or not isinstance(record.get("epoch"), int):
            raise CutoverHold("WRITER_RECORD_INVALID")
        return cls(str(record["scope"]), writer if isinstance(writer, str) else None, str(record["state"]),
                   int(record["epoch"]), record.get("checkpoint") if isinstance(record.get("checkpoint"), str) else None,
                   str(record.get("reason", "")))

    def activate(self, writer: str, checkpoint: str | None, reason: str) -> "WriterAuthority":
        if writer not in WRITERS:
            raise CutoverHold("UNKNOWN_WRITER", (writer,))
        return WriterAuthority(self.scope, writer, ACTIVE, self.epoch + 1, checkpoint, reason)

    def hold(self, reason: str) -> "WriterAuthority":
        return WriterAuthority(self.scope, None, HELD, self.epoch + 1, self.checkpoint, reason)


def admit(authority: WriterAuthority, writer: str, epoch: int) -> None:
    """Admit exactly one dispatch path: the approved writer at the record's current epoch."""
    if authority.state != ACTIVE:
        raise WriterRejected("HELD")
    if writer != authority.writer:
        raise WriterRejected("NOT_APPROVED_WRITER")
    if epoch != authority.epoch:
        raise WriterRejected("STALE_EPOCH")


def lane_of(resource: Mapping[str, object]) -> str:
    return f"{resource.get('repository')}#{resource.get('issue')}:{resource.get('role')}"


def _entries(state: Mapping[str, object], key: str) -> dict[str, dict[str, object]]:
    value = state.get(key) or {}
    if not isinstance(value, Mapping) or not all(isinstance(v, Mapping) for v in value.values()):
        raise CutoverHold("NODE_STATE_INVALID", (key,))
    return {str(k): dict(v) for k, v in value.items()}


def quiescence_blockers(state: Mapping[str, object], alive: Callable[[int], bool]) -> tuple[str, ...]:
    """Name every reason the Node writer is not quiescent; empty means quiesced."""
    blockers: list[str] = []
    for lane, claim in sorted(_entries(state, "active").items()):
        pid = claim.get("pid")
        if isinstance(pid, int) and alive(pid):
            blockers.append(f"WORKER_RUNNING:{lane}")
        for intent in PENDING_INTENTS:
            if claim.get(intent):
                blockers.append(f"PENDING_INTENT:{lane}:{intent}")
    for invocation, resource in sorted(_entries(state, "resources").items()):
        if resource.get("lifecycle") in IN_FLIGHT_LIFECYCLES:
            blockers.append(f"RESOURCE_IN_FLIGHT:{invocation}:{resource.get('lifecycle')}")
    for delivery, record in sorted(_entries(state, "deliveries").items()):
        if record.get("state") == "PROCESSING":
            blockers.append(f"DELIVERY_PROCESSING:{delivery}")
    return tuple(blockers)


@dataclass(frozen=True)
class ReconciliationPlan:
    """Every Node active lane, resource and closure with exactly one disposition."""

    reservations: tuple[tuple[str, str], ...] = ()          # (lane, invocationId): pending, carried as a reservation
    effects: tuple[tuple[str, str, str], ...] = ()          # (effect id, lane, Node receipt): confirmed, never re-run
    terminal: tuple[str, ...] = ()                          # removed resources: nothing outstanding
    ambiguous: tuple[str, ...] = field(default=())

    def to_record(self) -> dict[str, object]:
        return {"reservations": [list(r) for r in self.reservations], "effects": [list(e) for e in self.effects],
                "terminal": list(self.terminal), "ambiguous": list(self.ambiguous)}


def reconciliation_plan(state: Mapping[str, object]) -> ReconciliationPlan:
    active = _entries(state, "active")
    resources = _entries(state, "resources")
    reservations: dict[str, str] = {}
    effects: list[tuple[str, str, str]] = []
    ambiguous: list[str] = []
    terminal: list[str] = []
    for lane, claim in sorted(active.items()):
        invocation = str(claim.get("invocationId", ""))
        outcome = claim.get("result") or claim.get("control")
        if outcome:
            effects.append((f"node-effect:{invocation}", lane, f"node-result:{outcome}"))
        elif claim.get("pid") is not None and resources.get(invocation, {}).get("lifecycle") != "READY":
            ambiguous.append(lane)  # launched, no durable result: the external outcome is unknown
        else:
            reservations[lane] = invocation
    for invocation, resource in sorted(resources.items()):
        lane = lane_of(resource)
        if resource.get("lifecycle") == "READY":
            if reservations.get(lane, invocation) != invocation:
                ambiguous.append(lane)
            elif not any(effect[1] == lane for effect in effects):
                reservations[lane] = invocation
        elif resource.get("lifecycle") == "REMOVED":
            terminal.append(invocation)
    for invocation, closure in sorted(_entries(state, "closures").items()):
        effects.append((f"node-closure:{invocation}", str(closure.get("lane", invocation)), "node-closure"))
    return ReconciliationPlan(tuple(sorted(reservations.items())), tuple(effects), tuple(terminal), tuple(ambiguous))


def rollback_overlay(checkpoint_state: Mapping[str, object], completed: Mapping[str, str], epoch: int) -> dict[str, object]:
    """Restore Node from its checkpoint, marking lanes Python already completed so they are never re-dispatched.

    `completed` maps lane -> the confirmed Python effect id. Every other pending reservation is kept exactly.
    """
    restored = deepcopy(dict(checkpoint_state))
    active = _entries(restored, "active")
    resources = _entries(restored, "resources")
    for lane, effect in sorted(completed.items()):
        diagnostic = f"cutover-rollback: completed by PYTHON epoch {epoch} effect {effect}"
        claim = active.pop(lane, None)
        for invocation, resource in resources.items():
            if lane_of(resource) == lane or (claim and invocation == claim.get("invocationId")):
                resources[invocation] = resource | {"lifecycle": "REMOVED", "cleanupDiagnostic": diagnostic}
    restored["active"] = active
    restored["resources"] = resources
    return restored


def pending_lanes(state: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(lane for lane, _ in reconciliation_plan(state).reservations)
