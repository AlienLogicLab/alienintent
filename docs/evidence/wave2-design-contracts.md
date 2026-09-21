# Wave 2 Design Contracts — POSTW1-DESIGN-009

The [JSON contract](wave2-design-contracts.json) is authoritative. These are ten design candidates for independent Phase 10 review, not verified designs or permission to implement. Phase 8 specifications remain requirements authority. All work is local on baseline `3ea566f211a13aa6ec36c2bb8f9a4703d31a1f02`; no implementation, BIU decomposition, publication or live operation occurred.

## Architecture decisions

All ten contracts bind to existing Python contexts. `context_assembly` owns upstream representations and admission, `evidence_learning` owns typed proof/evidence, `execution_coordination` owns readiness consumption and canonical effects, `control_plane` owns episodes and attention, and `composition` owns offline proof wiring. No new bounded context is proposed. Node remains bootstrap authority; this design does not claim Python sovereignty.

The chosen persistence is the existing SQLite operational store plus a separate immutable local evidence repository. A new service/database would duplicate existing recovery machinery; a hand-edited canonical requirements register would duplicate source authority. Requirement import remains a derived view. Initial compilation lowers an explicitly supplied authorized allocation; it does not become a general planner or invent decomposition.

New internal port payloads are frozen, versioned domain values. External Agent-Ready serialization and existing worker contracts are not redefined. Explicit holds preserve missing authority instead of letting implementers invent it. `deferred_to_implementation` is empty in every contract; permitted local freedom is limited to helper naming/decomposition and ordering that preserves canonical outputs and effects.

## Composition and consumer boundaries

`composition/evidence_profile.py` is the proposed evidence repository constructor. `composition/upstream_profile.py` wires inventory, ambiguity inspection, proof planning, design applicability, compilation and readiness consumption. `composition/control_plane_profile.py` wires persistent attention, episode context and liveness around the existing coordinator and store. Existing `composition/offline_profile.py` assembles the same applications with local external-system adapters. These proposed names are design targets, not claims that the modules already exist.

Proof planning uses candidate design/premise inputs; independent design verification pins that exact design/proof pair before compilation. This avoids recursive auto-approval. Attention is available independently of ratification-dependent liveness recovery. Definitions and evidence share neutral references, not mutually recursive application services.

Every composed operation needs a real temporary-store success probe and a typed-failure probe under Phase 3 LRN-002. Import checks alone cannot establish wiring. The offline path must remove the current coordinator shortcut that advances a producer success through verification and closure. Distinct role invocations, candidate retrieval, trusted verifier evidence and actual closure receipts must drive the existing kernel transitions.

## Durable state, identity and concurrency

Operational aggregates use existing profile-scoped SQLite APIs and compare-and-swap versions. Evidence objects are canonical-content-addressed immutable files outside the repository. The adapter durably installs and verifies a file before publishing its operational reference; a crash may leave an unreferenced object, never an admitted reference to unwritten evidence. Required history is retained. Definition, Observation and Verdict remain different types and namespaces.

Input identity is a stable source requirement/decision identity plus a semantic revision, not its formatting. Every downstream applicability record pins its exact source, design, proof and authority revisions. Assessment attempts and episodes receive a persisted identity before invocation; histories are not edited to match new outcomes.

The current store fences reservation release but its ordinary effect methods do not accept the fence. The JSON therefore fixes a narrow `FencedOperationalStore` extension: atomically validate version vectors and reservations when committing/claiming/confirming effects, using the existing tables. Read-then-write across unrelated aggregates is insufficient. The consumer must also fence/dedupe the side effect; timeouts never grant unfenced takeover. Ambiguous sent effects stay parked until correlated readback or authorized resolution.

## Contract index

| Requirement | Existing context | Material decision |
|---|---|---|
| SF-REQ-011 | `context_assembly` | Derived, versioned inventory; source definitions retain authority. |
| SF-REQ-012 | `context_assembly` | Source/revision-bound questions with local holds and attributed answers. |
| SF-REQ-013 | `context_assembly` | Initial lowering of authorized allocation into existing BiuContract only. |
| SF-REQ-014 | `evidence_learning` | Pinned proof predicates, feasible premises and qualified negative controls. |
| SF-REQ-015 | `execution_coordination` | Immutable assessment consumer semantics; G1/G2 implementation ownership held. |
| SF-REQ-016 | `evidence_learning` | Typed Definition / Observation / Verdict with explicit admission. |
| SF-REQ-039 | `composition` | Real kernel and adapters composed with scripted external outcomes. |
| SF-REQ-051 | `context_assembly` | Mechanical-first, independently reviewed, revision-bound design applicability. |
| SF-REQ-053 | `control_plane` | Bounded epochs, reconstructible context and durable attention. |
| SF-REQ-056 | `execution_coordination` | Ratification-dependent, fenced missing-effect recovery; judgment suppresses relaunch. |

## SF-REQ-011 — Requirements IR

Requirements IR domain in context_assembly; source decision issuers retain normative ownership.

InventorySnapshot: schema_version, source_manifest_digest, definitions indexed by (requirement_id, revision), references, conflicts, unresolved IDs, retired/superseded IDs, dependency edges, BIU satisfaction-link references, prior_snapshot. Each definition has typed SF-REQ-016 role and authority reference.

**Ports and wiring.** RequirementSource.read(manifest) -> tuple[SourceDocument | SourceUnavailable]; manifest fixes repository/source identity, revision, path, digest, locator and access label. RequirementInventory.assemble(documents, authority_records) -> InventorySnapshot; resolve(id, revision) -> Definition | Conflict | Unresolved. Inputs/outputs are immutable context_assembly domain values. EvidenceRepository stores snapshot and source manifest; OperationalStore holds current snapshot pointer by expected version. Proposed composition/upstream_profile.py constructs source adapters, EvidenceRepository, inventory application and SQLite-backed pointer repository; control_plane CLI exposes the application. SF-REQ-012/013 consume its immutable snapshot, not source adapters.

**State changes and identity.** PINNED_INPUT -> ASSEMBLED when every readable source is classified; unreadable sources remain UNVERIFIED in a partial snapshot. Conflicting effective definitions -> CONFLICT for that ID; undefined mention -> UNRESOLVED; approved unambiguous definition -> ELIGIBLE_FOR_PREPARATION. Retirement is preserved, not ID deletion. A changed semantic or authority revision publishes a new snapshot and marks dependent design/compilation/readiness references stale; old satisfaction observations stay historical. Requirement identity is the supplied SF-REQ ID scoped to the source project. Revision digest uses canonical JSON of semantic fields and authority revision, excluding formatting/locator aliases. Equivalent formats with the same authority revision merge provenance into one revision; genuinely distinct decisions do not collapse. Snapshot identity hashes sorted source manifest and revision keys.

**Failure and recovery.** Heading-only parser omits prose definitions: refuse fixture acceptance. Two incompatible effective definitions: preserve both sources and block only that ID. Source missing/digest mismatch: UNVERIFIED; do not reuse a cached definition as confirmed current. Retired ID reuse: conflict requiring source authority resolution. Reassemble from the pinned manifest; compare snapshot digest. Repoint only by CAS. A partial or conflicted snapshot can support inspection but cannot supply compilable authorization for affected IDs.

**Operator and evidence.** Proposed upstream inventory show/export accepts a pinned manifest, returns JSON plus derived text, and names exact blocking IDs; it never edits sources or Issues. Manifest, per-form extraction ledger, exact source locators and digests, conflicts, revision graph, retirement links and requirement/BIU links; retain the historical 56 referenced / 53 defined fixture independently of the newly authored 056 revision.

**Fixed choices.** Compilation accepts only exact unambiguous authorized revisions, never the inventory status alone. No requirements-authoring or planning LLM is introduced: this is import/projection under the selected factory-plan SF-REQ-011.

**Deterministic enforcement.**

- `011-inventory` in `python_unit_integration`: All three definition forms yield baseline 56 references/53 definitions, one 050, retired 054 and unresolved 048/052/056; format aliases retain identity. Proven-red obligation: Disable either prose parser and require count/identity assertion failure; introduce conflicting definitions and require no effective definition.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-012 — Requirements ambiguity detection

Ambiguity application owns findings; existing Founder/decision authority alone resolves product meaning.

InspectionReport records required-field presence, contradictions already evidenced by source records, finding IDs, source spans, required decision actor, affected requirement/dependent references, and OPEN/RESOLVED/STALE history.

**Ports and wiring.** AmbiguityInspection.inspect(inventory_revision, supplied_semantic_findings) -> InspectionReport; resolve(finding_id, DecisionRecord, expected_version) -> Resolution | Hold. DecisionResolution port validates actor, authority scope, source revision and decision reference through the existing control_plane DecisionInbox/DecisionAdmission path; it does not mint approvals. composition/upstream_profile.py wires Inventory -> AmbiguityInspection -> DecisionResolution adapter -> existing DecisionInbox; inject the same store/profile and EvidenceRepository. Compilation receives InspectionReport, never a boolean manufactured by the CLI.

**State changes and identity.** Mechanical missing intent/scope/authority/acceptance/dependency meaning creates OPEN finding and branch-local hold. Authorized answer at matching revision appends RESOLVED only for its finding; mismatched answer stays evidence but does not clear it. Changed relevant input makes prior resolution STALE; material ambiguity discovered independently reopens the affected preparation hold. Finding identity is SHA-256(project, requirement revision, rule code, sorted source locators); semantic findings additionally include immutable reviewer finding reference. Resolution identity hashes finding, decision revision and actor.

**Failure and recovery.** Unattributed answer -> AUTHORITY_HOLD. Stale answer -> REVISION_HOLD. Incomplete inspection -> UNVERIFIED, not complete. No decision channel -> durable OPEN finding; unrelated requirements remain inspectable. Replay mechanical inspection idempotently; reattach resolutions only by exact revision and authority match. Resuming preparation is a new validated operation and launches no worker.

**Operator and evidence.** Proposed upstream questions list/show and resolve commands; resolve requires actor, authority ref, finding ID, input revision and expected version. Existing Decision Inbox remains decision authority. Finding, source span, question, missing decision, answer reference/actor/revision, affected work and retained prior status.

**Fixed choices.** Mechanical completeness is not exhaustive natural-language ambiguity detection. Independent semantic review may add findings but may not silently rewrite intent.

**Deterministic enforcement.**

- `012-local-holds` in `python_unit_integration`: Each missing-field fixture creates a source-bound local hold; unrelated complete input remains eligible; only matching attributed answer resolves. Proven-red obligation: Remove revision or authority matching, inject stale/unattributed answer, require hold assertion failure.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-013 — Requirements to BIU compilation: initial decomposition

Initial compilation application lowers a supplied authorized allocation into execution_coordination BiuContract; it does not choose product decomposition.

Compilation candidate records input digest, allocation revision, per-unit BiuContract content_digest, obligation coverage, edge/predicate set, validation report, prior candidate and INITIAL_ONLY mode.

**Ports and wiring.** InitialCompilation.compile(inventory, inspection, verified_design, proof_plan, allocation, authority_limits) -> CompilationCandidate | CompilationHold. Allocation input fields: stable unit_key, authorized BIU identity, obligation IDs with scope extents, baseline/repository refs, fixed decisions, capabilities, budgets, dependency edges with predicates, custody/closure/release/escalation duties. Missing allocation meaning is a planning hold, never guessed. Output contains execution_coordination.domain.contract.BiuContract canonical payloads, exact requirement/design/obligation revisions, DAG and coverage manifest. SF-REQ-015 alone consumes it for lint/assessment. composition/upstream_profile.py injects 011 inventory, 012 report, 051 applicability and 014 proof plan into InitialCompilation; it passes candidate to 015 lint only. execution_coordination retains release and lifecycle ownership.

**State changes and identity.** PINNED -> VALIDATED_PROPOSAL only after complete coverage, passing current independent design verification, resolved questions and valid DAG. Missing field/edge/authority or incompatible fixed decision -> HELD with no assessed/released state. Existing approved decomposition identity -> OUT_OF_SCOPE_REPLAN; no replacement or mutation. Revised still-unapproved input generates distinct candidate revision. Planning authority supplies stable unit_key and BIU identity; compiler never allocates Issues. Same normalized input tuple yields same candidate digest and BiuContract content_digest. Changed source/design/allocation yields a distinct candidate digest; identities never imply satisfaction.

**Failure and recovery.** Cycle -> report concrete cycle edges. Missing endpoint/predicate -> refuse that graph. Unmapped obligation or widened budget/capability -> reject candidate admission. No approved verified design -> design hold. Approved decomposition rewrite -> pending-amendment boundary. Regenerate the same proposal from immutable input; reconcile partial artifact writes by digest before updating pointer. Reassess changed proposals. Never modify approved BIUs during recovery.

**Operator and evidence.** Proposed upstream compile --inputs <manifest> produces a local proposal/coverage report. It has no Issue creation, status mutation or launch operation. Coverage maps every acceptance/proof obligation to explicit unit extents; DAG validation and bounds comparison retained beside exact contract payloads and source refs.

**Fixed choices.** No new planner competes with upstream Spec Kit/authorized planning. Allocation is a required authoritative input; inability to supply it returns to PLAN. SF-REQ-013 pending split/replan amendment (POSTW1-DECIDE-005A/-007A) is expressly excluded, not a dependency of initial compilation.

**Deterministic enforcement.**

- `013-graph-coverage` in `python_unit_integration`: BiuContract validation plus total obligation coverage and deterministic DAG check precede proposal admission. Proven-red obligation: Drop an obligation, edge endpoint or fixed decision independently; each named refusal must fire.

- `013-dependency-authority` in `python_unit_integration`: Reuse dependency-authority promotion at actual contract/admission boundary; open DONE predecessor remains satisfied; closed nonterminal predecessor does not. Reuses Phase 3 LRN-016 (blocking). Proven-red obligation: Mutate to trust Issue closure or omit a declared edge and fail the targeted eligibility assertion.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-014 — Mechanical verification obligations before implementation

ProofObligation domain owns predicate/evidence plans; reviewers own judgment predicates and premise feasibility.

ProofPlan contains stable requirement AC/obligation IDs, predicate kind, input fixture, expected result, observable endpoint, execution command reference, evidence schema, named guard/mutation, platform-premise references, reviewer role for judgment, and preserved prior/replacement obligations.

**Ports and wiring.** ProofPlanning.derive(requirement_revisions, verified_design, approved_predicate_mapping) -> ProofPlan | InfeasibleProof. ProofEvidence.record(obligation_ref, candidate_ref, fixture_digest, invocation, expected, observed, exit_code) -> ObservationRef. PremiseEvidence port reads pinned consumer/platform capability evidence from installation doctor evidence; no credential probe is implicit in plan derivation. composition/upstream_profile.py wires ProofPlanning to typed 016 EvidenceRepository and 051 premise/applicability inputs before 013 compilation. Existing verification runners consume the plan; no second test runner service.

**State changes and identity.** DRAFT -> FEASIBLE_PLAN only when every AC maps to mechanical or judgment obligation and premise evidence is applicable. Mechanical observations -> evaluation candidate; only authorized verdict admission yields proven. Repair appends candidate-bound replay and explicit authorized supersession; missing proof remains a hold. Infeasible premise returns to source authority. Obligation identity uses requirement ID plus supplied AC ID and stable predicate key; revision hashes predicate/expected inputs. Evidence identity adds candidate digest, fixture digest and invocation, never test filename alone.

**Failure and recovery.** Circular oracle derived only from implementation -> refuse plan. Unapplied mutation, timeout or unrelated exception -> not a qualified kill. Unachievable credential-denial premise -> infeasible proof, not waiver. Dropped/skipped prior obligation -> repair evidence failure. Re-run preserved probes against the new candidate; retain all original evidence. Plan correction requires authoritative predicate revision plus replacement proof; infrastructure failure leaves outcome UNVERIFIED.

**Operator and evidence.** Proposed upstream proof show/check exposes predicate mapping and feasibility failures. Human-judgment items name authority and inspection inputs; no generic green aggregate hides them. Per obligation retain controlled input, expected/actual result, exit code, candidate and harness digests, mutation application count, targeted assertion, restored run; judgment carries actor, input refs and decision.

**Fixed choices.** For platform isolation pin four observables: positive target access; configured profile/resource scoping; rejected out-of-scope application request; unchanged outside-state readback. Do not require impossible platform credential denial. Proof plans are derived before implementation; semantic predicate mappings are authority-reviewed input, not inferred from passing source code.

**Deterministic enforcement.**

- `014-discrimination` in `mutation_gate`: Reuse approved obligation/guard qualified intact-red-restored battery; constant assertions and untriggered guards are refused. Reuses Phase 3 LRN-001 (blocking). Proven-red obligation: Show unconditional success, zero-application and overdetermined fixtures fail battery evaluation.

- `014-composition` in `python_unit_integration`: Reuse named CLI/composition reachability probes with real temporary SQLite, required operation and typed failure postconditions. Reuses Phase 3 LRN-002 (blocking). Proven-red obligation: Disconnect the approved caller while domain tests remain green; composed assertion must fail.

- `014-proof-order` in `evidence_consistency`: Reuse advisory attributable harness/red ancestry diagnostics, never infer widening from timestamps. Reuses Phase 3 LRN-003 (advisory). Proven-red obligation: Out-of-order/missing-path evidence produces named advisory diagnostic, ordered control is clean.

- `014-repair-preservation` in `evidence_consistency`: Reuse stable prior-obligation replay and authorized supersession comparison. Reuses Phase 3 LRN-004 (blocking). Proven-red obligation: Drop, skip or fail prior B proof; reject each unless authorized replacement and passing replacement proof exist.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-015 — BIU lint/readiness and Agent-Ready process hardening

Readiness consumer owns lint/applicability/hold handling. Agent-Ready remains assessment authority; G1/G2 ownership is not assigned by this design.

Immutable AssessmentAttempt includes attempt ID, raw digest, authority/provider/invocation IDs, input fingerprint, predecessor assessment ref, observed disposition or failure, and lint report. Current applicability is a separate versioned pointer, never an edit to an old assessment.

**Ports and wiring.** ReadinessAdmission.lint(candidate, design_applicability, proof_plan, dependency_snapshot) -> LintReport. AssessmentConsumer.observe(raw_artifact, attempt_metadata, recognized_shape) -> SemanticAssessment | AttemptFailure; consume(assessment, current_input_fingerprint) -> ReadinessEligibility | Hold. This is an internal consumer contract, not a new Agent-Ready wire schema. AssessmentAuthority is an injected boundary accepting a pinned assessment request and returning raw bytes plus invocation metadata; transport/schema implementation is blocked on POSTW1-DECIDE-004A G1/G2 assignment. composition/upstream_profile.py wires lint and retained-evidence consumer into readiness admission. Live profile composition must fail closed when AssessmentAuthority is unbound. FactoryCoordinator release consumes applicable evidence through existing admission; it never creates READY.

**State changes and identity.** Lint failure -> HOLD without invoking assessment. READY plus matching inputs -> ELIGIBLE_FOR_SEPARATE_RELEASE_CHECKS; BLOCKED -> prerequisite hold; NEEDS_CLARIFICATION -> attributed-answer hold; SPLIT_RECOMMENDED -> planning-decision hold. Timeout/provider error/no terminal result/unknown or conflicting payload -> ATTEMPT_FAILURE and hold. Material input change invalidates applicability; fresh reassessment links predecessor. Clearing a blocker does not rewrite its outcome. Input fingerprint hashes BiuContract digest, exact baseline, governing decisions, prerequisites and verified design refs. Attempt UUID is assigned and persisted before invocation; replay retains it; a new authorized assessment uses a new UUID and predecessor link.

**Failure and recovery.** MCP error or conflicting direct/text/structured semantics -> attempt failure. No configured assessment contract or ownership -> hold. READY from stale revision -> inapplicable. Zero exit without semantic result -> failure, not readiness. Recover attempt from immutable raw evidence and original metadata. Unknown invocation completion stays held pending readback or separately authorized fresh attempt within existing budget. Historical PY-10 assessment Git blobs remain retrievable by revision.

**Operator and evidence.** Proposed upstream readiness show/lint/observe surfaces attempt lineage and four handling outcomes. Assessment invocation/schema migration stays unavailable until G1/G2 decisions; release remains existing control-plane authority. Raw envelope, parsed observation, all supplied disposition values, input fingerprint, failure reason, predecessor and independent release record; historical sequence BLOCKED -> SPLIT_RECOMMENDED -> fresh READY retained without coercion claim.

**Fixed choices.** Known MCP parsing: isError=true is failure; collect structuredContent disposition and parseable JSON text-content dispositions. Require at least one recognized terminal value and agreement among every supplied value. Unknown/malformed/conflicting purported result is failure. Preserve wrappers. This fixes intended consumer semantics only. No external versioned serialization, implementation maintainer or CLI is invented; implementation/migration of that boundary requires G1/G2 authority.

**Deterministic enforcement.**

- `015-envelope-applicability` in `python_unit_integration`: Equivalent retained direct and known MCP shapes have identical consumer handling; all non-READY/failure/stale cases hold. Proven-red obligation: Use top-level-only parsing, trust exit zero or overwrite prior outcome; corresponding fixture must fail.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-016 — Definition / Observation / Verdict separation

Evidence domain owns typed provenance and linkage. execution_coordination/domain/verdict.py retains execution acceptance policy.

Immutable schema_version=1 record envelope: kind, project/profile, logical ID, revision, source refs, authority refs where applicable, payload, access label, preceding/superseded refs. Operational applicability/hold pointers are separate from the evidence body.

**Ports and wiring.** EvidenceRepository.put(record) -> EvidenceRef; get(ref, access_scope) -> typed record; records use a discriminated Definition/Observation/Verdict union. EvidenceAdmission.validate(record, authority_snapshot) -> Admissible | Rejected. Definition requires issuer/ref; Observation requires method, input refs, observed value and uncertainty; Verdict requires definition refs, observation refs, evaluator identity/authority, policy revision and outcome. ExecutionVerdict bridge passes only validated definition/observation values to existing evaluate_verdict; generic evidence records cannot directly transition lifecycle. Proposed composition/evidence_profile.py builds one EvidenceRepository and access policy per profile; upstream_profile and existing offline_profile receive it. Execution acceptance bridge injects existing evaluate_verdict, never a competing policy.

**State changes and identity.** New record -> structurally validated -> authority/link validated -> admissible typed record. Observation conflict appends competing record and marks impacted applicability held; never overwrites a definition. Verdict with mismatched revision or missing evidence remains UNVERIFIED/refused at acceptance. Authorized supersession appends links. EvidenceRef uses SHA-256 of canonical envelope without self-digest. Logical IDs persist across revisions; source observations retain original invocation/event identity. No role conversion by changing a label on the same digest.

**Failure and recovery.** Observation submitted as Definition without normative authority -> reject. Missing artifact/hash mismatch -> UNVERIFIED and no PASS. Unknown numeric observation -> null plus reason, never zero. Invalid evaluator/source attribution -> verdict refusal. Validate object digest on read; rehydrate operational pointers from retained objects and receipt history. Missing evidence requires recovery from exact pinned source or fresh observation, never reconstruction of a measurement by inference.

**Operator and evidence.** Proposed evidence show/trace/export prints role and provenance chain explicitly; status never collapses observation into verdict. Retain role, exact definition/evidence/policy links, observations in source sequence, conflicts, rejection reasons and evaluator authorization.

**Fixed choices.** JSON scalar types and explicit null/uncertainty distinguish unavailable measurements from zero. No learning promotion or RAI wiring; definitions cannot be authored by evidence ingestion.

**Deterministic enforcement.**

- `016-role-boundary` in `python_unit_integration`: An observed test pass and worker success claim cannot produce authorized PASS alone; revision and evaluator links required. Proven-red obligation: Remove kind/authority/revision validation individually; injected role promotion or stale evidence must fail acceptance assertion.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-039 — Fake-agent / offline factory proof

Offline proof composition assembles the real execution_coordination kernel; scripts own external outcomes only.

Scenario manifest includes authorized BiuContract, exact expected transitions, ordered events, scripted outcome per role/attempt, fake clock and seed. Durable fixture state contains real operational store, local Work Management receipts and worker outcome journal.

**Ports and wiring.** Reuse WorkManagement, WorkerProvider, SourceControl, WorkspaceManager and OperationalStore ports. Scripted WorkerProvider.start/read_back/cancel retains outcome by invocation ID. ScenarioRunner.run(scenario_manifest, injected_clock, profile) -> ordered observations/effect receipts and terminal/hold snapshot. It may deliver inputs but cannot set lifecycle stage. Proposed OutcomeEvidencePort.get(correlation_id) -> immutable RoleOutcomeRecord | Missing. RoleOutcomeRecord fields: role, invocation ID, attempt, exact contract/candidate refs, findings, observation refs, outcome kind, terminal flag, and closure receipts. WorkerOutcome stays compatible; it is insufficient alone for role-specific evidence. The application validates the sidecar before transition; scripted and real local worker adapters supply it through the same port. OfflineProfile owns scenario adapter construction and passes them into FactoryCoordinator and invocation runtime. Present FactoryCoordinator._completed_for_outcome collapses success through verify/review/accept/close: the target path must instead consume separate role outcomes and actual closure receipts using existing transition/evaluate_verdict. ScenarioRunner cannot reproduce that shortcut.

**State changes and identity.** Seed authorized contract -> normal release admission -> producer candidate publication/readback -> VERIFY -> independent scripted verifier result -> REVIEW/ACCEPT policy -> required closure -> DONE. Verifier rejection follows canonical rework transition with findings; subsequent producer uses a distinct authorized attempt. Missing result, authority, custody or judgment-blocked outcome produces existing hold/attention, never a runner-forced transition. Scenario digest plus fixed seed determines fixture identity; actual role-specific invocation IDs remain distinct. Effect identities are the same canonical identities as production, not test-only dedupe keys. Comparison normalizes only declared incidental paths/times, never correlation or authority.

**Failure and recovery.** Network/provider access attempted -> test failure. Script exits zero without result/candidate -> hold. Wrong/unpublished candidate -> custody refusal. Missing fresh verifier or script directly changes stage -> scenario invalid. Kill only the disposable fixture process at named before/after-intent boundaries, reopen the real store and worker journal, and compare authorized action/lifecycle/effect sets. Unknown external effects remain parked.

**Operator and evidence.** Proposed offline scenario <manifest> command returns nonzero for assertion/harness failure and leaves evidence path. Existing production commands are not driven during tests. Scenario manifest, substituted-boundary list, ordered domain transitions, actual worker invocations, candidate branch/SHA and retrieved identity, effect/outcome readbacks, restart comparison and zero-provider-call counter.

**Fixed choices.** Implement the required role-by-role orchestration in execution_coordination application when authorized; retain existing domain lifecycle semantics and port signatures. WorkerInvocation correlation identifies role/attempt through a stored invocation record. Closure records only actions actually performed/read back by local adapters; never populate all required_closure_actions merely because producer succeeded. Offline tests exercise the production orchestration path through composition, not a second mocked lifecycle. A composed role router resolves PRODUCER/VERIFIER/CLOSURE from the durable invocation record keyed by correlation_id and injects the role-specific worker implementation. Existing WorkerProvider signatures stay intact; verifier output must reference retrieved candidate and independent invocation. Missing RoleOutcomeRecord holds even when WorkerOutcome.kind is success. On verifier rejection, persist finding refs and invoke existing transition(action=rework) at the current lifecycle version; enforce remaining authorized attempts/budget before producer allocation. REVIEW evaluates exactly required trusted evidence through evaluate_verdict. ACCEPT performs each required closure action and consumes its receipt; no synthesized closure evidence.

**Deterministic enforcement.**

- `039-composed-lifecycle` in `python_unit_integration`: Reuse LRN-002 composed-path promotion for OfflineProfile with actual store/adapters and fresh verifier; cover success, rejection, result/custody gaps, duplicate/restart, judgment hold. Reuses Phase 3 LRN-002 (blocking). Proven-red obligation: Disconnect verifier invocation or custody readback while unit tests stay green; targeted end-to-end assertion must fail.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-051 — Design Contract and Design Verification

DesignAdmission owns contract completeness and applicability; independent architecture reviewer owns Design Verification judgment.

Design record includes decisions, interfaces, ownership, trust/persistence/recovery constraints, bounded local freedoms and requirements; mechanical and independent review artifacts are separate objects. Applicability state is CANDIDATE, MECHANICALLY_HELD, REVIEW_REQUIRED, VERIFIED or STALE, solely internal semantic gate state.

**Ports and wiring.** DesignAdmission.inspect(contract_ref, requirement_refs, architecture_baseline, interface_manifest, premise_evidence) -> MechanicalReport. DesignAdmission.record_review(design_ref, mechanical_report, review_record, expected_version) -> Applicability | Hold; review_record includes reviewer actor/invocation, producer actor/invocation, reviewed refs, findings, decision and authority. DesignApplicability.check(design_ref, current_revision_vector) -> CurrentVerified | Held | Stale, consumed by 013 and 015. composition/upstream_profile.py binds DesignAdmission, EvidenceRepository and authority snapshot reader; outputs feed both compiler and readiness consumer so neither can bypass design gate. This phase writes contract candidates only, no review-record import.

**State changes and identity.** Contract complete and compatible -> REVIEW_REQUIRED after mechanical evidence. Missing material decision, authority or infeasible premise -> HELD; return product questions to SPECIFY. Fresh authorized independent review of exact design/checks -> VERIFIED only if no blocking findings. Any required requirement/design/baseline/decision revision change -> STALE downstream; prior verdict retained. Design identity is requirement-set key plus canonical content digest; review identity binds design digest, mechanical report digest and independent actor/invocation. Current applicability includes exact approved architecture/EOS revision, never document title only.

**Failure and recovery.** Self-review/shared producer invocation -> refuse verification admission. Mechanically consistent impossible capability premise -> review rejection. Missing approved EOS/architecture baseline -> explicit conformity hold, not inferred conformance. Unresolved API/persistence/security decision -> design hold. Retain old review; repair produces new design digest and reruns affected mechanical checks plus fresh independent review. Material authority conflict cannot be settled by the checker.

**Operator and evidence.** Proposed upstream design inspect/show and review-record import; import checks identity and applicability but never generates approval. This artifact remains unverified until a separate Phase 10 actor reviews it. Requirement/design refs, interface manifest with producer/consumer ownership, fixed decision inventory, platform capability evidence, mechanical output, reviewer independence/authority and finding disposition.

**Fixed choices.** Existing architecture fitness checks are necessary but cannot certify premise truth or semantic compatibility; independent judgment remains required. No new visible lifecycle state, service or approval lane; internal states implement SWF-25 semantic gates within SPECIFY/PLAN.

**Deterministic enforcement.**

- `051-architecture-boundary` in `architecture_fitness`: Extend existing architecture suite with context import-direction/port compatibility fixture and preserve intentional violation checks; design admission requires exact mechanical artifact. Proven-red obligation: Inject forbidden adapter import/vendor signature and incompatible consumer input; each named mechanical check must fail before review.

- `051-review-applicability` in `python_unit_integration`: Require fresh independent review and exact revision vector for downstream compilation/readiness. Proven-red obligation: Replay self-review or stale design review and require downstream hold; conforming independent control passes.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-053 — Persistent control plane and bounded coordinator episodes

Persistent control-plane application owns episodes/attention; context_assembly builds context, execution_coordination alone owns lifecycle and release.

Episode aggregate: objective, authorized BIU, epoch, ACTIVE/ENDED, start time, tenure policy digest, limits/usage, input version vector, permitted/prohibited commands and end cause. Attention aggregate: stable origin event/outcome, item kind, PENDING/SEEN/RESOLVED, required authority, notification attempts, consumer receipts, resolution refs; every change appended to immutable history.

**Ports and wiring.** EpisodeControl.begin(objective, authority_ref, state_vector, tenure_policy, budget) -> EpisodeContext | Hold; submit(episode_id, epoch, expected_vector, proposal) -> admitted command | stale/authority hold; end(episode_id,cause) -> receipt. AttentionPort.ensure(event_identity, work_ref, kind, authority_needed) -> AttentionRef; seen(item,actor) records delivery only; resolve(item,resolving_decision,expected_version) validates applicable authority. ContextAssembler.reconstruct(snapshot_manifest) -> context plus deterministic authorized_next_action_set/blocked_set; reuse existing DecisionInbox for HumanDecision, never merge queues. AttentionNotifier.notify(item_ref) -> delivery attempt; activation is a separate port requiring explicit policy authority, unbound by default. Use shared_contracts.atomic_fencing_extension for atomic vector/fence/intent admission; read-then-commit of several independent aggregates is insufficient. Proposed composition/control_plane_profile.py constructs persistent monitor, EpisodeControl, Attention service, ContextAssembler and notifier with shared store/evidence/profile. Existing offline_profile injects these for proof. Model invocation is a child capability of explicit activation, never owner of monitor or store. 056 calls AttentionPort; 053 does not require 056 to be operational to handle existing outcomes.

**State changes and identity.** Explicit authorized begin -> ACTIVE new epoch; no observer-triggered model start by default. Terminal outcome, objective/authority change, contradiction, stale vector, exhausted context/age/transition/block limit, provider replacement or explicit end -> ENDED; renewal always new episode/epoch and fresh context. Authorized DONE requiring next judgment or judgment-blocked outcome -> ensure durable PENDING before notify. Seen receipt does not clear blocking suppression; only matching resolution or newer correlated nonjudgment outcome allows reevaluation. Episode UUID plus monotonic per-objective epoch fences old invocations. Attention ID hashes (profile, project/work identity, canonical event/outcome identity, attention kind); never observation time. Bootstrap imports preserve original IDs via immutable one-to-one alias map; product attention and program mailbox have distinct namespaces.

**Failure and recovery.** Stale/expired episode -> reject result without authoritative mutation. Missing context record -> hold reconstruction. Notification failure/no receipt -> item pending, delivery failed/unconfirmed. No activation authority -> notify only. Partial migration -> keep old consumer authoritative; no retirement. After crash end any episode whose liveness cannot be established; successor receives new epoch and reconstructs manifest from durable state. Compare deterministic allowed/blocked action sets and lifecycle, not model wording. Rebuild pending attention from retained origin outcomes if notification crashed; idempotent ensure preserves identity.

**Operator and evidence.** Proposed episodes show/end/start and attention list/show/seen/resolve; writes require actor, authority, expected revision, idempotency key. Persistent monitor lifetime is independent of model invocation. Program mailbox remains a separate operator duty. Context manifest, policy/limits, epoch/version vector, proposed/admitted action IDs, termination cause, reconstruction equivalence, attention history, notification/receipt and resolution attribution. Migration fixture covers pending AND handled items and mailbox responsibilities.

**Fixed choices.** Default tenure policy is explicit: one BIU, maximum age 3600 seconds, maximum 32 admitted transitions, maximum blocked duration 300 seconds, context usage threshold 0.8 of the invocation limit, contradiction count 1, any relevant state-vector mismatch ends tenure. Missing context usage/limit ends tenure conservatively. Monotonic clock within process; persisted UTC deadline for restart; clock regression holds. Values are versioned composition policy, not new authority or increased execution budget. Terminal/objective/authority/provider/model changes and explicit request end immediately. Reaching any limit ends, never silently renews; authorized begin of new epoch retains budget accounting. SF-REQ-008 durability elaboration and SF-REQ-029 provider normalization amendments are excluded. Existing store versions/events suffice; no promise of normalized provider telemetry. POSTW1-DECIDE-006A gates actual bootstrap handoff. Tenure checks run on each result/event and an injected deadline timer independent of the model. Epoch expiry prevents new authority-bearing commands but does not fabricate cancellation of already-admitted workers. Relevant authority/source changes advance a durable applicability revision observed by guarded admission; an external source whose freshness cannot be checked causes a hold. Unknown context usage is conservative termination, not provider telemetry normalization.

**Deterministic enforcement.**

- `053-attention-delivery` in `python_unit_integration`: Reuse Phase 3 durable-attention-before-notification and correlated consumer receipt probes, preserving advisory delivery diagnostics. Reuses Phase 3 LRN-019 (advisory). Proven-red obligation: Disconnect attention creation then consumer bridge; fail the corresponding assertion; channel failure preserves item.

- `053-tenure-fence` in `python_unit_integration`: Exercise every named termination cause and stale-vector/epoch rejection; replacement reconstructs equal allowed/blocked sets from same snapshot. Proven-red obligation: Accept old epoch or omit context item and require stale-write/equivalence assertion failure.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## SF-REQ-056 — Canonical actor/effect liveness reconciliation

Liveness reconciliation application proposes missing canonical effects; kernel admission owns authorization and effect execution; control_plane owns attention.

Per active factory aggregate retain lifecycle-entry UTC time/revision, expected effect kind and generation, stable effect identity, reservation owner/fence, invocation correlation, pending/completed/unknown effect status, durable outcome/evidence ref and suppression/resolution ref. Store revisions and lifecycle-entry generation are distinct: observation writes cannot create a new launch generation.

**Ports and wiring.** Liveness.inspect(known_active_snapshot, correlated_effect_snapshot, now, policy) -> NoAction | Gap | Suppressed | EvidenceHold. Liveness.reconcile(gap, expected_version, authority_snapshot) -> existing canonical EffectRef | Hold; use OperationalStore reservation/commit_with_effect/claim_effect/confirm_effect and EffectExecutor readback. EffectObservation port supplies active invocation, reservation, pending/unknown effects and latest correlated durable outcome for the SAME work/lane/generation; unavailable data is a typed failure, not an empty set. AttentionPort.ensure/resolve from 053 supplies judgment records; canonical launch and recovery share one effect identity and admission entrypoint. Use shared_contracts.atomic_fencing_extension at intent, claim and receipt; existing unguarded store methods alone do not satisfy the cross-process fence contract. composition/control_plane_profile.py binds Liveness, real store observation adapter, FactoryCoordinator canonical effect admission, EffectExecutor and 053 AttentionPort. It scans only already-known active records. OfflineProfile uses identical services with fake clock/local effects. Ratification flag is validated authority input, never a config boolean that confers authorization.

**State changes and identity.** IMPLEMENT -> expects producer; VERIFY -> verifier; ACCEPT -> each required outstanding closure effect; REVIEW, terminal or ACCEPT with no outstanding closure -> no launch recovery. Age < G -> NO_ACTION; age >= G and complete absence proof -> GAP. Active/pending/correlated completed/unknown effect -> no new launch; unknown -> hold/readback. Judgment outcome -> durable suppression/attention regardless of age. Seen-only receipt leaves suppression. Valid matching resolution or newer same-lane correlated nonjudgment outcome permits reinspection, never unconditional retry. Authorized gap -> reserve -> re-read evidence/admission -> durable intent -> fenced dispatch -> receipt/readback -> normal kernel projection. Canonical effect key is hash(profile, persisted repository/project identity, BIU identity, contract digest, lifecycle-entry generation, role/closure-action key). Original delivery and every scan use this exact key; delivery ID and scan time never enter it. A new generation requires canonical authorized transition/attempt allocation, not scanner mutation. Existing launch:<identity>:<version> records retain identity via immutable alias binding; do not rename in-flight effects.

**Failure and recovery.** Incomplete/unavailable projection or outcome store -> EVIDENCE_HOLD. Stale version/fence -> refuse action, resnapshot. Crash after send before receipt -> UNKNOWN; correlate readback, otherwise park for decision. Completed judgment result -> suppression, not missing actor. Store unavailable -> no launch, explicit failure; cannot promise finite successful recovery. Startup reopens intent/outcome/reservation records. Pending unsent intent may execute through canonical claim; sent/unknown intent must read back with same correlation and preserve fencing, parking if uncertain. Resolutions are checked against current outcome identity/lane/authority. Scans never add retry entitlement; exhausted or unknown authorized budget remains held.

**Operator and evidence.** Proposed liveness inspect is read-only; reconcile uses existing operator actor/authority/version/idempotency requirements and is disabled until 056 ratification and separate operational authorization. Show suppression and evidence hold with actionable refs. Live bootstrap retirement requires independently authorized workload exercise. Inspection snapshot refs, lifecycle-entry time/generation, age/G/I, expected effect, all matched claims/outcomes, gap/refusal, intent key/fence, authority/budget admission, suppression item/resolution, effect receipt and exact readback.

**Fixed choices.** Policy defaults: G=300 seconds, I=60 seconds, confirmation bound C=90 seconds; all configurable positive finite durations, persisted with policy digest and tested just below/at boundaries. These are design defaults, not a claim that historical bootstrap 5 minutes is a canonical invariant. Missing/invalid policy blocks startup. Periodic scan is limited to SF-REQ-056 explicitly specified reconciliation of known active state; it is not a general polling integration or work discovery loop. Effectively-once action requires idempotent/fenced consumer and durable readback; physically exactly-once network delivery is not promised. If an existing provider cannot prove these, park rather than relax the boundary. Depends on POSTW1-DECIDE-008A ratification. Pending SF-REQ-008 and SF-REQ-022 amendments are excluded; no new nonterminal retries or budget reset. Operational replacement and SWF-29 retirement remain separately gated.

**Deterministic enforcement.**

- `056-liveness-classification` in `python_unit_integration`: Reuse advisory Phase 3 fake-clock absence classification and bounded correlated recovery confirmation, including pending and judgment controls. Reuses Phase 3 LRN-010 (advisory). Proven-red obligation: Trust exit zero or one early sample; targeted confirmation assertion fails, delayed within-bound control passes.

- `056-fenced-effect` in `python_unit_integration`: Race two store connections, delayed original trigger and restart between intent/send/receipt; require one effective authorized action and judgment suppression. Proven-red obligation: Disable identity/fence guard then judgment suppression in separate isolated runs; corresponding duplicate-action/suppression assertion must fail, restored runs pass.

Detailed persistence, concurrency, security, vocabulary, non-goals and one-to-one acceptance probes are in this requirement’s JSON contract; shared storage and fencing rules apply in full.

## Authority conditions and review limits

`SF-REQ-056` depends on Founder ratification through POSTW1-DECIDE-008A. SF-REQ-015’s production assessment/schema/consumer migration is blocked on POSTW1-DECIDE-004A G1/G2 assignment; specifying consumer behavior does not fill that gap. Actual bootstrap handoff and retirement remain separately governed by POSTW1-DECIDE-006A and live proof. Unattended authority-bearing episode activation is unbound by default.

No contract depends on adoption of the five pending amendments. SF-REQ-013 excludes general split/replan; SF-REQ-056 grants no new nonterminal retry budget; SF-REQ-053/056 use existing durable-state semantics without adopting the SF-REQ-008 elaboration; provider normalization and learning-policy promotion stay outside scope. Adoption of an amendment would require a new affected design revision and review.

All seven Phase 3 promotions are referenced, not represented as deployed controls. Advisory LRN-003, LRN-010 and LRN-019 remain advisory. LRN-014’s consumer-premise lesson is addressed through explicit platform evidence and independent review; it was not a promoted general mechanical gate. Runtime reachability is not inferred from architecture-fitness imports.

Phase 10 must independently assess semantic adequacy, permission premises, interface compatibility, contention/crash cases and fit to a pinned approved architecture/EOS baseline. The design checker establishes structural coverage, not those judgments. No independent review has been performed by the designer.

## Local disposition

PARKED on existing `main`, owned by POSTW1-DESIGN-009’s Codex designer. The two deliverables are in the worktree at `/mnt/d/Projects/alienintent/docs/evidence/wave2-design-contracts.json` and `/mnt/d/Projects/alienintent/docs/evidence/wave2-design-contracts.md`. No temporary branch/worktree was created. Commit, push and network are explicitly prohibited by this task. Next action belongs to the separately tasked fresh Phase 10 reviewer and Program Director disposition authority.

## Validation

Final command outcomes and scope are recorded in the authoritative JSON `validation` object. Proposed behavioral probes above have not been implemented or run in this design phase.

Required checks passed: design checker, 10 contracts and zero failures; Wave 1 evidence checker, 1,075 checks and 13/13 negative controls killed. Both commands exited 0. Additional checks matched all 53 source acceptance IDs and preserved all 28 snapshotted input/setup files. There are 17 enforcement opportunities, eight promotion-reuse entries covering seven distinct Phase 3 promotions, zero new contexts and zero deferred material decisions. These results establish neither independent design approval nor runtime behavior.
