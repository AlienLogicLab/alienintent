# SF029-SWF27-LEDGER candidate fixture

Authority: AlienLogicLab/alienintent#143, RELEASED/READY, baseline
`e6a10e3d83e7ec97b28df8494a0f7653ff403f8d`. This is a disposable local
fixture. It does not install a service, change the host state store, or grant
successor operation.

## Source contract

`src/runtime/node-state-ledger.mjs` owns `node-state-ledger.jsonl` beside the
configured `state.json`. The installed profile's state directory yields the
specified `/home/netmarine/.local/state/alienintent/node-state-ledger.jsonl`.
Each JSONL line is one canonical-digest-linked full post-state record. Schema
version 1 has `revision` (genesis UUID), `sequence` (zero-based),
`previousDigest`, `sourceUtc`, `changedLanes`, `occurrences` (stable
`revision:sequence:index` IDs with lane, field, invocation and outcome),
`stateDigest`, complete `state`, and `digest`. Genesis has
`historyBeforeGenesis: UNKNOWN`; it reports no invented transitions.
Canonical SHA-256 input is JSON with object keys sorted recursively, UTF-8,
without whitespace. The digest field is excluded from its own input.

The sole Dispatcher process acquires `node-state-ledger.jsonl.writer` using
exclusive creation before genesis, replay, or save. A live PID holds another
process out; a dead PID can be reclaimed. The same process checks its exact
lock identity on each replay. The migration barrier is first replay under this
lock, with the legacy `state.json` read once as the observed genesis state.
The installed writer must be quiesced for a version handoff; this candidate
does not perform that operational handoff. Every later save validates the
ledger, appends a full record and fsyncs the file, syncs its directory, writes
and syncs a head witness by atomic rename, then writes and syncs the JSON
projection by atomic rename. Both sidecars are mode 0600. The head witness
rejects deletion of a whole committed tail record. A head lag after a
committed append is recoverable. The compatibility projection remains plain
`state.json` with historical field names and values; replay replaces it when
its content differs from the committed post-state.

The Dispatcher checks replay/projection/source identity before startup Project
reads, webhook routing, direct admission, result routing, status transition,
closure resume and worker launch. Append or replay failure prevents the
following effect. A committed append remains authoritative if head update,
projection, or acknowledgement fails; restart repairs the projection without
repeating that save.

## `save(state)` coverage

All existing callers still use the one method: resource allocation/update and
cleanup; delivery reservation, completion and retry; diagnostics and release;
result intent, evidence and terminal outcome; operator recovery and pending
status; execution limit state and escalation; new claim reservation, launch
intent, PID and supervision; and startup recovery of active/diagnostic claims.
The source record includes deliveries, active claims, diagnostics, closures,
founder exceptions, resources, execution limits and any other persisted
property, even when no lane changes.

## Disposable proof matrix

Command: `rtk proxy node --test test/dispatcher.test.mjs test/legacy-state.test.mjs`
from the candidate worktree. The retained raw output is
`ledger-focused-tests.tap`. The focused tests use temporary directories and
synthetic launch/Project counters. In the table, `sequence count` is the number
of complete JSONL records; `effect count` is worker launches or Project reads
after the tested refusal boundary.

| Control | Expected | Observed | Exit |
| --- | --- | --- | --- |
| Intact genesis, save, restart | sequences 0 and 1, full post-state, no replay duplicate | 2 records, same complete state after restart | 0 |
| Before append fault | genesis only, 0 launches | 1 record, 0 launches | 0 |
| Committed append before head/projection | sequences 0 and 1, repaired projection, no duplicate | 2 records, repaired projection | 0 |
| Projection before acknowledgement | sequences 0 and 1, no duplicate | 2 records, committed state retained | 0 |
| Interrupted replay | 2 records, 0 Project reads/launches until repair | 2 records, 0 reads, 0 launches | 0 |
| Competing writer process | refused before source read | child nonzero, `LEDGER_WRITER_BUSY` | 0 |
| Missing source with head | 0 Project reads/launches | 0 reads, 0 launches | 0 |
| Partial, corrupt digest, forked record/head, nonconsecutive sequence, whole-record truncation | each refused before Project read/launch | each 0 reads, 0 launches | 0 |

The controls deliberately catch the expected exception or child-process
failure; their parent test exit is 0. Exact test names and timings are in the
raw output. Existing Dispatcher and legacy tests also exercise result routing,
resource identity, execution budgets and marker compatibility. The feature
regression manifest registers no pack for these changed paths; the verifier
runtime must still produce its exact-candidate receipt before cognition.

Fixture source SHA-256: `dispatcher.mjs`
`2ae756054c91d0f999fa52ad6170fab0eb8c79f47b593dc4b60fd93efb907991`,
`node-state-ledger.mjs`
`f4297fc2a445ad2e5488afbd3717768bd926a467144e8ce617d92f40c9603803`,
`dispatcher.test.mjs`
`e59ce7a07d01aa4eafdd622180f122da691f91ac16a2e248b3d23fb50974481f`.
The focused command exited 0: 182/182 passed, 0 failed; raw output SHA-256
`967daea8ec82cf7fea90edcddb907117d3d4921021e2d09596a61b76741d2930`.
`rtk proxy node scripts/check.mjs all` exited 0: runtime 360/360,
preflight PASS, RAI 18/18, policy 3/3; raw output
`ledger-full-check.tap` SHA-256
`f3aeb3bb7211213c51a03810b4ff6fa984f61f502937713943efa1d39eec9f91`.
