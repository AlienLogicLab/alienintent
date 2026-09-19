# Event Ingress — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-07](../../work-units/pre-python-gate/PG-07.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

Ownership refinement: [binding FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md), applied through [PG-17](../../work-units/pre-python-gate/PG-17.md). FD-01 is approved; other design choices remain candidate.

## Common ingress contract
Both direct webhook and outbound relay yield a neutral envelope with event ID, schema version, profile/work/BIU references, invocation/causation/correlation when applicable, occurrence/receipt time, authenticated source provenance, expected state/version and payload reference. Unknown profile, ambiguous routing, invalid authenticity or unsupported required version reject before domain action. Vendor headers/signatures remain adapter responsibilities.

Direct ingress validates raw-body authenticity and routes to the exact configured profile. Node's HMAC raw-byte check and public valid202/invalid401/tampered401 are behavioral evidence; HTTP path/header conventions are adapter-specific. Outbound relay uses authenticated outbound connection, durable event identities and resume cursor/acknowledgment. No hosted ALL dependency and no normal polling loop. Relay ownership/authentication/custody details require the FD-04 deployment decision before an operational adapter contract is final.

## Durable processing design
Candidate design: persist authenticated receipt and payload reference before acknowledging durable custody; process with idempotency key and expected aggregate version; persist resulting domain change plus an effect intent; effect adapter executes/reconciles with the same identity and records confirmed receipt. Duplicate event returns prior receipt. Reordered stale-version event does not roll work backward; it is rejected or retained for bounded reconciliation using authoritative evidence. FD-01 fixes ownership: internal transactions affect execution control; upstream snapshots retain external provenance and are not canonical product state. FD-05 still determines the concrete transaction/fencing implementation.

## Crash/replay cases
Crash before receipt persistence: no positive custody acknowledgment; sender may retry. Crash after persistence/before action: replay same ID, no duplicate admission. Crash after external effect/before recording its receipt: inspect exact external effect identity/readback, do not blindly repeat. Unknown effect outcome remains unresolved and blocks a conflicting mutation. Missing or forged invocation/role cannot advance lifecycle. Physically exactly-once network delivery is not promised.

Bounded reconnect/backoff is not permission to periodically list a remote backlog for integration. Operator replay enters this same contract with authenticated operator provenance and authorization; it cannot edit persisted state directly.

## Event categories and projection-loop guard

Distinguish upstream product-change notifications, explicit READY release commands, internal execution events and downstream projection receipts/echoes. Upstream events refresh a noncanonical view. Only an authorized validated release creates an execution; subsequent transitions require AlienIntent execution authority. A vendor event reporting an edited execution display is drift, not proof of an internal lifecycle transition.

Persist source and projection provenance alongside execution identity/revision so echoes cannot be reinterpreted as releases or new work. Authentication proves sender identity, not permission to cross the wrong ownership boundary. Duplicate releases and repeated projection callbacks are idempotent in their own namespaces; delayed callbacks cannot regress current execution or acknowledge the wrong revision. During provider outage preserve internal execution truth and expose bounded projection retries/uncertainty; required unavailable upstream READY evidence prevents a new release. No external workflow polling is introduced.

## Traceability and acceptance

- **G13 — event-ingress port and direct-webhook/outbound-relay adapters**: Direct and outbound relay adapters share a profile-scoped ingress contract, authenticity and acknowledgment semantics; relay reconnect uses durable replay without polling. Sources: Authority §3; bin/alienintent.mjs; Issue1 webhook proof.
- **G14 — no-polling / async integration rule**: Architectural integration uses events/asynchronous operations; polling has no normal path; exceptional timed retries are bounded and are not disguised polling. Sources: Authority §21; B-DISP D10; dispatcher event paths.
- **G15 — internal event model and once-only processing semantics**: Domain events include identity/schema/profile/causation/invocation/version; duplicates/delay/reorder/crash scenarios yield effectively once-only effects with durable evidence. Sources: dispatcher.mjs; github-authority tests; Issue1 replay evidence.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
