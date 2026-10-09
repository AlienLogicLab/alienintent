"""VERIFICATION-OUTCOME-INTEGRITY: the packet's own mutation spec, read by a pure parser. Names are TEST DATA."""
from __future__ import annotations

import json

import pytest

from alienintent.invocation_runtime.domain.mutation_spec import MutationSpecInvalid, parse_mutations


def packet(*blocks: object) -> str:
    fenced = "".join(f"```json alienintent-mutations\n{json.dumps(block)}\n```\n\n" for block in blocks)
    return f"# Packet\n\nSome prose.\n\n{fenced}The end.\n"


MUTATION = {"name": "drop-check", "path": "src/pkg/rule.py", "edits": [{"old": "if ok:", "new": "if True:"}],
            "tests": ["tests/test_rule.py::test_refuses"]}


def test_a_packet_without_a_block_has_no_spec_and_a_valid_block_is_read_exactly():
    assert parse_mutations(packet()) is None
    spec = parse_mutations(packet([MUTATION]))
    [mutation] = spec.mutations
    assert (mutation.name, mutation.path, mutation.tests) == ("drop-check", "src/pkg/rule.py",
                                                               ("tests/test_rule.py::test_refuses",))
    assert [(edit.old, edit.new) for edit in mutation.edits] == [("if ok:", "if True:")]
    assert spec.digest.startswith("sha256:") and spec.digest == parse_mutations(packet([MUTATION])).digest
    assert spec.digest != parse_mutations(packet([MUTATION | {"name": "other"}])).digest


def test_a_parametrize_id_may_hold_spaces_but_the_path_and_name_may_not():
    """Real pytest ids carry their parameters verbatim (`[gate regression]`, `[def f():\\n    x-stands0]`)."""
    ids = ["tests/test_rule.py::test_refuses[gate regression]", "tests/test_rule.py::test_x[def f():\\n    x-stands0]"]
    spec = parse_mutations(packet([MUTATION | {"tests": ids}]))
    assert spec.mutations[0].tests == tuple(ids)
    for bad in ("tests/test rule.py::test_refuses", "tests/test_rule.py::test refuses", "tests/test_rule.py::t[a\nb]"):
        with pytest.raises(MutationSpecInvalid):
            parse_mutations(packet([MUTATION | {"tests": [bad]}]))


@pytest.mark.parametrize("text", [
    packet([MUTATION], [MUTATION]),                                    # more than one block
    "```json alienintent-mutations\n[\n",                               # not closed
    "```json alienintent-mutations\nnot json\n```\n",                  # not JSON
    packet([]),                                                         # no mutation
    packet([MUTATION, MUTATION]),                                       # names not distinct
    packet([MUTATION | {"edits": [{"old": "", "new": "x"}]}]),          # empty old
    packet([MUTATION | {"edits": []}]),                                 # no edit
    packet([MUTATION | {"tests": []}]),                                 # no test
    packet([MUTATION | {"tests": ["--collect-only"]}]),                 # an option, not a node id
    packet([MUTATION | {"path": "../outside.py"}]),                     # path not normalized
    packet([MUTATION | {"path": "alienintent-evidence/test_x.py"}]),  # the evidence folder
    packet([MUTATION | {"edits": [{"old": "if ok:", "new": "\ud800"}]}]),  # not encodable as UTF-8
    packet([MUTATION | {"extra": 1}]),                                  # unknown key
])
def test_a_malformed_spec_is_invalid(text):
    with pytest.raises(MutationSpecInvalid):
        parse_mutations(text)
