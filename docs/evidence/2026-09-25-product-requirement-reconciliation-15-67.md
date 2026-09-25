# Product Requirement reconciliation — #15 and #17–#67

Date: 2026-09-25
Scope: continuation of `docs/evidence/2026-09-25-product-requirement-reconciliation-3-16.md`.

## Method

Each Product Requirement was reconciled against current requirement text, selected Wave/specification state, DAG acceptance ownership, candidate BIUs, retained implementation/verification evidence, and current Project state.

Rules:
- BIU completion alone does not close a Product Requirement.
- A requirement is PROVEN only when every currently authorized acceptance criterion has retained executable evidence and no deferred extent remains attached.
- Planned/deferred future-wave work is not promoted merely because precursor machinery exists.
- A genuine uncovered product gap routes through Proposal Intake; a missing DAG/BIU mapping inside an existing approved requirement routes through governed planning, not a duplicate proposal.
- Lifecycle changes are read back from Project #1 and fail closed on ambiguity.

## Reconciliation summary

| Issue | Requirement | Classification | Project disposition |
|---|---|---|---|
| #15 | SF-REQ-037 Installer | DEFERRED product surface; installation primitives exist but no `alienintent init` | CAPTURE |
| #17 | SF-REQ-011 Requirements IR | PARTIAL: AC-01..04 proven; AC-05/06 specified but unrouted | CAPTURE |
| #18 | SF-REQ-012 Ambiguity detection | PROVEN via U2 / WO-220202 | DONE |
| #19 | SF-REQ-013 Requirements→BIU compilation | PARTIAL: U7 AC-03..05 proven; U8/AC-01/02 unexecuted; AC-06..08 trace/candidate stale | CAPTURE |
| #20 | SF-REQ-014 Mechanical proof obligations | PROVEN via U4 / WO-220204 | DONE |
| #21 | SF-REQ-015 BIU lint/readiness | ROUTED / IN PROGRESS via U9 / #105 | TASKS |
| #22 | SF-REQ-016 Definition/Observation/Verdict | PROVEN via S1 / WO-220102 | DONE |
| #23 | SF-REQ-039 Offline factory proof | PLANNED / AUTHORITY-BLOCKED via O / WO-220404 | PLAN |
| #24 | SF-REQ-041 External artifact intake | Intentional Wave 2B defer | CAPTURE |
| #25 | SF-REQ-042 Immutable intake snapshot | Intentional Wave 2B defer | CAPTURE |
| #26 | SF-REQ-043 Intake authority modes | Intentional Wave 2B defer | CAPTURE |
| #27 | SF-REQ-044 Prototype→requirements | Intentional Wave 2B defer | CAPTURE |
| #28 | SF-REQ-017 Requirement-evidence traceability | Intentional Wave 3; precursor evidence only | CAPTURE |
| #29 | SF-REQ-018 Architecture conformance | Intentional Wave 3; architecture checks are precursor | CAPTURE |
| #30 | SF-REQ-019 Drift detection | Intentional Wave 3 | CAPTURE |
| #31 | SF-REQ-020 Fake-DONE prevention | Intentional Wave 3; strong precursor machinery | CAPTURE |
| #32 | SF-REQ-021 Independent verification | Intentional Wave 3; live JC pattern is precursor evidence | CAPTURE |
| #33 | SF-REQ-022 Bounded repair loops | Wave 3; extension pending POSTW1-DECIDE-007A | CAPTURE |
| #34 | SF-REQ-023 Product/outcome verification | Intentional Wave 3; closure distinctions are precursor | CAPTURE |
| #35 | SF-REQ-024 Factory yield metrics | Intentional Wave 3; partial telemetry only | CAPTURE |
| #36 | SF-REQ-040 Provider-free replay | Intentional Wave 3 | CAPTURE |
| #37 | SF-REQ-045 External code productionization | Wave 3, blocked by Wave 2B intake | CAPTURE |
| #38 | SF-REQ-046 Creation-tool adapters | Wave 3, blocked by Wave 2B intake | CAPTURE |
| #39 | SF-REQ-047 Prototype behavioral verification | Wave 3, blocked by Wave 2B intake | CAPTURE |
| #40 | SF-REQ-025 Provider capability discovery | Wave 4; current Wave 2 explicitly defers | CAPTURE |
| #41 | SF-REQ-026 Cheapest-capable routing | Wave 4; local-model work is evidence, not completion | CAPTURE |
| #42 | SF-REQ-027 Source intelligence | Wave 4 optimization | CAPTURE |
| #43 | SF-REQ-028 Execution economics | Wave 4; partial telemetry only | CAPTURE |
| #44 | SF-REQ-029 Engineering Trajectory | Wave 5; Wave 2 references but explicitly defers full requirement | CAPTURE |
| #45 | SF-REQ-030 Quality Evidence | Wave 5 canonical owner; current typed evidence is substrate | CAPTURE |
| #46 | SF-REQ-031 Evidence-derived routing learning | Wave 5 | CAPTURE |
| #47 | SF-REQ-032 Learning proposals | Wave 5 | CAPTURE |
| #48 | SF-REQ-033 Community learning | Wave 5 | CAPTURE |
| #49 | SF-REQ-036 Factory dashboard | Wave 6 productization | CAPTURE |
| #59 | SF-REQ-048 Minimum necessary work | Binding invariant now; mechanical productization remains Wave 3 | CAPTURE |
| #60 | SF-REQ-049 Convergent Repair | Strong precursor evidence; formal Wave 3 capability not routed | CAPTURE |
| #61 | SF-REQ-050 Proven-Red promotion | Wave 3; Wave 2 consumes constraints but explicitly defers full promotion capability | CAPTURE |
| #62 | SF-REQ-051 Design Contract / Design Verification | PARTIAL: U5 five criteria proven; U6 AC-03 blocked by R2-GAP-051-EDGE-AUTHORITY | TASKS |
| #63 | SF-REQ-052 Convergence Assistance | Wave 3 | CAPTURE |
| #64 | SF-REQ-053 Persistent control / bounded episodes | PARTIAL / DECOMPOSED: C1/C2 proven, C3 #99 PLAN, later capstone/replacement gates pending | TASKS |
| #66 | SF-REQ-055 Proposal Intake | Wave 3; current manual governed intake is precursor | CAPTURE |
| #67 | SF-REQ-056 Actor-launch liveness | PLANNED / AUTHORITY-GATED via L1/B2 | PLAN |

## Material findings

### Requirements that were already complete but stale on the board

#18, #20 and #22 had complete acceptance ownership and retained independent executable proof. Their CAPTURE statuses were stale and were corrected to DONE with canonical Project read-back.

### Current Wave 2 decomposition gaps

**SF-REQ-011 (#17):** AC-05 and AC-06 exist in the binding specification but have no acceptance-trace owner in the current DAG. This is a governed planning/decomposition gap, not a new Product Proposal.
**SF-REQ-013 (#19):** the 2026-09-22 specification defines AC-01..08. U7/#101 proves AC-03..05. U8/WO-220208 remains unexecuted and stale relative to the amendment: acceptance trace covers only AC-01..05, candidate WO-220208 lists only AC-01/02 and retains superseded allocation/split text. Before materialization, U8/candidate/trace must be reconciled to AC-06..08 while preserving the valid R2-GAP-051-EDGE-AUTHORITY gate.

**SF-REQ-051 (#62):** U5/#97 proves AC-01,02,04,05,06. U6 owns AC-03 and remains blocked by R2-GAP-051-EDGE-AUTHORITY.

**SF-REQ-053 (#64):** C1 and C2 extents are proven; C3 is #99 at PLAN; C and R5 remain separately authorized/deferred.

**SF-REQ-056 (#67):** L1 owns AC-01..07 and B2 owns AC-08, but both remain authority-gated/unexecuted.

## Existing Proposal Intake gap cohort

The prior #3–#16 cohort already routed genuine gaps:
- #102 — doctor validation of configured external capabilities (SF-REQ-038 amendment);
- #103 — reachable configurable concurrency policy (SF-REQ-003 Solve for N);
- #104 — feature-regression hardening for SF-REQ-002/004/010.

Other current proposals:
- #100 — mechanically prevent worker completion while owned background work remains active;
- #106 — local-agent Factory Director provider / shadow evaluation;
- #107 — FD-EVAL-01 evidence suite supporting #106;
- #108 — deployment-profile runtime normalization and stable capability surface.

These are not duplicate Product Requirements. #106/#107 provide bounded resilience/evaluation evidence that may later inform SF-REQ-025/026/028/031. #108 is immediate runtime/deployment hardening and should later inform SF-REQ-037 Installer and provider-capability configuration without replacing them.

## Pipeline-supply observation

During this reconciliation #105 (WO-220209) was in IMPLEMENT while #99 (WO-220303) remained PLAN despite its prior dependencies #95/#97 being DONE and prior owner-question triage recording no Founder hold.

The Factory Director Host reported active WIP 1/1 and no control-required reason, so it did not retain/wake Director cognition for PLAN-stage buffer preparation. This is further evidence that execution continuity is mechanically stronger than supply continuity.

The standing Founder no-starvation direction was relayed through the durable Director inbox so #99 can be prepared toward READY while #105 executes. This is an operational recovery action; the structural supply-continuity defect requires separate evidence-based analysis after flow is protected.

## Next grooming stage

1. Keep execution supply ahead of demand: #99 is the immediate near-READY buffer behind #105.
2. Deduplicate and prioritize #100/#102/#103/#104/#106/#107/#108 against factory operating priorities.
3. Reconcile Wave 2 planning defects (#17 AC-05/06; #19 U8/AC-06..08) through governed plan/DAG work rather than new proposals.
4. Preserve later-wave CAPTURE items without pulling them forward solely because precursor machinery exists.
