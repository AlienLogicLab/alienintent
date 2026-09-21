#!/usr/bin/env python3
"""Contract checker for the Wave 2 candidate BIU set (Phase 12).

The plan names seven learned decomposition rules. Five reduce to decidable properties, and each
is here because Wave 1 paid for its absence.

**No unowned substrate.** PY-10's live transport was needed by a capstone and owned by nobody,
discovered at Agent-Ready. Every capability a BIU needs must be provided by some BIU.

**Requirement conservation.** SWF-33 established that a decomposition must not lose an
obligation. Every requirement in the plan must appear in some BIU.

**No impossible acceptance criteria.** PY-09B binding rule 6 demanded proof that the platform's
permission model cannot give; SWF-34 was needed to undo it. A criterion no evidence could satisfy
is a defect, not a high standard.

**Proof harness established early.** Wave 1's repeated shape was a verification harness built
after the repair it was meant to judge. A BIU carrying acceptance criteria with no verification
obligation has deferred its proof.

**Capstones integrate rather than invent.** A capstone that both needs and provides a capability
is inventing the substrate it is supposed to integrate.

Usage: python3 tools/evidence/check_wave2_bius.py [bius.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BIU_FIELDS = ("intent", "requirement_links", "fixed_decisions", "scope", "non_goals",
              "dependencies", "acceptance_criteria", "verification_obligations",
              "evidence_obligations", "architecture_constraints", "capabilities", "budget",
              "candidate_custody", "release_policy", "stop_condition", "escalation_condition")

CHECKS = ("biu_fields_complete", "no_unowned_substrate", "requirement_conservation",
          "no_impossible_acceptance", "proof_harness_early", "capstone_integrates")

# Phrasings that demand proof of a universal negative. PY-09B's binding rule 6 was of this shape:
# the platform's permission model cannot produce evidence that a token reaches nothing else.
_IMPOSSIBLE_SHAPES = ("cannot access any other", "cannot ever", "can never", "no other project",
                      "prove the absence of", "cannot be reached", "never be reached",
                      "cannot access anything", "prove nothing else")

# Fields that must be present but may legitimately be empty. A root BIU has no dependencies, and
# forcing prose there would manufacture a dependency rather than elicit one.
_MAY_BE_NONE = ("non_goals", "architecture_constraints", "dependencies")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined")


def _absent(value) -> bool:
    if isinstance(value, (list, tuple)):
        return not [v for v in value if not _absent(v)]
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_bius(doc: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    bius = doc.get("bius", [])

    provided: set[str] = set()
    for b in bius:
        provided |= set(b.get("provides_capabilities") or [])

    linked: set[str] = set()

    for b in bius:
        bid = b.get("biu_id", "<no id>")

        missing = [f for f in BIU_FIELDS if f not in b]
        hollow = [f for f in BIU_FIELDS
                  if f in b and f not in _MAY_BE_NONE and _absent(b.get(f))]
        if missing or hollow:
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if hollow:
                detail.append(f"hollow on {hollow}")
            failures.append(f"biu_fields_complete: {bid} is " + "; ".join(detail))

        linked |= set(b.get("requirement_links") or [])

        for cap in b.get("needs_capabilities") or []:
            if cap not in provided:
                failures.append(
                    f"no_unowned_substrate: {bid} needs {cap!r}, which no BIU provides. That is "
                    "the PY-10 live-transport failure, found at planning instead of at readiness")

        acs = b.get("acceptance_criteria") or []
        for ac in acs:
            low = str(ac).lower()
            if any(s in low for s in _IMPOSSIBLE_SHAPES):
                failures.append(
                    f"no_impossible_acceptance: {bid} has an acceptance criterion demanding proof "
                    f"of a universal negative ({str(ac)[:80]!r}). PY-09B binding rule 6 was this "
                    "shape and SWF-34 was needed to undo it")

        if acs and _absent(b.get("verification_obligations")):
            failures.append(
                f"proof_harness_early: {bid} carries acceptance criteria with no verification "
                "obligation; the proof harness is deferred past the work it must judge")

        if b.get("is_capstone"):
            invented = set(b.get("needs_capabilities") or []) & set(b.get("provides_capabilities") or [])
            if invented:
                failures.append(
                    f"capstone_integrates: capstone {bid} both needs and provides "
                    f"{sorted(invented)}; it is inventing the substrate it should integrate")

    for rid in doc.get("required_requirements", []):
        if rid not in linked:
            failures.append(
                f"requirement_conservation: {rid} is in the plan and linked by no BIU; a "
                "decomposition may redistribute obligations, not drop them")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave2-candidate-bius.json")
    doc = json.loads(path.read_text())
    ok, failures = check_bius(doc)
    print(f"bius     : {path}")
    print(f"count    : {len(doc.get('bius', []))}")
    print(f"checks   : {', '.join(CHECKS)}")
    print(f"result   : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
