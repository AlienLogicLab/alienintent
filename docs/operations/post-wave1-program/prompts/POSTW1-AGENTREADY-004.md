# POSTW1-AGENTREADY-004 — Agent-Ready Outcome Completeness Audit

Fresh Codex GPT-6 Astra, dispatched by the local Program Director under the autonomous execution
amendment. Repository root, `workspace-write`, escalated solely for the two deliverables in §5.

## 1. Objective

Ensure **every supported Agent-Ready terminal disposition and execution failure has a
well-defined next process**, so that no supported outcome requires coordinator improvisation.

## 2. Read this before assuming anything

The program plan says your input is "the actual Agent-Ready implementation/schema/CLI" and warns
"do not infer supported outcomes only from Wave 1 observations". The Director checked
deterministically, and you must not spend tokens rediscovering it:

**There is no Agent-Ready implementation, no schema and no CLI in this repository.**

Evidence, in `docs/operations/post-wave1-program/prework/POSTW1-AGENTREADY-004-inputs.json`:

- No module, function or CLI produces an assessment. The only code that mentions Agent-Ready is
  `tools/evidence/reconcile_wave1.py`, which *reads* assessments.
- `src/domain/rai.mjs` is a different concept — its `DISPOSITIONS` are
  `RESOLVED/REJECTED/SUPERSEDED`, which are *finding* dispositions, not readiness dispositions.
  Do not mistake it for the Agent-Ready implementation.
- No `*.schema.json` describes an assessment. The assessment files carry no `schema_version`.

So the matrix must be derived from **governing authority** (the seven decision records listed in
the prework) plus the **retained assessment artifacts**. The absence of an implementation is not
an obstacle to the phase — it is the phase's primary finding, and it belongs in the gap analysis.

If you find an implementation the Director missed, say so in `DISPUTED` with the path. Being
wrong about this is a live possibility and correcting it is more valuable than agreeing.

## 3. Two further deterministic findings you must address

**Schema drift.** 32 retained assessment files carry two incompatible shapes: 17 are MCP
tool-response envelopes (`content`/`structuredContent`/`isError`), 15 carry readiness fields. No
field is present in all 32. `disposition` is present in only 15.

**Non-READY outcomes do not persist.** `BLOCKED` and `SPLIT_RECOMMENDED` appear nowhere as a
persisted disposition, though Wave 1 produced both — `tools/evidence/check_wave1.py:123` asserts
PY-10's verdict sequence as `BLOCKED → SPLIT_RECOMMENDED → READY`. PY-09B retained its non-READY
verdict as a dated sibling file (`PY-09B.assessment.2026-09-21-needs-clarification.json`); PY-10
did not, so its earlier verdicts survive only in trajectory evidence and in a checker's
expectations.

That is directly adjacent to the invariant in §4. Assess whether it constitutes silent coercion
in fact, or merely a retention inconsistency between two BIUs — the distinction matters and the
evidence should decide it, not the suggestive shape.

## 4. The required invariant

> Every Agent-Ready disposition has exactly one defined authority path.
> No non-READY outcome may be silently coerced into READY.
> Resolved prerequisites do not retroactively rewrite an old BLOCKED verdict; reassessment is
> required.

## 5. Deliverables

- `docs/evidence/wave1-agent-ready-outcome-matrix.json` (authoritative)
- `docs/evidence/wave1-agent-ready-outcome-matrix.md` (prose companion, no facts the JSON lacks)

### Per supported disposition

```
disposition  semantic_meaning  authority_owner  lifecycle_effect  next_action
required_artifact  attention_behavior  stale_assessment_rule  reassessment_trigger
DAG_effect  Founder_decision_required  implementation_allowed
```

Exactly one row per disposition. `implementation_allowed` must be `false` for every non-READY
disposition. `authority_owner` names exactly one owner, or an explicit ownership gap.

### Execution failures — separately, and not as dispositions

Cover at least `provider_or_tool_failure`, `timeout`, `malformed_result`,
`missing_terminal_result`, each with `mode`, `is_readiness_disposition: false`, and `next_action`.
These are not readiness dispositions unless the (nonexistent) schema says otherwise — and it
cannot, because it does not exist. Conflating them is how a provider timeout becomes a readiness
verdict, which is the failure LRN-008 records.

### Gap analysis

Include a `gaps` array. At minimum address: the absent implementation/schema/CLI, the schema
drift, and the non-persistence of non-READY dispositions. For each, state the consequence and
who would own a fix — **without creating a Product Requirement**. Recording an ownership gap is
required; minting an owner for it is not yours to do.

Add a provenance block: generating actor, task id `POSTW1-AGENTREADY-004`, HEAD read, input paths
opened.

## 6. Acceptance

```
python3 tools/evidence/check_agent_ready_matrix.py docs/evidence/wave1-agent-ready-outcome-matrix.json
python3 tools/evidence/check_wave1.py --negative-controls
```

The matrix checker enforces the §4 invariant mechanically: required fields, non-READY cannot
permit implementation, non-READY needs a reassessment trigger, one row per disposition, execution
failures not classed as dispositions, all four failure modes covered, and no outcome left to
improvisation. It treats `"none — <why>"` as absence.

Do not edit either checker. **If you believe a check is wrong, say so in `DISPUTED` and leave it
failing.** Twice now a dispute from your predecessor was upheld and found a real defect in a
checker; that outcome is wanted.

## 7. Out of scope

Do not create, amend or weaken any Product Requirement. Do not implement Agent-Ready. Do not
modify the Learning Ledger, the Gap Trap backlog, Wave 1 evidence, lifecycle state, Project
state, worker contracts or Node/B-DISP semantics. Do not `git commit`, push, or use the network.
Do not begin Phase 5.

## 8. Terminal report — this block only

```
DISPOSITIONS_DEFINED=<n>
EXECUTION_FAILURES_DEFINED=<n>
IMPLEMENTATION_FOUND=yes|no
COERCION_FINDING=<silent coercion | retention inconsistency | neither, one line>
GAPS=<n>
OWNERSHIP_GAPS=<n>
MATRIX_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
