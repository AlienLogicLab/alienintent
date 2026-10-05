"""WorkAuthorization: record the Founder's authorization of a registered work item as its release record
(`work authorize`).

The command records the Founder's approval; it does not grant it. It writes only when the exact packet commit,
assessment attempt and starting revision the Founder approved are still the item's current ones, the packet's
contract block is valid for the item and the existing release gate's preconditions, over the same wording the gate
checks at launch, would accept the record. One
evidence record binds the item, its pointer, its assessment, its contract digest, the baseline, the approver and
the Founder's words; its content digest is the release record's `record_ref`. Writes, in this order: the evidence
record, the release record (the commit point: written only if none exists, read back), the row's `approval_ref`.
Nothing here changes the item's workflow state, writes to GitHub or launches anything.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
import re
from typing import Protocol

from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import IDENTITY_RETIRED, UNKNOWN_IDENTITY, fingerprint
from alienintent.context_assembly.domain.work_contract import CONTRACT_INVALID, ContractInvalid, contract_block
from alienintent.context_assembly.domain.work_identity import CAPTURE, WorkItem
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.release import (
    BaselineEvidence, ReleaseAuthorization, ReleasePreconditionRefused, admit_release_preconditions, release_wording)
from alienintent.execution_coordination.ports.operational_store import VersionConflict
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer
from alienintent.execution_coordination.ports.release_admission import RevisionResolver

# Answers `work authorize` returns instead of writing: `ALREADY_AUTHORIZED` after a lost VersionConflict leaves this
# run's evidence object unreferenced; every other refusal writes nothing.
NOT_AUTHORIZABLE, AUTHORIZATION_STALE = "NOT_AUTHORIZABLE", "AUTHORIZATION_STALE"
BASELINE_INVALID, GATE_WOULD_REFUSE, ALREADY_AUTHORIZED = "BASELINE_INVALID", "GATE_WOULD_REFUSE", "ALREADY_AUTHORIZED"
# `work assess` refuses to move the pointer or open an attempt of an authorized item.
AUTHORIZED_INSTRUCTIONS_FIXED = "AUTHORIZED_INSTRUCTIONS_FIXED"
CONTRACT_UNSATISFIABLE = "CONTRACT_UNSATISFIABLE"
# The evidence record's fixed values, the way the READY view fixes its own: the same inputs give the same reference.
WORK_AUTHORIZATION = "work-authorization"
COMMIT = re.compile(r"[0-9a-f]{40}")


class ReleaseRecords(Protocol):
    """The existing durable release records, as this service uses them (bound by composition)."""

    def record(self, authorization: ReleaseAuthorization) -> None:
        """Create-only: VersionConflict when any release record already exists for the identity."""

    def release_authorization(self, identity: str) -> ReleaseAuthorization | None: ...


@dataclass(frozen=True)
class AuthorizationResult:
    """What `work authorize` answers. `answer` is None when the authorization is recorded (`repeated` when it already
    was); otherwise it is the refusal code and `detail` names which check refused."""
    identity: str
    answer: str | None = None
    evidence_ref: dict | None = None
    authorization: dict | None = None
    repeated: bool = False
    detail: str = ""


class WorkAuthorization:
    def __init__(self, records: WorkRecordService, identities: WorkIdentityService, consumer: AssessmentConsumer,
                 evidence: EvidenceRepository, project: str, profile: str, releases: ReleaseRecords,
                 revisions: RevisionResolver, release_points: Mapping[str, str],
                 satisfiable: Callable[[bytes, str, str], tuple[str, ...]] | None = None) -> None:
        """`project` and `profile` are the evidence repository's; `release_points` maps each configured repository to
        its default branch, the release point the release gate is composed with."""
        self.records, self.identities, self.consumer, self.evidence = records, identities, consumer, evidence
        self.releases, self.revisions, self.release_points = releases, revisions, dict(release_points)
        self.satisfiable = satisfiable
        self.definition = Ref(project, profile, WORK_AUTHORIZATION + "/definition",
                              "sha256:" + sha256(b"alienintent.context_assembly.application.work_authorization:"
                                                 b"work-authorization").hexdigest(),
                              "python:alienintent.context_assembly.application.work_authorization")

    def authorize(self, id_or_label: str, commit: str, attempt: str, baseline: str, quote: str) -> AuthorizationResult:
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError("the Founder's exact words are required")
        record = self.records.show(id_or_label)
        if record is None:
            return AuthorizationResult(id_or_label, UNKNOWN_IDENTITY)
        item = record.item
        if item.retired:
            return AuthorizationResult(item.id, IDENTITY_RETIRED)
        if item.state != CAPTURE or item.pointer is None:
            return AuthorizationResult(item.id, NOT_AUTHORIZABLE, detail=f"state {item.state}"
                                       if item.state != CAPTURE else "no packet pointer")
        stale, entry = self._stale(item, commit, attempt)
        if stale:
            return AuthorizationResult(item.id, AUTHORIZATION_STALE, detail=stale)
        try:
            contract = contract_block(record.packet, item.id)
        except ContractInvalid as error:
            return AuthorizationResult(item.id, CONTRACT_INVALID, detail=str(error))
        if self.satisfiable is not None:
            reasons = self.satisfiable(record.packet, item.pointer.commit, item.id)
            if reasons:
                return AuthorizationResult(item.id, CONTRACT_UNSATISFIABLE, detail="; ".join(reasons))
        repo = item.pointer.repo
        release_point = self.release_points.get(repo)
        if COMMIT.fullmatch(baseline) is None:
            return AuthorizationResult(item.id, BASELINE_INVALID, detail="not an exact 40-hex commit")
        resolves = release_point is not None and self.revisions.resolves(repo, baseline)
        if not resolves:
            return AuthorizationResult(item.id, BASELINE_INVALID, detail=f"does not resolve in {repo}")
        reachable = self.revisions.is_reachable(repo, baseline, release_point)
        if not reachable:
            return AuthorizationResult(item.id, BASELINE_INVALID, detail=f"not reachable from {release_point}")
        evidence = Observation(
            Header(self.definition.project, self.definition.profile, f"{WORK_AUTHORIZATION}/{item.id}", "1",
                   (self.definition,)),
            self.definition, WORK_AUTHORIZATION, WORK_AUTHORIZATION + "/v1", (),
            canonical_bytes({"identity": item.id,
                             "pointer": {"repo": repo, "path": item.pointer.path, "commit": item.pointer.commit},
                             "attempt_id": entry["attempt_id"], "assessment_ref": entry["raw_ref"],
                             "contract_digest": contract.content_digest, "baseline": baseline,
                             "approver": contract.authority_issuer, "quote": quote}).decode(),
            None, WORK_AUTHORIZATION, WORK_AUTHORIZATION)
        reference = record_ref(evidence)
        authorization = ReleaseAuthorization(item.id, reference.revision_digest, True, baseline, quote)
        # The release gate's own check, with the resolver and release point it is composed with, over the wording it
        # checks at launch: this contract and the readiness evidence the READY view puts on the row (`readiness` is
        # the assessment's logical id). Registry rows' metadata holds only system values, so none is passed here.
        wording = release_wording(contract, item.assessment_ref.logical_id, {})
        try:
            admit_release_preconditions(item.id, authorization, BaselineEvidence(release_point, resolves, reachable),
                                        wording)
        except ReleasePreconditionRefused as refused:
            return AuthorizationResult(item.id, GATE_WOULD_REFUSE, detail=refused.check)
        existing = self.releases.release_authorization(item.id)
        if existing is not None and existing != authorization:
            return AuthorizationResult(item.id, ALREADY_AUTHORIZED, authorization=asdict(existing))
        if existing is None:
            if self.evidence.put(evidence) != reference:
                raise RuntimeError("the evidence repository answered another reference")
            try:
                self.releases.record(authorization)
            except VersionConflict:  # Another run recorded first: a repeat only if its record equals this one.
                existing = self.releases.release_authorization(item.id)
                if existing is None:
                    raise RuntimeError("the release record conflicted but did not read back") from None
                if existing != authorization:
                    return AuthorizationResult(item.id, ALREADY_AUTHORIZED, authorization=asdict(existing))
            else:
                if self.releases.release_authorization(item.id) != authorization:
                    raise RuntimeError("the release record did not read back as written")
        if item.approval_ref != reference:
            self.identities.set_evidence(item.id, "approval", reference)
        return AuthorizationResult(item.id, None, asdict(reference), asdict(authorization), existing is not None)

    def _stale(self, item: WorkItem, commit: str, attempt: str) -> tuple[str, dict | None]:
        """Which approved value is no longer the item's current one (empty when all still are), and the attempt."""
        if commit != item.pointer.commit:
            return "--commit is not the pointer commit", None
        history = self.consumer.history(item.id)  # The assessment store's own order: the last is the latest.
        entry = next((a for a in history if a["attempt_id"] == attempt), None)
        if entry is None or item.assessment_ref is None or entry["raw_ref"] != asdict(item.assessment_ref):
            return "--attempt is not the item's assessment", entry
        if history[-1]["attempt_id"] != attempt:
            return "--attempt is not the latest attempt", entry
        outcome = entry["outcome"] or {}
        if outcome.get("failure_class") or outcome.get("disposition") != "READY":
            return "--attempt is not READY", entry
        if entry["input_fingerprint"] != fingerprint(item.id, item.pointer):
            return "--attempt is not of the current pointer", entry
        return "", entry
