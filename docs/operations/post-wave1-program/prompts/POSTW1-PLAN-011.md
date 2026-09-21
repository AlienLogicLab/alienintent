# POSTW1-PLAN-011 — Wave 2 PLAN and dependency DAG

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §5.
Targeted coordinator review follows on high-risk DAG assumptions.

## 1. Objective

Turn the verified designs into technical sequencing. Exit gate: **every planned capability has
one owner and one dependency path.**

## 2. The lesson this phase exists to encode

> A capstone must integrate previously proven capabilities.
> It must not secretly become first owner of infrastructure required to perform its own proof.

That is PY-10 → PY-09B. PY-10 was the Wave 1 capstone and turned out to be the first owner of the
live transport its own proof depended on. It reached Agent-Ready, returned SPLIT_RECOMMENDED, and
a new BIU had to be inserted mid-wave. The cost was not the split — it was discovering the
ownership gap at readiness assessment rather than at planning.

The checker enforces this directly: a capstone may not own a capability listed in its own
`proof_requires_capabilities`.

## 3. Inputs

- `docs/evidence/wave2-design-contracts.json` — 10 verified contracts (final disposition VERIFIED
  after two repair rounds)
- `docs/evidence/wave2-design-verification.json` — findings, both repairs, three verification
  rounds, and the five open authority gaps
- `docs/evidence/wave2-specified-requirements.json` — specifications and acceptance criteria
- `docs/evidence/wave1-bootstrap-retirement-matrix.json` — 9 mechanisms KEEP_UNTIL_REPLACED; their
  replacement sequence is part of your plan

## 4. Five authority gaps constrain the plan — do not plan around them silently

`R2-GAP-051-EDGE-AUTHORITY` · `R1-GAP-013-ALLOCATION` · `R1-GAP-039-ORCHESTRATION` ·
`R1-GAP-039-REAL-OUTCOME` · `R1-GAP-MONITOR-HOST`

`R1-GAP-013-ALLOCATION` explicitly **blocks Wave 2A completion claims**. A plan that sequences
work as if these were settled is a plan that will be invalidated by the first Founder decision.
Mark each affected node with the gap it waits on, and say what can proceed regardless.

## 5. Required work

identify implementation dependencies · shared substrate · parallel work · required proof fixtures ·
migrations · **bootstrap replacement sequence** · avoid circular dependencies ·
define integration/capstone work

Bootstrap replacement deserves particular care: Phase 6 left nine mechanisms
`KEEP_UNTIL_REPLACED`, and the rule there was "retire by replacement, not by date". The DAG should
make each replacement's dependency path explicit, so no protection is scheduled to disappear
before the thing replacing it exists.

## 6. Deliverables

- `docs/evidence/wave2-dependency-dag.json` (authoritative)
- `docs/evidence/wave2-technical-plan.md` (prose companion)

The JSON must carry `nodes` and `planned_capabilities`. Each node:

```
id  title  requirement_ids  depends_on  is_capstone  owns_capabilities
proof_requires_capabilities  proof_fixtures  parallelisable_with  authority_gap_refs
migration  bootstrap_replacement_for
```

`owns_capabilities` and `proof_requires_capabilities` are what the checker reasons over, so they
must reflect reality rather than aspiration. If a node's proof needs a capability, some node on
its dependency path must own it.

## 7. Acceptance

```
python3 tools/evidence/check_wave2_dag.py docs/evidence/wave2-dependency-dag.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Enforces: acyclicity, all dependencies resolve, exactly one owner per planned capability, the
capstone rule, and that every proof-required capability is reachable on the dependency path.

Do not edit any checker. **Dispute what you believe is wrong** in `DISPUTED` and leave it failing
— every dispute raised in this programme has been upheld, including two that found real defects in
a checker and one that corrected a Director instruction.

## 8. Out of scope

Do not decompose into BIUs (Phase 12) or assess readiness (Phase 13). Do not create, amend or
weaken any requirement, or close any authority gap. Do not modify prior deliverables, Wave 1
evidence, lifecycle state, Project state or worker contracts. Do not `git commit`, push, or use
the network.

## 9. Terminal report — this block only

```
NODES=<n> CAPSTONES=<n>
PLANNED_CAPABILITIES=<n> UNOWNED=<must be 0>
PARALLEL_TRACKS=<n>
BOOTSTRAP_REPLACEMENTS_SEQUENCED=<n of 9>
GAP_BLOCKED_NODES=<n> PROCEEDS_REGARDLESS=<n>
PROOF_FIXTURES=<n>
MIGRATIONS=<n>
DAG_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
