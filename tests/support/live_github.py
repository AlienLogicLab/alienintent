"""Recorded GitHub answers driving the live adapters offline, in the normal suite.

Every identity below is synthetic. No App id, installation id, Project node
identity or field identity from a real installation appears here, so the
offline suite is coupled to no environment and carries no installation
detail (binding rule 3).
"""

from __future__ import annotations

import json
from typing import Callable, Mapping

from alienintent.installation.ports.github_transport import TransportResponse, TransportUnavailable

SANDBOX_REPOSITORY = "AlienLogicLab/alienintent-sandbox"
SANDBOX_PROJECT = "PVT_kwDOfixtureSandboxProject"
FOREIGN_PROJECT = "PVT_kwDOfixtureForeignProject"
STATUS_FIELD = "PVTSSF_fixtureStatusField"
PRIORITY_FIELD = "PVTSSF_fixturePriorityField"

LEAST_PRIVILEGE = {"issues": "read", "metadata": "read", "organization_projects": "write", "contents": "write"}
SUBSCRIBED_EVENTS = ["issue_comment", "projects_v2_item"]

STATUS_OPTIONS = [
    {"id": "98416bef", "name": "READY"}, {"id": "b39bda1a", "name": "IMPLEMENT"},
    {"id": "64fca347", "name": "VERIFY"}, {"id": "b0653188", "name": "REVIEW"},
    {"id": "5e0040ab", "name": "ACCEPT"}, {"id": "9ca6f842", "name": "DONE"},
]
PRIORITY_OPTIONS = [{"id": "275d961a", "name": "P0"}, {"id": "f645bbdb", "name": "P1"}]


class RecordedTransport:
    """Answer recorded GitHub documents; unrecorded calls fail loudly, not silently."""

    def __init__(self, answers: Mapping[str, object], graphql: Callable[[str, dict], object] | None = None, unreachable: bool = False) -> None:
        self._answers, self._graphql, self._unreachable = dict(answers), graphql, unreachable
        self.calls: list[tuple[str, str]] = []
        self.authorizations: list[str] = []

    def request(self, method: str, url: str, headers: Mapping[str, str], body: bytes | None = None) -> TransportResponse:
        if self._unreachable:
            raise TransportUnavailable("recorded transport is unreachable")
        self.calls.append((method, url))
        self.authorizations.append(str(headers.get("Authorization", "")))
        if url.endswith("/graphql"):
            request = json.loads(body or b"{}")
            answer = self._graphql(request["query"], request["variables"]) if self._graphql else None
            return TransportResponse(200, json.dumps(answer or {"data": {}}).encode())
        for suffix, answer in self._answers.items():
            if url.endswith(suffix):
                status, document = answer if isinstance(answer, tuple) else (200, answer)
                return TransportResponse(status, json.dumps(document).encode())
        return TransportResponse(404, b'{"message":"not recorded"}')


def rest_answers(
    *,
    permissions: Mapping[str, str] | None = None,
    installation_permissions: Mapping[str, str] | None = None,
    events: list[str] | None = None,
    repository_selection: str = "selected",
    repositories: list[str] | None = None,
    expires_at: str = "2026-09-21T11:00:00Z",
    token_status: int = 201,
) -> dict[str, object]:
    granted = dict(permissions if permissions is not None else LEAST_PRIVILEGE)
    installed = dict(installation_permissions if installation_permissions is not None else granted)
    return {
        "/access_tokens": (token_status, {"token": "ghs-recorded-token", "expires_at": expires_at, "permissions": installed, "repository_selection": repository_selection}),
        "/app": {"id": 1000001, "slug": "recorded-app", "permissions": granted, "events": list(events if events is not None else SUBSCRIBED_EVENTS)},
        "/app/installations/2000002": {"app_id": 1000001, "repository_selection": repository_selection, "permissions": installed},
        "/installation/repositories": {"repositories": [{"full_name": name} for name in (repositories if repositories is not None else [SANDBOX_REPOSITORY])]},
        f"/repos/{SANDBOX_REPOSITORY}": {"full_name": SANDBOX_REPOSITORY, "private": True, "default_branch": "main"},
        "&state=all": [{"number": 1, "node_id": "I_sandbox_1", "title": "sandbox probe"}],
    }


def project_graphql(
    *,
    project_id: str = SANDBOX_PROJECT,
    project_number: int = 2,
    status_field: str = STATUS_FIELD,
    priority_field: str = PRIORITY_FIELD,
    items: list[dict] | None = None,
    written_status: str | None = None,
    read_back: str | None = None,
) -> Callable[[str, dict], object]:
    """A recorded Project that answers exactly what the live one answered."""
    applied = {"status": read_back}

    def answer(query: str, variables: dict) -> object:
        if "fields(first:50)" in query:
            return {"data": {"node": {
                "id": project_id, "number": project_number, "title": "recorded sandbox",
                "fields": {"nodes": [
                    {"id": status_field, "name": "Status", "options": STATUS_OPTIONS},
                    {"id": priority_field, "name": "Priority", "options": PRIORITY_OPTIONS},
                ]},
            }}}
        if "items(first:$limit)" in query:
            return {"data": {"node": {"id": project_id, "number": project_number, "items": {"nodes": items or []}}}}
        if "ProjectV2Item { id project" in query:
            return {"data": {"node": {
                "id": variables["item"], "project": {"id": project_id, "number": project_number},
                "content": {"id": "DI_recorded"},
                "fieldValues": {"nodes": [{"name": applied["status"], "field": {"id": status_field, "name": "Status"}}] if applied["status"] else []},
            }}}
        if "updateProjectV2ItemFieldValue" in query:
            applied["status"] = written_status if written_status is not None else _option_name(variables["option"])
            return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": variables["item"], "project": {"id": project_id, "number": project_number}}}}}
        if "addProjectV2DraftIssue" in query:
            return {"data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_recorded", "project": {"id": project_id, "number": project_number}}}}}
        if "deleteProjectV2Item" in query:
            return {"data": {"deleteProjectV2Item": {"deletedItemId": variables["item"]}}}
        return {"data": {}}

    return answer


def _option_name(option_id: str) -> str:
    return next(option["name"] for option in STATUS_OPTIONS if option["id"] == option_id)
