# POSTW1-RETRO-007 — Final Wave 1 Retrospective + Architecture Reconciliation

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §5.
**Risk: HIGH.** Independent coordinator review follows.

## 1. Objective

Produce the **authoritative evidence-backed conclusion of Wave 1**, and reconcile approved lessons
into architecture and requirements before Wave 2 planning begins.

Exit gate: canonical architecture and the requirement set reflect Wave 1 **evidence**, not
pre-Wave assumptions.

## 2. Yield — computed, not for recounting

`docs/operations/post-wave1-program/prework/POSTW1-RETRO-007-yield.json` carries the figures
computed directly from the accepted closure manifest:

11 BIUs · 44 verifier verdicts of which 33 rejections · 44 execution cycles · 2 first-pass
accepted (PY-09B, PY-10) · 9 Founder-exception markers across 7 BIUs · 44 repair records and 46
superseded · elapsed-to-done measured for all 11, totalling ~104,007 s · **token usage and cost
UNKNOWN for all 11**.

Two caveats carried with those numbers, both of which must survive into the retrospective:

- Wave 1 does not distinguish VERIFY failures from REVIEW discoveries, so 33 is a combined count
  and no unique-defect total is derivable.
- Per-BIU `test_count_at_landing` values are cumulative snapshots; their sum (1479) is **not** a
  wave total and must not be reported as one.

Dispute any figure you believe wrong rather than silently recomputing it. Three predecessors
disputed the Director's prework and were upheld each time.

## 3. Causality — the constraint that matters most here

FACT: PY-09B and PY-10 were both first-pass accepted.

The claim that verification-first sequencing or provider substitution **caused** that was tested
in Phase 2 as RAW-100 and not promoted: n=2, and the provider change is confounded with the
sequencing change. The coordinator asserted it and withdrew it. It may appear as HYPOTHESIS with
its confound stated, and as nothing stronger. **Do not claim causality without adequate
evidence** — this is the single most likely place for this retrospective to overreach.

## 4. Required content

**Yield** — the figures above, with UNKNOWN preserved as UNKNOWN.

**Learning** — propagated lessons, mechanized lessons, proven-red controls, and recurring
**ungraduated** failures. The last category is the honest one: Phase 3 declined 11 of 18
candidates, and those declines are findings, not omissions.

**Methodology** — verification-first sequencing, split/decomposition, Agent-Ready outcome
handling, Design Verification, and the REVIEW → Gap Trap → VERIFY movement. Assess whether each
actually worked, with evidence. "It was followed" is not "it worked".

**Architecture** — identity, recovery, provider capacity, observability, transport, Work
Management projection, lifecycle, control plane.

## 5. Reconciliation rule — strict

For every proposed change, in this order:

1. **Existing owner first.** Name it.
2. **Amendment preferred** over a new requirement.
3. **A new Product Requirement only if genuinely uncovered**, with the proof that no existing
   owner covers the semantics — the Phase 2 standard: "an existing owner could absorb it" is not
   "an existing owner owns it".
4. **Priority and Wave are never invented.** If a recommendation would need either, that is a
   Founder decision, not your choice.

You recommend. You do not enact. No requirement is created, amended or weakened by this phase.

## 6. Deliverables

- `docs/evidence/wave1-final-retrospective.json` (authoritative)
- `docs/evidence/wave1-final-retrospective.md` (prose companion)

The JSON must carry `yield`, `learning`, `methodology`, `architecture`, `recommendations` (each
with `proposed_change`, `existing_owner`, `change_type` ∈ {AMENDMENT, NEW_REQUIREMENT,
NO_CHANGE}, `ownership_proof`, `priority_or_wave_invented: false`), `unresolved_founder_decisions`,
and a provenance block.

Three Founder decisions are already open (`POSTW1-DECIDE-004A`, `-005A`, `-006A`); carry them
forward rather than restating them as new.

## 7. Acceptance

```
python3 tools/evidence/check_retrospective.py docs/evidence/wave1-final-retrospective.json
python3 tools/evidence/check_wave1.py --negative-controls
```

The checker enforces the reconciliation rule mechanically: every recommendation names an existing
owner or proves none covers it; `NEW_REQUIREMENT` requires an ownership proof; no recommendation
may invent Priority or Wave; UNKNOWN telemetry may not be reported as a number; and no causal
claim may be made about the two first-pass acceptances above HYPOTHESIS.

Do not edit any checker. If you believe a check is wrong, say so in `DISPUTED` and leave it
failing.

## 8. Out of scope

Do not begin Phase 8 or any Wave 2 design. Do not modify prior phase deliverables, Wave 1
evidence, lifecycle state, Project state, worker contracts or Node/B-DISP semantics. Do not
`git commit`, push, or use the network.

## 9. Terminal report — this block only

```
YIELD_FIGURES_DISPUTED=<list, or NONE>
LESSONS_PROPAGATED=<n> MECHANIZED=<n> UNGRADUATED=<n>
METHODOLOGY_WORKED=<comma list> METHODOLOGY_UNPROVEN=<comma list>
RECOMMENDATIONS=<n> AMENDMENTS=<n> NEW_REQUIREMENTS=<n> NO_CHANGE=<n>
CAUSALITY_CLAIMED=<none | hypothesis-only>
UNRESOLVED_FOUNDER_DECISIONS=<n>
RETRO_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
