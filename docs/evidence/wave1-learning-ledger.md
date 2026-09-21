# Wave 1 Learning Ledger

Authoritative artifact: [wave1-learning-ledger.json](wave1-learning-ledger.json). Status: **ANALYSIS_FOR_COORDINATOR_REVIEW**.

Task `POSTW1-LEARN-002`; actor `codex/gpt-6-astra`; recorded `2026-09-21T18:36:03Z`. Repository HEAD `473f026255a11193027f511f6ba9ced45734281e`; Wave 1 terminal implementation `10cc81620511af56befbb6140504d1991bb02846`.

30 lessons from 101 enumerated raw candidates (97 mapped, 4 not promoted). 2 ownership gaps; 0 new requirements; 100 scalar fields recorded UNKNOWN.

| Disposition | Lessons |
|---|---:|
| ALREADY_GRADUATED | 9 |
| STRENGTHEN_EXISTING_OWNER | 17 |
| GAP_TRAP_PROMOTION | 1 |
| NEW_CAPABILITY_GAP | 2 |
| BOOTSTRAP_ONLY | 1 |

Accepted Phase 0+1 terminal reconciliation. Local repository artifacts and retained captures only; no network or live operation.

Author validation is not the resident coordinator's independent review. No acceptance, merge, publication, lifecycle change or Phase 3 action is authorized by this artifact.

## Definitions and counting boundaries

**artifact_scope** — New scoped analysis artifact, not a trajectory event. Uses schema_version, recorded_at, provenance, repository evidence_refs and explicit UNKNOWN in the established evidence conventions; it does not claim conformance to either trajectory/quality schema.

**materiality** — A lesson is a distinct preventable failure or materially unproven control boundary with an existing owner or explicit ownership gap. Individual implementation defects are grouped by the control that would prevent or expose them. Participant-only candidates may inform hypotheses, never establish incident totals.

**raw_candidate_count** — Number of explicitly enumerated RAW entries considered, including four non-promoted hypotheses. It is not an incident count, unique-defect count or sum of verifier findings. Multiple raw propositions may describe the same incident.

**recurrence_count** — Count only the independently enumerated episodes/defects in occurrence_basis for this lesson, including its originating occurrence. Diagnostic repetitions, carried findings, provider retries and mentions do not create extra incidents. Otherwise UNKNOWN.

**occurrence_times** — first_occurrence and last_occurrence are the earliest/latest established incident instants within the scoped occurrence population, not decision-document dates or publication dates. Unestablished bounds remain UNKNOWN; identical instants denote one observed occurrence.

**originating_BIUs** — Known attributable BIUs are a list. Where no BIU attribution can be established, the value is the string UNKNOWN under task section 2.2, rather than an invented BIU or an empty list implying no attribution gap. This applies to the cross-cutting intake and untested coordinator-replacement lessons.

**enforcement_level** — Strength of the exercised mechanism for the scoped lesson, not completion status of the entire Product Requirement. A recorded test claim without retained execution or consumption does not establish a deployed deterministic gate.

**proven_red** — yes means retained semantic mutation, negative-control, or an actual meaningful invalid-input refusal by the applicable gate. no is used for an explicitly absent owning product control; UNKNOWN where red evidence for that control is not established. Particular red tests do not prove a generalized promotion pipeline or proof sequencing gate exists.

**disposition** — ALREADY_GRADUATED is limited to a named existing owner plus positive observed effectiveness, including review gates; it does not imply the whole owner is implemented. STRENGTHEN covers explicit but incomplete or uneven existing obligations. GAP_TRAP is a recurring concrete mechanically expressible trap to assess under existing owners, not authority to implement it.

**claim_labels** — FACT describes an artifact read, not necessarily an independently reproduced live event. INFERENCE gives the analytical reasoning. HYPOTHESIS is unverified. Raw candidate wording is a proposition under examination, not an accepted factual incident.

**requirement_conservation** — All suggested checks and structural remedies are recommendations for existing owners. No requirement, priority, wave, design mandate, lifecycle meaning or acceptance criterion is created or amended.

**unknown_count** — Count scalar JSON field values exactly equal to UNKNOWN, once at their authoritative JSON path. Do not count mentions inside prose, path names, raw-candidate duplication or the Markdown rendering.

## Cluster tests

### Proof quality — SEVERAL_LESSONS

INFERENCE: four controls are needed: assertion discrimination, actual composed-path execution, proof-before-repair sequencing, and preservation across candidates. Constant assertions and ineffective mutations merge within LRN-001; unit-only, CLI and impossible-store-double cases merge within LRN-002. One generic 'better tests' lesson would hide different missing controls.

Lessons: LRN-001, LRN-002, LRN-003, LRN-004.

Evidence: [docs/decisions/2026-09-20-deterministic-failure-class-promotion.md](../../docs/decisions/2026-09-20-deterministic-failure-class-promotion.md); [docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md](../../docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md); [docs/evidence/execution-trajectories/PY-06.jsonl](../../docs/evidence/execution-trajectories/PY-06.jsonl); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl)

### Identity — SEVERAL_LESSONS

INFERENCE: candidate identity binds bytes and custody; baseline identity binds release authority; attention identity deduplicates observations; terminal result identity admits work verdicts; cycle identity counts lifecycle passes; effect identity prevents duplicate execution. These have different equivalence relations, lifetimes and validators. Candidate publication, retention and partial-work custody merge into LRN-005. D8's BIU grammar claim is provisionally associated with LRN-006's identifier admission, not established as an additional incident.

Lessons: LRN-005, LRN-006, LRN-007, LRN-008, LRN-009, LRN-012.

Evidence: [docs/decisions/2026-09-20-candidate-worktree-retention.md](../../docs/decisions/2026-09-20-candidate-worktree-retention.md); [docs/decisions/2026-09-20-wave1-release-coordinator.md](../../docs/decisions/2026-09-20-wave1-release-coordinator.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/decisions/2026-09-21-biu-execution-cycle-counter.md](../../docs/decisions/2026-09-21-biu-execution-cycle-counter.md); [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md)

### Recovery — SEVERAL_LESSONS

INFERENCE: missing actor detection and delayed confirmation merge into LRN-010; completed blocked effects and suppression merge into LRN-011; provider capacity and governed failover merge into LRN-013; partial-work continuity folds into custody LRN-005. Duplicate prevention, expiry of the failover authorization, bounded nonterminal retries, and durable outcome read-back remain separate proof obligations. Recovery can be safe while still requiring unnecessary human intervention.

Lessons: LRN-005, LRN-010, LRN-011, LRN-012, LRN-013, LRN-020, LRN-029, LRN-030.

Evidence: [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md)

### Specification correctness — ONE_LESSON

INFERENCE: D4's copied permissions and D5's wrong-spec green preflight are one defect. D6's impossible isolation is another instance of validating a contract against the actual consumer/platform before implementing its checker. Both fit independent design verification under SF-REQ-051. The ledger keeps their distinct evidence and residual-risk limits inside one lesson; it does not mistake a corrected exact-set negative control for proof all specifications are correct.

Lessons: LRN-014.

Evidence: [docs/decisions/2026-09-20-design-contract-and-design-verification.md](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md); [docs/operations/py10-sandbox.md](../../docs/operations/py10-sandbox.md); [docs/decisions/2026-09-21-sandbox-isolation-standard.md](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md)

### Decomposition — ONE_LESSON

INFERENCE: SPLIT_RECOMMENDED, unowned transport, PY-09B lineage, predecessor rewrite and preserved requirement extents are one scope-conservation event. A split is useful here because it moves an owned implementation boundary while retaining total proof, not because the cycle count is high. Runtime projection drift is separately LRN-016; proposal-to-requirement deduplication is separately LRN-018.

Lessons: LRN-015.

Evidence: [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md); [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md)

### Observability — ONE_PROVISIONAL_LESSON

INFERENCE: provider log differences, normalized progress and buffered/streaming presentation belong to one provider-neutral observation boundary. FACT: raw terminal shapes and argument modes differ. HYPOTHESIS: buffering caused apparent stalls; comparative progress timing is not retained. Activation LRN-019 and diagnostic coalescing LRN-024 are adjacent controls, not evidence that a provider progress normalization mechanism exists.

Lessons: LRN-023.

Evidence: [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [src/providers/claude.mjs](../../src/providers/claude.mjs); [src/providers/codex.mjs](../../src/providers/codex.mjs); [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md)

## Learning records

### LRN-001 — EVIDENCE_PROOF_DEFECT

| Field | Value |
|---|---|
| learning_id | LRN-001 |
| failure_class | EVIDENCE_PROOF_DEFECT |
| originating_BIUs | PY-01, PY-02, PY-04, PY-05, PY-06, PY-08, PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-deterministic-failure-class-promotion.md](../../docs/decisions/2026-09-20-deterministic-failure-class-promotion.md); [docs/evidence/execution-trajectories/PY-02.jsonl](../../docs/evidence/execution-trajectories/PY-02.jsonl); [docs/evidence/execution-trajectories/PY-05.jsonl](../../docs/evidence/execution-trajectories/PY-05.jsonl); [docs/evidence/execution-trajectories/PY-09.jsonl](../../docs/evidence/execution-trajectories/PY-09.jsonl); [docs/evidence/PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [docs/evidence/py09b-proven-red-2026-09-21.json](../../docs/evidence/py09b-proven-red-2026-09-21.json); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SF-REQ-050 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | yes — a semantically applicable guard removal or inversion must make its assertion fail; SURVIVED and NOT_APPLIED cannot count as KILLED. |
| proven_red | yes |
| later_consumption | FACT: docs/evidence/PY-09B-live-transport.md records two overdetermined tests corrected before completion; docs/verification/PY-10-wave1-live-proof.md records the query-selection blind spot caught in PY-10. |
| effectiveness_evidence | FACT: PY-09's gutted validator left 183 tests green; PY-09B later retained 13/13 red guards and PY-10 22/22. These are specific batteries, not an implemented general promotion pipeline (docs/evidence/py09b-proven-red-2026-09-21.json; docs/evidence/py10/proven-red.json). |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: all four are discrimination failures against a stated obligation. Retain SF-REQ-050; specific successes do not establish general graduation. Historical finding mentions are not a deduplicated recurrence count.

### LRN-002 — unexecuted-composition-path

| Field | Value |
|---|---|
| learning_id | LRN-002 |
| failure_class | unexecuted-composition-path |
| originating_BIUs | PY-06, PY-07, PY-08, PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/evidence/execution-trajectories/PY-06.jsonl](../../docs/evidence/execution-trajectories/PY-06.jsonl); [docs/evidence/execution-trajectories/PY-07.jsonl](../../docs/evidence/execution-trajectories/PY-07.jsonl); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl); [docs/evidence/execution-trajectories/PY-09.jsonl](../../docs/evidence/execution-trajectories/PY-09.jsonl) |
| existing_owner | SF-REQ-014 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — execute each required operation through its real composition root and required failure path; dynamic reachability needs obligation-specific probes, not a universal static graph rule. |
| proven_red | yes |
| later_consumption | FACT: PY-06 acceptance re-executed a real CLI child, publication and read-back; PY-08 eventually gained subprocess negatives; PY-09 still exposed unused substrate (docs/evidence/execution-trajectories/PY-06.jsonl; docs/evidence/execution-trajectories/PY-08.jsonl; docs/evidence/execution-trajectories/PY-09.jsonl). |
| effectiveness_evidence | FACT: unit-tested RetrySchedule/ReservationBook objects were unwired, PY-06 composition raised TypeError, PY-07 used an impossible store double, and five of seven PY-08 commands errored under a real profile. PY-06 repaired exception paths were proven red by source reversion. No common composition-coverage admission gate is evidenced. |
| recommended_disposition | GAP_TRAP_PROMOTION |

INFERENCE: these collapse around executable composition, distinct from whether an already-executed assertion discriminates. SF-REQ-014 can absorb the proposed trap without a new requirement; this recommends assessment, not promotion authority.

### LRN-003 — verification-sequencing

| Field | Value |
|---|---|
| learning_id | LRN-003 |
| failure_class | verification-sequencing |
| originating_BIUs | PY-08, PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md](../../docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md); [docs/evidence/PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl); [docs/evidence/execution-trajectories/PY-09.jsonl](../../docs/evidence/execution-trajectories/PY-09.jsonl); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json) |
| existing_owner | SF-REQ-049 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — before widening a repair, require the named harness and changed-path red evidence; judging whether coverage is sufficient remains independent review. |
| proven_red | UNKNOWN |
| later_consumption | FACT: SWF-23 section 4b was carried into PY-09/PY-10; docs/evidence/PY-09B-live-transport.md and docs/verification/PY-10-wave1-live-proof.md record harness-first work and discoveries before the final candidate. |
| effectiveness_evidence | FACT: PY-08's sixth verdict closed the missing explain/kernel proof and subprocess negatives without fresh defects, but still REJECTED carried obligations. PY-09 later violated the sequencing despite its contract. The later first-pass acceptances do not isolate sequencing as their cause. Red evidence exists for particular checks, not for a gate enforcing proof-before-repair ordering. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one sequencing lesson, not three capabilities. SF-REQ-052 supplies related completion-context ideas; SF-REQ-049 owns this preservation/sequencing obligation. Specific red checks worked, but no gate enforces their timing.

### LRN-004 — repair-regression

| Field | Value |
|---|---|
| learning_id | LRN-004 |
| failure_class | repair-regression |
| originating_BIUs | PY-04, PY-07, PY-08, PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md](../../docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/execution-trajectories/PY-04.jsonl](../../docs/evidence/execution-trajectories/PY-04.jsonl); [docs/evidence/execution-trajectories/PY-05.jsonl](../../docs/evidence/execution-trajectories/PY-05.jsonl); [docs/evidence/execution-trajectories/PY-06.jsonl](../../docs/evidence/execution-trajectories/PY-06.jsonl); [docs/evidence/execution-trajectories/PY-07.jsonl](../../docs/evidence/execution-trajectories/PY-07.jsonl); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl) |
| existing_owner | SF-REQ-049 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | yes — compare previously satisfied obligations across candidates and fail lost behavior or proof unless an explicit authorized supersession names replacement evidence. |
| proven_red | yes |
| later_consumption | FACT: PY-05 recorded authorized test supersession; PY-06/PY-07 re-executed preserved obligations; PY-08 still regressed AC7 and diagnostics (docs/evidence/execution-trajectories/PY-05.jsonl; docs/evidence/execution-trajectories/PY-06.jsonl; docs/evidence/execution-trajectories/PY-07.jsonl; docs/evidence/execution-trajectories/PY-08.jsonl). |
| effectiveness_evidence | FACT: PY-04 replaced tests and lost proof for five criteria; PY-07 introduced redispatch after cancellation; PY-08's AC7 regression persisted across two reports. PY-07's source-reversion control caught its cancellation regression. The coordinator's attention fix also regressed the no-invocation case in PY-09. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: behavior loss, proof loss and continuity loss are one cross-candidate preservation invariant. This is distinct from first building the harness. Attention identity itself is LRN-007; its regression is evidence of this independent preservation failure.

### LRN-005 — CUSTODY_IDENTITY_DEFECT

| Field | Value |
|---|---|
| learning_id | LRN-005 |
| failure_class | CUSTODY_IDENTITY_DEFECT |
| originating_BIUs | PY-04, PY-06, PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-candidate-worktree-retention.md](../../docs/decisions/2026-09-20-candidate-worktree-retention.md); [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json) |
| existing_owner | SF-REQ-007 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — refuse VERIFY without exact independent read-back; permit local cleanup only after all seven retention conditions hold, including continuing reachability and absence of unique content. |
| proven_red | yes |
| later_consumption | FACT: SWF-30 was applied to 18 published worktrees with fresh fetched-tree comparisons; PY-09 preserved unique partial work; PY-09B/PY-10 exercised independent custody (docs/evidence/2026-09-20-worktree-retention-audit.md; docs/evidence/2026-09-21-py09-provider-capacity-interruption.md; docs/evidence/PY-09B-live-transport.md; docs/verification/PY-10-wave1-live-proof.md). |
| effectiveness_evidence | FACT: PY-04 verdict 9 could not identify its candidate; its presumptive SHA remains UNKNOWN as custody. Later custody gates and PY-10's custody-recheck mutation failed meaningfully. The audit retained sole copies and active work while removing redundant copies. Graduation is for this scoped identity/retention invariant, not universal automated cleanup. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: these collapse because custody is continuing retrievability of exact content. Cleanup and partial-work retention are the converse of the same invariant, as SWF-30 explicitly decided. Node cache-retention debt is not evidence the canonical Python fix failed.

### LRN-006 — release-admission-record

| Field | Value |
|---|---|
| learning_id | LRN-006 |
| failure_class | release-admission-record |
| originating_BIUs | PY-06, PY-07 |
| recurrence_count | 2 |
| first_occurrence | 2026-09-20T13:46:47Z |
| last_occurrence | 2026-09-20T16:54:46Z |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-20-wave1-release-coordinator.md](../../docs/decisions/2026-09-20-wave1-release-coordinator.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/evidence/2026-09-21-liveness-retry-and-release-admission.md](../../docs/evidence/2026-09-21-liveness-retry-and-release-admission.md); [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md) |
| existing_owner | SF-REQ-002 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — require durable IMPLEMENT authority, a resolvable ancestral baseline and explicit supersession of stale unauthorized wording before release. |
| proven_red | yes |
| later_consumption | FACT: PY-08/PY-09 release records consumed the amended admission checks (docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md; docs/evidence/wave1-source-observations.json); later PY-09B/PY-10 releases are retained in docs/evidence/wave1-evidence-reconciliation.md. |
| effectiveness_evidence | FACT: one PY-06 producer refused nonexistent 6a2d1e9; two PY-07 producers refused one incomplete release. A replay of the PY-07 record failed on its two actual authority defects; live PY-08 admission also refused before prerequisites were satisfied. D8's suffix-parser failure and claimed repair are participant-only; they are not counted as another established defective release or as proven-red evidence. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: one admission-record lesson; baseline existence and release authorization are fields of the same pre-launch decision. Recurrence counts the two defective releases, not three worker refusals; baseline-role confusion is a related candidate, not a third established release defect.

**Recurrence population:** Two defective releases, excluding the participant-only D8 claim and subsequent refusals of the same release.

- PY-06 release at 2026-09-20T13:46:47Z names nonexistent baseline.
- PY-07 release at 2026-09-20T16:54:46Z lacks consistent authorization and baseline.

### LRN-007 — attention-identity

| Field | Value |
|---|---|
| learning_id | LRN-007 |
| failure_class | attention-identity |
| originating_BIUs | PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md) |
| existing_owner | SF-REQ-053 |
| owner_fit | CANONICAL |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | yes — re-recording one invocation outcome must preserve attention identity; distinct invocation-free gaps must get distinct identities even after acknowledgement. |
| proven_red | UNKNOWN |
| later_consumption | FACT: the PY-09 incident records separate anchors for invocation outcomes and liveness gaps (docs/evidence/2026-09-21-py09-provider-capacity-interruption.md). Later independent exercise is not established. |
| effectiveness_evidence | FACT: one verifier outcome produced three attention items, then removing timestamps globally broke the neighboring invocation-free case. The incident says regression tests were added; the repository record does not retain their red run or demonstrate later effectiveness. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SF-REQ-053, through SWF-27, explicitly owns durable attention identity based on dispatcher outcomes rather than observation timestamps. Both invocation-correlated and invocation-free identity cases belong to that boundary. Documentary enforcement and unproven later effectiveness do not change semantic ownership.

### LRN-008 — invocation-success-without-verdict

| Field | Value |
|---|---|
| learning_id | LRN-008 |
| failure_class | invocation-success-without-verdict |
| originating_BIUs | PY-09 |
| recurrence_count | 1 |
| first_occurrence | 2026-09-21T03:03:29.309Z |
| last_occurrence | 2026-09-21T03:03:29.309Z |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SF-REQ-016 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — provider exit success cannot advance work without an admissible, invocation-correlated durable work result. |
| proven_red | yes |
| later_consumption | FACT: a fresh verifier reviewed the same cycle-4 candidate and accepted after the no-verdict invocation (docs/evidence/wave1-evidence-reconciliation.md; docs/evidence/wave1-source-observations.json). |
| effectiveness_evidence | FACT: verifier f5ca7bab ended with subtype=success, is_error=false and 39 turns but no B-DISP verdict. It became DURABLE_RESULT_MISSING rather than ACCEPT. This is a real adverse-input refusal, not a new run of the product. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: terminal work-result admissibility is distinct from provider capacity, cycle numbering and attention delivery. The observed refusal and independent replacement demonstrate the narrow separation worked.

**Recurrence population:** One retained verifier invocation that completed successfully without a work verdict.

- PY-09 verifier f5ca7bab ended at 2026-09-21T03:03:29.309Z.

### LRN-009 — execution-cycle-identity

| Field | Value |
|---|---|
| learning_id | LRN-009 |
| failure_class | execution-cycle-identity |
| originating_BIUs | PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-21-biu-execution-cycle-counter.md](../../docs/decisions/2026-09-21-biu-execution-cycle-counter.md); [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json); [docs/evidence/wave1-consistency-report.json](../../docs/evidence/wave1-consistency-report.json) |
| existing_owner | SF-REQ-009 |
| owner_fit | CANONICAL |
| owner_fit_basis | docs/decisions/2026-09-21-biu-execution-cycle-counter.md, "Canonical owner: SF-REQ-009, by amendment" and "Canonical semantics" rules 1–10: SWF-32 assigns the lifecycle-derived execution cycle to SF-REQ-009, including increment, same-phase retry/failover, duplicate-delivery and restart/reconstruction semantics. |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | yes — increment once per authoritative re-entry into IMPLEMENT from another state; preserve cycle on same-phase retries, failover, duplicate delivery and restart. |
| proven_red | UNKNOWN |
| later_consumption | FACT: terminal reconciliation reconstructs PY-09 as four cycles despite five verifier invocations (docs/evidence/wave1-evidence-reconciliation.md); its checker rejects a retry increment. That is analytical consumption, not a canonical runtime counter. |
| effectiveness_evidence | none — no durable runtime implementation of the SWF-32 counter is established. The evidence checker enforces reconstructed counts but does not own lifecycle state. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SWF-32 explicitly amends SF-REQ-009 to own the durable lifecycle-derived execution cycle and its retry/restart semantics. The missing runtime implementation is an enforcement gap, not an ownership gap. Scheduling remains unassigned; this ledger assigns neither priority nor implementation.

### LRN-010 — LIVENESS_GAP

| Field | Value |
|---|---|
| learning_id | LRN-010 |
| failure_class | LIVENESS_GAP |
| originating_BIUs | PY-06, PY-08, PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md) |
| existing_owner | SF-REQ-056 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — reconcile known nonterminal state against correlated active, pending and completed effects after grace; wait for bounded claim confirmation instead of one premature sample. |
| proven_red | UNKNOWN |
| later_consumption | FACT: PY-08's missing actor was recovered; PY-09's fixed 25-second confirmation produced a false alarm and was changed to bounded polling (docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md; docs/evidence/2026-09-21-py09-provider-capacity-interruption.md). |
| effectiveness_evidence | FACT: SWF-29 records a roughly 28-minute PY-06 dropped-delivery stall despite healthy services. Later recovery exercised the bootstrap mechanism, but the canonical fenced capability and its negative-control evidence are not established by the Wave 1 record. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one state-to-effect liveness lesson, including observation latency. Judgment suppression and duplicate safety remain separate because one decides whether to retry and the other limits concurrent effects.

### LRN-011 — judgment-required-retry

| Field | Value |
|---|---|
| learning_id | LRN-011 |
| failure_class | judgment-required-retry |
| originating_BIUs | PY-07, PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SWF-29 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — a latest unresolved judgment-required lane outcome suppresses re-emission after grace; merely seeing attention must not resolve it. |
| proven_red | yes |
| later_consumption | FACT: PY-09 at 02:20:07.366243Z had IMPLEMENT, no actor, age 441 seconds against 300-second grace and ATTENTION_WAIT; LIVENESS_SUPPRESSED was recorded (docs/evidence/wave1-evidence-reconciliation.md). |
| effectiveness_evidence | FACT: the PY-07 repeated refusal motivated the amendment; PY-09's quota interruption exercised it under a different outcome, preventing re-emission during the observed blocked interval. Eight tests are recorded in the decision. No nine-hour counterfactual retry total is inferred. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: these collapse into retry eligibility after a durable blocking outcome. The narrow bootstrap gate worked; SF-REQ-056 is its canonical replacement, not a second owner in this row.

### LRN-012 — effect-recovery-identity

| Field | Value |
|---|---|
| learning_id | LRN-012 |
| failure_class | effect-recovery-identity |
| originating_BIUs | PY-03, PY-04, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/execution-trajectories/PY-03.jsonl](../../docs/evidence/execution-trajectories/PY-03.jsonl); [docs/evidence/execution-trajectories/PY-04.jsonl](../../docs/evidence/execution-trajectories/PY-04.jsonl); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md) |
| existing_owner | SF-REQ-008 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — duplicate delivery cannot acquire a second effect identity; unknown external effects must park until attributable reconciliation authorizes progress. |
| proven_red | yes |
| later_consumption | FACT: PY-10 killed a process holding launch:SB-01:0, parked it, continued independent work and resumed on an attributable decision (docs/verification/PY-10-wave1-live-proof.md; docs/evidence/wave1-evidence-reconciliation.md). |
| effectiveness_evidence | FACT: the retained lost-effect mutation turns green to red; six sandbox BIUs have one published candidate each. This establishes scoped duplicate-safe publication and conservative recovery, not absence of computation before the kill. SWF-29's Node lane claim is explicitly single-process. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: one durable effect-identity invariant, distinct from liveness detection and from restoring knowable outcomes. Graduation is limited to the exercised boundary; no multi-dispatcher Node guarantee is inferred.

### LRN-013 — PROVIDER_CAPACITY_INTERRUPTION

| Field | Value |
|---|---|
| learning_id | LRN-013 |
| failure_class | PROVIDER_CAPACITY_INTERRUPTION |
| originating_BIUs | PY-03, PY-09, PY-10 |
| recurrence_count | 3 |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md](../../docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/execution-trajectories/PY-03.jsonl](../../docs/evidence/execution-trajectories/PY-03.jsonl) |
| existing_owner | SWF-09 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — retain typed capacity evidence and enforce required budgets/capabilities before an authorized failover; external quota prediction is possible only if the provider exposes usable evidence. |
| proven_red | UNKNOWN |
| later_consumption | FACT: PY-09 continued its repair under a scoped provider change; the later PY-10 assessment failover still returned SPLIT_RECOMMENDED and did not authorize release (docs/evidence/2026-09-21-py09-provider-capacity-interruption.md; docs/evidence/2026-09-21-agent-ready-provider-failover.md). |
| effectiveness_evidence | FACT: two execution interruptions are retained (PY-03 closure, PY-09 producer), plus one separately scoped Agent-Ready capacity interruption. Recovery worked by operator decision; predictive capacity admission or automatic authorized routing is not demonstrated. Funding-account sharing is a risk, not evidence of an observed second outage. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: capacity diagnosis and governed provider substitution collapse into one routing/budget boundary; work custody, cycle identity and temporary-authorization expiry are independent obligations. Count is the three enumerated interruptions, not complete provider telemetry.

**Recurrence population:** Two execution incidents plus one separately identified Agent-Ready capacity interruption; not exhaustive provider telemetry.

- PY-03 closure capacity interruption.
- PY-09 cycle-4 producer quota interruption.
- PY-10 Agent-Ready reassessment quota interruption.

### LRN-014 — specification-consumer-mismatch

| Field | Value |
|---|---|
| learning_id | LRN-014 |
| failure_class | specification-consumer-mismatch |
| originating_BIUs | PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-design-contract-and-design-verification.md](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md); [docs/operations/py10-sandbox.md](../../docs/operations/py10-sandbox.md); [docs/decisions/2026-09-21-sandbox-isolation-standard.md](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md); [docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json](../../docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json); [docs/work-units/python/PY-09B.assessment.json](../../docs/work-units/python/PY-09B.assessment.json); [docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json); [docs/evidence/py10-preflight-2026-09-21-negative-control.json](../../docs/evidence/py10-preflight-2026-09-21-negative-control.json); [docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json); [docs/evidence/PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md) |
| existing_owner | SF-REQ-051 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — compare expected permissions and acceptance claims with the consuming code and platform capabilities; mechanical exact-set checks cannot validate their own premise. |
| proven_red | yes |
| later_consumption | FACT: Agent-Ready blocked PY-09B, SWF-34 resolved isolation, and corrected permissions were independently exercised by PY-09B/PY-10 (docs/operations/py10-sandbox.md; docs/evidence/PY-09B-live-transport.md; docs/evidence/wave1-evidence-reconciliation.md). |
| effectiveness_evidence | FACT: preflight passed 17/17 against Node's permission set; the corrected expectation failed 2 of 17 before the grant, then passed 17/17. The same contract demanded impossible token-level Project isolation. Specific controls worked after correction; upstream specification derivation remains review-dependent. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one specification-validation lesson with two actual defects: D4/D5 are the same permission-premise failure, and D6 is the feasibility limb of the same upstream independent design review. Conformance, feasibility and accepted residual risk must be explicit. No general design gate effectiveness is inferred from corrected preflight.

### LRN-015 — decomposition-conservation

| Field | Value |
|---|---|
| learning_id | LRN-015 |
| failure_class | decomposition-conservation |
| originating_BIUs | PY-10, PY-09B |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md); [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md); [docs/work-units/python/PY-09B.assessment.json](../../docs/work-units/python/PY-09B.assessment.json); [docs/work-units/python/PY-10.assessment.json](../../docs/work-units/python/PY-10.assessment.json); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json) |
| existing_owner | SF-REQ-013 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — require every scoped capability and proof obligation to map to a retained owner through split lineage and dependency changes; deciding a useful split remains judgment. |
| proven_red | yes |
| later_consumption | FACT: PY-09B was inserted without renumbering, then PY-10 consumed its accepted transport; both were first-pass accepted (docs/decisions/2026-09-21-py10-transport-split.md; docs/evidence/wave1-evidence-reconciliation.md; docs/evidence/wave1-closure-manifest.json). |
| effectiveness_evidence | FACT: Agent-Ready returned SPLIT_RECOMMENDED for unowned live transport and an expensive coupled proof; release waited for approved SWF-33 and fresh READY. The split retained existing SF-REQ-005/007/038 ownership and capstone proof. A non-READY assessment visibly stopped release; no runtime mutation is claimed. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: one conservation lesson: reduce rework locality without dropping obligations or multiplying requirements. The unresolved PY-09B native-edge projection is tracked separately under LRN-016. First-pass results do not prove the split caused the yield change.

### LRN-016 — lifecycle-projection-authority

| Field | Value |
|---|---|
| learning_id | LRN-016 |
| failure_class | lifecycle-projection-authority |
| originating_BIUs | PY-06, PY-07, PY-08, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-20-wave1-closure-policy.md](../../docs/decisions/2026-09-20-wave1-closure-policy.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json) |
| existing_owner | SF-REQ-002 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | yes — dependency admission consumes authoritative lifecycle and declared edges; stale Issue closure or a missing projected edge must not silently redefine eligibility. |
| proven_red | yes |
| later_consumption | FACT: SWF-31 corrected PY-06/PY-07 Issue projections so PY-08 could be admitted; PY-10 respected its contract-declared sandbox dependency (docs/decisions/2026-09-20-wave1-closure-policy.md; docs/evidence/wave1-evidence-reconciliation.md; docs/evidence/py10/proven-red.json). |
| effectiveness_evidence | FACT: Project DONE preceded Issue closure and the native dependency check blocked completed predecessors. Terminal capture still found no PY-09B native blocked-by edges despite four declared predecessors. PY-10's sandbox uses matching descriptors/contracts, not native links, and projects lifecycle only at completion. Its dependency-disagreement guard is proven red; full projection alignment is not. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one authority/projection lesson: the projection cannot define execution truth. Unlike LRN-015's conservation of scope at planning, this concerns faithful downstream state/edge representation and admission. Existing amendments already own it.

### LRN-017 — evidence-derivation-consistency

| Field | Value |
|---|---|
| learning_id | LRN-017 |
| failure_class | evidence-derivation-consistency |
| originating_BIUs | PY-01, PY-02, PY-03, PY-04, PY-05, PY-06, PY-07, PY-08, PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-20-evidence-and-intake-ratification.md](../../docs/decisions/2026-09-20-evidence-and-intake-ratification.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-repair-cycles.json](../../docs/evidence/wave1-repair-cycles.json); [docs/evidence/wave1-consistency-report.json](../../docs/evidence/wave1-consistency-report.json); [docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md](../../docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [tools/evidence/check_wave1.py](../../tools/evidence/check_wave1.py); [tools/evidence/reconcile_wave1.py](../../tools/evidence/reconcile_wave1.py); [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md) |
| existing_owner | SF-REQ-030 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — recompute source-supported metrics under explicit populations and timestamps; reject contradictions, unmarked supersession, inferred custody and substitution of zero for unavailable telemetry. |
| proven_red | yes |
| later_consumption | FACT: the terminal reconciliation replaced inconsistent interim aggregates with source-backed rows and retained history; this task reproduced the existing derivation in memory (docs/evidence/wave1-evidence-reconciliation.md; tools/evidence/reconcile_wave1.py). |
| effectiveness_evidence | FACT: check_wave1.py --negative-controls exited 0 with 1,075 checks, zero failures and 13/13 killed. It rejects wrong counts, UNKNOWN-to-zero, chronology, retry increments, an invented seventh candidate, broken ancestry and removed supersession. It does not mechanically interpret all verifier prose or supply missing telemetry. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: one source-to-derived-evidence invariant. The prior extraction's tautological self-comparison and its later repair corroborate D2's consequence, not the participant's claim about what they did or did not read. The scoped offline checker graduated; generic evidence governance is not declared complete.

### LRN-018 — duplicate-canonical-owner

| Field | Value |
|---|---|
| learning_id | LRN-018 |
| failure_class | duplicate-canonical-owner |
| originating_BIUs | UNKNOWN |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/decisions/2026-09-20-evidence-and-intake-ratification.md](../../docs/decisions/2026-09-20-evidence-and-intake-ratification.md); [docs/decisions/2026-09-20-candidate-worktree-retention.md](../../docs/decisions/2026-09-20-candidate-worktree-retention.md); [docs/decisions/2026-09-21-biu-execution-cycle-counter.md](../../docs/decisions/2026-09-21-biu-execution-cycle-counter.md); [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/proposals/INDEX.md](../../docs/proposals/INDEX.md); [docs/proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md](../../docs/proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md); [docs/proposals/PROP-2026-0005-proposal-intake-as-product-capability.md](../../docs/proposals/PROP-2026-0005-proposal-intake-as-product-capability.md) |
| existing_owner | SF-REQ-055 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — require a stable proposal-to-owner mapping and prevent duplicate identifier delivery; semantic overlap requires authority review before choosing amendment, retirement or a distinct owner. |
| proven_red | UNKNOWN |
| later_consumption | FACT: after SF-REQ-054 was folded into SF-REQ-030, SWF-30 chose SF-REQ-007 and SWF-32 chose SF-REQ-009 rather than creating new owners (docs/decisions/2026-09-20-evidence-and-intake-ratification.md; docs/decisions/2026-09-20-candidate-worktree-retention.md; docs/decisions/2026-09-21-biu-execution-cycle-counter.md; docs/proposals/INDEX.md). |
| effectiveness_evidence | FACT: the index preserves immutable proposal history, retirement and amendment targets. SWF-29 separately explains why a new Wave 2 owner was needed to avoid retrofitting Wave 1. This is demonstrated authority-controlled intake practice, not an implemented idempotent intake service. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL, but STRENGTHEN_EXISTING_OWNER under POSTW1-DECIDE-002A. SF-REQ-055 explicitly owns proposal canonicalization and idempotent intake. The two correct outcomes demonstrate manual Founder-and-coordinator practice, not an implemented intake service that survives replacement of its authors. REVIEW_GATE, proven_red UNKNOWN and the original effectiveness evidence remain unchanged. Originating BIU attribution and recurrence remain UNKNOWN.

### LRN-019 — observation-without-activation

| Field | Value |
|---|---|
| learning_id | LRN-019 |
| failure_class | observation-without-activation |
| originating_BIUs | PY-06, PY-07, PY-08, PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md) |
| existing_owner | SF-REQ-053 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — inject an attention-worthy event and verify durable item creation plus an observable consumer wake-up; notification-command success alone does not prove human receipt. |
| proven_red | UNKNOWN |
| later_consumption | FACT: SWF-27 records a session-bound waiter restoring the callback; the PY-09 incident reports attention reached the resident coordinator in roughly 30 seconds (docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md; docs/evidence/2026-09-21-py09-provider-capacity-interruption.md). |
| effectiveness_evidence | FACT: externalizing monitoring preserved observation but lost the harness callback. SWF-27 records roughly 45 minutes waiting after PY-06 DONE and 1h45m before PY-08 release; PY-07's blocking event was unseen. These are source-recorded approximate delays, not freshly timed measurements. Windows notification seen-by-human remains unproven. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one observation-to-activation boundary. A resident-session workaround worked but does not establish durable activation of a replacement coordinator; the attention queue and product Decision Inbox retain different responsibilities.

### LRN-020 — temporary-authority-expiry

| Field | Value |
|---|---|
| learning_id | LRN-020 |
| failure_class | temporary-authority-expiry |
| originating_BIUs | PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/decisions/2026-09-20-wave1-release-coordinator.md](../../docs/decisions/2026-09-20-wave1-release-coordinator.md); [docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md](../../docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md) |
| existing_owner | SWF-27 |
| owner_fit | CANONICAL |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | partial — compare each temporary control's scope and expiry with current authority and replacement evidence; ambiguous expiry requires an explicit decision, not automatic retirement. |
| proven_red | UNKNOWN |
| later_consumption | FACT: SWF-26 has a durable expiry record; the later PY-09-only provider exception lacks a captured extension despite use in PY-09B/PY-10 (docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md; docs/evidence/wave1-evidence-reconciliation.md). |
| effectiveness_evidence | FACT: later producer modelUsage excerpts corroborate Claude use. Any separate extension or ratification is UNKNOWN; this ledger neither ratifies nor reverts it. The expiry inventory's service/profile observations are participant-time observations, not current operational reads. Python sandbox success does not satisfy SWF-21's live-profile replacement condition. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SWF-27 rule 10 explicitly requires temporary controls to carry scope, authority, expiry, provenance and a replacement target. The recurring lesson is enforcement of that exception lifecycle. It survives bootstrap; only the specific expired battery procedure is BOOTSTRAP_ONLY in LRN-026.

### LRN-021 — configuration-input-validation

| Field | Value |
|---|---|
| learning_id | LRN-021 |
| failure_class | configuration-input-validation |
| originating_BIUs | PY-09 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md) |
| existing_owner | SF-REQ-038 |
| owner_fit | CANONICAL |
| enforcement_level | DETERMINISTIC_GATE |
| mechanizable | yes — validate a proposed runtime profile against the consumer's accepted keys before activation, keeping provenance in its designated evidence record. |
| proven_red | yes |
| later_consumption | FACT: after removal of the unsupported provenance key, the PY-09 profile was accepted and recovery proceeded (docs/evidence/2026-09-21-py09-provider-capacity-interruption.md). |
| effectiveness_evidence | FACT: the loader rejected _providerChangeProvenance as invalid config.workers.PRODUCER. This is observed fail-closed behavior. Exactly three failed starts and zero blast radius are participant claims not independently enumerated in the retained incident record; neither is asserted as a measured result here. Earlier pre-restart validation is not demonstrated. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: SF-REQ-038 reasonably owns this readiness validation; the loader is a concrete existing mechanism. Graduation covers refusal of invalid configuration, not a complete pre-mutation workflow or the correctness of valid values.

### LRN-022 — ambient-provider-credentials

| Field | Value |
|---|---|
| learning_id | LRN-022 |
| failure_class | ambient-provider-credentials |
| originating_BIUs | PY-10 |
| recurrence_count | 1 |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md) |
| existing_owner | SF-REQ-025 |
| owner_fit | ADJACENT |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | yes — construct the provider invocation environment deliberately and prove an unrelated ambient credential cannot override the authorized authentication profile. |
| proven_red | UNKNOWN |
| later_consumption | FACT: Agent-Ready failover succeeded after removing the ambient key; PY-10 later retained red evidence for an explicitly stated worker environment (docs/evidence/2026-09-21-agent-ready-provider-failover.md; docs/evidence/py10/proven-red.json). |
| effectiveness_evidence | FACT: the first Claude assessment attempt returned 401 because ANTHROPIC_API_KEY took precedence over the subscription login. The incident says worker launching already filters ambient secrets while coordinator tooling did not. The later worker-environment test does not prove the coordinator-tooling gap was structurally closed. |
| recommended_disposition | NEW_CAPABILITY_GAP |

INFERENCE: ADJACENT; NEW_CAPABILITY_GAP under POSTW1-DECIDE-002A. SF-REQ-025 owns exposing provider capabilities and authenticated readiness, not constructing and isolating coordinator-tool invocation environments so ambient credentials cannot override the authorized authentication profile. The prior absorbability rationale stretched that owner. No existing canonical owner cleanly owns the scoped credential-precedence isolation semantics in the reviewed authority. The retained existing_owner names the adjacent requirement, not an assignment of the gap; no requirement is created.

**Recurrence population:** One recorded Agent-Ready credential-precedence incident.

- PY-10 Claude assessment attempt returned 401 with ambient ANTHROPIC_API_KEY.

### LRN-023 — provider-progress-observability

| Field | Value |
|---|---|
| learning_id | LRN-023 |
| failure_class | provider-progress-observability |
| originating_BIUs | PY-09, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [src/providers/codex.mjs](../../src/providers/codex.mjs); [src/providers/claude.mjs](../../src/providers/claude.mjs) |
| existing_owner | SF-REQ-029 |
| owner_fit | ADJACENT |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | partial — normalize typed started/progress/terminal/capacity observations where available, preserve provider provenance, and report unavailable progress as unknown rather than worker death. |
| proven_red | UNKNOWN |
| later_consumption | not consumed — no later normalized progress contract or comparable progress trace was established in the reviewed Wave 1 evidence. |
| effectiveness_evidence | FACT: retained terminal records differ (Codex turn.failed versus Claude result/success), and adapter arguments differ (--json versus --output-format json). HYPOTHESIS: buffered versus streaming output contributed to operator uncertainty. No retained comparative timing series establishes buffering, recurrence, or a causal stall; those claims remain unverified. |
| recommended_disposition | NEW_CAPABILITY_GAP |

INFERENCE: ADJACENT; NEW_CAPABILITY_GAP under POSTW1-DECIDE-002A. SF-REQ-029 owns recording engineering trajectory; it does not establish the provider-neutral started/progress/terminal/capacity normalization boundary, including explicit unavailable progress. Activation and diagnostic coalescing are also adjacent controls. No existing canonical owner cleanly owns these scoped normalization semantics in the reviewed authority. The buffering explanation remains a hypothesis; missing implementation alone is not the basis for this ownership finding. The retained existing_owner identifies adjacency; no requirement is created.

### LRN-024 — persistent-diagnostic-coalescing

| Field | Value |
|---|---|
| learning_id | LRN-024 |
| failure_class | persistent-diagnostic-coalescing |
| originating_BIUs | PY-06, PY-08 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SF-REQ-034 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | yes — repeated observations of one unchanged condition preserve first_seen, last_seen and repeat_count without emitting a new incident each sweep; cleared or changed conditions remain visible. |
| proven_red | UNKNOWN |
| later_consumption | FACT: the worktree audit assigned coalescing to unreleased PY-08; its later verifier records W10 closed and preserved (docs/evidence/2026-09-20-worktree-retention-audit.md; docs/evidence/execution-trajectories/PY-08.jsonl). |
| effectiveness_evidence | FACT: the audit counted 1,202 emissions from 43 invocation/error pairs, including 980 dirty-retention and 222 registration/branch mismatches. PY-08's verifier later confirmed coalescing and preserved it. Frozen Node noise and remaining CLI logging gaps are distinct from this completed scoped mechanism. |
| recommended_disposition | ALREADY_GRADUATED |

INFERENCE: one persistent-condition aggregation lesson, distinct from attention dedupe: retaining diagnostic history does not itself decide which events warrant a coordinator wake-up. No red trace for the coalescer was found, so proven_red remains UNKNOWN.

### LRN-025 — FALSE_OR_ESCALATED_AUTHORITY_REQUEST

| Field | Value |
|---|---|
| learning_id | LRN-025 |
| failure_class | FALSE_OR_ESCALATED_AUTHORITY_REQUEST |
| originating_BIUs | PY-03, PY-04, PY-08 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/execution-trajectories/PY-03.jsonl](../../docs/evidence/execution-trajectories/PY-03.jsonl); [docs/evidence/execution-trajectories/PY-04.jsonl](../../docs/evidence/execution-trajectories/PY-04.jsonl); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SF-REQ-006 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — resolve named artifacts and scope mechanically, but judge whether authority is actually missing against the binding contract and landed code; no universal deterministic semantic verdict is claimed. |
| proven_red | UNKNOWN |
| later_consumption | FACT: PY-08's claim of four missing predecessor services was checked against the landed tree and rejected without changing its contract or baseline (docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md; docs/evidence/execution-trajectories/PY-08.jsonl; docs/evidence/wave1-source-observations.json). |
| effectiveness_evidence | FACT: PY-03/PY-04 records distinguish incomplete contracted work from genuine authority decisions; PY-08's false escalation was resolved by code-aware review. This worked when judgment was available, but does not establish a durable authority-triage mechanism independent of the resident coordinator. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one qualitative adjudication lesson. Do not turn correct producer refusals on bad releases into this class, or turn the incident report's scoped count of two into a global Wave 1 total.

### LRN-026 — bootstrap-mutation-gate-tenure

| Field | Value |
|---|---|
| learning_id | LRN-026 |
| failure_class | bootstrap-mutation-gate-tenure |
| originating_BIUs | PY-04 |
| recurrence_count | 1 |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md](../../docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md); [docs/decisions/2026-09-20-deterministic-failure-class-promotion.md](../../docs/decisions/2026-09-20-deterministic-failure-class-promotion.md); [docs/evidence/execution-trajectories/PY-04.jsonl](../../docs/evidence/execution-trajectories/PY-04.jsonl); [docs/evidence/execution-trajectories/PY-05.jsonl](../../docs/evidence/execution-trajectories/PY-05.jsonl); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md) |
| existing_owner | SWF-26 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | yes — scope the manual battery to PY-04 and reject use as standing later-BIU authority after its explicit expiry. |
| proven_red | yes |
| later_consumption | FACT: PY-05's release evidence explicitly states SWF-26 does not apply (docs/evidence/execution-trajectories/PY-05.jsonl); the general mutation principle remains with SF-REQ-050. |
| effectiveness_evidence | FACT: the temporary coordinator battery reproduced five survivors and found a sixth on 1b372c2a; the accepted candidate killed 23/23. Its decision is explicitly EXPIRED. The expiry note's 12:27:21Z DONE time differs from the accepted terminal dispatcher time 12:26:25.430Z; the event, not that old timestamp, defines the expiry. |
| recommended_disposition | BOOTSTRAP_ONLY |

INFERENCE: this specific manual procedure expires with bootstrap authority and is not a new permanent gate. LRN-001 owns reusable proof quality and LRN-020 owns exception-expiry governance; neither inherits this exceptional coordinator role.

**Recurrence population:** One scoped temporary procedure, not the number of battery runs or surviving mutants.

- SWF-26 applied only to PY-04 and explicitly expired at its DONE.

### LRN-027 — coordinator-replacement-continuity

| Field | Value |
|---|---|
| learning_id | LRN-027 |
| failure_class | coordinator-replacement-continuity |
| originating_BIUs | UNKNOWN |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md) |
| existing_owner | SF-REQ-053 |
| owner_fit | CANONICAL |
| owner_fit_basis | docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md names "Canonical requirement: SF-REQ-053"; "Durable rules" 3, 7, 8 and 9 require durable state for correct continuation after coordinator replacement, successor reconstruction from authoritative state, restart equivalence and no hidden session state. |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | partial — reconstruct authorized next actions from durable state in a fresh episode and compare them under the same state/events; mechanical state equality cannot fully prove judgment equivalence. |
| proven_red | UNKNOWN |
| later_consumption | not consumed — a Wave 1 coordinator replacement exercise is not established by the reviewed artifacts. |
| effectiveness_evidence | none — the inventory says no handover occurred and the checkpoint was untested. This is participant evidence of an unproven property, not independent proof that a replacement would fail. SWF-27 documents monitoring decoupling and permits multi-BIU tenure during bootstrap; neither proves restart equivalence. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SF-REQ-053 through SWF-27 rules 3, 7, 8 and 9 explicitly owns durable continuation and restart equivalence across coordinator replacement. Activation is a distinct obligation under that same owner. No handover occurred and the checkpoint was untested, so effectiveness remains absent without turning explicit ownership into adjacency. BIU attribution remains UNKNOWN; this analysis is not a lifecycle-handover test.

### LRN-028 — acceptance-extent-and-residual-proof

| Field | Value |
|---|---|
| learning_id | LRN-028 |
| failure_class | acceptance-extent-and-residual-proof |
| originating_BIUs | PY-06, PY-07, PY-08, PY-09, PY-09B, PY-10 |
| recurrence_count | UNKNOWN |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json); [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/py10/acceptance-verification.json](../../docs/evidence/py10/acceptance-verification.json) |
| existing_owner | SF-REQ-017 |
| owner_fit | CANONICAL |
| enforcement_level | REVIEW_GATE |
| mechanizable | partial — map acceptance claims to exact obligations and evidence, retain residual findings and proof limits, and refuse to infer full requirement completion from a scoped BIU verdict. |
| proven_red | UNKNOWN |
| later_consumption | FACT: terminal quality and closure records retain nonblocking observations and scoped requirement extents (docs/evidence/wave1-evidence-reconciliation.md; docs/evidence/wave1-closure-manifest.json); PY-10's independent verifier disclosed its production-read limitation. |
| effectiveness_evidence | FACT: PY-08 ACCEPT retained Y7/Y8 despite inaccurate WIP reporting and sparse mutation logs; PY-09 retained a missing proof observation. PY-10's independent verifier could not re-derive the historical production digest. Retained before/after digests and zero observed production events corroborate a limited claim, not absence of every possible write. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: one claim-to-evidence extent lesson. LRN-017 validates derived counts; this lesson judges what a count or verdict can legitimately establish. Disclosure worked, but outstanding proof and scope gaps prevent broad graduation.

### LRN-029 — unbounded-nonterminal-retry

| Field | Value |
|---|---|
| learning_id | LRN-029 |
| failure_class | unbounded-nonterminal-retry |
| originating_BIUs | PY-10 |
| recurrence_count | 1 |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json) |
| existing_owner | SF-REQ-022 |
| owner_fit | CANONICAL |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | yes — repeated ineligible/rework outcomes must consume a durable run/retry budget and terminate or escalate when exhausted rather than rely solely on a harness timeout. |
| proven_red | no |
| later_consumption | not consumed — the PY-10 proof and closure explicitly carried this limitation forward; no subsequent bounded-run product mechanism is established. |
| effectiveness_evidence | FACT: breaking the per-invocation capability grant made the drain never finish; the retained matrix records exit 124 under the test bound. The proof says the real product re-dispatches nonterminal outcomes indefinitely. The harness fails on timeout; an owning product run-level budget was not demonstrated to fail closed. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SF-REQ-022 explicitly owns bounded retries/budgets and escalation on exhaustion of repair loops. Repeated nonterminal rework that never reaches an effective stop exposes an incomplete bound within that subject; the missing run-level enforcement does not require a new owner. This remains distinct from capacity diagnosis and suppression of completed judgment-required outcomes.

**Recurrence population:** One distinct disclosed PY-10 nonterminal redispatch limitation, not a measured number of retries.

- PY-10 per-invocation grant mutation hung until harness timeout.

### LRN-030 — volatile-worker-outcome-recovery

| Field | Value |
|---|---|
| learning_id | LRN-030 |
| failure_class | volatile-worker-outcome-recovery |
| originating_BIUs | PY-10 |
| recurrence_count | 1 |
| first_occurrence | UNKNOWN |
| last_occurrence | UNKNOWN |
| evidence_refs | [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json) |
| existing_owner | SF-REQ-008 |
| owner_fit | CANONICAL |
| enforcement_level | DOCUMENTED_ONLY |
| mechanizable | yes — persist attributable worker outcomes so restart can reconcile a known effect; absent or ambiguous evidence must still park rather than guess. |
| proven_red | no |
| later_consumption | not consumed — no later durable worker-outcome reconciliation replacing the PY-10 in-memory read-back was established. |
| effectiveness_evidence | FACT: the PY-10 process kill destroyed RealWorkerProvider's in-memory read-back. Safe parking worked, but an operator decision was required to resume. This is evidence of conservative safety, not automatic recovery of a knowable completed effect; no durable read-back mechanism or red proof for it is retained. |
| recommended_disposition | STRENGTHEN_EXISTING_OWNER |

INFERENCE: CANONICAL. SF-REQ-008 explicitly owns preservation of canonical execution state and reconciliation across crashes/restarts. Durable attributable outcome read-back is within that subject even though only conservative parking was demonstrated. Distinct from LRN-012: preventing duplicate effects does not establish preservation of knowable outcomes.

**Recurrence population:** One demonstrated loss of worker-outcome knowledge at the PY-10 kill/restart boundary.

- PY-10 SB-01 in-flight process kill lost volatile read-back and required judgment.

## Coordinator structural assessment

INFERENCE: concentration of contract authoring, infrastructure setup, evidence publication, release and recovery judgment in one coordinator allowed the same premise to author both an artifact and its apparent proof. Independent consumption boundaries detected several mistakes after propagation. This is a structural separation-of-duties finding, not an attribution of all Wave 1 rejections to the coordinator.

**FACT:** Bad upstream release records reached workers: PY-06 had one baseline refusal; PY-07 had two refusals for one missing/contradictory release record.

**Cost and limit:** Three producer invocations refused these upstream defects. Their complete token cost is UNKNOWN; this count is not three distinct defective releases.

**Mechanism:** Retain the SF-REQ-002 pre-launch release-record gate; independently resolve authority and exact baseline before dispatch.

Lessons: LRN-006. Evidence: [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/decisions/2026-09-20-wave1-release-coordinator.md](../../docs/decisions/2026-09-20-wave1-release-coordinator.md); [docs/evidence/2026-09-21-liveness-retry-and-release-admission.md](../../docs/evidence/2026-09-21-liveness-retry-and-release-admission.md)

**FACT:** The sandbox permission expectation and the passing preflight shared the same incorrect Node-derived premise. Agent-Ready later found both the custody permission gap and the impossible Project-isolation criterion.

**Cost and limit:** The environment had been represented as verified at 17/17 before correction; additional pre-release clarification/reassessment was needed. The claimed roughly 19-hour delay is not adopted as a measured interval.

**Mechanism:** Use the existing SF-REQ-051 independent design-verification boundary to review consumer-derived expectations and technical feasibility before provisioning is called proven. Preserve SWF-34's explicit residual risk.

Lessons: LRN-014, LRN-015. Evidence: [docs/operations/py10-sandbox.md](../../docs/operations/py10-sandbox.md); [docs/decisions/2026-09-21-sandbox-isolation-standard.md](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json](../../docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json)

**FACT:** Evidence generation itself produced conflicting populations and an initial self-comparing consistency assertion. Independent reconciliation/review corrected further candidate-identity, timing and negative-control defects.

**Cost and limit:** Published evidence needed correction and explicit supersession. A complete repair effort or cost cannot be reconstructed from these artifacts.

**Mechanism:** Apply SF-REQ-030 source-to-derived checks with semantic negative controls and independent evidence review before publication; passing self-comparison is not proof.

Lessons: LRN-001, LRN-017. Evidence: [docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md](../../docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md)

**INFERENCE:** Coordinator recovery tooling had neighboring cases that a narrow test-first change did not preserve: fixing timestamp dedupe broke invocation-free liveness attention, and fixed-delay confirmation generated a false alarm.

**Cost and limit:** The incident records three wake-ups for one result and a later false recovery alarm. It does not establish a complete duplicate/false-alarm count or prove that a later genuine event was permanently lost.

**Mechanism:** Retain typed identity cases and regression obligations under SF-REQ-053/SF-REQ-049; verify the recovery outcome over a bounded correlation-aware interval under SF-REQ-056.

Lessons: LRN-004, LRN-007, LRN-010. Evidence: [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md)

**INFERENCE:** Persistence of monitoring did not prove activation or coordinator replaceability. Moving watchers out of the session removed the callback, while the checkpoint's replacement property remained unexercised.

**Cost and limit:** SWF-27 records roughly 45 minutes after PY-06 DONE and 1h45m before PY-08 release, plus an unseen PY-07 blocking outcome. These intervals must not be summed with overlapping liveness/refusal time as a total coordinator cost.

**Mechanism:** Keep activation and successor reconstruction as separate proof obligations of SF-REQ-053. Multi-BIU tenure was explicitly permitted; its duration alone is not a policy violation.

Lessons: LRN-019, LRN-027. Evidence: [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md); [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md)

**FACT:** The PY-09-only provider change was used by two later producers, while a durable extension was not found in accepted captured evidence.

**Cost and limit:** The authorization boundary remains qualified; the first-pass results remain observed facts. No provider-caused product defect or exhaustive unauthorized-action verdict is inferred.

**Mechanism:** Track temporary scope/expiry/replacement under SWF-27. Expiry disposition or ratification belongs to the appropriate authority after this analysis.

Lessons: LRN-020. Evidence: [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md)

HYPOTHESIS: separation of upstream authorship and review would reduce propagation cost. Wave 1 provides concrete mechanisms and catches, not a controlled comparison. Two first-pass BIUs differ in scope, substrate, sequencing, provider and baseline; no causal yield or model ranking follows.

| Unavailable coordinator metric | Value |
|---|---|
| complete_coordinator_tokens | UNKNOWN |
| complete_coordinator_cost | UNKNOWN |
| deduplicated_coordinator_delay_seconds | UNKNOWN |

### Participant account adjudication

**D1 — FACT:** The nonexistent SHA and correction are corroborated by captured Issue comments. The participant's 'could not have escaped' counterfactual is not adopted.

Lessons: LRN-006. Evidence: [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md)

**D2 — INFERENCE:** The incompatible derived populations and reconciliation are corroborated. The assertion that the author never read a schema and the exact discovery conversation are not independently established.

Lessons: LRN-017. Evidence: [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md](../../docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md)

**D3 — FACT:** The unsupported key rejection is in the incident record. Exactly three failed restarts and zero blast radius lack an independently retained enumeration; no zero is fabricated.

Lessons: LRN-021. Evidence: [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md)

**D4/D5 — FACT:** One permission-premise defect, not two independent recurrences. Three preflight states and consuming custody responsibility corroborate it.

Lessons: LRN-014. Evidence: [docs/operations/py10-sandbox.md](../../docs/operations/py10-sandbox.md); [docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json); [docs/evidence/py10-preflight-2026-09-21-negative-control.json](../../docs/evidence/py10-preflight-2026-09-21-negative-control.json); [docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json)

**D6 — FACT:** The retained NEEDS_CLARIFICATION assessment and SWF-34 corroborate the impossible criterion and authorized correction.

Lessons: LRN-014. Evidence: [docs/decisions/2026-09-21-sandbox-isolation-standard.md](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md); [docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json](../../docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json)

**D7 — INFERENCE:** A separate durable incident account describes both attention identity defects, but a raw regression-test red trace is not retained. The statement that a later genuine gap would never wake anyone is a reasoned failure mode, not a measured lifetime failure.

Lessons: LRN-004, LRN-007. Evidence: [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md)

**D8 — HYPOTHESIS:** SWF-33 corroborates valid PY-09B naming; the parser failure and claimed tests are only in the participant self-assessment. Keep provisional within LRN-006; do not use it as effectiveness evidence or another measured release defect.

Lessons: LRN-006. Evidence: [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md)

**D9 — INFERENCE:** The audit corroborates the measured worktree population and SWF-27 corroborates the lost background callback. The missed-process, shell-kill, cleanup-cwd, partial-commit and waiter-lifetime details remain participant-only; MEMORY-ONLY anecdotes are not promoted.

Lessons: LRN-005, LRN-017, LRN-019. Evidence: [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md); [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md); [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md)

## Durable source conflicts and qualifications

**PY-10 branch count**

Claim tested: Coordinator closure narrative: seven candidates plus a repair cycle.

FACT: accepted reconciliation and retained proof establish six candidate branches plus main; no extra verifier rejection or capstone repair cycle supports that narrative.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json); [docs/evidence/py10/acceptance-verification.json](../../docs/evidence/py10/acceptance-verification.json)

**PY-04 presumptive identity**

Claim tested: A timestamp-correlated tree can stand in for the unrecorded candidate of verdict 9.

FACT: the verifier explicitly rejected that inference. Preserve f95199e6 only as a presumptive tree, with candidate identity UNKNOWN.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-repair-cycles.json](../../docs/evidence/wave1-repair-cycles.json)

**Repair populations**

Claim tested: Historical cycle/finding counts can be added as unique defects; ACCEPT means no open observations.

FACT: terminal rows count 44 verifier verdicts, including 33 rejections. PY-08 verdict 6 has five open IDs, three directed repairs and two decisive AC groups. These are different populations; no unique-defect count is inferred.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-repair-cycles.json](../../docs/evidence/wave1-repair-cycles.json)

**Node suite counts**

Claim tested: 310 versus 330 is a test regression or necessarily a false report.

FACT: the reconciliation separates 310 runtime tests from 310+18+2 aggregate tests. Scope reconciliation resolves this apparent discrepancy.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md)

**PY-09 recovery ordering**

Claim tested: Continuation comment was posted before launch.

FACT: allocation at 02:21:37.058Z preceded comment publication at 02:21:38Z by 0.942 seconds. This does not determine the instant of Founder authorization.

authorization_instant: `UNKNOWN`.

Evidence: [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json)

**PY-09-only provider authority**

Claim tested: The inventory states that two later producers crossed authority without a decision.

FACT: later Claude use is corroborated; no extension is present in captured records. Any separate authorization remains UNKNOWN. Preserve first-pass outcomes without ratifying operation.

authorization_extension: `UNKNOWN`.

Evidence: [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md)

**SWF-26 expiry timestamp**

Claim tested: Expired when PY-04 reached DONE at 12:27:21Z.

FACT: SWF-26 is explicitly expired, but the accepted terminal dispatcher DONE time is 12:26:25.430Z. Preserve the old timestamp conflict; apply the named DONE event as the expiry condition.

Evidence: [docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md](../../docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json)

**PY-06 missing actor account**

Claim tested: Interim FI-6 says cause UNKNOWN and the gap closed by itself; SWF-29 records missing delivery and operator recovery.

FACT: both durable accounts exist. The accepted reconciliation follows the SWF-29 incident account; the earlier observer coverage cannot independently reconstruct the pre-capture delivery mechanism. Do not silently reuse the interim 'closed by itself' claim.

Evidence: [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md); [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md)

**Worktree population**

Claim tested: Initial audit reports 45 before, 25 removed, 21 retained and 17 published-but-unlanded.

FACT: these are not a reconciled static population. The amendment records the undercount and a direct 18+2+1=21 recount; the active factory created another verifier worktree during the operation. Use scoped recounts, not subtraction across changing capture moments.

Evidence: [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md); [docs/decisions/2026-09-20-candidate-worktree-retention.md](../../docs/decisions/2026-09-20-candidate-worktree-retention.md); [docs/proposals/INDEX.md](../../docs/proposals/INDEX.md)

**Cleanup implementation debt**

Claim tested: The ignored-cache defect remains unimplemented because later worktrees still emit dirty-retention diagnostics.

FACT: the audit's landing amendment closes debt A in canonical Python; the same defect persists in frozen Node. Historical diagnostic noise cannot overturn the scoped Python closure.

Evidence: [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md); [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md)

**Isolation and no-duplicate proof**

Claim tested: 17/17 means exhaustive independent proof of no production writes, no duplicate computation and continuous WIP across all concurrency scenarios.

FACT: the independent verifier could not re-derive the historical production digest; remote candidate evidence proves scoped published effects; WIP has 34 samples plus one refused acquisition. Accepted limitations remain. No sovereignty or live-profile replacement follows.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md); [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json); [docs/evidence/py10/acceptance-verification.json](../../docs/evidence/py10/acceptance-verification.json)

**Snapshot versus terminal outcome**

Claim tested: Earlier no-first-pass or PY-09-in-flight statements contradict terminal 2/11 first-pass acceptance.

FACT: they describe earlier evidence boundaries and are superseded for aggregation. PY-09B and PY-10 are the two first-pass BIUs; the provider and authorization qualifications remain attached.

Evidence: [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md); [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json); [docs/evidence/wave1-yield-snapshot.md](../../docs/evidence/wave1-yield-snapshot.md); [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md)

## Raw candidate mapping

Raw candidate claims are propositions considered, not an independently counted incident series. Per-candidate evidence paths are retained in the authoritative JSON.

| Candidate | Claim type | Proposition considered | Lesson / assessment |
|---|---|---|---|
| RAW-001 | INFERENCE | Tests compare constants or fail before the named guard. | LRN-001 |
| RAW-002 | INFERENCE | Mutation leaves a binding-rule violation green. | LRN-001 |
| RAW-003 | INFERENCE | A fixture response masks an omitted live query field. | LRN-001 |
| RAW-004 | INFERENCE | A mutation that is not applied is mistaken for a kill. | LRN-001 |
| RAW-005 | INFERENCE | A correct domain object has no executed production caller. | LRN-002 |
| RAW-006 | INFERENCE | A CLI unit test uses a call shape no real profile supports. | LRN-002 |
| RAW-007 | INFERENCE | A store double admits states the real store forbids. | LRN-002 |
| RAW-008 | INFERENCE | The required proof harness is built only after repeated repairs. | LRN-003 |
| RAW-009 | INFERENCE | Repeated repair churn is mistaken for a need to split. | LRN-003 |
| RAW-010 | INFERENCE | Near-completion context omits the smallest remaining proof obligation. | LRN-003 |
| RAW-011 | INFERENCE | A repair deletes previously valid tests. | LRN-004 |
| RAW-012 | INFERENCE | A behavioral fix regresses an already-satisfied criterion. | LRN-004 |
| RAW-013 | INFERENCE | A repair restarts from baseline rather than preserving the rejected candidate. | LRN-004 |
| RAW-014 | INFERENCE | An attention dedupe fix removes the anchor another record type needs. | LRN-004 |
| RAW-015 | INFERENCE | A candidate is inferred from timestamp proximity. | LRN-005 |
| RAW-016 | INFERENCE | Producer mutable bytes are treated as the verifier's immutable candidate. | LRN-005 |
| RAW-017 | INFERENCE | Local worktrees are retained merely because they contain ignored caches. | LRN-005 |
| RAW-018 | INFERENCE | A transient push is treated as durable retention. | LRN-005 |
| RAW-019 | INFERENCE | Unique partial work is lost during provider replacement. | LRN-005 |
| RAW-020 | INFERENCE | A release names a fabricated baseline. | LRN-006 |
| RAW-021 | INFERENCE | A status transition occurs without a complete authorizing release record. | LRN-006 |
| RAW-022 | INFERENCE | Assessment baseline is confused with release/allocation baseline. | LRN-006 |
| RAW-023 | INFERENCE | Rewritten timestamps mint duplicate attention items. | LRN-007 |
| RAW-024 | INFERENCE | All invocation-free liveness gaps collapse onto an acknowledged attention item. | LRN-007 |
| RAW-025 | INFERENCE | A successful provider invocation is mistaken for a work verdict. | LRN-008 |
| RAW-026 | INFERENCE | A no-verdict replacement verifier is counted as a rejected candidate. | LRN-008 |
| RAW-027 | INFERENCE | Provider replacement increments an invocation count but not an execution cycle. | LRN-009 |
| RAW-028 | INFERENCE | Verifier restart is mistaken for another repair pass. | LRN-009 |
| RAW-029 | INFERENCE | An operator display or trajectory owns the cycle instead of consuming kernel state. | LRN-009 |
| RAW-030 | INFERENCE | A dropped trigger leaves a nonterminal BIU without its required actor. | LRN-010 |
| RAW-031 | INFERENCE | Healthy dispatcher and tunnel are mistaken for progress. | LRN-010 |
| RAW-032 | INFERENCE | A single 25-second sample declares recovery failed before a valid lane claim arrives. | LRN-010 |
| RAW-033 | INFERENCE | A completed blocking effect is treated as a missing actor. | LRN-011 |
| RAW-034 | INFERENCE | Provider exhaustion causes repeated quota-burning launches. | LRN-011 |
| RAW-035 | INFERENCE | Acknowledged is used to mean seen rather than resolved or superseded. | LRN-011 |
| RAW-036 | INFERENCE | Delivery-id dedupe is mistaken for effect dedupe. | LRN-012 |
| RAW-037 | INFERENCE | An unknown effect is blindly repeated after restart. | LRN-012 |
| RAW-038 | INFERENCE | A watcher pre-check is claimed to prevent a racing duplicate. | LRN-012 |
| RAW-039 | INFERENCE | Measured-only CLI budgets fail as interrupted invocations. | LRN-013 |
| RAW-040 | INFERENCE | A provider-capacity failure is misclassified as a readiness or implementation verdict. | LRN-013 |
| RAW-041 | INFERENCE | Alternate-provider continuation requires explicit bounded routing authority. | LRN-013 |
| RAW-042 | INFERENCE | D4: Node permission assumptions are copied across a changed custody boundary. | LRN-014 |
| RAW-043 | INFERENCE | D5: a discriminating preflight passes the wrong specification. | LRN-014 |
| RAW-044 | INFERENCE | D6: acceptance demands isolation the platform cannot enforce. | LRN-014 |
| RAW-045 | INFERENCE | Provisioning is mistaken for implementation of the live transport. | LRN-015 |
| RAW-046 | INFERENCE | A capability is deferred to a capstone whose scope does not own it. | LRN-015 |
| RAW-047 | INFERENCE | SPLIT_RECOMMENDED creates a preceding BIU with explicit lineage. | LRN-015 |
| RAW-048 | INFERENCE | Dependency rewrites and requirement extents must survive the split. | LRN-015 |
| RAW-049 | INFERENCE | Issue CLOSED is treated as canonical DONE. | LRN-016 |
| RAW-050 | INFERENCE | Native dependency projections disagree with the authorized contract DAG. | LRN-016 |
| RAW-051 | INFERENCE | Sandbox dependency representation differs from the plan. | LRN-016 |
| RAW-052 | INFERENCE | Intermediate lifecycle state is absent from the Project display. | LRN-016 |
| RAW-053 | INFERENCE | D2: a second evidence dataset diverges from the established trajectory conventions. | LRN-017 |
| RAW-054 | INFERENCE | Unknown or partial telemetry is converted to zero. | LRN-017 |
| RAW-055 | INFERENCE | Closed and carried findings are counted as unique defects. | LRN-017 |
| RAW-056 | INFERENCE | DONE signal, dispatcher completion and Issue closure are conflated. | LRN-017 |
| RAW-057 | INFERENCE | Six candidates plus main is reported as seven candidates plus repair. | LRN-017 |
| RAW-058 | INFERENCE | Runtime-only and aggregate Node test counts are compared as if equivalent. | LRN-017 |
| RAW-059 | INFERENCE | Worktree population arithmetic contradicts its own classification table. | LRN-017 |
| RAW-060 | INFERENCE | Evidence consistency is captured as overlapping SF-REQ-054 beside SF-REQ-030. | LRN-018 |
| RAW-061 | INFERENCE | A custody-retention rule is incorrectly presumed to need a new requirement. | LRN-018 |
| RAW-062 | INFERENCE | Cycle consumers are mistaken for separate owners of execution state. | LRN-018 |
| RAW-063 | INFERENCE | Persistent monitoring survives while its session wake-up disappears. | LRN-019 |
| RAW-064 | INFERENCE | DONE is classified healthy even though another release requires judgment. | LRN-019 |
| RAW-065 | INFERENCE | A delivered notification command is treated as proof someone saw it. | LRN-019 |
| RAW-066 | INFERENCE | A recovery-only provider override persists into later BIUs. | LRN-020 |
| RAW-067 | INFERENCE | Wave completion is mistaken for proof every bootstrap replacement is ready. | LRN-020 |
| RAW-068 | INFERENCE | Temporary coordinator behavior silently becomes standing authority. | LRN-020 |
| RAW-069 | INFERENCE | D3: provenance is inserted as an unsupported profile key. | LRN-021 |
| RAW-070 | INFERENCE | Coordinator provider tooling inherits an ambient credential that selects the wrong authentication path. | LRN-022 |
| RAW-071 | INFERENCE | Provider-specific invocation flags do not have identical enforcement semantics. | LRN-022 |
| RAW-072 | INFERENCE | Provider adapters expose different raw log shapes. | LRN-023 |
| RAW-073 | INFERENCE | Normalized progress signals are missing from the compared evidence. | LRN-023 |
| RAW-074 | INFERENCE | Buffered versus streaming output may change apparent liveness. | LRN-023 |
| RAW-075 | INFERENCE | Persistent cleanup diagnostics are emitted as new events on every sweep. | LRN-024 |
| RAW-076 | INFERENCE | Diagnostic volume hides operational signal. | LRN-024 |
| RAW-077 | INFERENCE | Incomplete contracted work is presented as missing Founder authority. | LRN-025 |
| RAW-078 | INFERENCE | A worker misreads adapter-only scope and asks for authority already granted. | LRN-025 |
| RAW-079 | INFERENCE | The coordinator temporarily executes a PY-04 mutation battery before independent verification. | LRN-026 |
| RAW-080 | INFERENCE | A checkpoint exists but no replacement episode is shown consuming it. | LRN-027 |
| RAW-081 | INFERENCE | A long coordinator episode can hide required continuation state. | LRN-027 |
| RAW-082 | INFERENCE | Zero blocking findings is mistaken for zero residual observations. | LRN-028 |
| RAW-083 | INFERENCE | A scoped accepted BIU is reported as completing an entire Product Requirement. | LRN-028 |
| RAW-084 | INFERENCE | A retained producer proof is described as independently reproduced when access was unavailable. | LRN-028 |
| RAW-085 | INFERENCE | A sampled WIP or unchanged endpoint check is overstated as continuous exhaustive isolation proof. | LRN-028 |
| RAW-086 | INFERENCE | Nonterminal outcomes cause indefinite redispatch. | LRN-029 |
| RAW-087 | INFERENCE | An external proof timeout is mistaken for a product-owned run budget. | LRN-029 |
| RAW-088 | INFERENCE | Worker outcome read-back disappears on process restart. | LRN-030 |
| RAW-089 | INFERENCE | A restart therefore needs human judgment even where durable outcome evidence could make recovery decidable. | LRN-030 |
| RAW-090 | HYPOTHESIS | D8: release parser does not recognize PY-09B suffix grammar. | LRN-006 — Participant-only incident and test claim; a valid suffix is corroborated by SWF-33, but the actual parser failure/red run is not retained. Absorb compatibility review into existing release admission; do not count another proven release defect. |
| RAW-091 | HYPOTHESIS | D9: a process filter misses the systemd-managed Node bootstrap. | LRN-017 — Participant account only; do not assert PID or operational status from this anecdote. |
| RAW-092 | INFERENCE | D9: a worktree estimate of about 14 is corrected by a count of 45. | LRN-017 — The audit corroborates the measured initial count; the earlier estimate itself is participant-only. |
| RAW-093 | INFERENCE | D9: detached background watcher loses harness notifications. | LRN-019 — SWF-27 independently exists as binding durable mechanism/incident record. |
| RAW-094 | HYPOTHESIS | D9: deleting a branch from the wrong cwd leaves cleanup incomplete. | LRN-005 — Participant-only cleanup anecdote; retained as a candidate for custody read-back discipline, not a measured cleanup failure. |
| RAW-095 | HYPOTHESIS | D9: a script abort leaves a partial documentation commit. | LRN-017 — Participant-only publication anecdote; no new incident count or causal attribution. |
| RAW-096 | HYPOTHESIS | D9: a 3602-second waiter is misreported as a 35-minute unexplained failure. | LRN-017 — Participant labels this a reporting error, not a system defect; no measured lifetime is adopted. |
| RAW-097 | HYPOTHESIS | D9: pkill matches its own shell. | NOT PROMOTED — Not promoted to a material Wave 1 lesson: only participant recollection, no independently reconstructible incident or distinct control established. |
| RAW-098 | HYPOTHESIS | D9 MEMORY-ONLY: stale hardcoded watcher timestamp fires again. | NOT PROMOTED — Durability gap; not counted as an observed recurrence. Related known attention identity is already LRN-007. |
| RAW-099 | HYPOTHESIS | D9 MEMORY-ONLY: mutation battery fails on a minimal environment. | NOT PROMOTED — Durability gap; no supported standalone lesson. Reproducibility concerns remain with LRN-002 and LRN-017. |
| RAW-100 | HYPOTHESIS | Verification-first sequencing or provider substitution caused the two first-pass acceptances. | NOT PROMOTED — Not established: scope, provider, baseline and sequencing changed together; no causal performance conclusion. |
| RAW-101 | INFERENCE | Typed error paths fail closed but escape as raw exceptions. | LRN-002 — Absorb into real-composition negative-path proof rather than minting a generic error-handling requirement. |

## Verification and exit gate

```json
{
  "verification": {
    "existing_checker": {
      "command": "rtk proxy python3 -B tools/evidence/check_wave1.py --negative-controls",
      "exit_code": 0,
      "checks": 1075,
      "failures": 0,
      "negative_controls_killed": 13,
      "negative_controls_total": 13,
      "scope": "Offline retained source/Git consistency only; no live proof rerun and no external readback."
    },
    "existing_derivation": {
      "command": "rtk proxy python3 -B -",
      "entrypoint": "Imported tools/evidence/reconcile_wave1.py and called derive(read(SOURCE)) in memory, without generate() or --write.",
      "exit_code": 0,
      "bius": 11,
      "verdict_records": 44,
      "derived_events": 235,
      "manifest_rows_equal": true,
      "repair_records_equal": true
    },
    "ledger_validation": {
      "status": "PASS",
      "command": "rtk proxy python3 -B - (in-memory ledger contract validator; no additional file written)",
      "exit_code": 0,
      "scope": "Exact 14 lesson fields; stable unique IDs/classes; one owner and disposition; repository evidence paths opened and existing; attributable BIU/UNKNOWN handling; source-defined recurrence counts; timestamp validity; raw mapping and six-cluster coverage; known requirement IDs; exact JSON/Markdown readback.",
      "negative_controls_killed": 12,
      "negative_controls_total": 12,
      "negative_controls": [
        {
          "violation": "duplicate lesson ID",
          "result": "KILLED",
          "failure": "unique stable sequential IDs"
        },
        {
          "violation": "missing evidence",
          "result": "KILLED",
          "failure": "nonempty evidence"
        },
        {
          "violation": "UNKNOWN recurrence to zero",
          "result": "KILLED",
          "failure": "unestablished recurrence cannot become zero"
        },
        {
          "violation": "multiple owners",
          "result": "KILLED",
          "failure": "exactly one owner"
        },
        {
          "violation": "multiple dispositions",
          "result": "KILLED",
          "failure": "exactly one disposition"
        },
        {
          "violation": "new requirement field",
          "result": "KILLED",
          "failure": "exact 14 lesson fields"
        },
        {
          "violation": "nonexistent evidence",
          "result": "KILLED",
          "failure": "evidence path exists and was opened"
        },
        {
          "violation": "orphan candidate mapping",
          "result": "KILLED",
          "failure": "raw mapping"
        },
        {
          "violation": "wrong raw population",
          "result": "KILLED",
          "failure": "summary populations"
        },
        {
          "violation": "graduation without effectiveness",
          "result": "KILLED",
          "failure": "graduation has factual effectiveness"
        },
        {
          "violation": "missing cluster",
          "result": "KILLED",
          "failure": "six clusters covered"
        },
        {
          "violation": "fabricated source count",
          "result": "KILLED",
          "failure": "source-defined occurrence count"
        }
      ],
      "validator_repair": "The first validator run exited 1 with TypeError on the deliberately list-valued disposition: aggregation ran after shape rejection. It was not counted as a killed control. Validation now returns the explicit shape error before aggregation; all twelve semantic controls then returned specific failures and the valid artifact passed.",
      "input_hashes_verified": 140,
      "preexisting_file_hashes_verified": 2,
      "repository_head_unchanged": true,
      "json_markdown_exact_parity": true,
      "write_scope": "Only docs/evidence/wave1-learning-ledger.json and docs/evidence/wave1-learning-ledger.md were created; both preexisting dispatch metadata files retain their captured hashes. No commit, push, network operation or temporary branch/worktree.",
      "semantic_deduplication": "Author comparison found distinct control predicates for all 30 rows, including discrimination/execution/sequencing/preservation; artifact/effect identity; missing actor/completed judgment/duplicate safety; activation/reconstruction; safe parking/durable outcome recovery; and planning conservation/projection fidelity/owner canonicalization. This is analytical review, not a claim that a string-uniqueness check proves semantic uniqueness."
    }
  },
  "exit_gate": {
    "status": "PASS",
    "material_lessons_evidenced_owned_and_dispositioned": "PASS — each record has opened existing evidence, one existing owner and one disposition; unsupported candidates are explicitly qualified or not promoted.",
    "no_restatements": "PASS — author semantic review of distinct control predicates, raw-candidate mappings and the six cluster decisions; this remains reviewable by the independent coordinator.",
    "no_new_requirement": "PASS — all SF-REQ references preexist; zero new requirements; no existing file, requirement or decision was modified.",
    "internal_consistency_and_paths": "PASS — exact field/type/count checks, source hash preservation, local HEAD readback and deterministic JSON-derived companion parity; twelve malformed controls were rejected.",
    "independent_review": "Subsequent resident coordinator review; not performed or self-approved here."
  }
}
```

## Provenance and preserved repository state

Repository inputs opened or parsed; detailed claims rely on reviewed excerpts cited in evidence_refs. Schema conventions were read first. Existing derivation/checking functions were reused without regeneration writes.

KNOWN_AUTHORIZED dispatch metadata: program-state marks POSTW1-LEARN-002 RUNNING and names its prompt. Both preexisting paths preserved. Task creates no temporary branch/worktree and leaves only the two requested deliverables uncommitted for review.

Preexisting file digests:

| Path | SHA-256 |
|---|---|
| docs/operations/post-wave1-program/program-state.json | `b8e774320cc7f7ffaf5d1c97dc851f024389786ee2e550d620ed2e6d40750cf8` |
| docs/operations/post-wave1-program/prompts/POSTW1-LEARN-002.md | `529bf7f76036546e56eeea091bc3a6a38356a68b14887a35c309dd36df2c066c` |

<details>
<summary>Repository input paths opened (140); per-file hashes are retained in JSON</summary>

- [docs/decisions/2026-09-20-candidate-worktree-retention.md](../../docs/decisions/2026-09-20-candidate-worktree-retention.md)
- [docs/decisions/2026-09-20-convergence-assistance-willing-convergence.md](../../docs/decisions/2026-09-20-convergence-assistance-willing-convergence.md)
- [docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md](../../docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md)
- [docs/decisions/2026-09-20-design-contract-and-design-verification.md](../../docs/decisions/2026-09-20-design-contract-and-design-verification.md)
- [docs/decisions/2026-09-20-deterministic-failure-class-promotion.md](../../docs/decisions/2026-09-20-deterministic-failure-class-promotion.md)
- [docs/decisions/2026-09-20-evidence-and-intake-ratification.md](../../docs/decisions/2026-09-20-evidence-and-intake-ratification.md)
- [docs/decisions/2026-09-20-liveness-reconciliation.md](../../docs/decisions/2026-09-20-liveness-reconciliation.md)
- [docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md)
- [docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md](../../docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md)
- [docs/decisions/2026-09-20-py04-custody-transfer.md](../../docs/decisions/2026-09-20-py04-custody-transfer.md)
- [docs/decisions/2026-09-20-wave1-closure-policy.md](../../docs/decisions/2026-09-20-wave1-closure-policy.md)
- [docs/decisions/2026-09-20-wave1-execution-decisions.md](../../docs/decisions/2026-09-20-wave1-execution-decisions.md)
- [docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md](../../docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md)
- [docs/decisions/2026-09-20-wave1-release-coordinator.md](../../docs/decisions/2026-09-20-wave1-release-coordinator.md)
- [docs/decisions/2026-09-21-biu-execution-cycle-counter.md](../../docs/decisions/2026-09-21-biu-execution-cycle-counter.md)
- [docs/decisions/2026-09-21-py10-transport-split.md](../../docs/decisions/2026-09-21-py10-transport-split.md)
- [docs/decisions/2026-09-21-sandbox-isolation-standard.md](../../docs/decisions/2026-09-21-sandbox-isolation-standard.md)
- [docs/decisions/alienintent-software-factory-plan.md](../../docs/decisions/alienintent-software-factory-plan.md)
- [docs/evidence/2026-09-20-worktree-retention-audit.md](../../docs/evidence/2026-09-20-worktree-retention-audit.md)
- [docs/evidence/2026-09-21-agent-ready-provider-failover.md](../../docs/evidence/2026-09-21-agent-ready-provider-failover.md)
- [docs/evidence/2026-09-21-bootstrap-expiry-inventory.md](../../docs/evidence/2026-09-21-bootstrap-expiry-inventory.md)
- [docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md](../../docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md)
- [docs/evidence/2026-09-21-liveness-retry-and-release-admission.md](../../docs/evidence/2026-09-21-liveness-retry-and-release-admission.md)
- [docs/evidence/2026-09-21-py09-provider-capacity-interruption.md](../../docs/evidence/2026-09-21-py09-provider-capacity-interruption.md)
- [docs/evidence/PY-09B-live-transport.md](../../docs/evidence/PY-09B-live-transport.md)
- [docs/evidence/execution-trajectories/PY-01-summary.md](../../docs/evidence/execution-trajectories/PY-01-summary.md)
- [docs/evidence/execution-trajectories/PY-01.jsonl](../../docs/evidence/execution-trajectories/PY-01.jsonl)
- [docs/evidence/execution-trajectories/PY-02-summary.md](../../docs/evidence/execution-trajectories/PY-02-summary.md)
- [docs/evidence/execution-trajectories/PY-02.jsonl](../../docs/evidence/execution-trajectories/PY-02.jsonl)
- [docs/evidence/execution-trajectories/PY-03-summary.md](../../docs/evidence/execution-trajectories/PY-03-summary.md)
- [docs/evidence/execution-trajectories/PY-03.jsonl](../../docs/evidence/execution-trajectories/PY-03.jsonl)
- [docs/evidence/execution-trajectories/PY-04-evidence-inventory.md](../../docs/evidence/execution-trajectories/PY-04-evidence-inventory.md)
- [docs/evidence/execution-trajectories/PY-04-summary.md](../../docs/evidence/execution-trajectories/PY-04-summary.md)
- [docs/evidence/execution-trajectories/PY-04.jsonl](../../docs/evidence/execution-trajectories/PY-04.jsonl)
- [docs/evidence/execution-trajectories/PY-05-release-snapshot.md](../../docs/evidence/execution-trajectories/PY-05-release-snapshot.md)
- [docs/evidence/execution-trajectories/PY-05-summary.md](../../docs/evidence/execution-trajectories/PY-05-summary.md)
- [docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md](../../docs/evidence/execution-trajectories/PY-05-to-PY-09-extraction-verification.md)
- [docs/evidence/execution-trajectories/PY-05.jsonl](../../docs/evidence/execution-trajectories/PY-05.jsonl)
- [docs/evidence/execution-trajectories/PY-06-summary.md](../../docs/evidence/execution-trajectories/PY-06-summary.md)
- [docs/evidence/execution-trajectories/PY-06.jsonl](../../docs/evidence/execution-trajectories/PY-06.jsonl)
- [docs/evidence/execution-trajectories/PY-07-summary.md](../../docs/evidence/execution-trajectories/PY-07-summary.md)
- [docs/evidence/execution-trajectories/PY-07.jsonl](../../docs/evidence/execution-trajectories/PY-07.jsonl)
- [docs/evidence/execution-trajectories/PY-08-summary.md](../../docs/evidence/execution-trajectories/PY-08-summary.md)
- [docs/evidence/execution-trajectories/PY-08.jsonl](../../docs/evidence/execution-trajectories/PY-08.jsonl)
- [docs/evidence/execution-trajectories/PY-09-summary.md](../../docs/evidence/execution-trajectories/PY-09-summary.md)
- [docs/evidence/execution-trajectories/PY-09.jsonl](../../docs/evidence/execution-trajectories/PY-09.jsonl)
- [docs/evidence/execution-trajectories/PY-09B-summary.md](../../docs/evidence/execution-trajectories/PY-09B-summary.md)
- [docs/evidence/execution-trajectories/PY-09B.jsonl](../../docs/evidence/execution-trajectories/PY-09B.jsonl)
- [docs/evidence/execution-trajectories/PY-10-sandbox-run.jsonl](../../docs/evidence/execution-trajectories/PY-10-sandbox-run.jsonl)
- [docs/evidence/execution-trajectories/PY-10-summary.md](../../docs/evidence/execution-trajectories/PY-10-summary.md)
- [docs/evidence/execution-trajectories/PY-10.jsonl](../../docs/evidence/execution-trajectories/PY-10.jsonl)
- [docs/evidence/py09b-live-checks-2026-09-21.json](../../docs/evidence/py09b-live-checks-2026-09-21.json)
- [docs/evidence/py09b-proven-red-2026-09-21.json](../../docs/evidence/py09b-proven-red-2026-09-21.json)
- [docs/evidence/py10-preflight-2026-09-21-negative-control.json](../../docs/evidence/py10-preflight-2026-09-21-negative-control.json)
- [docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-post-contents-grant.json)
- [docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json](../../docs/evidence/py10-preflight-2026-09-21-pre-contents-grant.json)
- [docs/evidence/py10/acceptance-verification.json](../../docs/evidence/py10/acceptance-verification.json)
- [docs/evidence/py10/ingress-admissions.json](../../docs/evidence/py10/ingress-admissions.json)
- [docs/evidence/py10/offline-suite.json](../../docs/evidence/py10/offline-suite.json)
- [docs/evidence/py10/project-final.json](../../docs/evidence/py10/project-final.json)
- [docs/evidence/py10/proof-run.json](../../docs/evidence/py10/proof-run.json)
- [docs/evidence/py10/proven-red.json](../../docs/evidence/py10/proven-red.json)
- [docs/evidence/py10/run-timeline.jsonl](../../docs/evidence/py10/run-timeline.jsonl)
- [docs/evidence/py10/seed.json](../../docs/evidence/py10/seed.json)
- [docs/evidence/quality/PY-01-quality-evidence.json](../../docs/evidence/quality/PY-01-quality-evidence.json)
- [docs/evidence/quality/PY-02-quality-evidence.json](../../docs/evidence/quality/PY-02-quality-evidence.json)
- [docs/evidence/quality/PY-03-quality-evidence.json](../../docs/evidence/quality/PY-03-quality-evidence.json)
- [docs/evidence/quality/PY-04-quality-evidence.json](../../docs/evidence/quality/PY-04-quality-evidence.json)
- [docs/evidence/quality/PY-05-quality-evidence.json](../../docs/evidence/quality/PY-05-quality-evidence.json)
- [docs/evidence/quality/PY-06-quality-evidence.json](../../docs/evidence/quality/PY-06-quality-evidence.json)
- [docs/evidence/quality/PY-07-quality-evidence.json](../../docs/evidence/quality/PY-07-quality-evidence.json)
- [docs/evidence/quality/PY-08-quality-evidence.json](../../docs/evidence/quality/PY-08-quality-evidence.json)
- [docs/evidence/quality/PY-09-quality-evidence.json](../../docs/evidence/quality/PY-09-quality-evidence.json)
- [docs/evidence/quality/PY-09B-quality-evidence.json](../../docs/evidence/quality/PY-09B-quality-evidence.json)
- [docs/evidence/quality/PY-10-quality-evidence.json](../../docs/evidence/quality/PY-10-quality-evidence.json)
- [docs/evidence/quality/PY-10-sandbox-run-quality-evidence.json](../../docs/evidence/quality/PY-10-sandbox-run-quality-evidence.json)
- [docs/evidence/quality/wave1-cross-biu-comparison.md](../../docs/evidence/quality/wave1-cross-biu-comparison.md)
- [docs/evidence/schema/execution-trajectory-v1.schema.json](../../docs/evidence/schema/execution-trajectory-v1.schema.json)
- [docs/evidence/schema/quality-evidence-v1.schema.json](../../docs/evidence/schema/quality-evidence-v1.schema.json)
- [docs/evidence/wave1-closure-manifest.json](../../docs/evidence/wave1-closure-manifest.json)
- [docs/evidence/wave1-closure-manifest.md](../../docs/evidence/wave1-closure-manifest.md)
- [docs/evidence/wave1-consistency-report.json](../../docs/evidence/wave1-consistency-report.json)
- [docs/evidence/wave1-consistency-report.md](../../docs/evidence/wave1-consistency-report.md)
- [docs/evidence/wave1-evidence-reconciliation.md](../../docs/evidence/wave1-evidence-reconciliation.md)
- [docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md](../../docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md)
- [docs/evidence/wave1-repair-cycles.json](../../docs/evidence/wave1-repair-cycles.json)
- [docs/evidence/wave1-repair-cycles.md](../../docs/evidence/wave1-repair-cycles.md)
- [docs/evidence/wave1-source-observations.json](../../docs/evidence/wave1-source-observations.json)
- [docs/evidence/wave1-yield-snapshot.md](../../docs/evidence/wave1-yield-snapshot.md)
- [docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md](../../docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md)
- [docs/operations/forward-momentum.md](../../docs/operations/forward-momentum.md)
- [docs/operations/py10-sandbox.md](../../docs/operations/py10-sandbox.md)
- [docs/proposals/INDEX.md](../../docs/proposals/INDEX.md)
- [docs/proposals/PROP-2026-0001-deterministic-failure-class-promotion.md](../../docs/proposals/PROP-2026-0001-deterministic-failure-class-promotion.md)
- [docs/proposals/PROP-2026-0002-design-contract-and-design-verification.md](../../docs/proposals/PROP-2026-0002-design-contract-and-design-verification.md)
- [docs/proposals/PROP-2026-0003-persistent-control-plane-bounded-coordinator-episodes.md](../../docs/proposals/PROP-2026-0003-persistent-control-plane-bounded-coordinator-episodes.md)
- [docs/proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md](../../docs/proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md)
- [docs/proposals/PROP-2026-0005-proposal-intake-as-product-capability.md](../../docs/proposals/PROP-2026-0005-proposal-intake-as-product-capability.md)
- [docs/proposals/PROP-2026-0006-deterministic-actor-launch-liveness-reconciliation.md](../../docs/proposals/PROP-2026-0006-deterministic-actor-launch-liveness-reconciliation.md)
- [docs/proposals/PROP-2026-0007-candidate-worktree-retention.md](../../docs/proposals/PROP-2026-0007-candidate-worktree-retention.md)
- [docs/proposals/PROP-2026-0008-biu-execution-cycle-counter.md](../../docs/proposals/PROP-2026-0008-biu-execution-cycle-counter.md)
- [docs/templates/work-packet.md](../../docs/templates/work-packet.md)
- [docs/verification/PY-10-wave1-live-proof.json](../../docs/verification/PY-10-wave1-live-proof.json)
- [docs/verification/PY-10-wave1-live-proof.md](../../docs/verification/PY-10-wave1-live-proof.md)
- [docs/work-units/pre-python-gate/assessments/PG-00.receipt.json](../../docs/work-units/pre-python-gate/assessments/PG-00.receipt.json)
- [docs/work-units/pre-python-gate/assessments/PG-01.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-01.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-02.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-02.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-03.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-03.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-04.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-04.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-05.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-05.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-06.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-06.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-07.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-07.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-08.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-08.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-09.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-09.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-10.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-10.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-11.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-11.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-12.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-12.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-13.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-13.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-14.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-14.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-15.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-15.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-16.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-16.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-17.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-17.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-18.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-18.assessment.json)
- [docs/work-units/pre-python-gate/assessments/PG-19.assessment.json](../../docs/work-units/pre-python-gate/assessments/PG-19.assessment.json)
- [docs/work-units/python/PY-01.assessment.json](../../docs/work-units/python/PY-01.assessment.json)
- [docs/work-units/python/PY-02.assessment.json](../../docs/work-units/python/PY-02.assessment.json)
- [docs/work-units/python/PY-03.assessment.json](../../docs/work-units/python/PY-03.assessment.json)
- [docs/work-units/python/PY-04.assessment.json](../../docs/work-units/python/PY-04.assessment.json)
- [docs/work-units/python/PY-05.assessment.json](../../docs/work-units/python/PY-05.assessment.json)
- [docs/work-units/python/PY-06.assessment.json](../../docs/work-units/python/PY-06.assessment.json)
- [docs/work-units/python/PY-07.assessment.json](../../docs/work-units/python/PY-07.assessment.json)
- [docs/work-units/python/PY-08.assessment.json](../../docs/work-units/python/PY-08.assessment.json)
- [docs/work-units/python/PY-09.assessment.json](../../docs/work-units/python/PY-09.assessment.json)
- [docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json](../../docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json)
- [docs/work-units/python/PY-09B.assessment.json](../../docs/work-units/python/PY-09B.assessment.json)
- [docs/work-units/python/PY-10.assessment.json](../../docs/work-units/python/PY-10.assessment.json)
- [src/providers/claude.mjs](../../src/providers/claude.mjs)
- [src/providers/codex.mjs](../../src/providers/codex.mjs)
- [tools/evidence/check_wave1.py](../../tools/evidence/check_wave1.py)
- [tools/evidence/reconcile_wave1.py](../../tools/evidence/reconcile_wave1.py)

</details>

<details>
<summary>UNKNOWN field paths (100)</summary>

- `records[0].recurrence_count`
- `records[0].first_occurrence`
- `records[0].last_occurrence`
- `records[1].recurrence_count`
- `records[1].first_occurrence`
- `records[1].last_occurrence`
- `records[2].recurrence_count`
- `records[2].first_occurrence`
- `records[2].last_occurrence`
- `records[2].proven_red`
- `records[3].recurrence_count`
- `records[3].first_occurrence`
- `records[3].last_occurrence`
- `records[4].recurrence_count`
- `records[4].first_occurrence`
- `records[4].last_occurrence`
- `records[6].recurrence_count`
- `records[6].first_occurrence`
- `records[6].last_occurrence`
- `records[6].proven_red`
- `records[8].recurrence_count`
- `records[8].first_occurrence`
- `records[8].last_occurrence`
- `records[8].proven_red`
- `records[9].recurrence_count`
- `records[9].first_occurrence`
- `records[9].last_occurrence`
- `records[9].proven_red`
- `records[10].recurrence_count`
- `records[10].first_occurrence`
- `records[10].last_occurrence`
- `records[11].recurrence_count`
- `records[11].first_occurrence`
- `records[11].last_occurrence`
- `records[12].first_occurrence`
- `records[12].last_occurrence`
- `records[12].proven_red`
- `records[13].recurrence_count`
- `records[13].first_occurrence`
- `records[13].last_occurrence`
- `records[14].recurrence_count`
- `records[14].first_occurrence`
- `records[14].last_occurrence`
- `records[15].recurrence_count`
- `records[15].first_occurrence`
- `records[15].last_occurrence`
- `records[16].recurrence_count`
- `records[16].first_occurrence`
- `records[16].last_occurrence`
- `records[17].originating_BIUs`
- `records[17].recurrence_count`
- `records[17].first_occurrence`
- `records[17].last_occurrence`
- `records[17].proven_red`
- `records[18].recurrence_count`
- `records[18].first_occurrence`
- `records[18].last_occurrence`
- `records[18].proven_red`
- `records[19].recurrence_count`
- `records[19].first_occurrence`
- `records[19].last_occurrence`
- `records[19].proven_red`
- `records[20].recurrence_count`
- `records[20].first_occurrence`
- `records[20].last_occurrence`
- `records[21].first_occurrence`
- `records[21].last_occurrence`
- `records[21].proven_red`
- `records[22].recurrence_count`
- `records[22].first_occurrence`
- `records[22].last_occurrence`
- `records[22].proven_red`
- `records[23].recurrence_count`
- `records[23].first_occurrence`
- `records[23].last_occurrence`
- `records[23].proven_red`
- `records[24].recurrence_count`
- `records[24].first_occurrence`
- `records[24].last_occurrence`
- `records[24].proven_red`
- `records[25].first_occurrence`
- `records[25].last_occurrence`
- `records[26].originating_BIUs`
- `records[26].recurrence_count`
- `records[26].first_occurrence`
- `records[26].last_occurrence`
- `records[26].proven_red`
- `records[27].recurrence_count`
- `records[27].first_occurrence`
- `records[27].last_occurrence`
- `records[27].proven_red`
- `records[28].first_occurrence`
- `records[28].last_occurrence`
- `records[29].first_occurrence`
- `records[29].last_occurrence`
- `coordinator_assessment.unknown_costs.complete_coordinator_tokens`
- `coordinator_assessment.unknown_costs.complete_coordinator_cost`
- `coordinator_assessment.unknown_costs.deduplicated_coordinator_delay_seconds`
- `source_conflicts[4].authorization_instant`
- `source_conflicts[5].authorization_extension`

</details>
