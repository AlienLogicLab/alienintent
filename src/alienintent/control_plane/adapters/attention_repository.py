"""Immutable history first, then a versioned pointer in the existing store."""
from dataclasses import asdict
import json

from alienintent.control_plane.domain.attention import AttentionHold, AttentionItem, Resolution
from alienintent.control_plane.ports.attention import AttentionRepository
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, SchemaIncompatible


class DurableAttentionRepository(AttentionRepository):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str,
                 profile: str, invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.profile, self.invocation = project, profile, invocation

    def _record(self, identity: str, ref: Ref) -> Observation:
        record = self.evidence.get(ref, frozenset({"private"}))
        if (not isinstance(record, Observation) or record.header.logical_id != identity
                or record.method != "attention-history" or not isinstance(record.value, str)):
            raise AttentionHold("INVALID_ATTENTION_HISTORY")
        return record

    def load(self, identity: str) -> tuple[int, dict[str, object], Ref]:
        version, pointer = self.store.read_state(self.profile, identity)
        if not pointer:
            raise KeyError(identity)
        if type(pointer.get("schema_version")) is not int or pointer["schema_version"] != 1:
            raise SchemaIncompatible("attention pointer requires schema_version=1")
        ref = ref_from_document(pointer["history_ref"])
        record = self._record(identity, ref)
        if record.header.revision != str(version):
            raise AttentionHold("HISTORY_VERSION_MISMATCH")
        # A missing historical object cannot silently disappear on the next write.
        self.history(identity)
        return version, json.loads(record.value), ref

    def save(self, identity: str, expected_version: int, body: dict[str, object], source: Ref,
             actor: str, preceding: Ref | None) -> tuple[int, Ref]:
        if not identity.startswith(("attention:", "attention-stage:", "attention-delivery:")):
            raise AttentionHold("INVALID_ATTENTION_NAMESPACE")
        record = Observation(Header(self.project, self.profile, identity, str(expected_version + 1),
            (source,), preceding_refs=() if preceding is None else (preceding,)), source,
            identity, "attention-history", (source,), canonical_bytes(body).decode(), None,
            actor, self.invocation)
        ref = self.evidence.put(record)
        version = self.store.commit(self.profile, identity, expected_version,
            {"schema_version": 1, "history_ref": asdict(ref)})
        return version, ref

    def validate_resolution(self, item: AttentionItem, decision: Resolution) -> None:
        record = self.evidence.get(decision.decision_ref, frozenset({"private"}))
        expected = {"item_identity": item.identity, "actor": decision.actor,
                    "authority": decision.authority, "work_revision": decision.work_revision,
                    "lane": decision.lane, "expected_version": decision.expected_version}
        if (not isinstance(record, Observation) or record.method != "attention-resolution"
                or record.evidence_id != item.identity or record.observer != decision.actor
                or item.history_ref not in record.input_refs
                or record.value != canonical_bytes(expected).decode()):
            raise AttentionHold("INVALID_RESOLVING_DECISION")

    def identities(self, prefix: str) -> tuple[str, ...]:
        return tuple(identity for identity, _, _ in self.store.list_states(self.profile, prefix))

    def history(self, identity: str) -> tuple[dict[str, object], ...]:
        version, pointer = self.store.read_state(self.profile, identity)
        if not pointer:
            raise KeyError(identity)
        ref = ref_from_document(pointer["history_ref"])
        records = []
        while ref is not None:
            record = self._record(identity, ref)
            if record.header.revision != str(version):
                raise AttentionHold("HISTORY_VERSION_MISMATCH")
            records.append(json.loads(record.value))
            resolution_ref = records[-1].get("resolution_ref")
            if resolution_ref is not None:
                self.evidence.get(ref_from_document(resolution_ref), frozenset({"private"}))
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise AttentionHold("HISTORY_CHAIN_MISMATCH")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(records))
