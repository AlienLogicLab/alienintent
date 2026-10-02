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
