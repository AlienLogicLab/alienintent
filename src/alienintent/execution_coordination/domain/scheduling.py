"""Deterministic, side-effect-free scheduling selection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    global_limit: int
    profile_mutating_limit: int
    repository_mutating_limit: int = 1


@dataclass(frozen=True)
class ScheduledItem:
    identity: str
    fifo: int
    repository: str
    profile: str
    priority: int | None
    dependencies_satisfied: bool
    mutating: bool = True
    released_or_releasable: bool = True


def select_admissible(items: tuple[ScheduledItem, ...], active: tuple[ScheduledItem, ...], capacity: Capacity) -> tuple[ScheduledItem, ...]:
    selected: list[ScheduledItem] = []
    ordered = sorted(items, key=lambda item: (item.priority is None, item.priority if item.priority is not None else 0, item.fifo))
    for item in ordered:
        occupied = (*active, *selected)
        if not item.released_or_releasable or not item.dependencies_satisfied or len(occupied) >= capacity.global_limit:
            continue
        if item.mutating:
            profile_count = sum(entry.mutating and entry.profile == item.profile for entry in occupied)
            repository_count = sum(entry.mutating and entry.repository == item.repository for entry in occupied)
            if profile_count >= capacity.profile_mutating_limit or repository_count >= capacity.repository_mutating_limit:
                continue
        selected.append(item)
    return tuple(selected)
