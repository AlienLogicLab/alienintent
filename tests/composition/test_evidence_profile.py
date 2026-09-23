"""Public composition refuses invalid schema, storage and stale CAS inputs."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.evidence_learning.domain.records import record_ref
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible, StoreUnavailable
from tests.evidence_learning.support import definition, observation, profile, seeded


def test_reopen_idempotence_stale_cas_and_identity_conflict(tmp_path):
    p, dref, oref = seeded(tmp_path)
    reopened = profile(tmp_path)
    assert reopened.service.read().refs == (dref, oref)
    assert reopened.service.admit(observation(), 2).version == 2
    with pytest.raises(EvidenceHold, match="VERSION_CONFLICT"):
        reopened.service.admit(observation(), 1)
    with pytest.raises(EvidenceHold, match="IDENTITY_CONFLICT"):
        reopened.service.admit(observation(value=False), 2)
    assert reopened.service.read().version == 2


def test_incompatible_pointer_and_unavailable_store_prevent_object_install(tmp_path):
    p = profile(tmp_path)
    p.store.commit(p.name, p.service.aggregate, 0, {"schema_version": 2})
    with pytest.raises(SchemaIncompatible):
        p.service.admit(definition(), 1)
    assert list((tmp_path / "evidence/objects").iterdir()) == []
    (tmp_path / "state.sqlite").unlink()
    with pytest.raises(StoreUnavailable):
        p.service.admit(definition(), 0)


@pytest.mark.parametrize("side,expected_version", [("before", 0), ("after", 1)])
def test_process_death_on_each_side_of_real_cas_is_read_verified(tmp_path, side, expected_version):
    # Kill the child at the actual storage boundary, not an adapter simulation.
    script = '''
import os, sys
from pathlib import Path
from tests.evidence_learning.support import profile, definition
p = profile(Path(sys.argv[1]))
commit = p.store.commit
def crash(*args, **kwargs):
    if sys.argv[2] == "before": os._exit(73)
    result = commit(*args, **kwargs)
    os._exit(74)
p.store.commit = crash
p.service.admit(definition(), 0)
'''
    env = {**os.environ, "PYTHONPATH": str(Path("src").resolve()) + os.pathsep + str(Path.cwd())}
    child = subprocess.run([sys.executable, "-c", script, str(tmp_path), side], env=env, capture_output=True, text=True)
    assert child.returncode == (73 if side == "before" else 74), child.stderr
    p = profile(tmp_path)
    state = p.service.read()
    assert state.version == expected_version
    ref = record_ref(definition())
    assert p.repository.get(ref, p.access_scope) == definition()
    assert state.refs == ((ref,) if side == "after" else ())


def test_object_failure_prevents_cas_and_cas_race_retains_orphan(tmp_path, monkeypatch):
    p = profile(tmp_path)
    original = p.store.commit
    def race(*args):
        original(p.name, p.service.aggregate, 0, {"schema_version": 1, "refs": [], "held_definitions": []})
        return original(*args)
    monkeypatch.setattr(p.store, "commit", race)
    with pytest.raises(EvidenceHold, match="VERSION_CONFLICT"):
        p.service.admit(definition(), 0)
    assert p.service.read().refs == ()
    assert p.repository.get(record_ref(definition()), p.access_scope) == definition()
    monkeypatch.setattr(p.store, "commit", original)
    def fail(record):
        raise StoreUnavailable("disk")
    monkeypatch.setattr(p.repository, "put", fail)
    with pytest.raises(StoreUnavailable):
        p.service.admit(definition(), 1)
    assert p.service.read().version == 1


def test_profile_root_escape_is_refused(tmp_path):
    from alienintent.composition.evidence_profile import EvidenceProfile
    from tests.evidence_learning.support import authority
    with pytest.raises(EvidenceHold, match="UNSAFE_ROOT"):
        EvidenceProfile(tmp_path.parent / "escape", permitted_root=tmp_path, project="p", name="fx-s1", authority=authority(), database=tmp_path / "state.sqlite")


def test_offline_profile_receives_same_evidence_store_without_lifecycle_wiring(tmp_path):
    from alienintent.composition.offline_profile import OfflineProfile
    from tests.evidence_learning.support import authority
    # No coordinator method is invoked; construction accepts the existing ports.
    offline = OfflineProfile(tmp_path / "state.sqlite", None, None, tmp_path / "artifacts", name="fx-s1",
                             evidence_root=tmp_path / "evidence", evidence_permitted_root=tmp_path,
                             evidence_project="AlienLogicLab/alienintent", evidence_authority=authority())
    assert offline.evidence.store is offline.store
    offline.evidence.service.admit(definition(), 0)
    assert profile(tmp_path).service.read().version == 1


def test_definition_upgrade_retains_history_and_identical_old_put_is_noop(tmp_path):
    p, dref, oref = seeded(tmp_path)
    second = replace(definition("2"), header=replace(definition("2").header, preceding_refs=(dref,)))
    second_ref = p.service.admit(second, 2).ref
    assert p.service.admit(definition(), 3).version == 3
    assert p.service.read().refs == (dref, oref, second_ref)
    assert p.service.read().current_definitions()["requirement/tests"] == second_ref
