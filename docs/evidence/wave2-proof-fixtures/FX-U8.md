# FX-U8 — initial compilation derives the INITIAL candidate (WO-220208, U8)

Authority: Issue #117 RELEASED comment (Factory Director, 2026-09-26T08:27:44Z, SWF-35
standing Wave 2 authority), `docs/work-units/wave2/WO-220208.md` and the pinned packet
`docs/evidence/wave2-execution-packets/WO-220208.{packet,allocation}.json` plus
`WO-220208.proof-packet.md`. PRODUCER invocation
`AlienLogicLab/alienintent#117:PRODUCER:13bb35b4-c7a1-4b73-89d0-9813dd64de42`
(worker Morty, claude-opus-5-5), branch `b-disp/bfb63d89-6c57-425c-99d0-2beb08a4059d`.
Proof level `LOCAL_COMPOSED_OR_MECHANICAL`; disposable local state only. Nothing here
authorizes release, split apply, Issue allocation, materialization or live operation.

## Admission

- Baseline `d716552b430a9bf6157b9dcd8f6241551028759e` (= `origin/main` at release).
- Predecessors WO-220207 (#101, U7) and WO-220206 (#110, U6) are DONE per the RELEASED
  record; their source and proof are unmodified here.
- Fresh native Agent Ready READY:
  `docs/evidence/wave2-readiness-assessments/WO-220208.2026-09-26T072001.985395Z.assessment.json`.
- F4 (context_assembly is an internal capability of Requirements / Planning):
  `docs/decisions/2026-09-26-f4-context-assembly-bounded-context-disposition.md`.

## Design verification (reuse before build)

- No producer in the project, Alien Logic Lab or tool ecosystem derives BiuContract
  candidates from requirements/design/proof. Agent Ready is a readiness judge consumed
  via SF-REQ-015 and is neither copied nor called here.
- Reused interfaces: `BiuContract`/`BudgetPolicy` (via the U7 validator), the U1
  `InventoryService`, U2 `AmbiguityService.report`, U5 `DesignReadiness` gate and the
  retained verified design (`VerifiedDesignDecisions.design`), U4 `ProofPlanning.current`,
  `OperationalStore` (expected-version commits) and `EvidenceRepository` (immutable
  Observations). The U7 `validate` runs unchanged over every derived candidate.
- Design source: SF-REQ-013 design contract
  (`docs/evidence/wave2-design-contracts.json#/contracts/2`: ports 0–2, identities,
  transitions 0–2, security, `013-graph-coverage`).

## Implementation (U8 initial-compilation extent only)

- `context_assembly/domain/initial_compilation.py` — pure `compile_initial`:
  - **Derivation rule `REQUIREMENT_BOUNDED_UNITS_v1`**: one unit per requirement the
    verified design satisfies (stable `unit_key` `requirement:<id>`). Finer semantic
    boundaries are Agent Ready SPLIT judgment applied by a later authorized Split
    Transaction; the compiler never chooses them. The rule and its rationale are recorded
    in every candidate and labelled
    `IDENTITY_RULES_CANDIDATE_NOT_INDEPENDENTLY_DESIGN_VERIFIED`.
  - Every BiuContract field is copied from one named source: requirement labelled fields
    (Intent, Scope, Non-goals, Acceptance, dependencies), verified design (FIXED
    decisions, capabilities, evidence, non-goals), the requirement's proof plan
    (verification and evidence duties), or `authority_limits` (issuer, policies,
    custody/closure/escalation duties, repositories, baselines, budget).
    `authority_references` link the exact requirement, design, proof-plan and inspection
    revisions (AC-01). `budget_rule` `PER_UNIT_CAP_FROM_AUTHORITY_LIMITS`: the authorized
    cap is copied, never divided or raised; capabilities outside the limits hold
    (`BOUNDS_WIDENED`).
  - Four obligation categories are frozen with forward (obligation → explicit unit
    extent) and reverse (contract clause → obligation) trace (AC-02). An acceptance
    criterion without a proof obligation, or a proof obligation for an undeclared
    acceptance, holds.
  - Identities (`INITIAL_IDENTITY_RESERVATION_v1`, the contract's candidate identity
    design): a persisted per-`unit_key` reservation is reused; otherwise the lowest
    unused unsuffixed number of the configured family/width, excluding active, retired,
    reserved, persisted and existing-decomposition identities, assigned in `unit_key`
    value order. Collision and exhaustion fail closed.
  - Existing decomposition is immutable: a requirement that already has one holds
    (`EXISTING_DECOMPOSITION`).
- `context_assembly/application/initial_compilation_service.py` — `InitialCompilation`:
  - Order: design gate, then the retained design of that exact verified revision, then
    the current inventory, inspection and proof plans, then derivation.
  - A candidate commits new reservations to `upstream:identity-reservations` (expected
    version). A concurrent identical reservation counts as success; any other conflict
    is `PERSISTENCE_CONFLICT`.
  - Every result is retained as an immutable Observation (`compilation.derived` /
    `compilation.held`) under the CAS pointer `upstream:initial-compilation:<input digest>`.
  - `completed()` accepts only a derived record.
  - It never writes `factory:*`, `release:*`, Issues, projections or existing
    decomposition state.
- `context_assembly/ports/compilation.py`: `VerifiedDesigns`, `InventorySource`,
  `InspectionSource`, `ProofPlans`.
- `composition/compilation.py`: `VerifiedDesignDecisions.design` and
  `CurrentProofPlanDocuments`. Proof plans cross into `context_assembly` as documents, so
  the module gains no cross-module import and the coupling register is unchanged.
- `composition/upstream_profile.py`: `UpstreamProfile.initial_compilation`, composed when
  compiler validation and proof planning are configured.
- `context_assembly/domain/compilation.py`: `INPUT_UNPINNED`, `EXISTING_DECOMPOSITION` and
  `IDENTITY_EXHAUSTED` are appended to `COMPILATION_HOLD_CODES_v1`. They are appended, so
  no existing code changes rank or meaning.

## Probes (`tests/context_assembly/test_initial_compilation.py`, 33 cases)

| Failure class | Probes |
|---|---|
| 1 derived from pinned requirements, reviewed design, proof; no supplied mapping | `test_derives_initial_candidate_from_pinned_inputs` (compile signature takes no mapping; every field and link; four-category coverage; one record, reservations only), `test_unverified_design_holds_without_candidate`, `test_unresolved_authority_holds` (AC-04), `test_unpinned_input_holds[design/requirement/inspection]` |
| 2 conservation with explicit extent and reverse trace | `test_obligation_omission_holds`, `test_obligation_invention_holds`, `test_missing_proof_plan_holds`, `test_malformed_proof_plan_is_a_typed_hold` |
| 3 deterministic, valid identity/dependencies/custody/budget | `test_derivation_is_deterministic_under_permutation` (AC-06: domain-level identical digest; composed reversed sources/predicates/design/limits give identical identities, edges and mapping), `test_reservation_is_stable_and_not_sort_derived`, `test_changed_input_is_a_distinct_revision`, `test_identity_dependency_and_bound_violations_hold[collision, foreign_unit, foreign_unreserved, foreign_new, exhausted, capability, endpoint, existing]`, `test_malformed_limits_is_a_typed_hold[9 variants]`, `test_regeneration_keeps_one_pointer`, `test_hold_reserves_and_transitions_nothing` |
| 4 validator-only supplied INITIAL mapping cannot complete | `test_validator_only_supplied_mapping_cannot_complete`: the compiler's own units handed to U7 are admitted `VALIDATION_ONLY` / `SUPPLIED_CANDIDATE_NOT_DERIVED`, yet `is_initial_compilation` and `completed()` are false for that report |

## Commands and results (candidate implementation commit `f7a146726f6c19c16c65798dfaa94330cce568c6`)

1. `python3 -B tools/evidence/fx_u8_evidence.py --commit f7a146726f6c19c16c65798dfaa94330cce568c6 --output docs/evidence/wave2-proof-fixtures/FX-U8 --invocation AlienLogicLab/alienintent#117:PRODUCER:13bb35b4-c7a1-4b73-89d0-9813dd64de42`
   - Exit 0, `result` PASS. Run 2026-09-26T09:14:29Z–09:17:01Z, Python 3.12.3, runner
     sha256 `e382e038…a724e`.
   - The runner extracts `git archive <commit>` and runs there. Intact runs exit 0:
     FX-U8 probes (observation `cc5acda0…b491`) and the packet's bounded command
     `pytest -q tests/context_assembly/test_compilation_validation.py tests/execution_coordination/domain/test_contract.py`
     plus the FX-U8 probes (`295bd919…75d4`).
   - Proven-red controls: each applied exactly once (count 1), exited 1, and failed every
     named probe.

     | Control | Class | Mutation | Observation |
     |---|---|---|---|
     | K1 | 1 | design gate bypassed | `36db1840…` |
     | K2 | 1 | ineligible inspection admitted | `e3f5587d…` |
     | K9 | 1 | stale proof-plan design revision admitted | `b1bbd5a7…` |
     | K3 | 2 | unproven acceptance admitted | `2f158d7f…` |
     | K4 | 2 | invented proof obligation admitted | `6cdb7ec2…` |
     | K5 | 3 | persisted reservation ignored | `6415e7ff…` |
     | K6 | 3 | proof enumeration order used | `50e37650…` |
     | K7 | 3 | occupied identity admitted (3 probes) | `7a86e3b5…` |
     | K8 | 4 | completion accepts any INITIAL document | `11f6390d…` |

   - Full records: `FX-U8/run-report.json` (sha256 `53bb22fa…433a`),
     `FX-U8/observations/<sha256>` and `FX-U8/digest-manifest.json`.
2. Feature regression:
   `python3 -B tools/verification/run_feature_regressions.py --base d716552b… --candidate f7a14672…`.
   - Exit 0. The applicable pack `requirement-priority-continuity` passed.
   - Receipt digest `sha256:61a91085…f03f` (not retained; the verifier runtime produces
     its own receipt).
3. Architecture: `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`
   → `PASS: all architecture fitness checks`.
4. Broad regression, once: `python3 -B -m pytest -q` → 25 failed, 1144 passed, 4 skipped.
   - All 25 failures are in `tests/evidence_learning/test_proof_planning.py`
     (`DESIGN_MISMATCH`). The identical 25 fail on an unmodified `git archive` of baseline
     `d716552` (25 failed, 26 passed in that module).
   - Cause: that fixture pins design revision `56676dd9…`, and
     `docs/evidence/wave2-design-contracts.json` changed after it (F4, `aa1603b`).
   - They are pre-existing and outside this node. They are recorded, not repaired.
     Every other test passes.

Tokens and cost are UNKNOWN (not exposed), never zero. The independent verdict is
`PENDING_FRESH_BIU_VERIFIER`, and `live_proof` is `NOT_ESTABLISHED`.

## Independent pre-candidate reviews (fresh read-only Claude subagents)

- **R1: REJECT**, two blocking findings, each reproduced as a failing probe first, then
  repaired:
  - A persisted reservation equal to another requirement's active unit was admitted.
    Now `IDENTITY_COLLISION`.
  - Malformed `authority_limits` raised exceptions. Now retained `INVALID_CANDIDATE`.
  - Non-blocking notes also repaired:
    - The pointer is keyed without reservation state, so regeneration updates one
      pointer.
    - A concurrent identical reservation counts as success.
    - Malformed plans are typed holds.
    - The candidate records its rationale and budget rule.
    - Probes were added for `INPUT_UNPINNED` and regeneration.
- **R2: REJECT**, both R1 repairs incomplete:
  - Identities listed only under `existing_decomposition` were not treated as occupied.
  - Values that are not canonical JSON (inf/nan, sets, int keys) passed validation.
  - Both were repaired test-first.
- **R3: confirmed both repairs** (25 adversarial limits fuzzed; every control verified to
  discriminate). **REJECT** for one runner defect: the FX-U8 probes imported the U7 test
  module, which needs Git at collection.
  - Repaired: the import was removed, and the runner supplies the retained FX-U7
    fixture inputs for the bounded U7 run.
  - Also closed: `RecursionError` on pathological limits, and identity width is capped
    at the grammar's 6.

## Residuals (not claimed as repaired)

- `DERIVATION_RULE_CANDIDATE`: `REQUIREMENT_BOUNDED_UNITS_v1` and
  `INITIAL_IDENTITY_RESERVATION_v1` are candidate design mechanisms subject to
  independent Design Verification. No authority text fixes the unit rule beyond the
  contract's ports and the escalation not to invent.
- `SUFFIXED_IDENTITY_DOES_NOT_BLOCK_BASE`: `WO-000005A` in the snapshot does not stop
  `WO-000005` being assigned. The design text ("lowest unused unsuffixed number") is
  ambiguous and needs a design decision.
- `SNAPSHOT_AND_DECOMPOSITION_CALLER_SUPPLIED`: immutability of existing decomposition
  relies on a complete `existing_decomposition` in `authority_limits`.
- `TRACE_BY_CONSTRUCTION`: `_trace` checks can fire only under code mutation. The
  independent guards for weakening and invention are the plan-versus-requirement checks
  and U7.
- `RACE_CONFLICT_NO_RETRY`: a concurrent compile of an unrelated design yields
  `PERSISTENCE_CONFLICT`, with no blind retry.
- `BASELINE_FX_U4_DESIGN_PIN_STALE`: the 25 pre-existing failures above.

## Non-claims

The following are not claimed:
- split prepare or apply;
- Issue allocation or materialization;
- any lifecycle, release or projection transition;
- SF-REQ-015 lint or assessment;
- SF-REQ-013-AC-05, AC-07 or AC-08 (split/replan);
- obligation satisfaction (coverage is not satisfaction);
- live or operational success from a local result.
