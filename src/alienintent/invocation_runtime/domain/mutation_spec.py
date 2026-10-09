"""Mutation spec: the packet's own mutations, which the control plane runs against a candidate before VERIFY. Pure.

A packet may hold one block fenced as ```json alienintent-mutations, separate from its contract block (contract fields
feed the contract's content digest; the spec does not). The block is a JSON list of mutations, each with exactly
`name` (distinct), `path` (one normalized relative path, as `plan_authority.normalized` reads it), `edits` (a
non-empty list of `{"old", "new"}`, `old` non-empty, applied together and in order) and `tests` (a non-empty list of
distinct pytest node ids that must fail with the edits and pass without them). `MutationSpec.digest` is `sha256:` of
the spec's canonical JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from alienintent.execution_coordination.domain.scope_containment import normalized, under

OPEN, CLOSE = "```json alienintent-mutations", "```"
MUTATION_KEYS = frozenset({"name", "path", "edits", "tests"})
EDIT_KEYS = frozenset({"old", "new"})
# The untracked folder of a fresh candidate checkout where the control plane writes a reproducer; no mutation, named
# test or text predicate may point into it, so no evidence reads what another evidence item wrote.
EVIDENCE_FOLDER = "alienintent-evidence"
# A pytest node id names a test file under the checkout; it is never an option. The path and the test name hold no
# whitespace; a parametrize id in brackets is pytest's own text and may hold spaces, never a line break.
_NODE_ID = re.compile(r"[A-Za-z0-9_][^\s\x00]*\.py(::[^\s\x00\[]+(\[[^\x00\n\r]*\])?)?")


class MutationSpecInvalid(ValueError):
    """The packet holds more than one, or a malformed, mutations block."""


@dataclass(frozen=True)
class Edit:
    old: str
    new: str


@dataclass(frozen=True)
class Mutation:
    name: str
    path: str
    edits: tuple[Edit, ...]
    tests: tuple[str, ...]


@dataclass(frozen=True)
class MutationSpec:
    mutations: tuple[Mutation, ...]

    def document(self) -> list[dict[str, object]]:
        """The block's JSON value, as `parse_mutations` reads it back."""
        return [{"name": m.name, "path": m.path, "edits": [{"old": e.old, "new": e.new} for e in m.edits],
                 "tests": list(m.tests)} for m in self.mutations]

    @property
    def digest(self) -> str:
        encoded = json.dumps(self.document(), sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + sha256(encoded).hexdigest()


def utf8(text: object) -> bool:
    """A string that encodes as UTF-8 (JSON can carry a lone surrogate, which does not)."""
    if not isinstance(text, str):
        return False
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def repository_path(path: object) -> bool:
    """A normalized relative path of the candidate, outside EVIDENCE_FOLDER."""
    return utf8(path) and normalized(path) == path and not under(str(path), EVIDENCE_FOLDER)


def node_ids(value: object) -> tuple[str, ...] | None:
    """A non-empty list of distinct pytest node ids, each naming a file under the checkout (never an option), or
    None."""
    if not isinstance(value, list) or not value or not all(
            utf8(entry) and _NODE_ID.fullmatch(entry) and repository_path(entry.split("::")[0])
            for entry in value) or len(set(value)) != len(value):
        return None
    return tuple(value)


def parse_mutations(text: str) -> MutationSpec | None:
    """The packet's one mutations block; None when it has none, MutationSpecInvalid for more than one or a malformed
    one."""
    lines = text.split("\n")
    opens = [index for index, line in enumerate(lines) if line == OPEN]
    if not opens:
        return None
    if len(opens) > 1:
        raise MutationSpecInvalid("more than one mutations block")
    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
    if close is None:
        raise MutationSpecInvalid("the mutations block is not closed")
    try:
        document = json.loads("\n".join(lines[opens[0] + 1:close]))
    except ValueError as error:
        raise MutationSpecInvalid(f"the mutations block is not JSON: {error}") from None
    return spec_from(document)


def spec_from(document: object) -> MutationSpec:
    """A MutationSpec from the block's JSON value."""
    if not isinstance(document, list) or not document:
        raise MutationSpecInvalid("the mutations block must be a non-empty list")
    mutations = tuple(_mutation(entry) for entry in document)
    if len({mutation.name for mutation in mutations}) != len(mutations):
        raise MutationSpecInvalid("mutation names must be distinct")
    return MutationSpec(mutations)


def _mutation(entry: object) -> Mutation:
    if not isinstance(entry, dict) or set(entry) != MUTATION_KEYS:
        raise MutationSpecInvalid(f"each mutation needs exactly {', '.join(sorted(MUTATION_KEYS))}")
    name, path, edits, tests = entry["name"], entry["path"], entry["edits"], entry["tests"]
    if not utf8(name) or not name:
        raise MutationSpecInvalid("a mutation's name must be a non-empty string")
    if not repository_path(path):
        raise MutationSpecInvalid(f"{name}: path must be a normalized relative path outside {EVIDENCE_FOLDER}")
    if not isinstance(edits, list) or not edits or not all(
            isinstance(edit, dict) and set(edit) == EDIT_KEYS and utf8(edit["old"]) and edit["old"]
            and utf8(edit["new"]) for edit in edits):
        raise MutationSpecInvalid(f"{name}: edits must be a non-empty list of UTF-8 {{old, new}}, old non-empty")
    if node_ids(tests) is None:
        raise MutationSpecInvalid(f"{name}: tests must be a non-empty list of distinct pytest node ids")
    return Mutation(name, path, tuple(Edit(edit["old"], edit["new"]) for edit in edits), tuple(tests))
