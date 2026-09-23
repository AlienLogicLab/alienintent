---
proposal_id: PROP-2026-0009
title: Governed Project Plan Management
submitted_by: founder
submitted_at: 2026-09-23
proposal_type: product_capability
authority_level: unresolved
status: submitted
---

# Governed Project Plan Management

## Intent

AlienIntent should maintain a durable, versioned and inspectable Project Plan as an
authority-bearing planning artifact. New ideas, proposals, requirements and discoveries
must be recorded and classified without silently changing an approved plan.

## Proposed capability

The Project Plan records its scope, priority, sequence, dependencies, lineage and the
authority/provenance for each governed change. Incoming information is classified against
the current plan as `PLAN_NEUTRAL`, `DEFERRED_OPPORTUNITY`, `REQUIRED_REPAIR`,
`PLAN_RISK`, `PLAN_AMENDMENT_CANDIDATE`, or `PLAN_INVALIDATING` (or a subsequently
approved canonical equivalent). Classification is not plan mutation.

Only the applicable governed plan-change authority may alter committed scope, priority,
sequence or dependencies. The prior plan version, proposed delta, rationale, evidence,
decision and effective lineage remain inspectable.

## Boundaries

- A proposal, finding, dashboard, Director episode or Work Management edit cannot alter
  the committed Project Plan merely by being observed.
- The capability does not replace Product/Work Management authority, execution authority,
  or the current Wave 2 plan and DAG.
- It creates neither a BIU nor implementation/release authority.
- This is preservation of a future capability, not authority to amend a current plan.

## Semantic overlap reconciliation

SF-REQ-055 owns immutable proposal intake, not an approved plan's change control. The
Requirements / Planning context performs planning work, while FD-01 preserves the Work
Management product-authority boundary. The Factory Director consumes and coordinates the
approved plan but does not own its substantive mutation. No existing requirement is a
clean canonical owner of governed Project Plan lineage and amendment semantics; a new
canonical capability is therefore likely, pending intake and Founder authority.

## Scheduling

Deferred until Factory core is sufficiently complete and hardened. Priority and Wave are
unassigned. This proposal must not displace current Factory-core or Wave 2 work.
