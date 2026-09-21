"""Standard-library HTTP transport for GitHub, with a bounded per-call budget."""

from __future__ import annotations

from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from alienintent.installation.ports.github_transport import GitHubTransport, TransportResponse, TransportUnavailable


class UrllibGitHubTransport(GitHubTransport):
    """One request, one answer: no retry policy and no ambient configuration.

    A provider answer — including a refusal — is returned as a status so the
    caller can adjudicate it; only an unreachable provider raises, so
    `UNAVAILABLE` stays distinguishable from `FAIL`.
    """

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._timeout_seconds = timeout_seconds

    def request(self, method: str, url: str, headers: Mapping[str, str], body: bytes | None = None) -> TransportResponse:
        request = Request(url, data=body, method=method, headers=dict(headers))
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return TransportResponse(int(response.status), response.read())
        except HTTPError as error:
            return TransportResponse(int(error.code), error.read())
        except (URLError, TimeoutError, OSError) as error:
            raise TransportUnavailable("github transport is unreachable") from error
