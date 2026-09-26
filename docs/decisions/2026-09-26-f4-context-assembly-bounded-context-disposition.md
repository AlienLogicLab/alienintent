# F4 — `context_assembly` bounded-context identity disposition

Date: 2026-09-26. Status: **Founder decision — binding**.

Recorded via Director inbox handoff `founder-f4-context-assembly-boundary-20260926T071415Z`
(2026-09-26T07:14:16Z, relayed by a Founder-authorized observing session, not acting as
Factory Director).

## Decision

Requirements / Planning is the bounded context. `context_assembly` is an internal
module/application capability within that bounded context, not a separate bounded
context.

This resolves follow-up **F4** (Design Contract, SF-REQ-051): docs/architecture/2026-09-22-founder-decisions-canonicalization-report.md section 4 conflict 4 and section 6 F4.

## Why

The approved architecture already establishes Requirements / Planning as the semantic
boundary owning intake/normalization, provenance, specification, planning,
requirement-to-BIU compilation, dependency DAG construction, Agent Ready invocation
through a port, disposition processing, and split/replan. `context_assembly` was
previously an approved initial module, not an independently approved bounded context.
No demonstrated distinct ubiquitous language, invariant set, or ownership boundary
justifies promoting it to its own bounded context. This preserves the modular-monolith
and Hexagonal design and avoids turning a package/module name into a domain boundary.

## Consequences

Canonical design/contracts classify `context_assembly` under Requirements / Planning.
Existing package names may remain for compatibility and implementation organization;
this decision is semantic/architectural, not a package-renaming mandate. Dependency/
fitness rules reflect Requirements / Planning as the context boundary and
`context_assembly` as its internal module/capability.

This disposition unblocks a fresh native Agent Ready assessment of WO-220208 (Issue
#117) and, once #117 reaches DONE, of downstream WO-220211 (Issue #119) — subject to
all other gates each of those BIUs independently states.
