# FX-O — Offline multi-role lifecycle capstone (WO-220404, SF-REQ-039)

Fixture contract for `docs/work-units/wave2/WO-220404.md`:

- **Contract input.** sha256 `556b7887…1ce8`, the exact input of the READY assessment
  `WO-220404.2026-09-26T002627.317407Z` (work-unit revision `fe46a19`, which carries the Founder AC-08 clarification).
- **Release.** Founder critical-path release on Issue #121 (superseding record, 2026-09-26T00:31:40Z): IMPLEMENT authorized;
  AC-08 implementation bounded to the existing Execution Coordination / Invocation Runtime owners; limits
  maxCycles=3, maxReplacementsPerPhase=1.
- **Baseline.** `4a9a3b67a1f5fea5d3caedd2f597bab23a94cf12` (`origin/main` at the release). It is also the code baseline.
- **Predecessors, all present at the baseline.**

  | Node | BIU / Issue | Retained identity |
  |---|---|---|
  | S0 | WO-220101 / #69 | FX-S0 source `37f09a6`; manifest and substrate consumed |
  | C1 | WO-220301 / #78 | FX-C1 source `a8077b8`; `AttentionService` consumed unchanged |
  | K1 | WO-220401 / #113 | candidate `4cb84173…`, merge `23c408d`; journal and `correlated_outcome` consumed |
  | K2 | WO-220402 / #115 | FX-K2 source `90f7fb9`, candidate `81d9cc5`; role routing consumed unchanged |
  | K3 | WO-220403 / #120 | candidate `4c262994bdb7121ee47a1a4aec1b0eb72ed64aad`, merge `57099f0`; `RoleBindingGuard` consumed, one fallback added |

- **Scope.** Proof level `LOCAL_COMPOSED_OR_MECHANICAL`. A local PASS is not operational acceptance and activates nothing.

## Pre-implementation findings

1. **Baseline defect (repaired at the fixture level, gate untouched).** At `4a9a3b6` eleven K1/K3/PY-10 proof nodes fail
   (`test_role_binding.py` ×7, `test_sandbox_run_profile.py` ×2, `test_real_worker_outcome.py` ×2). The cause is `4a9a3b6`
   ("accumulate feature regression gates"). `CliWorkerProvider` now runs `tools/verification/run_feature_regressions.py`
   inside every verifier workspace. The disposable repositories those fixtures seed did not carry that runner, so each
   verifier failed.
   - Repair: `tests/support/feature_regressions.py` copies the repository's own runner and manifest, byte for byte, into
     each fixture's baseline commit. The gate then runs for real there.
   - No pack is deleted, weakened or bypassed. All eleven pass after the repair.
   - The nodes affected are among the packet's own bounded commands.
2. **K1 seam check.** Two gaps that FX-K3 returned unrepaired are exactly the AC-08 behaviour this BIU is now authorized to
   implement:
   - *Restart-time ownership.* The journal recorded no owner identity, so conclusive death was unobservable after a
     restart.
   - *Supervision boundary.* `CliWorkerProvider` supervised only by output EOF, so detached background work escaped.
   Both are implemented below inside the Invocation Runtime owner. K3's composition consumes the result through one
   fallback.

## Design Verification (WorkerOutcome capacity)

No field is added to `WorkerOutcome` or `WorkerInvocation`, and no `RoleOutcomeRecord` or sidecar owner is added. Every
new observable lives in the existing invocation journal (K1's durable evidence record):

- `invocation-started` gains `owner`: `{pid, start, boot, pidns}` of the composing process, read from the kernel. The
  start time is in clock ticks since boot. It is recorded only when the process adapter marks all owned work
  (`marks_owned_work`), because only then can surviving work be observed later.
- `publication-started` is appended just before a producer's publication. That publication is the one external effect a
  role invocation performs.
- The retained `missing-terminal-result` record (K3) carries `ownership: "owner-terminated"` when the restart attestation
  produced it.

`correlated_outcome` ignores all three, so correlation is unchanged.

## AC-08 implementation (Invocation Runtime owner; consumed at the K3 guard)

- **Ownership includes owned background work** (`invocation_runtime/adapters/cli_worker.py`).
  - The client starts as the leader of its own process group. Its stated environment carries two markers:
    `ALIENINTENT_INVOCATION_ID` and `ALIENINTENT_INVOCATION_OWNER` (`<owner token>/<supervisor instance>`).
  - An invocation identity (`launch:<work>:<version>`) repeats across profiles. Owned work is therefore matched on
    both markers, so no supervisor ever awaits or stops another owner's work.
  - The invocation ends only when every process it owns has ended:
    - the client itself;
    - anything still in its process group;
    - any live process carrying its marker, including descendants that ran `setsid` and redirected their output away.
  - Owned work that outlives the wall clock is stopped with the client, and the result is `timeout`.
  - The invocation is recorded as finished only when no owned work is observed. Otherwise a later `cancel` answers
    `unresolved-recovery`, never `already-finished`.
  - An unexpected exception stops owned work before it propagates.
  - The VERIFY feature-regression runner now runs in its own process group. It is stopped as a group at the wall clock,
    and its quiescence is observed, not assumed.
- **Kernel observation** (`invocation_runtime/adapters/process_ownership.py`, port `ports/process_ownership.py`).
  `ProcOwnership` identifies a process by pid, start time and boot id.
  - A missing pid, a reused pid (different start time), a zombie or an earlier boot reads as `terminated`.
  - An owner recorded in another pid namespace, or anything unreadable, reads as `unknown`, never `terminated`.
  - `owned_work` scans `/proc/*/environ` for both markers. Given an owner token, it matches every supervisor that owner
    process ran.
- **Restart attestation** (`RealWorkerProvider.attest_ownership`). This is answered from the journal and the kernel only.
  The answer is `owner-terminated` (quiescent) only when all of the following hold:
  - the invocation has exactly one journaled start, and that start names an owner;
  - that owner has ended;
  - no process carrying this invocation's marker under that owner is alive;
  - no `publication-started` exists.

  Otherwise the answer is `owner-unattested`, `owner-alive`, `owned-work-active` or `effect-unknown`, and every one of
  those is UNKNOWN.
- **Consumption** (`composition/role_binding.py`). When the owning call did not conclude in this process, the guard asks
  for the runtime's attestation and accepts only `owner-terminated`. That is its only change.
  - The K3 path then does the rest unchanged: it retains `missing-terminal-result` against the **original** invocation and
    reads it back through K1.
  - The coordinator's existing rule records it with no lifecycle consequence.
  - The same run re-dispatches the role once under the existing `REPLACEMENTS_PER_PHASE = 1` and attempt budget. No
    Factory Director and no status event is involved.
  - `SandboxRunProfile` composes one `ProcOwnership` into both the process adapter and the provider.

## Fixture

`src/alienintent/composition/lifecycle_capstone.py` composes `CapstoneSubstrate`, S0's `OfflineProofSubstrate` with every
seam bound:

- `RealWorkerProvider(journal=…, ownership=ProcOwnership())` behind `RoleBindingGuard`;
- per-role grants (`ROLE_OPERATIONS`);
- the Deterministic Test Worker (`ScriptedWorkerProcess`) as the only worker process;
- C1 `AttentionService` behind an `AttentionDecisionNotifier`. Each escalation becomes one JUDGMENT item; the
  DecisionInbox stays the only decision path.

`offline_profile.py` gains two composition hooks (`_compose_worker`, `_compose_notifier`), and `OfflineProfile` gains
optional `store=`/`notifier=`. S0's own composition is unchanged.

The pinned input is [`FX-O/manifest.json`](FX-O/manifest.json): one work item `O-LIFE` with `maximum_attempts: 2`, and 13
scenarios, each with its script, its fault or crash boundary, and the script of the restarted process.

- Each scenario runs in its own disposable root.
- Faults are injected only at a transport boundary: the journal, the store's custody record, the local remote, the worker
  process, or by killing the composing process (`os._exit`). No fault writes lifecycle state.
- The only store write a fixture makes is the forged custody record in `wrong-candidate`. It leaves the stage untouched,
  and the guard must refuse it.

`python -m alienintent.composition.lifecycle_capstone --root R --manifest M` runs every scenario:

- **Exit 0 (PASS)** when every check passes.
- **Exit 1 (FAIL)** when any check fails.
- **Exit 2 (HOLD)** when a credential is present or network denial is not enforced. A HOLD is never reported as PASS or
  as zero.

## Material classes, probes and controls

The probes are in `tests/composition/test_lifecycle_capstone.py` (scenario checks) and
`tests/invocation_runtime/test_owned_work.py`.

| Class | Scenario checks / probes | Control (fault → red) |
|---|---|---|
| 1. Denied-network lifecycle, actual Git publication and fresh verifier retrieval; wrong/unpublished candidate refused | Proof command inside `unshare -rn` (network `ENFORCED`); L3, L4; W1 (forged custody refused before the verifier launches); U1 (withdrawn branch cannot be retrieved) | `custody_unchecked`; environment controls `network_denial_absent` and `credential_present` (the proof command must HOLD) |
| 2. Distinct producer/verifier flow: rejection, repair, fresh candidate, REVIEW/ACCEPT/closure, no collapse | L1, L2, L5, L6, L7 | `rework_skipped` |
| 3. Missing, stale or miscorrelated outcome holds despite process success; restart is idempotent | M1, N1, F1, D1, L9 | `outcome_correlation_bypassed` |
| 4. Judgment holds; exactly one authorized effect and read-back identity | J1–J4 (hold, one JUDGMENT item deduped across restart, SEEN is not a decision, one decision resumes once); E1–E2 (escaped publication is UNKNOWN, one decision authorizes exactly one effect, original branch untouched); L8 | `judgment_released_without_decision` |
| 5. Custody, verifier independence, binding and correlation controls | Controls of classes 1 and 3; the binding probe (a grant for another role is refused before launch) | `verifier_self_approval` (producer success taken as its own acceptance); `binding_guard_bypassed` |
| AC-07 | M1 (miscorrelated), N1 (duplicate), F1 (malformed), D1 (delayed correlated read-back applied once, no re-run) | `duplicate_outcome_accepted` |
| AC-08 | `test_owned_work.py` (detached background work keeps the invocation; wall-clock stop; kernel identity; marker scan; another owner's same-id work neither awaited nor stopped; only marked workers journal an attestable owner; foreign pid namespace is unknown); C1/C2 (crash before output); P1/P2 (progress then crash; worktree keeps the progress commit); A1 (owner alive); B1 (owned work alive); E1 (effect escaped) | `owned_work_ignored`, `attested_recovery_disabled`, `escaped_effect_assumed_absent`, `live_owner_assumed_dead`, `owned_work_assumed_absent`, `reused_pid_read_as_owner`, `owner_marker_ignored` |

There are fourteen source controls and two environment controls:

- Classes 2, 3, 4 and AC-07 have one control each.
- Class 5 names four controls. Custody and correlation are shared with classes 1 and 3.
- AC-08 has seven controls, one per distinct invariant:
  - owned work keeps ownership;
  - conclusive loss recovers;
  - an escaped effect blocks;
  - a live owner blocks;
  - surviving owned work blocks;
  - a reused pid is not the owner;
  - owned work is bound to its owner, not to the id alone.

## Commands (all under `rtk proxy`)

1. The packet's bounded command:
   `python3 -m pytest -q tests/composition/test_offline_proof.py tests/composition/test_sandbox_run_profile.py tests/execution_coordination/test_factory_coordinator.py tests/invocation_runtime/test_runtime.py`
2. `env -i PATH=$PATH HOME=<h> LANG=C.UTF-8 PYTHONPATH=src unshare -rn python3 -m alienintent.composition.lifecycle_capstone --root <new> --manifest docs/evidence/wave2-proof-fixtures/FX-O/manifest.json`
3. `python3 -B tools/evidence/fx_o_evidence.py --output <new-dir> --invocation <exact-invocation> --baseline 4a9a3b67a1f5fea5d3caedd2f597bab23a94cf12`
   - Runs (2), the focused suites (a superset of (1)), `check_architecture.py --check all`, the architecture fitness tests,
     the full pytest suite once and `node scripts/check.mjs all`.
   - Then applies every control once to a disposable copy.
   - A full-suite failure is admissible only when the same nodes fail at the code baseline in a detached worktree.

## Compatibility and disclosures

- **K3's historical controls.** The `client_exit_releases_ownership` control (`communicate` → `wait`) no longer turns
  K3's probe red at this revision, because supervision is now stronger than output EOF. K3's retained run remains valid
  at its own source revision.
- **Needles kept intact.** K3's other guard and sandbox needles are preserved byte for byte.
- **S0 frozen-kernel guard.** The changed-path list is unchanged: `real_worker.py` and `sqlite_store.py` are already
  listed, and no other kernel path changed.
- **Effect ledger read.** `SQLiteOperationalStore` gains one read-only method, `effect_ledger(profile)`, so the fixture
  can observe effect statuses and receipts through the declared persistence owner. It writes nothing, and the port is
  unchanged. A direct `sqlite3` read from the composition would violate the persistence-ownership fitness check.
- **Marker coverage.**
  - The markers reach a worker only through a *stated* environment. A worker composed with an inherited environment
    (`environment=None`) is supervised by process group only.
  - Such a worker's invocations journal no owner, so after a restart they read `owner-unattested` (UNKNOWN) and are
    never replaced.
  - A descendant that both leaves the process group and clears its environment (or makes itself unreadable) escapes
    observation. A missing marker is not proof of absence beyond that boundary. Full containment (for example, cgroups)
    remains with the Invocation Runtime owner.
  - Observation is Linux `/proc` only. Elsewhere it reads `unknown`, so it holds and never replaces.
- **Worker lifetime.**
  - A worker in its own session now outlives a crashed control plane until it ends. It holds its item as
    `owned-work-active`, which is the safe direction.
  - A long-lived marked daemon started by a worker turns that run into a `timeout` at the wall clock.
- **Process-group probe.** The probe uses the reaped leader's pid as the group id. A pid reused as a new group leader
  within one 50 ms poll could be misread. This is residual and bounded by the kernel's pid space.
- **In-process versus restart.** In process, an owning call that *returned* concluded its publication (K3), so K3 still
  retains and replaces it once. After a restart, an owner that died after `publication-started` leaves the effect
  UNKNOWN, and nothing replaces it (E1).
- **GitHub profile.** `GitHubProfileComposition` receives a supplied worker. It gains no ownership composition here, so
  its restart recovery stays UNKNOWN (a hold), as before.
- **Owned work across a restart.** Work left by a dead owner (`owned-work-active`) holds and parks for a decision. The
  successor never kills another invocation's work.
- **Allowance.** The replacement allowance and attempt budget are K3's and K2's, unchanged. A second loss in one phase is
  refused at launch; K3 proves this and it was not re-proven here.
- **Substitutions.** Every external substitution is listed in the report's `substituted_boundaries`, including the
  scripted verifier's `SCRIPTED_FIXTURE` feature-regression receipt. The verifier's real pack run is not exercised by
  FX-O.

## Independent pre-verification review and repairs

A read-only reviewer examined candidate `41591b1`. It found no HIGH issues.

- **MEDIUM — repaired.** The marker was the invocation identity alone, which repeats across profiles. One owner could
  await, or stop, another owner's same-id work.
  - Repair: owner-bound markers (`ALIENINTENT_INVOCATION_OWNER`).
  - Probe: `test_another_owners_work_with_the_same_invocation_identity_is_neither_awaited_nor_stopped`. It was red before
    the repair: the other owner's work was awaited and stopped at the wall clock. It is green after.
  - Control: `owner_marker_ignored`.
- **MEDIUM — repaired.** Unmarked owned work could pass as none after a restart.
  - Repair: the owner is journaled only when the process adapter marks all owned work, so an inherited-environment
    worker is `owner-unattested`. The VERIFY regression runner is now group-supervised.
  - Probe: `test_only_a_worker_whose_owned_work_is_marked_journals_an_attestable_owner` (red before, green after).
  - The reviewer's remaining sub-cases (a cleared environment, a non-dumpable process) are disclosed above.
- **LOW — repaired.** A pid-namespace change now reads `unknown`: `test_an_owner_recorded_in_another_pid_namespace_is_unknown`.
- **LOW — repaired.** The control gaps are closed: `owned_work_assumed_absent` and `reused_pid_read_as_owner`. The
  sidecar probe now pins the single store write to the custody fault.
- **LOW — disclosed.** The process-group pid-reuse window, worker lifetime and the in-process-versus-restart semantics
  are recorded under Compatibility and disclosures.

## Non-claims

- No live transport, shared-profile, sovereignty or retirement proof, and no activation.
- No scenario-written lifecycle state, `RoleOutcomeRecord`, sidecar outcome store or new lifecycle owner.
- No Node product repair. Tokens and cost are UNKNOWN, never zero. No provider is composed.

## Retained run

Pending: the harness run over the clean committed candidate is retained under `FX-O/` in the next commit.
