# AlienIntent — Durable 36-Hour Operating Record

**Window:** 2026-09-23 18:00 ICT through 2026-09-25 ~06:00 ICT  
**Captured:** 2026-09-25  
**Scope:** AlienIntent factory execution, Factory Director continuity, Agent Ready integration, Wave 2 flow, backlog-reconciliation methodology, provider failure/failover, and durable Founder decisions.

This is an operational continuity record, not a new source of product or architecture authority. Canonical decisions, Product Requirements, Issue records, BIU contracts, accepted candidate SHAs, Factory Director inbox entries, and retained evidence remain authoritative in their own scopes.

## Executive summary

During this window AlienIntent crossed an important operating boundary: the factory stopped depending on a persistent human/Claude coordinator session and transferred Factory Director duty to the durable Python Factory Director Host. The host survived live restarts, reconstructed state from durable records, released work without Founder prompting, handled verifier rejection/repair cycles, and maintained a forward pipeline.

The operating model was also refined. The Factory Director is a director, not the worker doing every cognitive task. Detailed requirement reconciliation is delegated to bounded read-only specialist episodes; deterministic tooling should do mechanical work first; cognition is reserved for semantic judgment; validated gaps are routed through the existing Proposal Intake -> SPECIFY -> DESIGN -> independent Design Verification -> PLAN -> candidate BIU -> Agent Ready -> READY path.

A major provider-failure incident then exposed important gaps. Claude subscription capacity exhaustion took both the Factory Director and Morty/PRODUCER offline. Manual failover to Codex preserved authority boundaries but the Codex-hosted Director repeatedly failed because its environment lacked required operational write access and its specialist collaboration launch path failed. An automated overnight restoration task did not restore routing. On 2026-09-25 the normal routing was manually restored and the Claude Director resumed the factory, releasing #95 to IMPLEMENT.

## Durable operating decisions

1. **Factory Director Host owns Factory Director duty.** Old session-bound/manual mechanisms are inactive fallback only.
2. **Rollback insurance is retained.** The previous continuity mechanism is not retired, deleted, disabled, or repurposed. Retirement requires an explicit future Founder decision.
3. **No PR workflow for AlienIntent or Agent Ready.** Accepted AlienIntent work lands by direct merge preserving the accepted candidate SHA.
4. **Pipeline must not run dry.** Maintain dependency-safe READY/near-READY supply where the approved plan permits it, without bypassing proof, design, dependency, or authority gates.
5. **Product Requirement closure rule:** a Product Requirement may reach DONE only when all currently authorized acceptance criteria are covered by retained executable feature-level regression evidence. Future/deferred extent remains explicit and prevents full closure.
6. **Feature regression tests assert externally meaningful AlienIntent behavior** and should remain valid across implementation replacement where practical; they should not freeze Node/Python internals merely because those internals exist today.
7. **Backlog reconciliation starts from Product Requirements, not only candidate BIUs.** TASKS/CAPTURE lanes must be reconciled against delivered evidence because board lifecycle state can lag implementation progress.
8. **Gap findings do not become BIUs directly.** A genuine uncovered gap becomes Proposal Intake / canonical planning input and proceeds through the normal lifecycle.
9. **Factory Director delegates specialist analysis.** Requirement-level reconciliation should normally be one bounded read-only specialist episode per Product Requirement. Specialists analyze/report; they do not mutate code, requirements, priority, architecture, Project state, lifecycle state, or create BIUs.
10. **Minimum-capability routing:** deterministic inspection first; when cognition is required, use the least-cost provider/model demonstrated capable of the bounded specialist task. Escalate capability only when necessary and retain provider/model/cost/time/token evidence when available.
11. **Cognition-to-determinism rule:** cognitive judgment patterns may become deterministic controls when the pattern is stable, mechanically expressible, and worth encoding. Repetition alone is not sufficient.
12. **REVIEW explores; VERIFY accumulates.** Newly discovered failure classes should become durable mechanical checks when justified rather than relying on workers to remember them.

## Factory Director Host build and proof

Issue #89 (FDH-01) implemented the non-cognizant Python host plus authoritative activation predicate and provider-neutral episode launcher. Initial candidate 8da68f7 was rejected; the repaired candidate was accepted and landed.

The live continuity proof is retained under:
- docs/evidence/fdh-01-live-proof/
- evidence commit 59db3c5

The proof demonstrated twelve live steps including fresh episode launch, durable-state reconstruction, autonomous release of real work, handoff to successor episodes, WIP-aware idling, and no Founder prompt required.

The host then survived a deliberate restart while a Director episode remained active. Evidence:
- docs/evidence/fdh-01-restart-recovery/
- commit 0eda915

The episode survived the service restart, the new host recognized the same active lease, no duplicate Director launched, and control resumed after the episode exited. A later self-initiated host redeploy produced a second real restart/recovery observation.

## FDH follow-ups #91 and #92

Two live-proof defects were converted into bounded follow-up Issues.

**#91 / P1 — PATH / gh availability**
- fixed the systemd/live-proof environment so gh can resolve;
- installer seeds PATH only for new env files and preserves existing env files;
- missing gh now produces a specific diagnostic;
- discriminating tests were run against earlier baselines;
- landed as merge f0386c8.

**#92 / P2 — WIP classification**
- changed the WIP predicate from equality to claims >= wipLimit;
- preserves fail-safe action during transient PRODUCER/VERIFIER/closure overlap;
- landed as merge 669e5f1;
- deployed to the live host;
- live overlap behavior was subsequently observed as WIP_INTENTIONALLY_FULL.

The retirement threshold is met. A correction was recorded on #89 after the first retirement report incorrectly claimed no worker/verifier failures had occurred. Actual host-era evidence includes multiple verifier rejections and a worker failure recovered without Founder intervention. Founder decision: **threshold met, old continuity retained as inactive rollback insurance.**

## Project materialization / GitHub Projects indexing incident

Project materialization was made durable and fail-closed. Canonical documentation:
- docs/operations/alienintent-project-board-materialization.md
- board repair work #83 / BRD-83 ultimately landed as 2ba8c3c

A GitHub Projects v2 indexing delay was reproduced on both the primary Project and a sandbox Project. item-add returned an item, Issue-side membership/direct lookup showed it, while the forward Project item collection temporarily omitted it. #86 later appeared after roughly 70 minutes; later materializations recovered progressively faster.

The 3-hour recovery probe subsequently reported three consecutive recoveries and real materializations #94/#97/#99 worked normally. The probe timer is now **disabled and inactive**. Probe script/logs remain available for reactivation if the symptom returns.

## Agent Ready integration

Agent Ready is an independent repository at /mnt/d/Projects/agent-ready.

Important design rules reinforced during this window:
- no hard-coded exact model/provider dependency;
- provider evidence must be capability/provenance based;
- native Agent Ready, not prompt emulation, is the execution-readiness authority.

AlienIntent Issue #86 (ARP-01) repaired the provenance reader so native Agent Ready evidence can be provider-generic. JC rejected two real defects: malformed provider evidence values could crash rather than reject; and present provider_evidence:null could be treated as absent and pass.

The accepted candidate 299c412 landed via merge 5d3d14a. Claude-backed native Agent Ready then worked end-to-end.

## Wave 2 work completed in this window

- **#80 / WO-220202 — Ambiguity and attributed decision resolution:** DONE, merge 70fa714, accepted candidate d0eacfb.
- **#81 / WO-220203 — Pinned premise evidence bridge:** DONE, merge 474343a; verifier rejection/repair handled autonomously.
- **#83 / BRD-83 — Project board visibility/release-admission repair:** DONE, merge 2ba8c3c; multiple JC rejection cycles exposed real release-path defects.
- **#86 / ARP-01:** DONE, merge 5d3d14a.
- **#89 / FDH-01:** DONE.
- **#91 / FDH P1:** DONE, merge f0386c8.
- **#92 / FDH P2:** DONE, merge 669e5f1.
- **#94 / WO-220204 — Pre-implementation proof plans:** DONE, merge 44fd55c. The work experienced a background-task/worker completion failure, preserved partial work, used a bounded replacement, and later accepted/landed with discriminating evidence.
- **#97 / WO-220205 — Design admission and independent review mechanics:** DONE, merge 036c5fc.

#97 is important methodologically. JC rejected the first candidate because a stale design review could become admitted again after invalidation/reinspection when the same content-only digest was reconstructed. Morty repaired the freshness semantics, preserved prior evidence, and JC accepted the repaired candidate. This was a normal repair cycle with no Founder intervention.

## #94 background-work failure -> Proposal Intake

A Claude PRODUCER invocation on #94 ended while background evidence work it owned was still active, yielding DURABLE_RESULT_MISSING. Partial work was retained and a bounded replacement completed the candidate.

Founder explicitly directed this failure to normal gap intake rather than direct implementation. Issue **#100** now exists at CAPTURE:

Proposal: prevent worker completion while owned background work remains active

Desired outcome: mechanically prevent a worker from declaring completion or ending its session while owned child/background work remains active. The mechanism is intentionally undecided. Launch flags, process accounting, preflight, or runtime guards are candidates to evaluate through SPECIFY/DESIGN rather than Director decisions.

## Backlog reconciliation methodology

The Project board contains Product Requirement Issues in TASKS/CAPTURE that do not directly represent unfinished implementation. Wave 1 PY-02 through PY-10 already delivered and live-proved substantial extents of #3-#14 and #16. Therefore backlog prioritization must first reconcile each Product Requirement against retained evidence and feature regressions.

Agreed requirement classifications:
- SATISFIED
- PARTIALLY_SATISFIED
- NEEDS_DECOMPOSITION
- DESIGN_GAP
- AUTHORITY_BLOCKED
- DEFERRED_BY_WAVE

Per-acceptance-criterion evidence classifications:
- PROVEN
- PARTIAL
- UNPROVEN
- DEFERRED
- AUTHORITY_BLOCKED

Specialist output must include exact evidence refs, executable feature-regression refs, evidence sufficiency, remaining gap, overall classification, stale board-state assessment, proposal candidates, authority questions, and unsupported/uncertain claims.

The specialist may recommend that a requirement is satisfied; it cannot itself move the Product Requirement to DONE.

### Reconciliation #3 completed

A fresh read-only specialist reconciled **#3 / SF-REQ-001 Continuous factory execution**, followed by Director validation. Durable report is retained as Issue #3 comment issuecomment-5816932386.

The result did not simply close #3. It found strong retained proof for bounded continuous drain, priority/dependency handling, automatic refill at WIP=1, independent work during blocks, restart safety, and no human per-BIU trigger. It also preserved a broader repeated-nonterminal progress residual and correctly deduplicated that residual against an existing proposed SF-REQ-022 extension rather than inventing a new proposal.

Disposition: evidence map retained; bounded feature proven; full requirement closure **not yet decided**.

### Reconciliation #4 onward blocked by specialist-launch failure

After #3, repeated attempts to commission the #4 specialist failed before agent creation with “collab spawn failed: no thread with id ...”. No specialist report exists for #4 from those attempts.

This is a real Factory Director delegation/runtime gap: the methodology now expects bounded specialist delegation, but the Codex-hosted Director path did not have a functioning fresh specialist launcher.

## Factory Director role separation

Current operating architecture:

Founder -> Factory Director -> bounded specialists / implementation workers / verifier

The Factory Director reconstructs authoritative state, maintains flow and pipeline health, commissions bounded work, validates specialist results, resolves ordinary control decisions within delegated authority, routes genuine gaps into Proposal Intake, and escalates real product/architecture/Founder authority questions.

The Factory Director should not personally perform every detailed reconciliation or implementation task.

Specialist cognition should be ephemeral, bounded, and read-only by default. Mechanical evidence lookup, SHA/revision checks, regression existence, dependency/provenance validation, and lifecycle eligibility should be deterministic where possible.

## Provider-capacity incident and failover

On 2026-09-24 Claude subscription capacity was exhausted. This affected more than the observer:
- Factory Director host was configured to Claude Opus 5.5;
- Morty/PRODUCER was also configured to Claude Opus 5.5.

The Claude Director episode handling backlog reconciliation exited after consuming significant capacity, then subsequent Claude launches failed quickly with zero useful output and the host entered exponential crash-loop backoff.

Founder authorized temporary failover:
- Factory Director -> Codex / GPT-6 Astra
- Morty/PRODUCER -> Codex / GPT-6 Astra
- JC/VERIFIER remained Codex / GPT-6 Astra

Authority, GitHub identities, WIP limits, inbox, history, and durable state were preserved. Provider-specific crash-loop backoff was cleared when switching providers.

The failover preserved continuity mechanics but exposed operational incompatibilities:
1. **Codex Director episodes repeatedly exited EXIT_1.**
2. The Codex Director sandbox lacked write access to operational paths such as ~/.config/alienintent/self-hosting.json and the Factory Director processed-inbox directory. It could diagnose #95 release prerequisites but could not bind the required execution limit or receipt completed inbox items.
3. Specialist collaboration launch failed (“collab spawn failed: no thread with id ...”).
4. Repeated Codex episodes checkpointed the same blocked control state rather than advancing it.
5. Crash-loop backoff grew to one-hour intervals.

This is not an authority failure. It is an execution-environment/provider-routing failure.

### Overnight restoration failure

A one-time scheduled recovery task was created to restore normal routing after Claude reset, with instructions not to interrupt active Codex work. The task ran, but **did not restore the live configuration**. By morning, both Director and Morty were still routed to Codex and the host had accumulated repeated Codex EXIT_1 crash-loop events.

This is retained as a failure of the operational recovery path. The scheduled task must not be represented as successful merely because it executed.

### Manual restoration on 2026-09-25

Normal routing was manually restored:
- Factory Director -> Claude Opus 5.5
- Morty / PRODUCER -> Claude Opus 5.5
- JC / VERIFIER -> Codex GPT-6 Astra

The stale Codex crash-loop backoff was cleared and relevant services restarted. Fresh Claude Director episode factory-director-3b19543ca543423f8ef9791f7be8c90b became ACTIVE.

That Director then cleared the #95 operational-write blocker:
- bound execution.biuLimits for #95 to 3 cycles / 1 replacement per phase;
- restarted alienintent.service with no active claims;
- re-probed worker credentials;
- posted the RELEASED record;
- advanced #95 to IMPLEMENT.

Current #95 PRODUCER invocation at capture:
AlienLogicLab/alienintent#95:PRODUCER:4a2582db-0aaf-4794-94a1-ad6ae61bc1c6

## Current pipeline at capture

- **#95 / WO-220302 — Durable context reconstruction:** IMPLEMENT
- **#96 / WO-220304 — Monitor ticks, scan health and trajectory seam:** READY
- **#97 / WO-220205 — Design admission and independent review mechanics:** DONE
- **#99 / WO-220303 — Bounded episodes and stale-command refusal:** PLAN
- **#100 / background-work completion gap:** CAPTURE

#99 has a draft proof packet with unresolved owner questions. U-9/U-11 may eventually require Founder input, but standing decision is to keep them parked until they actually block dependent work.

Planned forward flow remains: complete #95, keep #96 as READY supply, continue #99 when prerequisites/questions are resolved, and prepare WO-220207 / WO-220209 as dependencies permit.

## Known gaps / follow-up candidates exposed in this window

1. **Automatic provider-capacity failover for Factory Director cognition.**
2. **Provider/capability routing should be least-cost capable**, with deterministic preflight and explicit provider availability/capability checks.
3. **Fresh specialist-launch capability is not reliable across Director providers/environments.**
4. **Factory Director execution environment must match the operational authority it is expected to exercise.**
5. **Scheduled restoration/failback is not yet trustworthy.**
6. **Worker-owned background task completion guard** is captured as Proposal #100.
7. **Product Requirement closure projection is not automatically reconciled from completed BIUs/evidence.**
8. **Provider/model diversity temporarily collapses during failover** when both PRODUCER and VERIFIER use the same provider/model.

## Important retained evidence / continuity locations

- Factory Director inbox: ~/.local/state/alienintent/factory-director/inbox/
- Processed inbox receipts: ~/.local/state/alienintent/factory-director/inbox/processed/
- Host history: ~/.local/state/alienintent/factory-director-host/history.jsonl
- Host lease: ~/.local/state/alienintent/factory-director-host/lease.json
- Node runtime state: ~/.local/state/alienintent/state.json
- Self-hosting config: ~/.config/alienintent/self-hosting.json
- Factory Director host config: ~/.config/alienintent/factory-director-host.json
- Project materialization procedure: docs/operations/alienintent-project-board-materialization.md
- FDH live proof: docs/evidence/fdh-01-live-proof/
- FDH restart proof: docs/evidence/fdh-01-restart-recovery/
- Wave 2 candidate DAG: docs/evidence/wave2-candidate-bius.json
- Proposal Intake Product Requirement: Issue #66 / SF-REQ-055
- Backlog reconciliation Founder direction: founder-backlog-reconciliation-20260924T132525Z.json
- Background-work gap direction: founder-gap-94-background-completion-20260924T133019Z.json
- Retirement correction direction: founder-retirement-report-correction-20260924T133019Z.json

## Methodology state after this window

AlienIntent now has a materially clearer development methodology:

**Product Requirement -> evidence/gap reconciliation -> Proposal Intake where needed -> SPECIFY -> DESIGN -> independent Design Verification -> PLAN -> bounded candidate BIU -> Agent Ready -> READY -> RELEASE -> IMPLEMENT -> independent VERIFY -> REVIEW -> ACCEPT -> DONE -> requirement-level feature regression / closure evidence.**

Roles are separated:
- Founder owns genuine product/architecture/priority authority.
- Factory Director owns flow, delegation, bounded control, and ordinary coordination.
- Specialists own narrow cognitive analysis.
- PRODUCER owns implementation within BIU authority.
- VERIFIER independently challenges the exact candidate.
- Deterministic control owns canonical lifecycle, evidence gates, WIP, reservations, custody, and refusal conditions.

The direction is deliberate: **a disciplined development factory, not a collection of autonomous smart agents.**

## Source basis for this record

This record was reconstructed from:
- Git history on origin/main across the stated window;
- GitHub Project #1 current item/status readback;
- Issues #3, #80, #81, #83, #86, #89, #91, #92, #94, #95, #97, #99, #100 and their durable comments;
- Factory Director inbox entries and processed receipts;
- Factory Director host history and lease;
- runtime active-claim state;
- retained FDH / Wave 2 evidence;
- Founder decisions made during the working session and durably relayed into the Factory Director inbox.

Where an event was only observed operationally and not yet represented as a canonical Product Requirement/decision, this document records the observation without upgrading it to authority.
