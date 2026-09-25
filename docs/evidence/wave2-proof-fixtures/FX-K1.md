# FX-K1 — Real-worker role outcome readback (WO-220401, SF-REQ-039 prerequisite)

Fixture contract for `docs/work-units/wave2/WO-220401.md` (sha256 `f45d0024…df93d`, the exact input of the READY
assessment `WO-220401.2026-09-25T100631.201140Z`). Admission baseline `308188c9bce7eb5557d1307bf4d017d907ade16a`,
candidate contract `e9c556e1…272408`; code baseline `fc5c0a7fcbc0d70772c07cd35a4fe52a3e2641c7`. Proof level
`LOCAL_COMPOSED_OR_MECHANICAL`. Disposable local profile only. No live store, provider, model, network, credential or
RAI. A local PASS is not operational acceptance.

The Issue #113 body still shows the pre-clarify revision (baseline `6ea9284`, contract `9278b865…`), which put the
success-collapse refactor inside K1. This candidate implements the re-pinned repository revision that Agent Ready
assessed READY. That revision assigns the refactor to K2.

## Design Verification (WorkerOutcome capacity)

The result contract stays unchanged. `WorkerOutcome` already carries the two observables the coordinator acts on: the
outcome `kind` and the exact `CandidateRef`. The other correlation observables (role, invocation, attempt, contract)
are attributes of the invocation. They live in the existing invocation evidence record: the S0 worker journal's
`invocation-started` and `invocation-outcome` events, now written by `RealWorkerProvider` itself. `read_back`
checks them against the invocation it is asked about. No `RoleOutcomeRecord` or sidecar state owner is added.

There is one compatible request-side addition: `WorkerInvocation.contract_digest: str | None = None`. It is optional
and defaulted, so existing callers are unchanged. With it, recovery after a restart asks for the result of *this*
contract. The coordinator supplies it on launch and on recovery.

## Surface

| Module | Change |
|---|---|
| `invocation_runtime/ports/invocation_journal.py` | New port `InvocationJournal.append/records`. |
| `invocation_runtime/adapters/invocation_journal.py` | `JsonlInvocationJournal`. The S0 `journal_append`/`journal_records` move here unchanged (fsync plus identical read-back). `scripted_worker` re-imports them. |
| `invocation_runtime/application/real_worker.py` | Optional `journal=`. `start` journals `invocation-started` before any effect, then `invocation-outcome` with `correlation_id`, `work_identity`, `role`, `attempt`, `contract_digest`, `kind` and `candidate`. With a journal, `read_back` answers only from `correlated_outcome`. That function requires exactly one started record and one outcome record for the correlation, equal work identity and `PRODUCER` role in both, equal contract digests (and the caller's, when supplied), and for success an attempt ≥ 1 and a source-revision candidate published on this invocation's branch. Anything else is `None`, which is a hold. |
| `execution_coordination/application/factory_coordinator.py` | `_run` admits a started outcome only if `read_back` of the same invocation returns the same `(kind, candidate)`. Otherwise it parks the claimed effect as unknown through the existing FD-05 authority block. Recovery reads back with the contract digest. The success-collapse fallback is **not** removed (K2). |
| `execution_coordination/ports/worker_provider.py` | `WorkerInvocation.contract_digest` (optional). |

Profiles that do not pass `journal=` keep in-memory read-back. They are not claimed as durable or as multi-role
proof. That includes the existing offline, sandbox and GitHub profiles, which this candidate leaves unchanged.

## Fixture

`tests/invocation_runtime/k1_fixture.py` composes the production `OfflineProfile` over the following:

- A real SQLite store and `LocalWorkManagement`.
- `RealWorkerProvider` over `CliWorkerProvider`, a real `python -c` child process that commits into its worktree
  and logs each run outside it.
- `GitSourceControl` publishing to a local bare remote with fresh-clone read-back.
- `GitWorktreeAdapter` and `JsonlInvocationJournal`.

The fixture also fixes these conditions:

- The clock and git dates are injected (`1758542400`).
- The child environment is stated in full and contains no credential.
- The probe contract is the S0 probe contract, re-pinned to `K1-PROBE`.

Reopening a root is a restart: only the store, journal, remote and worktrees persist. Faults are injected only at
the journal boundary, or by killing the composing process (`python -m tests.invocation_runtime.k1_fixture
crash-after-outcome`, exit 17 right after the durable outcome).

## Material classes, probes and controls

| Class | Probe (`tests/invocation_runtime/test_real_worker_outcome.py::…`) | Control (fault → red) |
|---|---|---|
| Durable correlated read-back across restart | `test_real_path_durably_retains_attributable_outcome_and_reads_it_back_after_restart` | `readback_not_durable`: `read_back` answers from memory |
| Process success without a durable result holds | `test_process_success_without_a_durable_result_holds_the_transition`: exit 0, published candidate, outcome record lost → `IMPLEMENT`, `authority-block`, unknown effect, decision-inbox entry | `transition_gate_removed` |
| Wrong correlation holds | `test_miscorrelated_durable_result_holds_rather_than_being_accepted[role\|work_identity\|contract_digest\|candidate\|duplicate]` (in-run); `test_restart_read_back_holds_on_a_miscorrelated_record[role\|candidate]` (restart path, no in-memory outcome to compare) | `role_correlation_unchecked` (applied to `[role]`) |
| Restart keeps identity, no duplication | `test_restart_after_crash_reads_back_the_original_identity_without_duplicating_the_result`: the child is killed after the durable outcome; the restart recovers it once under `launch:K1-PROBE:0`, with one run, one outcome record, no unresolved effect or reservation, and an idempotent second restart | `recovery_identity_replaced` |

The split recommendation stays a compatibility constraint through the existing authority-block carrier. There is no
dedicated control for it.

## Commands (all under `rtk proxy`)

1. `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py tests/invocation_runtime/test_scripted_worker.py tests/invocation_runtime/test_real_worker_outcome.py`
2. `python3 -B tools/evidence/fx_k1_evidence.py --output <new-dir> --invocation <exact-invocation> --baseline <code-baseline>`.
   This runs (1), `check_architecture.py --check all`, `tests/test_architecture_fitness.py`, the full pytest suite
   and `node scripts/check.mjs all`, then applies each control once to a disposable copy. A full-suite failure is
   admissible only when the same nodes fail at the code baseline in a detached worktree.

## Compatibility edits outside the new surface

- `tests/control_plane/test_cli.py` and `tests/control_plane/test_operator.py`: two `Worker` fakes implemented `start`
  but not the Protocol's `read_back`. The gate now calls `read_back`, so each fake returns its outcome.

- `tests/execution_coordination/test_decision_inbox.py`: `EscalatingWorker` is declared `durable=True` but did not
  persist its authority-block outcome. Under the K1 gate an unrecorded outcome holds, so the fake now records it.
- `tests/composition/test_offline_proof.py`: the S0 frozen-kernel guard lists the kernel paths changed since
  `ade44cb`. K1's two authorized kernel edits are added. S0's historical proof and immutable manifest are unchanged.

## Independent pre-verification review and repairs

A read-only reviewer checked the first candidate `989facf`. It found no path to DONE without a correlated durable
result and no accepted miscorrelation. It raised these findings:

- **Repaired.** Without a journal, `RealWorkerProvider` stored no in-memory outcome for its early `ineligible`
  returns. The gate would then have parked a plain refusal as an authority block in profiles that pass no journal,
  such as the sandbox profile. `start` now records every returned outcome. Probe:
  `test_ineligible_outcome_reads_back_without_a_journal`.
- **Repaired.** On the in-run path, `(kind, candidate)` equality already masks the candidate-branch check. The new
  restart-path probe `[candidate]` goes red when `_publishes_to` is disabled. That check was run once by hand; it
  is not added to the harness, which keeps one control per class.
- **Repaired.** The harness output was not yet retained; it is now under `FX-K1/`.
- **Disclosed; no change.** The durable path is opt-in, and no existing profile opts in (see Surface).
- **Disclosed; no change.** Wrapping a journal-enabled `RealWorkerProvider` in `ScriptedWorkerProvider` on the same
  file would hold every run as a duplicate. That fails safe, and no composition does it.

The first harness run over `989facf` held on two full-suite nodes, `test_cli`/`test_operator`, which failed through
the fakes above. That run is superseded by the retained run and was not retained.

## Retained run

`FX-K1/` holds the run for invocation `AlienLogicLab/alienintent#113:PRODUCER:948a9918-30b9-433e-b80e-c324a4076e9b`.

- Source: clean committed revision `db4585ace3d2df5eac535c8d4c4e80ceafe72191`. Code baseline `fc5c0a7`.
- Result: exit 0, no holds.
- Checks: the focused suite, `check_architecture.py --check all`, the architecture fitness tests and
  `node scripts/check.mjs all` all exit 0.
- Controls: all 4 discriminate (intact 0, fault 1, restored 0).
- Full suite: 27 nodes fail (`tests/context_assembly/test_design_admission.py`,
  `tests/evidence_learning/test_proof_planning.py`). The same 27 nodes fail at the code baseline in a detached
  worktree, so they are recorded as the residual `PREEXISTING_BASELINE_FAILURES`, outside the K1 extent. This is
  the same residual FX-C3 recorded.
- Provider calls: 0. Tokens and cost: UNKNOWN.
- Independent verdict: pending.

## Non-claims

- No success-collapse removal, VERIFY/IMPLEMENT loop, verifier invocation or closure-action change (K2).
- No `RoleOutcomeRecord` or sidecar owner.
- No live or multi-role profile activation.
- No full SF-REQ-039 capstone.
- Token and cost are UNKNOWN (no provider composed), never zero.
