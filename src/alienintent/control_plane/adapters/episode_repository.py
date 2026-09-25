"""Immutable `episode-history` first, then the versioned `episode:<objective>` authority pointer (U-1).

The pointer carries the S2 authority fields `SQLiteOperationalStore._validate_vector` reads
(`active`, `epoch`, `invocation`, finite `expires_at`), plus the persisted UTC deadline for restart.
"""
from dataclasses import asdict
import json
from typing import Mapping

from alienintent.control_plane.domain.episode import (
    SECOND, EpisodeHold, EpisodeRecord, EpisodeState, HoldReason, canonical,
)
from alienintent.control_plane.ports.episode import EpisodeRepository
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, SchemaIncompatible

POINTER_FIELDS = {"schema_version", "active", "epoch", "invocation", "expires_at", "deadline_utc_us", "history_ref"}


class DurableEpisodeRepository(EpisodeRepository):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str, profile: str,
                 invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.profile, self.invocation = project, profile, invocation

    @staticmethod
    def identity(objective: str) -> str:
        return "episode:" + objective

    def _pointer(self, objective: str) -> tuple[int, dict[str, object]] | None:
        version, pointer = self.store.read_state(self.profile, self.identity(objective))
        if not pointer:
            return None
        if type(pointer.get("schema_version")) is not int or pointer["schema_version"] != 1:
            raise SchemaIncompatible("episode pointer requires schema_version=1")
        if set(pointer) != POINTER_FIELDS:
            raise EpisodeHold(HoldReason.INVALID_RECORD, "episode pointer shape")
        return version, pointer

    def _body(self, objective: str, ref: Ref, version: int) -> tuple[dict[str, object], Observation]:
        try:
            record = self.evidence.get(ref, frozenset({"private"}))
        except EvidenceHold as error:
            raise EpisodeHold(HoldReason.INVALID_RECORD, "episode history: " + error.reason_code) from error
        if (not isinstance(record, Observation) or record.header.logical_id != self.identity(objective)
                or record.method != "episode-history" or not isinstance(record.value, str)
                or record.header.revision != str(version)):
            raise EpisodeHold(HoldReason.INVALID_RECORD, "episode history")
        return json.loads(record.value), record

    def load(self, objective: str) -> tuple[int, EpisodeRecord | None]:
        pointer = self._pointer(objective)
        if pointer is None:
            return 0, None
        version, state = pointer
        try:
            body, _ = self._body(objective, ref_from_document(state["history_ref"]), version)
            record = EpisodeRecord.from_document(body["record"])
        except (KeyError, TypeError, ValueError, EvidenceHold) as error:
            raise EpisodeHold(HoldReason.INVALID_RECORD, "episode history body") from error
        if (record.objective != objective or record.epoch != state["epoch"] or record.invocation != state["invocation"]
                or (record.state is EpisodeState.ACTIVE) is not state["active"]
                or record.deadline_us != state["deadline_utc_us"]):
            raise EpisodeHold(HoldReason.INVALID_RECORD, "pointer and history disagree")
        return version, record

    def save(self, expected_version: int, record: EpisodeRecord, event: Mapping[str, object]) -> int:
        identity = self.identity(record.objective)
        preceding = () if expected_version == 0 else (ref_from_document(self._pointer(record.objective)[1]["history_ref"]),)
        body = {"record": record.document(), "event": dict(event)}
        source = Ref(self.project, self.profile, "episode-policy:" + record.objective, record.policy_digest,
                     "episode-policy:" + record.policy_digest.removeprefix("sha256:"))
        history = Observation(Header(self.project, self.profile, identity, str(expected_version + 1), (source,),
            preceding_refs=preceding), source, identity, "episode-history", (source,), canonical(body).decode(), None,
            "episode-invocation:" + record.invocation, self.invocation)
        ref = self.evidence.put(history)
        return self.store.commit(self.profile, identity, expected_version, {
            "schema_version": 1, "active": record.state is EpisodeState.ACTIVE, "epoch": record.epoch,
            "invocation": record.invocation, "expires_at": record.deadline_us / SECOND,
            "deadline_utc_us": record.deadline_us, "history_ref": asdict(ref)})

    def history(self, objective: str) -> tuple[dict[str, object], ...]:
        """Every event across epochs, oldest first; a broken chain holds."""
        pointer = self._pointer(objective)
        if pointer is None:
            raise KeyError(objective)
        version, state = pointer
        ref, records = ref_from_document(state["history_ref"]), []
        while ref is not None:
            body, record = self._body(objective, ref, version)
            records.append(body)
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise EpisodeHold(HoldReason.INVALID_RECORD, "history chain")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(records))
