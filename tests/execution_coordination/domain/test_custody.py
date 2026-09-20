from __future__ import annotations

import pytest

from alienintent.execution_coordination.domain.custody import CandidateRef, CandidateValidationError


@pytest.mark.parametrize("factory", (CandidateRef.local_artifact, CandidateRef.source_revision, CandidateRef.archive))
def test_candidate_variants_are_digest_bound_and_provider_neutral(factory: object) -> None:
    candidate = factory("sha256:" + "a" * 64, "store://candidate")  # type: ignore[operator]

    assert candidate.content_digest == "sha256:" + "a" * 64
    assert candidate.content_digest in candidate.identity


def test_candidate_refuses_identity_that_does_not_resolve_to_its_digest() -> None:
    with pytest.raises(CandidateValidationError, match="digest"):
        CandidateRef.local_artifact("sha256:" + "a" * 64, "store://candidate", identity="artifact:old")


def test_verify_requires_independent_read_back() -> None:
    candidate = CandidateRef.archive("sha256:" + "a" * 64, "store://candidate")

    assert not candidate.verify_admissible
    assert candidate.with_independent_read_back().verify_admissible


def test_changed_content_digest_creates_a_different_candidate_identity() -> None:
    first = CandidateRef.local_artifact("sha256:" + "a" * 64, "store://candidate")
    changed = CandidateRef.local_artifact("sha256:" + "b" * 64, "store://candidate")

    assert first.identity != changed.identity
