# Reconciliation delta

**INFERENCE — All four requirements need bounded re-SPECIFY, followed by corresponding design-contract revision.** SF-REQ-013 directly contradicts its old scope; the other three omit amended obligations or retain superseded authority assumptions. **S0’s bounded substrate extent need not expand.**

**FACT —** The supplied requirement text, eight specification/contract objects, and S0 object match the current repository artifacts. No files were modified and no provider inference was run.

Citation shorthand below denotes exact file plus JSON pointer; appended paths extend that pointer:

| Shorthand | Artifact and pointer |
|---|---|
| `S11`, `S13`, `S15`, `S39` | [wave2-specified-requirements.json](/mnt/d/Projects/alienintent/docs/evidence/wave2-specified-requirements.json), respectively `#/candidates/0`, `/2`, `/4`, `/6` |
| `C11`, `C13`, `C15`, `C39` | [wave2-design-contracts.json](/mnt/d/Projects/alienintent/docs/evidence/wave2-design-contracts.json), respectively `#/contracts/0`, `/2`, `/4`, `/6` |
| `D` | [wave2-dependency-dag.json](/mnt/d/Projects/alienintent/docs/evidence/wave2-dependency-dag.json) |
| `B` | [wave2-candidate-bius.json](/mnt/d/Projects/alienintent/docs/evidence/wave2-candidate-bius.json) |

All table **status judgments are INFERENCE**, based on the **FACT** content identified in the evidence column. “Satisfies” means textual coverage, not implemented or executed proof. “Omits” means absent from the inspected specification/contract object.

## SF-REQ-011

**FACT — Amended authority:** [factory plan:920](/mnt/d/Projects/alienintent/docs/decisions/alienintent-software-factory-plan.md:920); Requirements / Planning ownership and source neutrality: [architecture authority:661](/mnt/d/Projects/alienintent/docs/architecture/alienintent-architecture-authority-2026-09-19.md:661).

| amended obligation | spec status | contract status | evidence |
|---|---|---|---|
| Intake through `RequirementSource`, distinct from `WorkManagement`; requirement information versus work-state representation/projection; one vendor may serve both through separate adapters | **Partially satisfies:** source independence, but no named port or two-role distinction | **Partially satisfies:** names `RequirementSource`; does not establish the distinct roles/separate-adapter rule | `S11/intent`, `/scope`; `C11/ports/0`, `/adapters`, `/composition` |
| Supported source kinds: GitHub Issues/Projects, Jira, Linear, Azure DevOps, GitLab, local files, structured product documents, native proposals, imported prototypes/artifacts | **Partially satisfies:** source-format independence and three historical definition forms | **Partially satisfies:** local files/Git blobs and three prose parsers; broader source-kind support is unspecified | `S11/scope/1`, `/acceptance_criteria/1`; `C11/adapters/0` |
| Adapters translate Source Records and provenance into a provider-neutral internal requirements model; core uses that model | **Partially satisfies:** independent representation, without explicit Source Record boundary | **Partially satisfies:** domain inventory values and vendor-neutral architecture, but the source port returns documents and parser/model translation is not fully specified against the new Source Record contract | `S11/intent`; `C11/ports/0`, `/ports/1`, `/adapters/0`, `/architecture_fitness`; [hexagonal contracts:25](/mnt/d/Projects/alienintent/docs/architecture/pre-python-gate/hexagonal-contracts.md:25) |
| Each Requirement retains external source, external identity, external revision, source link, ingestion timestamp, authority status, synchronization/projection semantics | **Partially satisfies:** generic provenance, revisions and authority; no complete seven-field obligation | **Partially satisfies:** manifest source identity/revision/path/locator and definition authority reference; no complete per-Requirement provenance record, notably ingestion time and synchronization/projection semantics | `S11/scope/0`, `/acceptance_criteria/1`; `C11/ports/0`, `/state`, `/identities`, `/evidence` |
| Jira Epic ≠ Requirement; GitHub Issue ≠ BIU; Linear Project ≠ Wave; external vocabulary is not domain vocabulary | **Partially satisfies:** source independence and prohibition on approving proposals implicitly; named non-identities omitted | **Partially satisfies:** vendor-neutral values and exact internal identity rules; named external/domain distinctions omitted | `S11/intent`, `/non_goals/0`; `C11/architecture_fitness`, `/identities`, `/ubiquitous_language`; [UL:80](/mnt/d/Projects/alienintent/docs/architecture/alienintent-ubiquitous-language-v0.1.md:80) |
| Replace a source or work-management provider without rewriting Requirements / Planning | **Partially satisfies:** same requirement through two formats preserves identity and meaning; not source/provider replacement | **Partially satisfies:** ports and adapters support separation, but no replacement/conformance proof | `S11/acceptance_criteria/1`; `C11/ports`, `/adapters`, `/architecture_fitness`, `/acceptance_design_trace/1` |
| Explicit Requirements / Planning semantic owner | **Omits** that context assignment | **Partially satisfies:** assigns `context_assembly`; its relationship to the newly established context is unresolved design work, not automatically a forbidden package choice | `S11/scope`; `C11/bounded_context`, `/domain_owner`; [FD-02 refinement:27](/mnt/d/Projects/alienintent/docs/architecture/pre-python-gate/founder-decisions.md:27) |

**INFERENCE — Minimum revision:** retain the existing inventory, conflict, identity and historical-corpus acceptance work. Add specification obligations and acceptance coverage for the two ports’ roles, source kinds, complete provenance, non-identities and substitution. Revise the source/value/adapter contracts and context ownership accordingly. The amendment does not itself require implementing every referenced intake product or changing their waves.

## SF-REQ-013

**FACT — Amended authority:** [factory plan:932–934](/mnt/d/Projects/alienintent/docs/decisions/alienintent-software-factory-plan.md:932).

| amended obligation | spec status | contract status | evidence |
|---|---|---|---|
| SF-REQ-013 owns authority-bearing split/replan in Requirements / Planning; SPLIT-G1 is resolved | **Contradicts:** expressly excludes general split/replan and calls amendment unapproved | **Contradicts:** `INITIAL_ONLY`, `OUT_OF_SCOPE_REPLAN`, pending-amendment refusal | `S13/selection_reason`, `/non_goals/0`, `/authority_gaps/0`, `/acceptance_criteria/4`; `C13/state`, `/transitions/3`, `/non_goals/specified/0`, `/design_decisions/1` |
| Agent Ready supplies split judgment/recommended semantic boundaries and mutates nothing; AlienIntent owns mutation; SF-REQ-015 lints results and preserves assessment authority | **Partially satisfies:** readiness dependency exists, but split responsibility is excluded | **Partially satisfies:** outputs go to SF-REQ-015; split judgment/mutation handoff omitted | `S13/dependencies/5`, `/non_goals/0`; `C13/ports/2`, `/composition`, `/non_goals` |
| Freeze original obligations; map 100% of requirements, acceptance, verification and evidence obligations to resulting units or retained Integration Parent | **Partially satisfies:** initial coverage and evidence duties exist; frozen split set and Integration Parent omitted | **Partially satisfies:** initial coverage checks exist; split conservation and retained parent absent | `S13/scope/1`, `/acceptance_criteria/0`, `/acceptance_criteria/1`; `C13/state`, `/evidence`, `/deterministic_enforcement_opportunities/0` |
| Splitting cannot lose, invent or weaken authorized intent or proof | **Partially satisfies:** initial compilation guards loss/invention and authority bounds, but no split invariant | **Partially satisfies:** initial completeness/bounds guards, no conserved split transaction | `S13/failure_modes`, `/security_constraints`; `C13/failure_modes/2`, `/security`, `/non_goals/specified/0` |
| Deterministic dependency identity rewrites; no judgment redirection, cycles or weakened predicates | **Partially satisfies:** validates cycles/endpoints/predicates and authoritative dependency meaning; rewrite semantics omitted | **Partially satisfies:** graph validation and dependency authority exist; deterministic rewrite transaction omitted | `S13/acceptance_criteria/2`, `/operational_constraints/1`; `C13/deterministic_enforcement_opportunities/0`, `/1`, `/transitions/3` |
| Record split lineage | **Omits:** source/output traceability is not split lineage | **Omits:** prior compilation candidate is not parent/child split lineage | `S13/operational_constraints/0`, `/observability_evidence`; `C13/state`, `/recovery` |
| Invalidate stale assessments, materialize resulting candidate BIUs, resubmit **each** for assessment | **Contradicts** executable split scope; resulting-unit sequence omitted | **Contradicts** approved-decomposition mutation; generic reassessment only partially covers the obligation | `S13/acceptance_criteria/4`; `C13/transitions/3`, `/recovery`, `/composition` |
| Identity allocation follows a stated grammar; never derives from sort order | **Omits** explicit grammar and ordering invariant | **Partially satisfies:** forbids sorting-derived identity, but leaves new identity assignment behind the old allocation gap | `S13/operational_constraints`; `C13/identities` |
| Compiler itself derives initial decomposition; external hand-authored allocation is not mandatory; R1-GAP-013-ALLOCATION resolved | **Partially satisfies:** initial compilation is intended, but derivation responsibility is not explicit | **Contradicts** current gate: correctly rejects mandatory external allocation, yet still prohibits successful compilation pending the now-settled decision | `S13/intent`, `/scope/0`; `C13/design_decisions/0`, `/ports/0`, `/transitions/0`, `/authority_gap_refs/0` |
| Compile-time term is **obligation mapping**, distinct from execution-time Allocation | **Partially satisfies:** expresses mapping but retains allocation wording | **Contradicts:** defines compile-time `Allocation` and uses “derived allocation” throughout | `S13/scope/1`, `/acceptance_criteria/1`; `C13/ubiquitous_language/Allocation`, `/state`, `/identities` |
| Phase 5 split design is the candidate design; SWF-33 is precedent | **Partially satisfies:** cites Phase 5 solely for its former ownership gap | **Omits** adoption/reconciliation of that candidate design and precedent | `S13/provenance/2`; `C13/design_decisions`, `/source_specification`; [Phase 5 design](/mnt/d/Projects/alienintent/docs/evidence/wave1-biu-split-replan-design.json)`#/ownership_audit`, `#/identity_grammar`, `#/destination_bindings/retained_integration_parent` |

**INFERENCE — Minimum revision:** revise the title/scope, exclusion, authority-gap assertions and AC-05; specify the complete conserved split/replan transaction and compiler-derived initial decomposition. Preserve existing coverage, graph, authority and budget protections. Reconcile the Phase 5 candidate design, identity grammar, lineage, invalidation and reassessment contracts; replace compile-time “Allocation” terminology. Do not treat designation as candidate design as proof that every Phase 5 mechanism is already approved.

## SF-REQ-015

**FACT — Amended authority:** [factory plan:946–950](/mnt/d/Projects/alienintent/docs/decisions/alienintent-software-factory-plan.md:946); product ownership and public-interface boundary: [architecture authority:650](/mnt/d/Projects/alienintent/docs/architecture/alienintent-architecture-authority-2026-09-19.md:650).

| amended obligation | spec status | contract status | evidence |
|---|---|---|---|
| Agent Ready owns semantics, schema, CLI and local MCP; SF-REQ-015 owns integration only | **Contradicts** the continued assertion that ownership is unassigned, although assessment authority is preserved | **Contradicts** G1/G2 owner-assignment holds; authority is now assigned to the independent product | `S15/selection_reason`, `/non_goals/0`, `/dependencies/4`, `/authority_gaps/0`; `C15/domain_owner`, `/ports/2`, `/adapters/1`, `/source_specification/authority_conditions/0` |
| Requirements / Planning obtains assessment through `ReadinessAssessment.assess(candidate_work_unit)` with CLI/MCP adapters | **Partially satisfies:** consumer/MCP handling exists; named invocation port, CLI adapter and context ownership omitted | **Partially satisfies:** injected `AssessmentAuthority` is analogous, but wrong named contract, unbound production adapter and `execution_coordination` ownership remain | `S15/scope/2`, `/acceptance_criteria/3`; `C15/bounded_context`, `/ports/1`, `/ports/2`, `/adapters`, `/composition` |
| Domain knows no executable location, subprocess syntax, transport or private package details; no imported private implementation, copied rubric or duplicate decision logic | **Partially satisfies:** preserves authority and consumer-only scope; explicit prohibitions omitted | **Partially satisfies:** injected boundary, vendor-neutral architecture and no replacement engine; complete explicit product boundary omitted | `S15/intent`, `/authority_gaps/0`; `C15/ports/2`, `/adapters/1`, `/architecture_fitness` |
| Exactly one of READY/CLARIFY/SPLIT/HOLD; assessment result ≠ lifecycle state; BLOCKED is not an Agent Ready disposition | **Contradicts** exhaustiveness: calls the four outcomes “not a claimed exhaustive external schema”; otherwise terminology mostly repaired | **Partially satisfies:** four semantic outcomes and rejection of unknown/conflicting results exist; explicit disposition/lifecycle distinction needs pinning | `S15/scope/1`, `/operational_constraints/0`; `C15/ubiquitous_language/Disposition`, `/design_decisions/0`, `/transitions/1` |
| READY gives eligibility for separate release gates, never release itself | **Satisfies** | **Satisfies** | `S15/acceptance_criteria/1`, `/non_goals/1`; `C15/transitions/1`, `/composition` |
| CLARIFY resolves only material owner questions through SF-REQ-035, then reassesses | **Partially satisfies:** attributable answer and generic reassessment; materiality and decision-authority route omitted | **Partially satisfies:** attributed-answer hold and generic reassessment; same missing route/boundary | `S15/acceptance_criteria/1`, `/2`; `C15/transitions/1`, `/3` |
| SPLIT invokes SF-REQ-013 transaction, then reassesses each result | **Partially satisfies:** stops at “authorized planning decision” | **Partially satisfies:** stops at “planning-decision hold”; no transaction/result reassessment handoff | `S15/acceptance_criteria/1`, `/non_goals/1`; `C15/transitions/1`, `/composition` |
| HOLD requires prerequisite completion and reassessment; old disposition never rewritten | **Satisfies** | **Satisfies** | `S15/acceptance_criteria/1`, `/2`; `C15/transitions/3`, `/state` |
| Timeout, malformed/missing result and provider failure are execution failures, not dispositions or READY | **Satisfies** | **Satisfies:** `AttemptFailure` is separate from semantic assessment | `S15/acceptance_criteria/3`; `C15/ports/1`, `/transitions/2`, `/failure_modes/3` |
| Historical bootstrap assessments retain their own vocabulary and are not Agent Ready assessments | **Partially satisfies:** repair note identifies bootstrap vocabulary, but AC-05 mixes historical BLOCKED with canonical SPLIT | **Satisfies** textual classification: evidence explicitly says historical bootstrap-assessor sequence | `S15/acceptance_criteria/4`, `/terminology_repair_2026_09_22`; `C15/evidence`, `/terminology_repair_2026_09_22` |
| Readiness Assessment is raw product assessment plus provenance; producer identity must be established, not inferred from compatible shape | **Partially satisfies:** raw output, input and provider/invocation identity retained; product/version contract incomplete | **Partially satisfies:** raw bytes, IDs and fingerprints retained; Agent Ready/contract versions and actual-product binding need completion | `S15/observability_evidence/0`; `C15/state`, `/evidence`, `/deterministic_enforcement_opportunities/1`; [hexagonal contracts:26](/mnt/d/Projects/alienintent/docs/architecture/pre-python-gate/hexagonal-contracts.md:26), [Reuse Before Build:727](/mnt/d/Projects/alienintent/docs/architecture/alienintent-architecture-authority-2026-09-19.md:727) |

**INFERENCE — Minimum revision:** update the specification’s ownership assumptions, exact outcome set, public-port boundary, CLARIFY/SPLIT processing and historical fixture wording. Preserve immutability, execution-failure handling and separate release gates. Replace obsolete owner-assignment gates with contracts for actual supported interfaces, configured producer identity and applicable versions; settle integration ownership without duplicating Agent Ready.

## SF-REQ-039

**FACT — Amended authority:** [factory plan:1103–1108](/mnt/d/Projects/alienintent/docs/decisions/alienintent-software-factory-plan.md:1103).

| amended obligation | spec status | contract status | evidence |
|---|---|---|---|
| Name is Deterministic Test Worker; identity, priority and Wave remain unchanged; avoid names implying LLM imitation | **Contradicts** current title; identity remains correct | **Contradicts** current title; identity remains correct | `S39/title`, `/requirement_id`, `/priority_or_wave_invented`; `C39/title`, `/requirement_id` |
| Deterministic implementation of the **same production worker-facing port/protocol**, using a test adapter | **Partially satisfies:** canonical/current interfaces required, but exact shared-port parity not explicit | **Satisfies:** reuses `WorkerProvider.start/read_back/cancel`, compatible `WorkerOutcome`, canonical effect identities | `S39/dependencies/0`, `/operational_constraints/1`; `C39/ports/0`, `/ports/2`, `/identities`, `/design_decisions/3` |
| Exercise real control plane, lifecycle, recovery, identity, evidence and faults with scripted valid/invalid behavior | **Satisfies** broad intent, with scenario gaps below | **Satisfies** broad architecture, with scenario gaps below | `S39/scope`, `/acceptance_criteria`; `C39/ports`, `/transitions`, `/recovery`, `/evidence` |
| No model inference, credentials or token spend; does not simulate frontier-model intelligence | **Partially satisfies:** credentials/spend and zero provider calls explicit; intelligence non-identity omitted | **Partially satisfies:** deterministic scripts and no provider/network access; intelligence non-identity omitted | `S39/intent`, `/acceptance_criteria/0`, `/non_goals/1`; `C39/security`, `/observability`, `/ubiquitous_language/ScriptedWorker` |
| No test-specific lifecycle shortcuts; scripts cannot mark work done | **Satisfies** | **Satisfies:** scenario runner cannot set stage; existing success-collapse limitation is disclosed, not claimed as full proof | `S39/non_goals/0`, `/acceptance_criteria/1`; `C39/ports/1`, `/composition`, `/design_decisions/5` |
| Valid outcome and normal end-to-end success | **Satisfies** specified target | **Satisfies** conditional design target, not current implementation readiness | `S39/acceptance_criteria/0`; `C39/transitions/0`, `/acceptance_design_trace/0`, `/authority_gap_refs` |
| Missing outcome | **Satisfies** | **Satisfies** | `S39/acceptance_criteria/2`; `C39/failure_modes/1`, `/ports/2` |
| Malformed outcome | **Omits** explicit scenario | **Omits** explicit scenario; missing result is not malformed result | `S39/scope/1`, `/acceptance_criteria`; `C39/failure_modes`, `/deterministic_enforcement_opportunities/0` |
| Delayed outcome | **Omits** explicit scenario | **Partially satisfies:** scheduled events/injected clock support it, but no delayed-outcome acceptance case | `S39/scope/1`; `C39/ubiquitous_language/Scenario`, `/state`, `/concurrency` |
| Duplicate outcome | **Partially satisfies:** duplicate trigger/event, not explicitly duplicate worker output | **Partially satisfies:** duplicate/restart proof, without explicit duplicate-outcome case | `S39/acceptance_criteria/3`; `C39/acceptance_design_trace/3`, `/deterministic_enforcement_opportunities/0` |
| Wrong identity/correlation | **Partially satisfies:** wrong candidate identity; worker correlation not explicit | **Satisfies** conditional target: exact candidate identity and missing/miscorrelated role outcome refusal | `S39/acceptance_criteria/2`; `C39/ports/2`, `/identities`, `/design_decisions/5` |
| Provider/capacity failure | **Omits** simulated failure scenario | **Omits** explicit scenario; forbidding actual provider access does not cover simulated capacity failure | `S39/scope/1`, `/acceptance_criteria`; `C39/failure_modes`, `/deterministic_enforcement_opportunities/0` |
| Crash before output; progress then crash | **Partially satisfies:** restart exists, but neither crash case is explicit | **Partially satisfies:** process kills at intent boundaries and durable journal; neither required worker-output sequence is pinned | `S39/acceptance_criteria/3`; `C39/recovery`, `/state` |
| Restart/resume | **Satisfies** | **Satisfies** | `S39/acceptance_criteria/3`; `C39/persistence`, `/recovery` |
| Repair cycle; verification rejection | **Satisfies** | **Satisfies** conditional target | `S39/acceptance_criteria/1`; `C39/transitions/1`, `/design_decisions/4` |
| Human-decision condition | **Satisfies** | **Satisfies** | `S39/acceptance_criteria/4`; `C39/transitions/2`, `/acceptance_design_trace/4` |
| Split recommendation where appropriate | **Omits** | **Omits** | `S39/scope/1`, `/acceptance_criteria`; `C39/transitions`, `/deterministic_enforcement_opportunities/0` |

**INFERENCE — Minimum revision:** update the title, explicitly state protocol parity and the intelligence non-identity, and complete the scenario/acceptance matrix. Preserve current-interface substrate work and conditional later lifecycle work. The abstract term `WorkerPort` does **not** by itself require renaming the existing `WorkerProvider` code interface.

## Answers 1–5

**1. Re-SPECIFY versus contract-only revision**

**INFERENCE — All four need re-SPECIFY. None is contract-only or no-revision.**

| Requirement | Minimum specification revision | Minimum corresponding contract revision |
|---|---|---|
| 011 | Source-role separation, source-kind coverage, complete provenance, non-identities and substitution acceptance | Source Record/value boundary, provenance schema, adapter separation, context mapping and conformance probes |
| 013 | Replace initial-only exclusion with conserved split/replan; explicit compiler derivation, identity constraints and obligation mapping | Transaction, lineage, integration parent, deterministic rewrites, invalidation/reassessment; remove settled-gap holds |
| 015 | Correct owner/gates, exact vocabulary, public-interface boundary, CLARIFY/SPLIT responses and historical fixture | `ReadinessAssessment` adapters, actual producer/version provenance, context responsibility and revised processing |
| 039 | Rename and complete shared-protocol/non-intelligence/scenario obligations | Scenario matrix, correlated outcome probes and updated traces, retaining conditional kernel boundaries |

**FACT —** Shared design text also remains stale: `wave2-design-contracts.json#/shared_contracts/amendments` excludes general replan; `/shared_contracts/authority_boundaries` still treats G1/G2 and compiler derivation as unresolved.

**INFERENCE —** Those shared assertions and affected acceptance traces need corresponding revision and independent verification. The recorded `wave2-design-verification.json#/final_disposition = VERIFIED` verified the earlier repaired design; it does not establish conformance to these amendments. Its `/reverification_r2/verifier_note` expressly distinguishes design verification from implementation readiness.

**2. Effect on WO-220101 / S0 / FX-S0**

**INFERENCE — No semantic expansion of S0’s extent, acceptance criterion or FX-S0 is required by these deltas. Its existing architecture constraints already express the relevant worker-parity and no-shortcut obligations.**

**FACT —** `B#/bius/0/scope`, `/acceptance_criteria/0`, `/architecture_constraints`, and `/verification_obligations/proof_fixture` bound S0 to:

- Real temporary SQLite, disposable local Git publication/retrieval and a fresh verifier worktree.
- Local work-management/provider transports, injected clock/IDs and durable scripted-worker journal.
- Absent credentials, enforced network denial and zero provider calls.
- Existing kernel unchanged, disclosed success-collapse limitation and no scripted lifecycle transitions.

`D#/nodes/0` has no dependencies; `D#/proof_fixtures/0` is FX-S0 and remains `PLANNED_NOT_EXECUTED`.

**INFERENCE —** The expanded SF-REQ-039 scenario matrix must be allocated and traced during revision; it must not silently become S0’s entire acceptance burden. S0 explicitly does not own the whole requirement: `B#/bius/0/scope/boundary` and `/fixed_decisions/0/applicability`. Multi-role routing, real outcome emission and complete lifecycle proof remain in K1–K3/O: `D#/nodes/20` through `/nodes/23`.

**INFERENCE —** Refresh S0’s applicable design baseline/references and terminology after revision. That is artifact reconciliation, not permission to add a role router, an Agent Ready substitute or split/replan execution to S0. Its entry-point status also does not waive its recorded budget, assessment, custody or release conditions: `B#/bius/0/budget`, `/assessment_status`, `/release_policy`.

**3. Effect on DAG structure beyond the four requirements’ nodes**

**INFERENCE — No particular new node, removed node or changed dependency outside their scopes is compelled by the amended text. However, “no DAG impact” would be too strong.**

**FACT —** Existing nodes encode superseded assumptions:

- U7/U8 reject replanning or retain compiler-allocation authority holds: `D#/nodes/9`, `/nodes/10`.
- U9/U10 retain G1/G2 owner-assignment assumptions: `D#/nodes/11`, `/nodes/12`.
- A’s completion predicate still says the allocation hold blocks completion: `D#/nodes/13/completion_predicate`.
- Inherited allocation/assessment gates appear downstream, including B3, B6, R6 and R7: `D#/nodes/30`, `/nodes/33`, `/nodes/41`, `/nodes/42`.

**INFERENCE —** These completion predicates, capability descriptions, fixtures and propagated gate annotations require reconciliation. That is not automatically a topology change. The split/replan transaction and assessment feedback loop also require revised capability/proof coverage; a runtime reassessment loop does not imply a cyclic implementation DAG.

**UNKNOWN —** The final revised topology is not established by the existing artifacts. It follows from the revised, verified contracts. Existing unrelated edge-authority, lifecycle-owner, monitor-host and operational-release gates must not be removed merely because compiler derivation and Agent Ready ownership are now settled.

**4. Remaining terminology contamination**

**FACT — Remaining defects in the four objects:**

| Location | Finding |
|---|---|
| `S15/acceptance_criteria/4/criterion` | Historical PY-10 replay says **“BLOCKED then SPLIT then … READY.”** This mixes the bootstrap vocabulary with canonical Agent Ready vocabulary. |
| `S39/title` | Still **“Fake-agent / offline factory proof.”** |
| `C39/title` | Same obsolete title. |

**INFERENCE —** Repair AC-05 by identifying the bootstrap producer and preserving the historical `BLOCKED → SPLIT_RECOMMENDED → READY` sequence, as `C15/evidence` already does. Do not normalize historical records into purported Agent Ready assessments.

**FACT — Not contaminations:**

- `C15/evidence` explicitly labels its legacy sequence historical bootstrap-assessor evidence.
- `S15/terminology_repair_2026_09_22` and `C15/terminology_repair_2026_09_22` mention old vocabulary as provenance.
- No `Gap Trap` product-term occurrence was found in the four specification objects or four contract objects.
- `C39/state`’s “fake clock” and `/concurrency`’s warning against a fake store are not obsolete worker-product names.

**FACT —** The canonicalization report explicitly acknowledges unrevised SF-REQ-039 titles in its §6 F8; those were retained knowingly, not rendered invalid by identifier. A separate remaining collision is compile-time `Allocation` in `C13/ubiquitous_language/Allocation`, discussed above.

**5. Genuine Founder decisions versus engineering revision**

**INFERENCE — No new Founder decision is necessary to reconcile these four amendments.** Existing authority answers ownership of source intake, split/replan, compiler derivation, Agent Ready integration and deterministic worker semantics.

Checked authority includes:

- Factory-plan amendments at lines 920, 932–934, 946–950 and 1103–1108.
- Architecture Authority A1–A3, A5, A7, A9–A11 and amendment (b).
- UL definitions for Source Record, Requirement, Split Transaction, Integration Parent and Readiness Assessment.
- Hexagonal port rows and FD-02’s explicit delegation of `context_assembly` mapping to Design Contract work.

**FACT — Pre-existing unresolved decisions remain distinct.** The [canonicalization report](/mnt/d/Projects/alienintent/docs/architecture/2026-09-22-founder-decisions-canonicalization-report.md), §6 F7 and §7, says the SF-REQ-039 orchestration/real-outcome and module-edge authority gaps remain open. `C39/authority_gap_refs` and `D#/nodes/20`–`/nodes/22` preserve them. The report also flags Founder confirmation of the FD-01 interpretation in F1.

**INFERENCE —** None should be silently closed by this reconciliation. Conversely, none makes the already-decided port names, disposition vocabulary, split ownership or scenario coverage a fresh Founder question. The report’s F1 confirmation follow-up does not erase the explicit canonical A2 boundary.

## Evidence I could not obtain

**FACT —** All user-specified inputs were readable. The actual DAG was obtained at `docs/evidence/wave2-dependency-dag.json`; an initial lookup under `wave2-technical-dag.json` found no file.

**UNKNOWN —** This read-only artifact analysis does not establish runtime adapter behavior, executed scenario coverage, current Agent Ready interface compatibility or fresh verification of revised artifacts. No such execution was performed. The final post-revision DAG and acceptance allocation do not yet follow from the inspected artifacts alone.

RECON: RE_SPECIFY_REQUIRED