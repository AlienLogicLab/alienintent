"""Live Projects v2 directory for exactly one configured Project.

Every query and every mutation names the configured Project node identity and
routes its answer through `ProjectAddress.resolve`, so no code path here
enumerates Projects or opportunistically selects an alternate one.
"""

from __future__ import annotations

import json
from typing import Callable, Mapping

from alienintent.execution_coordination.ports.project_directory import (
    ProjectDirectory,
    ProjectItemState,
    ProjectRejected,
    ProjectSchema,
    ProjectUnavailable,
)
from alienintent.installation.domain.project_identity import ProjectAddress, ProjectAddressRejected
from alienintent.installation.ports.github_transport import GitHubTransport

GITHUB_GRAPHQL = "https://api.github.com/graphql"

_SCHEMA_QUERY = """query($project:ID!){ node(id:$project){ ... on ProjectV2 { id number title
  fields(first:50){ nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }"""

_ITEMS_QUERY = """query($project:ID!,$limit:Int!){ node(id:$project){ ... on ProjectV2 { id number
  items(first:$limit){ nodes { id content { ... on Issue { id } ... on DraftIssue { id } }
    fieldValues(first:20){ nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { id name } } } } } } } } } }"""

_ITEM_QUERY = """query($item:ID!){ node(id:$item){ ... on ProjectV2Item { id project { id number }
  content { ... on Issue { id } ... on DraftIssue { id } }
  fieldValues(first:20){ nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { id name } } } } } } } }"""

_WRITE_MUTATION = """mutation($project:ID!,$item:ID!,$field:ID!,$option:String!){
  updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:{singleSelectOptionId:$option}}){
    projectV2Item { id project { id number } } } }"""

_ADD_DRAFT_MUTATION = """mutation($project:ID!,$title:String!){ addProjectV2DraftIssue(input:{projectId:$project,title:$title}){
  projectItem { id project { id number } } } }"""

_DELETE_MUTATION = """mutation($project:ID!,$item:ID!){ deleteProjectV2Item(input:{projectId:$project,itemId:$item}){ deletedItemId } }"""


class GitHubProjectsV2Directory(ProjectDirectory):
    def __init__(
        self,
        address: ProjectAddress,
        transport: GitHubTransport,
        authorization: Callable[[], Mapping[str, str]],
        endpoint: str = GITHUB_GRAPHQL,
    ) -> None:
        self._address, self._transport, self._authorization, self._endpoint = address, transport, authorization, endpoint
        self.addressed: list[str] = []

    # --- reads ---------------------------------------------------------------

    def schema(self) -> ProjectSchema:
        project = self._project(self._graphql(_SCHEMA_QUERY, {"project": self._address.project_id}))
        fields = {
            node["name"]: node
            for node in _nodes(project.get("fields"))
            if isinstance(node, Mapping) and isinstance(node.get("name"), str)
        }
        status, priority = fields.get("Status"), fields.get("Priority")
        if not isinstance(status, Mapping) or not isinstance(priority, Mapping):
            raise ProjectRejected("configured Project does not expose both a Status and a Priority field")
        if status.get("id") != self._address.status_field_id or priority.get("id") != self._address.priority_field_id:
            raise ProjectRejected("observed Status or Priority field is not the configured field identity")
        return ProjectSchema(
            self._address.project_id, self._address.project_number, str(project.get("title") or ""),
            str(status["id"]), _options(status), str(priority["id"]), _options(priority),
        )

    def items(self, limit: int = 50) -> tuple[ProjectItemState, ...]:
        project = self._project(self._graphql(_ITEMS_QUERY, {"project": self._address.project_id, "limit": limit}))
        return tuple(_item_state(node) for node in _nodes(project.get("items")) if isinstance(node, Mapping))

    def read_status(self, item_id: str) -> ProjectItemState:
        node = self._graphql(_ITEM_QUERY, {"item": item_id}).get("node")
        if not isinstance(node, Mapping):
            raise ProjectUnavailable("Project item could not be read back")
        self._resolve(node.get("project"))
        return _item_state(node)

    # --- fenced projection write --------------------------------------------

    def write_status(self, item_id: str, status: str, expected_revision: int) -> int:
        """Apply the lifecycle projection and confirm it by independent read-back.

        The returned revision is the caller's expected revision only when the
        Project answers with exactly the state that was written, so an
        unconfirmed write can never be mistaken for a confirmed one.
        """
        option = self.schema().status_options.get(status)
        if option is None:
            raise ProjectRejected("lifecycle state has no configured Status option")
        answer = self._graphql(_WRITE_MUTATION, {
            "project": self._address.project_id, "item": item_id,
            "field": self._address.field_for("Status"), "option": option,
        })
        written = answer.get("updateProjectV2ItemFieldValue")
        if not isinstance(written, Mapping) or not isinstance(written.get("projectV2Item"), Mapping):
            raise ProjectUnavailable("Project refused the projection write")
        self._resolve(written["projectV2Item"].get("project"))
        return expected_revision if self.read_status(item_id).status == status else -1

    # --- transient probe subject --------------------------------------------

    def add_draft_item(self, title: str) -> str:
        """Create the item a projection write needs when the Project is empty.

        This is the projection probe's own subject, removed by `delete_item`; it
        is not backlog seeding, which belongs to PY-10.
        """
        added = self._graphql(_ADD_DRAFT_MUTATION, {"project": self._address.project_id, "title": title}).get("addProjectV2DraftIssue")
        if not isinstance(added, Mapping) or not isinstance(added.get("projectItem"), Mapping):
            raise ProjectUnavailable("Project refused the probe item")
        self._resolve(added["projectItem"].get("project"))
        return str(added["projectItem"]["id"])

    def delete_item(self, item_id: str) -> str:
        deleted = self._graphql(_DELETE_MUTATION, {"project": self._address.project_id, "item": item_id}).get("deleteProjectV2Item")
        if not isinstance(deleted, Mapping):
            raise ProjectUnavailable("Project refused the probe item removal")
        return str(deleted.get("deletedItemId") or "")

    # --- internals -----------------------------------------------------------

    def _project(self, answer: Mapping[str, object]) -> Mapping[str, object]:
        node = answer.get("node")
        if not isinstance(node, Mapping):
            raise ProjectUnavailable("configured Project could not be read")
        self._resolve(node)
        return node

    def _resolve(self, observed: object) -> str:
        """Fail closed on every answer: only the configured Project is ever addressed."""
        if not isinstance(observed, Mapping):
            raise ProjectAddressRejected("observed project identity is absent or ambiguous")
        number = observed.get("number")
        resolved = self._address.resolve(observed.get("id"), number if isinstance(number, int) else None)
        self.addressed.append(resolved)
        return resolved

    def _graphql(self, query: str, variables: Mapping[str, object]) -> Mapping[str, object]:
        body = json.dumps({"query": query, "variables": dict(variables)}).encode("utf-8")
        headers = dict(self._authorization()) | {"Content-Type": "application/json"}
        response = self._transport.request("POST", self._endpoint, headers, body)
        if response.status != 200:
            raise ProjectUnavailable(f"Projects v2 answered {response.status}")
        try:
            document = json.loads(response.body or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProjectUnavailable("Projects v2 answer is not a readable document") from error
        if not isinstance(document, Mapping) or document.get("errors"):
            raise ProjectUnavailable("Projects v2 reported an error for the configured Project")
        data = document.get("data")
        if not isinstance(data, Mapping):
            raise ProjectUnavailable("Projects v2 returned no data for the configured Project")
        return data


def _nodes(container: object) -> tuple[object, ...]:
    listed = container.get("nodes") if isinstance(container, Mapping) else None
    return tuple(listed) if isinstance(listed, list) else ()


def _options(field: Mapping[str, object]) -> Mapping[str, str]:
    listed = field.get("options")
    if not isinstance(listed, list):
        return {}
    return {str(option["name"]): str(option["id"]) for option in listed if isinstance(option, Mapping) and "name" in option and "id" in option}


def _item_state(node: Mapping[str, object]) -> ProjectItemState:
    values = {}
    for value in _nodes(node.get("fieldValues")):
        if not isinstance(value, Mapping):
            continue
        field = value.get("field")
        if isinstance(field, Mapping) and isinstance(field.get("name"), str):
            values[field["name"]] = value.get("name")
    content = node.get("content")
    content_id = content.get("id") if isinstance(content, Mapping) else None
    return ProjectItemState(
        str(node.get("id") or ""),
        values.get("Status") if isinstance(values.get("Status"), str) else None,
        values.get("Priority") if isinstance(values.get("Priority"), str) else None,
        content_id if isinstance(content_id, str) else None,
    )
