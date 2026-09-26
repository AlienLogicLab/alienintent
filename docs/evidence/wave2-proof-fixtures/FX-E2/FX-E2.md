# FX-E2 — Conditional one-writer migration and rollback substrate (WO-220503, Issue #123)

Status: **PINNED before implementation** by PRODUCER invocation
`AlienLogicLab/alienintent#123:PRODUCER:159cdf95-a22d-49e1-a910-6f6a1cd7dc1c` (worker Morty),
admission baseline `b07be02db62bdbc1c39753de4da32697b6dbd4e0`. This contract is committed before any
source change. Later commits may add evidence but may not weaken these probes or controls. Changing
them needs the authority that owns the node.

## Governing inputs

- Work unit: `docs/work-units/wave2/WO-220503.md`. Agent Ready READY input SHA-256
  `9dde655ebd91a8fc1e4d20b5b3994ba061adfc12c3bee90b338ab522a01cffee`.
- Execution packet: `docs/evidence/wave2-execution-packets/WO-220503.packet.json` and `.allocation.json`.
- DAG node E2, capability `one_writer_cutover_control`, migration `M-CUTOVER` (`conditional_one_writer`).
  Candidate contract sha256 `fa63d0cd88b48f5ca98f0315470e1dedfa0e1e450fdd680f1179d4953b567b12`.
- Authority: Founder decision `WAVE2_BOUNDED_OPERATIONAL_AUTHORITY_DELEGATION`
  (`docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md`). It disposes
  EXPLICIT_SOVEREIGNTY_CUTOVER_AUTHORITY, EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY and POSTW1-DECIDE-006A
  for this BIU's **isolated-rehearsal extent only**. Release on Issue #123 (2026-09-26T21:11:00Z) under SWF-35.
- Procedure source: `docs/architecture/pre-python-gate/conformance-and-sovereignty.md` § "Cutover and rollback".

## Predecessor proof (step 1, done before this pin)

[`predecessor-reuse/predecessor-reuse.json`](predecessor-reuse/predecessor-reuse.json) records the result:
**CONFIRMED_REUSABLE**.

- WO-220502 / FX-E1: accepted candidate `5a98c26a…`, landed in `c5ef2bc`. At this baseline, the
  evaluator replays the accepted run at 10/10 PASS with K1–K10 discriminating, and
  `tools/live/test_fx_e1.py` gives 8 passed. E1 identified the canonical Python control
  (`py10-sandbox`, production path `alienintent.composition.sandbox_run_profile:profile`). It also
  identified the live Node writer (`AlienLogicLab/alienintent`, Project #1), which is must-not-touch.
- WO-220302 / FX-C2: accepted candidate `46920041…`, landed in `7b6e19c`. The harness re-run at the
  exact accepted SHA exits 0 with 13/13 controls. At this baseline the focused reconstruction tests
  give 18 passed.

## What E2 delivers (the canonical control this BIU owns)

Before this BIU, the repository had no cutover control. Neither runtime has a writer lease,
checkpoint or rollback. E2 **is** the node that owns `one_writer_cutover_control`, so building the
substrate is this BIU's own scope. It is not the B6 capstone implementing its own machinery.

The substrate is one bounded Python unit inside `execution_coordination`:

| Layer | Path | Role |
|---|---|---|
| domain | `src/alienintent/execution_coordination/domain/cutover.py` | writer-authority record and admission; Node state inventory, quiescence and reconciliation plan; rollback overlay. Pure. |
| ports | `src/alienintent/execution_coordination/ports/cutover.py` | writer-authority record store, checkpoint store and Node-writer observation. |
| adapters | `src/alienintent/execution_coordination/adapters/cutover_files.py` | file writer-authority record with compare-and-set on epoch under an exclusive lock; checkpoint of Node state bytes plus a SQLite online backup, with a sha256 manifest. |
| application | `src/alienintent/execution_coordination/application/cutover.py` | `OneWriterCutover`, which runs M-CUTOVER: canonical-control check, isolation check, inventory, quiescence, checkpoint, reconcile, activate exactly one writer, admission, Node-writer detection and rollback. |

Writer-authority record: `{schema_version:1, scope, writer: "NODE"|"PYTHON"|null, state: "ACTIVE"|"HELD",
epoch, checkpoint, reason}`. Every writer transition increments `epoch`. A dispatch is admitted only when
the record is ACTIVE, the writer matches, and the epoch equals the record's current epoch.
Otherwise it gets the typed refusal `WriterRejected(code)`:

- `HELD`: the record is held;
- `NOT_APPROVED_WRITER`: another writer holds the record;
- `STALE_EPOCH`: the caller's epoch is not current.

Ambiguity holds **both** dispatch paths (`state=HELD`, `writer=null`), and durable state is retained.

The Node state schema is read exactly as `src/runtime/dispatcher.mjs` writes it. Its keys are
`active`, `resources`, `deliveries`, `closures` and `diagnostics`, and pending intents are
`pendingSignal`, `pendingStatus` and `pendingOperatorEvent`. The substrate never writes a live Node
state file. It reads only a copy inside the isolated rehearsal root.

## Probes (LOCAL, mechanical; never operational acceptance)

Test module: `tests/execution_coordination/test_one_writer_cutover.py`.

| Probe | Predicate |
|---|---|
| E2-01 isolation | The rehearsal refuses, with `ISOLATION_VIOLATION`, to operate when its root, Node state path or Python store path is, or lies under, a configured must-not-touch path. The live Node state and live sandbox store are the defaults. Refusal comes before any file is written. |
| E2-02 keep-node | If canonical control is absent, the disposition is `RETURN_TO_EXISTING_AUTHORITY`: the record stays NODE/ACTIVE at the same epoch, no checkpoint or reconciliation is written, and Python dispatch is refused. |
| E2-03 quiescence | Each blocker holds `NOT_QUIESCED` with its named reason and no writer change: a live worker PID on an active claim, a pending intent (`pendingSignal`/`pendingStatus`/`pendingOperatorEvent`), a resource in `ALLOCATING`/`LAUNCHING`/`RUNNING`, a delivery in `PROCESSING`, or an observed live Node writer process. A quiesced state passes. |
| E2-04 checkpoint-integrity | The checkpoint binds the Node state bytes and a SQLite online backup of the Python store with sha256 digests. Verification recomputes them. A tampered or missing member holds `CHECKPOINT_CORRUPT` for both cutover and rollback. |
| E2-05 reconciliation | Every Node active lane, resource and closure maps to exactly one durable Python record: a pending reservation (scope `cutover-lane`) or a confirmed effect (`node-effect:<invocationId>`, receipt naming the Node result). Counts match the inventory. The reconciliation record is written as an aggregate at the cutover epoch and survives reopening the store. An active lane with neither a result nor a reservation holds `RECONCILIATION_AMBIGUOUS`. |
| E2-06 pending-reservations | Each pending Node reservation (resource `READY`, or an active claim without a result) becomes a Python reservation with the same identity. It remains present after cutover and after rollback, and is never silently released. |
| E2-07 one-writer | After cutover, Node admission is refused and Python is admitted at the current epoch. Two controllers racing to activate from the same epoch produce exactly one winner; the loser gets `VersionConflict`. A Node state change after the checkpoint (Node writer detected) moves the record to HELD, and then **both** Node and Python are refused. |
| E2-08 nonduplicating-rollback | After Python confirms an effect for a migrated lane, rollback restores Node from the verified checkpoint and marks that lane completed (removed from `active`, resource `REMOVED` with a `cutover-rollback` diagnostic). Rollback does not leave the lane to be re-dispatched. Every other pending reservation is retained unchanged. Node's confirmed effects are identical before and after. Running rollback a second time changes nothing. |
| E2-09 rollback-order | Rollback first moves Python to HELD (epoch +1). It refuses with `PYTHON_EFFECTS_UNRECONCILED`, and leaves Node disabled, while any Python effect is pending or unknown or a Python-originated reservation is unreleased. Node is re-enabled (NODE/ACTIVE, epoch +1) only after that check passes. |
| E2-10 durability | A fresh controller instance on the same root reads back an identical writer record, epoch, checkpoint reference and reconciliation record. No conversation or in-process state is used. |

## Mechanical controls (intact / fault / restored)

Each control is applied once to a disposable `git archive HEAD` copy by `tools/evidence/fx_e2_evidence.py`.
The intact and restored runs must pass. The fault run must fail with an `AssertionError` that
contains the pinned assertion text. The application count must be exactly 1.

| Control | Failure class | Assertion text |
|---|---|---|
| `quiescence_ignores_pending_intent` | quiescence asserted with an unresolved external intent | `a pending intent must block quiescence` |
| `checkpoint_unverified` | checkpoint integrity not verified | `a tampered checkpoint must hold` |
| `admission_unchecked` | simultaneous Node/Python writer not rejected | `the non-approved writer must be refused` |
| `rollback_replays_python_effect` | rollback duplicates an effect Python already confirmed | `a lane Python completed must not be re-dispatchable after rollback` |
| `reservation_dropped` | pending reservation lost in migration | `every pending reservation must be retained` |
| `keep_node_bypassed` | canonical control absent but migration proceeds anyway | `absent canonical control must keep Node` |
| `rollback_before_python_stopped` | old writer enabled before the new writer is stopped and reconciled | `Node must stay disabled while Python effects are unreconciled` |

## Commands (pinned)

```
PYTHONPATH=src:. python3 -B tools/evidence/fx_e2_evidence.py --output <new dir> --invocation <exact invocation>
```

This runs:

1. `python3 -B -m pytest -q -p no:cacheprovider -rfEs tests/execution_coordination/test_one_writer_cutover.py`, the focused probes;
2. `python3 -B -m pytest -q -p no:cacheprovider tests/execution_coordination/test_operational_store.py tests/execution_coordination/test_fenced_store.py tests/execution_coordination/test_factory_coordinator.py`, the adjacent store and coordinator suites;
3. `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`;
4. `python3 -B -m pytest -q -p no:cacheprovider tools/verification/test_feature_regressions.py`;
5. the seven controls above.

Expected outcome: exit 0, `run_state=COMPLETE`, E2-01…E2-10 PASS, and all seven controls discriminating.
A registered feature-regression pack, `one-writer-cutover-fx-e2`, re-runs the focused probes for any
change on the substrate paths.

## Evidence schema

The evidence layout is the FX-B5/FX-C layout under `FX-E2/local-run/<UTC ts>/`:

- `execution-record.json`:
  - `fixture`, `biu`, `issue`, `label: "LOCAL"`, `invocation`, `admission_baseline`;
  - `source_candidate`: the commit, and a digest for every source file;
  - `commands[]`: `argv`, `exit_status` and an `observation` ref for each;
  - `probes{}`, `holds[]`, `run_state`, `exit_status`, `non_claims`.
- `proven-red.json`: the controls, with application counts and intact/fault/restored observation refs.
- `run-report.json`: acceptance criteria mapped to probes, and `operational_acceptance: NOT CLAIMED`.
- `digest-manifest.json`, plus `observations/<sha256>` holding immutable canonical JSON.

An interrupted run reads as INCOMPLETE. Missing measurements are holds, never zero or PASS.

## Substitutions (labelled)

- **The Node writer is represented by its state file, not a Node process.** The rehearsal Node state
  uses the exact `dispatcher.mjs` schema. Node writer activity is simulated by writing that file the
  way `EventRelay.save()` does: a temp file plus an atomic rename. No Node process is started. The
  live Node runtime, its state file, `AlienLogicLab/alienintent` and Project #1 are not read or written.
  The Node runtime is not modified. Making Node consult the writer record is part of any future live
  cutover, under that cutover's separate grant.
- **The Python writer is the shipped `SQLiteOperationalStore`**, on a disposable root. No provider,
  GitHub call, tunnel or ingress is used.

## Non-claims

- LOCAL proof only. This is not operational acceptance, release, live cutover, a production writer
  switch, live self-hosting, or Node/bootstrap retirement.
- The "prove Node-independent live self-hosting" wording in the fixed decisions belongs to the B6
  capstone and to a future operational grant. This BIU's completion predicate is the isolated rehearsal.
- No sibling BIU scope. No change to `src/runtime/*.mjs`, `bin/` or live configuration.
