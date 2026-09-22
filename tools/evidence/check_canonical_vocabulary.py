#!/usr/bin/env python3
"""Canonical-vocabulary boundary checker (Founder decisions v0.1, canonicalized 2026-09-22).

Five invariants, each mechanically decidable over the *active* canonical artifacts:

1. **agent_ready_dispositions_exact** — Agent Ready has exactly READY, CLARIFY, SPLIT, HOLD.
   The AlienIntent bootstrap assessor's `BLOCKED / NEEDS_CLARIFICATION / SPLIT_RECOMMENDED`
   may appear only where explicitly marked historical / bootstrap-assessor / legacy. `BLOCKED`
   alone is a legitimate AlienIntent lifecycle or verdict state; what is contaminated is the
   *disposition-set shape* — READY co-occurring with the legacy names on one line.
2. **no_agent_ready_internals_ownership** — no AlienIntent text claims to own Agent Ready's
   engine, CLI, MCP server, schema or readiness rubric.
3. **gap_trap_not_ul** — `Gap Trap` is not defined as an AlienIntent Ubiquitous Language term.
   Attribution prose is allowed; a definition heading is not.
4. **sf_req_039_identity** — the requirement keeps its identifier through its rename.
5. **ports_are_vendor_neutral** — no core port definition names a specific vendor as required.

Historical evidence is out of scope by construction: `docs/evidence/wave1-*`, `docs/work-units`,
the post-Wave-1 programme's operating plan, prompts and reports, and the Founder decision
document itself (which quotes the old vocabulary in order to correct it).

Usage: python3 tools/evidence/check_canonical_vocabulary.py [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CHECKS = ("agent_ready_dispositions_exact", "no_agent_ready_internals_ownership",
          "gap_trap_not_ul", "sf_req_039_identity", "ports_are_vendor_neutral")

# Active canonical authority and current design artifacts. Deliberately explicit rather than a
# glob: adding a path here is a decision that the artifact is normative today.
ACTIVE_ARTIFACTS = (
    "docs/architecture/alienintent-architecture-authority-2026-09-19.md",
    "docs/architecture/alienintent-ubiquitous-language-v0.1.md",
    "docs/architecture/canonical-architecture.md",
    "docs/architecture/pre-python-gate/hexagonal-contracts.md",
    "docs/architecture/pre-python-gate/domain-model.md",
    "docs/decisions/alienintent-software-factory-plan.md",
    "docs/decisions/2026-09-19-alienintent-work-management-execution-authority.md",
    "docs/decisions/2026-09-20-deterministic-failure-class-promotion.md",
    "docs/decisions/2026-09-20-design-contract-and-design-verification.md",
    "docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md",
    "docs/decisions/2026-09-20-liveness-reconciliation.md",
    "docs/decisions/2026-09-21-py10-transport-split.md",
    "docs/evidence/wave2-specified-requirements.json",
    "docs/evidence/wave2-design-contracts.json",
    "docs/operations.md",
    "tools/evidence/check_agent_ready_set.py",
)

_LEGACY = ("NEEDS_CLARIFICATION", "SPLIT_RECOMMENDED")
_HISTORICAL_MARKERS = ("historical", "bootstrap assessor", "bootstrap-assessor", "legacy",
                       "was the", "were the", "formerly", "wave 1 evidence", "retained verbatim")
_INTERNALS = ("assessment engine", "readiness engine", "mcp server", "agent ready cli",
              "agent-ready cli", "assessment schema", "readiness rubric", "readiness prompt")
_OWNERSHIP_VERBS = ("owns", "own the", "implements", "maintains", "canonical owner of")
_VENDORS = ("github", "jira", "linear", "gitlab", "azure devops", "factorychecks")
# The contaminated shape for BLOCKED is an *enumeration* with READY: the two names joined only by
# list punctuation and other identifiers ("READY, BLOCKED, …", "READY/BLOCKED/…"). A sentence
# that merely mentions both — including one denying that BLOCKED is a disposition — is not it.
_BLOCKED_ENUM = re.compile(
    r"\bREADY\b`?(?:\s*[,/|]\s*`?[A-Z_]+`?)*\s*[,/|]\s*`?BLOCKED\b|"
    r"\bBLOCKED\b`?(?:\s*[,/|]\s*`?[A-Z_]+`?)*\s*[,/|]\s*`?READY\b")
_PORT_ROW = re.compile(r"^\|\s*(RequirementSource|WorkManagement|ReadinessAssessment|"
                       r"AssessmentFeedback|WorkerProvider|SourceControl)\w*\s*\|", re.I)


def _lines(text: str):
    """Yield text lines; JSON files are yielded as their string values so a rule sees the
    same shape the reader sees."""
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            obj = json.loads(text)
        except Exception:
            yield from text.splitlines()
            return
        stack = [obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, str):
                yield cur
        return
    yield from text.splitlines()


_NOTE_WINDOW = 15  # a terminology note counts only if it opens the document


def _historical_record(path: str, text: str) -> bool:
    """A Markdown *record* (a decision or evidence document) may declare, in a terminology note
    near its top, that the vocabulary it quotes is historical. That exempts the record's quoted
    lines without rewriting history. A JSON design artifact never gets this exemption: design
    is normative, and a note elsewhere in it does not launder a legacy line."""
    if not path.endswith(".md"):
        return False
    head = "\n".join(text.splitlines()[:_NOTE_WINDOW]).lower()
    return "terminology note" in head and "historical" in head and \
        ("bootstrap-assessor" in head or "bootstrap assessor" in head)


def check_texts(texts: dict[str, str]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    plan_text = texts.get("docs/decisions/alienintent-software-factory-plan.md", "")

    for path, text in texts.items():
        record_exempt = _historical_record(path, text)
        for line in _lines(text):
            low = line.lower()
            historical = record_exempt or any(m in low for m in _HISTORICAL_MARKERS)

            legacy_hit = any(name in line for name in _LEGACY) or bool(_BLOCKED_ENUM.search(line))
            if legacy_hit and not historical:
                failures.append(
                    f"agent_ready_dispositions_exact: {path}: presents bootstrap-assessor "
                    f"vocabulary as a disposition set — {line.strip()[:120]!r}. Agent Ready has "
                    "exactly READY, CLARIFY, SPLIT, HOLD; mark legacy text historical")

            if any(i in low for i in _INTERNALS) and any(v in low for v in _OWNERSHIP_VERBS) \
                    and "alienintent" in low and "agent ready" in low.replace("-", " "):
                failures.append(
                    f"no_agent_ready_internals_ownership: {path}: claims AlienIntent ownership "
                    f"of Agent Ready internals — {line.strip()[:120]!r}")

            if re.match(r"^\s*#{1,6}\s*Gap Trap\s*$", line, re.I) or \
                    re.match(r"^\s*\*\*Gap Trap\*\*\s*[—:-]", line, re.I):
                failures.append(
                    f"gap_trap_not_ul: {path}: defines 'Gap Trap' as a term — {line.strip()!r}. "
                    "It is the name of an external project; the product-native term is "
                    "deterministic failure-class promotion")

            if _PORT_ROW.match(line) and any(v in low for v in _VENDORS) and "required" in low:
                failures.append(
                    f"ports_are_vendor_neutral: {path}: a core port names a vendor as required "
                    f"— {line.strip()[:120]!r}")

    if plan_text and not re.search(r"^##\s*SF-REQ-039\s*—", plan_text, re.M):
        failures.append(
            "sf_req_039_identity: the factory plan no longer defines SF-REQ-039 under its own "
            "identifier; renaming must preserve identity and provenance")

    return (not failures), failures


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root)
    texts = {p: (root / p).read_text() for p in ACTIVE_ARTIFACTS if (root / p).exists()}
    missing = [p for p in ACTIVE_ARTIFACTS if not (root / p).exists()]
    ok, failures = check_texts(texts)
    print(f"artifacts : {len(texts)} active ({len(missing)} listed but absent)")
    for m in missing:
        print(f"  absent  : {m}")
    print(f"checks    : {', '.join(CHECKS)}")
    print(f"result    : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
