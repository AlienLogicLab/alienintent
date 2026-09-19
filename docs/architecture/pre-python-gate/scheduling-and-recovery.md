# Scheduling And Recovery — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-08](../../work-units/pre-python-gate/PG-08.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Candidate admission protocol
Admission checks BIU release/version, dependency satisfaction, profile/repository authorization, capability and budget readiness before mutation. Reserve capacity atomically for global, profile and repository scopes before awaiting worker preparation. A reservation names invocation, owner, version/fence and workspace. Default architectural convention is one active mutating worker per repository; numerical global/profile limits are explicit deployment configuration, not invented here. N profiles never share unscoped ownership keys.

Allocate a distinct worktree per invocation. Never reuse a live resource solely because a lane looks idle. Provenance checks bind canonical repository, baseline, branch/path and ownership record. A worktree cleanup failure produces a resource diagnostic, not a rewritten lifecycle result.

## Cancellation and retries
Authorized cancellation records actor/reason and cancellation intent, fences future grant use and successor admission, signals owned worker termination, confirms quiescence, preserves trajectory/results, then cleans owned ephemeral resources and releases reservation. Timeout/unknown process identity is an explicit unresolved recovery condition; never delete a plausible live workspace or trust a recycled PID alone. Late results are retained as evidence but cannot silently undo cancellation or approve a successor candidate.

Retry policy carries finite attempts, timeout, exponential backoff, jitter and hard budget; state records attempt and next eligible event/deadline. Timers for bounded retry/cancellation deadlines do not become remote workflow polling. Authorization/identity failures require changed authority/evidence, not repeated retry.

## Recovery scenarios
Two concurrent events competing for one repository yield one reservation and one pending/rejected outcome. Crash after allocation before process identity leaves the resource held for diagnosis until ownership/liveness is established. Durable correlated result precedes a successor; evidence-read failure retains ownership. Repeated cancel is idempotent. A stale child exit cannot release a newer invocation's reservation. These retain Node D17/D18/D31 behavior while the multi-instance fencing implementation remains a candidate persistence contract (FD-05).

## Traceability and acceptance

- **G16 — concurrency/cancellation/retry policy**: Global/profile/repository bounds, atomic reservations, cancellation and finite retry budgets prevent double mutation and preserve live/ambiguous resources on recovery. Sources: dispatcher/worktree-manager; worktree-lifecycle tests; B-DISP D17,D18,D31.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
