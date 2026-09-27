"""The one durable, append-only journal of a live trajectory capture stream."""
from collections.abc import Mapping
from typing import Protocol


class TrajectoryJournal(Protocol):
    """Immutable entry first, then the versioned head pointer (compare-and-set). An entry is
    committed exactly when the pointer names it; `entries` verifies the whole chain."""

    def version(self) -> int: ...
    def append(self, expected_version: int, entry: Mapping[str, object]) -> int: ...
    def entries(self) -> tuple[dict[str, object], ...]: ...
