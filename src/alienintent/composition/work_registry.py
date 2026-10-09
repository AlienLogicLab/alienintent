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
With both, `launcher()` (`work launch`, unit 6c-2) is that coordinator over the existing worker chain, launching one
PRODUCER or VERIFIER step with its package assembled at launch and its model routed from the shared routing file at
every launch (LaunchPreparation). Workers keep their user's filesystem access: no operating-system containment is
claimed. At ACCEPT, for a contract whose `required_closure_actions` are exactly the five fixed closure names, the same
launch runs a fresh CLOSURE session on the VERIFIER's route (granted `git-read` and `process-control` only) whose only
output is a bounded closure request; `RegistryClosure` (the control plane) then performs and reads back each requested
effect in the fixed order and alone issues the exact receipts. The landing itself is pushed only by the Landing
Authority, built only when the `github` entry sets `"landing": true`, with its own landing-scoped token; without it the
outcome is a verified `ready-to-land`. After the coordinator's DONE the row is projected to DONE through
`WorkCompletion.record_coordinated`. Every token the registry mints is scoped: `work link`, `work display` and the
READY view use DISPLAY_PERMISSIONS for the one repository.
With the optional `worker_user` entry (unit WORKER-CREDENTIAL-BOUNDARY), every cognitive session and every command
run on its behalf runs as that Unix user through the one sudo rule, in its own worker-owned clone under
`launch/worker/`, with a HOME (`launch/worker/home`) recreated at each session holding only a `safe.directory`-only
`.gitconfig`, and the worker's own persistent Codex login in `launch/worker/auth/codex` as `CODEX_HOME` (the Founder's
login is never read or copied). The candidate is handed over by exact object identity through a
bundle imported into the control-plane-owned `launch/intake.git`, and published from there; worker results are read
from `launch/results/<invocation>/` through checked descriptors only. Without it, launches run as today. This is a
credential and authority boundary, not containment.

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
                   "private_key_path": "<path to the App private key file>", "landing": false,
                   "project": {"project_id": "PVT_...", "project_number": <int>, "organization": "<owner>",
                               "status_field_id": "<id>", "priority_field_id": "<id>"}},
        "worker_user": "alienintent-worker"}}}
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import signal
import subprocess
import sysconfig
import time
from types import SimpleNamespace
from uuid import uuid4

from alienintent.composition.landing_authority import LANDING_PERMISSIONS, LandingAuthority, LandingOrder, git_environment
from alienintent.composition.model_routing import provider_command, resolve_route
from alienintent.composition.readiness import assessment_environment, compose_producer, resolve_binding
from alienintent.composition.role_binding import ROLE_OPERATIONS, RoleBindingGuard
from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS, worker_environment
from alienintent.composition.sandbox_profile import APP_KEY_REFERENCE
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.application.initial_compilation_service import PacketLocation, WorkRegistration
from alienintent.context_assembly.application.packet_assessment import PacketAssessment
from alienintent.context_assembly.application.work_authorization import WorkAuthorization
from alienintent.context_assembly.application.work_completion import WorkCompletion
from alienintent.context_assembly.application.work_context import EXPORT_FILE, ContextCommand, WorkContext
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_link import WorkLink
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.packet_assessment import fingerprint
from alienintent.context_assembly.domain.reconstruction import ContextHold, HoldReason
from alienintent.context_assembly.application.work_completion import landing_check
from alienintent.context_assembly.domain.work_context import CLOSURE, PRODUCER, VERIFIER
from alienintent.context_assembly.domain.work_contract import ContractInvalid, contract_block
from alienintent.context_assembly.domain.work_identity import DONE, STATES, GitReadFailed, StoredPointer, \
    WorkIdentityRefused, valid_path
from alienintent.context_assembly.domain.work_link import REQUIRED_PERMISSIONS, LinkResult, render
from alienintent.context_assembly.ports.work_item_repository import (
    PacketRef, PublicationFailed, RefPublisher, RepositoryLocation)
from alienintent.control_plane.adapters.attention_repository import DurableAttentionRepository
from alienintent.control_plane.application.attention import AttentionService
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.control_plane.application.operator import OperatorControlPlane, export_context
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
from alienintent.execution_coordination.application.factory_coordinator import NEVER_STARTED, FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
from alienintent.execution_coordination.domain.satisfiability import unsatisfiable
from alienintent.execution_coordination.domain.closure import (
    BOARD_UPDATED, LANDING_RECORD, MERGED_TO_MAIN, WORKSPACES_CLEANED, hold, is_fixed, parse_request, performable,
    ready_to_land, receipt, rework, session_finding)
from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.escalation import DecisionRecord, HumanDecisionRequired
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.execution_coordination.ports.project_directory import ProjectItemState
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.installation.adapters.app_jwt import app_assertion
from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
from alienintent.installation.application.installation_credentials import InstallationCredentials
from alienintent.installation.domain.app_credentials import AppIdentity
from alienintent.installation.domain.project_identity import ProjectAddress
from alienintent.installation.ports.github_transport import GitHubTransport
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider, kill_as_worker, run_as_worker, \
    worker_prefix
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl, IntakeSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorkspace, GitWorktreeAdapter, WorkerCloneAdapter, \
    ref_safe
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.application.real_worker import (
    CLOSURE_ORDERED, EFFECT_UNKNOWN, OWNED_WORK_ACTIVE, OWNER_ALIVE, PUBLICATION_STARTED, RealWorkerProvider)
from alienintent.invocation_runtime.application.regression_gate import (
    SUITE_JUNIT_LIMIT, SUITE_WALL_CLOCK, RegressionGate, SuiteUnrunnable, suite)
from alienintent.invocation_runtime.domain.runtime import (
    INVOCATION_MARKER, INVOCATION_OWNER_MARKER, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable,
    ReservationBook, owner_token, workspace_folder)
from alienintent.invocation_runtime.ports.process_ownership import ProcessOwnership
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
# Every registry token is scoped: `work link`, `work display` and the READY view need these, for the one repository.
DISPLAY_PERMISSIONS = dict(REQUIRED_PERMISSIONS) | {"metadata": "read"}
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
    landing: bool = False  # The Founder's authorization of the landing App permission: builds the Landing Authority.


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
    worker_user: str | None = None  # The Unix user cognitive sessions run as; None runs them as today.


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
        worker_user = entry.get("worker_user")
        if worker_user is not None and (not isinstance(worker_user, str) or not _USER_NAME.fullmatch(worker_user)):
            raise ConfigurationInvalid(f"project {project}: worker_user must be a Unix user name")
        configuration = ProjectConfiguration(project, Path(entry["database"]), repositories, packets["repository"],
                                             packets["directory"], profiles, readiness, github,
                                             worker_user=worker_user)
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


_USER_NAME = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
# The one provider with a persistent worker-owned login (revision 8): its store is `<launch>/worker/auth/codex`.
WORKER_PROVIDER = "codex"
_LOGIN_CHECK = 'test -d "$1" && ! test -L "$1" && test -f "$1/auth.json" && ! test -L "$1/auth.json"'


def worker_login_present(user: str, environment: Mapping[str, str], store: Path) -> bool:
    """Whether the worker's own login is in place, checked as the worker through the sudo rule: `store` a real
    folder (not a symlink) holding a regular `auth.json` (not a symlink). Only the exit code is read."""
    return run_as_worker(user, environment, ["sh", "-c", _LOGIN_CHECK, "sh", str(store)]).returncode == 0


def prepare_worker_session(user: str, environment: Mapping[str, str], packets_clone: Path, intake: Path) -> None:
    """Prepare one worker session, as the worker through the sudo rule, after `worker_login_present`: recreate the
    HOME (`environment["HOME"]`) empty, mode 0700, holding only a `.gitconfig` whose only key is `safe.directory`,
    for the packets clone and the intake repository, and make TMPDIR; then remove everything in the worker's
    persistent login store (`environment["CODEX_HOME"]`) except `auth.json`, so no session leaves configuration or
    instructions for the next. The control plane opens no file and never reads, writes or copies a login file; no
    gh login, credential helper, SSH key, configuration or App key reaches the worker."""
    home, tmp, store = Path(environment["HOME"]), Path(environment["TMPDIR"]), Path(environment["CODEX_HOME"])
    safe = "[safe]\n" + "".join(f"\tdirectory = {path}\n" for path in (packets_clone, intake))
    write = ["sh", "-c", 'umask 077 && exec cat > "$1"', "sh"]
    for argv, data_in in ((["rm", "-rf", "--", str(home)], None), (["mkdir", "-m", "0700", "--", str(home)], None),
                          (["mkdir", "-p", "-m", "0700", "--", str(tmp)], None),
                          ([*write, str(home / ".gitconfig")], safe.encode()),
                          (["find", "-P", str(store), "-mindepth", "1", "-maxdepth", "1", "!", "-name", "auth.json",
                            "-exec", "rm", "-rf", "--", "{}", "+"], None)):
        if run_as_worker(user, environment, argv, input=data_in).returncode:
            raise OSError(f"the worker session cannot be prepared: {argv[0]}")


def worker_uid(user: str) -> int:
    try:
        return pwd.getpwnam(user).pw_uid
    except KeyError:
        raise ConfigurationInvalid(f"worker_user {user} is not a Unix user (run tools/live/setup_worker_user.sh)") \
            from None


def _readiness(value: object) -> ReadinessConfiguration:
    if not isinstance(value, dict) or set(value) != {"database", "evidence_root", "executable", "provider"} \
            or not all(isinstance(v, str) and v for v in value.values()):
        raise ConfigurationInvalid("readiness needs exactly database, evidence_root, executable and provider")
    return ReadinessConfiguration(Path(value["database"]), Path(value["evidence_root"]), Path(value["executable"]),
                                  value["provider"])


def _github(value: object) -> GitHubConfiguration:
    fields = {"repository", "application_id", "installation_id", "private_key_path", "project"}
    if not isinstance(value, dict) or set(value) not in (fields, fields | {"landing"}) \
            or type(value.get("landing", False)) is not bool or not isinstance(value["repository"], str) \
            or value["repository"].count("/") != 1 or not all(value["repository"].split("/")) \
            or not all(type(value[name]) is int and value[name] > 0 for name in ("application_id", "installation_id")) \
            or not isinstance(value["private_key_path"], str) or not value["private_key_path"] \
            or not isinstance(value["project"], dict):
        raise ConfigurationInvalid("github needs exactly repository, application_id, installation_id, "
                                   "private_key_path and project (and the optional boolean landing)")
    return GitHubConfiguration(value["repository"], value["application_id"], value["installation_id"],
                               Path(value["private_key_path"]), ProjectAddress(**value["project"]),
                               value.get("landing", False))


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


def suite_runner(user: str | None, environment: Mapping[str, str]) -> Callable[[Path, Path], int]:
    """REGRESSION-GATE's suite run: `SUITE` in `folder` with the worker's environment (never the control plane's
    own) and PYTHONDONTWRITEBYTECODE=1, as the worker through the sudo rule (`worker_prefix`), or directly without a
    worker user; one process group, stopped at SUITE_WALL_CLOCK, which is `SuiteUnrunnable`. Answers the exit
    code."""
    variables = dict(environment) | {"PYTHONDONTWRITEBYTECODE": "1"}

    def run(folder: Path, junit: Path) -> int:
        if user is None:
            argv, child = suite(junit), variables
        else:
            argv, child = [*worker_prefix(user, variables), *suite(junit)], None
        process = subprocess.Popen(argv, cwd=folder, env=child, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            return process.wait(timeout=SUITE_WALL_CLOCK)
        except subprocess.TimeoutExpired:
            for signum in (signal.SIGTERM, signal.SIGKILL):
                if user is not None:
                    kill_as_worker(user, signum, f"-{process.pid}")
                try:
                    os.killpg(process.pid, signum)
                except (ProcessLookupError, PermissionError):
                    pass
                try:
                    process.wait(timeout=5)
                    break
                except subprocess.TimeoutExpired:
                    continue
            raise SuiteUnrunnable("the suite outran its wall clock") from None
    return run


def _read_junit(path: Path) -> bytes:
    """A control-plane `regression-results` junit file, at most SUITE_JUNIT_LIMIT bytes (OSError beyond)."""
    with path.open("rb") as stream:
        data = stream.read(SUITE_JUNIT_LIMIT + 1)
    if len(data) > SUITE_JUNIT_LIMIT:
        raise OSError("the suite's junit file is too large")
    return data


class WorkRegistry:
    """The one work identity service of a project, with its repository adapter, publisher and the operator's
    work-record operations (`records`); `registration` is the compiler's. `suite_run` replaces REGRESSION-GATE's
    real suite run (`suite_runner`) for tests."""

    def __init__(self, configuration: ProjectConfiguration, source_control: SourceControl | None = None,
                 transport: GitHubTransport | None = None, host_configuration: Path = HOST_CONFIGURATION,
                 ownership: ProcessOwnership | None = None, *,
                 suite_run: Callable[[Path, Path], int] | None = None) -> None:
        self.configuration = configuration
        self._suite_run = suite_run
        # The existing process ownership observation: the launch chain's, and the exclusive `work launch` owner's.
        self.ownership = ownership if ownership is not None else ProcOwnership() if configuration.worker_user is None \
            else ProcOwnership(worker_uid=worker_uid(configuration.worker_user))
        self.host_configuration = host_configuration
        self._transport = transport
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
        self.satisfiable = self._satisfiable
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
        credentials = self._credentials(github, transport, DISPLAY_PERMISSIONS)
        return WorkLink(self.records, self.items,
                        GitHubRepositoryApi(github.repository, transport, credentials.authorization),
                        GitHubProjectsV2Directory(github.project, transport, credentials.authorization), credentials,
                        self.cycles if self.assessment is not None else None)

    @staticmethod
    def _credentials(github: GitHubConfiguration, transport: GitHubTransport,
                     permissions: Mapping[str, str]) -> InstallationCredentials:
        """The App installation's credentials, every mint scoped to `permissions` for the one repository."""
        return InstallationCredentials(
            AppIdentity(github.application_id, github.installation_id, APP_KEY_REFERENCE),
            ProtectedLocalFileSecretProvider({APP_KEY_REFERENCE: github.private_key_path}), transport, time.time,
            app_assertion, permissions=permissions, repositories=(github.repository.split("/", 1)[1],))

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
        admission. Closure: `landing_enabled` is the `github` entry's `landing` flag, `started_item` builds a started
        item from its registry record (0.9) and `completed` projects the row after DONE (0.8)."""
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
                                  recorded_completion=self.completion.recorded,
                                  landing_enabled=lambda: configuration.github.landing,
                                  started_item=self._started_item, completed=self._project_completed)

    def _journal_records(self) -> tuple[dict[str, object], ...]:
        return JsonlInvocationJournal(launch_root(self.configuration) / "invocation-journal.jsonl", time.time).records()

    def _started_item(self, identity: str, correlation: str) -> ReadyWorkItem | None:
        """A started work item built from its registry record alone (not the board): the row (not retired, with a
        pointer), its packet and contract block, and its assessment reference; the contract digest must be the one
        the correlation's `invocation-started` event journaled. Otherwise None."""
        try:
            record = self.records.show(identity)
            item = None if record is None else record.item
            if item is None or item.retired or item.pointer is None or record.packet is None \
                    or item.assessment_ref is None:
                return None
            contract = contract_block(record.packet, item.id)
            started = [entry for entry in self._journal_records() if entry.get("event") == "invocation-started"
                       and entry.get("correlation_id") == correlation and entry.get("work_identity") == item.id]
            if len(started) != 1 or started[0].get("contract_digest") != contract.content_digest:
                return None
            return ReadyWorkItem(item.id, 0, self.configuration.github.repository, "registry", None,
                                 tuple(contract.dependencies), contract, contract.content_digest,
                                 item.assessment_ref.logical_id, automatic_release=False)
        except Exception:  # noqa: BLE001 - an unusable registry record answers None, as recovery expects
            return None

    def _project_completed(self, identity: str) -> None:
        """The coordinator's `completed` hook: nothing when the row is already DONE, otherwise
        `record_coordinated` with the last journaled `closure-ordered` event of this item and its custodied
        candidate (of any correlation). A refusal raises, which the coordinator records as a diagnostic."""
        item = self.identities.find(identity)
        if item is None:
            raise LookupError("no work item")
        if item.state == DONE:
            return
        _, raw = self.store.read_state("registry", f"factory:{identity}")
        held = raw.get("candidate")
        revision = str(held.get("locator", "")).rpartition("@")[2] if isinstance(held, dict) else None
        orders = [entry for entry in self._journal_records() if entry.get("event") == CLOSURE_ORDERED
                  and entry.get("work_identity") == identity and entry.get("candidate") == revision]
        result = self.completion.record_coordinated(identity, orders[-1] if orders else None)
        if result.answer is not None:
            raise RuntimeError(f"{result.answer}: {result.detail}")

    def launcher(self) -> FactoryCoordinator:
        """`work launch` (unit 6c-2): `coordinator(worker, artifacts)` with the existing worker chain of
        SandboxRunProfile — CliWorkerProvider (its command built at every run from the route `prepare` read, with the
        `worker_environment` allowlist plus the two variables the context command names), RealWorkerProvider over the
        packets repository's clone with the invocation journal, GitWorktreeAdapter, ProcOwnership and one grant per
        dispatch, then RoleBindingGuard. Its state lives beside the `readiness` database, in `launch/`. No other
        configuration is read; the model routing file is read by `prepare` at every launch."""
        return self._launch_chain()[0]

    @property
    def store(self) -> OperationalStore:
        """The `readiness` store the `registry` coordinator and the exclusive `work launch` reservation live in."""
        return self.assessment.consumer.store

    def decide(self, identity: str, choice: str, quote: str) -> dict[str, object]:
        """`work decide`: the choice on the work item's open decision request, submitted through the existing path of
        `decisions decide` (OperatorControlPlane.decisions_decide: DecisionInbox.submit, then the registry
        coordinator's `validate_decision` and `record_decision`) with an admission whose resume does nothing, so it
        never launches. Before an `authorize` it refuses, writing nothing, while the owner or owned work runs, when an
        empty journal does not prove the launch never started, and until a publication that began is reconciled
        against the remote. The answer names the retained PRODUCER worktree of the launch it resolves."""
        coordinator, worker, root = self._launch_chain()
        store, workspaces = self.store, root / "workspaces"
        packets = self.configuration.repositories[self.configuration.packets_repository]
        inbox = DecisionInbox(store, _DecisionOnly(coordinator), "registry")
        request = next((entry for entry in inbox.list_open() if entry.work_item == identity), None)
        if request is None:
            recorded = None
            try:
                recorded = inbox.show(identity)
            except KeyError:
                pass
            if not isinstance(recorded, DecisionRecord) or recorded.submission.choice != choice:
                return {"answer": NO_OPEN_DECISION}
            biu_version = recorded.submission.biu_version  # A repeat: the same idempotency key answers it.
        else:
            biu_version = request.biu_version
        revision, raw = store.read_state("registry", f"factory:{identity}")
        correlation = raw.get("correlation") if isinstance(raw.get("correlation"), str) else None
        # The key names the held launch: at ACCEPT the version never moves, so a later hold needs its own decision.
        key = recorded.event.idempotency_key if request is None \
            else f"work-decide:{identity}:{biu_version}:{correlation}:{choice}"
        worktree = None if correlation is None else _producer_worktree(
            workspaces, WorkerInvocation(identity, correlation)) if self.configuration.worker_user is None \
            else _producer_worktree(root / "worker", WorkerInvocation(identity, correlation), "producer-")
        retained = worktree.path if worktree is not None and worktree.path.is_dir() else None
        parked = correlation is not None and any(effect.identity == correlation
                                                 for effect in store.unresolved_effects("registry"))
        if request is not None and choice == "authorize" and parked:
            # With a worker user the remote is read from the Founder-owned packets clone, never the worker's.
            refusal = self._authorize_refusal(worker, identity, correlation, request.reason,
                                              workspaces / workspace_folder(correlation) if self.configuration.worker_user is None
                                              else packets.clone)
            if refusal is not None:
                return refusal | {"correlation": correlation, "retained_worktree": None if retained is None
                                  else str(retained)}
        packet = self.records.show(identity)
        issuer = contract_block(packet.packet, identity).authority_issuer
        decided = OperatorControlPlane("registry", store, None, _DecisionOnly(coordinator), lambda: True)\
            .decisions_decide(identity, actor=issuer, authority=issuer, target=identity, intent=choice, reason=quote,
                              expected_version=revision, idempotency_key=key,
                              biu_version=biu_version, choice=choice)
        if request is not None and choice == "authorize" and parked and retained is not None:
            worker.retained_workspaces[correlation] = retained
            worker.cleanup_diagnostics[correlation] = f"{identity}: authorized and relaunched"
        return {"answer": None, "decision": decided, "correlation": correlation,
                "retained_worktree": None if retained is None else str(retained),
                "cleanup_diagnostics": dict(worker.cleanup_diagnostics)}

    def _authorize_refusal(self, worker: RealWorkerProvider, identity: str, correlation: str, reason: str,
                           workspace: Path) -> dict[str, object] | None:
        """Why `authorize` may not lift the parked launch's effect yet, or None."""
        invocation = WorkerInvocation(identity, correlation)
        attested = worker.attest_ownership(invocation).kind
        if attested in {OWNER_ALIVE, OWNED_WORK_ACTIVE}:
            return {"answer": OWNER_STILL_RUNNING, "attestation": attested}
        try:
            records = [record for record in worker.journal.records() if record.get("correlation_id") == correlation]
        except JournalUnreadable:
            return {"answer": START_UNPROVEN, "missing": "a readable invocation journal"}
        if not records:
            # An empty journal is not proof of no start: recovery must have found the effect `pending` and parked it,
            # and no process may carry the correlation's marker.
            if reason != f"{NEVER_STARTED}: {correlation}":
                return {"answer": START_UNPROVEN, "missing": f"the park reason '{NEVER_STARTED}'"}
            if self.ownership.owned_work(correlation) != ():
                return {"answer": START_UNPROVEN, "missing": "no process carrying the correlation's marker"}
            return None
        if any(record.get("event") == CLOSURE_ORDERED for record in records):
            # A begun landing: settled deterministically by the next CLOSURE, once the remote can be read.
            packets = self.configuration.repositories[self.configuration.packets_repository]
            try:
                self.source_control.remote_revision(packets.clone, packets.remote, packets.default_branch)
            except CandidateUnavailable:
                return {"answer": REMOTE_UNVERIFIED, "branch": packets.default_branch, "missing": "a readable remote"}
            return None
        published = [record.get("revision") for record in records if record.get("event") == PUBLICATION_STARTED]
        if not published:
            return None
        branch = worker.candidate_branch(invocation)
        if not workspace.is_dir():
            return {"answer": REMOTE_UNVERIFIED, "branch": branch, "missing": "the PRODUCER worktree"}
        packets = self.configuration.repositories[self.configuration.packets_repository]
        try:
            remote = self.source_control.remote_revision(workspace, packets.remote, branch)
        except CandidateUnavailable:
            return {"answer": REMOTE_UNVERIFIED, "branch": branch, "missing": "a readable remote"}
        if remote is None:
            return None if attested == EFFECT_UNKNOWN else {"answer": REMOTE_UNVERIFIED, "branch": branch,
                                                            "attestation": attested}
        if remote == published[-1]:
            return {"answer": CANDIDATE_PUBLISHED, "branch": branch, "revision": remote}
        return {"answer": REMOTE_CONFLICT, "branch": branch, "revision": remote}

    def _launch_chain(self) -> tuple[FactoryCoordinator, RealWorkerProvider, Path]:
        """The `launcher()` coordinator, its RealWorkerProvider and the launch folder."""
        if self.context is None or self.ready_view is None:
            raise ConfigurationInvalid("work launch needs the github and readiness entries and a configuration file")
        configuration = self.configuration
        packets = configuration.repositories[configuration.packets_repository]
        repository, store = configuration.github.repository, self.assessment.consumer.store
        root = launch_root(configuration)
        for directory in (root / "workspaces", root / "verifier", root / "custody", root / "artifacts",
                          root / "context", root / "worker-tmp"):
            directory.mkdir(parents=True, exist_ok=True)
        (root / "landing").mkdir(mode=0o700, exist_ok=True)
        user = configuration.worker_user
        if user is not None:  # `<launch>/context` stays Founder-only and is never named to a worker (0.6b)
            os.chmod(root / "context", 0o700)
        environment = worker_environment(root) | dict(self.context.command.environment)
        if user is None:
            source, workspaces, handover, preparation = GitSourceControl(), \
                GitWorktreeAdapter(packets.clone, root / "workspaces"), None, \
                LaunchPreparation(self.context, root / "context", repository)
            recovered = lambda invocation: _producer_worktree(root / "workspaces", invocation)  # noqa: E731
        else:
            worker_root = root / "worker"
            environment = environment | {"HOME": str(worker_root / "home"), "TMPDIR": str(worker_root / "tmp"),
                                         "CODEX_HOME": str(worker_root / "auth" / "codex"),
                                         "USER": user, "LOGNAME": user}
            for directory in (worker_root, root / "results", root / "handoff"):
                if not directory.is_dir():  # normally made by the setup; made here as the worker, mode 0711
                    run_as_worker(user, environment, ["mkdir", "-p", "-m", "0711", "--", str(directory)])
            (root / "intake-bundles").mkdir(mode=0o700, exist_ok=True)
            workspaces = WorkerCloneAdapter(packets.clone, worker_root, root / "results", user, environment)
            source = handover = IntakeSourceControl(packets.clone, packets.remote, root, user, worker_uid(user),
                                                    environment, os.environ, workspaces)
            preparation = LaunchPreparation(self.context, root / "context", repository, worker=handover, user=user,
                                            environment=environment, packets_clone=packets.clone,
                                            exports=root / "exports")
            recovered = lambda invocation: _producer_worktree(worker_root, invocation, "producer-")  # noqa: E731
        ownership = self.ownership
        process = CliWorkerProvider("routed", preparation.command, (), "explicit", PROVIDER_DIMENSIONS,
                                    environment=environment, ownership=ownership, worker_user=user,
                                    results=None if user is None else root / "results",
                                    regression_base=None if user is None else preparation.starting.get,
                                    work_identity=None if user is None else preparation.identities.get,
                                    feature_regressions=False)
        journal = JsonlInvocationJournal(root / "invocation-journal.jsonl", time.time)
        closure = RegistryClosure(self, root, journal, preparation, self._landing_authority(journal))
        gate = self._regression_gate(root, user, environment, source, workspaces, handover)
        worker = RealWorkerProvider(
            process, source, packets.clone, packets.remote,
            lambda invocation: f"candidate/{ref_safe(invocation.correlation_id)}", root / "verifier",
            lambda invocation: launch_grant(invocation, repository), repository,
            workspaces, ReservationBook(1, 2), now=time.time,
            sleep=time.sleep, journal=journal, ownership=ownership, preparation=preparation,
            recovered_workspace=recovered, closure=closure, handover=handover, regression_gate=gate,
            regression_base=preparation.starting.get)
        closure.worker = worker
        closure.worker_workspaces = None if user is None else workspaces
        guard = RoleBindingGuard(worker, journal, store, "registry", repository, time.time)
        return self.coordinator(guard, LocalArtifactStore(root / "artifacts", root / "custody")), worker, root

    def _regression_gate(self, root: Path, user: str | None, environment: Mapping[str, str], source,
                         workspaces: GitWorktreeAdapter | WorkerCloneAdapter, handover) -> RegressionGate:
        """REGRESSION-GATE for the registry profile: the baseline is a fresh checkout by the producer allocator under
        `baseline-<sha>-<invocation>`, its revision read (as the worker with one) and checked, removed when the block
        ends (a refusal is "workspace retained" and does not fail the gate; without a worker user its branch is
        deleted after a successful cleanup); each junit file is read by the control plane (with a worker user through
        `read_result`, from `<results>/<identity>/`; without one from `<launch>/regression-results/<identity>/`, a
        folder the control plane makes); baselines are cached in `<launch>/regression-baselines`."""
        run = self._suite_run if self._suite_run is not None else suite_runner(user, environment)

        @contextmanager
        def checkout(sha: str, identity: str) -> Iterator[Path]:
            workspace = workspaces.allocate(identity, identity, sha)
            try:
                if source.revision(workspace.path) != sha:
                    raise CandidateUnavailable("the baseline checkout is not at its revision")
                yield workspace.path
            finally:
                try:
                    workspaces.cleanup(workspace, None)
                    if handover is None:
                        workspaces.remove_branch(workspace)
                except (CandidateUnavailable, OSError):
                    pass  # workspace retained; the gate's decision does not depend on it

        if handover is not None:
            read = lambda path: handover.read_result(path.parent.name, path.name, limit=SUITE_JUNIT_LIMIT)  # noqa: E731
            return RegressionGate(run, read, checkout, root / "regression-baselines", handover.results)

        def own(folder: Path, junit: Path) -> int:
            junit.parent.mkdir(parents=True, exist_ok=True)
            return run(folder, junit)
        return RegressionGate(own, _read_junit, checkout, root / "regression-baselines", root / "regression-results")

    def _landing_authority(self, journal: JsonlInvocationJournal) -> LandingAuthority | None:
        """Only with `"landing": true`: its own landing-scoped credentials (never `_links`'), the coordinator record's
        custodied candidate at ACCEPT, and the launch journal's last `closure-ordered` event of a correlation."""
        github = self.configuration.github
        if not github.landing:
            return None
        packets = self.configuration.repositories[self.configuration.packets_repository]
        store = self.store

        def accepted(identity: str) -> str | None:
            _, raw = store.read_state("registry", f"factory:{identity}")
            held = raw.get("candidate")
            if raw.get("stage") != LifecycleStage.ACCEPT.value or not isinstance(held, dict):
                return None
            return str(held.get("locator", "")).rpartition("@")[2]

        def ordered(correlation: str) -> Mapping[str, object] | None:
            found = [entry for entry in journal.records() if entry.get("event") == CLOSURE_ORDERED
                     and entry.get("correlation_id") == correlation]
            return found[-1] if found else None

        return LandingAuthority(self._credentials(github, self._transport or UrllibGitHubTransport(),
                                                  LANDING_PERMISSIONS),
                                github.repository, packets.default_branch, accepted, ordered)

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
                                StoredReleaseAuthorizations(consumer.store, "registry"), self.satisfiable)

    def _authorization(self, configuration: ProjectConfiguration) -> WorkAuthorization:
        """`work authorize`: release records on the `readiness` store under profile `registry` (the READY view's), the
        evidence record in the assessment evidence folder, baselines checked in each repository's configured clone
        against its configured default branch."""
        consumer, repositories = self.assessment.consumer, configuration.repositories
        return WorkAuthorization(self.records, self.identities, consumer, consumer.repository, consumer.project,
                                 consumer.profile, self.assessment.authorizations,
                                 GitRevisionResolver({name: location.clone for name, location in repositories.items()}),
                                 {name: location.default_branch for name, location in repositories.items()},
                                 self.satisfiable)

    def _satisfiable(self, packet: bytes, commit: str, identity: str) -> tuple[str, ...]:
        try:
            contract = contract_block(packet, identity)
        except ContractInvalid as error:
            return (f"contract: {error}",)

        def present_at_pointer(path: str) -> bool:
            if not valid_path(path):
                return False
            try:
                record = self.records.show(identity)
                if record is None or record.item.pointer is None:
                    return False
                self.items.read_packet(StoredPointer(record.item.pointer.repo, path, commit))
            except WorkIdentityRefused:
                return False
            return True

        def registered(dependency: str) -> bool:
            item = self.identities.find(dependency)
            return item is not None and not item.retired

        github = self.configuration.github
        return unsatisfiable(contract, landing=github is not None and github.landing,
                             present_at_pointer=present_at_pointer, registered=registered,
                             provider_dimensions=PROVIDER_DIMENSIONS)

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
                              lambda identity: consumer.store.read_state("registry", f"factory:{identity}")[1],
                              releases=StoredReleaseAuthorizations(consumer.store, "registry"), fetch=self._fetch)

    def _fetch(self, repository: str) -> str:
        """`git fetch <remote> <default branch>` in the repository's configured clone (only the remote-tracking ref
        changes); answers that ref."""
        location = self.configuration.repositories[repository]
        result = subprocess.run(["git", "fetch", "--quiet", location.remote, location.default_branch],
                                cwd=location.clone, capture_output=True, check=False, timeout=300)
        if result.returncode:
            raise GitReadFailed("git fetch", str(location.clone), result.stderr.decode(errors="replace")[:200])
        return f"refs/remotes/{location.remote}/{location.default_branch}"


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


def _intake_diff(intake: Path) -> Callable[[Path, str, str], bytes]:
    """With a worker user: the VERIFIER's `diff`, computed in the control-plane-owned intake repository (explicit
    GIT_DIR, hooks, fsmonitor, replace objects, external diff and textconv off) between two full SHAs; the worker's
    clone is never read."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | {
        "GIT_DIR": str(intake), "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0"}

    def diff(clone: Path, base: str, revision: str) -> bytes:
        if not all(re.fullmatch(r"[0-9a-f]{40}", value or "") for value in (base, revision)):
            raise GitReadFailed("git diff", str(intake), "not a full SHA")
        try:
            result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "diff",
                                     "--no-ext-diff", "--no-textconv", "--no-color", base, revision, "--"],
                                    cwd=intake, env=environment, capture_output=True, check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise GitReadFailed("git diff", str(intake), type(error).__name__) from error
        if result.returncode:
            raise GitReadFailed("git diff", str(intake), result.stderr.decode(errors="replace").strip()[:200])
        return result.stdout
    return diff


def _work_context(configuration: ProjectConfiguration, records: WorkRecordService, items: SQLiteWorkItemRepository,
                  consumer: RetainedAssessmentConsumer) -> WorkContext:
    """WorkContext over the `readiness` store (profile `registry`: coordinator state, reservations, release and
    self-review records) and evidence folder; its command is `work context` under the read-only worker profile, or,
    with a worker user, `work context --export` over the invocation's bounded export (no configuration path)."""
    command = ContextCommand(str(installed_executable()), WORK_CONTEXT_PROFILE, {
        "ALIENINTENT_PROJECT_CONFIGURATION": str(configuration.path), "ALIENINTENT_PROJECT": configuration.project}) \
        if configuration.worker_user is None else ContextCommand(str(installed_executable()), WORK_CONTEXT_PROFILE, {},
                                                                 export_root=launch_root(configuration) / "exports")
    return WorkContext(records, items.read_packet, consumer, consumer.store, consumer.repository,
                       StoredReleaseAuthorizations(consumer.store, "registry"), FactoryCoordinator.decode,
                       _git_diff if configuration.worker_user is None
                       else _intake_diff(launch_root(configuration) / "intake.git"),
                       command, consumer.project, consumer.profile, "registry")


def context_export_reader() -> Callable[[str], dict[str, object]]:
    """The CLI's `work context --export <file>` (WORKER-CREDENTIAL-BOUNDARY section 0.6b), loaded before and instead of
    any profile factory: `export_context` over the worker's three identity variables. It builds no profile and opens
    no database, evidence repository or configuration."""
    environment = {name: os.environ.get(name, "") for name in (
        "ALIENINTENT_WORK_IDENTITY", "ALIENINTENT_ROLE", "ALIENINTENT_CORRELATION")}
    return lambda export: export_context(export, environment)


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


# --- unit 6c-2: the registry worker launch ---------------------------------------------------------------------------

# The one instruction text a launched worker receives on standard input. It names where the package is and where the
# result goes; everything else the worker needs is in its package.
INSTRUCTIONS = """You are the {role} for AlienIntent work item {identity}, invocation {invocation}.

Your context package is this JSON file:
{package}
Read it first and do only what it states: its goal, instructions, contract, allowed scope and stop conditions bind you.

{context}

Only the control plane publishes: do not push, do not open a pull request, and do not change any branch or
repository outside your current working directory. This is a workflow rule.

{result}
"""
CONTEXT_LINE = """For further facts, run the package's `context_command`: its `argv` exactly, with its `environment` added to yours. It
is read-only and answers a package or a named hold."""
EXPORT_CONTEXT_LINE = """To read your package again, run the package's `context_command`: its `argv` exactly, with its `environment` added
to yours. It is read-only and prints the package exported for this invocation, or `not-in-export`."""
PRODUCER_RESULT = """Your current working directory is your git worktree at the package's starting_revision. Make the
change there and commit it. Then write your self-review of the complete diff, as plain text, to this file:
{self_review}"""
CLOSURE_RESULT = """Your current working directory is a fresh read-only clone of the accepted candidate. Change
nothing there. Read the package and decide which of its closure_actions to request. Then write exactly one JSON file:
{request}
as {{"identity": "<the work item id>", "revision": "<the candidate commit, git rev-parse HEAD>",
"actions": ["<some of the five names>"], "findings": ["<finding>", ...]}}. The revision is the bare 40-hex commit
alone, never the package's candidate identity. The control plane performs and checks every effect; nothing else you write is read."""
VERIFIER_RESULT = """Your current working directory is a fresh clone of the candidate. Verify it against the package.
Then write .alienintent/verdict.json in that directory as {{"revision": "<the candidate commit, git rev-parse HEAD>",
"verdict": "accept" or "reject", "findings": ["<finding>", ...]}}; a reject needs at least one finding."""
WORKER_VERIFIER_RESULT = """Your current working directory is a fresh clone of the candidate. Verify it against the package.
Then write your verdict as one JSON file, to this file:
{verdict}
as {{"revision": "<the candidate commit, git rev-parse HEAD>", "verdict": "accept" or "reject",
"findings": ["<finding>", ...]}}; a reject needs at least one finding."""
# The worker results the control plane reads, each in `<launch>/results/<invocation>/`.
SELF_REVIEW, CLOSURE_REQUEST, VERDICT = "self-review.md", "closure-request.json", "verdict.json"
GRANT_SECONDS = 3600


# `work decide` answers that write nothing (command answers, not outcome kinds).
NO_OPEN_DECISION, OWNER_STILL_RUNNING, START_UNPROVEN = "NO_OPEN_DECISION", "OWNER_STILL_RUNNING", "START_UNPROVEN"
REMOTE_UNVERIFIED, REMOTE_CONFLICT, CANDIDATE_PUBLISHED = "REMOTE_UNVERIFIED", "REMOTE_CONFLICT", "CANDIDATE_PUBLISHED"


class _DecisionOnly:
    """The registry coordinator as the DecisionInbox admission of `work decide`: validation and recording only."""

    def __init__(self, coordinator: FactoryCoordinator) -> None:
        self._coordinator = coordinator

    def validate_decision(self, record: DecisionRecord) -> None:
        self._coordinator.validate_decision(record)

    def record_decision(self, record: DecisionRecord) -> None:
        self._coordinator.record_decision(record)

    def resume_after_decision(self) -> None:
        """Nothing: the next step is always an explicit `work launch`."""


def _producer_worktree(root: Path, invocation: WorkerInvocation, prefix: str = "") -> GitWorkspace | None:
    """The PRODUCER worktree a correlation owns at its fixed path `<root>/<workspace_folder(correlation)>` (what
    GitWorktreeAdapter.allocate creates; with a worker user `<launch>/worker/producer-<workspace_folder(correlation)>`, what
    WorkerCloneAdapter.allocate creates), or None for an identity that could name a path outside the root."""
    correlation = invocation.correlation_id
    if not correlation or any(part in correlation for part in ("/", "\\", "..", "\x00")):
        return None
    return GitWorkspace(correlation, invocation.work_identity, root.resolve() / f"{prefix}{workspace_folder(correlation)}",
                        f"invocation/{ref_safe(correlation)}")


def launch_root(configuration: ProjectConfiguration) -> Path:
    """The launch state folder: `launch/` beside the `readiness` database (the existing registry folder)."""
    return configuration.readiness.database.parent / "launch"


def launch_grant(invocation: WorkerInvocation, repository: str) -> CapabilityGrant:
    """One capability grant per dispatch, naming the invocation and the role it authorizes, issued by profile
    `registry` for the work items' repository (what RoleBindingGuard checks)."""
    role = InvocationRole(invocation.role)
    return CapabilityGrant(f"registry-{invocation.work_identity}", "1", invocation.correlation_id, role, "registry",
                           repository, ROLE_OPERATIONS[str(role)], int(time.time()) + GRANT_SECONDS)


class LaunchPreparation:
    """RealWorkerProvider's preparation hook for registry launches, and the per-invocation worker command.

    `prepare` refuses with a complete authority-block outcome (its one finding the same text as the escalation's
    reason) when the contract's budget states no execution or shutdown limit, when assembly holds, or when the role
    has no usable route; otherwise it writes the package to `<context root>/<invocation id>.json`, keeps the route
    and the instruction text, and returns the starting revision. `command` builds the provider command at `run`.
    `published` records the PRODUCER's self-review file against the published, read-back candidate; it never
    raises.

    With `worker` (the hand-over, unit WORKER-CREDENTIAL-BOUNDARY) every worker result lives in
    `<launch>/results/<invocation>/` and is read only through `worker.read_result`; `prepare` refuses a route whose
    provider is not codex (`worker provider unsupported: <provider>`) and, after the worker-run
    `worker_login_present`, a missing worker login (`worker provider login missing: <store>`); and `command` first
    runs `prepare_worker_session`: the worker HOME recreated holding only the `safe.directory`-only `.gitconfig`,
    and the worker's own login store (`CODEX_HOME`) cleaned of all but `auth.json`. No login file is read or copied."""

    def __init__(self, context: WorkContext, context_root: Path, repository: str,
                 route: Callable[[str], dict[str, str]] = resolve_route, *, worker=None, user: str | None = None,
                 environment: Mapping[str, str] | None = None, packets_clone: Path | None = None,
                 exports: Path | None = None) -> None:
        self.context, self.context_root, self.repository, self.route = context, Path(context_root), repository, route
        self.kept: dict[str, tuple[dict[str, str], str]] = {}
        # Each invocation's starting revision from its package: the VERIFIER's regression base with a worker user.
        self.starting: dict[str, str] = {}
        self.worker, self.user, self.packets_clone = worker, user, packets_clone
        self.environment = dict(environment or {})
        # With a worker user: `<launch>/exports`, where each invocation's package is exported (section 0.6b).
        self.exports = None if exports is None else Path(exports)
        self.identities: dict[str, str] = {}  # each invocation's work item, for the worker's identity variables

    def package_path(self, invocation_id: str) -> Path:
        """The package path named to the worker: with a worker user only its bounded export."""
        if self.exports is not None:
            return self.exports / invocation_id / EXPORT_FILE
        return self.context_root / f"{invocation_id}.json"

    def _result(self, invocation_id: str, name: str) -> Path:
        return self.worker.results / invocation_id / name

    def self_review_path(self, invocation_id: str) -> Path:
        if self.worker is not None:
            return self._result(invocation_id, SELF_REVIEW)
        return self.context_root / f"{invocation_id}.self-review.md"

    def closure_request_path(self, invocation_id: str) -> Path:
        """Where the CLOSURE session writes its one request, outside its clone."""
        if self.worker is not None:
            return self._result(invocation_id, CLOSURE_REQUEST)
        return self.context_root / f"{invocation_id}.closure-request.json"

    def read(self, path: Path) -> bytes:
        """A result file's bytes: with a worker user only through the hand-over's checked descriptor."""
        if self.worker is not None:
            return self.worker.read_result(path.parent.name, path.name)
        return path.read_bytes()

    def prepare(self, invocation: WorkerInvocation, clone: Path | None) -> str | WorkerOutcome:
        identity, role = invocation.work_identity, invocation.role
        if not self._budget_stated(identity):
            return self._refusal(invocation, f"{HoldReason.MISSING_RECORD}: budget_policy: the contract's "
                                             "budget_policy states no hard_wall_clock_seconds or cancellation_limit")
        if role == CLOSURE and not self._fixed(identity):
            return WorkerOutcome("ineligible")  # A guard only: `launch` answers closure-not-automated first.
        package = self.context.assemble(identity, role, invocation.correlation_id, invocation.contract_digest,
                                        invocation.candidate if role in (VERIFIER, CLOSURE) else None, clone)
        if isinstance(package, ContextHold):
            return self._refusal(invocation, f"{package.reason}: {', '.join(package.affected_refs)}: {package.detail}")
        try:
            route = self.route(VERIFIER if role == CLOSURE else role)  # CLOSURE runs on the VERIFIER's route
        except (OSError, ValueError, TypeError, AttributeError) as error:
            return self._refusal(invocation, f"model-routing-unavailable: {role}: {type(error).__name__}: {error}")
        if self.worker is not None:
            if route.get("provider") != WORKER_PROVIDER:  # no persistent worker login exists for it yet
                return self._refusal(invocation, f"worker provider unsupported: {route.get('provider')}")
            store = Path(self.environment["CODEX_HOME"])
            if not worker_login_present(self.user, self.environment, store):
                return self._refusal(invocation, f"worker provider login missing: {store}")
        self.deliver(invocation, package.document(), route)
        self.starting[invocation.correlation_id] = str(package.fields["starting_revision"])
        return str(package.fields["starting_revision"])

    def deliver(self, invocation: WorkerInvocation, document: Mapping[str, object], route: dict[str, str]) -> Path:
        """Write the package outside any worktree and keep the route and the instruction text for `command`."""
        path = self.package_path(invocation.correlation_id)
        data = json.dumps(dict(document), indent=1, sort_keys=True).encode("utf-8")
        if self.exports is None:
            self.context_root.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        else:
            self._export(path, data)
        self.identities[invocation.correlation_id] = invocation.work_identity
        result = PRODUCER_RESULT.format(self_review=self.self_review_path(invocation.correlation_id)) \
            if invocation.role == PRODUCER else CLOSURE_RESULT.format(
                request=self.closure_request_path(invocation.correlation_id)) \
            if invocation.role == CLOSURE else VERIFIER_RESULT if self.worker is None \
            else WORKER_VERIFIER_RESULT.format(verdict=self._result(invocation.correlation_id, VERDICT))
        self.kept[invocation.correlation_id] = (dict(route), INSTRUCTIONS.format(
            role=invocation.role, identity=invocation.work_identity, invocation=invocation.correlation_id,
            package=path, result=result, context=CONTEXT_LINE if self.exports is None else EXPORT_CONTEXT_LINE))
        return path

    def _export(self, path: Path, data: bytes) -> None:
        """Write exactly the package to `<launch>/exports/<c>/context.json`: both folders the Founder's, mode 0711,
        no ACL for the worker; the file the Founder's, mode 0640 with the one access ACL entry `u:<worker>:r`,
        written to a temporary file in `<launch>/exports/<c>` and renamed into place."""
        for folder in (path.parent.parent, path.parent):
            folder.mkdir(mode=0o711, exist_ok=True)
            if folder.is_symlink() or not folder.is_dir() or folder.lstat().st_uid != os.getuid():
                raise OSError(f"the export folder is not the control plane's: {folder}")
            os.chmod(folder, 0o711)
        temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o640)
            granted = subprocess.run(["setfacl", "-m", f"u:{self.user}:r", "--", str(temporary)],
                                     capture_output=True, check=False, timeout=30)
            if granted.returncode:
                raise OSError(f"the export cannot be granted to the worker: {granted.stderr.decode(errors='replace')}")
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def command(self, invocation_id: str, role: object, workspace: Path) -> tuple[list[str], str]:
        """CliWorkerProvider's per-invocation command: the provider command for the kept route and this workspace,
        and the instruction text for standard input."""
        route, text = self.kept[invocation_id]
        if self.worker is not None:
            prepare_worker_session(self.user, self.environment, self.packets_clone, self.worker.intake)
        return provider_command(route, workspace), text

    def published(self, invocation: WorkerInvocation, candidate: CandidateRef) -> None:
        try:
            text = self.read(self.self_review_path(invocation.correlation_id)).decode("utf-8")
            if text.strip():
                self.context.record_self_review(invocation.work_identity, candidate, text)
        except Exception:  # noqa: BLE001 - nothing is recorded; the VERIFIER's launch is held MISSING_RECORD
            pass

    def _fixed(self, identity: str) -> bool:
        try:
            record = self.context.records.show(identity)
            return record is not None and record.packet is not None and is_fixed(
                contract_block(record.packet, identity).required_closure_actions)
        except (WorkIdentityRefused, ContractInvalid):
            return False

    def _budget_stated(self, identity: str) -> bool:
        """Whether the contract states both launch limits; a packet or contract that cannot be read is left to
        assembly, which names it."""
        try:
            record = self.context.records.show(identity)
            if record is None or record.packet is None:
                return True
            budget = contract_block(record.packet, identity).budget_policy
        except (WorkIdentityRefused, ContractInvalid):
            return True
        return budget.hard_wall_clock_seconds is not None and budget.cancellation_limit is not None

    def _refusal(self, invocation: WorkerInvocation, reason: str) -> WorkerOutcome:
        """The complete authority-block outcome: an escalation naming the hold, and the same text as its finding."""
        _, raw = self.context.store.read_state(self.context.store_profile, f"factory:{invocation.work_identity}")
        version = raw.get("version") if isinstance(raw.get("version"), int) else 0
        escalation = HumanDecisionRequired(
            profile=self.context.store_profile, project=self.repository, work_item=invocation.work_identity,
            biu_version=version,
            decision="Resolve the launch hold, then authorize the blocked execution to continue.", reason=reason,
            options=("authorize", "defer"), tradeoffs=("authorize permits one normal guarded re-admission",
                                                       "defer retains the scoped authority block"),
            recommendation="defer", affected_requirements=("authority-required",),
            affected_architecture=("FD-05",), cost_of_waiting="The work item and its dependents remain blocked.",
            authorizations=("authorize permits one normal guarded re-admission", "defer authorizes continued blocking"))
        return WorkerOutcome("authority-block", None, escalation, (reason,))


# --- automated closure: the control plane ----------------------------------------------------------------------------

LANDING_NAME, LANDING_EMAIL = "AlienIntent Landing", "landing@alienintent.invalid"
MAX_ORDERS = 3
_WORKSPACE_PREFIXES = ("producer", "verifier", "closure", "landing")


def landing_record_path(label: str | None, identity: str, candidate: str) -> str:
    """The existing naming: `docs/evidence/<label, lower case, or the id>-landing-<first 7 of the candidate>.md`."""
    return f"docs/evidence/{(label or identity).lower()}-landing-{candidate[:7]}.md"


def render_landing_record(facts: Mapping[str, object]) -> bytes:
    """The one deterministic rendering of a landing record: fixed, bounded facts only, never session text."""
    lines = [f"# Landing record: {facts['label'] or facts['identity']}", "",
             f"- work item: {facts['identity']}", f"- label: {facts['label'] or ''}",
             f"- candidate: {facts['candidate']}", f"- base: {facts['base']}", f"- merge: {facts['merge']}",
             f"- instructions sha256: {facts['instructions_sha256']}",
             f"- verifier correlation: {facts['verifier_correlation']}",
             f"- closure correlation: {facts['closure_correlation']}",
             f"- requested actions: {', '.join(facts['actions'])}",
             f"- closure request sha256: {facts['request_sha256']}", ""]
    return "\n".join(lines).encode()


class RegistryClosure:
    """The CLOSURE control plane (`ClosureActions`): it prepares the exact landing, journals the order before the first
    irreversible effect, hands it to the Landing Authority, reads every effect back, recovers after a crash and alone
    issues receipts and control-plane findings. It never runs or trusts a session."""

    def __init__(self, registry: WorkRegistry, root: Path, journal: JsonlInvocationJournal,
                 preparation: LaunchPreparation, authority: LandingAuthority | None) -> None:
        self._registry, self._root, self._journal = registry, Path(root), journal
        self._preparation, self._authority = preparation, authority
        configuration = registry.configuration
        self._repository = configuration.packets_repository
        self._location = configuration.repositories[self._repository]
        self.worker: RealWorkerProvider | None = None  # set by `_launch_chain`, for PRODUCER worktree disposal
        self.worker_workspaces: WorkerCloneAdapter | None = None  # with a worker user, its clones' removal
        self.cleanup_diagnostics: dict[str, str] = {}

    # --- ClosureActions -------------------------------------------------------------------------------------------

    def close(self, invocation: WorkerInvocation, candidate: CandidateRef, journal) -> tuple[tuple[str, ...], tuple[str, ...]]:
        identity, revision = invocation.work_identity, candidate.locator.rpartition("@")[2]
        try:
            document = self._preparation.read(self._preparation.closure_request_path(invocation.correlation_id))
        except OSError:
            document = None
        request = parse_request(document, identity, revision)
        if isinstance(request, str):
            return (), (hold(request),)
        findings = tuple(session_finding(text) for text in request.findings)
        actions = performable(request.actions)
        if LANDING_RECORD not in actions:
            return (), findings
        clone = self._clone(invocation.correlation_id)
        head = self._fetch(clone, candidate)
        if head is None:
            return (), (*findings, hold("remote-unreadable"))
        if self._reachable(clone, revision, head):
            return (), (*findings, hold("landing-ambiguous", head, revision))
        if not self._ancestor(clone, head, revision):
            return (), (*findings, rework(self._merge_base(clone, head, revision), head))
        digest = sha256(document).hexdigest()
        return self._order(invocation, candidate, clone, head, 1, actions, digest, findings)

    def reconcile(self, invocation: WorkerInvocation, candidate: CandidateRef,
                  orders: tuple[Mapping[str, object], ...]) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
        """Settle the last journaled order with no session. For an earlier correlation, None when it provably did
        not land; for the invocation's own order, the recovery rules of 0.4."""
        if not orders:
            return None
        last = orders[-1]
        own = last.get("correlation_id") == invocation.correlation_id
        clone = self._clone(invocation.correlation_id)
        return self._settle(invocation, candidate, clone, orders, retry=own, earlier=not own)

    # --- the landing ----------------------------------------------------------------------------------------------

    def _order(self, invocation, candidate, clone, base, attempt, actions, digest, findings):
        identity, revision = invocation.work_identity, candidate.locator.rpartition("@")[2]
        built = self._build(clone, invocation, revision, base, actions, digest)
        if isinstance(built, str):
            return (), (*findings, hold(built, base, revision))
        merge, record, path = built
        if self._authority is None:
            return (), (*findings, ready_to_land(merge))
        event = {"event": CLOSURE_ORDERED, "correlation_id": invocation.correlation_id, "work_identity": identity,
                 "role": invocation.role, "candidate": revision,
                 "order": {"base": base, "merge": merge, "record": record, "record_path": path, "attempt": attempt,
                           "actions": list(actions), "request_sha256": digest}}
        try:
            self._journal.append(event)
            journaled = [entry for entry in self._journal.records() if entry.get("event") == CLOSURE_ORDERED
                         and entry.get("correlation_id") == invocation.correlation_id]
        except (JournalUnreadable, OSError):
            journaled = []
        if not journaled or {key: journaled[-1].get(key) for key in event} != event:
            return (), (*findings, hold("order-unrecorded", base, merge, record))
        self._authority.land(self._landing_order(journaled[-1], clone))  # Trusted in neither answer.
        orders = tuple(entry for entry in self._journal.records() if entry.get("event") == CLOSURE_ORDERED
                       and entry.get("work_identity") == identity and entry.get("candidate") == revision)
        receipts, settled = self._settle(invocation, candidate, clone, orders, retry=False, earlier=False)
        return receipts, (*findings, *settled)

    def _settle(self, invocation, candidate, clone, orders, *, retry: bool, earlier: bool):
        identity, revision = invocation.work_identity, candidate.locator.rpartition("@")[2]
        last = orders[-1]
        order = last["order"]
        head = self._fetch(clone, candidate)
        if head is None:
            return (), (hold("landing-ambiguous", order["base"], order["merge"], order["record"], "unreadable"),)
        published = (receipt("candidate-published", identity, revision),) \
            if self._present(clone, revision) else ()
        landed = next((entry for entry in reversed(orders) if self._reachable(clone, entry["order"]["record"], head)),
                      None)
        if landed is not None:
            return self._after_landing(invocation, candidate, clone, landed, head, published)
        if self._reachable(clone, revision, head) or self._path_taken(clone, head, order["record_path"]):
            return published, (hold("landing-ambiguous", order["base"], order["merge"], order["record"], head),)
        if earlier:
            return None  # Provably not landed: a new session may start.
        if head == order["base"]:
            if self._authority is None:
                return published, (ready_to_land(order["merge"]),)
            if retry:
                self._authority.land(self._landing_order(last, clone))
                return self._settle(invocation, candidate, clone, orders, retry=False, earlier=False)
            return published, (hold("landing-refused", order["base"], order["merge"], order["record"]),)
        # Main moved and our order did not land (the push is fast-forward only).
        if not self._ancestor(clone, head, revision):
            return published, (rework(order["base"], head),)
        if int(order["attempt"]) >= MAX_ORDERS:
            return published, (hold("base-unstable", order["base"], head),)
        actions = tuple(order["actions"])
        receipts, findings = self._order(invocation, candidate, clone, head, int(order["attempt"]) + 1, actions,
                                         str(order["request_sha256"]), ())
        return tuple(dict.fromkeys((*published, *receipts))), findings

    def _after_landing(self, invocation, candidate, clone, landed, head, published):
        identity, revision = invocation.work_identity, candidate.locator.rpartition("@")[2]
        order, actions = landed["order"], tuple(landed["order"]["actions"])
        unverified = self._unverified(clone, identity, revision, order)
        if unverified is not None:
            return published, (hold("landing-unverified", order["merge"], order["record"], head),)
        receipts = [*published, receipt(MERGED_TO_MAIN, identity, revision), receipt(LANDING_RECORD, identity, revision)]
        if BOARD_UPDATED not in actions or not self._board(identity):
            return tuple(receipts), ()
        receipts.append(receipt(BOARD_UPDATED, identity, revision))
        if WORKSPACES_CLEANED in actions and self._cleanup(invocation):
            receipts.append(receipt(WORKSPACES_CLEANED, identity, revision))
        return tuple(receipts), ()

    def _build(self, clone: Path, invocation: WorkerInvocation, revision: str, base: str, actions, digest: str):
        """The merge of the candidate onto `base` and the record commit on top, checked locally; or a hold reason."""
        record = self._registry.records.show(invocation.work_identity)
        if record is None or record.packet is None:
            return "record-unreadable"
        _, raw = self._registry.store.read_state("registry", f"factory:{invocation.work_identity}")
        verdict = raw.get("verdict") if isinstance(raw.get("verdict"), dict) else {}
        identity = ("-c", f"user.name={LANDING_NAME}", "-c", f"user.email={LANDING_EMAIL}", "-c", "commit.gpgsign=false")
        if not self._git(clone, "checkout", "-q", "--detach", base, check=True) \
                or not self._git(clone, *identity, "merge", "-q", "--no-ff", "--no-edit", "-m",
                                 f"Land {invocation.work_identity} candidate {revision}", revision, check=True):
            self._git(clone, "merge", "--abort")
            return "merge-failed"
        merge = self._git(clone, "rev-parse", "HEAD")
        if self._parents(clone, merge) != [base, revision] or self._tree(clone, merge) != self._tree(clone, revision):
            return "merge-tree"
        path = landing_record_path(record.item.label, invocation.work_identity, revision)
        data = render_landing_record({
            "identity": invocation.work_identity, "label": record.item.label, "candidate": revision, "base": base,
            "merge": merge, "instructions_sha256": sha256(record.packet).hexdigest(),
            "verifier_correlation": verdict.get("verifier_correlation"),
            "closure_correlation": invocation.correlation_id, "actions": list(actions), "request_sha256": digest})
        target = clone / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if not self._git(clone, "add", "--", path, check=True) or not self._git(
                clone, *identity, "commit", "-q", "-m", f"Landing record for {invocation.work_identity}", check=True):
            return "record-failed"
        commit = self._git(clone, "rev-parse", "HEAD")
        if self._parents(clone, commit) != [merge] or self._git(
                clone, "diff-tree", "--no-commit-id", "--name-status", "-r", merge, commit) != f"A\t{path}":
            return "record-changes"
        return merge, commit, path

    def _unverified(self, clone: Path, identity: str, revision: str, order: Mapping[str, object]) -> str | None:
        """Read-back of a landed order: the record's only parent is the merge, the merge's parents are (base,
        candidate) with the candidate's tree, and the shared landing check passes on the fetched default branch."""
        merge, record = str(order["merge"]), str(order["record"])
        if self._parents(clone, record) != [merge] or self._parents(clone, merge) != [order["base"], revision] \
                or self._tree(clone, merge) != self._tree(clone, revision):
            return "commits"
        shown = self._registry.records.show(identity)

        def read(pointer: StoredPointer) -> bytes:
            result = subprocess.run(["git", "show", f"{pointer.commit}:{pointer.path}"], cwd=clone,
                                    env=git_environment(clone), capture_output=True, check=False, timeout=120)
            if result.returncode:
                raise GitReadFailed("git show", str(clone), "missing")
            return result.stdout

        checked = landing_check(GitRevisionResolver({self._repository: clone}), read, self._repository,
                                self._tracking, revision, record, str(order["record_path"]), identity,
                                b"" if shown is None or shown.packet is None else shown.packet)
        return checked if isinstance(checked, str) else None

    def _landing_order(self, event: Mapping[str, object], clone: Path) -> LandingOrder:
        order = event["order"]
        return LandingOrder(str(event["work_identity"]), str(event["candidate"]), str(event["correlation_id"]),
                            order["base"], order["merge"], order["record"], order["record_path"], clone,
                            tuple(order["actions"]), order["attempt"])

    # --- board and cleanup ----------------------------------------------------------------------------------------

    def _board(self, identity: str) -> bool:
        """`work display` reads back current, and the card's Status reads back DONE after the write."""
        try:
            links = self._registry.links
            shown = links.display(identity)
            if shown.answer is not None or shown.card_id is None:
                return False
            links.board.write_status(shown.card_id, "DONE", 0)
            return links.board.read_status(shown.card_id).status == "DONE"
        except Exception:  # noqa: BLE001 - an unconfirmed board update issues no receipt
            return False

    def _cleanup(self, invocation: WorkerInvocation) -> bool:
        """Every workspace owned by a journaled correlation of this work item, under the ownership checks; the
        running correlation's landing clone last. Anything kept is named in `cleanup_diagnostics`."""
        try:
            started = [entry for entry in self._journal.records() if entry.get("event") == "invocation-started"
                       and entry.get("work_identity") == invocation.work_identity]
        except JournalUnreadable:
            self.cleanup_diagnostics[invocation.correlation_id] = "journal unreadable"
            return False
        ownership, verifier, kept, last = self._registry.ownership, self._root / "verifier", False, None
        for entry in started:
            correlation = str(entry.get("correlation_id"))
            if not correlation or any(part in correlation for part in ("/", "\\", "..", "\x00")):
                continue
            running = correlation == invocation.correlation_id
            owner = entry.get("owner")
            reason = None
            if not isinstance(owner, dict):
                reason = "no journaled owner"
            else:
                try:
                    if not running and ownership.owner_state(owner) != "terminated":
                        reason = "owner alive"
                    elif ownership.owned_work(correlation, owner_token(owner)) != ():
                        reason = "marked process alive"
                except Exception as error:  # noqa: BLE001 - an unreadable observation keeps the workspace
                    reason = f"ownership unreadable: {type(error).__name__}"
            if entry.get("role") == PRODUCER and self.worker is not None:
                worktree = _producer_worktree(self._root / "workspaces", WorkerInvocation(
                    invocation.work_identity, correlation)) if self.worker_workspaces is None else _producer_worktree(
                    self._root / "worker", WorkerInvocation(invocation.work_identity, correlation), "producer-")
                if worktree is not None and worktree.path.exists():
                    if reason is None:
                        self.worker.finalize(WorkerInvocation(invocation.work_identity, correlation), False)
                    if worktree.path.exists():
                        kept = True
                        self.cleanup_diagnostics[str(worktree.path)] = reason or "worktree kept"
            if self.worker_workspaces is not None:  # worker clones: removed only as the worker
                for prefix in ("verifier", "closure"):
                    path = (self._root / "worker").resolve() / f"{prefix}-{workspace_folder(correlation)}"
                    if not os.path.lexists(path):
                        continue
                    if reason is None:
                        try:
                            self.worker_workspaces.cleanup(GitWorkspace(correlation, invocation.work_identity, path,
                                                                        ""), None)
                        except CandidateUnavailable:
                            pass
                    if os.path.lexists(path):
                        kept = True
                        self.cleanup_diagnostics[str(path)] = reason or "not removable"
            for prefix in _WORKSPACE_PREFIXES:
                path = (self._root / "landing" if prefix == "landing" else verifier) / f"{prefix}-{workspace_folder(correlation)}"
                if not path.exists():
                    continue
                if reason is not None:
                    kept = True
                    self.cleanup_diagnostics[str(path)] = reason
                elif running and prefix == "landing":
                    last = path
                else:
                    shutil.rmtree(path, ignore_errors=True)
                    if path.exists():
                        kept = True
                        self.cleanup_diagnostics[str(path)] = "not removable"
        if last is not None:
            shutil.rmtree(last, ignore_errors=True)
            if last.exists():
                kept = True
                self.cleanup_diagnostics[str(last)] = "not removable"
        return not kept

    # --- git in the landing clone ---------------------------------------------------------------------------------

    @property
    def _tracking(self) -> str:
        return f"refs/remotes/landing/{self._location.default_branch}"

    def _clone(self, correlation: str) -> Path:
        clone = self._root / "landing" / f"landing-{workspace_folder(correlation)}"  # Founder-only, outside every worker root
        if not (clone / ".git").is_dir():
            clone.mkdir(parents=True, exist_ok=True)
            self._git(clone, "init", "-q")
        return clone

    def _url(self) -> str:
        return self._git(self._location.clone, "remote", "get-url", self._location.remote)

    def _fetch(self, clone: Path, candidate: CandidateRef) -> str | None:
        """Fetch the remote default branch (and the candidate branch) fresh, with no credential; the head or None."""
        url, branch = self._url(), self._location.default_branch
        if not url or not self._git(clone, "fetch", "-q", url, f"+refs/heads/{branch}:{self._tracking}", check=True):
            return None
        reference = candidate.locator.rpartition("#")[2].rpartition("@")[0]
        if reference:
            self._git(clone, "fetch", "-q", url, f"+refs/heads/{reference}:refs/remotes/landing/candidate", check=True)
        head = self._git(clone, "rev-parse", self._tracking)
        return head or None

    def _present(self, clone: Path, revision: str) -> bool:
        return self._git(clone, "cat-file", "-e", f"{revision}^{{commit}}", check=True)

    def _reachable(self, clone: Path, commit: str, head: str) -> bool:
        return self._present(clone, commit) and self._git(clone, "merge-base", "--is-ancestor", commit, head, check=True)

    def _ancestor(self, clone: Path, head: str, revision: str) -> bool:
        """`head` is a proper ancestor of the candidate."""
        return head != revision and self._reachable(clone, head, revision)

    def _merge_base(self, clone: Path, head: str, revision: str) -> str:
        return self._git(clone, "merge-base", head, revision) or head

    def _path_taken(self, clone: Path, head: str, path: str) -> bool:
        return self._git(clone, "cat-file", "-e", f"{head}:{path}", check=True)

    def _parents(self, clone: Path, commit: str) -> list[str]:
        return self._git(clone, "rev-list", "--parents", "-n", "1", commit).split()[1:]

    def _tree(self, clone: Path, commit: str) -> str:
        return self._git(clone, "rev-parse", f"{commit}^{{tree}}")

    @staticmethod
    def _git(clone: Path, *args: str, check: bool = False):
        """git with no user configuration and no credential; `check` answers success, else the trimmed output."""
        try:
            result = subprocess.run(["git", "-c", "credential.helper=", "-c", "core.hooksPath=/dev/null", *args],
                                    cwd=clone, env=git_environment(clone), capture_output=True, check=False,
                                    timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            return False if check else ""
        if check:
            return result.returncode == 0
        return result.stdout.decode(errors="replace").strip() if result.returncode == 0 else ""
