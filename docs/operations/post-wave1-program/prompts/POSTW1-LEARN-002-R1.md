# POSTW1-LEARN-002-R1 — narrow repair of the Wave 1 Learning Ledger

You are a fresh Codex GPT-6 Astra session. You authored
`docs/evidence/wave1-learning-ledger.json` and `.md` in POSTW1-LEARN-002 (not in this session —
you have no memory of it; read the artifacts). Independent coordinator review returned
PASS_WITH_QUALIFICATIONS, and the Founder has since issued a decision that changes one of the
constraints you worked under. This is a **narrow repair**, not a re-derivation.

Sandbox is `workspace-write`, escalated solely to rewrite the two ledger files. Change nothing
else.

## 1. What went wrong, and whose fault it was

Not yours. Your dispatch defined the gap bucket as:

> `NEW_CAPABILITY_GAP` — no owner exists and no existing owner can reasonably absorb it

That tests **absorbability**, not **ownership**. Requirement scope is prose, and prose stretches
to absorb almost anything, so the definition routed every lesson to an existing owner. You applied
it faithfully and you flagged the problem in your own text anyway — "SF-REQ-025 **can absorb this
gap**", "SF-REQ-029 **can own** normalized observations", and three records whose
`effectiveness_evidence` you recorded honestly as `"none"`. The schema had nowhere to put that
honesty, because authority and enforcement shared one column. Do not treat those records as errors
you made; treat them as evidence you already surfaced and that now has a field to live in.

## 2. Founder decision POSTW1-DECIDE-002A — quoted, and binding

> Learning Consolidation may and must identify genuine NEW_CAPABILITY_GAP findings when no
> existing canonical owner cleanly owns the semantics. The prohibition on creating new
> requirements during Phase 2 does not prohibit discovering ownership gaps. Do not force-fit
> lessons into adjacent requirements. Repair LRN-018 to STRENGTHEN_EXISTING_OWNER. Perform a
> narrow owner-fit review of LRN-023 and any other lesson whose assigned owner is merely adjacent
> or whose cluster text says no corresponding capability exists. Preserve authority, enforcement
> strength, proven-red status, and effectiveness evidence as separate dimensions. Re-run the
> ledger checks and Claude review of the affected classifications only.

**Discovering an ownership gap is not creating a requirement.** You still create no requirement.
Naming a gap is the finding; minting an owner for it is Phase 3's business and the Founder's.

## 3. Required changes — exactly these

### 3a. Add `owner_fit` to every record (all 30)

A new dimension, separate from `existing_owner` and from `enforcement_level`:

```
CANONICAL   an existing owner cleanly owns these semantics; this lesson is within its subject
ADJACENT    the named owner is related but does not own these semantics; it was stretched to fit
NONE        no existing owner is even adjacent
```

`owner_fit` answers *authority*. `enforcement_level` answers *strength*. `proven_red` answers
*was it ever shown to fail*. `effectiveness_evidence` answers *did it ever demonstrably work*.
Four independent questions. A record may be CANONICAL with no enforcement, or ADJACENT with a
deterministic gate. Do not let one imply another.

### 3b. Repair LRN-018

`ALREADY_GRADUATED` → `STRENGTHEN_EXISTING_OWNER`. The review's reasoning, for the record: your own
effectiveness evidence reads "demonstrated authority-controlled intake practice, not an implemented
idempotent intake service", `proven_red=UNKNOWN`, enforcement `REVIEW_GATE`, evidenced by two
correct outcomes produced by the same Founder-and-coordinator pair that is about to be replaced.
Graduation must survive its authors.

### 3c. Owner-fit review of the adjacent candidates

Deterministically identified for you — every record with `DOCUMENTED_ONLY` or `NONE` enforcement:

    LRN-007, LRN-009, LRN-020, LRN-022, LRN-023, LRN-027, LRN-029, LRN-030

Assess each on **semantic fit alone**. Specific signals already present in your own text:

- **LRN-009** — `effectiveness_evidence: "none"`; "no durable runtime implementation of the SWF-32
  counter is established".
- **LRN-023** — the Observability cluster states adjacent controls are "not evidence that a
  provider progress normalization mechanism exists".
- **LRN-027** — `effectiveness_evidence: "none"`; "no handover occurred and the checkpoint was
  untested".
- **LRN-022** — "SF-REQ-025 can absorb this gap" (your word: gap).

Reaching `NEW_CAPABILITY_GAP` for some of these is an expected outcome, not a failure. Reaching it
for *all* of them would be as suspicious as reaching it for none — assess each on its evidence.
Also check the other 22 records for the same shape; the eight above are where it is most likely,
not where it is exclusively possible.

### 3d. Keep `summary.ownership_gaps` consistent

It must equal the number of records carrying `NEW_CAPABILITY_GAP`. Update
`summary.dispositions` to match the records.

## 4. Acceptance — a checker exists and currently fails

```
python3 tools/evidence/check_learning_ledger.py docs/evidence/wave1-learning-ledger.json
```

Right now it exits 1 with 30 failures. It must exit 0 when you are done. It enforces: `owner_fit`
declared and valid; dimension values valid; **no force-fit** (CANONICAL owner + weak enforcement +
no effectiveness evidence is refused); graduation requires both effectiveness evidence and a
CANONICAL owner; and the declared gap count matches the records.

Do not edit the checker or its tests. If you believe a check is wrong, say so in your terminal
report and leave it failing — an author silently rewriting the check that constrains them is the
exact failure this ledger catalogues.

Also re-run `python3 tools/evidence/check_wave1.py --negative-controls` and confirm it still
passes; the repair must not disturb Wave 1 closure evidence.

## 5. Out of scope — do not expand

- Do not re-derive lessons, re-run the cluster analysis, or change any `learning_id`.
- Do not change records beyond `owner_fit`, and `recommended_disposition` where 3b/3c require it,
  plus any `disposition_rationale` entry you must update to stay truthful.
- Do not analyze the Director's `next_task()` defect. The Founder explicitly deferred it:
  *"don't expand Phase 2 to analyze that now."*
- Do not create, amend or weaken any Product Requirement.
- Do not modify Wave 1 evidence, lifecycle state, Project state or worker contracts.
- Do not `git commit`, `git push`, or use the network.
- Do not begin Phase 3.

## 6. Terminal report — this block and nothing else

```
OWNER_FIT_CANONICAL=<n>
OWNER_FIT_ADJACENT=<n>
OWNER_FIT_NONE=<n>
RECLASSIFIED=<learning_id:OLD->NEW, comma separated, or NONE>
OWNERSHIP_GAPS=<n>
DISPOSITIONS=ALREADY_GRADUATED:<n> STRENGTHEN:<n> GAP_TRAP:<n> NEW_GAP:<n> BOOTSTRAP_ONLY:<n>
LEDGER_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED_CHECKS=<any check you believe is wrong, or NONE>
NOTES=<one line, or NONE>
```
