# Work unit: the per-role context package for a registered work item

**Label:** `WORK-CONTEXT-PACKAGE` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 3 (work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`, at CAPTURE) for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6c-1. The Founder split unit 6c on 2026-10-03 into two dependency-ordered units: 6c-1 (this unit) assembles each role's context package; 6c-2 launches the PRODUCER and the VERIFIER with it, from the release record's starting revision, with runtime-injected model assignments. Builds on units 6a and 6b (`main` `14ffb44`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "5befff2f-a0dd-4cea-9556-54c33ed86c1b",
 "version": "revision-3",
 "intent": "Assemble, before any launch, each role's per-role context package for one registered work item and the exact attempt from existing authoritative records, with dependencies and design references resolved to their authoritative contents and a read-only `work context` command for further facts through a read-only worker profile; missing or conflicting required facts give a typed hold that prevents launch; record the PRODUCER's self-review in the existing evidence repository, referenced by a create-only record bound to the exact candidate, and carry it to the VERIFIER as labelled input.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-03: use the per-role context package specified in docs/architecture/interface-contracts.md sections 6-7, assembled from existing authoritative records; missing or conflicting required facts prevent launch.",
  "Founder 2026-10-03: the PRODUCER's self-review is stored in the existing evidence repository, bound to the exact candidate commit, never as a file in the product repository; the VERIFIER receives it through its context package.",
  "Founder 2026-10-03: the package includes how to call the deterministic context API for further facts.",
  "Founder 2026-10-03: context assembly (6c-1) and worker launch (6c-2) are separate dependency-ordered units; no new storage or configuration.",
  "Founder 2026-10-03: workers reach the API through a read-only worker profile backed by the same configuration and records; it hides write commands and opens the databases read-only. This protects this API only; it does not stop a shell-enabled worker reaching writable files or credentials elsewhere, and no stronger protection is claimed. Worker launch (6c-2) enforces whatever existing access restrictions provide that.",
  "Path plan row 6 and section 4A (unit 6c, split 2026-10-03) on branch manual/claude-workflow-design-20260930."
 ],
 "authorized_scope": [
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/context_assembly/domain/work_context.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tests/context_assembly/test_work_context.py",
  "tests/composition/test_work_registry.py",
  "tests/control_plane/test_cli.py",
  "src/alienintent/execution_coordination/adapters/sqlite_store.py",
  "src/alienintent/context_assembly/adapters/work_item_repository.py",
  "tests/execution_coordination/test_operational_store.py",
  "tests/context_assembly/test_work_identity_service.py"
 ],
 "excluded_scope": [
  "launching workers or delivering the package",
  "starting the PRODUCER from the starting revision",
  "capturing the self-review from the PRODUCER process",
  "model assignment",
  "changing the context reconstruction service, the release gate, WIP admission or the coordinator",
  "a new store or configuration",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "git",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-9 pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "landing record on main"
 ],
 "non_goals": [
  "worker launch",
  "model routing"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/architecture/interface-contracts.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "a required fact has no existing authoritative record",
  "scope outside the authorized files"
 ]
}
```

## 0. The whole design (plain English)

A PRODUCER or VERIFIER must not reconstruct the project by searching. Before either is launched for an attempt, this unit assembles its **context package**: one document, built only from existing authoritative records, holding everything that role needs for that work item and that attempt — with dependencies and design references resolved to their authoritative contents — and the command it can run for any further fact. The package is the one specified in `docs/architecture/interface-contracts.md` §6 (context isolation: the VERIFIER gets the work item, the exact candidate, its diff and the proof requirements, never the PRODUCER's transcript) and §7 (every worker context states `goal`, `allowed_scope`, `required_evidence`, `stop_condition` and `escalation_condition`). A missing or conflicting required fact produces a typed hold naming it; no package is produced, so nothing can be launched. The PRODUCER's self-review is kept in the existing evidence repository and reaches the VERIFIER as clearly labelled input to check. This unit launches nothing; unit 6c-2 does.

## 1. Assembly, bound to the exact attempt

`WorkContext.assemble(identity, role, correlation, contract_digest, candidate=None) -> ContextPackage | ContextHold` (`context_assembly/application/work_context.py`), for role PRODUCER or VERIFIER, takes the invocation's own values as unit 6c-2 will have them just before the worker starts (`correlation` = `launch:<identity>:<version>`, the invocation's `contract_digest`, and for the VERIFIER its `CandidateRef`). A first PRODUCER launch with no coordinator state yet is attempt 1, not a hold. Every field comes from the named existing record; nothing is inferred.

| Field | Source |
| --- | --- |
| `identity`, `label`, `role`, `attempt` | the `work_item` row; the role; the correlation `launch:<identity>:<version>`, whose version is the store version `read_state` returns for `factory:<identity>` (0 with no state yet) |
| `goal` | the contract's `intent` |
| `instructions` | the packet bytes at the row's pointer commit (`WorkRecordService.show`), with repository, path and commit |
| `contract` | the packet's contract block (`work_contract.contract_block`), with its `content_digest` |
| `assessment` | the row's `assessment_ref` and its READY attempt (attempt id, fingerprint of the current pointer) |
| `release_record` | `release_authorization(identity)` on the registry store, and its evidence read through the row's `approval_ref` (pointer, attempt id, assessment ref, contract digest, baseline, approver, quote) |
| `starting_revision` | the release record's `baseline` |
| `allowed_scope` | the contract's `authorized_scope` and `excluded_scope` |
| `required_evidence` | the contract's `verification_obligations`, `required_evidence`, `completion_criteria` |
| `stop_condition` | the contract's `completion_criteria` and its `budget_policy.maximum_attempts` |
| `escalation_condition` | the contract's `stop_escalation_conditions` |
| `dependencies` | each dependency identity resolved to its row (label, state, pointer), its packet bytes at its pointer commit, and its `factory:<dependency>` stage and outcome on the registry store |
| `design_rules` | the contract's `fixed_decisions` as given; each `authority_references` entry whose first token is a repository path, resolved to its bytes from `git show <pointer commit>:<path>` in the pointer's repository, with path and commit |
| `history` | from the raw coordinator state `factory:<identity>`: stage, version, `implement_cycles`, `verify_cycles` (via `FactoryCoordinator.decode`), and `rejections` and `findings` read from the raw record |
| `resources` | the WIP reservation (scope `wip`, key `<identity>`, owner `work:<identity>`) and the repository reservation (scope `repository`, owner `<correlation>`), with owner and fence, from `recovery_reservations`; and `cleanup` = the contract's `required_closure_actions` and `candidate_custody_requirements` |
| `context_command` | the exact read-only command for further facts (section 3) |

**The VERIFIER's package** has exactly: `identity`, `label`, `role`, `attempt`, `goal`, `instructions`, `contract`, `release_record`, `starting_revision`, `allowed_scope`, `required_evidence`, `stop_condition`, `escalation_condition`, `dependencies`, `design_rules`, `history`, `resources`, `context_command`; `candidate` (the exact `CandidateRef`, which must equal the coordinator state's candidate); `diff` (`git diff <starting_revision> <candidate revision>`, run in the VERIFIER's fresh candidate clone, the revision read from the candidate's source-revision locator `git:<remote>#<branch>@<revision>`; any other candidate kind is a `MISSING_RECORD` hold); and `producer_self_review` with the fixed label `"input to check — not findings and not a verdict"` (section 4). It never contains the PRODUCER's transcript, invocation output or journal entries, and the self-review is never placed into `findings`.

## 2. Holds: missing or conflicting facts prevent launch

`assemble` runs its checks in a fixed order and returns the **first** failing one as a `ContextHold` (`context_assembly/domain/reconstruction.py`, existing `HoldReason` values), naming the field in `affected_refs` and the rule in `detail`:
1. row: missing, retired or no pointer; packet bytes unreadable at the pointer → `MISSING_RECORD`;
2. contract block invalid or its identity not the work item's → `MALFORMED_RECORD` (detail = which);
3. no READY assessment of the current pointer → `MISSING_RECORD`;
4. no release record, or no evidence at `approval_ref` → `MISSING_RECORD`; the evidence's `revision_digest` ≠ the release record's `record_ref`, or its pointer commit, attempt id or contract digest ≠ the row's pointer commit, the row's assessment attempt or the contract's digest → `DIGEST_MISMATCH`;
5. the invocation's `contract_digest` ≠ the contract's → `DIGEST_MISMATCH`; the correlation's version ≠ the store version that `read_state` returns for `factory:<identity>` (0 when the work item has no state yet) → `VERSION_DRIFT`; undecodable state → `MALFORMED_RECORD`;
6. missing WIP or repository reservation → `MISSING_RECORD`;
7. an unregistered dependency, or an `authority_references` entry that is not a path present at the pointer commit (a vault document, prose, a branch-only file) → `MISSING_RECORD` naming it;
8. for the VERIFIER: no candidate in the state, a `--candidate` locator that differs from the locator of the candidate in the coordinator state → `DIGEST_MISMATCH`; no self-review record for that candidate → `MISSING_RECORD`;
9. any evidence read failing → `EVIDENCE_UNAVAILABLE`; any store read failing → `STORE_UNAVAILABLE`.

Authoring rule that follows from 7: `authority_references` hold repository paths at the packet's commit; a decision without such a record is written into `fixed_decisions` as text.

## 3. The context command and the read-only worker profile

One read-only CLI subcommand, `work context <id or label> --role PRODUCER|VERIFIER --correlation <launch:…> [--candidate <locator>]`, prints `assemble`'s package or hold as JSON. Workers reach it through a **read-only worker profile**, a profile factory in `composition/work_registry.py` backed by the same project configuration and records: it builds only the readers `work context` needs — not `WorkRegistry`, whose constructor initializes the readiness store and resolves the Agent Ready executable — and opens the work and readiness databases read-only through a new read-only open on the two existing adapters: `SQLiteOperationalStore` and `SQLiteWorkItemRepository` each gain a read-only mode that opens the file with SQLite `mode=ro` and skips schema creation, migration and index statements (today both always open writable and create or migrate). It does not use the `github` entry (the shared configuration file still names the App key) and has no Agent Ready connection. It exposes only `work context`; every writing command (`work register`, `work assess`, `work authorize`, `work link`, `work display`, `work migrate`) answers the stated error `{"error": "not-available-in-worker-profile"}` instead of running. The package's `context_command` states the full command line: the absolute path of the installed `alienintent` executable, `--profile-factory` naming the read-only worker profile, and the two environment variables `ALIENINTENT_PROJECT_CONFIGURATION` and `ALIENINTENT_PROJECT` with their values; unit 6c-2 adds exactly those to the worker's environment. `explain` and the context reconstruction runner are not offered: neither serves a single registry work item.

**Limit (stated, not exceeded):** the read-only profile protects this API. It does not stop a shell-enabled worker from reaching writable files or credentials elsewhere on the machine; no stronger protection is claimed here. Worker launch (6c-2) must enforce whatever existing access restrictions provide that.

## 4. The PRODUCER's self-review

`WorkContext.record_self_review(identity, candidate: CandidateRef, text) -> Ref`: the self-review's **contents** go to the existing evidence repository (the registry's readiness evidence folder) as one record of kind `self-review`, content `{identity, candidate locator, candidate digest, text}`, built with fixed fields only the way the READY view builds its fixed records. Then a **create-only** record on the existing registry store, aggregate `self-review:<identity>:<candidate digest>`, written with expected version 0 (the store's existing check, as the release record is), holds only the evidence `Ref` and the exact `CandidateRef`. The same text for the same candidate returns the existing reference; different text is `SELF_REVIEW_EXISTS` (the store's `VersionConflict`). The VERIFIER's package finds it by that aggregate name and reads the contents from the evidence repository. Nothing is written to the product repository. Unit 6c-2's launch path calls `record_self_review` after the PRODUCER publishes its candidate.

## 5. No retention on assembly

Assembly is read-only: it writes nothing. Unit 6c-2 keeps the evidence reference of the package it actually delivers.

## 6. Exact permitted files

Production: `src/alienintent/context_assembly/application/work_context.py` (new), `src/alienintent/context_assembly/domain/work_context.py` (new: package and field values, check order, labels), `src/alienintent/composition/work_registry.py` (`WorkRegistry.context`, the read-only worker profile factory), `src/alienintent/control_plane/adapters/cli.py` and `src/alienintent/control_plane/application/operator.py` (`work context`, the stated error), `src/alienintent/execution_coordination/adapters/sqlite_store.py` and `src/alienintent/context_assembly/adapters/work_item_repository.py` (the read-only open only; their existing writable behaviour unchanged). Tests: `tests/context_assembly/test_work_context.py` (new), `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`, `tests/execution_coordination/test_operational_store.py`, `tests/context_assembly/test_work_identity_service.py`.

## 7. Acceptance checks (each names the wrong implementation it catches)

1. **What each role receives.** For an authorized, admitted work item, the PRODUCER package holds exactly the section 1 fields with values equal to their source records, instructions byte-equal to `git show <pointer>`; the VERIFIER package holds exactly its listed fields; with a marker string planted in the PRODUCER's journal entry and invocation output, the marker appears nowhere in the VERIFIER's package. Catches a partial package and leaked PRODUCER output.
2. **Missing facts prevent launch.** Each missing fact of section 2, one at a time, gives a `ContextHold` with the stated reason and field, and no package. Catches assembly from partial facts.
3. **Conflicting facts prevent launch.** Each mismatch of section 2 steps 4, 5 and 8 gives `DIGEST_MISMATCH` (or `VERSION_DRIFT`) naming the field. Catches stale or mismatched authorization.
4. **Exact attempt.** A first PRODUCER with no state gets a package for attempt 1; a stale correlation gives `VERSION_DRIFT`; a missing reservation gives `MISSING_RECORD`. Catches a package for the wrong attempt and a hold on every first launch.
5. **Resolution.** A registered dependency arrives with its packet bytes and stage; a reference path at the pointer commit arrives with its bytes and commit; an unregistered dependency or an unresolvable reference gives `MISSING_RECORD`. Catches raw references that make a worker search.
6. **Self-review.** Recording stores the contents in the evidence repository and a create-only store record holding its `Ref` and the exact `CandidateRef`; the same text returns the reference; different text is `SELF_REVIEW_EXISTS`; a package for another candidate does not find it; in the VERIFIER package it carries the fixed label and is not in `findings`. Catches unbound, replaceable or mislabelled self-reviews.
7. **The command works in the worker's environment.** With only the stated worker environment (no inherited `ALIENINTENT_*` or `PYTHONPATH`) plus the two variables, the package's `context_command`, run from a worktree, prints the same package for the same work item and attempt; through the read-only worker profile, `work assess`, `work authorize`, `work link`, `work register`, `work display` and `work migrate` answer `not-available-in-worker-profile`; a read-only open writes nothing (file bytes unchanged) and any write through it fails. Catches a command that only works in the operator's shell and a profile that can write.
8. **Deterministic and read-only.** Assembling twice with unchanged records gives byte-identical packages; no record, reservation, evidence or state changes. Catches non-deterministic or mutating assembly.
9. **Fitness.** The test files above and `check_architecture.py --check all` pass.

## 8. Excluded

Launching workers, delivering the package into a workspace, starting the PRODUCER from the starting revision, capturing the self-review from the PRODUCER process, model assignment, and enforcing filesystem or credential restrictions on the worker (all unit 6c-2); changing the context reconstruction service, the release gate, WIP admission or the coordinator; a new store or configuration; changing earlier packets.

## 9. Review record

**Revision 3 (2026-10-03).** The REVIEWER's recheck of `4108889`: the read-only open is added to `SQLiteOperationalStore` and `SQLiteWorkItemRepository` (nothing on main opened them read-only) and the worker profile builds only the readers it needs; the attempt version is the store version from `read_state`, 0 without state; the diff is taken in the VERIFIER's candidate clone; `stop_condition` is completion criteria plus maximum attempts; the candidate is compared by locator; writing commands answer a stated error; the profile does not use the `github` entry.

**Revision 2 (2026-10-03).** The REVIEWER's review of `83509db` (FAIL) and the Founder's decisions: `work context` through a read-only worker profile replaces `explain` and the reconstruction runner, with its stated limit; the command must work in the worker's environment; assembly is bound to the exact attempt; dependencies and design references resolve to their authoritative contents; the VERIFIER's fields are listed, with the diff and the labelled self-review; the self-review's contents are in the evidence repository and a create-only store record references them and the exact candidate; holds return the first failing check; nothing is retained on assembly; §7 field names.

**Revision 1 (2026-10-03).** First draft, against `main` `14ffb44`, with the Founder's decisions: the per-role context package from the design, assembled from authoritative records; missing or conflicting facts prevent launch; the PRODUCER's self-review stored in the existing evidence repository bound to the exact candidate commit and carried in the VERIFIER's package; the package states how to call the deterministic context API; context assembly and worker launch split into 6c-1 and 6c-2.
