# AlienIntent v2 — Canonical Project Plan

Date: 2026-09-29  
Status: **Founder-directed canonical v2 planning baseline. Planning authority only; this document does not mutate or retire v1.**

Governing architecture: `docs/architecture/alienintent-factory-v2-formal-design.md`.

## 1. Objective

Build AlienIntent v2 feature-by-feature from a small deterministic foundation into a complete autonomous software factory while minimizing implementation surface, integration risk, and rework.

The optimization target is:

> **Minimum work for maximum verified capability.**

The desired operating character is efficient, elegant, refined, robust, resilient and reliable: Swiss-watch behavior produced by simple deterministic mechanisms, strong boundaries, explicit authority, and discriminating proof.

v1 is evidence and a requirements source, not an implementation template.

## 2. Delivery rules

1. Architecture and Ubiquitous Language precede implementation topology.
2. Every Work Unit maps to explicit `SF-REQ-*` requirements and architecture sections.
3. A Work Unit must produce one cohesive, independently verifiable increment.
4. No implementation agent invents architecture, product priority, or missing authority.
5. Claude Code is the default PRODUCER for the v2 foundation unless the Founder changes that policy.
6. Verification uses a separate invocation/workspace/context and exact candidate identity.
7. Deterministic/mechanical proof runs before expensive model review.
8. Prefer vertical slices that create demonstrable capability over horizontal infrastructure with no user-visible/provable outcome.
9. Do not carry forward a v1 mechanism unless the underlying requirement/invariant still justifies it.
10. Every v1 incident promoted into v2 becomes either an invariant, negative-control test, typed failure, or explicit non-goal.
11. No milestone is DONE until its end-to-end demonstration succeeds from a clean environment/restart boundary.
12. Work after the current milestone may be specified/prepared in parallel, but implementation priority follows this plan unless the Founder explicitly changes priority.

## 3. Milestone strategy

The milestones deliberately add capability in this order:

```text
M0  Architecture locked
        |
M1  Deterministic offline factory
        |
M2  Product intent -> READY through stable interfaces
        |
M3  Real single-project autonomous delivery
        |
M4  Production resilience + N projects + quality evidence
        |
M5  Local Factory Director cognition + adaptive allocation/learning
        |
M6  Publication/productization/community surfaces
```

Each milestone is useful on its own and reduces uncertainty for the next.

# M0 — Architecture Locked

**Goal:** make the domain, boundaries, contracts, engineering standards and conformance harness unambiguous before substantial v2 implementation.

### V2-001 — Ubiquitous Language and bounded-context ratification

Owns:
- audit `alienintent-ubiquitous-language-v0.1.md` against the canonical v2 architecture;
- remove stale v1/control-plane aliases from current v2 language;
- ratify context ownership and context map;
- preserve Agent Ready as an independent external bounded context.

Requirements: supporting architecture for all; especially SF-REQ-009/010/011/013/016/034.

### V2-002 — Hexagonal port/ACL contract freeze

Owns:
- neutral port signatures and typed outcomes;
- Query/Command/Event application ports;
- adapter capability/version contract;
- ACL rules and negative examples;
- no vendor/framework types inward.

Requirements: SF-REQ-005, 011, 015, 025, 034, 038.

### V2-003 — Python engineering and architecture-fitness baseline

Owns:
- `src/` package skeleton by bounded context;
- typing/lint/test configuration;
- dependency-direction checks;
- strict config/result/error conventions;
- async/resource rules;
- negative-control architecture tests.

Requirements: SF-REQ-018 plus architecture-wide implementation discipline.

### V2-004 — Canonical domain/state/event schema

Owns:
- WorkItem, Requirement, Dependency, Claim, Blocker, Candidate, Evidence, Effect, Decision;
- lifecycle enums and legal-transition table;
- command/result/event schemas;
- versioning/idempotency identity rules;
- canonical persistence contract.

Requirements: SF-REQ-007/008/009/010/016/017/020.

### V2-005 — Conformance harness + Deterministic Test Worker skeleton

Owns:
- pure transition/property harness;
- scripted valid/invalid workers over the real worker protocol;
- replayable fixtures for v1 failure classes;
- proven-red negative-control convention.

Requirements: SF-REQ-018, 039, 040.

**M0 exit:** a new developer/agent can derive the allowed dependency graph, lifecycle transitions, port contracts, schemas and proof rules without reading v1 implementation code.

# M1 — Deterministic Offline Factory

**Goal:** prove the core factory without GitHub, remote providers, REST, MCP or LLM cognition.

### V2-101 — SQLite canonical ledger and replay

Implement transactional event append + projection update, optimistic concurrency, WAL, replay equivalence and corruption detection.

Requirements: SF-REQ-008, 009, 016, 040.

### V2-102 — Pure transition kernel

Implement one lifecycle transition function and invariant enforcement. No network/process/provider calls.

Requirements: SF-REQ-009, 010, 016, 020.

### V2-103 — Deterministic scheduler, dependencies, priority, READY refill and WIP

Implement priority/FIFO, dependency eligibility, configurable WIP, rolling slot refill, no-idle invariants and queue projections.

Requirements: SF-REQ-001, 002, 003 foundation, 004, 009.

### V2-104 — Claims, blockers, decisions and bounded retries

Implement claim generations/leases, typed blockers, Decision records, authority-required handling, bounded retries and exhaustion.

Requirements: SF-REQ-006, 009, 022 foundation, 035 minimum.

### V2-105 — Effect intents, idempotency, restart recovery and provider-free replay

Implement PENDING/APPLIED/READ_BACK effects, unknown outcome fencing, crash/restart reconciliation and exact replay.

Requirements: SF-REQ-008, 040.

### V2-106 — Minimal CLI Operator Control Plane + doctor

Implement CLI `status`, `explain`, `health/doctor`, queue/claim/blocker/effect inspection and legitimate typed commands. No direct state editing.

Requirements: SF-REQ-034 minimum, 038 minimum.

### V2-107 — Deterministic Test Worker end-to-end lifecycle

Drive READY -> IMPLEMENT -> VERIFY -> ACCEPT -> DONE using the real kernel/claims/effects protocol with scripted workers.

Requirements: SF-REQ-001/004/039/040.

### V2-108 — Candidate custody + independent verifier protocol

Require immutable candidate identity/retrievability before VERIFY; verifier runs in independent assignment/workspace and returns typed verdict.

Requirements: SF-REQ-007, 021, 022 foundation.

**M1 demonstration:** from a clean local installation, feed several prebuilt BIUs with different priorities/dependencies into SQLite, run the deterministic factory with scripted producer/verifier workers, kill/restart it mid-flight, and prove exact eventual DONE order with no duplicate effects or lost obligations.

**M1 value:** the hardest control-plane behavior is proven before any external integration or LLM can obscure defects.

# M2 — Product Intent to READY Through Stable Interfaces

**Goal:** turn authorized product intent into bounded READY work through product-quality interfaces while preserving every obligation.

### V2-201 — Query/Command/Event application services + REST/OpenAPI v1

Expose canonical typed services and first network adapter. OpenAPI is generated/validated from stable schemas; no REST-specific domain logic.

Requirements: SF-REQ-034 minimum/API architecture; foundation for all external UX.

### V2-202 — MCP adapter v1

Expose the same supported Query/Command/Event capabilities to agents/tools through MCP. Contract equivalence tests prove REST/MCP/CLI share semantics.

Requirements: SF-REQ-034; architecture interface invariant.

### V2-203 — Requirement Source, Requirements IR, provenance and durable intake

Implement authorized capture, exact source retention, provenance, stable IDs, duplicate/supersession semantics, priority conservation and obligation-through-DONE behavior.

Requirements: SF-REQ-011, 012, 057.

### V2-204 — Requirements/UX intake slice

Build the first user-facing UX over the REST application surface: submit requirement/proposal, inspect interpretation/provenance, answer ambiguity/authority questions, and see `why waiting`/progress.

Requirements: SF-REQ-006/011/012/034/035/057; UX foundation for SF-REQ-055.

### V2-205 — Specification, Design Contract, Plan and Decision artifacts

Implement typed/versioned artifacts and authority transitions for SPECIFY/PLAN, plus Decision Inbox integration for genuine owner decisions.

Requirements: SF-REQ-006, 012, 035; architecture Design Contract discipline.

### V2-206 — BIU Compiler + obligation conservation/replan

Compile authorized Plan scope into BIUs and dependency DAGs; preserve obligations through split/replan with lineage and integration ownership.

Requirements: SF-REQ-010, 013.

### V2-207 — Agent Ready integration through `ReadinessAssessment` port

Integrate Agent Ready only through its public CLI/MCP contract; retain raw assessment + provenance; AlienIntent performs authority-bearing lifecycle mutation.

Requirements: SF-REQ-015.

### V2-208 — Mechanical obligations and architecture conformance before READY

Derive mechanically testable obligations before implementation and enforce architecture fitness/readiness preconditions.

Requirements: SF-REQ-014, 018.

**M2 demonstration:** submit a P0 requirement through REST or the requirements UX, preserve the exact input/provenance, resolve one deliberately ambiguous decision, produce specification/design/plan, compile BIUs, assess through Agent Ready, and obtain a correctly prioritized READY queue without hand-editing files or Project fields.

# M3 — Real Single-Project Autonomous Delivery

**Goal:** connect the proven core to a real repository/work-management system and real implementation/verification agents while retaining one-writer deterministic authority.

### V2-301 — GitHub WorkManagement projection adapter

Implement GitHub Projects/Issues as noncanonical projection/intake surfaces behind `WorkManagement`; enforce complete identity/membership/version readback and stale-write fencing.

Requirements: SF-REQ-005.

### V2-302 — SourceControl + Workspace adapters

Implement immutable revision/candidate operations and isolated workspace custody/cleanup with quiescence proof.

Requirements: SF-REQ-007, 008, 021.

### V2-303 — WorkerProvider adapter with Claude Code foundation path

Implement the provider-neutral worker protocol with Claude Code as the default v2 foundation producer configuration; preserve exact invocation/budget/context/capabilities.

Requirements: SF-REQ-025 foundation; implementation policy.

### V2-304 — Real Producer -> independent Verifier -> closure path

Execute an actual repository-changing BIU through immutable candidate publication, independent verification, acceptance, landing and DONE.

Requirements: SF-REQ-007/020/021/022/023 foundation.

### V2-305 — Live crash/fault injection and reconciliation

Kill/restart at transaction/effect/worker boundaries; prove no lost/duplicate work and exact custody recovery.

Requirements: SF-REQ-008, 020, 040.

### V2-306 — Minimal `alienintent init` and production doctor

Configure one project/profile, persistence, repository, work-management adapter and worker provider with convention-heavy defaults; fail closed before autonomous execution if health prerequisites are absent.

Requirements: SF-REQ-037 minimum, 038.

**M3 demonstration:** from a fresh installation, ingest one authorized requirement, produce READY work, implement it in a real Git repository with Claude Code, independently verify the exact candidate, land it, project state to GitHub and reach truthful DONE after restart/fault injection.

**First production milestone:** M3 is the earliest point at which v2 can credibly replace a narrow slice of v1 production authority.

# M4 — Production Resilience, N Projects and Quality Evidence

**Goal:** broaden from one proven vertical path to robust production operation without weakening the deterministic core.

### V2-401 — Profiles, N projects and bounded concurrency

Isolate project authority/state/evidence/configuration; support configurable concurrent independent streams while preserving per-project and global WIP invariants.

Requirements: SF-REQ-003.

### V2-402 — Verification quality controls

Implement requirement-evidence traceability, drift detection, fake-DONE prevention, architecture catches, bounded repair loops and known failure-class verification.

Requirements: SF-REQ-017/018/019/020/021/022.

### V2-403 — Engineering Trajectory, Quality Evidence, metrics and economics

Record observation/artifact/check/finding/repair lineage; derive consistent quality evidence and yield/cost/latency metrics with UNKNOWN preserved.

Requirements: SF-REQ-024/028/029/030.

### V2-404 — Proposal Intake product capability

Add immutable noncanonical proposal intake, validation/classification/deduplication and authority-controlled promotion to Requirement Candidate/Requirement.

Requirements: SF-REQ-055.

### V2-405 — Full Operator Control Plane and Decision Inbox

Complete replay/resume/reconcile/cancel diagnostics, event inspection, workers/invocations/evidence/cost/capability/transport/adapter views and durable decisions over REST/MCP/CLI.

Requirements: SF-REQ-034/035.

### V2-406 — Product/outcome closure verification

Add typed deployment/API/browser/SLO/release/publication outcome predicates as optional closure obligations rather than conflating task completion with outcome success.

Requirements: SF-REQ-023.

### V2-407 — v1 shadow conformance and migration ledger

Mirror real v1 inputs/outcomes into v2 read-only shadow execution; classify every semantic divergence; reconcile open obligations before any one-writer cutover.

Requirements: migration proof supporting all P0/P1 semantics.

**M4 demonstration:** operate multiple projects/profiles with bounded concurrency, survive faults, explain every block/queue decision, retain evidence and metrics, and produce no unexplained v1/v2 semantic divergence in the accepted conformance set.

# M5 — Local Factory Director Cognition, Allocation and Learning

**Goal:** add cognition only after deterministic state, interfaces and evaluation packets exist.

### V2-501 — Normalized Director cognition packet + CognitionPort

Create the smallest provenance-bearing state packet sufficient for Factory Director interpretation/proposals; no raw repository/history dump and no mutation authority.

Requirements: supports SF-REQ-026/031/032/034/035.

### V2-502 — Local Director benchmark: Qwen3.5-9B vs Stanford/NVIDIA CLM-8B

Build versioned replay corpus from real Director episodes and evaluate exact state reconstruction, legal action selection, authority restraint, blocker classification, output-contract adherence, recovery quality, latency, compute efficiency, repeated-action reuse/cache benefit and escalation rate.

Requirements: SF-REQ-026 plus v2 cognition architecture.

### V2-503 — Shadow Factory Director

Run the selected local model shadow-only on live canonical packets; compare proposed actions against deterministic outcomes and human/frontier reference where cognition is actually required.

Requirements: SF-REQ-026/032/034/035.

### V2-504 — Provider capability discovery + cognizant Allocator

Add capability/readiness discovery and cheapest-capable allocation using measured task/model evidence. Deterministic rules settle trivial cases; local cognition handles bounded nontrivial choice.

Requirements: SF-REQ-025/026.

### V2-505 — Source intelligence

Add provider-neutral structural source intelligence behind ports for bounded relevant-code context.

Requirements: SF-REQ-027.

### V2-506 — Evidence-derived routing learning and proposal governance

Derive model/provider recommendations from quality/economics evidence; emit cited Learning Proposals only; no autonomous policy mutation.

Requirements: SF-REQ-031/032.

**M5 demonstration:** the selected local Director model operates in shadow with materially lower cost/latency than frontier cognition, zero violations of deterministic policy, and sufficient quality to receive bounded proposal authority for explicitly selected cognitive decisions.

# M6 — Publication, Productization and Community Surfaces

**Goal:** finish external product surfaces only after the factory core is reliable.

### V2-601 — Publication classification + allowlist assembler

Implement INTERNAL/PUBLIC_SOURCE/PUBLIC_DOCUMENTATION classification, fail-closed allowlist assembly, secret/private-reference scanning, public build/test/API checks and immutable publication candidates.

Requirements: canonical v2 publication architecture.

### V2-602 — Separate public repository publication adapter

Publish an explicitly authorized fresh curated snapshot/release without worker branches/internal Issues/Project/work units/evidence/private history.

Requirements: publication architecture; SF-REQ-023 where publication is an outcome obligation.

### V2-603 — Factory dashboard

Build a read-oriented dashboard over Query ports for active/queued/completed work, WIP/capacity, workers, stage, elapsed time, costs, decisions, events and integration health. It owns no truth.

Requirements: SF-REQ-036.

### V2-604 — Installer/doctor product polish

Complete discovery, guided configuration, upgrades/migrations, rollback, noninteractive automation and external publication-target setup.

Requirements: SF-REQ-037/038.

### V2-605 — Opt-in community learning

Contribute generalized/anonymized evidence without proprietary code, secrets or sensitive project content; preserve explicit consent/revocation and trust boundaries.

Requirements: SF-REQ-033.

**M6 demonstration:** install AlienIntent, operate the factory, expose polished operator UX, and publish an intentional public distribution repository entirely from deterministic publication policy without exposing canonical engineering internals.

# 4. Active requirement coverage

Every active canonical requirement is assigned. SF-REQ-054 is retired and intentionally excluded.

| Requirement | Primary delivery Work Unit(s) |
|---|---|
| SF-REQ-001 | V2-103, V2-107 |
| SF-REQ-002 | V2-103 |
| SF-REQ-003 | V2-103 foundation, V2-401 complete |
| SF-REQ-004 | V2-103 |
| SF-REQ-005 | V2-002, V2-301 |
| SF-REQ-006 | V2-104, V2-205 |
| SF-REQ-007 | V2-004, V2-108, V2-302 |
| SF-REQ-008 | V2-101, V2-105, V2-305 |
| SF-REQ-009 | V2-004, V2-102, V2-103 |
| SF-REQ-010 | V2-004, V2-108, V2-206 |
| SF-REQ-011 | V2-203 |
| SF-REQ-012 | V2-203, V2-205 |
| SF-REQ-013 | V2-206 |
| SF-REQ-014 | V2-208 |
| SF-REQ-015 | V2-207 |
| SF-REQ-016 | V2-004, V2-101, V2-102 |
| SF-REQ-017 | V2-402 |
| SF-REQ-018 | V2-003, V2-208, V2-402 |
| SF-REQ-019 | V2-402 |
| SF-REQ-020 | V2-102, V2-402 |
| SF-REQ-021 | V2-108, V2-304, V2-402 |
| SF-REQ-022 | V2-104 foundation, V2-402 |
| SF-REQ-023 | V2-406, V2-602 where publication applies |
| SF-REQ-024 | V2-403 |
| SF-REQ-025 | V2-303 foundation, V2-504 |
| SF-REQ-026 | V2-501–V2-504 |
| SF-REQ-027 | V2-505 |
| SF-REQ-028 | V2-403 |
| SF-REQ-029 | V2-403 |
| SF-REQ-030 | V2-403 |
| SF-REQ-031 | V2-506 |
| SF-REQ-032 | V2-503, V2-506 |
| SF-REQ-033 | V2-605 |
| SF-REQ-034 | V2-002, V2-106, V2-201, V2-202, V2-405 |
| SF-REQ-035 | V2-104, V2-205, V2-405 |
| SF-REQ-036 | V2-603 |
| SF-REQ-037 | V2-306, V2-604 |
| SF-REQ-038 | V2-003 foundation, V2-106, V2-306, V2-604 |
| SF-REQ-039 | V2-005, V2-107 |
| SF-REQ-040 | V2-005, V2-105, V2-107 |
| SF-REQ-055 | V2-204 foundation, V2-404 complete |
| SF-REQ-057 | V2-203, V2-204 |

# 5. Critical path

The shortest path to a trustworthy autonomous v2 factory is:

```text
V2-001 -> V2-002 -> V2-003 -> V2-004 -> V2-005
                                         |
                                         v
V2-101 -> V2-102 -> V2-103 -> V2-104 -> V2-105
                         |                 |
                         v                 v
                      V2-107 <- V2-108 <-+
                         |
                         v
V2-201 -> V2-203 -> V2-205 -> V2-206 -> V2-207 -> V2-208
   |          |
V2-202     V2-204
                         |
                         v
V2-301 -> V2-302 -> V2-303 -> V2-304 -> V2-305 -> V2-306
```

M4–M6 build on that proven spine. Do not pull later sophistication onto the critical path unless it removes a demonstrated blocker.

# 6. Work-in-progress policy for building v2

During foundation construction:

- one implementation Work Unit is the default mutating WIP;
- next Work Units may be specified/reviewed/prepared ahead of the active unit;
- independent verification may overlap preparation but not compromise candidate custody;
- architectural changes discovered during implementation return to architecture authority before code continues;
- do not accumulate more than a small READY buffer until actual throughput demonstrates value.

The plan intentionally prioritizes correctness and low rework over artificial parallelism during M0/M1.

# 7. Definition of milestone completion

A milestone is DONE only when:

1. every Work Unit mapped to the milestone is accepted or explicitly superseded by an equally authoritative plan revision;
2. the milestone demonstration passes from a clean environment/profile;
3. architecture fitness passes;
4. negative controls prove the milestone's critical invariants can fail;
5. requirement coverage/evidence is mechanically traceable;
6. no unresolved blocker is hidden by a status label;
7. the next milestone can consume the resulting interfaces without reaching into implementation internals.

# 8. First action

The first v2 implementation work is **V2-001**, not a runtime port and not a model integration.

Before Claude Code writes substantial v2 code, M0 must freeze the Ubiquitous Language/context map, port contracts, Python engineering baseline, canonical domain/event schema and conformance harness.

That is the smallest investment most likely to prevent a second v1.
