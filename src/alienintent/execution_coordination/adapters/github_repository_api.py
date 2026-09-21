"""Live repository reads for exactly the repository the profile names."""

from __future__ import annotations

import json
from typing import Callable, Mapping

from alienintent.execution_coordination.ports.repository_directory import (
    RepositoryDirectory,
    RepositoryRejected,
    RepositoryUnavailable,
)
from alienintent.installation.ports.github_transport import GitHubTransport

GITHUB_API = "https://api.github.com"


class GitHubRepositoryApi(RepositoryDirectory):
    def __init__(self, repository: str, transport: GitHubTransport, authorization: Callable[[], Mapping[str, str]], api_root: str = GITHUB_API) -> None:
        self._repository, self._transport, self._authorization, self._api_root = repository, transport, authorization, api_root

    def metadata(self) -> Mapping[str, object]:
        document = self._read(f"/repos/{self._repository}")
        if document.get("full_name") != self._repository:
            raise RepositoryRejected("observed repository is not the configured repository")
        return document

    def issues(self, limit: int = 10) -> tuple[Mapping[str, object], ...]:
        document = self._read(f"/repos/{self._repository}/issues?per_page={int(limit)}&state=all")
        listed = document.get("items")
        if not isinstance(listed, list):
            raise RepositoryUnavailable("repository issues could not be read back")
        return tuple(entry for entry in listed if isinstance(entry, Mapping))

    def _read(self, path: str) -> Mapping[str, object]:
        response = self._transport.request("GET", f"{self._api_root}{path}", dict(self._authorization()))
        if response.status != 200:
            raise RepositoryUnavailable(f"repository answered {response.status}")
        try:
            document = json.loads(response.body or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RepositoryUnavailable("repository answer is not a readable document") from error
        if isinstance(document, list):
            return {"items": document}
        if not isinstance(document, Mapping):
            raise RepositoryUnavailable("repository answer is not a readable document")
        return document
