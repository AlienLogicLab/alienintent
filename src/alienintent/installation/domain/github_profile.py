"""Minimum typed configuration for one GitHub-backed profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from alienintent.installation.domain.project_identity import ProjectAddress


class ProfileRejected(ValueError):
    """A profile would invert the upstream-to-execution authority boundary."""


@dataclass(frozen=True)
class GitHubProfile:
    profile: str
    repository: str
    project_reference: str
    lifecycle_statuses: Mapping[str, str]
    projection_fields: Mapping[str, str]
    webhook_secret_reference: str
    automatic_release: bool
    # Recorded sandbox identities. Defaulted so a fixture-backed profile stays
    # constructible from the seven fields PY-05 defined; a live profile supplies them.
    webhook_listen_address: str = ""
    webhook_listen_port: int = 0
    webhook_public_url: str = ""
    project_number: int = 0
    project_status_field: str = ""
    project_priority_field: str = ""

    def __post_init__(self) -> None:
        if not self.profile or not self.repository or not self.project_reference or not self.webhook_secret_reference:
            raise ProfileRejected("profile identity and references are required")
        if not self.lifecycle_statuses or "READY" not in self.lifecycle_statuses.values():
            raise ProfileRejected("exactly mapped upstream READY status is required")
        if any(status in {"IMPLEMENT", "VERIFY", "REVIEW", "ACCEPT", "DONE"} for status in self.lifecycle_statuses):
            raise ProfileRejected("downstream execution displays cannot authorize release")
        if not self.projection_fields:
            raise ProfileRejected("downstream projection mapping is required")
        if self.webhook_listen_port and not 1 <= self.webhook_listen_port <= 65535:
            raise ProfileRejected("webhook ingress port is outside the addressable range")
        if self.webhook_listen_port and not self.webhook_listen_address:
            raise ProfileRejected("webhook ingress port requires a bind address")
        if "/" not in self.repository.strip("/"):
            raise ProfileRejected("repository must name an owner and a repository")

    @property
    def organization(self) -> str:
        return self.repository.split("/", 1)[0]

    def project_address(self) -> ProjectAddress:
        """The exact Project this profile targets; refuses an incomplete identity."""
        return ProjectAddress(
            self.project_reference, self.project_number, self.organization,
            self.project_status_field, self.project_priority_field,
        )
