"""Project work registry composition: one project database, one configured clone per repository, every profile.

The project-level configuration entry is looked up by the project string already threaded through UpstreamProfile.
It names the one project database file, maps each repository name to its one configured clone (with the remote
that clone publishes to, named explicitly, and the default and packets branches that retain packet commits), names
where compiled packets are written, and lists every configured profile of the project with its own operational
database path. Each profile's database is opened read-only in effect (it must already exist at the current schema,
so opening it writes nothing) for the compiler's migration check and `work migrate`. The same WorkIdentityService,
repository adapter and publisher are handed to every client of the project. The optional `readiness` object configures
`work assess`: its own assessment store and evidence folder, and the Agent Ready executable and provider; without it
the project has no assessment service. The optional `github` object configures `work link` and `work display`: the
one repository and board the project's work items are linked to, and the GitHub App installation that writes them
(its private key file named directly); without it the project has no link service. With both, the registry has a
READY view of that board (`ready_view`, `ready_refusals`, `repair_displays`): each READY row is built only from the
card's registered work record, and the view's attention items are kept in the `readiness` store and evidence folder.
With `readiness`, `work authorize` (`authorization`) records release records on that store under profile `registry`
and its evidence in that folder; the starting revision is checked in the pointer repository's configured clone
against its `default_branch`, the values the release gate for registry items is composed with. With `readiness`,
`work record-completed` (`completion`) records an existing item's completed work: its evidence in that folder,
landings checked the same way, and the `registry` coordinator's record read from that store. With the READY view,
`coordinator(worker, artifacts)` composes the existing FactoryCoordinator over it on the `readiness` store (profile
`registry`) with that release gate, the WIP limit read from the Factory Director host configuration on every
admission and `completion`'s reader of recorded completions for dependencies; the work items' displays carry the
IMPLEMENT and VERIFY cycle counts of that coordinator's state.
With `readiness` and a configuration loaded from its file, `context` (WorkContext) assembles each role's context
package from those same records; `work_context_profile` is the read-only worker profile its `work context` command
runs under, opening the work and `readiness` databases with SQLite `mode=ro`.

Configuration document (JSON):

    {"schema_version": 1, "projects": {"<project>": {
        "database": "<path to the project work database>",
        "repositories": {"<name>": {"clone": "<path>", "remote": "origin", "default_branch": "main",
                                    "packets_branch": "alienintent/work-packets"}},
        "packets": {"repository": "<name>", "directory": "work-packets"},
        "profiles": {"<profile>": "<path to that profile's operational state.sqlite>"},
        "readiness": {"database": "<path>", "evidence_root": "<path>", "executable": "<agent-ready path>",
                      "provider": "<provider>"},
        "github": {"repository": "<owner>/<name>", "application_id": <int>, "installation_id": <int>,
                   "private_key_path": "<path to the App private key file>",
                   "project": {"project_id": "PVT_...", "project_number": <int>, "organization": "<owner>",
                               "status_field_id": "<id>", "priority_field_id": "<id>"}}}}}
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sysconfig
import time
from types import SimpleNamespace
from uuid import uuid4

from alienintent.composition.readiness import assessment_environment, compose_producer, resolve_binding
from alienintent.composition.sandbox_profile import APP_KEY_REFERENCE
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.application.initial_compilation_service import PacketLocation, WorkRegistration
from alienintent.context_assembly.application.packet_assessment import PacketAssessment
from alienintent.context_assembly.application.work_authorization import WorkAuthorization
from alienintent.context_assembly.application.work_completion import WorkCompletion
from alienintent.context_assembly.application.work_context import ContextCommand, WorkContext
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_link import WorkLink
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import fingerprint
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.context_assembly.domain.work_identity import STATES, GitReadFailed, valid_path
from alienintent.context_assembly.domain.work_link import LinkResult, render
from alienintent.context_assembly.ports.work_item_repository import (
    PacketRef, PublicationFailed, RefPublisher, RepositoryLocation)
from alienintent.control_plane.adapters.attention_repository import DurableAttentionRepository
from alienintent.control_plane.application.attention import AttentionService
from alienintent.control_plane.domain.attention import AttentionOrigin
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters import assessment_consumer
from alienintent.execution_coordination.adapters.assessment_consumer import RetainedAssessmentConsumer
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory
from alienintent.execution_coordination.adapters.github_repository_api import GitHubRepositoryApi
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.release_admission import (
    GitRevisionResolver, StoredReleaseAuthorizations)
from alienintent.execution_coordination.adapters.sqlite_store import SCHEMA_VERSION, SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.execution_coordination.ports.project_directory import ProjectItemState
from alienintent.execution_coordination.ports.worker_provider import WorkerProvider
from alienintent.installation.adapters.app_jwt import app_assertion
from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
from alienintent.installation.application.installation_credentials import InstallationCredentials
from alienintent.installation.domain.app_credentials import AppIdentity
from alienintent.installation.domain.project_identity import ProjectAddress
from alienintent.installation.ports.github_transport import GitHubTransport
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.runtime import INVOCATION_MARKER, INVOCATION_OWNER_MARKER, owner_token
from alienintent.invocation_runtime.ports import source_control
from alienintent.invocation_runtime.ports.source_control import PublishRef, SourceControl


# The READY view: its refusal kinds, the owner of each, and the fixed values of every attention origin it records.
READY_VIEW = "ready-view"
NO_LINK, NOT_ELIGIBLE, ASSESSMENT_MISSING = "NO_LINK", "NOT_ELIGIBLE", "ASSESSMENT_MISSING"
CONTRACT_INVALID, DISPLAY_DIFFERS, ROW_REFUSED = "CONTRACT_INVALID", "DISPLAY_DIFFERS", "ROW_REFUSED"
WORK_PREPARATION, OPERATOR = "Work Preparation", "Operator"
OWNERS = {NO_LINK: WORK_PREPARATION, NOT_ELIGIBLE: WORK_PREPARATION, ASSESSMENT_MISSING: WORK_PREPARATION,
          CONTRACT_INVALID: WORK_PREPARATION, DISPLAY_DIFFERS: WORK_PREPARATION, ROW_REFUSED: OPERATOR}
# The shared Factory Director host configuration whose `wipLimit` is the WIP limit (bin/alienintent.mjs reads it too).
HOST_CONFIGURATION = Path("~/.config/alienintent/factory-director-host.json")
MAX_SAFE_INTEGER = 2 ** 53 - 1  # the Number.isSafeInteger bound of bin/alienintent.mjs; a JSON 1.0 is not an integer here


class ConfigurationInvalid(ValueError):
    """The project-level configuration entry is missing or malformed; nothing was opened."""


@dataclass(frozen=True)
class ReadinessConfiguration:
    """`work assess`: its own assessment database and evidence folder, the Agent Ready executable and provider."""
    database: Path
    evidence_root: Path
    executable: Path
    provider: str


@dataclass(frozen=True)
class GitHubConfiguration:
    """`work link` and `work display`: the one repository and board, and the App installation that writes them."""
    repository: str
    application_id: int
    installation_id: int
    private_key_path: Path
    project: ProjectAddress


@dataclass(frozen=True)
class ProjectConfiguration:
    project: str
    database: Path
    repositories: Mapping[str, RepositoryLocation]
    packets_repository: str
    packets_directory: str
    profiles: Mapping[str, Path]
    readiness: ReadinessConfiguration | None = None
    github: GitHubConfiguration | None = None
    path: Path | None = None  # The configuration file it was loaded from (load_project_configuration), if any.


def project_configuration(document: object, project: str) -> ProjectConfiguration:
    """The entry for `project`; every field is required and checked before anything is opened."""
    try:
        if not isinstance(document, dict) or document.get("schema_version") != 1:
            raise ConfigurationInvalid("schema_version")
        entry = document["projects"][project]
        repositories = {name: RepositoryLocation(Path(value["clone"]), value["remote"], value["default_branch"],
                                                 value["packets_branch"])
                        for name, value in entry["repositories"].items()}
        packets = entry["packets"]
        profiles = {name: Path(path) for name, path in entry["profiles"].items()}
        readiness = _readiness(entry["readiness"]) if "readiness" in entry else None
        github = _github(entry["github"]) if "github" in entry else None
        configuration = ProjectConfiguration(project, Path(entry["database"]), repositories, packets["repository"],
                                             packets["directory"], profiles, readiness, github)
    except ConfigurationInvalid:
        raise
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ConfigurationInvalid(f"project {project}: {type(error).__name__}: {error}") from None
    if configuration.packets_repository not in repositories or not profiles or not all(
            isinstance(name, str) and name for name in [*repositories, *profiles]) \
            or not isinstance(configuration.packets_directory, str) or not valid_path(configuration.packets_directory):
        raise ConfigurationInvalid(f"project {project}: packets repository, directory and profiles must be configured")
    if readiness is not None and readiness.database.resolve() in {
            path.resolve() for path in (configuration.database, *profiles.values())}:
        raise ConfigurationInvalid(f"project {project}: the readiness database must be its own database")
    return configuration


def _readiness(value: object) -> ReadinessConfiguration:
    if not isinstance(value, dict) or set(value) != {"database", "evidence_root", "executable", "provider"} \
            or not all(isinstance(v, str) and v for v in value.values()):
        raise ConfigurationInvalid("readiness needs exactly database, evidence_root, executable and provider")
    return ReadinessConfiguration(Path(value["database"]), Path(value["evidence_root"]), Path(value["executable"]),
                                  value["provider"])


def _github(value: object) -> GitHubConfiguration:
    fields = {"repository", "application_id", "installation_id", "private_key_path", "project"}
    if not isinstance(value, dict) or set(value) != fields or not isinstance(value["repository"], str) \
            or value["repository"].count("/") != 1 or not all(value["repository"].split("/")) \
            or not all(type(value[name]) is int and value[name] > 0 for name in ("application_id", "installation_id")) \
            or not isinstance(value["private_key_path"], str) or not value["private_key_path"] \
            or not isinstance(value["project"], dict):
        raise ConfigurationInvalid("github needs exactly repository, application_id, installation_id, "
                                   "private_key_path and project")
    return GitHubConfiguration(value["repository"], value["application_id"], value["installation_id"],
                               Path(value["private_key_path"]), ProjectAddress(**value["project"]))


def load_project_configuration(path: Path, project: str) -> ProjectConfiguration:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigurationInvalid(f"{path}: {type(error).__name__}") from None
    return replace(project_configuration(document, project), path=Path(path).resolve())


def wip_limit(path: Path) -> int | None:
    """The `wipLimit` of the host configuration at `path`, opened and parsed on every call: an integer of at least 1
    (not a boolean), else None for a missing, unreadable or invalid file or value. Nothing is kept between calls and
    there is no default."""
    try:
        document = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = document.get("wipLimit") if isinstance(document, dict) else None
    return value if type(value) is int and 1 <= value <= MAX_SAFE_INTEGER else None


def read_only_store(path: Path) -> OperationalStore:
    """A configured profile's existing operational database at the current schema: opening it writes nothing.
    A missing file or another schema is refused rather than created or migrated."""
    if not Path(path).is_file():
        raise ConfigurationInvalid(f"profile database {path} does not exist")
    preflight = SQLiteOperationalStore.preflight(Path(path))
    if preflight.current_version != SCHEMA_VERSION or preflight.migration is not None:
        raise ConfigurationInvalid(f"profile database {path} is not at schema {SCHEMA_VERSION}")
    return SQLiteOperationalStore(Path(path))


@dataclass(frozen=True)
class ReadyRefusal:
    """A READY card the view did not import (or whose display differs from its record), with its one open attention
    item. `recorded` is False when that item could not be written; `cleared` marks an open item whose defect the last
    snapshot no longer observed."""
    card: str
    kind: str
    owner: str
    reason: str
    attention: str | None
    recorded: bool
    cleared: bool = False


class _Refused(Exception):
    def __init__(self, kind: str, reason: str) -> None:
        self.kind, self.reason = kind, reason
        super().__init__(f"{kind}: {reason}")


def _step(kind: str, call):
    """One step of building a READY row; any failure of it (an unreadable database, store or packet) is that step's
    refusal naming the error, so the other cards continue."""
    try:
        return call()
    except Exception as error:
        raise _Refused(kind, f"{type(error).__name__}: {error}") from error


class SourceControlRefPublisher(RefPublisher):
    """Binds Work Preparation's RefPublisher to the one source-control `publish_refs` operation; no other code pushes
    packet refs. Composition owns this bridge so context_assembly never imports the invocation runtime."""

    def __init__(self, source_control: SourceControl) -> None:
        self._source_control = source_control

    def publish(self, clone: Path, remote: str, refs: tuple[PacketRef, ...]) -> None:
        try:
            values = tuple(PublishRef(r.ref, r.commit, r.force) for r in refs)
        except ValueError as error:  # A ref value publish_refs would refuse to push.
            raise PublicationFailed(tuple(r.ref for r in refs), str(error)) from error
        try:
            self._source_control.publish_refs(clone, remote, values)
        except source_control.PublicationFailed as error:
            raise PublicationFailed(error.refs, str(error)) from error


class WorkRegistry:
    """The one work identity service of a project, with its repository adapter, publisher and the operator's
    work-record operations (`records`); `registration` is the compiler's."""

    def __init__(self, configuration: ProjectConfiguration, source_control: SourceControl | None = None,
                 transport: GitHubTransport | None = None, host_configuration: Path = HOST_CONFIGURATION) -> None:
        self.configuration = configuration
        self.host_configuration = host_configuration
        self.profile_stores = {name: read_only_store(path) for name, path in sorted(configuration.profiles.items())}
        self.items = SQLiteWorkItemRepository(configuration.database, configuration.repositories)
        self.source_control = source_control if source_control is not None else GitSourceControl()
        self.publisher = SourceControlRefPublisher(self.source_control)
        self.identities = WorkIdentityService(self.items, self.publisher, configuration.repositories,
                                              self.profile_stores)
        self.registration = WorkRegistration(
            self.identities, self.items, self.publisher,
            PacketLocation(configuration.packets_repository, configuration.packets_directory,
                           configuration.repositories[configuration.packets_repository]),
            self.profile_stores)
        self.records = WorkRecordService(self.identities, self.items, self.items.read_packet)
        self.assessment = self._assessment(configuration) if configuration.readiness is not None else None
        self.authorization = self._authorization(configuration) if self.assessment is not None else None
        self.completion = self._completion(configuration) if self.assessment is not None else None
        self.links = self._links(configuration.github, transport) if configuration.github is not None else None
        self.ready_view = self._ready_view(configuration) if self.links is not None and self.assessment is not None \
            else None
        # Each role's context package (unit 6c-1) over the `readiness` store and evidence folder; its command names
        # the configuration file, so a configuration not loaded from a file has none.
        self.context = _work_context(configuration, self.records, self.items, self.assessment.consumer) \
            if self.assessment is not None and configuration.path is not None else None

    def _links(self, github: GitHubConfiguration, transport: GitHubTransport | None) -> WorkLink:
        """`work link` and `work display` over the same constructors SandboxProfileComposition uses, without its
        profile document; nothing is read or sent until a command runs."""
        transport = transport or UrllibGitHubTransport()
        credentials = InstallationCredentials(
            AppIdentity(github.application_id, github.installation_id, APP_KEY_REFERENCE),
            ProtectedLocalFileSecretProvider({APP_KEY_REFERENCE: github.private_key_path}), transport, time.time,
            app_assertion)
        return WorkLink(self.records, self.items,
                        GitHubRepositoryApi(github.repository, transport, credentials.authorization),
                        GitHubProjectsV2Directory(github.project, transport, credentials.authorization), credentials,
                        self.cycles if self.assessment is not None else None)

    def cycles(self, identity: str) -> tuple[int | None, int | None] | None:
        """The IMPLEMENT and VERIFY cycle counts of the work item's recorded `registry` coordinator state on the
        `readiness` store, decoded by the coordinator's own decoder; None when it has no state."""
        _, raw = self.assessment.consumer.store.read_state("registry", f"factory:{identity}")
        if not raw:
            return None
        state = FactoryCoordinator.decode(raw)
        return state.implement_cycles, state.verify_cycles

    def coordinator(self, worker: WorkerProvider, artifacts: LocalArtifactStore) -> FactoryCoordinator:
        """The existing FactoryCoordinator over the READY view on the `readiness` store under profile `registry`, with
        the caller's worker and artifacts. Nothing is released automatically: a work item becomes eligible only through
        `release_and_start`, and the release gate re-checks its release record against the packets repository's clone
        and default branch (what `work authorize` checks) before every PRODUCER. The WIP limit is read on every
        admission."""
        if self.ready_view is None:
            raise ConfigurationInvalid("the coordinator needs both the github and readiness entries")
        configuration = self.configuration
        packets, store = configuration.repositories[configuration.packets_repository], self.assessment.consumer.store
        gate = ReleasePreconditionGate(StoredReleaseAuthorizations(store, "registry"),
                                       GitRevisionResolver({configuration.github.repository: packets.clone}),
                                       packets.default_branch)
        return FactoryCoordinator(store, self.ready_view, worker, artifacts, "registry",
                                  automatic_release=False, release_gate=gate,
                                  wip_limit=lambda: wip_limit(self.host_configuration),
                                  recorded_completion=self.completion.recorded)

    def _ready_view(self, configuration: ProjectConfiguration) -> GitHubProjectsWorkManagement:
        """The READY view of board #1: profile `registry`, each formal workflow state mapped to itself, no projection
        fields or writes; rows from `_ready_snapshot` and each row's contract the one that snapshot read for it.
        Attention items live in the `readiness` store and evidence folder, under the assessment profile."""
        consumer = self.assessment.consumer
        project, profile = configuration.project, consumer.profile
        self._attention = AttentionService(
            DurableAttentionRepository(consumer.store, consumer.repository, project=project, profile=profile,
                                       invocation=READY_VIEW),
            project=project, profile=profile, clock=lambda: datetime.now(UTC).isoformat(),
            next_id=lambda: str(uuid4()), resolvers=())
        # Fixed, so the content-addressed repository answers the same source Ref in every process.
        self._definition = Ref(project, profile, READY_VIEW + "/definition",
                               "sha256:" + sha256(b"alienintent.composition.work_registry:ready-view").hexdigest(),
                               "python:alienintent.composition.work_registry")
        self._observed: tuple[tuple[str, str, str], ...] = ()  # (card, kind, reason) refused by the snapshot
        self._differs: tuple[tuple[str, str], ...] = ()  # (card, item id) whose display differs from its record
        self._contracts: dict[str, BiuContract] = {}
        self._board_read = False  # Whether the last snapshot read the whole board; only then can a defect clear.
        return GitHubProjectsWorkManagement("registry", configuration.github.repository,
                                            {state: state for state in STATES}, {}, self._ready_snapshot,
                                            lambda row: self._contracts[str(row["card"])])

    def _ready_snapshot(self) -> tuple[dict[str, object], ...]:
        """The READY column of the whole board in the sandbox reader's order (READY-entry time, then card id), one
        row per card built from its work record; nothing is written to GitHub."""
        self._observed, self._differs, self._contracts, self._board_read = (), (), {}, False
        cards = sorted((card for card in self.links.board.items() if card.status == "READY"),
                       key=lambda card: (card.status_updated_at or "", card.item_id))
        rows, observed, differs = [], [], []
        for card in cards:
            try:
                rows.append(self._ready_row(card, differs))
            except _Refused as refused:
                observed.append((card.item_id, refused.kind, refused.reason))
        self._observed, self._differs, self._board_read = tuple(observed), tuple(differs), True
        return tuple(rows)

    def _ready_row(self, card: ProjectItemState, differs: list[tuple[str, str]]) -> dict[str, object]:
        linked = _step(NO_LINK, lambda: self.items.find_by_card(card.item_id))
        if linked is None:
            raise _Refused(NO_LINK, "no work item is linked to this card")
        record = _step(NOT_ELIGIBLE, lambda: self.records.show(linked.id))
        item = record.item if record is not None else None
        if item is None or item.retired or item.pointer is None:
            raise _Refused(NOT_ELIGIBLE, "no record" if item is None else "retired" if item.retired else
                           "no packet pointer")
        history = _step(ASSESSMENT_MISSING, lambda: self.assessment.consumer.history(item.id))
        assessed = next((entry for entry in history if item.assessment_ref is not None
                         and entry["raw_ref"] == asdict(item.assessment_ref)), None)
        if assessed is None:
            raise _Refused(ASSESSMENT_MISSING, "no retained assessment is the row's assessment_ref")
        if assessed["input_fingerprint"] != fingerprint(item.id, item.pointer):
            raise _Refused(ASSESSMENT_MISSING, "the assessment is not of the current pointer")
        outcome = assessed["outcome"] or {}
        if outcome.get("failure_class") or outcome.get("disposition") != "READY":
            raise _Refused(ASSESSMENT_MISSING, f"outcome {outcome.get('disposition') or outcome.get('failure_class')}")
        contract = _step(CONTRACT_INVALID, lambda: contract_block(record.packet, item.id))
        rendered = render(item, self.cycles(item.id))  # Compared with the card's text, never read for anything else.
        if (card.title, card.body or "") != (rendered.title, rendered.body):
            differs.append((card.item_id, item.id))
        self._contracts[card.item_id] = contract
        return {"complete": True, "membership": True, "repository": self.configuration.github.repository,
                "status": card.status, "priority": card.priority, "identity": item.id,
                "contract_digest": contract.content_digest, "readiness": item.assessment_ref.logical_id,
                "dependencies": list(contract.dependencies), "card": card.item_id}

    def ready_refusals(self) -> tuple[ReadyRefusal, ...]:
        """After `ready_view.import_ready_snapshot()`: every refusal of that snapshot and of its translation, and every
        display difference, each with its one open attention item (ensured, so a rerun finds the same item); then
        every open READY-view item whose defect was not observed again, listed as cleared — only when that snapshot
        read the whole board. Nothing is resolved."""
        observed = [*self._observed,
                    *((card, DISPLAY_DIFFERS, f"work item {identity}") for card, identity in self._differs),
                    *((card, ROW_REFUSED, reason) for card, reason in self.ready_view.last_refusals)]
        refusals = [self._ensure(card, kind, reason) for card, kind, reason in observed]
        seen = {(refusal.card, refusal.kind) for refusal in refusals}
        try:
            pending = self._attention.list_pending() if self._board_read else ()
        except Exception:  # noqa: BLE001 - an unreadable store lists no cleared items; the refusals still stand
            pending = ()
        return (*refusals, *(ReadyRefusal(item.origin.work_ref, item.origin.event_identity,
                                          item.origin.required_authority, "", item.identity, True, True)
                             for item in pending if item.origin.lane == READY_VIEW
                             and (item.origin.work_ref, item.origin.event_identity) not in seen))

    def _ensure(self, card: str, kind: str, reason: str) -> ReadyRefusal:
        """One JUDGMENT item per card and kind whose origin, source evidence included, is the same in every process;
        the reason is reported, never stored."""
        owner, consumer = OWNERS[kind], self.assessment.consumer
        try:
            source = consumer.repository.put(Observation(
                Header(consumer.repository.project, consumer.repository.profile, f"{READY_VIEW}/{kind}/{card}", "1",
                       (self._definition,)),
                self._definition, READY_VIEW, READY_VIEW + "/v1", (),
                canonical_bytes({"kind": kind, "card": card}).decode(), None, READY_VIEW, READY_VIEW))
            item = self._attention.ensure(AttentionOrigin(card, kind, "JUDGMENT", READY_VIEW, READY_VIEW, owner,
                                                          READY_VIEW, source))
        except Exception:  # noqa: BLE001 - an unwritable attention store marks the refusal unrecorded
            return ReadyRefusal(card, kind, owner, reason, None, False)
        return ReadyRefusal(card, kind, owner, reason, item.identity, True)

    def repair_displays(self) -> tuple[LinkResult, ...]:
        """The one GitHub write of the READY view, never called by a snapshot: `work display` (with its read-back) for
        each item the last snapshot found with DISPLAY_DIFFERS; Issue title and body only, never Status or fields."""
        return tuple(self.links.display(identity) for _, identity in self._differs)

    def _assessment(self, configuration: ProjectConfiguration) -> PacketAssessment:
        """`work assess` over its own retained-assessment store; each attempt's Agent Ready launch carries the
        worker runtime's invocation markers naming that attempt and the recorded owner process."""
        readiness = configuration.readiness
        consumer = _consumer(configuration, SQLiteOperationalStore(readiness.database))
        binding = resolve_binding(readiness.executable, "cli")
        return PacketAssessment(self.records, self.identities, consumer, binding, ProcOwnership(),
                                lambda attempt, owner: compose_producer(binding, readiness.provider, {
                                    **assessment_environment(), INVOCATION_MARKER: attempt,
                                    INVOCATION_OWNER_MARKER: owner_token(owner)}),
                                StoredReleaseAuthorizations(consumer.store, "registry"))

    def _authorization(self, configuration: ProjectConfiguration) -> WorkAuthorization:
        """`work authorize`: release records on the `readiness` store under profile `registry` (the READY view's), the
        evidence record in the assessment evidence folder, baselines checked in each repository's configured clone
        against its configured default branch."""
        consumer, repositories = self.assessment.consumer, configuration.repositories
        return WorkAuthorization(self.records, self.identities, consumer, consumer.repository, consumer.project,
                                 consumer.profile, self.assessment.authorizations,
                                 GitRevisionResolver({name: location.clone for name, location in repositories.items()}),
                                 {name: location.default_branch for name, location in repositories.items()})

    def _completion(self, configuration: ProjectConfiguration) -> WorkCompletion:
        """`work record-completed`: the evidence record in the assessment evidence folder, landings checked in each
        repository's configured clone against its configured default branch (what `work authorize` checks), the
        landing record read with the repository adapter's `read_packet`, and the `registry` coordinator's
        `factory:<id>` record on the `readiness` store (the record `cycles` reads)."""
        consumer, repositories = self.assessment.consumer, configuration.repositories
        return WorkCompletion(self.records, self.identities, consumer.repository, consumer.project, consumer.profile,
                              GitRevisionResolver({name: location.clone for name, location in repositories.items()}),
                              {name: location.default_branch for name, location in repositories.items()},
                              self.items.read_packet,
                              lambda identity: consumer.store.read_state("registry", f"factory:{identity}")[1])


def _consumer(configuration: ProjectConfiguration, store: OperationalStore) -> RetainedAssessmentConsumer:
    """The retained-assessment consumer of `work assess` over `store`, the `readiness` database."""
    readiness, profile = configuration.readiness, "work-preparation"
    definition_ref = Ref(configuration.project, profile, "readiness-consumer",
                         "sha256:" + sha256(Path(assessment_consumer.__file__).read_bytes()).hexdigest(),
                         "python:alienintent.execution_coordination.adapters.assessment_consumer")
    return RetainedAssessmentConsumer(
        LocalEvidenceRepository(readiness.evidence_root, configuration.project, profile), store,
        configuration.project, profile, definition_ref, "alienintent work assess", frozenset({"public", "private"}))


# The read-only worker profile `work context` runs under, and the installed executable that runs it.
WORK_CONTEXT_PROFILE = "alienintent.composition.work_registry:work_context_profile"


def installed_executable() -> Path:
    """The `alienintent` console script installed with this interpreter (its scripts directory)."""
    return Path(sysconfig.get_path("scripts")) / "alienintent"


def _git_diff(clone: Path, base: str, revision: str) -> bytes:
    """`git diff <base> <revision>` in the VERIFIER's candidate clone; any failure is GIT_READ_FAILED."""
    try:
        result = subprocess.run(["git", "diff", "--no-ext-diff", "--no-color", base, revision], cwd=clone,
                                capture_output=True, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitReadFailed("git diff", str(clone), type(error).__name__) from error
    if result.returncode:
        raise GitReadFailed("git diff", str(clone), result.stderr.decode(errors="replace").strip()[:200])
    return result.stdout


def _work_context(configuration: ProjectConfiguration, records: WorkRecordService, items: SQLiteWorkItemRepository,
                  consumer: RetainedAssessmentConsumer) -> WorkContext:
    """WorkContext over the `readiness` store (profile `registry`: coordinator state, reservations, release and
    self-review records) and evidence folder; its command is `work context` under the read-only worker profile."""
    command = ContextCommand(str(installed_executable()), WORK_CONTEXT_PROFILE, {
        "ALIENINTENT_PROJECT_CONFIGURATION": str(configuration.path), "ALIENINTENT_PROJECT": configuration.project})
    return WorkContext(records, items.read_packet, consumer, consumer.store, consumer.repository,
                       StoredReleaseAuthorizations(consumer.store, "registry"), FactoryCoordinator.decode, _git_diff,
                       command, consumer.project, consumer.profile, "registry")


def work_context_profile() -> SimpleNamespace:
    """The read-only worker profile (`--profile-factory alienintent.composition.work_registry:work_context_profile`):
    the same configuration file and project as `work_registry_profile`, but only the readers `work context` needs,
    with the work and `readiness` databases opened read-only (SQLite `mode=ro`). It builds no WorkRegistry, uses no
    `github` entry and resolves no Agent Ready executable; the CLI answers every other command
    `not-available-in-worker-profile`. It protects this API only, not other files a worker's shell can reach."""
    path, project = (os.environ.get(name) for name in ("ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"))
    if not path or not project:
        raise ConfigurationInvalid("ALIENINTENT_PROJECT_CONFIGURATION and ALIENINTENT_PROJECT are required")
    configuration = load_project_configuration(Path(path), project)
    if configuration.readiness is None:
        raise ConfigurationInvalid(f"project {project}: work context needs the readiness entry")
    items = SQLiteWorkItemRepository(configuration.database, configuration.repositories, read_only=True)
    # Only `find` and `children` are used: no publisher and no profile stores, so nothing can publish or migrate.
    records = WorkRecordService(WorkIdentityService(items, None, configuration.repositories, {}), items,
                                items.read_packet)
    consumer = _consumer(configuration, SQLiteOperationalStore(configuration.readiness.database, read_only=True))
    return SimpleNamespace(worker_profile=True, work_registry=SimpleNamespace(
        context=_work_context(configuration, records, items, consumer)))


def work_registry_profile() -> SimpleNamespace:
    """The CLI's `--profile-factory alienintent.composition.work_registry:work_registry_profile` for the `work`
    commands: the project configuration file named by ALIENINTENT_PROJECT_CONFIGURATION and the project named by
    ALIENINTENT_PROJECT, both required; exposes `work_registry`."""
    path, project = (os.environ.get(name) for name in ("ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"))
    if not path or not project:
        raise ConfigurationInvalid("ALIENINTENT_PROJECT_CONFIGURATION and ALIENINTENT_PROJECT are required")
    return SimpleNamespace(work_registry=WorkRegistry(load_project_configuration(Path(path), project)))
