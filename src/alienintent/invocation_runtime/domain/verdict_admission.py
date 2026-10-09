"""Verdict admission: a VERIFIER session's REJECT changes lifecycle state only when every finding is reproduced. Pure.

The model discovers defects; the control plane proves they exist before the Work Item returns to PRODUCER. A reject
verdict's `findings` are objects `{"finding": "<text>", "evidence": <typed evidence>}`; the typed evidence is one of
a closed set:
- `{"type": "pytest", "node_ids": [...]}`: existing tests, reproduced when every id is present and at least one fails;
- `{"type": "reproducer", "name": "test_<x>.py", "source": "<python test file>"}`: a VERIFIER-written test, run in an
  untracked folder of a fresh candidate checkout, reproduced when it is collected and at least one of its tests fails;
- `{"type": "fitness", "check": "<name>"}`: the architecture fitness check at the candidate, reproduced when it fails;
- `{"type": "text", "path": "<repo path>", "contains" | "absent": "<exact text>"}`: a predicate on the candidate's
  file bytes, reproduced when it is true.
Reproduction itself runs outside this module; `admit` decides from its per-finding results. A reject is admitted only
when every finding has valid evidence and that evidence reproduced; otherwise it is invalid verification evidence.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from alienintent.invocation_runtime.domain.mutation_spec import node_ids, repository_path, utf8

FINDING_KEYS = frozenset({"finding", "evidence"})
_REPRODUCER_NAME = re.compile(r"test_[A-Za-z0-9_]+\.py")
_CHECK = re.compile(r"[a-z0-9][a-z0-9_-]*")
NOT_ADMITTED = "not-admitted"


@dataclass(frozen=True)
class PytestEvidence:
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReproducerEvidence:
    name: str
    source: str

    @property
    def digest(self) -> str:
        return "sha256:" + sha256(self.source.encode()).hexdigest()


@dataclass(frozen=True)
class FitnessEvidence:
    check: str


@dataclass(frozen=True)
class TextEvidence:
    path: str
    text: str
    present: bool  # `contains` when True, `absent` when False


Evidence = PytestEvidence | ReproducerEvidence | FitnessEvidence | TextEvidence


@dataclass(frozen=True)
class Claim:
    """One finding of a reject verdict: its text and its typed evidence, or the problem that left it without."""
    finding: str
    evidence: Evidence | None
    problem: str | None = None


@dataclass(frozen=True)
class Reproduction:
    """The control plane's result of reproducing one finding's evidence on a fresh checkout of the candidate."""
    reproduced: bool
    detail: str


@dataclass(frozen=True)
class Admission:
    admitted: bool
    findings: tuple[str, ...]


def claims(findings: Sequence[object]) -> tuple[Claim, ...]:
    """Each reject finding read as a Claim; a finding without valid typed evidence names its problem."""
    return tuple(_claim(entry) for entry in findings)


def _claim(entry: object) -> Claim:
    if isinstance(entry, str):
        return Claim(entry, None, "no typed evidence")
    if not isinstance(entry, dict) or set(entry) != FINDING_KEYS:
        return Claim(_text(entry), None, f"a finding needs exactly {', '.join(sorted(FINDING_KEYS))}")
    finding = entry["finding"]
    if not utf8(finding) or not finding:
        return Claim(_text(entry), None, "the finding text must be a non-empty string")
    try:
        return Claim(finding, evidence(entry["evidence"]))
    except ValueError as error:
        return Claim(finding, None, f"invalid evidence: {error}")


def evidence(value: object) -> Evidence:
    """One typed evidence value; ValueError names why it is not one."""
    kind = value.get("type") if isinstance(value, dict) else None
    keys = set(value) if isinstance(value, dict) else set()
    if kind == "pytest" and keys == {"type", "node_ids"}:
        ids = node_ids(value["node_ids"])
        if ids is None:
            raise ValueError("node_ids must be a non-empty list of distinct pytest node ids")
        return PytestEvidence(ids)
    if kind == "reproducer" and keys == {"type", "name", "source"}:
        if not isinstance(value["name"], str) or not _REPRODUCER_NAME.fullmatch(value["name"]):
            raise ValueError("a reproducer's name must be test_<name>.py")
        if not utf8(value["source"]) or not value["source"].strip():
            raise ValueError("a reproducer's source must be a non-empty python test file")
        return ReproducerEvidence(value["name"], value["source"])
    if kind == "fitness" and keys == {"type", "check"}:
        if not isinstance(value["check"], str) or not _CHECK.fullmatch(value["check"]):
            raise ValueError("a fitness check must be named")
        return FitnessEvidence(value["check"])
    if kind == "text" and len(keys) == 3 and {"type", "path"} < keys and keys - {"type", "path"} <= {"contains", "absent"}:
        [predicate] = keys - {"type", "path"}
        if not repository_path(value["path"]) or not utf8(value[predicate]) or not value[predicate]:
            raise ValueError("a text predicate needs a normalized path outside the evidence folder and non-empty text")
        return TextEvidence(value["path"], value[predicate], predicate == "contains")
    raise ValueError("the evidence must be one of pytest, reproducer, fitness or text, with exactly its keys")


def describe(item: Evidence) -> dict[str, object]:
    """The evidence as recorded with the finding (a reproducer with its source and its sha256)."""
    if isinstance(item, PytestEvidence):
        return {"type": "pytest", "node_ids": list(item.node_ids)}
    if isinstance(item, ReproducerEvidence):
        return {"type": "reproducer", "name": item.name, "sha256": item.digest, "source": item.source}
    if isinstance(item, FitnessEvidence):
        return {"type": "fitness", "check": item.check}
    return {"type": "text", "path": item.path, "contains" if item.present else "absent": item.text}


def admit(read: Sequence[Claim], reproductions: Sequence[Reproduction | None]) -> Admission:
    """Admitted only when every claim has evidence and its reproduction (same position) reproduced: then each finding
    with its evidence and result; otherwise each finding that was not admitted, with why."""
    refused = []
    for claim, reproduction in zip(read, reproductions, strict=True):
        if claim.evidence is None:
            refused.append(f"{NOT_ADMITTED}: {claim.finding}: {claim.problem}")
        elif reproduction is None or not reproduction.reproduced:
            why = "not reproduced" if reproduction is None else f"not reproduced: {reproduction.detail}"
            refused.append(f"{NOT_ADMITTED}: {claim.finding}: {why}")
    if refused or not read:
        return Admission(False, tuple(refused) or (f"{NOT_ADMITTED}: a reject needs at least one finding",))
    return Admission(True, tuple(
        f"{claim.finding} [evidence {json.dumps(describe(claim.evidence), sort_keys=True)}: {reproduction.detail}]"
        for claim, reproduction in zip(read, reproductions, strict=True)))


def receipt(candidate_sha: str, read: Sequence[Claim], reproductions: Sequence[Reproduction]) -> str:
    """`reject-reproduced:sha256:` over the canonical JSON of the candidate, each finding, its evidence and result."""
    document = {"candidate_sha": candidate_sha, "findings": [
        {"finding": claim.finding, "evidence": None if claim.evidence is None else describe(claim.evidence),
         "reproduced": reproduction.reproduced, "detail": reproduction.detail}
        for claim, reproduction in zip(read, reproductions, strict=True)]}
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return "reject-reproduced:sha256:" + sha256(encoded).hexdigest()


def _text(entry: object) -> str:
    return json.dumps(entry, sort_keys=True, default=str)[:200]
