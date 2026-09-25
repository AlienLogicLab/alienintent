# FX-L1 — known-active liveness reconciliation (WO-220306, SF-REQ-056)

**Owner:** `WO-220306` / DAG node `L1` (`liveness_reconciliation`), Issue #112.
**Proof level:** `LOCAL_COMPOSED_OR_MECHANICAL`. **Live proof:** `NOT_ESTABLISHED`.

This is a disposable local fixture for the pinned FX-L1 proof packet
(`docs/evidence/wave2-execution-packets/WO-220306.proof-packet.md`). Its contract input is
`docs/work-units/wave2/WO-220306.md`, sha256
`5364dc7b6349d3246f3cf58b92792d253d36c8d870fffd35398388695a488293`, which is the exact input of the native READY
assessment `WO-220306.2026-09-25T090348.165457Z`. The release baseline is `98a56bf3c9f424b2507ee39ba3bcd1628bf85eae`
(Factory Director RELEASED record on Issue #112). The fixture hosts, supervises and launches nothing. It binds no remote
worker provider and performs no live action. The host remains unassigned (`R1-GAP-MONITOR-HOST`).

## Predecessors consumed unchanged

- **WO-220103 (#74, FX-S2):** `FencedOperationalStore` `acquire_many` / `commit_guarded` / `claim_guarded` /
  `consume_guarded` / `readback_guarded` / `confirm_guarded`, and `GuardedEffectExecutor`. FX-S2 evidence commit:
  `8e2547980ca1d95849460b9abf0c08857a6671b9`.
- **WO-220301 (#78, FX-C1):** `AttentionService.ensure/seen/resolve`, which provides SEEN≠RESOLVED and actor, revision,
  lane and authority checks. FX-C1 evidence commit: `8c810d2df815907cb3c1a383d6a645b3cddc7c6e`.
- **WO-220304 (#96, FX-C4):** `MonitorService` (`ScanProgress`) and `inspect`. Candidate
  `4c806feb8456c68a590b1482ae340338b7d47c7d`, merged at `3285c9e087b78909501995a662a008e9e0565dc5`.

## Implemented surface

- `execution_coordination/domain/liveness.py`: `LivenessPolicy` (G/I/C, positive and finite, `policy_digest`),
  `KnownActive`, the canonical `effect_key`, `expected_effects`, and the pure ordered `inspect` rule, which returns
  `NoAction | Gap | Suppressed | EvidenceHold`.
- `execution_coordination/ports/liveness.py`: `EffectObservation`, `JudgmentAttention`, `MonitorHealthView` and
  `LifecycleJournal`. Unavailable data is the typed value `Unavailable`, never an empty set.
- `execution_coordination/application/liveness.py`:
  - `CanonicalEffectAdmission` is the one admission entrypoint for original delivery and recovery: reserve, then re-read
    evidence and admission, then durable guarded intent, then fenced claim/consume, then readback, then confirm.
  - `LivenessReconciler` provides `start` (persists the policy digest, then reopens durable intents), read-only
    `inspect`, and `scan`.
- `execution_coordination/adapters/liveness_observations.py`: `StoreEffectObservation` reads lane, effect and consumer
  records, same-work/same-generation invocation and outcome records, and legacy `launch:` effects for the same work.
  `StoreLifecycleJournal` is the local stand-in for the canonical transition and runtime/outcome writers. The
  reconciler never holds it.
- `composition/liveness_profile.py`: `LivenessProfile` binds the real SQLite store, admission and executor, C1
  attention through `AttentionJudgment`, and C4 health and scan progress through `MonitorHealthBridge`. Constructing it
  starts nothing.

## Pinned local choices

- **Time.** Times are integer UTC microseconds from one injected clock, shared with C4. G/I/C are compared as
  `Fraction`s. The store's authority-expiry clock is the same reading in seconds.
- **Grace.** Age < G gives `WITHIN_GRACE`. Age ≥ G with complete absence evidence gives `Gap`.
- **Confirmation bound C.** A PENDING or UNKNOWN intent younger than C is `PENDING_EFFECT`. At C it becomes
  `CONFIRMATION_OVERDUE`. The reconciler then calls `resume`, which never creates a new intent:
  - pending unsent is executed through the canonical claim;
  - claimed is read back only;
  - with no receipt it parks as `READBACK_PENDING`, with a durable `liveness-hold:<biu>`.
- **Effect key.** The key is `sha256(profile, repository, BIU, contract digest, lifecycle-entry generation,
  role/closure key)`. The delivery source and scan time never enter it. A lifecycle-entry generation only advances
  through `LifecycleJournal.enter`; a same-or-lower generation is refused with `GENERATION_NOT_ADVANCED`.
- **Lane and fencing.** Each effect key has its own lane aggregate `liveness-lane:<key>` and reservation
  `(liveness-lane, key)`. The guard vector covers the known-active aggregate revision, the authority aggregate and the
  lane. `EFFECT_IDENTITY_USED`, `RESERVED` and `STALE_SNAPSHOT` are refusals. The lifecycle aggregate is never written
  by recovery, so there is no status toggling.
- **Judgment.** `FOUNDER_EXCEPTION`, `HUMAN_DECISION_REQUIRED` and `AUTHORITY_BLOCK` are the judgment outcomes. When
  the latest same-generation outcome is one of them, the reconciler ensures one C1 `JUDGMENT` item and returns
  `Suppressed`, regardless of age.
  - A RESOLVED item (resolved by C1's own actor/revision/lane/authority checks) permits reinspection only. That role
    stays completed for the generation, and a relaunch needs a canonical new generation.
  - A newer non-judgment outcome also lifts suppression.
  - SEEN, out-of-lane and stale (older-outcome) resolutions keep suppression.
- **Holds.** Missing or inactive authority, unknown budget (`budget_admitted` false), missing custody for verifier or
  closure, and unavailable observation, attention or store evidence during a scan are holds, never launches. Each is
  written to `liveness-hold:<biu>`. If that write itself fails, the scan reports FAILED, never quiet success.
- **Reservations.** A reservation never outlives a failed admission. If an admission fails after reserving and before
  a durable intent exists, the reservation is released. `start()` releases orphan lane reservations left by a crash
  before intent. It also reopens lanes whose confirmed effect still retains a reservation. A live contender whose
  reservation is released this way is refused by its stale fence.
- **Monitor failure.** If C4 scan progress or the health read fails (for example `NOT_STARTED` or
  `CLOCK_REGRESSION`), reconciliation continues and the claim is withdrawn as
  `WITHDRAWN:PROGRESS_UNRECORDED:<cause>`.
- **G+I claim.** `ScanReport.bound_claim` is `G_PLUS_I_CLAIMED` only while C4 health is HEALTHY. Otherwise it is
  `WITHDRAWN:<status>:<reason>`. With no monitor bound it is `WITHDRAWN:UNVERIFIED:MONITOR_UNBOUND`. Each scan reports
  COMPLETE, EVIDENCE_HOLD or FAILED through C4 `ScanProgress`.

## Labelled deviations and non-claims

- **`LOCAL_JOURNAL_CONSUMER_ONLY`.** The only effect consumer that proves idempotent, fenced consumption with durable
  readback is the store's guarded journal (FX-S2). No CLI, sandbox or GitHub worker provider is bound. Following the
  fixed decision to park rather than relax, binding one is left to a provider that can prove the same contract.
- **`FACTORY_COORDINATOR_NOT_MIGRATED`.** `FactoryCoordinator` still dispatches through its legacy unguarded
  `launch:<identity>:<version>` path, and this node does not rename or adopt in-flight legacy effects. A pending or
  unknown legacy `launch:` effect for the same work is observed read-only: a pending one suppresses recovery, and an
  unknown one holds it. A settled legacy launch has no immutable generation alias yet. When one is projected on
  `factory:<work>` in the same store, the reconciler holds with `LEGACY_EFFECT_UNALIASED` rather than relaunching.
  Routing the coordinator's dispatch through `CanonicalEffectAdmission`, with the alias binding, belongs to the
  capstone `C` integration.
- **`LOCAL_LIFECYCLE_JOURNAL_STAND_IN`.** Known-active entries, running invocations and correlated outcomes are
  written by `StoreLifecycleJournal`. They are not read from WorkManagement or worker `read_back`.
- **Not provided:**
  - no work-discovery polling;
  - no operator `liveness reconcile` command;
  - no bootstrap liveness (SWF-29) retirement;
  - no live monitor-host replacement;
  - no SF-REQ-056-AC-08 live-profile exercise.

## Commands

Run all commands under `rtk proxy` with `PYTHONPATH=src` from a clean checkout of the candidate.

1. `python3 -B -m pytest -q tests/execution_coordination/test_liveness_reconciliation.py`
2. `python3 -B -m pytest -q tests/control_plane/test_monitor_health.py tests/control_plane/test_attention.py` (the
   pinned bounded initial command).
3. `python3 -B tools/evidence/fx_l1_evidence.py --output /tmp/fx-l1-<run-id> --invocation <exact-invocation>`. The
   output directory must be new.

Command 3 runs commands 1 and 2, the architecture check and its tests, the full Python regression and
`node scripts/check.mjs all`. It then applies each of the five `CONTROLS` exactly once in a disposable source copy.
This is one control per material failure class, and two of them are the AC-07 pinned controls:

| Control | Failure class |
|---|---|
| `grace_ignored` | a missing effect after G yields one gap |
| `unknown_as_absent` | unknown evidence holds rather than fabricating absence |
| `judgment_suppression_removed` | AC-07 judgment suppression |
| `identity_fence_removed` | AC-07 durable identity fencing (delayed original + contenders + restart). The control removes this node's identity binding: the delivery source enters the admission key, so paths no longer share one canonical key. The store-side identity and fence guards belong to WO-220103 and keep their own FX-S2 proven-red controls. |
| `bound_claim_unconditional` | unhealthy monitor evidence withdraws the G+I claim |

Each control records intact 0, fault 1 with the named assertion, and restored 0. Finally, the harness performs a
composed readback of the lane, consumer, lifecycle, policy, attention and monitor records.

## Baseline condition

At the admission baseline `98a56bf`, 25 tests in `tests/evidence_learning/test_proof_planning.py` already fail with
`DESIGN_MISMATCH`. The harness re-runs that file in a disposable baseline worktree. It records the regression as
`PRE_EXISTING_BASELINE_FAILURE` only when the failing node ids are identical. Any other failure is a HOLD. The defect
belongs to the FX-U4 proof-planning owner (WO-220204) and is not repaired here.

## Preparatory review and repair

Before evidence capture, a separate read-only reviewer examined commit `74e1a82`. It confirmed four defects and two
overstatements:

1. A reservation leaked after a post-reserve store failure or crash, and was reported as a quiet COMPLETE.
2. A confirmed legacy `launch:` effect was invisible, so it could be relaunched.
3. A monitor failure raised out of `scan()`.
4. A release failure after confirmation raised out of `scan()`.
5. The label of the identity control overstated its reach.
6. The claim that holds are durable was overstated.

All of these are repaired above. Each repair is covered by a test that failed against `74e1a82` and passes on the
repaired source:

- `test_crash_after_reservation_before_intent_is_released_at_start`
- `test_store_failure_after_reservation_does_not_strand_it`
- `test_confirmed_legacy_launch_holds_instead_of_relaunching`
- `test_monitor_failure_withdraws_claim_but_reconciliation_continues`
- `test_release_failure_after_confirmation_does_not_escape`
- `test_unrecorded_hold_fails_the_scan`

The reviewer found no path where a judgment outcome fails to suppress, and no hold path that launches. This review
is preparatory. It is not the fresh BIU verifier verdict.

## Evidence

The evidence is in this directory, following the FX-C1 and FX-C4 conventions:

- `execution-record.json`
- `run-report.json`
- `proven-red.json`
- `observations/`, named by sha256 and written with `xb`
- `digest-manifest.json`

Tokens, cost and provider calls are `null` with reason `UNKNOWN`. A dirty source, failed command, non-discriminating
control or missing readback is recorded as a HOLD, never as a PASS.
