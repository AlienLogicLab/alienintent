"""Retained Readiness Assessment consumer over the shared EvidenceRepository and OperationalStore.

Raw result bytes are stored privately, byte-for-byte, before any normalization. Every attempt is opened (its UUID
persisted) before invocation, and every outcome is a new immutable record; the readiness:<identity> pointer is
append-only for attempts and commits only by expected version. Applicability is decided at read time and kept
separately; no old assessment is ever rewritten. Nothing here writes factory:* or release:* state.
"""
import base64
from dataclasses import asdict, replace
import json
from typing import Callable
import uuid

from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_CONFLICT, ATTEMPT_IN_PROGRESS, CONTRACT_VERSION, MALFORMED, NO_ASSESSMENT, PERSISTENCE_CONFLICT, PROVENANCE,
    RAW_EVIDENCE_NOT_RETAINED, STALE_ASSESSMENT, UNKNOWN, AttemptFailure, AttemptMetadata, Hold, ProducerBinding, ReadinessEligibility,
    SemanticAssessment, binding_refusal, canonical, decide, digest, provenance_failure, recognize,
    response_problem)
from alienintent.execution_coordination.domain.readiness import HistoricalAssessment
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer, SurrogateHistoryReplay

RETAINED_ASSESSMENT = "readiness.assessment.retained"  # The raw-bytes event U7's assessment history reads back.
OPENED, OBSERVED, FAILED = "readiness.attempt_opened", "readiness.observed", "readiness.attempt_failed"
STALE, INVALIDATED = "readiness.stale", "readiness.invalidated"
SURROGATE_RAW, SURROGATE = "readiness.surrogate_history.raw", "readiness.surrogate_history.retained"


def _put(owner, event: str, logical_id: str, value: str, method: str, raw_digest: str,
         preceding: tuple[Ref, ...] = ()) -> Ref:
    record = Observation(Header(owner.project, owner.profile, logical_id, raw_digest.removeprefix("sha256:"),
                                (owner.definition_ref,), "private", preceding), owner.definition_ref, event, method,
                         (), value, None, "readiness-consumer", owner.invocation, raw_digest)
    ref = owner.repository.put(record)
    owner.repository.get(ref, owner.access_scope)  # Read back before any pointer can reference it.
    return ref


def _document(owner, event: str, logical_id: str, body: dict, preceding: tuple[Ref, ...] = ()) -> Ref:
    value = canonical(body)
    return _put(owner, event, logical_id, value, "readiness_consumer/v1", digest(value), preceding)


def _raw(owner, event: str, logical_id: str, raw: bytes, preceding: tuple[Ref, ...] = ()) -> Ref:
    try:
        value, method = raw.decode("utf-8"), "raw-bytes/utf-8"
    except UnicodeDecodeError:
        value, method = base64.b64encode(raw).decode("ascii"), "raw-bytes/base64"
    return _put(owner, event, logical_id, value, method, digest(raw), preceding)


def _read(owner, ref: dict) -> Observation:
    record = owner.repository.get(ref_from_document(ref), owner.access_scope)
    if not isinstance(record, Observation):
        raise EvidenceHold("NOT_READINESS_EVIDENCE", (ref_from_document(ref),))
    return record


class RetainedAssessmentConsumer(AssessmentConsumer):
    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, access_scope: frozenset[str],
                 ids: Callable[[], str] | None = None) -> None:
        self.repository, self.store, self.project, self.profile = repository, store, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope
        self._ids = ids or (lambda: str(uuid.uuid4()))

    @staticmethod
    def aggregate(identity: str) -> str:
        return "readiness:" + identity

    def read(self, identity: str) -> tuple[int, dict]:
        version, state = self.store.read_state(self.profile, self.aggregate(identity))
        return version, {"schema_version": 1, "identity": identity, "attempts": [], "applicability": None,
                         "invalidated": [], "events": [], **state}

    def _commit(self, identity: str, version: int, state: dict, attempt: str | None = None) -> Hold | None:
        try:
            self.store.commit(self.profile, self.aggregate(identity), version, state)
        except VersionConflict:
            return Hold(PERSISTENCE_CONFLICT, identity, attempt, "pointer moved; no blind retry")
        return None

    @staticmethod
    def _event(state: dict, event: str, attempt: str | None, ref: Ref) -> list:
        return [*state["events"], {"event": event, "attempt_id": attempt, "ref": asdict(ref)}]

    def open(self, identity: str, input_fingerprint: str, input_sha256: str, contract_digest: str | None,
             predecessor: dict | None, lint_ref: dict | None, binding: ProducerBinding | None) -> str | Hold:
        version, state = self.read(identity)
        attempts = state["attempts"]
        if any(a["outcome"] is None and a["input_fingerprint"] == input_fingerprint for a in attempts):
            return Hold(ATTEMPT_IN_PROGRESS, identity, None, "one active assessment per input fingerprint")
        attempt = self._ids()
        # A predecessor is an attempt of this unit, or the SPLIT attempt of the unit this one was split from.
        source = (attempts if not predecessor or predecessor["identity"] == identity
                  else self.read(predecessor["identity"])[1]["attempts"])
        prior = next((a for a in source if predecessor and a["attempt_id"] == predecessor["attempt_id"]), None)
        ref = _document(self, OPENED, f"readiness/{identity}/{attempt}", {
            "record_kind": "AssessmentAttempt", "attempt_id": attempt, "identity": identity,
            "input_fingerprint": input_fingerprint, "input_sha256": input_sha256, "contract_digest": contract_digest,
            "predecessor": predecessor, "predecessor_ref": prior["opened_ref"] if prior else None,
            "lint_ref": lint_ref, "binding": asdict(binding) if binding else None},
            (ref_from_document(prior["opened_ref"]),) if prior else ())
        entry = {"attempt_id": attempt, "opened_ref": asdict(ref), "input_fingerprint": input_fingerprint,
                 "input_sha256": input_sha256, "contract_digest": contract_digest, "predecessor": predecessor,
                 "raw_ref": None, "outcome_ref": None, "outcome": None}
        attempts = [*attempts, entry]
        hold = self._commit(identity, version, {**state, "attempts": attempts,
                                                "events": self._event(state, OPENED, attempt, ref)}, attempt)
        return hold or attempt

    def observe(self, raw_artifact: bytes | None, attempt_metadata: AttemptMetadata,
                recognized_shape: str) -> SemanticAssessment | AttemptFailure | Hold:
        identity, attempt = attempt_metadata.identity, attempt_metadata.attempt_id
        problem = response_problem(raw_artifact, attempt_metadata, recognized_shape)
        if problem:  # Trust none of a wrong-typed response; the failure is built from consumer values only.
            raw_artifact, recognized_shape = None, "invalid"
            attempt_metadata = replace(attempt_metadata, exit_status=None, timed_out=False, custody=None)
        version, state = self.read(identity)
        entry = next((a for a in state["attempts"] if a["attempt_id"] == attempt), None)
        if entry is None:
            return Hold(NO_ASSESSMENT, identity, attempt, "response for an attempt that was never opened")
        raw_digest = digest(raw_artifact) if raw_artifact is not None else None
        if entry["outcome"] is not None:
            if entry["outcome"]["raw_digest"] == raw_digest:
                return self._result(entry)  # A duplicate response attaches to the same attempt.
            return Hold(ATTEMPT_CONFLICT, identity, attempt, "a different terminal response for this attempt")
        # Raw evidence first, byte-for-byte, before any parsing or normalization.
        raw_ref, unretained = None, None
        try:
            raw_ref = (_raw(self, RETAINED_ASSESSMENT, f"readiness/{identity}/{attempt}/raw", raw_artifact)
                       if raw_artifact is not None else None)
        except EvidenceHold as hold:
            unretained = hold.reason_code  # Unretained bytes can never supply readiness.
        try:
            result = (AttemptFailure(MALFORMED, (), problem, None) if problem else
                      AttemptFailure(RAW_EVIDENCE_NOT_RETAINED, (), unretained, raw_digest) if unretained else
                      recognize(raw_artifact, attempt_metadata.exit_status, attempt_metadata.timed_out,
                                recognized_shape))
        except (TypeError, ValueError, RecursionError) as error:  # Unrecognizable fails the attempt; never open.
            result = AttemptFailure(MALFORMED, (), type(error).__name__, raw_digest)
        body = json.loads(result.body) if isinstance(result, SemanticAssessment) else None
        if isinstance(result, SemanticAssessment):
            reason = provenance_failure(attempt_metadata.binding, attempt_metadata, body)
            if reason:
                result = AttemptFailure(PROVENANCE, result.values, reason, result.raw_digest)
        try:
            document = self._outcome(result, attempt_metadata, recognized_shape, raw_digest, body)
            canonical(document)  # Proves the record is writable before anything depends on it.
        except Exception as error:  # Unrecordable producer evidence fails closed.
            result = AttemptFailure(MALFORMED, tuple(v for v in result.values if isinstance(v, str)),
                                    "producer evidence is not recordable: " + type(error).__name__, raw_digest)
            document = self._outcome(result, replace(attempt_metadata, custody=None), recognized_shape, raw_digest,
                                     None)
        preceding = (ref_from_document(entry["opened_ref"]), *((raw_ref,) if raw_ref else ()))
        event = OBSERVED if isinstance(result, SemanticAssessment) else FAILED
        outcome_ref = _document(self, event, f"readiness/{identity}/{attempt}/outcome", document, preceding)
        outcome = {"raw_digest": raw_digest, "disposition": document.get("disposition"),
                   "failure_class": document.get("failure_class")}
        hold = None
        for _ in range(2):  # The outcome record is immutable; one re-read binds it after a moved pointer.
            if hold is not None:
                version, state = self.read(identity)
                current = next((a for a in state["attempts"] if a["attempt_id"] == attempt), None)
                if current is None or current["outcome"] is not None:
                    return Hold(ATTEMPT_CONFLICT, identity, attempt, "the attempt changed while it was observed")
            attempts = [{**a, "raw_ref": asdict(raw_ref) if raw_ref else None, "outcome_ref": asdict(outcome_ref),
                         "outcome": outcome} if a["attempt_id"] == attempt else a for a in state["attempts"]]
            hold = self._commit(identity, version, {**state, "attempts": attempts,
                                                    "events": self._event(state, event, attempt, outcome_ref)},
                                attempt)
            if hold is None:
                return result
        return hold

    def _outcome(self, result: SemanticAssessment | AttemptFailure, metadata: AttemptMetadata, shape: str,
                 raw_digest: str | None, body: object) -> dict:
        document = {"record_kind": "ReadinessObservation" if isinstance(result, SemanticAssessment)
                    else "AttemptFailure", "attempt_id": metadata.attempt_id, "identity": metadata.identity,
                    "shape": shape, "raw_digest": raw_digest, "values": list(result.values),
                    "exit_status": metadata.exit_status, "timed_out": metadata.timed_out,
                    "provenance": self._provenance(metadata, body)}
        if isinstance(result, SemanticAssessment):
            document.update(disposition=result.disposition, body=result.body,
                            owner_clarifications=list(result.owner_clarifications))
        else:
            document.update(failure_class=result.failure_class, detail=result.detail)
        return document

    @staticmethod
    def _provenance(metadata: AttemptMetadata, body: object) -> dict:
        """C#/contracts/4/provenance_contract fields; provider_evidence is retained unmodified and never trusted."""
        binding, custody = metadata.binding, metadata.custody
        return {"producer": binding.product if binding else UNKNOWN,
                "product_version": binding.product_version if binding else UNKNOWN,
                "version_source": binding.version_source if binding else UNKNOWN,
                "editable_revision": binding.editable_revision if binding else None,
                "executable": binding.executable if binding else None,
                "transport": binding.transport if binding else None,
                "schema_binding": binding.schema_binding if binding else None,
                "contract_version": CONTRACT_VERSION,
                "binding_refusal": binding_refusal(binding),
                "provider": custody.provider if custody else None,
                "provider_evidence": body.get("provider_evidence") if isinstance(body, dict) else None,
                "model": UNKNOWN,
                "input_fingerprint": metadata.input_fingerprint, "input_sha256": metadata.input_sha256,
                "invocation": asdict(custody) if custody else None,
                "exit_status": metadata.exit_status, "timed_out": metadata.timed_out}

    def _result(self, entry: dict) -> SemanticAssessment | AttemptFailure:
        document = json.loads(_read(self, entry["outcome_ref"]).value)
        if document["record_kind"] == "ReadinessObservation":
            return SemanticAssessment(document["disposition"], document["body"],
                                      tuple(document["owner_clarifications"]), tuple(document["values"]),
                                      document["shape"], document["raw_digest"])
        return AttemptFailure(document["failure_class"], tuple(document["values"]), document["detail"],
                              document["raw_digest"])

    def consume(self, identity: str, current_input_fingerprint: str) -> ReadinessEligibility | Hold:
        version, state = self.read(identity)
        entry = state["attempts"][-1] if state["attempts"] else None
        result = decide(identity, entry, current_input_fingerprint, frozenset(state["invalidated"]))
        status = "APPLICABLE" if isinstance(result, ReadinessEligibility) else "INAPPLICABLE"
        applicability = {"attempt_id": entry["attempt_id"] if entry else None, "status": status,
                         "reason": getattr(result, "reason_code", None),
                         "input_fingerprint": current_input_fingerprint}
        if applicability == state["applicability"]:
            return result
        events = state["events"]
        if isinstance(result, Hold) and result.reason_code == STALE_ASSESSMENT:
            ref = _document(self, STALE, f"readiness/{identity}/stale/{current_input_fingerprint}",
                                         {"record_kind": "StaleAssessment", **applicability, "detail": result.detail,
                                          "assessed_fingerprint": entry["input_fingerprint"]})
            events = self._event(state, STALE, result.attempt_id, ref)
        hold = self._commit(identity, version, {**state, "applicability": applicability, "events": events})
        return hold or result

    def latest(self, identity: str) -> dict | None:
        attempts = self.read(identity)[1]["attempts"]
        return attempts[-1] if attempts else None

    def history(self, identity: str) -> tuple[dict, ...]:
        return tuple(self.read(identity)[1]["attempts"])

    def raw(self, identity: str, attempt_id: str) -> tuple[dict, str] | None:
        entry = next((a for a in self.history(identity) if a["attempt_id"] == attempt_id), None)
        if entry is None or entry["raw_ref"] is None:
            return None
        return entry["raw_ref"], _read(self, entry["raw_ref"]).value

    def annotate(self, identity: str, attempt_id: str, key: str, value: object) -> Hold | None:
        """Record a routing fact on an attempt once; a different later value is a conflict, not an overwrite."""
        hold = None
        for _ in range(2):  # The annotation is idempotent, so one re-read after a moved pointer is safe.
            version, state = self.read(identity)
            entry = next((a for a in state["attempts"] if a["attempt_id"] == attempt_id), None)
            if entry is None:
                return Hold(NO_ASSESSMENT, identity, attempt_id)
            if key in entry:
                return None if entry[key] == value else Hold(ATTEMPT_CONFLICT, identity, attempt_id, key)
            attempts = [{**a, key: value} if a["attempt_id"] == attempt_id else a for a in state["attempts"]]
            hold = self._commit(identity, version, {**state, "attempts": attempts}, attempt_id)
            if hold is None:
                return None
        return hold

    def invalidate(self, identity: str, reason: str, cause: str) -> Hold | None:
        """Mark the current attempt inapplicable; its immutable records are unchanged."""
        version, state = self.read(identity)
        entry = state["attempts"][-1] if state["attempts"] else None
        if entry is None or entry["attempt_id"] in state["invalidated"]:
            return None
        ref = _document(self, INVALIDATED, f"readiness/{identity}/{entry['attempt_id']}/invalidated",
                                     {"record_kind": "ApplicabilityInvalidated", "identity": identity,
                                      "attempt_id": entry["attempt_id"], "reason": reason, "cause": cause})
        return self._commit(identity, version, {
            **state, "invalidated": [*state["invalidated"], entry["attempt_id"]],
            "applicability": {"attempt_id": entry["attempt_id"], "status": "INAPPLICABLE", "reason": reason,
                              "input_fingerprint": entry["input_fingerprint"]},
            "events": self._event(state, INVALIDATED, entry["attempt_id"], ref)}, entry["attempt_id"])

    def retain(self, identity: str, event: str, document: dict) -> dict:
        return asdict(_document(self, event, f"readiness/{identity}/{event}/{digest(canonical(document))}",
                                             document))


class RetainedSurrogateHistory(SurrogateHistoryReplay):
    """Historical Surrogate Readiness Assessments retained verbatim by revision; never an attempt or a disposition."""

    def __init__(self, repository: EvidenceRepository, project: str, profile: str, definition_ref: Ref,
                 invocation: str, access_scope: frozenset[str]) -> None:
        self.repository, self.project, self.profile = repository, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope

    def replay(self, history: tuple[HistoricalAssessment, ...]) -> tuple[dict, ...] | Hold:
        for item in history:
            if digest(item.raw) != "sha256:" + item.sha256:
                return Hold("HISTORY_DIGEST_MISMATCH", item.path, None, item.blob)
        records, previous = [], ()
        for item in history:
            raw_ref = _raw(self, SURROGATE_RAW, f"surrogate/{item.blob}", item.raw)
            document = json.loads(item.raw)
            disposition = document.get("disposition")
            evidence = document.get("provider_evidence") if isinstance(document.get("provider_evidence"), dict) else {}
            record = {"record_kind": "SurrogateReadinessAssessment", "producer": item.producer,
                      "native_agent_ready": False,
                      "disposition": disposition, "revision": item.revision, "path": item.path, "blob": item.blob,
                      "raw_sha256": item.sha256, "raw_ref": asdict(raw_ref),
                      "assessed_baseline": evidence.get("baseline"),
                      "label": "SURROGATE_READINESS_HISTORY_NOT_AGENT_READY"}
            ref = _document(self, SURROGATE, f"surrogate/{item.revision}", record, (*previous, raw_ref))
            records.append({**record, "ref": asdict(ref)})
            previous = (ref,)
        return tuple(records)
