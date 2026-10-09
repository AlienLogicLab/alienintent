"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.ports.worker_provider import (
    MISSING_TERMINAL_RESULT, WorkerInvocation, WorkerOutcome, WorkerProvider)
from alienintent.invocation_runtime.application.regression_gate import RegressionGate, SuiteUnrunnable
from alienintent.invocation_runtime.domain.diagnostics import cause
from alienintent.invocation_runtime.domain.runtime import FEATURE_REGRESSION_RECEIPT_PATH, VERDICT_PATH, BudgetIneligible, BudgetRecord, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable, ProcessResult, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, owner_token, require_eligible, workspace_folder
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal
from alienintent.invocation_runtime.ports.process_ownership import ProcessOwnership
from alienintent.invocation_runtime.ports.source_control import SourceControl
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess
from alienintent.invocation_runtime.ports.workspace import Workspace, WorkspaceManager


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


# AC-08 restart-time attestation answers (``attest_ownership``). Only
# ``owner-terminated`` is conclusive; every other answer leaves the invocation
# UNKNOWN, and nothing may replace it.
OWNER_TERMINATED = "owner-terminated"
OWNER_UNATTESTED, OWNER_ALIVE, OWNED_WORK_ACTIVE, EFFECT_UNKNOWN = "owner-unattested", "owner-alive", "owned-work-active", "effect-unknown"
# Journaled just before a producer's publication, the one external effect a
# role invocation performs; once present, a lost result's effect is UNKNOWN.
PUBLICATION_STARTED = "publication-started"
# Journaled by the control plane before a landing's first irreversible effect (the same rule).
CLOSURE_ORDERED = "closure-ordered"
# The exact `candidate-published` receipt (execution_coordination/domain/closure.py `receipt`, whose format this
# repeats so the runtime takes no cross-module domain import): `<action>:<work item id>:<full candidate revision>`.
CANDIDATE_PUBLISHED_RECEIPT = "candidate-published:{identity}:{revision}"


_FULL_SHA = re.compile(r"[0-9a-f]{40}")


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


def _read_path(path: Path) -> bytes:
    return path.read_bytes()


def _feature_regression_receipt(path: Path, candidate: CandidateRef,
                                read: Callable[[Path], bytes] = _read_path) -> str | None:
    try:
        document = json.loads(read(path).decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(document, Mapping) or document.get("kind") != "FeatureRegressionReceipt" or document.get("passed") is not True:
        return None
    if document.get("candidate") != _revision_of(candidate):
        return None
    packs = document.get("packs")
    if not isinstance(packs, list) or any(not isinstance(pack, Mapping) or pack.get("passed") is not True for pack in packs):
        return None
    digest = document.get("receipt_digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        return None
    body = dict(document)
    del body["receipt_digest"]
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if digest != "sha256:" + sha256(encoded).hexdigest():
        return None
    return "feature-regressions:" + digest


def read_verdict(path: Path, candidate: CandidateRef, read: Callable[[Path], bytes] = _read_path, *,
                 gate_receipt: str | None = None) -> WorkerOutcome:
    """The verdict a verifier process left for exactly ``candidate``.

    A missing, malformed or other-revision verdict is not a verdict: it reads
    as a kind the coordinator holds on, never as acceptance. ``read`` reads the
    verdict and the receipt beside it (with a worker user: through the
    hand-over's checked descriptor, never a worker-chosen path). With
    ``gate_receipt`` (the control plane's own REGRESSION-GATE receipt) no
    worker-written ``feature-regressions.json`` is read.
    """
    try:
        document = json.loads(read(path).decode("utf-8"))
    except (OSError, ValueError):
        return WorkerOutcome("verdict-missing")
    if not isinstance(document, Mapping):
        return WorkerOutcome("verdict-malformed")
    if document.get("revision") != _revision_of(candidate):
        return WorkerOutcome("verdict-miscorrelated")
    findings = _strings(document.get("findings", []))
    if findings is None:
        return WorkerOutcome("verdict-malformed")
    regression_receipt = gate_receipt if gate_receipt is not None \
        else _feature_regression_receipt(path.parent / "feature-regressions.json", candidate, read)
    if regression_receipt is None:
        return WorkerOutcome("feature-regressions-missing")
    receipts = (regression_receipt,)
    if document.get("verdict") == "accept":
        return WorkerOutcome.accept(candidate, findings, receipts)
    if document.get("verdict") == "reject" and findings:
        return WorkerOutcome.reject(candidate, findings, receipts)
    return WorkerOutcome("verdict-malformed")


def _publishes_to(candidate: CandidateRef, branch: str) -> bool:
    if candidate.kind is not CandidateKind.SOURCE_REVISION or "#" not in candidate.locator:
        return False
    return candidate.locator.rsplit("#", 1)[1].rsplit("@", 1)[0] == branch


class WorkerPreparation(Protocol):
    """An optional hook, in the style of the `branch` and `grant` hooks, run before a role's process starts.

    `prepare` is called first in `_produce` (`clone` None) and in `_evaluate` right after the fresh candidate clone
    is made (`clone` that clone). It returns the PRODUCER's starting revision (ignored for the VERIFIER) or a complete
    refusal outcome, returned unchanged with nothing started. `published` is called after a PRODUCER candidate is
    published and read back, with that candidate; it must not raise. `gated`, when the hook has it, is called in
    `_evaluate` after the REGRESSION-GATE passed and before the session starts, with the baseline, the candidate
    revision and the gate's receipt; it must not raise.
    """

    def prepare(self, invocation: WorkerInvocation, clone: Path | None) -> str | WorkerOutcome: ...

    def published(self, invocation: WorkerInvocation, candidate: CandidateRef) -> None: ...


class CandidateHandover(Protocol):
    """With a worker user (unit WORKER-CREDENTIAL-BOUNDARY): the candidate's hand-over by exact object identity and
    the worker's own clones. `revision` is the SHA the worker claims (run as the worker); `hand_over` imports exactly
    that SHA into the control plane's intake repository; `publish_intake` publishes it from there and reads it back;
    `candidate_clone` makes a VERIFIER or CLOSURE worker clone after the custody checks; `read_result` reads one file
    of `<results>/<invocation>/` through a checked descriptor (OSError when refused)."""

    results: Path

    def revision(self, workspace: Path) -> str: ...

    def hand_over(self, correlation: str, workspace: Path, claimed: str, starting: str) -> str: ...

    def publish_intake(self, correlation: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...

    def candidate_clone(self, prefix: str, invocation_id: str, owner: str, candidate: CandidateRef) -> Workspace: ...

    def read_result(self, invocation_id: str, name: str, limit: int = 1 << 20) -> bytes: ...


class ClosureActions(Protocol):
    """An optional hook, in the style of `WorkerPreparation`, that performs and reads back CLOSURE's effects.

    `close` runs after the CLOSURE session ended, with the journal the provider writes; `reconcile` settles the
    journaled `closure-ordered` events of this work item and candidate (`orders`, in journal order) with no session,
    or answers None when the last of them provably did not land. Each answers (receipts, findings).
    """

    def close(self, invocation: WorkerInvocation, candidate: CandidateRef,
              journal: InvocationJournal | None) -> tuple[tuple[str, ...], tuple[str, ...]]: ...

    def reconcile(self, invocation: WorkerInvocation, candidate: CandidateRef,
                  orders: tuple[Mapping[str, object], ...]) -> tuple[tuple[str, ...], tuple[str, ...]] | None: ...


class RealWorkerProvider(WorkerProvider):
    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str | Callable[[WorkerInvocation], str], verifier_root: Path, grant: CapabilityGrant | Callable[[WorkerInvocation], CapabilityGrant], target: str, workspaces: WorkspaceManager | None, reservations: ReservationBook | None = None, *, now: Callable[[], float], sleep: Callable[[float], None], journal: InvocationJournal | None = None, ownership: ProcessOwnership | None = None, preparation: WorkerPreparation | None = None, recovered_workspace: Callable[[WorkerInvocation], Workspace | None] | None = None, closure: ClosureActions | None = None, handover: CandidateHandover | None = None, regression_gate: RegressionGate | None = None, regression_base: Callable[[str], str | None] | None = None) -> None:
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
        self._ownership = ownership
        self._preparation = preparation
        # The PRODUCER worktree a correlation owns at its fixed path, for one this process did not run (or None).
        self._recovered_workspace = recovered_workspace
        # The only CLOSURE hook this provider holds: no credential and no Landing Authority.
        self._closure = closure
        # With a worker user: the only source of a candidate (the intake import) and of every worker clone.
        self._handover = handover
        # REGRESSION-GATE: the control plane's whole-suite comparison before each VERIFIER session, against the
        # baseline `regression_base(invocation id)` (the release record's starting revision). None: unchanged.
        self._regression_gate, self._regression_base = regression_gate, regression_base

    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        """Run one role invocation; with a journal, retain its attributable outcome durably first."""
        try:
            return self._journaled(invocation, context, grants, budget)
        finally:
            self._diagnostics(invocation.correlation_id)  # never left behind, whatever happened

    def _diagnostics(self, correlation: str) -> dict[str, object] | None:
        """The bounded diagnostics of the invocation's last process, taken from the process adapter (None without)."""
        kept = getattr(self._process, "diagnostics", None)
        return kept.pop(correlation, None) if isinstance(kept, dict) else None

    def _journaled(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str],
                   budget: BudgetPolicy) -> WorkerOutcome:
        if self._journal is None:
            outcome = self._start(invocation, context, grants, budget)
            # Every returned outcome, including an early refusal, must read back.
            self._outcomes[invocation.correlation_id] = outcome
            return outcome
        attribution = {
            "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity, "role": invocation.role,
            "contract_digest": None if context is None else context.content_digest,
        }
        # The owner is attestable later only if every process the invocation
        # starts carries its markers; otherwise surviving work is unobservable.
        marked = getattr(self._process, "marks_owned_work", False) is True
        owner = None if self._ownership is None or not marked else self._ownership.current()
        self._journal.append({"event": "invocation-started"} | attribution | ({} if owner is None else {"owner": dict(owner)}))
        outcome = self._start(invocation, context, grants, budget)
        retry = self.retry_evidence.get(invocation.correlation_id)
        # The last process's bounded diagnostics and the cause they show, kept with the outcome so they outlive the
        # launcher (a process adapter without diagnostics records none; of several attempts, the last).
        process = self._diagnostics(invocation.correlation_id)
        self._journal.append({"event": "invocation-outcome"} | attribution | {
            "attempt": None if retry is None else retry.attempts, "kind": outcome.kind, "candidate": encode_candidate(outcome.candidate),
            "findings": list(outcome.findings), "receipts": list(outcome.receipts),
            "process": process, "cause": cause(outcome.kind, process),
        })
        return outcome

    def _start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        if invocation.role == str(InvocationRole.VERIFIER):
            outcome = self._evaluate(invocation, budget)
        elif invocation.role == str(InvocationRole.CLOSURE):
            outcome = self._close(invocation, budget)
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
            workspace = self._verifier_root / f"verifier-{workspace_folder(invocation.correlation_id)}"
            try:
                if self._handover is not None:
                    workspace = self._handover.candidate_clone("verifier", invocation.correlation_id,
                                                               invocation.work_identity, candidate).path
                else:
                    self._source.retrieve_for_verification(candidate, workspace)
            except CandidateUnavailable:
                return WorkerOutcome("candidate-unavailable")
            self.verifier_provenance[invocation.correlation_id] = workspace.as_posix()
            if self._preparation is not None:
                prepared = self._preparation.prepare(invocation, workspace)
                if isinstance(prepared, WorkerOutcome):
                    return prepared
            if self._handover is not None:
                # The verdict is a worker result in its fresh `<results>/<invocation>/` folder (it cannot preexist);
                # nothing is read from the worker's clone.
                handover = self._handover
                verdict = handover.results / invocation.correlation_id / Path(VERDICT_PATH).name
                read = lambda path: handover.read_result(path.parent.name, path.name)  # noqa: E731
            else:
                verdict, read = workspace / VERDICT_PATH, _read_path
                if verdict.exists():
                    # The candidate itself carries a verdict: a producer cannot approve its own work.
                    return WorkerOutcome("verdict-preexisting")
            gate_receipt = None
            if self._regression_gate is not None:
                gated = self._gate(invocation, candidate, workspace, verdict)
                if isinstance(gated, WorkerOutcome):
                    return gated
                gate_receipt = gated
                passed = getattr(self._preparation, "gated", None)
                if passed is not None and self._regression_base is not None:
                    # The session is told the whole suite is proven, so it never runs it again.
                    passed(invocation, self._regression_base(invocation.correlation_id), _revision_of(candidate), gated)
            result = self._process.run(invocation.correlation_id, InvocationRole.VERIFIER, workspace, budget.hard_wall_clock_seconds)
            if result.kind != "success":
                return WorkerOutcome(result.kind)
            return read_verdict(verdict, candidate, read, gate_receipt=gate_receipt)
        finally:
            if self._reservations is not None:
                self._reservations.release(invocation.correlation_id)

    def _gate(self, invocation: WorkerInvocation, candidate: CandidateRef, workspace: Path,
              verdict: Path) -> str | WorkerOutcome:
        """REGRESSION-GATE, before the session: the receipt when the candidate has no findings, else the outcome.

        The decision is taken from the bytes the control plane read as each suite ended and is kept in memory. With
        findings the session is not started (a `reject` naming them); no result is `feature-regressions-missing`;
        a verdict present after the suite is `verdict-preexisting`.
        """
        assert self._regression_gate is not None
        base = None if self._regression_base is None else self._regression_base(invocation.correlation_id)
        revision = _revision_of(candidate)
        if not isinstance(base, str) or not _FULL_SHA.fullmatch(base) or revision is None:
            return WorkerOutcome("feature-regressions-missing")
        try:
            findings, receipt = self._regression_gate.check(invocation.correlation_id, workspace, base, revision)
        except (SuiteUnrunnable, CandidateUnavailable, OSError):
            return WorkerOutcome("feature-regressions-missing")
        if self._handover is not None:
            try:
                self._handover.read_result(invocation.correlation_id, verdict.name)
                return WorkerOutcome("verdict-preexisting")
            except FileNotFoundError:
                pass
            except OSError:
                return WorkerOutcome("verdict-preexisting")
        elif verdict.exists():
            return WorkerOutcome("verdict-preexisting")
        if findings:
            return WorkerOutcome.reject(candidate, findings, (receipt,))
        return receipt

    def _close(self, invocation: WorkerInvocation, budget: BudgetPolicy) -> WorkerOutcome:
        """Perform and read back the closure actions this adapter can attest.

        Without the `closure` hook only ``candidate-published`` is performable
        here: the accepted exact revision is re-read from the remote into a
        fresh directory. No other action is claimed, so a contract requiring
        more holds at ACCEPT. With the hook: a fresh CLOSURE session on that
        clone (granted `git-read` and `process-control` only), after which the
        hook performs and reads back the requested actions; an earlier journaled
        order of this item and candidate is settled first, with no session.
        """
        grant, candidate = self._grant_for(invocation), invocation.candidate
        if candidate is None or grant.invocation_id != invocation.correlation_id:
            return WorkerOutcome("ineligible")
        if self._closure is not None:
            return self._close_with(invocation, budget, grant, candidate)
        receipts: list[str] = []
        try:
            self._source.retrieve_for_verification(candidate, self._verifier_root / f"closure-{workspace_folder(invocation.correlation_id)}")
            receipts.append("candidate-published")
        except CandidateUnavailable:
            pass
        return WorkerOutcome.closed(candidate, tuple(receipts))

    def _close_with(self, invocation: WorkerInvocation, budget: BudgetPolicy, grant: CapabilityGrant,
                    candidate: CandidateRef) -> WorkerOutcome:
        assert self._closure is not None
        try:
            grant.require("git-read", self._target, self._now())
            grant.require("process-control", self._target, self._now())
        except PermissionError:
            return WorkerOutcome("ineligible")
        revision = _revision_of(candidate)
        if revision is None or budget.hard_wall_clock_seconds is None:
            return WorkerOutcome("ineligible")
        earlier = self._closure_orders(invocation, candidate)
        if earlier:
            settled = self._closure.reconcile(invocation, candidate, earlier)
            if settled is not None:
                return WorkerOutcome("closed", candidate, findings=tuple(settled[1]), receipts=tuple(settled[0]))
        clone = self._verifier_root / f"closure-{workspace_folder(invocation.correlation_id)}"
        try:
            if self._handover is not None:
                clone = self._handover.candidate_clone("closure", invocation.correlation_id, invocation.work_identity,
                                                       candidate).path
            else:
                self._source.retrieve_for_verification(candidate, clone)
        except CandidateUnavailable:
            return WorkerOutcome.closed(candidate, ())
        published = CANDIDATE_PUBLISHED_RECEIPT.format(identity=invocation.work_identity, revision=revision)
        if self._preparation is not None:
            prepared = self._preparation.prepare(invocation, clone)
            if isinstance(prepared, WorkerOutcome):
                return prepared
        result = self._process.run(invocation.correlation_id, InvocationRole.CLOSURE, clone, budget.hard_wall_clock_seconds)
        if result.kind != "success":
            return WorkerOutcome(result.kind)
        receipts, findings = self._closure.close(invocation, candidate, self._journal)
        return WorkerOutcome("closed", candidate, findings=tuple(findings),
                             receipts=tuple(dict.fromkeys((published, *receipts))))

    def _closure_orders(self, invocation: WorkerInvocation, candidate: CandidateRef,
                        records: Sequence[Mapping[str, object]] | None = None) -> tuple[Mapping[str, object], ...]:
        """The journaled `closure-ordered` events of this work item and candidate, in journal order."""
        if records is None:
            try:
                records = self._journal.records() if self._journal is not None else ()
            except JournalUnreadable:
                records = ()
        return tuple(record for record in records if record.get("event") == CLOSURE_ORDERED
                     and record.get("work_identity") == invocation.work_identity
                     and record.get("candidate") == _revision_of(candidate))

    def reconcile_closure(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        """Settle a CLOSURE invocation that began a landing and left no outcome line, with no model session.

        Only when its own events include `closure-ordered` and its owner ended with nothing owned alive
        (`effect-unknown`). The settled outcome is journaled (`"reconciled": true`) and read back; otherwise None.
        """
        if invocation.role != str(InvocationRole.CLOSURE) or self._journal is None or self._closure is None \
                or invocation.candidate is None:
            return None
        try:
            records = self._journal.records()
        except JournalUnreadable:
            return None
        own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
        started = [record for record in own if record.get("event") == "invocation-started"]
        if len(started) != 1 or any(record.get("event") == "invocation-outcome" for record in own) \
                or not any(record.get("event") == CLOSURE_ORDERED for record in own):
            return None
        if self.attest_ownership(invocation).kind != EFFECT_UNKNOWN:
            return None
        settled = self._closure.reconcile(invocation, invocation.candidate,
                                          self._closure_orders(invocation, invocation.candidate, records))
        if settled is None:
            return None
        self._journal.append({
            "event": "invocation-outcome", "correlation_id": invocation.correlation_id,
            "work_identity": invocation.work_identity, "role": invocation.role,
            "contract_digest": started[0].get("contract_digest"), "attempt": None, "kind": "closed",
            "candidate": encode_candidate(invocation.candidate), "findings": list(settled[1]),
            "receipts": list(settled[0]), "reconciled": True})
        return self.read_back(invocation)

    def _produce(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        starting_revision = "HEAD"
        if self._preparation is not None:
            prepared = self._preparation.prepare(invocation, None)
            if isinstance(prepared, WorkerOutcome):
                self._outcomes[invocation.correlation_id] = prepared
                return prepared
            starting_revision = prepared
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
        workspace = self._workspaces.allocate(invocation.correlation_id, invocation.work_identity, starting_revision)
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
                # With a worker user the claim is the worker's and the candidate comes only from the intake import.
                revision = (self._source if self._handover is None else self._handover).revision(workspace.path)
                if self._journal is not None:
                    self._journal.append({"event": PUBLICATION_STARTED, "correlation_id": invocation.correlation_id,
                                          "work_identity": invocation.work_identity, "role": invocation.role, "revision": revision})
                if self._handover is not None:
                    self._handover.hand_over(invocation.correlation_id, workspace.path, revision, starting_revision)
                    candidate = self._handover.publish_intake(invocation.correlation_id, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
                else:
                    candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
                if self._preparation is not None:
                    self._preparation.published(invocation, candidate)
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

    @property
    def journal(self) -> InvocationJournal | None:
        """The durable journal this provider writes and reads back, read-only."""
        return self._journal

    def grant_for(self, invocation: WorkerInvocation) -> CapabilityGrant:
        """The grant this provider will launch ``invocation`` under, read-only."""
        return self._grant_for(invocation)

    def candidate_branch(self, invocation: WorkerInvocation) -> str:
        """The branch a producer ``invocation`` publishes to, read-only."""
        return self._candidate_branch(invocation)

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
        return self._verifier_root / f"producer-{workspace_folder(invocation.correlation_id)}"

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
            self._finalize_recovered(invocation, retain)
            return
        if retain:
            self.retained_workspaces[invocation.correlation_id] = workspace.path
            return
        try:
            self._workspaces.cleanup(workspace, None)
        except Exception as error:
            self.cleanup_diagnostics[invocation.correlation_id] = type(error).__name__

    def _finalize_recovered(self, invocation: WorkerInvocation, retain: bool) -> None:
        """After a restart: the PRODUCER worktree at its fixed path, owned by its correlation.

        It is cleaned only when the journaled owner has ended and no owned work runs (`owner-terminated` or
        `effect-unknown`), with the existing cleanup guards and the journaled owner's process id. Every worktree kept
        is reported in `cleanup_diagnostics` with its work item and reason.
        """
        if invocation.correlation_id in self.cleanup_diagnostics or invocation.correlation_id in self.retained_workspaces:
            return  # This process already disposed of it (and reported why it was kept).
        workspace = None if self._recovered_workspace is None else self._recovered_workspace(invocation)
        if workspace is None or self._workspaces is None or not workspace.path.exists():
            return
        reason = self._kept_reason(invocation) if retain else self.attest_ownership(invocation).kind
        if reason in {OWNER_TERMINATED, EFFECT_UNKNOWN}:
            try:
                self._workspaces.cleanup(workspace, self._owner_pid(invocation))
                return
            except Exception as error:
                reason = str(error) or type(error).__name__
        self.retained_workspaces[invocation.correlation_id] = workspace.path
        self.cleanup_diagnostics[invocation.correlation_id] = f"{invocation.work_identity}: {reason}"

    def _kept_reason(self, invocation: WorkerInvocation) -> str:
        """Why a recovered worktree the coordinator keeps is kept, from this correlation's journal: a journaled
        `missing-terminal-result` outcome, else (no outcome) a parked launch."""
        try:
            records = self._journal.records() if self._journal is not None else []
        except JournalUnreadable:
            records = []
        missing = any(record.get("event") == "invocation-outcome" and record.get("kind") == MISSING_TERMINAL_RESULT
                      and record.get("correlation_id") == invocation.correlation_id for record in records)
        return MISSING_TERMINAL_RESULT if missing else "parked"

    def _owner_pid(self, invocation: WorkerInvocation) -> int | None:
        """The owner process id of the correlation's one `invocation-started` record."""
        try:
            records = self._journal.records() if self._journal is not None else []
        except JournalUnreadable:
            records = []
        started = [record for record in records if record.get("event") == "invocation-started"
                   and record.get("correlation_id") == invocation.correlation_id]
        owner = started[0].get("owner") if len(started) == 1 else None
        pid = owner.get("pid") if isinstance(owner, Mapping) else None
        return pid if type(pid) is int else None

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

    def attest_ownership(self, invocation: WorkerInvocation) -> ProcessResult:
        """AC-08: whether an invocation this process did not run has conclusively ended.

        Answered from the durable journal and the process-ownership
        observation only, never from a caller's claim. It is conclusive
        (``owner-terminated``, quiescent) only when the one journaled start
        names an owner process that has ended, no process carrying the
        invocation's marker is alive, and no publication had begun. Anything
        else - no attested owner, an owner still running, owned work still
        active, a publication that may have escaped, an unreadable journal or
        observation - is UNKNOWN.
        """
        def answer(kind: str) -> ProcessResult:
            return ProcessResult(kind, None, kind == OWNER_TERMINATED, BudgetRecord.unknown())

        if self._journal is None or self._ownership is None:
            return answer(OWNER_UNATTESTED)
        try:
            records = self._journal.records()
        except JournalUnreadable:
            return answer(OWNER_UNATTESTED)
        own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
        started = [record for record in own if record.get("event") == "invocation-started"]
        owner = started[0].get("owner") if len(started) == 1 else None
        if not isinstance(owner, Mapping):
            return answer(OWNER_UNATTESTED)
        state = self._ownership.owner_state(owner)
        if state != "terminated":
            return answer(OWNER_ALIVE if state == "alive" else OWNER_UNATTESTED)
        work = self._ownership.owned_work(invocation.correlation_id, owner_token(owner))
        if work is None or work:
            return answer(OWNED_WORK_ACTIVE)
        if any(record.get("event") in (PUBLICATION_STARTED, CLOSURE_ORDERED) for record in own):
            return answer(EFFECT_UNKNOWN)
        return answer(OWNER_TERMINATED)

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
