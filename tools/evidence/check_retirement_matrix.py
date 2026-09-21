#!/usr/bin/env python3
"""Contract checker for the Bootstrap Retirement Matrix (Phase 6).

Exit gate:

    No temporary mechanism quietly becomes permanent.
    No known protection disappears before its replacement is operational.

The rule is "retire by replacement, not by date", so RETIRE_CANDIDATE must either have its
replacement implemented or state explicitly what protection is not lost. An unfired protection
is not thereby retirable — it may simply never have been tested — so the checker does not treat
a missing `demonstrated_failure_prevented` as licence to retire.

Usage: python3 tools/evidence/check_retirement_matrix.py [matrix.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = ("mechanism", "purpose", "demonstrated_failure_prevented", "authority",
                   "stated_expiry_condition", "replacement_requirement",
                   "replacement_implemented", "bootstrap_still_operating",
                   "recommended_disposition", "evidence")

REQUIRED_MECHANISMS = (
    "SWF-21 release authority",
    "SWF-29 liveness reconciliation",
    "SWF-27 observer",
    "attention queue",
    "Windows notification",
    "session-bound attention waiter",
    "coordinator checkpoint",
    "PRODUCER-on-Claude temporary profile change",
    "Node/bootstrap execution authority",
)

DISPOSITIONS = ("RETIRE_CANDIDATE", "KEEP_UNTIL_REPLACED", "REVERT_TEMPORARY_CHANGE",
                "NEEDS_DECISION")

CHECKS = ("required_fields", "all_mechanisms_covered", "valid_disposition",
          "retire_by_replacement", "revert_needs_expiry", "transition_plan_complete")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined")


def _absent(value) -> bool:
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def _norm(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def check_matrix(matrix: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    mechs = matrix.get("mechanisms", [])

    for m in mechs:
        name = m.get("mechanism", "<unnamed>")

        missing = [f for f in REQUIRED_FIELDS if f not in m]
        if missing:
            failures.append(f"required_fields: {name} is missing {missing}")
            continue

        disp = m["recommended_disposition"]
        if disp not in DISPOSITIONS:
            failures.append(
                f"valid_disposition: {name} has {disp!r}, not one of {DISPOSITIONS}")
            continue

        if disp == "RETIRE_CANDIDATE":
            replaced = m["replacement_implemented"] in (True, "true", "yes")
            if not replaced and _absent(m.get("protection_not_lost")):
                failures.append(
                    f"retire_by_replacement: {name} is a RETIRE_CANDIDATE with no implemented "
                    "replacement and no statement of what protection is not lost. Retire by "
                    "replacement, not by date")

        if disp == "REVERT_TEMPORARY_CHANGE" and _absent(m["stated_expiry_condition"]):
            failures.append(
                f"revert_needs_expiry: {name} is a REVERT_TEMPORARY_CHANGE with no stated expiry "
                "condition; a change cannot be shown to have outlived an authorization that was "
                "never bounded")

    present = {_norm(m.get("mechanism")) for m in mechs}
    for required in REQUIRED_MECHANISMS:
        if not any(_norm(required) in p or p in _norm(required) for p in present):
            failures.append(f"all_mechanisms_covered: {required!r} is not audited")

    planned = {_norm(s.get("mechanism")) for s in matrix.get("transition_plan", [])}
    for m in mechs:
        if m.get("recommended_disposition") in ("RETIRE_CANDIDATE", "REVERT_TEMPORARY_CHANGE",
                                                "NEEDS_DECISION"):
            if _norm(m.get("mechanism")) not in planned:
                failures.append(
                    f"transition_plan_complete: {m.get('mechanism')} is not retained but has no "
                    "step in the transition plan; an ordering is what prevents a protection "
                    "disappearing before its replacement")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave1-bootstrap-retirement-matrix.json")
    matrix = json.loads(path.read_text())
    ok, failures = check_matrix(matrix)
    print(f"matrix     : {path}")
    print(f"mechanisms : {len(matrix.get('mechanisms', []))}")
    print(f"checks     : {', '.join(CHECKS)}")
    print(f"result     : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
