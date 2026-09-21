# Wave 1 bootstrap retirement / transition audit

Authoritative artifact: [wave1-bootstrap-retirement-matrix.json](wave1-bootstrap-retirement-matrix.json). POSTW1-BOOTSTRAP-006; 2026-09-22; baseline `45c0697921d9b538101a33def6e337cd12bfd218`.

**Audit and recommendations only.** No retirement, service/profile change, authority mutation, commit, push, network access or phase progression. Coordinator review is pending. Retire by replacement, not by date.

## Findings and evidence limits

- SWF-21 Wave 1 purpose is complete, but its live-profile expiry is not proven; formal scope closure must never be treated as Wave 2 authority.
- Participant attribution of PY-06 recovery to SWF-29 conflicts with the decision: recovery preceded the rule. PY-09 suppression is the demonstrated protection.
- Participant low-value Windows retirement recommendation is unsupported: delivery is not human receipt and absence of proof does not authorize removal.
- Tunnel temporary label does not override PY-10 explicit nondismantling closure contract.
- External modules have partial prose authority and reported tests; absence of repository-controlled code and suite provenance is the precise custody gap, not proof that every module is ungoverned or untested.
- Checkpoint continuity and multi-BIU tenure benefit are unproven. Program-state reconstruction proof is not a coordinator-handover proof.
- PRODUCER exception outlived PY-09 authority; use by later producers does not ratify it. Reversion is a recommendation only.

Coordinator inventory and supplied live snapshot are testimony/recorded observations. Decisions establish authority; local evidence corroborates claims. No fresh systemctl, provider, attention or external-module execution was performed. Snapshot has a matching derived_at_head but no observation timestamp; do not claim current operational readiness.

Existing routing/program-state edits and untracked audit preparation were inspected as known authorized inputs and preserved. Source and pre-existing-change hashes are in JSON provenance. Only these two deliverables are written. They remain PARKED for review in the existing `/mnt/d/Projects/alienintent` worktree on `main`; the direct packet prohibits committing or publishing them.

## Dispositions

| Mechanism | Disposition | Still operating/available | Demonstrated prevention |
| --- | --- | --- | --- |
| M01: SWF-21 release authority | NEEDS_DECISION | Yes | Not demonstrated |
| M02: SWF-29 liveness reconciliation | KEEP_UNTIL_REPLACED | Yes | Source-recorded; see qualification below |
| M03: SWF-27 observer | KEEP_UNTIL_REPLACED | Yes | Not demonstrated |
| M04: attention queue | KEEP_UNTIL_REPLACED | Yes | Source-recorded; see qualification below |
| M05: Windows notification | NEEDS_DECISION | Yes | Not demonstrated |
| M06: session-bound attention waiter | NEEDS_DECISION | Yes | Source-recorded; see qualification below |
| M07: coordinator checkpoint | KEEP_UNTIL_REPLACED | Yes | Not demonstrated |
| M08: PRODUCER-on-Claude temporary profile change | REVERT_TEMPORARY_CHANGE | Yes | Source-recorded; see qualification below |
| M09: Node/bootstrap execution authority | KEEP_UNTIL_REPLACED | Yes | Not demonstrated |
| M10: sandbox ingress tunnel | NEEDS_DECISION | Yes | Not demonstrated |
| M11: eighteen external bootstrap modules | NEEDS_DECISION | Yes | Not demonstrated |
| M12: resident coordinator multi-BIU tenure | NEEDS_DECISION | Yes | Not demonstrated |
| M13: Program Director mailbox bridge waiter | KEEP_UNTIL_REPLACED | Yes | Source-recorded; see qualification below |
| M14: SWF-26 PY-04 mutation gate | RETIRE_CANDIDATE | No; already expired | Source-recorded; see qualification below |
| M15: bootstrap release-admission gate | KEEP_UNTIL_REPLACED | Yes | Source-recorded; see qualification below |
| M16: b-disp command compatibility alias | KEEP_UNTIL_REPLACED | Yes | Not demonstrated |
| M17: Local Program Director bootstrap orchestration role | KEEP_UNTIL_REPLACED | Yes | Not demonstrated |

Counts: mechanisms_audited=17, RETIRE_CANDIDATE=1, KEEP_UNTIL_REPLACED=9, REVERT_TEMPORARY_CHANGE=1, NEEDS_DECISION=6, still_operating=16, transition_plan_steps=17.

“Still operating” includes dormant retained authority and available tooling. It does not mean all 18 external modules or tests are executing. “Never fired” means no demonstrated prevented failure, not absence of use. Unfired controls may simply be untested. Every replacement flag is false because full operational substitution has not been shown; this does not deny partial Python implementation.

## Mechanism assessments

### M01 — SWF-21 release authority

**Purpose:** Fill the Node automatic-release gap for eligible Wave 1 BIUs, subject to readiness and admission.

**Demonstrated failure prevented:** No separately demonstrated prevented failure for the authority grant itself. Releases occurred, but the grant also allowed the defective PY-07 release. The admission gate has a separate demonstrated refusal (M15).

**Authority:** SWF-21: eligible Wave 1 BIUs only; six admission preconditions amend the nine eligibility conditions.

**Stated expiry:** Canonical SF-REQ-001/002 automatic release operating on the live profile replaces manual transitions; scope is explicitly Wave 1.

**Replacement gate:** Operational live-profile automatic release with durable authorization, exact baseline, readiness, dependencies, capacity and refusal checks; explicit authority for any subsequent wave. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** Wave 1 purpose is complete; sandbox automatic release does not satisfy the stated live-profile expiry. Recommend formally ending the Wave 1 grant, without carrying it into Wave 2. No decision here extinguishes authority. Preserve the separate admission protection and decide the next release owner before any new live work.

**Evidence:** `docs/decisions/2026-09-20-wave1-release-coordinator.md` — Authority granted; Release admission preconditions; Expiry; `docs/evidence/wave1-closure-manifest.json` — bius: Wave 1 DONE/CLOSED; `docs/verification/PY-10-wave1-live-proof.md` — AC 14 and sandbox-only limitation; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_services.detail.alienintent.service; `src/alienintent/composition/github_profile.py` — automatic_release composition.

### M02 — SWF-29 liveness reconciliation

**Purpose:** Repair missing actors/effects after the grace period while yielding to completed outcomes requiring judgment.

**Demonstrated failure prevented:** PY-09 capacity incident records ATTENTION_WAIT (DURABLE_RESULT_MISSING) and no repeated relaunch; suppression prevented retrying an exhausted provider. PY-06 was the motivating gap, already recovered before SWF-29 took effect, not a save by this watch.

**Authority:** SWF-29 Part 1 and judgment-suppression amendment; Node single-dispatcher lane guard supplies duplicate exclusion.

**Stated expiry:** When operational SF-REQ-056 replaces the bootstrap capability.

**Replacement gate:** SF-REQ-056 or an authorized equivalent operating on the live workload: missing-effect detection, completed-outcome suppression, explicit resolution/supersession, durable fenced recovery, delayed-delivery duplicate safety and correlated outcome readback. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Service active in supplied snapshot. Specification/CAPTURE is not operational replacement. Preserve the queue dependency and exactly one Node dispatcher until replacement is proven.

**Evidence:** `docs/decisions/2026-09-20-liveness-reconciliation.md` — Motivating incident; Part 1; Duplicate prevention; Amendment; `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — The suppression rule earned its keep; SEEN != RESOLVED; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_services.detail.alienintent-liveness.service.

### M03 — SWF-27 observer

**Purpose:** Persist lifecycle observations independently of the resident model session.

**Demonstrated failure prevented:** No demonstrated prevented operational failure. SWF-27 records timely PY-06 DONE and PY-07 blocking-event observations but attention still failed. Externalization removes session-process coupling; no complete coordinator replacement exercise proves continuity.

**Authority:** SWF-27 bootstrap monitoring interpretation; docs/operations.md observer boundary.

**Stated expiry:** Canonical control plane records its own trajectory under SF-REQ-029.

**Replacement gate:** Operational live-profile trajectory capture preserving identity, ordering, timestamps, anomalies, retention and consumption by an attention producer across process/session restart. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Observer is observation only. Retire it separately from the queue and only after evidence continuity is demonstrated; Python sandbox trajectories alone do not replace live Node observations.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — Monitoring decoupled; activation boundary; `docs/operations.md` — Coordinator-independent monitoring; `docs/evidence/wave1-learning-ledger.json` — LRN-019; LRN-027; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_services.detail.alienintent-observer.service.

### M04 — attention queue

**Purpose:** Durably retain judgment-required observations and handled state; supply the identity and resolution boundary used by liveness suppression.

**Demonstrated failure prevented:** During PY-09 the item remained unacknowledged while the provider was blocked, preserving suppression until recovery readiness. This is a shared queue/liveness protection, not an independently isolated causal effect.

**Authority:** SWF-27 Applied and Relationship to Decision Inbox; SWF-29 suppression amendment.

**Stated expiry:** File queue expires when SF-REQ-053 activation and SF-REQ-035 Decision Inbox integration replace its bootstrap function.

**Replacement gate:** Durable attention ingestion/identity/deduplication, attribution, resolved-versus-seen semantics, replay and migration of pending and historical items; verified liveness consumer and SF-REQ-053 activation. Keep product decision authority separate. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Zero outstanding items is a snapshot, not absence of future demand. Decision Inbox implementation does not replace the attention queue. Never delete the historical queue as part of retiring its producer.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — Applied; Relationship to the Decision Inbox; `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — SEEN != RESOLVED; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — attention_queue.

### M05 — Windows notification

**Purpose:** Best-effort human notification after a durable attention item is written.

**Demonstrated failure prevented:** No demonstrated prevented failure. Participant evidence records successful notification commands but no confirmed human receipt; exit zero is not a seen toast.

**Authority:** SWF-27 Applied: notification, not activation.

**Stated expiry:** No independent explicit expiry in the decision; participant inventory ties it to the queue it serves.

**Replacement gate:** SF-REQ-035 notification adapter or explicitly approved alternative with an end-to-end human receipt/response exercise, durable attempts/failures and preserved attention records. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** Reject the participant recommendation to retire merely as lowest-value. Removal changes a fallback notification path without demonstrated replacement. Founder must choose a tested replacement or explicitly accept removal risk. Current availability is participant-reported, not independently probed.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — Applied: Notification, not activation; `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md` — 6. Windows notification path; `docs/evidence/wave1-learning-ledger.json` — LRN-019.

### M06 — session-bound attention waiter

**Purpose:** Wake the resident coordinator by exiting a tracked task when durable attention needs judgment.

**Demonstrated failure prevented:** PY-09 incident reports the capacity-interruption attention item reached the resident coordinator in about 30 seconds, avoiding the previously observed silent waiting pattern. Timing is source-reported, not freshly measured.

**Authority:** SWF-27 wake-up bridge; docs/operations.md attention waiter.

**Stated expiry:** Expires with Wave 1 bootstrap or canonical SF-REQ-053 activation replacement; scoped to a resident episode.

**Replacement gate:** Before resident exit, a tested successor/human consumer for bootstrap attention, or operational SF-REQ-053; prove delivery and handling from durable identity while monitors remain independent. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** Re-armed after closure to preserve status quo. May retire with resident coordinator only after remaining attention duty is assigned and exercised or explicitly ended by authority; an empty queue does not prove it is no longer needed.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — The wake-up bridge, restored; `docs/operations.md` — Attention waiter; `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — SEEN != RESOLVED; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — session_bound_waiters.attention_waiter.

### M07 — coordinator checkpoint

**Purpose:** Provide durable continuation context to a fresh coordinator without relying on the old conversation.

**Demonstrated failure prevented:** No demonstrated prevented failure: no Wave 1 handover exercise is established. The checkpoint is untested for restart equivalence.

**Authority:** SWF-27 rules 3, 7, 8 and 9; bootstrap checkpoint described in operations.

**Stated expiry:** No explicit artifact expiry; continuation obligations survive bootstrap retirement.

**Replacement gate:** SF-REQ-053 durable project-owned context and a fresh invocation reconstructing authorized next actions, unresolved decisions and evidence from the same durable state; compare results before retiring the checkpoint as active input. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Retention is justified by the still-unreplaced continuity obligation, not by an invented successful handover. Preserve historical checkpoint evidence after migration; location outside the repository is not a reason to delete it.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — Durable rules 3, 7, 8, 9; `docs/operations.md` — Coordinator-independent monitoring; `docs/evidence/wave1-learning-ledger.json` — LRN-027; `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md` — 5. Coordinator checkpoint.

### M08 — PRODUCER-on-Claude temporary profile change

**Purpose:** Resume the interrupted PY-09 cycle-4 repair using the configured alternate provider and preserve partial work.

**Demonstrated failure prevented:** PY-09 recovery launched replacement producer 9979bdcc after quota exhaustion, retaining partial work and producing a candidate. It avoided waiting for the reported roughly nine-hour quota reset; exact counterfactual delay was not measured.

**Authority:** Founder PY-09 recovery-only authorization in the provider-capacity record; no accepted extension found.

**Stated expiry:** Completion of the current PY-09 recovery; explicitly does not redefine the default producer provider. PY-09 is DONE/CLOSED.

**Replacement gate:** Restore the prior PRODUCER provider block under a separately authorized operational change, validating current provider readiness, no owned invocation, profile schema and identity/auth/budget continuity; alternatively obtain an explicit scoped new decision before further use. Replacement operational: **not established**.

**Finding / REVERT_TEMPORARY_CHANGE:** Live snapshot reads workers.PRODUCER.provider, not the incorrect workers.PRODUCER.adapter path. Exception persisted into PY-09B/PY-10. Recommend narrow reversion, not blind full-backup restore or VERIFIER changes. Audit does not authorize reconfiguration/restart; historical backup existence is not readiness proof.

**Evidence:** `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — Recovery: scope; before/after block; backup; sequence; `docs/evidence/wave1-learning-ledger.json` — LRN-020; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_worker_providers.PRODUCER and verified_by; `docs/evidence/wave1-closure-manifest.json` — PY-09 terminal state.

### M09 — Node/bootstrap execution authority

**Purpose:** Own live execution while canonical Python is built and sovereignty remains unproven.

**Demonstrated failure prevented:** No demonstrated prevented duplicate failure in the cited recovery: PY-09 records exactly one lane claim and live worker, but no competing delivery rejected by the guard is shown there. SWF-29 identifies the Node lane guard as the protection; successful execution and absence of a duplicate do not alone prove a prevented attempt.

**Authority:** Architecture Authority §§42–43; FD-01 retains bootstrap operational authority until approved cutover.

**Stated expiry:** Python operates development end-to-end without Node and passes full conformance, live self-hosting, recovery, control-plane, evidence and learning proof.

**Replacement gate:** Full sovereignty evidence, approved one-writer live-profile migration, active-work/effect reconciliation, backup and nonduplicating rollback; conformance S1–S7 is a design elaboration, not current operational proof. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** PY-10 explicitly claims neither Node retirement nor live-work migration. Keep exactly one execution writer; retained liveness currently depends on Node lane exclusion.

**Evidence:** `docs/architecture/alienintent-architecture-authority-2026-09-19.md` — §§42–43; `docs/architecture/pre-python-gate/conformance-and-sovereignty.md` — Required sovereignty proof matrix; Cutover and rollback (candidate design); `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — Recovery step 6; `docs/decisions/2026-09-20-liveness-reconciliation.md` — Duplicate prevention; `docs/work-units/python/PY-10.md` — Non-goals; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_services.detail.alienintent.service.

### M10 — sandbox ingress tunnel

**Purpose:** Provide the isolated webhook ingress route for SWF-08/PY-10 live sandbox proof.

**Demonstrated failure prevented:** No demonstrated prevented failure attributable to the tunnel itself. PY-10 proves functioning isolated ingress; signature checks and profile isolation supply protections, not the tunnel alone.

**Authority:** SWF-08 sandbox infrastructure; PY-10 contract says sandbox is not dismantled by closure.

**Stated expiry:** Unit description says temporary Wave 1 infrastructure; no accepted automatic shutdown trigger. Wave 1/PY-10 terminal state alone does not override retention in the contract.

**Replacement gate:** Decision on continued isolated proof infrastructure versus retirement; before shutdown verify no pending sandbox delivery/effect or required consumer, preserve proof/configuration identities and establish reproducible isolated ingress if future proofs need it. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** In scope because explicitly temporary and still active. Current evidence cannot establish unused ingress or grant shutdown. Do not confuse it with the Node production route; no change to either is made.

**Evidence:** `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — live_services.detail.alienintent-sandbox-tunnel.service; `docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md` — SWF-08; `docs/work-units/python/PY-10.md` — BIU-specific closure: environment not dismantled; `docs/verification/PY-10-wave1-live-proof.md` — Ingress; Isolation; sandbox left standing.

### M11 — eighteen external bootstrap modules

**Purpose:** Implement operational observation, attention, release admission, liveness, preflight and evidence utilities with colocated tests outside repository custody.

**Demonstrated failure prevented:** Module-specific successes exist for liveness suppression and release admission (M2/M15), but no demonstrated prevention attributable to the external location or a complete 18-module suite. Test filenames are not executed-test evidence.

**Authority:** Component authority comes from SWF-21/27/29 and operator ownership in operations; no blanket authority or common expiry for the directory.

**Stated expiry:** Per-component replacement and scope expiry; no accepted directory-wide retirement condition.

**Replacement gate:** An authorized custody/maintenance disposition naming each module, consumer, authority, revision, test evidence and successor; migrate necessary protections under existing owners and retain historical evidence. Do not bulk-delete or bulk-promote this directory into permanent product architecture. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** In scope as an external operational dependency. Repository prose names and owns some functions, so the supplied claim that no artifact governs or tests them is too broad if read literally. Their code/revisions and full test coverage are not repository-controlled or independently validated here. Operating=true means operational components in the bundle, not that all test modules are running.

**Evidence:** `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — bootstrap_tooling_outside_the_repository: all 18 names; `docs/operations.md` — Coordinator-independent monitoring: bootstrap operator ownership; `docs/evidence/2026-09-21-liveness-retry-and-release-admission.md` — 14 admission tests and live refusal; `docs/evidence/2026-09-21-py09-provider-capacity-interruption.md` — Three defects found in coordinator tooling.

### M12 — resident coordinator multi-BIU tenure

**Purpose:** Preserve judgment continuity across Wave 1 under a scoped bootstrap exception.

**Demonstrated failure prevented:** No demonstrated prevented failure attributable to long tenure. LRN-027 establishes neither a handover nor restart equivalence; continuity benefit is a rationale, not measured comparative evidence.

**Authority:** SWF-27 Wave 1 tenure exception; post-Wave1 Program Director role/amendment supplies bounded program duties, not a perpetual extension of Wave 1 release authority.

**Stated expiry:** Wave 1 exception is bounded to Wave 1 with externalized state; subsequent program duties end at the approved program boundary or an authorized handoff.

**Replacement gate:** Explicit successor/tenure decision and fresh-context reconstruction from checkpoint, program state and authority; independently test product attention and program mailbox delivery after handoff. Replacement operational: **not established**.

**Finding / NEEDS_DECISION:** Wave 1 is terminal but a resident coordinator is still participating in the separately authorized program. Do not erase those duties or use them to carry SWF-21 into Wave 2. Independent author recommends a bounded handoff; participant reviewer testimony cannot alone prove continuity.

**Evidence:** `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` — Coordinator tenure during Wave 1; rules 6–10; `docs/evidence/wave1-learning-ledger.json` — LRN-027; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — coordinator_status; `docs/operations/post-wave1-program/program-director.md` — Execution posture; `docs/operations/alienintent-program-director-autonomous-execution-amendment.md` — §15 program completion.

### M13 — Program Director mailbox bridge waiter

**Purpose:** Deliver program review/task messages into the resident coordinator via tracked-task completion.

**Demonstrated failure prevented:** Bootstrap proof records correlated request/reply cor-957146bd3a1b without Founder relay and no duplicate delivery on re-arm. This demonstrates prevention of silent mailbox delivery in that exercise, not wake-up of a new coordinator.

**Authority:** Program Director operating rules and supported file-backed mailbox; separate from product attention.

**Stated expiry:** Session lifetime; role says a supported delivery helper supersedes this mailbox when available. No timed retirement is specified.

**Replacement gate:** A tested program-message consumer in the successor episode or supported helper preserving request/reply identity, pending messages, handled attribution and duplicate suppression; or completed program with no outstanding duties. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Do not retire alongside the product waiter merely because both are session-bound. This program remains in progress and its separate communication dependency must survive coordinator replacement.

**Evidence:** `docs/operations/post-wave1-program/program-director.md` — Direct messaging; `docs/operations/post-wave1-program/reports/bootstrap-proofs.md` — §7 bridge proof; §8 reconstruction; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — session_bound_waiters.bridge_waiter.

### M14 — SWF-26 PY-04 mutation gate

**Purpose:** Temporarily corroborate PY-04 mutation evidence before independent VERIFY.

**Demonstrated failure prevented:** Battery reproduced five survivors and found a sixth on 1b372c2a; accepted 03896f62 killed all 23. It detected insufficient mutation proof rather than merely asserting protection.

**Authority:** SWF-26 explicit Founder expiry; LRN-026 BOOTSTRAP_ONLY.

**Stated expiry:** PY-04 DONE, already occurred; earlier equivalent promotion would also have ended the exception.

**Replacement gate:** No replacement of this expired PY-04-only coordinator role is needed. General mutation-proof promotion remains with SF-REQ-050 and normal independent verification. Replacement operational: **not established**.

**Finding / RETIRE_CANDIDATE:** Already expired precedent, not a new retirement action. Keep historical battery evidence and do not reinstate it for later BIUs. Expiry event matters, not the conflicting historic DONE timestamps.

**Protection not lost:** No protection is lost by keeping the already-expired PY-04-only coordinator gate retired: PY-04 acceptance and its 23/23 mutation evidence remain intact; ordinary independent VERIFY and SF-REQ-050 obligations are unchanged. No later BIU is authorized to rely on this exceptional gate.

**Evidence:** `docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md` — Expiry; Evidence it produced; Battery provenance; `docs/evidence/wave1-learning-ledger.json` — LRN-026 and timestamp discrepancy.

### M15 — bootstrap release-admission gate

**Purpose:** Refuse release before launch when authorization, exact resolvable baseline, consistent wording or other admission conditions fail.

**Demonstrated failure prevented:** Recorded live run against PY-08 refused TASKS/no authorization/stale wording/open dependency; replay against defective PY-07 refused the same grounds cited by workers. This demonstrates a refusal, not proof it prevented the earlier PY-07 invocations.

**Authority:** SWF-21 admission amendment and durable SF-REQ-002 ownership.

**Stated expiry:** Bootstrap implementation is superseded when equivalent canonical admission operates at the live release boundary; durable admission obligations do not expire with manual release authority.

**Replacement gate:** Canonical live release admission enforcing all six preconditions plus eligibility before any launch, with meaningful negative controls and production-profile boundary evidence. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Separate mechanism from authority to perform transitions. Keep the check available even if Wave 1 release authority is formally ended; availability grants no authority to release new work.

**Evidence:** `docs/decisions/2026-09-20-wave1-release-coordinator.md` — Release admission preconditions; `docs/evidence/2026-09-21-liveness-retry-and-release-admission.md` — Incident 2; live validation output and replay; `docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json` — bootstrap_tooling_outside_the_repository.modules.

### M16 — b-disp command compatibility alias

**Purpose:** Keep existing installations launch-compatible during the AlienIntent rename.

**Demonstrated failure prevented:** No demonstrated prevented launch failure attributable to the alias in the reviewed evidence. package.json proves availability, not active installation use.

**Authority:** AlienIntent name/organization decision; preserve persisted identities and protocol markers.

**Stated expiry:** After installations migrate their launch commands.

**Replacement gate:** Installation-by-installation proof that launch commands and integrations use alienintent; canonical command exists, but complete migration is unproven. Persisted B-DISP markers/IDs are not alias-removal targets. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Explicitly temporary mechanism beyond the Wave 1 list. Operating=true means still shipped/available; invocation frequency is UNKNOWN. Command replacement exists but the migration condition is not demonstrated.

**Evidence:** `docs/decisions/2026-09-18-alienintent-name-and-organization.md` — Temporary compatibility alias; persisted-state compatibility; `package.json` — bin.alienintent and bin.b-disp.

### M17 — Local Program Director bootstrap orchestration role

**Purpose:** Route and sequence the approved post-Wave1 program using durable task state, review gates and scoped execution.

**Demonstrated failure prevented:** No independently demonstrated prevented operational failure for the role as a whole. Bootstrap reconstruction tests and corrected capacity-classification tests support narrow properties, not permanent orchestration effectiveness; this task required a routing correction.

**Authority:** Program Director role and autonomous execution amendment §§1, 6, 9, 15; no canonical BIU lifecycle authority.

**Stated expiry:** Approved program completion conditions in amendment §15; continued product/runtime orchestration is not granted.

**Replacement gate:** Complete or explicitly disposition approved program tasks, reviews, decision branches and final packet, then end the scoped role or obtain separately bounded continuation authority; preserve program state and evidence. Replacement operational: **not established**.

**Finding / KEEP_UNTIL_REPLACED:** Include as noncanonical bootstrap orchestration, not a proposed product requirement. Retain for unfinished authorized program duties; do not turn this role or its mailbox into permanent product architecture. This audit does not advance any program phase.

**Evidence:** `docs/operations/post-wave1-program/program-director.md` — Status; Authority boundaries; Execution posture; `docs/operations/alienintent-program-director-autonomous-execution-amendment.md` — §§1, 6, 9, 15; `docs/operations/post-wave1-program/program-state.json` — POSTW1-BOOTSTRAP-006 routing and RUNNING state; `docs/operations/post-wave1-program/reports/bootstrap-proofs.md` — §8 reconstruction; §10 corrected capacity classification.

## Safe transition order

Dependency order is necessary, not authorization. Obtain coordinator review and exact operational authority before any action; this phase executes no transition. Retained controls have conditional replacement gates, not calendar deadlines. Steps on independent branches may be considered independently; decisions block only dependent work.

Before any future action, refresh service/profile/queue/owned-work observations locally, pin component revisions, preserve rollback/evidence and obtain the exact decision named by the step. Approval of this audit is not approval to stop services. Negative-control and operational exercises below are proposed gates, not tests performed in this phase.

1. **SWF-26 PY-04 mutation gate** (depends on steps none). Record the already-expired SWF-26 precedent as historical; do not run or reintroduce the gate. Gate: Review confirms PY-04-only scope and retained acceptance/mutation evidence; no deletion or live action.

2. **eighteen external bootstrap modules** (depends on steps none). Before any cutover, have the bootstrap operator enumerate all 18 modules, consumers, revisions and test provenance and obtain a per-component custody decision. Gate: No bulk import or deletion; preserve release, monitoring, attention, notification and evidence dependencies.

3. **SWF-21 release authority** (depends on steps 2). Ask Founder to formally close the Wave 1 release grant and explicitly identify authority for any future live releases. Gate: No implied Wave 2 continuation; ending the grant does not remove M15 admission checks or assign release to the Director.

4. **PRODUCER-on-Claude temporary profile change** (depends on steps 2). Recommend narrow PRODUCER provider reversion at an authorized safe boundary, or obtain a new explicit exception before further use. Gate: Founder standing no-profile-change instruction must be superseded; prove quiescence, retained work, current original-provider readiness and validated exact provider-block diff. Preserve identities and verifier profile; verify operational readback after authorized change.

5. **sandbox ingress tunnel** (depends on steps 2). Obtain explicit sandbox tunnel retention/shutdown decision reconciling temporary label with contractual retention. Gate: Before any shutdown prove no consumer, pending delivery/effect or scheduled proof depends on ingress; retain evidence and reproducible isolated route. Do not affect production tunnel.

6. **coordinator checkpoint** (depends on steps 2). Prepare and test fresh-context continuation from durable checkpoint and authoritative state. Gate: Successor reconstructs scope, unresolved decisions, effects and authorized next actions without prior conversation; mismatch blocks tenure change. Preserve checkpoint until equivalent canonical continuity works.

7. **Program Director mailbox bridge waiter** (depends on steps 6). Prove successor program mailbox consumption and correlated reply, or settle all program duties. Gate: Deliver an authorized harmless test through the intended replacement path, with pending-message reconciliation and no duplicate handling. Keep current bridge until demonstrated.

8. **Windows notification** (depends on steps 2, 6). Resolve the Windows notification decision separately from queue retention. Gate: Prove human receipt/response through replacement, or obtain explicit Founder risk acceptance for removal; command success alone cannot clear this gate.

9. **session-bound attention waiter** (depends on steps 6, 7, 8). Resolve product attention activation and plan waiter retirement at resident handoff. Gate: Demonstrate replacement consumer for new and unresolved attention, including judgment-required outcomes, or explicit end of those duties. Queue stays durable and liveness suppression remains intact.

10. **resident coordinator multi-BIU tenure** (depends on steps 3, 6, 7, 8, 9). Authorize and execute a bounded resident-coordinator handoff only after both wake-up paths and durable continuity are ready. Gate: Explicit tenure decision; no loss of program review/communication duties; monitors independent; fresh invocation verifies equivalent authority and continuation. Unattended activation requires its own authority.

11. **bootstrap release-admission gate** (depends on steps 2, 3). Retire external admission implementation only after canonical live-profile admission is operational. Gate: All six preconditions plus eligibility refuse meaningful invalid cases before launch; formal release-authority closure alone does not clear this gate.

12. **SWF-29 liveness reconciliation** (depends on steps 2). Replace SWF-29 only after SF-REQ-056 or authorized equivalent runs operationally on the target live workload. Gate: Prove dropped-event recovery, suppression during provider/judgment block, explicit resolution, delayed delivery and restart duplicate safety. Preserve one writer and queue linkage; specification or sandbox-only tests fail this gate.

13. **SWF-27 observer** (depends on steps 2). Replace observer after canonical trajectory capture runs and evidence continuity is reconciled. Gate: No observation loss across the boundary; consumer/identity/restart/retention proof. Keep attention queue even if observer retires.

14. **attention queue** (depends on steps 9, 12, 13). Replace file-based attention queue only after its producers and consumers support canonical attention. Gate: Migrate retained history and pending items; prove dedupe, seen versus resolved, liveness suppression and SF-REQ-053/SF-REQ-035 integration. Empty queue alone fails the gate.

15. **Node/bootstrap execution authority** (depends on steps 11, 12, 13, 14). Consider Node retirement only after full sovereignty proof and explicit cutover decision. Gate: Single approved live-profile writer; reconcile owned work and external effects, retain compatible checkpoint/rollback, prove Node-independent live self-hosting and full required suite. No simultaneous Node/Python dispatch of the same work.

16. **b-disp command compatibility alias** (depends on steps none). Retire command alias only after all installation launch references are migrated and validated. Gate: Prove installation coverage and canonical command launches; preserve protocol markers, persisted lane/resource identities and history.

17. **Local Program Director bootstrap orchestration role** (depends on steps 7, 10). Close the scoped Director role only at its approved program completion boundary or an explicitly authorized successor handoff. Gate: Amendment §15 completion evidence, reviews and decision branches resolved/dispositioned; mailbox and artifacts preserved. No Phase 7 or later work is performed by this audit.

The bundle custody decision in step 2 is an inventory/ownership prerequisite, not retirement of the bundle. Individual modules stay until their component gates clear; evidence/test helpers may remain historical artifacts. Step 15 is conditional on future authorized sovereignty work, not authorization to implement it. Any failed gate retains the old protection and blocks that transition.

## Scope and validation

Additional mechanisms beyond the explicitly named list: resident coordinator multi-BIU tenure; Program Director mailbox bridge waiter; SWF-26 PY-04 mutation gate; bootstrap release-admission gate; b-disp command compatibility alias; Local Program Director bootstrap orchestration role. The separately flagged tunnel and external modules are both included.

SWF-10 scripted worker is bounded test infrastructure, not a live authority exception with a retirement mandate; preserve regression fixtures. Durable Product Requirements, SWF-29 Part 2, Decision Inbox authority, persisted B-DISP markers and historical evidence do not expire with these implementations.

The external bundle contains exactly the 18 module names preserved in JSON scope_notes, including colocated tests. It is assessed as a custody mechanism; its known protection-bearing components also have separate rows.

Validation (exit 0 for both):

- `rtk proxy python3 tools/evidence/check_retirement_matrix.py docs/evidence/wave1-bootstrap-retirement-matrix.json` — PASS, 17 mechanisms, 0 failures.
- `rtk proxy python3 tools/evidence/check_wave1.py --negative-controls` — PASS, 1,075 checks, 0 failures, 13/13 negative controls killed.

Input/source hashes remain unchanged; all cited paths resolve; transition dependencies point only to earlier steps. Neither checker was edited. These results validate artifact structure and retained evidence consistency, not runtime replacement, handover, notification receipt, provider readiness or sovereignty. Ancestry uses existing local Git objects and `origin/main`; no remote verification occurred. DISPUTED: NONE.
