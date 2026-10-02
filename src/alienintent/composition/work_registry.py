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
(its private key file named directly); without it the project has no link service.

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
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from alienintent.composition.readiness import assessment_environment, compose_producer, resolve_binding
from alienintent.composition.sandbox_profile import APP_KEY_REFERENCE
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.application.initial_compilation_service import PacketLocation, WorkRegistration
from alienintent.context_assembly.application.packet_assessment import PacketAssessment
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.application.work_link import WorkLink
from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.work_identity import valid_path
from alienintent.context_assembly.ports.work_item_repository import (
    PacketRef, PublicationFailed, RefPublisher, RepositoryLocation)
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters import assessment_consumer
from alienintent.execution_coordination.adapters.assessment_consumer import RetainedAssessmentConsumer
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory
from alienintent.execution_coordination.adapters.github_repository_api import GitHubRepositoryApi
from alienintent.execution_coordination.adapters.sqlite_store import SCHEMA_VERSION, SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import OperationalStore
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
    return project_configuration(document, project)


def read_only_store(path: Path) -> OperationalStore:
    """A configured profile's existing operational database at the current schema: opening it writes nothing.
    A missing file or another schema is refused rather than created or migrated."""
    if not Path(path).is_file():
        raise ConfigurationInvalid(f"profile database {path} does not exist")
    preflight = SQLiteOperationalStore.preflight(Path(path))
    if preflight.current_version != SCHEMA_VERSION or preflight.migration is not None:
        raise ConfigurationInvalid(f"profile database {path} is not at schema {SCHEMA_VERSION}")
    return SQLiteOperationalStore(Path(path))


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
                 transport: GitHubTransport | None = None) -> None:
        self.configuration = configuration
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
        self.links = self._links(configuration.github, transport) if configuration.github is not None else None

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
                        GitHubProjectsV2Directory(github.project, transport, credentials.authorization), credentials)

    def _assessment(self, configuration: ProjectConfiguration) -> PacketAssessment:
        """`work assess` over its own retained-assessment store; each attempt's Agent Ready launch carries the
        worker runtime's invocation markers naming that attempt and the recorded owner process."""
        readiness, profile = configuration.readiness, "work-preparation"
        definition_ref = Ref(configuration.project, profile, "readiness-consumer",
                             "sha256:" + sha256(Path(assessment_consumer.__file__).read_bytes()).hexdigest(),
                             "python:alienintent.execution_coordination.adapters.assessment_consumer")
        consumer = RetainedAssessmentConsumer(
            LocalEvidenceRepository(readiness.evidence_root, configuration.project, profile),
            SQLiteOperationalStore(readiness.database), configuration.project, profile, definition_ref,
            "alienintent work assess", frozenset({"public", "private"}))
        binding = resolve_binding(readiness.executable, "cli")
        return PacketAssessment(self.records, self.identities, consumer, binding, ProcOwnership(),
                                lambda attempt, owner: compose_producer(binding, readiness.provider, {
                                    **assessment_environment(), INVOCATION_MARKER: attempt,
                                    INVOCATION_OWNER_MARKER: owner_token(owner)}))


def work_registry_profile() -> SimpleNamespace:
    """The CLI's `--profile-factory alienintent.composition.work_registry:work_registry_profile` for the `work`
    commands: the project configuration file named by ALIENINTENT_PROJECT_CONFIGURATION and the project named by
    ALIENINTENT_PROJECT, both required; exposes `work_registry`."""
    path, project = (os.environ.get(name) for name in ("ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"))
    if not path or not project:
        raise ConfigurationInvalid("ALIENINTENT_PROJECT_CONFIGURATION and ALIENINTENT_PROJECT are required")
    return SimpleNamespace(work_registry=WorkRegistry(load_project_configuration(Path(path), project)))
