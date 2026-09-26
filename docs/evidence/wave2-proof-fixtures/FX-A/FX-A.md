# FX-A — Wave 2A upstream integration capstone (WO-220211, node A)

**Owner:** `WO-220211` / DAG node `A` (integration capstone; owns no capability), Issue #119.
**Requirements (extent):** SF-REQ-011..016, SF-REQ-051. **Proof level:** `LOCAL_COMPOSED_OR_MECHANICAL`.
**Live proof:** `NOT_ESTABLISHED`.

This is a disposable local fixture for the pinned FX-A proof packet
(`docs/evidence/wave2-execution-packets/WO-220211.proof-packet.md`).

- **Contract input:** `docs/work-units/wave2/WO-220211.md`, sha256
  `9e47a79ee56993ec09c979a9434433a4757368db43378e29f5a651f55d2ee07e`. This is the exact input of the native READY
  assessment `WO-220211.2026-09-26T101031.613435Z`.
- **Release and code baseline:** `c5ef2bc033e712b61da045df47f25b01b40f4dcc` (Factory Director RELEASED record on
  Issue #119).
- **PRODUCER invocation:** `AlienLogicLab/alienintent#119:PRODUCER:c35b931d-a6be-43ba-8232-43c960067adb`, worker
  Morty, branch `b-disp/5fd5d12d-e1f4-4a10-82d2-52f2b819103b`.

The fixture launches no Agent Ready, provider or model. It releases nothing, transitions no lifecycle state and
writes no Issue or Project item.

## Predecessors composed unchanged

| BIU | Stage | Accepted candidate | Landing merge |
|---|---|---|---|
| WO-220201 (#76) | U1 inventory | `43ea5e2b745be02df6aebaf5ba1e328f4c75fa5e` | `fcb65ff` |
| WO-220202 (#80) | U2 ambiguity | `d0eacfb6dd8626b07ff1d99e9c633294f13d9de4` | `70fa714` |
| WO-220203 (#81) | U3 premise evidence | `3e8dc7032dc7e61aac48b66ea9d08a3e789757ad` | `474343a` |
| WO-220204 (#94) | U4 proof plans | `c8ed707efdb0cd70294bfdb6814ec9f9eb71216d` | `44fd55c` |
| WO-220205 (#97) | U5 design admission | `6518d1ef09fc99e8abccf1c6234106f860fce7e6` | `036c5fc` |
| WO-220206 (#110) | U6 coupling checks | `99e238b677da46c7b9d9ad65dd1b9477c28cf9ff` | `f03b0cb` |
| WO-220207 (#101) | U7 compilation validation | `9d97365f58d41147923d3070ac2f838937ed0f4f` | `0588eae` |
| WO-220208 (#117) | U8 initial compilation | `e5a61dcd5746dcc158cf4fe823e4ab4d82d4ed5e` | `610703b` |
| WO-220209 (#105) | U9 readiness consumer | `6eecc30c002785f0cc82f0645fbef601c1503e84` | `7595c9c` |

The harness re-checks that every candidate and landing merge is an ancestor of this candidate. No predecessor source
file changes in this BIU. Issue #76 (WO-220201) is still open on GitHub; its candidate is landed on `main`, and FX-A
records only that ancestry, not its closure.

## Composition

`composition/upstream_integration.py` adds `UpstreamIntegration`. It is wiring only, over one `UpstreamProfile` that
composes every stage (one store, one evidence repository, the FactoryCoordinator lifecycle):

- **Current revision vector.** The design gate is always asked with a vector recomputed from the current inputs of
  every stage. The architecture baseline, premise evidence and direction authority are re-read through the design
  admission's own checks and passed to the unchanged `inspect_design`. A requirement revision counts only when there
  is exactly one definition in the current inventory, approved (eligible) and not retired, and an inspection of that
  same inventory digest reports it `ELIGIBLE_FOR_PREPARATION`. This is stricter than U8 `_pinned`, which relies on
  the inspection alone. Anything else is
  `None`, which no design pins. A candidate's pinned vector is never reused.
- **Governing decisions.** Each is re-read by path, confined to the configured decision root, as
  `path@sha256:<current bytes>`. An unreadable or out-of-root decision is an attributable `LintHold` (duty
  `decision`, field `governing_decisions`) before any assessment.
- **Compilation to readiness.** `candidate()` projects one derived unit of a `CompilationCandidate` into the U9
  readiness candidate:
  - the contract is the unit's contract unchanged;
  - the text is the unit's canonical document;
  - the dependency edges are the compiled edges into that unit.

  `proof_plan()` is the digests of the proof plans the unit was derived from. If any satisfied requirement has no
  plan, it pins none, so lint holds on the proof-plan duty. At read time, a pinned plan that is no longer the
  current feasible U4 plan is a `LintHold` (`verification/proof_plan`).
- **Read time.** `current()` and `assess()` refresh the vector and decisions, then call the unchanged
  `ReadinessAdmission`.

Nothing in the module writes. Every write is the predecessor services' own: `upstream:` and `readiness:` records, and
the ambiguity stage's questions in the existing DecisionInbox (`decision-inbox`), which launches no work.

## Scenarios

The FX-A world is the FX-U8 requirement set (`SF-REQ-911` and `SF-REQ-912` in scope, `SF-REQ-913` already
decomposed as `WO-990300` DONE). It uses:
- the pinned U3 premise mapping and the U5/U6 design contracts;
- the real architecture checker;
- a governing decision file in the disposable profile;
- the U9 scripted producer bound to a disposable fixture package (`FIXTURE_PRODUCER_NOT_NATIVE`).

| Test | Failure class |
|---|---|
| `test_chain_runs_in_order_to_eligibility` | ordered chain (positive) |
| `test_failed_upstream_evidence_stops_before_design_and_compilation[inventory,ambiguity,premise]` | 1 |
| `test_revision_mismatch_invalidates_downstream_readiness[source,approval,ambiguity,decision,design]` | 2 and 4 |
| `test_unavailable_governing_decision_holds_before_assessment` | 2 |
| `test_superseded_proof_plan_invalidates_readiness` | 2 |
| `test_compilation_and_assessment_stay_separate_boundaries` | 3 |
| `test_unbound_producer_holds_before_launch` | 3 |
| `test_integration_mutates_no_lifecycle_or_project_state` | 4 |
| `test_composition_requires_every_stage` | composition boundary |

**Ordered chain.**
1. Inventory is published and inspected.
2. The design's premise is checked against retained evidence, then independently reviewed at that exact revision.
3. Proof plans are derived from reviewed mappings bound to that design revision.
4. Initial compilation derives `WO-000005`/`WO-000006` with no supplied mapping.
5. The integration projects `WO-000005` and lints it. One attempt is persisted before the single launch, and the
   outcome is `ReadinessEligibility`, whose contract digest is the compiled unit's `content_digest`.
6. Unchanged upstream reads the retained READY back.

`WO-000006` depends on the not-yet-materialized `WO-000005`. That compiled edge reaches lint as a `dependency` hold,
and nothing is launched.

**Class 1.** Each case below stops the chain at the design gate. Design applicability is not current, and compilation
is `DESIGN_HOLD`:
- an unapproved source (inventory: never eligible), detail `STALE`;
- a requirement without an authority line (ambiguity: held by the inspection), detail `STALE`;
- a premise requesting `PLATFORM_CREDENTIAL_DENIAL`, which the retained evidence cannot supply. Design admission is
  `MECHANICALLY_HELD`, review is refused, and the detail is `MECHANICALLY_HELD`.

No reservation is made and no producer is launched. Behind the gate, U8's own `_pinned` rule would also refuse the
first two cases (`UNRESOLVED_AUTHORITY`).

**Class 2.** After READY, one revision per case is applied:

| Revision | Downstream result |
|---|---|
| source: requirement text changed and republished | `LintHold architecture/design_applicability STALE`, recompilation `DESIGN_HOLD` |
| approval: the same text republished as `proposed` (revision digest unchanged) | `LintHold ... STALE`, recompilation `DESIGN_HOLD` |
| ambiguity: an independent semantic question holds the requirement at its unchanged revision | `LintHold ... STALE`, recompilation `DESIGN_HOLD` |
| decision: governing decision bytes changed | `Hold STALE_ASSESSMENT` (fingerprint changed) |
| design: FIXED decision statement changed and re-inspected | `LintHold ... REVIEW_REQUIRED`, recompilation `DESIGN_HOLD` |

In every case:
- the stale READY is not reused;
- nothing is relaunched;
- the retained attempt history is byte-identical;
- nothing outside `upstream:`/`readiness:`/`decision-inbox` changes.

A deleted governing decision holds before assessment. A proof plan re-derived from a revised reviewed mapping holds
the READY the same way (`verification/proof_plan`).

**Class 3.** Each case below is refused, with zero launches and zero attempts. This class is mostly composed
predecessor behaviour: the bypass case and its control call U9 `ReadinessAdmission` directly, without the
integration, to show that the boundary holds on its own.
- A compiled candidate that was never assessed reads `NO_ASSESSMENT`.
- A whole compilation document offered as a readiness candidate is a `LintHold`.
- A caller that bypasses the integration with a stale pinned vector is still refused by the design gate inside lint.
- An unbound producer is `CAPABILITY_PROVENANCE_HOLD` before launch.

**Class 4.** The readback covers:
- every store aggregate outside `upstream:`/`readiness:`/`decision-inbox` (lifecycle, release, other aggregates);
- LocalWorkManagement receipts (the Project stand-in);
- recovery reservations.

These stay identical across compile, assess, source revision, read-time hold and recompilation. A spy on
`admit_release` covers both the release domain and FactoryCoordinator's imported name, and it records no call. No retained evidence record carries a release record kind or release flag, and no output is a release
value.

## Negative controls (one per material failure class)

| Control | Class | Mutation (disposable copy) | Required failing assertion |
|---|---|---|---|
| `premise_gate_removed` | 1 | U5 `_premises` never reports an infeasible premise | failed upstream evidence must not compile |
| `stale_source_revision_reused` | 2 | the integration's vector pins the design's own requirement revisions instead of the inventory's | a stale READY must never be reused after a revision |
| `lint_design_duty_removed` | 3 | U9 lint stops consuming design applicability | readiness must not bypass design applicability |
| `reservations_in_lifecycle_namespace` | 4 | U8 keeps identity reservations under `factory:` | the integration must not write lifecycle, release or Project state |

`stale_source_revision_reused` targets the composition seam this BIU adds. The other three apply predecessor
mutations to the composed path. Each records intact 0, fault 1 with the named assertion, and restored 0.

## Labelled deviations, observations and non-claims

- **Carried labels.**
  - `FIXTURE_PRODUCER_NOT_NATIVE`, `FIXTURE_PACKAGE_NOT_AGENT_READY` (U9): positive native-producer proof stays the
    U10 extent (`NATIVE_PRODUCER_POSITIVE_PROOF_U10_EXTENT`). No Agent Ready implementation or rubric is copied.
  - `VALIDATION_ONLY` and `coverage_is_not_satisfaction` stay on the compiled candidate (U8).
- **Candidate text.** The readiness candidate text is the compiled unit's canonical JSON document. Rendering a
  work-unit document for native assessment is not an FX-A claim.
- **Current-vector recomputation.** The integration re-runs the design admission's configured checks at read time.
  With the real `RepositoryArchitectureChecks` this runs the architecture checker per read. FX-A uses the U5 recorded
  checker report (`_Recorded`, computed once per process over `src/alienintent`).
- **Stale reads write upstream history.** A stale read commits the U5 `design.stale` event, which is the U5 contract.
  The test readback excludes only `upstream:`/`readiness:`/`decision-inbox`.
- **Feature-regression registry.** The new `wave2a-upstream-integration-capstone` pack overlaps the
  `requirement-priority-continuity` pack on `src/alienintent/context_assembly/**`. The existing
  `test_priority_feature_pack_is_selected_by_every_owned_boundary` asserted that pack as the only selection. It now
  asserts that pack is selected. The pack's paths and command are unchanged, and packs accumulate at VERIFY by
  design.
- **Not provided:**
  - release or execution admission;
  - lifecycle transition, Project/Issue projection or live operation;
  - U8 SplitTransaction prepare/apply;
  - native Agent Ready invocation;
  - operational acceptance;
  - re-verification of any predecessor beyond its composed behaviour here.

## Independent pre-candidate review (R1) and repairs

A fresh read-only reviewer (a Claude subagent outside this producer's context) confirmed three things:
- all four controls discriminate;
- no predecessor source changes;
- no write outside the upstream namespaces and no release assertion.

It returned **REJECT** with two blocking findings. Both were reproduced as failing probes first
(`[approval]`, `[ambiguity]`), then repaired:

1. **Approval withdrawn at the same text.** `authority_status` is not part of a requirement's revision digest. The
   vector was unchanged, so `current()` and `assess()` kept returning READY while recompilation held
   `UNRESOLVED_AUTHORITY`.
2. **Ambiguity hold at the same revision.** A semantic-review question held the requirement, but the vector never
   consulted the inspection, so the READY was reused.

The repair is one rule. The current revision counts only under U8's `_pinned` conditions (see Composition). The
class 2 control needle moved with it.

Non-blocking findings repaired:
- the release spy now also patches FactoryCoordinator's imported `admit_release`;
- `proof_plan()` pins nothing when any satisfied requirement lacks a plan;
- decision paths are confined to the decision root;
- class 3 is labelled as mostly composed predecessor behaviour.

Recorded, not repaired: `current_vector` fails closed on a broad set of read errors, which yields a hold.

## Confirmation review (R2) and repair

A second fresh read-only reviewer returned **ACCEPT** with no blocking finding. It confirmed:
- B1 and B2 now hold;
- the four controls apply once each and discriminate;
- no predecessor `src` changed.

It also probed further changes, and each held rather than reusing READY:
- the architecture baseline, direction authority or premise evidence changed;
- a requirement removed;
- a later rejecting review;
- a wrong design key.

Non-blocking findings:
- **Superseded proof plan.** A plan re-derived from a revised reviewed mapping kept the old READY, because U9 lint
  checks only that a plan exists and the plan is not in the fingerprint. This was reproduced first
  (`test_superseded_proof_plan_invalidates_readiness`) and repaired: the integration compares the pinned plans with
  the current feasible U4 plans.
- **`decision-inbox` readback exclusion.** The exclusion also covers FactoryCoordinator escalations, which write
  that aggregate. Every such caller also writes `factory:*` state, which the readback sees, so no lifecycle write can
  hide there. This is recorded, not narrowed.
- **`_pinned` wording.** The wording overstated the match with U8 `_pinned`. It is corrected above.

These reviews are preparatory. They are not the fresh BIU verifier verdict.

## Commands

Run all commands under `rtk proxy` with `PYTHONPATH=src:.` from a clean checkout of the candidate.

1. `python3 -B -m pytest -q tests/composition/test_upstream_integration_capstone.py`
2. `python3 -B -m pytest -q tests/context_assembly/test_design_admission.py tests/context_assembly/test_compilation_validation.py tests/context_assembly/test_readiness_consumer.py`
   (the pinned bounded initial command).
3. `python3 -B tools/evidence/fx_a_evidence.py --output /tmp/fx-a-<run-id> --invocation <exact-invocation>`. The
   output directory must be new.

Command 3 records:
- predecessor ancestry and the pinned input digests;
- commands 1 and 2, `tests/context_assembly` with the U3 premise tests, the architecture check and its tests, and the
  registry tests;
- the full Python regression, compared node by node with a full run at the release baseline in a disposable
  worktree;
- `node scripts/check.mjs all`.

It then applies each of the four `CONTROLS` exactly once and performs a composed readback of one chain per revision
kind. Any of the following is a HOLD, never a PASS:
- a dirty source;
- a failed command;
- an unavailable baseline;
- a mutation needle that does not match exactly once;
- a non-discriminating control;
- a failed readback;
- a stopped run, which leaves `run_state: INCOMPLETE`.

Tokens, cost and provider calls are `null` with reason `UNKNOWN`.

The feature-regression pack `wave2a-upstream-integration-capstone` (`tools/verification/feature_regressions.json`)
reruns command 1 whenever a candidate changes any chained stage.

### Feature-regression receipt custody

This follows the landed FX-C rule. `.alienintent/feature-regressions.json` binds the exact candidate SHA, so it is not
tracked. It is written into the checkout of the exact candidate being verified: by the invocation runtime, or by the
verifier at the retrieved SHA:

```
python3 tools/verification/run_feature_regressions.py --base c5ef2bc033e712b61da045df47f25b01b40f4dcc \
  --candidate HEAD --receipt .alienintent/feature-regressions.json
```

The PRODUCER records its own receipt for the published SHA on the Issue for comparison only.

## Evidence

Retained evidence follows the FX-C layout in this directory:
- `execution-record.json`, `run-report.json` and `proven-red.json`;
- `observations/`, named by sha256;
- `digest-manifest.json`.

The retained run is described in the evidence section below once captured. The independent verdict is pending the
fresh BIU verifier.
