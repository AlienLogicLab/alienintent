# Conformance And Sovereignty — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-16](../../work-units/pre-python-gate/PG-16.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

Ownership refinement: [binding FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md), applied through [PG-17](../../work-units/pre-python-gate/PG-17.md). FD-01 is approved; other design choices remain candidate.

## Coexistence and behavior inventory
Node remains frozen except critical bootstrap fixes and remains operational authority. Python will coexist in this repository after this gate is released. No Python scaffold or implementation BIU exists in this work. Shared conformance cases should express neutral inputs/expected effects, exercised separately against Node adapters and Python adapters; do not port Node's incidental internal structure.

Retain: authenticated exact invocation/role result; immutable candidate review; complete authority readback; reserve-before-await/durable ownership; duplicate/replay protection; restart durable-result recovery; safe resource cleanup; ACCEPT versus DONE; material closure rework; truthful secret-safe diagnostics. Adapt: GitHub event/comment protocol to ACLs, fixed external identities to domain role bindings, JSON snapshots to approved persistence, three dispatched phases to lifecycle-aware policy without forcing all ten to spawn workers. Preserve compatibility markers/IDs while Node runs. Never give both implementations mutation authority over the same profile.

## Required sovereignty proof matrix
S1: neutral behavior suite includes valid/forged/stale/wrong-role/multiple results, concurrent duplicates, out-of-order events, crash boundaries and ambiguous authority. S2: Python-only fresh install plus PRODUCER→VERIFIER→closure→DONE live self-hosting with exact candidate evidence. S3: restart/replay/cancel/retry/reconcile at each durable boundary creates no duplicate effect or lost owner. S4: operator CLI status/explain/emit/replay/resume/cancel/doctor uses real application/event paths and denies unauthorized mutation. S5: trajectory and multidimensional Quality Evidence persist/retrieve with redaction, retention and provenance; one reviewed learning proposal links evidence to a controlled measured experiment without private reasoning or automatic policy adoption. S6: profile/repository isolation, capabilities, hard budgets and provider compatibility are enforced at real boundaries. S7: installation/upgrade/migration backup and rollback preserve known-good operation.

Each proof records revision/config/policy/provider versions, inputs, actual commands/events, outputs and independent verification. Mocks alone cannot establish live sovereignty. Instrument process/dependency paths to prove no Node invocation is required. Test-suite existence, parity percentage or local commit alone cannot justify retirement.

## Cutover and rollback
Before cutover, quiesce/settle owned work, checkpoint Node state/evidence, validate migration and exact profile ownership; activate only the approved Python writer and verify. On failed required proof retain/restore the Node authority from compatible checkpoint without replaying already-confirmed external effects. Founder approves cutover/Node retirement only after all sovereignty evidence passes. Issue1 demonstrates the Node reference path, not any of S1–S7 for Python. FD-01 has settled the architectural authority split; FD-05 and the remaining gate work still govern persistence/migration mechanisms before any implementation BIU can be prepared.

## Intentional authority change and shared conformance limits

Node currently uses external Project execution state and exact GitHub readback. Preserve that behavior operationally until approved cutover; do not call it the target canonical ownership model. Python conformance must preserve authenticated/correlated authority and no-duplicate-effect invariants while intentionally changing the execution-state owner under FD-01. Whole-lifecycle external authority is not a parity requirement. Upstream Work Management remains canonical in both target design and migration scope; importing historical released work never makes AlienIntent the product-backlog owner.

Add canonical-target scenarios: (1) READY without release starts no execution; (2) duplicate valid release returns one execution identity; (3) automatic ON generates the same explicit release boundary as human OFF; (4) external ACCEPT/DONE edits and projection echoes do not advance/duplicate execution; (5) post-release upstream edits do not rewrite pinned execution scope; (6) external outage/stale projection preserves committed execution truth and truthful delivery diagnostics; (7) reordered projection writes cannot overwrite a newer displayed execution revision; (8) profiles/vendors cannot select another ownership mode. These are future design/conformance obligations, not newly passed runtime tests.

Before any cutover, identify each active/released BIU and its exact authority/candidate/result lineage; settle or explicitly migrate it with one execution writer. Do not backfill an internal ACCEPT/DONE solely from a board label. Rollback must account for accepted external effects and new internal authoritative execution evidence; never resume Node on a stale snapshot that would duplicate effects or regress authority.

## Traceability and acceptance

- **G33 — Node→Python coexistence/conformance strategy**: Node/Python coexistence has per-invariant parity/adapt/deviation mapping, isolated environments, one operational writer, migration backups and rollback; Node remains authority. Sources: Authority §§42–43; Node source/test suites; B-DISP extraction/migration records.
- **G34 — Python Sovereignty acceptance criteria**: Python-only live self-hosting, behavioral conformance, recovery, operator actions, evidence and learning all have named required proofs; no Node invocation and explicit retirement approval. Sources: Authority §43; Issue1 proof and regression evidence (Node only).

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
