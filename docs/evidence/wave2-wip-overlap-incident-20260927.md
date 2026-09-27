# Incident — WIP=1 overlap, 2026-09-27

Status: **incident record, repair not yet applied to the runtime**. Reported via Director
inbox handoff `director-urgent-wip-reconcile-python-critical-path-20260927T0310Z`. Investigated
by Factory Director episode `factory-director-1e91d4e924fe45668dd38201276218b0`.

## What happened

`~/.config/alienintent/self-hosting.json` sets `wipLimit: 1`. At the time this episode began,
exactly one PRODUCER claim was active: `AlienLogicLab/alienintent#140:PRODUCER` (WO-220610),
started `2026-09-27T02:34:xxZ`.

This episode released two further BIUs to `IMPLEMENT` in sequence, each independently checked
against `tools/live/release_admission.py` and each returning `ADMITTED`:

- Issue #130 (WO-220601) released `READY -> IMPLEMENT` at approximately `2026-09-27T02:56Z`.
- Issue #127 (WO-220507) released `READY -> IMPLEMENT` at approximately `2026-09-27T03:10Z`.

The Node runtime dispatched a PRODUCER for each independently:

- `AlienLogicLab/alienintent#130:PRODUCER:6ec08ebe-...` started `2026-09-27T02:58:25.823Z`
  (pid `2503493`, still running at investigation time, `systemd-run --user --wait` unit
  `alienintent-f926bc77...`).
- `AlienLogicLab/alienintent#127:PRODUCER:f9799689-...` started `2026-09-27T03:07:00.417Z`
  (pid `2509658`, still running at investigation time, unit `alienintent-969af3bb...`).

Both were simultaneously present in `~/.local/state/alienintent/state.json` `active` at
investigation time (`2026-09-27T03:1x`): `activeClaims: 2` against `wipLimit: 1`.
`factory-director-host/inputs.diagnostics.json` confirms this
(`"activeClaims": 2`, `"executable_capacity": false`, `"140": "eligible:IMPLEMENT_UNCLAIMED"`
in `controlRequiredBy`).

Separately, and apparently unrelated to the double-release: Issue #140's own PRODUCER claim is
no longer present in `state.json active` at investigation time, but Issue #140's Project status
is still `IMPLEMENT` and no `RESULT=VERIFY`/`RESULT=FOUNDER_EXCEPTION` comment was ever posted to
Issue #140. Its worker log
(`AlienLogicLab%2Falienintent%23140%3APRODUCER%3A98658283-....log`) is only 2.2 KB, consistent
with an early exit/crash rather than completed work. This left Issue #140 in an
`IMPLEMENT_UNCLAIMED` state — eligible again, but with no durable result — at the exact moment
this episode's #130 release landed, which is almost certainly what let the dispatcher pick up
#130 without any claim conflict.

## Root cause

**There is no enforcement of `wipLimit` anywhere in the actual worker-dispatch path.**
`wipLimit` is read only in `tools/orchestration/factory_director_inputs.py` (the
Factory-Director-Host adapter, which uses it solely to decide whether *Director* cognition is
required — i.e. whether to launch another Director episode). A repository-wide search
(`grep -rl wipLimit src/ tools/`) finds it nowhere under `src/runtime/` (the Node dispatcher that
actually launches PRODUCER/VERIFIER processes) and nowhere in
`tools/live/release_admission.py` (the gate this Director runs before flipping
`READY -> IMPLEMENT`). `release_admission.py`'s own `no_active_invocation` check
(`admit()` in `tools/live/release_admission.py`) only refuses release when *the same issue*
already has an active claim (`f"#{issue}:" in k` — scoped per-issue, not global). Nothing checks
"is the total active-claim count already at or above `wipLimit`" before admitting a second,
independent, graph-unrelated Issue to `IMPLEMENT`.

**This episode's own causal role:** this Director released #127 to `IMPLEMENT` without first
checking `~/.local/state/alienintent/state.json`'s current `active` map for claims on *other*
issues. It incorrectly treated `wipLimit` as a runtime-enforced invariant that would
automatically queue a second release rather than dispatch it immediately (the prior episode's
own handoff language, and this episode's own execution-packet text, both described releases as
"queuing" behind WIP capacity — that description is wrong for how the dispatcher actually
behaves). This is the proximate trigger of the overlap. #140's own claim disappearing from
`active` without a posted result (cause not established by this investigation — worth its own
look, but out of this incident's bounded scope) created the capacity gap #130's release then
filled; #127's release then created the genuine overlap, since #130's claim was still active at
that point.

## What this incident is not

- Not a duplicate-effect or shared-file-conflict finding: #127 (B4) and #130 (R1) are
  graph-independent DAG nodes with disjoint dependencies and disjoint worktrees
  (`.../worktrees/c6cf1bd7-...` and `.../worktrees/cd37c36a-...`). No evidence of the two workers
  touching the same files or Issue.
- Not evidence that either worker's output is invalid. Both remain live, running real `claude -p`
  PRODUCER invocations under normal supervision (`systemd-run --user --wait`, standard
  `RuntimeMaxSec`/`TimeoutStartSec` limits). Per the inbox handoff's own instruction, neither was
  killed, hidden, or otherwise interfered with by this investigation.

## Disposition

- **No further `READY -> IMPLEMENT` or `VERIFY` release from this or any successor episode until
  a tested guard exists and active claims return to at most `wipLimit`.** Recorded as a Director
  inbox handoff constraint (see `director-followthrough-126-isolation-design-20260927T0320Z`
  and the processed receipts for the two 2026-09-27T03:0xZ entries).
- Both live claims (#127, #130) are left to run to completion undisturbed. Their eventual
  `RESULT=` comments and VERIFIER handling proceed through the normal path; this incident does
  not pre-judge their acceptance.
- #140's own unclaimed-`IMPLEMENT`-with-no-result state is flagged for separate investigation
  (why the claim disappeared without a posted result) — not resolved here, out of this
  incident's bounded scope.
- **Repair recommendation** (not applied by this episode; needs its own tested change, per the
  runtime contract's own preference for `MECHANICAL_ENFORCEMENT` over remembered policy): add a
  global active-claim count check to `tools/live/release_admission.py`'s `admit()` — refuse
  admission when `len(state.json active) >= wipLimit` at check time, in addition to the existing
  per-issue `no_active_invocation` check — with its own test coverage alongside the existing
  `tools/live/test_release_admission.py` suite. `wipLimit` itself is already-decided policy
  (`~/.config/alienintent/self-hosting.json`); adding an enforcement check for it is fixing the
  machinery to match already-decided intent, per the runtime contract §6, not a new Founder
  decision — but the change still needs its own careful authoring and test pass, not a hurried
  edit appended to an already-long incident response.
