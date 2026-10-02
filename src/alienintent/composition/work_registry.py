"""Project work registry composition: one project database, one configured clone per repository, every profile.

The project-level configuration entry is looked up by the project string already threaded through UpstreamProfile.
It names the one project database file, maps each repository name to its one configured clone (with the remote
that clone publishes to, named explicitly, and the default and packets branches that retain packet commits), names
where compiled packets are written, and lists every configured profile of the project with its own operational
database path. Each profile's database is opened read-only in effect (it must already exist at the current schema,
so opening it writes nothing) for the compiler's migration check and `work migrate`. The same WorkIdentityService,
repository adapter and publisher are handed to every client of the project.

Configuration document (JSON):

    {"schema_version": 1, "projects": {"<project>": {
        "database": "<path to the project work database>",
        "repositories": {"<name>": {"clone": "<path>", "remote": "origin", "default_branch": "main",
                                    "packets_branch": "alienintent/work-packets"}},
        "packets": {"repository": "<name>", "directory": "work-packets"},
        "profiles": {"<profile>": "<path to that profile's operational state.sqlite>"}}}}
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path

from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.application.initial_compilation_service import PacketLocation, WorkRegistration
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.ports.work_item_repository import RepositoryLocation
from alienintent.execution_coordination.adapters.sqlite_store import SCHEMA_VERSION, SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.ports.source_control import SourceControl


class ConfigurationInvalid(ValueError):
    """The project-level configuration entry is missing or malformed; nothing was opened."""


@dataclass(frozen=True)
class ProjectConfiguration:
    project: str
    database: Path
    repositories: Mapping[str, RepositoryLocation]
    packets_repository: str
    packets_directory: str
    profiles: Mapping[str, Path]


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
        configuration = ProjectConfiguration(project, Path(entry["database"]), repositories, packets["repository"],
                                             packets["directory"], profiles)
    except ConfigurationInvalid:
        raise
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ConfigurationInvalid(f"project {project}: {type(error).__name__}: {error}") from None
    if configuration.packets_repository not in repositories or not profiles or not all(
            isinstance(name, str) and name for name in [*repositories, *profiles]):
        raise ConfigurationInvalid(f"project {project}: packets repository and profiles must be configured")
    return configuration


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


class WorkRegistry:
    """The one work identity service of a project, with its repository adapter and publisher."""

    def __init__(self, configuration: ProjectConfiguration, source_control: SourceControl | None = None) -> None:
        self.configuration = configuration
        self.profile_stores = {name: read_only_store(path) for name, path in sorted(configuration.profiles.items())}
        self.items = SQLiteWorkItemRepository(configuration.database, configuration.repositories)
        self.source_control = source_control if source_control is not None else GitSourceControl()
        self.identities = WorkIdentityService(self.items, self.source_control, configuration.repositories,
                                              self.profile_stores)
        self.registration = WorkRegistration(
            self.identities, self.items, self.source_control,
            PacketLocation(configuration.packets_repository, configuration.packets_directory,
                           configuration.repositories[configuration.packets_repository]),
            self.profile_stores)
