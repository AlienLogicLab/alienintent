"""Explicit local SF-REQ-056 liveness composition (L1); no host, supervisor or bootstrap cutover.

Binds the reconciler to the real SQLite store observation adapter, the shared
canonical effect admission and guarded executor, C1 attention and C4 monitor
health. Constructing it starts nothing (R1-GAP-MONITOR-HOST): an external caller
drives `reconciler.start()` and each `reconciler.scan()`. It scans only
already-known active records, and binds no remote worker provider.
"""
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

from alienintent.composition.control_plane_profile import AttentionProfile, MonitorProfile
from alienintent.control_plane.application.monitor_health import MonitorService
from alienintent.control_plane.domain.attention import AttentionHold, AttentionOrigin
from alienintent.control_plane.ports.attention import AttentionPort
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.adapters.liveness_observations import StoreEffectObservation, StoreLifecycleJournal
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.liveness import CanonicalEffectAdmission, LivenessReconciler
from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome, KnownActive, LivenessHold, LivenessPolicy
from alienintent.execution_coordination.ports.liveness import (
    JudgmentAttention, JudgmentState, MonitorHealthView, Unavailable,
)
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible, StoreUnavailable, VersionConflict


class AttentionJudgment(JudgmentAttention):
    """One attributable C1 JUDGMENT item per correlated outcome; resolution stays C1's authority."""

    def __init__(self, attention: AttentionPort, *, project: str, profile: str, required_authority: str,
                 producer: str = "liveness-reconciler") -> None:
        self.attention, self.project, self.profile = attention, project, profile
        self.required_authority, self.producer = required_authority, producer

    def origin(self, active: KnownActive, outcome: CorrelatedOutcome) -> AttentionOrigin:
        body = [outcome.identity, outcome.biu, outcome.generation, outcome.role_key, outcome.kind, outcome.sequence]
        source = Ref(self.project, self.profile, outcome.identity, "sha256:" + sha256(canonical_bytes(body)).hexdigest(),
                     "liveness-outcome:" + outcome.biu)
        return AttentionOrigin(active.biu, outcome.identity, "JUDGMENT",
                               f"{active.contract_digest}:generation:{active.generation}", outcome.role_key,
                               self.required_authority, self.producer, source)

    def ensure_judgment(self, active: KnownActive, outcome: CorrelatedOutcome) -> JudgmentState | Unavailable:
        try:
            item = self.attention.ensure(self.origin(active, outcome))
        except (AttentionHold, EvidenceHold, KeyError, StoreUnavailable, SchemaIncompatible, VersionConflict) as error:
            return Unavailable(type(error).__name__ + ":" + str(error))
        return JudgmentState(item.identity, item.status)


class MonitorHealthBridge(MonitorHealthView):
    def __init__(self, monitor: MonitorService | None) -> None:
        self.monitor = monitor

    def health(self) -> tuple[str, str]:
        if self.monitor is None:
            return "UNVERIFIED", "MONITOR_UNBOUND"
        report = self.monitor.inspect()
        return str(report.status), report.reason


class LivenessProfile:
    def __init__(self, root: Path, *, project: str, name: str, policy: LivenessPolicy | None,
                 clock: Callable[[], object], attention: AttentionProfile, monitor: MonitorProfile | None,
                 required_authority: str) -> None:
        if not isinstance(policy, LivenessPolicy):
            raise LivenessHold("POLICY_MISSING" if policy is None else "POLICY_INVALID")
        policy.validate()
        root = Path(root).resolve(strict=True)

        def store_seconds() -> float | None:
            now = clock()
            return now / 1_000_000 if type(now) is int else None

        self.store = SQLiteOperationalStore(root / "liveness.sqlite", clock=store_seconds)
        self.observations = StoreEffectObservation(self.store, profile=name)
        self.journal = StoreLifecycleJournal(self.store, profile=name)
        self.admission = CanonicalEffectAdmission(self.store, profile=name, clock=clock)
        self.judgment = AttentionJudgment(attention.attention, project=project, profile=attention.attention.profile,
                                          required_authority=required_authority)
        service = None if monitor is None else monitor.monitor
        self.reconciler = LivenessReconciler(self.store, self.observations, self.judgment, MonitorHealthBridge(service),
                                             self.admission, profile=name, policy=policy, clock=clock, progress=service)
