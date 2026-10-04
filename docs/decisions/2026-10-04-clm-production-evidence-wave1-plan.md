# CLM Production Evidence Wave 1 — Post-Self-Build Planning Baseline

**Date:** 2026-10-04  
**Status:** **Founder-approved planning authority. Not implementation authority.**  
**Applies to:** AlienIntent v2 after the current self-building milestone and the already-planned first ten post-milestone work units.  
**Purpose:** Make normal AlienIntent operation continuously generate production-grade CLM training/evaluation records without changing factory behavior.

## 1. Founder direction

AlienIntent's immediate priority remains unchanged:

> **Reach the point where AlienIntent can begin building itself.**

This plan must not delay or distract from that milestone.

Once self-building is achieved, AlienIntent already has a planned first cohort of ten work units. This document defines the **next ten planning units** to establish a continuous production-grade CLM evidence pipeline.

These are planning units, not yet BIUs. Before implementation they must be reconciled against the canonical v2 plan, decomposed into bounded implementation units, assessed by Agent Ready, and released through the normal AlienIntent lifecycle.

## 2. Why this matters

AlienIntent has already proved that a local generative Director can be benchmarked and that a CLM-style bounded selector can be adapted on AlienIntent decisions. The first CLM adaptation also proved that a small corpus and an overly broad candidate catalog can produce unstable collapse rather than robust selection.

The strategic conclusion is:

> **Do not make learned cognition solve what deterministic system structure can constrain.**

The target stack is:

1. **TRUTH** — deterministic canonical state.
2. **POSSIBILITY** — deterministic legal/action candidate generation.
3. **PREFERENCE** — CLM bounded ranking/selection.
4. **REASONING** — generative Director cognition only when bounded preference is insufficient.
5. **ENFORCEMENT** — deterministic validation and execution.

CLM is therefore not the Factory Director and never owns legal-action generation, lifecycle authority, product priority, or canonical state.

The required milestone is not "CLM v2 trains successfully."

It is:

> **Normal AlienIntent operation continuously emits trustworthy, immutable, adjudication-ready decision records from which CLM models can be trained, evaluated, compared, and retrained without changing how the factory is operated.**

## 3. Relationship to existing benchmark work

The private benchmark workspace at `/mnt/d/Projects/alienintent-model-benchmark` remains the current experimental environment.

Existing work already provides:

- passive Director launch/completion capture;
- a frozen action catalog;
- reviewed cognitive examples;
- family-aware train/validation discipline;
- Qwen3.5-9B generative baseline results;
- CLM-8B zero-shot/adaptation experiments;
- proof-carrying admissibility experiments;
- the rule that candidate reduction must preserve the gold action;
- the rule that repeated episodes from one problem family do not constitute independent holdout evidence.

This plan productionizes the missing evidence path. It does not replace that work.

## 4. Scope

The first production proof is limited to:

> **Factory Director bounded coordination decisions.**

The record schema may carry a generic `decision_family`, but this wave does not independently implement CLM training pipelines for Allocator, recovery, failure classification, context ranking, monitoring, or other future families.

Those are future consumers of the same evidence architecture.

## 5. Planning dependency order

```text
CLM-REC-01  Canonical decision snapshot
      |
CLM-REC-02  Deterministic legal-action generator
      |
CLM-REC-03  Versioned action semantics
      |
CLM-REC-04  Atomic decision-event capture
      |
CLM-REC-05  Decision outcome linkage
      |
CLM-REC-06  Adjudication queue and gold workflow
      |
CLM-REC-07  Family identity and near-duplicate control
      |
CLM-REC-08  Contrast and hard-negative generation
      |
CLM-REC-09  Continuous corpus builder
      |
CLM-REC-10  Shadow CLM evaluation in live operation
```

Some implementation parallelism may be possible after decomposition, but dependency truth governs final BIU scheduling.

## 6. Planning units

### CLM-REC-01 — Canonical decision snapshot

**Outcome:** every bounded cognitive decision can be tied to an immutable, replayable canonical state snapshot.

The current passive capture deliberately leaves `canonical_decision_snapshot_id` null because the Director Host launch fingerprint is not a complete decision-state identity.

The snapshot must contain only authoritative facts required for the decision, including as applicable:

- lifecycle state;
- requirement/work priority;
- dependencies and eligibility;
- WIP/capacity;
- active claims/reservations;
- readiness disposition;
- unresolved external effects;
- blockers/holds;
- applicable authority;
- provider/role availability;
- relevant evidence/policy versions.

**Acceptance direction:**
- deterministic serialization and digest;
- same authoritative state produces the same decision snapshot;
- replay can reconstruct the same bounded facts;
- missing/unknown facts remain explicitly unknown;
- conversational prose and model memory are not authoritative snapshot inputs.

### CLM-REC-02 — Deterministic legal-action generator

**Outcome:** given a canonical decision snapshot, AlienIntent deterministically emits only the actions legally and contextually available at that moment.

Candidate generation must enforce existing:

- dependency rules;
- WIP/capacity;
- lifecycle semantics;
- authority boundaries;
- custody requirements;
- budgets;
- unresolved-effect/reconciliation rules;
- role boundaries.

It ranks nothing.

**Acceptance direction:**
- known gold actions are never excluded when their authoritative preconditions hold;
- deterministically illegal hard negatives are excluded;
- exclusions carry proof/reason codes;
- missing or stale proof fails open with respect to candidate retention rather than incorrectly removing an action;
- candidate generation is versioned and replayable.

### CLM-REC-03 — Versioned action semantics

**Outcome:** reusable CLM actions become stable, versioned model-input contracts.

Each action defines:

- canonical action ID;
- purpose;
- preconditions;
- effects;
- authority limits;
- permitted decision families;
- schema/version identity.

Action wording/semantics are model inputs and must not drift invisibly.

**Acceptance direction:**
- candidate records bind exact action versions;
- semantic changes require a new version/digest;
- cached action representations can be invalidated deterministically;
- aliases/display text cannot silently change model meaning.

### CLM-REC-04 — Atomic decision-event capture

**Outcome:** AlienIntent captures actual decision points rather than treating an entire Director episode as one training example.

Each record binds:

- canonical snapshot ID;
- decision family;
- legal candidate set and action versions;
- selected action;
- selecting actor/model/policy;
- timestamp;
- decision-policy version;
- provenance.

One Director episode may yield zero, one, or multiple atomic decision records.

**Acceptance direction:**
- capture occurs on the real decision boundary;
- no retrospective prose parsing is required to infer what the decision was;
- records are immutable/raw;
- capture failure does not change the production decision path;
- no private chain-of-thought is required or stored.

### CLM-REC-05 — Decision outcome linkage

**Outcome:** decisions can later be associated with observed consequences without fabricating causal certainty.

Outcome evidence may include:

- immediate effect/result;
- worker outcome;
- verifier verdict;
- repair cycles;
- elapsed time;
- provider/model usage;
- cost/token evidence where available;
- resulting blocker;
- downstream lifecycle state;
- supersession or contradiction.

**Acceptance direction:**
- distinguish decision, immediate effect, eventual outcome, and unknown outcome;
- preserve evidence type/provenance;
- no "later therefore caused by" inference;
- outcome updates append evidence rather than rewrite the source decision.

### CLM-REC-06 — Adjudication queue and gold workflow

**Outcome:** immutable raw decision records can be reviewed into training/evaluation labels through a separate governed process.

Adjudication records include:

- preferred/gold action;
- confidence;
- hard negatives;
- adjudication rationale;
- adjudicator identity/model where applicable;
- training eligibility;
- review status;
- problem-family identity;
- disagreement/resolution history.

**Acceptance direction:**
- adjudication never mutates raw capture;
- every gold label has provenance;
- low-confidence/unresolved cases remain excluded from fixed evaluation/training where policy requires;
- Founder-authority and open-reasoning cases remain distinguishable from technical decisions.

### CLM-REC-07 — Family identity and near-duplicate control

**Outcome:** corpus construction cannot count repeated manifestations of one problem as independent evidence or leak near-duplicates across splits.

Capture/adjudication gains:

- problem-family identity;
- incident/lineage identity where applicable;
- near-duplicate fingerprints/signals;
- split-exclusion group.

**Acceptance direction:**
- family members remain in one split group;
- repeated retries/handoffs do not inflate independent sample counts;
- uncertain family identity is explicit;
- corpus builder reports family overlap before release.

### CLM-REC-08 — Contrast and hard-negative generation

**Outcome:** real production decisions can yield controlled training contrasts when deterministic rules prove how a bounded state mutation changes the legal/preferred result.

Examples include:

- WIP free versus WIP occupied;
- dependency satisfied versus unsatisfied;
- known effect versus UNKNOWN effect requiring reconciliation;
- available retry budget versus exhausted retry budget.

These are derived/synthetic records, never independent production episodes.

**Acceptance direction:**
- every derived record points to its real source;
- changed facts are explicit;
- expected consequence is mechanically provable;
- derived data is separately labeled and can be excluded from evaluation holdouts;
- no unconstrained LLM-generated synthetic states enter the trusted corpus.

### CLM-REC-09 — Continuous corpus builder

**Outcome:** a deterministic build produces versioned training/validation/holdout candidates from eligible reviewed records.

The builder must:

- enforce family grouping;
- pin candidate-generator and action-schema versions;
- balance/report class coverage;
- retain hard negatives;
- exclude consumed or contaminated holdouts;
- emit manifests and hashes;
- report missing action coverage and data-quality gates.

**Acceptance direction:**
- same eligible evidence + same policy produces the same corpus;
- manifests record exact input identities;
- family overlap audit is automatic;
- no record silently moves between training and protected holdout populations;
- insufficient coverage fails promotion rather than being hidden by aggregate accuracy.

### CLM-REC-10 — Shadow CLM evaluation in live operation

**Outcome:** a CLM selector can score real production decision packets prospectively without receiving any execution authority.

For every eligible bounded decision:

- normal production path makes the authoritative decision;
- shadow CLM receives the exact canonical snapshot and legal candidates;
- its ranking/confidence/margin and latency are recorded;
- disagreements are retained;
- later observed outcomes can be linked.

**Acceptance direction:**
- shadow execution cannot mutate lifecycle, queue, authority, workspaces, or providers;
- per-family Top-1/Top-k and confidence calibration are measurable;
- illegal-action rate is zero by construction if candidate generation is correct;
- disagreement and escalation behavior are measurable;
- model/head/version drift is visible;
- promotion to any autonomous selection authority requires a separate Founder-approved gate.

## 7. Explicit non-goals

This wave does **not** authorize:

- CLM production decision authority;
- CLM generation of legal actions;
- CLM ownership of lifecycle or product priority;
- automatic model retraining;
- automatic model/head promotion;
- automatic policy adoption;
- weakening deterministic guards to increase model coverage;
- changing Director routing solely to generate training data;
- community/shared-learning upload infrastructure;
- training all future CLM decision families simultaneously;
- replacing Qwen/frontier open reasoning;
- using hidden/private model chain-of-thought as training evidence.

## 8. Evidence principles

1. Raw production observations are immutable.
2. Interpretation/adjudication is separate from observation.
3. Unknown is a valid value and must never be fabricated into certainty.
4. Correlation is not causality.
5. Real and derived/synthetic records are distinguishable.
6. Candidate-set generation must be deterministic and versioned.
7. Action semantics are versioned model inputs.
8. Family/lineage separation protects evaluation validity.
9. Training data never becomes authority merely because it is large.
10. Promotion depends on prospective/shadow evidence, not internal training accuracy alone.

## 9. Significance to all AlienIntent agents

All agents working on AlienIntent should understand this plan because implementation choices made before this wave can either preserve or destroy the evidence needed later.

Agents must therefore avoid introducing architecture that:

- hides decision boundaries inside opaque orchestration;
- merges state observation with model judgment;
- makes legal-action derivation dependent on conversational prose;
- discards action/provider/model/policy identity;
- rewrites evidence rather than appending superseding evidence;
- makes decision/outcome linkage impossible;
- stores required truth only inside a long-lived model session.

This does **not** authorize agents to implement CLM capture opportunistically outside approved BIUs. It establishes a future evidence obligation and design direction.

## 10. Conversion to BIUs

These planning units are intentionally larger than final implementation units.

Before execution:

1. reconcile this plan against the current canonical v2 project plan and requirements;
2. identify existing capabilities that already satisfy part of each planning unit;
3. preserve requirement/architecture ownership rather than duplicating it;
4. decompose each planning unit into cohesive, independently verifiable candidate BIUs;
5. define dependency edges;
6. run Agent Ready against each exact candidate;
7. resolve CLARIFY/SPLIT/HOLD outcomes;
8. create/materialize only READY BIUs;
9. release to IMPLEMENT only through normal authority.

The factory, once capable of self-building, should perform as much of this conversion as its authorized planning/specification machinery permits.

## 11. Completion criterion

This wave is complete when:

> **Normal AlienIntent Factory Director operation continuously produces immutable, replayable, production-grade decision records; those records can be adjudicated into family-safe versioned corpora; and a CLM can run prospectively in shadow mode against the same legal decision packets without influencing factory behavior.**

At that point AlienIntent has earned the right to pursue the next question:

> **Can bounded local learned cognition safely replace a material fraction of expensive generative coordination decisions?**

That question is deliberately outside this plan.
