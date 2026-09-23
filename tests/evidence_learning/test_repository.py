"""Exercise actual files: overwrite, corruption, isolation and fsync ordering."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os

import pytest

from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.evidence_learning.domain.records import record_ref
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible, StoreUnavailable
from tests.evidence_learning.support import definition


def repository(root):
    from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
    return LocalEvidenceRepository(root, "AlienLogicLab/alienintent", "fx-s1")


def test_concurrent_puts_never_overwrite_and_are_read_verified(tmp_path):
    repo = repository(tmp_path / "evidence")
    with ThreadPoolExecutor(max_workers=4) as pool:
        refs = list(pool.map(repo.put, [definition()] * 8))
    assert len(set(refs)) == 1
    assert repo.get(refs[0], frozenset({"private"})) == definition()
    assert len(list((tmp_path / "evidence" / "objects").iterdir())) == 1
    assert (tmp_path / "evidence").stat().st_mode & 0o077 == 0


def test_missing_corrupt_cross_profile_and_private_records_refuse(tmp_path):
    repo = repository(tmp_path)
    ref = repo.put(definition())
    with pytest.raises(EvidenceHold, match="ACCESS_DENIED"):
        repo.get(ref, frozenset({"public"}))
    with pytest.raises(EvidenceHold, match="REF_SCOPE"):
        repo.get(replace(ref, profile="other"), frozenset({"private"}))
    path = tmp_path / ref.locator
    path.write_text("{}")
    with pytest.raises(EvidenceHold, match="HASH_MISMATCH"):
        repo.get(ref, frozenset({"private"}))
    with pytest.raises(EvidenceHold, match="HASH_MISMATCH"):
        repo.put(definition())
    path.unlink()
    with pytest.raises(EvidenceHold, match="MISSING_OBJECT"):
        repo.get(ref, frozenset({"private"}))


def test_install_is_fsynced_before_readback_and_failure_is_typed(tmp_path, monkeypatch):
    repo = repository(tmp_path)
    calls = []
    real_sync, real_link = os.fsync, os.link
    def sync(fd):
        calls.append("sync")
        return real_sync(fd)
    def link(src, dst):
        calls.append("install")
        return real_link(src, dst)
    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "link", link)
    repo.put(definition())
    assert calls == ["sync", "install", "sync"]
    def fail(fd):
        raise OSError("disk unavailable")
    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(StoreUnavailable):
        repo.put(definition("2"))
    assert not (tmp_path / record_ref(definition("2")).locator).exists()


def test_symlink_object_and_size_limit_refused(tmp_path):
    repo = repository(tmp_path / "evidence")
    ref = record_ref(definition())
    outside = tmp_path / "outside"
    outside.write_text("private")
    (tmp_path / "evidence" / ref.locator).symlink_to(outside)
    with pytest.raises(EvidenceHold):
        repo.get(ref, frozenset({"private"}))
    from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
    tiny = LocalEvidenceRepository(tmp_path / "tiny", ref.project, ref.profile, max_bytes=10)
    with pytest.raises(EvidenceHold, match="INPUT_LIMIT_HOLD"):
        tiny.put(definition())
    assert outside.read_text() == "private"


def test_unknown_object_schema_and_wrong_logical_identity_refused(tmp_path):
    from hashlib import sha256
    from alienintent.evidence_learning.domain.records import canonical_bytes, record_document
    repo = repository(tmp_path)
    original = repo.put(definition())
    with pytest.raises(EvidenceHold, match="REF_IDENTITY"):
        repo.get(replace(original, logical_id="different"), frozenset({"private"}))
    doc = record_document(definition())
    doc["schema_version"] = 2
    body = canonical_bytes(doc)
    digest = sha256(body).hexdigest()
    ref = replace(original, revision_digest="sha256:" + digest, locator="objects/" + digest)
    (tmp_path / ref.locator).write_bytes(body)
    with pytest.raises(SchemaIncompatible):
        repo.get(ref, frozenset({"private"}))


def test_missing_parent_is_refused_without_creating_unsynced_ancestors(tmp_path):
    with pytest.raises(StoreUnavailable):
        repository(tmp_path / "new-a" / "new-b" / "evidence")
    assert not (tmp_path / "new-a").exists()
