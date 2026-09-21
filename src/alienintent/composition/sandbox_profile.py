"""Composition root binding one recorded live GitHub profile to real transport.

Configuration is read here and nowhere else. The document holds resource
identities and secret *references* only: no secret value, no App private key
and no resolved credential is stored, returned in a diagnostic, or retained.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Callable, Mapping

from alienintent.composition.doctor_probes import (
    execution_evidence,
    live_provider_evidence,
    live_source_control_evidence,
    live_transport_evidence,
    live_work_management_evidence,
)
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory
from alienintent.execution_coordination.adapters.github_repository_api import GitHubRepositoryApi
from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress, serve_webhook
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.installation.adapters.app_jwt import app_assertion
from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor
from alienintent.installation.application.installation_credentials import InstallationCredentials
from alienintent.installation.domain.app_credentials import AppIdentity, CredentialRejected
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.installation.domain.project_identity import foreign_project_identities, foreign_repositories
from alienintent.installation.ports.github_transport import GitHubTransport

APP_KEY_REFERENCE = "app-private-key"


def load_profile_document(path: Path) -> Mapping[str, object]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise CredentialRejected("profile document is not a mapping")
    return document


def compose_profile(document: Mapping[str, object]) -> GitHubProfile:
    webhook = document.get("webhook") or {}
    return GitHubProfile(
        str(document["profile"]), str(document["repository"]), str(document["project_reference"]),
        dict(document["lifecycle_statuses"]), dict(document["projection_fields"]),
        str(document["webhook_secret_reference"]), bool(document["automatic_release"]),
        webhook_listen_address=str(webhook.get("listen_address") or ""),
        webhook_listen_port=int(webhook.get("listen_port") or 0),
        webhook_public_url=str(webhook.get("public_url") or ""),
        project_number=int(document.get("project_number") or 0),
        project_status_field=str(document.get("project_status_field") or ""),
        project_priority_field=str(document.get("project_priority_field") or ""),
    )


def compose_secrets(document: Mapping[str, object]) -> ProtectedLocalFileSecretProvider:
    """Every credential, including the App private key, resolves by reference."""
    references = {name: Path(str(location)) for name, location in (document.get("secret_references") or {}).items()}
    application = document.get("githubApp") or {}
    if APP_KEY_REFERENCE not in references:
        key_path = application.get("privateKeyPath")
        if not key_path:
            raise CredentialRejected("profile records no App private key reference")
        references[APP_KEY_REFERENCE] = Path(str(key_path))
    return ProtectedLocalFileSecretProvider(references)


def compose_identity(document: Mapping[str, object]) -> AppIdentity:
    application = document.get("githubApp") or {}
    return AppIdentity(int(application.get("applicationId") or 0), int(application.get("installationId") or 0), APP_KEY_REFERENCE)


class SandboxProfileComposition:
    """Bind credentials, repository, Project, ingress and doctor for one profile."""

    def __init__(
        self,
        document: Mapping[str, object],
        database: Path,
        contract: BiuContract,
        notify: Callable[[str], None],
        transport: GitHubTransport | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.document = document
        self.profile = compose_profile(document)
        self.secrets = compose_secrets(document)
        self.identity = compose_identity(document)
        self.address = self.profile.project_address()
        self.transport = transport or UrllibGitHubTransport()
        self.credentials = InstallationCredentials(self.identity, self.secrets, self.transport, clock, app_assertion)
        self.repository = GitHubRepositoryApi(self.profile.repository, self.transport, self.credentials.authorization)
        self.projects = GitHubProjectsV2Directory(self.address, self.transport, self.credentials.authorization)
        self.store = SQLiteOperationalStore(database)
        self.work = GitHubProjectsWorkManagement(
            self.profile.profile, self.profile.repository, self.profile.lifecycle_statuses,
            self.profile.projection_fields, self.project_snapshot, contract,
            self.project_projection_write, directory=self.projects,
        )
        self.ingress = GitHubWebhookIngress(
            self.profile.profile, self.profile.repository,
            self.secrets.resolve(self.profile.webhook_secret_reference), self.store, notify,
            project_reference=self.profile.project_reference,
        )

    # --- live work-management wiring ----------------------------------------

    def project_snapshot(self) -> tuple[Mapping[str, object], ...]:
        """Live Project items, described only by what the Project actually answers."""
        schema = self.projects.schema()
        return tuple(
            {
                "identity": item.item_id, "repository": self.profile.repository,
                "membership": True, "complete": True, "status": item.status,
                "priority": item.priority, "dependencies": [],
                "contract": "", "contract_digest": item.item_id, "readiness": item.status or "",
                "wave": "", "source_version": schema.project_id,
            }
            for item in self.projects.items()
            if item.status in self.profile.lifecycle_statuses
        )

    def project_projection_write(self, identity: str, field: str, state: str, revision: int) -> int:
        """Apply a fenced lifecycle projection to the configured Project only."""
        return self.projects.write_status(identity, state, revision)

    # --- credentialed source control ----------------------------------------

    def authenticated_remote(self) -> str:
        """Secret-bearing remote URL for installation-credentialed candidate custody.

        Never logged and never recorded: candidate evidence carries the
        userinfo-stripped form `GitSourceControl` derives from it.
        """
        return f"https://x-access-token:{self.credentials.token().value}@github.com/{self.profile.repository}.git"

    # --- isolation evidence --------------------------------------------------

    def isolation_findings(self) -> tuple[str, ...]:
        """Repository scope as GitHub enforces it, Project addressing as configuration enforces it.

        This never claims the token reaches only the configured Project:
        `organization_projects` is organization scoped and cannot provide that.
        """
        configuration = json.dumps(dict(self.document), sort_keys=True)
        findings = tuple(
            f"configuration names project {identity}"
            for identity in foreign_project_identities(configuration, self.profile.project_reference)
        )
        findings += tuple(
            f"configuration targets repository {name}"
            for name in foreign_repositories((str(self.document.get("repository") or ""),), self.profile.repository)
        )
        return findings + self.credentials.repository_scope_findings(self.profile.repository)

    # --- doctor --------------------------------------------------------------

    def resident_ingress(self):
        """Serve the ingress on the bind address and port the profile records."""
        return serve_webhook(self.ingress, self.profile.webhook_listen_address or "127.0.0.1", self.profile.webhook_listen_port)

    def doctor(self, workspace_root: Path, repository_workspace: Path, worker: object, executable: str) -> InstallationDoctor:
        granted = self.credentials.granted_permissions()
        return InstallationDoctor(DoctorDependencies(
            self.profile, self.secrets,
            lambda: live_work_management_evidence(self.work, self.profile, granted),
            lambda: live_source_control_evidence(self.repository, granted, self.authenticated_remote()),
            lambda: live_provider_evidence(worker, executable),
            lambda: live_transport_evidence(self.profile, self.secrets),
            lambda: {"preflight": lambda: SQLiteOperationalStore.preflight(self.store.path)},
            lambda: execution_evidence(repository_workspace, workspace_root, worker, executable),
        ))
