# POSTW1-BIU-012 — Wave 2 BIU decomposition

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §5.
High-risk decomposition review follows.

## 1. Objective

Compile the verified Wave 2 plan into **bounded execution units**, each ready to undergo
Agent-Ready assessment in Phase 13.

## 2. Inputs

- `docs/evidence/wave2-dependency-dag.json` — 46 nodes, 13 capstones, 41 capabilities with zero
  unowned, 9 sequenced bootstrap replacements, 46 proof fixtures, 18 migrations
- `docs/evidence/wave2-design-contracts.json` — 10 verified contracts (VERIFIED after two repairs)
- `docs/evidence/wave2-specified-requirements.json` — specifications and acceptance criteria
- `docs/evidence/wave2-design-verification.json` — the five open authority gaps

The DAG is the plan. A BIU set that re-plans rather than compiles is doing Phase 11's job again
and losing the verification that phase earned.

## 3. Apply the learned decomposition rules

The plan names seven. Each is in the ledger because Wave 1 paid for its absence:

- **bounded rework locality** — a defect should not force rework across many units
- **proof harness established early** — Wave 1's recurring shape was a harness built after the
  repair it was meant to judge
- **no unowned substrate** — PY-10 needed live transport nobody owned; found at Agent-Ready
- **no impossible acceptance criteria** — PY-09B binding rule 6 demanded proof the platform
  cannot give, and SWF-34 was needed to undo it
- **requirement conservation** — obligations may be redistributed, never dropped
- **shared capabilities separated where appropriate**
- **capstones integrate rather than invent dependencies**

Five are enforced mechanically by the checker. Two — bounded rework locality and shared-capability
separation — are yours to apply with judgement, and you should say in the companion how you
applied them.

## 4. Per BIU — all sixteen fields

```
intent  requirement_links  fixed_decisions  scope  non_goals  dependencies
acceptance_criteria  verification_obligations  evidence_obligations
architecture_constraints  capabilities  budget  candidate_custody  release_policy
stop_condition  escalation_condition
```

Plus `biu_id`, `is_capstone`, `needs_capabilities`, `provides_capabilities`, `dag_node_ids`, and
`authority_gap_refs`.

`non_goals`, `architecture_constraints` and `dependencies` may legitimately be empty — a root BIU
has no dependencies. The rest may not.

`fixed_decisions` carries what Phase 9 settled so the implementer does not re-decide it. Phase 9's
whole discipline was that implementation is local execution rather than architecture invention;
a BIU that omits the fixed decisions hands that invention back.

## 5. Identifiers

Phase 5 settled the BIU identifier grammar and established that identity must never be derived
from sorting: `\A(?:(?:PG|PY)-[0-9]{2}|WO-[0-9]{6})(?:[A-Z])?\Z`. Wave 2 needs identifiers this
grammar can express, or an explicit statement that Wave 2 requires a grammar extension — which is
an authority question to record, not to settle. Do not invent a shape that the settled grammar
rejects and leave the conflict unstated.

## 6. Authority gaps constrain the set

Five remain open. 23 of 46 DAG nodes are gap-blocked, and the blocking overlaps: resolving
`R1-GAP-MONITOR-HOST` alone frees five nodes completely, the two SF-REQ-039 gaps together free
six, and the rest free one or none individually. Mark each BIU with the gaps it waits on. A BIU
that cannot reach READY until a Founder decision lands should say so rather than appear ready.

## 7. Deliverables

- `docs/evidence/wave2-candidate-bius.json` (authoritative), with `bius`,
  `required_requirements` (the 10 selected ids), `dag_coverage` mapping BIUs to DAG nodes, and
  provenance
- `docs/evidence/wave2-candidate-bius.md` (prose companion, including how you applied the two
  judgement rules)

## 8. Acceptance

```
python3 tools/evidence/check_wave2_bius.py docs/evidence/wave2-candidate-bius.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Enforces: all sixteen fields present and substantive; every needed capability provided by some
BIU; every planned requirement linked; no acceptance criterion demanding proof of a universal
negative; acceptance criteria accompanied by verification obligations; and no capstone both
needing and providing the same capability.

Do not edit any checker. **Dispute what you believe wrong** in `DISPUTED` and leave it failing.

## 9. Out of scope

Do not run Agent-Ready assessment (Phase 13). Do not create, amend or weaken any requirement, or
close any authority gap. Do not modify prior deliverables, Wave 1 evidence, lifecycle state,
Project state or worker contracts. Do not `git commit`, push, or use the network.

## 10. Terminal report — this block only

```
BIUS=<n> CAPSTONES=<n>
DAG_NODES_COVERED=<n of 46>
REQUIREMENTS_LINKED=<n of 10>
GAP_BLOCKED_BIUS=<n> READY_ELIGIBLE_NOW=<n>
IDENTIFIER_GRAMMAR=<conforms | extension_required_recorded>
BOUNDED_REWORK_LOCALITY=<one line on how applied>
SHARED_CAPABILITY_SEPARATION=<one line on how applied>
BIU_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
