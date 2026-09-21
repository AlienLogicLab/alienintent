# Bootstrap expiry / replacement inventory — read-only

> **No retirement action has been taken.** Nothing was stopped, reverted, reconfigured or expired to
> produce this document. Every service named below is still running and every authority named below is
> still in force. Dispositions are **preliminary classifications for review**, not decisions.

Date: 2026-09-21, after Wave 1 reached terminal state. Compiled by the bootstrap coordinator, which is
an interested party in several of these items — the coordinator's own release authority is entry 1.

**Verified live at compile time:** `alienintent.service`, `alienintent-liveness.service`,
`alienintent-observer.service`, `alienintent-sandbox-tunnel.service` all running; PRODUCER and VERIFIER
both on the `claude` adapter; SF-REQ-053 (#64) and SF-REQ-056 (#67) both **CAPTURE**, P0/Wave 2,
unimplemented.

---

## 1. SWF-21 — Wave 1 coordinator release authority

| | |
|---|---|
| **Authority** | [SWF-21](../decisions/2026-09-20-wave1-release-coordinator.md), amended 2026-09-21 with release-admission preconditions |
| **Purpose** | Coordinator performs READY → IMPLEMENT for eligible Wave 1 BIUs, filling the gap where the Node bootstrap has no automatic release |
| **Demonstrated failure it prevents** | Without it, a released-but-unstarted BIU never begins; with its admission amendment it also refuses releases whose record names no resolvable baseline — the defect that cost a PY-06 invocation and two PY-07 invocations |
| **Stated expiry** | *"until Python AlienIntent provides the canonical automatic-release capability (SF-REQ-001/002 realized through PY-04 and its successors, operating on the live profile)"* |
| **Has that occurred?** | **Partially, and the distinction matters.** `automatic_release` exists in canonical Python (`composition/github_profile.py`, `offline_profile.py`) and PY-10 proved a live run consuming READY work without human IMPLEMENT transitions (AC 14). But it operated on the **sandbox** profile, not the live AlienIntent profile. The expiry condition says *live profile*. |
| **Canonical replacement** | SF-REQ-001 / SF-REQ-002, realised and operating on the live profile |
| **Replacement implemented?** | In canonical Python, yes. On the live profile, **no** — the live profile is still the Node bootstrap |
| **Bootstrap still operating?** | Yes, but **no longer exercised**: Wave 1 is terminal and nothing is eligible |
| **Preliminary disposition** | **NEEDS_DECISION** |
| **Evidence** | The authority's own text; PY-10 proof report §AC 14; the live profile remains `self-hosting.json` driving the Node dispatcher |

**Why not RETIRE_CANDIDATE:** the capability exists but has never run the live backlog. Retiring the
authority before that cutover would leave no release mechanism at all for the live Project.

## 2. SWF-29 — liveness reconciliation (and its judgment-suppression amendment)

| | |
|---|---|
| **Authority** | [SWF-29](../decisions/2026-09-20-liveness-reconciliation.md), Part 1 temporary; amended 2026-09-21 |
| **Purpose** | Detect a nonterminal lifecycle state with no corresponding actor beyond a 5-minute grace, and recover through the narrowest already-authorized idempotent mechanism |
| **Demonstrated failure it prevents** | **Both directions, both observed.** It recovered PY-06 from a dropped webhook delivery that left the BIU inert for 28 minutes; and its amendment **suppressed** recovery during PY-09's provider-capacity interruption, preventing a relaunch into an exhausted quota every grace period for hours |
| **Stated expiry** | *"when the canonical Python liveness capability (SF-REQ-056) replaces it"* |
| **Has that occurred?** | **No.** SF-REQ-056 (#67) is CAPTURE, P0/Wave 2. A source search finds no actor-launch reconciliation in `src/alienintent` |
| **Canonical replacement** | SF-REQ-056 |
| **Replacement implemented?** | **No** |
| **Bootstrap still operating?** | Yes — `alienintent-liveness.service` running |
| **Preliminary disposition** | **KEEP_UNTIL_REPLACED** |
| **Evidence** | `coordinator-liveness.jsonl`; `2026-09-21-py09-provider-capacity-interruption.md` |

**Note for the reviewer:** the suppression amendment is younger than the original rule and has one
demonstrated save. It is the part most worth carrying into SF-REQ-056's design, not merely retiring.

## 3. SWF-27 bootstrap infrastructure — observer and attention queue

| | |
|---|---|
| **Authority** | [SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md) bootstrap-evidence sections |
| **Purpose** | Deterministic monitoring independent of coordinator tenure; durable attention items for observations needing judgment |
| **Demonstrated failure it prevents** | Monitoring formerly ran as child processes of the coordinator session — ending the episode would have stopped monitoring and deleted the monitors. Separately, the attention queue is the only durable record of what needed judgment across the wave |
| **Stated expiry** | Liveness service expires with SWF-29/SF-REQ-056; the observer *"expires when the canonical control plane records its own trajectory (SF-REQ-029)"* |
| **Has that occurred?** | **No.** SF-REQ-029 is P4 and unimplemented |
| **Canonical replacement** | SF-REQ-053 (activation), SF-REQ-029 (trajectory) |
| **Replacement implemented?** | **No** — both CAPTURE |
| **Bootstrap still operating?** | Yes — `alienintent-observer.service` running |
| **Preliminary disposition** | **KEEP_UNTIL_REPLACED** |
| **Evidence** | `coordinator-observations.jsonl`, `coordinator-attention.jsonl` |

**Caveat:** during the post-mortem the observer is the only thing still recording operational
evidence. Stopping it would create the gap the post-mortem is trying to examine.

## 4. Session-bound attention waiter (the wake-up bridge)

| | |
|---|---|
| **Authority** | SWF-27 activation-boundary section, 2026-09-21 |
| **Purpose** | Bridge durable attention items into the Claude harness by exiting a tracked background task, restoring the wake-up that externalizing monitoring had removed |
| **Demonstrated failure it prevents** | Before it, PY-06's DONE waited 45 minutes for a manual prompt, PY-07's `FOUNDER_EXCEPTION` was never seen, and PY-08 sat in TASKS for 1h45m. After it, a `FOUNDER_EXCEPTION` reached the coordinator in ~30 seconds |
| **Stated expiry** | *"expires with the Wave 1 bootstrap, or when canonical coordinator activation (SF-REQ-053) replaces it"* |
| **Has that occurred?** | **Wave 1 bootstrap is terminal — so the first clause has arguably occurred.** SF-REQ-053 has not |
| **Canonical replacement** | SF-REQ-053 |
| **Replacement implemented?** | **No** |
| **Bootstrap still operating?** | Yes — one waiter armed |
| **Preliminary disposition** | **NEEDS_DECISION** |
| **Evidence** | SWF-27 activation-boundary section; `coordinator-attention.jsonl` notification records |

**Why NEEDS_DECISION rather than RETIRE_CANDIDATE:** its expiry names Wave 1's end, which has arrived —
but it is also the mechanism that would surface an incident *during* the post-mortem. Retiring it now
optimises for tidiness over evidence.

## 5. Coordinator checkpoint

| | |
|---|---|
| **Authority** | SWF-27 rules 3, 7 and 9 — a successor must reconstruct context from durable state, never from conversation |
| **Purpose** | Successor handoff without the prior conversation |
| **Demonstrated failure it prevents** | Untested in anger. **No coordinator handover has ever occurred in Wave 1** — this episode ran the entire wave |
| **Stated expiry** | None explicitly. It is bootstrap tooling for a bootstrap tenure model |
| **Has that occurred?** | N/A |
| **Canonical replacement** | SF-REQ-053 bounded episodes with durable continuity |
| **Replacement implemented?** | **No** |
| **Bootstrap still operating?** | Yes — updated 2026-09-21 to reflect Wave 1 completion |
| **Preliminary disposition** | **KEEP_UNTIL_REPLACED** |
| **Evidence** | `~/.local/state/alienintent/coordinator-checkpoint.md` |

**Honest limitation:** its value is entirely unproven. A Wave 1 that never rotated its coordinator
never tested the artifact that exists to survive rotation. That is itself a finding for the post-mortem.

## 6. Windows notification path

| | |
|---|---|
| **Authority** | SWF-27 activation-boundary section |
| **Purpose** | Reach the Founder when a durable attention item needs human judgment |
| **Demonstrated failure it prevents** | Notification delivery is recorded per attempt; a `FOUNDER_EXCEPTION` notification was delivered |
| **Stated expiry** | With the attention queue it serves |
| **Has that occurred?** | Tied to entry 4 |
| **Canonical replacement** | SF-REQ-035 notification adapters (Decision Inbox notifiers) |
| **Replacement implemented?** | Partially — PY-07 landed a notification port with a Work Management projection adapter; the Windows path is separate bootstrap tooling |
| **Bootstrap still operating?** | Yes |
| **Preliminary disposition** | **RETIRE_CANDIDATE** — the lowest-value item here |
| **Evidence** | `notify_founder.py`; delivery records in `coordinator-attention.jsonl` |
| **Known limitation** | **Delivery was never confirmed as *seen*.** Exit 0 proves the command ran, not that a toast appeared. A GitHub comment could not be used because the only credential authenticates as the Founder's own account and GitHub does not notify authors of their own comments |

## 7. Temporary PRODUCER-on-Claude provider change

| | |
|---|---|
| **Authority** | Founder decision 2026-09-21 — *"applies to the current PY-09 recovery; does not permanently redefine the default producer provider"* |
| **Purpose** | Continue PY-09 cycle 4 after the codex quota exhausted mid-repair, rather than wait ~9 hours |
| **Demonstrated failure it prevents** | It unblocked a stalled repair; partial work in worktree `63097907` was preserved and continued rather than rebuilt |
| **Stated expiry** | **The PY-09 recovery**, which is complete |
| **Has that occurred?** | **Yes — unambiguously.** PY-09 is DONE and closed |
| **Canonical replacement** | None required; this is a profile setting. The pre-change block is recorded in the provider-capacity evidence record and a profile backup exists at `~/.config/alienintent/self-hosting.json.bak-20260921T0220Z` |
| **Replacement implemented?** | N/A |
| **Bootstrap still operating?** | **Yes — and it has outlived its authorization.** PY-09B and PY-10 both ran their producers on `claude` under an authorization scoped to PY-09 |
| **Preliminary disposition** | **REVERT_TEMPORARY_CHANGE** *or* ratify — but it should not silently persist |
| **Evidence** | `2026-09-21-py09-provider-capacity-interruption.md`; live profile shows both workers on `claude`/`claude-subscription` |

**This is the clearest expiry in the inventory, and I did not notice it at the time.** Two subsequent
BIUs were produced under a provider authorization that had already expired. Neither produced a defect
traceable to the provider, and both were accepted first-pass — but the authorization boundary was
crossed without a decision. **Consequence for the post-mortem:** PY-09B and PY-10 are the two BIUs
whose first-pass acceptance is being examined, and they also ran on a different provider than most
predecessors. That is a third confound in the causal question, and it exists because a temporary
authorization was not tracked to its expiry.

**Also unresolved:** producer and verifier now share one Claude subscription, so exhausting it stalls
**both** roles. Acceptable for a bounded recovery; a single point of failure if it persists.

## 8. Node / B-DISP bootstrap execution authority

| | |
|---|---|
| **Authority** | Architecture Authority §42 (Node frozen), FD-01, SWF-01 |
| **Purpose** | Execute the BIUs that build canonical Python, without Python owning live execution |
| **Demonstrated failure it prevents** | It is the only thing that has ever executed the live backlog |
| **Stated expiry** | Architecture Authority §43 Python Sovereignty — explicitly **not** claimed by Wave 1; PY-10's contract states *"no Python Sovereignty claim, no Node retirement, no migration of live work"* |
| **Has that occurred?** | **No.** Wave 1 proved Python on a sandbox, not sovereignty |
| **Canonical replacement** | The full S1–S7 conformance matrix under §43 |
| **Replacement implemented?** | **No** |
| **Bootstrap still operating?** | Yes — `alienintent.service` is the live control plane |
| **Preliminary disposition** | **KEEP_UNTIL_REPLACED** |
| **Evidence** | PY-10 contract §Non-goals; `conformance-and-sovereignty.md` |

## 9. SWF-26 — already expired (included as the precedent)

Expired at PY-04 DONE rather than allowed to persist. Listed because it is the repository's only
worked example of a temporary control being retired on schedule, and the standard the entries above
should be held to.

---

## Summary

| # | Mechanism | Expiry occurred? | Replacement ready? | Disposition |
|---|---|---|---|---|
| 1 | SWF-21 release authority | Partially — sandbox yes, live profile no | No | **NEEDS_DECISION** |
| 2 | SWF-29 liveness | No | No | **KEEP_UNTIL_REPLACED** |
| 3 | SWF-27 observer + attention | No | No | **KEEP_UNTIL_REPLACED** |
| 4 | Attention waiter | Arguably — Wave 1 is terminal | No | **NEEDS_DECISION** |
| 5 | Coordinator checkpoint | N/A — never exercised | No | **KEEP_UNTIL_REPLACED** |
| 6 | Windows notification | Tied to #4 | Partially | **RETIRE_CANDIDATE** |
| 7 | PRODUCER on Claude | **Yes — already exceeded** | N/A | **REVERT_TEMPORARY_CHANGE** or ratify |
| 8 | Node execution authority | No | No | **KEEP_UNTIL_REPLACED** |

**One mechanism has already outlived its authorization (7).** Two have expiry conditions that have
arguably arrived but no replacement (1, 4). Four are still doing work their replacements cannot yet do.
One is retirable on low value (6).

**SWF-27 rule 10 is the standard this inventory serves:** *temporary coordinator behaviour must not
silently become architecture through continued use.* Entry 7 shows that happening within a single day,
unnoticed by the coordinator responsible for noticing it.
