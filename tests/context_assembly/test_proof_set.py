"""The packet's targeted proof set (WORK-PREPARATION-REFILL R2, Founder decisions section 43): the exact test files
Agent Ready assessed, read from one ```json alienintent-proof block. Packets are TEST DATA."""
from __future__ import annotations

import json

import pytest

from alienintent.context_assembly.domain.proof_set import ProofSet, ProofSetInvalid, parse_proof


def packet(*blocks: object) -> str:
    body = "".join(f"\n```json alienintent-proof\n{json.dumps(block)}\n```\n" for block in blocks)
    return f"# Work unit\n\n```json alienintent-contract\n{{}}\n```\n{body}"


def test_a_packet_without_a_proof_block_declares_no_proof_set():
    assert parse_proof(packet()) is None


def test_the_proof_block_names_the_exact_targeted_test_files():
    proof = parse_proof(packet({"targeted_tests": ["tests/a/test_one.py", "tools/test_two.py"]}))
    assert proof == ProofSet(("tests/a/test_one.py", "tools/test_two.py"))


@pytest.mark.parametrize("block", [
    pytest.param([], id="not-an-object"),
    pytest.param({}, id="no-targeted-tests"),
    pytest.param({"targeted_tests": [], "extra": 1}, id="extra-key"),
    pytest.param({"targeted_tests": []}, id="empty"),
    pytest.param({"targeted_tests": ["tests/a.py", "tests/a.py"]}, id="repeated"),
    pytest.param({"targeted_tests": ["tests/../src/a.py"]}, id="not-normalized"),
    pytest.param({"targeted_tests": ["/tests/a.py"]}, id="absolute"),
    pytest.param({"targeted_tests": ["src/a.py"]}, id="outside-tests-and-tools"),
    pytest.param({"targeted_tests": ["tests/data.json"]}, id="not-a-python-file"),
    pytest.param({"targeted_tests": [3]}, id="not-a-string"),
])
def test_a_malformed_proof_block_is_refused(block):
    with pytest.raises(ProofSetInvalid):
        parse_proof(packet(block))


def test_two_proof_blocks_or_an_unclosed_one_are_refused():
    with pytest.raises(ProofSetInvalid):
        parse_proof(packet({"targeted_tests": ["tests/a.py"]}, {"targeted_tests": ["tests/b.py"]}))
    with pytest.raises(ProofSetInvalid):
        parse_proof("```json alienintent-proof\n{\"targeted_tests\": [\"tests/a.py\"]}\n")
    with pytest.raises(ProofSetInvalid):
        parse_proof("```json alienintent-proof\nnot json\n```\n")
