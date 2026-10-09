"""VERIFICATION-OUTCOME-INTEGRITY: a session REJECT is admitted only when every finding's typed evidence reproduces.

The rule is pure: it reads the findings and decides from per-finding reproduction results. Texts are TEST DATA.
"""
from __future__ import annotations

import pytest

from alienintent.invocation_runtime.domain.verdict_admission import (
    PytestEvidence, Reproduction, ReproducerEvidence, admit, claims)

PYTEST = {"finding": "the refusal is missing", "evidence": {"type": "pytest", "node_ids": ["tests/t.py::test_a"]}}
TEXT = {"finding": "the old name remains", "evidence": {"type": "text", "path": "src/a.py", "contains": "old_name"}}
REPRODUCER = {"finding": "an empty list is accepted", "evidence": {
    "type": "reproducer", "name": "test_empty.py", "source": "def test_empty():\n    assert False\n"}}
FITNESS = {"finding": "a layer is crossed", "evidence": {"type": "fitness", "check": "layers"}}


def test_each_typed_evidence_is_read():
    read = claims([PYTEST, TEXT, REPRODUCER, FITNESS])
    assert [claim.problem for claim in read] == [None] * 4
    assert read[0].evidence == PytestEvidence(("tests/t.py::test_a",))
    assert isinstance(read[2].evidence, ReproducerEvidence) and read[2].evidence.digest.startswith("sha256:")


@pytest.mark.parametrize("finding", [
    "a plain text finding",
    {"finding": "no evidence"},
    {"finding": "unknown type", "evidence": {"type": "opinion"}},
    {"finding": "no ids", "evidence": {"type": "pytest", "node_ids": []}},
    {"finding": "bad name", "evidence": {"type": "reproducer", "name": "../x.py", "source": "x"}},
    {"finding": "both", "evidence": {"type": "text", "path": "a.py", "contains": "x", "absent": "y"}},
    {"finding": "", "evidence": PYTEST["evidence"]},
    {"finding": "not UTF-8", "evidence": {"type": "reproducer", "name": "test_x.py", "source": "x = '\ud800'\n"}},
    {"finding": "not UTF-8", "evidence": {"type": "text", "path": "src/a.py", "contains": "\ud800"}},
    {"finding": "in the evidence folder", "evidence": {"type": "pytest", "node_ids": ["alienintent-evidence/test_x.py"]}},
    {"finding": "in the evidence folder", "evidence": {"type": "text", "path": "alienintent-evidence/test_x.py",
                                                       "contains": "x"}},
])
def test_a_finding_without_valid_typed_evidence_is_not_admitted(finding):
    read = claims([PYTEST, finding])
    assert read[1].evidence is None and read[1].problem
    admission = admit(read, [Reproduction(True, "1 failed"), None])
    assert not admission.admitted
    assert len(admission.findings) == 1 and admission.findings[0].startswith("not-admitted:")


def test_a_reject_is_admitted_only_when_every_finding_reproduces():
    read = claims([PYTEST, TEXT])
    admitted = admit(read, [Reproduction(True, "test_a failed"), Reproduction(True, "the text is present")])
    assert admitted.admitted and len(admitted.findings) == 2
    assert admitted.findings[0].startswith("the refusal is missing") and "test_a failed" in admitted.findings[0]
    refused = admit(read, [Reproduction(True, "test_a failed"), Reproduction(False, "the text is not present")])
    assert not refused.admitted
    assert refused.findings == ("not-admitted: the old name remains: not reproduced: the text is not present",)


def test_the_reproducer_source_reaches_the_producer():
    [claim] = claims([REPRODUCER])
    [finding] = admit([claim], [Reproduction(True, "test_empty failed")]).findings
    assert "def test_empty():" in finding and claim.evidence.digest in finding
