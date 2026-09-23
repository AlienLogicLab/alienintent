---
proposal_id: PROP-2026-0013
title: Factory Commissioning and Minimum Viable Project Intent
submitted_by: founder
submitted_at: 2026-09-23
proposal_type: product_capability
authority_level: unresolved
status: submitted
---

# Factory Commissioning and Minimum Viable Project Intent

## Intent

Enable a fresh AlienIntent installation to progress from minimally sufficient product
intent, or intent plus existing artifacts, to a governed Project Plan and first Agent-Ready
BIU with minimal Founder input and without assuming evidence is product authority.

## Proposed capability

Distinguish `INSTALL → COMMISSION → OPERATE` and support greenfield, brownfield and
prototype/artifact startup. A new install receives a sensible Project Plan skeleton and
safe operating defaults; that structure is not product intent.

Define Minimum Viable Project Intent (MVPI): for greenfield, a minimal desired
product/outcome from which only safe conclusions are derived, interrupting only for material
authority or product ambiguity. For brownfield, approximately a target repository/artifact
plus desired change/outcome, with additional context optional. Brownfield commissioning must
keep descriptive truth (what a system does) distinct from normative intent (what it should
do): code, tests, docs and issues are evidence, not automatic product authority.

The absence of a complete PRD, architecture, backlog or formal requirements does not block
commissioning. Bootstrap exit criteria govern `PROJECT_BOOTSTRAPPING → FACTORY_ACTIVE` only
after Project identity, sources, authority, safe defaults, the initial governed plan and a
first Agent-Ready BIU path are sufficiently established.

## Semantic overlap reconciliation

SF-REQ-037/038 own installation and validation; SF-REQ-041–047 own artifact intake and
observed behavior/provenance; SF-REQ-055 owns proposal intake; Requirement Source and Work
Management preserve source versus product/work-state roles. Those capabilities provide
inputs and safeguards but do not cleanly own commissioning, MVPI, startup-mode semantics or
bootstrap exit. A new canonical capability is likely, pending intake and Founder authority.

## Scheduling

Deferred until Factory core is sufficiently complete and hardened. Priority and Wave are
unassigned; no BIU, implementation/release authority or current Wave 2 change is created.
