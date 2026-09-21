"""Mint, verify and refresh the installation credential a live profile runs on.

The App identity and private key resolve through the `SecretProvider`; the
clock and the assertion signer arrive as callables, so expiry and refresh are
exercised deterministically offline and the same code path runs live.
"""

from __future__ import annotations

import json
from typing import Callable, Mapping

from alienintent.installation.domain.app_credentials import (
    AppIdentity,
    CredentialRejected,
    CredentialUnavailable,
    InstallationToken,
    epoch_from_iso8601,
    event_drift,
    permission_drift,
    repository_scope_violations,
)
from alienintent.installation.ports.github_transport import GitHubTransport, TransportResponse
from alienintent.installation.ports.secret_provider import SecretProvider


GITHUB_API = "https://api.github.com"
_ACCEPT = "application/vnd.github+json"


class InstallationCredentials:
    """One credential per profile, refreshed rather than reused past expiry."""

    def __init__(
        self,
        identity: AppIdentity,
        secrets: SecretProvider,
        transport: GitHubTransport,
        clock: Callable[[], float],
        assertion: Callable[[int, bytes, float], str],
        api_root: str = GITHUB_API,
        refresh_safety_seconds: float = 60.0,
    ) -> None:
        self._identity, self._secrets, self._transport = identity, secrets, transport
        self._clock, self._assertion, self._api_root = clock, assertion, api_root
        self._refresh_safety_seconds = refresh_safety_seconds
        self._token: InstallationToken | None = None
        self.mints = 0

    # --- credential lifecycle ----------------------------------------------

    def token(self) -> InstallationToken:
        """Return a usable token, minting a fresh one once the held one is stale."""
        held = self._token
        if held is not None and not held.stale_at(self._clock(), self._refresh_safety_seconds):
            return held
        self._token = self._mint()
        return self._token

    def authorization(self) -> Mapping[str, str]:
        """Headers for an installation-authenticated call; the value is never logged."""
        return {"Authorization": f"token {self.token().value}", "Accept": _ACCEPT}

    def _mint(self) -> InstallationToken:
        document = self._application_call("POST", f"/app/installations/{self._identity.installation_id}/access_tokens", expected=201)
        value, expiry = document.get("token"), document.get("expires_at")
        if not isinstance(value, str) or not value or not isinstance(expiry, str):
            raise CredentialUnavailable("installation token response is incomplete")
        permissions = document.get("permissions")
        self.mints += 1
        return InstallationToken(
            value,
            epoch_from_iso8601(expiry),
            dict(permissions) if isinstance(permissions, Mapping) else {},
            str(document.get("repository_selection") or ""),
        )

    # --- least privilege and scope -----------------------------------------

    def application(self) -> Mapping[str, object]:
        return self._application_call("GET", "/app")

    def installation(self) -> Mapping[str, object]:
        return self._application_call("GET", f"/app/installations/{self._identity.installation_id}")

    def repositories(self) -> tuple[str, ...]:
        document = self._installation_call("GET", "/installation/repositories")
        listed = document.get("repositories")
        if not isinstance(listed, list):
            raise CredentialUnavailable("installation repository scope could not be read back")
        return tuple(str(entry.get("full_name")) for entry in listed if isinstance(entry, Mapping))

    def least_privilege_findings(self) -> tuple[str, ...]:
        """Exact-grant drift at both the App and the installation, plus events."""
        application, installation = self.application(), self.installation()
        return (
            tuple(f"app {finding}" for finding in permission_drift(_permissions(application)))
            + tuple(f"app {finding}" for finding in event_drift(application.get("events")))
            + tuple(f"installation {finding}" for finding in permission_drift(_permissions(installation)))
        )

    def repository_scope_findings(self, sandbox_repository: str) -> tuple[str, ...]:
        installation = self.installation()
        return repository_scope_violations(
            str(installation.get("repository_selection") or ""), self.repositories(), sandbox_repository,
        )

    def granted_permissions(self) -> Mapping[str, str]:
        """What GitHub reports as granted — never what an adapter declares it has."""
        return _permissions(self.installation())

    # --- transport ----------------------------------------------------------

    def application_call(self, method: str, path: str, expected: int = 200) -> Mapping[str, object]:
        """An App-authenticated call; the assertion is minted per call and never held."""
        return self._application_call(method, path, expected)

    def _application_call(self, method: str, path: str, expected: int = 200) -> Mapping[str, object]:
        headers = {"Authorization": f"Bearer {self._app_assertion()}", "Accept": _ACCEPT}
        return _document(self._transport.request(method, f"{self._api_root}{path}", headers), expected)

    def _installation_call(self, method: str, path: str, expected: int = 200) -> Mapping[str, object]:
        return _document(self._transport.request(method, f"{self._api_root}{path}", dict(self.authorization())), expected)

    def _app_assertion(self) -> str:
        try:
            material = self._secrets.resolve(self._identity.private_key_reference)
        except Exception as error:
            raise CredentialRejected("App private key reference does not resolve") from error
        if not isinstance(material, bytes) or not material:
            raise CredentialRejected("App private key reference resolves to unusable material")
        return self._assertion(self._identity.application_id, material, self._clock())


def _permissions(document: Mapping[str, object]) -> Mapping[str, str]:
    permissions = document.get("permissions")
    return dict(permissions) if isinstance(permissions, Mapping) else {}


def _document(response: TransportResponse, expected: int) -> Mapping[str, object]:
    if response.status != expected:
        raise CredentialUnavailable(f"github answered {response.status} where {expected} was required")
    try:
        document = json.loads(response.body or b"{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CredentialUnavailable("github answer is not a readable document") from error
    if isinstance(document, list):
        return {"items": document}
    if not isinstance(document, Mapping):
        raise CredentialUnavailable("github answer is not a readable document")
    return document
