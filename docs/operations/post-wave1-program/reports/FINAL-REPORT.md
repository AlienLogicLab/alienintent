# POSTW1-PACKET-014 — Final report and Founder approval packet

Prepared at local repository HEAD `f94e58e833cd44d264b15b0351416097dbca8c34`, branch `main`. Wave 1 terminal implementation: `10cc81620511af56befbb6140504d1991bb02846`. This is the programme's durable terminal report artifact, revised under POSTW1-PACKET-014-R1 after the fresh-Claude accuracy check returned CORRECTIONS_REQUIRED, pending review closure and Founder action. It does not declare full programme completion under amendment §15: independent review closure, landing and remote verification remain outstanding. The direct task prohibits commits, push, network, programme-state changes and Wave 2 execution. The packet author honoured that boundary. The Director subsequently corrected the orchestration record and modified `program-state.json` in the working tree, including the VERIFY-010 routing correction at 2026-09-21T22:31:40Z. The Director also repaired `route()` and its tests. Attribution and sequencing are supplied by POSTW1-PACKET-014-R1; the current local diffs confirm the changes. This repair changes only the report and approval packet.

The [structured approval packet](../../../evidence/wave2-founder-approval-packet.json) contains all **23 required sections**, source hashes, historical repository SHAs, full candidate contracts/DAG/assessments, seven recommendations and validation output. Its source copies are evidence snapshots, not new canonical requirements. All recommendations below are **NOT ENACTED**; none assigns Priority/Wave or closes authority gaps.

## 1. What happened

Wave 1 proved bounded continuous execution on real sandbox infrastructure, independent candidate retrieval and verdict admission, live GitHub transport/readback, and conservative recovery that parks ambiguous effects. Eleven BIUs reached DONE. That does not complete every linked requirement, establish production cutover, or prove economic efficiency. The [final retrospective](../../../evidence/wave1-final-retrospective.json) preserves Definition, Observation and Verdict separately across eight architecture areas.

The accepted yield is 44 verifier verdicts, 33 rejections, 44 execution cycles, two first-pass acceptances (PY-09B and PY-10), nine Founder-exception markers across seven BIUs, 44 repair records and 46 superseded records. Rejections mix VERIFY failures and REVIEW discoveries; a unique-defect count is UNKNOWN. Same-phase retries are not execution cycles. Summed elapsed-to-DONE is 104,007.129 seconds across eleven BIUs, ranging from 3,706.544 to 21,523.43 seconds; this is neither active compute time nor measured coordinator delay. The 1,479 sum of cumulative tests-at-landing snapshots is **not** a wave test total. Token usage and cost are **UNKNOWN for all eleven BIUs**.

Failures included green tests with ineffective guards, unexercised composition paths, repair regressions, invalid release records, candidate identity loss, invocation success without a valid verdict, uncertain readback after a process kill, unbounded nonterminal redispatch, provider capacity interruptions and incomplete observations. PY-09's gutted validator left 183 tests green. The corrected permission premise first failed 2/17 checks before the necessary grant and passed 17/17 afterward; the original green premise had omitted the real consumer's needs.

Corrections established scoped custody, release refusal, no-verdict refusal, evidence consistency and recovery controls. PY-09B retained 13 red guards; PY-10 retained 22. Agent-Ready BLOCKED/SPLIT_RECOMMENDED and NEEDS_CLARIFICATION outcomes held admission until resolution and fresh assessment. PY-10's historical non-READY results survive in Git; no silent coercion is demonstrated. The 32 current assessment files normalize from 15 direct objects and 17 MCP envelopes to 31 READY and one NEEDS_CLARIFICATION; a top-level-only reader was wrong.

The [Learning Ledger](../../../evidence/wave1-learning-ledger.json) consolidated 101 raw candidates into 30 lessons: nine ALREADY_GRADUATED, seventeen STRENGTHEN_EXISTING_OWNER, one GAP_TRAP_PROMOTION, two NEW_CAPABILITY_GAP and one BOOTSTRAP_ONLY. Twenty-six lessons have documented consumption, eight have scoped deterministic enforcement and fourteen have red evidence. These populations overlap. Two later first-pass acceptances do not establish causality: provider substitution and verification-first sequencing are confounded, with n=2.

## 2. What changed

Historical authority changes include SWF-23 convergent repair/proof preservation, SWF-24 deterministic failure-class promotion, SWF-25 independent Design Verification, amended SWF-21 release admission, SWF-29 liveness/retry handling, SWF-30 custody/retention, SWF-32 cycle semantics, SWF-33 the authorized PY-10 transport split, and SWF-34 configuration-based Project isolation with compensating proof. They are historical source decisions; this packet creates or changes none.

The programme produced eleven deterministic artifact checkers during phases 2–13; `tools/evidence/check_wave1.py` predates it, from the Phase 0/1 evidence pass. Twelve checkers passed in the original packet validation. The programme also produced the learning/promotion evidence, a four-outcome Agent-Ready handling matrix, a conserved split/replan design, a seventeen-mechanism retirement audit, architecture reconciliation, ten selected specifications and Design Contracts, a verified repaired design, and a 46-node plan with 46 candidate BIUs and assessments. These are process/design capabilities and evidence controls, not implemented Wave 2 runtime capability.

The [Gap Trap backlog](../../../evidence/wave1-gap-trap-promotion-backlog.json) considered eighteen lessons and proposes seven promotions: LRN-001 mutation proof, LRN-002 composed-path proof, LRN-003 sequencing, LRN-004 repair preservation, LRN-010 liveness, LRN-016 lifecycle dependency admission and LRN-019 durable context. Four are proposed BLOCKING and three ADVISORY, using three existing layers; eleven declines retain explicit revisit conditions. No proposed promotion is reported as deployed. The final contracts preserve eighteen designed enforcement obligations, including nine promotion entries representing seven unique promotions.

The [split/replan design](../../../evidence/wave1-biu-split-replan-design.json) conserves 69 obligations with an integration parent, identity/lineage, invalidation, lifecycle, projection and recovery protocol. A generalized split transaction remains unimplemented and SPLIT-G1 unassigned. SF-REQ-013 compilation ownership does not automatically own recompilation transactions; SF-REQ-015 validation does not confer rewrite authority.

Five Phase 7 amendment directions remain recommendations: SF-REQ-008 durable attributable outcome readback; SF-REQ-022 durable nonterminal retry/run budgets; adjacent SF-REQ-025 coordinator-tool environment/authentication precedence; adjacent SF-REQ-029 provider-neutral observations; and SF-REQ-013 split/replan. SF-REQ-056 was authored during SPECIFY from a referenced but undefined ID and still requires ratification. No pending amendment was silently adopted.

Architecture reconciliation retains distinct identities for candidates, invocations, attention and cycles; fenced effect recovery; capability/budget-constrained provider routing; observations separate from verdicts and human awareness; transport behind ports; lifecycle-authoritative dependencies with Work Management as projection; and Node/bootstrap authority until sovereignty proof. Native dependency projection, intermediate projection, durable runtime cycle counting, normalized progress and full operational replacement remain incomplete or unproven. RAI remains unwired and compatibility markers/resource identities remain protected.

## 3. What remains unresolved

Seven Founder decision records are open in [programme state](../program-state.json), covering more than seven underlying questions. Their `critical_path=false` labels meant preparation could continue; they do **not** make execution permissible. POSTW1-DECIDE-013A now holds the only assessable entry point.

LRN-022 and LRN-023 are the two NEW_CAPABILITY_GAP items: coordinator-tool environment/authentication precedence and provider-neutral started/progress/terminal/capacity normalization. Adjacent requirements are proposed amendment targets, not existing complete owners. G1/G2 assessment implementation/schema/CLI and serialization ownership, SPLIT-G1, five design authority gaps, SF-REQ-056 ratification and component-specific operational duties also remain unresolved. These overlapping populations must not be added as distinct new requirements.

The [retirement matrix](../../../evidence/wave1-bootstrap-retirement-matrix.json) contains one already-expired RETIRE_CANDIDATE (SWF-26 PY-04 mutation gate), nine KEEP_UNTIL_REPLACED mechanisms, one proposed PRODUCER reversion and six NEEDS_DECISION mechanisms. Sixteen were still operating/available in its historical snapshot; this task made no fresh live observation. An expired precedent does not require a new shutdown. No retirement or provider change is performed here.

Retain checkpoint, mailbox bridge, liveness reconciliation, observer, attention queue, release-admission gate, Node execution authority, command alias and scoped Director duties until their individual gates hold. Queue emptiness is not retirement evidence. Ending Wave 1's SWF-21 grant does not remove admission protection or authorize Wave 2 releases. Windows notification needs tested replacement or explicit risk acceptance; session waiter/resident duties need demonstrated handoff; tunnel and eighteen external modules need custody/dependency decisions. PRODUCER reversion requires narrow operational authority; VERIFIER was baseline and must not be reverted with it.

Residual UNKNOWNs include usage/cost for every programme dispatch, exact unique defects, provider comparative effects, repeated-reasoning savings, Windows human receipt, coordinator replacement equivalence, external module revision/test completeness and current remote/live state. The structured packet retains the original index of 232 UNKNOWN observations using source JSON pointers plus telemetry/residual records; that is not a count of distinct risks. Its historical pending-accuracy-verdict entry is now superseded by CORRECTIONS_REQUIRED; independent closure of this R1 repair remains pending. Missing allocations remain UNBOUND, not zero. SWF-34's historical configuration-isolation acceptance remains bounded; no new residual risk is accepted by this report. Deferred work includes all Wave 2 implementation, proposed promotion deployment, general split/replan, product durability/budgets, normalization and live replacement.

## 4. Wave 2

**Wave 2 has zero READY BIUs. All 46 were assessed: 45 BLOCKED and one NEEDS_CLARIFICATION.** Forty-six well-formed candidates are not forty-six startable jobs. WO-220101 (S0) is the single assessable entry point and waits on AR13-CQ-001: identify the authorized allocator and exact retained execution packet with positive limits and current remaining allowance, then bind executable proof inputs. A fresh assessment is required after resolution; the current verdict cannot be edited into READY.

The selected ten requirements are SF-REQ-011 requirements IR; 012 ambiguity detection; 013 initial BIU compilation; 014 pre-implementation verification; 015 lint/readiness process; 016 Definition/Observation/Verdict; 039 offline factory proof; 051 Design Contract/Verification; 053 persistent control and bounded episodes; and 056 liveness. SPECIFY evaluated 41 candidates and rejected 31 with reasons. Ratification and authority holds remain visible.

The repaired design is **VERIFIED as design, not implementation-ready**. Three fresh-Claude verification rounds required two repairs: the first repair introduced two material defects, an import-direction table conflicting with existing imports and identifier handling rejecting legitimate acceptance IDs. R2 withdrew the unauthorized table, retained descriptive imports and an explicit authority hold, and pinned token categories/source manifest. Final verification retained prior closures and found no new material defect within its targeted scope. It did not rerun the whole initial design audit or execute the eighteen future probes. SQLite concurrency, denied-network fixtures, real-worker readback durability and provider context telemetry remain future proof obligations.

The [DAG/technical plan](../../../evidence/wave2-technical-plan.md) has 46 nodes, 41 scoped capability owners, thirteen capstones, five technical tracks, 53 acceptance criteria, 46 fixture groups and eighteen migration records. Fourteen nodes are independent of the five gaps and separate authority; nine more are held only by other authority; 23 are gap-blocked, fifteen of those also carrying separate gates. These are planning classifications, not readiness results. S0 proof substrate precedes evidence/fencing, upstream admission and control/lifecycle branches; capstones consume predecessor proof. Offline proof must use the actual shared kernel, not a second scripted lifecycle. Real outcome emission must precede role-router activation.

Gap leverage must use complete propagated gap sets, not raw per-gap fan-out:

| Resolution set | Nodes freed of the five design-gap holds |
|---|---:|
| R1-GAP-013-ALLOCATION alone | 0 |
| R1-GAP-039-ORCHESTRATION alone | 0 |
| R1-GAP-039-REAL-OUTCOME alone | 1 |
| R2-GAP-051-EDGE-AUTHORITY alone | 1 |
| R1-GAP-MONITOR-HOST alone | 5 |
| Both SF-REQ-039 gaps together | 6 |
| All five gaps | 23 |

These counts were recomputed from `authority_gap_refs`. Only resolving all five unblocks the full plan **with respect to those five gaps**. Separate decisions, predecessor proof, allocation, readiness and release still apply; none of these numbers counts newly READY BIUs.

Eight execution prerequisites are tracked (their scope matters):

1. **W2-P01 — Before any Wave 2 implementation:** Founder approves execution scope at the final gate after the fresh independent Phase 14 accuracy check. This packet is not that approval.

2. **W2-P02 — Single entry point WO-220101:** Resolve AR13-CQ-001 with attributable allocator, exact retained execution packet, authorized positive limits and current remaining allowance; otherwise retain the hold.

3. **W2-P03 — Each candidate before implementation:** Pin executable proof inputs, commands, expected results and evidence schema against the current contract and baseline. Planned fixtures are not executed proof.

4. **W2-P04 — Each candidate before release:** Obtain a distinct fresh Agent-Ready assessment after clarification/dependency/authority resolution, preserving old verdicts. Then satisfy separate release admission, exact candidate/baseline and eligibility checks.

5. **W2-P05 — Downstream candidates:** Prove predecessors in DAG order using attributable accepted evidence; structural well-formedness and future parallel tracks confer no readiness.

6. **W2-P06 — Five-gap-blocked branches and full plan:** Resolve all five design authority gaps for the full plan, revise affected specifications/contracts and reverify; partial decisions free only the recorded overlapping subsets.

7. **W2-P07 — Separately gated branches:** Assign G1/G2, ratify SF-REQ-056 and fulfill component-specific custody/handoff/installation/operational authority. Resolve split/replan and other pending amendments before invoking those proposed semantics; do not impose them on unrelated bounded work.

8. **W2-P08 — Live replacement/cutover:** Retain existing protections until actual component replacement proof, one-writer migration, active-effect reconciliation and nonduplicating rollback are approved and exercised; local fixtures cannot authorize retirement.

Bootstrap replacement sequencing preserves checkpoint → mailbox; live liveness/observer and waiter handoff → attention retirement; admission replacement plus full sovereignty/one-writer reconciliation → Node retirement. Alias retirement needs installation evidence; Director retirement needs completed or explicitly transferred programme duties. No sandbox or local fixture substitutes for operational proof.

## 5. Factory effectiveness

Eight distinct ledger failure classes have moved to **scoped existing deterministic control**. This count includes bootstrap/evidence tooling and is not eight new production gates built by this programme:

| Lesson | Controlled class | Retained red evidence |
|---|---|---|
| LRN-005 | CUSTODY_IDENTITY_DEFECT | yes |
| LRN-006 | release-admission-record | yes |
| LRN-008 | invocation-success-without-verdict | yes |
| LRN-010 | LIVENESS_GAP | UNKNOWN |
| LRN-011 | judgment-required-retry | yes |
| LRN-012 | effect-recovery-identity | yes |
| LRN-017 | evidence-derivation-consistency | yes |
| LRN-021 | configuration-input-validation | yes |

LRN-010's red evidence is UNKNOWN; do not call all eight proven-red. Nine ALREADY_GRADUATED lessons, eight mechanized lessons, fourteen red-evidenced lessons, seven proposed promotions and eighteen designed obligations are different populations. The packet implements no new runtime promotion.

Deterministic checks now handle exact fields/identities, preserved obligation sets, evidence consistency/UNKNOWN retention, graph cycles/capability reachability, enum/outcome completeness and authority-hold propagation. The twelve existing artifact checkers all passed in the original packet task: eleven built during phases 2–13 plus the pre-existing Phase 0/1 `check_wave1.py`. The R1 repair reruns only the required Wave 1 acceptance check. Wave 1 acceptance (`rtk proxy python3 tools/evidence/check_wave1.py --negative-controls`) passed 1,075 checks with zero failures and 13/13 negative controls killed. Every checker exited 0; raw outputs and invocation details are retained in packet section 20. No checker was modified or historical report regenerated.

Model cognition remains necessary for source meaning, owner fit, acceptance sufficiency, consumer/platform premises, architecture authority, whether a mutation is discriminating, and risk decisions. The design checker passed text with four material defects that independent verification found. Measurable evidence is 26 consumed lessons, specific refusals/red controls and repeatable checker results. Reduced model reasoning, token savings or causal rework reduction are UNKNOWN; 33 historical rejections and repair-induced defects prevent a broad effectiveness claim.

## 6. Orchestration effectiveness

The [coordinator orchestration record](../prework/POSTW1-PACKET-014-orchestration-record.json) is **participant evidence**, not an independent finding. Its task-routing totals describe the 23 tasks before this packet: twelve Codex-primary identities, two coordinator identities, one independent-review identity and eight Founder branches (one decided, seven open). **STATE014-001 — upheld and reconciled:** the corrected record distinguishes the pre-packet population (23 tasks, twelve Codex-primary) from current programme state (24 tasks, thirteen Codex-primary), including this RUNNING packet task. Seven open decisions are unchanged. These are task counts, not dispatch counts; repair and verification rounds add invocations. OpenAI GPT-6 Astra was routed to substantive analysis, reconciliation, design, DAG/BIU authoring and assessments. Anthropic Claude supplied resident historical cross-check and fresh independent design verification. Exact Claude model and complete invocation census are UNKNOWN.

Eight named prework artifacts establish concrete mechanical preparation: candidate/layer enumeration, outcome inventory, split inputs, bootstrap state snapshot, yield, requirement inventory and design inputs. Twelve checkers validate the resulting artifacts. This demonstrates work executable without a model; the participant claim that every phase avoided all rediscovery is not independently established or measured. Deterministic substitution must not turn a shallow parser into authority: missing nesting, Git history and definition forms repeatedly misled the coordinator.

The corrected participant record reports seven dispatched-session disputes, all seven upheld: the original four — ownership versus enforcement conflation; historical persistence of BLOCKED/SPLIT_RECOMMENDED; LRN-008 as successful refusal rather than coercion; and nested dispositions missed in seventeen files. The other three are ORCH014-001, ORCH014-002 and STATE014-001, now reconciled. The accepted ledger/matrix preserve the corrected semantics. The corrected error count is `AMBIGUOUS — corrected`, with eight surface-read errors found: wrong lesson array, weak 'none' effectiveness match, capacity-keyword false positive, current-file-only verdict read, top-level-only envelope read, mistaken VERIFIER reversion, wrong provider-config nesting and heading-only requirement discovery. It additionally lists four logic errors: advancing past REPAIR, empty-queue false completion, self-routing the retirement audit and assigning an unresolved architecture decision to a designer.

**ORCH014-001 — upheld and reconciled:** the record now separates `surface_read_error_count: 8` and `logic_error_count: 4`, with `unique_combined_count: UNKNOWN` because overlap was never assessed. These are found-not-total counts; neither eight nor twelve is exhaustive. **ORCH014-002 — upheld, found-and-repaired:** VERIFY-010 now records `routing.model: null` and provider Claude (fresh session), exact model UNKNOWN. The Director corrected the underlying `route()` defect that assigned the resolved Codex model to the fresh-reviewer tier, recorded as fixed test-first and visible in the local code/test diff. These repairs were made by the Director after the original report, not by this two-file repair. No Founder reconciliation follow-up remains for these three disputes.

Retained repair reports show two Learning Ledger repair rounds, one Gap Trap repair round and two Design Contract repair rounds. Design Verification has three rounds ending VERIFIED. These are five explicitly retained author repair rounds, not a complete programme retry count. Programme state records PASS for completed production phases and PASS_WITH_QUALIFICATIONS for closure review; final design verification is VERIFIED. Coordinator cross-checks are not independent review of its own conduct. This packet's fresh-Claude accuracy check examined 108 figures and returned CORRECTIONS_REQUIRED; this R1 repair addresses its four figure corrections and three framing points without self-approving review closure.

Token usage and cost are **UNKNOWN for every programme dispatch**, including coordinator activity, author/repair/review sessions and this packet. No numeric estimate, zero, provider price comparison or economic ranking is justified. For Wave 2, recommend deterministic inventory/hash/DAG/history checks first; bounded fresh Codex for irreducible technical work; participant Claude for historical location only; independent fresh review for design/authority risks with targeted repair regression checks. Record actual model/provider, invocation identity, budgets, tokens and cost before evaluating routing economics. Escalate on evidence/authority failure, not keyword-based capacity guesses. These are recommendations, not new routing authority.

Disposition: **PARKED_FOR_REQUESTED_REVIEW** on existing `main`, owned by POSTW1-PACKET-014 author. Unique content is this report and the structured packet, both in `/mnt/d/Projects/alienintent` (the worktree, not `/tmp`). No temporary branch/worktree was created. User prohibitions on commit/push/network and review closure prevent publication/landing; next action is independent confirmation of this accuracy repair. Existing input changes are preserved. No live or remote claim is made from local refs.

## 7. Founder action

**APPROVALS REQUIRED:** After the independent accuracy check, approve or revise the proposed Wave 2 scope and bounded execution authorization. This is not blanket release or cutover approval. WO-220101 remains held until AR13-CQ-001, concrete proof binding and fresh Agent-Ready assessment are satisfied.

**DECISIONS REQUIRED:** Seven open records, each with a recommendation; no decision is closed here.

| Decision | Recommended disposition (not enacted) |
|---|---|
| POSTW1-DECIDE-004A | Assign G1/G2 implementation and versioned-serialization owners; preserve assessor authority and raw history. |
| POSTW1-DECIDE-005A | Amend SF-REQ-013 for conserved split/replan; preserve all 69 obligations and integration proof. |
| POSTW1-DECIDE-006A | Formally end Wave 1-only release authority while retaining protection; decide notification, waiter, tunnel, external-module and resident custody; separately authorize narrow PRODUCER reversion. |
| POSTW1-DECIDE-007A | Accept the five R02–R06 amendment directions for authority processing; explicitly assign LRN-022/023. R06 is the same split decision as 005A. |
| POSTW1-DECIDE-008A | Ratify SF-REQ-056 with explicit scope/defaults and host interface; host authority remains separately required. |
| POSTW1-DECIDE-010A | Resolve all five design gaps under their named authorities; treat both 039 gaps together. Preserve initial compilation semantics and hold unapproved edge policy. |
| POSTW1-DECIDE-013A | Resolve first for entry: name authorized allocator and exact retained execution packet/limits/remaining allowance for WO-220101, or explicitly defer it; then reassess. |

**OPTIONAL FOLLOW-UPS:** Request invocation-level economic telemetry and a controlled routing/yield comparison; review the eleven declined promotions when their stated revisit conditions are met. These do not replace mandatory allocation, readiness, authority or operational gates.
