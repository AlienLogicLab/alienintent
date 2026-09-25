"""ReadinessAdmission (SF-REQ-015): lint, provenance gate, one attributable attempt, then the disposition route.

Order: lint (a hold invokes nothing), producer binding (unbound or unestablished provenance is
CAPABILITY_PROVENANCE_HOLD before launch), the reassessment gate of the latest attempt, then exactly one invocation
whose attempt UUID is persisted first. Routes stop at their handoff boundaries: READY is eligibility for the
separate SF-REQ-002 release gate only; CLARIFY opens SF-REQ-035 inbox questions; SPLIT hands the raw assessment to
U8's SplitTransaction and lints/reassesses each materialized result; HOLD waits for a prerequisite change. Nothing
here releases, transitions lifecycle state or judges readiness.
"""
from alienintent.context_assembly.domain.readiness import (
    LintHold, LintReport, Outcome, SplitRouted, identity_of, lint)
from alienintent.context_assembly.ports.compilation import DependencyLifecycle, DesignGate
from alienintent.context_assembly.ports.readiness import ClarificationChannel, SplitTransactionHandoff
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_FAILURE, CAPABILITY_PROVENANCE_HOLD, CLARIFY, CLARIFY_PENDING_DECISION, HOLD, PREREQUISITE_PENDING, READY,
    SPLIT, SPLIT_RESULT_SET_NOT_MATERIALIZED, AttemptFailure, AttemptMetadata, CandidateWorkUnit, Hold,
    ProducerBinding, ProducerResponse, ReadinessEligibility, binding_refusal, digest, input_fingerprint)
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer, ReadinessAssessment

LINT_HELD, LINT_PASSED, PROVENANCE_HELD = "readiness.lint_held", "readiness.lint_passed", "readiness.provenance_held"
SPLIT_HANDOFF = "readiness.split_handoff"


class ReadinessAdmission:
    def __init__(self, consumer: AssessmentConsumer, producer: ReadinessAssessment | None,
                 binding: ProducerBinding | None, design: DesignGate, lifecycle: DependencyLifecycle,
                 clarifications: ClarificationChannel, split: SplitTransactionHandoff | None) -> None:
        self.consumer, self.producer, self.binding = consumer, producer, binding
        self.design, self.lifecycle, self.clarifications, self.split = design, lifecycle, clarifications, split

    def lint(self, candidate: object, proof_plan: tuple[str, ...] | None) -> tuple[LintReport, dict]:
        """Lint and retain the report or hold as an immutable observation; no assessment is invoked here."""
        design = None
        if isinstance(candidate, dict) and isinstance(candidate.get("design_key"), str) \
                and isinstance(candidate.get("design_vector"), dict):
            design = self.design.admit(candidate["design_key"], candidate["design_vector"]).applicability
        contract = candidate.get("contract") if isinstance(candidate, dict) else None
        declared = contract.get("dependencies") if isinstance(contract, dict) else None
        snapshot = {d: self.lifecycle.stage(d) for d in declared if isinstance(d, str)} \
            if isinstance(declared, list) else {}
        report = lint(candidate, design, proof_plan, snapshot)
        event = LINT_HELD if report.holds else LINT_PASSED
        return report, self.consumer.retain(report.identity, event, report.document())

    @staticmethod
    def fingerprint(candidate: dict, report: LintReport) -> str:
        return input_fingerprint(report.contract_digest, str(candidate.get("baseline")),
                                 tuple(str(d) for d in candidate.get("governing_decisions") or ()),
                                 dict(report.dependencies),
                                 {"design_digest": str(report.design_digest), "review_digest": str(report.review_digest)})

    def current(self, candidate: object, proof_plan: tuple[str, ...] | None) -> ReadinessEligibility | Hold | LintHold:
        """Read-time applicability of the latest assessment against the candidate's current inputs."""
        report, _ = self.lint(candidate, proof_plan)
        if report.holds:
            return report.holds[0]
        return self.consumer.consume(report.identity, self.fingerprint(candidate, report))

    def assess(self, candidate: object, proof_plan: tuple[str, ...] | None,
               predecessor: dict | None = None) -> Outcome:
        report, lint_ref = self.lint(candidate, proof_plan)
        if report.holds:
            return report.holds[0]  # Attributable, and nothing is invoked.
        identity = report.identity
        refusal = binding_refusal(self.binding) if self.producer is not None else "UNBOUND"
        if refusal:
            self.consumer.retain(identity, PROVENANCE_HELD, {
                "record_kind": "CapabilityProvenanceHold", "reason_code": CAPABILITY_PROVENANCE_HOLD,
                "identity": identity, "refusal": refusal, "binding": repr(self.binding), "launched": False})
            return Hold(CAPABILITY_PROVENANCE_HOLD, identity, None, refusal)
        fingerprint = self.fingerprint(candidate, report)
        latest = self.consumer.latest(identity)
        gate = self._reassessment_gate(identity, latest, fingerprint)
        if gate is not None:
            return gate
        if predecessor is None and latest is not None:
            predecessor = {"identity": identity, "attempt_id": latest["attempt_id"]}
        return self._invoke(candidate, report, lint_ref, fingerprint, predecessor, proof_plan)

    def _reassessment_gate(self, identity: str, latest: dict | None, fingerprint: str) -> Outcome | None:
        """A fresh attempt only after what the previous disposition requires; the old verdict is never rewritten."""
        if latest is None or latest["outcome"] is None:
            return None
        disposition, attempt = latest["outcome"]["disposition"], latest["attempt_id"]
        if disposition == CLARIFY:
            routed = latest.get("clarifications") or []
            pending = [w for w in routed if self.clarifications.resolved(w) is not None] or \
                ([] if routed or latest["input_fingerprint"] != fingerprint else ["NO_CLARIFICATION_ROUTED"])
            if pending:
                return Hold(CLARIFY_PENDING_DECISION, identity, attempt, ",".join(pending))
        if disposition == HOLD and latest["input_fingerprint"] == fingerprint:
            return Hold(PREREQUISITE_PENDING, identity, attempt, "no prerequisite changed since the HOLD")
        if disposition == SPLIT:
            return Hold(SPLIT_RESULT_SET_NOT_MATERIALIZED, identity, attempt, "a SPLIT unit is superseded by its "
                        "materialized results, never reassessed in place")
        if disposition == READY and latest["input_fingerprint"] == fingerprint:
            current = self.consumer.consume(identity, fingerprint)  # Invalidated READY is reassessed, not reused.
            return current if isinstance(current, ReadinessEligibility) else None
        return None

    def _invoke(self, candidate: dict, report: LintReport, lint_ref: dict, fingerprint: str,
                predecessor: dict | None, proof_plan: tuple[str, ...] | None) -> Outcome:
        identity, text = report.identity, str(candidate.get("text"))
        input_sha256 = digest(text)
        attempt = self.consumer.open(identity, fingerprint, input_sha256, report.contract_digest, predecessor,
                                     lint_ref, self.binding)
        if isinstance(attempt, Hold):
            return attempt
        try:
            response = self.producer.assess(CandidateWorkUnit(identity, text, attempt, fingerprint))
        except Exception as error:  # A raising adapter fails the opened attempt; it never leaves it open.
            response = ProducerResponse(None, None, False, "raised:" + type(error).__name__, None)
        if type(response) is not ProducerResponse:  # Exactly the frozen value: no subclass can intercept reads.
            response = ProducerResponse(None, None, False, "invalid:" + type(response).__name__, None)
        metadata = AttemptMetadata(identity, attempt, fingerprint, input_sha256, response.exit_status,
                                   response.timed_out, response.custody, self.binding)
        observed = self.consumer.observe(response.raw, metadata, response.shape)
        if isinstance(observed, Hold):
            return observed
        if isinstance(observed, AttemptFailure):
            return Hold(ATTEMPT_FAILURE, identity, attempt, observed.failure_class)
        if observed.disposition == READY:
            return self.consumer.consume(identity, fingerprint)
        if observed.disposition == CLARIFY:
            items = [self.clarifications.open(identity, attempt, i, q)
                     for i, q in enumerate(observed.owner_clarifications)]
            hold = self.consumer.annotate(identity, attempt, "clarifications", items)
            return hold or Hold(CLARIFY_PENDING_DECISION, identity, attempt, ",".join(items))
        if observed.disposition == SPLIT:
            return self._split(identity, attempt, report, fingerprint, observed.body, proof_plan)
        return Hold(PREREQUISITE_PENDING, identity, attempt, "satisfy the prerequisite, then reassess")

    def _split(self, identity: str, attempt: str, report: LintReport, fingerprint: str, body: str,
               proof_plan: tuple[str, ...] | None) -> Outcome:
        retained = self.consumer.raw(identity, attempt)
        raw_ref, raw = retained if retained else (None, "")
        results = self.split.handoff(identity, attempt, raw_ref, raw, (body,)) if self.split is not None else None
        hold = self.consumer.annotate(identity, attempt, "split_handoff", self.consumer.retain(identity, SPLIT_HANDOFF, {
            "record_kind": "SplitHandoff", "identity": identity, "attempt_id": attempt, "assessment_ref": raw_ref,
            "materialized": results is not None, "label": getattr(results, "label", None)}))
        if hold is not None:
            return hold
        if results is None:
            return Hold(SPLIT_RESULT_SET_NOT_MATERIALIZED, identity, attempt, "U8 supplied no materialized result set")
        for stale in results.invalidated:
            self.consumer.invalidate(stale, "SPLIT", attempt)
        outcomes = []
        for unit in (*results.children, results.integration_parent):
            outcomes.append((identity_of(unit), self.assess(unit, proof_plan,
                                                            {"identity": identity, "attempt_id": attempt})))
        return SplitRouted(identity, attempt, tuple(outcomes))
