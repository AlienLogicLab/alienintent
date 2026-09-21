"""Translate a GitHub webhook delivery into one neutral, fail-closed reference.

Recorded normalized fixtures and live GitHub payloads reach the same rule. A
delivery that identifies neither a repository nor a Project is ambiguous and is
never admitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class DeliveryRejected(ValueError):
    """A delivery payload carries no unambiguous work, repository or Project reference."""


@dataclass(frozen=True)
class DeliveryReference:
    work: str
    version: int
    repository: str | None
    project: str | None


def delivery_reference(payload: Mapping[str, object], category: str) -> DeliveryReference:
    if not isinstance(payload, Mapping):
        raise DeliveryRejected("unsupported payload")
    recorded = payload.get("project_item")
    if isinstance(recorded, Mapping):
        return _recorded(recorded, payload)
    live_item = payload.get("projects_v2_item")
    if isinstance(live_item, Mapping):
        return _projects_v2_item(live_item)
    issue = payload.get("issue")
    if isinstance(issue, Mapping) and category in {"issue_comment", "issues"}:
        return _issue(issue, payload)
    raise DeliveryRejected("ambiguous profile or work reference")


def _recorded(item: Mapping[str, object], payload: Mapping[str, object]) -> DeliveryReference:
    work, version = item.get("id"), item.get("version", 0)
    if not isinstance(work, str) or not work or not isinstance(version, int):
        raise DeliveryRejected("ambiguous profile or work reference")
    return DeliveryReference(work, version, _repository(payload), None)


def _projects_v2_item(item: Mapping[str, object]) -> DeliveryReference:
    """A live `projects_v2_item` names its Project and never names a repository.

    The Project identity is therefore the only boundary this delivery can be
    admitted against, which is exactly the control SWF-34 requires.
    """
    work = item.get("content_node_id") or item.get("node_id")
    project = item.get("project_node_id")
    if not isinstance(work, str) or not work or not isinstance(project, str) or not project:
        raise DeliveryRejected("ambiguous profile or work reference")
    return DeliveryReference(work, 0, None, project)


def _issue(issue: Mapping[str, object], payload: Mapping[str, object]) -> DeliveryReference:
    work = issue.get("node_id")
    repository = _repository(payload)
    if not isinstance(work, str) or not work or repository is None:
        raise DeliveryRejected("ambiguous profile or work reference")
    return DeliveryReference(work, 0, repository, None)


def _repository(payload: Mapping[str, object]) -> str | None:
    reference = payload.get("repository")
    name = reference.get("full_name") if isinstance(reference, Mapping) else None
    return name if isinstance(name, str) and name else None
