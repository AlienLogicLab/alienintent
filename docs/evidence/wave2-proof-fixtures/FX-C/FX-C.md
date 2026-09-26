# FX-C — local bounded-control integration capstone (WO-220307, SF-REQ-053/056)

**Owner:** `WO-220307` / DAG node `C` (planned capstone, owns no capability), Issue #118.
**Acceptance:** `SF-REQ-053-AC-04`. **Proof level:** `LOCAL_COMPOSED_OR_MECHANICAL`. **Live proof:** `NOT_ESTABLISHED`.

This is a disposable local fixture for the pinned FX-C proof packet
(`docs/evidence/wave2-execution-packets/WO-220307.proof-packet.md`).

- **Contract input:** `docs/work-units/wave2/WO-220307.md`, sha256
  `a5199d8d60075eca1bb41b6d8247f0ecef263b130bf0777cee8845575640eeef`. This is the exact input of the native READY
  assessment `WO-220307.2026-09-25T221218.340064Z`.
- **Release baseline:** `b86b9fbd1978ccf3c341155d0dd64d153ad6cb19` (Factory Director RELEASED record on Issue #118).
- **Code baseline:** `5efe484`, a README-only successor of the release baseline.

The fixture hosts, supervises and launches nothing, binds no provider and performs no live action. The host remains
unassigned (`R1-GAP-MONITOR-HOST`), and bootstrap handoff stays gated (`POSTW1-DECIDE-006A`).

## Predecessors composed unchanged

| BIU | Fixture | Accepted candidate | Landing merge |
|---|---|---|---|
| WO-220303 (#99, C3) | FX-C3 | `d69c00480c895da80d63eb185b534ca1befad0c7` | `fc5c0a7` |
| WO-220304 (#96, C4) | FX-C4 | `4c806feb8456c68a590b1482ae340338b7d47c7d` | `3285c9e087b78909501995a662a008e9e0565dc5` |
| WO-220306 (#112, L1) | FX-L1 | `3cac3912ff7f7d17648fc8dcee4ab7195baaefc8` | `1753fde3638c26e47f33d793e59d11a6799ce74b` |

The harness re-checks that every candidate and landing merge is an ancestor of this candidate. C1 attention
(WO-220301) and C2 context reconstruction (WO-220302) enter through these profiles unchanged. No predecessor source
file changes in this BIU.

## Composition

`composition/bounded_control_profile.py` adds `BoundedControlProfile`. It is wiring only: it constructs the unchanged
`AttentionProfile`, `MonitorProfile`, `LivenessProfile` and `EpisodeProfile` over one profile root and one injected
integer-microsecond UTC clock. Constructing it begins, starts and hosts nothing.

- **Coordinator authority.** The coordinator episode is fenced by its own `episode:<objective>` pointer (C3 U-1). Its
  commands go through S2 `commit_guarded`.
- **Liveness authority.** Liveness recovery keeps its own dispatch authority record in the liveness store (L1). This
  is deliberate. SF-REQ-053-AC-04 requires monitor operation to continue after the model episode ends, and the
  contract says 053 must not require 056 to be operational. Recovery therefore never depends on a live coordinator
  epoch.
- **Judgment attention.** L1 judgment attention is the C1 service on the C2 profile store (`attention.sqlite`). A
  judgment item therefore enters every fresh context's `pending_attention` and `blocked_set`. The C3 episode observes
  that block (U-3), and the injected timer ends tenure at the blocked limit. This is the composed seam that
  `judgment_attention_detached` guards.
- **One clock.** Episode tenure (monotonic and UTC anchor), monitor health, liveness and the store authority expiry
  all read the same fake clock. The attention history timestamp is its ISO rendering.

## Reconstruction-equality predicate

`authorized_view` compares these fields:

- the pinned C2 manifest ref;
- the canonical digest of the reconstructed document;
- the document's `authorized_next_action_set`, `blocked_set`, `pending_attention` and `lifecycle`.

"Identical authorized actions" means all of these are equal across three readers:

1. the ended context, just before its end;
2. the fresh context, which has a new invocation and new objects, with every predecessor object discarded;
3. an independent OS process that shares only the durable store.

The fresh epoch's `begin` pins the same manifest ref and context digest. The action it reconstructs is then admitted
(`CONFIRMED`) for the current epoch only.

The two scenarios test this predicate with different strength:

- **Class 1.** Nothing the C2 manifest reads changes between the end and the fresh context. The episode pointer and
  the liveness store are outside it. Equality there shows only that reconstruction depends on durable state alone,
  not on process memory.
- **Class 2.** The comparison runs over a changed state: the judged view seen before the episode ended, including the
  pending item and the block, must equal the fresh and independent views. After a valid resolution, the view must
  equal the pre-judgment authorized set.

In class 1 the in-flight verifier effect is not part of the C2 view. The C2 `factory:` lifecycle and the L1
known-active stand-in are separate records (`LOCAL_LIFECYCLE_JOURNAL_STAND_IN`).

## Scenarios (fake time, one seeded FX-C2 world each)

| Test | Material failure class |
|---|---|
| `test_episode_end_during_duplicate_and_delayed_outcomes` | 1 and 4 |
| `test_judgment_attention_survives_episode_end_and_suppresses_recovery` | 2 |
| `test_stopped_scans_surface_stale_or_degraded_never_healthy` | 3 |
| `test_constructing_the_composition_starts_nothing` | composition boundary: construction writes nothing; a missing policy blocks startup |

**Classes 1 and 4: episode end during duplicate and delayed outcomes.**

1. At T0+G−5 s, epoch 1 has computed a coordinator result and dispatched the verifier through the canonical admission.
   The dispatch leaves a durable pending intent whose delivery is delayed.
2. The episode ends explicitly. Monitor health stays HEALTHY.
3. At T0+G a duplicate recovery scan sees `PENDING_EFFECT` and creates no second intent. A duplicate original is
   `RESERVED`. The delayed coordinator result is refused `NOT_ACTIVE`. Every table of all three stores and every
   evidence-repository file stay byte-equal, and no effect row exists for the result.
4. The context is discarded. The fresh context reconstructs the identical view.
5. The fresh context's `start()` reopens the intent by canonical claim with readback.
6. The late original is then refused twice: `DELIVERY_REFUSED` because its fence is released, and
   `EFFECT_IDENTITY_USED` on re-admission.
7. The ledger then holds exactly one consumer outcome. Its receipt names the canonical key and the dispatch
   invocation, and no pending, unknown or reserved remainder is left.
8. Epoch 2 is an explicit authorized begin. It carries budget accounting (`epochs=2`) over the same manifest.
9. Three stale sends are refused `STALE_EPOCH`, with byte-equal stores and evidence and no effect row for any of
   them:
   - epoch 1's delayed result, sent through epoch 2;
   - the same result from a straggler process that keeps the old invocation;
   - the straggler copying epoch 2's identity.

**Class 2: attention survives, and completed judgment suppresses recovery.**

1. A `HUMAN_DECISION_REQUIRED` verifier outcome is observed twice. Two scans ensure one JUDGMENT item with one identity.
2. C2 reconstruction shows the item as pending and blocking. `item-verify` leaves the authorized set.
3. The episode observes the block and arms the injected timer at +300 s. One microsecond below that, tenure is
   still ACTIVE. At the limit it ends with `BLOCKED_LIMIT`. Monitor and liveness keep running after the end, which
   holds by construction because neither references the episode.
4. After restart, the fresh context finds the same identity in C1. Its C2 view equals the judged view from before
   the end, and equals the independent process's view.
5. Scans at 3G, 5G, 20G and 100G stay `liveness.suppressed` with zero consumer outcomes.
6. Epoch 2 is refused `AUTHORITY_REFUSED` on the judged item.
7. A valid matching C1 resolution permits reinspection only (`COMPLETED_AWAITING_PROJECTION`, no relaunch), and
   restores the identical pre-judgment authorized action set.
8. The unbound activation spy stays at 0.

**Class 3: stopped, stale or degraded monitor evidence is never a healthy claim.**

1. The monitor survives the ended episode.
2. Once the old context and its ticker are gone, a fresh read-only inspection is `STALE TICK_OVERDUE`, and it writes
   nothing.
3. A reconciler with no started monitor instance withdraws its claim (`PROGRESS_UNRECORDED`).
4. After a generation-2 restart, the monitor's states and the reconciler's claim move as follows:

   | Condition | Monitor state | Claim |
   |---|---|---|
   | stopped ticks | `STALE:TICK_OVERDUE` | withdrawn |
   | failed scan | `DEGRADED:SCAN_FAILED` | withdrawn |
   | scanner dies mid-scan | `DEGRADED SCAN_STARTED` | — |
   | stopped scans | `STALE SCAN_OVERDUE` | withdrawn |

5. Only a fresh tick plus a completed scan restores `G_PLUS_I_CLAIMED`.

## Negative controls (one per material failure class)

| Control | Class | Mutation (disposable copy) | Required failing assertion |
|---|---|---|---|
| `stale_epoch_sends` | 1 | C3 admission stops comparing the acting process's invocation, so a straggler copying epoch 2's identity is `Admitted`/`CONFIRMED` | a stale epoch cannot send |
| `judgment_attention_detached` | 2 | composition binds liveness judgment to a detached attention store | judgment attention must be durable in the store every fresh context reconstructs |
| `health_bridge_unconditional` | 3 | the monitor-health bridge reports HEALTHY unconditionally | a scan must never claim G+I while the monitor's ticks have stopped |
| `identity_fence_removed` | 4 | the delivery source enters the L1 admission key | a duplicate recovery during the episode end must not create a second intent |

Two controls target composition seams (`judgment_attention_detached`, `health_bridge_unconditional`). The other two
apply predecessor mutations to the composed path under episode end and restart. Each records intact 0, fault 1 with
the named assertion, and restored 0.

## Labelled deviations, observations and non-claims

- **Carried stand-ins.**
  - `LOCAL_LIFECYCLE_JOURNAL_STAND_IN` (L1): the harness plays the canonical lifecycle and outcome writer.
  - A local dispatch-authority record (the L1 `authority:dispatch` shape) plays the dispatcher.
  - `LOCAL_JOURNAL_CONSUMER_ONLY` (L1/S2): the effect consumer is the store's guarded journal.
- **`FACTORY_COORDINATOR_NOT_MIGRATED` (carried, not repaired).**
  - The epoch-1 "original delivery" is issued through `CanonicalEffectAdmission`, the one admission entrypoint L1
    provides.
  - Routing `FactoryCoordinator` dispatch through it, with a generation alias for legacy `launch:` effects, is a
    capability change. The non-goals exclude that from this capstone, and no such claim is made.
- **Stale-epoch scope.** "Stale epoch cannot send" covers coordinator results, which C3 and the S2 pointer fence
  guard. Liveness admission is fenced by the dispatch authority, the lane reservation and the canonical effect
  identity, not by the coordinator epoch. An ended coordinator context can still call `CanonicalEffectAdmission`,
  and the canonical key keeps that to at most one effect. This follows from the authority choice above and is not
  claimed as a coordinator-epoch fence.
- **C3 observation (not exercised as a pass, not repaired).** An admitted coordinator transition whose delivery stays
  UNKNOWN keeps the episode reservation. A new epoch then holds as `RESERVATION_RETAINED`
  (`test_expiry_does_not_cancel_admitted`). This fixture's delayed coordinator result was never admitted, so that
  hold is not reached. No readback-and-release path for such an effect is claimed.
- **Not provided:**
  - supervised-host deployment or monitor-host replacement;
  - bootstrap liveness or checkpoint replacement or retirement;
  - live G+I, live transport, cutover or sovereignty;
  - work-discovery polling;
  - provider context-usage telemetry: the usage source stays UNBOUND and is never represented as zero or safe.

## Commands

Run all commands under `rtk proxy` with `PYTHONPATH=src:.` from a clean checkout of the candidate.

1. `python3 -B -m pytest -q tests/composition/test_bounded_control_capstone.py`
2. `python3 -B -m pytest -q tests/control_plane/test_episode_control.py tests/control_plane/test_attention.py tests/control_plane/test_monitor_health.py`
   (the pinned bounded initial command).
3. `python3 -B tools/evidence/fx_c_evidence.py --output /tmp/fx-c-<run-id> --invocation <exact-invocation>`. The
   output directory must be new.

Command 3 records:

- predecessor ancestry;
- the pinned input digests;
- commands 1 and 2 and the L1 suite;
- the architecture check and its tests;
- the full Python regression, compared node by node with a full run at the release baseline in a disposable
  worktree;
- `node scripts/check.mjs all`.

It then applies each of the four `CONTROLS` exactly once and performs a composed readback of the stores. Each of
these is recorded as a HOLD, never a PASS:

- a dirty source;
- a failed command;
- an unavailable baseline;
- a mutation needle that does not match exactly once;
- a non-discriminating control;
- a failed readback;
- a run stopped before it finishes.

Tokens, cost and provider calls are `null` with reason `UNKNOWN`.

The harness rewrites `execution-record.json` and `proven-red.json` before every stage. A run stopped at any point
therefore leaves a durable record with `run_state: INCOMPLETE`, the stage it stopped at, `exit_status: null` and an
`INCOMPLETE` hold. The focused, bounded, L1 and architecture commands run first. The two slow full-suite runs follow:
the release baseline in a disposable worktree, then the candidate. A complete run records `run_state: COMPLETE`.

The feature-regression pack `local-bounded-control-capstone` (`tools/verification/feature_regressions.json`) reruns
command 1 whenever a candidate changes the composed C3/C4/L1 boundaries.

### Feature-regression receipt custody

`.alienintent/feature-regressions.json` binds the exact candidate SHA (`candidate`) and a `receipt_digest` over its
body. A commit cannot contain a receipt naming its own SHA, so the receipt is not a tracked file. It is written into
the checkout of the exact candidate being verified. The invocation runtime does this before launching a verifier
(`CliWorkerProvider._feature_regressions`), and `read_verdict` reads it beside the verdict. When the runtime is not
the launcher, the verifier produces it in its own worktree at the retrieved SHA:

```
python3 tools/verification/run_feature_regressions.py --base <admission baseline> --candidate HEAD \
  --receipt .alienintent/feature-regressions.json
```

The PRODUCER records its own receipt for the published SHA on the Issue for comparison. It does not replace the
verifier-side receipt.

## Preparatory review

Before evidence capture, a separate read-only reviewer examined the working candidate.

**Confirmed defect.** The first class-1 control (`ended_epoch_sends`) only changed the refusal reason:
`FENCE_REFUSED` replaced `NOT_ACTIVE`, and nothing was sent. It was replaced by `stale_epoch_sends`, which produces
a real stale send (`Admitted`/`CONFIRMED`).

**Overclaims and gaps, all repaired above:**

- the class-1 reconstruction equality is over unchanged C2 state, which is now stated, and class 2 now compares
  across the end;
- the missing liveness-epoch non-claim is now stated;
- the snapshot was narrower than "byte-equal" and now covers every table and all evidence files;
- the blocked-limit boundary had no below-limit check;
- the harness raised instead of recording a hold for a needle mismatch or baseline failure;
- the regression pack missed the reconstruction core and the helper test modules.

This review is preparatory. It is not the fresh BIU verifier verdict.

## Evidence

The evidence is in this directory, following the FX-C4 and FX-L1 conventions:

- `execution-record.json`
- `run-report.json`
- `proven-red.json`
- `observations/`, named by sha256 and written with `xb`
- `digest-manifest.json`

The independent verdict is pending the fresh BIU verifier.
