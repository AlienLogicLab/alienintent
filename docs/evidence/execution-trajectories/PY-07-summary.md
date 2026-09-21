# PY-07 execution trajectory

PY-07 ran from the READY → IMPLEMENT transition at 2026-09-20T16:54:46Z to DONE at 19:59:03Z — 11,057 seconds. It is the only BIU in PY-05–PY-09 with both authority interruptions and liveness incidents, and the only one where the *release itself* was the defect. Six candidates, six independent verifications, five rejections. Accepted candidate `9caaa71f` landed by normal merge `946e3cc0`.

Raw events: [`PY-07.jsonl`](PY-07.jsonl). Derived measures: [`../quality/PY-07-quality-evidence.json`](../quality/PY-07-quality-evidence.json).

## The release that was not recorded

The coordinator performed READY → IMPLEMENT without the release record that PY-02…PY-06 each carried. No baseline was named, and the Issue body still read *"Implementation is **not** authorized by this Issue."* Two producer invocations refused on exactly those grounds, eight minutes apart, and made no repository change. Between them a liveness watch fired, found no running actor past the grace period, and re-emitted IMPLEMENT — which produced the second identical refusal.

The coordinator's own assessment: *"The producers were right to refuse, and the omission is the coordinator's."* It then supplied the missing record naming baseline `6c3f8432`, created no new authority, and changed no lifecycle state. 806 seconds elapsed from the first refusal to that record.

**Two authority interruptions, zero Founder decisions.** Both were caused by a coordinator-side release defect. Full account: [`../2026-09-21-liveness-retry-and-release-admission.md`](../2026-09-21-liveness-retry-and-release-admission.md).

## Liveness retried a judgment-required outcome

Both liveness gaps (state ages 459 s and 539 s against a 300 s grace) fired on a lane whose actor had **already run and finished**, returning a result only a human could act on. The rule could not distinguish *the actor never launched* — a missing effect, which is what liveness exists to repair — from *the actor completed and returned a judgment-required outcome*. Left alone it would have relaunched a producer every grace period against a condition no number of retries could resolve.

Nothing malfunctioned. The specification did not distinguish the two conditions. Recovery in both cases was operator status re-emission IMPLEMENT → READY → IMPLEMENT, which the coordinator recorded as evidence of the required outcome and explicitly **not** the canonical design (SF-REQ-056 forbids it).

## Cycles

| Cycle | Candidate | Verifier | Verdict | Blocking findings | pytest | Lineage |
|---|---|---|---|---:|---:|---|
| 1 | `f067a8d0` | `dcb6fc65` | REJECT | 4 | 112 | descendant of baseline |
| 2 | `e0d56b72` | `464e01a6` | REJECT | 2 | 118 | **re-implementation on baseline** |
| 3 | `9ea54fdb` | `9e505fde` | REJECT | 3 | 120 | **re-implementation on baseline** |
| 4 | `1bc31011` | `d0c18255` | REJECT | 3 | 123 | **re-implementation on baseline** |
| 5 | `a2826d46` | `149e5477` | REJECT | 1 | 129 | descendant repair of `1bc3101` |
| 6 | `9caaa71f` | `87e3ab30` | **ACCEPT** | 0 | 129 | descendant repair of `a2826d4` |

Blocking findings counted here are the verifier's own numbered items under "Why this is (still) a REJECT". Items the verifier explicitly labelled restated, minor or producer-judgment are excluded; the JSONL description for each cycle records what was excluded and why.

## Re-implementation versus repair

Cycles 2, 3 and 4 were **not descendants of the candidate they were repairing**. The verifier said so each time: *"another re-implementation on the same base."* Across exactly those three cycles the same Scope §2 requirement — escalation at the PY-03 unresolved-effect condition — was reported unsatisfied three times in three different shapes: registered-but-undecidable, unexecutable against the real store, and the canonical FD-05 crash case stopping the whole factory.

Commit `822ca38` is titled *"chore: start PY-07 repair cycle 5 from rejected candidate"*. From that point the candidates are descendants, the reviewable deltas collapse to 4 files +189/−23 and then 3 files +55/−13, and the BIU converges in two cycles.

**FACT:** the switch from re-implementation to descendant repair coincides with the finding count falling to 1 and then 0.
**HYPOTHESIS, not established here:** that re-implementation caused the stagnation. A single BIU cannot separate that from the possibility that the remaining work had simply narrowed. Recorded so a later BIU can test it.

## The recurring failure class

Four of the five rejections are the same class in different code paths: **an escalation that is registered but not decidable — recorded, reported, not recoverable.** It appeared at the admission path (cycle 1), the unresolved-effect path (cycles 2–4), the worker-raised path (cycle 4), and in the `defer` disposition (cycle 4), whose own recommendation was terminal and unrecoverable on every path.

## The one regression

Cycle 5's repair introduced a defect in its own answer to the previous finding: `cancelled-by-decision` was not added to the admission guard's excluded-outcome set, so a cancelled BIU was silently re-dispatched and completed by the next loop tick — and because `resume_after_decision()` *is* `start()`, deciding **any unrelated escalation** revived it. The durable authority record said `choice: cancel` while the store reported `DONE / success`. The candidate's own test asserted only the instant after submission and never ran another tick.

That is one behavioural regression, introduced and closed within PY-07. No proof regression: no previously required test, negative control or fitness check was removed in any cycle.

## Acceptance

The cycle-6 verifier ran five independent probes, including the exact two-tick-plus-unrelated-decision scenario cycle 5 required, closure depth to grandchildren, durability across a fresh store handle, and order symmetry. It then confirmed red–green by reverting only `factory_coordinator.py` to the parent: the candidate's own new regression test fails with the exact cycle-5 defect, `assert 'success' == 'cancelled-by-decision'`.

Four items were carried forward as non-blockers and recorded rather than waived, including one ordering case where a dependent shared by two escalating roots misses the cancel disposition — inert for the correct reason, but an imprecise terminal label.

## Landing

Normal merge `946e3cc0`, parents `2a01a25b` and the accepted SHA. Re-verified in this extraction: reachable from `origin/main`, two parents, accepted SHA second, `git diff 9caaa71f 946e3cc0 -- src tests` empty. Required merge-result Actions — offline verification (run 35533948704) and architecture fitness (run 35533948729) — both succeeded.

`946e3cc0` then became PY-08's release baseline.
