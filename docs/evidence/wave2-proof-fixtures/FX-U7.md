# FX-U7 — compiler validation and conserved obligation mapping (WO-220207, U7)

Authority: Issue #101 RELEASED comment (Factory Director episode
`factory-director-e3cc2e8799f34746a8b1f77b761ccfee`, 2026-09-25T02:08:42Z) and the
pinned proof packet in `docs/work-units/wave2/WO-220207.md` § "Pinned proof packet
(FX-U7)". Worker Morty (`morty-worker`). The source, tests and runner were authored
by PRODUCER invocation
`AlienLogicLab/alienintent#101:PRODUCER:34c025ad-5b9a-401c-a007-a6f2c39fc780`
(worktree branch `b-disp/40d43c3f-3ac7-44ca-8af4-a0a56a547884`). That invocation ended
with `DURABLE_RESULT_MISSING` and left the work uncommitted. The replacement invocation
`AlienLogicLab/alienintent#101:PRODUCER:9a062e63-2fd1-4e7a-aa36-904db870a5f1`
(branch `b-disp/d48a98bd-ac48-4f98-9745-2622c4e57064`) carried the same working-tree
files forward byte-for-byte (sha256 compared), re-ran every check, obtained the
independent re-review (R2) below, committed the candidate and produced the evidence.
Proof level `LOCAL_COMPOSED_OR_MECHANICAL`; disposable local state only. Nothing here
authorizes release, split apply, Issue allocation or live operation.

## Admission (verified before implementation)

- Admission baseline `7b6e19c4a17f1d797f61c99edafadd4857940dd6` (= `origin/main` at
  dispatch). Contract `0e05a120…0390e9525`, packet `5c4a88eb…532efde` and allocation
  `2e297c63…6f810ac9` were recomputed and equal the RELEASED record and the Agent Ready
  `input_sha256`.
- U5 (#97) is DONE with an independent ACCEPT and closure receipts (cited in the
  contract's Admission row). U5 source and proof are unmodified.
- **Baseline reconciliation (Agent Ready first-step risk).** The contract header names
  `7a18e0b`; the proof packet's digests were verified at `e36e335`; admission is
  `7b6e19c`. The contract's pin revision is `5a79622`, the Director pin commit that
  added this packet. Every other input is pinned at `e36e335`. At `7b6e19c`, C, S, P5,
  contract, packet and allocation are byte-identical to their pins. D and B differ from their `e36e335` pins, but only in U9 pointers
  (`D#/acceptance_trace/17,18,21`, `/enforcement_obligations/9`, `/proof_fixtures/11`,
  `B#/bius/11`, from `ffbc993`, the WO-220209 repair). Every U7 pointer
  (`D#/nodes/9`, `/proof_fixtures/9`, `/acceptance_trace/10..12`,
  `/enforcement_obligations/3`, `B#/bius/9`) is byte-identical. The pinned whole-file
  digests are therefore verified against the `e36e335` blobs, not substituted. Between
  `e36e335` and `7b6e19c`, `src/tests/tools` changed only for WO-220302 (context
  reconstruction) and WO-220304 (monitor health); no interface this unit consumes
  changed. The runner recomputes all of this into `baseline_reconciliation_ref` and
  holds if it does not reconcile.

## Implementation (U7 extent only)

- `context_assembly/domain/compilation.py`: frozen values (`DependencyEdge`,
  `CompilationHold`, `ValidationReport`) and the pure validators `validate` (INITIAL)
  and `validate_split` (SPLIT_REPLAN). Holds use the `COMPILATION_HOLD_CODES_v1`
  vocabulary, name every offending ref, and are ordered by value, never by input order.
  The split rules are `C#/contracts/2/design_decisions/4` candidate mechanisms, labelled
  `PHASE5_CANDIDATE_MECHANISMS_NOT_INDEPENDENTLY_DESIGN_VERIFIED`.
- `context_assembly/ports/compilation.py`: `DesignGate` (satisfied by U5
  `DesignReadiness`), `DesignDecisions`, `OpenQuestions` (satisfied by
  `AmbiguityService`), `DependencyLifecycle`, `AssessmentHistory`.
- `context_assembly/application/compilation_validation_service.py`: the design gate,
  then open questions, then dependency authority, then validation. Each result is kept
  as an immutable S1 `Observation` (`compilation.validated` / `compilation.held`) with a
  CAS `upstream:compilation:<digest>` pointer. The service never writes `factory:*`,
  `release:*`, reservations, projections or decomposition state.
- `context_assembly/adapters/compilation_repository.py`: `EvidenceAssessmentHistory`,
  which reads back retained prior assessments and never writes.
- `composition/compilation.py` plus a compatible `UpstreamProfile(dependency_lifecycle=…)`
  addition: `CoordinatorDependencyLifecycle` over `FactoryCoordinator.state().stage`,
  and `VerifiedDesignDecisions`, which reads FIXED decisions from the exact verified
  design revision.
- **D-1 condition.** `context_assembly` gains no new cross-group import pair. New
  modules import only `execution_coordination.domain`/`ports` and `evidence_learning`.
  The coordinator is injected at composition. This is asserted by
  `test_context_assembly_adds_no_cross_group_import_pair`.

## Fixture decisions (implementation-local, within the pinned dispositions)

- **Family A (SWF-33 replay).** The four pinned blobs are extracted with
  `git cat-file blob`, and a digest mismatch exits 2 before any probe. Destinations
  resolve through `P5#/destination_bindings`. The integration parent must retain every
  clause byte-exactly. A child extent is either the verbatim clause or an elaborated
  extent under the same obligation ID (the three shared rows in PY-09B). Edges use
  `HISTORICAL_EDGE_SET` semantics: only preserved and added edge sets are asserted,
  never a relabelled historical predicate (N-2). The P13[bound] elaboration binding
  names `docs/decisions/2026-09-21-py10-transport-split.md`
  (sha256 `71c2fce2…10e27e0`) for exactly `PY-10-SCOPE-01` and
  `PY-10-READINESS-PREREQUISITES`. Its semantic adequacy is the residual
  `SWF33_ELABORATION_BINDING_INTERPRETIVE`.
- **Family B (synthetic).** `O=WO-990100`, children `WO-990101`/`WO-990102`,
  downstream `WO-990110` and predecessors `WO-990001`/`WO-990002`, with a synthetic
  issuer (N-5). The weakened-clause variants remove a conjunct from a parent clause
  after byte 20. K15 relaxes the comparison to a whitespace-normalized 20-character
  prefix, which discriminates both P14[weakened_clause] and P13[unbound]; both SWF-33
  non-verbatim rows share a 20-character normalized prefix with their source.
- A dependency whose issue is `CLOSED` but whose lifecycle stage is not DONE is
  unsatisfied. An `OPEN` issue whose lifecycle stage is DONE is satisfied. The issue
  projection is never read as lifecycle authority.

## Commands (under `rtk proxy`, `PYTHONPATH=src`)

1. `python3 -B -m pytest -q tests/context_assembly/test_compilation_validation.py`
2. `python3 -B tools/evidence/fx_u7_evidence.py --output docs/evidence/wave2-proof-fixtures/FX-U7 --invocation <invocation>`,
   run against the committed candidate with a new output directory.
3. Regression: `python3 -B -m pytest -q`;
   `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`;
   `node scripts/check.mjs all`.

Controls K01–K34 are the packet's table. K35–K42 are repair controls added after the
first independent review (R1), and K43 after the re-review (R2), both below. The mutation sites are in the runner's
`CONTROLS`. Each control applies exactly one mutation, and each is judged on the named
failing test IDs, or on the checker's `domain imports adapters` for K34. A control that
does not discriminate, a count other than 1, or a missing observation is a HOLD.

## Independent pre-candidate review (R1) and repairs

A fresh read-only reviewer (Claude subagent, not this producer's context) returned
**REJECT** with four blocking findings. Each finding was reproduced as a failing probe
first and then repaired. Each repair also has a control:

1. Duplicate `(from,to)` edges were order-dependent and could admit a weakened
   predicate. They are now `INVALID_CANDIDATE` in any order (K35).
2. Open questions were only checked against the candidate's self-declared
   `requirements`. Linked requirements now include every unit or original contract's
   `satisfied_requirement_ids` and every requirement obligation (K36).
3. The original graph and frozen inventory were taken from the proposal itself. With a
   contract original:
   - incoming edges must equal the original's `dependencies`, else
     `ORIGINAL_GRAPH_MISMATCH` (K37);
   - every obligation-field clause must be frozen, else `OBLIGATION_LOST` (K38);
   - contract clauses must match a whole entry, not a substring (K41).

   The Markdown original of family A keeps a supplied inventory (residual
   `ORIGINAL_INVENTORY_SUPPLIED_FOR_MARKDOWN_ORIGINAL`).
4. An omitted `dependencies` field skipped the declared-edge check. It now declares
   none (K39).

Non-blocking repairs:
- `operation_id` is required (K40).
- Malformed shapes are typed `INVALID_CANDIDATE` holds, never exceptions. They are
  named by value, not by index.
- Split validation no longer requires DONE predecessors. A split is planning, not
  execution eligibility. The label is `DEPENDENCY_SATISFACTION_INITIAL_ONLY`, and the
  declared-edge rule still applies (K42).
- Each named node must now fail by assertion.
- K23's mutation now genuinely accepts the redirect.
- The D-1 test also inspects plain `import` statements.

## Independent re-review (R2) and repair

A second fresh read-only reviewer (Claude subagent, not the producer's context)
confirmed that all four R1 blocking findings are repaired. It returned **REJECT**
for one new blocking defect:

- **B1.** Take a split whose original is a contract, and give one result no
  `BiuContract` (either a plain `body`, or no contract and no mapping rows). That
  result was admitted, and `bounds: WITHIN_ORIGINAL` was reported without ever checking
  its budget, capabilities, scope or declared edges. Now every result under a contract
  original must carry a contract; otherwise the hold is `INCOMPLETE_CONTRACT`
  (`<unit>:contract`). Both variants were watched failing first
  (`test_review_r2_result_without_contract_refused`). The discriminating control is K43.

R2's non-blocking notes are recorded as residuals, not claimed as repaired:
- `DOWNSTREAM_EDGES_SUPPLIED_BY_PROPOSAL`: a contract original carries no outgoing
  edges, so downstream edges come from the proposal and are bound only by
  `graph_revision` inside the authority digest.
- `ELABORATION_APPROVAL_DIGEST_NOT_RECOMPUTED`: the validator does not recompute an
  approval's decision digest from the decision file. The pinned file does match
  `71c2fce2…`.
- `CHILD_EXTENT_ACCEPTS_OBLIGATION_ID`: a child extent passes if it contains the
  obligation ID. The integration parent must still hold every non-approved clause
  byte-exactly.
- `MALFORMED_INPUT_HOLD_REF_ORDER_DEPENDENT`: with more than one malformed edge, the
  `INVALID_CANDIDATE` ref names the first one. Well-formed inputs are
  permutation-independent (P23).

A runner defect was also found in this invocation's first evidence run and repaired
before the retained run. `FX_U7_FIXTURE_INPUTS` was passed as a relative path, while the
controls run with the disposable copy as their working directory, so every control
exited 4 at collection. The runner now resolves the path. That first run was discarded
and was never retained.

Additional residuals:
- `EXPECTED_VERSIONS_APPLY_TIME_NOT_CHECKED`: `expected_versions` is carried but
  checked only at apply time (U8).
- `GRAPH_REVISION_BINDING_WITHIN_PAYLOAD_DIGEST`.

## Evidence layout (`FX-U7/`, FX-C1 layout)

`execution-record.json`, `run-report.json`, `proven-red.json`, `fixture-inputs/`
(blobs by ID with `digests.json`), immutable `observations/<sha256>` and
`digest-manifest.json`. Tokens and cost are `null` with an `UNKNOWN` reason. The
independent verdict is `PENDING_FRESH_BIU_VERIFIER`, and `live_proof` is
`NOT_ESTABLISHED`.

## Non-claims

The following are not claimed:
- initial derivation;
- split prepare or apply, identity reservation, invalidation records, atomic apply,
  readback or recovery (U8);
- SF-REQ-015 lint or assessment;
- `013-graph-coverage`;
- any SF-REQ-013-AC-06, AC-07 or AC-08 ownership (`UNASSIGNED_IN_DAG`);
- the active-invocation fence (N-10);
- Phase 5 approval.

Residuals: `SPLIT_APPLY_AND_DERIVATION_NOT_PROVEN_U8_EXTENT`,
`AC_06_08_TRACE_OWNERSHIP_UNASSIGNED_IN_DAG`, `BUDGET_ENVELOPE_PARTITION_UNPROVEN`,
`ACTIVE_INVOCATION_FENCE_NOT_PROVEN_BY_FX_U7`, `SWF33_ELABORATION_BINDING_INTERPRETIVE`,
plus the R1/R2 residuals above.
