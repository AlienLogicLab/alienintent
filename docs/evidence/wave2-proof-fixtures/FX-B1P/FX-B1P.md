# FX-B1P — live trajectory-capture composition (WO-220610, SF-REQ-053)

**Owner:** `WO-220610` / DAG node `B1P` (`live_trajectory_capture`), Issue #140. This is a bounded prerequisite
implementation BIU that WO-220504/B1 integrates later.
**Proof level:** `LOCAL_SELF_SUPERVISED`. **Live proof:** `NOT_ESTABLISHED`.

- **Contract input:** `docs/work-units/wave2/WO-220610.md`. This is the exact input of the native READY assessment
  `WO-220610.2026-09-27T023136.204114Z`.
- **Execution packet:** `docs/evidence/wave2-execution-packets/WO-220610.packet.json` and `WO-220610.allocation.json`.
- **Release baseline:** `322baf4ae45776acb59d303370b12d48d76085ee`. This is the Factory Director READY → IMPLEMENT
  release record on Issue #140, 2026-09-27T02:37:13Z.

## Predecessors composed unchanged

| BIU | Node | Fixture | Accepted candidate | Landing merge |
|---|---|---|---|---|
| WO-220101 (#69) | S0 | FX-S0 | `761a3cb4d6e24dc24ec370de45e25fe8c505eeda` | `9174849713df2685117de7a8150126d916a4b644` |
| WO-220305 (#114) | C5 | FX-C5 | `ef29d04e9c6bbc4fe3211472daa66819aca7298d` | `7ccb1e74b1abd3bfe356595258d5222b6ede91cb` |

The harness checks that each candidate and each landing merge is an ancestor of this candidate. It also checks that
these sources are byte-identical to the release baseline:

- the C5 host, supervisor, manager, alert and ownership sources;
- `composition/offline_proof.py`, the S0/WO-220101 offline trajectory writer;
- the evidence repository and SQLite store.

No predecessor file changes in this BIU.

## What was built

- **Values** (`evidence_learning/domain/trajectory_capture.py`). A `Submission` is what a live source hands the
  capture. Its `event` is a trajectory event in the same shape as the S0 offline writer's `trajectory.jsonl` rows:
  it names `event_id` and `event_type`, and every other field is kept verbatim. The submission also carries the
  source's own 1-based `source_seq` and its own clock, `observed_at`, in integer UTC microseconds.
  - `CaptureState.apply` is the only state transition. It is used both live and on replay, so a restarted capture
    rebuilds exactly the state the killed one had.
  - `admit`, `session` and `stall` build journal entries. None of them waits, alerts or halts.
- **Journal** (`evidence_learning/ports/trajectory_journal.py`, `adapters/trajectory_journal.py`). This uses the same
  write discipline as C5's `monitor-host:<profile>` history:
  1. Each entry is an immutable, content-addressed `Observation` in the typed evidence repository, chained to its
     predecessor.
  2. The head pointer `trajectory-capture:<stream>` in `trajectory-capture.sqlite` then advances by compare-and-set.

  An entry is **accepted exactly when the pointer names it**. A crash between the two steps leaves an unreferenced
  object and no accepted entry. The stream is the supervised `host_invocation`, so a restarted launch reopens the same
  journal.
- **Capture service** (`evidence_learning/application/trajectory_capture_service.py`). There is one writer per launch.
  - `start` replays and verifies the whole chain, then records the launch's `SESSION` entry naming what it
    reconciled: entries, events, prior sessions and per-source cursors.
  - `submit` acknowledges only after the commit.
  - A lost compare-and-set (`JOURNAL_VERSION_CONFLICT`) means another writer exists; the host exits as superseded.
- **Composition** (`composition/trajectory_capture.py`). This is the C5 supervision, reused unchanged.
  - `TrajectoryCaptureProfile` is `MonitorHostProfile`, and only its hosted command changes, to this module. The
    `MonitorHostSupervisor` is untouched, so launch, the manager-owned observer timer, the durable alert and the
    explicitly granted restart are C5's. The transient `Restart=no` unit under `app.slice` with `env -i` is also C5's.
  - The capture process body first constructs C5's `HostedMonitor`. All C5 refusals happen before the capture journal
    is opened: `HOST_NOT_OWNED`, `HOST_OUTSIDE_OWNED_UNIT` and `HOST_CONFIGURATION_CHANGED`. The process then ticks
    its C4 generation every `I`, so the external observer sees its health exactly as for C5.
  - The only new configuration is a `capture.stall_seconds` section in the same supervision document. Each `SESSION`
    entry records the policy it ran under.

### Pinned engineering choices (the READY assessment's open unknowns)

- **Ingestion interface.** One JSON `Submission` per connection on the Unix socket `<root>/trajectory-capture.sock`
  (mode 0600). The reply is sent only after the entry commits:
  - `CAPTURED` with `capture_seq`, `identity` and `captured_at`;
  - `DUPLICATE` naming the original;
  - `{"hold": ...}` for an invalid submission, which writes nothing.

  A client must finish its submission within 0.5 s, or it is dropped with nothing written. This keeps the
  single-threaded host's C4 tick inside its bound. Unparsable, over-deep or oversized input is a hold, never a crash.
  A source that cannot connect has nothing accepted; nothing is buffered for a down capture. B1 can integrate a real
  source through the same `submit` without redefining the interface.
- **Assignment.** The capture assigns every value itself, at acceptance:
  - `identity` is the sha256 of exactly what was submitted;
  - order is a gapless `capture_seq`;
  - `captured_at` is the capture's clock.

  The source's own `source_seq` and `observed_at` are kept verbatim and are only inputs to anomaly detection.
  `captured_at` never runs backwards: a regressed capture clock is recorded, and the event is stamped with the last
  capture time.
- **Restart reconciliation.** The journal is the only resume state: replay the chain, then append a `SESSION` entry.
  A duplicate is detected by `event_id` against the replayed index. A retry of an event whose acknowledgement was lost
  is recorded as `DUPLICATE_IDENTITY` (with `same_content: true`). It is never captured twice.
- **Anomaly classes** (disposed 2026-09-27; record only, no alert or halt). Each is one durable anomaly record inside a
  journal entry, with its own `anomaly:<entry_seq>:<n>` identity:

  | Class | Recorded when | Is the event captured? |
  |---|---|---|
  | `SEQUENCE_GAP` | `source_seq` is above the source's high mark + 1 | yes |
  | `OUT_OF_ORDER` | `source_seq` is at or below the high mark, with a new `event_id` | yes |
  | `DUPLICATE_IDENTITY` | the source already had this `event_id` captured (ids are unique within a source) | no: a `DUPLICATE` entry, never a second capture |
  | `TIMESTAMP_REGRESSION` | an event advancing the source's order has an `observed_at` below the highest the source already reported, or the capture clock went backwards | yes |
  | `CAPTURE_STALL` | no event was accepted for longer than `stall_seconds` | not applicable (no event) |

  A late (out-of-order) event is expected to be older and is not also a timestamp regression.

  A capture stall is measured from the later of the last accepted event and the current session start. The host checks
  for it after every poll (0.1 s) and after every served connection. A detected stall is recorded once per idle
  interval, and the record is durable: a restart neither loses nor repeats it. An idle interval that ends before any
  check runs (by an event or a kill) is not recorded. The window is bounded by the poll plus the per-connection read
  deadline.
- **Restart-loss boundary** (disposed). The guarantee covers only entries already committed at the kill. Events a
  source emits while the capture is down are not recovered. The next accepted event from that source shows them as a
  `SEQUENCE_GAP`, and the composed probe demonstrates this.

## Probes

| Acceptance | Mechanical (`tests/evidence_learning/test_trajectory_capture.py`, `tests/composition/test_trajectory_capture_host.py`) | Composed, real manager (`tests/composition/test_trajectory_capture_systemd.py`) |
|---|---|---|
| (a) identity/order/time assigned, stable across restart | `test_capture_assigns_identity_order_and_time`, `test_restart_reconciles_accepted_events_without_loss_or_duplication` | every acknowledgement's `capture_seq`/`identity`/`captured_at` equals the journal after restart; pre-kill events are an unchanged prefix |
| (b) no loss or duplication across restart | `test_restart_reconciles_…`, `test_an_unacknowledged_submission_was_never_accepted`, `test_a_killed_capture_is_detected_and_its_granted_restart_loses_and_duplicates_nothing` | SIGKILL → observer alert `UNIT_FAILED_FAILED_SIGNAL` → granted restart → C4 generation 2; the retry is `DUPLICATE`; a submission while down is refused, and the next event records the gap |
| (c) each anomaly class durable | `test_each_seeded_anomaly_class_is_recorded_durably`, `test_stall_is_measured_from_…_and_not_repeated`, `test_source_clock_regression_is_measured_against_the_highest_reported_time`, `test_event_ids_are_unique_within_their_source_only` | all five kinds are read back from the journal after restart; source-clock regression is seeded, and capture-clock regression is mechanical only |
| (d) durable and readable after restart | every assertion reads from fresh store objects; `test_a_broken_or_inconsistent_journal_holds` | fresh reader in the test process; `SESSION` reconciliation counts |
| (e) own local systemd `--user` supervision only | `test_the_c5_supervisor_launches_and_observes_the_capture_host`, `test_the_capture_host_refuses_outside_its_owned_unit_before_opening_the_journal` | `host` from the session process exits 3 `HOST_OUTSIDE_OWNED_UNIT`; transient units are removed at the end |

## Discriminating controls (`tools/evidence/fx_b1p_evidence.py`)

The harness applies each control exactly once, in a disposable copy. It records intact 0 → fault 1 with the named
test failing → restored 0.

| Control | Material failure class | Mutation |
|---|---|---|
| `order_from_journal_position` | identity/order/timestamp incorrect | `capture_seq` from the journal position |
| `capture_time_not_monotonic` | identity/order/timestamp incorrect | drop the capture-clock clamp |
| `ack_without_durable_commit` | accepted event lost across restart | acknowledge events without committing them |
| `duplicate_recaptured` | accepted event duplicated across restart | ignore the captured `event_id` index |
| `restart_clean_start` | restart does not reconcile the journal | each launch opens its own stream |
| `sequence_gap_undetected`, `out_of_order_undetected`, `timestamp_regression_undetected`, `capture_stall_undetected` | a seeded anomaly class is not detected or recorded | disable that one detection |

`DUPLICATE_IDENTITY` detection is discriminated by `duplicate_recaptured`.

## Commands

All commands run with `PYTHONPATH=src:.` and `XDG_RUNTIME_DIR=/run/user/<uid>`.

1. `python3 -B -m pytest -q tests/evidence_learning/test_trajectory_capture.py tests/composition/test_trajectory_capture_host.py`
2. `python3 -B -m pytest -q tests/composition/test_trajectory_capture_systemd.py`. A skip is a HOLD.
3. The predecessor regressions:
   - `python3 -B -m pytest -q tests/control_plane/test_monitor_host.py tests/control_plane/test_monitor_host_systemd.py`
     (C5; a skip is a HOLD);
   - `python3 -B -m pytest -q tests/composition/test_offline_proof.py` (S0).
4. `python3 -B tools/verification/run_feature_regressions.py --base 322baf4ae45776acb59d303370b12d48d76085ee --candidate HEAD`
5. The terminal checks:
   - `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`
   - `python3 -B -m pytest -q tests/test_architecture_fitness.py`
   - `python3 -B -m pytest -q`. This is compared with the admission baseline in a disposable worktree; identical
     failing node ids are recorded as `PRE_EXISTING_BASELINE_FAILURE`.
   - `node scripts/check.mjs all`
6. `python3 -B tools/evidence/fx_b1p_evidence.py --output <new dir> --invocation <exact invocation>`. The harness runs
   all of the above and must run on a clean committed candidate.

## Feature regression pack

`tools/verification/feature_regressions.json` registers `live-trajectory-capture`. It runs the two mechanical test
files for any change to:

- the capture sources and the evidence repository;
- the C5 host, supervisor and domain it composes;
- `tests/control_plane/test_monitor_host.py`, whose in-memory manager the composed test reuses;
- the FX-B1P tests or harness.

The real-manager probe stays in this fixture.

## Evidence

The evidence commit retains the harness run under `local-run/<UTC stamp>/`. The retained files are:

- `execution-record.json` (`ProofFixtureExecution`);
- `run-report.json` (the acceptance mapping and the composed readback);
- `proven-red.json`;
- `observations/`;
- `digest-manifest.json`.

A missing measurement or readback is a HOLD, never a PASS. Tokens, cost and provider calls are `null` with an
`UNKNOWN` reason. The independent verdict is `PENDING_FRESH_BIU_VERIFIER`.

## Non-claims

- The fixture binds, requests or proves nothing against a live operational target. It issues no live trajectory
  receipts: that is `live_trajectory_receipts`, WO-220504's own scope.
- There is no claim of external-observer replacement or retirement. `alienintent-observer.service` is untouched.
- No buffered or replayable upstream source is built. No unit is installed or enabled persistently; the fixture's
  transient units are removed at the end of the run.
- No release, cutover or broader production mutation is authorized by this proof.
