# WO-220202 / FX-U2 execution record (PRODUCER)

These are local proof receipts only. They are not an independent verdict, not a
release, and not operational success.

## Identity and authority

- **Issue:** #80. RELEASED comment 5808501234 authorizes IMPLEMENT for WO-220202 only
  (DAG node U2, SF-REQ-012).
- **Invocation:** `AlienLogicLab/alienintent#80:PRODUCER:fe10b943-9ca2-450f-9478-88103cf9fd1b`.
- **Worker:** Morty (`morty-worker@factorychecks.com`), Claude `claude-opus-5-5`.
- **Branch:** runtime-managed `b-disp/329464b3-4928-4c6f-bffb-a58291395b1c`.
- **Admission baseline:** `ec9645adc4013c83b405f9080dde3215af90dcb5`. It was clean at
  admission, and baseline `pytest tests` passed 513/513.
- **Work order:** `docs/work-units/wave2/WO-220202.md`, candidate contract sha256
  `ceec9662834ed61f73fa6cc0a80fa792e2efa66b61ad99a56523b79f01fff602`. The packet and
  allocation are `docs/evidence/wave2-execution-packets/WO-220202.{packet,allocation}.json`.
- **Agent Ready:** the native READY receipt is
  `docs/evidence/wave2-readiness-assessments/WO-220202.2026-09-23T161839.955776Z.assessment.json`.
- **Predecessor:** WO-220201 / U1, merged at `fcb65ff`. Its receipts under
  `docs/evidence/wo-220201-*` and its inventory code are unmodified (`git diff ec9645a`
  is empty for those paths). U2 consumes U1's `InventoryService.read()` snapshot and
  re-verifies its digest.

## Commits (in order)

1. `56f4e0b`: FX-U2 contract pinned before implementation
   (`docs/evidence/wo-220202-fx-u2.md`).
2. `e94c6e8`: implementation. Changed files:
   - `context_assembly/domain/ambiguity.py`
   - `application/ambiguity_service.py`
   - `ports/decision_resolution.py`
   - `adapters/decision_resolution.py`
   - `composition/upstream_profile.py`
   - `tests/context_assembly/test_ambiguity.py`
   - `tools/evidence/fx_u2_evidence.py`
3. `54aa525`: repair of independent review 1.
4. `b89def8`: repair of independent review 2, plus contract Revision 1. This is the
   revision proven below.

The evidence commit that adds this record and `docs/evidence/wo-220202-fx-u2/` is the
published candidate head. The Issue comment records its exact SHA.

## Independent adversarial reviews (fresh read-only subagent sessions; not the BIU verifier)

**Review 1 (of `e94c6e8`):** 2 HIGH, 2 MEDIUM, 3 LOW. Dispositions:

- Stale semantic-review hold dropped: fixed.
- Reopened finding resolvable only by the old decision: fixed with per-cycle inbox
  questions.
- One stale review stalling all inspection: fixed.
- Forged replay returning success: fixed.
- Defer misreported as AUTHORITY_HOLD: fixed.
- Weak AC-04 test: fixed with an import-graph check and a check that execution state
  is unchanged.
- STALE questions stay listed in the DecisionInbox: accepted residual, returned to the
  DecisionInbox owner (needs a withdraw API outside this node).

**Review 2 (of `54aa525`):** confirmed all fixes (the inbox listing remains the accepted
residual). It found 2 MEDIUM defects, which are now fixed:

- Malformed locators persisted and broke inspection.
- A review with no other state change was not persisted.

Its contract-drift note is resolved by contract Revision 1. Its LOW legacy-history crash
is fixed by the shape check on read.

## Commands and results at `b89def8`

| Command | Exit | Result | Retained log |
|---|---|---|---|
| `PYTHONPATH=src python3 tools/evidence/fx_u2_evidence.py --output docs/evidence/wo-220202-fx-u2` | 0 | 15/15 controls discriminated (intact 0, fault nonzero with `FAIL:`, restored 0) | `wo-220202-fx-u2/report.json` sha256 `fe4e17a19549131f335c126f588581d31e17bb86c8741d6d0df6cbbed0e7f03e`, plus per-phase logs and observation objects |
| `PYTHONPATH=src python3 -m unittest tests.context_assembly.test_ambiguity -v` | 0 | 13 tests OK | `regression/unittest-ambiguity.log` (`ce21adb6…b284972`) |
| `PYTHONPATH=src python3 -m unittest tests.context_assembly.test_inventory` (U1 unchanged) | 0 | 15 tests OK | `regression/unittest-inventory-u1.log` (`8309b562…590d23`) |
| `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` | 0 | PASS | `regression/architecture.log` (`395cf0ad…d57ba`) |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 526 passed (baseline 513 + 13 new) | `regression/python-tests.log` (`6c7f87ce…cf6e7`) |
| `node scripts/check.mjs all` | 0 | 340 + 18 + 3 passed | `regression/node.log` (`86dac346…e3c16`) |
| `python3 -m pytest -q tools` | 1 | 464 passed; 1 failed: the known non-hermetic baseline debt `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary` (reads the live `~/.codex/config.toml`; out of scope, unmodified) | `regression/python-tools-known-baseline-debt.log` (`bfec1f8b…b5ea1`) |

The 15 negative controls each have 1 application per fault phase and 0 in the intact
and restored phases:

1. `revision-matching-removed`
2. `authority-matching-removed`
3. `unattributed-answer-accepted`
4. `stale-transition-removed`
5. `resolve-applies-to-every-finding`
6. `missing-intent-rule-disabled`
7. `scope-conflict-rule-disabled`
8. `acceptance-placeholder-accepted`
9. `conflicting-sources-ignored`
10. `semantic-finding-not-holding`
11. `hold-propagates-globally`
12. `worker-launch-injected`
13. `worker-path-composed`
14. `semantic-stale-hold-removed`
15. `reopen-reuses-prior-answer`

Together they cover the design's proven-red obligation `012-local-holds`: revision or
authority matching removed, and a stale or unattributed answer injected.

## Acceptance trace

| Criterion | Test | What it proves |
|---|---|---|
| AC-01 | `test_missing_fields_and_conflicting_sources_open_source_linked_questions` | Each of omitted intent, scope conflict, missing authority, TBD acceptance and conflicting sources opens exactly one question. Each question has a source locator, names the requirement, states a blocked reason, names the required actor, and holds its branch. |
| AC-02 | `test_only_matching_attributed_decision_resolves_that_question`, `test_reopened_finding_requires_a_fresh_answer` | Wrong revision gives REVISION_HOLD. A wrong or unadmitted actor gives AUTHORITY_HOLD. A forged or unrecorded decision gives AUTHORITY_HOLD. Another question's decision gives FINDING_MISMATCH. The exact decision resolves only its own question. Changed input makes prior findings and resolutions STALE, and a fresh question opens. |
| AC-03 | `test_complete_requirement_passes_and_semantic_review_holds_without_editing_intent`, `test_changed_input_keeps_an_unanswered_semantic_review_hold` | A complete requirement is COMPLETE and ELIGIBLE. A recorded semantic review adds a held question, and the requirement's revision, semantic digest and inventory stay unchanged. |
| AC-04 | `test_unrelated_requirement_stays_preparable_and_no_worker_launches`, `test_upstream_composition_has_no_worker_path` | Only the affected requirement and its dependent are HELD, and the independent requirement stays ELIGIBLE. Across the question lifecycle there are zero dispatches, zero pending effects and zero reservations, and the co-located coordinator state is unchanged. The upstream path imports no worker or dispatch module. |

## Measurements and limits

- **Tokens and cost:** UNKNOWN. Invocation billing telemetry is unavailable, and these
  values are not zero.
- **Cycles:** this record is PRODUCER cycle 1 of 3.
- **Proof scope:** proof level is LOCAL_COMPOSED_OR_MECHANICAL on a disposable local
  profile. There was no live operation.
- **Not done here:**
  - No worker was launched.
  - No requirement was rewritten.
  - No DAG was replanned.
  - No sibling node was implemented.
  - RAI remains unwired.
- **Independent verdict:** pending the separate VERIFIER invocation (JC on Codex), which
  must retrieve the exact published SHA.
