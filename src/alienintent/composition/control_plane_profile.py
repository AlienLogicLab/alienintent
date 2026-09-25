"""Explicit local attention, context and monitor composition; no bootstrap cutover or host activation."""
from collections.abc import Callable
import json
from pathlib import Path

from alienintent.context_assembly.application.reconstruction_service import ContextReconstructionService
from alienintent.context_assembly.domain.reconstruction import ContextHold, digest, validate_manifest
from alienintent.context_assembly.ports.context_assembler import ContextAssembler
from alienintent.control_plane.adapters.attention_import import BootstrapAttentionImport
from alienintent.control_plane.adapters.attention_repository import DurableAttentionRepository
from alienintent.control_plane.adapters.episode_repository import DurableEpisodeRepository
from alienintent.control_plane.adapters.monitor_health_repository import DurableMonitorRepository
from alienintent.control_plane.application.attention import AttentionService
from alienintent.control_plane.application.episode_control import EpisodeControlService
from alienintent.control_plane.application.monitor_health import MonitorService
from alienintent.control_plane.domain.attention import ActivationPolicy, ResolverGrant
from alienintent.control_plane.domain.episode import OperatorGrant, TenurePolicy
from alienintent.control_plane.domain.monitor_health import MonitorPolicy
from alienintent.control_plane.ports.attention import AttentionActivation, AttentionNotifier
from alienintent.control_plane.ports.episode import (
    ContextSource, ContextUnavailable, ContextUsageObservation, ContextView, DeadlineTimer,
)
from alienintent.control_plane.ports.monitor_health import MonitorHealthPort
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore, SchemaIncompatible, StoreUnavailable,
)


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
        self.context = ContextReconstructionService(self.store, self.evidence, project=project,
            profile=name, invocation=invocation)


class ContextProfile:
    """A successor's view of an existing profile; it never creates a store."""

    def __init__(self, root: Path, *, project: str, name: str, invocation: str) -> None:
        root = Path(root).resolve(strict=True)
        database = root / "attention.sqlite"
        if not database.is_file():
            raise StoreUnavailable("profile store is absent")
        self.store = SQLiteOperationalStore(database)
        self.evidence = LocalEvidenceRepository(root / "attention-evidence", project, name)
        self.context = ContextReconstructionService(self.store, self.evidence, project=project,
            profile=name, invocation=invocation)


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


class EpisodeContext(ContextSource):
    """C2 reconstruction translated for C3; the only C3 import of context_assembly (U-9)."""

    def __init__(self, assembler: ContextAssembler, store: OperationalStore, evidence: LocalEvidenceRepository, *,
                 project: str, profile: str) -> None:
        self.assembler, self.store, self.evidence = assembler, store, evidence
        self.project, self.profile = project, profile

    def pin(self) -> str | ContextUnavailable:
        try:
            return self.assembler.pin()
        except ContextHold as hold:
            return ContextUnavailable(str(hold.reason), hold.affected_refs)

    def entries(self, manifest_ref: str) -> tuple[tuple[str, int], ...] | ContextUnavailable:
        """The manifest's pinned `{aggregate: version}` pairs, read without comparing live state."""
        try:
            _, pointer = self.store.read_state(self.profile, manifest_ref)
            record = self.evidence.get(ref_from_document(pointer["manifest_ref"]), frozenset({"public", "private"}))
            if not isinstance(record, Observation) or not isinstance(record.value, str):
                return ContextUnavailable("INVALID_MANIFEST", (manifest_ref,))
            manifest = validate_manifest(json.loads(record.value), self.project, self.profile)
            if digest(manifest) != pointer["manifest_digest"]:
                return ContextUnavailable("DIGEST_MISMATCH", (manifest_ref,))
        except ContextHold as hold:
            return ContextUnavailable(str(hold.reason), hold.affected_refs)
        except (KeyError, TypeError, ValueError, EvidenceHold, StoreUnavailable, SchemaIncompatible) as error:
            return ContextUnavailable("MANIFEST_UNAVAILABLE", (manifest_ref, str(error)))
        return tuple((entry["aggregate"], entry["version"]) for entry in manifest["entries"])

    def reconstruct(self, manifest_ref: str) -> ContextView | ContextUnavailable:
        result = self.assembler.reconstruct(manifest_ref)
        if isinstance(result, ContextHold):
            return ContextUnavailable(str(result.reason), result.affected_refs)
        document = dict(result.document)
        return ContextView(result.manifest_ref, document, digest(document))


class EpisodeProfile:
    """Local bounded-episode composition over the C2 profile store. Constructing it begins nothing;
    the caller drives `begin`, `submit`, `tick` and events (no bootstrap handoff, POSTW1-DECIDE-006A)."""

    def __init__(self, root: Path, *, project: str, name: str, invocation: str,
                 monotonic: Callable[[], int], utc_clock: Callable[[], int], timer: DeadlineTimer,
                 policy: TenurePolicy, usage: ContextUsageObservation | None = None,
                 context_assembler: ContextAssembler | None = None, operators: tuple[OperatorGrant, ...]) -> None:
        root = Path(root).resolve(strict=True)
        self.store = SQLiteOperationalStore(root / "attention.sqlite", clock=lambda: self.episodes.store_seconds())
        self.evidence = LocalEvidenceRepository(root / "episode-evidence", project, name)
        context_evidence = LocalEvidenceRepository(root / "attention-evidence", project, name)
        assembler = context_assembler or ContextReconstructionService(self.store, context_evidence, project=project,
                                                                       profile=name, invocation=invocation)
        self.context = EpisodeContext(assembler, self.store, context_evidence, project=project, profile=name)
        self.repository = DurableEpisodeRepository(self.store, self.evidence, project=project, profile=name,
                                                   invocation=invocation)
        self.episodes = EpisodeControlService(self.repository, self.store, self.context, profile=name,
            invocation=invocation, monotonic=monotonic, utc_clock=utc_clock, timer=timer, policy=policy,
            usage=usage, operators=operators)
