"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Mapping, Sequence

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.domain.runtime import BudgetIneligible, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, require_eligible
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


def correlated_outcome(records: Sequence[Mapping[str, object]], invocation: WorkerInvocation, branch: str) -> WorkerOutcome | None:
    """The one durable producer outcome attributable to ``invocation``, or None.

    None is a hold, not a failure: no record, a duplicate record, or a record
    naming another work item, role, contract or candidate branch is not this
    invocation's result, however its process exited.
    """
    own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
    started = [record for record in own if record.get("event") == "invocation-started"]
    finished = [record for record in own if record.get("event") == "invocation-outcome"]
    if len(started) != 1 or len(finished) != 1:
        return None
    begun, record = started[0], finished[0]
    for entry in (begun, record):
        if entry.get("work_identity") != invocation.work_identity or entry.get("role") != str(InvocationRole.PRODUCER):
            return None
    if record.get("contract_digest") != begun.get("contract_digest"):
        return None
    if invocation.contract_digest is not None and record.get("contract_digest") != invocation.contract_digest:
        return None
    kind, attempt, encoded = record.get("kind"), record.get("attempt"), record.get("candidate")
    if not isinstance(kind, str) or not (encoded is None or isinstance(encoded, Mapping)):
        return None
    try:
        candidate = decode_candidate(encoded)
    except (KeyError, TypeError, ValueError):
        return None
    if kind == "success":
        if candidate is None or not isinstance(attempt, int) or attempt < 1 or not _publishes_to(candidate, branch):
            return None
    elif candidate is not None:
        return None
    return WorkerOutcome(kind, candidate)


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
        """Run one producer invocation; with a journal, retain its attributable outcome durably first."""
        if self._journal is None:
            outcome = self._start(invocation, context, grants, budget)
            # Every returned outcome, including an early refusal, must read back.
            self._outcomes[invocation.correlation_id] = outcome
            return outcome
        attribution = {
            "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity, "role": str(InvocationRole.PRODUCER),
            "contract_digest": None if context is None else context.content_digest,
        }
        self._journal.append({"event": "invocation-started"} | attribution)
        outcome = self._start(invocation, context, grants, budget)
        retry = self.retry_evidence.get(invocation.correlation_id)
        self._journal.append({"event": "invocation-outcome"} | attribution | {
            "attempt": None if retry is None else retry.attempts, "kind": outcome.kind, "candidate": encode_candidate(outcome.candidate),
        })
        return outcome

    def _start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
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
