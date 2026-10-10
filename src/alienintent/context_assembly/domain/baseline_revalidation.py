"""Baseline revalidation: whether an assessed Work Item still holds at current canonical main. Pure.

"Never silently retarget an assessed Work Item onto changed code. Revalidate it first." (Founder, decisions section
39; WORK-PREPARATION-REFILL spec 3.8.) Main unchanged: proceed at the assessed baseline. Main no longer containing
the baseline (moved backward, or rewritten): back to preparation, never execution from a revision ahead of canonical
main, which would carry commits main no longer has (Founder, 2026-10-11). Main advanced past the baseline: retarget
to main only when every check passes, in order: the contract is inside the plan authority at that main; the packet
declares its targeted proof set (decisions section 43); its proof and mutations blocks read; and every guarded entry
(authorized scope, proof files, mutation paths and tests, authority references) is a path, none of which a path main
changed equals, lies under or lies over. An entry that is not a path (prose or anything with whitespace, a glob)
cannot be guarded, so it holds. Anything else goes back through Work Preparation and Agent Ready at the assessed
baseline. Every fact is read by the caller at one main SHA.
"""
from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from alienintent.execution_coordination.domain.plan_authority import normalized, under

PROCEED, RETARGET, REPREPARE = "proceed", "retarget", "reprepare"
# How canonical main relates to the assessed baseline in the commit graph, as the caller read it.
BEHIND, ADVANCED, DIVERGED = "behind", "advanced", "diverged"


def reference_paths(references: Sequence[str], plan_path: str) -> tuple[str, ...]:
    """The guarded entries of a contract's authority references: `<path> obligation:<label>` guards its path; any
    other reference is guarded whole, so prose cannot be guarded and holds. The canonical plan is left out: the plan
    authority check judges it by content."""
    entries = []
    for reference in references:
        parts = reference.split()
        entry = parts[0] if len(parts) == 2 and parts[1].startswith("obligation:") else reference
        if parts and entry != plan_path:
            entries.append(entry)
    return tuple(entries)


@dataclass(frozen=True)
class BaselineDecision:
    kind: str  # PROCEED | RETARGET | REPREPARE
    revision: str  # the starting revision: main for a retarget, else the assessed baseline
    checks: tuple[tuple[str, bool, str], ...]  # (check, passed, detail), in order; empty for PROCEED


def revalidate(baseline: str, main: str, relation: str, changed: Collection[str], guarded: Collection[str],
               authority_reasons: Sequence[str], proof_declared: bool,
               packet_errors: Sequence[str] = ()) -> BaselineDecision:
    """The decision for an item assessed at `baseline` when canonical main is `main` (`relation`: BEHIND, ADVANCED
    or DIVERGED), from the paths `changed` between them, the item's `guarded` paths, its `outside_authority` reasons
    at `main`, whether its packet declares a proof set and why its proof or mutations block cannot be read."""
    if baseline == main:
        return BaselineDecision(PROCEED, baseline, ())
    if relation != ADVANCED:
        return BaselineDecision(REPREPARE, baseline, (("baseline-on-main", False, f"canonical main {relation}"),))
    paths = {entry: None if any(c.isspace() for c in str(entry)) else normalized(entry) for entry in guarded}
    unguardable = sorted(entry for entry, path in paths.items() if path is None)
    readable = [path for path in paths.values() if path is not None]
    touched = sorted(path for path in changed if any(under(path, entry) or under(entry, path) for entry in readable))
    checks = (("plan-authority", not authority_reasons, "; ".join(authority_reasons)),
              ("proof-declared", proof_declared, "" if proof_declared else "the packet declares no proof set"),
              ("packet-readable", not packet_errors, "; ".join(packet_errors)),
              ("scope-proof-references-untouched", not touched and not unguardable,
               ", ".join([*touched, *(f"not a path: {entry}" for entry in unguardable)])))
    if all(passed for _, passed, _ in checks):
        return BaselineDecision(RETARGET, main, checks)
    return BaselineDecision(REPREPARE, baseline, checks)
