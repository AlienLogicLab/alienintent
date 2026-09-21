# Coordinator self-assessment — participant evidence, not independent review

> **This artifact is explicitly noncanonical.** It was written by the Wave 1 bootstrap coordinator
> about its own performance. The author is a principal actor in every incident below and therefore an
> interested party, not a neutral evaluator. It creates no requirement, no decision and no authority.
> It exists so that an independent analyst has the participant's account **on the record and
> challengeable**, not so that the participant's account stands as the finding.
>
> Where a claim rests on conversation memory rather than a durable artifact, it is marked
> **MEMORY-ONLY** and should be treated as a durability gap, not as evidence.

Date: 2026-09-21. Scope: Wave 1 (PY-01…PY-10 and PY-09B). Candidate structural improvements are marked
**HYPOTHESIS** and are not proposals.

---

## Part 1 — Coordinator-originated defects

### D1. Fabricated baseline SHA

| | |
|---|---|
| **What I did** | Released PY-06 with a release record naming baseline `6a2d1e9` — a commit that did not exist. |
| **Why it looked reasonable** | I was writing a release record in the established format and produced a plausible-looking short SHA without resolving it against the repository. |
| **Wrong assumption** | That a value I had written was a value I had verified. |
| **How discovered** | The producer refused to select a baseline for itself and raised `FOUNDER_EXCEPTION`. |
| **Caught by** | **Producer refusal** — the worker's own authority check, not any coordinator-side gate. |
| **How early** | Immediately, at the first invocation. Cost: one wasted producer invocation. |
| **Deterministic prevention now?** | **Yes.** The release admission gate resolves every named baseline (`git cat-file -e`) and checks ancestry; a non-existent SHA now refuses the transition before a worker launches. |
| **Documented-only?** | No — mechanised. |
| **Could it have escaped?** | No. The producer could not have proceeded without a resolvable baseline. |
| **HYPOTHESIS** | Any coordinator-authored identifier destined for a worker should be machine-resolved at authoring time, not at consumption time. The gate does this at release; nothing does it while the record is being drafted. |

**Evidence:** issue #54 comments `2026-09-20T13:49:09Z` (`RESULT=FOUNDER_EXCEPTION`) and
`13:50:55Z` (coordinator correction naming `93b9b09`).

### D2. Parallel evidence format built without checking the existing schema

| | |
|---|---|
| **What I did** | Built and pushed `docs/evidence/wave1-repair-cycles.{json,md}` as a new per-cycle dataset without first reading `docs/evidence/schema/`, which already defined **execution-trajectory-v1** and **quality-evidence-v1**. |
| **Why it looked reasonable** | The task ("acquire data from each BIU") felt self-contained, and I went straight to building an extractor. |
| **Wrong assumption** | That no prior structure existed, without spending one command to check. |
| **How discovered** | The Founder's next instruction referenced the existing schema; `ls docs/evidence/` then showed schema, trajectory and quality directories already populated. |
| **Caught by** | **Founder instruction** — no automated control. A peer session independently kept and cited the artifact rather than deleting it. |
| **How late** | After commit and push. The incompatible artifact was live on `main`. |
| **Deterministic prevention now?** | **No.** Only a memory note. |
| **Documented-only?** | **Yes** — this is the weakest item in the list. |
| **Could it have escaped?** | **Yes.** Nothing would have flagged a second evidence format; it would simply have diverged. |
| **HYPOTHESIS** | Evidence artifacts could be schema-gated the way candidates are custody-gated: a check that refuses a new file under `docs/evidence/` that neither conforms to a declared schema nor declares a new one. |

**Evidence:** commit `9797a3a` (creation), peer cross-session message, commit `f790d84` (reconciliation).

### D3. Invalid profile mutation — three dispatcher restart failures

| | |
|---|---|
| **What I did** | Added a `_providerChangeProvenance` key to the PRODUCER worker object while re-pointing its provider, to record why the change was made. |
| **Why it looked reasonable** | Recording provenance beside the change seemed better than recording it elsewhere. |
| **Wrong assumption** | That the profile loader tolerated unknown keys. |
| **How discovered** | The dispatcher refused to start: `AlienIntent: invalid config.workers.PRODUCER`, three restart attempts. |
| **Caught by** | **Fail-closed configuration validation** in the product itself. |
| **How early** | Immediately, and while **no invocation was active** — I had verified that before restarting, which is why the blast radius was zero. |
| **Deterministic prevention now?** | **Yes, pre-existing** — the loader validates worker objects against a fixed key set. I added no new control; the product already had one. |
| **Documented-only?** | No. |
| **Could it have escaped?** | No. The dispatcher cannot run with an invalid profile. |
| **HYPOTHESIS** | I should have read the validator before writing the edit. The general form — *read the consumer's contract before authoring input to it* — recurs in D4 and D6 below and may be the single most repeated failure in this list. |

**Evidence:** `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` §"Recovery sequence", step 2.

### D4. Node permission model copied into a Python architecture with different custody responsibilities

| | |
|---|---|
| **What I did** | Provisioned the sandbox GitHub App with `issues: read`, `metadata: read`, `organization_projects: write` — exactly the set `src/github/app-client.mjs` enforces. |
| **Why it looked reasonable** | It was the repository's own enforced least-privilege set, derived from working production code. |
| **Wrong assumption** | That the two architectures have the same responsibility boundary. They do not: **Node's workers publish with their own GitHub identities**; canonical Python publishes and reads back candidates **through the installation credential**. |
| **How discovered** | PY-09B's Agent-Ready assessment read the landed Python code — `doctor.py:165` requires `contents:write` in the read-back publication permissions — and reported that the BIU was unimplementable as provisioned. |
| **Caught by** | **Agent-Ready**, reading source rather than documentation. |
| **How late** | ~19 hours after provisioning, after I had documented the sandbox as verified and reported it complete. |
| **Deterministic prevention now?** | **Partially.** The preflight now enforces the corrected four-permission set with a live negative control. Nothing prevents the *next* specification from being copied from the wrong source. |
| **Documented-only?** | The general lesson, yes. The specific set, no — mechanised. |
| **Could it have escaped?** | **No, but only just.** It would have surfaced as an implementation failure inside PY-09B rather than as a pre-release finding. |
| **HYPOTHESIS** | Capability requirements should be derived from the consuming code path, not from a sibling implementation. A check that reads what the code requires and compares it to what the environment grants would have caught this at provisioning time. |

**Evidence:** `docs/operations/py10-sandbox.md` §"Permission-set correction"; `PY-09B.assessment.2026-09-21-needs-clarification.json`; commit `aaabfa7`.

### D5. A preflight that passed 17/17 against the wrong specification

| | |
|---|---|
| **What I did** | Wrote a sandbox preflight enforcing D4's permission set, ran it, reported **17/17 passing**, and used that as evidence the environment was ready. |
| **Why it looked reasonable** | The checks were genuinely discriminating — exact-set comparison, extra grants and missing grants both fail. I tested that behaviour and it worked. |
| **Wrong assumption** | That a check which cannot be fooled about *conformance* also tells you the *specification* is right. |
| **How discovered** | Same finding as D4. |
| **Caught by** | **Agent-Ready** — not by the preflight, which could not detect its own premise. |
| **How late** | The false confidence persisted about a day and was reported to the Founder as verified. |
| **Deterministic prevention now?** | **No.** The specification is corrected; the class of error is not prevented. |
| **Documented-only?** | **Yes** — recorded as: *a discriminating check proves conformance to its specification; it does not prove the specification is correct.* |
| **Could it have escaped?** | **Yes**, in the sense that the preflight would never have caught it. Something reading the consuming code had to. |
| **HYPOTHESIS** | This is SWF-24's proven-red rule applied one level up: a check that cannot fail is not evidence, **and a check whose specification is unvalidated is not evidence either**. Wave 2 could require that any conformance check name the authority its expected values derive from, so the derivation is reviewable. |

**Evidence:** the three preflight snapshots — `py10-preflight-2026-09-21-pre-contents-grant.json` (passing, wrong spec), `-negative-control.json` (failing, right spec), `-post-contents-grant.json` (passing, right spec).

### D6. An unsatisfiable acceptance criterion in PY-09B

| | |
|---|---|
| **What I did** | Wrote binding rule 6 and AC 10 requiring evidence that the installation *"reaches the sandbox repository and Project only"* — while binding rule 4 fixed `organization_projects: write` as required, and my own sandbox record documented that this grant is organization-scoped and reaches production Project #1. |
| **Why it looked reasonable** | I copied the isolation language from PY-10's binding rules, which were Founder-approved, and strengthened it. |
| **Wrong assumption** | That an acceptance criterion can demand a property the platform cannot provide. I had *documented the contradiction myself* an hour earlier and did not connect the two. |
| **How discovered** | PY-09B's first Agent-Ready assessment: an implementer could not satisfy it and could not weaken a non-delegated rule. |
| **Caught by** | **Agent-Ready**, before release. |
| **How early** | Before any producer ran. Cost: one assessment cycle and a Founder decision (SWF-34). |
| **Deterministic prevention now?** | **No.** SWF-34 fixes this criterion and records the general lesson. |
| **Documented-only?** | **Yes** — *acceptance criteria must describe properties the underlying platform can actually enforce or prove.* |
| **Could it have escaped?** | **Yes.** Without Agent-Ready it would have reached a producer, which would have failed or silently reinterpreted it. |
| **HYPOTHESIS** | Contract authoring is the least-gated activity in the factory. Candidates get custody, verification and review; contracts get one readiness assessment. Wave 2's Design Contract/Verification requirement (SF-REQ-051) may be the structural answer, and this incident is a concrete test case for it. |

**Evidence:** `PY-09B.assessment.2026-09-21-needs-clarification.json`; `docs/decisions/2026-09-21-sandbox-isolation-standard.md`.

### D7. A dedupe fix that broke a neighbouring liveness case

| | |
|---|---|
| **What I did** | Fixed attention-item identity to key on invocation + outcome instead of a timestamp the dispatcher rewrites. This removed the timestamp anchor for **all** record types. |
| **Why it looked reasonable** | The fix was correct for the case in front of me — one verifier failure had produced three wake-ups — and was written test-first. |
| **Wrong assumption** | That every record type carries an invocation. Liveness records do not. |
| **How discovered** | A real `LIVENESS_GAP` arrived minutes later and would have collapsed onto an acknowledged id, silently never waking anyone again. |
| **Caught by** | **A live event**, not by my tests. My test suite passed throughout. |
| **How late** | Within minutes — by luck of timing, not by design. |
| **Deterministic prevention now?** | **Partially.** A regression test now covers successive liveness gaps. Nothing systematically checks that a narrow fix preserves neighbouring cases. |
| **Documented-only?** | No — tested. |
| **Could it have escaped?** | **Yes, and silently.** The failure mode was "no wake-up ever again" — indistinguishable from a quiet period. |
| **HYPOTHESIS** | The most dangerous defects in this wave were the ones whose failure mode resembles normal operation. That is the same class as D5. A control that distinguishes *quiet* from *broken* deserves explicit Wave 2 treatment. |

**Evidence:** `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` §"Three defects found in the coordinator's own tooling".

### D8. Release admission gate could not read its own new identifier convention

| | |
|---|---|
| **What I did** | Introduced `PY-09B` under the repository's suffix convention; the gate's pattern was `PY-\d\d`. |
| **How discovered** | The gate refused PY-09B's release reporting *"Agent-Ready disposition is None"* for a BIU whose assessment said `READY`. |
| **Caught by** | **The gate itself, failing closed** — right refusal, wrong reason. |
| **Deterministic prevention now?** | **Yes**, for this pattern; tested. |
| **Could it have escaped?** | No, but it was *right for the wrong reason*, which is only safe by accident. |
| **HYPOTHESIS** | A gate that reports a wrong reason erodes trust in its right refusals. Wave 2 controls should distinguish "check failed" from "check could not run". |

### D9. Smaller coordinator errors, recorded for completeness

- **Claimed the Node bootstrap was not running** when it was (systemd-managed, PID 77365); my `ps` filter missed it. Caught by the Founder. Corrected publicly. *Lesson: check the supervisor, not the process table.*
- **Estimated "~14 worktrees"** where the real count was **45**. Caught by counting. Recorded in the audit.
- **`pkill -f <pattern>` matched its own shell**, killing my own watchers (exit 144). Replaced with PID-targeted kills after a read-only `pgrep`.
- **A background watcher launched with `&`** detached and became untracked, silently ending harness notifications — the same defect class later formalised in the SWF-27 activation-boundary record.
- **Cleanup pushed `--delete` from a non-repository directory**, leaving a verification branch on the sandbox after I had already destroyed the clones. Caught by checking rather than assuming; removed via the API.
- **Committed a partial documentation edit** when a multi-part script aborted mid-way, then completed it in a follow-up commit.
- **Misread a waiter's lifetime as ~35 minutes** and reported an unexplained "rough edge"; measurement showed 3602 s against a 3600 s timeout — correct behaviour. I corrected the claim rather than leaving a phantom defect on the record. **This one is a reporting error, not a system defect.**
- **MEMORY-ONLY:** several early watcher and battery-script mishaps (a stale hardcoded timestamp re-firing a resolved rejection; a mutation battery failing on a minimal environment) predate durable capture and are not reconstructible from artifacts.

---

## Part 2 — Controls that worked

Labelled as required. **FACT** = the mechanism demonstrably caught or prevented a defect, traceable to
a durable artifact. **INFERENCE** = the control plausibly reduced risk or cost, without a
counterfactual. **HYPOTHESIS** = a causal claim not established by the available evidence.

| # | Control | Class | Evidence |
|---|---|---|---|
| 1 | **Producer refusal on invalid release authority** caught the fabricated baseline (D1) and, separately, refused PY-07 twice when the release record named no baseline and the Issue still said implementation was unauthorized | **FACT** | #54 `13:49:09Z`; #55 `16:56:31Z`, `17:05:55Z` |
| 2 | **Agent-Ready caught decomposition and contract contradictions**: PY-10's unowned live-transport surface (`SPLIT_RECOMMENDED`), PY-09B's unsatisfiable isolation criterion, and the sandbox permission gap — all **before** any producer ran | **FACT** | PY-10 and PY-09B assessment files, including the preserved superseded ones |
| 3 | **Proven-red / mutation checks caught non-discriminating evidence**: the PY-09 verifier established by gutting `_secrets` that 189 tests stayed green; PY-08's `_ReadOnlyFixture` could not make AC 4 go red | **FACT** | #57 and #56 verifier reports |
| 4 | **Fail-closed configuration validation** prevented an invalid dispatcher runtime state (D3) | **FACT** | `invalid config.workers.PRODUCER`, three refused starts |
| 5 | **SWF-29 judgment suppression prevented a provider-burning retry loop**: PY-09 sat in `IMPLEMENT` past grace with no actor for the full blocked interval and **nothing relaunched** | **FACT** | `judgment_suppression` → `ATTENTION_WAIT`; liveness log shows no gap entry for that window |
| 6 | **Candidate custody preserved partial work through provider failure**: worktree `63097907` retained 65 insertions / 60 deletions across three files after the codex quota interruption, and the replacement producer continued from it | **FACT** | provider-capacity interruption record |
| 7 | **Independent verification caught coordinator mistakes** — every item in Part 1 except D3 and D8 was found by a mechanism outside the coordinator | **FACT** | Part 1 "Caught by" column |
| 8 | The admission gate's baseline resolution and ancestry checks would have refused D1 | **INFERENCE** | The gate postdates the incident; no counterfactual run exists |
| 9 | Verification-first sequencing (§4b) reduced repair cost on PY-09 | **INFERENCE** | PY-09's verifier cited §4b at cycle 2; PY-08 took six cycles to surface the same class. Confounded by BIU difference |
| 10 | **PY-09B and PY-10 were accepted first-pass** — `VERIFY → ACCEPT`, zero rejection cycles, against a prior record of **0 first-pass acceptances in 9 accepted BIUs** with rejections ranging 1–9 | **FACT** (the outcome) | Marker sequences on #68 and #58; `wave1-repair-cycles.json` |
| 11 | §4b and improved decomposition **caused** that improvement | **HYPOTHESIS — not established** | Two observations, two confounds: both BIUs also had bounded scope from SWF-33, and both ran on a different provider than most predecessors. A wave with n=2 cannot separate these |

**On #10 and #11 specifically:** the outcome is fact and the explanation is not. Any post-mortem
conclusion of the form "verification-first sequencing produces first-pass acceptance" is unsupported
by this wave's evidence. The honest statement is that the two BIUs following the rule change were the
first two accepted outright, and that at least three plausible causes are entangled.

---

## Part 3 — The question this artifact exists to keep answerable

> Did Wave 1 place too much contract-authoring, provisioning, release and recovery authority in one
> coordinator context, such that independent gates detected mistakes only after they had propagated?

**I am not answering it here**, and I am the wrong party to answer it. The evidence it needs is
preserved above: for each defect, what caught it, how late, and whether a deterministic control now
exists. The pattern visible to me — offered as participant observation, not finding — is that the
defects caught **earliest and most cheaply** were those crossing an authority boundary into a worker
(D1, D3, D6), and those caught **latest** were those that stayed inside coordinator-owned artifacts
where no boundary was crossed (D2, D4, D5).

An independent analyst should test that against the durable record rather than accept it from me.
