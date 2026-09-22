#!/usr/bin/env python3
"""Contract checker for the Wave 2 specified requirement set (Phase 8).

Exit gate: every selected candidate is sufficiently specified for Design Contract work, and no
unresolved product intent is hidden in design.

Three Wave 1 lessons are enforced mechanically.

A requirement authored from an id that was never defined anywhere must be flagged for Founder
ratification. `SF-REQ-048`, `SF-REQ-052` and `SF-REQ-056` are referenced across the repository
but defined in no form, and `SF-REQ-056` is a Wave 2 candidate — so specifying it is writing a
requirement, which amendment §10 permits only when it is not done silently.

An acceptance criterion must be verifiable. PY-09B binding rule 6 demanded proof that the
platform's permission model cannot give, and SWF-34 was needed to undo it. A criterion no
evidence could satisfy is a defect, not a high standard; so is one that restates the
requirement.

A lane must carry operational semantics. A lane that exists only as a name is worse than an
absent one, because it looks like coverage.

Usage: python3 tools/evidence/check_wave2_specify.py [specified-requirements.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SPEC_FIELDS = ("intent", "value", "scope", "non_goals", "dependencies", "acceptance_criteria",
               "authority_gaps", "security_constraints", "operational_constraints",
               "observability_evidence", "failure_modes")

# Fields where "none" is never a meaningful answer. A requirement with no intent, no value, no
# scope, no acceptance criteria or no conceivable failure mode has not been specified.
# The remainder must be *present* but may legitimately answer "none identified" -- a requirement
# genuinely may have no authority gap and no security constraint, and forcing prose there
# manufactures content rather than eliciting it.
_MUST_BE_SUBSTANTIVE = ("intent", "value", "scope", "acceptance_criteria", "failure_modes")

NAMED_CANDIDATES = ("SF-REQ-051", "SF-REQ-053", "SF-REQ-056", "SF-REQ-039", "SWF-32")

LANES = ("CAPTURE", "SPECIFY", "DESIGN", "PLAN", "TASKS", "READY")

CHECKS = ("spec_fields_complete", "rejection_needs_reason", "authored_needs_ratification",
          "all_named_candidates_evaluated", "verifiable_acceptance",
          "never_invent_priority_or_wave", "lanes_have_semantics")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined")
_SELF_REFERENTIAL = ("the requirement is satisfied", "the requirement is met",
                     "requirement met", "works as intended", "behaves correctly",
                     "the capability works")


def _absent(value) -> bool:
    if isinstance(value, (list, tuple)):
        return not [v for v in value if not _absent(v)]
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_specify(doc: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    cands = doc.get("candidates", [])

    for c in cands:
        rid = c.get("requirement_id", "<no id>")
        selected = c.get("selected")

        if not selected:
            if _absent(c.get("rejection_reason")):
                failures.append(
                    f"rejection_needs_reason: {rid} is not selected and gives no reason; "
                    "declining is legitimate, declining silently is not")
            continue

        absent_fields = [f for f in SPEC_FIELDS if f not in c]
        hollow = [f for f in _MUST_BE_SUBSTANTIVE if f in c and _absent(c.get(f))]
        if absent_fields or hollow:
            detail = []
            if absent_fields:
                detail.append(f"missing {absent_fields}")
            if hollow:
                detail.append(f"empty on {hollow}, where 'none' is not a meaningful answer")
            failures.append(f"spec_fields_complete: {rid} is " + "; ".join(detail))

        if c.get("definition_status") == "AUTHORED_IN_THIS_PHASE" and \
                c.get("founder_ratification_required") is not True:
            failures.append(
                f"authored_needs_ratification: {rid} is authored in this phase from an id that "
                "was never defined, without flagging Founder ratification. Amendment §10 permits "
                "specifying in-scope requirements, never introducing one silently")

        acs = c.get("acceptance_criteria") or []
        if _absent(acs):
            failures.append(f"verifiable_acceptance: {rid} has no acceptance criteria")
        for ac in acs:
            if any(s in str(ac).strip().lower() for s in _SELF_REFERENTIAL):
                failures.append(
                    f"verifiable_acceptance: {rid} has a self-referential acceptance criterion "
                    f"({ac!r}); restating the requirement is not a criterion")

        if c.get("priority_or_wave_invented") not in (False, "false", "no"):
            failures.append(
                f"never_invent_priority_or_wave: {rid} invents Priority or Wave; that is Founder "
                "authority")

    evaluated = {c.get("requirement_id") for c in cands}
    for named in NAMED_CANDIDATES:
        if named not in evaluated:
            failures.append(
                f"all_named_candidates_evaluated: {named} was named for evaluation and does not "
                "appear; evaluate and reject with a reason, or select and specify it")

    lanes = doc.get("lane_semantics", {})
    for lane in LANES:
        if lane not in lanes or _absent(lanes.get(lane)):
            failures.append(
                f"lanes_have_semantics: {lane} has no operational semantics. Do not mechanically "
                "preserve a lane that exists only as a name")

    return (not failures), failures


RENDER_CHECKS = ("markdown_render_equivalent",)


def render_inventory_row(c: dict) -> str:
    """The one way an inventory row is rendered; the Markdown must contain it verbatim."""
    sel = "Yes" if c.get("selected") else "No"
    reason = (c.get("selection_reason") or c.get("rejection_reason") or "").replace("\n", " ").replace("|", "/")
    return f"| {c['requirement_id']} | {sel} | {c.get('title', '')}: {reason} |"


def render_acceptance_line(ac) -> str:
    if not isinstance(ac, dict):  # older fixtures render a bare criterion
        return f"- {str(ac).replace(chr(10), ' ')}"
    crit = str(ac.get("criterion", "")).replace("\n", " ")
    ver = str(ac.get("verification", "")).replace("\n", " ")
    return f"- **{ac['id']}**: {crit} Verification: {ver}"


def check_render(doc: dict, markdown: str) -> tuple[bool, list[str]]:
    """DV-9 (2026-09-22): a Markdown rendering that disagrees with the JSON is a live
    contradiction, not a cosmetic drift — the stale AC-05 prescribed a different acceptance scope.
    Every selected candidate's inventory row and acceptance criteria must appear verbatim."""
    failures: list[str] = []
    for c in doc.get("candidates", []):
        if not c.get("selected"):
            continue
        row = render_inventory_row(c)
        if row not in markdown:
            failures.append(f"markdown_render_equivalent: inventory row for {c['requirement_id']} does not "
                            "match the JSON title/selection reason")
        for ac in c.get("acceptance_criteria", []):
            if render_acceptance_line(ac) not in markdown:
                failures.append(f"markdown_render_equivalent: {ac.get('id')} in the Markdown does not match "
                                "the JSON criterion/verification")
    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave2-specified-requirements.json")
    doc = json.loads(path.read_text())
    ok, failures = check_specify(doc)
    md = path.with_suffix(".md")
    if md.exists():
        rok, rfail = check_render(doc, md.read_text())
        ok, failures = ok and rok, failures + rfail
    sel = [c for c in doc.get("candidates", []) if c.get("selected")]
    print(f"document   : {path}")
    print(f"candidates : {len(doc.get('candidates', []))} evaluated, {len(sel)} selected")
    print(f"checks     : {', '.join(CHECKS + RENDER_CHECKS)}")
    print(f"result     : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
