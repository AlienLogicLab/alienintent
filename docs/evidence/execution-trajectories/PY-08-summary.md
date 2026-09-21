# PY-08 execution trajectory

PY-08 ran from release at 2026-09-20T21:50:02Z to DONE at 2026-09-21T01:00:45Z — 11,443 seconds. Seven candidates, seven independent verifications, six rejections, one false authority escalation, one liveness incident, four coordinator convergence assessments, **two SWF-23 regressions** and **three defects introduced by repair**. Accepted candidate `b76d639e` landed by normal merge `2c179e5e`, and the Issue was closed 134 seconds later as routine closure under SWF-31.

PY-08 is the BIU that produced SWF-23 §4b. This record reconstructs that evidence rather than restating the conclusion.

Raw events: [`PY-08.jsonl`](PY-08.jsonl). Derived measures: [`../quality/PY-08-quality-evidence.json`](../quality/PY-08-quality-evidence.json).

## Release

The first release to run the new admission preconditions: implementation authorized, exact baseline named, baseline resolves, baseline reachable from the release point, no unsuperseded "not authorized" wording, no worker launched before the checks. All passed. The contract carried an assigned diagnostic-coalescing implementation debt and a readiness gate whose substantive checks PY-09 would supply.

## The false authority escalation

After the first rejection the producer raised `FOUNDER_EXCEPTION`, claiming PY-08 could not produce a compliant candidate from the released predecessor interfaces without broader authority, and naming four missing services. It published no candidate, discarded its draft and left the worktree clean.

The coordinator checked each of the four claims **against the landed tree** rather than adjudicating from contract prose, and classified it as not a missing-authority gap: all four blockers were inside approved scope. The one thing genuinely unclear — whether "adapter-only" was a constraint — was clarified as a misreading: binding rule 1 positively *requires* the missing application services. The contract was not amended and no acceptance criterion changed. 134 seconds of blocked time.

Classified `FALSE_OR_ESCALATED_AUTHORITY_REQUEST`. It is the only one in PY-05–PY-09, and the second in Wave 1 after PY-04's.

A liveness gap fired ten minutes later (state age 575 s) and the recovery re-emission launched the actor that produced cycle 2's candidate.

## Cycles

| Cycle | Candidate | Verdict | Findings | Decisive | pytest | vs parent | Regression |
|---|---|---|---:|---:|---:|---|---|
| 1 | `80aa7c0f` | REJECT | 12 (F1–F12) | — | 132 | +217/−0 | — |
| 2 | `9e48a6ea` | REJECT | 14 (V1–V14) | 1 | 133 | +197/−1 | — |
| 3 | `9dfdb23b` | REJECT | 11 (W1–W11) | 4 | 134 | +40/−8 | — |
| 4 | `5f6c9cfd` | REJECT | 10 (X1–X10) | 4 | 144 | +265/−35 | **X1 (SWF-23)** |
| 5 | `f0706794` | REJECT | 8 (Y1–Y8) | 4 | 149 | +127/−30 | **Y1, Y3 (SWF-23)** |
| 6 | `8f85513b` | REJECT | 3 (Y2, Y4, Z1) | 0 | 154 | +168/−7 | none |
| 7 | `b76d639e` | **ACCEPT** | 0 | 0 | 158 | +98/−2 | none |

Two separate size series exist and must not be conflated. The table gives each candidate's diff **against its own parent**, computed from Git. The coordinator's convergence assessments quote 197 → 314 → 545, which is **cumulative added lines over the release baseline**.

## What the trajectory actually shows

**Findings rose before they fell.** 12 → 14. The coordinator addressed this directly after the third rejection and rejected the divergence reading: the first candidate's `cancel` crash — a one-line dispatch defect that hid behind a unit test using a different call shape — *masked* the semantics underneath it. Fixing the crash exposed them. That is convergence through a layered defect, not thrashing. The four decisive findings in cycle 3 against one in cycle 2 do not contradict this.

**Then it plateaued while trading defects.** 11 → 10 → 8 across cycles 3, 4 and 5, with no acceptance. Each of those cycles closed several findings and shipped one or two new ones:

- **X1** — AC 7 regressed from working to unreachable. No `--expected-version` value could succeed. Nothing superseded it. It stayed broken for a second cycle as **Y1** after being named the single top priority.
- **X3** — `VersionConflict` undefined in `factory_coordinator.py`; both new staleness guards raised `NameError`. That code had never executed successfully once.
- **X5** — `status` began writing the store, breaking AC 5 under concurrency. A read command mutating.
- **Y2** — introduced by the X3 repair: `stop` accepted `--expected-version` and silently ignored it.
- **Y3** — the second SWF-23 regression: operator diagnostics that worked at two prior candidates were removed. Binding rule 5 asks for *sanitized* diagnostics, not absent ones.

**Two obligations were never attempted across all five of those cycles.** AC 4's proof that `explain` reproduces the kernel's own decision — `FactoryCoordinator.guard_account` had zero tests through cycle 5 — and the verification requirements' subprocess, negative-control and backdoor coverage (`grep -rc backdoor tests/control_plane/` → 0; `readiness` → 0).

The verifier named the causal link at the end of **four** consecutive rejections, each time in a "repair order" that put the missing proof last in priority but underneath everything else: *"until `cancel`, `stop`, `run` and `decisions` are driven as subprocesses with the three required negative tests, defects of exactly this class will keep reaching VERIFY."*

## The intervention

The coordinator's cycle-5 assessment states it plainly:

> **Those obligations are exactly the machinery that would catch the defects being introduced.** AC 4 proves `explain` against the kernel's own decision — the discipline that would have caught Y1. The negative-control and backdoor tests are what stop a repair from silently removing behaviour, as Y3 did. Implementation has been repaired five times while the proof harness that protects it was never built. The defect pattern and the skipped obligations are one problem, not two.

Cycle 6 was directed to be **verification only**: build AC 4's proof, build the verification requirements, repair the AC 7 regression, restore the removed diagnostics, change nothing else.

## What changed after it

The cycle-6 verifier's own framing: *"FAIL — but for the first time in six cycles, not because of anything this candidate did."*

| | Cycles 1–5 | Cycle 6 |
|---|---|---|
| New defects introduced | 3 | **0** |
| SWF-23 regressions | 2 | **0** |
| Findings | 12 → 14 → 11 → 10 → 8 | **3** |
| Findings that were fresh rather than carried | at least one every cycle | **0** |
| AC 4 | unproven, 5 cycles | **closed** against a real kernel over a real store |
| Verification requirements | unmet, 4 consecutive cycles | **closed**, four subprocess tests with real exit statuses |

Cycle 7 closed the three carried findings and was accepted. The verifier noted that cycle 7 *"is the first repair cycle that will have"* the proof harness.

The coordinator also resolved a planning question it had referred to the Founder: this looked like a BIU that needed splitting, and it was not. **The sequencing was wrong, not the size.**

## Acceptance and carried debt

The ACCEPT closed Y2, Y4 and Z1 by the verifier's own reproduction rather than the producer's claim, with nothing previously passing traded away. Two findings were **recorded not waived** because neither maps to a numbered acceptance criterion:

- **Y7** — `status` reports `wip` as `len(items)` and so counts terminal and cancelled work. Reproduced: a profile whose three items are `DONE/success`, `cancelled-by-operator` and `cancelled-by-operator` reports `"wip": 3`. The verifier's words: an operator reading that figure is actively misinformed.
- **Y8** — only `status` logs; no mutating command does.

A third, non-decisive: the `stop` fence is one-sided. It rejects a view *below* the newest nonterminal aggregate, as AC 2 asks, but accepts a view *above* every aggregate, so `stop --expected-version 999999` succeeds.

## Landing

Normal merge `2c179e5e`, parents `9f64ebf3` and the accepted SHA. Re-verified in this extraction: reachable from `origin/main`, two parents, accepted SHA second, `git diff b76d639e 2c179e5e -- src tests` empty. Required merge-result Actions — offline verification (run 35549355425) and architecture fitness (run 35549355438) — both succeeded; 158 tests pass on the merge result.

`2c179e5e` became PY-09's release baseline.
