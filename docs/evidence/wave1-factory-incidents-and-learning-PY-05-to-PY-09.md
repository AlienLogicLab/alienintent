# Wave 1 factory incidents and learning graduation — PY-05 to PY-09

> **Terminal reconciliation notice — Superseded by:** [Wave 1 Closure Manifest](wave1-closure-manifest.md) and [evidence reconciliation](wave1-evidence-reconciliation.md) for terminal counts, timestamps and comparisons. This document is retained as historical observation/interpretation at its original capture boundary; it is not the current Wave 1 aggregate. No historical hypothesis becomes a terminal causal conclusion.


A BIU can succeed while teaching the factory something about itself. This record separates **product implementation defects**, which belong in the per-BIU Quality Evidence, from **factory and bootstrap defects discovered while processing a BIU**, which belong here — and then tracks what happened to each lesson afterwards.

Sources: Issue comments #53–#57, the dispatcher state record, the coordinator liveness / attention / observation logs, Git, and the decision records named below. Capture boundary 2026-09-21T02:45Z; PY-09 is in flight.

Companion records: [per-BIU trajectories](execution-trajectories/), [per-BIU Quality Evidence](quality/), [cross-BIU comparison](quality/PY-05-through-PY-09.md).

---

## Part 1 — Factory incidents

### FI-1 — A release record named a baseline that never existed

| | |
|---|---|
| Observed during | **PY-06**, before any implementation |
| Symptom | The producer refused to start. `git cat-file -e 6a2d1e9^{commit}` fails; no ref advertises it. |
| Root cause | Coordinator transcription error into a durable contract field. The SHA was never produced by anything. |
| Immediate repair | Coordinator corrected the record 106 s later, naming `93b9b096` whose parent is the PY-05 landing merge. |
| Classification | **Not a missing-authority gap.** Contracted work continued; no Founder decision. |
| Generalized lesson | Candidate-identity discipline applies to the baseline, not only to the candidate. |
| Canonical owner | SF-REQ-002 READY scheduling |
| Enforcement | **GATED** — folded into the release-admission preconditions (see FI-2), which check that the baseline resolves and is reachable from the release point |
| Later BIUs affected | PY-08 and PY-09 released with the preconditions running; neither had a baseline defect |

### FI-2 — A release was performed without a release record

| | |
|---|---|
| Observed during | **PY-07**, at the READY → IMPLEMENT transition |
| Symptom | Two producer invocations raised `FOUNDER_EXCEPTION` eight minutes apart on identical grounds and made no repository change. 806 s of human-blocked time. |
| Root cause | The transition was performed without the release record PY-02…PY-06 each carried: no named baseline, and the Issue body still read *"Implementation is not authorized by this Issue."* |
| Immediate repair | Coordinator supplied the record naming baseline `6c3f8432` and stated the omission was its own. Both refusals judged correct. |
| Generalized lesson | A release is not a status transition. A worker must not launch until the release record is complete, and a failed check is a refusal, not a warning. |
| Canonical owner | SF-REQ-002 amendment; bootstrap checklist in SWF-21 |
| Enforcement | **GATED** — `release_admission.py`, `test_release_admission.py` (14 tests). Replayed against PY-07 as it stood at 16:54: the gate refuses on `implementation_authorized` and `authority_wording_consistent`, **the two grounds the producers themselves cited**. |
| Later BIUs affected | PY-08's release comment records all six admission checks passing before any worker launched; PY-09's likewise. Zero release-record authority blocks after PY-07. |

### FI-3 — Liveness retried a completed effect awaiting judgment

| | |
|---|---|
| Observed during | **PY-07** (two gaps), and the mechanism fired again benignly in **PY-08** |
| Symptom | Two `LIVENESS_GAP` records at state ages 459 s and 539 s. Recovery re-emitted IMPLEMENT against a lane whose actor had already run, finished, and returned a judgment-required result. The second producer refused identically. |
| Root cause | The rule could not distinguish *the actor never launched* — a missing effect, which liveness exists to repair — from *the actor completed and returned an outcome only a human can act on*. Nothing malfunctioned; the specification did not distinguish the conditions. |
| Immediate repair | Operator status re-emission IMPLEMENT → READY → IMPLEMENT, recorded explicitly as evidence of the required outcome and **not** the canonical design (SF-REQ-056 forbids it). |
| Generalized lesson | Liveness reconciliation repairs missing effects; it must not retry completed effects whose result requires judgment. |
| Canonical owner | SF-REQ-056; bootstrap rule in SWF-29 |
| Enforcement | **GATED** — `judgment_suppression` in the bootstrap watch, `test_liveness_suppression.py` (8 tests), including that an older judgment outcome does not block after newer progress and that suppression names the *same* attention item the observer created. |
| Later BIUs affected | PY-08's single liveness gap was a genuine missing effect, correctly recovered. PY-09 has had none. |

### FI-4 — Worktree cleanup treated build artifacts as uncommitted work

| | |
|---|---|
| Observed during | **PY-06** (audit conducted while it was live) |
| Symptom | Unbounded worktree retention and accumulating `WORKTREE_CLEANUP_FAILED` diagnostics. 45 worktrees before the audit. |
| Root cause | `worktreeManager.cleanup()` passes `--ignored` to `git status`, so any worktree that has run the Python suite is reported dirty by its own `.pytest_cache/` and `__pycache__/`. The check could not distinguish "a worker left work worth keeping" from "pytest wrote a cache directory". |
| Immediate repair | Audit and classified cleanup: 25 removed, 21 retained on an explicit reachability test. |
| Generalized lesson | A local candidate worktree is operational cache, not evidence, once the candidate identity is known, durably published, independently retrievable and read back — and "durably published" is a statement about *continuing* reachability, not about a `git push` having succeeded. |
| Canonical owner | SF-REQ-007, as amended |
| Enforcement | **DOCUMENTED + CHECKED** — SWF-30 states the seven-condition rule; the audit applies it. The `--ignored` flag itself is assigned implementation debt, not yet fixed. |
| Later BIUs affected | PY-07, PY-08 and PY-09 worktrees still carry "dirty worktree retained" diagnostics in the state record. The cause persists. |
| Note | The diagnostic being *recorded rather than rewriting the lifecycle result* is PY-06's binding rule 7 working correctly. The flooding is a separate defect from the erasure PY-06 fixed. |

### FI-5 — Issue closure blocked dependency admission

| | |
|---|---|
| Observed during | **PY-06 and PY-07**, surfacing in **PY-08**'s admission check |
| Symptom | PY-06 and PY-07 were `DONE` in the Project while their Issues stayed open — 20,997 s and 6,482 s respectively. GitHub's native blocked-by links read Issue state, so PY-08's admission check saw an unsatisfied dependency for BIUs complete for hours. |
| Root cause | Nothing in the dispatcher closes Issues, and the bootstrap made dependency admission depend on a secondary projection. |
| Immediate repair | Coordinator closed both Issues after verifying all four closure conditions. The admission gate was **not** weakened. |
| Generalized lesson | Issue closure is a bookkeeping projection, not canonical lifecycle authority. Dependency satisfaction is a question about lifecycle state, which the control plane owns, not about a Work Management projection it writes to. |
| Canonical owner | SWF-31, recorded against the SF-REQ-002 admission amendment |
| Enforcement | **DOCUMENTED + PROMPTED** — SWF-31 authorizes the coordinator to close as routine closure once four conditions hold. Nothing performs it automatically. |
| Later BIUs affected | PY-08's Issue closed 134 s after DONE. The coupling itself remains in the bootstrap; the canonical Python design is directed not to inherit it. |

### FI-6 — A 1,653-second dispatch gap with no recorded actor

| | |
|---|---|
| Observed during | **PY-06**, between repair cycles 2 and 3 |
| Symptom | Candidate `d9537d1` published 14:19:20Z, producer worktree exited 14:19:27Z, next VERIFIER invocation started 14:47:00Z. |
| Root cause | **UNKNOWN.** The liveness watch records no gap for issue 54. The coordinator observation log does not begin until 15:32Z. |
| Immediate repair | None; the gap closed by itself. |
| Generalized lesson | Telemetry that starts mid-wave cannot explain what happened before it started. This gap is the clearest example of an interval the factory cannot account for. |
| Canonical owner | SF-REQ-024 factory yield |
| Enforcement | **DOCUMENTED** — recorded here so it is not read as zero. |

### FI-7 — A false authority escalation

| | |
|---|---|
| Observed during | **PY-08**, after the first rejection |
| Symptom | Producer raised `FOUNDER_EXCEPTION` claiming four missing predecessor services, published no candidate, discarded its draft. 134 s blocked. |
| Root cause | A misreading of "adapter-only" as a contract constraint. Binding rule 1 positively requires the application services the producer said were missing. |
| Immediate repair | Coordinator checked each of the four claims **against the landed tree**, not against contract prose, and found all four in scope. Contract not amended; no acceptance criterion changed; baseline unchanged. |
| Generalized lesson | An authority request is adjudicated against the tree, not the prose. The second such request in Wave 1 after PY-04's. |
| Canonical owner | SF-REQ-006 / SF-REQ-029's `FALSE_OR_ESCALATED_AUTHORITY_REQUEST` classification |
| Enforcement | **DOCUMENTED** — the classification exists in SF-REQ-029; nothing mechanizes the adjudication. |
| Note | Both false escalations so far were resolved by a coordinator reading the code. That is model cognition, and it is cheap here only because the coordinator was present. |

### FI-8 — Telemetry coverage starts mid-wave

| | |
|---|---|
| Observed during | **PY-05 and PY-06** |
| Symptom | The coordinator observation log begins 2026-09-20T15:32Z and the attention queue 17:08:53Z. PY-05 completed at 13:43Z and PY-06 at 15:59Z. |
| Consequence | PY-05 has **no** observation or attention coverage; PY-06's authority interruption and all four rejection cycles have no attention coverage. Its only attention entry is a backfilled `DONE_TO_DONE`. |
| Generalized lesson | Absent telemetry must be recorded as UNKNOWN. A zero here would falsely make PY-05 and PY-06 look like the calmest BIUs in the cohort on a dimension that was simply not being measured. |
| Canonical owner | SF-REQ-024, SF-REQ-030 |
| Enforcement | **CHECKED** — the consistency verification for this cohort fails if an UNKNOWN metric is expressed as a number. Negative control: substituting `0` for `token_usage` goes red. |

### FI-9 — A provider quota killed an invocation mid-cycle

| | |
|---|---|
| Observed during | **PY-09**, repair cycle 4 |
| Symptom | PRODUCER `e84d12a0` started 02:06:56Z and died 02:12:46Z, about 350 s in, with no result marker. The dispatcher recorded `DURABLE_RESULT_MISSING`. |
| Root cause | The producer's provider account hit its usage limit; the provider returned `turn.failed`. The worker was operating normally — suite at 33 passed / 2 failed, mid-edit on `tests/installation/test_doctor.py`. |
| Why it surfaces this way | SWF-09 anticipates it: for CLI providers token and monetary budget are **measured, not hard-enforced**, so exhaustion appears as a dead invocation rather than a clean budget refusal. |
| Immediate handling | Liveness recovery **suppressed** under SWF-29; the worktree retained as required evidence under SWF-30 condition 6; the choice of provider escalated as an operator decision under SWF-09. |
| Resolution | Founder authorized the `claude` adapter for this recovery only. Contract, scope, acceptance criteria, baseline and cycle number unchanged. 532 s blocked. |
| Generalized lesson | A measured-not-enforced budget dimension fails as an unexplained death, and the recovery must not be a retry. Three rules written for other conditions handled it correctly without amendment. |
| Canonical owner | SWF-09 budget policy; SF-REQ-029's `PROVIDER_CAPACITY_INTERRUPTION` classification |
| Enforcement | **GATED for the recovery behaviour** (SWF-29 suppression, SWF-30 retention); **DOCUMENTED for the exhaustion itself** — nothing predicts or pre-empts it, and the token count that would have made it predictable is not collected |
| Later BIUs affected | PY-10 runs on a dedicated sandbox and will have the same exposure |

**This is the single best evidence in the cohort that the learning loop works.** Three durable rules — one from PY-06, one from PY-07, one from the Wave 1 plan approval — did correct work on a condition none of them was written for, with no coordinator improvisation and no lifecycle change. It is also the cohort's first genuine human decision.

---

## Part 2 — Learning graduation

Enforcement maturity uses the analytical scale from the extraction brief: `DOCUMENTED` → `PROMPTED` → `CHECKED` → `PROVEN_RED` → `GATED` → `STRUCTURALLY_ENFORCED`. **These labels are analytical. They are not product states and do not appear in any canonical AlienIntent vocabulary.**

| Lesson | Origin | Durable artifact | Consumed by | Mechanizable | Maturity |
|---|---|---|---|---|---|
| A release must carry a complete release record before a worker launches | PY-07 FI-2 | SF-REQ-002 amendment, SWF-21 checklist, `release_admission.py` | PY-08, PY-09 releases | yes | **GATED** (replayed proven-red against the originating incident) |
| Liveness repairs missing effects, never retries judgment-required completed effects | PY-07 FI-3 | SWF-29, `judgment_suppression`, 8 tests | PY-08's one gap | yes | **GATED** |
| Candidate-identity discipline applies to the baseline | PY-06 FI-1 | folded into release admission | PY-08, PY-09 | yes | **GATED** (via the above) |
| When a repair loop keeps trading defects, the missing verification is usually the cause | PY-08 | **SWF-23 §4b**, commit `9f64ebf`; carried in PY-09 and PY-10 contracts | PY-09 contract + Agent-Ready + release comment | partly | **PROMPTED** |
| Wrong sequencing imitates wrong decomposition; spend one verification-only cycle before proposing a split | PY-08 | SWF-23 §4b prose | — | no | **DOCUMENTED** |
| A local worktree is cache once the candidate is durably published and read back | PY-06 FI-4 | SWF-30 seven-condition rule | the retention audit | yes | **CHECKED** |
| Issue closure is a projection, not lifecycle authority | FI-5 | SWF-31 | PY-08 closure | yes | **PROMPTED** |
| Liveness suppression applies to any judgment-required dead invocation, not only `FOUNDER_EXCEPTION` | PY-07 FI-3, exercised by PY-09 FI-9 | SWF-29 | PY-09 cycle 4 | yes | **GATED** |
| A local worktree holding real uncommitted content is required evidence | PY-06 FI-4 | SWF-30 condition 6 | PY-09 cycle 4 | yes | **CHECKED** |
| Prove your own tests before publishing: neuter the code a test covers and confirm the suite goes red | PY-09 cycle 3 coordinator direction | Issue comment only | — | **yes** | **PROMPTED** |
| **A check that cannot fail is not evidence** | PY-02, re-observed PY-05 ×2, PY-06, PY-08 ×5 cycles, PY-09 ×2 | SWF-24 / SF-REQ-050 — a capability to be built, Wave 3 | nothing mechanical | **yes** | **DOCUMENTED** |
| **A production symbol unreachable from any composition root is not implemented** | PY-06 ×3 cycles, PY-08, PY-09 | none | nothing | **yes** | *(not recorded before this document)* |
| A command surface never driven as a subprocess against a real composition root has not been executed | PY-08 | verifier practice only | PY-09 verifier | yes | *(not recorded before this document)* |
| Restart a repair from the rejected candidate, not from the baseline | PY-07 | commit message `822ca38` only | — | partly | *(not recorded before this document)* |
| A previously satisfied acceptance criterion that now fails outranks every other finding | PY-08 X1/Y1 | SWF-23 §1–§2 | coordinator assessments | **yes** | **PROMPTED** |

---

## Part 3 — Gap Trap: what VERIFY still cannot check

> **VERIFY proves what AlienIntent already knows how to check. REVIEW discovers what AlienIntent does not yet know how to check. Suitable REVIEW discoveries should graduate through deterministic failure-class promotion into future VERIFY capability.** — SWF-24 / SF-REQ-050

For each recurring class: *is AlienIntent still spending model cognition rediscovering this?*

### GT-1 — "A check that cannot fail is not evidence" — **INCOMPLETE GRADUATION, highest value**

Rediscovered by a model at least **eleven separate times** across five BIUs: PY-02 (recorded, not promoted), PY-05 findings 1 and 7, PY-06's weak malformed-locator control, PY-08 AC 4 and the verification requirements across five consecutive cycles, PY-09's gutted-`_require` control at cycles 2 and 3.

It is mechanically expressible and three verifiers have already written the mechanism by hand:

- PY-05 — thirteen targeted mutations, twelve caught, re-derived independently at the next cycle;
- PY-06 — revert the repaired source files, require the new tests to fail;
- PY-09 — delete the validator body, require the suite to go red; then per-check mutation.

PY-09's form is the cheapest and most general: *make the validator unconditionally pass; the suite must go red.* It is currently the habit of one verifier, re-invented per BIU, and carried by nothing.

**Flag: incomplete learning graduation candidate.** SF-REQ-050 owns it and is Wave 3, P1. Nothing in Wave 1 catches it.

### GT-2 — "A correct object with no executed path" — **INCOMPLETE GRADUATION**

Rediscovered in PY-06 (three consecutive cycles, `RetrySchedule`, the verifier half of `ReservationBook`, `verify()`'s unused workspace, the composition wiring that raised `TypeError` on first real use), PY-08 (the duck-typed profile shape no profile implements), and PY-09 (an aggregator over callables nothing constructs).

Mechanically expressible as: a production symbol added by a candidate must be reachable from at least one composition root, and at least one test must traverse that path. Architecture fitness already walks the module graph, so the substrate exists.

**Flag: incomplete learning graduation candidate.** Not recorded in any canonical artifact before this document.

### GT-3 — Proof regression across candidates — **PARTIALLY GRADUATED**

SWF-23 §7 already names this as a future verification obligation and enumerates exactly what to compare: a removed acceptance test, a removed negative control, a weakened architecture check, lost mutation coverage, lost custody proof, behaviour no longer reproducing, a CI check no longer running.

Today it is carried by the verifier diffing test inventories by hand (PY-06, PY-07) and by the coordinator's convergence assessments (PY-08). PY-08's AC 7 regression survived **two full cycles** despite being named the single top priority — which is what a human-memory mechanism looks like when it fails.

**Flag: incomplete learning graduation candidate.** The comparison is mechanical and the requirement already exists.

### GT-4 — Whole-BIU claim reconciliation — **NOT GRADUATED, low value**

The producer reported `npm test` as 310 in every PY-05 and PY-06 comment; the verifier observed 330 every time. Four cycles, never reconciled, correctly treated as non-blocking. Trivially mechanizable, near-zero value — recorded so the count is not later mistaken for a defect.

### GT-5 — Adjudicating an authority request against the tree — **NOT MECHANIZABLE, correctly left to cognition**

Both false escalations in Wave 1 were resolved by a coordinator reading the code and checking each claim against the landed tree. That is judgment, and SWF-24's non-goals say so: not every REVIEW judgment becomes deterministic. Recorded to mark it as deliberately out of scope rather than overlooked.

---

## Part 4 — The one-sentence reading

Across PY-05 to PY-09 the factory's **control-plane** lessons graduated quickly and completely — gates with proven-red evidence, consumed by later BIUs, and in PY-09's capacity incident three of them handled a condition none was written for — while its **engineering-quality** lessons did not graduate at all, and the single most expensive class in the cohort is one that was already written down as a candidate learning after PY-02 and left there.

The asymmetry has a plausible cause worth testing rather than asserting: control-plane lessons are about **the factory's own deterministic mechanisms**, which the factory owns and can change in an afternoon; engineering-quality lessons are about **what a producing model does inside a candidate**, and the only channels available for those today are prose in a contract and a rejection comment. SF-REQ-050 exists precisely to give the second kind a mechanical channel, and it is Wave 3.
