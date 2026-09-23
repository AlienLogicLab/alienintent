---
proposal_id: PROP-2026-0012
title: Factory Supervisory Controls and Safety
submitted_by: founder
submitted_at: 2026-09-23
proposal_type: product_capability
authority_level: unresolved
status: submitted
---

# Factory Supervisory Controls and Safety

## Intent

Define explicit supervisory-control semantics so operators can safely constrain factory
operation without direct UI mutation or ambiguity between materially different actions.

## Proposed capability

Controls include Emergency Stop, Pause, Drain, Resume, Pause Releases, Pause Intake,
project/provider/model isolation, worker/profile disablement, WIP/concurrency limits,
budget controls within authority, governed reprioritization, cancel, retry/reconcile,
quarantine and Maintenance Mode. E-STOP, Pause, Drain and Cancel are distinct commands
with explicit effects, authority, audit/evidence and recovery semantics.

Every control flows through the canonical authority and domain interfaces. A display or
console may initiate an authorized command, but must not directly mutate local UI state as
if it were factory state.

## Semantic overlap reconciliation

SF-REQ-034 is the primary existing owner because it already covers Control Plane actions,
including cancel, resume and reconcile, through normal domain/event paths. SF-REQ-009,
SF-REQ-003, SF-REQ-028, SF-REQ-026 and SF-REQ-035 respectively constrain deterministic
enforcement, WIP, budgets, allocation and authority decisions. The proposed semantics
should likely strengthen SF-REQ-034 while retaining these owners; whether an independent
safety requirement is needed is unresolved and must not be decided by this proposal.

## Scheduling

Deferred until Factory core is sufficiently complete and hardened. Priority and Wave are
unassigned; no BIU, implementation/release authority or current Wave 2 change is created.
