# BIU split / replan process design

Authoritative design proposal for independent Claude bootstrap coordinator review; not enacted Product Requirement, runtime or lifecycle authority.

Splitting may change decomposition, but it must conserve authorized intent and proof obligations.

## Decision

Original lifecycle role: **retained_integration_parent**. Proposed identity grammar: `\A(?:(?:PG|PY)-[0-9]{2}|WO-[0-9]{6})(?:[A-Z])?\Z`.

## Authority

SPLIT_RECOMMENDED is a recommendation, not mutation authority. Under SWF-21/SWF-33 and the Phase 4 matrix, the Founder authorizes a change to the Founder-approved decomposition by a durable decision naming exact input revisions, resulting contracts, mappings and graph. A coordinator may prepare and apply that exact decision within delegation; Agent-Ready, producers, verifiers and the Program Director task dispatch cannot independently authorize a decomposition change or product intent change. A future delegation must explicitly grant planning authority and its bounds. This document proposes a process, not that delegation. Missing authority holds affected work and emits a durable decision request.

## Lineage

Retain original BIU identity and immutable contract revision. One split record links its assessment, decision, pre/post contract hashes, original and resulting requirement extents, child IDs, integration parent, dependency graphs, assessment supersession and evidence manifests. Children carry split_from and the same operation ID; the parent records all children. A repeated operation ID with identical payload returns the same result; a different payload conflicts. No renumbering, deletion of history or inference of ancestry from a suffix. The real lineage is PY-10 -> {PY-09B, retained PY-10}; there is no second child in this incident.

## Requirement conservation

Inventory every original requirement, acceptance criterion, verification obligation and evidence obligation from the immutable original contract plus its referenced binding authority. Use stable obligation IDs and verbatim text, source revision, destination extent and rationale; mappings are nonempty and resolve to resulting contracts. Shared mappings mean all stated extents must be proven, never an OR. Every destination obligation also points back to an original obligation or an explicitly approved elaboration of an existing requirement. UNKNOWN tracing remains allocated to the integration parent for custody, expressly unsatisfied, and blocks activation and closure until resolved. A mapping is not proof of satisfaction. The incident inventory below preserves whole clauses where they contain several conjunctive duties; none of those duties may be dropped.

## Scope conservation

Compare the union of resulting authorized extents to the original authorized product intent, including exclusions, architecture, capabilities, budget and proof strength. Assign implementation responsibility without weakening original integration proof. Newly explicit prerequisite work needs an existing requirement owner plus a planning decision: SWF-33 assigned previously unnamed transport to PY-09B under SF-REQ-005/007/038, not by pretending it was already explicit PY-10 scope. Unowned product semantics stop as an authority gap. A split grants no extra spend, credentials, concurrency or deployment permission; child budgets partition the authorized envelope and the parent retains integration budget, with any increase requiring separate authority.

## Dependency rewriting

Use predecessor -> dependent edges and retain their lifecycle satisfaction predicates. For original O with incoming predecessors P, resulting children C and retained parent O: preserve every pre-existing edge, copy each P -> O prerequisite to each child P -> c with the identical predicate, add each c -> O requiring child DONE, and add only expressly approved inter-child edges. Every old downstream O -> d stays O -> d with its original predicate: children cannot substitute for the integration completion boundary. Thus all downstream rewrites are identity rewrites recorded explicitly, not judgment calls or redirection to whichever child seems relevant. Reject self-edges, cycles, unresolved endpoints, weakened predicates or unspecified inter-child ordering. No transitive-edge pruning. The incident graph delta is detailed below; this future default is deliberately conservative and does not rewrite historical accepted-vs-DONE predicates.

## Identity allocation

Adopt the explicit full-string grammar below as a proposed first grammar, not an observed parser. Preserve case, family and existing widths: PG/PY two digits and WO six digits, optionally one uppercase ASCII suffix. Preserve all existing identities, including PY-09B and WO-000013; no migration or alias normalization. New children default to the lowest unused positive unsuffixed number in the original family at its fixed width, reserved atomically against all active, retired and reserved IDs. Zero is syntactically compatible but not newly allocated. A decision may explicitly reserve an unused suffixed insertion identity; it must name the complete ID, never derive lineage or dependencies from sorting. Collision fails closed; exhaustion requires a separately approved grammar extension, never truncation, width growth or reuse. PY-09B is preserved as the historical explicit SWF-33 allocation, not regenerated by the default allocator.

## Lifecycle semantics

Choose retained_integration_parent: original O remains an executable integration BIU with the same identity and final satisfaction boundary, consuming independently proven child work. This is a decomposition role, not a new lifecycle Status. Preserve historical statuses and assessments; do not mark O DONE, cancelled or superseded merely because children exist. Place an admission hold during replan; changed contracts require fresh readiness and ordinary lifecycle admission. Children and parent traverse the existing lifecycle independently, and parent implementation waits for declared prerequisites. Do not split an active invocation in place: hold release and wait for its existing terminal/safe recovery boundary under separate authority; do not cancel it through this operation. An already DONE original cannot be reopened by this design.

## Agent ready invalidation

A decomposition commit makes previous assessments inapplicable to the new contract/baseline; retain them as immutable history with explicit reassessment links. Reassess all new children and the changed parent, plus any existing unit whose assessed contract, baseline, dependency semantics or material prerequisite changed. READY is necessary but not sufficient for IMPLEMENT: normal authority, custody, baseline, dependency and release gates still apply. BLOCKED triggers reassessment after documented prerequisite resolution; NEEDS_CLARIFICATION after attributable Founder clarification and contract correction; SPLIT_RECOMMENDED after the authorized decomposition correction and relevant input/prerequisite change. None permits implementation. Provider/tool failure or malformed/unknown results remain failed assessment attempts with a hold and bounded authorized retry after recovery, never READY. For PY-10 preserve BLOCKED -> SPLIT_RECOMMENDED -> fresh READY and require PY-09B complete before the final reassessment as SWF-33 specifies.

## Project projection

Canonical approved split state is the source; Project is a one-way projection, never split authority or execution truth. Project views show the original integration role, exact child identities, lineage, satisfaction links, dependency predicates and current lifecycle/readiness separately. Use durable idempotent delivery keyed by operation ID and target revision, expected-version fencing, exact resource identity and readback. Partial delivery records pending/failed targets and retries the same payload; no duplicate BIUs and no readiness advance from a Project edit. Hold affected release until required contract/Issue/Project projection consistency is confirmed; unrelated work continues. No new Project status or field is assumed available: bindings require approved configuration, otherwise activation remains held. This design changes no Project.

## Evidence

Retain the source contract and authority snapshots, recommendation and provider provenance, authorizing decision, obligation inventory and trace verdicts, before/after graph, reserved identities, scope/budget comparison, independent design review, validated payload hash, commit/readback receipts, and fresh assessment/release links. Definition, observed artifact and verdict stay distinct. Capture exact revisions and command exit statuses; redact credentials and installation details. Existing accepted evidence survives with its scope and baseline; supersession requires an explicit record and replacement proof, never silent deletion. The mapping below demonstrates contract traceability, not a new live proof or terminal verdict. Checker success establishes only the checker contract; it does not prove inventory completeness, authorization or implementation.

## Closure

The original intent is satisfied only when every child is DONE under its ordinary closure policy, the retained integration parent has independently verified every original acceptance/verification obligation at the required integrated scope, all requirement extents and retained evidence are accounted for, UNKNOWN traces and authority gaps affecting activation are resolved, and the parent completes ACCEPT -> DONE with its existing landing/evidence duties. Child completion alone, Issue closure, split commit or Project projection is insufficient. No extra live rerun is required when trusted accepted evidence already establishes it. Record an original-obligation-to-accepted-evidence completion manifest and reconcile canonical/project closure. Failed children leave the parent incomplete; abandoning a child requires another authorized conserved replan, not dropping its rows.

## Operation protocol

1. PREPARE: freeze original contract/graph/authority revisions and applicable requirements; record recommendation, current invocations, proposed identity reservations, complete obligations, boundaries and budget. Hold affected admission; no lifecycle verdict is synthesized.
2. REVIEW: validate total mapping, reverse scope coverage, dependency predicates and DAG, unique IDs, unchanged intent/proof strength, projection bindings and assessment invalidation set; independent reviewer records findings. Any UNKNOWN or conflict stops activation.
3. AUTHORIZE: Founder or explicitly delegated planning authority approves the exact payload hash and revisions. Material review changes require a new approved payload; a generic split approval cannot authorize unspecified scope.
4. APPLY: compare expected revisions and reservation state under one canonical operation boundary, record original/children/contracts/graph/invalidation and durable projection work atomically. Concurrent revision change aborts without partially activating the split. Prior staged/reserved state is non-executable. Same operation ID is idempotent; different content conflicts. Atomic mechanism is a future implementation obligation, not an implemented capability claim.
5. RECOVER: if canonical apply did not commit, retry only after validating current expected revisions; if it did commit, resume recorded projection/readback work without allocating again. Partial external writes never become canonical truth; affected release stays held. Do not roll back a committed split by erasing history; any reversal is another authorized conserved replan.
6. REASSESS: after canonical and required external records agree, assess each affected contract at its eligible current baseline. Preserve old verdicts. Release only fresh READY work through normal admission; reassess parent after children and prerequisites are complete.
7. CLOSE: discharge all obligation extents with accepted evidence and ordinary child/parent closure. Record the conserved original intent as satisfied only at parent DONE.

## Ownership

SF-REQ-013 by amendment. Current verdict: ownership gap.

SF-REQ-013 says only to lower governed requirements into bounded BIUs with explicit satisfaction links and dependency DAGs. It does not specify revision of an existing decomposition or conservation/transaction semantics. SF-REQ-015 checks unresolved decisions, boundaries, missing acceptance/verification, architecture and dependencies, while preserving Agent-Ready authority; checking an input is not authority or an operation to rewrite it. SWF-33 authorizes this particular split, not a general product mechanism. Neither candidate presently owns the complete operation explicitly.

Amend SF-REQ-013 to own recompilation of existing BIUs with this conserved transaction; use SF-REQ-015 for validation checks and preserve Agent-Ready assessment authority. No new requirement recommended or enacted.

G1 assessment implementation/schema/CLI ownership and G2 canonical serialization ownership remain unresolved carryovers per Phase 4. They are not resolved or double-counted as new split gaps; integration with them requires authority before implementation.

## Historical conservation inventory

One row per identified contract clause/obligation; a compound clause retains every conjunct in full. Scope 4/5, closure evidence and repair records retain the additional evidence obligations. Binding rules, constraints, closure and readiness obligations are included rather than omitted from the four-kind inventory. Requirement-kind constraint rows are contract obligations, not newly created Product Requirements.

Trace to resulting authorized contracts only. No claim that a proposed conservation record existed historically, and no reinterpretation of later SWF-34 as part of the original SWF-33 payload. Current child contract was read for context; historical split references resolve at the split commit.

69 obligations; 13 requirement links, 17 acceptance criteria and three primary verification bullets; 0 untraceable obligations. Child A is PY-09B; retained integration parent is PY-10; child B is unused.

Each row below is contract traceability, not a satisfaction verdict. Full original text, immutable source and destination references are in the authoritative JSON.

| Obligation | Kind | Destination | Rationale |
|---|---|---|---|
| SF-REQ-001 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-002 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-003 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-004 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-005 | requirement | child_a, retained_integration_parent | TRACED: SWF-33 assigns the live substrate extent to PY-09B under this existing requirement; PY-10 retains its original live integration extent verbatim. Both extents are required, not interchangeable. |
| SF-REQ-006 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-007 | requirement | child_a, retained_integration_parent | TRACED: SWF-33 assigns the live substrate extent to PY-09B under this existing requirement; PY-10 retains its original live integration extent verbatim. Both extents are required, not interchangeable. |
| SF-REQ-008 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-009 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-010 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-034 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-035 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| SF-REQ-038 | requirement | child_a, retained_integration_parent | TRACED: SWF-33 assigns the live substrate extent to PY-09B under this existing requirement; PY-10 retains its original live integration extent verbatim. Both extents are required, not interchangeable. |
| PY-10-AC-01 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-02 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-03 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-04 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-05 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-06 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-07 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-08 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-09 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-10 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-11 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-12 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-13 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-14 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-15 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-16 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-AC-17 | acceptance_criterion | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-VERIFY-01 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-VERIFY-02 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-VERIFY-03 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-01 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-02 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-03 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-04 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-05 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-BIND-06 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-SCOPE-01 | requirement | retained_integration_parent | TRACED: original dedicated sandbox prerequisite is retained as provisioned infrastructure consumed by PY-10 Scope 1. SWF-33 adds explicit ownership of previously unnamed live transport in PY-09B; it does not transfer sandbox provisioning into that child or delete the environment obligation. |
| PY-10-SCOPE-02 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-SCOPE-03 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-SCOPE-04 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-SCOPE-05 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-INTENT | requirement | retained_integration_parent | TRACED: the original constraint remains in PY-10 after the split; additional SWF-33 reference clarifies substrate ownership without deleting the original constraint. |
| PY-10-ARCH | requirement | retained_integration_parent | TRACED: the original constraint remains in PY-10 after the split; additional SWF-33 reference clarifies substrate ownership without deleting the original constraint. |
| PY-10-EXCLUSIONS | requirement | retained_integration_parent | TRACED: the original constraint remains in PY-10 after the split; additional SWF-33 reference clarifies substrate ownership without deleting the original constraint. |
| PY-10-CAPABILITIES | requirement | retained_integration_parent | TRACED: the original constraint remains in PY-10 after the split; additional SWF-33 reference clarifies substrate ownership without deleting the original constraint. |
| PY-10-CLOSURE-01 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-02 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-03 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-04 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-05 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-RULE-01 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-RULE-02 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-RULE-03 | requirement | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-CLOSURE-RULE-04 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-01 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-02 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-03 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-04 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-05 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-RECORD-06 | evidence_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-VERIFY-01 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-VERIFY-02 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-VERIFY-03 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-VERIFY-04 | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-REPAIR-MONOTONICITY | verification_obligation | retained_integration_parent | TRACED: retained verbatim in the post-split PY-10 contract; the original integrated obligation is not discharged by child-only proof. |
| PY-10-READINESS-PREREQUISITES | requirement | retained_integration_parent | TRACED: post-split Readiness retains original predecessors and adds PY-09B. SWF-33 is the required Founder decision, and expressly requires a fresh READY against the current baseline with PY-09B complete; neither prior verdict is converted. |

## Provenance and disposition

Read HEAD: `f9b7ebfbf56cd6d407c8301f30818a367d92f857`. Original contract: `1f16b816cb0d30681eacbb2ea178eb2cf92ddd02:docs/work-units/python/PY-10.md`. Post-split contract: `35de8d7e9fa0e06f3e3e54e5fe546d78994883ec:docs/work-units/python/PY-10.md`.

Offline repository evidence only; no current remote, product acceptance or live operation claim. No memory-derived facts used. Grammar absence accepted from supplied prework; design-critical contract and ownership claims checked locally.

Prework reports PG-NN 20 and PY-NN 11 plus one suffix. Assessment filenames inspected contain PG-01 through PG-19, PY-01 through PY-10, PY-09B and WO-000013. These are different inventory surfaces; no count-dependent allocator or claim of exhaustive global absence is made. Supplied absence-of-grammar finding is used as prework, not independently reproven by a repository-wide search.

PARKED: Task explicitly forbids commits, pushes, network and authority amendments; delivery is uncommitted design artifacts for independent review.

Claude bootstrap coordinator independently reviews these two artifacts; any enactment or publication requires separate authority. No Phase 6 begun.

No branch or worktree created.

## Validation

Design check: PASS, exit 0. Wave 1 check: PASS, exit 0; 1,075 checks, zero failures, 13/13 negative controls killed. Offline consistency only; `origin/main` is a local stored ref, not freshly verified remote state.

PASS: unique obligation IDs, bound destinations, grammar valid/invalid examples, and all 68 verbatim clauses found in the original Git blob; readiness row is an explicit summary.

Independent Claude bootstrap coordinator design review pending; no self-approval or enactment.
