# Work unit: the PREPARER and Work Preparation (WORK-PREPARATION-REFILL R3a)

**Label:** `WORK-PREPARATION-REFILL-R3a` (a document label; permanent id `9eedc2c9-085b-4e2d-9190-de133a960fa8`).
**Status:** Revision 1, 2026-10-11. Registered as work item 9eedc2c9-085b-4e2d-9190-de133a960fa8.
**Authority:** plan-derived from obligation WORK-PREPARATION-REFILL of the live canonical plan (tip `821e95d`,
`sha256:3be660b28ca00d450a0baa195161e9dcfe33ed63b2cbd13da9ca712c556f2324`); acceptance WPR-A2. Released by `work release` (inherited release) and run by `work run --wait`; no
`work launch`.
**Starting revision:** main `821e95d`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "9eedc2c9-085b-4e2d-9190-de133a960fa8",
 "version": "revision-1",
 "intent": "WPR-A2: a PREPARER derives the next bounded Work Item for the next eligible obligation from the live plan tip, with provenance, and the control plane refuses any packet outside the obligation's authority before anything is written: `work prepare` (Work Preparation's prepare_next) selects the next eligible obligation from registry-derived obligation state, runs one bounded PREPARER session, checks the packet, commits it to the packets branch, registers and binds it, assesses it with Agent Ready and releases a READY item by inherited release; every other outcome is a typed stop, never the Decision Inbox.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-10 (decisions sections 38-39): the PREPARER proposes executable interpretation; the canonical plan owns intent; deterministic code owns authority; Agent Ready owns readiness judgment; the runner owns execution. The PREPARER may not invent intent, broaden authority, touch protected policy, resolve owner ambiguity, change priority or dependencies, weaken acceptance or release its own work.",
  "Founder 2026-10-11 (decisions sections 49-50): smallest acceptable scope; this child is credited with WPR-A2 only; a real SPLIT and re-issue in the shared budget are WORK-PREPARATION-REFILL R3b (WPR-A3, WPR-A5); here an Agent Ready SPLIT stops as the typed fallback \"cannot safely split yet\".",
  "Founder 2026-10-11 (decisions section 44): \"Infrastructure failure is not an owner decision.\"",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_preparation.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/adapters/work_item_repository.py",
  "src/alienintent/context_assembly/application/work_identity_service.py",
  "src/alienintent/context_assembly/domain/preparation.py",
  "src/alienintent/context_assembly/ports/work_item_repository.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tests/composition/test_work_preparation.py",
  "tests/composition/test_work_registry.py",
  "tests/context_assembly/test_preparation.py",
  "tests/control_plane/test_cli.py"
 ],
 "excluded_scope": [
  "every protected path of the canonical plan authority",
  "src/alienintent/invocation_runtime/",
  "src/alienintent/execution_coordination/",
  "real SPLIT children and re-issue (R3b); refill in the run loop and the READY-supply fault (R4)"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-4 pass",
  "WPR-A2"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "no test id collected at the starting revision is missing at the candidate (acceptance check 3)",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r3a.diff (sha256 f56a045fbaa93cb832b3a5ecc81d0af2c77783586e46da3888b387f25f38be77), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "supplying a PREPARER CLARIFY's missing fact from canonical context",
  "owner-boundary classification of a HOLD into the Decision Inbox"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "automatic-on",
 "authority_issuer": "plan-authority:sha256:3be660b28ca00d450a0baa195161e9dcfe33ed63b2cbd13da9ca712c556f2324",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md obligation:WORK-PREPARATION-REFILL",
  "docs/work-units/python/work-preparation-refill-r3a.diff"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "the `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r3a.diff is absent from the context package, its text's sha256 is not f56a045fbaa93cb832b3a5ecc81d0af2c77783586e46da3888b387f25f38be77, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

```json alienintent-acceptance
{"satisfies": ["WPR-A2"]}
```

## 1. Why

The factory needs the next plan-derived Work Item prepared without the Founder, or Claude acting for the Founder,
writing it (decisions sections 37-41). This child adds the PREPARER and Work Preparation's `prepare_next`.

## 2. The change: exactly the referenced prototype diff at `821e95d`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/work-preparation-refill-r3a.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `f56a045fbaa93cb832b3a5ecc81d0af2c77783586e46da3888b387f25f38be77` (67,126 bytes, 12 files, unified diff, `git apply` format).
- **Baseline:** main `821e95d`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 12 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `f56a045fbaa93cb832b3a5ecc81d0af2c77783586e46da3888b387f25f38be77`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. `context_assembly/domain/preparation.py` (new, pure): `parse_acceptance` (the ```json alienintent-acceptance```
   block) and `check_packet` (contract under the pending identity, exactly the selected obligation, issuer = the live tip,
   automatic-on, `outside_authority` empty, the obligation's own acceptance ids, a proof set).
2. `context_assembly` work item repository/service: `packet_items()` (non-retired packet items).
3. `composition/work_registry.py`: `derived_items`, `mapping_holds`, `obligation_states` (obligation state from the
   registry); `preparation` composed; `composition/work_preparation.py` (new): `WorkPreparation.prepare_next` and
   `WorkerPreparer` (the PREPARER session as the worker user in a fresh clone of canonical main).
4. `control_plane`: `work prepare`.
5. Tests: the pure check; obligation state from registry rows; prepare_next end to end on the fixture with a fake
   PREPARER (released with provenance; refused writes nothing; PREPARER HOLD stops; Agent Ready CLARIFY gets one
   revision of the same item; budget exhausted stops; nothing while an item is live; the next item is a new Work
   Item); the real PREPARER runner with a fake provider; the CLI.

## 3. Acceptance checks

1. The targeted proof set, the block below, passes. It is deliberately small (Founder decision 52: the smallest
   sufficiently complete set; the regression gate owns whole-suite coverage): the two new test files of this diff and
   `tests/context_assembly/test_obligation_state.py`, which already exists at main `821e95d` (landed by R1) and
   exercises the obligation state `prepare_next` relies on. The new tests this diff adds to the large existing files
   `tests/composition/test_work_registry.py` and `tests/control_plane/test_cli.py` run by exact node id: the
   registry ones through the `alienintent-mutations` block below (each mutation names them), the `work prepare` CLI test
   by node id `tests/control_plane/test_cli.py::test_work_prepare_runs_one_preparation_and_renders_its_typed_answer`;
   every other test in those files is run by the regression gate.
2. `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
3. **No test id disappears**: `python3 -m pytest --collect-only -q tests` at the starting revision and at the candidate;
   every id collected at the starting revision is collected at the candidate (collection only; nothing runs).
4. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-proof
{"targeted_tests": ["tests/context_assembly/test_preparation.py", "tests/composition/test_work_preparation.py", "tests/context_assembly/test_obligation_state.py"]}
```

```json alienintent-mutations
[
 {
  "name": "an older plan revision may issue a prepared packet",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "    if contract.authority_issuer != ISSUER_PREFIX + authority.content_digest:\n",
    "new": "    if False:\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[older-issuer]"
  ]
 },
 {
  "name": "a packet may claim another obligation's acceptance ids",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "        elif not set(satisfies) <= own:\n",
    "new": "        elif False:\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[acceptance-id-not-the-obligations]"
  ]
 },
 {
  "name": "a packet may reference another obligation",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "    if obligation_labels(contract) != (label,):\n",
    "new": "    if False:\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[other-obligation]"
  ]
 },
 {
  "name": "a prepared packet may be explicitly released",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "    if contract.release_policy != \"automatic-on\":\n",
    "new": "    if False:\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[explicit-release]"
  ]
 },
 {
  "name": "a packet outside the live authority is not refused",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "    reasons.extend(outside_authority(contract, authority))\n",
    "new": ""
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_a_refused_packet_writes_nothing_and_uses_one_run",
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[scope-outside-the-obligation]"
  ]
 },
 {
  "name": "a packet without a proof set passes",
  "path": "src/alienintent/context_assembly/domain/preparation.py",
  "edits": [
   {
    "old": "            reasons.append(\"proof: the packet declares no targeted proof set\")\n",
    "new": "            pass\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_preparation.py::test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason[no-proof-block]"
  ]
 },
 {
  "name": "a DONE item's acceptance block is ignored",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                satisfies = parse_acceptance(record.packet.decode(\"utf-8\")) or ()\n",
    "new": "                satisfies = ()\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_an_obligation_is_finished_only_by_done_items_naming_its_acceptance_ids"
  ]
 },
 {
  "name": "a satisfied_by commit off canonical main holds",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        return bool(_is_ancestor(self.configuration.repositories[name].clone, entry.landed_commit, main))\n",
    "new": "        return True\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_satisfied_by_mapping_holds_only_for_a_done_item_whose_landed_commit_is_on_canonical_main"
  ]
 },
 {
  "name": "preparation runs while a derived item is live",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "        if live:\n            return PreparationResult(IN_PROGRESS, live[0])\n",
    "new": ""
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_while_a_derived_item_is_live_nothing_is_prepared"
  ]
 },
 {
  "name": "the obligation budget is never exhausted",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "            if record[\"runs\"] >= self.budget:\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_three_refused_packets_exhaust_the_obligation_budget_and_stop_it"
  ]
 },
 {
  "name": "an Agent Ready CLARIFY gets no PREPARER revision",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "                if disposition == \"CLARIFY\" and not revised:",
    "new": "                if False:"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_an_agent_ready_clarify_gets_one_preparer_revision_of_the_same_item"
  ]
 },
 {
  "name": "the obligation's next item re-binds the released one",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "                    record.update(identity=None, path=None, items=[*record.get(\"items\", []), identity])\n",
    "new": "                    record.update(items=[*record.get(\"items\", []), identity])\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_the_next_item_of_an_obligation_is_a_new_work_item_with_its_own_identity"
  ]
 },
 {
  "name": "an item that will not be released stays live",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "            self.registry.identities.retire(identity)\n",
    "new": "            pass\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_a_release_that_fails_stops_the_obligation_and_retires_its_item",
   "tests/composition/test_work_preparation.py::test_an_assessment_hold_stops_the_obligation_and_retires_its_item"
  ]
 },
 {
  "name": "a refused revision is retried instead of stopped",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "                if record.get(\"identity\"):  # a refused revision: the registered item stops with its obligation\n",
    "new": "                if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_a_refused_revision_stops_the_obligation_and_retires_its_item"
  ]
 },
 {
  "name": "a new obligation revision reuses the old item's path",
  "path": "src/alienintent/composition/work_preparation.py",
  "edits": [
   {
    "old": "        tag = f\"{revision_digest.removeprefix('sha256:')[:8]}-{record['runs']}\"\n",
    "new": "        tag = f\"{record['runs']}\"\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_preparation.py::test_a_new_obligation_revision_prepares_a_new_item_never_the_old_one"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `821e95d`. Built test-first; the proof set passes; 0 test ids
missing against main; fitness passes; the 15 mutations each fail their named tests and pass when
restored; one fresh review (decisions section 49).
