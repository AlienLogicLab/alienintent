#!/usr/bin/env python3
"""Contract checker for the Agent-Ready Outcome Handling Matrix (Phase 4).

The invariant this exists to enforce, from the program plan:

    Every Agent-Ready disposition has exactly one defined authority path.
    No non-READY outcome may be silently coerced into READY.
    Resolved prerequisites do not retroactively rewrite an old BLOCKED verdict;
    reassessment is required.

Deterministic prework gives this teeth. Across 32 retained assessment files, BLOCKED and
SPLIT_RECOMMENDED never appear as a persisted disposition, although Wave 1 produced both
(`tools/evidence/check_wave1.py:123` asserts PY-10 verdicts BLOCKED → SPLIT_RECOMMENDED →
READY). PY-09B kept its non-READY verdict as a dated sibling file; PY-10's was overwritten by
the READY reassessment. Silent coercion is therefore not hypothetical here.

Execution failures are not readiness dispositions. Conflating them is how a provider timeout
becomes a readiness verdict — which is exactly the failure LRN-008 records.

Usage: python3 tools/evidence/check_agent_ready_matrix.py [matrix.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = ("disposition", "semantic_meaning", "authority_owner", "lifecycle_effect",
            "next_action", "required_artifact", "attention_behavior", "stale_assessment_rule",
            "reassessment_trigger", "DAG_effect", "Founder_decision_required",
            "implementation_allowed")

REQUIRED_FAILURE_MODES = {"provider_or_tool_failure", "timeout", "malformed_result",
                          "missing_terminal_result"}

CHECKS = ("required_fields", "no_silent_coercion", "reassessment_required",
          "one_authority_path", "failures_are_not_dispositions", "failure_modes_covered",
          "no_improvisation")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "improvise", "unclear")


def _absent(value) -> bool:
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_matrix(matrix: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    rows = matrix.get("dispositions", [])

    seen: dict[str, int] = {}
    for row in rows:
        name = row.get("disposition", "<unnamed>")
        seen[name] = seen.get(name, 0) + 1

        missing = [f for f in REQUIRED if f not in row]
        if missing:
            failures.append(f"required_fields: {name} is missing {missing}")
            continue

        if _absent(row["authority_owner"]):
            failures.append(
                f"one_authority_path: {name} has no authority owner; every disposition needs "
                "exactly one defined authority path")

        if name != "READY" and row["implementation_allowed"] not in (False, "false", "no"):
            failures.append(
                f"no_silent_coercion: {name} permits implementation. A non-READY outcome must "
                "not be coerced into READY; only READY authorizes implementation")

        if name != "READY" and _absent(row["reassessment_trigger"]):
            failures.append(
                f"reassessment_required: {name} defines no reassessment trigger. Resolved "
                "prerequisites must not retroactively rewrite the verdict — something must "
                "force a fresh assessment")

        if _absent(row["next_action"]):
            failures.append(
                f"no_improvisation: {name} defines no next action, so handling it would require "
                "coordinator improvisation — the exit gate this phase must satisfy")

    for name, count in seen.items():
        if count > 1:
            failures.append(
                f"one_authority_path: {name} appears {count} times; exactly one row per "
                "disposition, or two authority paths could disagree")

    modes = matrix.get("execution_failures", [])
    covered = {m.get("mode") for m in modes}
    uncovered = REQUIRED_FAILURE_MODES - covered
    if uncovered:
        failures.append(
            f"failure_modes_covered: execution failure modes not covered: {sorted(uncovered)}")
    for m in modes:
        if m.get("is_readiness_disposition") not in (False, "false", "no"):
            failures.append(
                f"failures_are_not_dispositions: {m.get('mode')} is marked a readiness "
                "disposition; an execution failure is not a readiness verdict")
        if _absent(m.get("next_action")):
            failures.append(f"no_improvisation: {m.get('mode')} defines no next action")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave1-agent-ready-outcome-matrix.json")
    matrix = json.loads(path.read_text())
    ok, failures = check_matrix(matrix)
    print(f"matrix       : {path}")
    print(f"dispositions : {len(matrix.get('dispositions', []))}")
    print(f"checks       : {', '.join(CHECKS)}")
    print(f"result       : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
