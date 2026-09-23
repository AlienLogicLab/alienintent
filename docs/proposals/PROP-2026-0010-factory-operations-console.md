---
proposal_id: PROP-2026-0010
title: Factory Operations Console
submitted_by: founder
submitted_at: 2026-09-23
proposal_type: product_capability
authority_level: unresolved
status: submitted
---

# Factory Operations Console

## Intent

Provide a unified supervisory projection of the governed Project Plan and live factory,
without creating an alternate lifecycle or planning authority.

## Proposed capability

The Console visually monitors every non-terminal lane: CAPTURE, SPECIFY, DESIGN, PLAN,
TASKS, Agent Ready, READY, RELEASE, IMPLEMENT, VERIFY, REVIEW and ACCEPT. It shows queue
depth and age, responsible capability/agent, current activity, dependencies, holds,
elapsed time, next transition, evidence, provider/model and applicable cost/budget.

It also projects plan/Wave/Sprint/Epic/requirements/BIUs, dependency graph, critical path,
execution frontier, progress and risks. Every displayed control, event and state is read
from or sent through canonical domain interfaces; UI state never mutates lifecycle or plan
state directly.

## Semantic overlap reconciliation

SF-REQ-034 owns the Operator Control Plane's status, explain, inspection and legitimate
domain-event actions. SF-REQ-036 owns the Factory Dashboard's operational view. This
proposal is best treated as a future strengthening/amendment of those two requirements,
with the Console as an adapter/projection composition rather than a new lifecycle owner.
It may consume the proposed governed Project Plan but cannot own it.

## Boundaries and scheduling

The Console is not a second Work Management Provider, execution kernel or Decision Inbox.
It creates no BIU, implementation or release authority. Deferred until Factory core is
sufficiently complete and hardened; Priority and Wave are unassigned and current Wave 2
scope/DAG remain unchanged.
