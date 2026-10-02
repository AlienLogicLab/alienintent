"""Initial compilation (U8) for one store/profile: design gate, pinned inputs, registered identities, derivation,
packets committed to Git, published refs, one record.

Order: the U5 design gate and the retained design of that exact verified revision, then the current U1 inventory,
U2 inspection and U4 proof plans. Then identities: the old upstream:identity-reservations record of every configured
profile of the project is read (each from that profile's own operational database); a requirement any record maps
must already be migrated (MIGRATION_INCOMPLETE otherwise), and one project-database transaction registers every
requirement through the work identity service (a retired row holds IDENTITY_RETIRED). compile_initial receives the
unit_key -> identity map, so every digest is final. A derived candidate's packets are then committed on the packets
branch and every unit's pointer is set in ONE write transaction that also checks that no unit past CAPTURE would
change (POINTER_PRESENT); the packets branch and the units' work/<id> tags are published through publish_refs
(PUBLICATION_FAILED holds); only then is the candidate retained as an immutable Observation bound by an
upstream:initial-compilation:<input digest> pointer. The reservation aggregate is never written. Nothing here writes
factory:* or release:* state, Issues or work-management projections; a candidate is admitted for assessment only.
"""
from dataclasses import asdict
from hashlib import sha256
import json

from collections.abc import Mapping
from dataclasses import dataclass

from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.domain.ambiguity import AmbiguityHold, snapshot_from_document
from alienintent.context_assembly.domain.compilation import INITIAL, CompilationHold, canonical, digest, hold
from alienintent.context_assembly.domain.initial_compilation import (
    CompilationCandidate, compile_initial, input_digest, is_initial_compilation, packet_bytes, unit_key)
from alienintent.context_assembly.domain.inventory import InventoryHold
from alienintent.context_assembly.domain.work_identity import (
    CAPTURE, RESERVATIONS, CloneUnavailable, IdentityRetired, MigrationIncomplete, Pointer, PointerPresent,
    UnknownWorkItem, WorkItem, valid_path)
from alienintent.context_assembly.ports.compilation import (
    DependencyLifecycle, DesignGate, InspectionSource, InventorySource, ProofPlans, VerifiedDesigns)
from alienintent.context_assembly.ports.work_item_repository import (
    PacketRef, PublicationFailed, RefPublisher, RepositoryLocation, WorkItemRepository)
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict

DERIVED_EVENT, HELD_EVENT = "compilation.derived", "compilation.held"
UNREADABLE = (AmbiguityHold, InventoryHold, EvidenceHold, KeyError, TypeError, ValueError)
# Holds of the identity and pointer steps: returned before _persist, nothing committed for them.
IDENTITY_HOLDS = (MigrationIncomplete, IdentityRetired)
POINTER_HOLDS = (PointerPresent, CloneUnavailable)


@dataclass(frozen=True)
class PacketLocation:
    """Where compiled packets live: a configured repository name, its location, and the packets directory."""
    repo: str
    directory: str
    location: RepositoryLocation

    def __post_init__(self) -> None:
        if not self.repo or not valid_path(self.directory):
            raise ValueError(f"packet location is not a repository and relative directory: {self!r}")


@dataclass(frozen=True)
class WorkRegistration:
    """The project-level identity collaborators composition injects into the compiler."""
    identities: WorkIdentityService
    items: WorkItemRepository
    publisher: RefPublisher
    packets: PacketLocation
    profile_stores: Mapping[str, OperationalStore]


class InitialCompilation:
    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, access_scope: frozenset[str], design: DesignGate,
                 designs: VerifiedDesigns, inventory: InventorySource, inspection: InspectionSource,
                 proofs: ProofPlans, lifecycle: DependencyLifecycle, registration: WorkRegistration) -> None:
        self.repository, self.store, self.project, self.profile = repository, store, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope
        self.design, self.designs, self.inventory, self.inspection = design, designs, inventory, inspection
        self.proofs, self.lifecycle, self.registration = proofs, lifecycle, registration
        if profile not in registration.profile_stores:
            raise ValueError(f"profile {profile} is not a configured profile of the project")

    @staticmethod
    def aggregate(identity: str) -> str:
        return "upstream:initial-compilation:" + identity.removeprefix("sha256:")

    def compile(self, design_key: str, design_vector: dict,
                authority_limits: dict) -> CompilationCandidate | CompilationHold:
        """Derive the INITIAL candidate of one verified design; it takes no mapping or unit input."""
        decision = self.design.admit(design_key, design_vector)
        if not decision.admitted:
            return self._persist(hold(INITIAL, digest({"design_key": design_key, "design_vector": design_vector}),
                                      [("DESIGN_HOLD", (design_key,))], decision.reason_code))
        design = self.designs.design(design_key, getattr(decision.applicability, "design_digest", ""))
        if design is None:
            return self._persist(hold(INITIAL, digest({"design_key": design_key, "design_vector": design_vector}),
                                      [("DESIGN_HOLD", (design_key,))], "DESIGN_UNREADABLE"))
        try:
            _, document = self.inventory.read()
            inventory = snapshot_from_document(document) if document else None
            inspection = self.inspection.report()
        except UNREADABLE as error:
            return self._persist(hold(INITIAL, digest({"design": design.digest}),
                                      [("INPUT_UNPINNED", ("unreadable:" + type(error).__name__,))]))
        plans = {r: self.proofs.document(r) for r in sorted(design.requirements)}
        existing = authority_limits.get("existing_decomposition") if isinstance(authority_limits, dict) else None
        # Only well-formed identities are looked up; a malformed value reaches compile_initial and holds there.
        stages = {i: self.lifecycle.stage(i) for i in sorted({
            i for ids in (existing.values() if isinstance(existing, dict) else ()) if isinstance(ids, list)
            for i in ids if isinstance(i, str)})}
        review_digest = getattr(decision.applicability, "review_digest", "")
        registered = self._register(sorted(design.requirements), input_digest(
            inventory, inspection, design, review_digest, plans, authority_limits, stages))
        if isinstance(registered, CompilationHold):
            return registered
        result = compile_initial(inventory, inspection, design, review_digest, plans, authority_limits,
                                 {unit_key(r): item.id for r, item in registered.items()}, stages)
        if isinstance(result, CompilationCandidate):
            held = self._point_and_publish(result)
            if held is not None:
                return held
        return self._persist(result)

    def _register(self, requirements: list[str], identity: str) -> dict[str, WorkItem] | CompilationHold:
        """Every configured profile's old assignment checked, then every requirement registered, in one transaction
        on the project database; a hold rolls back so nothing is registered."""
        reg = self.registration
        records = {}
        for profile, store in sorted(reg.profile_stores.items()):  # Sequential reads, each its own database.
            _, state = store.read_state(profile, RESERVATIONS)
            records[profile] = state.get("reservations") or {}
        try:
            with reg.items.transaction():
                missing = []
                for requirement in requirements:
                    key = unit_key(requirement)
                    for profile, mapping in records.items():
                        name = mapping.get(key)
                        if name is None:
                            continue
                        row = reg.items.find(name) if isinstance(name, str) else None
                        if row is None or row.id != name or row.request_ref != key:
                            missing.append(f"{requirement}:{profile}")
                if missing:
                    raise MigrationIncomplete(*sorted(missing))
                items = {r: reg.identities.register(unit_key(r), unit_key(r), "BIU") for r in requirements}
                retired = [f"{r}:{item.id}" for r, item in items.items() if item.retired]
                if retired:
                    raise IdentityRetired(*retired)
        except IDENTITY_HOLDS as error:
            return hold(INITIAL, identity, [(error.code, error.values)])
        return items

    def _point_and_publish(self, candidate: CompilationCandidate) -> CompilationHold | None:
        """One write transaction: read every unit's row, refuse if a unit past CAPTURE would change, then commit each
        packet to Git and set each pointer; after COMMIT (tags set) publish the packets branch and the units' tags."""
        reg, packets = self.registration, self.registration.packets
        units = [(u["identity"], packet_bytes(u)) for u in candidate.body["units"]]
        pointed: dict[str, WorkItem] = {}
        try:
            with reg.items.transaction():
                rows = {i: self._row(i) for i, _ in units}
                present = [i for i, data in units if rows[i].state != CAPTURE and (
                    rows[i].pointer is None or not reg.items.holds(rows[i].pointer.with_instructions(data)))]
                if present:
                    raise PointerPresent(*present)
                for identity, data in units:
                    path = f"{packets.directory}/{identity}.json"
                    commit = reg.items.commit_packet(packets.repo, path, data, rows[identity].pointer)
                    pointed[identity] = reg.items.set_pointer(identity, Pointer(packets.repo, path, commit, data))
        except POINTER_HOLDS as error:
            return hold(INITIAL, candidate.input_digest, [(error.code, error.values)])
        head = reg.items.packets_head(packets.repo)
        if head is None:  # The transaction above left every unit on the packets branch; a missing branch is a fault.
            return hold(INITIAL, candidate.input_digest, [("CLONE_UNAVAILABLE", (str(packets.location.clone),))])
        refs = (PacketRef("refs/heads/" + packets.location.packets_branch, head, force=False),) + tuple(
            PacketRef(item.tag, item.pointer.commit, force=rows[i].state == CAPTURE) for i, item in pointed.items())
        try:
            reg.publisher.publish(packets.location.clone, packets.location.remote, refs)
        except PublicationFailed as error:
            return hold(INITIAL, candidate.input_digest, [(error.code, error.refs)])
        return None

    def _row(self, identity: str) -> WorkItem:
        item = self.registration.items.find(identity)
        if item is None or item.id != identity:
            raise UnknownWorkItem(identity)  # Registered in this compile's first transaction; never deleted.
        return item

    def read(self, identity: str) -> tuple[int, dict]:
        return self.store.read_state(self.profile, self.aggregate(identity))

    def retained(self, ref: Ref) -> Observation:
        record = self.repository.get(ref, self.access_scope)
        if not isinstance(record, Observation) or record.evidence_id not in (DERIVED_EVENT, HELD_EVENT):
            raise EvidenceHold("NOT_INITIAL_COMPILATION_EVIDENCE", (ref,))
        return record

    def completed(self, identity: str) -> bool:
        """Completion reads back only a derived candidate record; a validated supplied candidate never counts."""
        _, state = self.read(identity)
        if state.get("status") != "DERIVED":
            return False
        record = self.retained(ref_from_document(state["result_ref"]))
        return record.evidence_id == DERIVED_EVENT and is_initial_compilation(json.loads(record.value))

    def _persist(self, result: CompilationCandidate | CompilationHold) -> CompilationCandidate | CompilationHold:
        identity = result.input_digest if isinstance(result, CompilationCandidate) else result.candidate_digest
        event, status = (DERIVED_EVENT, "DERIVED") if isinstance(result, CompilationCandidate) else (HELD_EVENT, "HELD")
        body = result.document()
        version, state = self.read(identity)
        history = state.get("history") if isinstance(state.get("history"), list) else []
        previous = ref_from_document(history[-1]["ref"]) if history else None
        ref = self._put(event, identity, body, (previous,) if previous else ())
        pointer = {"schema_version": 1, "input_digest": identity, "mode": INITIAL, "status": status,
                   "candidate_digest": getattr(result, "candidate_digest", None), "result_ref": asdict(ref),
                   "result_digest": digest(body), "history": [*history, {"event": event, "ref": asdict(ref)}]}
        try:
            self.store.commit(self.profile, self.aggregate(identity), version, pointer)
        except VersionConflict:
            return hold(INITIAL, identity, [("PERSISTENCE_CONFLICT", (identity,))])  # Never blindly retry.
        return result

    def _put(self, evidence_id: str, identity: str, body: dict, preceding: tuple[Ref, ...]) -> Ref:
        value = canonical(body)
        body_digest = sha256(value.encode()).hexdigest()
        record = Observation(Header(self.project, self.profile, "initial-compilation/" + identity, body_digest,
                                    (self.definition_ref,), "private", preceding), self.definition_ref, evidence_id,
                             "initial_compilation/v1", (), value, None, "initial-compilation", self.invocation,
                             "sha256:" + body_digest)
        ref = self.repository.put(record)
        self.repository.get(ref, self.access_scope)  # Read back before the pointer can reference it.
        return ref

