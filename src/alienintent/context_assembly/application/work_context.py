"""WorkContext: each role's context package for one registered work item and the exact attempt (unit 6c-1).

`assemble` reads only existing authoritative records — the work item row and its packet at the pointer commit, the
packet's contract block, the READY assessment, the release record and its evidence, the `factory:<identity>` state,
the reservations, the dependencies' rows and the reference paths at the pointer commit and, for the VERIFIER, the
candidate, its diff and the PRODUCER's self-review — and writes nothing. It runs its checks in a fixed order and
returns the first failing one as a `ContextHold` naming the field (`affected_refs`) and the rule (`detail`); then no
package exists, so nothing can be launched. `record_self_review` keeps the PRODUCER's self-review in the existing
evidence repository and one create-only record on the existing store that references it and the exact candidate.
Nothing here launches a worker or writes to the product repository.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

from alienintent.context_assembly.application.work_authorization import ReleaseRecords
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import fingerprint
from alienintent.context_assembly.domain.reconstruction import ContextHold, HoldReason, canonical
from alienintent.context_assembly.domain.work_context import (
    FIELDS, PRODUCER, SELF_REVIEW, SELF_REVIEW_EXISTS, SELF_REVIEW_LABEL, VERIFIER, ContextPackage,
    candidate_document, candidate_revision, content, self_review_aggregate)
from alienintent.context_assembly.domain.work_contract import ContractInvalid, contract_block
from alienintent.context_assembly.domain.work_identity import (
    RegistryBusy, RegistryUnavailable, StoredPointer, WorkIdentityRefused, valid_path)
from alienintent.context_assembly.domain.work_registration import WorkRecord
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref, \
    ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.lifecycle import ExecutionState
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore, SchemaIncompatible, StoreUnavailable, VersionConflict)
from alienintent.execution_coordination.ports.readiness import AssessmentConsumer

MISSING, MALFORMED = HoldReason.MISSING_RECORD, HoldReason.MALFORMED_RECORD
MISMATCH, DRIFT = HoldReason.DIGEST_MISMATCH, HoldReason.VERSION_DRIFT
SCOPE = frozenset({"public", "private"})
# The release record evidence fields carried in the package (WorkAuthorization writes exactly these).
RELEASE_EVIDENCE = ("pointer", "attempt_id", "assessment_ref", "contract_digest", "baseline", "approver", "quote")


class SelfReviewExists(VersionConflict):
    """SELF_REVIEW_EXISTS: another self-review is already recorded for this work item and candidate."""
    code = SELF_REVIEW_EXISTS


@dataclass(frozen=True)
class ContextCommand:
    """The read-only `work context` command line a worker runs for further facts: the installed executable, the
    read-only worker profile and the two environment variables naming the project configuration."""
    executable: str
    profile_factory: str
    environment: Mapping[str, str]

    def document(self, identity: str, role: str, correlation: str, candidate: str | None) -> dict[str, object]:
        argv = [self.executable, "--profile-factory", self.profile_factory, "--json", "work", "context", identity,
                "--role", role, "--correlation", correlation, *(("--candidate", candidate) if candidate else ())]
        return {"argv": argv, "environment": dict(self.environment)}


def _hold(reason: HoldReason, *refs: str, detail: str = "") -> ContextHold:
    return ContextHold(reason, refs, detail)


class WorkContext:
    def __init__(self, records: WorkRecordService, read_file: Callable[[StoredPointer], bytes],
                 consumer: AssessmentConsumer, store: OperationalStore, evidence: EvidenceRepository,
                 releases: ReleaseRecords, decode: Callable[[Mapping[str, object]], ExecutionState],
                 diff: Callable[[Path, str, str], bytes], command: ContextCommand, project: str, profile: str,
                 store_profile: str) -> None:
        """`read_file` is the repository adapter's `git show <commit>:<path>`; `decode` the coordinator's own decoder;
        `diff` runs `git diff <base> <revision>` in a clone; `project` and `profile` are the evidence repository's;
        `store_profile` is the profile of the coordinator state, reservations and release records."""
        self.records, self.read_file, self.consumer, self.store = records, read_file, consumer, store
        self.evidence, self.releases, self.decode, self.diff = evidence, releases, decode, diff
        self.command, self.store_profile = command, store_profile
        self.definition = Ref(project, profile, SELF_REVIEW + "/definition",
                              "sha256:" + sha256(b"alienintent.context_assembly.application.work_context:"
                                                 b"self-review").hexdigest(),
                              "python:alienintent.context_assembly.application.work_context")

    # --- assembly -----------------------------------------------------------------------------------------------

    def assemble(self, identity: str, role: str, correlation: str, contract_digest: str | None,
                 candidate: CandidateRef | str | None = None, clone: Path | None = None) -> ContextPackage | ContextHold:
        """The role's package, or the first failing check as a hold. `contract_digest` is the invocation's (None when
        the caller holds none, as the `work context` command); `candidate` is the VERIFIER's CandidateRef or its
        locator (None: the coordinator state's candidate); `clone` is the VERIFIER's fresh candidate clone."""
        if role not in FIELDS or (role == PRODUCER and candidate is not None) or (role == VERIFIER and clone is None):
            raise ValueError("role PRODUCER or VERIFIER; a candidate and a clone only for the VERIFIER")
        try:
            return self._assemble(identity, role, correlation, contract_digest, candidate, clone)
        except ContextHold as hold:
            return hold

    def _assemble(self, identity: str, role: str, correlation: str, contract_digest: str | None,
                  candidate: CandidateRef | str | None, clone: Path | None) -> ContextPackage:
        # 1. The row and its packet at the pointer commit.
        record = self._show(identity, "work_item")
        item = record.item if record is not None else None
        if item is None or item.retired or item.pointer is None or record.packet is None:
            raise _hold(MISSING, "work_item", detail="no row" if item is None else "retired" if item.retired
                        else "no packet pointer")
        pointer = item.pointer
        # 2. The contract block.
        try:
            contract = contract_block(record.packet, item.id)
        except ContractInvalid as error:
            raise _hold(MALFORMED, "contract", detail=error.which) from None
        # 3. The READY assessment of the current pointer.
        history = self._read("assessment", lambda: self.consumer.history(item.id))
        entry = next((a for a in history if item.assessment_ref is not None
                      and a.get("raw_ref") == asdict(item.assessment_ref)), None)
        outcome = (entry or {}).get("outcome") or {}
        if entry is None or entry.get("input_fingerprint") != fingerprint(item.id, pointer) \
                or outcome.get("failure_class") or outcome.get("disposition") != "READY":
            raise _hold(MISSING, "assessment", detail="no READY assessment of the current pointer")
        # 4. The release record and its evidence.
        release = self._read("release_record", lambda: self.releases.release_authorization(item.id))
        if release is None or item.approval_ref is None:
            raise _hold(MISSING, "release_record", detail="no release record" if release is None else
                        "no approval_ref")
        approval = self._evidence(item.approval_ref, "release_record")
        evidence_pointer = approval.get("pointer")
        for field, actual, expected in (
                ("record_ref", item.approval_ref.revision_digest, release.record_ref),
                ("pointer", evidence_pointer.get("commit") if isinstance(evidence_pointer, dict) else None,
                 pointer.commit),
                ("attempt_id", approval.get("attempt_id"), entry["attempt_id"]),
                ("contract_digest", approval.get("contract_digest"), contract.content_digest)):
            if actual != expected:
                raise _hold(MISMATCH, "release_record", field, detail=f"the release evidence {field} differs")
        if not release.baseline:
            raise _hold(MISSING, "starting_revision", detail="the release record has no baseline")
        # 5. The invocation's contract digest and the exact attempt.
        if contract_digest is not None and contract_digest != contract.content_digest:
            raise _hold(MISMATCH, "contract_digest", detail="the invocation's contract digest is not the contract's")
        version, raw = self._read("history", lambda: self.store.read_state(self.store_profile, f"factory:{item.id}"))
        attempt = self._attempt(item.id, correlation, version)
        try:
            state = self.decode(raw) if raw else None
            rejections, findings = raw.get("rejections", 0), raw.get("findings", [])
            if type(rejections) is not int or not isinstance(findings, list):
                raise TypeError("rejections or findings")
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise _hold(MALFORMED, "history", detail=f"undecodable coordinator state: {error}") from None
        # 6. The reservations this attempt owns.
        reservations = self._read("resources", lambda: self.store.recovery_reservations(self.store_profile))
        wip = next((r for r in reservations if (r.scope, r.key, r.owner) == ("wip", item.id, f"work:{item.id}")),
                   None)
        repository = next((r for r in reservations if (r.scope, r.owner) == ("repository", correlation)), None)
        if wip is None or repository is None:
            raise _hold(MISSING, "resources", "wip" if wip is None else "repository",
                        detail="no reservation held for this attempt")
        # 7. Dependencies and design references, resolved.
        dependencies = [self._dependency(dependency) for dependency in contract.dependencies]
        references = [self._reference(pointer, reference) for reference in contract.authority_references]
        fields: dict[str, object] = {
            "identity": item.id, "label": item.label, "role": role,
            "attempt": attempt,
            "goal": contract.intent,
            "instructions": {"repository": pointer.repo, "path": pointer.path, "commit": pointer.commit,
                             **content(record.packet)},
            "contract": {"block": contract.canonical_payload(), "content_digest": contract.content_digest},
            "release_record": {**asdict(release), "evidence_ref": asdict(item.approval_ref),
                               "evidence": {name: approval.get(name) for name in RELEASE_EVIDENCE}},
            "starting_revision": release.baseline,
            "allowed_scope": {"authorized_scope": contract.authorized_scope,
                              "excluded_scope": contract.excluded_scope},
            "required_evidence": {"verification_obligations": contract.verification_obligations,
                                  "required_evidence": contract.required_evidence,
                                  "completion_criteria": contract.completion_criteria},
            "stop_condition": {"completion_criteria": contract.completion_criteria,
                               "maximum_attempts": contract.budget_policy.maximum_attempts},
            "escalation_condition": contract.stop_escalation_conditions,
            "dependencies": dependencies,
            "design_rules": {"fixed_decisions": contract.fixed_decisions, "authority_references": references},
            "history": {"stage": None if state is None else str(state.stage),
                        "version": None if state is None else state.version,
                        "implement_cycles": 0 if state is None else state.implement_cycles,
                        "verify_cycles": 0 if state is None else state.verify_cycles,
                        "rejections": rejections, "findings": findings},
            "resources": {"wip": asdict(wip), "repository": asdict(repository),
                          "cleanup": {"required_closure_actions": contract.required_closure_actions,
                                      "candidate_custody_requirements": contract.candidate_custody_requirements}},
        }
        if role == PRODUCER:
            fields["assessment"] = {"assessment_ref": asdict(item.assessment_ref), "attempt_id": entry["attempt_id"],
                                    "input_fingerprint": entry["input_fingerprint"]}
            fields["context_command"] = self.command.document(item.id, role, correlation, None)
        else:
            # 8. The exact candidate, its self-review and its diff.
            held = state.candidate if state is not None else None
            if held is None:
                raise _hold(MISSING, "candidate", detail="no candidate in the coordinator state")
            if candidate is not None and (candidate != held if isinstance(candidate, CandidateRef)
                                          else candidate != held.locator):
                raise _hold(MISMATCH, "candidate", detail="the candidate is not the coordinator state's candidate")
            fields["candidate"] = candidate_document(held)
            fields["producer_self_review"] = {"label": SELF_REVIEW_LABEL, **self._self_review(item.id, held)}
            revision = candidate_revision(held)
            if revision is None:
                raise _hold(MISSING, "diff", detail="the candidate is not a source revision git:<remote>#<branch>@<sha>")
            try:
                diff = self.diff(clone, release.baseline, revision)
            except WorkIdentityRefused as error:
                raise _hold(MISSING, "diff", detail=str(error)) from None
            fields["diff"] = {"base": release.baseline, "revision": revision, **content(diff)}
            fields["context_command"] = self.command.document(item.id, role, correlation, held.locator)
        return ContextPackage(role, json.loads(canonical(fields)))

    def _attempt(self, identity: str, correlation: str, version: int) -> int:
        """Step 5's attempt check: `launch:<identity>:<v>` is current when it names this work item and either the
        store version of `factory:<identity>` is v (the launch is not yet saved) or it is v + 1 and the store's effect
        record for exactly this correlation is `pending` or `unknown` (the coordinator saved this launch and its
        worker has not reported). The attempt is v; anything else is VERSION_DRIFT."""
        prefix, _, number = correlation.rpartition(":")
        attempt = int(number) if prefix == f"launch:{identity}" and re.fullmatch(r"0|[1-9][0-9]*", number) else None
        if attempt is not None and version == attempt:
            return attempt
        if attempt is not None and version == attempt + 1:
            ledger = self._read("attempt", lambda: self.store.effect_ledger(  # type: ignore[attr-defined]
                self.store_profile))
            if any(effect == correlation and status in ("pending", "unknown") for effect, status, _ in ledger):
                return attempt
        raise _hold(DRIFT, "attempt", detail=f"{correlation} is not a current launch of factory:{identity} "
                                             f"(store version {version})")

    def _show(self, identity: str, field: str) -> WorkRecord | None:
        try:
            return self.records.show(identity)
        except (RegistryUnavailable, RegistryBusy) as error:
            raise _hold(HoldReason.STORE_UNAVAILABLE, field, detail=str(error)) from None
        except WorkIdentityRefused as error:  # The packet at the pointer commit cannot be read.
            raise _hold(MISSING, field, identity, detail=f"packet unreadable at the pointer: {error}") from None

    def _read(self, field: str, call: Callable[[], object]):
        try:
            return call()
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise _hold(HoldReason.STORE_UNAVAILABLE, field, detail=str(error)) from None

    def _evidence(self, ref: Ref, field: str) -> dict:
        """The JSON content of the evidence record at `ref`: a missing object is a missing record, any other failure
        to read it is EVIDENCE_UNAVAILABLE."""
        try:
            values = json.loads(self.evidence.get(ref, SCOPE).value)
        except EvidenceHold as error:
            reason = MISSING if error.reason_code == "MISSING_OBJECT" else HoldReason.EVIDENCE_UNAVAILABLE
            raise _hold(reason, field, detail=f"evidence {error.reason_code}") from None
        except (StoreUnavailable, AttributeError, TypeError, ValueError) as error:
            raise _hold(HoldReason.EVIDENCE_UNAVAILABLE, field, detail=type(error).__name__) from None
        if not isinstance(values, dict):
            raise _hold(HoldReason.EVIDENCE_UNAVAILABLE, field, detail="evidence content is not an object")
        return values

    def _dependency(self, identity: str) -> dict[str, object]:
        record = self._show(identity, "dependencies")
        if record is None:
            raise _hold(MISSING, "dependencies", identity, detail="the dependency is not registered")
        item = record.item
        _, raw = self._read("dependencies", lambda: self.store.read_state(self.store_profile, f"factory:{item.id}"))
        return {"identity": item.id, "label": item.label, "state": item.state, "retired": item.retired,
                "pointer": None if item.pointer is None else asdict(item.pointer),
                "packet": None if record.packet is None else content(record.packet),
                "stage": raw.get("stage"), "outcome": raw.get("outcome")}

    def _reference(self, pointer: StoredPointer, reference: str) -> dict[str, object]:
        path = (reference.split() or [""])[0]
        try:
            data = self.read_file(StoredPointer(pointer.repo, path, pointer.commit)) if valid_path(path) else None
        except WorkIdentityRefused:  # `git show` failed: the path is not present at the pointer commit.
            data = None
        if data is None:
            raise _hold(MISSING, "design_rules", reference, detail="not a path present at the pointer commit")
        return {"reference": reference, "repository": pointer.repo, "path": path, "commit": pointer.commit,
                **content(data)}

    def _self_review(self, identity: str, candidate: CandidateRef) -> dict[str, object]:
        _, stored = self._read("producer_self_review", lambda: self.store.read_state(
            self.store_profile, self_review_aggregate(identity, candidate)))
        if not stored or stored.get("candidate") != candidate_document(candidate):
            raise _hold(MISSING, "producer_self_review", detail="no self-review record for this candidate")
        try:
            reference = ref_from_document(stored.get("evidence_ref"))
        except EvidenceHold:
            raise _hold(MALFORMED, "producer_self_review", detail="the record holds no evidence reference") from None
        values = self._evidence(reference, "producer_self_review")
        return {"evidence_ref": asdict(reference), "text": values.get("text")}

    # --- the PRODUCER's self-review -------------------------------------------------------------------------------

    def record_self_review(self, identity: str, candidate: CandidateRef, text: str) -> Ref:
        """The contents go to the evidence repository; one create-only store record holds its Ref and the exact
        candidate. The same text for the same candidate returns the existing Ref; other text is SELF_REVIEW_EXISTS."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("the self-review text is required")
        item = self.records.identities.find(identity)
        if item is None:
            raise ValueError(f"no work item {identity}")
        evidence = Observation(
            Header(self.definition.project, self.definition.profile,
                   f"{SELF_REVIEW}/{item.id}/{candidate.content_digest}", "1", (self.definition,)),
            self.definition, SELF_REVIEW, SELF_REVIEW + "/v1", (),
            canonical_bytes({"identity": item.id, "candidate_locator": candidate.locator,
                             "candidate_digest": candidate.content_digest, "text": text}).decode(),
            None, SELF_REVIEW, SELF_REVIEW)
        reference = record_ref(evidence)
        aggregate = self_review_aggregate(item.id, candidate)
        expected = {"evidence_ref": asdict(reference), "candidate": candidate_document(candidate)}
        _, existing = self.store.read_state(self.store_profile, aggregate)
        if not existing:
            if self.evidence.put(evidence) != reference:
                raise RuntimeError("the evidence repository answered another reference")
            try:
                self.store.commit(self.store_profile, aggregate, 0, expected)
                return reference
            except VersionConflict:  # Another run recorded first: a repeat only if its record equals this one.
                _, existing = self.store.read_state(self.store_profile, aggregate)
        if existing != expected:
            raise SelfReviewExists(aggregate)
        return reference
