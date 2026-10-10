"""Proof set: the exact targeted test files of a Work Item, as Agent Ready assessed them in its packet. Pure.

A packet may hold one block fenced as ```json alienintent-proof, beside its contract and mutations blocks: an object
with exactly `targeted_tests`, a non-empty list of distinct normalized relative paths of Python files under `tests/` or
`tools/`. Baseline revalidation guards these files (WORK-PREPARATION-REFILL R2, Founder decisions section 43): the
proof set is declared, never inferred from mutations or scope.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from alienintent.execution_coordination.domain.plan_authority import normalized, under

OPEN, CLOSE = "```json alienintent-proof", "```"
PROOF_KEYS = frozenset({"targeted_tests"})
PROOF_ROOTS = ("tests", "tools")


class ProofSetInvalid(ValueError):
    """The packet holds more than one, or a malformed, proof block."""


@dataclass(frozen=True)
class ProofSet:
    targeted_tests: tuple[str, ...]


def parse_proof(text: str) -> ProofSet | None:
    """The packet's one proof block; None when it has none, ProofSetInvalid for more than one or a malformed one."""
    lines = text.split("\n")
    opens = [index for index, line in enumerate(lines) if line == OPEN]
    if not opens:
        return None
    if len(opens) > 1:
        raise ProofSetInvalid("more than one proof block")
    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
    if close is None:
        raise ProofSetInvalid("the proof block is not closed")
    try:
        document = json.loads("\n".join(lines[opens[0] + 1:close]))
    except ValueError as error:
        raise ProofSetInvalid(f"the proof block is not JSON: {error}") from None
    if not isinstance(document, dict) or set(document) != PROOF_KEYS:
        raise ProofSetInvalid("the proof block needs exactly targeted_tests")
    tests = document["targeted_tests"]
    if not isinstance(tests, list) or not tests or len(set(map(str, tests))) != len(tests) or not all(
            isinstance(path, str) and normalized(path) == path and path.endswith(".py")
            and any(under(path, root) for root in PROOF_ROOTS) for path in tests):
        raise ProofSetInvalid("targeted_tests must be distinct normalized paths of Python files under tests/ or "
                              "tools/")
    return ProofSet(tuple(tests))
