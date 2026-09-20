"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Callable

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.domain.runtime import BudgetIneligible, CandidateUnavailable, CapabilityGrant, InvocationRole, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, require_eligible
from alienintent.invocation_runtime.ports.source_control import SourceControl
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess
from alienintent.invocation_runtime.ports.workspace import WorkspaceManager


class RealWorkerProvider(WorkerProvider):
    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str, verifier_root: Path, grant: CapabilityGrant, target: str, workspaces: WorkspaceManager | None, reservations: ReservationBook | None = None, *, now: Callable[[], float], sleep: Callable[[float], None]) -> None:
        self._process, self._source, self._workspace = process, source_control, workspace
        self._remote, self._branch, self._verifier_root, self._grant, self._target, self._workspaces = remote, branch, verifier_root, grant, target, workspaces
        self._outcomes: dict[str, WorkerOutcome] = {}
        self._active_workspaces: dict[str, object] = {}
        self._reservations = reservations
        self.cleanup_diagnostics: dict[str, str] = {}
        self.retry_evidence: dict[str, RetryEvidence] = {}
        self.verifier_provenance: dict[str, str] = {}
        self._now = now
        self._sleep = sleep

    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        if budget.hard_wall_clock_seconds is None or budget.cancellation_limit is None or self._grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        try:
            self._grant.require("process-control", self._target, self._now())
            self._grant.require("git-write", self._target, self._now())
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
                candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._branch, revision, self._verifier_root)
                outcome = WorkerOutcome.success(candidate)
        finally:
            try:
                self._workspaces.cleanup(workspace, None)
            except Exception as error:
                self.cleanup_diagnostics[invocation.correlation_id] = type(error).__name__
            if self._reservations is not None:
                self._reservations.release(invocation.correlation_id)
            self._active_workspaces.pop(invocation.correlation_id, None)
        self._outcomes[invocation.correlation_id] = outcome
        return outcome

    def cancel(self, invocation_id: str, reason: str):
        """Fence a live owned invocation; its runner performs quiescent cleanup."""
        if invocation_id not in self._active_workspaces:
            return self._process.cancel(invocation_id, reason)
        result = self._process.cancel(invocation_id, reason)
        if result.quiescent and self._reservations is not None:
            self._reservations.release(invocation_id)
        return result

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        return self._outcomes.get(invocation.correlation_id)

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
