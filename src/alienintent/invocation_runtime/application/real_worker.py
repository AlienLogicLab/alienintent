"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Callable, Mapping, Sequence

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.domain.runtime import VERDICT_PATH, BudgetIneligible, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, require_eligible
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal
from alienintent.invocation_runtime.ports.source_control import SourceControl
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess
from alienintent.invocation_runtime.ports.workspace import WorkspaceManager


def encode_candidate(candidate: CandidateRef | None) -> dict[str, object] | None:
    if candidate is None:
        return None
    return {
        "kind": str(candidate.kind), "identity": candidate.identity, "content_digest": candidate.content_digest,
        "locator": candidate.locator, "provenance": candidate.provenance,
        "independent_read_back_proven": candidate.independent_read_back_proven,
    }


def decode_candidate(record: Mapping[str, object] | None) -> CandidateRef | None:
    if record is None:
        return None
    return CandidateRef(
        CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]),
        str(record["locator"]), str(record["provenance"]), bool(record["independent_read_back_proven"]),
    )


# Outcome kinds that must name the exact candidate the role acted on.
CANDIDATE_KINDS = {str(InvocationRole.PRODUCER): frozenset({"success"}), str(InvocationRole.VERIFIER): frozenset({"accept", "reject"}), str(InvocationRole.CLOSURE): frozenset({"closed"})}


def _strings(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, (list, tuple)) or not all(isinstance(entry, str) and entry for entry in value):
        return None
    return tuple(value)


def correlated_outcome(records: Sequence[Mapping[str, object]], invocation: WorkerInvocation, branch: str) -> WorkerOutcome | None:
    """The one durable role outcome attributable to ``invocation``, or None.

    None is a hold, not a failure: no record, a duplicate record, or a record
    naming another work item, role, contract or candidate (a producer's branch,
    or the exact candidate a verifier or closure invocation was given) is not
    this invocation's result, however its process exited.
    """
    own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
    started = [record for record in own if record.get("event") == "invocation-started"]
    finished = [record for record in own if record.get("event") == "invocation-outcome"]
    if len(started) != 1 or len(finished) != 1:
        return None
    begun, record = started[0], finished[0]
    for entry in (begun, record):
        if entry.get("work_identity") != invocation.work_identity or entry.get("role") != invocation.role:
            return None
    if record.get("contract_digest") != begun.get("contract_digest"):
        return None
    if invocation.contract_digest is not None and record.get("contract_digest") != invocation.contract_digest:
        return None
    kind, attempt, encoded = record.get("kind"), record.get("attempt"), record.get("candidate")
    findings, receipts = _strings(record.get("findings", ())), _strings(record.get("receipts", ()))
    if not isinstance(kind, str) or not (encoded is None or isinstance(encoded, Mapping)) or findings is None or receipts is None:
        return None
    try:
        candidate = decode_candidate(encoded)
    except (KeyError, TypeError, ValueError):
        return None
    if kind not in CANDIDATE_KINDS.get(invocation.role, ()):
        if candidate is not None:
            return None
    elif invocation.role == str(InvocationRole.PRODUCER):
        if candidate is None or not isinstance(attempt, int) or attempt < 1 or not _publishes_to(candidate, branch):
            return None
    elif not _same_candidate(candidate, invocation.candidate):
        return None
    return WorkerOutcome(kind, candidate, findings=findings, receipts=receipts)


def _same_candidate(reported: CandidateRef | None, given: CandidateRef | None) -> bool:
    return reported is not None and given is not None and (reported.kind, reported.identity, reported.content_digest) == (given.kind, given.identity, given.content_digest)


def _revision_of(candidate: CandidateRef) -> str | None:
    if candidate.kind is not CandidateKind.SOURCE_REVISION or "@" not in candidate.locator:
        return None
    return candidate.locator.rsplit("@", 1)[1]


def read_verdict(path: Path, candidate: CandidateRef) -> WorkerOutcome:
    """The verdict a verifier process left for exactly ``candidate``.

    A missing, malformed or other-revision verdict is not a verdict: it reads
    as a kind the coordinator holds on, never as acceptance.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return WorkerOutcome("verdict-missing")
    if not isinstance(document, Mapping):
        return WorkerOutcome("verdict-malformed")
    if document.get("revision") != _revision_of(candidate):
        return WorkerOutcome("verdict-miscorrelated")
    findings = _strings(document.get("findings", []))
    if findings is None:
        return WorkerOutcome("verdict-malformed")
    if document.get("verdict") == "accept":
        return WorkerOutcome.accept(candidate, findings)
    if document.get("verdict") == "reject" and findings:
        return WorkerOutcome.reject(candidate, findings)
    return WorkerOutcome("verdict-malformed")


def _publishes_to(candidate: CandidateRef, branch: str) -> bool:
    if candidate.kind is not CandidateKind.SOURCE_REVISION or "#" not in candidate.locator:
        return False
    return candidate.locator.rsplit("#", 1)[1].rsplit("@", 1)[0] == branch


class RealWorkerProvider(WorkerProvider):
    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str | Callable[[WorkerInvocation], str], verifier_root: Path, grant: CapabilityGrant | Callable[[WorkerInvocation], CapabilityGrant], target: str, workspaces: WorkspaceManager | None, reservations: ReservationBook | None = None, *, now: Callable[[], float], sleep: Callable[[float], None], journal: InvocationJournal | None = None) -> None:
        self._process, self._source, self._workspace = process, source_control, workspace
        self._remote, self._branch, self._verifier_root, self._grant, self._target, self._workspaces = remote, branch, verifier_root, grant, target, workspaces
        self._outcomes: dict[str, WorkerOutcome] = {}
        self._active_workspaces: dict[str, object] = {}
        self._finished_workspaces: dict[str, object] = {}
        self.retained_workspaces: dict[str, Path] = {}
        self._reservations = reservations
        self.cleanup_diagnostics: dict[str, str] = {}
        self.retry_evidence: dict[str, RetryEvidence] = {}
        self.verifier_provenance: dict[str, str] = {}
        self._now = now
        self._sleep = sleep
        self._journal = journal

    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        """Run one role invocation; with a journal, retain its attributable outcome durably first."""
        if self._journal is None:
            outcome = self._start(invocation, context, grants, budget)
            # Every returned outcome, including an early refusal, must read back.
            self._outcomes[invocation.correlation_id] = outcome
            return outcome
        attribution = {
            "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity, "role": invocation.role,
            "contract_digest": None if context is None else context.content_digest,
        }
        self._journal.append({"event": "invocation-started"} | attribution)
        outcome = self._start(invocation, context, grants, budget)
        retry = self.retry_evidence.get(invocation.correlation_id)
        self._journal.append({"event": "invocation-outcome"} | attribution | {
            "attempt": None if retry is None else retry.attempts, "kind": outcome.kind, "candidate": encode_candidate(outcome.candidate),
            "findings": list(outcome.findings), "receipts": list(outcome.receipts),
        })
        return outcome

    def _start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        if invocation.role == str(InvocationRole.VERIFIER):
            outcome = self._evaluate(invocation, budget)
        elif invocation.role == str(InvocationRole.CLOSURE):
            outcome = self._close(invocation)
        elif invocation.role == str(InvocationRole.PRODUCER):
            return self._produce(invocation, context, grants, budget)
        else:
            outcome = WorkerOutcome("ineligible")
        self._outcomes[invocation.correlation_id] = outcome
        return outcome

    def _evaluate(self, invocation: WorkerInvocation, budget: BudgetPolicy) -> WorkerOutcome:
        """A distinct verifier invocation over a fresh retrieval of the exact candidate."""
        grant, candidate = self._grant_for(invocation), invocation.candidate
        if candidate is None or budget.hard_wall_clock_seconds is None or grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        try:
            grant.require("process-control", self._target, self._now())
            capabilities = getattr(self._process, "capabilities", None)
            if capabilities is None:
                raise BudgetIneligible("provider capabilities are required")
            require_eligible(capabilities, frozenset(budget.required_dimensions))
        except (PermissionError, BudgetIneligible):
            return WorkerOutcome("ineligible")
        if self._reservations is not None:
            try:
                self._reservations.reserve(invocation.correlation_id, InvocationRole.VERIFIER)
            except RuntimeError:
                return WorkerOutcome("ineligible")
        try:
            workspace = self._verifier_root / f"verifier-{invocation.correlation_id}"
            try:
                self._source.retrieve_for_verification(candidate, workspace)
            except CandidateUnavailable:
                return WorkerOutcome("candidate-unavailable")
            self.verifier_provenance[invocation.correlation_id] = workspace.as_posix()
            verdict = workspace / VERDICT_PATH
            if verdict.exists():
                # The candidate itself carries a verdict: a producer cannot approve its own work.
                return WorkerOutcome("verdict-preexisting")
            result = self._process.run(invocation.correlation_id, InvocationRole.VERIFIER, workspace, budget.hard_wall_clock_seconds)
            if result.kind != "success":
                return WorkerOutcome(result.kind)
            return read_verdict(verdict, candidate)
        finally:
            if self._reservations is not None:
                self._reservations.release(invocation.correlation_id)

    def _close(self, invocation: WorkerInvocation) -> WorkerOutcome:
        """Perform and read back the closure actions this adapter can attest.

        Only ``candidate-published`` is performable here: the accepted exact
        revision is re-read from the remote into a fresh directory. No other
        action is claimed, so a contract requiring more holds at ACCEPT.
        """
        grant, candidate = self._grant_for(invocation), invocation.candidate
        if candidate is None or grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        receipts: list[str] = []
        try:
            self._source.retrieve_for_verification(candidate, self._verifier_root / f"closure-{invocation.correlation_id}")
            receipts.append("candidate-published")
        except CandidateUnavailable:
            pass
        return WorkerOutcome.closed(candidate, tuple(receipts))

    def _produce(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        grant = self._grant_for(invocation)
        if budget.hard_wall_clock_seconds is None or budget.cancellation_limit is None or grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        try:
            grant.require("process-control", self._target, self._now())
            grant.require("git-write", self._target, self._now())
            capabilities = getattr(self._process, "capabilities", None)
            if capabilities is None:
                raise BudgetIneligible("provider capabilities are required")
            require_eligible(capabilities, frozenset(budget.required_dimensions))
        except (PermissionError, BudgetIneligible):
            return WorkerOutcome("ineligible")
        if self._reservations is not None:
            try:
                self._reservations.reserve(invocation.correlation_id, InvocationRole.PRODUCER)
            except RuntimeError:
                return WorkerOutcome("ineligible")
        if self._workspaces is None:
            return WorkerOutcome("ineligible")
        workspace = self._workspaces.allocate(invocation.correlation_id, invocation.work_identity, "HEAD")
        self._active_workspaces[invocation.correlation_id] = workspace
        outcome = WorkerOutcome("failure")
        try:
            schedule = RetrySchedule(budget.maximum_attempts, budget.retry_limit, .01, .001)
            attempts, next_eligible = 0, None
            while True:
                attempts += 1
                result = self._process.run(invocation.correlation_id, InvocationRole.PRODUCER, workspace.path, budget.hard_wall_clock_seconds)
                if result.kind == "success":
                    break
                next_eligible = schedule.next_after_failure(attempts, float(self._now()))
                if next_eligible is None:
                    break
                self._sleep(max(0, next_eligible - float(self._now())))
            self.retry_evidence[invocation.correlation_id] = RetryEvidence(attempts, next_eligible)
            if result.kind != "success" or ("token" in budget.required_dimensions and result.budget.token_cost is None) or ("monetary" in budget.required_dimensions and result.budget.monetary_cost is None):
                outcome = WorkerOutcome(result.kind)
            else:
                revision = self._source.revision(workspace.path)
                candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
                outcome = WorkerOutcome.success(candidate)
        finally:
            if outcome.kind in {"success", "authority-block"}:
                self._finished_workspaces[invocation.correlation_id] = workspace
            else:
                try:
                    self._workspaces.cleanup(workspace, None)
                except Exception as error:
                    self.cleanup_diagnostics[invocation.correlation_id] = type(error).__name__
            if self._reservations is not None:
                self._reservations.release(invocation.correlation_id)
            self._active_workspaces.pop(invocation.correlation_id, None)
        self._outcomes[invocation.correlation_id] = outcome
        return outcome

    def _grant_for(self, invocation: WorkerInvocation) -> CapabilityGrant:
        """The capability grant issued for this invocation.

        A grant names the invocation it authorizes, so one fixed grant admits
        exactly one invocation. A profile draining a backlog issues one per
        dispatch; a fixed grant stays valid for a single-invocation caller.
        """
        return self._grant(invocation) if callable(self._grant) else self._grant

    def _producer_read_back(self, invocation: WorkerInvocation) -> Path:
        """A fresh, unused directory for this invocation's publication read-back.

        `verify` already treats `verifier_root` as a root it allocates under.
        Publication read-back refuses a directory that already exists, so the
        second candidate a profile publishes would fail against the root
        itself; each invocation reads back into its own child.
        """
        return self._verifier_root / f"producer-{invocation.correlation_id}"

    def _candidate_branch(self, invocation: WorkerInvocation) -> str:
        """The branch this candidate publishes to.

        A profile draining more than one work item cannot publish every
        candidate to one branch: sibling revisions off the same baseline are
        not fast-forwards of each other, so the second publication would be
        refused and custody could never be proven for it.
        """
        return self._branch(invocation) if callable(self._branch) else self._branch

    def finalize(self, invocation: WorkerInvocation, retain: bool) -> None:
        """Complete workspace disposition after the coordinator durably records truth."""
        workspace = self._finished_workspaces.pop(invocation.correlation_id, None)
        if workspace is None:
            return
        if retain:
            self.retained_workspaces[invocation.correlation_id] = workspace.path
            return
        try:
            self._workspaces.cleanup(workspace, None)
        except Exception as error:
            self.cleanup_diagnostics[invocation.correlation_id] = type(error).__name__

    def cancel(self, invocation_id: str, reason: str):
        """Fence a live owned invocation; its runner performs quiescent cleanup."""
        if invocation_id not in self._active_workspaces:
            return self._process.cancel(invocation_id, reason)
        result = self._process.cancel(invocation_id, reason)
        if result.quiescent and self._reservations is not None:
            self._reservations.release(invocation_id)
        return result

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        """With a journal, answer only from durable, correlated evidence; this survives a restart."""
        if self._journal is None:
            return self._outcomes.get(invocation.correlation_id)
        try:
            records = self._journal.records()
        except JournalUnreadable:
            return None
        return correlated_outcome(records, invocation, self._candidate_branch(invocation))

    def verify(self, candidate, producer_invocation_id: str, verifier_invocation_id: str) -> WorkerOutcome:
        try:
            VerifierIndependence(producer_invocation_id, verifier_invocation_id).require(InvocationRole.VERIFIER)
        except PermissionError:
            return WorkerOutcome("self-approval-rejected")
        if self._reservations is not None:
            try:
                self._reservations.reserve(verifier_invocation_id, InvocationRole.VERIFIER)
            except RuntimeError:
                return WorkerOutcome("ineligible")
        try:
            workspace = self._verifier_root / verifier_invocation_id
            verified = self._source.retrieve_for_verification(candidate, workspace)
            self.verifier_provenance[verifier_invocation_id] = workspace.as_posix()
            return WorkerOutcome.success(verified)
        except CandidateUnavailable:
            return WorkerOutcome("candidate-unavailable")
        finally:
            if self._reservations is not None:
                self._reservations.release(verifier_invocation_id)
