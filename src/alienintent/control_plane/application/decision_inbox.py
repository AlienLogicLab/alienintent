"""Durable decision inbox; mutation is handed back to normal factory guards."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from alienintent.execution_coordination.domain.escalation import (
    DecisionConflict, DecisionRecord, DecisionRecorded, DecisionSubmission,
    HumanDecisionRequired, SupersededDecision,
)
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict


class DecisionAdmission(Protocol):
    def validate_decision(self, record: DecisionRecord) -> None: ...
    def record_decision(self, record: DecisionRecord) -> None: ...
    def resume_after_decision(self) -> None: ...


class DecisionInbox:
    """Lists unresolved authority requests and records attributable decisions."""

    _INDEX = "decision-inbox"

    def __init__(self, store: OperationalStore, admission: DecisionAdmission, profile: str) -> None:
        self._store, self._admission, self._profile = store, admission, profile

    def register(self, escalation: HumanDecisionRequired) -> None:
        version, raw = self._store.read_state(self._profile, self._INDEX)
        entries = dict(raw.get("open", {}))
        entries.setdefault(escalation.work_item, _encode_escalation(escalation))
        self._store.commit(self._profile, self._INDEX, version, {"open": entries})

    def list_open(self) -> tuple[HumanDecisionRequired, ...]:
        _, raw = self._store.read_state(self._profile, self._INDEX)
        entries = raw.get("open", {})
        if not isinstance(entries, dict):
            return ()
        return tuple(_decode_escalation(value) for _, value in sorted(entries.items()) if isinstance(value, dict))

    def show(self, work_item: str) -> DecisionRecord | HumanDecisionRequired:
        open_request = next((entry for entry in self.list_open() if entry.work_item == work_item), None)
        if open_request is not None:
            return open_request
        _, raw = self._store.read_state(self._profile, f"decision:{work_item}")
        if raw:
            return _decode_record(raw)
        raise KeyError(work_item)

    def submit(self, submission: DecisionSubmission) -> DecisionRecord:
        try:
            existing = self._record_for_key(submission.idempotency_key)
        except KeyError:
            existing = None
        if existing is not None:
            if existing.submission != submission:
                raise DecisionConflict("idempotency key already records a different decision")
            if any(entry.work_item == submission.work_item for entry in self.list_open()):
                return existing
            self._admission.record_decision(existing)
            self._close_open(submission.work_item)
            self._admission.resume_after_decision()
            return existing
        escalation = next((entry for entry in self.list_open() if entry.work_item == submission.work_item), None)
        if escalation is None or escalation.biu_version != submission.biu_version:
            raise SupersededDecision("decision does not name an open BIU version")
        if submission.choice not in escalation.options:
            raise ValueError("decision choice is not one of the escalated options")
        record = DecisionRecord(submission, DecisionRecorded(submission.work_item, submission.biu_version, submission.idempotency_key, submission.actor))
        self._admission.validate_decision(record)
        self._commit_new(record)
        self._admission.record_decision(record)
        self._close_open(submission.work_item)
        self._admission.resume_after_decision()
        return record

    def _record_for_key(self, key: str) -> DecisionRecord:
        _, raw = self._store.read_state(self._profile, f"decision-key:{key}")
        if not raw:
            raise KeyError(key)
        return _decode_record(raw)

    def _commit_new(self, record: DecisionRecord) -> None:
        payload = _encode_record(record)
        key = f"decision-key:{record.submission.idempotency_key}"
        version, existing = self._store.read_state(self._profile, key)
        if existing:
            prior = _decode_record(existing)
            if prior.submission != record.submission:
                raise DecisionConflict("idempotency key already records a different decision")
            return
        try:
            self._store.commit(self._profile, key, version, payload)
            work_version, _ = self._store.read_state(self._profile, f"decision:{record.event.work_item}")
            self._store.commit(self._profile, f"decision:{record.event.work_item}", work_version, payload)
        except VersionConflict as error:
            raise DecisionConflict("concurrent decision submission") from error

    def _close_open(self, work_item: str) -> None:
        version, raw = self._store.read_state(self._profile, self._INDEX)
        entries = dict(raw.get("open", {}))
        entries.pop(work_item, None)
        self._store.commit(self._profile, self._INDEX, version, {"open": entries})


def _encode_escalation(value: HumanDecisionRequired) -> dict[str, object]:
    return asdict(value)


def _decode_escalation(value: dict[str, object]) -> HumanDecisionRequired:
    return HumanDecisionRequired(**{key: tuple(entry) if key in {"options", "tradeoffs", "affected_requirements", "affected_architecture", "authorizations"} else entry for key, entry in value.items()})  # type: ignore[arg-type]


def _encode_record(value: DecisionRecord) -> dict[str, object]:
    return {"submission": asdict(value.submission), "event": asdict(value.event)}


def _decode_record(value: dict[str, object]) -> DecisionRecord:
    submission = value["submission"]
    event = value["event"]
    if not isinstance(submission, dict) or not isinstance(event, dict):
        raise ValueError("invalid durable decision record")
    return DecisionRecord(DecisionSubmission(**submission), DecisionRecorded(**event))  # type: ignore[arg-type]
