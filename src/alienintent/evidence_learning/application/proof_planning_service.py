"""Derive, persist and check pre-implementation proof plans over the shared store and evidence."""
from dataclasses import asdict
from hashlib import sha256
import json

from alienintent.evidence_learning.application.premise_service import PremiseEvidenceReader
from alienintent.evidence_learning.domain.premise import InfeasibleProof
from alienintent.evidence_learning.domain.proof_order import (
    FAULT, INTACT, PLAN, RESTORED, ProofDiagnostic, ProofStep, proof_order_diagnostics)
from alienintent.evidence_learning.domain.proof_plan import (
    PlanHold, ProofPlan, RequirementRevision, derive_plan, plan_document, plan_from_document)
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.domain.repair import RepairAccepted, ReplayStatus, evaluate_repair
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.evidence_learning.ports.proof_planning import PredicateMappingSource
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict

PLAN_EVIDENCE, HELD_EVIDENCE, PROOF_EVIDENCE = "proof.plan", "proof.plan.held", "proof.observed"
_STATE_KEYS = {"schema_version", "requirement_id", "plan_ref", "plan_digest", "history"}


def _valid_ref(value: object) -> bool:
    try:
        ref_from_document(value)
    except EvidenceHold:
        return False
    return True


def _valid_state(state: object, requirement_id: str, version: int) -> bool:
    """The pointer is exactly the latest plan event; a lost or foreign pointer is never an empty history."""
    if not isinstance(state, dict) or type(state.get("schema_version")) is not int or state.get("schema_version") != 1 or set(state) != _STATE_KEYS \
            or state["requirement_id"] != requirement_id or not isinstance(state["history"], list):
        return False
    # Every commit appends exactly one event, so an erased or truncated history cannot pass as a shorter one.
    if len(state["history"]) != version:
        return False
    for event in state["history"]:
        if not isinstance(event, dict) or event.get("event") not in ("plan", "held") or not _valid_ref(event.get("ref")) \
                or set(event) != ({"event", "digest", "ref"} if event["event"] == "plan" else {"event", "reason", "ref"}) \
                or (event["event"] == "plan" and not isinstance(event.get("digest"), str)) \
                or (event["event"] == "held" and not isinstance(event.get("reason"), str)):
            return False
    plans = [e for e in state["history"] if e["event"] == "plan"]
    if not plans:
        return state["plan_ref"] is None and state["plan_digest"] is None
    return state["plan_ref"] == plans[-1]["ref"] and state["plan_digest"] == plans[-1]["digest"]


def _preceding(plan_ref: Ref | None, previous: Ref | None) -> tuple[Ref, ...]:
    """A plan or hold follows the current plan and the latest event, so no event can be repeated or dropped."""
    return tuple(dict.fromkeys(r for r in (plan_ref, previous) if r is not None))


class ProofPlanning:
    """ProofPlanning.derive and ProofEvidence.record for one store/profile and EvidenceRepository."""

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, mappings: PredicateMappingSource,
                 premises: PremiseEvidenceReader | None, project: str, profile: str, definition_ref: Ref,
                 invocation: str, mapping_reviewer: str, supersession_authority: str,
                 implementation_roots: tuple[str, ...], access_scope: frozenset[str]) -> None:
        self.repository, self.store, self.mappings, self.premises = repository, store, mappings, premises
        self.project, self.profile, self.definition_ref, self.invocation = project, profile, definition_ref, invocation
        self.mapping_reviewer, self.supersession_authority = mapping_reviewer, supersession_authority
        self.implementation_roots, self.access_scope = implementation_roots, access_scope

    @staticmethod
    def aggregate(requirement_id: str) -> str:
        return "upstream:proof-plan:" + requirement_id

    def read(self, requirement_id: str) -> tuple[int, dict]:
        version, state = self.store.read_state(self.profile, self.aggregate(requirement_id))
        # Only a never-written aggregate is empty; an emptied one at a later version lost its history.
        if (version, state) != (0, {}) and not (_valid_state(state, requirement_id, version)
                                                and self._retained_history(requirement_id, state["history"])):
            raise EvidenceHold("INCOMPATIBLE_PROOF_PLAN_STATE")
        return version, state

    def _retained_history(self, requirement_id: str, history: list) -> bool:
        """Each event is its own retained record, chained to the plan and the event before it."""
        plan_ref = previous = None
        for event in history:
            ref = ref_from_document(event["ref"])
            try:
                record = self.repository.get(ref, self.access_scope)
            except (EvidenceHold, ValueError, TypeError, KeyError):
                return False
            expected = PLAN_EVIDENCE if event["event"] == "plan" else HELD_EVIDENCE
            if not isinstance(record, Observation) or record.evidence_id != expected \
                    or record.header.logical_id != "proof-plan/" + requirement_id \
                    or record.header.preceding_refs != _preceding(plan_ref, previous):
                return False
            plan_ref = ref if event["event"] == "plan" else plan_ref
            previous = ref
        return True

    def _state(self, requirement_id: str) -> tuple[int, dict] | PlanHold:
        try:
            return self.read(requirement_id)
        except EvidenceHold as hold:
            return PlanHold(hold.reason_code, (requirement_id,), required_action="repair the operational proof-plan pointer")

    def current(self, requirement_id: str) -> ProofPlan | PlanHold | None:
        read = self._state(requirement_id)
        if isinstance(read, PlanHold):
            return read
        state = read[1]
        if not state or state["plan_ref"] is None:
            return None
        return self._plan(ref_from_document(state["plan_ref"]), state["plan_digest"])

    def plan(self, requirement_id: str, digest: str) -> ProofPlan | PlanHold | None:
        """A retained prior plan, found through the append-only history."""
        read = self._state(requirement_id)
        if isinstance(read, PlanHold):
            return read
        entry = next((e for e in (read[1].get("history") or []) if e["event"] == "plan" and e["digest"] == digest), None)
        return None if entry is None else self._plan(ref_from_document(entry["ref"]), digest)

    def derive(self, requirement: RequirementRevision, design_ref: Ref,
               expected_version: int) -> ProofPlan | PlanHold | InfeasibleProof:
        read = self._state(requirement.requirement_id)
        if isinstance(read, PlanHold):
            return read
        version, state = read
        if version != expected_version:
            return PlanHold("STALE_INPUT", (requirement.requirement_id,), required_action="read the current version and rederive")
        prior = self.current(requirement.requirement_id)
        if isinstance(prior, PlanHold):
            return prior
        reader = self.premises.read if self.premises is not None else None
        result = derive_plan(requirement, design_ref, self.mappings.load(requirement.requirement_id), reader, prior,
                             self.mapping_reviewer, self.supersession_authority, self.implementation_roots)
        plan_ref = ref_from_document(state["plan_ref"]) if state and state["plan_ref"] else None
        previous = ref_from_document(state["history"][-1]["ref"]) if state and state["history"] else None
        if isinstance(result, ProofPlan):
            document, evidence_id = plan_document(result), PLAN_EVIDENCE
        else:
            document, evidence_id = {"schema_version": 1, "kind": type(result).__name__, **asdict(result)}, HELD_EVIDENCE
        ref = self._put(evidence_id, "proof-plan/" + requirement.requirement_id, document,
                        (requirement.ref, design_ref), _preceding(plan_ref, previous))
        event = ({"event": "plan", "digest": result.digest, "ref": asdict(ref)} if isinstance(result, ProofPlan) else
                 {"event": "held", "reason": result.reason_code, "ref": asdict(ref)})
        # A hold is appended to history; it never replaces the current plan.
        committed = {"schema_version": 1, "requirement_id": requirement.requirement_id,
                     "plan_ref": asdict(ref) if isinstance(result, ProofPlan) else (state or {}).get("plan_ref"),
                     "plan_digest": result.digest if isinstance(result, ProofPlan) else (state or {}).get("plan_digest"),
                     "history": [*(state or {}).get("history", []), event]}
        try:
            self.store.commit(self.profile, self.aggregate(requirement.requirement_id), version, committed)
        except VersionConflict:
            return PlanHold("STALE_INPUT", (requirement.requirement_id,), (ref,), "read the current version and rederive")
        return result

    def record(self, obligation_id: str, candidate_ref: Ref, fixture_digest: str, invocation: str, expected: str,
               observed: str, exit_code: int | None, *, control: str, phase: str,
               preceding: tuple[Ref, ...] = ()) -> Ref | PlanHold:
        """ProofEvidence.record: evidence identity adds candidate, fixture and invocation to the obligation."""
        requirement_id = obligation_id.split("/", 1)[0]
        read = self._state(requirement_id)
        if isinstance(read, PlanHold):
            return read
        state = read[1]
        plan = self.current(requirement_id)
        if not isinstance(plan, ProofPlan) or plan.obligation(obligation_id) is None:
            return PlanHold("UNPLANNED_OBLIGATION", (obligation_id,), required_action="derive a plan naming this obligation first")
        if phase not in (INTACT, FAULT, RESTORED):
            return PlanHold("UNKNOWN_PHASE", (phase,))
        value = {"obligation_id": obligation_id, "candidate_ref": asdict(candidate_ref), "fixture_digest": fixture_digest,
                 "invocation": invocation, "expected": expected, "observed": observed, "exit_code": exit_code,
                 "control": control, "phase": phase, "plan_digest": plan.digest}
        # The plan is always an ancestor: evidence recorded here cannot precede its plan.
        chain = tuple(dict.fromkeys((ref_from_document(state["plan_ref"]), *preceding)))
        return self._put(PROOF_EVIDENCE, f"proof-observation/{obligation_id}/{control}/{phase}", value,
                         (candidate_ref,), chain, invocation)

    def proof_order(self, refs: tuple[Ref, ...]) -> tuple[ProofDiagnostic, ...]:
        """Advisory ancestry diagnostics over retained plan and proof observations."""
        steps = []
        for ref in refs:
            record = self.repository.get(ref, self.access_scope)
            if not isinstance(record, Observation) or record.evidence_id not in (PLAN_EVIDENCE, PROOF_EVIDENCE):
                raise EvidenceHold("NOT_PROOF_EVIDENCE", (ref,))
            value = json.loads(record.value)
            kind = PLAN if record.evidence_id == PLAN_EVIDENCE else value["phase"]
            steps.append(ProofStep(ref, kind, None if kind == PLAN else value["control"],
                                   record.header.preceding_refs, record.observer))
        return proof_order_diagnostics(tuple(steps))

    def evaluate_repair(self, requirement_id: str, replay: dict[str, ReplayStatus]) -> RepairAccepted | PlanHold:
        current = self.current(requirement_id)
        if isinstance(current, PlanHold) and current.reason_code == "INCOMPATIBLE_PROOF_PLAN_STATE":
            return current
        if not isinstance(current, ProofPlan):
            return current if isinstance(current, PlanHold) else PlanHold("NO_CURRENT_PLAN", (requirement_id,))
        prior = None if current.prior_plan_digest is None else self.plan(requirement_id, current.prior_plan_digest)
        if not isinstance(prior, ProofPlan):
            return prior if isinstance(prior, PlanHold) else PlanHold("NO_PRIOR_PLAN", (requirement_id,))
        return evaluate_repair(prior, current, replay)

    def _plan(self, ref: Ref, digest: str) -> ProofPlan | PlanHold:
        try:
            record = self.repository.get(ref, self.access_scope)
            if not isinstance(record, Observation) or record.evidence_id != PLAN_EVIDENCE:
                raise ValueError("not a plan observation")
            plan = plan_from_document(json.loads(record.value))
        except (EvidenceHold, ValueError, TypeError, KeyError) as error:
            return PlanHold("PERSISTED_PLAN_INVALID", (str(error) or type(error).__name__,), (ref,))
        if plan.digest != digest:
            return PlanHold("PERSISTED_PLAN_INVALID", ("digest mismatch",), (ref,))
        return plan

    def _put(self, evidence_id: str, logical_id: str, document: dict, sources: tuple[Ref, ...],
             preceding: tuple[Ref, ...], invocation: str | None = None) -> Ref:
        value = canonical_bytes(document).decode()
        digest = sha256(value.encode()).hexdigest()
        record = Observation(Header(self.project, self.profile, logical_id, digest, sources, "private", preceding),
                             self.definition_ref, evidence_id, "proof-plan-derivation", sources, value, None,
                             "proof-planning", invocation or self.invocation, "sha256:" + digest)
        return self.repository.put(record)
