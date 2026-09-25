"""Explicit local attention and monitor composition; no bootstrap cutover or host activation."""
from collections.abc import Callable
from pathlib import Path

from alienintent.control_plane.adapters.attention_import import BootstrapAttentionImport
from alienintent.control_plane.adapters.attention_repository import DurableAttentionRepository
from alienintent.control_plane.adapters.monitor_health_repository import DurableMonitorRepository
from alienintent.control_plane.application.attention import AttentionService
from alienintent.control_plane.application.monitor_health import MonitorService
from alienintent.control_plane.domain.attention import ActivationPolicy, ResolverGrant
from alienintent.control_plane.domain.monitor_health import MonitorPolicy
from alienintent.control_plane.ports.attention import AttentionActivation, AttentionNotifier
from alienintent.control_plane.ports.monitor_health import MonitorHealthPort
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore


class AttentionProfile:
    def __init__(self, root: Path, *, project: str, name: str, invocation: str,
                 clock: Callable[[], str], next_id: Callable[[], str], resolvers: tuple[ResolverGrant, ...],
                 notifier: AttentionNotifier | None = None, activation: AttentionActivation | None = None,
                 activation_policy: ActivationPolicy | None = None) -> None:
        root = Path(root).resolve(strict=True)
        self.store = SQLiteOperationalStore(root / "attention.sqlite")
        self.evidence = LocalEvidenceRepository(root / "attention-evidence", project, name)
        self.repository = DurableAttentionRepository(self.store, self.evidence,
            project=project, profile=name, invocation=invocation)
        self.attention = AttentionService(self.repository, project=project, profile=name,
            clock=clock, next_id=next_id, resolvers=resolvers, notifier=notifier,
            activation=activation, activation_policy=activation_policy)
        self.migration = BootstrapAttentionImport(self.repository, project=project, profile=name)


class MonitorProfile:
    """Local monitor-health composition. Constructing it starts, hosts and supervises nothing
    (R1-GAP-MONITOR-HOST): an external caller drives `start`, `tick` and scan progress."""

    def __init__(self, root: Path, *, project: str, name: str, invocation: str,
                 policy: MonitorPolicy | None, clock: Callable[[], object], next_id: Callable[[], str]) -> None:
        root = Path(root).resolve(strict=True)
        self.store = SQLiteOperationalStore(root / "monitor.sqlite")
        self.evidence = LocalEvidenceRepository(root / "monitor-evidence", project, name)
        self.repository = DurableMonitorRepository(self.store, self.evidence,
            project=project, name=name, invocation=invocation)
        self.health: MonitorHealthPort = self.repository
        self.monitor = MonitorService(self.repository, profile=name, policy=policy, clock=clock, next_id=next_id)
