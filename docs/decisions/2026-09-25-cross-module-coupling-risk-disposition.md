# Cross-module coupling risk disposition

Date: 2026-09-25. Status: **Founder decision — binding**.

## Decision

The historical R1 cross-module `allowed_edges` table is **not adopted as AlienIntent policy**.

AlienIntent will instead assess and mechanically constrain coupling using the existing modular-monolith, Domain-Driven Design, Hexagonal Architecture and Python boundaries, extended by the concrete risk checks below.

This resolves `R2-GAP-051-EDGE-AUTHORITY`: the withdrawn R1 edge table remains historical design material only and must not be used as an allowed-import policy or as a reason to declare current source defective.

## Why

A quick current-source review found enough coupling signals that architecture scrutiny should not simply be removed:

1. **Ubiquitous language / bounded-context vocabulary:** current mechanical architecture checks do not verify semantic ownership or vocabulary leakage across modules. This remains an explicit review obligation.
2. **Cross-module domain-object imports:** present in current source, including direct imports of domain values/types across major modules.
3. **Shared database ownership:** no clear evidence was found that separate bounded contexts directly share named business tables. AlienIntent currently reuses a generic operational SQLite store through composition. This must remain an ownership check rather than being presumed safe or defective.
4. **Circular dependencies:** present in the current package dependency graph, including cycles involving execution coordination, control plane, invocation runtime, installation and evidence learning.

The existence of these signals does not prove every observed dependency is wrong. Leaf value/port dependencies can be legitimate in a modular monolith. They do prove that a blanket removal of coupling scrutiny would be premature.

## Required architecture-conformance questions

Before refactoring or accepting a new cross-module dependency, answer:

1. Can each module's **ubiquitous language and domain ownership** be identified clearly? A term with materially different meaning in two modules must not silently share one model.
2. Does one module directly import another module's **domain objects**? If yes, determine whether the imported object is a deliberately shared stable value/contract or inappropriate domain leakage. Prefer ports/translation/ACL boundaries when ownership differs.
3. Do multiple modules directly own or mutate the same **database tables or persistence schema**? Shared infrastructure is permitted; shared domain ownership is not presumed.
4. Are there **circular dependencies between modules**? Any cycle must be explicit, minimal and justified. Application/adaptor cycles are higher risk than leaf value/port references.

A "yes" does not automatically require refactoring. It requires classification against bounded-context ownership, stability and cost of later separation.

## Mechanical enforcement direction

The existing architecture fitness suite remains authoritative for its current checks:
- domain/application code must not import adapters;
- vendor types must not leak into domain/port signatures;
- adapters must declare port contracts;
- configuration reads stay in composition;
- nondeterministic facilities stay out of pure layers.

The next governed SF-REQ-051 design/plan revision should add mechanically useful checks where feasible for:
- cross-module dependency-cycle detection;
- cross-module domain import inventory/classification;
- persistence/table ownership assertions where ownership can be expressed mechanically.

Ubiquitous-language consistency remains partly judgment-based unless/until a reliable mechanical representation exists.

## Risk and timing

Current evidence shows **moderate architectural-coupling risk**, not a demonstrated production defect requiring immediate broad refactoring.

Therefore:
- add visibility and enforceable boundaries now;
- do not refactor every existing dependency merely because it appears in the inventory;
- repair only dependencies shown to violate approved bounded-context/domain ownership or to create material cycle/coupling risk;
- preserve existing working behavior and evidence;
- re-evaluate as the modular monolith evolves.

This is the minimum necessary intervention: prevent obvious architectural leakage from becoming expensive future rework without freezing AlienIntent to an unproven import topology.

## Effect on SF-REQ-051 / U6

`R2-GAP-051-EDGE-AUTHORITY` is resolved by this decision.

U6 / WO-220206 may be replanned against this scoped disposition. Its proof for SF-REQ-051-AC-03 should demonstrate that a genuinely forbidden dependency or incompatible interface is caught mechanically before independent review, using the approved architecture rules plus the scoped coupling checks above.

It must **not** enforce the withdrawn R1 edge table.

Normal plan revision, independent design verification, proof pinning, Agent Ready and release gates still apply.
