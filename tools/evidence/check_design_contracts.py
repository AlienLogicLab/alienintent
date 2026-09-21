#!/usr/bin/env python3
"""Contract checker for Wave 2 Design Contracts (Phase 9).

Required discipline, from the program plan:

    Do not let implementation agents make material design decisions.
    Design must be explicit enough that implementation becomes local execution rather than
    architecture invention.

That discipline is checkable. A contract that defers a material decision to implementation has
not made implementation local — it has moved the architecture into the implementer's head. Wave 1
paid for that twice: PY-06's unit-tested objects were never wired into a composition root, and
PY-09B's permission expectation and its passing preflight shared one wrong premise for about
nineteen hours.

Bounded contexts are checked against the ones that actually exist in this repository. A design
that invents a parallel structure is unimplementable against the codebase it governs, so a new
context must be justified rather than assumed.

Every contract must name at least one deterministic enforcement opportunity. Phase 3 promoted
seven gates into layers that already existed and proposed zero new ones; a design that names none
has not looked.

Usage: python3 tools/evidence/check_design_contracts.py [contracts.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_FIELDS = ("bounded_context", "domain_owner", "ubiquitous_language", "ports", "adapters",
                   "state", "transitions", "identities", "persistence", "concurrency",
                   "failure_modes", "recovery", "evidence", "observability", "security",
                   "operator_surface", "non_goals", "architecture_fitness",
                   "deterministic_enforcement_opportunities")

# Contexts that exist in the repository today.
KNOWN_CONTEXTS = ("composition", "context_assembly", "control_plane", "evidence_learning",
                  "execution_coordination", "installation", "invocation_runtime",
                  "alienintent", "config", "domain", "github", "providers", "runtime")

CHECKS = ("contract_fields_complete", "no_material_decision_deferred", "bounded_context_known",
          "every_requirement_covered", "enforcement_opportunity_named")

# Fields where "none" can be a truthful answer rather than an omission.
_MAY_BE_NONE = ("non_goals", "concurrency", "security")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "undefined",
                 "to be decided", "implementation decides", "implementer's choice")


def _absent(value) -> bool:
    if isinstance(value, (list, tuple)):
        return not [v for v in value if not _absent(v)]
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_contracts(doc: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    contracts = doc.get("contracts", [])

    for c in contracts:
        rid = c.get("requirement_id", "<no requirement>")

        missing = [f for f in CONTRACT_FIELDS if f not in c]
        hollow = [f for f in CONTRACT_FIELDS
                  if f in c and f not in _MAY_BE_NONE and _absent(c.get(f))]
        if missing or hollow:
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if hollow:
                detail.append(f"hollow on {hollow}")
            failures.append(f"contract_fields_complete: {rid} is " + "; ".join(detail))

        deferred = [d for d in (c.get("deferred_to_implementation") or []) if not _absent(d)]
        if deferred:
            failures.append(
                f"no_material_decision_deferred: {rid} defers {deferred} to implementation. "
                "Design must be explicit enough that implementation is local execution, not "
                "architecture invention; record bounded choices under implementation_local_freedom")

        ctx = c.get("bounded_context")
        if not _absent(ctx) and ctx not in KNOWN_CONTEXTS and \
                _absent(c.get("new_context_justification")):
            failures.append(
                f"bounded_context_known: {rid} names bounded context {ctx!r}, which does not exist "
                f"in the repository, without justification. Existing contexts: {KNOWN_CONTEXTS}")

        if _absent(c.get("deterministic_enforcement_opportunities")):
            failures.append(
                f"enforcement_opportunity_named: {rid} names no deterministic enforcement "
                "opportunity. Phase 3 promoted seven gates into existing layers; a design that "
                "finds none has not looked")

    covered = {c.get("requirement_id") for c in contracts}
    for rid in doc.get("required_requirements", []):
        if rid not in covered:
            failures.append(
                f"every_requirement_covered: {rid} was selected in Phase 8 and has no design "
                "contract; Phase 10 verification would have nothing to verify")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave2-design-contracts.json")
    doc = json.loads(path.read_text())
    ok, failures = check_contracts(doc)
    print(f"contracts : {path}")
    print(f"count     : {len(doc.get('contracts', []))}")
    print(f"checks    : {', '.join(CHECKS)}")
    print(f"result    : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
