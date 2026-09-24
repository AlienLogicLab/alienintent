# WO-220207 candidate consistency repair (U7, SF-REQ-013)

Date: 2026-09-25. This is a consistency repair of planning evidence. It is not implementation, independent Design Verification, readiness assessment, contract re-compilation or release authority.

## Finding

The Phase 12 candidate `B#/bius/9` (WO-220207, DAG node U7) was compiled at `01af974`, before the 2026-09-22 SF-REQ-013 re-specification (`8ca65da`, recorded in `2026-09-22-respecify-011-013.md`). The re-specification revised `D#/nodes/9`, SF-REQ-013 and contract 2. It did not re-derive the candidate or the U7 fixture and trace narratives. The Factory Director's preparation record on Issue #101 found three contradictions:

1. The candidate required `AUTHORITY_GAP_HOLD` for R1-GAP-013-ALLOCATION. That gap is `SETTLED_BY_AMENDMENT` (`C#/authority_gaps/2/resolution_2026_09_22`, DV-1). `D#/nodes/9/authority_gap_refs` is already empty.
2. The candidate refused every rewrite and excluded split/replan. The revised `D#/nodes/9/completion_predicate` and SF-REQ-013-AC-05 (`S#/candidates/2/acceptance_criteria/4`) instead require validation of conserved split/replan candidates. The re-specification says `INITIAL_ONLY` and `OUT_OF_SCOPE_REPLAN` are superseded.
3. `D#/proof_fixtures/9` (FX-U7) and `D#/acceptance_trace/12` (SF-REQ-013-AC-05, owner U7) still carried the stale narrative.

Pointer key: B = `docs/evidence/wave2-candidate-bius.json`, D = `docs/evidence/wave2-dependency-dag.json`, S = `docs/evidence/wave2-specified-requirements.json`, C = `docs/evidence/wave2-design-contracts.json`. Before editing, each element's identity was asserted: `B#/bius/9` is `WO-220207` / `["U7"]`; `D#/nodes/9` is `U7` / `SF-REQ-013`; `D#/proof_fixtures/9` is `FX-U7`, owner U7; `D#/acceptance_trace/12` is `SF-REQ-013-AC-05`, owner U7, fixture FX-U7; `S#/candidates/2` and `C#/contracts/2` are `SF-REQ-013`; `C#/authority_gaps/2` is `R1-GAP-013-ALLOCATION`.

## Authority

- Issue #101, Factory Director preparation record (episode `factory-director-3b19543ca543423f8ef9791f7be8c90b`): "This is a consistency repair, not a Founder decision". Next authorized action 1 is this repair.
- `2026-09-22-respecify-011-013.md`: the factory plan SF-REQ-013 amendment of 2026-09-22. It settles compiler derivation and split/replan ownership and records "New Founder decision required for this reconciliation: none".
- `2026-09-22-dv-005-repairs.md`, DV-19 rule: "Each finding is applied when its affected unit is next scheduled." WO-220207 is the unit now being scheduled.

## Derivation rule (nothing invented)

At `01af974` the Phase 12 candidate fields were mechanical copies of Phase 11 and Phase 9 sources. This was checked against the retained bytes:

| Candidate field | Source |
|---|---|
| `title`; `intent` = "Deliver the bounded planned extent: " + title | `D#/nodes/9/title` |
| `scope/dag_scope` | `D#/nodes/9/scope` (empty at `01af974`) |
| `scope/extent`, `acceptance_criteria/0` | `D#/nodes/9/completion_predicate` |
| `acceptance_criteria/1..` = "ID: criterion" for each `acceptance_ids` entry | `S#/candidates/2/acceptance_criteria/*/criterion` |
| `acceptance_extents` | `D#/acceptance_trace` rows owned by U7 |
| `verification_obligations/proof_fixture` | `D#/proof_fixtures/9`. At `01af974`, every fixture's `scenario` equalled its node's `completion_predicate` (46 of 46). |
| `acceptance_probes/*/specified_verification`, `design_probe` | `S#/candidates/2/acceptance_criteria/*/verification`; `C#/contracts/2/acceptance_design_trace/*/design_probe` |
| `fixed_decisions/0/decisions` | `C#/contracts/2/design_decisions` (all entries, verbatim) |
| `partial_work_that_proceeds` | `D#/nodes/9/proceeds_regardless` |

The repair re-applies the same rule to the current revised sources. Every new sentence is a verbatim copy of one of those sources.

## Changes

### `docs/evidence/wave2-dependency-dag.json`

| Pointer | Before | After (source) |
|---|---|---|
| `/proof_fixtures/9/scenario` | "…stale design and rewrite of existing decomposition. With allocation gap open, composed initial compile returns AUTHORITY_GAP_HOLD and emits no successful candidate. Hand-authored allocation fixtures prove validation only." | "Reject incomplete contract, uncovered requirement/acceptance/verification/evidence obligation, … stale design or unauthorized/nonconserving replan. Validate deterministic identity rewrites, preserved predicates, lineage and immutable stale-assessment history. A hand-authored mapping fixture proves validation only; U8 must derive initial decomposition." (`D#/nodes/9/completion_predicate`, verbatim) |
| `/proof_fixtures/9/scenario_history` | absent | Holds the old scenario verbatim under `until_2026_09_25`, plus the repair and record path. This follows the DV-15 `FX-U10/scenario_history` precedent. |
| `/acceptance_trace/12/source_design_probe` | "Approved decomposition identity refuses rewrite without mutating prior candidate/BIUs." | "Freeze original clauses, conserve all obligation extents in child/Integration Parent, preserve intent/proof and budget; reject stale/unauthorized or weakening mutation before atomic apply." (`C#/contracts/2/acceptance_design_trace/4/design_probe`) |
| `/acceptance_trace/12/source_design_probe_history` | absent | Holds the old probe verbatim under `until_2026_09_25`, plus the repair and record path. |

No node, edge, `depends_on`, capability owner, priority, completion status, fixture `acceptance_ids`/`enforcement_ids`, statistic or requirement changed.

### `docs/evidence/wave2-candidate-bius.json`, `/bius/9` only

| Pointer | Before | After (source) |
|---|---|---|
| `/title` | "Compiler validation and explicit allocation hold" | "Compiler validation and conserved obligation mapping" (`D#/nodes/9/title`) |
| `/intent` | "…: Compiler validation and explicit allocation hold" | "…: Compiler validation and conserved obligation mapping" (derived from the title) |
| `/fixed_decisions/0/decisions` | Two entries: "…return the allocation-source question and constraints to SPECIFY via R1-GAP-013-ALLOCATION…" and "SF-REQ-013 pending split/replan amendment (POSTW1-DECIDE-005A/-007A) is expressly excluded…" | The six current entries of `C#/contracts/2/design_decisions`, verbatim. They open with "R1-GAP-013-ALLOCATION is resolved by the SF-REQ-013 amendment…" and "SPLIT-G1 is resolved by the same amendment: SF-REQ-013 owns Split Transactions…". |
| `/scope/dag_scope` | "" | "Validation of compiler-derived initial candidates and conserved split/replan candidates: …" (`D#/nodes/9/scope`) |
| `/scope/extent`, `/acceptance_criteria/0`, `/verification_obligations/proof_fixture/scenario` | The stale AUTHORITY_GAP_HOLD / "rewrite of existing decomposition" text | `D#/nodes/9/completion_predicate`, verbatim |
| `/acceptance_criteria/3` | "SF-REQ-013-AC-05: A request to rewrite an existing approved decomposition is identified as outside this initial-compilation scope and retained for the pending split/replan decision; it must not mutate existing BIUs." | "SF-REQ-013-AC-05: Given an authorized split of a pinned existing decomposition, freeze all original obligations and conserve 100% in resulting units or a retained Integration Parent. …" (`S#/candidates/2/acceptance_criteria/4/criterion`) |
| `/acceptance_extents/2/source_design_probe` | "Approved decomposition identity refuses rewrite…" | `C#/contracts/2/acceptance_design_trace/4/design_probe` (same as the repaired D trace) |
| `/verification_obligations/acceptance_probes/2/specified_verification` | "Controlled fixture or independently inspected versioned artifact; …" | "Replay the SWF-33 PY-10 / PY-09B precedent as a historical contract fixture, not a live mutation; …" (`S#/candidates/2/acceptance_criteria/4/verification`) |
| `/verification_obligations/acceptance_probes/2/design_probe` | "Approved decomposition identity refuses rewrite…" | `C#/contracts/2/acceptance_design_trace/4/design_probe` |
| `/partial_work_that_proceeds` | "Validation and refusal mechanics without decomposition algorithm or BIU output." | "Independent validation/refusal mechanics remain testable; successful compilation and mutation additionally require the exact verified design and applicable authority." (`D#/nodes/9/proceeds_regardless`) |
| `/revision_2026_09_25` | absent | Reason, authority, changed pointers and preserved holds. This follows the `/bius/0/revision_2026_09_22` precedent. |

The following fields are unchanged: `biu_id`, `dag_node_ids`, requirement links, `dependencies` and `dependency_predicates`, `acceptance_ids` (AC-03/04/05), `acceptance_criteria/1..2` (AC-03/04 text unchanged in S), the AC-03/04 extents and probes, the capability identities (including the persisted `compilation_validation_hold`), enforcement obligation `013-dependency-authority`, budget, custody, release policy, stop/escalation conditions, `planning_eligibility` and authority refs (already empty). The other 45 BIUs are unchanged.

### `docs/evidence/wave2-candidate-bius.md`

The WO-220207 inventory row now uses the repaired title. That is the only change.

## Holds preserved

- Exact authority, verified design and normal admission gates (`D#/nodes/9/revision_2026_09_22/preserved_holds`).
- Independent revised Design Verification of the Phase 5 candidate mechanisms (`C#/contracts/2/design_decisions/4`).
- Budget, capability, custody and release prerequisites.
- The candidate's own stop rule: "obtain reviewed affected design/DAG revision before implementation". This repair still needs independent review.

## Digests

| File | Before (`710da90`) | After |
|---|---|---|
| `docs/evidence/wave2-candidate-bius.json` | `61f9324e7d1b7f0937bbc1aff7cbaba77c50192204e109cad5d78edb04f677f7` | `6c6e530059a0c076b43ac10750fb313a04b5f5dcd9db7959edc1c6c4c7487fd3` |
| `docs/evidence/wave2-dependency-dag.json` | `f99c0a7a392f8dd1f7889bb99d926f0a5a9de0948cb09845686f9d7e6f2b1e8d` | `b767305fde58e503bfacac95f3ea8c8eb23c6aabd7bb0211c93d5c6af16402af` |
| `docs/evidence/wave2-candidate-bius.md` | `ea3d2cf3ce38962ecf54ccaa8c04c7e46477a7438d771def05cf5396afa6bb39` | `a2825259f1d793465c19955b56cb6e1bb42672cdbce80fbc49cd1c868a91c2f4` |
| `B#/bius/9`, sorted compact JSON (the contract's candidate digest) | `b2c56f51c99e006a4fef35d082a12585b806a2b46403fec06c20d76042aedcb6` | `00148ba18b4466cb0d30f18ba50af44226210a0c564d15d2f50045af4c3a1ec7` |

Serialization is unchanged. The B file uses `indent=2`, `ensure_ascii=True` and a trailing newline. The D file uses `indent=2`, `ensure_ascii=False` and a trailing newline. Key order is preserved and new keys are appended.

## Pinned consumers

These consumers pin the old whole-file digests:

- `docs/work-units/wave2/WO-220302.md` (lines 108–109) and `docs/work-units/wave2/WO-220304.md` (lines 106–107) pin D and B.
- `docs/evidence/wave2-execution-packets/WO-220303.proof-packet.draft.md` (lines 15–16) and `WO-220304.proof-packet.draft.md` (line 13) pin D and B.
- `docs/evidence/wave2-proof-fixtures/FX-S2/fixture-plan.json` (`input_digests`) pins B.
- `docs/evidence/wo-220203-fx-u3.md`, `wo-220204-fx-u4.md` and `wo-220205-fx-u5.md` pin D.
- `docs/evidence/wave2-execution-packets/WO-220207.proof-packet.draft.md` (line 104) pins D and B by short prefix.

These pins stay valid for their own units. Each one pins the baseline revision it was compiled or proved against, and that revision remains retrievable at `710da90`. The repair does not change any byte of their own elements: C2/C3/C4 nodes, fixtures and `/bius/15..17`, WO-220103's `/bius/2`, or U3/U4/U5 and their fixtures. No tool or test compares these pins to the live files. `tools/evidence/fx_*_evidence.py` records digests when it runs; it does not verify historical pins. The pins were therefore left as they are.

These consumers need updating, but that is the Director's re-compilation step and out of scope here: `docs/work-units/wave2/WO-220207.md` and `docs/evidence/wave2-execution-packets/WO-220207.{packet,allocation}.json`, plus the WO-220207 draft proof packet. They carry the pre-repair candidate (digest `b2c56f51…dcb6`) and the stale AUTHORITY_GAP_HOLD text. They are stale by design until WO-220207 is re-compiled. They were not touched.

`docs/evidence/wave2-founder-approval-packet.json`, `wave2-agent-ready-assessments.json` and `wave2-design-verification.json` embed the Phase 11/12 text as historical snapshots. `wave2-agent-ready-assessments.json` and `wave2-founder-approval-packet.json` also carry `contract_sha256: b2c56f51…` for the bound historical assessment `POSTW1-READY-013:WO-220207:1` (baseline `01af974`, disposition BLOCKED). That assessment stays valid as history for its own baseline. It does not apply to the repaired candidate, which needs a fresh native Agent Ready run. The 2026-09-22 re-specification left them unchanged, and this repair does the same.

## Recorded, not repaired (other units; DV-19 rule)

- `B#/bius/10..13` (WO-220208 through WO-220211, nodes U8, U9, U10 and A) were also compiled before the 2026-09-22 revisions. Their `scope/extent` differs from the revised node predicates. U8 and U10 also carry stale titles, and WO-220208 carries the same superseded contract-2 decisions. The fixture scenarios FX-U8, FX-U9, FX-U10 and FX-A likewise differ from their revised predicates. Each is repaired when its unit is next scheduled.
- `D#/enforcement_obligations/2` (`013-graph-coverage`, owner U8) still says "With R1-GAP-013-ALLOCATION open, composed compilation must return AUTHORITY_GAP_HOLD". This belongs to U8.
- `D#/acceptance_trace` has no rows for SF-REQ-013-AC-06, AC-07 or AC-08, which the re-specification appended. `D#/acceptance_trace/9` (AC-02, owner U8) still carries "After SPECIFY resolves the gap…". Assigning proof ownership for AC-06 to AC-08 would be a DAG trace change, so this repair does not do it. The U7 completion predicate already requires validating deterministic identity rewrites, preserved predicates, lineage and immutable stale-assessment history. Formal AC-07/AC-08 trace ownership should be settled in a DAG revision before U8 or A is scheduled.
- `docs/evidence/wave2-candidate-bius.md` line 5 still says "U7/U8 separate honest allocation holds from conditional initial compilation". That shared U7/U8 narrative is left for the U8 repair.

## Topology and decisions

**Topology change: none.** The DAG still has 46 nodes, and every edge, capability owner, completion status and statistic is unchanged.

**New Founder decision required: none.** Every changed value is copied from a source that the 2026-09-22 SF-REQ-013 amendment already settled: the revised U7 node, the SF-REQ-013 criteria, contract 2 decisions and the probe trace. The repair makes no product or architecture choice.

## Validation

All commands were run with the `rtk proxy` prefix on the final content:

| Command | Exit | Result |
|---|---:|---|
| `python3 tools/evidence/check_wave2_bius.py` | 0 | `result   : PASS  (0 failure(s))` |
| `python3 tools/evidence/check_wave2_dag.py` | 0 | `result     : PASS  (0 failure(s))` |
| `python3 tools/evidence/check_wave2_specify.py docs/evidence/wave2-specified-requirements.json` | 0 | `result     : PASS  (0 failure(s))` |
| `python3 tools/evidence/check_design_contracts.py docs/evidence/wave2-design-contracts.json` | 0 | `result    : PASS  (0 failure(s))` |
| `python3 tools/evidence/check_canonical_vocabulary.py` | 0 | `result    : PASS  (0 failure(s))` |
| `python3 -m pytest tools/evidence -q` | 0 | `351 passed` |

A structural comparison against `710da90` found changes only at the pointers listed above. `git diff --check` is clean. These checks confirm structural and evidence contracts only. They do not execute FX-U7.

## Next action

The next step is an independent review of this repair, as the candidate stop rule requires. After that review, the Factory Director re-compiles WO-220207, re-checks U-1 to U-11, pins the FX-U7 packet and runs native Agent Ready. The WO-220207 contract has no dependency on the Issue #101 title, but the Issue title still reads "explicit allocation hold" and the Director may align it.

## Independent review

A fresh read-only reviewer who did not author the change gave the verdict **ACCEPT_WITH_NOTES**, with no blocking defects.

The reviewer:
- matched every changed pointer exactly against `D#/nodes/9`, `S#/candidates/2` and `C#/contracts/2`;
- ran a recursive structural diff, which showed only the claimed pointers moved;
- checked that re-serialization is byte-identical;
- recomputed the digests;
- ran all five checkers (PASS) and `pytest tools/evidence` (351 passed).

The title/intent change was judged within the repair, because it is the verbatim node title. Note N1, the assessment-digest wording above, is corrected here. Note N2 (the full old digest at line 18 of the WO-220207 draft proof packet) is superseded at re-compile. Note N3 covers the deferred items for U8/A, which are already listed above.

Landed by Factory Director episode `factory-director-4370af4e4d824430a4f3a580cf207686`.
