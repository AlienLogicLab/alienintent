"""Pure work identity rules (acceptance check 5 and the domain side of checks 1 and 2).

Labels are not identities; the grammar admits existing names and service-issued UUIDs; request references have a
closed set of kinds with a per-kind value format; migration planning keeps one key per name and one name per key.
Names below are TEST DATA.
"""
from pathlib import Path
import re

import pytest

from alienintent.context_assembly.domain.compilation import identity_valid
from alienintent.context_assembly.domain.work_identity import (
    TRANSITIONS, IllegalTransition, InvalidRequestRef, InvalidWorkItem, MigrationConflict, Pointer, RequestRef,
    check_transition, is_uuid, parse_request_ref, plan_migration, valid_identity)

ROOT = Path(__file__).resolve().parents[2]
UUID = "6f1c2a9e-4b7d-4e2f-9a31-0c5d8e7f6a12"
POLICIES = ({"family": "PY", "width": 2}, {"family": "WO", "width": 6}, {"family": "PG", "width": 2})


@pytest.mark.parametrize("policy", POLICIES)
def test_uuid_is_valid_under_any_policy_and_never_suffixed(policy):
    assert identity_valid(UUID, policy) and valid_identity(UUID) and is_uuid(UUID)
    for invalid in (UUID + "B", UUID.upper(), UUID.replace("-4e2f-", "-1e2f-"), "PY-SELF-00", "PY-1", "WO-1"):
        assert not identity_valid(invalid, policy) and not valid_identity(invalid), invalid


def test_existing_names_keep_their_policy_rules():
    assert identity_valid("PY-09", POLICIES[0]) and identity_valid("PY-09B", POLICIES[0])
    assert not identity_valid("PY-09", POLICIES[1]) and identity_valid("WO-000005", POLICIES[1])
    assert valid_identity("PY-09B") and not is_uuid("PY-09")


def test_no_production_file_parses_a_number_out_of_a_name():
    sources = [ROOT / "src/alienintent/context_assembly" / p for p in (
        "domain/work_identity.py", "domain/initial_compilation.py", "application/work_identity_service.py",
        "application/initial_compilation_service.py", "adapters/work_item_repository.py")]
    for source in sources:
        text = source.read_text()
        assert not re.search(r"10 \*\*|:0\{width\}d|int\(\s*(?:name|identity)|range\(1,", text), source


@pytest.mark.parametrize("text, expected", [
    ("requirement:SF-REQ-911", RequestRef("requirement", "SF-REQ-911")),
    ("packet:alienintent/docs/p.md", RequestRef("packet", "alienintent/docs/p.md")),
    ("packet:AlienLogicLab/alienintent/docs/p.md", RequestRef("packet", "AlienLogicLab/alienintent/docs/p.md")),
    ("issue:153", RequestRef("issue", "153")), ("legacy:PY-09B", RequestRef("legacy", "PY-09B"))])
def test_request_reference_kinds_and_values(text, expected):
    parsed = parse_request_ref(text, ("alienintent", "AlienLogicLab/alienintent"))
    assert parsed == expected and str(parsed) == text


@pytest.mark.parametrize("text", ["label:PY-10", "PY-10", "", None, "packet:docs/p.md", "packet:alienintent/../x",
                                  "packet:other/docs/p.md", "issue:-1", "issue:1a", "legacy:" + UUID,
                                  "legacy:PY-SELF-00", "requirement:", "requirement:R/1", "requirement:é"])
def test_invalid_request_references_are_refused(text):
    with pytest.raises(InvalidRequestRef):
        parse_request_ref(text, ("alienintent",))


def test_transition_table_is_formal_design_7_3():
    assert len(TRANSITIONS) == 9
    check_transition("CAPTURE", "SPECIFY")
    check_transition("VERIFY", "IMPLEMENT")
    for pair in (("CAPTURE", "DONE"), ("SPECIFY", "SPECIFY"), ("DONE", "CAPTURE"), ("READY", "TASKS")):
        with pytest.raises(IllegalTransition):
            check_transition(*pair)


def test_pointer_requires_an_exact_commit_and_a_relative_path():
    Pointer("alienintent", "docs/p.md", "a" * 40, b"x")
    for args in (("alienintent", "docs/p.md", "a" * 7, b"x"), ("alienintent", "/abs.md", "a" * 40, b"x"),
                 ("alienintent", "docs/../p.md", "a" * 40, b"x"), ("alienintent", "docs/p.md", "a" * 40, "text")):
        with pytest.raises(InvalidWorkItem):
            Pointer(*args)


def test_migration_plan_keys_names_once():
    entries = plan_migration({"active": ["PY-01"], "retired": ["PY-09"], "reserved": ["PY-10"]},
                             {"a": {"requirement:R": "PY-10"}, "b": {"requirement:Q": "PY-09"}})
    assert [(e.id, e.request_ref, e.retired) for e in entries] == [
        ("PY-01", "legacy:PY-01", False), ("PY-09", "requirement:Q", True), ("PY-10", "requirement:R", False)]
    for records in ({"a": {"requirement:R": "PY-10"}, "b": {"requirement:S": "PY-10"}},
                    {"a": {"requirement:R": "PY-10"}, "b": {"requirement:R": "PY-11"}},
                    {"a": {"label:R": "PY-10"}}, {"a": {"requirement:R": UUID}}):
        with pytest.raises(MigrationConflict):
            plan_migration({"active": []}, records)
    with pytest.raises(MigrationConflict):
        plan_migration({"active": ["not a name"]}, {})
