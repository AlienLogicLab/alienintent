"""FX-C local bounded-control composition (WO-220307): C3 episodes, C1 attention, C4 monitor
health and L1 liveness over one profile root and one injected integer-microsecond UTC clock.

Wiring only: every predecessor profile is constructed unchanged. Constructing it begins no
episode, starts no monitor or reconciler, and hosts or supervises nothing
(R1-GAP-MONITOR-HOST, POSTW1-DECIDE-006A).

- The coordinator episode is fenced by its own `episode:<objective>` pointer (C3).
- Liveness recovery keeps its own dispatch authority in the liveness store (L1), so monitor
  and liveness operation continue after a model episode ends (SF-REQ-053-AC-04).
- L1 judgment attention is the C1 service on the C2 profile store, so every fresh context
  reconstructs pending judgment in `pending_attention`/`blocked_set`.
"""
from collections.abc import Callable
from datetime import UTC, datetime
from itertools import count
from pathlib import Path

from alienintent.composition.control_plane_profile import AttentionProfile, EpisodeProfile, MonitorProfile
from alienintent.composition.liveness_profile import LivenessProfile
from alienintent.control_plane.domain.attention import ResolverGrant
from alienintent.control_plane.domain.episode import SECOND, OperatorGrant, TenurePolicy
from alienintent.control_plane.domain.monitor_health import MonitorPolicy
from alienintent.control_plane.ports.attention import AttentionActivation
from alienintent.control_plane.ports.episode import ContextUsageObservation, DeadlineTimer
from alienintent.execution_coordination.domain.liveness import LivenessPolicy


class BoundedControlProfile:
    def __init__(self, root: Path, *, project: str, name: str, invocation: str, clock: Callable[[], int],
                 tenure: TenurePolicy, liveness: LivenessPolicy | None, monitor: MonitorPolicy | None,
                 timer: DeadlineTimer, operators: tuple[OperatorGrant, ...], resolvers: tuple[ResolverGrant, ...],
                 required_authority: str, usage: ContextUsageObservation | None = None,
                 activation: AttentionActivation | None = None) -> None:
        attempts, instances = count(1), count(1)
        self.attention = AttentionProfile(root, project=project, name=name, invocation=invocation,
            clock=lambda: datetime.fromtimestamp(clock() / SECOND, UTC).isoformat(),
            next_id=lambda: f"{invocation}:attempt-{next(attempts)}", resolvers=resolvers, activation=activation)
        self.monitor = MonitorProfile(root, project=project, name=name, invocation=invocation, policy=monitor,
                                      clock=clock, next_id=lambda: f"{invocation}:monitor-{next(instances)}")
        self.liveness = LivenessProfile(root, project=project, name=name, policy=liveness, clock=clock,
                                        attention=self.attention, monitor=self.monitor,
                                        required_authority=required_authority)
        self.episode = EpisodeProfile(root, project=project, name=name, invocation=invocation, monotonic=clock,
                                      utc_clock=clock, timer=timer, policy=tenure, usage=usage, operators=operators)
