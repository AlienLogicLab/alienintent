"""Neutral monitor-health read port and its versioned persistence."""
from typing import Protocol

from alienintent.control_plane.domain.monitor_health import MonitorHealth, MonitorPolicy, MonitorSnapshot, Unavailable


class MonitorHealthPort(Protocol):
    def read(self, profile: str) -> MonitorHealth | None | Unavailable: ...


class MonitorRepository(MonitorHealthPort, Protocol):
    def snapshot(self, profile: str) -> MonitorSnapshot | None | Unavailable: ...
    def save(self, expected_version: int, record: MonitorHealth, policy: MonitorPolicy,
             observation: dict[str, object], preceding: MonitorSnapshot | None) -> MonitorSnapshot: ...
    def history(self, profile: str) -> tuple[dict[str, object], ...]: ...
