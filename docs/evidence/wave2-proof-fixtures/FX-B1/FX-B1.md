# FX-B1 — Operational trajectory receipts (WO-220504, SF-REQ-053)

Status: **PINNED before implementation** by PRODUCER invocation
`AlienLogicLab/alienintent#124:PRODUCER:a7d5020d-757d-44e2-8208-11d766e36362` (worker Morty),
admission baseline `01764fccf144a536023854dd533b05952131cb44`. This contract is committed before any
source change. Later commits may add evidence but may not weaken these probes. Changing them needs
the authority that owns the node.

**Owner:** `WO-220504` / DAG node `B1` (`live_trajectory_receipts`), Issue #124.
**Proof level:** `OPERATIONAL_OR_EXTERNAL_AUTHORITY`, on the bound `fx-b1-trajectory-operational`
target only. Local mechanical probes are labelled `LOCAL` and never satisfy operational acceptance.

## Governing inputs

- Work unit: `docs/work-units/wave2/WO-220504.md` ("Target binding — 2026-09-27" and
  "Cutover-reconciliation scope disposed — 2026-09-27"). Native Agent Ready READY
  `WO-220504.2026-09-27T131311.200780Z`, input SHA-256
  `3f9a56090cffb40cdfe0a20024801593db1f52762519c12761481dd1d7fe9fa4`.
- Execution packet: `docs/evidence/wave2-execution-packets/WO-220504.packet.json` and `.allocation.json`.
- Candidate contract sha256 `bad671f1e29119dfa83955c4a500d4dcf5ecec3a979d204c3c7728014d40ab77`.
- Target authority: Director inbox handoff `founder-authorize-local-live-proof-target-20260927T0102Z`
  (`AUTHORIZE_BOUNDED_LOCAL_OPERATIONAL_PROOF_TARGET_CREATION`, names #124).
- Predecessor, composed unchanged: WO-220610 / B1P / FX-B1P (Issue #140), accepted candidate
  `2d3d1f970e262e5f330cfb848784c74a0c991a0d`, landing merge `5f5d8de`. Through it: WO-220305 / C5
  (supervision, durable alert, granted restart) and WO-220301 / C1 (attention queue).

## Bound target

| Item | Value |
|---|---|
| Composition | `alienintent.composition.trajectory_capture` (B1P), unchanged |
| Supervisor | real `systemd --user` via `/usr/bin/systemd-run`, `/usr/bin/systemctl` (C5 `SystemdHostManager`) |
| Profile name | `fx-b1-trajectory-operational` |
| Profile root | `~/.local/state/alienintent/fx-b1/trajectory` — must be absent or empty when a run starts |
| Configuration | `<root>/fx-b1-supervision.json` (C5 supervision document plus `capture.stall_seconds`) |
| Host actor / authority | `factory-director` / `founder-authorize-local-live-proof-target-20260927T0102Z` |

The root is disjoint from the factory `state.json`, `worktrees/`, the coordinator observation files
and every live BIU claim. The root and its stores are **retained** after the run (the queue and the
journal stay readable); only the transient units are removed.

## What this node adds: live trajectory receipts (the attention producer)

`alienintent.composition.trajectory_receipts` is the attention producer that consumes the capture
journal. It integrates against B1P through B1P's own read-only journal reader and C5's own
attention profile for the same root; it changes neither.

- **Consumption pass** (`consume`). One pass, one process. It reads every committed journal entry
  (chain verified), then:
  1. verifies that the prefix it already receipted is byte-identical (prefix digest), and holds
     `RECEIPTS_PREFIX_MISMATCH` otherwise; a receipt chain longer than the journal holds
     `RECEIPTS_AHEAD_OF_JOURNAL`;
  2. for every anomaly in a newly committed entry, ensures exactly one C1 attention item in the
     profile's attention queue (`attention.sqlite`, the queue C5 alerts already use):
     `kind=JUDGMENT`, `work_ref=trajectory-capture:<stream>`, `event_identity=<anomaly_id>`,
     `work_revision=<entry digest>`, `lane=trajectory-anomaly:<KIND>`,
     `required_authority=<judgment_authority>`, `producer=trajectory-receipts`, and a
     `source_ref` naming the journal entry by its content digest;
  3. appends one **trajectory receipt**: an immutable content-addressed evidence `Observation`
     chained to the previous receipt, naming the entry range it consumed, the prefix digest, and for
     each entry its `entry_seq`, kind, launch, entry digest, the captured event's
     `capture_seq`/`event_id`/`identity`/`captured_at`, and each anomaly with its attention identity.
     The head pointer `trajectory-receipts:<stream>` in `trajectory-receipts.sqlite` advances by
     compare-and-set; a lost compare-and-set holds `RECEIPTS_VERSION_CONFLICT`.
- **Crash safety.** Attention items are ensured before the receipt commits. A pass that dies between
  the two re-ensures the same deterministic identities on the next pass: never a second item.
- **No new entries** means no receipt is written.
- **Readback** (`receipts`) is read-only: the receipt chain, the attention items this producer
  made, and a reconciliation of receipts against the journal (every committed entry receipted once,
  every captured event observed once with its journal identity, every anomaly with exactly one
  attention item).

Nothing here alerts, notifies, acknowledges, resolves or activates. The attention items stay
`PENDING`.

## Probes (local, mechanical; labelled LOCAL)

Test module: `tests/composition/test_trajectory_receipts.py`.

| Probe | Predicate |
|---|---|
| B1-01 receipts-observe-events | A pass over a seeded journal receipts every entry; each captured event's `capture_seq`/`identity`/`captured_at` in the receipt equals the journal. |
| B1-02 one-item-per-anomaly | Each of the five anomaly kinds yields exactly one PENDING JUDGMENT attention item with the pinned origin. |
| B1-03 idempotent-pass | A second pass with no new entries writes nothing and changes no item. |
| B1-04 restart-reconciles | Across a C5 kill and granted restart (in-memory manager), passes by fresh consumer objects before, during and after the restart receipt old and new entries once each, in order; the pre-restart receipts are an unchanged prefix. |
| B1-05 queue-retained | Items and receipts read back identically from fresh store objects after every restart. |
| B1-06 crash-between | A pass that fails after ensuring items but before committing its receipt, then reruns, leaves one item per anomaly and one receipt covering the range. |
| B1-07 prefix-rewrite-holds | A receipt chain whose prefix digest no longer matches the journal, or that is ahead of it, holds and writes nothing. |
| B1-08 second-consumer-refused | A lost receipt compare-and-set holds `RECEIPTS_VERSION_CONFLICT`. |

Operational driver checks: `tools/live/test_fx_b1_operational.py`.

| Probe | Predicate |
|---|---|
| B1-09 read-audit | The audit detector flags any opened path under a protected prefix outside the allowed root and names it; the operational run supplies the factory state directory as the protected prefix and the bound root as the only allowed subtree. |
| B1-10 root-guard | The driver refuses a root outside `~/.local/state/alienintent/fx-b1/`, a non-empty root, or a root containing `state.json`, before writing anything. |

### Discriminating controls (`tools/evidence/fx_b1_evidence.py`)

Each is applied once in a disposable copy: intact 0 → fault 1 with the named test failing → restored 0.

| Control | Material failure class | Mutation |
|---|---|---|
| `receipt_skips_events` | an attention-producer consumer does not observe the captured receipts | the receipt omits `EVENT` entries |
| `attention_not_produced` | an anomaly is not consumed into the attention queue | skip ensuring attention items |
| `prefix_unchecked` | pre/post-restart observations do not reconcile | drop the prefix-digest check |
| `receipt_before_attention` | a crash loses an anomaly's attention item | commit the receipt before ensuring items |
| `cursor_ignored` | an entry is consumed twice across restart | start every pass from entry 1 |
| `audit_blind` | a read of observer or factory state goes undetected | the detector ignores protected paths |

## Operational run (pinned commands)

All commands run with `PYTHONPATH=src` and `XDG_RUNTIME_DIR=/run/user/<uid>`. The driver runs every
CLI below as a subprocess under the read-audit wrapper `tools/live/fx_b1_audit.py`, which records
every path opened by that process.

```
python3 -B tools/live/fx_b1_operational.py run --root ~/.local/state/alienintent/fx-b1/trajectory \
  --output docs/evidence/wave2-proof-fixtures/FX-B1/operational/<UTC stamp> --invocation <exact invocation>
```

It performs, in order, on the bound root:

1. **Provision**: root guard; write `fx-b1-supervision.json` (`stall_seconds` 2).
2. **Launch**: `trajectory_capture launch --config <root>/fx-b1-supervision.json --actor factory-director --authority <authority>`.
3. **Seed**: `trajectory_capture submit` — events 1, 2, 3, 6 (SEQUENCE_GAP), 4 late (OUT_OF_ORDER),
   2 again (DUPLICATE_IDENTITY), 7 with an older clock (TIMESTAMP_REGRESSION); then wait for the
   `CAPTURE_STALL` record.
4. **Consume 1**: `trajectory_receipts consume` (fresh process).
5. **Fault**: `systemctl --user kill --signal=SIGKILL --kill-whom=main <unit>`; wait for the C5 alert
   `UNIT_FAILED_FAILED_SIGNAL`; a submission while down must not be accepted.
6. **Consume 2 while down**: the journal stays readable, no receipt is written, and the attention
   queue reads back identical (queue retained).
7. **Restart**: `trajectory_capture restart ... --replaces <launch 1> --alert <alert>`.
8. **Post-restart**: retry of event 7 (recorded `DUPLICATE`); event 9 (`SEQUENCE_GAP` for 8, emitted while down).
9. **Consume 3** and **Consume 4** (fresh processes; 4 must write nothing).
10. **Readback**: `trajectory_capture journal`, `trajectory_receipts receipts`, and
    `attention_inbox list` over the same root (independent C1 reader).
11. **Teardown**: stop the observer timer/service and the unit, `reset-failed`, confirm no unit remains.

Expected outcome: exit 0, `OPERATIONAL_READBACK_COMPLETE`, with every predicate below `PASS`.

| Acceptance (packet) | Operational predicate |
|---|---|
| identity/order/timestamps stable across kill/restart | every acknowledgement equals the post-restart journal; pre-kill events are an unchanged prefix; `capture_seq` gapless; `captured_at` non-decreasing |
| five anomaly classes durable | all five kinds read back from the journal after the restart |
| no loss or duplication; queue retained and readable | every CAPTURED acknowledgement present exactly once; the retry is `DUPLICATE`; attention items identical before/during the outage and a superset after, zero duplicate origins |
| pre/post-restart observations reconcile (disposed cutover) | receipts cover journal entries 1..N exactly once in order; the second session's `reconciled` counts equal the pre-kill journal |
| attention-producer consumer observes the receipts | the receipts name every captured event with its journal identity; one PENDING JUDGMENT item per anomaly, read back by `attention_inbox list` |
| non-claims | the record states no observer replacement/retirement, and the read audit shows no path opened under `~/.local/state/alienintent` outside the bound root |

Negative controls recorded by the operational run: the root guard result; the audit's opened-path
set and the empty forbidden set; the unit list after teardown. The capture host process itself runs
under `env -i` in its transient unit and is not audited; its configuration names only paths inside
the root and the source tree, which the record binds by digest (label `HOST_PROCESS_CONFIG_CONFINED`).

## Clarification after independent review — 2026-09-27

An independent read-only review of implementation commit `31fae99` found that the audit was less
strict than this contract states. This section records the repair. It adds probes and narrows what
the audit allows; no probe above is weakened.

- **Allowed subtrees, stated exactly.** Every audited process imports the candidate's own source,
  and this checkout sits under `~/.local/state/alienintent/worktrees/`. The allowed set is therefore
  the bound root, plus from this checkout only `src/`, `tools/` and the run's output directory.
  It is recorded as label `AUDIT_ALLOWS_CANDIDATE_SRC_TOOLS_OUTPUT`. The first implementation allowed
  the whole checkout; that is withdrawn.
- **Child processes and symlinks.**
  - The audit records every child process (`subprocess.Popen`, `os.exec`, `os.posix_spawn`,
    `os.spawn`, `os.system`) with its argument vector.
  - Every absolute path argument counts as a touched path.
  - Symlinks are resolved on both sides of the forbidden-path check, and an undecodable path is
    always forbidden.
  - An executable outside `python3`, `systemd-run`, `systemctl` and `env` makes the
    observer-boundary predicate HOLD.
  - New probe: `test_the_audit_names_a_protected_path_reached_through_a_child_process_or_symlink`.
- **Unaudited units.** The C5 monitor-observer unit (`trajectory_capture observe`) runs unaudited
  under systemd, in addition to the capture host. Both are bound by their configuration, which
  names only the root and the source tree (label `HOST_AND_MONITOR_OBSERVER_UNITS_CONFIG_CONFINED`).
- **Predicates decided from counts and every status.**
  - Queue retention and the PENDING check now use `trajectory_receipts receipts`, which reads
    items in every status, at each stage. `attention_inbox list` reads only pending items.
  - The operational predicates assert the pinned counts: 7 captured events (6 before the kill),
    5 items before and during the outage, 7 after, and exactly one refused submission while down.
- **Store faults and origin checks.**
  - A store fault while ensuring an item holds `ATTENTION_STORE_UNAVAILABLE:<error>` and writes no
    receipt.
  - `reconcile` compares every item with the origin its journal entry implies (kind, lane, entry
    digest, authority), and with the attention identity named in the receipt. It also compares
    every receipted entry digest with the journal.
  - New probes: `test_a_store_failure_while_ensuring_items_holds_and_writes_no_receipt` and
    `test_an_item_whose_origin_differs_from_its_entry_does_not_reconcile`.
- **Retained readback.** `readback --root <root> --output <dir>` reads a retained root through the
  same CLIs under the same audit. It returns `RETAINED_READBACK_RECONCILED` only when the audit
  finds no forbidden path.

## Evidence schema

Local run (`local-run/<UTC stamp>/`) and operational run (`operational/<UTC stamp>/`) each hold:
`execution-record.json` (`ProofFixtureExecution`: fixture, BIU, invocation, source revision and
status, admission baseline, predecessor custody, input digests, commands with argv/exit status/
observation ref, predicates or probes, holds, run state, exit status), `run-report.json` or
`readback.json`, `proven-red.json` (local only), `observations/<sha256>` (immutable canonical JSON)
and `digest-manifest.json`. A missing measurement or readback is a HOLD, never a PASS. Tokens, cost
and provider calls are `null` with an `UNKNOWN` reason. The independent verdict is
`PENDING_FRESH_BIU_VERIFIER`.

## Feature regression pack

`tools/verification/feature_regressions.json` registers `live-trajectory-receipts`, running
`tests/composition/test_trajectory_receipts.py` and `tools/live/test_fx_b1_operational.py` for any
change to the receipts composition, the B1P capture sources it reads, the C1 attention sources it
writes through, or the FX-B1 tools. The receipt custody rule of FX-B1P applies unchanged.

## Non-claims

- No claim that `alienintent-observer.service` is replaced, retired, read or perturbed. The proof
  reads none of its data; "old/new observations across cutover" are this composition's own
  pre/post-restart observations (disposed 2026-09-27).
- No claim that this proof substitutes for FX-B1P; B1P's composition-level evidence is cited.
- No release, migration cutover, persistent unit installation, notification, acknowledgement,
  resolution or activation is performed or authorized.
