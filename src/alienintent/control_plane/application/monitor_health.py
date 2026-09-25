"""Persistent monitor ticks and scan outcomes, independent of model life and workload.

Every write is an explicit call with an injected clock; nothing here runs a
thread, waiter, host or supervisor. Inspection is read-only.
"""
from collections.abc import Callable
from dataclasses import replace

from alienintent.control_plane.domain.monitor_health import (
    HealthReport, HealthStatus, MonitorHealth, MonitorHold, MonitorPolicy, MonitorSnapshot,
    Unavailable, classify, valid_clock_reading,
)
from alienintent.control_plane.ports.monitor_health import MonitorRepository
from alienintent.execution_coordination.ports.scan_progress import ScanOutcome, ScanProgress


class MonitorService(ScanProgress):
    def __init__(self, repository: MonitorRepository, *, profile: str, policy: MonitorPolicy | None,
                 clock: Callable[[], object], next_id: Callable[[], str]) -> None:
        self.repository, self.profile, self.policy = repository, profile, policy
        self.clock, self.next_id = clock, next_id
        self.instance: tuple[str, int] | None = None

    def _snapshot(self) -> MonitorSnapshot | None:
        snapshot = self.repository.snapshot(self.profile)
        if isinstance(snapshot, Unavailable):
            raise MonitorHold(snapshot.reason)
        return snapshot

    def _require(self) -> MonitorSnapshot:
        """Only the instance this service started may write; a superseded one holds."""
        snapshot = self._snapshot()
        if snapshot is None or self.instance is None:
            raise MonitorHold("NOT_STARTED")
        if (snapshot.record.instance_id, snapshot.record.generation) != self.instance:
            raise MonitorHold("STALE_INSTANCE")
        return snapshot

    def _now(self, current: MonitorSnapshot | None) -> int:
        """Absent, unreadable, invalid or regressing clocks never write an observation."""
        try:
            now = self.clock()
        except Exception as error:
            raise MonitorHold("CLOCK_UNREADABLE") from error
        if now is None:
            raise MonitorHold("CLOCK_ABSENT")
        if not valid_clock_reading(now):
            raise MonitorHold("CLOCK_INVALID")
        if current is not None and now < current.record.latest_observation():
            raise MonitorHold("CLOCK_REGRESSION")
        return now

    @staticmethod
    def _due(now: int, policy: MonitorPolicy) -> int:
        return int(now + policy.interval_micros)

    def _write(self, current: MonitorSnapshot, observation: dict[str, object], **changes: object) -> MonitorHealth:
        record = replace(current.record, **changes)
        return self.repository.save(current.version, record, current.policy, observation, current).record

    def start(self) -> MonitorHealth:
        """Begin a new instance/generation; earlier generations stay in history."""
        policy = self.policy
        if not isinstance(policy, MonitorPolicy):
            raise MonitorHold("POLICY_MISSING")
        policy.validate()
        current = self._snapshot()
        now = self._now(current)
        instance_id = self.next_id()
        if current is not None and instance_id == current.record.instance_id:
            raise MonitorHold("INSTANCE_REUSED")
        generation = 1 if current is None else current.record.generation + 1
        record = MonitorHealth(self.profile, instance_id, generation, policy.digest(), now,
                               None, None, None, None, self._due(now, policy), None)
        version = 0 if current is None else current.version
        saved = self.repository.save(version, record, policy, {"action": "STARTED", "at": now}, current).record
        self.instance = (saved.instance_id, saved.generation)
        return saved

    def tick(self) -> MonitorHealth:
        current = self._require()
        now = self._now(current)
        return self._write(current, {"action": "TICK", "at": now}, last_monitor_tick=now)

    def scan_started(self) -> MonitorHealth:
        current = self._require()
        now = self._now(current)
        return self._write(current, {"action": "SCAN_STARTED", "at": now},
                           last_scan_started_at=now, last_scan_outcome="STARTED", last_error=None)

    def scan_finished(self, outcome: ScanOutcome) -> MonitorHealth:
        """Only a COMPLETE full attempt advances last_scan_completed_at."""
        if not isinstance(outcome, ScanOutcome):
            raise MonitorHold("INVALID_SCAN_OUTCOME")
        current = self._require()
        if current.record.last_scan_outcome != "STARTED":
            raise MonitorHold("SCAN_NOT_STARTED")
        now = self._now(current)
        changes: dict[str, object] = {"last_scan_outcome": outcome.status, "last_error": outcome.error,
                                      "next_scan_due": self._due(now, current.policy)}
        if outcome.status == "COMPLETE":
            changes["last_scan_completed_at"] = now
        return self._write(current, {"action": "SCAN_FINISHED", "at": now, "outcome": outcome.status,
                                     "error": outcome.error, "active_work": outcome.active_work}, **changes)

    def inspect(self) -> HealthReport:
        snapshot = self.repository.snapshot(self.profile)
        if isinstance(snapshot, Unavailable):
            return HealthReport(HealthStatus.UNVERIFIED, snapshot.reason, None, None)
        record = None if snapshot is None else snapshot.record
        try:
            now = self.clock()
        except Exception:
            return HealthReport(HealthStatus.UNVERIFIED, "CLOCK_UNREADABLE", record, None)
        if now is None:
            return HealthReport(HealthStatus.UNVERIFIED, "CLOCK_ABSENT", record, None)
        status, reason = classify(record, None if snapshot is None else snapshot.policy, now)
        return HealthReport(status, reason, record, now if valid_clock_reading(now) else None)
