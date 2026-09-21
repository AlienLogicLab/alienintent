# POSTW1-LEARN-002-R2 — two records, one field

Fresh Codex GPT-6 Astra session. `workspace-write`, solely to edit
`docs/evidence/wave1-learning-ledger.json` and its `.md` companion. This is the smallest possible
repair; do not re-derive anything.

## Your dispute was upheld

In R1 you reported:

> DISPUTED_CHECKS=no_force_fit conflates semantic ownership with enforcement/effectiveness;
> explicit ownership survives absent implementation. Checker unchanged.

That was correct, and you were right to leave the checker alone and say so rather than edit the
constraint you were working under. The rule has been changed, not you: `no_force_fit` no longer
forbids CANONICAL ownership with weak enforcement and no effectiveness evidence. Authority,
enforcement strength, proven-red status and effectiveness remain four separate dimensions.

A defect in the checker was also found and fixed, and it is mine: `_has_effectiveness` compared
for exact equality with `"none"`, so `"none — no durable runtime implementation is established"`
read as *evidence present*. Two records passed that should not have. Absence is a prefix, not an
equality. That is why this second round exists — R1's PASS was partly my check failing to
discriminate, not your work.

## The one remaining requirement

A CANONICAL claim with weak enforcement and no effectiveness evidence must **cite** its coverage,
because unevidenced it is indistinguishable from the force-fit it replaced. Add a new field:

```
owner_fit_basis   where the named owner explicitly covers these semantics
                  (e.g. "SWF-32 amends SF-REQ-009 to own execution_cycle semantics")
```

Exactly two records currently fail:

- **LRN-009** — `existing_owner: SF-REQ-009`, `DOCUMENTED_ONLY`, effectiveness `"none — no
  durable runtime implementation of the SWF-32 counter is established"`.
- **LRN-027** — `existing_owner: SF-REQ-053`, `DOCUMENTED_ONLY`, effectiveness `"none — the
  inventory says no handover occurred and the checkpoint was untested"`.

For each, do exactly one of:

1. **Cite the coverage** — add `owner_fit_basis` quoting or referencing where that requirement or
   decision explicitly owns these semantics, with a repository path. Keep `owner_fit: CANONICAL`.
2. **Declare the fit ADJACENT** — if on reading the owner you find it does not explicitly cover
   the semantics, set `owner_fit: ADJACENT` and reassess the disposition accordingly.

Verify the citation against the actual text of the owning requirement or decision. Do not assert
coverage from the owner's name or number. If the coverage is not there, option 2 is the honest
answer and costs nothing.

Add `owner_fit_basis` to any other record where you can cite it cheaply, but it is only *required*
for these two.

## Acceptance

```
python3 tools/evidence/check_learning_ledger.py docs/evidence/wave1-learning-ledger.json   # exit 0
python3 tools/evidence/check_wave1.py --negative-controls                                  # still passes
```

Do not edit the checker or its tests. If you dispute a check again, say so and leave it failing.

Keep `summary.ownership_gaps` equal to the count of `NEW_CAPABILITY_GAP` records, and
`summary.dispositions` equal to the records.

## Out of scope

Everything else. No re-derivation, no cluster changes, no `learning_id` changes, no requirement
creation, no lifecycle/Project/worker-contract changes, no commit, no network, no Phase 3.

## Terminal report — this block only

```
LRN-009=CITED|ADJACENT
LRN-027=CITED|ADJACENT
OTHER_BASIS_ADDED=<n>
OWNERSHIP_GAPS=<n>
DISPOSITIONS=ALREADY_GRADUATED:<n> STRENGTHEN:<n> GAP_TRAP:<n> NEW_GAP:<n> BOOTSTRAP_ONLY:<n>
LEDGER_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED_CHECKS=<or NONE>
NOTES=<one line, or NONE>
```
