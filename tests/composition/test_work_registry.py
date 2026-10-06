"""Project work registry composition: the configuration entry, read-only profile stores and injection.

The entry is looked up by the project string; it names the one project database, maps each repository name to one
configured clone with an explicit remote, and lists every profile with its own operational database, which must
already exist (opening it writes nothing). UpstreamProfile composes initial compilation only with the registry of
its own project. The optional `readiness` entry composes `work assess` over its own database and evidence folder.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from alienintent.composition.work_registry import (
    ConfigurationInvalid, WorkRegistry, load_project_configuration, project_configuration, read_only_store)
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.runtime import owner_token
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, Harness, Project, project_clone
from tests.context_assembly.test_readiness_consumer import fixture_package
from tests.context_assembly.test_work_identity_service import commit_file


def passing_suite(folder: Path, junit: Path) -> int:
    """REGRESSION-GATE's suite run for fixtures that launch a VERIFIER through the registry: one passing test case."""
    junit.write_text('<?xml version="1.0"?><testsuites><testsuite name="pytest">'
                     '<testcase classname="tests.fixture" name="test_passes"/></testsuite></testsuites>')
    return 0


def entry(root: Path, **changes) -> dict:
    value = {"database": str(root / "work.sqlite"),
             "repositories": {REPO: {"clone": str(root / "clone"), "remote": "upstream", "default_branch": "main",
                                     "packets_branch": "alienintent/work-packets"}},
             "packets": {"repository": REPO, "directory": "work-packets"},
             "profiles": {"fx": str(root / "fx.sqlite")}}
    value.update(changes)
    return {"schema_version": 1, "projects": {PROJECT: value}}


def test_configuration_entry_is_looked_up_by_project_and_names_the_remote(tmp_path):
    path = tmp_path / "projects.json"
    path.write_text(json.dumps(entry(tmp_path)))
    configuration = load_project_configuration(path, PROJECT)
    location = configuration.repositories[REPO]
    assert (configuration.database, location.remote, location.packets_branch) == (
        tmp_path / "work.sqlite", "upstream", "alienintent/work-packets")
    assert configuration.profiles == {"fx": tmp_path / "fx.sqlite"}
    with pytest.raises(ConfigurationInvalid):
        load_project_configuration(path, "AlienLogicLab/other")


@pytest.mark.parametrize("changes", [
    {"packets": {"repository": "missing", "directory": "work-packets"}}, {"profiles": {}},
    {"packets": {"repository": REPO, "directory": "../escape"}},
    {"repositories": {REPO: {"clone": "/c", "remote": "--mirror", "default_branch": "main", "packets_branch": "p"}}},
    {"repositories": {REPO: {"clone": "/c", "default_branch": "main", "packets_branch": "p"}}}])
def test_malformed_configuration_is_refused_before_anything_opens(tmp_path, changes):
    with pytest.raises(ConfigurationInvalid):
        project_configuration(entry(tmp_path, **changes), PROJECT)
    assert not (tmp_path / "work.sqlite").exists()


def test_profile_databases_are_opened_read_only(tmp_path):
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(ConfigurationInvalid):
        read_only_store(missing)
    assert not missing.exists()
    existing = tmp_path / "fx.sqlite"
    SQLiteOperationalStore(existing)
    digest = hashlib.sha256(existing.read_bytes()).hexdigest()
    store = read_only_store(existing)
    assert store.read_state("fx", "upstream:identity-reservations") == (0, {})
    assert hashlib.sha256(existing.read_bytes()).hexdigest() == digest


def test_one_service_is_shared_and_injected_into_the_compiler(tmp_path):
    h = Harness(tmp_path / "h")
    assert h.profile.work_registry is h.registry
    assert h.service.registration.identities is h.registry.identities
    assert h.service.registration.items is h.registry.items is h.registry.identities.items
    assert set(h.registry.profile_stores) == {h.name}


def test_registry_of_another_project_or_profile_is_refused(tmp_path):
    from dataclasses import replace
    from alienintent.composition.upstream_profile import UpstreamProfile
    from alienintent.context_assembly.application.initial_compilation_service import InitialCompilation
    h = Harness(tmp_path / "h")
    other = Project(tmp_path / "other", {"elsewhere": tmp_path / "h" / "operational.sqlite"})
    with pytest.raises(ValueError, match="not a configured profile"):
        InitialCompilation(h.repository, h.store, PROJECT, h.name, h.definition, "inv", frozenset(), None, None, None,
                           None, None, None, WorkRegistry(other.configuration).registration)
    foreign = WorkRegistry(replace(other.configuration, project="AlienLogicLab/other"))
    with pytest.raises(ValueError, match="another project"):
        UpstreamProfile(h.repository, h.store, PROJECT, h.name, h.definition, "inv", "Founder",
                        frozenset({"private"}), work_registry=foreign)


@pytest.mark.parametrize("missing", ["ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"])
def test_profile_factory_reads_two_required_environment_variables(tmp_path, monkeypatch, missing):
    from alienintent.composition.work_registry import work_registry_profile
    from alienintent.context_assembly.application.initial_compilation_service import WorkRegistration
    from alienintent.context_assembly.application.work_registration import WorkRecordService
    path = tmp_path / "projects.json"
    path.write_text(json.dumps(entry(tmp_path)))
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    monkeypatch.setenv("ALIENINTENT_PROJECT_CONFIGURATION", str(path))
    monkeypatch.setenv("ALIENINTENT_PROJECT", PROJECT)
    registry = work_registry_profile().work_registry
    assert registry.configuration == load_project_configuration(path, PROJECT)
    assert isinstance(registry.records, WorkRecordService) and isinstance(registry.registration, WorkRegistration)
    assert registry.records.identities is registry.identities and registry.records.items is registry.items
    monkeypatch.delenv(missing)
    with pytest.raises(ConfigurationInvalid):
        work_registry_profile()


def readiness(root: Path, **changes) -> dict:
    value = {"database": str(root / "readiness.sqlite"), "evidence_root": str(root / "evidence"),
             "executable": str(root / "fixture-agent-ready" / "bin" / "agent-ready"), "provider": "claude"}
    value.update(changes)
    return value


def fixture_agent_ready(root: Path, launched: Path) -> Path:
    """FIXTURE_PACKAGE_NOT_AGENT_READY: an executable an `agent-ready` distribution declares; it records the
    environment it was launched with and prints a READY result."""
    executable = fixture_package(root)
    executable.write_text(f"#!/bin/sh\nenv > '{launched}'\nprintf '%s' '{{\"disposition\": \"READY\"}}'\n")
    executable.chmod(0o700)
    return executable


@pytest.mark.parametrize("value", [
    lambda root: readiness(root, database=str(root / "work.sqlite")),
    lambda root: readiness(root, database=str(root / "fx.sqlite")), lambda root: readiness(root, provider=""),
    lambda root: readiness(root, executable=7), lambda root: readiness(root, extra="x"),
    lambda root: {"database": str(root / "r.sqlite")}])
def test_malformed_readiness_or_a_shared_database_is_refused(tmp_path, value):
    with pytest.raises(ConfigurationInvalid):
        project_configuration(entry(tmp_path, readiness=value(tmp_path)), PROJECT)


def test_without_readiness_there_is_no_assessment_service(tmp_path):
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    configuration = project_configuration(entry(tmp_path), PROJECT)
    assert configuration.readiness is None and WorkRegistry(configuration).assessment is None


def test_assessment_launches_the_bound_executable_with_the_attempt_markers(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-key-never-passed")
    clone, _ = project_clone(tmp_path)
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    executable = fixture_agent_ready(tmp_path, tmp_path / "launched.env")
    repositories = {REPO: {"clone": str(clone), "remote": "origin", "default_branch": "main",
                           "packets_branch": "alienintent/work-packets"}}
    registry = WorkRegistry(project_configuration(entry(tmp_path, repositories=repositories,
                                                        readiness=readiness(tmp_path, executable=str(executable))),
                                                  PROJECT))
    registry.assessment.satisfiable = None  # This legacy launch fixture has no contract block.
    assert isinstance(registry.assessment.ownership, ProcOwnership)
    packet = b"# Work unit: fixture\n"
    item = registry.records.register(packet, REPO, "docs/p.md", commit_file(clone, "main", "docs/p.md", packet), "P")
    result = registry.assessment.assess(item.id)
    assert result.disposition == "READY"
    [attempt] = registry.assessment.consumer.history(item.id)
    launched = dict(line.split("=", 1) for line in (tmp_path / "launched.env").read_text().splitlines() if "=" in line)
    assert launched["ALIENINTENT_INVOCATION_ID"] == result.attempt_id
    assert attempt["owner"] == dict(ProcOwnership().current())
    assert launched["ALIENINTENT_INVOCATION_OWNER"] == owner_token(attempt["owner"])
    assert "ANTHROPIC_API_KEY" not in launched
    assert registry.records.show(item.id).item.assessment_ref == ref_from_document(attempt["raw_ref"])
    assert (tmp_path / "readiness.sqlite").is_file() and any((tmp_path / "evidence").rglob("*"))


def test_authorization_is_wired_on_the_readiness_store_clone_and_default_branch(tmp_path):
    """`work authorize` exists only with `readiness`; its release records are the ones `work assess` checks, on the
    readiness store under profile `registry`; baselines are checked in the configured clone against its configured
    default branch; the evidence goes to the assessment evidence folder."""
    from alienintent.context_assembly.application.work_authorization import WorkAuthorization
    from alienintent.execution_coordination.domain.release import ReleaseAuthorization
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    assert WorkRegistry(project_configuration(entry(tmp_path), PROJECT)).authorization is None
    clone, _ = project_clone(tmp_path)
    head = commit_file(clone, "main", "docs/p.md", b"p\n")
    repositories = {REPO: {"clone": str(clone), "remote": "origin", "default_branch": "trunk",
                           "packets_branch": "alienintent/work-packets"}}
    registry = WorkRegistry(project_configuration(entry(tmp_path, repositories=repositories,
                                                        readiness=readiness(tmp_path)), PROJECT))
    authorization = registry.authorization
    assert isinstance(authorization, WorkAuthorization)
    assert authorization.releases is registry.assessment.authorizations
    assert authorization.release_points == {REPO: "trunk"} and authorization.consumer is registry.assessment.consumer
    assert authorization.evidence is registry.assessment.consumer.repository
    assert authorization.revisions.resolves(REPO, head)
    assert not authorization.revisions.is_reachable(REPO, head, "trunk")
    authorization.releases.record(ReleaseAuthorization("fixture", "sha256:" + "a" * 64, True, head, "fixture"))
    store = SQLiteOperationalStore(tmp_path / "readiness.sqlite")
    _, raw = store.read_state("registry", "release-authorization:fixture")
    assert raw["baseline"] == head


def test_completion_is_wired_on_the_readiness_store_clone_and_default_branch(tmp_path):
    """`work record-completed` exists only with `readiness`: its evidence goes to the assessment evidence folder,
    landings are checked in the configured clone against its configured default branch, the landing record is read
    with the adapter's `read_packet`, and the coordinator record it checks is `factory:<id>` under profile `registry`
    on the readiness store."""
    from alienintent.context_assembly.application.work_completion import WorkCompletion
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    assert WorkRegistry(project_configuration(entry(tmp_path), PROJECT)).completion is None
    clone, _ = project_clone(tmp_path)
    head = commit_file(clone, "main", "docs/p.md", b"p\n")
    repositories = {REPO: {"clone": str(clone), "remote": "origin", "default_branch": "trunk",
                           "packets_branch": "alienintent/work-packets"}}
    registry = WorkRegistry(project_configuration(entry(tmp_path, repositories=repositories,
                                                        readiness=readiness(tmp_path)), PROJECT))
    completion = registry.completion
    assert isinstance(completion, WorkCompletion) and completion.records is registry.records
    assert completion.evidence is registry.assessment.consumer.repository
    assert completion.release_points == {REPO: "trunk"} and completion.read_packet == registry.items.read_packet
    assert completion.revisions.resolves(REPO, head) and not completion.revisions.is_reachable(REPO, head, "trunk")
    assert completion.coordinator_record("fixture") == {}
    registry.assessment.consumer.store.commit("registry", "factory:fixture", 0, {"stage": "IMPLEMENT"})
    assert completion.coordinator_record("fixture") == {"stage": "IMPLEMENT"}

def github(root: Path, **changes) -> dict:
    value = {"repository": "AlienLogicLab/alienintent-sandbox", "application_id": 1000001,
             "installation_id": 2000002, "private_key_path": str(root / "key.pem"),
             "project": {"project_id": "PVT_kwDOfixtureSandboxProject", "project_number": 2,
                         "organization": "AlienLogicLab", "status_field_id": "PVTSSF_s",
                         "priority_field_id": "PVTSSF_p"}}
    value.update(changes)
    return value


def test_without_github_there_is_no_link_service_and_with_it_nothing_is_sent_at_composition(tmp_path):
    from alienintent.context_assembly.application.work_link import WorkLink
    from tests.support.live_github import RecordedTransport
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    configuration = project_configuration(entry(tmp_path), PROJECT)
    assert configuration.github is None and WorkRegistry(configuration).links is None
    configuration = project_configuration(entry(tmp_path, github=github(tmp_path)), PROJECT)
    assert (configuration.github.repository, configuration.github.private_key_path,
            configuration.github.project.project_number) == (
        "AlienLogicLab/alienintent-sandbox", tmp_path / "key.pem", 2)
    transport = RecordedTransport({})
    registry = WorkRegistry(configuration, transport=transport)
    assert isinstance(registry.links, WorkLink) and registry.links.records is registry.records
    assert registry.links.items is registry.items and transport.calls == []


@pytest.mark.parametrize("value", [
    lambda root: github(root, application_id="4990774"), lambda root: github(root, installation_id=0),
    lambda root: github(root, repository="alienintent"), lambda root: github(root, private_key_path=""),
    lambda root: github(root, extra=1), lambda root: github(root, project={"project_id": "PVT_x"}),
    lambda root: github(root, project=dict(github(root)["project"], project_id="not-a-node")), lambda root: []])
def test_a_malformed_github_entry_is_refused(tmp_path, value):
    with pytest.raises(ConfigurationInvalid):
        project_configuration(entry(tmp_path, github=value(tmp_path)), PROJECT)


# --- the READY view of board #1 (checks 2-7) ------------------------------------------------------------------------

from alienintent.composition.work_registry import (  # noqa: E402
    ASSESSMENT_MISSING, CONTRACT_INVALID, DISPLAY_DIFFERS, NO_LINK, NOT_ELIGIBLE, OPERATOR, READY_VIEW, ROW_REFUSED,
    WORK_PREPARATION)
from alienintent.context_assembly.domain.work_contract import UNCLOSED  # noqa: E402
from alienintent.context_assembly.domain.work_identity import Pointer  # noqa: E402
from alienintent.context_assembly.domain.work_link import UPDATED, render  # noqa: E402
from alienintent.context_assembly.domain.work_contract import contract_block  # noqa: E402
from tests.context_assembly.test_readiness_consumer import fixture_package as _package  # noqa: E402
from tests.context_assembly.test_work_contract import contract_payload  # noqa: E402
from tests.context_assembly.test_work_link import Linked, RecordedGitHub  # noqa: E402
from tests.support.live_github import PRIORITY_FIELD, SANDBOX_PROJECT, STATUS_FIELD  # noqa: E402


class Board(RecordedGitHub):
    """The recorded GitHub of `work link`, whose board also answers the paginated items read with each card's Status
    (and its READY-entry time) and Priority, and its Issue's current title and body."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, dict[str, str | None]] = {}

    def _board(self, query: str, variables: dict) -> object:
        if "items(first:100,after:$cursor)" not in query:
            return super()._board(query, variables)
        self.log.append("items")
        nodes = [self._node(card) for card in self.cards]
        return {"data": {"node": {"id": SANDBOX_PROJECT, "number": 2, "items": {
            "totalCount": len(nodes), "pageInfo": {"hasNextPage": False, "endCursor": "end"}, "nodes": nodes}}}}

    def _node(self, card: str) -> dict:
        issue = next((i for i in self.issues.values() if i["node_id"] == self.cards[card]), None)
        fields = self.fields.get(card, {})
        values = [{"name": fields["Status"], "updatedAt": fields.get("at"), "field": {"id": STATUS_FIELD, "name": "Status"}}]
        if fields.get("Priority"):
            values.append({"name": fields["Priority"], "updatedAt": None,
                           "field": {"id": PRIORITY_FIELD, "name": "Priority"}})
        content = {"id": self.cards[card], "title": issue["title"], "body": issue["body"]} if issue else None
        return {"id": card, "content": content, "fieldValues": {"nodes": values if fields.get("Status") else []}}


class ReadyBoard(Linked):
    """A fixture project with both the `github` and `readiness` entries over the recorded board; Agent Ready is a
    fixture executable answering the disposition written in `answer`."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.answer = root / "disposition"
        self.answer.write_text("READY")
        executable = _package(root)
        executable.write_text(f"#!/bin/sh\nprintf '{{\"disposition\": \"%s\"}}' \"$(cat '{self.answer}')\"\n")
        executable.chmod(0o700)
        self.document["projects"][PROJECT]["readiness"] = readiness(root, executable=str(executable))
        self.github = Board()
        self.registry = self.second()
        self.links = self.registry.links

    def second(self) -> WorkRegistry:
        """Another registry instance over the same configuration, as another process would build it."""
        registry = WorkRegistry(project_configuration(self.document, PROJECT), transport=self.github,
                                suite_run=passing_suite)
        registry.assessment.satisfiable = None  # Legacy READY-view packets exercise the existing view gates.
        registry.authorization.satisfiable = None
        return registry

    def packet(self, item, *, payload: dict | None = None, raw: str | None = None) -> bytes:
        payload = payload(item) if callable(payload) else payload
        text = raw if raw is not None else json.dumps(payload or contract_payload(item.id), indent=1)
        return (f"# Work unit: {item.label}\n\nidentity: not-this-one\n\n```json alienintent-contract\n{text}\n```\n"
                .encode())

    def ready(self, label: str, *, at: str, priority: str | None = "P1", payload=None, raw: str | None = None,
              assess: bool = True, link: bool = True):
        """Register, give the packet its contract block at a new commit, assess it, link it and put it in READY."""
        item = self.item(label)
        data = self.packet(item, payload=payload, raw=raw)
        commit = commit_file(self.clone, "main", f"docs/{label}.md", data)
        if assess:
            self.registry.assessment.assess(item.id, (data, commit))
        else:
            self.registry.identities.set_pointer(item.id, Pointer(REPO, f"docs/{label}.md", commit, data))
        if link:
            card = self.links.link(item.id).card_id
            self.github.fields[card] = {"Status": "READY", "at": at, "Priority": priority}
        return self.stored(label)

    def snapshot(self, registry: WorkRegistry | None = None):
        registry = registry or self.registry
        imported = registry.ready_view.import_ready_snapshot()
        return imported, registry.ready_refusals()


@pytest.fixture
def board(tmp_path) -> ReadyBoard:
    return ReadyBoard(tmp_path / "fx")


def test_one_composed_check_refuses_an_authority_reference_missing_at_the_pointer(board):
    from alienintent.execution_coordination.domain.closure import ACTIONS
    from alienintent.context_assembly.application.work_authorization import CONTRACT_UNSATISFIABLE

    registry = WorkRegistry(project_configuration(board.document, PROJECT), transport=board.github)
    assert registry.assessment.satisfiable is registry.authorization.satisfiable is registry.satisfiable
    item = board.item("MISSING-REFERENCE")
    payload = contract_payload(
        item.id, required_evidence=["independent-verifier-accepted"],
        budget_policy={"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1},
        required_closure_actions=list(ACTIONS), authority_references=["docs/absent.md explanation"])
    packet = board.packet(item, payload=payload)
    commit = commit_file(board.clone, "main", "docs/MISSING-REFERENCE.md", packet)
    result = registry.assessment.assess(item.id, (packet, commit))
    assert result.reason_code == CONTRACT_UNSATISFIABLE
    assert "authority_references: absent at pointer: docs/absent.md explanation" in result.detail
    assert not registry.assessment.consumer.history(item.id)


def kinds(refusals) -> dict[tuple[str, str], object]:
    return {(refusal.card, refusal.kind): refusal for refusal in refusals}


def ready_view_items(registry: WorkRegistry) -> list:
    return [item for item in registry._attention.list_pending() if item.origin.lane == READY_VIEW]


def test_the_view_exists_only_with_both_the_github_and_readiness_entries(tmp_path):
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    for changes in ({}, {"github": github(tmp_path)}, {"readiness": readiness(tmp_path)}):
        assert WorkRegistry(project_configuration(entry(tmp_path, **changes), PROJECT)).ready_view is None
    view = WorkRegistry(project_configuration(entry(tmp_path, github=github(tmp_path), readiness=readiness(tmp_path)),
                                              PROJECT)).ready_view
    assert view._profile == "registry" and view._projection_fields == {} and view._projection_write is None
    assert view._status_mapping["READY"] == "READY" and view._repository == "AlienLogicLab/alienintent-sandbox"


def test_check2_the_row_comes_from_the_record_and_the_display_is_repaired_separately(board):
    item = board.ready("RV-A", at="2026-10-02T10:00:00Z",
                       payload=lambda item: contract_payload(item.id, dependencies=["dep-1"]))
    issue = board.github.issues[item.issue_number]
    other = contract_payload("other-identity", dependencies=["dep-9"])
    issue.update(title="OTHER", body="biu: other-identity\ncontract: biu/OTHER.json\ndepends_on: dep-9\n"
                 f"```json alienintent-contract\n{json.dumps(other)}\n```\n")
    board.github.log.clear()
    calls = len(board.github.calls)

    imported, refusals = board.snapshot()

    [row] = imported
    expected = contract_block(board.registry.records.show(item.id).packet, item.id)
    assert (row.identity, row.dependencies, row.contract, row.readiness_digest) == (
        item.id, ("dep-1",), expected, expected.content_digest)
    assert row.readiness_evidence == item.assessment_ref.logical_id and row.priority == 1
    assert [(r.card, r.kind, r.owner, r.recorded) for r in refusals] == [
        (item.card_id, DISPLAY_DIFFERS, WORK_PREPARATION, True)]
    assert board.github.log == ["items"]  # The snapshot read the board and wrote nothing.
    assert [url for _, url in board.github.calls[calls:] if not url.endswith(("/graphql", "/access_tokens"))] == []

    [repaired] = board.registry.repair_displays()
    assert repaired.display == UPDATED and repaired.answer is None
    assert board.github.writes() == ["update"]
    assert (issue["title"], issue["body"]) == (render(item).title, render(item).body)

    imported, refusals = board.snapshot()
    assert [r.identity for r in imported] == [item.id]
    assert [(r.kind, r.cleared) for r in refusals] == [(DISPLAY_DIFFERS, True)]
    assert board.registry.repair_displays() == ()


@pytest.mark.parametrize(("change", "detail"), [
    ({"raw": '{"identity": "x",'}, "invalid JSON"),
    ({"payload": lambda item: contract_payload("another-item")}, "identity is not the work item's id"),
    ({"payload": lambda item: contract_payload(item.id, intent="")}, "refused by the validator")])
def test_check3_an_invalid_block_is_contract_invalid_naming_which(board, change, detail):
    board.ready("RV-C", at="2026-10-02T10:00:00Z", **change)

    imported, refusals = board.snapshot()

    assert imported == ()
    [refusal] = refusals
    assert (refusal.kind, refusal.owner) == (CONTRACT_INVALID, WORK_PREPARATION) and detail in refusal.reason


def test_check3_an_unclosed_block_is_contract_invalid(board):
    item = board.item("RV-U")
    data = f"# Work unit\n\n```json alienintent-contract\n{json.dumps(contract_payload(item.id))}\n".encode()
    commit = commit_file(board.clone, "main", "docs/RV-U.md", data)
    board.registry.assessment.assess(item.id, (data, commit))
    board.github.fields[board.links.link(item.id).card_id] = {"Status": "READY", "at": "t", "Priority": "P1"}

    [refusal] = board.snapshot()[1]
    assert refusal.kind == CONTRACT_INVALID and UNCLOSED in refusal.reason


def test_check4_only_a_ready_assessment_of_the_exact_commit_imports(board):
    unassessed = board.ready("RV-N", at="2026-10-02T10:00:01Z", assess=False)
    board.answer.write_text("HOLD")
    held = board.ready("RV-H", at="2026-10-02T10:00:02Z")
    board.answer.write_text("READY")
    moved = board.ready("RV-M", at="2026-10-02T10:00:03Z")
    data = board.packet(moved) + b"\nA later edit.\n"
    board.registry.identities.set_pointer(moved.id, Pointer(REPO, "docs/RV-M.md",
                                                            commit_file(board.clone, "main", "docs/RV-M.md", data), data))
    assert board.stored("RV-M").assessment_ref == moved.assessment_ref  # READY, but of the earlier commit

    imported, refusals = board.snapshot()

    assert imported == ()
    found = kinds(refusals)
    assert {key[1] for key in found} == {ASSESSMENT_MISSING}
    assert {key[0] for key in found} == {unassessed.card_id, held.card_id, moved.card_id}
    assert "HOLD" in found[(held.card_id, ASSESSMENT_MISSING)].reason
    assert "current pointer" in found[(moved.card_id, ASSESSMENT_MISSING)].reason


def test_check5_a_ready_card_with_no_link_is_never_imported(board):
    number = board.github.seed(json.dumps(contract_payload("free")), title="free")
    board.github.cards["PVTI_free"] = board.github.issues[number]["node_id"]
    board.github.fields["PVTI_free"] = {"Status": "READY", "at": "2026-10-02T10:00:00Z", "Priority": "P0"}

    imported, refusals = board.snapshot()

    assert imported == ()
    assert [(r.card, r.kind, r.owner) for r in refusals] == [("PVTI_free", NO_LINK, WORK_PREPARATION)]


def test_check6_one_bad_card_of_each_kind_never_stalls_the_valid_ones_and_order_is_kept(board):
    first = board.ready("RV-Z", at="2026-10-02T10:00:05Z")
    second = board.ready("RV-Y", at="2026-10-02T10:00:01Z")
    tied = board.ready("RV-A", at="2026-10-02T10:00:05Z")  # same second as RV-Z: the card id decides, not the title
    board.github.cards["PVTI_free"] = "I_free"
    board.github.fields["PVTI_free"] = {"Status": "READY", "at": "2026-10-02T10:00:00Z", "Priority": "P0"}
    retired = board.ready("RV-R", at="2026-10-02T10:00:00Z")
    board.registry.identities.retire(retired.id)
    unassessed = board.ready("RV-N", at="2026-10-02T10:00:00Z", assess=False)
    invalid = board.ready("RV-I", at="2026-10-02T10:00:00Z", raw="not json")
    unprioritized = board.ready("RV-P", at="2026-10-02T10:00:00Z", priority=None)
    not_ready = board.ready("RV-X", at="2026-10-02T09:00:00Z")
    board.github.fields[not_ready.card_id]["Status"] = "IMPLEMENT"

    imported, refusals = board.snapshot()

    ordered = sorted([first, second, tied], key=lambda item: (
        board.github.fields[item.card_id]["at"], item.card_id))
    assert [row.identity for row in imported] == [item.id for item in ordered]
    assert ordered == [second, first, tied] and first.card_id < tied.card_id
    assert [row.fifo for row in imported] == sorted(row.fifo for row in imported)
    assert {(r.card, r.kind, r.owner, r.recorded) for r in refusals} == {
        ("PVTI_free", NO_LINK, WORK_PREPARATION, True),
        (retired.card_id, NOT_ELIGIBLE, WORK_PREPARATION, True),
        (unassessed.card_id, ASSESSMENT_MISSING, WORK_PREPARATION, True),
        (invalid.card_id, CONTRACT_INVALID, WORK_PREPARATION, True),
        (unprioritized.card_id, ROW_REFUSED, OPERATOR, True)}
    assert len({r.attention for r in refusals}) == 5 and len(ready_view_items(board.registry)) == 5


def test_check7_one_open_item_per_card_and_kind_across_snapshots_and_instances(board):
    card = board.ready("RV-7", at="2026-10-02T10:00:00Z", priority=None).card_id
    instances, seen = (board.registry, board.second()), set()
    for number in range(50):  # Alternating instances, and the reason text changes between them.
        board.github.fields[card]["Priority"] = None if number % 2 else "P9"
        imported, refusals = board.snapshot(instances[number % 2])
        [refusal] = refusals
        assert (imported, refusal.kind, refusal.recorded, refusal.cleared) == ((), ROW_REFUSED, True, False)
        seen.add((refusal.attention, refusal.reason))
    assert len({attention for attention, _ in seen}) == 1 and len({reason for _, reason in seen}) == 2
    [item] = ready_view_items(board.second())
    assert (item.origin.work_ref, item.origin.event_identity, item.origin.kind, item.origin.required_authority,
            item.version) == (card, ROW_REFUSED, "JUDGMENT", OPERATOR, 1)

    issue = board.github.issues[board.stored("RV-7").issue_number]
    issue["title"] = "edited"
    _, refusals = board.snapshot(board.second())
    found = kinds(refusals)
    assert set(found) == {(card, ROW_REFUSED), (card, DISPLAY_DIFFERS)}
    assert found[(card, ROW_REFUSED)].attention == item.identity != found[(card, DISPLAY_DIFFERS)].attention
    assert len(ready_view_items(board.registry)) == 2

    board.github.fields[card]["Priority"] = "P1"
    issue["title"] = "RV-7"
    imported, refusals = board.snapshot()
    assert [row.identity for row in imported] == [board.stored("RV-7").id]
    assert {(r.kind, r.cleared, r.attention) for r in refusals} == {
        (ROW_REFUSED, True, item.identity), (DISPLAY_DIFFERS, True, found[(card, DISPLAY_DIFFERS)].attention)}
    assert all(i.status != "RESOLVED" for i in ready_view_items(board.registry))


def test_an_unwritable_attention_store_marks_refusals_unrecorded_and_import_continues(board):
    good = board.ready("RV-G", at="2026-10-02T10:00:00Z")
    board.github.cards["PVTI_free"] = "I_free"
    board.github.fields["PVTI_free"] = {"Status": "READY", "at": "2026-10-02T10:00:00Z", "Priority": "P0"}

    def unwritable(*_):
        raise OSError("read-only")
    board.registry._attention.repository.save = unwritable

    imported, refusals = board.snapshot()
    assert [row.identity for row in imported] == [good.id]
    assert [(r.card, r.kind, r.recorded, r.attention) for r in refusals] == [("PVTI_free", NO_LINK, False, None)]


def test_an_unreadable_board_fails_the_snapshot_with_no_rows_and_no_items(board):
    from alienintent.execution_coordination.ports.work_management import WorkUnavailable
    board.github.cards["PVTI_free"] = "I_free"
    board.github.fields["PVTI_free"] = {"Status": "READY", "at": "t", "Priority": "P0"}
    board.snapshot()
    original = board.github._graphql
    board.github._graphql = lambda query, variables: (
        {"errors": [{"message": "fault"}]} if "items(first:100" in query else original(query, variables))
    with pytest.raises(WorkUnavailable):
        board.registry.ready_view.import_ready_snapshot()
    assert board.registry.ready_view.last_refusals == ()
    assert board.registry.ready_refusals() == ()  # An unread board clears nothing.
    assert WorkRegistry(project_configuration(board.document, PROJECT), transport=board.github).ready_refusals() == ()
    assert len(ready_view_items(board.registry)) == 1


# --- READY selection, release gate and WIP admission (unit 6b, checks 5, 7 and 8) ---------------------------------

from alienintent.composition.work_registry import wip_limit  # noqa: E402
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage  # noqa: E402
from alienintent.execution_coordination.domain.release import ReleaseAuthorization  # noqa: E402


@pytest.mark.parametrize(("document", "expected"), [
    ({"wipLimit": 1}, 1), ({"wipLimit": 7, "founderHoldRecord": 3}, 7), ({"wipLimit": 0}, None),
    ({"wipLimit": -2}, None), ({"wipLimit": "1"}, None), ({"wipLimit": 1.0}, None), ({"wipLimit": True}, None),
    ({"wipLimit": 2 ** 53}, None), ({}, None), ([1], None), ("{", None), (None, None)])
def test_check5_the_wip_limit_reader_reads_the_file_on_every_call(tmp_path, document, expected):
    host = tmp_path / "factory-director-host.json"
    if document is not None:
        host.write_text(document if isinstance(document, str) else json.dumps(document))
    assert wip_limit(host) == expected
    host.write_text(json.dumps({"wipLimit": 5}))
    assert wip_limit(host) == 5  # nothing kept from the previous call
    host.unlink()
    assert wip_limit(host) is None  # no default


def _registry_run(board, tmp_path, label: str, *, record: dict | None, release: bool = True):
    """A READY-view work item, an optional release record on the registry store, and one coordinator run."""
    from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
    from tests.execution_coordination.test_factory_coordinator import ScriptedWorker
    item = board.ready(label, at="2026-10-03T10:00:00Z")
    if record is not None:
        values = {"identity": item.id, "record_ref": f"issue:{item.id}:release", "authorizes_implement": True,
                  "baseline": item.pointer.commit, "text": "IMPLEMENT is authorized."} | record
        board.registry.assessment.authorizations.record(ReleaseAuthorization(**values))
    host = tmp_path / "factory-director-host.json"
    host.write_text(json.dumps({"wipLimit": 1}))
    registry = WorkRegistry(project_configuration(board.document, PROJECT), transport=board.github,
                            host_configuration=host)
    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
    worker = ScriptedWorker(artifacts, {item.id: ["success"]})
    coordinator = registry.coordinator(worker, artifacts)
    summary = coordinator.release_and_start(item.id) if release else coordinator.start()
    return registry, coordinator, worker, summary, item


def test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store(board, tmp_path):
    """The release gate reads the release record from the readiness store (profile `registry`) and checks the starting
    revision in the packets repository's clone against its default branch; WIP admission and the launch follow."""
    registry, coordinator, worker, summary, item = _registry_run(board, tmp_path, "RV-OK", record={})
    assert (coordinator._profile, coordinator._automatic_release) == ("registry", False)
    assert coordinator._store is registry.assessment.consumer.store and worker.dispatched == [item.id]
    state = coordinator.state(item.id)
    # contract_payload allows one attempt and requires evidence no verifier gives: REVIEW reworks into `failure`.
    assert (state.outcome, state.record["hold_reason"]) == ("failure", "attempt-budget-exhausted")
    assert summary.dispatched == (item.id,) and registry.cycles(item.id) == (2, 1)
    assert [r for r in registry.assessment.consumer.store.recovery_reservations("registry")] == []


@pytest.mark.parametrize(("record", "check"), [
    (None, "implementation-authorized"), ({"baseline": "side"}, "baseline-reachable"),
    ({"baseline": "0" * 40}, "baseline-resolves")])
def test_check7_without_a_valid_release_record_nothing_is_launched(board, tmp_path, record, check):
    if record is not None and record["baseline"] == "side":
        record = {"baseline": commit_file(board.clone, "side", "docs/side.md", b"side\n")}
    registry, coordinator, worker, summary, item = _registry_run(board, tmp_path, "RV-NO", record=record)
    projected = coordinator.state(item.id)
    assert worker.invocations == [] and summary.authority_blocked == (item.id,)
    assert (projected.outcome, projected.record["hold_reason"]) == ("authority-block", f"release-precondition:{check}")
    assert registry.cycles(item.id) == (0, 0)  # a gate refusal never entered implementation
    assert registry.assessment.consumer.store.recovery_reservations("registry") == ()


def test_check7_a_registry_item_is_never_selected_without_release_and_start(board, tmp_path):
    registry, coordinator, worker, summary, item = _registry_run(board, tmp_path, "RV-HELD", record={}, release=False)
    assert worker.invocations == [] and summary.stop_reason.value == "dependencies-or-authority-blocked"
    with pytest.raises(KeyError):
        coordinator.state(item.id)
    assert registry.cycles(item.id) is None


def test_check8_work_display_shows_the_counts_from_the_coordinator_state(board, tmp_path):
    """After a transition the READY view reports DISPLAY_DIFFERS until `repair_displays` writes the counts; then it
    no longer differs. A work item without coordinator state renders as before; unknown counts are shown unknown."""
    registry, coordinator, _, _, item = _registry_run(board, tmp_path, "RV-COUNT", record={})
    plain = board.ready("RV-PLAIN", at="2026-10-03T11:00:00Z")
    imported, refusals = board.snapshot(registry)
    assert {(r.card, r.kind) for r in refusals} == {(item.card_id, DISPLAY_DIFFERS)}
    [repaired] = registry.repair_displays()
    assert repaired.display == UPDATED
    body = board.github.issues[item.issue_number]["body"]
    assert body == render(item, (2, 1)).body and body.endswith("\nIMPLEMENT cycles: 2 · VERIFY cycles: 1")
    assert board.github.issues[plain.issue_number]["body"] == render(plain).body
    assert "IMPLEMENT cycles" not in render(plain).body and registry.cycles(plain.id) is None
    _, refusals = board.snapshot(registry)
    assert [(r.card, r.kind, r.cleared) for r in refusals] == [(item.card_id, DISPLAY_DIFFERS, True)]
    assert registry.links.display(item.id).display == "unchanged"  # a display repair changes no count
    assert registry.cycles(item.id) == (2, 1)

    store = registry.assessment.consumer.store  # an older record without launch evidence: unknown, shown unknown
    store.commit("registry", f"factory:{plain.id}", 0, {"stage": LifecycleStage.IMPLEMENT.value, "version": 0,
                                                       "accepted": False, "closure": [], "candidate": None})
    assert registry.cycles(plain.id) == (None, None)
    assert registry.links.display(plain.id).display == UPDATED
    assert board.github.issues[plain.issue_number]["body"].endswith("\nIMPLEMENT cycles: unknown · VERIFY cycles: unknown")


def test_the_coordinator_counts_recorded_completions_through_the_completion_reader(board):
    """RECORD-COMPLETED-WORK check 4: the registry coordinator is given `completion`'s reader for dependencies."""
    assert board.registry.coordinator(None, None)._recorded_completion == board.registry.completion.recorded

def test_the_coordinator_needs_the_ready_view(tmp_path):
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    with pytest.raises(ConfigurationInvalid):
        WorkRegistry(project_configuration(entry(tmp_path, readiness=readiness(tmp_path)), PROJECT)).coordinator(None, None)


# --- unit 6c-1: the read-only worker profile -------------------------------------------------------------------------


def test_the_worker_profile_assembles_read_only_over_wal_databases(tmp_path, monkeypatch):
    """Founder check (b): both databases in WAL mode with -wal and -shm present, the last writes only in the -wal;
    after assembly through the worker profile the database and -wal bytes are unchanged. A profile opening either
    database writable checkpoints its -wal on close; one building WorkRegistry resolves the Agent Ready executable."""
    from alienintent.composition import work_registry
    from alienintent.composition.work_registry import work_context_profile
    from alienintent.context_assembly.domain.work_context import PRODUCER, ContextPackage
    from alienintent.execution_coordination.ports.operational_store import StoreUnavailable
    from tests.context_assembly.test_work_context import Cx
    from tests.execution_coordination.test_operational_store import file_bytes, leave_in_wal
    cx = Cx(tmp_path / "cx")
    cx.registry.assessment.satisfiable = None  # This preexisting WAL fixture uses a legacy contract.
    cx.registry.authorization.satisfiable = None
    item = cx.admitted(reserve=False)
    work, readiness_database = cx.root / "work.sqlite", cx.root / "readiness.sqlite"
    leave_in_wal(readiness_database, "INSERT INTO reservations VALUES ('registry', 'repository', 'repository-UNIT', "
                                     f"'launch:{item.id}:0', 1)")
    leave_in_wal(work, f"UPDATE work_item SET updated_at = '2026-10-03T00:00:00.000Z' WHERE id = '{item.id}'")
    before = file_bytes(work), file_bytes(readiness_database)
    monkeypatch.setenv("ALIENINTENT_PROJECT_CONFIGURATION", str(cx.configuration_file))
    monkeypatch.setenv("ALIENINTENT_PROJECT", PROJECT)

    def refused(*_, **__):
        raise AssertionError("the worker profile builds only the readers work context needs")
    monkeypatch.setattr(work_registry, "resolve_binding", refused)
    monkeypatch.setattr(work_registry, "WorkRegistry", refused)
    profile = work_context_profile()
    assert profile.worker_profile is True and set(vars(profile.work_registry)) == {"context"}
    context = profile.work_registry.context
    package = context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None)
    assert isinstance(package, ContextPackage)  # The reservation it needs exists only in the -wal file.
    with pytest.raises(StoreUnavailable):
        context.store.commit("registry", "anything", 0, {})
    assert (file_bytes(work), file_bytes(readiness_database)) == before
    monkeypatch.undo()
    assert cx.registry.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None) == package


# --- unit 6c-2: the launch composition ------------------------------------------------------------------------------


def test_the_launcher_needs_the_ready_view_and_a_configuration_file(board, tmp_path):
    """`work launch` needs the context command, which names the configuration file; and the READY view."""
    with pytest.raises(ConfigurationInvalid):
        board.registry.launcher()  # loaded from a document, not a file: no context command
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    path = tmp_path / "readiness-only.json"
    path.write_text(json.dumps(entry(tmp_path, readiness=readiness(tmp_path))))
    with pytest.raises(ConfigurationInvalid):
        WorkRegistry(load_project_configuration(path, PROJECT)).launcher()
