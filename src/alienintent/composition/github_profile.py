"""Composition root for a fixture-backed GitHub profile."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Mapping

from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.installation.ports.secret_provider import SecretProvider


class GitHubProfileComposition:
    """Wire configuration-owned references at the outer boundary only."""

    def __init__(self, profile: GitHubProfile, secrets: SecretProvider, database: Path, snapshot: Callable[[], tuple[Mapping[str, object], ...]], contract: BiuContract, notify: Callable[[str], None], projection_write: Callable[[str, str, str, int], int] | None = None) -> None:
        self.store = SQLiteOperationalStore(database)
        writer = projection_write or (lambda identity, field, state, revision: -1)
        self.work = GitHubProjectsWorkManagement(profile.profile, profile.repository, profile.lifecycle_statuses, profile.projection_fields, snapshot, contract, writer)
        self.ingress = GitHubWebhookIngress(profile.profile, secrets.resolve(profile.webhook_secret_reference), self.store, notify)
