"""K3 (WO-220403): a composed multi-role launch is bound before it happens.

`FactoryCoordinator` routes one canonical role per stage (K2) and trusts only
an outcome the worker durably reads back (K1). Neither says whether the worker
a *profile* composed is actually bound to that evidence: a journal-less
provider, a provider journaling somewhere the profile never reads, a grant
issued for another role, or a verifier handed a candidate the producer never
durably published would all still launch.

`RoleBindingGuard` is the one WorkerProvider a shared profile hands its
coordinator. Before any launch it requires, from existing records only:

- **durable outcome binding** - the provider writes and reads back the very
  journal the profile composed, that journal is readable and this correlation
  is fresh in it;
- **role authority** - the grant the provider will launch under names this
  invocation, this role, this profile and target, and covers the role's
  operations;
- **exact candidate custody** - the launch matches the prepared execution
  record and its claimed effect, and a verifier or closure candidate is the
  one the recorded producer invocation durably published and read back.

A refusal launches nothing and journals nothing, so the coordinator's own
read-back gate holds the transition.

It also carries the founder amendment at this boundary. A provider/client
exit is not the end of ownership: the worker process adapter returns only once
the process and everything still holding its output have finished. When the
owning call has *returned* in this process - so the provider's own effects
concluded - and the process adapter attests quiescence, a started
invocation with no durable terminal record gets exactly that - a
``missing-terminal-result`` outcome retained against the *original*
invocation in the same journal and read back through the unchanged K1
correlation - before any successor is considered. The unchanged stage then
re-dispatches its role once (``REPLACEMENTS_PER_PHASE``); a further loss in
the same phase is refused at launch and holds. While ownership is not
attested terminal - a restarted process cannot observe a child it did not
start, and a call that raised may have pushed after its process exited -
nothing is retained and nothing replaces it.

The guard owns no state: it reads the store, the journal and the provider,
and writes only the one retained record, through the existing journal port.
"""

from __future__ import annotations

from typing import Callable, Mapping

from alienintent.execution_coordination.application.factory_coordinator import ROLE_BY_STAGE
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, PRODUCER, VERIFIER, WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.invocation_runtime.application.real_worker import correlated_outcome, decode_candidate
from alienintent.invocation_runtime.domain.runtime import JournalUnreadable
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal

BINDING_REFUSED = "binding-refused"
REPLACEMENTS_PER_PHASE = 1
# What each canonical role must be granted; a grant for another role never covers it.
ROLE_OPERATIONS = {
    PRODUCER: frozenset({"process-control", "git-write"}),
    VERIFIER: frozenset({"process-control"}),
    CLOSURE: frozenset({"git-read"}),
}
# Process-adapter answers that attest the owned process and its output holders are gone.
TERMINAL_OWNERSHIP = frozenset({"already-finished"})


def phase_of(invocation: WorkerInvocation) -> str:
    """One role acting on one candidate for one work item: the replacement scope."""
    return "|".join((invocation.work_identity, invocation.role, "" if invocation.candidate is None else invocation.candidate.identity))


def _same_candidate(left: CandidateRef | None, right: CandidateRef | None) -> bool:
    return left is not None and right is not None and (left.kind, left.identity, left.content_digest) == (right.kind, right.identity, right.content_digest)


def _candidate(record: object) -> CandidateRef | None:
    return decode_candidate(record) if isinstance(record, Mapping) else None


class RoleBindingGuard(WorkerProvider):
    def __init__(
        self, worker: object, journal: InvocationJournal | None, store: OperationalStore, profile: str, repository: str,
        now: Callable[[], float], *, replacements_per_phase: int = REPLACEMENTS_PER_PHASE,
    ) -> None:
        self.provider, self._journal, self._store = worker, journal, store
        self._profile, self._repository, self._now = profile, repository, now
        self._replacements = replacements_per_phase
        # Diagnostics only: why a launch was refused, and which retained outcomes this process wrote.
        self.refusals: dict[str, str] = {}
        self.retained: dict[str, str] = {}
        # In-process only, so a restart can never attest another process's call.
        self._concluded: set[str] = set()

    # --- the worker boundary -------------------------------------------------

    def start(self, invocation: WorkerInvocation, context: BiuContract, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        refusal = self.refusal(invocation, context)
        if refusal is not None:
            self.refusals[invocation.correlation_id] = refusal
            return WorkerOutcome(BINDING_REFUSED)
        outcome = self.provider.start(invocation, context, grants, budget)  # type: ignore[attr-defined]
        # Only an owning call that returned has concluded its own effects. One
        # that raised may have pushed or published after its process exited,
        # so it stays UNKNOWN and recovery parks it, as before K3.
        self._concluded.add(invocation.correlation_id)
        durable = self.read_back(invocation)
        return durable if durable is not None and durable.kind == MISSING_TERMINAL_RESULT else outcome

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        if not self._bound():
            return None
        durable = self.provider.read_back(invocation)  # type: ignore[attr-defined]
        return durable if durable is not None else self._retain_missing(invocation)

    def cancel(self, invocation_id: str, reason: str) -> object:
        return self.provider.cancel(invocation_id, reason)  # type: ignore[attr-defined]

    def finalize(self, invocation: WorkerInvocation, retain: bool) -> None:
        finalize = getattr(self.provider, "finalize", None)
        if callable(finalize):
            finalize(invocation, retain)

    # --- binding -------------------------------------------------------------

    def _bound(self) -> bool:
        return self._journal is not None and getattr(self.provider, "journal", None) is self._journal

    def refusal(self, invocation: WorkerInvocation, context: BiuContract | None) -> str | None:
        """Why this launch is not bound, or None when it may start."""
        if self._journal is None or getattr(self.provider, "journal", None) is None:
            return "durable-outcome-binding-missing"
        if not self._bound():
            return "durable-outcome-binding-disconnected"
        try:
            records = self._journal.records()
        except JournalUnreadable:
            return "durable-outcome-binding-unreadable"
        if any(record.get("correlation_id") == invocation.correlation_id for record in records):
            return "durable-outcome-binding-not-fresh"
        if context is None or invocation.contract_digest != context.content_digest:
            return "durable-outcome-binding-contract-miscorrelated"
        return self._role_authority(invocation) or self._custody(invocation, records) or self._replacement(invocation, records)

    def _role_authority(self, invocation: WorkerInvocation) -> str | None:
        operations = ROLE_OPERATIONS.get(invocation.role)
        grant_for = getattr(self.provider, "grant_for", None)
        if operations is None or not callable(grant_for):
            return "role-authority-missing"
        try:
            grant = grant_for(invocation)
        except Exception:  # noqa: BLE001 - an issuer that cannot answer grants nothing
            return "role-authority-missing"
        if (grant.invocation_id, str(grant.role), grant.issuer, grant.target) != (invocation.correlation_id, invocation.role, self._profile, self._repository):
            return "role-authority-miscorrelated"
        try:
            for operation in sorted(operations):
                grant.require(operation, self._repository, int(self._now()))
        except PermissionError:
            return "role-authority-insufficient"
        return None

    def _custody(self, invocation: WorkerInvocation, records: tuple[Mapping[str, object], ...]) -> str | None:
        _, raw = self._store.read_state(self._profile, f"factory:{invocation.work_identity}")
        try:
            stage = LifecycleStage(str(raw.get("stage")))
            prepared, custodied = _candidate(raw.get("invocation_candidate")), _candidate(raw.get("candidate"))
        except (KeyError, TypeError, ValueError):
            return "prepared-launch-miscorrelated"
        effects = [effect for effect in self._store.unresolved_effects(self._profile) if effect.identity == invocation.correlation_id]
        if (
            raw.get("role") != invocation.role or ROLE_BY_STAGE.get(stage) != invocation.role or len(effects) != 1
            or effects[0].payload.get("role") != invocation.role or effects[0].payload.get("work") != invocation.work_identity
        ):
            return "prepared-launch-miscorrelated"
        if prepared != invocation.candidate:
            return "candidate-custody-miscorrelated"
        if invocation.role == PRODUCER:
            return None if invocation.candidate is None else "candidate-custody-miscorrelated"
        candidate = invocation.candidate
        if candidate is None or custodied != candidate:
            return "candidate-custody-missing"
        if candidate.kind is not CandidateKind.SOURCE_REVISION or not candidate.independent_read_back_proven:
            return "candidate-custody-unproven"
        producer = raw.get("producer_correlation")
        branch = getattr(self.provider, "candidate_branch", None)
        if not isinstance(producer, str) or producer == invocation.correlation_id or not callable(branch):
            return "candidate-custody-unattributable"
        published = WorkerInvocation(invocation.work_identity, producer, invocation.contract_digest)
        outcome = correlated_outcome(records, published, branch(published))
        if outcome is None or outcome.kind != "success" or not _same_candidate(outcome.candidate, candidate):
            return "candidate-custody-unattributable"
        return None

    def _replacement(self, invocation: WorkerInvocation, records: tuple[Mapping[str, object], ...]) -> str | None:
        phase = phase_of(invocation)
        lost = sum(1 for record in records if record.get("event") == "invocation-outcome" and record.get("kind") == MISSING_TERMINAL_RESULT and record.get("phase") == phase)
        return "replacement-allowance-exhausted" if lost > self._replacements else None

    # --- conclusive loss -----------------------------------------------------

    def _ownership_terminal(self, invocation: WorkerInvocation) -> tuple[bool, str]:
        """Whether this process's own returned call ended the invocation, as its process adapter attests.

        The adapter is asked only after the owning call returned, so the probe
        never reaches a live process; only ``already-finished`` attests it.
        """
        if invocation.correlation_id not in self._concluded:
            return False, "owning-call-not-concluded"
        observed = self.provider.cancel(invocation.correlation_id, "K3 ownership probe: owning call returned without a durable result")  # type: ignore[attr-defined]
        kind = str(getattr(observed, "kind", observed))
        return getattr(observed, "quiescent", False) is True and kind in TERMINAL_OWNERSHIP, kind

    def _retain_missing(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        """Retain a conclusively missing terminal result against the original invocation."""
        assert self._journal is not None
        try:
            records = self._journal.records()
        except JournalUnreadable:
            return None
        own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
        if [record.get("event") for record in own] != ["invocation-started"]:
            return None
        begun = own[0]
        if begun.get("work_identity") != invocation.work_identity or begun.get("role") != invocation.role:
            return None
        terminal, ownership = self._ownership_terminal(invocation)
        if not terminal:
            return None
        try:
            self._journal.append({
                "event": "invocation-outcome", "correlation_id": invocation.correlation_id,
                "work_identity": invocation.work_identity, "role": invocation.role, "contract_digest": begun.get("contract_digest"),
                "attempt": None, "kind": MISSING_TERMINAL_RESULT, "candidate": None, "findings": [], "receipts": [],
                "ownership": ownership, "phase": phase_of(invocation),
            })
        except (JournalUnreadable, OSError):
            return None
        self.retained[invocation.correlation_id] = ownership
        return self.provider.read_back(invocation)  # type: ignore[attr-defined]
