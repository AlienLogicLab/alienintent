"""PlanApproval: record the Founder's approval of one exact canonical-plan revision (`work approve-plan`).

The command records the Founder's approval; it does not grant it. It reads the canonical plan at the exact commit
from the packets repository's clone, only when that commit is reachable from the default branch, and parses its one
plan-authority block. One evidence record binds the plan path, the commit, the content digest (`sha256:` of the file's
bytes), the parsed scope, the approver and the Founder's words; the store aggregate `plan-authority:<digest>` (create
only) names that record, so the same bytes approved again are a repeat and write no second record. The aggregate
`plan-authority:current`, written with the store's expected version, names the one current approval: each approval,
a re-approval of an older digest included, makes its digest current. Nothing else is current, so an item issued under
another digest fails the issuer rule and stops as owner-decision-required. Nothing here releases, launches or writes
to GitHub.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re

from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref, \
    ref_from_document
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.plan_authority import (
    PLAN_PATH, PlanAuthority, PlanScopeInvalid, parse_scope, scope_from)
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict
from alienintent.execution_coordination.ports.release_admission import RevisionResolver

# Answers `work approve-plan` returns instead of writing.
PLAN_NOT_ON_MAIN, PLAN_SCOPE_INVALID = "PLAN_NOT_ON_MAIN", "PLAN_SCOPE_INVALID"
PLAN_AUTHORITY, CURRENT = "plan-authority", "plan-authority:current"
APPROVER = "Founder"
COMMIT = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class PlanApprovalResult:
    """What `work approve-plan` answers. `answer` is None when the approval is recorded and current (`repeated` when
    these bytes were already approved); otherwise it is the refusal code and `detail` names which check refused."""
    commit: str
    answer: str | None = None
    content_digest: str | None = None
    evidence_ref: dict | None = None
    repeated: bool = False
    detail: str = ""


class PlanApproval:
    def __init__(self, evidence: EvidenceRepository, project: str, profile: str, store: OperationalStore,
                 store_profile: str, repository: str, revisions: RevisionResolver, release_point: str,
                 read: Callable[[str], bytes]) -> None:
        """`read(commit)` answers the plan file's bytes at `commit` from the packets repository's clone;
        `repository` and `release_point` are that clone's name and default branch."""
        self.evidence, self.store, self.store_profile = evidence, store, store_profile
        self.repository, self.revisions, self.release_point, self.read = repository, revisions, release_point, read
        self.definition = Ref(project, profile, PLAN_AUTHORITY + "/definition",
                              "sha256:" + sha256(b"alienintent.context_assembly.application.plan_approval:"
                                                 b"plan-authority").hexdigest(),
                              "python:alienintent.context_assembly.application.plan_approval")

    def approve(self, commit: str, quote: str) -> PlanApprovalResult:
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError("the Founder's exact words are required")
        if COMMIT.fullmatch(commit or "") is None or not self.revisions.resolves(self.repository, commit) \
                or not self.revisions.is_reachable(self.repository, commit, self.release_point):
            return PlanApprovalResult(commit, PLAN_NOT_ON_MAIN, detail=f"not reachable from {self.release_point}")
        try:
            data = self.read(commit)
            scope = parse_scope(data.decode("utf-8"))
        except PlanScopeInvalid as error:
            return PlanApprovalResult(commit, PLAN_SCOPE_INVALID, detail=str(error))
        except Exception as error:  # noqa: BLE001 - a plan that cannot be read at the commit has no block to approve
            return PlanApprovalResult(commit, PLAN_SCOPE_INVALID, detail=f"{type(error).__name__}: {error}")
        digest = "sha256:" + sha256(data).hexdigest()
        evidence = Observation(
            Header(self.definition.project, self.definition.profile, f"{PLAN_AUTHORITY}/{digest}", "1",
                   (self.definition,)),
            self.definition, PLAN_AUTHORITY, PLAN_AUTHORITY + "/v1", (),
            canonical_bytes({"plan_path": PLAN_PATH, "commit": commit, "content_digest": digest,
                             "scope": scope.document(), "approver": APPROVER, "quote": quote}).decode(),
            None, PLAN_AUTHORITY, PLAN_AUTHORITY)
        aggregate = f"{PLAN_AUTHORITY}:{digest}"
        _, existing = self.store.read_state(self.store_profile, aggregate)
        if not existing:
            reference = record_ref(evidence)
            if self.evidence.put(evidence) != reference:
                raise RuntimeError("the evidence repository answered another reference")
            try:
                self.store.commit(self.store_profile, aggregate, 0,
                                  {"content_digest": digest, "record_ref": asdict(reference)})
            except VersionConflict:  # Another run approved the same bytes first: its record stands.
                pass
            _, recorded = self.store.read_state(self.store_profile, aggregate)
        else:
            recorded = existing
        if recorded.get("content_digest") != digest:
            raise RuntimeError("the plan authority record did not read back as written")
        version, current = self.store.read_state(self.store_profile, CURRENT)
        if current.get("content_digest") != digest:
            self.store.commit(self.store_profile, CURRENT, version, dict(recorded))
        return PlanApprovalResult(commit, None, digest, dict(recorded["record_ref"]), bool(existing))

    def current(self) -> PlanAuthority | None:
        """The current approved plan authority, rebuilt from its evidence record; None when none is current or its
        record cannot be read back exactly (no authority is inherited from an unreadable record)."""
        _, current = self.store.read_state(self.store_profile, CURRENT)
        if not current:
            return None
        try:
            reference = ref_from_document(current["record_ref"])
            values = json.loads(self.evidence.get(reference, frozenset({"private"})).value)
            if values["content_digest"] != current["content_digest"]:
                return None
            return PlanAuthority(values["plan_path"], values["commit"], values["content_digest"],
                                 reference.revision_digest, values["approver"], values["quote"],
                                 scope_from(values["scope"]))
        except Exception:  # noqa: BLE001 - an unreadable record is no authority
            return None
