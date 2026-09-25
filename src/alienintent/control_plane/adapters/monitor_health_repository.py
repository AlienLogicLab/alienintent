"""Immutable monitor history first, then a versioned `monitor:<profile>` pointer."""
from dataclasses import asdict
import json

from alienintent.control_plane.domain.monitor_health import (
    MonitorHealth, MonitorHold, MonitorPolicy, MonitorSnapshot, Unavailable,
)
from alienintent.control_plane.ports.monitor_health import MonitorRepository
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, SchemaIncompatible, StoreUnavailable


class DurableMonitorRepository(MonitorRepository):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str,
                 name: str, invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.name, self.invocation = project, name, invocation

    @staticmethod
    def identity(profile: str) -> str:
        return "monitor:" + profile

    def _record(self, identity: str, ref: Ref, version: int) -> Observation:
        record = self.evidence.get(ref, frozenset({"private"}))
        if (not isinstance(record, Observation) or record.header.logical_id != identity
                or record.method != "monitor-history" or not isinstance(record.value, str)):
            raise MonitorHold("INVALID_MONITOR_HISTORY")
        if record.header.revision != str(version):
            raise MonitorHold("HISTORY_VERSION_MISMATCH")
        return record

    def _pointer(self, profile: str) -> tuple[int, Ref] | None:
        version, pointer = self.store.read_state(self.name, self.identity(profile))
        if not pointer:
            return None
        if type(pointer.get("schema_version")) is not int or pointer["schema_version"] != 1:
            raise SchemaIncompatible("monitor pointer requires schema_version=1")
        try:
            return version, ref_from_document(pointer["history_ref"])
        except (KeyError, TypeError, ValueError, EvidenceHold) as error:
            raise MonitorHold("INVALID_MONITOR_POINTER") from error

    def _load(self, profile: str) -> MonitorSnapshot | None:
        pointer = self._pointer(profile)
        if pointer is None:
            return None
        version, ref = pointer
        try:
            body = json.loads(self._record(self.identity(profile), ref, version).value)
            policy, record = MonitorPolicy(**body["policy"]), MonitorHealth(**body["record"])
        except (KeyError, TypeError, ValueError) as error:
            raise MonitorHold("INVALID_MONITOR_HISTORY") from error
        if record.profile != profile or record.policy_digest != policy.digest():
            raise MonitorHold("INVALID_MONITOR_HISTORY")
        return MonitorSnapshot(version, record, policy, ref)

    def snapshot(self, profile: str) -> MonitorSnapshot | None | Unavailable:
        try:
            return self._load(profile)
        except StoreUnavailable:
            return Unavailable("STORE_UNAVAILABLE")
        except SchemaIncompatible:
            return Unavailable("SCHEMA_INCOMPATIBLE")
        except EvidenceHold as error:
            return Unavailable("EVIDENCE_" + error.reason_code)
        except MonitorHold as error:
            return Unavailable(error.reason)

    def read(self, profile: str) -> MonitorHealth | None | Unavailable:
        snapshot = self.snapshot(profile)
        return snapshot if snapshot is None or isinstance(snapshot, Unavailable) else snapshot.record

    def save(self, expected_version: int, record: MonitorHealth, policy: MonitorPolicy,
             observation: dict[str, object], preceding: MonitorSnapshot | None) -> MonitorSnapshot:
        identity = self.identity(record.profile)
        if record.policy_digest != policy.digest():
            raise MonitorHold("POLICY_DIGEST_MISMATCH")
        source = Ref(self.project, self.name, "monitor-policy:" + record.profile, record.policy_digest,
                     "monitor-policy:" + record.policy_digest.removeprefix("sha256:"))
        body = {"record": asdict(record), "policy": policy.document(), "observation": observation}
        history = Observation(Header(self.project, self.name, identity, str(expected_version + 1), (source,),
            preceding_refs=() if preceding is None else (preceding.history_ref,)), source, identity,
            "monitor-history", (source,), canonical_bytes(body).decode(), None,
            "monitor-instance:" + record.instance_id, self.invocation)
        ref = self.evidence.put(history)
        version = self.store.commit(self.name, identity, expected_version,
            {"schema_version": 1, "history_ref": asdict(ref)})
        return MonitorSnapshot(version, record, policy, ref)

    def history(self, profile: str) -> tuple[dict[str, object], ...]:
        """Every observation across generations, oldest first; a broken chain holds."""
        pointer = self._pointer(profile)
        if pointer is None:
            raise KeyError(profile)
        version, ref = pointer
        records = []
        while ref is not None:
            record = self._record(self.identity(profile), ref, version)
            records.append(json.loads(record.value))
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise MonitorHold("HISTORY_CHAIN_MISMATCH")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(records))
