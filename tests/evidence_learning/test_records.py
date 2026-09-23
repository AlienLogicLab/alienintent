"""Catch role confusion, lossy measurement encoding and mutable reference values."""
from dataclasses import FrozenInstanceError, replace
import importlib.util
import math

import pytest


def test_typed_evidence_capability_exists():
    assert importlib.util.find_spec("alienintent.evidence_learning.domain.records") is not None


def test_scalar_types_and_null_survive_canonical_roundtrip():
    from alienintent.evidence_learning.domain.records import record_from_document, record_document
    from tests.evidence_learning.support import observation
    for value in [None, 0, 0.0, False, True, "0", 1.25]:
        item = observation(value=value, uncertainty="not measured" if value is None else None)
        restored = record_from_document(record_document(item))
        assert type(restored.value) is type(value)
        assert restored.value == value
        assert restored.uncertainty == item.uncertainty


def test_invalid_numbers_null_without_reason_and_role_changes_refused():
    from alienintent.evidence_learning.domain.records import record_from_document, record_document
    from alienintent.evidence_learning.domain.refs import EvidenceHold
    from tests.evidence_learning.support import observation
    for value in [math.inf, -math.inf, math.nan, [], {}]:
        with pytest.raises(EvidenceHold):
            record_document(observation(value=value))
    with pytest.raises(EvidenceHold):
        record_document(observation(value=None, uncertainty=None))
    doc = record_document(observation())
    doc["kind"] = "Definition"
    with pytest.raises(EvidenceHold):
        record_from_document(doc)


def test_refs_are_frozen_and_digest_locator_is_not_a_path():
    from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
    from tests.evidence_learning.support import external_ref
    ref = external_ref("source")
    with pytest.raises(FrozenInstanceError):
        ref.logical_id = "other"
    for digest in ["../escape", "sha256:" + "g" * 64, "sha256:" + "0" * 63]:
        with pytest.raises(EvidenceHold):
            Ref(ref.project, ref.profile, ref.logical_id, digest, ref.locator)
    assert replace(ref, locator="../untrusted") != ref


def test_caller_mutation_cannot_change_frozen_record_or_authority_snapshot():
    from alienintent.evidence_learning.domain.records import record_ref
    from tests.evidence_learning.support import authority, definition, external_ref
    sources = [external_ref("source")]
    original = definition()
    record = replace(original, header=replace(original.header, source_refs=sources), required_ids={"tests"})
    before = record_ref(record)
    sources.append(external_ref("injected"))
    assert record_ref(record) == before
    assert isinstance(record.header.source_refs, tuple)
    assert isinstance(record.required_ids, frozenset)
    grants = list(authority().definitions)
    snapshot = replace(authority(), definitions=grants)
    grants.clear()
    assert len(snapshot.definitions) == 2
