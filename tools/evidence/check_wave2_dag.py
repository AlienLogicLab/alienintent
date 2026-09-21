#!/usr/bin/env python3
"""Contract checker for the Wave 2 dependency DAG (Phase 11).

Three properties are mechanically decidable, and all three failed somewhere in Wave 1.

**Acyclicity.** A dependency cycle is not a planning opinion.

**Single ownership.** The phase exit gate is "every planned capability has one owner and
dependency path". PY-10's live transport was owned by nobody until Agent-Ready found it, which
cost a SPLIT_RECOMMENDED and an inserted BIU.

**The capstone rule.** "A capstone must integrate previously proven capabilities. It must not
secretly become first owner of infrastructure required to perform its own proof." That is
PY-10 → PY-09B stated as a rule rather than as a war story: a capstone that first-owns what its
own proof depends on has no proven substrate to integrate, and discovers this at readiness
assessment.

A fourth follows from the third: if a node's proof requires a capability, that capability must be
reachable through its dependency path. A proof obligation with no dependency path is how unowned
substrate hides.

Usage: python3 tools/evidence/check_wave2_dag.py [dag.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKS = ("acyclic", "dependencies_resolve", "one_owner_per_capability", "capstone_integrates",
          "proof_inputs_reachable")


def _reachable(start: str, edges: dict[str, list[str]]) -> set[str]:
    """Every node reachable from `start` by following depends_on."""
    seen: set[str] = set()
    stack = list(edges.get(start, []))
    while stack:
        n = stack.pop()
        if n in seen or n not in edges:
            seen.add(n)
            continue
        seen.add(n)
        stack.extend(edges.get(n, []))
    return seen


def _find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {n: WHITE for n in edges}
    path: list[str] = []

    def visit(n: str) -> list[str] | None:
        colour[n] = GREY
        path.append(n)
        for m in edges.get(n, []):
            if m not in colour:
                continue
            if colour[m] == GREY:
                return path[path.index(m):] + [m]
            if colour[m] == WHITE:
                found = visit(m)
                if found:
                    return found
        path.pop()
        colour[n] = BLACK
        return None

    for n in edges:
        if colour[n] == WHITE:
            found = visit(n)
            if found:
                return found
    return None


def check_dag(dag: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    nodes = dag.get("nodes", [])
    edges = {n["id"]: list(n.get("depends_on") or []) for n in nodes}

    for n in nodes:
        for dep in n.get("depends_on") or []:
            if dep not in edges:
                failures.append(
                    f"dependencies_resolve: {n['id']} depends on {dep!r}, which is not a node")

    cycle = _find_cycle(edges)
    if cycle:
        failures.append(f"acyclic: dependency cycle {' -> '.join(cycle)}")

    owners: dict[str, list[str]] = {}
    for n in nodes:
        for cap in n.get("owns_capabilities") or []:
            owners.setdefault(cap, []).append(n["id"])

    for cap in dag.get("planned_capabilities", []):
        who = owners.get(cap, [])
        if not who:
            failures.append(
                f"one_owner_per_capability: {cap!r} is planned and owned by no node. Unowned "
                "substrate is what PY-10 discovered at Agent-Ready")
        elif len(who) > 1:
            failures.append(
                f"one_owner_per_capability: {cap!r} is owned by {who}; exactly one owner")

    for n in nodes:
        needs = set(n.get("proof_requires_capabilities") or [])
        if n.get("is_capstone"):
            first_owned = needs & set(n.get("owns_capabilities") or [])
            if first_owned:
                failures.append(
                    f"capstone_integrates: capstone {n['id']} first-owns {sorted(first_owned)}, "
                    "which its own proof requires. A capstone integrates previously proven "
                    "capabilities; owning what it must prove with leaves nothing proven to "
                    "integrate")

        if not cycle:
            upstream = _reachable(n["id"], edges)
            available = {c for m in nodes if m["id"] in upstream
                         for c in (m.get("owns_capabilities") or [])}
            available |= set(n.get("owns_capabilities") or [])
            unreachable = sorted(needs - available)
            if unreachable:
                failures.append(
                    f"proof_inputs_reachable: {n['id']} requires {unreachable} to prove itself, "
                    "but no node on its dependency path owns them")

    return (not failures), failures


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/evidence/wave2-dependency-dag.json")
    dag = json.loads(path.read_text())
    ok, failures = check_dag(dag)
    print(f"dag        : {path}")
    print(f"nodes      : {len(dag.get('nodes', []))}")
    print(f"checks     : {', '.join(CHECKS)}")
    print(f"result     : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
