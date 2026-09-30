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
5. Use PRODUCER, VERIFIER, REVIEWER and CLOSURE as role names. Model names are assignments supplied by the shared configuration, not architectural roles. The Founder may change those assignments.
6. Verification uses a separate invocation/workspace/context and exact candidate identity.
7. Deterministic/mechanical proof runs before expensive model review.
8. Prefer vertical slices that create demonstrable capability over horizontal infrastructure with no user-visible/provable outcome.
9. Do not carry forward a v1 mechanism unless the underlying requirement/invariant still justifies it.
10. Every v1 incident promoted into v2 becomes either an invariant, negative-control test, typed failure, or explicit non-goal.
11. No milestone is DONE until its end-to-end demonstration succeeds from a clean environment/restart boundary.
12. Work after the current milestone may be specified/prepared in parallel, but implementation priority follows this plan unless the Founder explicitly changes priority.

## 2.1 Existing connections, reliable facts and visible progress

Founder decisions, 2026-09-30:

- Python must use the exact same webhook, user accounts, GitHub App installation, repository, existing AlienIntent Project 1 board, and other external GitHub resources as the previous application. Read the actual protected settings and prove access to those resources; do not substitute example settings or create replacement infrastructure. The formal design, section 18.1, defines the required checks.
- Reliable facts for agents are part of the application, not an optional future convenience. The formal design, section 33.6, defines what an agent can ask, how answers identify their source and version, and how shared model assignments are supplied at launch and updated during operation. Use the existing assignment resolver where it fits; do not report the broader interface complete merely because that resolver exists.
- Every active work unit must have a real Issue on the existing board, with its actual stage, current owner, candidate code link, independent review result and specific blocker when waiting. An implementation repair returns to IMPLEMENT; independent review uses VERIFY. Passing checks do not authorize DONE before independent acceptance and separate closure.
- Keep the queue of Founder-inspected, independently checked and Agent Ready-approved work visible on that same board. Do not create a second backlog or a separate progress system.
- The approved first work unit is [Issue 153](https://github.com/AlienLogicLab/alienintent/issues/153). Its exact approved packet remains unchanged. It provides checked assessed work for a later queue-publishing step; it does not itself complete live queue publishing or the self-building milestone.

These requirements guide the missing connections on the shortest path. They do not authorize widening the already approved first implementation packet.

## 3. Milestone strategy

The first delivery target is a Python factory that can build AlienIntent under its own control. Reuse working Python code and implement only missing connections.

1. For the work immediately ahead, describe what it must do, which part of the application owns it, and how we will check it.
2. Run prepared and approved work through implementation and independent verification, with one active work item and recovery after a crash.
3. Prepare approved work from a requirement, including its description, plan, assessment and priority.
4. Complete real AlienIntent work, prove the intended result, finish it accurately, then restart and take the next eligible item automatically.
5. Complete the remaining replacement obligations, then perform the separately approved repository and publication changes.
6. Add broader product capabilities when justified.

The fourth step is the first credible self-building milestone. It requires preparation, real implementation, independent verification of the exact code, a proved outcome, and automatic continuation. Merely taking a second manually prepared item does not prove that the factory prepares its own work. Repository and publication changes remain later work; they are not a prerequisite to building Python.

The existing numbered milestone and work-unit identifiers below remain reference labels for their detailed requirements.

# M-1 — Repository Authority and Deterministic Publication Boundary (after Node retirement)

**Goal:** establish the private canonical engineering repository and curated public publication boundary after the Python factory builds itself and all AlienIntent Node duties are retired.

The current `AlienLogicLab/alienintent` identity remains in use through the self-building and retirement proofs. V2-000A begins the repository migration afterward.

### V2-000A — Contain canonical engineering authority: make current repository PRIVATE

Change `AlienLogicLab/alienintent` visibility from PUBLIC to PRIVATE while preserving repository identity, Issue numbers, Project relationships, branches, tags, GitHub App/webhook configuration and current v1 factory references.

This containment is the first repository migration action after accepted Node retirement.

Acceptance:
- GitHub reports the canonical repository PRIVATE;
- existing clone/remote identity is unchanged;
- no history rewrite;
- current Issues/Project/branches/tags remain intact;
- Python factory integrations remain capable of referencing the same repository identity.

### V2-000B — Post-visibility integration health proof

Immediately prove that making the canonical repository private did not break current operational integrations.

Verify at minimum:
- GitHub App installation/repository access;
- webhook delivery and authentication path;
- Project read/write;
- worker repository access for authorized identities;
- Python factory operator/control-plane read access;
- source-control fetch/push for authorized factory identities;
- relevant Actions/packages/release access if currently used.

Any failure is repaired as an integration/configuration defect; do not revert to public visibility as the normal fix.

### V2-000C — Publication classification and machine-readable allowlist

Make the Founder-approved classification model operational:

- `INTERNAL` — default;
- `PUBLIC_SOURCE`;
- `PUBLIC_DOCUMENTATION`.

Unknown/unclassified means INTERNAL. There is no denylist publication mode.

Deliver a versioned machine-readable allowlist/classification manifest rooted in the private canonical repository. The manifest is publication policy, not a manually remembered convention.

### V2-000D — Deterministic publication assembler

Build the smallest deterministic publication tool that consumes:

- exact private canonical revision;
- publication classification/allowlist;
- explicit publication configuration;

and produces an immutable public candidate.

Required pipeline:

```text
private canonical revision
  -> explicit allowlist/classification
  -> reject unknown/unclassified public candidates
  -> secret scan
  -> private-reference/internal-path scan
  -> public build/tests
  -> API/package compatibility checks where applicable
  -> immutable publication candidate
```

The assembler has no authority to publish by itself.

### V2-000E — Establish separate public publication repository

Create/configure a separate public publication target from a **fresh curated snapshot**, not from the full private Git object/history graph.

V2-000H owns the post-retirement identity migration and its Python integration readback. Create the public `AlienLogicLab/alienintent` target only after the private canonical identity has moved and the publication candidate passes review.

Public repository content is limited to explicitly approved artifacts such as:
- released source and appropriate public tests;
- README / LICENSE / CONTRIBUTING / SECURITY;
- installation and stable API/extension documentation;
- curated public architecture/contributor/security documentation;
- intentional releases/tags.

It excludes by default:
- requirements and internal design/architecture source documents;
- private ADRs/decisions;
- work units;
- factory evidence/trajectory;
- internal Issues/Project state;
- worker/candidate branches;
- Director records/prompts/model evaluations;
- private operations/continuity/migration material.

### V2-000F — Public surface and leakage audit

Audit both the now-private canonical repository and the new public publication surface.

Audit at minimum:
- repository tree;
- public history/object ancestry included in the publication candidate;
- branches and tags;
- Issues/Discussions/Wiki if enabled;
- releases;
- Actions logs/artifacts;
- packages;
- Pages;
- uploaded attachments;
- public documentation links/references;
- secrets/private references/internal path names;
- candidate/worker branch leakage.

The objective is future deterministic disclosure control, not an impossible claim that prior public copies/caches have been erased.

### V2-000G — Publication authority and repeatability proof

Add explicit publication authority after candidate assembly and prove:

- commit to private canonical repo != publication;
- publication requires explicit authority;
- same canonical revision + same publication policy produces the same public candidate;
- unknown classification fails closed;
- secret/private-reference failures prevent publication;
- worker/candidate branches are never mirrored;
- public Issues cannot directly create requirements/BIUs/execution authority;
- publication receipts record canonical revision, policy version, candidate identity and public target revision.

### V2-000H — Repository-identity migration after Node retirement

The target identity is settled: `AlienLogicLab/alienintent-internal` is the private canonical engineering repository; `AlienLogicLab/alienintent` is the curated public distribution repository created from a fresh approved snapshot.

After accepted Node retirement, inventory live Python repository references and exact evidence identities, freeze writers and checkpoint effects. Make the existing canonical repository private and verify integrations, then migrate the private canonical identity to `alienintent-internal`, reconfigure and read back Python webhooks, workers, Project access and Git remotes. Establish the public `alienintent` repository through the explicit allowlist/publication gate. A failed name or integration preflight is a typed blocker to resolve within M-1, not indefinite deferral.

**M-1 exit:**
- canonical engineering repository is PRIVATE;
- Python factory integrations remain healthy after visibility and identity changes;
- public publication is a separate configured target;
- publication is generated only by deterministic allowlist-based tooling from an exact private revision;
- first public candidate has passed secret/private-reference/build/API checks and manual review;
- internal Issues/Project/evidence/work units/worker branches are not public;
- publication authority is explicit and repeatable;
- the private canonical identity is `AlienLogicLab/alienintent-internal`, the curated public identity is `AlienLogicLab/alienintent`, and Python integrations pass readback after migration.

M-1 does not gate M0–M3 or the self-building proof. Its exit follows accepted Node retirement.

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

**M3 demonstration:** from a fresh installation, ingest one authorized AlienIntent requirement, specify/assess/prioritize its READY BIU, implement it in a real Git repository with a configured real worker, independently verify the exact candidate, land it, prove the required product outcome, project truthful DONE, recover across restart/fault injection and take the next eligible BIU without a manual lane edit.

**First self-building milestone:** M3 is the earliest point at which Python can credibly take an AlienIntent requirement through assessed READY work, real implementation, independent exact-candidate verification, landed outcome and truthful DONE, then recover and continue. M3 proves a narrow slice of production authority; it does not by itself retire every Node duty.

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

# M6 — Product Polish and Community Surfaces

**Goal:** finish optional/polished external product surfaces after the factory core is reliable. Publication foundations already exist from M-1; M6 extends them only where the finished product requires additional UX/integration polish.

### V2-601 — Factory dashboard

Build a read-oriented dashboard over Query ports for active/queued/completed work, WIP/capacity, workers, stage, elapsed time, costs, decisions, events and integration health. It owns no truth.

Requirements: SF-REQ-036.

### V2-602 — Installer/doctor product polish

Complete discovery, guided configuration, upgrades/migrations, rollback, noninteractive automation and external publication-target setup.

Requirements: SF-REQ-037/038.

### V2-603 — Opt-in community learning

Contribute generalized/anonymized evidence without proprietary code, secrets or sensitive project content; preserve explicit consent/revocation and trust boundaries.

Requirements: SF-REQ-033.

**M6 demonstration:** install AlienIntent, operate the factory, expose polished operator/community UX, and continue publishing intentional public releases through the deterministic M-1 publication boundary without exposing canonical engineering internals.

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
| SF-REQ-023 | V2-406; V2-000D/V2-000G where publication is a closure obligation |
| SF-REQ-024 | V2-403 |
| SF-REQ-025 | V2-303 foundation, V2-504 |
| SF-REQ-026 | V2-501–V2-504 |
| SF-REQ-027 | V2-505 |
| SF-REQ-028 | V2-403 |
| SF-REQ-029 | V2-403 |
| SF-REQ-030 | V2-403 |
| SF-REQ-031 | V2-506 |
| SF-REQ-032 | V2-503, V2-506 |
| SF-REQ-033 | V2-603 |
| SF-REQ-034 | V2-002, V2-106, V2-201, V2-202, V2-405 |
| SF-REQ-035 | V2-104, V2-205, V2-405 |
| SF-REQ-036 | V2-601 |
| SF-REQ-037 | V2-306, V2-602 |
| SF-REQ-038 | V2-003 foundation, V2-106, V2-306, V2-602 |
| SF-REQ-039 | V2-005, V2-107 |
| SF-REQ-040 | V2-005, V2-105, V2-107 |
| SF-REQ-055 | V2-204 foundation, V2-404 complete |
| SF-REQ-057 | V2-203, V2-204 |

# 5. Critical path

The capability path to Python self-building is M0's necessary contracts → M1 run prepared BIUs → M2 turn a requirement into an assessed READY BIU → M3 implement and independently verify in the real repository, recover and continue. Existing Python code and accepted predecessor BIUs are evidence to assess and reuse; V2-001–306 identify capability owners, not an instruction to rewrite functioning components or complete unrelated breadth first.

After M3, prove the remaining liveness, observation, admission, attention/mailbox, launcher/alias and bootstrap successors under the full Python-only cutover contract. **Node retirement precedes M-1.** V2-000A–H then establish repository authority and publication. M4–M6 add broader product capability as justified; their minimum quality requirements needed for truthful M3 closure are pulled into that gate.

# 6. Work-in-progress policy for building v2

During foundation construction:

- one implementation Work Unit is the default mutating WIP;
- next Work Units may be specified/reviewed/prepared ahead of the active unit;
- independent verification may overlap preparation but not compromise candidate custody;
- architectural changes discovered during implementation return to architecture authority before code continues;
- do not accumulate more than a small READY buffer until actual throughput demonstrates value.

The plan prioritizes correctness and low rework over artificial parallelism during M0–M3 and the later retirement/migration work.

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

The first implementation work is to assess the existing Python coordinator, persistence, GitHub backlog and real worker against the M0–M3 contracts. Identify the smallest missing connection for M1's prepared-work path, then prove M2's requirement-to-READY path and M3's real self-building run. Use bounded BIUs and independently verified receipts; do not recreate already working Python capabilities merely because a planned V2 unit has not been materialized as an Issue.

Once the Python factory builds itself, complete the remaining Node retirement gates. **Then** start M-1 with V2-000A. Repository migration is not a prerequisite to Python implementation or self-building.
