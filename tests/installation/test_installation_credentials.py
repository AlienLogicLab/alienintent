"""Discriminating offline proof for the PY-09B installation credential.

Every test names the guard it protects; removing that guard turns it red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from alienintent.installation.adapters.app_jwt import app_assertion
from alienintent.installation.application.installation_credentials import InstallationCredentials
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
from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
from tests.support.disposable_rsa import disposable_private_key
from tests.support.live_github import LEAST_PRIVILEGE, SANDBOX_REPOSITORY, RecordedTransport, rest_answers


def _identity() -> AppIdentity:
    return AppIdentity(1000001, 2000002, "app-private-key")


def _credentials(tmp_path: Path, clock, **recorded) -> tuple[InstallationCredentials, RecordedTransport]:
    key = tmp_path / "key.pem"
    key.write_bytes(disposable_private_key())
    transport = RecordedTransport(rest_answers(**recorded))
    secrets = ProtectedLocalFileSecretProvider({"app-private-key": key})
    return InstallationCredentials(_identity(), secrets, transport, clock, app_assertion), transport


# --- AC 1: mint, live use, refresh, fail closed ------------------------------


def test_token_is_minted_from_the_referenced_key_and_used_for_a_live_call(tmp_path: Path) -> None:
    credentials, transport = _credentials(tmp_path, lambda: 1758445000.0)

    assert credentials.repositories() == (SANDBOX_REPOSITORY,)
    assert credentials.mints == 1
    assert any(header.startswith("token ") for header in transport.authorizations)
    assert any(header.startswith("Bearer ey") for header in transport.authorizations)


def test_token_is_reused_before_expiry_and_refreshed_rather_than_reused_past_it(tmp_path: Path) -> None:
    """Removing the staleness comparison must make this fail with a single mint."""
    now = {"value": epoch_from_iso8601("2026-09-21T10:00:00Z")}
    credentials, _ = _credentials(tmp_path, lambda: now["value"], expires_at="2026-09-21T11:00:00Z")

    first = credentials.token()
    assert credentials.token() is first
    assert credentials.mints == 1

    now["value"] = epoch_from_iso8601("2026-09-21T10:59:30Z")
    assert credentials.token().stale_at(now["value"]) or credentials.mints == 2
    assert credentials.mints == 2


def test_expiry_inside_the_refresh_margin_is_already_stale() -> None:
    token = InstallationToken("value", 1000.0, {}, "selected")

    assert token.stale_at(941.0)
    assert not token.stale_at(939.0)


def test_missing_credential_reference_fails_closed_with_a_typed_outcome(tmp_path: Path) -> None:
    """AC 1 negative case: an unresolvable key reference is never a silent pass."""
    transport = RecordedTransport(rest_answers())
    credentials = InstallationCredentials(
        _identity(), ProtectedLocalFileSecretProvider({}), transport, lambda: 0.0, app_assertion,
    )

    with pytest.raises(CredentialRejected):
        credentials.token()
    assert transport.calls == []


def test_unusable_credential_material_fails_closed_before_any_live_call(tmp_path: Path) -> None:
    empty = tmp_path / "empty.pem"
    empty.write_bytes(b"")
    credentials = InstallationCredentials(
        _identity(), ProtectedLocalFileSecretProvider({"app-private-key": empty}),
        RecordedTransport(rest_answers()), lambda: 0.0, app_assertion,
    )

    with pytest.raises(CredentialRejected, match="resolves to unusable material"):
        credentials.token()


def test_refused_token_request_is_unavailable_rather_than_an_empty_credential(tmp_path: Path) -> None:
    credentials, _ = _credentials(tmp_path, lambda: 0.0, token_status=403)

    with pytest.raises(CredentialUnavailable):
        credentials.token()


def test_unreadable_expiry_fails_closed_instead_of_assuming_a_lifetime() -> None:
    for value in ("", "2026-09-21 11:00:00", "2026-09-21T11:00:00+00:00", "not-a-time-at-all"):
        with pytest.raises(CredentialRejected):
            epoch_from_iso8601(value)


# --- AC 11: the credential never appears in a diagnostic ---------------------


def test_installation_token_representation_never_carries_the_bearer_material() -> None:
    """Removing the redacted representation must make this fail."""
    token = InstallationToken("ghs-super-secret", 1.0, LEAST_PRIVILEGE, "selected")

    rendered = repr(token)
    assert "ghs-super-secret" not in rendered
    assert "<redacted>" in rendered
    assert "selected" in rendered


# --- AC 2: least privilege is exact -----------------------------------------


def test_exactly_the_least_privilege_set_reports_no_drift(tmp_path: Path) -> None:
    credentials, _ = _credentials(tmp_path, lambda: 0.0)

    assert credentials.least_privilege_findings() == ()


@pytest.mark.parametrize(
    ("granted", "expected"),
    [
        (LEAST_PRIVILEGE | {"pull_requests": "write"}, "extra grant pull_requests:write"),
        ({name: level for name, level in LEAST_PRIVILEGE.items() if name != "issues"}, "missing grant issues:read"),
        (LEAST_PRIVILEGE | {"contents": "read"}, "grant contents is read, required write"),
    ],
)
def test_an_extra_a_missing_and_a_read_only_contents_grant_each_fail_the_check(granted: dict, expected: str) -> None:
    """AC 2: `contents: read` alone permits the clone half of read-back, not the push half."""
    assert expected in permission_drift(granted)


def test_permission_drift_on_a_live_profile_is_reported_from_both_app_and_installation(tmp_path: Path) -> None:
    credentials, _ = _credentials(tmp_path, lambda: 0.0, installation_permissions=LEAST_PRIVILEGE | {"contents": "read"})

    findings = credentials.least_privilege_findings()
    assert findings == ("installation grant contents is read, required write",)


@pytest.mark.parametrize(
    ("events", "expected"),
    [(["issue_comment"], "missing event projects_v2_item"), (["issue_comment", "projects_v2_item", "push"], "extra event push")],
)
def test_event_subscriptions_are_exact_in_both_directions(events: list[str], expected: str) -> None:
    assert expected in event_drift(events)


# --- AC 10a: the repository boundary GitHub enforces -------------------------


def test_selected_scope_limited_to_the_sandbox_repository_has_no_violation() -> None:
    assert repository_scope_violations("selected", [SANDBOX_REPOSITORY], SANDBOX_REPOSITORY) == ()


@pytest.mark.parametrize(
    ("selection", "repositories", "expected"),
    [
        ("all", [SANDBOX_REPOSITORY], "installation repository_selection is 'all', required 'selected'"),
        ("selected", [SANDBOX_REPOSITORY, "AlienLogicLab/other"], "installation scope includes AlienLogicLab/other"),
        ("selected", [], "installation grants access to no repository at all"),
        ("selected", ["AlienLogicLab/other"], f"installation scope excludes {SANDBOX_REPOSITORY}"),
    ],
)
def test_repository_scope_drift_is_reported_rather_than_tolerated(selection: str, repositories: list[str], expected: str) -> None:
    assert expected in repository_scope_violations(selection, repositories, SANDBOX_REPOSITORY)


def test_live_repository_scope_findings_read_the_installation_rather_than_the_profile(tmp_path: Path) -> None:
    credentials, _ = _credentials(tmp_path, lambda: 0.0, repository_selection="all", repositories=[SANDBOX_REPOSITORY, "AlienLogicLab/other"])

    findings = credentials.repository_scope_findings(SANDBOX_REPOSITORY)
    assert "installation repository_selection is 'all', required 'selected'" in findings
    assert "installation scope includes AlienLogicLab/other" in findings
