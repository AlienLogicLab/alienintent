#!/usr/bin/env python3
"""Contract checker for the final Wave 1 retrospective (Phase 7).

Two rules here are worth enforcing mechanically because prose reliably erodes them.

The reconciliation rule: existing owner first, amendment preferred, a new Product Requirement
only where genuinely uncovered and proven so, and Priority/Wave never invented. Phase 2
established the standard the proof must meet — "an existing owner could absorb it" is not "an
existing owner owns it".

The causality constraint: PY-09B and PY-10 were both first-pass accepted, which is FACT. The
claim that verification-first sequencing or provider substitution *caused* that was tested as
RAW-100 and not promoted — n=2, and the provider change is confounded with the sequencing
change. The coordinator asserted it and withdrew it. A retrospective is exactly where such a
claim creeps back in wearing a stronger verb, so causal language about those acceptances is
refused unless it is labelled HYPOTHESIS.

UNKNOWN telemetry stays UNKNOWN (SF-REQ-030): token usage and cost are UNKNOWN for all 11 BIUs
and must not appear as numbers.

Usage: python3 tools/evidence/check_retrospective.py [retrospective.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("yield", "learning", "methodology", "architecture", "recommendations")
CHANGE_TYPES = ("AMENDMENT", "NEW_REQUIREMENT", "NO_CHANGE")

CHECKS = ("required_sections", "existing_owner_first", "new_requirement_needs_proof",
          "never_invent_priority_or_wave", "unknown_preserved", "no_unproven_causality")

# Telemetry the accepted manifest records as UNKNOWN for every BIU.
_UNKNOWN_TELEMETRY = ("token_usage", "cost")

_CAUSAL_VERBS = ("caused", "causes", "because of", "due to", "resulted in", "led to",
                 "drove", "produced by", "attributable to")
_HEDGES = ("hypothesis", "may have", "might have", "could have", "possibly", "unproven",
           "not established", "confounded")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing")


def _absent(value) -> bool:
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_retrospective(retro: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    for s in REQUIRED_SECTIONS:
        if s not in retro:
            failures.append(f"required_sections: {s} is missing")

    for rec in retro.get("recommendations", []):
        what = rec.get("proposed_change", "<unnamed>")
        ctype = rec.get("change_type")

        if ctype not in CHANGE_TYPES:
            failures.append(f"existing_owner_first: {what} has change_type={ctype!r}")
            continue

        if ctype != "NEW_REQUIREMENT" and _absent(rec.get("existing_owner")):
            failures.append(
                f"existing_owner_first: {what} names no existing owner. Existing owner first, "
                "amendment preferred; an unowned change is a new requirement and must prove it")

        if ctype == "NEW_REQUIREMENT" and _absent(rec.get("ownership_proof")):
            failures.append(
                f"new_requirement_needs_proof: {what} proposes a new Product Requirement without "
                "proving no existing owner covers the semantics")

        if rec.get("priority_or_wave_invented") not in (False, "false", "no"):
            failures.append(
                f"never_invent_priority_or_wave: {what} invents Priority or Wave; that is a "
                "Founder decision, not a recommendation's to make")

    y = retro.get("yield", {})
    for field in _UNKNOWN_TELEMETRY:
        if field in y and not isinstance(y[field], str):
            failures.append(
                f"unknown_preserved: yield.{field} is {y[field]!r}; the manifest records it as "
                "UNKNOWN for all 11 BIUs and UNKNOWN is never silently converted to a number")

    claim = str(retro.get("causality_claim", ""))
    low = claim.lower()
    if any(v in low for v in _CAUSAL_VERBS) and not any(h in low for h in _HEDGES):
        failures.append(
            "no_unproven_causality: the causality_claim asserts a cause for the first-pass "
            "acceptances without hedging. RAW-100 was tested and not promoted (n=2, confounded "
            "with the provider change); HYPOTHESIS with its confound stated is the ceiling")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave1-final-retrospective.json")
    retro = json.loads(path.read_text())
    ok, failures = check_retrospective(retro)
    print(f"retrospective   : {path}")
    print(f"recommendations : {len(retro.get('recommendations', []))}")
    print(f"checks          : {', '.join(CHECKS)}")
    print(f"result          : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
