# Pre-Python gate matrix

All 34 binding rows are preserved verbatim. Initial classification records the inventory result; candidate documents do not retroactively become approved artifacts. PASS here is design-authority coverage, not Python implementation proof. Final admission status is in gate-report.md.

FD-01 update: the upstream Work Management / released AlienIntent Execution split is now [binding](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md). Initial classifications below remain the historical inventory result; ownership is no longer an unanswered choice. Candidate completeness and remaining approvals still govern each whole gate row.

## G01 — Product Intent

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [product-intent.md](product-intent.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: reset §§2–13,39–40; current-strategy; canonical-architecture; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Purpose, users, outcomes and non-goals are explicit; repository-neutral early intent and N-repository work are represented; upstream planning is not reimplemented.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-01](../../work-units/pre-python-gate/PG-01.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Product intent stays canonical upstream; execution outcomes and evidence become canonical in AlienIntent only after explicit READY-BIU release.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G02 — Ubiquitous Language v1

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [domain-model.md](domain-model.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: reset §§15–18,21,26–30; EOS ADR-0004 and ontology; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Terms have one definition, examples/non-examples and ownership; BIU remains; domain roles are not external users; EOS mapping preserves project language.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-02](../../work-units/pre-python-gate/PG-02.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Work Item imports are noncanonical views; released BIU, execution identity and downstream projection are distinct terms.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G03 — bounded-context model

- Initial classification: **FOUNDER DECISION REQUIRED**.
- Artifact to satisfy the gate: [domain-model.md](domain-model.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§7,8,41; canonical-architecture responsibility list; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Each business invariant has exactly one owning context, aggregates and identities are explicit, dependencies and integration seams form a coherent context map with Founder-approved boundaries.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-02](../../work-units/pre-python-gate/PG-02.md), assessed READY before drafting.
- FD-01 acceptance/refinement: The two ownership contexts are approved and not configurable. FD-02 concerns internal decomposition/aggregates only.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G04 — Hexagonal Architecture / ports-and-adapters specification

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [hexagonal-contracts.md](hexagonal-contracts.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§3,17,29,41; interface-contracts; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Core/domain dependency direction and named input/output port contracts include success, rejection and unavailable evidence; no vendor types leak inward.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-03](../../work-units/pre-python-gate/PG-03.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Ports must distinguish upstream imports, explicit release and downstream projections from execution commands.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G05 — Anti-Corruption Layer rules

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [hexagonal-contracts.md](hexagonal-contracts.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§3,8,17; src/github/authority.mjs; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: GitHub and a non-GitHub example map external IDs/status/events/errors to domain concepts and fail closed on ambiguous or incomplete translations.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-03](../../work-units/pre-python-gate/PG-03.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Vendor downstream edits/projection echoes never acquire execution authority; configurable mappings preserve the fixed split.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G06 — Python engineering standard

- Initial classification: **MISSING**.
- Artifact to satisfy the gate: [python-engineering.md](python-engineering.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§33,41; no dedicated Python standard; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Python standards cover src layout, typing, errors, async/resource management, packaging, migrations and test strategy; package naming follows approved contexts.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-04](../../work-units/pre-python-gate/PG-04.md), assessed READY before drafting.

## G07 — BIU/domain execution model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [work-and-release.md](work-and-release.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: docs/templates/work-packet.md; interface-contracts; B-DISP BIU history; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: BIU binds authority, immutable requirements/baseline/candidate, bounded scope, dependencies, capabilities, budget, required evidence and terminal/rework outcomes.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-05](../../work-units/pre-python-gate/PG-05.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Release binds exact upstream READY BIU version and authority; post-release edits cannot silently replace it.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G08 — lifecycle semantics and external mapping rules

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [work-and-release.md](work-and-release.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: src/domain/lifecycle.mjs; lifecycle correction; reset §§27–30; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: All ten semantic states are defined, mapping is explicit and unambiguous, dispatch is distinct from lifecycle, merge belongs to closure, accepted-result-changing rework invalidates acceptance.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-05](../../work-units/pre-python-gate/PG-05.md), assessed READY before drafting.
- FD-01 acceptance/refinement: CAPTURE–READY remain upstream; IMPLEMENT–DONE/closure are AlienIntent execution; external downstream fields are projections.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G09 — automatic-release policy model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [work-and-release.md](work-and-release.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §10; Node IMPLEMENT admission (not automatic READY release); exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: READY is insufficient authorization; ON and OFF have observable guards, authority provenance and deterministic denial; duplicate release cannot double-launch.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-05](../../work-units/pre-python-gate/PG-05.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Automatic ON and human OFF both emit an explicit authorized release; explicit does not mean mandatory human-only.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G10 — verifier-independence / assurance-policy model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [capabilities-and-assurance.md](capabilities-and-assurance.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§4,5,11; worker-runner/worktree manager; Issue1 JC proof; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Separate invocation/worktree/context/provenance and immutable candidate prevent self-approval; assurance can strengthen controls without mandatory account/provider differences.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-06](../../work-units/pre-python-gate/PG-06.md), assessed READY before drafting.

## G11 — capability/authority model, including live deployment authority

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [capabilities-and-assurance.md](capabilities-and-assurance.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§13–14,45; bootstrap-only JC exception (not canonical model); exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Grant records name BIU/worker/target/actions/limits/expiry/revocation; authorized live changes require post-action evidence; rejected/cross-target actions have defined behavior.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-06](../../work-units/pre-python-gate/PG-06.md), assessed READY before drafting.

## G12 — optional sandbox/container model

- Initial classification: **MISSING**.
- Artifact to satisfy the gate: [capabilities-and-assurance.md](capabilities-and-assurance.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §12; no dedicated sandbox design; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Unsandboxed trusted and Linux-native/container-backed policies are explicit; capabilities and credential handling remain controlled; sandbox failure never silently falls back.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-06](../../work-units/pre-python-gate/PG-06.md), assessed READY before drafting.

## G13 — event-ingress port and direct-webhook/outbound-relay adapters

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [event-ingress.md](event-ingress.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §3; bin/alienintent.mjs; Issue1 webhook proof; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Direct and outbound relay adapters share a profile-scoped ingress contract, authenticity and acknowledgment semantics; relay reconnect uses durable replay without polling.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-07](../../work-units/pre-python-gate/PG-07.md), assessed READY before drafting.

## G14 — no-polling / async integration rule

- Initial classification: **PASS**.
- Artifact to satisfy the gate: [event-ingress.md](event-ingress.md); binding authority takes precedence. Existing Authority §21 and D10 directly satisfy this rule.
- Supporting evidence: Authority §21; B-DISP D10; dispatcher event paths; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Architectural integration uses events/asynchronous operations; polling has no normal path; exceptional timed retries are bounded and are not disguised polling.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-07](../../work-units/pre-python-gate/PG-07.md), assessed READY before drafting.

## G15 — internal event model and once-only processing semantics

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [event-ingress.md](event-ingress.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: dispatcher.mjs; github-authority tests; Issue1 replay evidence; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Domain events include identity/schema/profile/causation/invocation/version; duplicates/delay/reorder/crash scenarios yield effectively once-only effects with durable evidence.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-07](../../work-units/pre-python-gate/PG-07.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Separate upstream notifications/release commands/internal execution events/projection receipts; duplicates and echoes cannot double-admit.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G16 — concurrency/cancellation/retry policy

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [scheduling-and-recovery.md](scheduling-and-recovery.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: dispatcher/worktree-manager; worktree-lifecycle tests; B-DISP D17,D18,D31; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Global/profile/repository bounds, atomic reservations, cancellation and finite retry budgets prevent double mutation and preserve live/ambiguous resources on recovery.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-08](../../work-units/pre-python-gate/PG-08.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Admission/recovery use internal accepted release/ownership evidence; stale external display cannot re-admit work.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G17 — provider capability/routing contract

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [providers-and-budgets.md](providers-and-budgets.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: B-DISP capability-based-provider-compatibility decision; src/providers; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Provider contract advertises required capabilities/version evidence; known/novel/incompatible versions have probe-based admission and normalized outcomes.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-09](../../work-units/pre-python-gate/PG-09.md), assessed READY before drafting.

## G18 — cheapest-capable / local-first routing policy

- Initial classification: **PASS**.
- Artifact to satisfy the gate: [providers-and-budgets.md](providers-and-budgets.md); binding authority takes precedence. Existing Authority §23 and the model-selection decision directly satisfy this policy.
- Supporting evidence: Authority §23; B-DISP model-selection-cost-quality decision; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Selection optimizes cost subject to demonstrated quality; capable local models preferred; stale/insufficient evidence cannot invent rankings or permanent model hierarchy.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-09](../../work-units/pre-python-gate/PG-09.md), assessed READY before drafting.

## G19 — Context Engineering v1 carried forward

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [context-and-memory.md](context-and-memory.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: B-DISP near-term-scope §§4–6; canonical-architecture context compiler; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Six context kinds, static/dynamic split, role/phase selection, versions/provenance, budgets, skills and measurements are carried forward with independent verifier inputs.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-10](../../work-units/pre-python-gate/PG-10.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Context manifests distinguish upstream source versions from pinned released authority; a refreshed import does not supersede execution.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G20 — memory/state/evidence separation carried forward

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [context-and-memory.md](context-and-memory.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §25; near-term-scope §4.3; trajectory source §17; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Operational state, task context, engineering knowledge, organizational knowledge, trajectory, Quality Evidence and learned policy have separate ownership/lifetimes/retrieval.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-10](../../work-units/pre-python-gate/PG-10.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Imported upstream context is not canonical product state; execution state/trajectory/evidence remain separately owned.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G21 — operational-state persistence design

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [persistence-and-evidence.md](persistence-and-evidence.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§15–16; src/config/state-compatibility.mjs; Node JSON snapshots; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: SQLite and PostgreSQL honor the same transaction/identity/recovery semantics, namespace profiles and separate durable evidence lifetimes from operational cleanup.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-11](../../work-units/pre-python-gate/PG-11.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Execution store is authoritative for released control state; imports/cache and projection receipts cannot overwrite it.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G22 — Engineering Trajectory / Quality Evidence persistence design

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [persistence-and-evidence.md](persistence-and-evidence.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: north-star amendment §§8–13; trajectory source §§4–17; Node logs; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Trajectory facts and derived multidimensional measurements/findings/interventions/outcomes have stable lineage, immutable accepted evidence, configurable retention/redaction and no private reasoning requirement.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-11](../../work-units/pre-python-gate/PG-11.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Engineering Trajectory and Quality Evidence are canonical AlienIntent execution evidence, not provider projections.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G23 — community-learning contribution model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [community-learning.md](community-learning.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: community-evidence-commons; community-evidence-service architecture; Authority §28; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Contribution is OFF by default and separate from private records, consent and sanitization are explicit, no opt-out penalty, poisoning/retention/query controls do not become automatic authority.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-12](../../work-units/pre-python-gate/PG-12.md), assessed READY before drafting.

## G24 — cost/token governance

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [providers-and-budgets.md](providers-and-budgets.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §22; historical D08,D16; sanitized subscription worker auth; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: BIU/project/deployment/retry hard limits apply at actual launch/tool boundaries; reservations and uncertain consumption cannot overspend; costs are attributable and billing claims qualified.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-09](../../work-units/pre-python-gate/PG-09.md), assessed READY before drafting.

## G25 — operator Control Plane application model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [control-plane.md](control-plane.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: canonical-architecture Operator surface; implementation-plan phases1–6; Authority §36; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Operator status/explain/emit/replay/resume/reconcile/cancel/doctor act through normal application/domain services and authorization; no state-edit backdoor.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-13](../../work-units/pre-python-gate/PG-13.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Status/explain label upstream truth, internal execution truth and projection health; reconcile cannot import external ACCEPT/DONE as truth.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G26 — control-plane presentation adapters (CLI/web as approved)

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [control-plane.md](control-plane.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: interface-contracts Operator; Authority §§33,37; bin/alienintent.mjs limited CLI; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: CLI exposes approved operations and machine-readable diagnostics; any web surface uses same services/policies, with explicit approval status and no hidden permissions.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-13](../../work-units/pre-python-gate/PG-13.md), assessed READY before drafting.
- FD-01 acceptance/refinement: CLI/web adapters expose the same ownership distinction and validated execution commands; no presentation becomes authority.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G27 — adapter versioning/extensibility model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [hexagonal-contracts.md](hexagonal-contracts.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§29–30; provider compatibility decision; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Versioned ports advertise capability/compatibility with conformance rejection; third-party replacement possible; two implementations required before API stability claim.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-03](../../work-units/pre-python-gate/PG-03.md), assessed READY before drafting.

## G28 — configuration and SecretProvider model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [configuration-and-installation.md](configuration-and-installation.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: src/config/profile.mjs; config/profile.example.json; Authority §§31–32; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Typed profiles isolate state/queues/workspaces/evidence/secrets; secrets referenced through a port; discovery validates rather than guesses provider IDs.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-14](../../work-units/pre-python-gate/PG-14.md), assessed READY before drafting.
- FD-01 acceptance/refinement: No profile setting can choose lifecycle ownership; vendor/release-source/lifecycle/projection mappings remain configurable.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G29 — installer/bootstrap design

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [configuration-and-installation.md](configuration-and-installation.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§33–34,38; operations.md; historical manual self-hosting setup; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Init/install lifecycle covers discovery/authorization/providers/transport/lifecycle/health, resumable steps and rollback, automation and active-work-safe upgrades.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-14](../../work-units/pre-python-gate/PG-14.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Init validates the fixed split and rejects adapters/mappings that use downstream display edits as execution authorization.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G30 — observability model

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [control-plane.md](control-plane.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §35; streaming worker logs, diagnostics, Issue1 evidence; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Structured logs/readiness/health/timelines/metrics/provider cost/lifecycle and sanitized diagnostics correlate to BIU/invocation without exposing credentials or private reasoning.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-13](../../work-units/pre-python-gate/PG-13.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Diagnostics distinguish upstream availability from valid internal execution state and projection delivery failure.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G31 — EOS inheritance/contribution mechanism

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [eos-inheritance.md](eos-inheritance.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: EOS Constitution, ontology, ADR0004, knowledge lifecycle, evidence chains and engineering discipline; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: EOS commit and artifact statuses are pinned; inheritance/translation and evidence-linked contribution review are explicit; no automatic promotion of unreviewed proposals.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-15](../../work-units/pre-python-gate/PG-15.md), assessed READY before drafting.

## G32 — architecture fitness rules

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [python-engineering.md](python-engineering.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §39; scripts/check.mjs; test/check.test.mjs; policy checks; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Named automated fitness checks prohibit vendor dependencies and reversed layering, verify port contracts/config boundaries and preserve real failure exit statuses.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-04](../../work-units/pre-python-gate/PG-04.md), assessed READY before drafting.

## G33 — Node→Python coexistence/conformance strategy

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [conformance-and-sovereignty.md](conformance-and-sovereignty.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §§42–43; Node source/test suites; B-DISP extraction/migration records; exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Node/Python coexistence has per-invariant parity/adapt/deviation mapping, isolated environments, one operational writer, migration backups and rollback; Node remains authority.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-16](../../work-units/pre-python-gate/PG-16.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Node external-Project execution authority is preserved bootstrap behavior but intentionally not the canonical target ownership model.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.


## G34 — Python Sovereignty acceptance criteria

- Initial classification: **PARTIAL**.
- Artifact to satisfy the gate: [conformance-and-sovereignty.md](conformance-and-sovereignty.md); binding authority takes precedence. Candidate design now exists; adoption and applicable Founder decisions remain unresolved.
- Supporting evidence: Authority §43; Issue1 proof and regression evidence (Node only); exact corpus baselines and file paths are in inventory.md/artifact-manifest.json.
- Acceptance: Python-only live self-hosting, behavioral conformance, recovery, operator actions, evidence and learning all have named required proofs; no Node invocation and explicit retirement approval.
- Agent-Ready verification: Agent-Ready checks a self-contained packet containing binding authority, gate row, relevant EOS constraints, cited Node scenarios and this acceptance criterion; author checks source links and scenario completeness. READY is task readiness, not Founder approval or executable Python proof.
- Design BIU: [PG-16](../../work-units/pre-python-gate/PG-16.md), assessed READY before drafting.
- FD-01 acceptance/refinement: Sovereignty cases require READY-release handoff and resistance to projection echoes/drift without duplicate execution.
- PG-17 verification: check the corresponding explicit release/projection/authority scenario in the refined candidate against the binding FD-01 record; no runtime proof or complete artifact approval is implied.
