"""Install immutable inventory observations before CAS of a derived pointer."""
from dataclasses import asdict
import json

from alienintent.context_assembly.domain.inventory import InventorySnapshot, Manifest, InventoryHold, canonical, digest
from alienintent.evidence_learning.domain.records import Header, Observation
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict


class InventoryService:
    aggregate = "upstream:requirements:current"

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str,
                 profile: str, definition_ref: Ref, invocation: str, access_scope: frozenset[str]) -> None:
        self.repository, self.store = repository, store
        self.project, self.profile, self.definition_ref = project, profile, definition_ref
        self.invocation, self.access_scope = invocation, access_scope

    def read(self) -> tuple[int, dict | None]:
        version, document, _, _ = self._read_current()
        return version, document

    def _read_current(self) -> tuple[int, dict | None, Ref | None, str]:
        version, state = self.store.read_state(self.profile, self.aggregate)
        if version == 0 and not state:
            return 0, None, None, "public"
        if set(state) != {"schema_version", "snapshot_ref", "snapshot_digest"} or state["schema_version"] != 1:
            raise InventoryHold("INVALID_INVENTORY_POINTER")
        ref = Ref(**state["snapshot_ref"])
        if (ref.project, ref.profile) != (self.project, self.profile):
            raise InventoryHold("PROJECT_MISMATCH")
        record = self.repository.get(ref, self.access_scope)
        if not isinstance(record, Observation) or record.evidence_id != "inventory.snapshot":
            raise InventoryHold("INVALID_INVENTORY_OBSERVATION")
        document = json.loads(record.value)
        if digest(document) != state["snapshot_digest"] or document["project"] != self.project:
            raise InventoryHold("SNAPSHOT_DIGEST_MISMATCH")
        # Every source/manifest object must remain retrievable, not merely the pointer.
        for source_ref in record.input_refs + record.header.preceding_refs:
            self.repository.get(source_ref, self.access_scope)
        return version, document, ref, record.header.access_label

    def publish(self, manifest: Manifest, snapshot: InventorySnapshot, expected_version: int) -> tuple[int, Ref]:
        if manifest.project != self.project or snapshot.project != self.project:
            raise InventoryHold("PROJECT_MISMATCH")
        if snapshot.source_manifest_digest != digest([asdict(s) for s in sorted(manifest.entries, key=lambda s: (s.path, s.revision))]):
            raise InventoryHold("MANIFEST_DIGEST_MISMATCH")
        version, current, current_ref, prior_access = self._read_current()
        if version != expected_version:
            raise VersionConflict("read current inventory and reevaluate")
        if current is not None and snapshot.prior_snapshot != digest(current) and snapshot.digest != digest(current):
            raise InventoryHold("PRIOR_SNAPSHOT_MISMATCH")
        if current is None and snapshot.prior_snapshot is not None:
            raise InventoryHold("MISSING_PRIOR_SNAPSHOT")
        if current is not None and digest(current) == snapshot.digest:
            return version, current_ref
        access = "private" if prior_access == "private" or any(e.access_label == "private" for e in manifest.entries) else "public"
        manifest_body = canonical(asdict(manifest))
        manifest_record = Observation(Header(self.project, self.profile, "inventory.manifest:"+snapshot.source_manifest_digest,
                                             snapshot.source_manifest_digest, (self.definition_ref,), access),
                                      self.definition_ref, "inventory.manifest", "explicit-source-manifest", (), manifest_body,
                                      None, "requirements_inventory", self.invocation)
        manifest_ref = self.repository.put(manifest_record)
        self.repository.get(manifest_ref, self.access_scope)
        record = Observation(Header(self.project, self.profile, "inventory.snapshot:"+snapshot.digest, snapshot.digest,
                                    (manifest_ref,), access, (current_ref,) if current_ref else ()), self.definition_ref, "inventory.snapshot", "requirements_inventory/v1",
                             (manifest_ref,), canonical(asdict(snapshot)), None, "requirements_inventory", self.invocation)
        ref = self.repository.put(record)
        self.repository.get(ref, self.access_scope)
        new_version = self.store.commit(self.profile, self.aggregate, expected_version,
                                        {"schema_version": 1, "snapshot_ref": asdict(ref), "snapshot_digest": snapshot.digest})
        return new_version, ref
