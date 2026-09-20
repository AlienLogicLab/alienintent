---
proposal_id: PROP-2026-0002
title: Design Contract and Design Verification before BIU execution
submitted_by: founder
submitted_at: 2026-09-20
proposal_type: workflow_architecture
authority_level: founder
status: submitted
---

# Design Contract and Design Verification before BIU execution

## Intent

AlienIntent should introduce an explicit design stage between approved requirements and executable BIUs.

The worker should receive everything needed to implement the approved solution without being given unnecessary authority to redesign the system.

The core principle is:

> **Close every decision that affects product meaning, architecture, trust, persistence, interfaces, or verification before implementation begins. Leave only local implementation choices open.**

## Problem

A workflow of:

```text
Requirement
→ BIU
→ IMPLEMENT
```

leaves too much design responsibility inside the implementation worker.

That increases the chance of:

- architecture drift;
- scope expansion;
- inconsistent domain ownership;
- unnecessary mechanisms;
- persistence choices made ad hoc;
- interface redesign during implementation;
- acceptance criteria being reinterpreted;
- expensive verifier cycles discovering design defects too late.

## Proposed workflow semantics

The engineering flow should semantically become:

```text
Requirement / Proposal
        ↓
SPECIFY
        ↓
DESIGN
        ↓
DESIGN VERIFICATION
        ↓
PLAN / decomposition
        ↓
BIU Contract
        ↓
Agent-Ready
        ↓
READY
        ↓
IMPLEMENT
        ↓
VERIFY
        ↓
REVIEW
        ↓
ACCEPT
        ↓
DONE
```

This proposal does not require immediate addition of visible DESIGN or DESIGN VERIFY Project lanes.

These may initially exist as artifacts/gates inside SPECIFY/PLAN.

## Design Contract

Introduce a first-class Design Contract artifact.

A Design Contract should contain, where applicable:

- requirements being satisfied;
- product behavior affected;
- bounded contexts/modules affected;
- domain ownership;
- architecture impact;
- invariants;
- public interfaces;
- persistence/data changes;
- dependency direction;
- external-system boundaries;
- failure behavior;
- recovery behavior;
- idempotency expectations;
- security/privacy constraints;
- capabilities required;
- observability requirements;
- explicit design decisions;
- deferred implementation-local decisions;
- acceptance criteria;
- verification strategy;
- evidence obligations;
- non-goals.

## Design authority boundary

The implementation worker may decide local implementation details such as:

- function decomposition;
- local helpers;
- variable naming;
- internal control flow;
- minor refactoring inside the approved boundary.

The implementation worker must not independently decide:

- bounded-context ownership;
- new services/databases/queues;
- public API semantics;
- persistence strategy;
- security/privacy model;
- architecture direction;
- product behavior;
- verification obligations;
- acceptance-criteria reinterpretation.

If such a decision remains unresolved, the BIU is not ready.

## Design Verification

Before BIU decomposition or release, AlienIntent should verify the Design Contract against project standards.

Design Verification should evaluate:

- EOS;
- project architecture authority;
- DDD boundaries;
- Hexagonal dependency direction;
- ACL boundaries;
- Ubiquitous Language;
- existing ADRs / Founder decisions;
- security/privacy rules;
- canonical existing mechanisms;
- consistency with requirements;
- compatibility with existing interfaces;
- unnecessary mechanism/complexity;
- observability/recovery expectations.

## Mechanical-first principle

Use the same Gap Trap principle here:

> **If a design rule can be checked mechanically, verify it mechanically before model/human review spends intelligence on it.**

Examples may include:

- forbidden dependency direction;
- illegal bounded-context references;
- vendor concepts in domain;
- invalid interface dependencies;
- duplicate mechanism introduction;
- schema compatibility constraints.

Remaining design judgment should be independently reviewed.

## Relationship to BIU

A BIU should be derived from an approved Design Contract.

The BIU should not reopen approved design decisions.

It should carry:

- relevant design references;
- fixed decisions;
- allowed implementation freedom;
- boundaries;
- completion criteria;
- evidence obligations.

## Relationship to Agent-Ready

Agent-Ready should eventually confirm not only that the BIU is complete, but that:

- required design exists;
- design verification passed;
- no unresolved design authority remains;
- implementation-local freedom is clearly bounded.

## Measurement

Candidate metrics:

- design_defects_caught_before_implement;
- architecture_defects_caught_during_design_verify;
- implementation_rework_caused_by_missing_design;
- verifier_findings_attributable_to_design_ambiguity;
- founder_decisions_discovered_after_implement;
- design_to_biu_traceability_coverage;
- percentage_of_bius_with_verified_design_contract;
- late_architecture_changes_per_biu;
- design_review_cost_vs_downstream_rework_avoided.

## Non-goals

This proposal does not require:

- line-by-line implementation design;
- eliminating worker judgment entirely;
- adding visible DESIGN lanes immediately;
- duplicating PLAN;
- creating bureaucracy for trivial changes.

The design depth should be proportional to the change.

## Desired outcome

Implementation workers receive a closed-enough engineering package that makes disciplined execution natural and minimizes unnecessary design freedom during implementation.
