# Wave 1 final retrospective and architecture reconciliation

Authoritative artifact: [wave1-final-retrospective.json](wave1-final-retrospective.json). Task **POSTW1-RETRO-007**. Pending independent coordinator review. Recommendations only; no requirement, Priority, Wave, lifecycle, runtime, or canonical architecture document is changed.

Wave 1 demonstrates bounded continuous execution on real sandbox infrastructure and several effective safety controls, while recurring proof defects, manual bootstrap dependence and incomplete recovery/observability remain. DONE for eleven BIUs is not completion of every linked Product Requirement, production cutover, or proof of economic efficiency.

This phase supplies the evidence-to-owner reconciliation and recommended amendments. It does not enact them. Canonical-document adoption and unresolved Founder decisions remain pending; the broader architecture/requirements adoption exit gate is not claimed satisfied by writing this retrospective.

Source baseline: `712d39f5c70be6fa98e53a68742dde2c341d4666`, branch `main`; Wave 1 terminal implementation: `10cc81620511af56befbb6140504d1991bb02846`. All operational claims below concern retained historical evidence, not current live verification.

## Yield

Copied from the accepted [yield prework](../operations/post-wave1-program/prework/POSTW1-RETRO-007-yield.json), without recounting. No yield figure is disputed.

| Measure | Accepted value |
|---|---:|
| BIUs | 11 |
| Verifier verdicts | 44 |
| Rejections | 33 |
| Execution cycles | 44 |
| First-pass acceptances | 2: PY-09B, PY-10 |
| Founder-exception markers | 9 across 7 BIUs |
| Repair records | 44 |
| Superseded records | 46 |
| Elapsed-to-DONE coverage | 11 of 11 |
| Sum of per-BIU elapsed-to-DONE | 104,007.129 seconds |
| Minimum / maximum elapsed-to-DONE | 3,706.544 / 21,523.43 seconds |
| Token usage | UNKNOWN for all 11 |
| Cost | UNKNOWN for all 11 |

The 33 rejections combine VERIFY failures and REVIEW discoveries: Wave 1 did not separate them. No unique-defect total is derivable. Same-phase retries are excluded from execution cycles. Elapsed-to-DONE is an aggregate of per-BIU intervals, not active compute time or a measured coordinator-delay total.

Per-BIU `test_count_at_landing` values are cumulative snapshots. Their arithmetic sum, 1479, is **not a wave total**. This retrospective makes no wave-wide test-count claim and no economic-efficiency claim.

HYPOTHESIS ONLY: verification-first sequencing or provider substitution may have contributed to PY-09B/PY-10 first-pass acceptance. RAW-100 was not promoted: n=2, provider change confounded with sequencing change; the coordinator asserted and withdrew causality. FACT is limited to both being first-pass accepted. No comparative causal effect or provider ranking is established.

## Learning: reuse, enforcement and limits

The ledger contains 30 lessons. Under the explicit definitions below, 26 were propagated, 8 have a scoped deterministic gate, and 14 have retained red evidence. These sets overlap and must not be added. Nine ledger lessons are ALREADY_GRADUATED; that is a scoped effectiveness disposition, distinct from deterministic enforcement.

**propagated:** Ledger records with FACT-labelled later_consumption (26). Counts documented reuse, correction or analytical consumption, including explicitly limited same-incident use; not 26 effective preventive controls.

**mechanized:** Ledger enforcement_level=DETERMINISTIC_GATE (8), scoped to the exercised control. Includes bootstrap and evidence-analysis gates; not eight fully implemented Product Requirements.

**proven_red:** Ledger proven_red=yes (14), including actual invalid-input refusal and specific mutation batteries. Does not certify a generic gate or every obligation of its owner.

**ungraduated:** The 11 Phase 3 not_promoted candidates, retained verbatim with revisit conditions. This is not a count of proven recurring defects. The seven promotion proposals also remain unimplemented by Phase 3; the populations must not be conflated.

**Propagated IDs:** LRN-001, LRN-002, LRN-003, LRN-004, LRN-005, LRN-006, LRN-007, LRN-008, LRN-009, LRN-010, LRN-011, LRN-012, LRN-013, LRN-014, LRN-015, LRN-016, LRN-017, LRN-018, LRN-019, LRN-020, LRN-021, LRN-022, LRN-024, LRN-025, LRN-026, LRN-028.

**Mechanized IDs:** LRN-005, LRN-006, LRN-008, LRN-010, LRN-011, LRN-012, LRN-017, LRN-021.

**Proven-red IDs:** LRN-001, LRN-002, LRN-004, LRN-005, LRN-006, LRN-008, LRN-011, LRN-012, LRN-014, LRN-015, LRN-016, LRN-017, LRN-021, LRN-026.

The eight mechanized records concern custody/retention, release admission, durable-result refusal, bootstrap liveness, judgment-required retry suppression, effect recovery, evidence consistency and profile validation. Liveness LRN-010 has UNKNOWN red evidence. Mechanization alone is therefore neither a proven-red claim nor a product-wide completion claim. The JSON carries all 30 lesson records with consumption, effectiveness, provenance and uncertainty.

LRN-001/002/003/004 retain repeated proof, composition, sequencing and regression failures despite downstream improvements; their proposed gates are not deployed graduation. Among declines, LRN-013 has three capacity interruptions and LRN-014/025 retain recurring specification/authority-judgment problems. LRN-007 duplicate observations do not establish recurrence, LRN-027 is an unexercised property, and LRN-029/030 are single observed cases. UNKNOWN recurrence remains UNKNOWN.

Phase 3 proposed the following seven promotions. Their blocking/advisory labels are recommendations, not live enforcement or newly assigned Priority/Wave.

| Lesson | Existing owner | Proposed layer | Proposed strength | Historical red |
|---|---|---|---|---|
| LRN-001 | SF-REQ-050 | mutation_gate | BLOCKING | yes |
| LRN-002 | SF-REQ-014 | python_unit_integration | BLOCKING | yes |
| LRN-003 | SF-REQ-049 | evidence_consistency | ADVISORY | UNKNOWN |
| LRN-004 | SF-REQ-049 | evidence_consistency | BLOCKING | yes |
| LRN-010 | SF-REQ-056 | python_unit_integration | ADVISORY | UNKNOWN |
| LRN-016 | SF-REQ-002 | python_unit_integration | BLOCKING | yes |
| LRN-019 | SF-REQ-053 | python_unit_integration | ADVISORY | UNKNOWN |

### Eleven declines retained as findings

**LRN-007 — declined.** One PY-09 incident produced three observations of one verifier outcome and a neighboring no-invocation regression. This establishes identity defects, but not independent recurrence of the same attention-identity failure or later effectiveness; duplicate wake-ups are not three incidents. **Revisit only when:** Retain an independently reproduced later identity failure or a repeatable red replay of both identity equivalence cases, with canonical attention integration and measured duplicate/lost-event effects.

**LRN-009 — declined.** The counter semantics are documented, but the cited runtime defect recurrence is unestablished. Existing evidence_consistency already rejects reconstructed retry increments; a new runtime counter would be implementation work, not graduation of this analytical check. **Revisit only when:** Retain attributable runtime cycle miscounts and red transition/restart controls against a canonical counter; distinguish repeated delivery from re-entry.

**LRN-013 — declined.** Capacity interruptions recur, but provider quota prediction is unsupported and the records show operator-authorized recovery, not a validated automatic routing contract. A generic budget-field reminder would not remove quota diagnosis or authority judgment. **Revisit only when:** An owned routing contract and provider evidence expose a specific deterministic refusal/failover predicate with adverse fixtures that preserve budget, capability and authorization bounds.

**LRN-014 — declined.** The corrected exact-set preflight is already a demonstrated narrow control. The recurring lesson is whether the permission/isolation premise matches the real consumer and platform; rechecking the same mistaken premise would repeat the observed 17/17 false assurance. **Revisit only when:** A specific missing consumer-capability assertion beyond the existing doctor is evidenced and proven red, with independently validated expected permissions; keep general specification correctness in REVIEW.

**LRN-018 — declined.** Semantic duplicate ownership cannot be settled by identifier uniqueness. The ledger shows authority-controlled amendments and retirements, not recurring duplicate-delivery failures of an implemented intake service. **Revisit only when:** Retain repeated idempotency defects under stable proposal identities and an authoritative proposal-to-owner mapping; semantic overlap remains reviewed.

**LRN-020 — declined.** Expiry issues need authority interpretation: the later provider-extension evidence is UNKNOWN and replacement criteria are not satisfied by sandbox success. A date comparison could incorrectly retire a protection or silently ratify use. **Revisit only when:** Capture explicit machine-decidable expiry predicates and replacement evidence with reviewed authority; prove red on a concrete repeated stale-authority case without automatic retirement.

**LRN-025 — declined.** False escalation recurs, but named-artifact existence does not establish scope, authority or adequacy of predecessor services. A universal refusal rule would suppress legitimate escalations and leave the real code-aware reasoning intact. **Revisit only when:** A bounded escalation subtype has an authoritative decidable predicate and real true/false examples; artifact lookup alone is insufficient.

**LRN-027 — declined.** No coordinator replacement exercise is established; an untested checkpoint is not an observed recurring replacement failure. State equality also cannot certify equivalent judgment. **Revisit only when:** Retain a controlled replacement/replay with attributable lost durable context or divergent authorized actions; define the deterministic state boundary separately from judgment.

**LRN-028 — declined.** Preserving residual findings is valuable, but deciding exact acceptance extent and whether evidence supports a broad claim remains semantic. Existing evidence consistency covers scoped propagation; a generic completeness field would add review work without settling proof sufficiency. **Revisit only when:** A repeated concrete mechanical loss of already-classified obligations/residuals escapes existing consistency checks, with a minimal corrupt fixture and authoritative mapping.

**LRN-029 — declined.** One PY-10 adverse run demonstrates unbounded nonterminal retry; recurrence_count is 1 and product proven_red is no. Harness exit 124 is not a demonstrated product budget refusal. Do not graduate a proposed new runtime behavior. **Revisit only when:** Observe or reproduce the class independently and retain an owned durable budget implementation with red exhaustion/restart controls distinct from harness timeout.

**LRN-030 — declined.** One PY-10 process kill exposes volatile read-back; recurrence_count is 1 and proven_red is no. Safe parking already worked. A durable outcome mechanism is future capability work, not established recurring-gate graduation. **Revisit only when:** Retain another attributable outcome-loss case or independent reproduction and an owned durable recovery design with red persistence/correlation controls; ambiguous effects must still park.

Sources: [wave1-learning-ledger.json](../../docs/evidence/wave1-learning-ledger.json); [wave1-gap-trap-promotion-backlog.json](../../docs/evidence/wave1-gap-trap-promotion-backlog.json).

## Methodology: what worked and what remains unproven

All five methods have a bounded observed success and an unproven broader claim. “Worked” below means the named detection, refusal or conservation outcome; it does not mean the method caused higher first-pass yield.

### verification-first

**Observation:** PY-09B corrected two overdetermined checks. PY-10 rehearsal caught redaction damage and lost seeding evidence; mutation work exposed the selection-set blind spot and unbounded drain. PY-09 had violated sequencing despite the contract.

**Assessment:** Specific harnesses exposed defects before final acceptance. That is demonstrated detection, not proof that ordering improved first-pass yield or that a general sequencing gate works. RAW-100 remains hypothesis-only.

Evidence: [wave1-learning-ledger.json#LRN-001](../../docs/evidence/wave1-learning-ledger.json#LRN-001); [wave1-learning-ledger.json#LRN-003](../../docs/evidence/wave1-learning-ledger.json#LRN-003); [PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [PY-10-wave1-live-proof.md#6-verification-harness](../../docs/verification/PY-10-wave1-live-proof.md#6-verification-harness).

### split/decomposition

**Observation:** SPLIT_RECOMMENDED held PY-10; SWF-33 inserted PY-09B under existing transport owners, and PY-10 consumed the accepted transport. Phase 5 maps 69 original obligations with a retained integration parent.

**Assessment:** Worked for this authorized decomposition and preservation of capstone proof. The 69-row mapping is design/reconciliation evidence, not execution of a generalized atomic split/replan operation; SPLIT-G1 remains open. Two acceptances do not establish a split-related yield effect.

Evidence: [wave1-learning-ledger.json#LRN-015](../../docs/evidence/wave1-learning-ledger.json#LRN-015); [wave1-biu-split-replan-design.json](../../docs/evidence/wave1-biu-split-replan-design.json); [2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md).

### Agent-Ready outcome handling

**Observation:** BLOCKED and SPLIT_RECOMMENDED for PY-10 and NEEDS_CLARIFICATION for PY-09B prevented release until prerequisite/Founder resolution and fresh READY. Historical assessments remain in Git; 15 direct objects and 17 MCP envelopes normalize to 31 READY and one NEEDS_CLARIFICATION in current files.

**Assessment:** Worked as a human-governed admission boundary. READY was not release authority and provider failure was not a readiness verdict. No silent coercion is demonstrated. G1 implementation/schema/CLI and G2 serialization ownership prevent claiming exhaustive automated outcome handling; G3 is a retention/discovery inconsistency.

Evidence: [wave1-agent-ready-outcome-matrix.json#dispositions](../../docs/evidence/wave1-agent-ready-outcome-matrix.json#dispositions); [wave1-agent-ready-outcome-matrix.json#coercion_finding](../../docs/evidence/wave1-agent-ready-outcome-matrix.json#coercion_finding); [wave1-agent-ready-outcome-matrix.json#gaps](../../docs/evidence/wave1-agent-ready-outcome-matrix.json#gaps).

### Design Verification

**Observation:** The copied Node permission expectation passed 17/17 while omitting the real consumer requirement. Corrected expectations failed 2/17 before the grant and passed 17/17 afterward. Agent-Ready challenged impossible token-level Project isolation; SWF-34 approved configuration isolation and compensating proof.

**Assessment:** Consumer-aware review and corrected checks worked on these defects. Initial green compliance proved the wrong premise. General design correctness remains judgment-dependent; exact-set checks cannot validate their own expected set. Production digest proof has the independent-verifier read limitation.

Evidence: [wave1-learning-ledger.json#LRN-014](../../docs/evidence/wave1-learning-ledger.json#LRN-014); [wave1-learning-ledger.json#LRN-028](../../docs/evidence/wave1-learning-ledger.json#LRN-028); [py10-preflight-2026-09-21-pre-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json); [py10-preflight-2026-09-21-post-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json).

### REVIEW -> Gap Trap -> VERIFY

**Observation:** Specific adverse controls failed meaningfully: PY-04 accepted battery 23/23, PY-09B 13/13, PY-10 reported 22/22, and evidence consistency 13/13 negative controls. Phase 3 proposed seven promotions and declined eleven of eighteen.

**Assessment:** Worked as specific defect detection and bounded reusable checks. A complete recurring-failure graduation pipeline and measured reduction in reviewer work are unproven. The PY-10 capability mutation timeout exposes retry debt; it is not semantic proof of a product budget refusal. Historical battery totals are not additive unique-guard or defect counts.

Evidence: [wave1-learning-ledger.json#LRN-001](../../docs/evidence/wave1-learning-ledger.json#LRN-001); [wave1-learning-ledger.json#LRN-017](../../docs/evidence/wave1-learning-ledger.json#LRN-017); [wave1-learning-ledger.json#LRN-026](../../docs/evidence/wave1-learning-ledger.json#LRN-026); [wave1-learning-ledger.json#LRN-029](../../docs/evidence/wave1-learning-ledger.json#LRN-029); [wave1-gap-trap-promotion-backlog.json](../../docs/evidence/wave1-gap-trap-promotion-backlog.json).

## Architecture reconciliation

The Founder-resolved Architecture Authority and later binding decisions define the target. The older canonical architecture mission remains a design baseline, not a shipped-capability inventory. FD-01 explicitly distinguishes the target execution owner from the protected Node/Project bootstrap arrangement. No observed workaround becomes canonical merely because it was used.

### identity

**Existing owners:** SF-REQ-007, SF-REQ-009, SF-REQ-016, SF-REQ-053.

**Definition:** Candidate, invocation, attention, execution-cycle and external-effect identities have distinct equivalence and retention rules; roles do not require distinct providers. Authority §§4-5 and SF-REQ-007 require fresh independent candidate retrieval.

**Observation:** PY-04 verdict 9 could not identify its candidate; PY-10 independently retrieved six candidates. PY-09 success-without-verdict was refused. Repeated outcome attention and invocation-free gap identities collided under an attempted repair.

**Verdict:** Custody and result admission worked in scope. Runtime cycle implementation and attention identity effectiveness remain unproven; reconstructed cycle counts are not invocations. Keep persisted identities and role independence.

Evidence: [wave1-learning-ledger.json#LRN-005](../../docs/evidence/wave1-learning-ledger.json#LRN-005); [wave1-learning-ledger.json#LRN-007](../../docs/evidence/wave1-learning-ledger.json#LRN-007); [wave1-learning-ledger.json#LRN-008](../../docs/evidence/wave1-learning-ledger.json#LRN-008); [wave1-learning-ledger.json#LRN-009](../../docs/evidence/wave1-learning-ledger.json#LRN-009); [wave1-learning-ledger.json#LRN-012](../../docs/evidence/wave1-learning-ledger.json#LRN-012); [alienintent-architecture-authority-2026-09-19.md#4-producer-and-verifier-identities](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md#4-producer-and-verifier-identities).

### recovery

**Existing owners:** SF-REQ-008, SF-REQ-056, SWF-29.

**Definition:** Crash recovery reconciles attributable effects, fences ownership and parks ambiguity. Liveness checks must account for pending/completed effects and unresolved judgment.

**Observation:** PY-10 kill parked lost in-memory read-back, continued independent work and resumed after attributable decision. PY-09 showed LIVENESS_SUPPRESSED; fixed early confirmation sampling had produced a false alarm.

**Verdict:** Conservative safety and scoped retry suppression worked; durable outcome recovery and canonical fenced liveness replacement are not demonstrated. Recovery before SWF-29 is not credited to the later rule.

Evidence: [wave1-learning-ledger.json#LRN-010](../../docs/evidence/wave1-learning-ledger.json#LRN-010); [wave1-learning-ledger.json#LRN-011](../../docs/evidence/wave1-learning-ledger.json#LRN-011); [wave1-learning-ledger.json#LRN-012](../../docs/evidence/wave1-learning-ledger.json#LRN-012); [wave1-learning-ledger.json#LRN-030](../../docs/evidence/wave1-learning-ledger.json#LRN-030).

### provider capacity

**Existing owners:** SWF-09, SF-REQ-025, SF-REQ-026, SF-REQ-028.

**Definition:** Authority §§22-23 require bounded spend and capability/quality-grounded routing. Unknown usage is not zero; assessment failure does not confer readiness.

**Observation:** Three ledger capacity interruptions include execution and assessment populations. Operator-authorized failover continued work; ambient credential precedence first returned 401. Later PRODUCER-on-Claude use has no retained extension of the PY-09-only exception.

**Verdict:** Manual recovery worked. Predictive quota admission, automatic authorized failover, provider superiority and economic yield remain unproven. Authentication mode is not hard-budget enforcement. LRN-022 is adjacent to SF-REQ-025, not already canonically owned.

Evidence: [wave1-learning-ledger.json#LRN-013](../../docs/evidence/wave1-learning-ledger.json#LRN-013); [wave1-learning-ledger.json#LRN-020](../../docs/evidence/wave1-learning-ledger.json#LRN-020); [wave1-learning-ledger.json#LRN-022](../../docs/evidence/wave1-learning-ledger.json#LRN-022); [alienintent-architecture-authority-2026-09-19.md#22-cost-governance](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md#22-cost-governance); [wave1-bootstrap-retirement-matrix.json](../../docs/evidence/wave1-bootstrap-retirement-matrix.json).

### observability

**Existing owners:** SF-REQ-029, SF-REQ-030, SF-REQ-034, SF-REQ-053.

**Definition:** Authority §35 separates structured observations from verdicts. Observation, durable attention, machine receipt and human awareness are distinct.

**Observation:** An observer continued recording without activating the coordinator. PY-09 bridge receipt was reported; Windows human receipt is unproven. Terminal provider shapes differ; normalized progress is not established. Evidence consistency protects UNKNOWN.

**Verdict:** Recorded evidence and scoped diagnostic coalescing worked. Provider-neutral progress normalization has an explicit ownership gap (LRN-023); missing progress cannot mean death. Buffering as a stall cause remains a hypothesis.

Evidence: [wave1-learning-ledger.json#LRN-017](../../docs/evidence/wave1-learning-ledger.json#LRN-017); [wave1-learning-ledger.json#LRN-019](../../docs/evidence/wave1-learning-ledger.json#LRN-019); [wave1-learning-ledger.json#LRN-023](../../docs/evidence/wave1-learning-ledger.json#LRN-023); [wave1-learning-ledger.json#LRN-024](../../docs/evidence/wave1-learning-ledger.json#LRN-024); [wave1-learning-ledger.json#LRN-027](../../docs/evidence/wave1-learning-ledger.json#LRN-027); [alienintent-architecture-authority-2026-09-19.md#35-observability](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md#35-observability).

### transport

**Existing owners:** SF-REQ-005, SF-REQ-007, SF-REQ-038.

**Definition:** Authority §3 keeps direct webhook/outbound relay behind a port. SWF-33 assigned live GitHub transport, custody and validation to existing owners.

**Observation:** PY-09B retained 35 bounded live checks and 13 red guards. PY-10 used real GitHub transport/custody and recorded five signed sandbox deliveries. Repository isolation was permission-enforced; Project isolation was configuration-enforced.

**Verdict:** Specified sandbox transport and read-back were exercised. This is not every adapter, live-profile sovereignty, or proof of token-scoped Project isolation. Tunnel retention and Node replacement require their existing gates.

Evidence: [wave1-learning-ledger.json#LRN-014](../../docs/evidence/wave1-learning-ledger.json#LRN-014); [wave1-learning-ledger.json#LRN-015](../../docs/evidence/wave1-learning-ledger.json#LRN-015); [wave1-learning-ledger.json#LRN-028](../../docs/evidence/wave1-learning-ledger.json#LRN-028); [alienintent-architecture-authority-2026-09-19.md#3-transport](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md#3-transport); [PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md).

### Work Management projection

**Existing owners:** SF-REQ-002, SF-REQ-005, SF-REQ-034, FD-01.

**Definition:** FD-01: external provider owns upstream work through READY; explicit release transfers execution authority to AlienIntent. Downstream fields are projections. Node external-Project execution authority is protected bootstrap behavior.

**Observation:** Project DONE and Issue closure diverged for PY-06/PY-07. PY-09B terminal capture lacked four declared native edges. PY-10 used agreeing descriptor/contract edges and projected READY to DONE only at completion.

**Verdict:** The sandbox proved dependency semantics, not native blocked-by alignment or intermediate projection completeness. Preserve the fixed authority boundary; repair projection fidelity under existing owners without importing external DONE into execution truth.

Evidence: [wave1-learning-ledger.json#LRN-016](../../docs/evidence/wave1-learning-ledger.json#LRN-016); [2026-09-19-alienintent-work-management-execution-authority.md](../../docs/decisions/2026-09-19-alienintent-work-management-execution-authority.md); [PY-10-wave1-live-proof.md#7-findings-carried-forward](../../docs/verification/PY-10-wave1-live-proof.md#7-findings-carried-forward).

### lifecycle

**Existing owners:** SF-REQ-009, SF-REQ-013, SF-REQ-016, SF-REQ-022.

**Definition:** Authority §9 defines lifecycle; SF-REQ-009 owns cycle semantics, excluding same-phase retry/failover. Readiness, release, invocation success, verdict, acceptance and operational closure are different facts.

**Observation:** PY-09 four execution cycles included five verifier invocations. PY-10 nonterminal worker outcomes could redispatch indefinitely under a harness wall-clock bound. Phase 5 identifies SPLIT-G1 despite SF-REQ-013 compilation ownership.

**Verdict:** Cycle reconstruction and no-verdict refusal worked. Runtime cycle durability is unproven; the external timeout does not satisfy a product run budget. Split conservation requires explicit owner amendment, not weakened predecessor proof.

Evidence: [wave1-learning-ledger.json#LRN-008](../../docs/evidence/wave1-learning-ledger.json#LRN-008); [wave1-learning-ledger.json#LRN-009](../../docs/evidence/wave1-learning-ledger.json#LRN-009); [wave1-learning-ledger.json#LRN-015](../../docs/evidence/wave1-learning-ledger.json#LRN-015); [wave1-learning-ledger.json#LRN-029](../../docs/evidence/wave1-learning-ledger.json#LRN-029); [wave1-biu-split-replan-design.json#ownership_audit](../../docs/evidence/wave1-biu-split-replan-design.json#ownership_audit).

### control plane

**Existing owners:** SF-REQ-034, SF-REQ-035, SF-REQ-053, SWF-21, SWF-27, SWF-29.

**Definition:** Authority §36 requires normal guarded domain interfaces; §§42-43 retain Node operational authority until sovereignty. Durable state must support bounded coordinator episodes.

**Observation:** Phase 6 audited 17 mechanisms: one expired retirement candidate, nine keep-until-replaced, one reversion recommendation, six decisions. External 18-module custody is incomplete. No coordinator replacement equivalence or live-profile sovereignty is established.

**Verdict:** Retain protection until its exact replacement gate and authority exist. Program mailbox proof is not product attention or handover proof. Formal closure of Wave 1 release authority is not permission to delete admission checks or release Wave 2.

Evidence: [wave1-learning-ledger.json#LRN-019](../../docs/evidence/wave1-learning-ledger.json#LRN-019); [wave1-learning-ledger.json#LRN-020](../../docs/evidence/wave1-learning-ledger.json#LRN-020); [wave1-learning-ledger.json#LRN-025](../../docs/evidence/wave1-learning-ledger.json#LRN-025); [wave1-learning-ledger.json#LRN-026](../../docs/evidence/wave1-learning-ledger.json#LRN-026); [wave1-learning-ledger.json#LRN-027](../../docs/evidence/wave1-learning-ledger.json#LRN-027); [wave1-bootstrap-retirement-matrix.json](../../docs/evidence/wave1-bootstrap-retirement-matrix.json); [alienintent-architecture-authority-2026-09-19.md#43-python-sovereignty](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md#43-python-sovereignty).

## Recommendations: existing owner first

Sixteen recommendations: **5 AMENDMENT, 0 NEW_REQUIREMENT, 11 NO_CHANGE**. NO_CHANGE means no new requirement text is needed for the stated semantics; it does not mean the implementation is complete. All recommendations have `priority_or_wave_invented: false`. Adoption and any scheduling remain Founder decisions. R04/R05 name adjacent amendment targets while preserving the accepted ownership gaps; R06 likewise does not claim that compilation already owns the full split transaction.

### R01 — NO_CHANGE

**Existing owner first:** SF-REQ-007; SF-REQ-016.

**Proposed change/disposition:** Retain exact custody, independent read-back and invocation-correlated verdict admission; no weakening based on provider success or local-copy retention.

**Ownership proof:** The plan explicitly owns durable candidate retrieval in SF-REQ-007 and observation/verdict separation in SF-REQ-016; the demonstrated controls satisfy these scoped semantics.

Evidence: [wave1-learning-ledger.json#LRN-005](../../docs/evidence/wave1-learning-ledger.json#LRN-005); [wave1-learning-ledger.json#LRN-008](../../docs/evidence/wave1-learning-ledger.json#LRN-008); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md).

### R02 — AMENDMENT

**Existing owner first:** SF-REQ-008.

**Proposed change/disposition:** Make durable attributable worker-outcome read-back and its restart proof explicit within crash-safe execution; preserve mandatory parking for absent/ambiguous evidence.

**Ownership proof:** SF-REQ-008 already owns crash/restart state and effect reconciliation. This strengthens proof specificity for an observed in-memory read-back limitation; it does not need a second recovery requirement.

Evidence: [wave1-learning-ledger.json#LRN-012](../../docs/evidence/wave1-learning-ledger.json#LRN-012); [wave1-learning-ledger.json#LRN-030](../../docs/evidence/wave1-learning-ledger.json#LRN-030); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md).

### R03 — AMENDMENT

**Existing owner first:** SF-REQ-022.

**Proposed change/disposition:** Explicitly cover repeated nonterminal worker outcomes with durable run/retry budget exhaustion and restart proof, distinct from per-invocation and harness timeouts.

**Ownership proof:** SF-REQ-022 explicitly owns bounded repair budgets and exhaustion escalation; Authority §§21-22 own finite retries and spend bounds. Clarifying ineligible/rework paths extends this existing boundary without inventing an amount.

Evidence: [wave1-learning-ledger.json#LRN-029](../../docs/evidence/wave1-learning-ledger.json#LRN-029); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

### R04 — AMENDMENT

**Existing owner first:** SF-REQ-025 (adjacent; proposed amendment target only).

**Proposed change/disposition:** Extend provider readiness ownership to isolation of coordinator-tool invocation environments and explicit authentication precedence; require an adverse ambient-credential fixture.

**Ownership proof:** Accepted Phase 2 LRN-022 identifies a real ownership gap: authenticated capability discovery does not own construction of coordinator-tool environments. Authority §32 SecretProvider and §12 sandboxing are adjacent to secret access/containment, not this precedence contract; worker-environment proof does not cover coordinator tooling. Prefer explicit SF-REQ-025 scope amendment over a new requirement; current ownership is not asserted.

Decision: `FOUNDER_RECONCILIATION_DISPOSITION`.

Evidence: [wave1-learning-ledger.json#LRN-022](../../docs/evidence/wave1-learning-ledger.json#LRN-022); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

### R05 — AMENDMENT

**Existing owner first:** SF-REQ-029 (adjacent; proposed amendment target only).

**Proposed change/disposition:** Extend trajectory ownership to provider-neutral started/progress/terminal/capacity normalization, preserving raw provenance and explicit unavailable progress.

**Ownership proof:** Accepted Phase 2 LRN-023 identifies a real ownership gap: trajectory recording does not own normalization. SF-REQ-053 activation and SF-REQ-034 diagnostic presentation/coalescing are neighboring consumers, not owners of the provider observation contract. Authority §35 lists observability surfaces without this contract. An explicit SF-REQ-029 amendment is preferred; no current ownership or buffering cause is presumed.

Decision: `FOUNDER_RECONCILIATION_DISPOSITION`.

Evidence: [wave1-learning-ledger.json#LRN-023](../../docs/evidence/wave1-learning-ledger.json#LRN-023); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

### R06 — AMENDMENT

**Existing owner first:** SF-REQ-013 (current compilation owner; proposed transaction owner).

**Proposed change/disposition:** Adopt the conserved split/replan transaction scope proposed in Phase 5, retaining integration parent, lineage, all 69 mapped obligations, invalidation and recovery conditions.

**Ownership proof:** SF-REQ-013 says only to lower governed requirements into bounded BIUs with explicit satisfaction links and dependency DAGs. It does not specify revision of an existing decomposition or conservation/transaction semantics. SF-REQ-015 checks unresolved decisions, boundaries, missing acceptance/verification, architecture and dependencies, while preserving Agent-Ready authority; checking an input is not authority or an operation to rewrite it. SWF-33 authorizes this particular split, not a general product mechanism. Neither candidate presently owns the complete operation explicitly. Amendment preferred over a new requirement; do not treat compilation ownership as existing complete transaction ownership.

Decision: `POSTW1-DECIDE-005A`.

Evidence: [wave1-biu-split-replan-design.json#ownership_audit](../../docs/evidence/wave1-biu-split-replan-design.json#ownership_audit); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md).

### R07 — NO_CHANGE

**Existing owner first:** SF-REQ-014; SF-REQ-049; SF-REQ-050.

**Proposed change/disposition:** Retain proof-before-widening, preserved obligations and discriminating mutation duties; carry Phase 3 proposals as prospective implementation under existing owners, not deployed gates.

**Ownership proof:** SF-REQ-014 owns prior mechanical obligations; SWF-23 assigns convergent repair to SF-REQ-049; SWF-24 assigns failure-class promotion to SF-REQ-050. The seven proposed gates and three advisory limits do not require new Product Requirements.

Evidence: [wave1-learning-ledger.json#LRN-001](../../docs/evidence/wave1-learning-ledger.json#LRN-001); [wave1-learning-ledger.json#LRN-002](../../docs/evidence/wave1-learning-ledger.json#LRN-002); [wave1-learning-ledger.json#LRN-003](../../docs/evidence/wave1-learning-ledger.json#LRN-003); [wave1-learning-ledger.json#LRN-004](../../docs/evidence/wave1-learning-ledger.json#LRN-004); [wave1-gap-trap-promotion-backlog.json](../../docs/evidence/wave1-gap-trap-promotion-backlog.json).

### R08 — NO_CHANGE

**Existing owner first:** SF-REQ-051.

**Proposed change/disposition:** Keep independent consumer/platform validation of design premises; exact-set checks alone cannot establish specification correctness.

**Ownership proof:** SWF-25 explicitly owns Design Contract and independent Design Verification in SF-REQ-051. The permission/isolation findings are failures within that obligation, not an uncovered new capability.

Evidence: [wave1-learning-ledger.json#LRN-014](../../docs/evidence/wave1-learning-ledger.json#LRN-014); [2026-09-20-design-contract-and-design-verification.md](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md).

### R09 — NO_CHANGE

**Existing owner first:** SF-REQ-002; SF-REQ-005; SF-REQ-034; FD-01.

**Proposed change/disposition:** Preserve lifecycle-authoritative dependency admission and separately visible projection disagreement; carry incomplete intermediate/native-link projection as existing-owner implementation debt.

**Ownership proof:** SF-REQ-002 explicitly says dependency satisfaction is lifecycle-based; FD-01 fixes upstream/execution/projection ownership; SF-REQ-005 owns the port and SF-REQ-034 its operator view. No new authority or dependency representation is selected.

Evidence: [wave1-learning-ledger.json#LRN-016](../../docs/evidence/wave1-learning-ledger.json#LRN-016); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [2026-09-19-alienintent-work-management-execution-authority.md](../../docs/decisions/2026-09-19-alienintent-work-management-execution-authority.md).

### R10 — NO_CHANGE

**Existing owner first:** SF-REQ-009.

**Proposed change/disposition:** Retain SWF-32 cycle semantics and explicit absence of runtime proof; never count same-phase retries as cycles.

**Ownership proof:** SWF-32 already amends SF-REQ-009 with transition, retry, duplicate delivery and reconstruction rules, and explicitly leaves implementation unscheduled. Consumers do not own the counter.

Evidence: [wave1-learning-ledger.json#LRN-009](../../docs/evidence/wave1-learning-ledger.json#LRN-009); [2026-09-21-biu-execution-cycle-counter.md](../../docs/decisions/2026-09-21-biu-execution-cycle-counter.md).

### R11 — NO_CHANGE

**Existing owner first:** SF-REQ-056; SWF-29; SF-REQ-053.

**Proposed change/disposition:** Retain bounded liveness reconciliation, judgment suppression and durable attention; replace bootstrap mechanisms only against the Phase 6 component gates.

**Ownership proof:** SWF-29 separates the bootstrap mechanism from SF-REQ-056 canonical capability; SWF-27/SF-REQ-053 owns persistent attention and restart equivalence. Existing owners already cover these unmet protections.

Evidence: [wave1-learning-ledger.json#LRN-007](../../docs/evidence/wave1-learning-ledger.json#LRN-007); [wave1-learning-ledger.json#LRN-010](../../docs/evidence/wave1-learning-ledger.json#LRN-010); [wave1-learning-ledger.json#LRN-011](../../docs/evidence/wave1-learning-ledger.json#LRN-011); [wave1-learning-ledger.json#LRN-019](../../docs/evidence/wave1-learning-ledger.json#LRN-019); [wave1-learning-ledger.json#LRN-027](../../docs/evidence/wave1-learning-ledger.json#LRN-027); [wave1-bootstrap-retirement-matrix.json](../../docs/evidence/wave1-bootstrap-retirement-matrix.json).

### R12 — NO_CHANGE

**Existing owner first:** SWF-21; SWF-27; Architecture Authority §§42-43.

**Proposed change/disposition:** Carry six bootstrap decisions and the separately authorized PRODUCER reversion forward; retain Node, compatibility and protections until their exact gates are satisfied.

**Ownership proof:** Phase 6 names each component authority and expiry. Sovereignty and live-profile replacement are already defined; this recommendation neither extends a temporary grant nor orders live retirement.

Decision: `POSTW1-DECIDE-006A`.

Evidence: [wave1-bootstrap-retirement-matrix.json](../../docs/evidence/wave1-bootstrap-retirement-matrix.json); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

### R13 — NO_CHANGE

**Existing owner first:** SF-REQ-015; SWF-21 (handling/custody only).

**Proposed change/disposition:** Preserve four-outcome handling, immutable reassessment lineage and non-READY release refusal; carry G1/G2 ownership assignment forward without inventing an assessment schema owner.

**Ownership proof:** SF-REQ-015 preserves Agent-Ready readiness authority; SWF-21 and SWF-33/34 govern evidenced release and reassessment. These do not own the missing implementation/schema/CLI or canonical serialization; Phase 4 expressly records G1/G2. No requirement change is proposed before the existing Founder assignment.

Decision: `POSTW1-DECIDE-004A`.

Evidence: [wave1-agent-ready-outcome-matrix.json](../../docs/evidence/wave1-agent-ready-outcome-matrix.json); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md).

### R14 — NO_CHANGE

**Existing owner first:** SF-REQ-025; SF-REQ-026; SF-REQ-028; SWF-09.

**Proposed change/disposition:** Retain capability, quality, budget and authorization predicates for any future provider routing; make no quota prediction, economic ranking or automatic-failover claim from these runs.

**Ownership proof:** The existing owners cover capability discovery, quality-constrained routing and attributable economics. Wave 1 operator substitution is not a new routing specification or measured cost comparison.

Evidence: [wave1-learning-ledger.json#LRN-013](../../docs/evidence/wave1-learning-ledger.json#LRN-013); [wave1-learning-ledger.json#LRN-020](../../docs/evidence/wave1-learning-ledger.json#LRN-020); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

### R15 — NO_CHANGE

**Existing owner first:** SF-REQ-030; SF-REQ-017; SF-REQ-055.

**Proposed change/disposition:** Retain source-backed evidence, UNKNOWN telemetry, residual acceptance limits and amendment-first intake; preserve the eleven declines as findings.

**Ownership proof:** SF-REQ-030 explicitly owns consistency and UNKNOWN negative controls, SF-REQ-017 owns claim-to-evidence traceability, and SF-REQ-055 owns proposal intake without duplicate canonical ownership.

Evidence: [wave1-learning-ledger.json#LRN-017](../../docs/evidence/wave1-learning-ledger.json#LRN-017); [wave1-learning-ledger.json#LRN-018](../../docs/evidence/wave1-learning-ledger.json#LRN-018); [wave1-learning-ledger.json#LRN-028](../../docs/evidence/wave1-learning-ledger.json#LRN-028); [alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md).

### R16 — NO_CHANGE

**Existing owner first:** SF-REQ-005; SF-REQ-007; SF-REQ-038; Architecture Authority §3.

**Proposed change/disposition:** Retain the transport port, scoped custody and validation obligations; record sandbox proof extents without upgrading them to live-profile sovereignty or changing isolation policy.

**Ownership proof:** SWF-33 already binds the live transport split to these owners; Authority §3 owns adapter separation. No uncovered transport semantics or new requirement is established by this retrospective.

Evidence: [wave1-learning-ledger.json#LRN-014](../../docs/evidence/wave1-learning-ledger.json#LRN-014); [wave1-learning-ledger.json#LRN-015](../../docs/evidence/wave1-learning-ledger.json#LRN-015); [wave1-learning-ledger.json#LRN-028](../../docs/evidence/wave1-learning-ledger.json#LRN-028); [2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md); [alienintent-architecture-authority-2026-09-19.md](../../docs/architecture/alienintent-architecture-authority-2026-09-19.md).

## Unresolved Founder decisions

There are **three existing registered decisions**, carried forward rather than duplicated, plus **one unregistered Phase 7 reconciliation question**. The terminal count is four decision entries, not four registered program tasks.

**POSTW1-DECIDE-004A** — Founder: assign an owner for the Agent-Ready implementation/schema/CLI (G1) and the canonical serialization contract (G2)

Scope: non-blocking: carried to the Phase 14 packet, does not halt phases 5-13.

Status: FOUNDER_DECISION_REQUIRED; carried forward unchanged, not newly registered.

**POSTW1-DECIDE-005A** — Founder: amend SF-REQ-013 to own the split/replan transaction (SPLIT-G1)

Scope: non-blocking: carried to the Phase 14 packet; phases 6-13 do not require it.

Status: FOUNDER_DECISION_REQUIRED; carried forward unchanged, not newly registered.

**POSTW1-DECIDE-006A** — Founder: 6 NEEDS_DECISION mechanisms plus the PRODUCER-on-Claude reversion

Scope: non-blocking: no phase 7-13 work depends on these; carried to the Phase 14 packet; SWF-21 release authority; Windows notification; session-bound attention waiter; sandbox ingress tunnel; eighteen external bootstrap modules; resident coordinator multi-BIU tenure; PRODUCER-on-Claude reversion requires a separately authorized operational change.

Status: FOUNDER_DECISION_REQUIRED; carried forward unchanged, not newly registered.

**FOUNDER_RECONCILIATION_DISPOSITION** — Accept, reject or revise the Phase 7 amendment recommendations, including explicit ownership of LRN-022 and LRN-023; assign any needed Priority/Wave only by Founder decision.

Scope: R02-R05 scope/proof amendments; R06 remains exclusively POSTW1-DECIDE-005A; R04/R05 preserve the two Phase 2 gaps, not two newly discovered gaps; No scheduling or canonical amendment is enacted; no new program task is created.

Status: RECOMMENDED_DECISION_FOR_FOUNDER; unregistered question, not an additional program-state task.

## Provenance, review and validation

The JSON provenance records source SHA-256 hashes, Git identity, baseline, the five pre-existing task-input changes and the authorized two-file scope. Input changes were classified by content: the program-state diff adds this RUNNING task; the prompt, yield prework, checker and tests match its contract. They were preserved. No network, commit, push, live operation, Phase 8 work or prior-phase rewrite was performed.

`rtk proxy python3 tools/evidence/check_retrospective.py docs/evidence/wave1-final-retrospective.json` — exit 0; PASS; 16 recommendations, six contract checks, zero failures.

`rtk proxy python3 tools/evidence/check_wave1.py --negative-controls` — exit 0; PASS; 1075 checks, zero failures, 13/13 negative controls killed.

These check artifact structure and accepted evidence consistency. They do not adjudicate semantic ownership, independently review the retrospective, or establish runtime effectiveness.

Disposition: **PARKED_FOR_REQUESTED_REVIEW**, two uncommitted deliverables in the existing repository worktree on `main`; no temporary branch or worktree created. The user explicitly prohibited commit/push/network. Next action is independent coordinator review, followed only by separately authorized adoption/publication. This author does not approve its own recommendations or mark the broader reconciliation/adoption gate complete.

DISPUTED: NONE.
