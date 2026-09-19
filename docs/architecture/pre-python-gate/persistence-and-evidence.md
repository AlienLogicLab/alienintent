# Persistence And Evidence — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-11](../../work-units/pre-python-gate/PG-11.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Logical stores and identity
Operational records: profile/work/BIU versions, ingress receipt, invocation/reservation/fencing, retry/cancellation, pending effect/readback and resource ownership. Trajectory records: immutable observable event identity, BIU/invocation/repository/role/provider/model/version/context-policy/policy IDs, occurrence/order, authorized inputs, commands/results, artifact lineage, verification/review and cost/time. Quality Evidence records: measurement definition/version and raw dimensions; finding; intervention; outcome; supporting/contradicting trajectory references and uncertainty. Learned policy remains a separately reviewed versioned decision.

SQLite is the approved default for a simple single service; PostgreSQL supports multiple instances. Physical schema choices must preserve the same profile-scoped keys, uniqueness, expected-version updates, reservation/budget atomicity and recoverable effect intents. This candidate proposes an inbox/outbox plus optimistic version/fence approach (FD-05), not a published schema or implemented event-sourcing framework.

## Custody and retention
Accepted evidence references immutable content/digests and provenance. Corrections append supersession/contradiction rather than erase accepted history. Operational cleanup never cascades into long-term evidence deletion. Local retention is configurable by evidence class, with reference/tombstone and integrity behavior for expired content. Secret redaction occurs before persisted/exported observable evidence; unavailable/redacted fields remain explicit. Private reasoning is neither required nor stored by contract. Raw quality dimensions remain distinguishable from derived scores, including under retention/compaction policy; historical 'permanent' wording is reconciled with later configurable-retention authority rather than an unbounded retention promise.

Migrations require schema version, preflight, active-work quiescence or proven compatibility, checkpoint/backup, deterministic verification and rollback where feasible. Unknown/new persisted schema never silently resets state.

## Proof scenarios
Crash between admission and launch preserves recoverable ownership. Replayed result does not duplicate transition/evidence. SQLite/PostgreSQL run identical transaction/conformance scenarios. Evidence exports cannot contain secret sentinels; deleting an expired raw payload does not misrepresent a retained measurement as fully reproducible. Conflicting usage reports preserve uncertainty. Node JSON state/logs are behavior and migration inputs, not the canonical persistence model.

## Traceability and acceptance

- **G21 — operational-state persistence design**: SQLite and PostgreSQL honor the same transaction/identity/recovery semantics, namespace profiles and separate durable evidence lifetimes from operational cleanup. Sources: Authority §§15–16; src/config/state-compatibility.mjs; Node JSON snapshots.
- **G22 — Engineering Trajectory / Quality Evidence persistence design**: Trajectory facts and derived multidimensional measurements/findings/interventions/outcomes have stable lineage, immutable accepted evidence, configurable retention/redaction and no private reasoning requirement. Sources: north-star amendment §§8–13; trajectory source §§4–17; Node logs.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
