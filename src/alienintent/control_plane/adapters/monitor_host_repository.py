"""Supervisor-owned `monitor-host:<profile>` ownership: immutable history first, then the pointer."""
from dataclasses import asdict
import json

from alienintent.control_plane.domain.monitor_host import HostHold, HostOwnership
from alienintent.control_plane.ports.monitor_host import HostRecords
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, SchemaIncompatible, StoreUnavailable

METHOD = "monitor-host-history"


class DurableHostRecords(HostRecords):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str, name: str,
                 invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.name, self.invocation = project, name, invocation

    @staticmethod
    def identity(profile: str) -> str:
        return "monitor-host:" + profile

    def _record(self, identity: str, ref: Ref, version: int) -> Observation:
        record = self.evidence.get(ref, frozenset({"private"}))
        if (not isinstance(record, Observation) or record.header.logical_id != identity
                or record.method != METHOD or not isinstance(record.value, str)):
            raise HostHold("INVALID_HOST_HISTORY")
        if record.header.revision != str(version):
            raise HostHold("HOST_HISTORY_VERSION_MISMATCH")
        return record

    def _pointer(self, profile: str) -> tuple[int, Ref | None]:
        try:
            version, pointer = self.store.read_state(self.name, self.identity(profile))
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise HostHold("HOST_STORE_UNAVAILABLE") from error
        if not pointer:
            return version, None
        if pointer.get("schema_version") != 1:
            raise HostHold("HOST_POINTER_SCHEMA_INCOMPATIBLE")
        try:
            return version, ref_from_document(pointer["history_ref"])
        except (KeyError, TypeError, ValueError, EvidenceHold) as error:
            raise HostHold("INVALID_HOST_POINTER") from error

    def read(self, profile: str) -> tuple[int, HostOwnership | None]:
        version, ref = self._pointer(profile)
        if ref is None:
            return version, None
        try:
            body = json.loads(self._record(self.identity(profile), ref, version).value)
        except (EvidenceHold, ValueError) as error:
            raise HostHold("INVALID_HOST_HISTORY") from error
        ownership = HostOwnership.from_document(body["ownership"])
        if ownership.binding.profile != profile:
            raise HostHold("INVALID_HOST_HISTORY")
        return version, ownership

    def save(self, expected_version: int, ownership: HostOwnership, observation: dict[str, object]) -> int:
        profile = ownership.binding.profile
        identity = self.identity(profile)
        version, preceding = self._pointer(profile)
        if version != expected_version:
            raise HostHold("HOST_VERSION_CONFLICT")
        source = Ref(self.project, self.name, "monitor-host-config:" + profile, ownership.config_digest,
                     "monitor-host-config:" + ownership.config_digest.removeprefix("sha256:"))
        body = {"ownership": ownership.document(), "observation": observation}
        history = Observation(Header(self.project, self.name, identity, str(expected_version + 1), (source,),
            preceding_refs=() if preceding is None else (preceding,)), source, identity, METHOD, (source,),
            canonical_bytes(body).decode(), None, "monitor-host-launch:" + ownership.launch_id, self.invocation)
        ref = self.evidence.put(history)
        return self.store.commit(self.name, identity, expected_version, {"schema_version": 1, "history_ref": asdict(ref)})

    def history(self, profile: str) -> tuple[dict[str, object], ...]:
        """Every supervisor record for the profile, oldest first; a broken chain holds."""
        version, ref = self._pointer(profile)
        records = []
        while ref is not None:
            record = self._record(self.identity(profile), ref, version)
            records.append(json.loads(record.value))
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise HostHold("HOST_HISTORY_CHAIN_MISMATCH")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(records))
