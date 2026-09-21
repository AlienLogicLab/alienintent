"""Installation-credential rules: identity, expiry, least privilege, repository scope.

Pure judgements only. The clock is supplied by the caller, so every rule here
is deterministic and runs offline in the normal suite.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from typing import Iterable, Mapping


class CredentialRejected(ValueError):
    """A credential reference, grant set or scope is unusable and fails closed."""


class CredentialUnavailable(RuntimeError):
    """A credential could not be positively established from its references."""


# Binding rule 4 of the PY-09B contract. `contents: write` is required because
# canonical Python publishes the candidate and reads it back through the
# installation credential against a private repository: read alone permits the
# clone half of read-back and not the push half.
REQUIRED_PERMISSIONS: Mapping[str, str] = {
    "issues": "read",
    "metadata": "read",
    "organization_projects": "write",
    "contents": "write",
}
REQUIRED_EVENTS: tuple[str, ...] = ("issue_comment", "projects_v2_item")


@dataclass(frozen=True)
class AppIdentity:
    """The App and installation a profile is bound to, plus its key reference."""

    application_id: int
    installation_id: int
    private_key_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.application_id, int) or self.application_id <= 0:
            raise CredentialRejected("application identity is absent or ambiguous")
        if not isinstance(self.installation_id, int) or self.installation_id <= 0:
            raise CredentialRejected("installation identity is absent or ambiguous")
        if not isinstance(self.private_key_reference, str) or not self.private_key_reference:
            raise CredentialRejected("private key reference is required")


@dataclass(frozen=True, repr=False)
class InstallationToken:
    """A minted installation token and the authority it was observed to carry.

    `value` is bearer material: it is excluded from the generated representation
    so no diagnostic, log line or retained evidence can carry it by accident.
    """

    value: str = field(repr=False)
    expires_at: float
    permissions: Mapping[str, str]
    repository_selection: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise CredentialRejected("installation token is empty")
        if not isinstance(self.expires_at, (int, float)):
            raise CredentialRejected("installation token has no usable expiry")

    def __repr__(self) -> str:
        return (
            "InstallationToken(value=<redacted>, "
            f"expires_at={self.expires_at!r}, repository_selection={self.repository_selection!r})"
        )

    def stale_at(self, now: float, safety_seconds: float = 60.0) -> bool:
        """True once the token is inside its refresh margin or already expired."""
        return now + safety_seconds >= self.expires_at


def epoch_from_iso8601(value: str) -> float:
    """Convert a GitHub `YYYY-MM-DDTHH:MM:SSZ` expiry to epoch seconds.

    Deterministic string arithmetic: the pure layers may not import `datetime`
    or `time`, and an expiry that cannot be read must fail closed rather than
    default to a lifetime the provider never granted.
    """
    if not isinstance(value, str) or len(value) < 20 or value[10] != "T" or not value.endswith("Z"):
        raise CredentialRejected("installation token expiry is not an ISO-8601 UTC instant")
    try:
        parts = (
            int(value[0:4]), int(value[5:7]), int(value[8:10]),
            int(value[11:13]), int(value[14:16]), int(value[17:19]),
        )
    except ValueError as error:
        raise CredentialRejected("installation token expiry is not an ISO-8601 UTC instant") from error
    return float(calendar.timegm((*parts, 0, 0, 0)))


def permission_drift(granted: Mapping[str, str] | None, required: Mapping[str, str] = REQUIRED_PERMISSIONS) -> tuple[str, ...]:
    """Least privilege is an exact match; an extra grant fails like a missing one."""
    observed = dict(granted or {})
    findings: list[str] = []
    for name in sorted(set(observed) | set(required)):
        expected, actual = required.get(name), observed.get(name)
        if actual is None:
            findings.append(f"missing grant {name}:{expected}")
        elif expected is None:
            findings.append(f"extra grant {name}:{actual}")
        elif actual != expected:
            findings.append(f"grant {name} is {actual}, required {expected}")
    return tuple(findings)


def event_drift(events: Iterable[str] | None, required: tuple[str, ...] = REQUIRED_EVENTS) -> tuple[str, ...]:
    observed = set(events or ())
    findings = [f"missing event {name}" for name in sorted(set(required) - observed)]
    findings += [f"extra event {name}" for name in sorted(observed - set(required))]
    return tuple(findings)


def repository_scope_violations(repository_selection: str | None, repositories: Iterable[str] | None, sandbox_repository: str) -> tuple[str, ...]:
    """The repository boundary GitHub itself enforces, judged on what is granted.

    Readability of a public repository proves nothing, so scope is judged on the
    installation's selected repositories rather than on what a request returns.
    """
    names = list(repositories or [])
    findings: list[str] = []
    if repository_selection != "selected":
        findings.append(f"installation repository_selection is {repository_selection!r}, required 'selected'")
    if not names:
        findings.append("installation grants access to no repository at all")
    findings += [f"installation scope includes {name}" for name in names if name != sandbox_repository]
    if names and sandbox_repository not in names:
        findings.append(f"installation scope excludes {sandbox_repository}")
    return tuple(findings)
