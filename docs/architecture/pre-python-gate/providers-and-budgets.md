# Providers And Budgets — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-09](../../work-units/pre-python-gate/PG-09.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Provider and routing contract
Provider adapters declare adapter/schema version, actual provider/model/version, supported invocation/output/cancellation/tool/evidence/budget controls and authentication mode. Required capabilities are checked at the real launch boundary. Preserve SUPPORTED, COMPATIBLE_UNVERIFIED and INCOMPATIBLE semantics: novelty needs an actual compatibility probe, not arbitrary rejection or silent trust. Probe evidence must be host-generated; missing capability fails closed.

Routing filters for demonstrated quality on comparable task/phase/evidence first, then minimizes attributable expected cost. Prefer local models when they satisfy the bar; do not assume local means capable or review means cheap. Record alternatives, selected model/version, task class, quality evidence, uncertainty and routing-policy version. Material model generation changes invalidate unsupported extrapolation and trigger revalidation. Community observations inform proposals, not automatic high-impact policy changes.

## Budget contract
BIU, project/deployment and retries have explicit hard limits and reservations before launch/tool spend. Settle attributable measured usage against reservation. Unknown consumption cannot be assumed zero or release all reserved capacity. Exhaustion prevents further spend and cancels safely where supported. A provider that cannot enforce the required budget boundary is ineligible under that policy; it is not silently run with telemetry alone. FD-03/FD-05 approve this fail-closed direction, not a chosen amount or paid-call authorization.

Subscription authentication proof, provider-reported list cost, token usage and charged money are distinct fields. Node JC's sanitized subscription check proves mode, not a general hard token/spend governor. Hard bounds required by Authority §22 remain future conformance obligations.

## Scenarios
A cheap model lacking required quality evidence is not selected merely on price. Unknown patch version with a valid probe is distinguishable from incompatible output capability. Two concurrent BIUs cannot each spend the same project budget reservation. A failed billing/usage read preserves uncertainty and stops additional unauthorized spend.

## Traceability and acceptance

- **G17 — provider capability/routing contract**: Provider contract advertises required capabilities/version evidence; known/novel/incompatible versions have probe-based admission and normalized outcomes. Sources: B-DISP capability-based-provider-compatibility decision; src/providers.
- **G18 — cheapest-capable / local-first routing policy**: Selection optimizes cost subject to demonstrated quality; capable local models preferred; stale/insufficient evidence cannot invent rankings or permanent model hierarchy. Sources: Authority §23; B-DISP model-selection-cost-quality decision.
- **G24 — cost/token governance**: BIU/project/deployment/retry hard limits apply at actual launch/tool boundaries; reservations and uncertain consumption cannot overspend; costs are attributable and billing claims qualified. Sources: Authority §22; historical D08,D16; sanitized subscription worker auth.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
