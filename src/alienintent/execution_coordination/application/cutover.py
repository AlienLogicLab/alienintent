"""M-CUTOVER: conditional one-writer migration and nonduplicating rollback (WO-220503, FX-E2).

Sequence: isolation and canonical-control check, quiesce and inventory the Node writer, hold both paths,
checkpoint, reconcile active work and effects into the Python store, then enable exactly one writer.
Rollback stops Python first, requires its effects reconciled, and restores Node from the verified checkpoint
without leaving any lane Python already completed dispatchable again.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from alienintent.execution_coordination.domain.cutover import (
    ACTIVE, MIGRATED_OWNER, NODE, PYTHON, RESERVATION_SCOPE, CutoverHold, WriterAuthority, WriterRejected, admit,
    quiescence_blockers, reconciliation_plan, rollback_overlay,
)
from alienintent.execution_coordination.ports.cutover import CheckpointStore, NodeWriterObservation, WriterAuthorityStore
from alienintent.execution_coordination.ports.operational_store import OperationalStore

PYTHON_EFFECT = "python-effect:"


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _lane_aggregate(lane: str) -> str:
    return f"cutover-lane:{lane}"


class OneWriterCutover:
    def __init__(self, *, scope: str, root: Path, node_state: Path, python_store_path: Path, store: OperationalStore,
                 profile: str, authority: WriterAuthorityStore, checkpoints: CheckpointStore,
                 observation: NodeWriterObservation, must_not_touch: tuple[Path, ...], canonical_control: bool) -> None:
        self.scope = scope
        self.root = root
        self.node_state = node_state
        self.python_store_path = python_store_path
        self.store = store
        self.profile = profile
        self.authority = authority
        self.checkpoints = checkpoints
        self.observation = observation
        self.must_not_touch = must_not_touch
        self.canonical_control = canonical_control

    # -- writer authority -------------------------------------------------------------------------------------
    def check_isolation(self) -> None:
        mine = tuple(p.resolve() for p in (self.root, self.node_state, self.python_store_path))
        for guarded in (m.expanduser().resolve() for m in self.must_not_touch):
            for path in mine:
                if path == guarded or guarded in path.parents or path in guarded.parents:
                    raise CutoverHold("ISOLATION_VIOLATION", (str(path), str(guarded)))

    def current(self) -> WriterAuthority:
        self.check_isolation()
        record = self.authority.read()
        if record is None:
            self.authority.create(WriterAuthority(self.scope, NODE, ACTIVE, 1, None, "existing authority").to_record())
            record = self.authority.read()
        assert record is not None
        return WriterAuthority.from_record(record)

    def _replace(self, before: WriterAuthority, after: WriterAuthority) -> WriterAuthority:
        self.authority.replace(before.epoch, after.to_record())
        return after

    def _node_bytes(self) -> bytes:
        return self.node_state.read_bytes()

    def _node_writer_detected(self, authority: WriterAuthority) -> tuple[str, ...]:
        found = tuple(f"NODE_WRITER_PROCESS:{pid}" for pid in self.observation.live_node_writer())
        if authority.checkpoint:
            members = self.checkpoints.verify(authority.checkpoint)["members"]
            if _digest(self._node_bytes()) != members["node-state.json"]:  # type: ignore[index]
                found += ("NODE_STATE_CHANGED_AFTER_CHECKPOINT",)
        return found

    def admit(self, writer: str, epoch: int) -> WriterAuthority:
        """Admit one dispatch; a Node writer seen under a Python record holds both paths."""
        authority = self.current()
        if authority.state == ACTIVE and authority.writer == PYTHON:
            detected = self._node_writer_detected(authority)
            if detected:
                self._replace(authority, authority.hold("NODE_WRITER_DETECTED: " + ", ".join(detected)))
                raise WriterRejected("HELD")
        admit(authority, writer, epoch)
        return authority

    # -- cutover ----------------------------------------------------------------------------------------------
    def cutover(self) -> dict[str, object]:
        authority = self.current()
        if authority.state != ACTIVE or authority.writer != NODE:
            raise CutoverHold("NOT_FROM_EXISTING_WRITER", (f"{authority.writer}/{authority.state}",))
        if not self.canonical_control:
            return {"disposition": "RETURN_TO_EXISTING_AUTHORITY", "writer": NODE, "epoch": authority.epoch}
        node_bytes = self._node_bytes()
        state = json.loads(node_bytes)
        blockers = quiescence_blockers(state, self.observation.pid_alive)
        blockers += tuple(f"NODE_WRITER_PROCESS:{pid}" for pid in self.observation.live_node_writer())
        if blockers:
            raise CutoverHold("NOT_QUIESCED", blockers)
        plan = reconciliation_plan(state)
        if plan.ambiguous:
            raise CutoverHold("RECONCILIATION_AMBIGUOUS", plan.ambiguous)
        held = self._replace(authority, authority.hold("cutover: quiesced; checkpoint and reconcile"))
        checkpoint = self.checkpoints.create(self.node_state, self.python_store_path, self.store.backup)  # type: ignore[attr-defined]
        self.checkpoints.verify(checkpoint)
        for lane, invocation in plan.reservations:
            self.store.acquire(self.profile, RESERVATION_SCOPE, lane, MIGRATED_OWNER + invocation)
        for effect_id, lane, receipt in plan.effects:
            version, lane_state = self.store.read_state(self.profile, _lane_aggregate(lane))
            self.store.commit_with_effect(self.profile, _lane_aggregate(lane), version,
                                          lane_state | {"lane": lane, "writer": NODE},
                                          effect_id, {"lane": lane, "writer": NODE, "receipt": receipt})
            self.store.claim_effect(self.profile, effect_id)
            self.store.confirm_effect(self.profile, effect_id, receipt)
        record = plan.to_record() | {"checkpoint": checkpoint, "node_state_digest": _digest(node_bytes),
                                     "epoch": held.epoch}
        self.store.commit(self.profile, f"cutover:reconciliation:{held.epoch}", 0, record)
        self._verify_reconciled(plan)
        if self._digest_changed(node_bytes):
            raise CutoverHold("NODE_WRITER_DETECTED", ("NODE_STATE_CHANGED_DURING_CUTOVER",))
        active = self._replace(held, held.activate(PYTHON, checkpoint, "cutover: reconciled"))
        return {"disposition": "CUTOVER", "writer": PYTHON, "epoch": active.epoch, "checkpoint": checkpoint,
                "reconciliation": record}

    def _digest_changed(self, node_bytes: bytes) -> bool:
        return _digest(self._node_bytes()) != _digest(node_bytes)

    def _verify_reconciled(self, plan) -> None:  # noqa: ANN001 - domain value
        reservations = {(r.scope, r.key) for r in self.store.recovery_reservations(self.profile)}
        confirmed = {identity for identity, status, _ in self.store.effect_ledger(self.profile) if status == "confirmed"}  # type: ignore[attr-defined]
        missing = tuple(lane for lane, _ in plan.reservations if (RESERVATION_SCOPE, lane) not in reservations)
        missing += tuple(effect for effect, _, _ in plan.effects if effect not in confirmed)
        if missing:
            raise CutoverHold("RECONCILIATION_INCOMPLETE", missing)

    def reconciliation(self, epoch: int) -> Mapping[str, object]:
        return self.store.read_state(self.profile, f"cutover:reconciliation:{epoch}")[1]

    # -- the Python writer inside the rehearsal ----------------------------------------------------------------
    def python_dispatch(self, lane: str, epoch: int, *, confirm: bool = True) -> str:
        """Dispatch one migrated lane as the Python writer; the reservation is released only once confirmed."""
        self.admit(PYTHON, epoch)
        owned = [r for r in self.store.recovery_reservations(self.profile) if (r.scope, r.key) == (RESERVATION_SCOPE, lane)]
        if not owned:
            raise CutoverHold("NO_RESERVATION", (lane,))
        effect_id = f"{PYTHON_EFFECT}{epoch}:{lane}"
        version, lane_state = self.store.read_state(self.profile, _lane_aggregate(lane))
        self.store.commit_with_effect(self.profile, _lane_aggregate(lane), version,
                                      lane_state | {"lane": lane, "writer": PYTHON},
                                      effect_id, {"lane": lane, "writer": PYTHON, "epoch": epoch})
        self.store.claim_effect(self.profile, effect_id)
        if confirm:
            self.store.confirm_effect(self.profile, effect_id, f"outcome:{lane}")
            self.store.release(self.profile, RESERVATION_SCOPE, lane, owned[0].owner, owned[0].fence)
        return effect_id

    def python_reserve(self, lane: str, epoch: int) -> None:
        self.admit(PYTHON, epoch)
        self.store.acquire(self.profile, RESERVATION_SCOPE, lane, f"python:{epoch}")

    # -- rollback ---------------------------------------------------------------------------------------------
    def rollback(self) -> dict[str, object]:
        authority = self.current()
        if authority.state == ACTIVE and authority.writer == NODE:
            return {"disposition": "NODE_ALREADY_ACTIVE", "writer": NODE, "epoch": authority.epoch}
        if authority.checkpoint is None:
            raise CutoverHold("NO_CHECKPOINT")
        if authority.state == ACTIVE:
            authority = self._replace(authority, authority.hold("rollback: PYTHON stopped"))
        checkpoint_bytes = self.checkpoints.node_state(authority.checkpoint)
        unresolved = tuple(e.identity for e in self.store.pending_effects(self.profile))
        unresolved += tuple(e.identity for e in self.store.unresolved_effects(self.profile))
        unresolved += tuple(f"reservation:{r.key}" for r in self.store.recovery_reservations(self.profile)
                            if r.scope == RESERVATION_SCOPE and not r.owner.startswith(MIGRATED_OWNER))
        if unresolved:
            raise CutoverHold("PYTHON_EFFECTS_UNRECONCILED", unresolved)
        completed = {}
        for identity, status, _ in self.store.effect_ledger(self.profile):  # type: ignore[attr-defined]
            if status == "confirmed" and identity.startswith(PYTHON_EFFECT):
                completed[identity.split(":", 2)[2]] = identity
        restored = rollback_overlay(json.loads(checkpoint_bytes), completed, authority.epoch)
        returned = []
        for reservation in self.store.recovery_reservations(self.profile):
            if reservation.scope == RESERVATION_SCOPE and reservation.owner.startswith(MIGRATED_OWNER):
                self.store.release(self.profile, RESERVATION_SCOPE, reservation.key, reservation.owner, reservation.fence)
                returned.append(reservation.key)
        temporary = self.node_state.with_name(self.node_state.name + ".rollback.tmp")
        temporary.write_text(json.dumps(restored, indent=2, sort_keys=True) + "\n")
        temporary.replace(self.node_state)
        record = {"checkpoint": authority.checkpoint, "completed_by_python": completed,
                  "returned_to_node": sorted(returned), "node_state_digest": _digest(self._node_bytes()),
                  "epoch": authority.epoch}
        self.store.commit(self.profile, f"cutover:rollback:{authority.epoch}", 0, record)
        node = self._replace(authority, authority.activate(NODE, authority.checkpoint, "rollback: reconciled"))
        return {"disposition": "ROLLED_BACK", "writer": NODE, "epoch": node.epoch, "rollback": record}
