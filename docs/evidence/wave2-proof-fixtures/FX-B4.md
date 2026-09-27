# FX-B4 — Successor program mailbox path proof, alternative discharge (WO-220507, SF-REQ-053)

This is the retained proof record for DAG node B4 (`external_proof_prerequisite`). B4 is discharged through its own
**alternative-discharge clause**: "completed programme with no outstanding message duties, proven by authority; no
new product mailbox requirement." This record **cites** retained programme records. It sends no message and binds or
exercises no operational target. Execution packet: `docs/evidence/wave2-execution-packets/WO-220507.packet.json`.
Work unit: `docs/work-units/wave2/WO-220507.md` (sections "Alternative discharge" and "Owner clarifications
disposed", 2026-09-27).

**Completion predicate (B4):** an explicitly authorized harmless request/reply through a successor episode or
supported helper preserves correlation, pending reconciliation, attributed handling and duplicate suppression.
Alternative discharge requires a completed programme with no outstanding message duties, proven by authority, and
no new product mailbox requirement.

## No mailbox is built; R2 is not discharged

This BIU builds no mailbox or messaging capability. Its candidate diff adds only this record, the `FX-B4/`
evidence directory and the read-only checker `tools/evidence/fx_b4_evidence.py`. The DAG lists
`successor_mailbox_consumer` and `successor_mailbox_receipts` in B4's `owns_capabilities`. They are discharged here
by authority citation, not by implementation, and no running code for either exists or is claimed.

This record does **not** discharge R2 ("Replacement gate: Program Director mailbox bridge waiter"). R2 is a
separate DAG node that depends on R1 and B4, and nothing here addresses its predicate. The bootstrap bridge
(BOOTSTRAP-M13) is not retired, replaced or declared retirable. No release, cutover or production mutation is
authorized or performed.

## Inputs and identities

| Item | Value |
|---|---|
| Invocation | `AlienLogicLab/alienintent#127:PRODUCER:f9799689-cd10-47a8-9145-82148b3c1d21` |
| Release baseline | `25f7aa33c4f29de509ee2e6ff9b3e1aa8ab8cbdd` (RELEASED record, Issue #127); packet authority baseline `4076a57010867a98022ee43ca6590814a962e4a9` is its parent |
| Candidate contract | sha256 `b08ca4e995a2511ddfae46f0dba3ff43f6dcc8c63188013ed535665fe2012745` |
| Readiness | native Agent Ready READY, `docs/evidence/wave2-readiness-assessments/WO-220507.2026-09-27T030323.491454Z.assessment.json` |
| Programme closure | `352fa9d7fce76b661ca98bebca0adec7a00a13df`: "Phase 14 Founder approval packet and final report — PROGRAM_COMPLETE" |
| Director closure addendum | added by `89389fd21bd1d3e388730f90cddec6e95a2eacc6`, whose only parent is `352fa9d7`; `FINAL-REPORT.md` is unchanged from that commit to the release baseline |
| Authority records | `docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md` (disposes POSTW1-DECIDE-006A); Founder grant `FULL_WAVE2_BIU_UNBLOCK_AUTHORITY` (2026-09-27T02:01:41Z), cited by reference only (see B4-F4) |
| Proof level | `OPERATIONAL_OR_EXTERNAL_AUTHORITY`, met on the **external-authority** limb: retained, landed programme records. No operational result is claimed. |

## Integrity check (bounded commands)

`tools/evidence/fx_b4_evidence.py` re-checks everything this record relies on, and nothing more. It reads git
objects and writes only `FX-B4/citation-check.json`.

```
rtk proxy python3 -B tools/evidence/fx_b4_evidence.py \
  --baseline 25f7aa33c4f29de509ee2e6ff9b3e1aa8ab8cbdd \
  --invocation "AlienLogicLab/alienintent#127:PRODUCER:f9799689-cd10-47a8-9145-82148b3c1d21" \
  --output docs/evidence/wave2-proof-fixtures/FX-B4
```

Observed: exit 0, 26 of 26 checks PASS, 0 failed. The result is retained as `FX-B4/citation-check.json`, which
records each check's command, expected result, observed result and exit status. The script also runs the packet's
three bounded commands:

- `git merge-base --is-ancestor 352fa9d7… 25f7aa3…`: exit 0. The addendum commit `89389fd` is also an ancestor.
- `git show 352fa9d7…:…/FINAL-REPORT.md`: exit 0, but the addendum is **not** in that tree (B4-F1).
- `jq '."POSTW1-BRIDGE-000",."POSTW1-LEARN-002"' program-state.json`: prints `null` twice, because the tasks live
  under `.tasks` (B4-F2). The checks use `.tasks["…"]` instead.

**Discrimination.** `FX-B4/discrimination.json` records five probes, all behaving as expected:

- Intact release baseline: 0 failed.
- Pre-closure commit `01af974`: 10 failed.
- `352fa9d7` itself as baseline: 9 failed.
- Injected message-duty fault in a throwaway clone: exactly the 3 expected checks failed. The fault set
  `POSTW1-BRIDGE-000` to `IN_PROGRESS`, set `POSTW1-LEARN-002` review to `PENDING` and added a third message file.
- Restored baseline: 0 failed.

Two checks are fixed to the closure commit, not the baseline, so baseline probes cannot fault them: the
closure-time `terminal_state()` recomputation and the post-closure-task checks.

## Predicate mapping (alternative discharge)

### "Successor episode or supported helper" names the retired bootstrap bridge

This follows the owner clarification disposed in WO-220507.md on 2026-09-27. Each cited text was verified at the
release baseline:

| Claim | Evidence (verified at baseline) |
|---|---|
| R2 names the bridge B4 feeds | `wave2-dependency-dag.json` node R2: title "Replacement gate: Program Director mailbox bridge waiter", `depends_on` includes B4. The same title appears at `wave2-technical-plan.md:120`. |
| The bridge is not a product mechanism | `wave2-specified-requirements.md:63`, BOOTSTRAP-M13 "Program Director mailbox bridge waiter replacement: REJECT as permanent product requirement". `:67`, BOOTSTRAP-M17 "REJECT permanent productization of the temporary Director role". |
| The role cannot be recreated | `factory-director-runtime-contract.md:15`: "Do not create a competing role such as Program Director, resident coordinator or bootstrap coordinator". |

### No outstanding message duties

- `program-state.json` at the baseline records `POSTW1-BRIDGE-000` as status `DONE`, review `PASS`, and
  `POSTW1-LEARN-002` as status `DONE`, review `PASS`. The closure commit records the same.
  `task-ledger.md:29` and `:40` agree.
- `messages/` at the baseline contains exactly `POSTW1-BRIDGE-000-request.md` and
  `POSTW1-LEARN-002-review-request.md`, per `git ls-tree`.
- Of all 33 tasks, only `POSTW1-BRIDGE-000` references `messages/` by path. The LEARN-002 message is tied to
  its task by name only: its title is "POSTW1-LEARN-002 — Wave 1 Learning Ledger: request for independent review".

### Completed programme, proven by authority

- The addendum is verified at the baseline, section sha256 `7bcf2a74…`. It states the §15 conditions "as of
  `352fa9d7…`", including:
  - condition 6: landed and remotely verified;
  - condition 7: no temporary worktree or task left without a durable disposition;
  - condition 8: `PROGRAM_COMPLETE`, computed by `ProgramState.terminal_state()`.
- **Reproduced:** the checker ran `ProgramState.terminal_state()` with the closure commit's own `director.py`
  and `program-state.json`. It returned `PROGRAM_COMPLETE` with no blocking decisions. That state has 24 tasks, and
  its 7 open Founder decisions are all `critical_path: false`, which matches the addendum.
- `352fa9d7` and `89389fd` were committed 2026-09-21T22:48:41Z and 22:49:26Z. Both are before the first
  materialized Wave 2 BIU Issue, #69 (WO-220101), created 2026-09-22T11:04:25Z (B4-F3).
- The disposed authority standard (WO-220507.md, owner clarification 2) says this recorded closure computation
  is sufficient "proof by authority".

## Findings for the verifier (recorded, not repaired here)

- **B4-F1: addendum commit.** Packet acceptance criterion 2 says `352fa9d7` "contains the cited FINAL-REPORT.md
  Director closure addendum". It does not. The addendum was added 45 seconds later by `89389fd`, whose only parent
  is `352fa9d7`, and the addendum itself explains why: "a final report cannot contain the identity of the commit
  that lands it". The addendum records its conditions "as of `352fa9d7`". WO-220507.md's own wording ("as of commit
  `352fa9d7…`") is accurate. The cited artifact exists, says what is claimed and resolves at the baseline, so this
  record treats the gap as packet imprecision, not a failed citation.
- **B4-F2: packet jq command.** The packet's bounded `jq` filter addresses top-level keys and prints `null`. The
  data it intends to read verifies under `.tasks`. Correcting the packet belongs to the Factory Director.
- **B4-F3: "predating any Wave 2 BIU".** The closure predates every materialized Wave 2 BIU Issue. It postdates
  the Phase 12 *candidate* BIU set, `01af974`, committed 2026-09-21T22:08:29Z.
- **B4-F4: grant text not retained.** `FULL_WAVE2_BIU_UNBLOCK_AUTHORITY` is cited by name and timestamp in the
  work unit, the DAG notes and the allocation records. No decision record under `docs/decisions/` retains its text.
  The 2026-09-26 delegation record is retained.
- **B4-F5: the state file changed after closure, and recomputing at the baseline gives a different answer.** The
  same state file gained 9 later tasks (`FACT-*`, phases F1–F5), all created 2026-09-22 after the addendum.
  `terminal_state()` at the release baseline returns `FOUNDER_DECISION_REQUIRED`, blocked by
  `FACT-S1-ADMISSION-008`. That task is `critical_path: true`, and the file's last update is
  2026-09-22T18:29:52Z. None of the 9 references a message file or `messages/`, and every message task stays
  DONE/PASS. One of them, `FACT-ARCLOSE-001`, is `BLOCKED` and assigned to `claude-bootstrap-coordinator`. It is an
  Agent Ready publication task parked at a PR merge, not a message with a pending reply. This record's reading: the
  alternative-discharge clause concerns *message* duties of the *completed* programme, and the disposed standard
  anchors on the recorded closure computation, which reproduces. These post-closure tasks are therefore not
  outstanding message duties. Whether that reading holds is for the independent verifier and, if disputed, the
  Founder. BOOTSTRAP-M13's text ("retain or hand off the separate program-message consumer for unfinished program
  duties") is the relevant clause. This BIU does not edit `program-state.json` (packet constraint).
- The DAG's `proof_fixtures` status for FX-B4 stays as planned. Updating the DAG is replanning, which is outside
  this BIU's extent.

## Non-claims

- No claim that R2 (Program Director mailbox bridge waiter) or any node other than B4 is discharged.
- No new or existing mailbox capability is built, claimed or implied. No message was sent.
- No new or reinterpreted Founder decision on the still-open post-Wave-1 decision records. `PROGRAM_COMPLETE` is
  cited as a fact and not reopened.
- No operational result, release, cutover or production mutation. The integrity check proves citation integrity
  only.
