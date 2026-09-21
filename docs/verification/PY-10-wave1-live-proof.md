# PY-10 — Wave 1 live proof on the dedicated sandbox

**BIU:** PY-10 ([contract](../work-units/python/PY-10.md), [Issue #58](https://github.com/AlienLogicLab/alienintent/issues/58))
**Run:** 2026-09-21, 11:47:34Z → 11:52:04Z UTC, one coherent run
**Target:** the SWF-08 sandbox — repository `AlienLogicLab/alienintent-sandbox`, Project `PVT_kwDOEcrpC84BkIEX` (number 2), profile `py10-sandbox`
**Machine-readable summary:** [`PY-10-wave1-live-proof.json`](PY-10-wave1-live-proof.json) · [execution trajectory](../evidence/execution-trajectories/PY-10-sandbox-run.jsonl) · [quality evidence](../evidence/quality/PY-10-sandbox-run-quality-evidence.json)
**Retained evidence:** [`docs/evidence/py10/`](../evidence/py10/)

**Result: 17 of 17 acceptance criteria verified from the retained evidence.**

> Given a prioritized backlog, sufficient execution authority, and no unresolved blockers,
> AlienIntent continuously consumes eligible READY BIUs until the executable backlog is exhausted.

Six BIUs were seeded READY into a real GitHub Project. Canonical Python AlienIntent consumed all
six to DONE with WIP = 1, FIFO among equals, a respected dependency, two genuine human-decision
escalations, and one deliberate process kill mid-work — publishing six candidate revisions to a real
private repository and reading every one of them back from a fresh clone before admitting VERIFY.
No human moved any BIU into IMPLEMENT. The live AlienIntent Project and the Node bootstrap were
untouched.

This proves **one Wave 1 product statement on real infrastructure**. It is not a Python Sovereignty
claim, not a cutover, and not a second deployment; §43 of the Architecture Authority is not invoked
here and the full S1–S7 matrix remains outstanding.

---

## 1. What ran

| | |
|---|---|
| Control plane | `alienintent` CLI, profile factory `alienintent.composition.sandbox_run_profile:profile` |
| Work Management | live GitHub Projects v2, read and projected through `GitHubProjectsWorkManagement` |
| Contracts | one BIU contract document per item, fetched live from the sandbox repository with the installation credential |
| Worker | `worker/run.sh` in the sandbox repository, which invokes the **`claude` provider CLI** headless and commits what it produced |
| Custody | `GitSourceControl` publishes to a per-invocation branch; the control plane re-clones the exact revision in a fresh process before VERIFY |
| Ingress | resident webhook ingress on the sandbox's own tunnel and hostname, signature-verifying every delivery |

### The seeded backlog

Deliberately minimal but sufficient to exercise the factory (binding rule 4). Each BIU's task is to
write one note file; the point is the loop, not the work.

| BIU | Priority | READY at | Depends on | Required capabilities | Role in the proof |
|---|---|---|---|---|---|
| SB-01 | P0 | 11:46:48Z | — | `python` | highest priority; the process kill lands here |
| SB-06 | P0 | 11:46:55Z | — | `python`, **`network-egress`** | requires a capability the profile does not hold |
| SB-02 | P1 | 11:47:01Z | — | `python` | equal-priority pair, made READY first |
| SB-03 | P1 | 11:47:09Z | — | `python` | equal-priority pair, made READY second |
| SB-04 | P2 | 11:47:15Z | **SB-05** | `python` | outranks its own blocker |
| SB-05 | P3 | 11:47:21Z | — | `python` | lowest priority, and SB-04's blocker |

Seeding wrote exactly one Status value, `READY` — recorded in
[`seed.json`](../evidence/py10/seed.json) and checked by the verifier.

### The run, as it happened

| UTC | Event |
|---|---|
| 11:47:34 | Isolation observed; `doctor` **PASS**, exit 0, all eight required checks |
| 11:48:04 | SB-01 (P0) takes the single repository slot |
| 11:48:12 | **`SIGKILL` to the run process group** while it holds `launch:SB-01:0` and that effect is unresolved |
| 11:48:2x | Restart. Recovery cannot read the lost worker back, so it **parks** the unknown effect and escalates |
| 11:48:31 → 11:49:22 | SB-02, then SB-03 — the equal-priority pair, in READY order |
| 11:49:24 → 11:49:48 | SB-05 (P3) |
| 11:49:50 → 11:50:14 | SB-04 (P2) — only now, because its blocker is DONE |
| — | SB-06 refused at release admission; escalated. Run ends `dependencies-or-authority-blocked` |
| 11:50:3x | Operator authorizes SB-01 → resumes automatically → DONE 11:50:50 |
| 11:51:0x | Operator authorizes SB-06 → resumes automatically → DONE 11:51:25 |
| 11:51:5x | `run` returns `eligible-backlog-exhausted`; all six DONE; upstream READY snapshot empty |

Thirteen operator commands in total, every one recorded with its exit status and elapsed time in
[`proof-run.json`](../evidence/py10/proof-run.json). None of them names IMPLEMENT.

---

## 2. Acceptance criteria

Each line below is decided by [`py10_verify_evidence.py`](../../tools/live/py10_verify_evidence.py)
from the retained files, not from this report. Re-run it:

```
python3 tools/live/py10_verify_evidence.py --evidence docs/evidence/py10 --live
```

| # | Criterion | Verified from |
|---|---|---|
| 1 | At least 3 READY BIUs consumed | 6 of 6 reached DONE in the durable store |
| 2 | Different priorities present and respected | P0/P1/P2/P3 seeded; first dispatch was a P0; over work no dependency or authority block deferred, the priority sequence `P1, P1, P3` never decreases |
| 3 | Two equal-priority BIUs prove FIFO | SB-02 and SB-03 are both P1, READY at 11:47:01Z and 11:47:09Z, dispatched in that order |
| 4 | A dependency is respected | SB-04 (P2) **outranks** SB-05 (P3) and still started 2.1s *after* SB-05 reached DONE |
| 5 | WIP = 1 enforced throughout | max 1 concurrent reservation across 34 sampled moments, **and** an independent acquisition of the held slot was refused |
| 6 | Slot refill automatic on release | one operator `run` consumed 4 BIUs in sequence; the slot fence reached 7 |
| 7 | `HumanDecisionRequired` with complete context | 2 escalations, each carrying every decision-ready field, each projected into the live Project |
| 8 | Only the affected BIU blocks | SB-01 and SB-06 blocked; SB-02, SB-03, SB-04, SB-05 completed regardless |
| 9 | A durable decision unblocks and resumes | 2 attributable decisions; each resumed its work item to DONE with no further operator action |
| 10 | A process restart occurs during the run | `SIGKILL` to the process group while holding `launch:SB-01:0` |
| 11 | No duplicate execution or external effect | exactly one candidate branch per BIU; every candidate exactly one commit ahead of `main` |
| 12 | Exact custody proven before every VERIFY | all 6 candidates are source revisions, marked independently read back, and still advertised at the remote |
| 13 | All executable work reaches DONE | all six, in the store **and** in the live Project |
| 14 | No human moves a BIU into IMPLEMENT | seeding wrote only `READY`; no operator command names IMPLEMENT across 13 commands |
| 15 | `doctor` passes before autonomous start | exit 0, disposition PASS, 8 required checks, recorded before the first `run` |
| 16 | Live Project and Node bootstrap unaffected | see §4 |
| 17 | No secret or private installation detail retained | the profile's own values were searched for in every retained file; none found |

### Where WIP = 1 and refill are structural rather than contested

The sandbox is a single repository, so the reservation scope admits one mutating invocation by
construction; the run never had two items competing for different repositories. What was observed is
therefore stated precisely: the slot was **held by exactly one owner at every sampled moment**, an
independent attempt to take it while held was **refused**, and the slot was **released and retaken
five times inside a single operator command**. That is exclusion and automatic refill observed; it is
not a claim about behaviour under contention across repositories, which Solve-for-N (SF-REQ-003)
still owes.

---

## 3. Candidate custody

Six revisions, each published by the control plane to its own branch and each re-cloned in a fresh
process before VERIFY was admitted:

| BIU | Branch | Revision | Changed |
|---|---|---|---|
| SB-01 | `candidate/launch-SB-01-3` | `cc6eac4d43…` | `docs/SB-01.md` |
| SB-02 | `candidate/launch-SB-02-0` | `7987efb9f0…` | `docs/SB-02.md` |
| SB-03 | `candidate/launch-SB-03-0` | `c365ac5a31…` | `docs/SB-03.md` |
| SB-04 | `candidate/launch-SB-04-0` | `a11e17760d…` | `docs/SB-04.md` |
| SB-05 | `candidate/launch-SB-05-0` | `8f3bb37742…` | `docs/SB-05.md` |
| SB-06 | `candidate/launch-SB-06-2` | `6f7a61c791…` | `docs/SB-06.md` |

The worker never publishes. It is launched with a **stated** environment rather than the control
plane's, so the credential rewrite that lets the control plane push and re-clone is not in the
worker's environment at all — and `worker/run.sh` exits non-zero if it ever finds one there. Only
the control plane publishes, and only the control plane proves retrieval.

The recorded locator carries no credential: `git:https://github.com/AlienLogicLab/alienintent-sandbox.git#<branch>@<revision>`.

---

## 4. Isolation — and what it does and does not prove

Two different controls, per [SWF-34](../decisions/2026-09-21-sandbox-isolation-standard.md):

**Repository isolation is permission enforced.** The installation reaches exactly
`['AlienLogicLab/alienintent-sandbox']`, `repository_selection: selected`. Observed live in the run.

**Project isolation is configuration enforced, not token enforced.** `organization_projects` is an
organization permission; the sandbox token *can* read other org Projects. Nothing here claims
otherwise. What operates is deterministic, exclusive, fail-closed addressing: the configuration names
one Project and no other, and a foreign identity offered to `ProjectAddress.resolve` met the typed
refusal *"observed project is not the configured project"* during the run.

**AC 16 is the compensating end-to-end control, and it held.** The production AlienIntent Project was
read read-only immediately before and immediately after the run and reduced to a digest over every
item identity and its `updatedAt`:

- 67 items before, 67 items after
- state digest `sha256:…` **identical** before and after
- Project `updatedAt` unchanged at `2026-09-21T10:45:23Z` — an hour before this run began

The Node bootstrap was neither started, stopped nor reconfigured. Its own ingress answered identically
before and after (`8788 → 401`), and `/etc/cloudflared/config.yml` was not modified. The sandbox ran
on its own tunnel, its own hostname and port 8789.

Five signed `projects_v2_item` deliveries — produced by this run's own projections — reached the
resident ingress and were admitted, recorded in
[`ingress-admissions.json`](../evidence/py10/ingress-admissions.json). Every one named the sandbox
Project.

---

## 5. The restart, in detail

This is the part worth reading closely, because the honest answer is more interesting than "it
recovered".

The run process group was killed with `SIGKILL` while it held the repository reservation
`launch:SB-01:0` and while that effect was still unresolved. Killing the **group** means the provider
CLI the control plane had launched died with it; publication happens after the worker process
returns, so no candidate had been pushed.

On restart the coordinator found the held reservation, asked the worker provider to read the
invocation back, and got nothing — `RealWorkerProvider` keeps outcomes in memory, and that memory
died with the process. It did **not** re-dispatch. It parked the unknown effect under FD-05, released
the slot, raised a decision request with complete context, and carried on with independent work.
SB-02, SB-03, SB-05 and SB-04 all reached DONE while SB-01 stayed blocked.

Only an attributable operator decision (`authorize`, idempotency key `py10-decision-0`) lifted the
guard, and SB-01 was then re-admitted through the normal release path under a new correlation,
`launch:SB-01:3`. The sandbox repository shows exactly one candidate branch for SB-01, one commit
ahead of `main`.

So AC 11 is satisfied in the strong sense: the kill did not produce a duplicate external effect, and
the system refused to *risk* producing one without a human saying so.

**The limitation this exposes** is real and should be carried forward: because `read_back` is
in-memory, *every* restart with work in flight costs a human decision, even when the effect is
knowable. A durable worker-outcome record would let recovery reconcile without escalating. That is a
Wave 2 concern, not a defect in this proof.

---

## 6. Verification harness

Built before the implementation widened, as [SWF-23 §4b](../decisions/2026-09-20-convergent-repair-monotonic-progress.md)
requires.

| Harness | Result |
|---|---|
| Offline suite (`python3 -m pytest -q`) | **344 passed** |
| Offline drain rehearsal — the whole acceptance shape against real Git, real worktrees, real custody, recorded GitHub | passes as part of the suite |
| Proven-red matrix (`tools/live/py10_proven_red.py`) | **22 of 22** guards pass intact and fail when broken |
| Live rehearsal on disposable seeds | full run completed before the coherent run; two defects found and fixed |
| Acceptance verifier (`tools/live/py10_verify_evidence.py`) | **17 of 17** |

The rehearsal earned its place. It found that the redaction boundary was corrupting the repository
name (the tunnel's name is a substring of it), which would have destroyed the isolation proof the
redaction exists to protect, and that discarding run state also discarded the seeding record. Both
were fixed before the coherent run.

The proven-red matrix earned its place twice. It found one guard that **could not** go red —
removing `updatedAt` from the Projects v2 query changed nothing offline, because a recorded answer
answers what it was written to answer regardless of the selection set. That is a real blind spot in
fixture-driven testing, and it is now closed by asserting the selection set directly. It also found
that breaking the per-invocation capability grant does not make the drain *fail* — it makes it never
finish, because the coordinator has no terminal handling for a non-success worker outcome and
re-dispatches the same item forever. See §7.

---

## 7. Findings carried forward

Stated here rather than left for a verifier to rediscover.

1. **A non-terminal worker outcome re-dispatches indefinitely.** `_completed_for_outcome` returns the
   state unchanged for `ineligible` and `rework`, and `_eligible` does not exclude those outcomes, so
   a misconfigured dispatch loops with real provider spend and no run-level wall clock. This run is
   bounded externally — every operator command runs under a wall-clock bound that kills the process
   group — but the bound belongs to the harness, not to the product. **The control plane should own a
   run-level budget.**
2. **In-memory worker read-back makes every in-flight restart cost a human decision** (§5).
3. **Lifecycle projection is applied once, at completion.** The Project shows `READY → DONE`; the
   intermediate IMPLEMENT/VERIFY/REVIEW/ACCEPT stages live only in the operational store. Nothing in
   the acceptance list requires otherwise, and adding projections was out of scope under SWF-20, but a
   human watching the Project sees less than the kernel knows.
4. **Dependency edges are contract-declared, not native GitHub blocked-by.** The Wave 1 plan fixes the
   representation as native blocked-by links. That is not reachable here: the sandbox App holds
   `issues: read`, so it can neither create the issues nor the dependency links, and the permission set
   is Founder-approved least privilege. Instead the edge is carried in the Project item's own
   descriptor **and** in the BIU contract, and the ACL refuses the row if the two disagree — a guard
   that is proven red. The fact under test (AC 4: a dependency is respected) is unaffected; the
   representation differs from the plan's and is recorded here rather than silently substituted.
5. **The provider CLI is real, but it is not doing hard work.** `claude -p` genuinely produced each
   note in a real worktree. Token and monetary cost are `UNKNOWN`, not zero, per SWF-09 — the CLI
   worker adapter records `BudgetRecord.unknown()`.

---

## 8. Scope discipline

Files owned by PY-09B and PY-06 were changed. Each was necessary and each is recorded:

| File | Change | Why PY-10 could not avoid it |
|---|---|---|
| `execution_coordination/ports/project_directory.py` | `ProjectItemState` gains `title`, `body`, `status_updated_at` | the FIFO key (AC 3) and the upstream descriptor (AC 4, 13) are not otherwise observable |
| `adapters/github_projects_v2.py` | query the item title/body and the Status value's own `updatedAt`; `add_draft_item` carries a body | same, plus AC 7 needs the escalation projected in full |
| `adapters/github_work_management.py` | `contract` may resolve per row | release admission compares each row's readiness digest against *its own* contract digest; one shared contract refuses every live row |
| `adapters/github_repository_api.py` | `contents()` | the per-item contract document lives in the repository |
| `invocation_runtime/adapters/git_worktree.py` | ref-safe branch names | `launch:<work>:<version>` is not a valid refname; no worktree could be allocated at all |
| `invocation_runtime/application/real_worker.py` | per-invocation branch, read-back workspace and capability grant | each was fixed at construction, so a profile draining a backlog could serve exactly one item |
| `invocation_runtime/adapters/cli_worker.py` | optional stated environment | one argument vector serves every invocation; a worker cannot otherwise know which BIU it is |

PY-09B's accepted evidence remains valid: its live checks and proven-red matrix are untouched, and
nothing above weakens a guarantee it established. No production Project, Node component, FactoryChecks
path or deployment target was touched.

---

## 9. Reproducing this

The environment is recorded in [`operations/py10-sandbox.md`](../operations/py10-sandbox.md). A second
run is a different run — what is reproducible is the environment, the commands and the checks:

```
python3 -m pytest -q                                                    # 344 passed
python3 tools/live/py10_proven_red.py --json                            # 22/22 guards proven red
python3 tools/live/py10_verify_evidence.py --evidence docs/evidence/py10 --live   # 17/17
python3 tools/live/py10_project_state.py                                # read the Project back
```

To take a fresh run against the sandbox:

```
python3 tools/live/py10_seed_backlog.py --apply --reset
python3 tools/live/py10_proof_run.py --apply --fresh --production-project <production Project identity>
```

The sandbox is left standing; closure does not dismantle it.
