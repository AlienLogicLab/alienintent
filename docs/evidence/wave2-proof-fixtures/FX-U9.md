# FX-U9 — readiness lint and retained assessment consumer (WO-220209, U9)

Authority: the Issue #105 RELEASED record (Factory Director episode
`factory-director-e88e1e81df3a416a9dcfed5b0f0cf6e3`, 2026-09-25T04:56:02Z, baseline `04cdd8c`) and the pinned
proof packet in `docs/work-units/wave2/WO-220209.md` § "Pinned proof packet (FX-U9)". Its Director dispositions
table controls over the reviewed draft `WO-220209.proof-packet.draft.md`. Worker Morty. Source, tests and runner were
authored by PRODUCER invocation `AlienLogicLab/alienintent#105:PRODUCER:55583f93-b75f-4ac6-b73c-fbbc1475c8da` on
branch `b-disp/bebbc42b-95c5-48db-a219-154d68b11087`. Proof level is `LOCAL_COMPOSED_OR_MECHANICAL`, on disposable
local state only. Nothing here authorizes release, split apply, lifecycle transition or live operation, and nothing
here invokes Agent Ready, a provider or a model.

## Admission (verified before implementation)

- **Baselines.** The RELEASED baseline is `04cdd8c`. The Director pinned the input digests at `0588eae`. The
  candidate was built on `origin/main` `5d79983`; between `04cdd8c` and `5d79983`, `src/`, `tests/` and `tools/`
  are unchanged (docs only).
- **Pinned inputs.** Every input in the contract's table was recomputed in this worktree and matches at all three
  revisions:
  - packet, allocation, B, D, S, C, REPAIR, RESP, M, PM, T;
  - the U7 contract and the U7 evidence;
  - the contract, `23f5b2ee…`, equal to the READY receipt's `input_sha256`;
  - the four input-4 records;
  - the three input-8 PY-10 blobs.

  The runner recomputes all of this into `baseline_reconciliation_ref` and holds if it does not reconcile. The
  draft is bound at its superseded digest `75a37ddf…`; only its status line differs from the reviewed `9c0f20c5…`.
- **Predecessors.** U5 (#97) and U7 (#101) are DONE with independent ACCEPT receipts. Their source and proof are
  unmodified.

## Implementation (U9 extent only; placement per U-4)

**`execution_coordination`** (vendor-neutral; imports no `context_assembly`):
- `domain/readiness.py`:
  - values: `ProducerBinding`, `InvocationCustody`, `CandidateWorkUnit`, `AttemptMetadata`,
    `SemanticAssessment`, `AttemptFailure`, `ReadinessEligibility`, `Hold`, `HistoricalAssessment`;
  - the `READINESS_CONSUMER_HOLD_CODES_v1` vocabulary;
  - `input_fingerprint`: contract digest, baseline, governing decisions, prerequisite states and verified design
    refs;
  - `recognize`: known direct and MCP parsing per `C#/contracts/4/design_decisions/0`;
  - `provenance_failure`: only correlated invocation custody from the bound producer authenticates;
  - `decide`: read-time applicability;
  - `binding_refusal`.
- `ports/readiness.py`: `ReadinessAssessment.assess`, `AssessmentConsumer` (open/observe/consume and read-back)
  and `SurrogateHistoryReplay`.
- `adapters/assessment_consumer.py`:
  - `RetainedAssessmentConsumer`:
    - raw bytes are stored byte-for-byte as `readiness.assessment.retained`, the event U7's
      `EvidenceAssessmentHistory` reads, before any parsing;
    - each attempt is opened, with its UUID persisted, before invocation;
    - every outcome is a new immutable record linked to its opened record and raw bytes;
    - `readiness:<identity>` is an append-only, CAS-committed pointer with a separate applicability entry and
      invalidation list.
  - `RetainedSurrogateHistory`: digest-checked verbatim retention of historical records.

**`context_assembly`**:
- `domain/readiness.py`:
  - lint (`LINT_DUTY_SOURCES_v1`). Every duty is checked, and the first hold is attributable (duty and field):
    - decision: `fixed_decisions`;
    - boundary: `authorized_scope` and `excluded_scope`;
    - verification: `verification_obligations` and the pinned proof plan;
    - any other BiuContract field: named;
    - architecture: U5 applicability must be `CURRENT_VERIFIED`, otherwise the U5 reason verbatim;
    - dependency: the lifecycle snapshot and the declared upstream edges.
  - `SplitResultSet` and `SplitRouted`.
- `ports/readiness.py`: `ClarificationChannel` and `SplitTransactionHandoff`, the consumer side of U8's port.
- `application/readiness_service.py`: `ReadinessAdmission`. Order: lint, then the binding gate, then the
  reassessment gate, then one attempt, then the route.
- `adapters/readiness_clarification.py`: `InboxClarifications`. Each Agent Ready `owner_clarifications` entry is
  registered verbatim as one `HumanDecisionRequired` with `("resolve","defer")` and no default answer.

**`composition`**:
- `readiness.py`: `resolve_binding`. The product version comes from installed-distribution metadata of the
  distribution that declares the configured executable's console script. No distribution means `UNKNOWN`, which
  blocks admission. Agent Ready modules are never imported.
- `upstream_profile.py`: a compatible addition. `readiness_producer`, `readiness_executable`,
  `readiness_transport` and `split_handoff` compose `readiness`, `readiness_consumer`, `readiness_binding` and
  `readiness_history` behind the same U5 gate and lifecycle as U7.

**Architecture fitness**: `tools/fitness/check_architecture.py` has a new `private-product` check ("Agent Ready
private import", any layer). `tests/test_architecture_fitness.py` has deliberate-violation fixtures for it.

**U-4 binding condition held.** No new cross-group `group.layer → group.layer` pair exists; this is asserted by
`test_no_new_cross_group_import_pair` against the pairs measured at `04cdd8c`. The CLARIFY route reaches
`control_plane.application` only through the `context_assembly.adapters` pair, which already existed.

## Delegated choices recorded (within the pinned dispositions)

- **U-5.** Lint does not consume a U7 `compilation_validation_hold`, and the label is
  `COMPILATION_VALIDATION_HOLD_NOT_CONSUMED_BY_LINT`. U7 validates graph candidates (INITIAL/SPLIT_REPLAN
  documents) under its own `upstream:compilation:` pointer, while U9 lints one BIU contract. No U7 function is
  called.
- **U-7.** The intact binding is a disposable local distribution named `agent-ready`, version `0.1.0rc1`
  (`FIXTURE_PACKAGE_NOT_AGENT_READY`), whose script is written mode 0600 and never executed. The fixture producer
  reports custody bound to it, so this proves the mechanics, not native-producer identity. The producer adapter is
  injected separately from the executable its binding is resolved from (residual
  `PRODUCER_ADAPTER_NOT_CONSTRUCTED_FROM_BINDING_U10`).
- **U-9.** The CLARIFY route reassesses only once every routed question has an attributable `resolve` decision
  from the configured decision actor. A CLARIFY with no owner clarification stays held.
- **U-10.** The SPLIT route hands the raw assessment to the port once. Case (a) holds
  `SPLIT_RESULT_SET_NOT_MATERIALIZED` and never reassesses the original in place. Case (b):
  1. invalidates the named units' current applicability;
  2. lints and reassesses each child and the Integration Parent;
  3. links each new attempt to the SPLIT attempt.

  A result set that U8 materializes later is not re-routed (residual
  `SPLIT_HANDOFF_NOT_RETRIED_AFTER_UNMATERIALIZED`).
- **U-12 codes.** `LINT_HOLD`, `ATTEMPT_FAILURE`, `CAPABILITY_PROVENANCE_HOLD`, `STALE_ASSESSMENT`,
  `SPLIT_RESULT_SET_NOT_MATERIALIZED`, `CLARIFY_PENDING_DECISION`, plus `PREREQUISITE_PENDING`,
  `ATTEMPT_CONFLICT`, `ATTEMPT_IN_PROGRESS`, `PERSISTENCE_CONFLICT` and `NO_ASSESSMENT`. None is an Agent Ready
  disposition.
- **Exit status.** A CLI result needs exit 0. An MCP tool result has no process exit, so `None` is accepted for MCP
  only. Every payload failure fails regardless of exit status.

## Commands (under `rtk proxy`, `PYTHONPATH=src`)

1. `python3 -B -m pytest -q tests/context_assembly/test_readiness_consumer.py`
2. `python3 -B tools/evidence/fx_u9_evidence.py --output docs/evidence/wave2-proof-fixtures/FX-U9 --invocation <invocation>`,
   run against the committed candidate with a new output directory.
3. Regression: `python3 -B -m pytest -q`;
   `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`;
   `python3 -B -m pytest -q tests/test_architecture_fitness.py`; `node scripts/check.mjs all`.

## Controls

- **K01–K30** follow the draft's table. K02 is split per duty and K14 per fingerprint component, so each duty and
  each component has its own discriminating control.
- **K31** proves the U-4 import test is discriminating.
- **K32–K36** are repair controls from the independent review below.

Each control applies exactly one mutation to a disposable copy and is judged on the named test IDs failing by
assertion, or on the checker message for K29/K30. The mutation sites are the runner's `CONTROLS`.

A few mutations are sharper than the draft's wording:
- **K20** makes a timed-out attempt's partial output be treated as a normal exit, so partial READY bytes would be
  admitted.
- **K22** flips the replay's `native_agent_ready` label. The admission refusal of the historical READY is asserted
  separately in P19, and that refusal is the generic missing-custody refusal, not a surrogate-specific one.

## Independent pre-candidate review (R1) and repairs

A fresh read-only reviewer (a Claude subagent outside this producer's context) returned **REJECT** with four
blocking findings. Each was reproduced as a failing probe first (`test_ambiguous_payload_fails`,
`test_raising_producer_records_attempt_failure`), then repaired:

1. **Duplicate JSON member names** resolved last-wins, so `{"disposition":"HOLD",…,"disposition":"READY"}` became
   READY. They are now MALFORMED, direct or inside a text item (K32).
2. **Non-boolean `isError`** (`"true"`, `1`) was not treated as an error. It is now MALFORMED (K33).
3. **`NaN`/`Infinity`, or a raising producer adapter,** left an opened attempt with no outcome, holding
   `ATTEMPT_IN_PROGRESS` indefinitely. Non-JSON constants are now MALFORMED. A raising adapter now fails the attempt
   as `PROVIDER_FAILURE` (K34). Unretainable raw bytes fail it as `RAW_EVIDENCE_NOT_RETAINED`. Any recognition error
   becomes MALFORMED.
4. **Structured and text bodies were not compared,** so a differing text body was dropped, along with its owner
   clarifications. Every supplied body must now agree with the disposition values, otherwise CONFLICTING. This is
   one agreement rule, and K19 disables it as a whole.

Non-blocking findings repaired:
- MCP results without a process exit (K36).
- The CLARIFY annotation re-reads once after a moved pointer, since it is idempotent (K35).
- The editable revision now comes from parsed PEP 610 `direct_url.json`.

The remaining non-blocking findings are recorded as residuals.

## Evidence layout (`FX-U9/`, FX-C1 layout)

The directory holds:
- `execution-record.json`, `run-report.json` and `proven-red.json`;
- `fixture-inputs/`: the PY-10 blobs by ID, the four retained records, `git-facts.json` and `digests.json`;
- immutable `observations/<sha256>`;
- `digest-manifest.json`.

In the execution record:
- Model-launch, provider-call and Agent Ready invocation counts are 0.
- Tokens and cost are `null` with an `UNKNOWN` reason.
- `independent_verdict` is `PENDING_FRESH_BIU_VERIFIER` and `live_proof` is `NOT_ESTABLISHED`.

## Non-claims and residuals

The following are not claimed:
- U8 `SplitTransaction` prepare/apply and result materialization;
- U10 native CLI/MCP adapter conformance and positive native-producer proof;
- SF-REQ-015-AC-06/07 (`UNASSIGNED_IN_DAG`);
- SF-REQ-029 serialization;
- release or lifecycle transition;
- anything about Agent Ready itself;
- re-verification of U7;
- operational acceptance.

The historical `POSTW1-READY-013:WO-220209:1` (BLOCKED, `01af974`) remains history for its own baseline.

Residuals:
- `NATIVE_PRODUCER_POSITIVE_PROOF_U10_EXTENT`
- `SPLIT_TRANSACTION_U8_EXTENT`
- `AC_06_07_TRACE_OWNERSHIP_UNASSIGNED_IN_DAG`
- `SF_REQ_029_SERIALIZATION_NOT_CLAIMED`
- `RUBRIC_COPY_AND_DUPLICATE_ENGINE_NOT_MECHANICALLY_DETECTED`: fitness catches private imports only.
- `OPERATOR_SURFACE_NOT_BUILT`
- `EDITABLE_CHECKOUT_REVISION_FROM_DIRECT_URL_ONLY`
- `PRODUCER_ADAPTER_NOT_CONSTRUCTED_FROM_BINDING_U10`
- `SPLIT_HANDOFF_NOT_RETRIED_AFTER_UNMATERIALIZED`
- `UNKNOWN_INVOCATION_COMPLETION_HELD`: a process crash between open and observe leaves the attempt held
  (`ATTEMPT_IN_PROGRESS`) until its inputs change, per `C#/contracts/4/recovery`.
