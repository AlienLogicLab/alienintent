"""Initial compilation (U8) for one store/profile: design gate, pinned inputs, derivation, reservation, one record.

Order: the U5 design gate and the retained design of that exact verified revision, then the current U1 inventory,
U2 inspection and U4 proof plans, then compile_initial. A derived candidate first commits its identity reservations
(one expected-version upstream:identity-reservations aggregate), then is retained as an immutable Observation bound by
an upstream:initial-compilation:<input digest> pointer. The same pinned input regenerates the same candidate and
reserves nothing new. Nothing here writes factory:* or release:* state, Issues, work-management projections or any
existing decomposition; a candidate is admitted for assessment only.
"""
from dataclasses import asdict
from hashlib import sha256
import json

from alienintent.context_assembly.domain.ambiguity import AmbiguityHold, snapshot_from_document
from alienintent.context_assembly.domain.compilation import INITIAL, CompilationHold, canonical, digest, hold
from alienintent.context_assembly.domain.initial_compilation import (
    CompilationCandidate, compile_initial, is_initial_compilation)
from alienintent.context_assembly.domain.inventory import InventoryHold
from alienintent.context_assembly.ports.compilation import (
    DependencyLifecycle, DesignGate, InspectionSource, InventorySource, ProofPlans, VerifiedDesigns)
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict

DERIVED_EVENT, HELD_EVENT = "compilation.derived", "compilation.held"
RESERVATIONS = "upstream:identity-reservations"
UNREADABLE = (AmbiguityHold, InventoryHold, EvidenceHold, KeyError, TypeError, ValueError)


class InitialCompilation:
    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, access_scope: frozenset[str], design: DesignGate,
                 designs: VerifiedDesigns, inventory: InventorySource, inspection: InspectionSource,
                 proofs: ProofPlans, lifecycle: DependencyLifecycle) -> None:
        self.repository, self.store, self.project, self.profile = repository, store, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope
        self.design, self.designs, self.inventory, self.inspection = design, designs, inventory, inspection
        self.proofs, self.lifecycle = proofs, lifecycle

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
        version, state = self.store.read_state(self.profile, RESERVATIONS)
        reservations = dict(state.get("reservations") or {})
        existing = authority_limits.get("existing_decomposition") if isinstance(authority_limits, dict) else None
        # Only well-formed identities are looked up; a malformed value reaches compile_initial and holds there.
        stages = {i: self.lifecycle.stage(i) for i in sorted({
            i for ids in (existing.values() if isinstance(existing, dict) else ()) if isinstance(ids, list)
            for i in ids if isinstance(i, str)})}
        result = compile_initial(inventory, inspection, design, getattr(decision.applicability, "review_digest", ""),
                                 plans, authority_limits, reservations, stages)
        if isinstance(result, CompilationCandidate):
            added = {k: v for k, v in result.reservations if reservations.get(k) != v}
            if added:  # An identical regeneration reserves nothing; a changed reservation set is a conflict.
                try:
                    self.store.commit(self.profile, RESERVATIONS, version, {
                        "schema_version": 1, "reservations": dict(sorted({**reservations, **added}.items())),
                        "history": [*(state.get("history") or []),
                                    {"input_digest": result.input_digest, "reserved": dict(sorted(added.items()))}]})
                except VersionConflict:
                    # A concurrent identical compile may have reserved exactly these identities: that is success.
                    current = self.reservations()
                    if any(current.get(k) != v for k, v in result.reservations):
                        return self._persist(hold(INITIAL, result.input_digest,
                                                  [("PERSISTENCE_CONFLICT", (RESERVATIONS,))]))
        return self._persist(result)

    def read(self, identity: str) -> tuple[int, dict]:
        return self.store.read_state(self.profile, self.aggregate(identity))

    def reservations(self) -> dict[str, str]:
        return dict(self.store.read_state(self.profile, RESERVATIONS)[1].get("reservations") or {})

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

