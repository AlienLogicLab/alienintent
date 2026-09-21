"""PY-10 composition root: the CLI-loadable live proof profile.

`SandboxProfileComposition` (PY-09B) binds credentials, repository, Project and
ingress for one recorded profile. It stops one step short of a profile the
control plane can drain: its snapshot describes Project rows without the BIU
contract, dependency edges or ordering key that release admission and the
scheduler need, and nothing binds a coordinator, a worker provider or a
readiness gate.

This module closes exactly that gap, and reads configuration — here and nowhere
else, per the architecture fitness rule — from the environment, so a run, a
rehearsal and a verifier can each point the same code at their own state.

No secret value is stored, returned in a diagnostic, or retained. The worker
process is launched with an environment this module states in full rather than
the control plane's own, so the credential that publishes a candidate is never
handed to the worker that produced it.
"""

from __future__ import annotations

import atexit
from dataclasses import dataclass
import json
import os
from pathlib import Path
import time
from typing import Callable, Mapping

from alienintent.composition.sandbox_profile import SandboxProfileComposition, load_profile_document
from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy, ContractValidationError
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.ports.work_management import WorkRejected
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.installation.application.doctor import InstallationDoctor
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook

DEFAULT_PROFILE = Path.home() / ".config/alienintent-sandbox/profile.json"
DEFAULT_STATE = Path.home() / ".local/state/alienintent-sandbox/run"
DEFAULT_PROVIDER = "claude"
DEFAULT_WORKER_COMMAND = ("/bin/bash", "worker/run.sh")
PROVIDER_DIMENSIONS = frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"})
GRANT_OPERATIONS = frozenset({"process-control", "git-write"})
GRANT_SECONDS = 3600

_CONTRACT_FIELDS = tuple(name for name in BiuContract.__dataclass_fields__ if name != "content_digest")
_SCALAR_FIELDS = frozenset({"identity", "version", "intent", "retry_policy", "release_policy", "authority_issuer", "budget_policy"})
_SEQUENCE_FIELDS = frozenset(name for name in _CONTRACT_FIELDS if name not in _SCALAR_FIELDS)


# --- upstream descriptor ------------------------------------------------------


class BacklogRejected(WorkRejected):
    """A live Project row cannot safely become an imported BIU."""


@dataclass(frozen=True)
class UpstreamDescriptor:
    """What the Project itself says about a row, before any contract is fetched."""

    identity: str
    contract_path: str
    readiness_digest: str
    dependencies: tuple[str, ...]


def descriptor_from_body(body: str | None) -> UpstreamDescriptor:
    """Read the BIU descriptor the Project item carries.

    The digest here is what upstream recorded when the item was made READY. It
    is deliberately *not* recomputed from the contract this run fetches: that
    comparison is the readiness guard, and deriving both sides from the same
    document would make the guard unable to fail.
    """
    fields: dict[str, str] = {}
    for line in (body or "").splitlines():
        name, separator, value = line.partition(":")
        if separator and name.strip():
            fields[name.strip().lower()] = value.strip()
    identity, contract_path = fields.get("biu", ""), fields.get("contract", "")
    digest = fields.get("readiness_digest", "")
    if not identity or not contract_path or not digest:
        raise BacklogRejected("Project item does not carry a complete BIU descriptor")
    dependencies = tuple(part.strip() for part in fields.get("depends_on", "").split(",") if part.strip())
    return UpstreamDescriptor(identity, contract_path, digest, dependencies)


def contract_from_document(document: Mapping[str, object]) -> BiuContract:
    """Build the immutable contract value from its repository document."""
    if not isinstance(document, Mapping):
        raise BacklogRejected("BIU contract document is not a mapping")
    unknown = sorted(set(document) - set(_CONTRACT_FIELDS) - {"task", "notes"})
    if unknown:
        raise BacklogRejected(f"BIU contract document carries an unknown field: {unknown[0]}")
    budget = document.get("budget_policy") or {}
    if not isinstance(budget, Mapping):
        raise BacklogRejected("BIU contract budget policy is not a mapping")
    values: dict[str, object] = {}
    for name in _CONTRACT_FIELDS:
        if name == "budget_policy":
            continue
        value = document.get(name)
        values[name] = tuple(value) if name in _SEQUENCE_FIELDS and isinstance(value, list) else value
    try:
        return BiuContract(budget_policy=BudgetPolicy(
            hard_required_dimensions=tuple(budget.get("hard_required_dimensions") or ()),
            maximum_attempts=int(budget.get("maximum_attempts", 1)),
            hard_wall_clock_seconds=budget.get("hard_wall_clock_seconds"),
            retry_limit=int(budget.get("retry_limit", 0)),
            concurrency_limit=budget.get("concurrency_limit"),
            cancellation_limit=budget.get("cancellation_limit"),
        ), **values)  # type: ignore[arg-type]
    except (ContractValidationError, TypeError, ValueError) as error:
        raise BacklogRejected(f"BIU contract document is not a valid contract: {error}") from error


# --- live backlog composition -------------------------------------------------


class SandboxBacklogComposition(SandboxProfileComposition):
    """Resolve the live Project into work the control plane can actually admit.

    Everything the scheduler and the release guard need is observed upstream:
    the identity, contract location, readiness digest and dependency edges come
    from the Project item, the ordering key is the moment the Status value
    itself became READY, and the contract is fetched from the repository with
    the installation credential.
    """

    def __init__(
        self,
        document: Mapping[str, object],
        database: Path,
        notify: Callable[[str], None],
        transport: object | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.item_ids: dict[str, str] = {}
        self.item_titles: dict[str, str] = {}
        self.ready_since: dict[str, str] = {}
        self.imported: list[dict[str, str]] = []
        self._documents: dict[str, BiuContract] = {}
        super().__init__(document, database, self._contract_for_row, notify, transport, clock)  # type: ignore[arg-type]

    # --- snapshot ------------------------------------------------------------

    def project_snapshot(self) -> tuple[Mapping[str, object], ...]:
        """Live Project items, ordered by the upstream READY-entry time.

        The plan fixes the FIFO key as READY-entry time observed through the
        ACL. Projects v2 timestamps a single-select value when that value
        changes, so the Status value's own `updatedAt` *is* that moment. Items
        whose Status changed within the same recorded second fall back to a
        deterministic receipt order on the item identity, so ordering among
        equals is never arbitrary.
        """
        schema = self.projects.schema()
        observed = [item for item in self.projects.items() if item.status in self.profile.lifecycle_statuses]
        observed.sort(key=lambda item: (item.status_updated_at or "", item.item_id))
        rows: list[Mapping[str, object]] = []
        self.item_ids, self.item_titles, self.ready_since, self.imported = {}, {}, {}, []
        for item in observed:
            descriptor = descriptor_from_body(item.body)
            self.item_ids[descriptor.identity] = item.item_id
            self.item_titles[descriptor.identity] = item.title or descriptor.identity
            self.ready_since[descriptor.identity] = item.status_updated_at or ""
            self.imported.append({
                "identity": descriptor.identity, "item": item.item_id, "priority": item.priority or "",
                "ready_since": item.status_updated_at or "", "contract": descriptor.contract_path,
            })
            rows.append({
                "identity": descriptor.identity, "repository": self.profile.repository,
                "membership": True, "complete": True, "status": item.status,
                "priority": item.priority, "dependencies": list(descriptor.dependencies),
                "contract": descriptor.contract_path, "contract_digest": descriptor.readiness_digest,
                "readiness": f"project-item {item.item_id} READY at {item.status_updated_at or 'unrecorded'}",
                "wave": "1", "source_version": schema.project_id,
            })
        return tuple(rows)

    # --- per-item contract ---------------------------------------------------

    def _contract_for_row(self, row: Mapping[str, object]) -> BiuContract:
        """Fetch this row's own contract and refuse any disagreement with upstream."""
        location = str(row.get("contract") or "")
        identity = str(row.get("identity") or "")
        if not location:
            raise BacklogRejected("imported row names no BIU contract document")
        contract = self._documents.get(location)
        if contract is None:
            try:
                document = json.loads(self.repository.contents(location))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise BacklogRejected("BIU contract document is not readable JSON") from error
            contract = contract_from_document(document)
            self._documents[location] = contract
        if contract.identity != identity:
            raise BacklogRejected("BIU contract document does not name the imported work item")
        if tuple(contract.dependencies) != tuple(row.get("dependencies") or ()):
            raise BacklogRejected("upstream dependency edges disagree with the BIU contract")
        return contract

    # --- projection ----------------------------------------------------------

    def project_projection_write(self, identity: str, field: str, state: str, revision: int) -> int:
        """Project onto the Project item the imported identity was read from."""
        item = self.item_ids.get(identity)
        if item is None:
            raise BacklogRejected("no live Project item is bound to this work identity")
        return self.projects.write_status(item, state, revision)


# --- decision projection ------------------------------------------------------


class ProjectDecisionNotifier(DecisionNotifier):
    """Project a decision request into the Project the profile targets.

    The escalation is written out in full and read back, so "a decision was
    escalated with complete context" is a fact recorded outside this process
    rather than a claim in its own log.
    """

    PREFIX = "DECISION REQUIRED"

    def __init__(self, projects: GitHubProjectsV2Directory) -> None:
        self._projects = projects
        self.projected: dict[str, str] = {}

    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        title = f"{self.PREFIX} — {escalation.work_item} @ v{escalation.biu_version}"
        try:
            item = self._projects.add_draft_item(title, decision_body(escalation))
            observed = self._projects.read_status(item)
        except Exception:  # noqa: BLE001 - delivery health is reported, never raised
            return DeliveryHealth(False, "decision notification projection unavailable")
        if observed.item_id != item or observed.title != title:
            return DeliveryHealth(False, "decision notification projection unconfirmed")
        self.projected[escalation.work_item] = item
        return DeliveryHealth(True, f"confirmed as project item {item}")


def decision_body(escalation: HumanDecisionRequired) -> str:
    """Every field of the escalation, so the projected request is complete."""
    return "\n".join([
        f"work_item: {escalation.work_item}", f"biu_version: {escalation.biu_version}",
        f"profile: {escalation.profile}", f"project: {escalation.project}", "",
        f"decision: {escalation.decision}", f"reason: {escalation.reason}",
        f"recommendation: {escalation.recommendation}", f"cost_of_waiting: {escalation.cost_of_waiting}", "",
        "options:", *(f"  - {value}" for value in escalation.options),
        "tradeoffs:", *(f"  - {value}" for value in escalation.tradeoffs),
        "authorizations:", *(f"  - {value}" for value in escalation.authorizations),
        "affected_requirements:", *(f"  - {value}" for value in escalation.affected_requirements),
        "affected_architecture:", *(f"  - {value}" for value in escalation.affected_architecture),
    ])


# --- run profile --------------------------------------------------------------


class SandboxRunProfile:
    """The object `alienintent --profile-factory` drives: one live sandbox run."""

    def __init__(
        self,
        composition: SandboxBacklogComposition,
        state_root: Path,
        checkout: Path,
        *,
        provider: str = DEFAULT_PROVIDER,
        worker_command: tuple[str, ...] = DEFAULT_WORKER_COMMAND,
        worker_environment: Mapping[str, str] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.composition = composition
        self.name = composition.profile.profile
        self.store = composition.store
        self.work = composition.work
        self.provider = provider
        self.state_root, self.checkout = state_root, checkout
        self.workspace_root = state_root / "workspaces"
        self.verifier_root = state_root / "verifier-evidence"
        self.producer_read_back_root = state_root / "producer-read-back"
        self.artifact_root = state_root / "artifacts"
        for directory in (self.workspace_root, self.verifier_root, self.producer_read_back_root, self.artifact_root):
            directory.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self.worker_process = CliWorkerProvider(
            provider, worker_command[0], tuple(worker_command[1:]), "bypassPermissions",
            PROVIDER_DIMENSIONS, environment=worker_environment,
        )
        self.worker = RealWorkerProvider(
            self.worker_process, GitSourceControl(), checkout, "origin", self.candidate_branch,
            self.producer_read_back_root, self.grant, composition.profile.repository,
            GitWorktreeAdapter(checkout, self.workspace_root), ReservationBook(1, 2),
            now=clock, sleep=time.sleep,
        )
        self.notifier = ProjectDecisionNotifier(composition.projects)
        self.coordinator = FactoryCoordinator(
            self.store, self.work, self.worker,
            LocalArtifactStore(self.artifact_root, self.verifier_root), self.name,
            automatic_release=composition.profile.automatic_release, notifier=self.notifier,
        )
        self.doctor = composition.doctor(self.workspace_root, checkout, self.worker_process, provider)
        self.ingress_route = ""
        self._resident: object | None = None

    # --- per-invocation authority and custody --------------------------------

    @staticmethod
    def candidate_branch(invocation: WorkerInvocation) -> str:
        return f"candidate/{ref_safe(invocation.correlation_id)}"

    def grant(self, invocation: WorkerInvocation) -> CapabilityGrant:
        """One capability grant per dispatch, naming the invocation it authorizes."""
        return CapabilityGrant(
            f"py10-{invocation.work_identity}", "1", invocation.correlation_id, InvocationRole.PRODUCER,
            self.name, self.composition.profile.repository, GRANT_OPERATIONS, int(self._clock()) + GRANT_SECONDS,
        )

    # --- residency -----------------------------------------------------------

    def become_resident(self) -> str:
        """Bind the ingress for this process's whole lifetime.

        The binding is held, not just entered: dropping it would let it be
        finalized, which shuts the server down and leaves the doctor's
        transport probe unable to reach the route this process is supposed to
        be answering on. Release is registered with `atexit` rather than left
        to garbage collection, because the ingress thread is a daemon: by the
        time an unreferenced binding would be collected, the thread its
        shutdown waits on is already stopped and the wait never ends. A
        process that is killed rather than exiting — which this proof does
        deliberately — releases the socket to the operating system instead,
        which is why the ingress can be rebound immediately afterwards.
        """
        if self._resident is None:
            binding = self.composition.resident_ingress()
            self.ingress_route = binding.__enter__()
            self._resident = binding
            atexit.register(self.release_residency)
        return self.ingress_route

    def release_residency(self) -> None:
        binding, self._resident = self._resident, None
        if binding is not None:
            binding.__exit__(None, None, None)

    # --- readiness -----------------------------------------------------------

    def readiness(self) -> bool:
        """`run` refuses autonomous start unless the live doctor passes."""
        return isinstance(self.doctor, InstallationDoctor) and self.doctor.run().ready


# --- environment --------------------------------------------------------------


def _path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else default


def worker_environment(state_root: Path) -> dict[str, str]:
    """The exact environment a worker process runs in.

    It is stated rather than inherited so no control-plane credential — the
    `GIT_CONFIG_*` credential rewrite that lets the control plane publish and
    read back a candidate, in particular — reaches the worker. A worker
    commits; only the control plane publishes.
    """
    inherited = {name: os.environ[name] for name in ("PATH", "HOME", "LANG", "LC_ALL", "TERM", "SHELL", "USER") if name in os.environ}
    return inherited | {
        "TMPDIR": str(state_root / "worker-tmp"),
        "GIT_AUTHOR_NAME": "AlienIntent sandbox worker", "GIT_AUTHOR_EMAIL": "worker@alienintent.invalid",
        "GIT_COMMITTER_NAME": "AlienIntent sandbox worker", "GIT_COMMITTER_EMAIL": "worker@alienintent.invalid",
    }


def compose(state_root: Path | None = None) -> SandboxRunProfile:
    """Build the run profile from the recorded environment."""
    profile_path = _path("ALIENINTENT_SANDBOX_PROFILE", DEFAULT_PROFILE)
    root = state_root or _path("ALIENINTENT_SANDBOX_STATE", DEFAULT_STATE)
    root.mkdir(parents=True, exist_ok=True)
    (root / "worker-tmp").mkdir(parents=True, exist_ok=True)
    checkout = _path("ALIENINTENT_SANDBOX_CHECKOUT", root / "repository")
    command = os.environ.get("ALIENINTENT_SANDBOX_WORKER_COMMAND")
    worker_command = tuple(json.loads(command)) if command else DEFAULT_WORKER_COMMAND
    ingress_log = root / "ingress-notifications.jsonl"

    def notify(notification: str) -> None:
        with ingress_log.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps({"at": time.time(), "notification": notification}) + "\n")

    composition = SandboxBacklogComposition(load_profile_document(profile_path), root / "state.sqlite", notify)
    return SandboxRunProfile(
        composition, root, checkout,
        provider=os.environ.get("ALIENINTENT_SANDBOX_PROVIDER", DEFAULT_PROVIDER),
        worker_command=worker_command,
        worker_environment=worker_environment(root),
    )


def profile() -> SandboxRunProfile:
    """Zero-argument factory for `alienintent --profile-factory`."""
    run = compose()
    if os.environ.get("ALIENINTENT_SANDBOX_INGRESS", "resident") == "resident":
        # The doctor's transport probe requires the configured public route to
        # reach *this* process, so a live profile is resident for its whole
        # lifetime. The server thread is a daemon: process exit — or a crash —
        # closes it without a shutdown handshake.
        run.become_resident()
    return run
