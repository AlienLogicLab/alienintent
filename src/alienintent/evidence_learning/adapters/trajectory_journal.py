"""Trajectory capture journal over the typed evidence repository and the operational store.

The same write discipline as the supervisor-owned `monitor-host:<profile>` history: each entry
is an immutable, content-addressed `Observation` chained to its predecessor, and the head
pointer in SQLite advances by compare-and-set only after the entry is installed. A crash
between the two leaves an unreferenced object and no accepted entry.
"""
from collections.abc import Mapping
from dataclasses import asdict
import json

from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.domain.trajectory_capture import CaptureHold, digest
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.evidence_learning.ports.trajectory_journal import TrajectoryJournal
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore, ReservationRejected, SchemaIncompatible, StoreUnavailable, VersionConflict,
)

METHOD = "trajectory-capture-journal"


class DurableTrajectoryJournal(TrajectoryJournal):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str, name: str,
                 stream: str, invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.name, self.stream, self.invocation = project, name, stream, invocation
        self.identity = "trajectory-capture:" + stream

    def _pointer(self) -> tuple[int, Ref | None]:
        try:
            version, pointer = self.store.read_state(self.name, self.identity)
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise CaptureHold("JOURNAL_STORE_UNAVAILABLE") from error
        if not pointer:
            return version, None
        if pointer.get("schema_version") != 1:
            raise CaptureHold("JOURNAL_POINTER_SCHEMA_INCOMPATIBLE")
        try:
            return version, ref_from_document(pointer["head_ref"])
        except (KeyError, TypeError, ValueError, EvidenceHold) as error:
            raise CaptureHold("JOURNAL_POINTER_INVALID") from error

    def _record(self, ref: Ref, version: int) -> Observation:
        try:
            record = self.evidence.get(ref, frozenset({"private"}))
        except EvidenceHold as error:
            raise CaptureHold("JOURNAL_ENTRY_UNREADABLE:" + error.reason_code) from error
        except StoreUnavailable as error:
            raise CaptureHold("JOURNAL_STORE_UNAVAILABLE") from error
        if (not isinstance(record, Observation) or record.header.logical_id != self.identity
                or record.method != METHOD or not isinstance(record.value, str)):
            raise CaptureHold("JOURNAL_ENTRY_INVALID")
        if record.header.revision != str(version):
            raise CaptureHold("JOURNAL_VERSION_MISMATCH")
        return record

    def version(self) -> int:
        return self._pointer()[0]

    def append(self, expected_version: int, entry: Mapping[str, object]) -> int:
        version, preceding = self._pointer()
        if version != expected_version:
            raise CaptureHold("JOURNAL_VERSION_CONFLICT")
        if entry.get("entry_seq") != expected_version + 1:
            raise CaptureHold("JOURNAL_ENTRY_OUT_OF_SEQUENCE")
        stream = digest({"project": self.project, "profile": self.name, "stream": self.stream})
        source = Ref(self.project, self.name, "trajectory-capture-stream:" + self.stream, stream,
                     "trajectory-capture-stream:" + stream.removeprefix("sha256:"))
        record = Observation(Header(self.project, self.name, self.identity, str(expected_version + 1), (source,),
            preceding_refs=() if preceding is None else (preceding,)), source, self.identity, METHOD, (source,),
            canonical_bytes(dict(entry)).decode(), None, "trajectory-capture-launch:" + str(entry.get("launch_id")),
            self.invocation)
        try:
            ref = self.evidence.put(record)
            return self.store.commit(self.name, self.identity, expected_version,
                                     {"schema_version": 1, "head_ref": asdict(ref)})
        except VersionConflict as error:
            raise CaptureHold("JOURNAL_VERSION_CONFLICT") from error
        except (StoreUnavailable, SchemaIncompatible, ReservationRejected, EvidenceHold) as error:
            raise CaptureHold("JOURNAL_STORE_UNAVAILABLE") from error

    def entries(self) -> tuple[dict[str, object], ...]:
        """Every committed entry, oldest first; a broken chain or renumbered entry holds."""
        version, ref = self._pointer()
        entries = []
        while ref is not None:
            record = self._record(ref, version)
            entry = json.loads(record.value)
            if entry.get("entry_seq") != version:
                raise CaptureHold("JOURNAL_CHAIN_MISMATCH")
            entries.append(entry)
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise CaptureHold("JOURNAL_CHAIN_MISMATCH")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(entries))
