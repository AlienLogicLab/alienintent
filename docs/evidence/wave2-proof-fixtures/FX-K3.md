# FX-K3 — Shared-profile role binding and compatibility (WO-220403, SF-REQ-039)

Fixture contract for `docs/work-units/wave2/WO-220403.md`:

- **Contract input.** sha256 `1e80ad27…17c0`. This is the exact input of the READY assessment
  `WO-220403.2026-09-25T193627.519498Z` (work-unit revision `e6945a7`).
- **Baselines.** Release baseline `178732f464a516f0cd6c108f18e25f1c6b978445` (`origin/main` at the Factory Director's
  RELEASED record on Issue #120). It is also the code baseline. `origin/main` has since gained `b9fcb09`, which touches
  only `tools/live/release_admission*`, outside this extent.
- **K1 dependency.** WO-220401 (Issue #113) is DONE. Candidate `4cb841734a0dadaa66b0574b544b6f9a53da1e0f`, merged at
  `23c408d6bea3cabea49c0f02e3157b3470f16416`. Its durable journal (`RealWorkerProvider(journal=…)`) and
  `correlated_outcome` are consumed unchanged.
- **K2 dependency.** WO-220402 (Issue #115) is DONE. Candidate `81d9cc57392a0d9fc7f8d75b8618ed446df2fd48`, merged at
  `975e128cf1b398cb5babf50bf7490ac2e6493df1`. Its `ROLE_BY_STAGE` routing, `_advance` and exact-candidate checks are
  consumed. One lifecycle-neutral rule is added (see below).
- **Scope.** Proof level `LOCAL_COMPOSED_OR_MECHANICAL`. It runs on the actual `SandboxRunProfile` and
  `GitHubProfileComposition` constructors, over local transports only. No live store, provider, model, network,
  credential or RAI is used. A local PASS is not operational acceptance, and it activates nothing.

## Pre-implementation seam check (per the READY assessment's next action)

K1 and K2 are DONE at the pinned baseline. The K1 seam was then checked for the three states the recovery invariant
must observe:

| State | What the existing seam exposes | Consequence here |
|---|---|---|
| Missing terminal result | The journal holds exactly one `invocation-started` and no `invocation-outcome` for the correlation. | Observable from existing records. It is read, never inferred. |
| Conclusive invocation death | `WorkerProcess.cancel(id)` answers `already-finished`/`cancelled` with `quiescent=True`, but only in the process that ran the invocation. | Conclusive only while the owning process is alive. |
| UNKNOWN ownership | A restarted process's adapter answers `unresolved-recovery`, `quiescent=False`. The journal records no owner or supervisor identity. | After a restart, ownership stays UNKNOWN. That is a hold, not a replacement. |

Two gaps are genuine and are **returned to the K1 / Invocation Runtime owner unrepaired** (see Disclosures). Neither
blocks the composition invariant, because both fail closed into UNKNOWN.

## Design Verification (WorkerOutcome capacity)

No field is added to `WorkerOutcome` or `WorkerInvocation`. Every K3 observable already has a carrier:

- Role and invocation come from `WorkerInvocation.role` and `correlation_id`.
- The grant comes from `CapabilityGrant.role`, `invocation_id`, `issuer`, `target` and `operations`.
- Custody comes from `WorkerInvocation.candidate`, the execution aggregate (`candidate`, `invocation_candidate`,
  `producer_correlation`, `role`), the claimed effect payload (`work`, `role`) and the producer's journaled outcome.

A conclusively missing result is one more outcome **kind**: `MISSING_TERMINAL_RESULT = "missing-terminal-result"`
(constant in `execution_coordination/ports/worker_provider.py`). It is retained in the existing journal as an
`invocation-outcome` record against the original correlation, and read back through K1's unchanged
`correlated_outcome`. It adds two extra fields that correlation ignores: `ownership` (the adapter's attested answer)
and `phase`.

No `RoleOutcomeRecord`, `OutcomeEvidencePort` or sidecar owner is added.

## Composition binding (`composed_role_bindings`)

`src/alienintent/composition/role_binding.py`: `RoleBindingGuard` is a stateless WorkerProvider. Each shared profile
hands it to its coordinator, and it wraps the configured provider. Before any launch it refuses, returning
`binding-refused` and launching and journaling nothing, unless every check below holds:

- **Durable outcome binding.**
  - The provider's `journal` is the very journal the profile composed. The refusal is `…-missing` when there is none
    and `…-disconnected` when it is a different journal.
  - The journal is readable.
  - The correlation is fresh in the journal.
  - The invocation's contract digest is the contract's.
- **Role authority.** The grant the provider will launch under (`grant_for`) names this invocation, **this role**,
  this profile and target. It must also cover `ROLE_OPERATIONS[role]`: PRODUCER `{process-control, git-write}`,
  VERIFIER `{process-control}`, CLOSURE `{git-read}`.
- **Exact candidate custody.**
  - The prepared execution aggregate and its single claimed effect name this role and work item.
  - The stage routes to this role.
  - The invocation's candidate is the prepared `invocation_candidate`.
  - A producer carries no candidate.
  - A verifier or closure candidate must meet four conditions:
    - it is the custodied candidate;
    - it is a read-back-proven source revision;
    - it comes from a recorded `producer_correlation` distinct from this one;
    - it is the candidate that producer invocation durably published, per `correlated_outcome` on the producer's
      branch.
- **Replacement allowance.** No more than `REPLACEMENTS_PER_PHASE = 1` retained losses in this phase
  (`work|role|candidate`).

After a refusal the coordinator's own K1 read-back gate finds no durable outcome and parks the item. The item holds
before launch, and dependents are blocked.

`read_back` answers only when the provider is bound to the profile's journal.

The profiles:

- `SandboxRunProfile` now composes `JsonlInvocationJournal(state_root/invocation-journal.jsonl)` into its
  `RealWorkerProvider` (`real_worker`). It hands the coordinator `worker = RoleBindingGuard(...)`, and `grant()` now
  issues the invocation's own role.
- `GitHubProfileComposition` gains keyword-only `journal=` and `clock=`. A supplied worker is always wrapped. Without a
  bound journal, every launch is refused.

## Founder amendment at the composition boundary

- **Ownership through background work.** `CliWorkerProvider.run` returns only at EOF on the child's stdout and stderr.
  A client that exits while work it started still holds that output keeps the invocation. The candidate is taken only
  after that work is done. This property is proven and was not changed.
- **Conclusive loss is retained.**
  - Trigger: the owning `start` call **returns** in this process with no durable outcome for a started invocation.
    Returning means the provider's own post-process effects, such as publication, have concluded.
  - A call that raised is never treated as concluded, because it may have pushed after its process exited. It stays
    UNKNOWN, and recovery parks it as before K3.
  - Then: the guard asks the process adapter for its own answer. That question is only asked after the call returned,
    so it never reaches a live process.
  - Only `quiescent` with `already-finished` counts as conclusive.
  - When conclusive, the guard appends the `missing-terminal-result` record against the **original** invocation and
    reads it back through `correlated_outcome` before anything else happens.
- **Exactly one deterministic replacement.** `FactoryCoordinator._advance` gains one rule: a
  `missing-terminal-result` outcome has no lifecycle consequence.
  - The stage is unchanged. The outcome is recorded, the effect is confirmed and the reservation is released.
  - The same role is re-dispatched on the same custodied candidate, in the same run.
  - No Factory Director decision and no external lifecycle/status event is involved.
  - A second loss in the phase is refused at launch and holds.
  - The attempt budget (`maximum_attempts`, rejections) and release admission are unchanged, and they still apply to
    the replacement.
- **UNKNOWN never replaces.** A restarted process cannot attest a child it did not start (`unresolved-recovery`). A
  journal that cannot be read, a record that is miscorrelated or duplicated, and an unattested exit are all left
  UNKNOWN, and so is a raising owning call. The coordinator parks them exactly as before K3.

## Fixture

`tests/composition/k3_fixture.py` composes the **actual** constructors:

- `sandbox()`: `SandboxRunProfile` over `SandboxBacklogComposition` with recorded GitHub answers.
- `github()`: `GitHubProfileComposition` with a local snapshot, a local secret file and a supplied production
  `RealWorkerProvider`. `binding` is `bound`, `missing` or `disconnected`.

Both profiles use the same parts:

- a real child worker (`worker/run.sh` via `CliWorkerProvider`, with a stated environment that carries no credential);
- `GitSourceControl` over a local bare remote;
- `GitWorktreeAdapter`;
- the real SQLite store.

Worker behaviour is selected by marker files in its `TMPDIR`: `reject-once` or `background`. Every process run is
logged outside the workspace. Reopening a root is a restart.

`python -m tests.composition.k3_fixture crash-before-producer-outcome|crash-after-verifier-outcome --root <r>` kills
the composing process with `os._exit(17)` at the named journal boundary.

Faults are injected only at the grant issuer, the journal, the execution store, or by killing the composing process.

## Material classes, probes and controls

Probes are in `tests/composition/test_role_binding.py`.

| Class | Probes | Control (fault → red) |
|---|---|---|
| 1. Refuse missing/miscorrelated role authority, custody or durable correlation before launch | `test_sandbox_profile_refuses_a_verifier_launch_whose_grant_names_another_role` (the pre-K3 PRODUCER-only issuer); `test_sandbox_profile_refuses_a_verifier_given_a_candidate_the_producer_never_published`; `test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch[missing\|disconnected]`; `test_a_refused_launch_journals_nothing_and_reads_back_nothing` | `role_grant_unchecked`; plus `outcome_correlation_disconnected` (distinct invariant: journal identity, not grant) |
| 2. Bound real adapter reaches correlated success, rejection and restart read-back | `test_bound_profiles_reach_correlated_success_through_every_role[sandbox\|github]`; `test_bound_sandbox_profile_reads_back_a_rejection_and_repairs_through_implement`; `test_bound_sandbox_profile_recovers_the_verifier_outcome_after_a_crash_without_re_running_it` (child killed after the durable verifier outcome) | `profile_journal_unbound`: the sandbox provider is composed without its journal |
| 3. Bypassing the guard or disconnecting correlation fails before advancement | `test_every_shared_profile_coordinator_reaches_its_worker_only_through_the_binding_guard`; the class-1 GitHub probes | `binding_guard_bypassed`: the GitHub coordinator is handed the raw worker |
| 4. No sidecar state owner, no activation | `test_the_binding_guard_owns_no_state_and_introduces_no_outcome_record` (source scan; after a drain, only existing aggregates and journal events exist) | `sidecar_state_owner`: the guard commits a `k3-outcome:` aggregate |
| 5. Client exit with owned background work keeps the invocation | `test_client_exit_with_owned_background_work_active_does_not_end_the_invocation` | `client_exit_releases_ownership`: the adapter waits for the client process only |
| 6. UNKNOWN refuses replacement; conclusive loss replaces exactly once | `test_no_replacement_launches_while_ownership_is_unknown_after_the_owner_died` (child killed before the producer outcome, then restart); `test_a_raising_owning_call_leaves_its_effects_unknown_and_is_never_replaced`; `test_conclusive_loss_without_a_durable_result_is_retained_and_replaced_exactly_once`; `test_a_conclusively_lost_verifier_result_re_dispatches_the_verifier_on_the_same_candidate`; `test_a_second_loss_in_the_same_phase_is_refused_at_launch_and_held` | `ownership_assumed_terminal`; plus three distinct invariants: `raising_call_assumed_concluded` (effect state, not ownership), `missing_result_advanced_as_verdict` (the coordinator rule for a non-producer role), `replacement_unbounded` (the per-phase allowance) |

There are ten controls, one per class. Class 1 has one more control and class 6 has three more. Each of those guards an
invariant that the class's first control cannot reach.

## Commands (all under `rtk proxy`)

1. `python3 -m pytest -q tests/composition/test_role_binding.py tests/composition/test_sandbox_run_profile.py tests/execution_coordination/test_github_work_management.py tests/invocation_runtime/test_real_worker_outcome.py tests/execution_coordination/test_role_orchestration.py tests/execution_coordination/test_factory_coordinator.py`
   This is a superset of the packet's initial bounded command.
2. `python3 -B tools/evidence/fx_k3_evidence.py --output <new-dir> --invocation <exact-invocation> --baseline 178732f464a516f0cd6c108f18e25f1c6b978445`
   - It runs (1), `check_architecture.py --check all`, `tests/test_architecture_fitness.py`, the full pytest suite and
     `node scripts/check.mjs all`.
   - It then applies each control once to a disposable copy.
   - A full-suite failure is admissible only when the same nodes fail at the code baseline in a detached worktree.

## Compatibility edits outside the new surface

- `RealWorkerProvider` gains three read-only accessors: `journal`, `grant_for` and `candidate_branch`. There is no
  behaviour change.
- `FactoryCoordinator._advance` gains the single `missing-terminal-result` rule above. No other outcome's path is
  changed. Verifier and closure outcomes still pass through every K2 attribution check.
- `SandboxRunProfile.worker` is now the guard. The raw provider is `real_worker`. `GRANT_OPERATIONS` is now
  `ROLE_OPERATIONS["PRODUCER"]`, which is the same set.
- The existing sandbox, GitHub, K1 and K2 suites pass unchanged. That includes the PY-10 crash test: a restart with no
  journaled start still parks for an attributable decision.
- The S0 frozen-kernel guard's changed-path list is unchanged, because `factory_coordinator.py` and `real_worker.py`
  are already listed.

## Independent pre-verification review and repairs

A read-only reviewer examined the first working tree. It found no bypass of the guard and no way for the coordinator
rule to skip K2's attribution checks or advance a stage.

- **MEDIUM — repaired.** A provider `start` that *raised* after its process exited was retained and replaced. An
  example is a read-back failure after a successful push. That call's effects are UNKNOWN, and the amendment forbids
  replacement then.
  - Repair: retention now requires an owning call that returned in this process (`_concluded`).
  - Regression probe: `test_a_raising_owning_call_leaves_its_effects_unknown_and_is_never_replaced`. It was red before
    the repair ("a replacement launched over an unknown effect") and is green after. Control:
    `raising_call_assumed_concluded`.
- **MEDIUM — repaired.** The coordinator rule was untested. A producer already records any non-success kind without
  transition, so only VERIFIER and CLOSURE depend on the rule.
  - Probe: `test_a_conclusively_lost_verifier_result_re_dispatches_the_verifier_on_the_same_candidate`. Control:
    `missing_result_advanced_as_verdict`.
  - The replacement bound lives only in the guard. No provider other than the guard produces the kind.
- **LOW — repaired.** The ownership probe answered `cancelled`, so an overlapping call could have killed a live process
  and counted that as conclusive. Now only `already-finished` counts, and the probe is asked only after the owning call
  returned.
- **LOW — disclosed:** the per-item producer allowance and the Invocation Runtime supervision boundary. Both are listed
  below.
- **LOW — disclosed: upgrade.** A sandbox state root from before K3 has no journal. An item already at VERIFY there
  holds as `candidate-custody-unattributable`, and an in-flight reservation is parked. This is safe, but it is a
  behaviour change for persisted state.
- **LOW — disclosed: grant read twice.** The guard checks the grant from `grant_for`, and the provider asks its issuer
  again at launch. Both profiles' issuers are deterministic.

## Disclosures

- **K1 gap, returned unrepaired: restart-time ownership.** The journal records no owner/supervisor identity (for
  example, a process id with a start or boot token).
  - After a control-plane restart, conclusive death of an in-flight invocation is not observable. K3 therefore holds it
    as UNKNOWN, and it goes to the existing decision path.
  - Deterministic replacement across a restart needs that seam.
- **Invocation Runtime gap, returned unrepaired: supervision boundary.** `CliWorkerProvider` supervises by output EOF.
  - Background work that detaches from the inherited stdout and stderr (`setsid`, `nohup … >file`) escapes supervision.
  - If `communicate` raises a non-timeout exception while the child lives, `run`'s `finally` still marks the
    invocation completed, so `cancel` would answer `already-finished`.
  - Process-group supervision belongs to the adapter's owner.
- The replacement allowance is scoped per `work|role|candidate`. A producer loss before a rework therefore consumes the
  producer allowance for later producer phases of the same item. This is conservative. The replacement is bounded by
  that allowance. It is not counted against `maximum_attempts`, which still bounds rejections exactly as in K2.
- The guard reads the coordinator's execution aggregate and effects read-only. It writes only the retained
  `invocation-outcome` record, through the existing journal port and after the provider's own `start` has ended.
- A refused or held launch parks through the existing generic FD-05 escalation. The specific refusal reason is kept in
  `RoleBindingGuard.refusals` (diagnostics, not state).
- Wiring a live verifier (Codex) or activating multi-role behaviour in any live or shared profile is **not** done or
  authorized here. The live `profile()` factory now composes the guard. It will therefore refuse an unbound launch,
  but that is not a claim that any live profile is proven.

## Non-claims

- No live or shared-profile multi-role activation. No new lifecycle owner or sidecar outcome state subsystem.
- The K1/K2 seams are not repaired. The gaps above are returned to their owners.
- Token and cost are UNKNOWN, never zero. No provider is composed.

## Retained run

`FX-K3/` holds the harness run for invocation `AlienLogicLab/alienintent#120:PRODUCER:92d60a69-dc02-4058-b64c-c5e22f06e52e`.

- Source: clean committed revision `e8c9f1be504b12898d7ca0ea88e3a1aeb5085cd9`. Code baseline `178732f`.
- Result: exit 0, no holds.
- Checks: the focused suite, `check_architecture.py --check all`, the architecture fitness tests and
  `node scripts/check.mjs all` all exit 0.
- Controls: all 10 discriminate (intact 0, fault 1, restored 0, with the named assertion in the fault output). Each was
  applied exactly once.
- Full suite: 25 nodes fail, all in `tests/evidence_learning/test_proof_planning.py`. The same 25 nodes fail at the
  code baseline in a detached worktree, so they are recorded as the residual `PREEXISTING_BASELINE_FAILURES`, outside
  the K3 extent. This is the same residual FX-K2 recorded.
- Provider calls: 0. Tokens and cost: UNKNOWN.
- Independent verdict: pending (fresh BIU verifier).
