# WO-220209 candidate consistency repair (U9, SF-REQ-015)

Date: 2026-09-25. This is a consistency repair of planning evidence. It is not implementation, independent Design Verification, readiness assessment, contract re-compilation or release authority.

## Finding

The Phase 12 candidate `B#/bius/11` (WO-220209, DAG node U9) was compiled at `01af974`, before the 2026-09-22 SF-REQ-015 re-specification (`654e0d7`, recorded in `2026-09-22-respecify-015-039.md`) and the 2026-09-22 SF-REQ-013 re-specification that revised its predecessor U7 (`2026-09-22-respecify-011-013.md`). The re-specifications revised `D#/nodes/11`, `D#/nodes/9`, SF-REQ-015 and contract 4. They did not re-derive the candidate or the U9 fixture, trace and enforcement narratives. Issue #101 comment 5824289247 lists `/bius/11` as stale. Re-applying the derivation rule mechanically found these contradictions:

1. The candidate extent, first criterion and fixture scenario require `OWNER_ASSIGNMENT_HOLD` at the profile boundary. The revised `D#/nodes/11/completion_predicate` requires `CAPABILITY_PROVENANCE_HOLD`, labels the PY-10 replay as historical bootstrap-assessor history ("never label as Agent Ready"), and adds established producer/package provenance plus CLARIFY/SPLIT routing. The re-specification says "D U9 now demands CAPABILITY_PROVENANCE_HOLD rather than OWNER_ASSIGNMENT_HOLD".
2. The candidate carries two contract-4 decisions, the second of which says implementation "requires G1/G2 authority". The current `C#/contracts/4/design_decisions` has three entries; ownership is settled by A1 and referenced through `#/contracts/4/ownership_statement`.
3. SF-REQ-015-AC-02 and AC-05 were rewritten in S (four Agent Ready dispositions READY/CLARIFY/SPLIT/HOLD and routes; PY-10 as Surrogate Readiness Assessment history). The candidate still carries the BLOCKED/NEEDS_CLARIFICATION text.
4. The contract-4 design probes for AC-01, AC-02 and AC-05 changed. `D#/acceptance_trace/17`, `/18`, `/21` and the candidate extents and probes still carry the old probes.
5. `C#/contracts/4/deterministic_enforcement_opportunities/1` (`015-composed-authority`) was rewritten to `CAPABILITY_PROVENANCE_HOLD` and surrogate/provenance negative controls. `D#/enforcement_obligations/9` and the candidate copy still demand `OWNER_ASSIGNMENT_HOLD` and a stub "without G1/G2 authority".
6. `/bius/11/dependency_predicates/WO-220207/completion_predicate` is the pre-revision U7 predicate ("…With allocation gap open, composed initial compile returns AUTHORITY_GAP_HOLD…"). `D#/nodes/9/completion_predicate` is the current source.
7. `/bius/11/partial_work_that_proceeds` ("…no G1/G2 transport implementation.") differs from `D#/nodes/11/proceeds_regardless`.

Pointer key: B = `docs/evidence/wave2-candidate-bius.json`, D = `docs/evidence/wave2-dependency-dag.json`, S = `docs/evidence/wave2-specified-requirements.json`, C = `docs/evidence/wave2-design-contracts.json`. Before editing, each element's identity was asserted in the repair script: `B#/bius/11` is `WO-220209` / `["U9"]`, its `fixed_decisions/0/source` ends `#/contracts/4`; `D#/nodes/11` is `U9` / `["SF-REQ-015"]`; `D#/nodes/9` is `U7`; `D#/nodes/7` is `U5`; `D#/proof_fixtures/11` is `FX-U9`, owner U9; `D#/acceptance_trace/17..21` are `SF-REQ-015-AC-01..05`, owner U9, fixture FX-U9; `D#/enforcement_obligations/8` is `015-envelope-applicability` and `/9` is `015-composed-authority`, both owner U9, source SF-REQ-015; `S#/candidates/4` and `C#/contracts/4` are `SF-REQ-015`; `C#/contracts/4/deterministic_enforcement_opportunities/1` is `015-composed-authority`; `B#/bius/11/dependency_predicates` maps `WO-220205` to U5 and `WO-220207` to U7.

## Authority

- Factory Director handoff inbox entry `director-handoff-wo220209-prep-20260925T0025Z`, under the Founder pipeline direction `founder-pipeline-direction-20260924T112523Z` (`prepareWhenWO220205Lands = [WO-220207, WO-220209]`). WO-220209 is the unit now being prepared.
- Issue #101 comment 5824289247, which lists `/bius/11` as stale.
- `2026-09-22-respecify-015-039.md`: the factory plan SF-REQ-015/039 amendments of 2026-09-22 (A1/A9). It records "New Founder decision required for this reconciliation: **none**".
- `2026-09-22-respecify-011-013.md`: the SF-REQ-013 amendment that revised U7, WO-220209's predecessor.
- `2026-09-22-dv-005-repairs.md`, general scheduling rule (lines 49–50; the precedent calls it the DV-19 rule): "Each finding is applied when its affected unit is next scheduled."

## Derivation rule (nothing invented)

At `01af974` the Phase 12 candidate fields were mechanical copies of Phase 11 and Phase 9 sources. This was re-checked for `/bius/11` against the retained bytes; every row below held exactly:

| Candidate field | Source |
|---|---|
| `title`; `intent` = "Deliver the bounded planned extent: " + title | `D#/nodes/11/title` |
| `scope/dag_scope` | `D#/nodes/11/scope` (empty at `01af974` and now) |
| `scope/extent`, `acceptance_criteria/0` | `D#/nodes/11/completion_predicate` |
| `acceptance_criteria/1..` = "ID: criterion" for each `acceptance_ids` entry | `S#/candidates/4/acceptance_criteria/*/criterion` |
| `acceptance_extents` | `D#/acceptance_trace` rows owned by U9 (`/17..21`) |
| `verification_obligations/proof_fixture` | `D#/proof_fixtures/11` (fixture `scenario` = node `completion_predicate`) |
| `acceptance_probes/*/specified_verification`, `design_probe` | `S#/candidates/4/acceptance_criteria/*/verification`; `C#/contracts/4/acceptance_design_trace/*/design_probe` |
| `fixed_decisions/0/decisions` | `C#/contracts/4/design_decisions` (all entries, verbatim) |
| `partial_work_that_proceeds` | `D#/nodes/11/proceeds_regardless` |
| `dependency_predicates/<BIU>/completion_predicate` | `D#/nodes/<dag_node>/completion_predicate`. Held for all 104 predicate entries in all 46 BIUs at `01af974`. |
| `verification_obligations/enforcement_obligations/*` | `D#/enforcement_obligations` rows with the same `id`. Held 18 of 18 at `01af974`. |
| `D#/enforcement_obligations/*` (`id`, `layer`, `rule`, `proven_red_obligation`, `phase3_promotion`, `status`, `strength`) | `C#/contracts/<req>/deterministic_enforcement_opportunities` entry with the same `id`, plus `source_requirement`, `owner_node`, `fixture_ref`. Held 18 of 18 at `01af974`. |
| `D#/acceptance_trace/*/source_design_probe` | `C#/contracts/<req>/acceptance_design_trace/*/design_probe` for the same acceptance ID. Held for every row at `01af974`. |

The last four rows extend the precedent's table. They were verified mechanically on the `01af974` bytes before being relied on. The repair re-applies the rule to the current revised sources. Every new sentence is a verbatim copy of one of those sources.

## Changes

### `docs/evidence/wave2-dependency-dag.json`

| Pointer | Before | After (source) |
|---|---|---|
| `/proof_fixtures/11/scenario` | "…Replay PY-10 immutable BLOCKED, SPLIT_RECOMMENDED and fresh READY refs. At actual profile boundary unbound/unauthorized stub yields OWNER_ASSIGNMENT_HOLD before launch." | "…Replay PY-10 historical bootstrap-assessor immutable BLOCKED, SPLIT_RECOMMENDED and fresh READY refs, never label as Agent Ready. At actual profile boundary unbound/unauthorized stub yields CAPABILITY_PROVENANCE_HOLD before launch. Require established producer/package provenance, not schema shape; CLARIFY routes via SF-REQ-035 then reassessment; SPLIT routes to the SplitTransaction port … after which U9 lints/reassesses each result." (`D#/nodes/11/completion_predicate`, verbatim) |
| `/proof_fixtures/11/scenario_history` | absent | Holds the old scenario verbatim under `until_2026_09_25`, plus the repair and record path (FX-U7 / DV-15 precedent). |
| `/acceptance_trace/17/source_design_probe` | "Missing lint duties yield pre-assessment hold and zero authority calls. 015-composed-authority covers unbound and unauthorized-stub live composition with OWNER_ASSIGNMENT_HOLD and no release." | "Missing lint duties yield pre-assessment hold and zero calls. 015-composed-authority covers unbound/surrogate composition with CAPABILITY_PROVENANCE_HOLD and no release." (`C#/contracts/4/acceptance_design_trace/0/design_probe`) |
| `/acceptance_trace/18/source_design_probe` | "Four-disposition table plus separate release gate; three non-READY values never launch." | "READY with applicable inputs -> eligibility for separate SF-REQ-002 release gates only; CLARIFY -> … Probe all four routes, stale applicability and reassessment of every split result; no generic planning hold substitutes for the handoff." (`C#/contracts/4/acceptance_design_trace/1/design_probe`) |
| `/acceptance_trace/21/source_design_probe` | "Replay exact retained PY-10 revisions and retrieve all historical blobs without rewriting." | "Replaying the retained PY-10 bootstrap-assessor history preserves verbatim BLOCKED → SPLIT_RECOMMENDED → READY, … retention does not coerce or relabel historical verdicts." (`C#/contracts/4/acceptance_design_trace/4/design_probe`) |
| `/acceptance_trace/17,18,21/source_design_probe_history` | absent | Each holds the old probe verbatim under `until_2026_09_25`, plus the repair and record path. |
| `/enforcement_obligations/9/rule` | "Reuse LRN-002 at the actual live-profile readiness construction/call boundary … Unbound AssessmentAuthority or a stub lacking assigned G1/G2 authority must refuse construction or return OWNER_ASSIGNMENT_HOLD before assessment/release; …" | "Reuse LRN-002 at actual readiness construction/admission with local transport and real temporary SQLite: unbound or unestablished product/package provenance returns CAPABILITY_PROVENANCE_HOLD; … Test doubles are explicitly fixture producers and cannot discharge native-producer proof." (`C#/contracts/4/deterministic_enforcement_opportunities/1/rule`) |
| `/enforcement_obligations/9/proven_red_obligation` | "Bind a stub that returns READY without G1/G2 authority, then bypass the unbound-authority guard separately: each must fail the expected OWNER_ASSIGNMENT_HOLD/no-release assertion; …" | "Supply a schema-perfect surrogate READY, copied provider_evidence, wrong package identity or a response disconnected from its invocation; each must fail native admission. …" (`C#/contracts/4/deterministic_enforcement_opportunities/1/proven_red_obligation`) |
| `/enforcement_obligations/9/rule_history`, `/proven_red_obligation_history` | absent | Each holds the old text verbatim under `until_2026_09_25`, plus the repair and record path. |

`/acceptance_trace/19` and `/20` (AC-03, AC-04) already equal their contract probes and are unchanged. `/enforcement_obligations/8` (`015-envelope-applicability`) already equals its contract entry and is unchanged. No node, edge, `depends_on`, capability owner, priority, completion status, fixture `acceptance_ids`/`enforcement_ids`, enforcement `id`/`layer`/`phase3_promotion`/`status`/`strength`, statistic or requirement changed.

### `docs/evidence/wave2-candidate-bius.json`, `/bius/11` only

| Pointer | Before | After (source) |
|---|---|---|
| `/fixed_decisions/0/decisions` | Two entries: "Known MCP parsing: …" and "This fixes intended consumer semantics only. … implementation/migration of that boundary requires G1/G2 authority." | The three current entries of `C#/contracts/4/design_decisions`, verbatim: "Known MCP parsing: …" (unchanged), "Ownership per #/contracts/4/ownership_statement (DV-5). Producer/version provenance per #/contracts/4/provenance_contract (DV-5)." and "Reuse Before Build: the public Agent Ready product already exists; …". |
| `/scope/extent`, `/acceptance_criteria/0`, `/verification_obligations/proof_fixture/scenario` | The stale OWNER_ASSIGNMENT_HOLD text | `D#/nodes/11/completion_predicate`, verbatim |
| `/dependency_predicates/WO-220207/completion_predicate` | "Reject incomplete contract, uncovered obligation, … With allocation gap open, composed initial compile returns AUTHORITY_GAP_HOLD and emits no successful candidate. Hand-authored allocation fixtures prove validation only." | "Reject incomplete contract, uncovered requirement/acceptance/verification/evidence obligation, … A hand-authored mapping fixture proves validation only; U8 must derive initial decomposition." (`D#/nodes/9/completion_predicate`, verbatim) |
| `/acceptance_criteria/2` | "SF-REQ-015-AC-02: For READY, retain exact assessed inputs and apply separate release gates. BLOCKED holds pending prerequisite resolution; NEEDS_CLARIFICATION holds …" | "SF-REQ-015-AC-02: READY with applicable inputs -> eligibility for separate SF-REQ-002 release gates only; CLARIFY -> …; SPLIT -> …; HOLD -> satisfy prerequisite, then reassess. …" (`S#/candidates/4/acceptance_criteria/1/criterion`) |
| `/acceptance_criteria/5` | "SF-REQ-015-AC-05: Replaying the retained PY-10 assessment revision sequence shows BLOCKED then SPLIT_RECOMMENDED then a distinct fresh READY …" | "SF-REQ-015-AC-05: Replaying the retained PY-10 bootstrap-assessor history preserves verbatim BLOCKED → SPLIT_RECOMMENDED → READY, … These are historical Surrogate Readiness Assessments, not an Agent Ready sequence; …" (`S#/candidates/4/acceptance_criteria/4/criterion`) |
| `/acceptance_extents/0,1,4/source_design_probe` | Old AC-01/02/05 probes | `C#/contracts/4/acceptance_design_trace/0,1,4/design_probe` (same as the repaired D trace rows) |
| `/verification_obligations/acceptance_probes/0,1,4/design_probe` | Old AC-01/02/05 probes | `C#/contracts/4/acceptance_design_trace/0,1,4/design_probe` |
| `/verification_obligations/enforcement_obligations/1/rule`, `/proven_red_obligation` | Old OWNER_ASSIGNMENT_HOLD text | Same values as the repaired `D#/enforcement_obligations/9` (from `C#/contracts/4/deterministic_enforcement_opportunities/1`) |
| `/partial_work_that_proceeds` | "Consumer semantics, retained-envelope parity and unbound-boundary tests with pinned local fixture authority; no G1/G2 transport implementation." | "Consumer semantics, retained-envelope parity and provenance/admission refusal tests at current interfaces; Agent Ready product ownership is settled by A1." (`D#/nodes/11/proceeds_regardless`) |
| `/revision_2026_09_25` | absent | Reason, authority, changed pointers and preserved holds, following `/bius/9/revision_2026_09_25`. |

The following fields are unchanged: `biu_id`, `title` and `intent` (the node title did not change), `dag_node_ids`, requirement links, `dependencies`, the WO-220205 predicate (equals current `D#/nodes/7/completion_predicate`), the dependency `admission` texts, `acceptance_ids` (AC-01..05), `acceptance_criteria/1,3,4` (AC-01/03/04 text unchanged in S), all five `specified_verification` values (unchanged in S), the AC-03/04 extents and probes, `scope/dag_scope` (still empty in D), capability identities, enforcement obligation `015-envelope-applicability`, budget, custody, release policy, stop/escalation conditions, `planning_eligibility` and authority refs (already empty). The other 45 BIUs are unchanged.

### `docs/evidence/wave2-candidate-bius.md`

Unchanged. The WO-220209 title did not change.

## Holds preserved

- Independent revised Design Verification of contract 4; release, budget, custody and live-operation gates (`D#/nodes/11/revision_2026_09_22/preserved_holds`). The R1-GAP-039-ORCHESTRATION and R1-GAP-039-REAL-OUTCOME entries in that record are untouched.
- "capability availability, producer identity, supported contract and independent design verification remain prerequisites" (`C#/contracts/4/ownership_statement`).
- The candidate's own stop rule: "obtain reviewed affected design/DAG revision before implementation". This repair still needs independent review.

## Digests

| File | Before (`5a79622`) | After |
|---|---|---|
| `docs/evidence/wave2-candidate-bius.json` | `6c6e530059a0c076b43ac10750fb313a04b5f5dcd9db7959edc1c6c4c7487fd3` | `5515b6ce24286dd83a40cd295f61dd74a6c55a5b1c407597c0a65db36504d1f1` |
| `docs/evidence/wave2-dependency-dag.json` | `b767305fde58e503bfacac95f3ea8c8eb23c6aabd7bb0211c93d5c6af16402af` | `be5f39f8d6d8c319dfd990ae9f52c32e84e7db6af13ef87f9d45b6cbeff20476` |
| `docs/evidence/wave2-candidate-bius.md` | `a2825259f1d793465c19955b56cb6e1bb42672cdbce80fbc49cd1c868a91c2f4` | unchanged |
| `B#/bius/11`, sorted compact JSON (`sort_keys=True`, `separators=(",", ":")`, default `ensure_ascii`; the contract's candidate digest) | `b859accedd9690a01427e61feb1979c9a9730b22802d5352a9a4595bbf44eeb2` | `0adf1ddfc35b430c91275b54faf26c40445c45b8d80c314d294ef96261add0f0` |

The candidate digest convention was confirmed by reproducing the precedent's `B#/bius/9` value `b2c56f51…dcb6` at `710da90`. Serialization is unchanged. The B file uses `indent=2`, `ensure_ascii=True` and a trailing newline. The D file uses `indent=2`, `ensure_ascii=False` and a trailing newline. Both files were confirmed to re-serialize byte-identically before and after the edit. Key order is preserved and new keys are appended.

## Pinned consumers

These consumers pin the pre-repair whole-file digests `6c6e5300…` (B) and `b767305f…` (D):

- `docs/work-units/wave2/WO-220207.md` (lines 132–133) and `docs/evidence/wave2-execution-packets/WO-220207.proof-packet.draft-r2.md` (lines 13–14), the FX-U7 packet pinned at `5a79622`.

These pins stay valid for their own unit. They pin the revision the packet was compiled against, which remains retrievable at `5a79622`. The repair does not change any byte of U7's elements: `B#/bius/9`, `D#/nodes/9`, `D#/proof_fixtures/9` (FX-U7), `D#/acceptance_trace/10..12` and `D#/enforcement_obligations` for SF-REQ-013. The older pins listed in the WO-220207 record likewise remain valid for their own elements, none of which changed. No tool or test compares these pins to the live files. They were left as they are.

`docs/evidence/wave2-agent-ready-assessments.json` (lines 995, 1011) and `docs/evidence/wave2-founder-approval-packet.json` (lines 28170, 28186) carry `contract_sha256: b859acce…` for the bound historical assessment `POSTW1-READY-013:WO-220209:1` (baseline `01af974`, disposition BLOCKED). That assessment stays valid as history for its own baseline. It does not apply to the repaired candidate, which needs a fresh native Agent Ready run. `wave2-design-verification.json` and the approval packet embed Phase 11/12 text as historical snapshots and are unchanged.

No work unit, execution packet or proof packet for WO-220209 exists yet; the Director's compile step will produce them from the repaired candidate.

## Recorded, not repaired (other units and shared registers; DV-19 rule)

- `S#/candidates/4/acceptance_criteria/5,6` (SF-REQ-015-AC-06 CLI/MCP adapter conformance and AC-07 producer/package provenance), appended by the re-specification, have no `D#/acceptance_trace` rows and are therefore not in `/bius/11/acceptance_ids`, `acceptance_criteria`, `acceptance_extents` or FX-U9 `acceptance_ids`. Assigning proof ownership would be a DAG trace change, so this repair does not do it. The revised U9 completion predicate (now copied into the candidate and FX-U9) already requires "established producer/package provenance, not schema shape", and the repaired `015-composed-authority` requires surrogate/copied-evidence/wrong-package negative controls; AC-06 CLI/MCP conformance also bears on U10. Formal AC-06/AC-07 trace ownership should be settled in a DAG revision before U10 or A is scheduled. The same gap exists for SF-REQ-011-AC-05/06, SF-REQ-013-AC-06..08 and SF-REQ-039-AC-07..09.
- `B#/acceptance_conservation/17`, `/18`, `/21` (U9) are copies of the D trace rows and still carry the old probes; `/12` (U7) was likewise left by the WO-220207 repair. The precedent confined B changes to the unit's own `/bius/N` object, and this repair does the same. The shared register should be re-derived in one pass (all four rows) with the next repair that is authorized to touch it.
- Dependency predicates on the revised U9 predicate are stale in `B#/bius/12` (WO-220210 → WO-220209), `/bius/13` (WO-220211 → WO-220209) and `/bius/22` (WO-220403 → WO-220209). These were already stale before this repair (U9 was revised 2026-09-22). Also stale: WO-220208 → WO-220207, WO-220211 → WO-220208, WO-220506 → WO-220211 and WO-220506 → WO-220210. Each is repaired when its unit is next scheduled. `B#/bius/12`, `/13` and `/22` also still contain `OWNER_ASSIGNMENT_HOLD` text.
- `D#/enforcement_obligations/2` (`013-graph-coverage`, owner U8) and `/11` (`039-composed-lifecycle`, owner O) differ from their contract entries; `D#/acceptance_trace/9` (SF-REQ-013-AC-02, owner U8) differs from its contract probe; FX-U8, FX-U10 and FX-A differ from their node predicates. These belong to U8, O, U10 and A.

## Topology and decisions

**Topology change: none.** The DAG still has 46 nodes, and every edge, capability owner, completion status and statistic is unchanged.

**New Founder decision required: none.** Every changed value is copied from a source that the 2026-09-22 SF-REQ-015 and SF-REQ-013 amendments already settled: the revised U9 and U7 nodes, the SF-REQ-015 criteria, and contract 4 decisions, probes and enforcement entry. The sources do not disagree with each other on any repaired field. The repair makes no product or architecture choice.

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
| `git diff --check` | 0 | clean |

A recursive structural comparison against `5a79622` found changes only at the pointers listed above: in B, 18 leaf/added paths under `/bius/11` (including `fixed_decisions/0/decisions` length 2→3 with entry 0 unchanged, and the added `revision_2026_09_25`); in D, `/proof_fixtures/11`, `/acceptance_trace/17,18,21` and `/enforcement_obligations/9` with their appended `*_history` keys; S and C unchanged; no key-order change. These checks confirm structural and evidence contracts only. They do not execute FX-U9.

## Next action

The next step is an independent review of this repair, as the candidate stop rule requires. After that review, the Factory Director compiles WO-220209 from the repaired candidate (work unit, execution packet, FX-U9 proof packet) and runs native Agent Ready. WO-220209's own admission still requires the verified WO-220205 and WO-220207 predecessor candidates and their retained proof receipts.

## Independent review

A fresh read-only reviewer who did not author the change gave the verdict **ACCEPT_WITH_NOTES**, with no blocking defects.

The reviewer:
- confirmed by recursive structural diff against `5a79622` that only the claimed pointers moved and that S and C are byte-identical;
- checked every identity assertion and the string equality of every new value against its source (D nodes 7/9/11, `S#/candidates/4`, `C#/contracts/4`);
- re-verified the extended derivation rows at `01af974` (104/104 dependency predicates, 18/18 B and D enforcement rows, 53/53 trace probes, 46/46 fixture scenarios) and judged the `015-composed-authority` and WO-220207 dependency-predicate updates to be within a verbatim consistency repair;
- checked byte-identical re-serialization and recomputed all digests (reproducing `b2c56f51…` for `/bius/9` at `710da90`);
- ran all five checkers (PASS), `pytest tools/evidence` (351 passed) and `git diff --check` (clean).

Notes: N1, the "DV-19 rule" attribution, is corrected in the Authority section above. N2, the four stale `B#/acceptance_conservation` rows (12, 17, 18, 21), is already recorded above for one-pass re-derivation. N3 (the coarse `acceptance_criteria` pointer in `revision_2026_09_25/changed`) and N4 (R1-GAP-039 holds retained in `D#/nodes/11/revision_2026_09_22`, not repeated) need no change.

Landed by Factory Director episode `factory-director-b72fe86b08d04397aedd046d9ef6562e`.
