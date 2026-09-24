"""Persist ambiguity findings and attributed resolutions; question and answer never launch work."""
from dataclasses import asdict
import json

from alienintent.context_assembly.domain.ambiguity import (
    OPEN, RESOLVED, STALE, AmbiguityHold, AnswerHold, Finding, InspectionReport, QuestionResolution, SemanticReview,
    finding_from_document, inspect, question_work_item, report_from_document, resolution_identity, review_from_document,
    snapshot_from_document)
from alienintent.context_assembly.domain.inventory import canonical, digest
from alienintent.context_assembly.ports.decision_resolution import DecisionResolution, InventoryReader, QuestionChannel
from alienintent.evidence_learning.domain.records import Header, Observation
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.escalation import DecisionRecord
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict


_OPENING = frozenset({"inspection", "reopened"})


def _work_item(history: list | tuple) -> str:
    return next(e["work_item"] for e in reversed(history) if e["event"] in _OPENING)


class UpstreamQuestionAdmission:
    """Decision Inbox admission for upstream questions: validate attribution, never resume workers."""

    def __init__(self, decision_actor: str) -> None:
        self._actor = decision_actor

    def validate_decision(self, record: DecisionRecord) -> None:
        if not record.submission.work_item.startswith("upstream-question:"):
            raise ValueError("not an upstream question")
        if record.submission.actor != self._actor or record.event.actor != self._actor:
            raise PermissionError("actor is not the required decision authority")

    def record_decision(self, record: DecisionRecord) -> None:
        self.validate_decision(record)  # The inbox record is the durable answer; resolution is separate.

    def resume_after_decision(self) -> None:
        return None  # Resuming preparation is a new validated operation and launches no worker.


class AmbiguityService:
    aggregate = "upstream:ambiguity:current"

    def __init__(self, inventory: InventoryReader, repository: EvidenceRepository, store: OperationalStore,
                 resolution: DecisionResolution, project: str, profile: str, definition_ref: Ref, invocation: str,
                 decision_actor: str, access_scope: frozenset[str], channel: QuestionChannel | None = None) -> None:
        self.inventory, self.repository, self.store, self.resolution = inventory, repository, store, resolution
        self.project, self.profile, self.definition_ref, self.invocation = project, profile, definition_ref, invocation
        self.decision_actor, self.access_scope, self.channel = decision_actor, access_scope, channel

    def read(self) -> tuple[int, dict]:
        version, state = self.store.read_state(self.profile, self.aggregate)
        if state and (state.get("schema_version") != 1 or set(state) != {
                "schema_version", "inventory_digest", "report_ref", "report_digest", "findings", "reviews"}):
            raise AmbiguityHold("INCOMPATIBLE_AMBIGUITY_STATE")
        return version, state

    def report(self) -> InspectionReport | None:
        _, state = self.read()
        if not state:
            return None
        record = self.repository.get(Ref(**state["report_ref"]), self.access_scope)
        if not isinstance(record, Observation) or record.evidence_id != "ambiguity.report":
            raise AmbiguityHold("INVALID_REPORT_OBSERVATION")
        report = report_from_document(json.loads(record.value))
        if report.digest != state["report_digest"]:
            raise AmbiguityHold("REPORT_DIGEST_MISMATCH")
        return report

    def questions(self, status: str | None = OPEN) -> tuple[tuple[Finding, str, tuple[dict, ...]], ...]:
        _, state = self.read()
        entries = sorted((state.get("findings") or {}).items())
        return tuple((finding_from_document(e["finding"]), e["history"][-1]["status"], tuple(e["history"]))
                     for _, e in entries if status is None or e["history"][-1]["status"] == status)

    def work_item(self, finding_id: str) -> str:
        """The Decision Inbox question for the finding's current OPEN cycle."""
        return _work_item(self.show(finding_id)[2])

    def show(self, finding_id: str) -> tuple[Finding, str, tuple[dict, ...]]:
        found = next((q for q in self.questions(None) if q[0].finding_id == finding_id), None)
        if found is None:
            raise KeyError(finding_id)
        return found

    def inspect(self, expected_version: int, reviews: tuple[SemanticReview, ...] = ()) -> InspectionReport | AnswerHold:
        version, state = self.read()
        if version != expected_version:
            return AnswerHold("STALE_INPUT")
        snapshot = self._snapshot()
        if snapshot is None:
            return AnswerHold("INVENTORY_UNAVAILABLE")
        stored = {k: review_from_document(v) for k, v in (state.get("reviews") or {}).items()}
        for review in reviews:
            if stored.get(review.key, review) != review:
                return AnswerHold("REVIEW_CONFLICT")
            stored[review.key] = review  # A non-current revision holds only its requirement (UNVERIFIED).
        findings = dict(state.get("findings") or {})
        prior = {fid: e["history"][-1]["status"] for fid, e in findings.items()}
        current = {f.finding_id: f for f in inspect(snapshot, tuple(stored.values()), self.decision_actor, prior).findings}
        opened = []
        for fid, entry in sorted(findings.items()):
            if fid not in current and prior[fid] != STALE:
                findings[fid] = {**entry, "history": entry["history"] + [
                    {"status": STALE, "event": "input_changed", "inventory_digest": snapshot.digest}]}
        for fid, finding in sorted(current.items()):
            history = findings[fid]["history"] if fid in findings else []
            if history and history[-1]["status"] != STALE:
                continue
            cycle = 1 + sum(e["event"] in _OPENING for e in history)
            event = {"status": OPEN, "event": "reopened" if history else "inspection",
                     "inventory_digest": snapshot.digest, "work_item": question_work_item(fid, cycle)}
            findings[fid] = {"finding": asdict(finding), "history": history + [event]}
            opened.append((finding, event["work_item"]))
        for finding, work_item in opened:
            if self.channel is not None:
                self.channel.open(finding, work_item)  # Idempotent; registered before commit so replay cannot lose it.
        return self._commit(version, state, snapshot, stored, findings)

    def resolve(self, finding_id: str, decision: DecisionRecord, input_revision: str,
                expected_version: int) -> QuestionResolution | AnswerHold:
        version, state = self.read()
        if version != expected_version:
            return AnswerHold("STALE_INPUT", finding_id)
        snapshot = self._snapshot()
        if snapshot is None or not state or snapshot.digest != state["inventory_digest"]:
            return AnswerHold("STALE_INSPECTION", finding_id)
        entry = state["findings"].get(finding_id)
        if entry is None:
            return AnswerHold("UNKNOWN_FINDING", finding_id)
        finding, last = finding_from_document(entry["finding"]), entry["history"][-1]
        submission = decision.submission
        resolution_id = resolution_identity(finding_id, submission.idempotency_key, submission.actor)
        work_item = _work_item(entry["history"])
        if last["status"] == RESOLVED:
            # Replay returns the stored resolution only for the identical, still-attributable decision.
            same = (last["resolution_id"], last["input_revision"], last["authority_reference"], last["choice"],
                    last["work_item"]) == (resolution_id, input_revision, submission.authority_reference,
                                           submission.choice, submission.work_item)
            if same and self.resolution.validate(finding, work_item, decision) is None:
                return QuestionResolution(resolution_id, finding_id, finding.requirement_revision, last["actor"],
                                          last["authority_reference"], last["idempotency_key"], last["evidence_ref"])
            return AnswerHold("ALREADY_RESOLVED", finding_id)
        if last["status"] == STALE or input_revision != finding.requirement_revision:
            reason = "REVISION_HOLD"
        else:
            reason = self.resolution.validate(finding, work_item, decision)
        answer = {"finding_id": finding_id, "requirement_id": finding.requirement_id,
                  "requirement_revision": finding.requirement_revision, "input_revision": input_revision,
                  "work_item": submission.work_item, "actor": submission.actor, "event_actor": decision.event.actor,
                  "authority_reference": submission.authority_reference, "idempotency_key": submission.idempotency_key,
                  "choice": submission.choice, "outcome": reason or RESOLVED}
        ref = self._put("ambiguity.answer_rejected" if reason else "ambiguity.resolution", answer, ())
        event = {"status": last["status"] if reason else RESOLVED, "event": "answer_rejected" if reason else "decision",
                 "reason": reason, "resolution_id": None if reason else resolution_id, "actor": submission.actor,
                 "authority_reference": submission.authority_reference, "idempotency_key": submission.idempotency_key,
                 "choice": submission.choice, "work_item": submission.work_item,
                 "input_revision": input_revision, "evidence_ref": asdict(ref)}
        findings = {**state["findings"], finding_id: {**entry, "history": entry["history"] + [event]}}
        stored = {k: review_from_document(v) for k, v in state["reviews"].items()}
        committed = self._commit(version, state, snapshot, stored, findings)
        if isinstance(committed, AnswerHold):
            return AnswerHold(committed.reason, finding_id, asdict(ref))
        if reason:
            return AnswerHold(reason, finding_id, asdict(ref))
        return QuestionResolution(resolution_id, finding_id, finding.requirement_revision, submission.actor,
                                  submission.authority_reference, submission.idempotency_key, asdict(ref))

    def _snapshot(self):
        _, document = self.inventory.read()
        return None if document is None else snapshot_from_document(document)

    def _put(self, evidence_id: str, body: dict, preceding: tuple[Ref, ...]) -> Ref:
        value = canonical(body)
        record = Observation(Header(self.project, self.profile, evidence_id+":"+digest(body), digest(body),
                                    (self.definition_ref,), "private", preceding), self.definition_ref, evidence_id,
                             "ambiguity_inspection/v1", (), value, None, "ambiguity_inspection", self.invocation)
        ref = self.repository.put(record)
        self.repository.get(ref, self.access_scope)  # Read back before any pointer can reference it.
        return ref

    def _commit(self, version: int, state: dict, snapshot, reviews: dict[str, SemanticReview],
                findings: dict[str, dict]) -> InspectionReport | AnswerHold:
        statuses = {fid: e["history"][-1]["status"] for fid, e in findings.items()}
        report = inspect(snapshot, tuple(reviews.values()), self.decision_actor, statuses)
        preceding = (Ref(**state["report_ref"]),) if state else ()
        if state and state["report_digest"] == report.digest and state["findings"] == findings:
            return report
        ref = self._put("ambiguity.report", asdict(report), preceding)
        new_state = {"schema_version": 1, "inventory_digest": snapshot.digest, "report_ref": asdict(ref),
                     "report_digest": report.digest, "findings": findings,
                     "reviews": {k: asdict(r) for k, r in sorted(reviews.items())}}
        try:
            self.store.commit(self.profile, self.aggregate, version, new_state)
        except VersionConflict:
            return AnswerHold("STALE_INPUT")  # Never blindly retry a decision.
        return report
