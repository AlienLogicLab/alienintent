# Wave 2 specified requirements

POSTW1-SPECIFY-008. The [JSON](wave2-specified-requirements.json) is authoritative for this phase. Existing source decisions remain product authority. No Priority or Wave is assigned, no amendment is enacted, and no Design Contract or live change is made.

Evaluated **41** candidates: **10 selected**, **31 rejected/deferred/folded**. Selection is for specification within authorized scope, not execution release.

## Selection and authority

Factory plan explicitly names SF-REQ-011 through SF-REQ-016 and SF-REQ-039; SWF-25/27 supply 051/053; the user expressly authorizes authoring in-scope 056.

SF-REQ-056 is **AUTHORED_IN_THIS_PHASE** and requires **Founder ratification**. SWF-29 supplies binding constraints; this does not make the complete definition pre-existing. SF-REQ-048 and SF-REQ-052 remain undefined.

The requirement inventory searches all three definition forms. At the pinned input baseline: 56 referenced IDs, 53 defined, including retired SF-REQ-054. The new 056 draft does not rewrite that historical count. The register need is covered by SF-REQ-011 rather than a second canonical authority store.

Agent-Ready process hardening is selected under SF-REQ-015. Its missing implementation/schema/CLI and serialization owners remain POSTW1-DECIDE-004A decisions. General split/replan is now included under the binding SF-REQ-013 amendment of 2026-09-22; the separately recorded original SPLIT-REPLAN evaluation below is historical and superseded by revised SF-REQ-013. SWF-32 is deferred because its implementation Wave is explicitly unassigned.

All nine KEEP_UNTIL_REPLACED mechanisms are evaluated below, together with the other eight Phase 6 mechanisms. No bootstrap mechanism is retired or claimed currently replaced.

Session A revision applies only to SF-REQ-011/013 and their rendered entries. Other candidate evaluations and Phase 8 validation/disposition below retain their recorded baseline; they do not override the 2026-09-22 amendments. Current revision provenance and local checks are in the [revision note](wave2-revisions/2026-09-22-respecify-011-013.md).

## Candidate inventory

| Evaluation ID | Selected | Title / disposition |
|---|---|---|
| SF-REQ-011 | Yes | Requirements IR: Select: the fragmented definition corpus makes stable identity and authoritative provenance necessary for CAPTURE/SPECIFY; the original plan already assigns the IR to this scope. |
| SF-REQ-012 | Yes | Requirements ambiguity detection: Select: without explicit ambiguity/authority questions, upstream lanes could pass unresolved product meaning into design or implementation. |
| SF-REQ-013 | Yes | Requirements to BIU compilation and conserved split/replan: Select initial compilation and the authority-bearing split/replan transaction under the binding SF-REQ-013 amendment of 2026-09-22; no new requirement, Priority or Wave. |
| SF-REQ-014 | Yes | Mechanical verification obligations before implementation: Select: upstream compilation needs feasible proof obligations before implementation; the Wave 1 impossible permission premise makes feasibility checking material. |
| SF-REQ-015 | Yes | BIU lint/readiness and Agent-Ready process hardening: Select existing lint/readiness process: four-outcome handling and immutable reassessment make READY operational. Defer schema ownership rather than invent it. |
| SF-REQ-016 | Yes | Definition / Observation / Verdict separation: Select: IR, evidence and readiness need explicit separation so imported claims cannot become authority or verdicts. |
| SF-REQ-039 | Yes | Fake-agent / offline factory proof: Select: the original plan includes deterministic offline lifecycle proof; it supplies affordable discriminating checks for the selected upstream/control-plane work. |
| SF-REQ-051 | Yes | Design Contract and Design Verification: Select: SWF-25 explicitly requires this gate for newly planned post-Wave-1 work; omitting it would bypass a binding design prerequisite. |
| SF-REQ-053 | Yes | Persistent control plane and bounded coordinator episodes: Select: binding bounded-tenure authority plus unreplaced attention/checkpoint duties establish a concrete need; no successful handover is presumed. |
| SF-REQ-056 | Yes | Canonical actor/effect liveness reconciliation: Select and author for ratification: SWF-29 has no operational canonical replacement and provides binding limits for this expressly in-scope undefined requirement. |
| SWF-32 | No | Execution cycle capability: DEFER: canonical semantics already amend SF-REQ-009, but the decision expressly withholds Priority/Wave. Evaluation does not assign it to Wave 2. Preserve all eleven cycle rules; obtain Founder scheduling before adding it to selected work. |
| SPLIT-REPLAN | No | General split/replan capability: DEFER: SF-REQ-013 currently owns initial compilation only. The Phase 5 conserved transaction remains a proposal with SPLIT-G1 ownership gap and pending POSTW1-DECIDE-005A/007A. SWF-33 authorizes one historical split, not a general product operation. Preserve the 69-obligation proposal as decision input; do not bury transaction authority in design. |
| REQUIREMENT-REGISTER | No | Separate requirement register: FOLD INTO SF-REQ-011: stable IDs, provenance and traceability already own the necessary inventory view. A separate canonical register would add a competing authority representation. No standalone new requirement is justified; unified discovery across all definition forms is selected under SF-REQ-011. |
| AGENT-READY-SCHEMA | No | Agent-Ready implementation/schema/CLI ownership and serialization: DEFER this extension pending POSTW1-DECIDE-004A G1/G2 owner assignment. Selected SF-REQ-015 covers current process semantics and retained source evidence without inventing an external schema or maintainer. |
| SF-REQ-008 | No | Crash-safety scope amendment: DEFER: Current crash-safe behavior is a dependency, not a new Wave 2 reimplementation. R02 durable control fields, explicit effect receipts and restart-proof elaboration is pending POSTW1-DECIDE-007A; do not enact it via 053/056. |
| SF-REQ-022 | No | Nonterminal retry exhaustion amendment: DEFER: Current requirement covers rejection/repair loops; extension to repeated nonterminal outcomes is pending POSTW1-DECIDE-007A and has no new Wave assignment. Existing bounded behavior remains a constraint, not authorization for new attempts. |
| SF-REQ-025 | No | Coordinator-tool credential environment ownership: DEFER: R04 is an adjacent-owner proposal, not existing ownership of coordinator environment construction/auth precedence. Defer until POSTW1-DECIDE-007A assigns scope; existing security boundaries remain mandatory. |
| SF-REQ-029 | No | Trajectory observer replacement and normalization: DEFER: Current trajectory ownership is defined, but its original implementation wave is later and provider-neutral progress/capacity normalization is an unapproved R05 scope extension. Retain observer replacement need without silently assigning Wave 2 or making SF-REQ-053 the normalization owner. |
| SF-REQ-041 | No | External creation-artifact intake subcapability: DEFER: factory plan explicitly places this in Wave 2B after the core Requirements IR and BIU compiler. Its separate intake/authority/provenance obligations are not prerequisites for making already-authorized requirements the normal input in this selected core set. |
| SF-REQ-042 | No | External creation-artifact intake subcapability: DEFER: factory plan explicitly places this in Wave 2B after the core Requirements IR and BIU compiler. Its separate intake/authority/provenance obligations are not prerequisites for making already-authorized requirements the normal input in this selected core set. |
| SF-REQ-043 | No | External creation-artifact intake subcapability: DEFER: factory plan explicitly places this in Wave 2B after the core Requirements IR and BIU compiler. Its separate intake/authority/provenance obligations are not prerequisites for making already-authorized requirements the normal input in this selected core set. |
| SF-REQ-044 | No | External creation-artifact intake subcapability: DEFER: factory plan explicitly places this in Wave 2B after the core Requirements IR and BIU compiler. Its separate intake/authority/provenance obligations are not prerequisites for making already-authorized requirements the normal input in this selected core set. |
| SF-REQ-055 | No | Proposal Intake product automation: DEFER: existing manual governed input is sufficient here; product intake is explicitly assigned to Wave 3. Do not promote proposals to canonical work or reschedule its automation merely to give CAPTURE semantics. |
| SF-REQ-050 | No | Standalone failure-class promotion implementation: DEFER as a separate selected delivery: Phase 3 gates are prospective proposals under existing owners, not an approved new Wave 2 schedule. SF-REQ-014/051 consume discriminating proof constraints now; neither selection declares the entire promotion backlog implemented or rescheduled. |
| BOOTSTRAP-M01 | No | SWF-21 release authority replacement: DEFER live automatic-release migration: Wave 1 release grant cannot authorize Wave 2; needs explicit next release owner and live-profile cutover proof under POSTW1-DECIDE-006A. |
| BOOTSTRAP-M02 | No | SWF-29 liveness reconciliation replacement: FOLD INTO selected SF-REQ-056; no second replacement requirement. Retain bootstrap until operational proof and authorized retirement. |
| BOOTSTRAP-M03 | No | SWF-27 observer replacement: DEFER live trajectory replacement under existing owner; no Wave reassignment or unapproved normalization amendment. SF-REQ-053 consumes observations but does not take over their ownership. |
| BOOTSTRAP-M04 | No | attention queue replacement: FOLD INTO selected SF-REQ-053 durable attention and SF-REQ-035 integration dependency; retain history and distinguish attention from decision authority. |
| BOOTSTRAP-M05 | No | Windows notification replacement: DEFER notification adapter/removal decision to POSTW1-DECIDE-006A. Selected SF-REQ-053 requires durable failed-attempt evidence but does not select a channel or authorize removal. |
| BOOTSTRAP-M06 | No | session-bound attention waiter replacement: FOLD INTO selected SF-REQ-053 activation/notification boundary; actual resident exit/consumer transfer remains POSTW1-DECIDE-006A work. |
| BOOTSTRAP-M07 | No | coordinator checkpoint replacement: FOLD INTO selected SF-REQ-053 fresh-context reconstruction proof; historical checkpoint existence is not tested equivalence. |
| BOOTSTRAP-M08 | No | PRODUCER-on-Claude temporary profile change replacement: REJECT as new product work: this is a separately authorized narrow profile reversion or new scoped exception, not an unbuilt requirement. Do not restore a profile or assume current readiness here. |
| BOOTSTRAP-M09 | No | Node/bootstrap execution authority replacement: DEFER sovereignty/cutover: requires full live conformance, one-writer migration and nonduplicating rollback. PY-10 sandbox success is insufficient and no Wave 2 migration assignment is invented. |
| BOOTSTRAP-M10 | No | sandbox ingress tunnel replacement: DEFER retention/retirement decision to POSTW1-DECIDE-006A. No new product requirement is needed to decide infrastructure custody; current tunnel remains untouched. |
| BOOTSTRAP-M11 | No | eighteen external bootstrap modules replacement: DEFER module-by-module custody and maintenance decision to POSTW1-DECIDE-006A; no blanket product adoption or deletion of the external bundle. |
| BOOTSTRAP-M12 | No | resident coordinator multi-BIU tenure replacement: FOLD INTO selected SF-REQ-053 bounded tenure target; actual handoff and any resident exception remain explicit operational decisions under POSTW1-DECIDE-006A. |
| BOOTSTRAP-M13 | No | Program Director mailbox bridge waiter replacement: REJECT as permanent product requirement: retain or hand off the separate program-message consumer for unfinished program duties. No evidence warrants making this temporary mailbox a new Wave 2 product mechanism. |
| BOOTSTRAP-M14 | No | SWF-26 PY-04 mutation gate replacement: REJECT replacement of an already expired PY-04-only role. Preserve its historical proof; use ordinary independent verification and existing general promotion authority. |
| BOOTSTRAP-M15 | No | bootstrap release-admission gate replacement: DEFER live release-admission replacement as a distinct migration obligation under an existing owner. Selected upstream readiness supplies inputs but cannot retire the live six-precondition gate. No new Wave assignment or release authority. |
| BOOTSTRAP-M16 | No | b-disp command compatibility alias replacement: REJECT new product requirement: canonical command already exists; missing evidence is installation-by-installation migration. Preserve compatibility aliases and persisted identities until separately authorized proof permits removal. |
| BOOTSTRAP-M17 | No | Local Program Director bootstrap orchestration role replacement: REJECT permanent productization of the temporary Director role. Complete or disposition program duties and preserve state under its existing authority; no new product owner or lifecycle is implied. |

## SF-REQ-011 — Requirements IR

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Represent authorized requirements independently of their source tool, retaining stable identity and source authority. Requirements / Planning owns intake and normalization through RequirementSource; the core consumes only the provider-neutral internal requirements model.

### Value

Make the actual requirement set discoverable and traceable before compilation; prevent heading-only omissions and a second conflicting authority store.

### Scope

- Stable requirement IDs, source revisions and provenance, status, dependencies and BIU satisfaction links.
- A unified inventory view includes all three observed definition forms, distinguishes references from definitions and preserves retirement/supersession. Existing source decisions remain authority until an authorized adoption changes that.
- RequirementSource obtains requirement/proposal information; WorkManagement separately represents and projects work state. One vendor may fill both roles through separate adapters.
- Supported Requirement Source kinds: GitHub Issues/Projects, Jira, Linear, Azure DevOps, GitLab, local files, structured product documents, AlienIntent-native proposal intake (SF-REQ-055), and imported prototypes/artifacts (SF-REQ-041–044). This is an extensibility/support contract, not a new Wave assignment or implementation of every intake product.
- Adapters translate Source Records plus provenance into the internal requirements model. Every Requirement retains external source, external identity, external revision, source link, ingestion timestamp, authority status and synchronization/projection semantics.
- External vocabulary is never domain identity: Jira Epic is not intrinsically a Requirement; GitHub Issue is not intrinsically a BIU; Linear Project is not intrinsically a Wave. Replace a source or Work Management Provider without rewriting Requirements / Planning.

### Non goals

- New product intent, automatic ratification, new Priority/Wave, importing proposals as approved requirements.
- A second hand-maintained canonical register or choice of storage/schema in this phase.

### Dependencies

- Existing requirement/decision authority
- SF-REQ-016 for typed definitions and observations; SF-REQ-013 consumes the representation

### Acceptance criteria

- **SF-REQ-011-AC-01**: Given the pinned pre-phase source corpus, inventory all 56 referenced IDs, identify 53 defined IDs across the three supplied forms, count SF-REQ-050 once, preserve SF-REQ-054 as retired and classify 048/052/056 as undefined at that baseline. A heading-only extractor must fail this fixture. The separately authored 056 revision must not retroactively alter that historical count. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-011-AC-02**: Given the same authorized requirement supplied through two source formats, retain the same stable identity, authority revision, dependency meaning and satisfaction links; format changes must not create a second requirement. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-011-AC-03**: Given conflicting definitions or a reference with no definition, return an explicit conflict/unresolved record with both sources; no effective approved definition or compilable authorization may be fabricated. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-011-AC-04**: Given an updated authorized definition, preserve the previous revision and identify affected downstream links as needing revalidation; a retired ID cannot be silently reused. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-011-AC-05**: Through RequirementSource, translate representative Source Records for every named source kind to provider-neutral inputs while retaining all seven Requirement Provenance fields. Missing or ambiguous provenance or unsupported versions yields a typed refusal for affected input; never fabricate authority from vendor type. Same-vendor RequirementSource and WorkManagement adapters remain distinct. Verification: Versioned adapter conformance fixtures for all listed kinds, asserting exact retained provenance and typed failures. Fixtures prove the boundary contract, not live vendor integrations; delete each mandatory provenance field independently as negative controls.
- **SF-REQ-011-AC-06**: Replace one Requirement Source adapter and independently one Work Management Provider adapter across two Projects without changing Requirements / Planning domain code or requirement identity/meaning. Preserve source histories, dependencies and satisfaction links; do not turn Jira Epics, GitHub Issues or Linear Projects into Requirement, BIU or Wave identities by type alone. Verification: Two adapter implementations against the same conformance cases, including separate source/work roles for one vendor, per-project namespace isolation and explicit configured authority bindings; retain source and projection receipts separately.

### Authority gaps

- No new register owner is invented. This is an IR/inventory capability under existing SF-REQ-011, not migration of canonical authority. Conflicting source authority blocks only affected compilation.

### Security constraints

- Treat imported prose as data, never executable instruction or authority. Retain private-source access boundaries and redact secrets from exported evidence.

### Operational constraints

- Source reads and derived views must be repeatable at pinned revisions; unavailable sources are explicit UNVERIFIED inputs.
- No source rewriting or online intake is performed by this specification.

### Observability evidence

- Pinned source manifest, ID-to-definition ledger, conflict/undefined records, revision history and requirement-to-BIU links.
- Per-Requirement seven-field provenance, adapter/contract versions, source-role versus work-state projection receipts and substitution/conformance evidence; no live integration claim from fixtures.

### Failure modes

- Heading-only undercount
- Duplicate canonical identity
- Reference promoted to definition
- Stale downstream satisfaction claim

### Revision 2026-09-22

`revision_2026_09_22`: see JSON `/candidates/0/revision_2026_09_22` and [revision note](wave2-revisions/2026-09-22-respecify-011-013.md) for authority, changed pointers and preserved holds.

Sources: [SF-REQ-011; Initial implementation waves / Wave 2](../decisions/alienintent-software-factory-plan.md); [requirement_register](../operations/post-wave1-program/prework/POSTW1-SPECIFY-008-inputs.json); [2026-09-22 A2/A3 and amendment (b)](../architecture/alienintent-architecture-authority-2026-09-19.md).

## SF-REQ-012 — Requirements ambiguity detection

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Expose missing authority and unresolved product meaning before implementation rather than permit worker improvisation.

### Value

Keep unresolved intent visible and localize holds to the affected work.

### Scope

- Detect absent intent, contradictory scope, unresolved authority, missing acceptance/evidence meaning and ambiguous dependencies in governed requirement inputs.
- Emit structured questions linked to exact sources and the decision needed; record attributed answers and invalidate dependent readiness when material inputs change.

### Non goals

- The model resolves Founder questions itself.
- Claiming exhaustive natural-language ambiguity detection or imposing a new approval lane.

### Dependencies

- SF-REQ-011 source identity
- SF-REQ-006 and SF-REQ-035 decision escalation
- SF-REQ-051 design boundary

### Acceptance criteria

- **SF-REQ-012-AC-01**: Fixtures omitting intent, presenting conflicting scope, lacking authority or leaving an acceptance result undefined each yield a source-linked question naming the affected requirement and a blocked advancement reason.
- **SF-REQ-012-AC-02**: An attributed decision answering a question against a pinned revision resolves only that question; a reply for a different revision leaves the hold intact.
- **SF-REQ-012-AC-03**: A requirement with complete authority, boundaries and measurable criteria passes the mechanical completeness checks; a recorded independent semantic review may still raise specific questions without silently editing its intent.
- **SF-REQ-012-AC-04**: An unrelated complete requirement remains eligible for upstream preparation while another awaits clarification; neither question creation nor answer receipt launches a worker.

### Authority gaps

- Unresolved product questions go to their existing authority; this requirement does not delegate decisions to designers.

### Security constraints

- Questions expose only the context the decision actor may read; untrusted source content cannot impersonate an authority response.

### Operational constraints

- Mechanical checks precede judgment; retain ambiguity findings even after resolution.
- Missing human decision capability holds the affected branch rather than assuming approval.

### Observability evidence

- Finding ID, exact source, affected work, question, decision authority, answer attribution and revision, hold/resolution evidence.

### Failure modes

- False readiness through omission
- Unattributed answer accepted
- Stale resolution reused
- Global stall for a local gap

Sources: [SF-REQ-012; SF-REQ-006; SF-REQ-035](../../docs/decisions/alienintent-software-factory-plan.md); [Design authority boundary](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md).

## SF-REQ-013 — Requirements to BIU compilation and conserved split/replan

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Lower governed requirements into bounded BIU contracts with explicit satisfaction links and a dependency DAG. The BIU Compiler in Requirements / Planning derives the initial decomposition itself and owns authorized Split Transactions; Agent Ready supplies judgment and recommended semantic boundaries, not mutation.

### Value

Make authorized requirements the normal input to execution without asking workers to invent decomposition intent.

### Scope

- Initial compilation from specified requirements and approved, verified design into proposed bounded BIUs. The compiler derives this decomposition; a hand-authored external obligation mapping is not a mandatory input.
- Trace every input obligation to BIU scope through obligation mapping, carry fixed decisions, boundaries, capabilities, budgets, verification and evidence duties, and validate the dependency graph.
- Freeze the original requirements, acceptance criteria, verification obligations and evidence obligations. Map 100% to resulting units or a retained Integration Parent; no loss, invention or weakening of authorized intent or proof.
- Deterministically rewrite dependency identities without judgment redirection, cycles or weakened satisfaction predicates; record original/result lineage and preserve original evidence.
- Invalidate applicability of stale Readiness Assessments without rewriting history, materialize resulting candidate BIUs, and submit each result (including the retained Integration Parent) to SF-REQ-015 lint and fresh Agent Ready assessment.
- Use a stated BIU identity grammar with collision-safe reservation, never sort-order identity. Reconcile the Phase 5 candidate design against the amendment and SWF-33; candidate mechanisms are not automatically approved.

### Non goals

- Unapproved product intent changes, silent reallocation or weakened proof; splitting active invocations in place, reopening DONE work or bypassing ordinary readiness, release and closure gates.
- Automatic execution, new priority, budget increases, new authority or implementation choices that belong in design.

### Dependencies

- SF-REQ-011
- SF-REQ-012
- SF-REQ-051 approved design gate
- SF-REQ-010 contract model
- SF-REQ-014 obligations
- SF-REQ-015 readiness

### Acceptance criteria

- **SF-REQ-013-AC-01**: For a specified fixture with named requirements and an approved design, each emitted BIU links its exact requirement and design revisions and carries every SF-REQ-010 contract field; an omitted boundary or evidence obligation blocks output admission. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-013-AC-02**: A coverage report maps each input requirement, acceptance criterion, verification obligation and evidence obligation to one or more explicit BIU extents through obligation mapping. Unmapped obligations block compilation acceptance; mapping alone never claims satisfaction. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-013-AC-03**: Fixtures with a cyclic dependency, missing endpoint or dependency whose satisfaction predicate is unspecified are refused with the offending edge identified; an acyclic fully resolved graph is admitted for assessment. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-013-AC-04**: Missing design verification, unresolved product authority or conflicting fixed decisions produces a hold and no READY or IMPLEMENT transition. Verification: Controlled fixture or independently inspected versioned artifact; retain inputs, observed outputs and verdict separately.
- **SF-REQ-013-AC-05**: Given an authorized split of a pinned existing decomposition, freeze all original obligations and conserve 100% in resulting units or a retained Integration Parent. Reject loss, invented intent, weakened proof, budget/capability expansion, stale authority and partial mapping before applying a mutation. Preserve existing identities/history and integration proof. Verification: Replay the SWF-33 PY-10 / PY-09B precedent as a historical contract fixture, not a live mutation; compare exact original clauses, resulting extents and retained integration duties. Proven-red omissions, weaker clauses and invented obligations must refuse admission.
- **SF-REQ-013-AC-06**: Initial compilation derives bounded units and obligation mapping from exact authorized requirements, verified design and proof inputs without a mandatory external hand-authored mapping. Every SF-REQ-010 field and stable identity is present; changed inputs produce an attributable distinct revision. Verification: Composed positive compilation fixture without external mapping; reject validator-only output, missing obligations or invented scope. Permute input enumeration and assert semantic mapping and identities do not derive from sorting.
- **SF-REQ-013-AC-07**: Split dependency rewrites are deterministic identity rewrites: preserve authoritative predicates and downstream integration boundary; reject cycles, missing endpoints, weakened predicates and judgment-based redirection. New identities satisfy the stated grammar and explicit reservations, with lineage stored independently of suffixes or sort order. Verification: Before/after graph and identity fixtures, including PY-09B compatibility, collisions, exhaustion, stale reservations, reordered inputs and changed predicates; each invalid case refuses mutation.
- **SF-REQ-013-AC-08**: A Split Transaction records lineage and invalidates old assessment applicability while retaining raw history, materializes every resulting candidate, then submits each child and retained Integration Parent through SF-REQ-015 lint and supported Agent Ready assessment. Each result is READY / CLARIFY / SPLIT / HOLD; no result itself releases execution. Verification: Inspect per-result submission and assessment links; missing one, reusing stale READY or trusting a shape-compatible surrogate fails. Retry/recovery preserves operation identity and immutable historical assessments; provider failure is an execution failure, never a disposition.

### Authority gaps

- SPLIT-G1 and R1-GAP-013-ALLOCATION are settled by the SF-REQ-013 amendment 2026-09-22. Existing product authority, exact authorized replan scope, independent design verification, dependency-edge authority and normal release/budget/custody gates still apply; ownership does not grant blanket mutation or release authority.

### Security constraints

- Compilation cannot widen credentials, source access, execution budget or trust boundaries beyond approved inputs.

### Operational constraints

- Stable source-to-output traceability across repeated compilation; changed source/design requires a distinct identifiable candidate revision.
- Dependency satisfaction retains authoritative lifecycle predicates; projections cannot redefine them.
- Identity grammar and reservation are explicit design constraints, never derived from sorted position; obligation mapping is compile-time, Allocation is execution-time only.
- A replan requires exact scope/baseline authority, conserved budget and a safe quiescent boundary; candidate design approval and fresh assessment remain prerequisites to release.

### Observability evidence

- Pinned input and design revisions, generated contract manifest, coverage report, graph validation and admission refusals.
- Frozen obligation inventory, forward/reverse obligation mapping, lineage, pre/post graphs and predicates, identity reservations, operation payload and authority, stale-assessment applicability records, materialized candidate digests and per-result fresh assessment submissions/outcomes.

### Failure modes

- Lost proof obligation
- Invented product behavior in BIU
- Cycle or unresolved dependency
- Unapproved replan disguised as compilation

### Revision 2026-09-22

`revision_2026_09_22`: see JSON `/candidates/2/revision_2026_09_22` and [revision note](wave2-revisions/2026-09-22-respecify-011-013.md) for authority, changed pointers and preserved holds.

Sources: [SF-REQ-010; SF-REQ-013](../decisions/alienintent-software-factory-plan.md); [Relationship to BIU and Agent-Ready](../decisions/2026-09-20-design-contract-and-design-verification.md); [candidate design: sections, identity_grammar, operation_protocol; ownership_audit/SPLIT-G1 superseded only by amendment 2026-09-22](../evidence/wave1-biu-split-replan-design.json); [SWF-33; retained Integration Parent and unchanged proof precedent; bootstrap-assessor history](../decisions/2026-09-21-py10-transport-split.md); [2026-09-22 A2/A3 and amendment (b)](../architecture/alienintent-architecture-authority-2026-09-19.md).

## SF-REQ-014 — Mechanical verification obligations before implementation

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Derive feasible verification obligations from authorized requirements before implementation can bias the acceptance oracle.

### Value

Catch wrong or weakened acceptance tests and ensure mechanical gates can actually reject a defect.

### Scope

- Pre-implementation completion, test and evidence obligations traceable to requirements and verified design.
- Separate mechanically decidable predicates from independent judgment and preserve earlier satisfied obligations during repair.

### Non goals

- Implementation code as sole acceptance oracle.
- An impossible universal platform-denial proof or a requirement for all quality judgments to be automated.

### Dependencies

- SF-REQ-011 and SF-REQ-013 traceability
- SF-REQ-051 platform premise verification
- SF-REQ-049 convergent repair and SF-REQ-050 meaningful negative controls as existing constraints

### Acceptance criteria

- **SF-REQ-014-AC-01**: Before a fixture implementation exists, each mechanically testable acceptance predicate has controlled inputs, expected observable result and retained evidence obligation linked to the authorized requirement revision.
- **SF-REQ-014-AC-02**: For a gate fixture, a valid case passes and a discriminating mutation violating its named invariant fails with a nonzero result. An unconditional-success or self-referential check is refused as proof.
- **SF-REQ-014-AC-03**: For a platform isolation obligation, use positive target access, configured profile/resource scoping, a rejected out-of-scope application request and unchanged outside-state readback in an authorized fixture; never demand platform credential denial that the permission model cannot provide.
- **SF-REQ-014-AC-04**: A predicate requiring human judgment records the reviewer authority, inspection inputs and decision record rather than claiming a mechanical PASS. Removing a required predicate blocks plan admission.

### Authority gaps

- No amendment is required to specify existing proof-before-implementation duties. Proposed Phase 3 gates are inputs, not already deployed enforcement.

### Security constraints

- Negative controls operate on isolated authorized fixtures; they cannot probe private installations or expose credentials.

### Operational constraints

- Expected outcomes exist before implementation; runnable test details may be designed later without changing the predicate.
- Infeasible proof is surfaced as a specification defect for correction by authority, never waived in design.

### Observability evidence

- Requirement-to-predicate mapping, fixture definition, expected/actual output, exit status, negative-control result and independent judgment records.

### Failure modes

- Circular acceptance oracle
- Unkillable gate
- Impossible permission proof
- Dropped repair evidence

Sources: [SF-REQ-014](../../docs/decisions/alienintent-software-factory-plan.md); [Binding isolation standard](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md); [decision_policy; candidates](../../docs/evidence/wave1-gap-trap-promotion-backlog.json).

## SF-REQ-015 — BIU lint/readiness and Agent-Ready process hardening

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Admit only complete, current BIUs for Agent-Ready assessment and honor the resulting readiness disposition without coercion.

### Value

Stop missing decisions, stale assessments and tool failures from masquerading as execution readiness.

### Scope

- Contract lint for boundaries, acceptance/verification, architecture and dependency problems; preserve Agent-Ready as readiness authority.
- Process semantics for READY, BLOCKED, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED; immutable assessment evidence and reassessment lineage.
- Design prerequisites are supplied by SF-REQ-051. Consumer handling must preserve source envelopes and reject ambiguous results.

### Non goals

- Assigning the missing Agent-Ready implementation/schema/CLI owner or inventing a canonical serialization contract.
- General split/replan execution, readiness by process exit code, or release solely because READY was returned.

### Dependencies

- SF-REQ-010
- SF-REQ-012
- SF-REQ-014
- SF-REQ-051
- Existing Agent-Ready assessment authority; G1/G2 assignment needed before schema/CLI implementation work

### Acceptance criteria

- **SF-REQ-015-AC-01**: A complete pinned BIU may proceed to assessment; fixtures missing a decision, boundary, verification obligation, architecture constraint or dependency produce an attributable lint hold before implementation.
- **SF-REQ-015-AC-02**: For READY, retain exact assessed inputs and apply separate release gates. BLOCKED holds pending prerequisite resolution; NEEDS_CLARIFICATION holds for an attributable answer; SPLIT_RECOMMENDED holds for an authorized planning decision. None of the three non-READY outcomes authorizes implementation.
- **SF-REQ-015-AC-03**: After a material contract, baseline, governing decision or prerequisite change, a fresh assessment links the prior immutable assessment. Resolving a blocker cannot rewrite the old verdict to READY.
- **SF-REQ-015-AC-04**: A direct readiness object and a known MCP envelope carrying the same disposition yield the same semantic handling while preserving raw evidence. Conflicting text/structured values, unknown disposition, missing terminal result, timeout or provider failure produce an attempt failure and hold, never synthesized readiness.
- **SF-REQ-015-AC-05**: Replaying the retained PY-10 assessment revision sequence shows BLOCKED then SPLIT_RECOMMENDED then a distinct fresh READY after prerequisite completion; all prior revision references remain retrievable in the fixture. This is a retention test, not proof that historical verdicts were coerced.

### Authority gaps

- POSTW1-DECIDE-004A must assign G1 assessment implementation/schema/CLI and G2 canonical serialization ownership before implementing those changes. This selected scope defines process and consumer semantics only, and does not fill those ownership gaps.

### Security constraints

- Only an attributable assessment authority can supply readiness; imported wrappers and worker success claims cannot promote themselves. Preserve credential and sandbox boundaries for assessment invocations.

### Operational constraints

- Four evidenced dispositions are the required handling set, not a claimed exhaustive external schema.
- Retries/failover remain within already authorized budgets and capability policy; unknown contract shape is held for owner resolution.

### Observability evidence

- Raw assessment, normalized semantic observation, assessed revision, provider/invocation identity, attempt failure, immutable predecessor link and separate release decision.

### Failure modes

- Top-level-only parser loses nested verdict
- Timeout becomes READY
- Historical assessment overwritten
- Stale READY reused
- Split recommendation treated as planning authority

Sources: [SF-REQ-015](../../docs/decisions/alienintent-software-factory-plan.md); [dispositions; execution_failures; gaps; coercion_finding](../../docs/evidence/wave1-agent-ready-outcome-matrix.json); [Relationship to BIU and Agent-Ready](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md).

## SF-REQ-016 — Definition / Observation / Verdict separation

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Keep normative definitions, observed facts and authorized evaluation verdicts distinct throughout upstream and execution evidence.

### Value

Prevent worker claims and imported evidence from silently acquiring authority or acceptance status.

### Scope

- Classify and link definitions, observations and verdicts with their source revisions and evaluation authority.
- Carry this distinction through IR, compiled obligations, readiness results and offline proof.

### Non goals

- A new lifecycle, autonomous policy promotion or private chain-of-thought storage.

### Dependencies

- SF-REQ-011 source provenance
- Existing verdict-admissibility rules in SF-REQ-009 and independent verification authority

### Acceptance criteria

- **SF-REQ-016-AC-01**: Given a requirement definition, a worker statement that tests passed and a test result, retain each with its role; none alone creates an authorized PASS verdict.
- **SF-REQ-016-AC-02**: A verdict identifies the exact definition revision, evidence inputs and authorized evaluator/policy. Missing evidence or mismatched revisions leaves the claim UNVERIFIED or blocks acceptance.
- **SF-REQ-016-AC-03**: A conflicting observation is preserved alongside earlier evidence and causes reevaluation/hold under the applicable policy rather than rewriting the requirement.
- **SF-REQ-016-AC-04**: A fixture presenting an observation or learned hypothesis as an authoritative definition is rejected at the admission boundary; a properly authorized versioned definition remains admissible.

### Authority gaps

- No new authority gap identified within existing separation semantics.

### Security constraints

- Evidence content is untrusted input; it cannot issue instructions or forge evaluator authority. Redact secrets without inventing missing measurements.

### Operational constraints

- UNKNOWN is retained as UNKNOWN; observation ordering and source identity survive replay.

### Observability evidence

- Typed source/evidence/verdict records and links, evaluator authority, revision mismatches and rejected promotion attempts.

### Failure modes

- Claim promoted to PASS
- Observation overwrites definition
- Unattributed verdict
- UNKNOWN silently becomes zero

Sources: [SF-REQ-016; SF-REQ-009; SF-REQ-030](../../docs/decisions/alienintent-software-factory-plan.md).

## SF-REQ-039 — Fake-agent / offline factory proof

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Exercise the real factory lifecycle using deterministic scripted workers without provider credentials or token spend.

### Value

Make upstream-to-execution verification repeatable and cheap while detecting lifecycle and custody defects before live use.

### Scope

- Scripted worker outcomes through real canonical lifecycle, admission, custody, verification and closure policy paths with isolated local external-system substitutes.
- Successful delivery, rejection/repair, missing result, missing authority, duplicate event, restart and judgment-blocking scenarios.

### Non goals

- A parallel mock lifecycle that bypasses the kernel.
- Proof of live GitHub permissions, real provider quality, live-profile sovereignty or bootstrap retirement.

### Dependencies

- Canonical SF-REQ-001 through SF-REQ-010 lifecycle interfaces
- SF-REQ-016 evidence separation
- Existing source-control/Work Management ports; SF-REQ-051 verified interface boundaries

### Acceptance criteria

- **SF-REQ-039-AC-01**: With provider credentials absent and outbound networking denied in a test environment, a seeded authorized fixture reaches its required terminal lifecycle state using scripted producer and fresh verifier invocations, and records zero provider calls.
- **SF-REQ-039-AC-02**: A verifier-rejection script returns the same BIU to implementation with findings and a subsequent passing candidate can proceed through normal closure; lifecycle transitions come from the real kernel, not the script.
- **SF-REQ-039-AC-03**: An unpublished or wrong-identity candidate and a missing durable work result each prevent VERIFY/acceptance as applicable, even if the scripted worker exits zero.
- **SF-REQ-039-AC-04**: Replay a duplicate trigger and restart from saved durable fixture state: retain one authorized effect for the same identity and the same reconstructed lifecycle state.
- **SF-REQ-039-AC-05**: A completed judgment-required outcome produces a hold/attention and no automatic replacement actor until resolved. The fixture records observed invocations and retained outcomes.
- **SF-REQ-039-AC-06**: Disable the tested custody guard in an isolated negative control: the corresponding test must fail. Test documentation identifies which external effects were substituted and does not label offline success as live proof.

### Authority gaps

- No scheduling change needed: explicitly included by the original Wave 2 plan. Live operations and paid providers remain separately authorized.

### Security constraints

- Use disposable repositories/state and dummy identities; fixtures must neither load installation secrets nor contact live services.

### Operational constraints

- Repeat runs from the same fixture/event inputs produce equivalent lifecycle/effect results; generated incidental IDs/times may be normalized explicitly.
- Scenarios involving new capabilities become runnable when those capabilities exist; offline harness itself must exercise current canonical interfaces.

### Observability evidence

- Fixture and seed revisions, event stream, real-kernel transition log, worker/effect identities, candidate custody receipts, network/provider-call guard results and negative-control output.

### Failure modes

- Mock proves its own lifecycle
- Credential leakage or accidental spend
- Nondeterministic fixture
- Offline result overclaimed as live proof

Sources: [SF-REQ-039; Initial implementation waves / Wave 2](../../docs/decisions/alienintent-software-factory-plan.md).

## SF-REQ-051 — Design Contract and Design Verification

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Close product, architecture, trust, persistence, interface and verification decisions before BIU decomposition or implementation.

### Value

Prevent impossible premises and material decisions from reaching implementation workers as hidden freedom.

### Scope

- Proportional Design Contracts for newly planned post-Wave-1 work; requirement linkage, explicit fixed/deferred decisions and evidence obligations.
- Mechanical-first conformance checks followed by independent design judgment; Agent-Ready consumes the required design verification outcome.

### Non goals

- Writing Design Contracts in this phase.
- Retrofitting Wave 1, adding a visible DESIGN Project status, eliminating independent judgment or prescribing a new service/database.

### Dependencies

- Specified SF-REQ-011/012 inputs
- Architecture Authority, EOS and applicable ADRs
- SF-REQ-014 proof feasibility
- SF-REQ-013 and SF-REQ-015 downstream consumers

### Acceptance criteria

- **SF-REQ-051-AC-01**: For a newly planned change, the design artifact identifies satisfied requirements, affected behavior/ownership/interfaces/persistence, invariants, failures/recovery, security, capabilities, evidence and non-goals; each inapplicable field has an explicit reason proportional to the change.
- **SF-REQ-051-AC-02**: Unresolved product behavior, public API, persistence or security decisions block design verification and decomposition; only explicitly bounded implementation-local choices remain open.
- **SF-REQ-051-AC-03**: A forbidden dependency or incompatible interface fixture fails mechanical design checks before independent review; a conforming fixture records those results and a separate attributable independent review.
- **SF-REQ-051-AC-04**: A platform-premise review rejects a proposed permission-denial criterion when authoritative capability evidence shows it cannot be satisfied; the design cannot pass by merely matching an internally consistent checklist.
- **SF-REQ-051-AC-05**: Changing a verified design decision or required requirement revision invalidates downstream design/readiness applicability until reverified; the prior artifact and verdict remain history.
- **SF-REQ-051-AC-06**: An admission fixture lacking required design, a passing design verification result or resolved design authority is refused by readiness processing, without adding a Project lifecycle state.

### Authority gaps

- No unresolved product meaning is delegated to design; an uncovered authority question returns to SPECIFY. SF-REQ-015 G1/G2 still govern assessment implementation ownership.

### Security constraints

- Design review must validate trust and secret boundaries with actual platform capabilities; independent review cannot be self-approval.

### Operational constraints

- Design depth is proportional; mechanical evidence precedes judgment.
- DESIGN and DESIGN VERIFICATION are semantic gates within SPECIFY/PLAN per SWF-25, not new external lanes.

### Observability evidence

- Requirement/design revisions, decision inventory, premise evidence, mechanical results, independent review identity/findings and downstream invalidation links.

### Failure modes

- Design checklist masks impossible premise
- Unresolved product decision disguised as local detail
- Self-review
- Stale design verification reused

Sources: [Workflow semantics; Design Contract; Design Verification; Founder clarifications](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md); [Binding isolation standard](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md).

## SF-REQ-053 — Persistent control plane and bounded coordinator episodes

Definition status: **DEFINED**. Founder ratification required: **false**.

### Intent

Keep authority, state and evidence durable while model-based coordinator reasoning has bounded, replaceable tenure.

### Value

Allow coordination to end or restart without losing authorized next actions, attention or control-plane progress.

### Scope

- Durable episode context and policy-controlled tenure; deterministic lifecycle ownership remains in the control plane.
- Durable attention identity, deduplication, handling and activation/notification boundary independent of session lifetime.
- Fresh-context reconstruction, stale-result refusal, and explicit migration proof before retiring checkpoint/queue/waiter functions.

### Non goals

- An immortal model coordinator, conversation as authority, new lifecycle semantics.
- Unattended authority-bearing model activation without explicit authorization, automatic next-wave release under expired SWF-21, or takeover of provider telemetry normalization.

### Dependencies

- SF-REQ-008 current crash-safe primitives
- SF-REQ-009 deterministic authority
- SF-REQ-034/035 operator and decision surfaces
- SF-REQ-051 verified separation
- SF-REQ-056 missing-effect versus judgment distinction

### Acceptance criteria

- **SF-REQ-053-AC-01**: Stop an episode after a durable event, then start a fresh context with no transcript. Given the identical authority/state/event snapshot, predecessor and successor identify the same authorized next-action set, blocked work and lifecycle state; record mismatches as failures, not merely a successfully started process.
- **SF-REQ-053-AC-02**: Each tenure termination cause in SWF-27 (terminal outcome, objective/authority change, context/contradiction/staleness/age/transition limits, prolonged block, provider replacement or explicit request) has a policy fixture that ends or renews tenure explicitly; the same expired episode cannot continue making authoritative changes.
- **SF-REQ-053-AC-03**: Return a coordinator result against an obsolete state revision: it is refused without overwriting newer authoritative state. A result at the applicable current revision still undergoes ordinary authority validation.
- **SF-REQ-053-AC-04**: A DONE event requiring next-work judgment and a judgment-required blocking outcome each create durable attention. Duplicate observation/restart retains the same item identity; monitor operation continues after the model episode ends.
- **SF-REQ-053-AC-05**: When notification delivery fails, the attention item remains pending and the failed attempt is recorded. A later authorized consumer can inspect and handle it without the old conversation. Seeing a notification alone does not resolve its blocker.
- **SF-REQ-053-AC-06**: With no unattended-activation authority, a pending item may notify for activation but must not launch an authority-bearing episode. An explicit authorized activation policy, if later supplied, is checked as an input rather than presumed.
- **SF-REQ-053-AC-07**: Before replacing a bootstrap attention/checkpoint consumer, a controlled migration fixture preserves pending and handled identities, attribution and historical evidence and demonstrates successor consumption without duplicate handling; product attention and program mailbox duties remain distinct.

### Authority gaps

- Thresholds and concurrency mechanisms are bounded design choices under SWF-27, not permission to weaken tenure.
- POSTW1-DECIDE-006A controls actual bootstrap handoff/retirement; no such operational action is authorized here. Unattended activation remains unauthorized unless separately granted.
- Pending SF-REQ-008 durability elaboration and SF-REQ-029 normalization are not adopted; this scope uses existing durable-state and observable-event contracts.

### Security constraints

- Stale or unauthorized coordinator output cannot mutate authority. Context contains only permitted project data; secrets and private reasoning are excluded.

### Operational constraints

- Episode default is one BIU, configurable by explicit tenure policy; Wave 1 multi-BIU exception is not the permanent default.
- Attention is distinct from HumanDecision authority; acknowledgment that permits recovery must record actual resolution under applicable authority.
- No prior successful Wave 1 handover is claimed.

### Observability evidence

- Episode objective/budget/state revision, tenure policy and cause, authoritative context manifest, reconstruction comparison, attention identity/history, notification attempts, handling attribution and stale-result refusals.

### Failure modes

- Monitoring survives but attention is lost
- Conversation-only authority
- Stale result overwrites state
- Seen mistaken for resolved
- Program mailbox silently abandoned at handoff

Sources: [Durable rules; Architectural separation; activation boundary; Relationship to Decision Inbox](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [SWF-27 observer; attention queue; coordinator checkpoint; resident coordinator multi-BIU tenure](../../docs/evidence/wave1-bootstrap-retirement-matrix.json); [LRN-027](../../docs/evidence/wave1-learning-ledger.json).

## SF-REQ-056 — Canonical actor/effect liveness reconciliation

Definition status: **AUTHORED_IN_THIS_PHASE**. Founder ratification required: **true**.

### Intent

Detect durable nonterminal lifecycle states lacking their required actor/effect and reconcile missing effects without duplicating work or retrying completed judgment outcomes.

### Value

Prevent indefinite stalls from lost delivery while avoiding repeated actors against unresolved authority or provider blocks.

### Scope

- Known active nonterminal BIUs: IMPLEMENT expects producer, VERIFY verifier, ACCEPT required closure effect only where its contract requires it.
- Configurable grace and deterministic consistency inspection using invocation, claim, pending effect and correlated outcome evidence.
- Durably correlated, fenced, idempotent recovery plus attention suppression/resolution and meaningful negative controls.

### Non goals

- Backlog discovery polling, status toggling as canonical recovery, disturbing healthy invocations, automatic resolution of human decisions.
- Replacing bounded repair policy or authoring the pending nonterminal retry-budget amendment.

### Dependencies

- SF-REQ-008 existing inbox/effect-intent/outbox/version/fencing model
- SF-REQ-009 lifecycle and claim authority
- SF-REQ-053 durable attention
- SF-REQ-007 custody and SF-REQ-002 admission gates

### Acceptance criteria

- **SF-REQ-056-AC-01**: Drop the original trigger for an authorized known BIU whose state age exceeds configured grace G: at the next reconciliation scan (interval I), identify the expected missing effect and submit one authorized recovery intent. Before G, do not recover. Under a progressing test clock the detection bound is G + I after entry.
- **SF-REQ-056-AC-02**: Fixtures with an active matching invocation, pending claim/effect or correlated completion awaiting projection yield no recovery invocation. ACCEPT without a required closure effect and terminal BIUs yield none.
- **SF-REQ-056-AC-03**: Race delayed original delivery, duplicate recovery scans and two reconciler attempts for the same effect identity; restart between durable intent and effect completion. The fixture must show one effective authorized action and correlated readback, with stale claims refused. A watcher-only absence check is insufficient.
- **SF-REQ-056-AC-04**: A completed FOUNDER_EXCEPTION, HumanDecisionRequired or equivalent judgment-blocking result suppresses relaunch after any number of grace periods and creates or retains one attributable durable attention item.
- **SF-REQ-056-AC-05**: A seen-only notification leaves suppression in place. Explicit resolution under applicable authority (including an attributable resolving acknowledgment) or a newer correlated non-judgment outcome permits reevaluation; stale/out-of-lane resolutions do not.
- **SF-REQ-056-AC-06**: Recovery follows canonical effect paths and retains lifecycle meaning without status toggling. If required authority/custody/fencing evidence is unavailable or inconsistent, record a hold/attention rather than launching speculatively.
- **SF-REQ-056-AC-07**: An isolated negative control removing durable identity fencing fails the concurrent/duplicate fixture, and removing judgment suppression fails the completed-outcome fixture. Retain proven-red output plus restored passing evidence.
- **SF-REQ-056-AC-08**: Before any bootstrap replacement is declared operational, an independently authorized live-profile exercise must demonstrate lost-trigger recovery, duplicate safety, judgment suppression and exact outcome readback on that workload; offline/sandbox proof alone cannot expire SWF-29.

### Authority gaps

- AUTHORED_IN_THIS_PHASE from an undefined ID under the supplied prework definition convention; Founder ratification of this complete specification is required. SWF-29 constrains its meaning but is not treated as a previously complete definition.
- Actual live-profile proof and retirement require separate operational authority; this document authorizes neither.
- Pending SF-REQ-008 durable-control-field elaboration and SF-REQ-022 nonterminal exhaustion amendment remain excluded; recovery must reuse current authority and never grant new retries.

### Security constraints

- Reconciliation cannot bypass actor authorization, candidate custody, resource identity or fencing. Multiple contenders must be safe even if the bootstrap previously relied on a single process.

### Operational constraints

- G and I are explicit configurable positive durations tested at boundaries; the bootstrap five-minute value is historical, not a fixed canonical constant.
- No finite success promise when infrastructure is unavailable; retain recoverable intent/attention and expose failure. Repeated scans cannot create new effect identities to evade deduplication.

### Observability evidence

- BIU/state revision, expected role/effect, age/grace/scan policy, matched claims/outcomes, recovery identity/fence, suppression/resolution link, effect receipt and readback.

### Failure modes

- Lost trigger stalls forever
- Late delivery duplicates recovery
- Completed judgment outcome relaunches endlessly
- Acknowledgment erases unresolved blocker
- Unavailable projection mistaken for missing effect

Sources: [Part 1; judgment-suppression amendment; Binding semantics preserved](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [SWF-29 liveness reconciliation](../../docs/evidence/wave1-bootstrap-retirement-matrix.json); [SEEN != RESOLVED](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [SF-REQ-056 undefined definition status](../../docs/operations/post-wave1-program/prework/POSTW1-SPECIFY-008-inputs.json).

## Operational upstream semantics

These are six semantic steps, not six newly created Project statuses. SWF-25 keeps DESIGN and DESIGN VERIFICATION inside SPECIFY/PLAN. The following are prospective operating requirements; this document does not move work between lanes.

### CAPTURE

- **meaning:** Retain a candidate need and its source/authority status without treating receipt as approval.
- **entry:** Identifiable source proposal, decision or existing requirement with provenance.
- **actor:** Existing intake/operator authority; deterministic inventory records facts, product authority resolves admission.
- **operation:** Identify and deduplicate against existing owners; preserve immutable source and distinguish reference, definition, retirement and unresolved authority.
- **output:** Source-linked candidate identity, ownership/overlap disposition and authority status.
- **exit gate:** A canonical authorized requirement or explicitly flagged in-scope authored draft can enter SPECIFY; unsupported proposals remain candidates.
- **failure:** Conflicting or absent authority is recorded for decision; no BIU or scheduling assignment is inferred.
- **evidence:** Pinned source, identity/overlap decision and admission attribution.
- **owners:** SF-REQ-011, SF-REQ-012
- **visible state:** Existing CAPTURE semantics; no product-intake automation or Project edits implied.

### SPECIFY

- **meaning:** Close intent, value, scope, exclusions and feasible acceptance/evidence meaning before design.
- **entry:** Identified in-scope requirement and authoritative source revisions.
- **actor:** Requirement analyst under existing product authority; Founder resolves product gaps and ratifies newly authored definitions.
- **operation:** Write the eleven fields, distinguish selected/rejected candidates, expose amendment dependencies and resolve ambiguity through attributed decisions.
- **output:** Versioned requirement specification, feasible acceptance predicates and explicit authority-gap disposition.
- **exit gate:** No unanswered product meaning is delegated to design. A ratification-pending specification may support explicitly conditional candidate design, but cannot be represented as adopted authority or execution-ready.
- **failure:** Unresolved intent returns to clarification; excluded pending extensions cannot leak into selected scope.
- **evidence:** Specification revision, authority references, ambiguity decisions and acceptance-feasibility review.
- **owners:** SF-REQ-011, SF-REQ-012, SF-REQ-014
- **visible state:** Existing SPECIFY semantics.

### DESIGN

- **meaning:** Close architecture, interfaces, trust, persistence, failure/recovery and verification decisions through a proportionate Design Contract and independent Design Verification.
- **entry:** Specified product meaning, with any conditional ratification clearly visible.
- **actor:** Designer followed by mechanical checks and an independent design reviewer; product questions return to their authority.
- **operation:** In a later authorized phase, prepare the contract, verify conformance/premises, and separate fixed decisions from implementation-local freedom.
- **output:** Identifiable Design Contract plus mechanical and independent verification results.
- **exit gate:** Required decisions closed, conformance and feasible proof accepted, unresolved authority surfaced; no BIU decomposition bypasses this gate.
- **failure:** Failed premise or authority conflict holds affected design; material revisions require re-verification.
- **evidence:** Design revision, fixed/deferred decision inventory, premise evidence and independent findings.
- **owners:** SF-REQ-051
- **visible state:** Semantic sub-stage/gate within SPECIFY/PLAN per SWF-25; not a new visible Project lane. This phase does not write a Design Contract.

### PLAN

- **meaning:** Arrange approved requirements and verified design into bounded deliverable extents and a coherent dependency plan.
- **entry:** Specified requirements and approved verified design, with explicit authority for the planned scope.
- **actor:** Planning authority prepares the dependency/coverage plan; Founder resolves scope, scheduling or decomposition changes outside delegation.
- **operation:** Allocate intent and proof coverage, identify prerequisite predicates and capability/budget constraints, validate the DAG without inventing priority.
- **output:** Versioned decomposition plan and requirement/obligation coverage graph.
- **exit gate:** No orphan obligations, unresolved endpoints or cycles; plan respects fixed design and authority. Existing-decomposition revisions require separate approved split/replan authority.
- **failure:** Unowned scope or infeasible dependency returns to SPECIFY/DESIGN or a planning decision; no automatic readiness.
- **evidence:** Source/design links, coverage manifest, graph and validation result.
- **owners:** SF-REQ-013, SF-REQ-014
- **visible state:** Existing PLAN; no pending SF-REQ-013 amendment enacted.

### TASKS

- **meaning:** Materialize bounded BIU contract candidates from the authorized plan and prepare them for readiness assessment.
- **entry:** Approved bounded decomposition and verified design references.
- **actor:** Compiler/contract author and deterministic lint; Agent-Ready is the separate readiness assessor.
- **operation:** Populate SF-REQ-010 contract duties, fixed decisions, baseline, dependency predicates, capabilities/budgets, candidate custody and pre-implementation verification/evidence obligations.
- **output:** Identifiable BIU contracts, lint findings and assessment input manifest.
- **exit gate:** Complete current contracts with resolved boundaries, authority, dependencies and design verification can be assessed; TASKS itself authorizes no implementation.
- **failure:** Missing/ambiguous fields hold assessment/admission; changed contract invalidates applicability of prior assessment without deleting it.
- **evidence:** Contract revisions, source/design/plan linkage, lint results and assessment lineage.
- **owners:** SF-REQ-010, SF-REQ-013, SF-REQ-014, SF-REQ-015
- **visible state:** Existing TASKS; no worker contracts are changed by this specification.

### READY

- **meaning:** An applicable Agent-Ready assessment establishes preparedness, separate from execution release.
- **entry:** Current complete BIU contract with required verified design and an attributable fresh READY assessment.
- **actor:** Agent-Ready assesses; canonical release policy separately evaluates authorization, baseline, dependencies and WIP.
- **operation:** Bind readiness to exact assessed inputs. Retain non-READY outcomes and failed attempts distinctly. Invalidate applicability on material changes and obtain a fresh assessment.
- **output:** Readiness record plus a separate admission/release eligibility result.
- **exit gate:** IMPLEMENT requires applicable READY plus SF-REQ-002 admission and release policy, satisfied lifecycle dependencies, capabilities and capacity. No manual Project edit can grant execution authority.
- **failure:** BLOCKED, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED, stale verdict or failed attempt holds affected work and routes the appropriate decision/reassessment.
- **evidence:** Immutable assessment, input revision, separate release/baseline record and refusal reasons.
- **owners:** SF-REQ-015, SF-REQ-002, SF-REQ-051
- **visible state:** Existing READY; preparedness is not execution authorization.

## Pending amendments

Five distinct amendment interfaces are tracked. None is approved. Each excluded extension depends on its decision; the bounded selected core does not assume that decision lands.

- **SF-REQ-008** — Explicit durability of budgets, retries, attention acknowledgments and snapshot confirmation/effect receipts. Use current crash-safe primitives and existing SWF-27/29 duties. Do not treat the proposed extra control-field or receipt model as approved implementation scope. Decision: POSTW1-DECIDE-007A.

- **SF-REQ-022** — Durable exhaustion for repeated nonterminal/ineligible/rework outcomes. Do not add a new run/retry budget policy via liveness or assessment processing. Hold and escalate under existing authorized policy; design must request approval before adopting the extension. Decision: POSTW1-DECIDE-007A.

- **SF-REQ-013** — Conserved transaction for revising an existing decomposition. Selected SF-REQ-013 stops at initial compilation. Full split/replan remains excluded pending its own ownership decision. Decision: POSTW1-DECIDE-007A, POSTW1-DECIDE-005A.

- **SF-REQ-025** — Coordinator-tool invocation environment isolation and authentication precedence. Preserve existing credential/sandbox constraints; do not assign environment-construction ownership or approve schema/tool changes. Decision: POSTW1-DECIDE-007A.

- **SF-REQ-029** — Provider-neutral started/progress/terminal/capacity normalization. Use attributable observable events and explicit unavailable telemetry. No ownership of normalization is transferred to SF-REQ-053; observer replacement is deferred. Decision: POSTW1-DECIDE-007A.

## Bootstrap replacement coverage

| Candidate | Phase 6 disposition | Canonical target / evaluation |
|---|---|---|
| BOOTSTRAP-M01 — SWF-21 release authority | NEEDS_DECISION | SF-REQ-001/SF-REQ-002: DEFER live automatic-release migration: Wave 1 release grant cannot authorize Wave 2; needs explicit next release owner and live-profile cutover proof under POSTW1-DECIDE-006A. |
| BOOTSTRAP-M02 — SWF-29 liveness reconciliation | KEEP_UNTIL_REPLACED | SF-REQ-056: FOLD INTO selected SF-REQ-056; no second replacement requirement. Retain bootstrap until operational proof and authorized retirement. |
| BOOTSTRAP-M03 — SWF-27 observer | KEEP_UNTIL_REPLACED | SF-REQ-029: DEFER live trajectory replacement under existing owner; no Wave reassignment or unapproved normalization amendment. SF-REQ-053 consumes observations but does not take over their ownership. |
| BOOTSTRAP-M04 — attention queue | KEEP_UNTIL_REPLACED | SF-REQ-053: FOLD INTO selected SF-REQ-053 durable attention and SF-REQ-035 integration dependency; retain history and distinguish attention from decision authority. |
| BOOTSTRAP-M05 — Windows notification | NEEDS_DECISION | SF-REQ-035: DEFER notification adapter/removal decision to POSTW1-DECIDE-006A. Selected SF-REQ-053 requires durable failed-attempt evidence but does not select a channel or authorize removal. |
| BOOTSTRAP-M06 — session-bound attention waiter | NEEDS_DECISION | SF-REQ-053: FOLD INTO selected SF-REQ-053 activation/notification boundary; actual resident exit/consumer transfer remains POSTW1-DECIDE-006A work. |
| BOOTSTRAP-M07 — coordinator checkpoint | KEEP_UNTIL_REPLACED | SF-REQ-053: FOLD INTO selected SF-REQ-053 fresh-context reconstruction proof; historical checkpoint existence is not tested equivalence. |
| BOOTSTRAP-M08 — PRODUCER-on-Claude temporary profile change | REVERT_TEMPORARY_CHANGE | operational profile owner: REJECT as new product work: this is a separately authorized narrow profile reversion or new scoped exception, not an unbuilt requirement. Do not restore a profile or assume current readiness here. |
| BOOTSTRAP-M09 — Node/bootstrap execution authority | KEEP_UNTIL_REPLACED | Architecture Authority sections 42-43: DEFER sovereignty/cutover: requires full live conformance, one-writer migration and nonduplicating rollback. PY-10 sandbox success is insufficient and no Wave 2 migration assignment is invented. |
| BOOTSTRAP-M10 — sandbox ingress tunnel | NEEDS_DECISION | sandbox operations authority: DEFER retention/retirement decision to POSTW1-DECIDE-006A. No new product requirement is needed to decide infrastructure custody; current tunnel remains untouched. |
| BOOTSTRAP-M11 — eighteen external bootstrap modules | NEEDS_DECISION | component-specific existing owners: DEFER module-by-module custody and maintenance decision to POSTW1-DECIDE-006A; no blanket product adoption or deletion of the external bundle. |
| BOOTSTRAP-M12 — resident coordinator multi-BIU tenure | NEEDS_DECISION | SF-REQ-053: FOLD INTO selected SF-REQ-053 bounded tenure target; actual handoff and any resident exception remain explicit operational decisions under POSTW1-DECIDE-006A. |
| BOOTSTRAP-M13 — Program Director mailbox bridge waiter | KEEP_UNTIL_REPLACED | post-Wave1 program authority: REJECT as permanent product requirement: retain or hand off the separate program-message consumer for unfinished program duties. No evidence warrants making this temporary mailbox a new Wave 2 product mechanism. |
| BOOTSTRAP-M14 — SWF-26 PY-04 mutation gate | RETIRE_CANDIDATE | SF-REQ-050 general proof; expired SWF-26 exception: REJECT replacement of an already expired PY-04-only role. Preserve its historical proof; use ordinary independent verification and existing general promotion authority. |
| BOOTSTRAP-M15 — bootstrap release-admission gate | KEEP_UNTIL_REPLACED | SF-REQ-002: DEFER live release-admission replacement as a distinct migration obligation under an existing owner. Selected upstream readiness supplies inputs but cannot retire the live six-precondition gate. No new Wave assignment or release authority. |
| BOOTSTRAP-M16 — b-disp command compatibility alias | KEEP_UNTIL_REPLACED | installation migration under rename decision: REJECT new product requirement: canonical command already exists; missing evidence is installation-by-installation migration. Preserve compatibility aliases and persisted identities until separately authorized proof permits removal. |
| BOOTSTRAP-M17 — Local Program Director bootstrap orchestration role | KEEP_UNTIL_REPLACED | bounded post-Wave1 program authority: REJECT permanent productization of the temporary Director role. Complete or disposition program duties and preserve state under its existing authority; no new product owner or lifecycle is implied. |

## Review and proof limits

Each selected criterion states controlled inputs or identifiable artifacts and observable pass/refusal evidence; negative cases discriminate the invariant. Human judgment is an attributable review outcome, not an impossible universal correctness proof.

Specified tests are prospective obligations, not executed capability proof. No selected criterion claims current implementation or live availability. Timing guarantees are bounded by configured grace/scan in controlled progressing fixtures; unavailable infrastructure yields explicit hold.

No unverifiable acceptance criterion was found in the selected set. This is an author feasibility review, not independent review or proof the capabilities already exist. Both supplied checkers are run separately; their results establish their stated contracts, not semantic approval.

Targeted coordinator review remains pending for these historical dependencies:
- SF-REQ-015: Confirm retained PY-10 assessment sequence and immutable reassessment interpretation against Phase 4; do not infer coercion from current-file retention.
- SF-REQ-053: Confirm activation/monitoring distinction and LRN-027 absence of exercised handover; no checkpoint success is presumed.
- SF-REQ-056: Confirm missing-effect versus completed-judgment suppression and SEEN versus RESOLVED from SWF-29/PY-09.
- BOOTSTRAP-M01 through BOOTSTRAP-M17: Review only mapped Phase 6 historical component duties/expiry dependencies where challenged; this phase makes no fresh live-state claim.

## Provenance and disposition

Baseline: `d83e87e6f2bb4ff90ff4f4f0e3940582f8d5c998`; branch `main`; worktree `/mnt/d/Projects/alienintent`. Git identity: netmarine / sanuk.du@gmail.com. Source SHA-256 manifest and preserved phase-setup changes are recorded in JSON. Local retained evidence only; no network or fresh live-state verification.

Outputs are in the existing worktree at `/mnt/d/Projects/alienintent/docs/evidence/wave2-specified-requirements.json` and `/mnt/d/Projects/alienintent/docs/evidence/wave2-specified-requirements.md`. No temporary branch/worktree was created.

**PARKED_FOR_TARGETED_REVIEW** under the direct no-commit/no-push/no-network instruction. The two outputs are the only authorized repository edits. Next action: targeted historical review and explicit handling of the recorded Founder gates; adoption/publication requires separate authorization. No Phase 9 work or lifecycle/program-state transition was performed.

DISPUTED: NONE.

## Validation

- SPECIFY checker: exit 0, PASS, zero failures.
- Wave 1 checker: exit 0, PASS, 1,075 checks, zero failures, 13/13 negative controls killed.
- Scope verification: all original tracked files and phase-setup inputs retain their original bytes. Only the two requested deliverables were added.

Checks do not confer independent review, product adoption or operational approval. Exact commands and result details are retained in JSON.
