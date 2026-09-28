# SF029-SWF27-LEDGER delivery repair fixture

Authority: Issue #143's released IMPLEMENT packet and the independent REJECT
comment on candidate `d57306e15d7ab69b898352b37e1edaccecd3be7c`. The
release baseline is `e6a10e3d83e7ec97b28df8494a0f7653ff403f8d`.
This repair builds on the original candidate in a runtime-owned branch. The
original `ledger-v1-fixture.md` and its raw logs remain intact; this record
adds proof for the blocking delivery-reservation finding.

## Finding and disposition

The rejected candidate treated every persisted delivery as complete. A
`PROCESSING` reservation appended before an interruption therefore suppressed
its own redelivery after restart. The verifier's durable Issue comment records
the initial reproduction: one reservation, no enrichment, no launch, followed
by `{accepted:true, duplicate:true}`. The first local focused run of the two
new tests exited 1 with 0/2 passing for precisely that duplicate response and
for deletion of a committed `PROCESSED` acknowledgement.

The repair distinguishes a delivery being handled by this process from a
persisted `PROCESSING` delivery left by a previous attempt. A durable
`PROCESSED` delivery remains a duplicate. The in-memory reservation retains
same-process duplicate exclusion while processing is pending. On failure,
cleanup removes only a still-`PROCESSING` reservation; it never erases a
committed `PROCESSED` record. The existing lane, result and status guards remain
responsible for effect idempotence on resumed processing.

## Disposable local cases

The tests use temporary state directories and synthetic Project and launch
counters. They do not touch installed service or state paths.

| Case | Expected and observed source/effect counts | Result |
| --- | --- | --- |
| Project delivery interrupted after reservation append | Genesis plus reservation: 2 records; 0 enrichment, 0 launches before interruption. Restart accepts the same delivery, then 1 enrichment and 1 launch; subsequent redelivery is duplicate. | PASS |
| Result comment interrupted after reservation append | Exactly 1 additional committed reservation; 0 status effects before interruption. Restart accepts it, routes VERIFY exactly once; subsequent redelivery is duplicate. | PASS |
| Project delivery interrupted after committed completion append | Last record is `PROCESSED`; restart retains it, redelivery is duplicate, total launches remain 1. | PASS |

The existing focused tests also retain concurrent duplicate exclusion, failed
dispatch/enrichment retry, ledger replay/projection repair, corrupt-source
refusal, and worker/result/status idempotence. No prior acceptance criterion or
valid evidence is superseded.

## Commands and retained evidence

Run from the candidate worktree:

| Command | Exit | Observed |
| --- | ---: | --- |
| `rtk proxy node --test test/dispatcher.test.mjs test/legacy-state.test.mjs > docs/evidence/sf-req-029/ledger-repair-focused-tests.tap 2>&1` | 0 | 185 passed, 0 failed |
| `rtk proxy node scripts/check.mjs all > docs/evidence/sf-req-029/ledger-repair-full-check.tap 2>&1` | 0 | runtime 363/363, preflight PASS, RAI 18/18, policy 3/3 |

The two raw logs named above are committed with this fixture. SHA-256:

| File | SHA-256 |
| --- | --- |
| `src/runtime/dispatcher.mjs` | `6a65edefda697e7fa6c63b24192d9131e8e426931b78fecd23c51e508800588d` |
| `src/runtime/node-state-ledger.mjs` | `f4297fc2a445ad2e5488afbd3717768bd926a467144e8ce617d92f40c9603803` |
| `test/dispatcher.test.mjs` | `c03e651a32f8dc7bfa11305ed90f30257a4b856f8b63ba0ffc9f312f1254606c` |
| `ledger-repair-focused-tests.tap` | `dbe6f9dcc98775744296367cd4d30230e11fd280298839aeadde3326fbfe9b73` |
| `ledger-repair-full-check.tap` | `597ce6fd645bfe922860abdf30621b05560ae08c6b8260462d15318d0c4951aa` |
