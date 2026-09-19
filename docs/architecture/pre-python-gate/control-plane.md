# Control Plane — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-13](../../work-units/pre-python-gate/PG-13.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Application model
Recover the existing status/explain/doctor/logs/version/resources projection and continue/reconcile design from canonical-architecture and implementation-plan. Add Authority §36's legitimate event generation, replay, resume, cancel/abort and inspection of BIUs, workers, queued events, routing, cost, grants and adapter/transport health. These are application services over the same domain contracts, not a second orchestration engine.

Read requests return profile/work/invocation scope, observed version/time, authoritative evidence and explicit unknown/unavailable classifications. Explain is a deterministic account of guards and evidence, not an LLM inventing current authority. Mutating commands carry actor/authority, target, intent, expected version, reason and idempotency key; validation and domain events use normal admission/transition guards. Dry-run evaluates without mutation or grant use. Synthetic test events must remain scoped to an explicitly authorized test target and cannot bypass production authorization.

## Presentation and observability
CLI is required, with human and structured machine-readable outcomes and nonzero error status. CLI and any later approved web interface call the same application services and authorization checks. No separate web state store or hidden administrative bypass. CLI is the mandatory presentation scope for this gate. The shared-service web interface remains a candidate extensibility design, with no web deployment or authentication scope adopted; FD-04 concerns relay trust only. Existing command sketches are reused, and no implemented web panel was found in the inventoried AlienIntent/B-DISP corpus.

Structured events/logs correlate profile, BIU, invocation, event, candidate and policy versions. Health distinguishes live process from ready dependencies; diagnostics expose sanitized causes, not keys/tokens/provider stderr. Timelines, metrics and optional traces include lifecycle, provider/model, token/cost/latency, grants and adapter/transport health. Operator projections can link immutable evidence without replaying a private reasoning transcript.

## Scenarios
Replay of a processed event returns prior custody/effects without duplicate work. Resume with stale authority cannot release a new worker. Cancel enters the same cancellation protocol, not deletion of a state row. A missing Project read is UNAVAILABLE, not a fabricated DONE or wrong-account diagnosis. FD-01 determines which external/internal evidence is authoritative when projections disagree.

## Traceability and acceptance

- **G25 — operator Control Plane application model**: Operator status/explain/emit/replay/resume/reconcile/cancel/doctor act through normal application/domain services and authorization; no state-edit backdoor. Sources: canonical-architecture Operator surface; implementation-plan phases1–6; Authority §36.
- **G26 — control-plane presentation adapters (CLI/web as approved)**: CLI exposes approved operations and machine-readable diagnostics; any web surface uses same services/policies, with explicit approval status and no hidden permissions. Sources: interface-contracts Operator; Authority §§33,37; bin/alienintent.mjs limited CLI.
- **G30 — observability model**: Structured logs/readiness/health/timelines/metrics/provider cost/lifecycle and sanitized diagnostics correlate to BIU/invocation without exposing credentials or private reasoning. Sources: Authority §35; streaming worker logs, diagnostics, Issue1 evidence.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
