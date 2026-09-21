#!/usr/bin/env python3
"""Contract checker for the Wave 1 Learning Ledger.

Why this exists. Phase 2's first ledger reported `ownership_gaps: 0` while several of its own
records stated, in their own text, that no corresponding capability exists — "SF-REQ-025 can
absorb this gap", "SF-REQ-029 can own normalized observations", and three records whose
`effectiveness_evidence` was literally "none". The records were honest; the schema had nowhere
to put the honesty, because authority and enforcement shared one column.

Founder decision POSTW1-DECIDE-002A:

    Learning Consolidation may and must identify genuine NEW_CAPABILITY_GAP findings when no
    existing canonical owner cleanly owns the semantics. The prohibition on creating new
    requirements during Phase 2 does not prohibit discovering ownership gaps. Do not force-fit
    lessons into adjacent requirements. Preserve authority, enforcement strength, proven-red
    status, and effectiveness evidence as separate dimensions.

So the four dimensions are checked separately:

    owner_fit          CANONICAL | ADJACENT | NONE      — does an owner own the *semantics*?
    enforcement_level  DETERMINISTIC_GATE | REVIEW_GATE | DOCUMENTED_ONLY | NONE
    proven_red         yes | no | UNKNOWN               — was it ever shown to fail?
    effectiveness_evidence                              — did it ever demonstrably work?

Usage:  python3 tools/evidence/check_learning_ledger.py [path] [--negative-controls]

Every check is exercised by a negative control in `test_check_learning_ledger.py`, because a
check that cannot fail is not evidence (SWF-24).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_LEDGER = Path("docs/evidence/wave1-learning-ledger.json")

OWNER_FITS = ("CANONICAL", "ADJACENT", "NONE")
ENFORCEMENT = ("DETERMINISTIC_GATE", "REVIEW_GATE", "DOCUMENTED_ONLY", "NONE")
PROVEN_RED = ("yes", "no", "UNKNOWN")
BUCKETS = ("ALREADY_GRADUATED", "STRENGTHEN_EXISTING_OWNER", "GAP_TRAP_PROMOTION",
           "NEW_CAPABILITY_GAP", "BOOTSTRAP_ONLY")

# An owner that neither enforces nor has ever been shown to work.
_WEAK_ENFORCEMENT = ("DOCUMENTED_ONLY", "NONE")

CHECKS = ("owner_fit_declared", "dimension_values_valid", "no_force_fit",
          "graduation_needs_evidence", "gap_count_matches_records")


def _has_effectiveness(rec: dict) -> bool:
    """The ledger writes absence as "none — <why>", not as the bare word "none".

    An exact-match test read that as evidence present and passed two records whose own text
    said no implementation exists. Absence is a prefix, not an equality.
    """
    val = str(rec.get("effectiveness_evidence", "")).strip().lower()
    if not val:
        return False
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head not in ("none", "unknown", "n/a", "not established", "no evidence")


def check_ledger(ledger: dict) -> tuple[bool, list[str]]:
    """Return (ok, failures). Each failure string names the check that produced it."""
    failures: list[str] = []
    records = ledger.get("records", [])

    for rec in records:
        rid = rec.get("learning_id", "<no id>")

        if "owner_fit" not in rec:
            failures.append(
                f"owner_fit_declared: {rid} names an owner without declaring owner_fit; "
                "authority and enforcement must not share one column")
            continue
        if rec["owner_fit"] not in OWNER_FITS:
            failures.append(f"owner_fit_declared: {rid} has owner_fit={rec['owner_fit']!r}, "
                            f"not one of {OWNER_FITS}")
            continue

        for field, allowed in (("enforcement_level", ENFORCEMENT), ("proven_red", PROVEN_RED),
                               ("recommended_disposition", BUCKETS)):
            if rec.get(field) not in allowed:
                failures.append(
                    f"dimension_values_valid: {rid} has {field}={rec.get(field)!r}, "
                    f"not one of {allowed}")

        # The force-fit shape: declared as the clean semantic owner, while nothing enforces it
        # and nothing shows it ever worked.
        #
        # This does NOT forbid the combination. The ledger's author disputed an earlier rule
        # that did, and was right: explicit ownership survives absent implementation — SWF-32
        # amended SF-REQ-009 to own execution-cycle semantics that nothing yet implements.
        # That is owned-but-unbuilt, a different state from force-fitted. Authority stays a
        # separate dimension from enforcement and effectiveness, per POSTW1-DECIDE-002A. What
        # the claim must carry is a citation: unevidenced, the two states are indistinguishable.
        if (rec["owner_fit"] == "CANONICAL"
                and rec.get("enforcement_level") in _WEAK_ENFORCEMENT
                and not _has_effectiveness(rec)
                and not str(rec.get("owner_fit_basis", "")).strip()):
            failures.append(
                f"no_force_fit: {rid} claims a CANONICAL owner ({rec.get('existing_owner')}) "
                f"with {rec.get('enforcement_level')} enforcement and no effectiveness "
                "evidence, and supplies no owner_fit_basis citing where that owner covers "
                "these semantics. Unevidenced, the claim is indistinguishable from a force-fit "
                "into an adjacent requirement: either cite the coverage or declare the fit "
                "ADJACENT")

        if rec.get("recommended_disposition") == "ALREADY_GRADUATED":
            if not _has_effectiveness(rec):
                failures.append(
                    f"graduation_needs_evidence: {rid} is ALREADY_GRADUATED without "
                    "effectiveness evidence; an owner that was never exercised has not graduated")
            if rec["owner_fit"] != "CANONICAL":
                failures.append(
                    f"graduation_needs_evidence: {rid} is ALREADY_GRADUATED while its owner fit "
                    f"is {rec['owner_fit']}; graduation requires an owner of the semantics")

    declared = ledger.get("summary", {}).get("ownership_gaps")
    actual = sum(1 for r in records
                 if r.get("recommended_disposition") == "NEW_CAPABILITY_GAP")
    if declared is not None and declared != actual:
        failures.append(
            f"gap_count_matches_records: summary ownership_gaps={declared} but {actual} "
            "record(s) carry NEW_CAPABILITY_GAP")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(next((a for a in argv if not a.startswith("-")), DEFAULT_LEDGER))
    ledger = json.loads(path.read_text())
    ok, failures = check_ledger(ledger)
    print(f"ledger        : {path}")
    print(f"records       : {len(ledger.get('records', []))}")
    print(f"checks        : {', '.join(CHECKS)}")
    print(f"result        : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
