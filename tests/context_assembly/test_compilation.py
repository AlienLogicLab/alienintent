"""The compiler identity grammar after the work identity service (acceptance check 5).

Existing names keep the candidate grammar; a service-issued UUID is admitted under any policy and never with a letter
suffix; the compiler still refuses an authority document without identity_policy or identity_snapshot.
"""
from copy import deepcopy
import re

import pytest

from alienintent.context_assembly.domain.compilation import IDENTITY_GRAMMAR, identity_valid
from alienintent.context_assembly.domain.initial_compilation import _limits
from alienintent.context_assembly.domain.compilation import CandidateInvalid
from tests.context_assembly.test_initial_compilation import LIMITS

UUID = "0b8f8d5e-6c1a-4f2e-8d3b-5a7c9e1f2a34"


@pytest.mark.parametrize("identity, valid", [
    ("PY-09", True), ("PY-09B", True), ("WO-000005", True), ("PG-01", True), (UUID, True),
    ("PY-SELF-00", False), (UUID + "B", False), (UUID.upper(), False), ("PY-9", False), ("WO-00005", False),
    (UUID[:-1], False), ("x" + UUID, False)])
def test_identity_grammar(identity, valid):
    assert (re.match(IDENTITY_GRAMMAR, identity) is not None) is valid


def test_uuid_ignores_family_and_width_but_names_do_not():
    assert identity_valid(UUID, {"family": "WO", "width": 6}) and identity_valid(UUID, {"family": "PY", "width": 2})
    assert identity_valid("PY-10", {"family": "PY", "width": 2})
    assert not identity_valid("PY-10", {"family": "WO", "width": 6})


@pytest.mark.parametrize("missing", ["identity_policy", "identity_snapshot"])
def test_authority_limits_still_require_identity_inputs(missing):
    limits = deepcopy(LIMITS)
    del limits[missing]
    with pytest.raises(CandidateInvalid, match=missing):
        _limits(limits)
    assert _limits(deepcopy(LIMITS))
