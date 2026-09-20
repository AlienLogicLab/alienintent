"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""

from __future__ import annotations

from pathlib import Path

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.domain.runtime import BudgetIneligible, CapabilityGrant, InvocationRole, require_eligible
from alienintent.invocation_runtime.ports.source_control import SourceControl
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess
from alienintent.invocation_runtime.ports.workspace import WorkspaceManager


class RealWorkerProvider(WorkerProvider):
    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str, verifier_root: Path, grant: CapabilityGrant, target: str, workspaces: WorkspaceManager) -> None:
        self._process, self._source, self._workspace = process, source_control, workspace
        self._remote, self._branch, self._verifier_root, self._grant, self._target, self._workspaces = remote, branch, verifier_root, grant, target, workspaces
        self._outcomes: dict[str, WorkerOutcome] = {}

    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        if budget.hard_wall_clock_seconds is None or budget.cancellation_limit is None or self._grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        try:
            self._grant.require("process-control", self._target, 0)
            self._grant.require("git-write", self._target, 0)
            capabilities = getattr(self._process, "capabilities", None)
            if capabilities is None:
                raise BudgetIneligible("provider capabilities are required")
            require_eligible(capabilities, frozenset(budget.required_dimensions))
        except (PermissionError, BudgetIneligible):
            return WorkerOutcome("ineligible")
        workspace = self._workspaces.allocate(invocation.correlation_id, invocation.work_identity, "HEAD")
        try:
            result = self._process.run(invocation.correlation_id, InvocationRole.PRODUCER, workspace.path, budget.hard_wall_clock_seconds)
            if result.kind != "success" or ("token" in budget.required_dimensions and result.budget.token_cost is None) or ("monetary" in budget.required_dimensions and result.budget.monetary_cost is None):
                outcome = WorkerOutcome(result.kind)
            else:
                revision = self._source.revision(workspace.path)
                candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._branch, revision, self._verifier_root)
                outcome = WorkerOutcome.success(candidate)
        finally:
            self._workspaces.cleanup(workspace, None)
        self._outcomes[invocation.correlation_id] = outcome
        return outcome

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        return self._outcomes.get(invocation.correlation_id)
