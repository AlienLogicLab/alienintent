"""Neutral HTTP boundary for authenticated GitHub REST and GraphQL access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


class TransportUnavailable(RuntimeError):
    """The provider could not be reached; no statement about its answer is implied."""


@dataclass(frozen=True)
class TransportResponse:
    status: int
    body: bytes


class GitHubTransport(Protocol):
    def request(self, method: str, url: str, headers: Mapping[str, str], body: bytes | None = None) -> TransportResponse: ...
