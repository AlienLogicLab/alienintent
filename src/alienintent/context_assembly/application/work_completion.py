"""WorkCompletion: record, for an existing registered work item, its actual approval, accepted candidate, verification
and verified landing on the default branch (`work record-completed`).

The command records completed work; it does not judge it. Only after every check below has passed against Git and the
given files does it move the existing row straight to DONE, the same "historical record, no invented step" rule
`work import` follows, applied to a row that already exists: no transition, no other row, no coordinator record.
Checks, in this order, each only reading and each refusal writing nothing: the row and its contract block; the
registry coordinator has no record for the item (any record, at any stage, is COORDINATOR_OWNED: the coordinator's
`close` is then the one completion path); the landing (full SHAs, on the default branch, the
candidate an ancestor, the landing record naming the identity, the candidate and the sha256 of the instructions at
the row's pointer); an ACCEPT verification naming the candidate and the identity; the approval file's `item` and
`commit` and the Founder's words. Then the evidence record's reference is computed and the row read: a row at DONE
is a repeat (same reference) or COMPLETION_CONFLICT, and either writes nothing. Writes, in this order: the one
fixed, content-addressed evidence record (read back), then the row (the commit point, guarded by the checked
pointer commit). Nothing here writes to GitHub, the coordinator or the release record.

`record_coordinated` is the row's projection of a coordinator-closed work item (the coordinator's DONE with all five
exact closure receipts): the same landing check (`landing_check`, shared with the landing control plane) on the
journaled order's record commit against the fetched default branch, then the same `work-completion` record kind,
definition and logical id, holding only facts that never change after DONE, and the same row write.
"""
from __future__ import annotations

from base64 import b64encode
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re

from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.work_contract import CONTRACT_INVALID, ContractInvalid, contract_block
from alienintent.context_assembly.domain.work_identity import DONE, GitReadFailed, StoredPointer
from alienintent.context_assembly.ports.work_item_repository import (
    COMPLETION_CONFLICT, NOT_RECORDABLE, CompletionRefused)
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.release_admission import ReleaseAuthorizationRecords, RevisionResolver

CONFLICTING_RECORDS, LANDING_UNVERIFIED = "CONFLICTING_RECORDS", "LANDING_UNVERIFIED"
VERIFICATION_MISSING, APPROVAL_MISSING = "VERIFICATION_MISSING", "APPROVAL_MISSING"
COORDINATOR_OWNED, COORDINATOR_INCOMPLETE = "COORDINATOR_OWNED", "COORDINATOR_INCOMPLETE"
# The evidence record's fixed values, the way `work authorize` fixes its own: the same inputs give the same reference.
WORK_COMPLETION = "work-completion"
COMMIT = re.compile(r"[0-9a-f]{40}")
SCOPE = frozenset({"private"})


@dataclass(frozen=True)
class CompletionResult:
    """What `work record-completed` answers. `answer` is None when the completion is recorded (`repeated` when it
    already was); otherwise it is the refusal code and `detail` names which check refused."""
    identity: str
    answer: str | None = None
    evidence_ref: dict | None = None
    repeated: bool = False
    detail: str = ""


class WorkCompletion:
    def __init__(self, records: WorkRecordService, identities: WorkIdentityService, evidence: EvidenceRepository,
                 project: str, profile: str, revisions: RevisionResolver, release_points: Mapping[str, str],
                 read_packet: Callable[[StoredPointer], bytes],
                 coordinator_record: Callable[[str], Mapping[str, object]], *,
                 releases: ReleaseAuthorizationRecords | None = None,
                 fetch: Callable[[str], str] | None = None) -> None:
        """`project` and `profile` are the evidence repository's; `release_points` maps each configured repository to
        its default branch; `read_packet` is the repository adapter's `git show <commit>:<path>`;
        `coordinator_record` reads the registry coordinator's `factory:<id>` record (empty when it has none);
        `releases` reads `work authorize`'s release records and `fetch` runs `git fetch <remote> <default branch>` in
        the repository's clone, answering the remote-tracking ref (both used only by `record_coordinated`)."""
        self.releases, self.fetch = releases, fetch
        self.records, self.identities, self.evidence = records, identities, evidence
        self.revisions, self.release_points = revisions, dict(release_points)
        self.read_packet, self.coordinator_record = read_packet, coordinator_record
        self.definition = Ref(project, profile, WORK_COMPLETION + "/definition",
                              "sha256:" + sha256(b"alienintent.context_assembly.application.work_completion:"
                                                 b"work-completion").hexdigest(),
                              "python:alienintent.context_assembly.application.work_completion")

    def record(self, id_or_label: str, candidate: str, landing: str, record_path: str,
               verifications: Sequence[tuple[str, bytes]], approval: tuple[str, bytes], quote: str) -> CompletionResult:
        """Each given file is (its resolved absolute path, its exact bytes), read by the CLI."""
        # 1. The row and its contract block.
        record = self.records.show(id_or_label)
        if record is None:
            return CompletionResult(id_or_label, NOT_RECORDABLE, detail="no work item")
        item = record.item
        if item.retired or item.pointer is None:
            return CompletionResult(item.id, NOT_RECORDABLE, detail="retired" if item.retired else "no packet pointer")
        try:
            contract = contract_block(record.packet, item.id)
        except ContractInvalid as error:
            return CompletionResult(item.id, CONTRACT_INVALID, detail=str(error))
        # 2. The registry coordinator has no record for the item: a coordinated item completes only through `close`.
        coordinated = self.coordinator_record(item.id)
        if coordinated:
            return CompletionResult(item.id, COORDINATOR_OWNED,
                                    detail=f"coordinator stage {coordinated.get('stage')}")
        # 3. Verified landing.
        repo, pointer = item.pointer.repo, item.pointer
        branch = self.release_points.get(repo)
        landed = self._landing(repo, branch, candidate, landing, record_path, item.id, record.packet)
        if isinstance(landed, str):
            return CompletionResult(item.id, LANDING_UNVERIFIED, detail=landed)
        # 4. Verification: at least one ACCEPT naming the candidate and the identity.
        if not any(data.split(b"\n", 1)[0] == b"ACCEPT" and candidate.encode() in data and item.id.encode() in data
                   for _, data in verifications):
            return CompletionResult(item.id, VERIFICATION_MISSING, detail="no ACCEPT naming the candidate and item")
        # 5. Approval: bound to the identity and the row's pointer commit; the Founder's words for this recording.
        missing = _approval(approval[1], item.id, pointer.commit) or ("" if quote.strip() else "quote")
        if missing:
            return CompletionResult(item.id, APPROVAL_MISSING, detail=missing)
        evidence = Observation(
            Header(self.definition.project, self.definition.profile, f"{WORK_COMPLETION}/{item.id}", "1",
                   (self.definition,)),
            self.definition, WORK_COMPLETION, WORK_COMPLETION + "/v1", (),
            canonical_bytes({"identity": item.id,
                             "pointer": {"repo": repo, "path": pointer.path, "commit": pointer.commit},
                             "contract_digest": contract.content_digest, "candidate": candidate,
                             "landing": {"commit": landing, "default_branch": branch,
                                         "record": _file(record_path, landed)},
                             "verifications": [_file(*given) for given in verifications],
                             "approval": _file(*approval),
                             "approver": contract.authority_issuer, "quote": quote}).decode(),
            None, WORK_COMPLETION, WORK_COMPLETION)
        reference = record_ref(evidence)
        # The reference is computed and the row read before any write: a repeat or a conflict writes nothing.
        current = self.identities.find(item.id)
        if current.state == DONE:
            if current.verification_ref == reference:
                return CompletionResult(item.id, None, asdict(reference), True)
            return CompletionResult(item.id, COMPLETION_CONFLICT, detail="DONE with other evidence")
        if self.evidence.put(evidence) != reference or record_ref(self.evidence.get(reference, SCOPE)) != reference:
            raise RuntimeError("the evidence record did not read back as written")
        try:  # The commit point: the row, guarded by the checked pointer commit, in one write transaction.
            _, written = self.identities.record_completed(item.id, pointer.commit, reference)
        except CompletionRefused as refused:
            return CompletionResult(item.id, refused.code, detail=refused.detail)
        return CompletionResult(item.id, None, asdict(reference), not written)

    def _landing(self, repo: str, branch: str | None, candidate: str, landing: str, path: str, identity: str,
                 instructions: bytes) -> bytes | str:
        """The landing record's bytes, or which landing check refused."""
        return landing_check(self.revisions, self.read_packet, repo, branch, candidate, landing, path, identity,
                             instructions)

    def record_coordinated(self, identity: str, order: Mapping[str, object] | None) -> CompletionResult:
        """Project a coordinator-closed work item's row to DONE (0.8); `order` is its last journaled `closure-ordered`
        event for the custodied candidate. A repeat with the same reference writes nothing."""
        record = self.records.show(identity)
        if record is None:
            return CompletionResult(identity, NOT_RECORDABLE, detail="no work item")
        item = record.item
        if item.retired or item.pointer is None:
            return CompletionResult(item.id, NOT_RECORDABLE, detail="retired" if item.retired else "no packet pointer")
        try:
            contract = contract_block(record.packet, item.id)
        except ContractInvalid as error:
            return CompletionResult(item.id, CONTRACT_INVALID, detail=str(error))
        coordinated = self.coordinator_record(item.id) or {}
        held = coordinated.get("candidate")
        candidate = str(held.get("locator", "")).rpartition("@")[2] if isinstance(held, Mapping) else ""
        receipts = sorted(str(text) for text in coordinated.get("receipts", ()) or ())
        # The exact receipt of each of the contract's closure actions (`<action>:<identity>:<candidate>`, the
        # coordinator's fixed-name rule; only those contracts reach DONE with exact receipts).
        exact = {f"{action}:{item.id}:{candidate}" for action in contract.required_closure_actions}
        if coordinated.get("stage") != LifecycleStage.DONE.value or COMMIT.fullmatch(candidate) is None \
                or len(exact) != 5 or not exact <= set(receipts):
            return CompletionResult(item.id, COORDINATOR_INCOMPLETE, detail="not DONE with the five exact receipts")
        facts = order.get("order") if isinstance(order, Mapping) else None
        if not isinstance(facts, Mapping) or order.get("candidate") != candidate or self.fetch is None:
            return CompletionResult(item.id, LANDING_UNVERIFIED, detail="no journaled landing order")
        repo, pointer = item.pointer.repo, item.pointer
        branch = self.release_points.get(repo)
        try:
            tracking = self.fetch(repo)
        except Exception as error:  # noqa: BLE001 - an unreadable remote projects nothing now; a later launch retries
            return CompletionResult(item.id, LANDING_UNVERIFIED, detail=f"fetch: {type(error).__name__}")
        landing, path = str(facts.get("record")), str(facts.get("record_path"))
        landed = landing_check(self.revisions, self.read_packet, repo, tracking, candidate, landing, path, item.id,
                               record.packet)
        if isinstance(landed, str):
            return CompletionResult(item.id, LANDING_UNVERIFIED, detail=landed)
        release = self.releases.release_authorization(item.id) if self.releases is not None else None
        verdict = coordinated.get("verdict")
        evidence = Observation(
            Header(self.definition.project, self.definition.profile, f"{WORK_COMPLETION}/{item.id}", "1",
                   (self.definition,)),
            self.definition, WORK_COMPLETION, WORK_COMPLETION + "/v1", (),
            canonical_bytes({"identity": item.id, "source": "coordinator",
                             "pointer": {"repo": repo, "path": pointer.path, "commit": pointer.commit},
                             "contract_digest": contract.content_digest, "candidate": candidate,
                             "landing": {"base": facts.get("base"), "merge": facts.get("merge"), "commit": landing,
                                         "default_branch": branch, "record": _file(path, landed)},
                             "coordinator": {"stage": coordinated.get("stage"), "version": coordinated.get("version"),
                                             "receipts": receipts, "verdict": verdict},
                             "release_record": None if release is None else release.record_ref,
                             "approver": contract.authority_issuer}).decode(),
            None, WORK_COMPLETION, WORK_COMPLETION)
        reference = record_ref(evidence)
        current = self.identities.find(item.id)
        if current.state == DONE:
            if current.verification_ref == reference:
                return CompletionResult(item.id, None, asdict(reference), True)
            return CompletionResult(item.id, COMPLETION_CONFLICT, detail="DONE with other evidence")
        if self.evidence.put(evidence) != reference or record_ref(self.evidence.get(reference, SCOPE)) != reference:
            raise RuntimeError("the evidence record did not read back as written")
        try:
            _, written = self.identities.record_completed(item.id, pointer.commit, reference)
        except CompletionRefused as refused:
            return CompletionResult(item.id, refused.code, detail=refused.detail)
        return CompletionResult(item.id, None, asdict(reference), not written)

    def recorded(self, identity: str) -> bool:
        """Dependency admission's reader: the row is not retired, is at DONE, and its `verification_ref` reads back
        as a `work-completion` record of this identity. Any doubt (no row, an unreadable or foreign record) is False."""
        try:
            item = self.identities.find(identity)
            if item is None or item.retired or item.state != DONE or item.verification_ref is None:
                return False
            stored = self.evidence.get(item.verification_ref, SCOPE)
            return (isinstance(stored, Observation) and stored.evidence_id == WORK_COMPLETION
                    and stored.header.logical_id == f"{WORK_COMPLETION}/{item.id}"
                    and json.loads(stored.value).get("identity") == item.id)
        except Exception:  # noqa: BLE001 - a reader that cannot establish completion refuses, never admits
            return False


def landing_check(revisions: RevisionResolver, read: Callable[[StoredPointer], bytes], repo: str,
                  release_point: str | None, candidate: str, landing: str, path: str, identity: str,
                  instructions: bytes) -> bytes | str:
    """The one landing check (`work record-completed`, the coordinator projection and the landing control plane): the
    landing record's bytes, or which check refused."""
    if COMMIT.fullmatch(landing) is None:
        return "landing is not an exact 40-hex commit"
    if release_point is None or not revisions.resolves(repo, landing):
        return f"landing does not resolve in {repo}"
    if not revisions.is_reachable(repo, landing, release_point):
        return f"landing not reachable from {release_point}"
    if COMMIT.fullmatch(candidate) is None:
        return "candidate is not an exact 40-hex commit"
    if not revisions.is_reachable(repo, candidate, landing):
        return "candidate is not an ancestor of the landing"
    try:
        data = read(StoredPointer(repo, path, landing))
    except GitReadFailed:
        return "landing record missing"
    if identity.encode() not in data or candidate.encode() not in data:
        return "landing record does not name the item and the candidate"
    if sha256(instructions).hexdigest().encode() not in data:
        return "instructions"
    return data


def _approval(data: bytes, identity: str, commit: str) -> str:
    """Which approval field refuses (empty when none does)."""
    try:
        document = json.loads(data)
    except ValueError:
        return "not a JSON object"
    if not isinstance(document, dict):
        return "not a JSON object"
    if document.get("item") != identity:
        return "item"
    value = document.get("commit")
    if not isinstance(value, str) or COMMIT.fullmatch(value) is None or value != commit:
        return "commit"
    return ""


def _file(path: str, data: bytes) -> dict[str, str]:
    return {"path": path, "sha256": sha256(data).hexdigest(), "bytes_base64": b64encode(data).decode()}
