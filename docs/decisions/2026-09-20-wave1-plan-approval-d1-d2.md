# Wave 1 PLAN approval — SWF-08 through SWF-11

Date: 2026-09-20. Status: **Founder decision — binding**.
Source: direct Founder instruction approving [the Wave 1 PLAN proposal](../work-units/sf-wave1-plan.md) subject to the clarifications below.
Predecessor: [SWF-01–07](2026-09-19-software-factory-wave1-founder-decisions.md).
Scope: planning and BIU contracts only. This record authorizes no implementation.

The Wave 1 PLAN (dependency DAG and BIU decomposition PY-02 through PY-10) is **approved** subject to SWF-08 through SWF-11.

## SWF-08 — D-1: Python live-proof environment

The PY-10 live proof uses a **dedicated AlienIntent sandbox environment**. The Python live proof must not share the active Node bootstrap's Project/profile in any way that could let both control planes dispatch the same work.

Design and create:

- a minimal dedicated sandbox repository;
- its own GitHub Project;
- its own AlienIntent Python profile;
- its own GitHub App installation / webhook identity, as the existing architecture requires;
- deliberately minimal source content, sufficient to exercise the factory.

This is test/integration infrastructure, not a second product deployment. The Node bootstrap is **not** stopped to make the Python proof possible.

## SWF-09 — D-2: budget policy

Providers advertise which budget dimensions they can actually enforce.

For current CLI worker providers, the default hard-enforced dimensions are:

- wall-clock duration;
- attempts;
- retries;
- concurrent invocation limits;
- cancellation.

Token usage and monetary cost are **measured** where the provider reports them. Missing or unreported token/cost data must never be treated as zero.

A provider is eligible for a BIU only if it can enforce every budget dimension that the BIU or deployment policy marks hard-required. Therefore:

- normal CLI-driven BIUs may run with hard time/attempt/retry limits while token and cost are measured;
- if a BIU requires a hard token or monetary ceiling and the provider adapter cannot enforce it, that provider is ineligible;
- a hard-required budget dimension is never silently downgraded to telemetry.

This preserves FD-03 fail-closed semantics.

## SWF-10 — PY-04 scripted worker is test infrastructure

The scripted/fake worker in PY-04 is Wave 1 test infrastructure only. PY-04 implements the minimum deterministic test double needed to prove the continuous factory control loop without provider spend.

PY-04 does **not** implement SF-REQ-039. The fuller user/developer-facing fake-agent/offline-factory capability remains SF-REQ-039 in Wave 2.

## SWF-11 — PY-10 live-proof acceptance

One coherent run must demonstrate all of:

1. at least 3 READY BIUs;
2. different priorities;
3. at least two equal-priority BIUs proving FIFO ordering;
4. at least one dependency;
5. WIP = 1;
6. automatic slot refill;
7. one HumanDecisionRequired event;
8. only the affected BIU blocks while independent eligible work continues;
9. a durable human decision automatically unblocks/resumes affected work;
10. a Python process restart during the run;
11. no duplicate execution/effects after restart;
12. exact candidate custody before VERIFY;
13. eventual DONE for all executable work;
14. no human manually moves individual BIUs into IMPLEMENT.

The proof demonstrates the product-level statement:

> Given a prioritized backlog, sufficient execution authority, and no unresolved blockers, AlienIntent continuously consumes eligible READY BIUs until the executable backlog is exhausted.

## Authorized next steps

1. Update the Wave 1 PLAN with these decisions.
2. Write PY-02 through PY-10 BIU contracts, preserving the dependency DAG and requirement links.
3. Run Agent-Ready on each BIU.
4. Create the BIU Issues and move them through TASKS toward READY only as dependencies and readiness permit.
5. Surface any genuine unresolved Founder/architecture decision.

Not authorized: implementing PY-02 or any later BIU; modifying FactoryChecks; extending the frozen Node bootstrap except under the existing critical bootstrap-fix rule.
