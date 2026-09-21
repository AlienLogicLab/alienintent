"""Live repository read boundary: metadata, issues and the published baseline."""

from __future__ import annotations

from typing import Mapping, Protocol


class RepositoryUnavailable(RuntimeError):
    """The repository could not be reached with the installation credential."""


class RepositoryRejected(ValueError):
    """The repository answer is incomplete or names a repository outside the profile."""


class RepositoryDirectory(Protocol):
    def metadata(self) -> Mapping[str, object]: ...
    def issues(self, limit: int = 10) -> tuple[Mapping[str, object], ...]: ...
