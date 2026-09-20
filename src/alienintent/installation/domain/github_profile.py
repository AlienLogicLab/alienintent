"""Minimum typed configuration for one GitHub-backed profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


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

    def __post_init__(self) -> None:
        if not self.profile or not self.repository or not self.project_reference or not self.webhook_secret_reference:
            raise ProfileRejected("profile identity and references are required")
        if not self.lifecycle_statuses or "READY" not in self.lifecycle_statuses.values():
            raise ProfileRejected("exactly mapped upstream READY status is required")
        if any(status in {"IMPLEMENT", "VERIFY", "REVIEW", "ACCEPT", "DONE"} for status in self.lifecycle_statuses):
            raise ProfileRejected("downstream execution displays cannot authorize release")
        if not self.projection_fields:
            raise ProfileRejected("downstream projection mapping is required")
