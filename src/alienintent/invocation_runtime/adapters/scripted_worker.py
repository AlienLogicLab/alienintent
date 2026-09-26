"""Deterministic scripted worker transport for the offline proof substrate (S0).

This substitutes exactly one boundary: the provider process behind the
production Worker Port. ``RealWorkerProvider``, ``GitSourceControl`` and
``GitWorktreeAdapter`` run unchanged above it, so a scripted "success" is a real
commit in a real worktree that the production path publishes to the fixture's
remote and reads back from a fresh clone. The script drives external outcomes
only: it holds no operational store, performs no lifecycle transition, runs no
model, spends no token and is handed no credential.

Every outcome is journaled durably by invocation identity before it is reported,
so a restart reopens the same journal and reads back the same truth.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
from typing import Callable, Mapping, Sequence

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.adapters.invocation_journal import journal_append, journal_records
from alienintent.invocation_runtime.application.real_worker import decode_candidate, encode_candidate
from alienintent.invocation_runtime.domain.runtime import FEATURE_REGRESSION_RECEIPT_PATH, VERDICT_PATH, BudgetRecord, InvocationRole, ProcessResult, ProviderCapabilities, ScriptRejected
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess

SCRIPTED_PROVIDER = "scripted"
SCRIPTED_DIMENSIONS = frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"})
PRODUCER_STEPS = frozenset({"success", "failure", "timeout", "authority-block", "provider-call"})
# A verifier step renders (or, for ``no-verdict``, withholds) a verdict on the
# exact revision checked out in the verifier's own fresh workspace.
VERIFIER_STEPS = frozenset({"accept", "reject", "no-verdict"})
SCRIPTED_STEPS = PRODUCER_STEPS | VERIFIER_STEPS
PROVIDER_NOT_CONFIGURED = "alienintent-provider-not-configured"



def work_identity_of(invocation_id: str) -> str:
    """The work item an invocation belongs to.

    The coordinator correlates an invocation as ``launch:<work>:<version>``; any
    other identity is taken to name the work item directly.
    """
    if invocation_id.startswith("launch:") and invocation_id.count(":") >= 2:
        _, identity, _ = invocation_id.rsplit(":", 2)
        return identity
    return invocation_id


def journal_outcome(path: Path, correlation_id: str) -> WorkerOutcome | None:
    """The durably recorded outcome of an invocation, or None when none was recorded."""
    for entry in reversed(journal_records(path)):
        if entry.get("event") == "invocation-outcome" and entry.get("correlation_id") == correlation_id:
            candidate = entry.get("candidate")
            return WorkerOutcome(
                str(entry["kind"]), decode_candidate(candidate if isinstance(candidate, dict) else None),
                findings=tuple(entry.get("findings") or ()), receipts=tuple(entry.get("receipts") or ()),
            )
    return None


def journal_provider_calls(path: Path) -> int:
    """Attempts by the process adapter to execute a provider executable; an observed count, never assumed."""
    return sum(int(entry.get("provider_calls", 0)) for entry in journal_records(path) if entry.get("event") == "process-run")


class ScriptedWorkerProcess(WorkerProcess):
    """Deterministic process behind the production Worker Port.

    ``run`` consumes the next scripted step for the invocation's work item. A
    ``success`` step commits the pinned note into the allocated worktree with
    the injected clock as author and committer date, so the same script and
    clock reproduce the same revision. A ``provider-call`` step *attempts* to
    execute a provider executable that is not configured; it exists so the
    zero-provider-call counter can be shown to move. Verifier steps write a
    verdict for the checked-out revision; a verifier with no remaining step
    renders none, which the production path holds on.
    """

    def __init__(
        self,
        script: Mapping[str, Sequence[str]],
        notes: Mapping[str, str],
        clock: Callable[[], float],
        journal_path: Path,
        environment: Mapping[str, str],
        *,
        provider_executable: str = PROVIDER_NOT_CONFIGURED,
    ) -> None:
        unknown = sorted({step for steps in script.values() for step in steps} - SCRIPTED_STEPS)
        if unknown:
            raise ScriptRejected(f"unknown scripted step: {unknown[0]}")
        self.capabilities = ProviderCapabilities(SCRIPTED_PROVIDER, SCRIPTED_DIMENSIONS)
        # Every step runs in this process and ends before ``run`` returns, so
        # no work of an invocation can outlive it unobserved.
        self.marks_owned_work = True
        self._remaining = {identity: list(steps) for identity, steps in script.items()}
        self._notes = dict(notes)
        self._clock, self.journal_path = clock, journal_path
        self._environment = dict(environment)
        self._provider_executable = provider_executable
        self._attempts: dict[str, int] = {}
        self._completed: set[str] = set()
        self.provider_calls = 0

    def run(self, invocation_id: str, role: InvocationRole, workspace: Path, wall_clock_seconds: float) -> ProcessResult:
        work = work_identity_of(invocation_id)
        steps = self._remaining.get(work)
        verifying = role is InvocationRole.VERIFIER
        if not steps and not verifying:
            raise ScriptRejected(f"no scripted step remains for {work}")
        step = steps.pop(0) if steps else "no-verdict"
        if (step in VERIFIER_STEPS) != verifying:
            raise ScriptRejected(f"scripted step {step} cannot run as {role}")
        attempt = self._attempts[work] = self._attempts.get(work, 0) + 1
        provider_calls = 0
        if step == "success":
            self._commit(work, invocation_id, workspace)
            result = ProcessResult("success", 0, True, BudgetRecord.unknown())
        elif verifying:
            if step != "no-verdict":
                self._verdict(work, invocation_id, workspace, step)
            result = ProcessResult("success", 0, True, BudgetRecord.unknown())
        elif step == "provider-call":
            provider_calls = 1
            self.provider_calls += 1
            result = ProcessResult("failure", self._attempt_provider(workspace), True, BudgetRecord.unknown())
        elif step == "failure":
            result = ProcessResult("failure", 1, True, BudgetRecord.unknown())
        elif step == "timeout":
            result = ProcessResult("timeout", None, True, BudgetRecord.unknown())
        else:
            result = ProcessResult("authority-block", 0, True, BudgetRecord.unknown())
        self._completed.add(invocation_id)
        journal_append(self.journal_path, self._clock, {
            "event": "process-run", "invocation_id": invocation_id, "work_identity": work, "role": str(role),
            "attempt": attempt, "step": step, "result": result.kind, "exit_status": result.exit_status,
            "provider_calls": provider_calls, "wall_clock_seconds": wall_clock_seconds,
            "token_cost": "UNKNOWN", "monetary_cost": "UNKNOWN",
        })
        return result

    def cancel(self, invocation_id: str, reason: str) -> ProcessResult:
        quiescent = invocation_id in self._completed
        journal_append(self.journal_path, self._clock, {"event": "process-cancel", "invocation_id": invocation_id, "reason": reason, "quiescent": quiescent})
        return ProcessResult("already-finished" if quiescent else "unresolved-recovery", None, quiescent, BudgetRecord.unknown())

    def _git(self, *args: str, cwd: Path) -> None:
        epoch = int(self._clock())
        environment = self._environment | {"GIT_AUTHOR_DATE": f"{epoch} +0000", "GIT_COMMITTER_DATE": f"{epoch} +0000"}
        result = subprocess.run(["git", *args], cwd=cwd, env=environment, capture_output=True, text=True, check=False)
        if result.returncode:
            raise ScriptRejected(f"scripted git step failed: {result.stderr.strip()[:200]}")

    def _commit(self, work: str, invocation_id: str, workspace: Path) -> None:
        note = workspace / self._notes.get(work, f"docs/{work}.md")
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"{work} produced by the scripted worker under {invocation_id}\n", encoding="utf-8")
        self._git("add", "-A", cwd=workspace)
        self._git("commit", "-q", "-m", f"{work}: scripted candidate", cwd=workspace)

    def _verdict(self, work: str, invocation_id: str, workspace: Path, step: str) -> None:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=workspace, env=self._environment, capture_output=True, text=True, check=False).stdout.strip()
        findings = [] if step == "accept" else [f"{work}: scripted rejection under {invocation_id}"]
        verdict = workspace / VERDICT_PATH
        verdict.parent.mkdir(parents=True, exist_ok=True)
        receipt_body = {
            "schema_version": 1, "kind": "FeatureRegressionReceipt", "base": "SCRIPTED_FIXTURE",
            "candidate": revision, "changed_paths": [], "manifest_digest": "SCRIPTED_FIXTURE",
            "packs": [{"id": "scripted-fixture", "passed": True}], "passed": True,
        }
        import hashlib
        encoded = json.dumps(receipt_body, sort_keys=True, separators=(",", ":")).encode()
        receipt_body["receipt_digest"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
        (workspace / FEATURE_REGRESSION_RECEIPT_PATH).write_text(
            json.dumps(receipt_body, sort_keys=True), encoding="utf-8")
        verdict.write_text(json.dumps({"verdict": step, "revision": revision, "findings": findings}), encoding="utf-8")

    def _attempt_provider(self, workspace: Path) -> int:
        try:
            completed = subprocess.run([self._provider_executable, "--version"], cwd=workspace, env=self._environment, capture_output=True, text=True, timeout=5, check=False)
        except FileNotFoundError:
            return 127
        except subprocess.TimeoutExpired:
            return 124
        return completed.returncode


class ScriptedWorkerProvider(WorkerProvider):
    """The production worker provider with a durable journal at its boundary.

    ``start`` journals the invocation before and after the wrapped provider
    runs it; ``read_back`` answers only from the journal, so a process that died
    between the two records reads back as unresolved rather than as any outcome.
    """

    def __init__(self, inner: WorkerProvider, journal_path: Path, clock: Callable[[], float]) -> None:
        self._inner, self.journal_path, self._clock = inner, journal_path, clock

    def _append(self, record: Mapping[str, object]) -> dict[str, object]:
        return journal_append(self.journal_path, self._clock, record)

    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        self._append({
            "event": "invocation-started", "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity,
            "role": invocation.role, "contract_digest": None if context is None else context.content_digest,
        })
        outcome = self._inner.start(invocation, context, grants, budget)
        self._append({
            "event": "invocation-outcome", "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity,
            "role": invocation.role, "kind": outcome.kind, "candidate": encode_candidate(outcome.candidate),
            "findings": list(outcome.findings), "receipts": list(outcome.receipts),
        })
        return outcome

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        return journal_outcome(self.journal_path, invocation.correlation_id)

    def cancel(self, invocation_id: str, reason: str) -> object:
        result = self._inner.cancel(invocation_id, reason)
        self._append({"event": "invocation-cancel", "correlation_id": invocation_id, "reason": reason, "result": getattr(result, "kind", str(result))})
        return result

    def finalize(self, invocation: WorkerInvocation, retain: bool) -> None:
        finalize = getattr(self._inner, "finalize", None)
        if callable(finalize):
            finalize(invocation, retain)
        self._append({"event": "workspace-finalized", "correlation_id": invocation.correlation_id, "retained": retain})
