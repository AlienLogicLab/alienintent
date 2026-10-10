"""Append-only durable invocation evidence behind the worker boundary."""

from typing import Mapping, Protocol


class InvocationJournal(Protocol):
    def append(self, record: Mapping[str, object]) -> dict[str, object]: ...
    def records(self, work: str | None = None) -> tuple[dict[str, object], ...]:
        """Every record, or with `work` only that work item's records: the routine read, whose cost follows that work
        item's own history, never the whole journal."""
        ...
