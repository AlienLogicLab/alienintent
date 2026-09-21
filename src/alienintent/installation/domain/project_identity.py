"""Deterministic, exclusive, fail-closed Project addressing (SWF-34).

`organization_projects` is an organization-scoped permission, so the sandbox
token can technically reach other Projects in the organization. This module is
the control that actually operates: the configured Project identity is the only
one this installation ever addresses, resolution refuses anything else, and no
rule here enumerates or opportunistically selects an alternate Project.

Nothing in this module claims token-level Project isolation, which the platform
cannot provide.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class ProjectAddressRejected(ValueError):
    """An observed Project identity is absent, ambiguous, or not the configured one."""


PROJECT_IDENTITY = re.compile(r"PVT_[A-Za-z0-9_-]+")


@dataclass(frozen=True)
class ProjectAddress:
    """The exact Project this profile targets, and nothing else."""

    project_id: str
    project_number: int
    organization: str
    status_field_id: str
    priority_field_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not PROJECT_IDENTITY.fullmatch(self.project_id):
            raise ProjectAddressRejected("project identity is absent or not a Projects v2 node identity")
        if not isinstance(self.project_number, int) or self.project_number <= 0:
            raise ProjectAddressRejected("project number is absent or ambiguous")
        if not isinstance(self.organization, str) or not self.organization:
            raise ProjectAddressRejected("project organization is required")
        for name, value in (("Status", self.status_field_id), ("Priority", self.priority_field_id)):
            if not isinstance(value, str) or not value:
                raise ProjectAddressRejected(f"{name} field identity is required")

    def resolve(self, observed_id: str | None, observed_number: int | None = None) -> str:
        """Return the configured Project identity, or refuse.

        Every read and every write routes through here, so a provider answer for
        any other Project can never become the target of an operation.
        """
        if not isinstance(observed_id, str) or not observed_id:
            raise ProjectAddressRejected("observed project identity is absent or ambiguous")
        if observed_id != self.project_id:
            raise ProjectAddressRejected("observed project is not the configured project")
        if observed_number is not None and observed_number != self.project_number:
            raise ProjectAddressRejected("observed project number is not the configured project number")
        return self.project_id

    def targets(self, observed_id: str | None) -> bool:
        """Non-raising form for ingress admission; the same single comparison."""
        return isinstance(observed_id, str) and observed_id == self.project_id

    def field_for(self, name: str) -> str:
        if name == "Status":
            return self.status_field_id
        if name == "Priority":
            return self.priority_field_id
        raise ProjectAddressRejected("only the configured Status and Priority fields are addressable")


def foreign_project_identities(configuration: str, permitted_project_id: str) -> tuple[str, ...]:
    """Any Projects v2 identity in the configuration that is not the permitted one.

    Stated as "anything other than Project #2" rather than as a blocklist of
    production identities, so a production identifier never has to be written
    into this repository to be excluded.
    """
    found = set(PROJECT_IDENTITY.findall(configuration or ""))
    return tuple(sorted(found - {permitted_project_id}))


def foreign_repositories(configured: Iterable[str] | None, permitted_repository: str) -> tuple[str, ...]:
    return tuple(sorted({name for name in (configured or ()) if name != permitted_repository}))
