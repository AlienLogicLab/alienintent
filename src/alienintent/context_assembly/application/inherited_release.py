"""InheritedRelease: the control plane's release of a plan-derived work item (`work release`, no quote).

A work item inherits execution authority from the live plan authority (the canonical plan at the tip of main,
PLAN-TIP-AUTHORITY-RUNTIME-FIX) only when it is at CAPTURE with a
pointer and no release record, its retained assessment of that pointer is READY, its contract is `automatic-on`, and
the composed satisfiability check with that authority gives no reasons. Otherwise it answers the named refusal and
writes nothing; OWNER_DECISION_REQUIRED also ensures the one durable owner-decision attention item (`owner_decision`).
Then, as `work authorize` does (its file is not changed): the evidence record with the same fields (approver the
contract's `authority_issuer`, quote the live plan's reference, and `plan`: the exact tip commit and content digest
it is released under and the digest it was prepared from; an item prepared from an older revision has been
revalidated against the tip by the satisfiability check and its release text says so), the release record (the commit
point: create only, read back, its baseline the default branch's current head) and the row's `approval_ref`. Then
the card: linked if the item has none (`work link`), its text written (`work display`), Status READY and Priority
the obligation's written and each read back. A rerun after an unconfirmed card writes only the card.
The release precondition gate is unchanged and re-checks the record before every PRODUCER.

Current canonical main is fetched once (`head`) and the plan authority is read at exactly that commit
(WORK-PREPARATION-REFILL R2). When it cannot be fetched the answer is CANONICAL_MAIN_UNAVAILABLE: typed infrastructure,
retried by the caller, nothing written and never an owner decision ("Infrastructure failure is not an owner decision",
Founder decisions section 44); no last-known tip ever grants a release.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Protocol

from alienintent.context_assembly.application.work_authorization import ReleaseRecords
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import fingerprint
from alienintent.context_assembly.domain.work_contract import CONTRACT_INVALID, ContractInvalid, contract_block
from alienintent.context_assembly.domain.work_identity import CAPTURE
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.plan_authority import PlanAuthority, obligation_labels
from alienintent.execution_coordination.domain.release import (
    BaselineEvidence, ReleaseAuthorization, ReleasePreconditionRefused, admit_release_preconditions, release_wording)
from alienintent.execution_coordination.ports.operational_store import VersionConflict
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer
from alienintent.execution_coordination.ports.release_admission import RevisionResolver

# Answers `work release` returns instead of writing (CARD_UNCONFIRMED after the release record is written).
NOT_RELEASABLE, ASSESSMENT_MISSING, NOT_PLAN_DERIVED = "NOT_RELEASABLE", "ASSESSMENT_MISSING", "NOT_PLAN_DERIVED"
OWNER_DECISION_REQUIRED, GATE_WOULD_REFUSE, CARD_UNCONFIRMED = \
    "OWNER_DECISION_REQUIRED", "GATE_WOULD_REFUSE", "CARD_UNCONFIRMED"
# Current canonical main could not be fetched: retry; nothing was written and no owner decision was raised.
CANONICAL_MAIN_UNAVAILABLE = "CANONICAL_MAIN_UNAVAILABLE"
INHERITED_RELEASE = "inherited-release"
INHERITED = "inherited from plan authority"


class Board(Protocol):
    def write_status(self, item_id: str, status: str, expected_revision: int) -> int: ...

    def write_priority(self, item_id: str, priority: str, expected_revision: int) -> int: ...


class Links(Protocol):
    """`work link` and `work display`, and the board they write (bound by composition)."""
    board: Board

    def link(self, id_or_label: str, issue: int | None = None): ...

    def display(self, id_or_label: str): ...


@dataclass(frozen=True)
class ReleaseResult:
    """What `work release` answers. `answer` is None when the item is released and its card reads back READY with its
    priority (`repeated` when the release record already was this release); otherwise the refusal code and `detail`."""
    identity: str
    answer: str | None = None
    evidence_ref: dict | None = None
    authorization: dict | None = None
    card_id: str | None = None
    priority: str | None = None
    repeated: bool = False
    detail: str = ""


class InheritedRelease:
    def __init__(self, records: WorkRecordService, identities: WorkIdentityService, consumer: AssessmentConsumer,
                 evidence: EvidenceRepository, project: str, profile: str, releases: ReleaseRecords,
                 revisions: RevisionResolver, release_points: Mapping[str, str], head: Callable[[str], str | None],
                 authority: Callable[[str], PlanAuthority | None],
                 satisfiable: Callable[[bytes, str, str, PlanAuthority], tuple[str, ...]], owner_decision: Callable[[str], None],
                 links: Links) -> None:
        """`head(repository)` answers current canonical main, fetched now, or None when it cannot be fetched;
        `authority(commit)` the plan authority at that commit; `satisfiable` the composed check with it;
        `owner_decision(identity)` ensures the
        item's owner-decision attention item."""
        self.records, self.identities, self.consumer, self.evidence = records, identities, consumer, evidence
        self.releases, self.revisions, self.release_points, self.head = releases, revisions, dict(release_points), head
        self.authority, self.satisfiable = authority, satisfiable
        self.owner_decision, self.links = owner_decision, links
        self.definition = Ref(project, profile, INHERITED_RELEASE + "/definition",
                              "sha256:" + sha256(b"alienintent.context_assembly.application.inherited_release:"
                                                 b"inherited-release").hexdigest(),
                              "python:alienintent.context_assembly.application.inherited_release")

    def release(self, id_or_label: str) -> ReleaseResult:
        record = self.records.show(id_or_label)
        item = None if record is None else record.item
        if item is None or item.retired or item.state != CAPTURE or item.pointer is None:
            return ReleaseResult(id_or_label if item is None else item.id, NOT_RELEASABLE, detail=(
                "no work item" if item is None else "retired" if item.retired else f"state {item.state}"
                if item.state != CAPTURE else "no packet pointer"))
        existing = self.releases.release_authorization(item.id)
        if existing is not None and not (existing.text.startswith(INHERITED) and item.approval_ref is not None
                                         and existing.record_ref == item.approval_ref.revision_digest):
            return ReleaseResult(item.id, NOT_RELEASABLE, detail="a release record exists")
        history = self.consumer.history(item.id)
        entry = next((a for a in history if item.assessment_ref is not None
                      and a["raw_ref"] == asdict(item.assessment_ref)), None)
        outcome = (entry or {}).get("outcome") or {}
        if entry is None or entry["input_fingerprint"] != fingerprint(item.id, item.pointer) \
                or outcome.get("failure_class") or outcome.get("disposition") != "READY":
            return ReleaseResult(item.id, ASSESSMENT_MISSING, detail="no READY assessment of the current pointer")
        try:
            contract = contract_block(record.packet, item.id)
        except ContractInvalid as error:
            return ReleaseResult(item.id, CONTRACT_INVALID, detail=str(error))
        if contract.release_policy != "automatic-on":
            return ReleaseResult(item.id, NOT_PLAN_DERIVED, detail=f"release_policy {contract.release_policy}")
        repo = item.pointer.repo
        baseline = self.head(repo)  # current canonical main, fetched once: the authority and the baseline
        if baseline is None:
            return ReleaseResult(item.id, CANONICAL_MAIN_UNAVAILABLE,
                                 detail="current canonical main could not be fetched; retry")
        authority = self.authority(baseline)
        reasons = ("no readable plan authority at the tip of main",) if authority is None \
            else self.satisfiable(record.packet, item.pointer.commit, item.id, authority)  # checked against this read
        if reasons:
            self.owner_decision(item.id)
            return ReleaseResult(item.id, OWNER_DECISION_REQUIRED, detail="; ".join(reasons))
        priority = authority.scope.obligation(obligation_labels(contract)[0]).priority
        if existing is not None:  # This release was recorded; only its card was unconfirmed.
            return self._card(item.id, priority, ReleaseResult(item.id, None, asdict(item.approval_ref),
                                                               asdict(existing), repeated=True))
        prepared = contract.authority_issuer.removeprefix("plan-authority:")  # the revision it was prepared from
        release_point = self.release_points.get(repo)
        resolves = release_point is not None and self.revisions.resolves(repo, baseline)
        reachable = resolves and self.revisions.is_reachable(repo, baseline, release_point)
        evidence = Observation(
            Header(self.definition.project, self.definition.profile, f"{INHERITED_RELEASE}/{item.id}", "1",
                   (self.definition,)),
            self.definition, INHERITED_RELEASE, INHERITED_RELEASE + "/v1", (),
            canonical_bytes({"identity": item.id,
                             "pointer": {"repo": repo, "path": item.pointer.path, "commit": item.pointer.commit},
                             "attempt_id": entry["attempt_id"], "assessment_ref": entry["raw_ref"],
                             "contract_digest": contract.content_digest, "baseline": baseline,
                             "approver": contract.authority_issuer, "quote": authority.record_ref,
                             "plan": {"commit": authority.commit, "content_digest": authority.content_digest,
                                      "prepared_from": prepared}}).decode(),
            None, INHERITED_RELEASE, INHERITED_RELEASE)
        reference = record_ref(evidence)
        revalidated = "" if prepared == authority.content_digest else f"; revalidated from {prepared}"
        authorization = ReleaseAuthorization(item.id, reference.revision_digest, True, baseline,
                                             f"{INHERITED} {authority.content_digest} ({authority.record_ref})"
                                             f"{revalidated}")
        try:  # The release gate's own check, over the wording it checks at launch (as `work authorize`).
            admit_release_preconditions(item.id, authorization, BaselineEvidence(str(release_point), resolves,
                                                                                 reachable),
                                        release_wording(contract, item.assessment_ref.logical_id, {}))
        except ReleasePreconditionRefused as refused:
            return ReleaseResult(item.id, GATE_WOULD_REFUSE, detail=refused.check)
        if self.evidence.put(evidence) != reference:
            raise RuntimeError("the evidence repository answered another reference")
        try:
            self.releases.record(authorization)
        except VersionConflict:  # Another run recorded first: nothing of this run is referenced.
            return ReleaseResult(item.id, NOT_RELEASABLE, detail="a release record exists")
        if self.releases.release_authorization(item.id) != authorization:
            raise RuntimeError("the release record did not read back as written")
        self.identities.set_evidence(item.id, "approval", reference)
        return self._card(item.id, priority, ReleaseResult(item.id, None, asdict(reference), asdict(authorization)))

    def _card(self, identity: str, priority: str, released: ReleaseResult) -> ReleaseResult:
        """Link (when unlinked), display, then Status READY and the priority, each read back."""
        try:
            linked = self.links.link(identity)
            shown = self.links.display(identity) if linked.answer is None else linked
            if shown.answer is not None or linked.card_id is None:
                raise RuntimeError(f"{shown.answer}: {shown.detail}")
            card = linked.card_id
            if self.links.board.write_status(card, "READY", 0) != 0 \
                    or self.links.board.write_priority(card, priority, 0) != 0:
                raise RuntimeError("the card did not read back READY with its priority")
        except Exception as error:  # noqa: BLE001 - the release stands; a rerun writes only the card
            return ReleaseResult(identity, CARD_UNCONFIRMED, released.evidence_ref, released.authorization,
                                 priority=priority, detail=f"{type(error).__name__}: {error}")
        return ReleaseResult(identity, None, released.evidence_ref, released.authorization, card, priority,
                             released.repeated)
