---
proposal_id: PROP-2026-0005
title: Proposal Intake as a Product Capability
submitted_by: durability-gap audit
submitted_at: 2026-09-20
proposal_type: product_requirement
authority_level: unresolved
status: submitted
---

# Proposal Intake as a Product Capability

## Intent

AlienIntent should treat a submitted proposal as immutable noncanonical
provenance until admission through applicable authority, then durably preserve
its relationship to the canonical artifact that owns current state.

## Proposed capability

```text
submitted Proposal
  -> validate / classify / deduplicate
  -> resolve required authority
  -> canonicalize into Product Requirement, decision, research, defect, or other artifact
  -> retain immutable proposal provenance
  -> record proposal-to-canonical mapping
```

The capability must provide:

- `proposal_id` idempotency: duplicate delivery never creates duplicate
  canonical work;
- explicit classification, deduplication and authority resolution;
- immutable original proposal provenance while canonical work owns current state;
- durable proposal-to-canonical mappings, including non-requirement
  dispositions;
- a provider-neutral core in which repository-backed `docs/proposals/` is an
  adapter rather than the domain architecture; and
- support for future CLI, API, control-panel and agent-generated submission
  adapters without changing the domain semantics.

## Boundaries

Intake cannot invent priority, Wave, product authority or architecture
authority. It does not create a BIU merely by accepting a proposal. Deduplication
does not erase proposal provenance; it records the disposition and canonical
target. No document layout, database or service implementation is prescribed.

## Relationship to existing authority

The current proposal index is an operating convention for immutable provenance.
SF-REQ-011–016 govern requirements, ambiguity, compilation and
observation/verdict separation; SF-REQ-032 forbids autonomous policy mutation.
SF-REQ-041–044 cover intake of external creation artifacts, not a proposal's
lifecycle into canonical factory work. This proposal makes that separate intake
capability explicit.

## Desired outcome

Each proposal has durable, idempotent provenance and an authoritative mapping
to its resulting work or non-requirement disposition without making a repository
folder the permanent domain model.
