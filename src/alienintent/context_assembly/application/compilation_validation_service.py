"""Compiler validation (U7) for one store/profile: gates first, then pure validation, then one immutable record.

Order: the U5 design gate, open upstream questions on linked requirements, dependency authority over the execution
lifecycle (never Issue state), then validate / validate_split. Each report or hold is retained as an immutable
Observation and bound by an upstream:compilation:<candidate digest> pointer. Nothing here writes factory:* or
release:* state, reservations, work-management projections or any decomposition aggregate; a report is admission
for assessment only.
"""
from dataclasses import asdict
from hashlib import sha256
from typing import Callable

from alienintent.context_assembly.domain.ambiguity import OPEN
from alienintent.context_assembly.domain.compilation import (
    INITIAL, SPLIT_REPLAN, UNREADABLE, CandidateInvalid, CompilationHold, ValidationReport, candidate_digest,
    canonical, dependency_authority, digest, edges_of, hold, initial_units, linked_requirements, split_units, validate,
    validate_split)
from alienintent.context_assembly.ports.compilation import (
    AssessmentHistory, DependencyLifecycle, DesignDecisions, DesignGate, OpenQuestions)
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict

VALIDATED_EVENT, HELD_EVENT = "compilation.validated", "compilation.held"


class CompilationValidation:
    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, access_scope: frozenset[str], design: DesignGate,
                 decisions: DesignDecisions, questions: OpenQuestions, lifecycle: DependencyLifecycle,
                 history: AssessmentHistory) -> None:
        self.repository, self.store, self.project, self.profile = repository, store, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope
        self.design, self.decisions, self.questions = design, decisions, questions
        self.lifecycle, self.history = lifecycle, history

    @staticmethod
    def aggregate(identity: str) -> str:
        return "upstream:compilation:" + identity.removeprefix("sha256:")

    def validate(self, candidate: object) -> ValidationReport | CompilationHold:
        """A supplied INITIAL candidate; admission proves validation only, never derivation."""
        return self._run(INITIAL, candidate, None, lambda decisions, stages: validate(candidate, decisions, stages))

    def validate_split(self, proposal: object, original: object, authority_limits: dict,
                       identity_policy: dict) -> ValidationReport | CompilationHold:
        """A frozen split proposal against the pinned original; nothing is prepared, reserved or applied."""
        def check(decisions, stages):
            priors = proposal.get("prior_assessments") if isinstance(proposal, dict) else None
            history = {str(p["ref"].get("locator")): self.history.digest(p["ref"])
                       for p in priors or () if isinstance(p, dict) and isinstance(p.get("ref"), dict)}
            return validate_split(proposal, original, authority_limits, identity_policy, stages, history)
        return self._run(SPLIT_REPLAN, proposal, original, check)

    def read(self, identity: str) -> tuple[int, dict]:
        return self.store.read_state(self.profile, self.aggregate(identity))

    def retained(self, ref: Ref) -> Observation:
        record = self.repository.get(ref, self.access_scope)
        if not isinstance(record, Observation) or record.evidence_id not in (VALIDATED_EVENT, HELD_EVENT):
            raise EvidenceHold("NOT_COMPILATION_EVIDENCE", (ref,))
        return record

    def _run(self, mode: str, document: object, original: object,
             check: Callable) -> ValidationReport | CompilationHold:
        identity = candidate_digest(document)
        return self._persist(mode, identity, self._gates(mode, identity, document, original, check))

    def _gates(self, mode: str, identity: str, document: object, original: object,
               check: Callable) -> ValidationReport | CompilationHold:
        if not isinstance(document, dict) or not isinstance(document.get("design_key"), str) \
                or not isinstance(document.get("design_vector"), dict):
            return hold(mode, identity, [("INVALID_CANDIDATE", ("design_key",))])
        key = document["design_key"]
        # Only an exact current VERIFIED design admits: stale, unreviewed and absent designs hold (U5).
        decision = self.design.admit(key, document["design_vector"])
        if not decision.admitted:
            return hold(mode, identity, [("DESIGN_HOLD", (key,))], decision.reason_code)
        try:
            return self._checks(mode, identity, key, decision, document, original, check)
        except CandidateInvalid as error:
            return hold(mode, identity, [("INVALID_CANDIDATE", (str(error),))])
        except UNREADABLE as error:  # Fail closed: an unreadable candidate is a typed hold, never an exception.
            return hold(mode, identity, [("INVALID_CANDIDATE", ("unreadable:" + type(error).__name__,))])

    def _checks(self, mode: str, identity: str, key: str, decision, document: dict, original: object,
                check: Callable) -> ValidationReport | CompilationHold:
        # Questions on any requirement the candidate touches hold it, not only those it chose to declare.
        linked = {key} | linked_requirements(document, original)
        unresolved = [f.finding_id for f, _, _ in self.questions.questions(OPEN)
                      if f.requirement_id in linked or linked & set(f.affected)]
        if unresolved:
            return hold(mode, identity, [("UNRESOLVED_AUTHORITY", tuple(unresolved))])
        decisions = self.decisions.fixed_decisions(key, getattr(decision.applicability, "design_digest", ""))
        if decisions is None:
            return hold(mode, identity, [("DESIGN_HOLD", (key,))], "DESIGN_DECISIONS_UNREADABLE")
        if mode == INITIAL:
            units, name = initial_units(document), "edges"
        else:
            units, name = {u: r.get("contract") or {} for u, r in split_units(document).items()}, "result_edges"
        values = document.get(name, [])
        if not isinstance(values, list):
            raise CandidateInvalid(name)
        edges = edges_of(values, name)
        origin = (original["identity"],) if isinstance(original, dict) and isinstance(original.get("identity"),
                                                                                      str) else ()
        stages = {i: self.lifecycle.stage(i) for i in sorted({*(e.source for e in edges), *(e.target for e in edges),
                                                               *origin})}
        projection = document.get("projection") if isinstance(document.get("projection"), dict) else {}
        findings = dependency_authority(units, edges, stages, projection, require_done=mode == INITIAL)
        if findings:
            return hold(mode, identity, findings)
        return check(decisions, stages)

    def _persist(self, mode: str, identity: str,
                 result: ValidationReport | CompilationHold) -> ValidationReport | CompilationHold:
        if isinstance(result, CompilationHold):
            event, status = HELD_EVENT, "HELD"
        else:
            event, status = VALIDATED_EVENT, "VALIDATED"
        body = result.document()
        version, state = self.read(identity)
        history = state.get("history") if isinstance(state.get("history"), list) else []
        previous = ref_from_document(history[-1]["ref"]) if history else None
        ref = self._put(event, identity, body, (previous,) if previous else ())
        pointer = {"schema_version": 1, "candidate_digest": identity, "mode": mode, "status": status,
                   "result_ref": asdict(ref), "result_digest": digest(body),
                   "history": [*history, {"event": event, "ref": asdict(ref)}]}
        try:
            self.store.commit(self.profile, self.aggregate(identity), version, pointer)
        except VersionConflict:
            return hold(mode, identity, [("PERSISTENCE_CONFLICT", (identity,))])  # Never blindly retry.
        return result

    def _put(self, evidence_id: str, identity: str, body: dict, preceding: tuple[Ref, ...]) -> Ref:
        value = canonical(body)
        body_digest = sha256(value.encode()).hexdigest()
        record = Observation(Header(self.project, self.profile, "compilation/" + identity, body_digest,
                                    (self.definition_ref,), "private", preceding), self.definition_ref, evidence_id,
                             "compilation_validation/v1", (), value, None, "compilation-validation", self.invocation,
                             "sha256:" + body_digest)
        ref = self.repository.put(record)
        self.repository.get(ref, self.access_scope)  # Read back before the pointer can reference it.
        return ref
