"""Live repository reads, and the Issue writes `work link` makes, for exactly the configured repository."""

from __future__ import annotations

import base64
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

    def contents(self, path: str, ref: str = "") -> bytes:
        """Read one repository file with the installation credential.

        A live backlog names the BIU contract it was made READY against, and
        that document lives in the repository rather than in the Project. It
        is fetched here, through the same credential the rest of the profile
        runs on, instead of being trusted from a local copy.
        """
        document = self._read(f"/repos/{self._repository}/contents/{path}" + (f"?ref={ref}" if ref else ""))
        if document.get("path") != path or document.get("type") != "file":
            raise RepositoryRejected("observed content is not the requested repository file")
        encoded = document.get("content")
        if document.get("encoding") != "base64" or not isinstance(encoded, str):
            raise RepositoryUnavailable("repository file could not be read back")
        try:
            return base64.b64decode(encoded, validate=False)
        except ValueError as error:
            raise RepositoryUnavailable("repository file could not be decoded") from error

    # --- Issues: the one Issue a work item is linked to (`work link`, `work display`) --------------------------

    def issue(self, number: int) -> Mapping[str, object]:
        """One Issue. A missing Issue and a pull request are both RepositoryRejected (the caller's ISSUE_NOT_FOUND)."""
        document = self._request("GET", f"/repos/{self._repository}/issues/{int(number)}", 200)
        if "pull_request" in document:
            raise RepositoryRejected(f"#{int(number)} is a pull request, not an Issue")
        return _issue(document, int(number))

    def create_issue(self, title: str, body: str) -> Mapping[str, object]:
        return _issue(self._request("POST", f"/repos/{self._repository}/issues", 201, {"title": title, "body": body}))

    def update_issue(self, number: int, title: str, body: str) -> Mapping[str, object]:
        return _issue(self._request("PATCH", f"/repos/{self._repository}/issues/{int(number)}", 200,
                                    {"title": title, "body": body}), int(number))

    def close_issue(self, number: int, body: str) -> Mapping[str, object]:
        """Close as not planned, with the body given (a duplicate's body ending with the line naming the link)."""
        return _issue(self._request("PATCH", f"/repos/{self._repository}/issues/{int(number)}", 200,
                                    {"state": "closed", "state_reason": "not_planned", "body": body}), int(number))

    def recent_issues(self, limit: int) -> tuple[Mapping[str, object], ...]:
        """The repository's newest Issues by creation, open and closed, one page; pull requests are skipped."""
        document = self._request("GET", f"/repos/{self._repository}/issues?state=all&sort=created&direction=desc"
                                        f"&per_page={int(limit)}", 200)
        listed = document.get("items")
        if not isinstance(listed, list):
            raise RepositoryUnavailable("repository issues could not be read back")
        return tuple(entry for entry in listed if isinstance(entry, Mapping) and "pull_request" not in entry)

    def _request(self, method: str, path: str, expected: int,
                 payload: Mapping[str, object] | None = None) -> Mapping[str, object]:
        """One call answered with `expected`; a 404 or 410 is RepositoryRejected (no such Issue), any other status
        RepositoryUnavailable."""
        headers = dict(self._authorization())
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(dict(payload)).encode("utf-8")
        response = self._transport.request(method, f"{self._api_root}{path}", headers, body)
        if response.status in (404, 410):
            raise RepositoryRejected(f"repository answered {response.status} for {method} {path}")
        if response.status != expected:
            raise RepositoryUnavailable(f"repository answered {response.status} for {method} {path}")
        return _document(response.body)

    def _read(self, path: str) -> Mapping[str, object]:
        response = self._transport.request("GET", f"{self._api_root}{path}", dict(self._authorization()))
        if response.status != 200:
            raise RepositoryUnavailable(f"repository answered {response.status}")
        return _document(response.body)


def _document(body: bytes | None) -> Mapping[str, object]:
    try:
        document = json.loads(body or b"{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RepositoryUnavailable("repository answer is not a readable document") from error
    if isinstance(document, list):
        return {"items": document}
    if not isinstance(document, Mapping):
        raise RepositoryUnavailable("repository answer is not a readable document")
    return document


def _issue(document: Mapping[str, object], number: int | None = None) -> Mapping[str, object]:
    """An Issue answer carrying its number and node id (the requested number, when one was requested)."""
    observed = document.get("number")
    if not isinstance(observed, int) or not isinstance(document.get("node_id"), str) \
            or (number is not None and observed != number):
        raise RepositoryUnavailable("Issue answer does not name the requested Issue")
    return document
