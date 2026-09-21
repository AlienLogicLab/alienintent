# PY-08 quality evidence

Derived from [PY-08-quality-evidence.json](PY-08-quality-evidence.json), reconciled against [the trajectory](../execution-trajectories/PY-08.jsonl) by a deterministic consistency check. Not a raw authority source.

## What it was trying to prove

The P0 minimum Operator Control Plane CLI: a presentation adapter over application services letting an operator run, observe, explain, recover, cancel and decide work without direct state mutation. SF-REQ-034 P0 only, plus the operator surface over PY-07's Decision Inbox.

## Verdict

`ACCEPTED_AND_DONE` after one false authority escalation, one liveness incident, six independent rejections and six repair cycles. Landed by normal merge `2c179e5e`; both required merge-result Actions succeeded; Issue closed 134 seconds after DONE under SWF-31.

| Measure | Value |
|---|---:|
| Verifier cycles / rejections | 7 / 6 |
| Findings by cycle | 12 → 14 → 11 → 10 → 8 → 3 → 0 |
| Decisive findings by cycle | — → 1 → 4 → 4 → 4 → 0 → 0 |
| **Proof regressions** | **2** |
| **Behavioural regressions** | **2** |
| **Defects introduced by repair** | **3** |
| Obligations never attempted for five cycles | **2** |
| Authority interruptions (all false/escalated) | 1 |
| Founder decisions required | **0** |
| Liveness incidents / operator interventions | 1 / 1 |
| Coordinator convergence assessments | 4 |
| Release → DONE | 11,443 s |
| Tests at landing | 158 |

## How difficult convergence was

Hardest in the cohort, and difficult in a specific, diagnosable way. Repair mode: **THRASHING_THEN_CONVERGING**.

Findings rose before they fell (12 → 14) because the first candidate's `cancel` crash *masked* the semantics underneath it; the coordinator explicitly rejected reading that as divergence. Then cycles 3–5 plateaued: 11 → 10 → 8, each closing several findings and shipping one or two fresh ones, with no acceptance.

## Regressions — the SWF-23 central case

- **X1 → Y1.** AC 7 regressed from working to unreachable: no `--expected-version` value could succeed. Nothing superseded it. It stayed broken for a second cycle after being named the single top priority.
- **Y3.** Operator diagnostics that worked at two prior candidates were removed. Binding rule 5 asks for *sanitized* diagnostics, not absent ones.

And three defects introduced by repair rather than carried: **X3**, `VersionConflict` undefined so both new staleness guards raised `NameError` — code that had never executed successfully once; **X5**, `status` writing the store, breaking AC 5 under concurrency; **Y2**, `stop` accepting `--expected-version` and silently ignoring it, introduced by the X3 repair.

## The cause, and the intervention

Two contract obligations went **untouched across all five of those cycles**: AC 4's proof that `explain` reproduces the kernel's own decision (`guard_account` had zero tests), and the verification requirements' subprocess, negative-control and backdoor coverage (`grep -rc backdoor tests/control_plane/` → 0).

The verifier named the causal link at the end of four consecutive rejections. The coordinator stated it as a rule in its cycle-5 assessment: *"Those obligations are exactly the machinery that would catch the defects being introduced… Implementation has been repaired five times while the proof harness that protects it was never built. The defect pattern and the skipped obligations are one problem, not two."*

Cycle 6 was directed to be **verification only**. Result: both never-attempted obligations closed, both outstanding regressions closed, five tests added, **zero new defects and zero regressions**, and for the first time in six cycles every remaining finding was carried rather than fresh. Cycle 7 closed those three and was accepted.

## What verification contributed

Almost the entire defect record. Every rejection was driven through the shipped CLI **as a subprocess against a real `OfflineProfile`** with a real SQLite store, and each rejection publishes the exact command/exit-status table. Cycle 1's root finding — that the control plane was written against a duck-typed profile shape no profile in the repository implements, so most of the command set had never executed — is only visible that way; the unit tests were green.

## Founder authority

None required. The single `FOUNDER_EXCEPTION` claimed four missing predecessor services. The coordinator checked each claim against the landed tree and found all four inside approved scope. Classified `FALSE_OR_ESCALATED_AUTHORITY_REQUEST`; 134 seconds of blocked time; contract not amended.

## Carried scope debt at ACCEPT — recorded, not waived

- **Y7** — `status` reports `wip` as `len(items)`, counting terminal and cancelled work. Reproduced: three items `DONE/success`, `cancelled-by-operator`, `cancelled-by-operator` → `"wip": 3`. The verifier: an operator reading that figure is actively misinformed.
- **Y8** — only `status` logs; no mutating command does.
- Non-decisive: the `stop` fence is one-sided — `stop --expected-version 999999` succeeds.

Neither Y7 nor Y8 maps to a numbered acceptance criterion, which is why the ACCEPT stands and why they are named here rather than forgotten.

## Lessons

- **PROMOTED, DOCUMENTED + PROMPTED:** *when a repair loop keeps trading defects, the missing verification is usually the cause rather than a parallel debt.* Made durable as **SWF-23 §4b verification-first repair sequencing** (commit `9f64ebf`), binding on PY-09 and PY-10 and carried in both contracts. Not yet mechanically enforced.
- **PROMOTED, DOCUMENTED:** *wrong sequencing imitates wrong decomposition.* The coordinator had referred a split question to the Founder; one verification-only cycle answered it. The cheap test is to spend one cycle on verification alone before proposing a split.
- **CANDIDATE LEARNING — NOT PROMOTED:** a command surface that has never been driven as a subprocess against a real composition root has not been executed, whatever its unit tests report.
- **CANDIDATE LEARNING — NOT PROMOTED:** an acceptance criterion that passed in an earlier candidate and fails in a later one is a blocking regression that outranks every other finding. Mechanizable as a per-criterion status diff between candidates; currently carried by the verifier's memory and the coordinator's assessments.

## Unknown

Provider and model identity, token usage, monetary cost and per-finding discovery cost are **UNKNOWN**.
