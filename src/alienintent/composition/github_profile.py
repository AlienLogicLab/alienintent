"""Composition root for a fixture-backed GitHub profile."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import time
from typing import Mapping

from alienintent.composition.role_binding import RoleBindingGuard
from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.control_plane.adapters.decision_notifier import WorkManagementDecisionNotifier
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.installation.ports.secret_provider import SecretProvider
from alienintent.execution_coordination.ports.worker_provider import WorkerProvider
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal


class GitHubProfileComposition:
    """Wire configuration-owned references at the outer boundary only."""

    def __init__(self, profile: GitHubProfile, secrets: SecretProvider, database: Path, snapshot: Callable[[], tuple[Mapping[str, object], ...]], contract: BiuContract, notify: Callable[[str], None], projection_write: Callable[[str, str, str, int], int] | None = None, worker: WorkerProvider | None = None, decision_projection_write: Callable[[HumanDecisionRequired], str] | None = None, journal: InvocationJournal | None = None, clock: Callable[[], float] = time.time) -> None:
        self.store = SQLiteOperationalStore(database)
        writer = projection_write or (lambda identity, field, state, revision: -1)
        self.work = GitHubProjectsWorkManagement(profile.profile, profile.repository, profile.lifecycle_statuses, profile.projection_fields, snapshot, contract, writer, decision_projection_write)
        self.ingress = GitHubWebhookIngress(profile.profile, profile.repository, secrets.resolve(profile.webhook_secret_reference), self.store, notify)
        # A real profile reaches the supplied real worker through the same control
        # plane as the offline double; no provider type crosses that boundary.
        # K3: it is reached only through the binding guard, so a worker not
        # bound to ``journal`` or to the launched role and candidate never starts.
        self.worker = None if worker is None else RoleBindingGuard(worker, journal, self.store, profile.profile, profile.repository, clock)
        self.coordinator = None if self.worker is None else FactoryCoordinator(
            self.store, self.work, self.worker,
            LocalArtifactStore(database.parent / "candidate-artifacts", database.parent / "candidate-artifacts" / "verifier-evidence"), profile.profile,
            automatic_release=profile.automatic_release,
            notifier=WorkManagementDecisionNotifier(self.work),
        )
