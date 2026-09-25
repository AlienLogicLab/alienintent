# Wave 2 authority-blocker grooming

Date: 2026-09-25
Status: retained backlog-grooming evidence. This record distinguishes stale authority questions from genuine remaining gates; it does not itself release work.

## Purpose

Wave 2 planning accumulated several authority-gap identifiers across specification/design iterations. Backlog grooming rechecked each against later binding Founder decisions, canonical architecture ownership, retained independent classification and current implementation evidence.

Principle:

> Do not ask the Founder to decide something already durably decided. Do not preserve an authority blocker merely because an old candidate/DAG still carries its identifier.

A stale gate is repaired through governed plan/design consistency work and fresh downstream assessment. Genuine operational proof/release gates remain intact.

## Findings

| Blocker | Grooming classification | Basis / next action |
|---|---|---|
| `R1-GAP-013-ALLOCATION` | **ALREADY SETTLED** | SF-REQ-013 amendment of 2026-09-22 assigns compiler-derived initial decomposition and conserved split/replan. Historical gap text remains provenance only. U8 artifacts still require consistency repair. |
| `R2-GAP-051-EDGE-AUTHORITY` | **RESOLVED 2026-09-25** | Founder disposition `docs/decisions/2026-09-25-cross-module-coupling-risk-disposition.md`: do not adopt historical blanket allowed-edge table; retain approved architecture checks and add evidence-driven coupling checks. Replan/reverify U6. |
| `POSTW1-DECIDE-008A` / SF-REQ-056 ratification | **STALE** | Binding SWF-29 already canonicalized SF-REQ-056 as P0 / Wave 2 under Founder authority. Repair stale L1/DAG/design/assessment inputs; do not ask for ratification again. |
| `R1-GAP-MONITOR-HOST` | **NOT A FOUNDER DECISION** | Retained independent classification already assigns persistent monitoring to SWF-27 / SF-REQ-053, with installation/doctor configuration under SF-REQ-037/038. Remaining need is concrete supervisor + restart/self-health/doctor proof and independent design verification. |
| `POSTW1-DECIDE-004A` / Agent Ready G1/G2 ownership | **STALE** | Binding Architecture Authority A1 assigns Agent Ready product ownership of implementation, public schema/contract, CLI, MCP, provider adapters and compatibility; SF-REQ-015 owns only AlienIntent integration through supported public interfaces. Replan U10; no new owner assignment. |
| `R1-GAP-039-ORCHESTRATION` | **RESOLVED BY EXISTING ARCHITECTURE OWNERSHIP; DESIGN REVISION REQUIRED** | FD-01/FD-02 place released-BIU lifecycle/verification/closure orchestration in Execution Coordination. SF-REQ-039 needs a real producer→independent verifier→repair lifecycle, but does not need a new state owner. |
| `R1-GAP-039-REAL-OUTCOME` | **RESOLVED BY EXISTING ARCHITECTURE OWNERSHIP; DESIGN REVISION REQUIRED** | Invocation Runtime owns worker/resource execution and implements the WorkerProvider boundary. Execution Coordination owns durable lifecycle/result correlation. Revise SF-REQ-039 around the existing port/evidence ownership; do not mandate a new RoleOutcomeRecord sidecar/state owner unless revised DV demonstrates necessity. |

## SF-REQ-039 residual design problem

The ownership question is resolved, but a real capability gap remains.

Current `FactoryCoordinator._completed_for_outcome` collapses a successful producer result mechanically through VERIFY → REVIEW → ACCEPT → closure without invoking a fresh independent verifier. That does not satisfy the canonical producer/verifier workflow or SF-REQ-039's deterministic test-worker scenarios requiring verifier rejection → repair → fresh candidate.

Revised design must:
- preserve Execution Coordination as lifecycle owner;
- preserve Invocation Runtime behind the common WorkerProvider port;
- support distinct producer and independent verifier invocations/results through the real lifecycle;
- retain exact candidate custody and fresh verifier retrieval;
- handle malformed/missing/delayed/duplicate/miscorrelated outcomes fail-closed;
- preserve restart/readback, budget, attempt and authority semantics;
- avoid test-mode lifecycle shortcuts;
- avoid a new cross-cutting state subsystem unless existing boundaries are proven insufficient.

## Near-term execution-supply consequence

At this grooming point:
- #105 / U9 is IMPLEMENT.
- #99 / C3 is READY.
- U6 is no longer waiting on Founder edge-policy authority but needs scoped plan/design repair + independent DV.
- U10's owner-assignment gate is stale; after #105 it needs integration-design refresh + proof/Agent Ready.
- L1's ratification/monitor-owner questions are stale/reclassified; it needs plan/design consistency repair + normal gates.
- C5 monitor-host work requires operational supervisor proof, not a new Founder ownership decision.
- K1/SF-REQ-039 real-worker work requires revised design under existing Execution Coordination / Invocation Runtime ownership, not new product ownership.

This materially improves the supply frontier, but none of these stale-gate corrections is itself READY/release authority.

## Genuine remaining decision/gate classes

Do not collapse the remaining gates into one opaque Founder bundle. Keep separate:
- actual operational/live-proof authority;
- bootstrap-retirement/cutover decisions with replacement evidence requirements;
- any still-unsettled product behavior or integration contract not already owned by binding architecture;
- explicit budget/cost decisions if delegated authority is insufficient.

Retained bootstrap protections marked KEEP_UNTIL_REPLACED remain in force until their stated replacement proofs are met.
