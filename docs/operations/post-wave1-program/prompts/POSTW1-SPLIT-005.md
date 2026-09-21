# POSTW1-SPLIT-005 — BIU Split / Replan Process Design

Fresh Codex GPT-6 Astra, dispatched by the local Program Director under the autonomous execution
amendment. Repository root, `workspace-write`, escalated solely for the deliverables in §5.
**Risk: HIGH.** Independent design review by the Claude bootstrap coordinator follows.

## 1. Objective

Turn `SPLIT_RECOMMENDED` from a signal into a **safe canonical decomposition operation**, so that
a future split can be processed without improvised coordinator procedure.

## 2. The strong invariant

> Splitting may change decomposition, but it must **conserve authorized intent and proof
> obligations**.

Every original requirement, acceptance criterion, verification obligation and evidence obligation
must map to child A, child B, or a retained integration parent. **Nothing silently disappears.**
Splitting redistributes authorized work; it does not alter product intent.

## 3. Deterministic prework — verified, do not redo

`docs/operations/post-wave1-program/prework/POSTW1-SPLIT-005-inputs.json` carries the canonical
text of both owner candidates, the reference incident's verified verdict sequence, and the
identity-allocation evidence.

A caution about that file's provenance, stated plainly because it bears on how much you should
trust it: the *previous* phase's prework contained three errors, all of the same kind — a surface
reading treated as a complete one. Your predecessor disputed all three and was right each time.
This prework records the command that verified each claim. **Check anything that matters to your
design, and dispute what does not hold.**

Two facts the design must reckon with:

- **No BIU-identifier grammar exists anywhere** — not in `src/`, `tools/`, `tests/`, `test/` or
  `scripts/`, and not in authority. The grammar you state will be the first one.
- **Three identifier families are in use with inconsistent widths**: `PG-NN` (20), `PY-NN` (11),
  `WO-NNNNNN` (1), plus exactly one suffixed split allocation, `PY-09B`. A grammar must cover
  what exists or say explicitly which form is canonical and what happens to the others.

## 4. Required semantics — all eleven

`authority` · `lineage` · `requirement_conservation` · `scope_conservation` ·
`dependency_rewriting` · `identity_allocation` · `lifecycle_semantics` ·
`agent_ready_invalidation` · `project_projection` · `evidence` · `closure`

Specifically:

- **Authority** — who may authorize a split/replan, and who may not.
- **Lineage** — original BIU → resulting BIUs, durably recorded.
- **Dependency rewriting** — downstream dependencies must update *deterministically*, not by
  judgement.
- **Identity allocation** — no ad hoc regex assumptions; state the grammar.
- **Lifecycle semantics** — the canonical status of the original BIU: parent, superseded,
  retained integration unit, or another canonical form. Pick one and justify it.
- **Agent-Ready invalidation** — decomposition invalidates stale assessments. Phase 4 established
  that only READY permits implementation and every non-READY outcome carries a reassessment
  trigger; stay consistent with `docs/evidence/wave1-agent-ready-outcome-matrix.json`.
- **Closure** — when is the original intent fully satisfied?

## 5. Deliverables

- `docs/evidence/wave1-biu-split-replan-design.json` (authoritative)
- `docs/evidence/wave1-biu-split-replan-design.md` (prose companion, no facts the JSON lacks)

The JSON must carry: `sections` (the eleven, each defined), `conservation_mapping` (one entry per
obligation with `obligation_id`, `kind`, `origin_biu`, `maps_to`, `rationale`), `identity_grammar`,
`strong_invariant_asserted: true`, `original_biu_lifecycle`, and a provenance block.

Populate `conservation_mapping` from the **real** PY-10 → PY-09B split, not from invented
examples. If an original obligation cannot be traced, record it with `maps_to` naming the
destination and a rationale saying the trace is UNKNOWN — do not fabricate a mapping, and do not
drop the obligation.

## 6. Prefer amendment over new authority

`SF-REQ-013` (Requirements → BIU compilation, with explicit requirement-satisfaction links and
dependency DAGs) and `SF-REQ-015` (BIU lint/readiness) are the candidates to audit. Their canonical
text is in the prework. **Do not presume a new requirement.** If neither cleanly owns the
semantics, record an ownership gap with the proof that neither covers it — Phase 2 established
that "an existing owner could absorb it" is not the same as "an existing owner owns it".

## 7. Acceptance

```
python3 tools/evidence/check_split_design.py docs/evidence/wave1-biu-split-replan-design.json
python3 tools/evidence/check_wave1.py --negative-controls
```

The checker enforces: all eleven sections defined; every obligation maps to a valid destination;
all four obligation kinds represented; an identifier grammar that can express `PY-09B` (the only
split identifier Wave 1 allocated — a grammar that rejects it is wrong about the system it
governs); the strong invariant asserted; and the original BIU's lifecycle defined.

Do not edit any checker. **If you believe a check is wrong, say so in `DISPUTED` and leave it
failing.** Your predecessors disputed checks twice and were upheld both times.

## 8. Out of scope

Do not create, amend or weaken any Product Requirement — recommending an amendment is in scope,
making one is not. Do not modify the Learning Ledger, Gap Trap backlog, Agent-Ready matrix, Wave 1
evidence, lifecycle state, Project state, worker contracts or Node/B-DISP semantics. Do not
retroactively rewrite any historical assessment. Do not `git commit`, push, or use the network.
Do not begin Phase 6.

## 9. Terminal report — this block only

```
SECTIONS_DEFINED=<n of 11>
OBLIGATIONS_MAPPED=<n>
UNTRACEABLE_OBLIGATIONS=<n>
IDENTITY_GRAMMAR=<the expression>
ORIGINAL_BIU_LIFECYCLE=<chosen canonical form>
RECOMMENDED_OWNER=<SF-REQ-### by amendment | ownership gap>
OWNERSHIP_GAPS=<n>
DESIGN_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
