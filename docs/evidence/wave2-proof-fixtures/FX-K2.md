# FX-K2 — Canonical multi-role orchestration (WO-220402, SF-REQ-039)

Fixture contract for `docs/work-units/wave2/WO-220402.md`:

- **Contract input.** sha256 `e6d5d1dc…2af2`. This is the exact input of the READY assessment
  `WO-220402.2026-09-25T120043.382139Z`.
- **Baselines.** Admission baseline `e3371827223d1a9abd3c4a1144667de1c61f3778`. Candidate contract `c563f688…e87f2`.
  Release admission ran at `origin/main` `92fae990…` (Issue #115). Code baseline is
  `e49aed5039e6395cb1bb190c729ebcd176e1bf8b`.
- **K1 dependency.** WO-220401 (Issue #113) is DONE and merged at `23c408d`. Its durable correlated read-back
  (`RealWorkerProvider(journal=…)`, `correlated_outcome`, the coordinator's `_correlated` gate) is present at the code
  baseline. K2 consumes that seam.
- **Scope.** Proof level `LOCAL_COMPOSED_OR_MECHANICAL`, on a disposable local profile only. No live store, provider,
  model, network, credential or RAI is used. A local PASS is not operational acceptance.

## Design Verification (WorkerOutcome capacity)

K1 showed that `WorkerOutcome(kind, candidate)` carries every observable the *producer* transition needs. K2 adds two
roles, and each needs one observable that the contract has no carrier for:

| Required observable | Why no existing field carries it |
|---|---|
| Verifier **findings** ("rejection records findings") | `kind` is one token and `candidate` is a `CandidateRef`. `escalation` is a `HumanDecisionRequired`, which is a request for authority, not a finding. |
| Closure **receipts** ("closure records only actions actually performed/read back") | The coordinator must know *which* actions were read back. That is a set of names, not a kind. Inferring the set from the contract is exactly what the fixed decision forbids. |

The contract is therefore extended by two optional, defaulted fields: `findings: tuple[str, ...] = ()` and
`receipts: tuple[str, ...] = ()`. The request side gains `WorkerInvocation.role: str = "PRODUCER"` and
`candidate: CandidateRef | None = None`, which name the role and the exact candidate a verifier or closure invocation
acts on. Every existing caller and fake is unchanged in meaning. Role, invocation, attempt, contract, candidate,
findings and receipts stay in the existing records:

- the invocation journal (`invocation-started`/`invocation-outcome`, now written with the invocation's own role);
- the effect payload (`role`);
- the execution aggregate `factory:<id>` (`role`, `producer_correlation`, `rejections`, `findings`, `verdict`,
  `receipts`, `outcome_kind`, `invocation_candidate`).

No `RoleOutcomeRecord` or sidecar owner is added.

## Orchestration (Execution Coordination)

`FactoryCoordinator` routes one canonical role per nonterminal stage (`ROLE_BY_STAGE`): IMPLEMENT→PRODUCER,
VERIFY→VERIFIER, ACCEPT→CLOSURE. Each role runs as its own launch under its own correlation `launch:<id>:<revision>`,
with its own reservation, effect and durable read-back through the K1 gate. `_advance` is the only place a role
outcome becomes a lifecycle transition. Recovery reuses it after a restart.

- **Producer** `success`: the control-plane custody re-check (`verify_in_fresh_process`) runs, then `verify`. The
  result is VERIFY and nothing further. The success-collapse path (`_completed_for_outcome`) is removed.
- **Verifier.** The outcome must be `accept` or `reject`. It must name the exact custodied candidate (kind, identity,
  digest) and come from a correlation distinct from the recorded `producer_correlation`. A `reject` must also carry
  findings. Anything else holds through the existing authority-block and decision inbox path. `failure`/`timeout`
  keep their existing terminal meaning.
  - `reject`: findings are recorded with source, verifier correlation and candidate identity. Then `rework` returns to
    IMPLEMENT.
  - `accept`: `review`, then a trusted policy verdict. `evaluate_verdict` must see the contract's required evidence plus
    `independent-verifier-accepted`. A REJECT verdict is recorded as a `review` finding and reworks. ACCEPT uses
    `accept`.
- **Budget.** Each rejection increments `rejections`. At `budget_policy.maximum_attempts` the item fails terminally
  (`failure`, `hold_reason=attempt-budget-exhausted`) instead of looping.
- **Closure.** The outcome must be `closed` for the exact candidate. Its **receipts** must cover every
  `required_closure_actions`; otherwise the item holds at ACCEPT (`closure-receipts-incomplete`). DONE records the
  receipts, never the contract's list.
- Only producer dispatches count as `RunSummary.dispatched`. Release admission and `propose_release` guard only the
  producer. A verifier or closure invocation acts on admitted work and never resets it. Fields the lifecycle needs
  after a hold (`producer_correlation`, `rejections`, `findings`, `verdict`) survive parking, decisions and
  re-admission.

## Worker boundary (Invocation Runtime)

`RealWorkerProvider.start` stays the one boundary for real and deterministic workers:

- **PRODUCER** is unchanged.
- **VERIFIER** (`_evaluate`) first checks the per-invocation grant (`process-control`), provider capability and a
  VERIFIER reservation. It then retrieves the exact candidate into a fresh `verifier-<correlation>` clone.
  `GitSourceControl.retrieve_for_verification` now checks out the exact revision, so the verifier sees the tree. The
  worker process runs as VERIFIER there, and `read_verdict` reads `.alienintent/verdict.json`: `{verdict, revision,
  findings}`.
  - A verdict for another revision reads as `verdict-miscorrelated`. A missing or malformed verdict reads as
    `verdict-missing` or `verdict-malformed`.
  - A candidate that already carries a verdict file reads as `verdict-preexisting`, so it cannot approve itself.
  - The coordinator holds on each of these kinds.
- **CLOSURE** (`_close`) re-reads the accepted revision from the remote into a fresh `closure-<correlation>` clone. Only
  on success does it receipt `candidate-published`. It claims no other action.
- `correlated_outcome` now checks the invocation's own role in both journal records. For verifier and closure
  outcomes, the record must name the exact candidate the invocation was given. Findings and receipts must be string
  lists. The coordinator's `_correlated` gate compares kind, candidate, findings and receipts.
- `ScriptedWorkerProcess` (the Deterministic Test Worker) gains the verifier steps `accept`, `reject` and
  `no-verdict`. Each writes, or withholds, a real verdict for the checked-out revision. A verifier with no remaining
  step renders no verdict, and a step run under the wrong role is refused. It still holds no store and writes no
  lifecycle field.

## Fixture

`tests/execution_coordination/k2_fixture.py` composes the production `OfflineProfile` from:

- a real SQLite store and `LocalWorkManagement`;
- the production `RealWorkerProvider` with `JsonlInvocationJournal`;
- `ScriptedWorkerProcess` behind the Worker Port;
- `GitSourceControl` over a local bare remote;
- `GitWorktreeAdapter`.

The clock and git dates are injected (`1758542400`). The child environment is stated in full and holds no credential.
The contract is the S0 probe contract, re-pinned to `K2-PROBE` with `maximum_attempts: 2`. Reopening a root is a
restart. Faults are injected only at the journal or process boundary, or by killing the composing process:
`python -m tests.execution_coordination.k2_fixture crash-after-verifier-outcome` exits 17 right after the durable
verifier outcome.

## Material classes, probes and controls

Probes are in `tests/execution_coordination/test_role_orchestration.py`.

| Class | Probes | Control (fault → red) |
|---|---|---|
| 1. Producer success advances only to VERIFY | `test_producer_success_advances_only_to_verify`; `test_the_full_lifecycle_is_three_distinct_role_invocations_with_exact_custody` | `success_collapse_restored`: the pre-K2 collapse is put back in the producer branch |
| 2. Distinct verifier; rejection → IMPLEMENT under budget | `test_verifier_rejection_records_findings_and_repairs_through_implement`; `test_rejection_beyond_the_attempt_budget_is_terminal_failure`; `test_a_candidate_that_carries_its_own_verdict_is_not_self_approved` | `rejection_budget_unenforced` |
| 3. REVIEW/ACCEPT, closure receipts only | `test_closure_records_only_actions_actually_read_back` (a required action no adapter performs holds at ACCEPT); `test_accepted_closure_carries_the_read_back_receipts` | `closure_inferred_from_contract` |
| 4. Missing/duplicate/stale/miscorrelated evidence holds | `test_missing_duplicate_stale_or_miscorrelated_role_evidence_holds[missing\|duplicate\|stale\|role\|no-verdict\|stale-verdict\|closure-receipts]` (every process run succeeds); `test_restart_after_the_verifier_outcome_recovers_its_role_without_re_running_it`; `test_restart_after_a_recorded_rejection_recovers_without_wedging_the_profile` | `role_observables_narrowed` (applied to `[closure-receipts]`) |
| 5. Shared boundary, no shortcut or sidecar owner | `test_deterministic_and_real_workers_share_the_production_boundary`; `test_no_parallel_role_outcome_state_owner_exists_in_source`; the real CLI child worker reaches DONE through the same boundary in `tests/invocation_runtime/test_real_worker_outcome.py` | `scripted_lifecycle_write` |

On the in-run path, `[stale]` and `[role]` are held by both layers: `correlated_outcome` and the coordinator's
exact-candidate check. The class-4 control therefore targets the one K2 comparison with no second layer, the
findings/receipts observables. This keeps one control per class.

## Commands (all under `rtk proxy`)

1. `python3 -m pytest -q tests/execution_coordination/test_role_orchestration.py tests/execution_coordination/test_factory_coordinator.py tests/invocation_runtime/test_real_worker_outcome.py tests/composition/test_sandbox_run_profile.py`
2. `python3 -B tools/evidence/fx_k2_evidence.py --output <new-dir> --invocation <exact-invocation> --baseline <code-baseline>`.
   This runs (1), `check_architecture.py --check all`, `tests/test_architecture_fitness.py`, the full pytest suite
   and `node scripts/check.mjs all`. It then applies each control once to a disposable copy. A full-suite failure is
   admissible only when the same nodes fail at the code baseline in a detached worktree.

## Compatibility edits outside the new surface

Removing the collapse means every existing fake or scripted worker must now answer the verifier and closure roles.
None of these edits weakens a producer-side assertion.

- `tests/execution_coordination/test_factory_coordinator.py`
  - `ScriptedWorker` answers each role. Its verifier accepts the exact candidate given, and its closure receipts the
    required actions. `dispatched` still counts producer dispatches.
  - `test_success_requires_policy_evidence_and_readback` expected an uncaught `LifecycleError`. It now asserts the
    canonical outcome: a REJECT review verdict records a `review` finding, returns to IMPLEMENT and exhausts the
    budget.
  - The projection fault test now sees VERIFY (1) and ACCEPT (3) before the DONE (4) fault.
- `tests/execution_coordination/test_decision_inbox.py`: `EscalatingWorker` escalates only as producer.
- `tests/invocation_runtime/k1_fixture.py` and `test_real_worker_outcome.py`
  - The K1 child worker gains a verifier branch that accepts the checked-out revision.
  - `outcome_records()` defaults to producer records. DONE is recorded as `closed`, and the producer correlation is
    read from `producer_correlation`.
  - The K1 probes are otherwise unchanged.
- `tests/composition/test_sandbox_run_profile.py`: the rehearsal `worker/run.sh` accepts as verifier, and the dispatch
  observers count producer invocations.
- `tests/composition/test_offline_proof.py`
  - The in-process S0 probes script `("success", "accept")` and expect distinct projections and role journal events.
  - The frozen-kernel guard now lists `git_source_control.py` as changed.
  - The guard asserts that the immutable S0 manifest, which scripts no verdict, holds at VERIFY over the current
    kernel: P1/P3/P4/P7/P11/P12/P13 no longer PASS and `success_collapse_limitation.observed` is false.
  - S0's positive proof stays retained at its historical source (`0515444b`).
- `tools/evidence/fx_k1_evidence.py` is historical tooling. Its mutation needles are bound to the K1 source
  `db4585a`, and several of those lines changed here, so it is not rerun at this revision.

## Independent pre-verification review and repairs

A read-only reviewer checked the first candidate `00eba91`. It confirmed three properties:

- ACCEPT is reachable only through a verifier `accept` on the exact candidate, from a correlation distinct from the
  producer's.
- DONE requires receipts covering every required closure action.
- Role routing adds no new unbounded dispatch loop.

It raised these findings:

- **HIGH — repaired.** A crash after a verifier (or review) rejection was recorded, but before the reservation was
  released, wedged the whole profile on restart. The rework clears the state's candidate, so recovery rebuilt the
  verifier invocation with no candidate. The durable record then did not correlate, and the already-confirmed effect
  could not be parked, so every later `start()` returned `capacity-unavailable`.
  - Repair: the exact candidate each invocation was given is retained as `invocation_candidate` in the prepared and
    recorded execution aggregate, and recovery re-asks with it.
  - Regression probe: `test_restart_after_a_recorded_rejection_recovers_without_wedging_the_profile`. It was red before
    the repair (`capacity-unavailable`) and is green after.
- **MEDIUM — disclosed; returned to its owner.** `DecisionInbox` records one decision per work item (`decision:<id>`
  is write-once, `control_plane/application/decision_inbox.py`). After an authorized hold, a second hold on the same
  item (for example at VERIFY, then at ACCEPT) cannot receive a second decision; only operator `cancel` clears it.
  - The write-once rule predates K2. K2 makes several holds on one item ordinary.
  - Decision identity belongs to the Control Plane decision-inbox owner (WO-220301). K2 does not change it.
  - A single hold, whether at VERIFY or ACCEPT, followed by authorize re-admits correctly: the reviewer reproduced
    that.
- **LOW — disclosed.** Two compositions do not enforce the full K1/K2 read-back correlation:
  - the S0 `ScriptedWorkerProvider`, whose journal read-back returns the last record for a correlation;
  - the journal-less `RealWorkerProvider`, which reads back from memory, as in the sandbox run profile.

  There, duplicate and role miscorrelation are not caught at read-back. The coordinator still checks the exact
  candidate for verifier and closure outcomes. The durable path is the opt-in `journal=` composition, as K1 disclosed,
  and it is what FX-K2 composes.
- **LOW — disclosed.** `maximum_attempts` bounds rejections (K2) and also, within one producer invocation, process
  retries (`RetrySchedule`, pre-existing). In-invocation retries do not count against the rejection budget.
- **LOW — disclosed.** Profile grant functions issue PRODUCER-role grants, and `_evaluate` checks the grant's
  invocation and `process-control` but not its role. A verifier that re-pushes the candidate branch is caught at
  closure: the read-back mismatch holds at ACCEPT.

## Disclosures

- The sandbox run profile (`SandboxRunProfile`) now requires its worker command to act as VERIFIER when
  `ALIENINTENT_ROLE=VERIFIER`. An unmodified external `worker/run.sh` renders no verdict, so the item holds at VERIFY.
  That is the no-collapse behaviour. It is not a claim that any shared or live profile satisfies multi-role proof.
- The real verifier protocol is the verdict file above. Wiring it to the configured Codex verifier is live activation
  and is not authorized here.

## Non-claims

- No live or shared-profile activation. No new lifecycle owner or sidecar outcome state subsystem.
- No closure action other than `candidate-published` is claimed as performable by the real adapter.
- Token and cost are UNKNOWN, never zero. No provider is composed.

## Retained run

`FX-K2/` holds the harness run for invocation `AlienLogicLab/alienintent#115:PRODUCER:3bb0bafe-3a4a-4b71-b428-416160e01ecb`.

- Source: clean committed revision `90f7fb9546c0e94c04c5d470d7ea0a104c5df5d5`. Code baseline `e49aed5`.
- Result: exit 0, no holds.
- Checks: the focused suite, `check_architecture.py --check all`, the architecture fitness tests and
  `node scripts/check.mjs all` all exit 0.
- Controls: all 5 discriminate (intact 0, fault 1, restored 0, with the named assertion in the fault output).
- Full suite: 25 nodes fail, all in `tests/evidence_learning/test_proof_planning.py`. The same 25 nodes fail at the
  code baseline in a detached worktree, so they are recorded as the residual `PREEXISTING_BASELINE_FAILURES`, outside
  the K2 extent.
- Provider calls: 0. Tokens and cost: UNKNOWN.
- Independent verdict: pending (fresh BIU verifier).
