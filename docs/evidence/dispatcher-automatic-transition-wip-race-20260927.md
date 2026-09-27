# Incident — dispatcher automatic-transition WIP race, 2026-09-27

Status: **incident record, repair not yet applied to the runtime**. Discovered while
resolving conflicting Founder priority handoffs (`founder-explicit-127-ready-140-producer-20260927T0344Z`,
`founder-urgent-127-claimed-after-ready-order-20260927T0346Z`). Investigated and corrected
manually by Factory Director episode `factory-director-ffa765583b8c4e50b020466aad3a3369`.

This is a **different** gap from `docs/evidence/wave2-wip-overlap-incident-20260927.md`
(which was about two *Director-initiated* `READY -> IMPLEMENT` releases racing past
`tools/live/release_admission.py`, since fixed at commit `b23f6eb`). That fix does not
cover this incident.

## What happened

The Founder explicitly ordered (`founder-explicit-127-ready-140-producer-20260927T0344Z`,
2026-09-27T03:43:36Z) that Issue #127 (WO-220507) should not continue consuming WIP=1 and
that Issue #140 (WO-220610) should get the next free PRODUCER slot. At that moment #127
had just been recovered from a `FOUNDER_EXCEPTION` (a packet defect, separately repaired
this episode) via the documented operator-status-nudge pattern
(`director-handoff-founder-exception-recovery-20260926T2046Z`), and its fresh PRODUCER
cycle was already resolving on its own.

That PRODUCER cycle genuinely completed (`RESULT=VERIFY`, candidate `e9fb20b`) and handed
to a live, independent VERIFIER, which the Director chose not to interrupt (interrupting a
live, already-in-flight, genuinely-produced verification was judged more destructive than
letting a near-complete step finish). The VERIFIER `ACCEPT`ed at `2026-09-27T03:52:24Z`,
leaving #127 at `ACCEPT` with **zero active claims** — real free WIP capacity.

The Director began nudging Issue #140's Project status to claim that capacity, per the
Founder's explicit order. Before that nudge's webhook could be processed, **the Node
dispatcher's own automatic post-`ACCEPT` closure step independently claimed a fresh
PRODUCER for #127** (`AlienLogicLab/alienintent#127:PRODUCER:2e8b5c3b-...`, started
`2026-09-27T03:55:20.416Z`) — a same-lane, dispatcher-internal transition, not a
Director-initiated release.

## Root cause, verified by direct code reading

`tools/live/release_admission.py`'s global active-claim guard
(`admit()`, `tools/live/release_admission.py:81-91`) is the **only** place in this
codebase that checks total active claims against `wipLimit`. It is invoked exclusively by
the Director's own `READY -> IMPLEMENT` release path.

`src/runtime/dispatcher.mjs` has **no equivalent concept at all** — confirmed by grep
(`wipLimit`/`wip_limit`/`MaxConcurrent` appear nowhere in the file). Its automatic
same-lane transitions — `PRODUCER RESULT=VERIFY -> start VERIFIER`,
`VERIFIER RESULT=REJECT -> start PRODUCER (repair)`,
`VERIFIER RESULT=ACCEPT -> start PRODUCER (post-ACCEPT closure)` — are gated only by
per-lane checks (`ACTIVE_INVOCATION_EXISTS`, `ownedWorkAlive`), never by the total count of
active claims across all lanes. Nothing stops the dispatcher from starting a same-lane
closure invocation for BIU A at the exact moment a Director (or an equivalent operator
nudge) is trying to route freed capacity to BIU B.

This is architecturally distinct from the earlier WIP=1 overlap incident: that one needed
two *different* BIUs to each be independently released to `IMPLEMENT` by the Director in
quick succession. This one needs only *one* BIU's own normal, automatic lifecycle
progression (`ACCEPT -> closure`) racing against an operator's attempt to redirect freed
capacity elsewhere. No Director action was required to trigger it — it would recur any
time a BIU reaches a free-capacity checkpoint (`ACCEPT` with no claim, or any recoverable
diagnostic state) at the same moment another BIU is waiting for that capacity.

## Resolution applied this episode

1. Verified `origin/main` was untouched (still at `240f7b2`, no landing merge) before
   taking any action — the closure invocation had not yet reached its merge step.
2. Stopped the closure invocation's transient systemd unit gracefully
   (`systemctl --user stop alienintent-bd49d57b....service`; exit `143`/`SIGTERM`,
   confirmed via `systemctl --user status`). No `RESULT` was fabricated; `#127`'s `ACCEPT`
   state and its verifier/candidate trail were left untouched.
3. Re-confirmed `origin/main` still untouched after stopping it.
4. Waited for the dispatcher's own periodic reconciliation to clear the stopped claim
   (observed a brief ~10s window where both `#127` and `#140` showed active, mid-clear/
   mid-dispatch, then settled to `#140` alone).
5. #140's fresh PRODUCER (`a7ea1a3c-...`) is now the sole active claim, matching the
   Founder's explicit priority.

Full narrative and readbacks posted to Issue #127
(https://github.com/AlienLogicLab/alienintent/issues/127#issuecomment-5852464445) and
Issue #140 (https://github.com/AlienLogicLab/alienintent/issues/140#issuecomment-5852466127).

## What this does not resolve

`#127` was not returned to `READY` as the Founder's first message requested, because by
the time the Director could act it had already (validly, via the VERIFIER it chose not to
interrupt) reached `ACCEPT` — a more advanced, verified state. Reverting a genuinely
accepted candidate to `READY` would discard real verified work for no remaining safety
benefit once `#140` had priority; this is a forward-only judgment call, not a literal
execution of the first instruction. `#127`'s own SWF-19 landing closure remains available
whenever capacity next frees, after `#140`.

## Recommended repair (not built here)

The dispatcher's automatic-transition path (`src/runtime/dispatcher.mjs`) likely needs the
same kind of `state.json` active-count check `tools/live/release_admission.py` already has
before starting a new same-lane invocation, so that an operator's attempt to redirect
freed capacity cannot be raced by the dispatcher's own next automatic step. This is a
real, generalizable gap, not built speculatively in this episode: it is Node-bootstrap
implementation work, and the Node bootstrap is itself the retirement target of R7
(WO-220607, see `docs/evidence/python-only-cutover-node-inventory-audit-20260927.md`) — a
fix should be scoped and authorized by whoever owns that path, not invented unilaterally
here, and any repair should preserve the existing per-lane behavior this incident's own
resolution depended on (a same-lane closure retry is otherwise correct and desirable).
