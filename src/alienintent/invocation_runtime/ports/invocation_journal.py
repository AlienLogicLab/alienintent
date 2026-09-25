"""Append-only durable invocation evidence behind the worker boundary."""

from typing import Mapping, Protocol


class InvocationJournal(Protocol):
    def append(self, record: Mapping[str, object]) -> dict[str, object]: ...
    def records(self) -> tuple[dict[str, object], ...]: ...
