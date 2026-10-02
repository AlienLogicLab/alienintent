"""PacketAssessment: run Agent Ready on the exact instructions a hand-registered work item points at (`work assess`).

The instructions are the bytes `git show <commit>:<path>` returns for the item's pointer, read through the work-record
service; the attempt, Agent Ready's raw output and the outcome are kept in the existing retained-assessment store,
and the item's `assessment_ref` names that raw output. A completed assessment of the same instructions is reused; a
failed one is run again. An attempt left without an outcome is recovered only when the operator names it and every
process that could still deliver its result has ended. The assessment is a record only: nothing here consumes it,
changes the item's state, approves or releases anything.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

from alienintent.context_assembly.application.readiness_service import PROVENANCE_HELD, ReadinessAdmission
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import (
    ASSESSMENT_PROCESS_RUNNING, IDENTITY_RETIRED, INSTRUCTIONS_NOT_TEXT, INTERRUPTED, NOT_A_REGISTERED_PACKET, OWNER,
    UNKNOWN_IDENTITY, PacketAssessed, fingerprint, in_progress, instructions_text, registered_packet, reusable)
from alienintent.context_assembly.domain.work_identity import Pointer, WorkIdentityRefused
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_CONFLICT, ATTEMPT_FAILURE, ATTEMPT_IN_PROGRESS, CAPABILITY_PROVENANCE_HOLD, NO_ASSESSMENT, AttemptFailure,
    AttemptMetadata, CandidateWorkUnit, Hold, ProducerBinding, binding_refusal, digest)
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer, ReadinessAssessment

# The worker runtime's answer for an owner process that has conclusively ended.
TERMINATED = "terminated"


class ProcessOwnership(Protocol):
    """The worker runtime's process ownership observation, as this service uses it (bound by composition)."""

    def current(self) -> Mapping[str, object] | None: ...

    def owner_state(self, owner: Mapping[str, object]) -> str: ...

    def owned_work(self, invocation_id: str, owner: str | None = None) -> tuple[int, ...] | None: ...


class PacketAssessment:
    def __init__(self, records: WorkRecordService, identities: WorkIdentityService, consumer: AssessmentConsumer,
                 binding: ProducerBinding | None, ownership: ProcessOwnership,
                 producer: Callable[[str, Mapping[str, object]], ReadinessAssessment | None]) -> None:
        self.records, self.identities, self.consumer, self.binding = records, identities, consumer, binding
        self.ownership, self.producer = ownership, producer

    def assess(self, id_or_label: str, revision: tuple[bytes, str] | None = None,
               recover: str | None = None) -> PacketAssessed | Hold:
        """`revision` is (the packet file's bytes, the commit holding them); `recover` names the interrupted attempt."""
        if revision is not None and recover is not None:
            raise ValueError("a revision cannot be combined with recovery")
        record = self.records.show(id_or_label)
        if record is None:
            return Hold(UNKNOWN_IDENTITY, id_or_label)
        item = record.item
        if not registered_packet(item.request_ref) or item.pointer is None:
            return Hold(NOT_A_REGISTERED_PACKET, item.id, None, item.request_ref)
        if item.retired:
            return Hold(IDENTITY_RETIRED, item.id)
        if revision is None and instructions_text(record.packet) is None:
            return Hold(INSTRUCTIONS_NOT_TEXT, item.id)
        refusal = binding_refusal(self.binding)
        if refusal:
            self.consumer.retain(item.id, PROVENANCE_HELD, {
                "record_kind": "CapabilityProvenanceHold", "reason_code": CAPABILITY_PROVENANCE_HOLD,
                "identity": item.id, "refusal": refusal, "binding": repr(self.binding), "launched": False})
            return Hold(CAPABILITY_PROVENANCE_HOLD, item.id, None, refusal)
        if revision is not None:
            packet, commit = revision
            if instructions_text(packet) is None:
                return Hold(INSTRUCTIONS_NOT_TEXT, item.id)
            try:
                self.identities.set_pointer(item.id, Pointer(item.pointer.repo, item.pointer.path, commit, packet))
            except WorkIdentityRefused as error:
                return Hold(error.code, item.id, None, ", ".join(error.values))
            record = self.records.show(item.id)
            item = record.item
        text = instructions_text(record.packet)
        current, input_sha256 = fingerprint(item.id, item.pointer), digest(text)
        history = self.consumer.history(item.id)
        active = in_progress(history, current)
        if recover is not None:
            if active is None or active["attempt_id"] != recover:
                return Hold(NO_ASSESSMENT, item.id, recover, "not the in-progress attempt for these instructions")
            held = self._confirm_exit(item.id, active)
            if held is not None:
                return held
            failed = self.consumer.observe(None, AttemptMetadata(item.id, recover, current, input_sha256, None, False,
                                                                 None, self.binding), INTERRUPTED)
            if isinstance(failed, Hold):
                return failed  # The original finished first; nothing is launched.
        else:
            latest = history[-1] if history else None
            if reusable(latest, current):
                return self._saved(item.id, latest["attempt_id"], current, latest["outcome"]["disposition"], True)
            if active is not None:
                return Hold(ATTEMPT_IN_PROGRESS, item.id, active["attempt_id"], "recover it by naming it")
        return self._run(item.id, text, current, input_sha256)

    def _run(self, identity: str, text: str, current: str, input_sha256: str) -> PacketAssessed | Hold:
        latest = self.consumer.latest(identity)
        predecessor = {"identity": identity, "attempt_id": latest["attempt_id"]} if latest is not None else None
        attempt = self.consumer.open(identity, current, input_sha256, None, predecessor, None, self.binding)
        if isinstance(attempt, Hold):
            if attempt.reason_code == ATTEMPT_IN_PROGRESS:  # Another run opened it meanwhile; name that attempt.
                active = in_progress(self.consumer.history(identity), current)
                return Hold(ATTEMPT_IN_PROGRESS, identity, active["attempt_id"] if active else None, attempt.detail)
            return attempt
        owner = self.ownership.current()
        held = (self.consumer.annotate(identity, attempt, OWNER, dict(owner)) if owner is not None else
                Hold(ATTEMPT_IN_PROGRESS, identity, attempt, "this process is not observable; nothing was launched"))
        if held is not None:
            return held  # The owner is not recorded, so nothing is launched.
        response = ReadinessAdmission.produce(self.producer(attempt, owner),
                                              CandidateWorkUnit(identity, text, attempt, current))
        metadata = AttemptMetadata(identity, attempt, current, input_sha256, response.exit_status,
                                   response.timed_out, response.custody, self.binding)
        observed = self.consumer.observe(response.raw, metadata, response.shape)
        if isinstance(observed, Hold):
            return observed
        if isinstance(observed, AttemptFailure):
            return Hold(ATTEMPT_FAILURE, identity, attempt, observed.failure_class)
        return self._saved(identity, attempt, current, observed.disposition, False)

    def _saved(self, identity: str, attempt: str, assessed: str, disposition: str, reused: bool) -> PacketAssessed:
        """Save the raw-output reference on the item only while its pointer is still the one assessed."""
        record = self.records.show(identity)
        if record is None or record.item.pointer is None or fingerprint(identity, record.item.pointer) != assessed:
            return PacketAssessed(identity, attempt, disposition, None, reused)
        raw_ref, _ = self.consumer.raw(identity, attempt)
        self.identities.set_evidence(identity, "assessment", ref_from_document(raw_ref))
        return PacketAssessed(identity, attempt, disposition, raw_ref, reused)

    def _confirm_exit(self, identity: str, entry: dict) -> Hold | None:
        """None only when the recorded owner is this recovery or has terminated and no process carries the marker.
        With no owner recorded, this recovery claims the write-once owner key first, so a paused original that has
        not recorded its owner yet can no longer launch."""
        attempt, mine = entry["attempt_id"], self.ownership.current()
        if OWNER not in entry:
            if mine is None:
                return Hold(ASSESSMENT_PROCESS_RUNNING, identity, attempt, "this process is not observable")
            claimed = self.consumer.annotate(identity, attempt, OWNER, dict(mine))
            if claimed is not None and claimed.reason_code != ATTEMPT_CONFLICT:
                return claimed
            entry = next(a for a in self.consumer.history(identity) if a["attempt_id"] == attempt)
        owner = entry[OWNER]
        running = [] if mine is not None and owner == dict(mine) or self.ownership.owner_state(owner) == TERMINATED \
            else [owner.get("pid")]
        owned = self.ownership.owned_work(attempt)
        if owned is None or running or owned:
            pids = ",".join(str(pid) for pid in (*running, *(owned or ())))
            return Hold(ASSESSMENT_PROCESS_RUNNING, identity, attempt, pids or "process table not readable")
        return None
