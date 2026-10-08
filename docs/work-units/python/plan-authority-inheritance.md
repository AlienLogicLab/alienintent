# Work unit: derived work inherits execution authority from an approved plan revision

**Label:** `PLAN-AUTHORITY-INHERITANCE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-08, for independent review. Not registered, not approved, not assessed, not released.
**Position on the path:** the second item of the autonomy path (Founder 2026-10-08): NO-CHANGE → **plan-authority
inheritance** → automatic assessment and runner over the existing `FactoryCoordinator.start()` loop →
BOUNDED-ROUTINE-LAUNCH → board projection → Work Preparation / READY refill → three-item autonomy proof.
This is the last item released under the old rules (bootstrap release 2 of 2). After it lands, no Founder click,
card move or per-item approval words are needed for plan-derived work.
**Starting revision:** main `1837fd4`. Every line number below is at `1837fd4`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "The Founder approves an exact revision of the canonical plan once. A Work Item derived from that revision, assessed READY, satisfiable, and inside the plan's recorded authority scope is released by the control plane with no Founder words and no manual board change: the control plane writes its release record and sets its card to READY with the plan's priority. Anything outside that scope stops with a typed owner-decision requirement. Work not derived from an approved plan keeps the explicit Founder release. The canonical plan's section 2.2 states this rule.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-08: Founder approval attaches to an exact canonical-plan revision, not routinely to each derived Work Item. A derived item inherits execution authority only when it is traceably derived from that approved plan revision, Agent Ready returns READY, satisfiability passes, dependencies and priority are deterministic, and it introduces no new owner decision (no new spend, credential or authority grant, irreversible external effect, architecture or policy supersession, or genuine product ambiguity). Otherwise it stops with a typed owner-decision requirement.",
  "Founder 2026-10-08: this replaces routine explicit-human-off for plan-derived work. Ad hoc work not derived from approved plan authority can still require explicit Founder approval.",
  "Founder 2026-10-08: docs/decisions/alienintent-v2-canonical-project-plan.md is the human-readable authority root, but authority binds to an exact approved revision and digest, never to the mutable path. The authority record names the plan identity, the exact Git commit and content digest, the Founder approval record, the scope of inherited authority, and the explicit exclusions that need fresh Founder authority. If the plan changes, the old approval does not authorize new content.",
  "Founder 2026-10-08: the board is a projection, never a release button. Until the board-projection item lands, the control plane writes the card's READY and priority itself when it releases an item.",
  "Founder 2026-10-08: canonical plan section 2.2's sentence 'After the Founder approves a queue item, ordinary advancement needs no additional prompt or repeated approval.' becomes 'After the Founder approves canonical product intent/plan authority, derived Work Items advance without additional Founder approval unless they cross a new owner-decision boundary.'",
  "Founder 2026-10-08: this item is bootstrap release 2 of 2; the exception expires when it lands."
 ],
 "authorized_scope": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "src/alienintent/execution_coordination/domain/plan_authority.py",
  "src/alienintent/execution_coordination/domain/satisfiability.py",
  "src/alienintent/context_assembly/application/plan_approval.py",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
  "tests/execution_coordination/domain/test_plan_authority.py",
  "tests/execution_coordination/domain/test_satisfiability.py",
  "tests/context_assembly/test_plan_approval.py",
  "tests/context_assembly/test_inherited_release.py",
  "tests/composition/test_work_registry.py",
  "tests/control_plane/test_cli.py",
  "tests/execution_coordination/test_github_projects_v2.py"
 ],
 "excluded_scope": [
  "execution_coordination/domain/release.py: admit_release and admit_release_preconditions stay byte-identical; inherited releases use the existing automatic-on / AUTOMATIC_POLICY path and the existing durable release record",
  "the release precondition gate, the regression gate and the Landing Authority",
  "execution_coordination/application/factory_coordinator.py",
  "the explicit-human-off path: work authorize --quote keeps working unchanged for work that is not plan-derived",
  "reading READY from work records instead of the card (the board-projection item)",
  "a runner or service that calls work assess, work release or FactoryCoordinator.start() (the runner item)",
  "Work Preparation that derives new Work Items from the plan"
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
  "acceptance checks 1-9 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1-M4 of check 8 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "deriving Work Items from the plan automatically",
  "changing which items exist or their order on the critical path"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md"
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
  "a named function or line does not exist at the starting revision",
  "the change would need a change to release.py, the release precondition gate or factory_coordinator.py",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The registry path puts the Founder inside the routine loop at three points (code at `1837fd4`):

- `satisfiability.py` lines 23-24 refuse any registry contract whose `release_policy` is not `explicit-human-off`, and
  the registry builds its coordinator and rows with `automatic_release=False` (`work_registry.py` lines 516 and 542).
  So no registry item can use the existing policy release (`automatic-on` with `ReleaseSource.AUTOMATIC_POLICY`,
  `release.py` lines 58-69; `factory_coordinator.py` lines 347, 360 and 803-804).
- Every PRODUCER needs a durable release record (`release.py` lines 151-171, check `implementation-authorized`). The
  only way to write one is `work authorize --quote` with the Founder's words (`cli.py` lines 109-111,
  `work_authorization.py` lines 83-140).
- An item is eligible only when its board card's Status reads READY, with priority from the card
  (`work_registry.py` lines 817-830 and 857). Only a person sets those.

The Founder-Out-of-Loop Autonomy Requirement (2026-10-06) and canonical plan section 2.2 (2026-09-30) already rejected
this. Nothing in the code knows about a plan approval or inherited authority.

## 2. The change

1. **The plan carries its authority scope.** The canonical plan gains a section `2.3 Plan authority` with:
   - the new section 2.2 sentence (fixed decision 5), replacing the old one;
   - one machine-readable block, fenced as ` ```json alienintent-plan-authority `, with exactly these keys:
     ```json
     {"target_repositories": ["AlienLogicLab/alienintent"],
      "capabilities": ["python", "filesystem", "process-control"],
      "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1},
      "priority": "P0",
      "excluded_paths": ["docs/decisions/", "docs/architecture/", ".github/", "src/alienintent/execution_coordination/domain/release.py",
                         "src/alienintent/execution_coordination/domain/plan_authority.py",
                         "src/alienintent/execution_coordination/domain/satisfiability.py"]}
     ```
   The block is part of the plan text, so the plan's content digest covers the scope.
2. **The pure domain rule** (`execution_coordination/domain/plan_authority.py`, new):
   - `PlanAuthority` (frozen dataclass): `plan_path`, `commit`, `content_digest` (`sha256:` of the plan file's bytes at
     `commit`), `record_ref` (the evidence reference of the approval), `approver`, `quote`, and the scope keys of 2.1.
   - `ISSUER_PREFIX = "plan-authority:"`. A plan-derived contract has `release_policy` `automatic-on` and
     `authority_issuer` `plan-authority:<content_digest>`.
   - `outside_authority(contract, authority) -> tuple[str, ...]`: one reason per failing rule, each starting with
     `owner-decision-required:`, in this order: issuer does not name this authority's `content_digest`;
     `target_repositories` not within scope; `required_capabilities` not within scope; any `budget_policy` limit above
     its cap or absent; any `authorized_scope` entry equal to, or starting with, an `excluded_paths` entry. An empty
     tuple means the contract inherits.
3. **Satisfiability accepts inherited release** (`satisfiability.py` lines 23-24). `unsatisfiable` gains a keyword
   argument `plan_authority: Callable[[BiuContract], tuple[str, ...]] | None`. The release-policy rule becomes:
   `explicit-human-off` passes as today; `automatic-on` passes only when `plan_authority` is given and returns no
   reasons, and otherwise adds those reasons (or `release_policy: automatic-on requires an approved plan authority`
   when it is `None`); any other value fails as today. Every other rule is unchanged.
   `WorkRegistry._satisfiable` (`work_registry.py` lines 924-949) passes `plan_authority` bound to the current
   approved authority (2.4), or `None` when there is none.
4. **One Founder approval of one plan revision** (`context_assembly/application/plan_approval.py`, new; command
   `work approve-plan --commit <sha> --quote <words>`):
   - Reads `docs/decisions/alienintent-v2-canonical-project-plan.md` at `<sha>` from the packets repository's clone,
     which must be on the default branch's history. Parses exactly one `alienintent-plan-authority` block; refuses
     `PLAN_SCOPE_INVALID` on a missing, duplicate or malformed block or wrong keys.
   - Writes an evidence record (as `WorkAuthorization` does, `work_authorization.py` lines 111-140) holding the plan
     path, commit, content digest, scope, approver `Founder` and the quote, and a create-only store aggregate
     `plan-authority:<content_digest>` with its reference. Repeating the same command is a repeat, not a new record.
   - The current approved authority is the most recently recorded one. An approval of a new plan revision does not
     change what an item issued under an older digest may do: such an item no longer matches the issuer rule of 2.2
     and stops as owner-decision-required.
5. **The control plane releases inherited work** (`context_assembly/application/inherited_release.py`, new; command
   `work release <id>`). No quote. In this order, refusing with the named answer and writing nothing on refusal:
   - the item exists, is not retired, is at CAPTURE, has a pointer and no release record (`NOT_RELEASABLE`);
   - its retained assessment of the current pointer is READY (`ASSESSMENT_MISSING`);
   - its contract has `release_policy` `automatic-on` (`NOT_PLAN_DERIVED`: the explicit `work authorize` path applies);
   - `unsatisfiable(...)` with the current plan authority gives no reasons (`OWNER_DECISION_REQUIRED`, detail the
     reasons joined with `; `);
   - then it writes the release record through the same evidence and `ReleaseRecords.record` path as
     `WorkAuthorization.authorize`, with `baseline` the default branch's current head and `text`
     `inherited from plan authority <content_digest> (<record_ref revision digest>)`. The release precondition gate
     (`release.py` lines 151-171) is unchanged and checks this record exactly as it checks a Founder's.
   - then it links the item if it has no card (the existing `work link` service), writes the card text (the existing
     `work display` service), writes Status `READY` and Priority (the plan's `priority`) on the card, and reads both
     back. `github_projects_v2.py` gains `write_priority(item_id, priority, expected_revision)`, written like
     `write_status` (lines 126-146) on the Priority field.
6. **Registry rows follow the contract** (`work_registry.py` lines 516, 542 and the row built by `_ready_row`, lines
   832-859). The coordinator is built with `automatic_release=True`. Each `ReadyWorkItem` has
   `automatic_release = contract.release_policy == "automatic-on"`. So an `explicit-human-off` item still needs its
   explicit release, exactly as today (`factory_coordinator.py` lines 347 and 797-801), and an inherited item is
   admitted through `AUTOMATIC_POLICY`. `factory_coordinator.py` is not changed.
7. **Commands** (`cli.py`, `operator.py`): `work approve-plan` and `work release` are added next to `work authorize`,
   with the same `--json` answers and argument errors. Both are refused by the read-only worker profile, like the
   other writing commands.

## 3. Acceptance checks

1. **The rule** (`tests/execution_coordination/domain/test_plan_authority.py`): `outside_authority` returns no reasons
   for a contract inside a sample scope, and exactly one `owner-decision-required:` reason for each single change: a
   wrong issuer digest, another repository, a capability outside scope, a budget above its cap, an absent budget
   limit, an `authorized_scope` entry under an excluded path, and one equal to an excluded path.
2. **Satisfiability** (`tests/execution_coordination/domain/test_satisfiability.py`): `explicit-human-off` contracts
   give the same reasons as before for every existing case; `automatic-on` with no authority gives
   `release_policy: automatic-on requires an approved plan authority`; with an authority it gives exactly the
   authority's reasons. The existing tests pass unchanged.
3. **Plan approval** (`tests/context_assembly/test_plan_approval.py`): with a fixture plan committed at a commit, the
   command records the exact commit, the `sha256:` of the file bytes and the parsed scope; a repeat answers repeated;
   a missing, duplicate or malformed block answers `PLAN_SCOPE_INVALID` and writes nothing; an empty quote is refused.
4. **Inherited release** (`tests/context_assembly/test_inherited_release.py`), with a fixture board:
   - a plan-derived item assessed READY gets a release record whose `text` names the plan digest, and its card reads
     back Status READY and Priority P0, with no quote anywhere;
   - each refusal of 2.5 answers its named code and writes nothing (no release record, no card change);
   - an item issued under an older plan digest, after a new revision is approved, answers `OWNER_DECISION_REQUIRED`.
5. **The explicit path is unchanged** (`tests/context_assembly/test_work_authorization.py` and
   `tests/control_plane/test_cli.py`): every existing `work authorize` test passes unchanged, and `work release` on an
   `explicit-human-off` item answers `NOT_PLAN_DERIVED`.
6. **End to end through the coordinator** (`tests/composition/test_work_registry.py`): with the fixture worker, a
   plan-derived item goes `work assess` → `work release` → `work launch` to its PRODUCER with no `work authorize`
   call and no test writing a card Status; an `explicit-human-off` item without a release still stops at
   `release-precondition:implementation-authorized`, exactly as today.
7. **The canonical plan** at the candidate contains the new section 2.2 sentence exactly as fixed decision 5, no longer
   contains the old one, and holds exactly one `alienintent-plan-authority` block that parses to the keys of 2.1.
8. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each):
   - **M1:** in `outside_authority`, drop the excluded-path rule. The check-1 excluded-path cases must fail.
   - **M2:** in `unsatisfiable`, let `automatic-on` pass when `plan_authority` is `None`. The check-2 no-authority case
     must fail.
   - **M3:** in `work release`, skip the READY assessment check. The check-4 refusal case for a non-READY item must
     fail.
   - **M4:** in `work_registry.py`, set every row's `automatic_release` to `True`. The check-6 `explicit-human-off`
     case must fail.
   Revert each, and its tests must pass.
9. **The suite stays green:** the regression gate's own run at the candidate (as the worker) has no failed and no
   error test case, `tools/fitness/check_architecture.py --root src/alienintent --check all` passes, and
   `git diff --name-only <starting revision> <candidate>` lists only files in authorized_scope. `release.py`,
   `release_admission.py`, `regression_gate.py` and `factory_coordinator.py` are byte-identical.

## 4. Review record

**Revision 1 (2026-10-08).** First draft, from the Founder's decisions of 2026-10-08
(`manual/path-to-done/founder-decisions-2026-10-08-autonomy.md`) and a code map of the Founder's gates at `a632147`.
