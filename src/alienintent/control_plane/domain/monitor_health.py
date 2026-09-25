"""Monitor liveness values and the ordered health rule; no clock, host or supervisor.

Times are integer UTC microseconds since the Unix epoch, so boundaries compare
exactly. Health is classified from persisted observations only; workload quiet
is never health evidence.
"""
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
import json
import math

from alienintent.evidence_learning.domain.refs import Ref

# U3 (pinned): scan staleness is measured from the last completed scan, not next_scan_due.
SCAN_AGE_FROM_LAST_COMPLETION = "SCAN_AGE_FROM_LAST_COMPLETION"
INCOMPLETE_SCAN_OUTCOMES = frozenset({"STARTED", "FAILED", "EVIDENCE_HOLD"})
SCAN_OUTCOMES = INCOMPLETE_SCAN_OUTCOMES | {"COMPLETE"}


class MonitorHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class Unavailable:
    reason: str


@dataclass(frozen=True)
class MonitorPolicy:
    """Only the scan interval I; G/C policy belongs to SF-REQ-056 reconciliation."""
    interval_seconds: int | float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        value = self.interval_seconds
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise MonitorHold("POLICY_INVALID")

    @property
    def interval_micros(self) -> Fraction:
        return Fraction(self.interval_seconds) * 1_000_000

    def document(self) -> dict[str, object]:
        return {"interval_seconds": self.interval_seconds}

    def digest(self) -> str:
        body = json.dumps(self.document(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return "sha256:" + sha256(body.encode()).hexdigest()


@dataclass(frozen=True)
class MonitorHealth:
    """Exactly the `#/shared_contracts/monitor_liveness` record fields."""
    profile: str
    instance_id: str
    generation: int
    policy_digest: str
    started_at: int
    last_monitor_tick: int | None
    last_scan_started_at: int | None
    last_scan_completed_at: int | None
    last_scan_outcome: str | None
    next_scan_due: int | None
    last_error: str | None

    def __post_init__(self) -> None:
        times = (self.started_at, self.last_monitor_tick, self.last_scan_started_at,
                 self.last_scan_completed_at, self.next_scan_due)
        if (any(not isinstance(v, str) or not v.strip() for v in (self.profile, self.instance_id, self.policy_digest))
                or type(self.generation) is not int or self.generation < 1
                or type(self.started_at) is not int
                or any(v is not None and type(v) is not int for v in times)
                or self.last_scan_outcome not in SCAN_OUTCOMES | {None}
                or self.last_error is not None and not isinstance(self.last_error, str)):
            raise MonitorHold("INVALID_MONITOR_RECORD")

    def latest_observation(self) -> int:
        return max(v for v in (self.started_at, self.last_monitor_tick, self.last_scan_started_at,
                               self.last_scan_completed_at) if v is not None)


@dataclass(frozen=True)
class MonitorSnapshot:
    version: int
    record: MonitorHealth
    policy: MonitorPolicy
    history_ref: Ref


@dataclass(frozen=True)
class HealthReport:
    status: HealthStatus
    reason: str
    record: MonitorHealth | None
    observed_at: int | None


def valid_clock_reading(value: object) -> bool:
    return type(value) is int and value >= 0


def _overdue(age: int, bound: Fraction) -> bool:
    # At exactly 2*I the observation is still within bound.
    return age > bound


def classify(record: MonitorHealth | None, policy: MonitorPolicy | None, now: object) -> tuple[HealthStatus, str]:
    """Ordered rule: UNVERIFIED, then STALE, then DEGRADED, otherwise HEALTHY.

    `policy` is the persisted policy of the record's generation.
    """
    if not valid_clock_reading(now):
        return HealthStatus.UNVERIFIED, "CLOCK_INVALID"
    if record is None:
        return HealthStatus.UNVERIFIED, "NO_RECORD"
    if policy is None or record.policy_digest != policy.digest():
        return HealthStatus.UNVERIFIED, "POLICY_DIGEST_MISMATCH"
    if now < record.latest_observation():
        return HealthStatus.UNVERIFIED, "CLOCK_REGRESSION"
    bound = 2 * policy.interval_micros
    # A generation with no tick or completed scan yet is measured from its start.
    tick_reference = record.started_at if record.last_monitor_tick is None else record.last_monitor_tick
    scan_reference = record.started_at if record.last_scan_completed_at is None else record.last_scan_completed_at
    if _overdue(now - tick_reference, bound):
        return HealthStatus.STALE, "TICK_OVERDUE"
    if _overdue(now - scan_reference, bound):
        return HealthStatus.STALE, "SCAN_OVERDUE"
    if record.last_scan_outcome in INCOMPLETE_SCAN_OUTCOMES:
        return HealthStatus.DEGRADED, "SCAN_" + record.last_scan_outcome
    return HealthStatus.HEALTHY, "IN_BOUND"
