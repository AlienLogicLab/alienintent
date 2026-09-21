#!/usr/bin/env python3
"""Contract checker for the canonical BIU split/replan design (Phase 5).

The strong invariant:

    Splitting may change decomposition, but it must conserve authorized intent and
    proof obligations.

Conservation is the mechanically checkable half. Every original requirement, acceptance
criterion, verification obligation and evidence obligation must map to a destination —
child A, child B, or a retained integration parent. "Nothing silently disappears" is the kind
of claim a checker can enforce and prose cannot.

Identity allocation is checked against reality rather than taste: Wave 1 made exactly one split
allocation, `PY-09B`, and a proposed identifier grammar that cannot express it is wrong about
the system it governs. The repository contains no BIU-identifier regex at all, so the grammar
this design states is the first one to exist.

Usage: python3 tools/evidence/check_split_design.py [design.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("authority", "lineage", "requirement_conservation", "scope_conservation",
                     "dependency_rewriting", "identity_allocation", "lifecycle_semantics",
                     "agent_ready_invalidation", "project_projection", "evidence", "closure")

VALID_DESTINATIONS = ("child_a", "child_b", "retained_integration_parent")
OBLIGATION_KINDS = ("requirement", "acceptance_criterion", "verification_obligation",
                    "evidence_obligation")

# The only split identifier Wave 1 actually allocated.
_REAL_SPLIT_IDENTIFIER = "PY-09B"

CHECKS = ("required_sections", "conservation", "valid_destinations", "all_obligation_kinds",
          "identity_grammar", "strong_invariant", "original_lifecycle")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined")


def _absent(value) -> bool:
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_design(design: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    sections = design.get("sections", {})
    for s in REQUIRED_SECTIONS:
        if s not in sections or _absent(sections.get(s)):
            failures.append(f"required_sections: {s} is not defined")

    mapping = design.get("conservation_mapping", [])
    for o in mapping:
        oid = o.get("obligation_id", "<no id>")
        dests = o.get("maps_to") or []
        live = [d for d in dests if not _absent(d)]
        if not live:
            failures.append(
                f"conservation: {oid} maps to nothing. Splitting may redistribute authorized "
                "work; it may not drop it")
        for d in live:
            if d not in VALID_DESTINATIONS:
                failures.append(
                    f"valid_destinations: {oid} maps to {d!r}, not one of {VALID_DESTINATIONS}")

    kinds = {o.get("kind") for o in mapping}
    missing_kinds = [k for k in OBLIGATION_KINDS if k not in kinds]
    if missing_kinds:
        failures.append(
            f"all_obligation_kinds: no mapping covers {missing_kinds}; the plan names four kinds "
            "of obligation and a mapping that covers one conserves little")

    grammar = design.get("identity_grammar")
    if _absent(grammar):
        failures.append(
            "identity_grammar: no identifier grammar stated. Identity allocation must not rest "
            "on ad hoc regex assumptions")
    else:
        try:
            if not re.match(str(grammar), _REAL_SPLIT_IDENTIFIER):
                failures.append(
                    f"identity_grammar: the stated grammar {grammar!r} cannot express "
                    f"{_REAL_SPLIT_IDENTIFIER}, the only split identifier Wave 1 allocated")
        except re.error as exc:
            failures.append(f"identity_grammar: {grammar!r} is not a valid expression ({exc})")

    if design.get("strong_invariant_asserted") is not True:
        failures.append(
            "strong_invariant: the design does not assert that splitting conserves authorized "
            "intent and proof obligations")

    if _absent(design.get("original_biu_lifecycle")):
        failures.append(
            "original_lifecycle: the canonical status of the original BIU after a split is not "
            "defined (parent, superseded, retained integration unit, or other canonical form)")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave1-biu-split-replan-design.json")
    design = json.loads(path.read_text())
    ok, failures = check_design(design)
    print(f"design      : {path}")
    print(f"obligations : {len(design.get('conservation_mapping', []))}")
    print(f"checks      : {', '.join(CHECKS)}")
    print(f"result      : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
