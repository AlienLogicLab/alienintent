"""Project work registry composition: the configuration entry, read-only profile stores and injection.

The entry is looked up by the project string; it names the one project database, maps each repository name to one
configured clone with an explicit remote, and lists every profile with its own operational database, which must
already exist (opening it writes nothing). UpstreamProfile composes initial compilation only with the registry of
its own project.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from alienintent.composition.work_registry import (
    ConfigurationInvalid, WorkRegistry, load_project_configuration, project_configuration, read_only_store)
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, Harness, Project


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
