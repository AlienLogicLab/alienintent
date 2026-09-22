#!/usr/bin/env python3
"""Contract checker for the Wave 2 Agent-Ready assessment set (Phase 13).

The invariant Phase 4 established and this enforces: **no disposition is coerced to READY**, and
every non-READY outcome follows the canonical handling matrix — implementation not permitted, a
defined next action, and a reassessment trigger, because resolved prerequisites must not
retroactively rewrite a verdict.

The strongest available check is mechanical. 23 of the 46 candidate BIUs carry open authority
gaps; a BIU that still waits on a Founder decision cannot be READY, whatever an assessment says.
That turns "do not silently vary the readiness bar" from an instruction into a property.

An assessment execution failure is not a disposition. LRN-008 records a verifier that exited
success with no B-DISP verdict and became DURABLE_RESULT_MISSING rather than ACCEPT — the control
working. Failures belong in `execution_failures`, never in `disposition`.

A SPLIT disposition (historical bootstrap-assessor name: SPLIT_RECOMMENDED) must invoke the
process Phase 5 designed rather than improvising, which is the whole point of having designed it.

Usage: python3 tools/evidence/check_agent_ready_set.py [assessments.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Agent Ready's dispositions are exactly these four (Founder decisions v0.1, 2026-09-22).
AGENT_READY_DISPOSITIONS = ("READY", "CLARIFY", "SPLIT", "HOLD")
# Historical bootstrap-assessor vocabulary: what Wave 1 and the post-Wave-1 programme produced
# through a coordinator-run prompt. Valid only for an artifact that declares it.
LEGACY_BOOTSTRAP_ASSESSOR_DISPOSITIONS = (  # historical bootstrap-assessor vocabulary
    "READY", "BLOCKED", "NEEDS_CLARIFICATION", "SPLIT_RECOMMENDED")  # historical, not Agent Ready
LEGACY_VOCABULARY = "alienintent-bootstrap-assessor"
_SPLIT_NAMES = ("SPLIT", "SPLIT_RECOMMENDED")  # canonical, then historical bootstrap-assessor name

CHECKS = ("every_biu_assessed", "canonical_disposition", "no_coercion_to_ready",
          "matrix_conformance", "provider_provenance", "terminal_result_validated",
          "split_invokes_process")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined")


def _absent(value) -> bool:
    if isinstance(value, (list, tuple)):
        return not [v for v in value if not _absent(v)]
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_set(doc: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    assessments = doc.get("assessments", [])
    legacy = doc.get("assessor_vocabulary") == LEGACY_VOCABULARY
    dispositions = LEGACY_BOOTSTRAP_ASSESSOR_DISPOSITIONS if legacy else AGENT_READY_DISPOSITIONS

    for a in assessments:
        bid = a.get("biu_id", "<no id>")
        disp = a.get("disposition")

        if disp not in dispositions:
            failures.append(
                f"canonical_disposition: {bid} has disposition {disp!r}, not one of "
                f"{dispositions}. Agent Ready has exactly READY, CLARIFY, SPLIT, HOLD; BLOCKED is "
                "a lifecycle state, and an execution failure belongs in execution_failures")
            continue

        if disp == "READY" and not _absent(a.get("open_authority_gaps")):
            failures.append(
                f"no_coercion_to_ready: {bid} is READY while authority gaps "
                f"{a.get('open_authority_gaps')} remain open. A BIU waiting on a Founder decision "
                "is not ready, whatever the assessment concluded")

        if disp != "READY":
            if a.get("implementation_allowed") not in (False, "false", "no"):
                failures.append(
                    f"matrix_conformance: {bid} is {disp} yet permits implementation; only READY "
                    "authorizes implementation")
            if _absent(a.get("reassessment_trigger")):
                failures.append(
                    f"matrix_conformance: {bid} is {disp} with no reassessment trigger; resolved "
                    "prerequisites must not retroactively rewrite the verdict")
            if _absent(a.get("next_action")):
                failures.append(
                    f"matrix_conformance: {bid} is {disp} with no next action, which leaves the "
                    "outcome to coordinator improvisation")

        if disp in _SPLIT_NAMES and _absent(a.get("split_process_ref")):
            failures.append(
                f"split_invokes_process: {bid} is {disp} without referencing the canonical "
                "split/replan process; the split transaction (SF-REQ-013) exists so this is not "
                "improvised")

        if _absent(a.get("provider")) or _absent(a.get("model")):
            failures.append(
                f"provider_provenance: {bid} records no explicit provider/model provenance")

        if a.get("terminal_result_valid") is not True:
            failures.append(
                f"terminal_result_validated: {bid} has no structurally validated terminal result; "
                "success is not inferred from an assessment having been attempted")

    assessed = {a.get("biu_id") for a in assessments}
    for bid in doc.get("required_bius", []):
        if bid not in assessed:
            failures.append(f"every_biu_assessed: {bid} has no assessment")

    for f in doc.get("execution_failures", []):
        if f.get("is_disposition") not in (False, "false", "no"):
            failures.append(
                f"canonical_disposition: execution failure for {f.get('biu_id')} is marked a "
                "disposition; it is not one")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave2-agent-ready-assessments.json")
    doc = json.loads(path.read_text())
    ok, failures = check_set(doc)
    a = doc.get("assessments", [])
    ready = sum(1 for x in a if x.get("disposition") == "READY")
    print(f"assessments : {path}")
    print(f"count       : {len(a)} ({ready} READY)")
    print(f"checks      : {', '.join(CHECKS)}")
    print(f"result      : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
