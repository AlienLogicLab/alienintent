# Python Engineering — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-04](../../work-units/pre-python-gate/PG-04.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Engineering constraints
Use a src layout and approved bounded contexts; keep domain/application/ports/adapters/composition distinguishable. Do not establish exact package names before FD-02. Typed immutable domain values carry IDs, versions, grants and evidence references; constructors validate invariants. Mutable orchestration/persistence objects stay outside domain values. Use explicit result/error categories; preserve failure causes in sanitized form without leaking credentials.

Async integration must propagate cancellation, bound timeouts/retries and close subprocesses, network sessions and transactions on all exit paths. Blocking Git/provider/database work must not stall an event loop; isolate it behind adapters. Dependency injection occurs in composition, not service locators in domain. Avoid shared mutable global configuration.

Provide a first-class CLI, declared Python support range, reproducible dependency resolution, distribution metadata and upgrade/migration contracts. The exact Python minor version/tool selections are later routine engineering choices only if supported by chosen dependencies and approved constraints; this document authorizes no installation. Typed configuration rejects unknown/invalid fields and embeds references rather than secrets. Schema changes are versioned with backup, preflight and rollback/fail-closed behavior.

## Fitness rules and future checks
F01: inspect import graph: vendor SDK or concrete adapter import in domain fails. F02: application imports ports, not implementations; reverse dependency fails. F03: port tests run against each adapter and reject unsupported mandatory capabilities. F04: serialized domain interfaces contain neutral IDs, not vendor SDK objects. F05: config/secret diagnostic tests reject leaked sentinel values. F06: cancellation/timeout tests assert owned child/resource cleanup and durable evidence. F07: packaging installs in clean environment and CLI health/version works. F08: verification subprocess failures retain nonzero status.

These are specified future checks, not tests claimed to exist. Use unit tests for pure invariants, contract tests for adapters, targeted integration for real boundaries and end-to-end proof for sovereignty. Add tests for demonstrated risks/acceptance, not line-count targets or mirrored implementation. Node's scripts/check.mjs and existing regression results are baseline evidence, not Python fitness results.

## Traceability and acceptance

- **G06 — Python engineering standard**: Python standards cover src layout, typing, errors, async/resource management, packaging, migrations and test strategy; package naming follows approved contexts. Sources: Authority §§33,41; no dedicated Python standard.
- **G32 — architecture fitness rules**: Named automated fitness checks prohibit vendor dependencies and reversed layering, verify port contracts/config boundaries and preserve real failure exit statuses. Sources: Authority §39; scripts/check.mjs; test/check.test.mjs; policy checks.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
