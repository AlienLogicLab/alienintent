"""Pin a context manifest, then reconstruct only from pinned durable records and evidence."""
from dataclasses import asdict
from hashlib import sha256
import json

from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.context_assembly.domain.inventory import InventoryHold
from alienintent.context_assembly.domain.reconstruction import (
    DERIVATION_RULE, INVENTORY, POINTER_PREFIX, RECORD_PREFIXES, RULE_TEXT, SINGLE_RECORDS, ContextHold, HoldReason,
    ReconstructedContext, canonical, decode_attention, derive, digest, pin_manifest, validate_manifest,
)
from alienintent.context_assembly.ports.context_assembler import ContextAssembler
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore, SchemaIncompatible, StoreUnavailable, VersionConflict,
)

_SCOPE = frozenset({"public", "private"})


def _decoded(value: str, reason: HoldReason, ref: str) -> object:
    try:
        return json.loads(value)
    except ValueError as error:
        raise ContextHold(reason, (ref,), "undecodable body") from error


class ContextReconstructionService(ContextAssembler):
    def __init__(self, store: OperationalStore, evidence: EvidenceRepository, *, project: str, profile: str,
                 invocation: str) -> None:
        self.store, self.evidence = store, evidence
        self.project, self.profile, self.invocation = project, profile, invocation
        self.definition_ref = Ref(project, profile, "context-reconstruction/v1",
                                  "sha256:" + sha256(RULE_TEXT.encode()).hexdigest(), "rule:" + DERIVATION_RULE)

    def _read(self, aggregate: str) -> tuple[int, dict[str, object]]:
        try:
            return self.store.read_state(self.profile, aggregate)
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise ContextHold(HoldReason.STORE_UNAVAILABLE, (aggregate,), str(error)) from error

    def _enumerate(self) -> tuple[tuple[str, int, dict[str, object]], ...]:
        try:
            listed = [row for prefix in RECORD_PREFIXES for row in self.store.list_states(self.profile, prefix)]
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise ContextHold(HoldReason.STORE_UNAVAILABLE, RECORD_PREFIXES, str(error)) from error
        return (*listed, *((aggregate, *self._read(aggregate)) for aggregate in SINGLE_RECORDS))

    def _get(self, ref: Ref, owner: str) -> object:
        try:
            return self.evidence.get(ref, _SCOPE)
        except (EvidenceHold, StoreUnavailable, SchemaIncompatible) as error:
            reason = HoldReason.INVENTORY_UNAVAILABLE if owner == INVENTORY else HoldReason.EVIDENCE_UNAVAILABLE
            raise ContextHold(reason, (owner,), str(error)) from error

    def _inventory(self) -> None:
        # Reuse the U1 reader rather than duplicating its pointer/snapshot checks.
        reader = InventoryService(self.evidence, self.store, self.project, self.profile, self.definition_ref,
                                  self.invocation, _SCOPE)
        try:
            reader.read()
        except (InventoryHold, EvidenceHold, KeyError, TypeError, ValueError) as error:
            raise ContextHold(HoldReason.INVENTORY_UNAVAILABLE, (INVENTORY,), str(error)) from error
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise ContextHold(HoldReason.STORE_UNAVAILABLE, (INVENTORY,), str(error)) from error

    def pin(self) -> str:
        """Return the pointer for the current durable state; raises ContextHold rather than pinning a guess."""
        try:
            return self._pin()
        except EvidenceHold as error:
            raise ContextHold(HoldReason.EVIDENCE_UNAVAILABLE, (), str(error)) from error
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise ContextHold(HoldReason.STORE_UNAVAILABLE, (), str(error)) from error

    def _pin(self) -> str:
        manifest = pin_manifest(self.project, self.profile, self._enumerate())
        self._inventory()
        refs = tuple(ref_from_document(entry["ref"]) for entry in manifest["evidence"])
        for entry, ref in zip(manifest["evidence"], refs):
            self._get(ref, entry["owner"])
        manifest_digest = digest(manifest)
        pointer = POINTER_PREFIX + manifest_digest.removeprefix("sha256:")
        _, existing = self._read(pointer)
        if existing:
            if existing.get("manifest_digest") != manifest_digest:
                raise ContextHold(HoldReason.DIGEST_MISMATCH, (pointer,), "existing pointer differs")
            return pointer
        record = Observation(Header(self.project, self.profile, "context.manifest:" + manifest_digest, manifest_digest,
                                    (self.definition_ref, *refs)), self.definition_ref, "context.manifest",
                             "context-manifest/v1", refs, canonical(manifest).decode(), None, "context_assembly",
                             self.invocation)
        ref = self.evidence.put(record)
        self._get(ref, pointer)
        wanted = {"schema_version": 1, "manifest_ref": asdict(ref), "manifest_digest": manifest_digest}
        try:
            self.store.commit(self.profile, pointer, 0, wanted)
        except VersionConflict as error:
            # A concurrent pinner of the same content is equivalent; anything else is a stale-input hold.
            if self._read(pointer)[1].get("manifest_digest") == manifest_digest:
                return pointer
            raise ContextHold(HoldReason.VERSION_DRIFT, (pointer,), "concurrent pointer install") from error
        if self._read(pointer)[1] != wanted:
            raise ContextHold(HoldReason.DIGEST_MISMATCH, (pointer,), "pointer read-back differs")
        return pointer

    def reconstruct(self, manifest_ref: str) -> ReconstructedContext | ContextHold:
        try:
            return self._reconstruct(manifest_ref)
        except ContextHold as hold:
            return hold

    def _reconstruct(self, manifest_ref: str) -> ReconstructedContext:
        if not isinstance(manifest_ref, str) or not manifest_ref.startswith(POINTER_PREFIX):
            raise ContextHold(HoldReason.INVALID_MANIFEST, (str(manifest_ref),))
        _, pointer = self._read(manifest_ref)
        if not pointer:
            raise ContextHold(HoldReason.MISSING_RECORD, (manifest_ref,), "manifest pointer is absent")
        if set(pointer) != {"schema_version", "manifest_ref", "manifest_digest"} or pointer["schema_version"] != 1:
            raise ContextHold(HoldReason.INVALID_MANIFEST, (manifest_ref,), "pointer shape")
        try:
            observation_ref = ref_from_document(pointer["manifest_ref"])
        except (EvidenceHold, TypeError) as error:
            raise ContextHold(HoldReason.INVALID_MANIFEST, (manifest_ref,), str(error)) from error
        record = self._get(observation_ref, manifest_ref)
        if not isinstance(record, Observation) or record.evidence_id != "context.manifest" or not isinstance(record.value, str):
            raise ContextHold(HoldReason.INVALID_MANIFEST, (manifest_ref,), "manifest observation")
        manifest = _decoded(record.value, HoldReason.INVALID_MANIFEST, manifest_ref)
        try:
            manifest_digest = digest(manifest)
        except ValueError as error:
            raise ContextHold(HoldReason.INVALID_MANIFEST, (manifest_ref,), "noncanonical manifest") from error
        if manifest_digest != pointer["manifest_digest"] or manifest_ref != POINTER_PREFIX + manifest_digest.removeprefix("sha256:"):
            raise ContextHold(HoldReason.DIGEST_MISMATCH, (manifest_ref,), "manifest digest")
        manifest = validate_manifest(manifest, self.project, self.profile)
        records, versions = {}, {}
        for entry in manifest["entries"]:
            aggregate = entry["aggregate"]
            version, state = self._read(aggregate)
            if entry["version"] > 0 and version == 0 and not state:
                raise ContextHold(HoldReason.MISSING_RECORD, (aggregate,), "pinned record is absent")
            if version != entry["version"]:
                raise ContextHold(HoldReason.VERSION_DRIFT, (aggregate,), f"pinned {entry['version']}, store {version}")
            if digest(state) != entry["digest"]:
                raise ContextHold(HoldReason.DIGEST_MISMATCH, (aggregate,), "pinned record digest")
            records[aggregate], versions[aggregate] = state, version
        unpinned = sorted(a for a, _, _ in self._enumerate() if a not in records)
        if unpinned:
            raise ContextHold(HoldReason.VERSION_DRIFT, tuple(unpinned), "record created after pinning")
        if records.get(INVENTORY):
            self._inventory()
        attention = []
        for entry in manifest["evidence"]:
            owner = entry["owner"]
            try:
                ref = ref_from_document(entry["ref"])
            except (EvidenceHold, TypeError) as error:
                raise ContextHold(HoldReason.INVALID_MANIFEST, (owner,), str(error)) from error
            body = self._get(ref, owner)
            if owner.startswith("attention:"):
                if (not isinstance(body, Observation) or body.method != "attention-history"
                        or body.header.logical_id != owner or body.header.revision != str(versions[owner])
                        or not isinstance(body.value, str)):
                    raise ContextHold(HoldReason.MALFORMED_RECORD, (owner,), "attention history")
                attention.append(decode_attention(owner, versions[owner],
                                                  _decoded(body.value, HoldReason.MALFORMED_RECORD, owner)))
        missing = sorted(a for a, state in records.items() if a.startswith("attention:") and state
                         and a not in {e["owner"] for e in manifest["evidence"]})
        if missing:
            raise ContextHold(HoldReason.EVIDENCE_UNAVAILABLE, tuple(missing), "unpinned attention history")
        document = derive(manifest, records, attention)
        return ReconstructedContext(manifest_ref, pointer["manifest_digest"],
                                    {"revision_digest": observation_ref.revision_digest, "locator": observation_ref.locator},
                                    document, digest(document))

    def retain(self, context: ReconstructedContext, observer: str) -> Ref:
        """Retain a reconstruction output as an immutable S1 observation."""
        manifest_ref = Ref(self.project, self.profile, "context.manifest:" + context.manifest_digest,
                           context.manifest_observation["revision_digest"], context.manifest_observation["locator"])
        record = Observation(Header(self.project, self.profile, "context.reconstruction:" + context.manifest_digest,
                                    context.digest, (manifest_ref,)), self.definition_ref, "context.reconstruction",
                             DERIVATION_RULE, (manifest_ref,), canonical(context.document).decode(), None, observer,
                             self.invocation)
        return self.evidence.put(record)
