# Work unit: derived work inherits execution authority from an approved plan revision

**Label:** `PLAN-AUTHORITY-INHERITANCE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 2, 2026-10-08, for independent review. Not registered, not approved, not assessed, not released.
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
 "version": "revision-2",
 "intent": "The Founder approves an exact revision of the canonical plan once. The plan names its obligations, each with the paths it may change. A Work Item that names one of those obligations, stays inside its paths and the plan's limits, is assessed READY and is satisfiable is released by the control plane with no Founder words and no manual board change: the control plane writes its release record and sets its card to READY with the plan's priority. Anything outside that scope stops with a typed owner-decision requirement. Work not derived from an approved plan keeps the explicit Founder release. The canonical plan's section 2.2 states this rule.",
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
  "context_assembly/application/work_authorization.py (inherited release copies its evidence fields; nothing is refactored)",
  "execution_coordination/adapters/github_work_management.py (the release flag is set by a wrapper in work_registry.py)",
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
  `work_authorization.py` lines 83-156).
- An item is eligible only when its board card's Status reads READY, with priority from the card
  (`work_registry.py` lines 817-830 and 857). Only a person sets those.

The Founder-Out-of-Loop Autonomy Requirement (2026-10-06) and canonical plan section 2.2 (2026-09-30) already rejected
this. Nothing in the code knows about a plan approval or inherited authority.

## 2. The change

1. **The plan names its obligations and its limits.** In the canonical plan, the sentence of fixed decision 5
   replaces the old one in section 2.2, and a new section `2.2.1 Plan authority` follows section 2.2 (no other
   section is renumbered; `2.3 One work identity…` at line 63 stays). Section 2.2.1 explains the rule in prose and
   holds exactly one block fenced as ` ```json alienintent-plan-authority `, with exactly these keys and values:
   ```json
   {"target_repositories": ["AlienLogicLab/alienintent"],
    "capabilities": ["python", "filesystem", "process-control"],
    "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
                    "retry_limit": 1, "concurrency_limit": 1,
                    "hard_required_dimensions": ["wall-clock", "attempts", "retries", "concurrency", "cancellation"]},
    "protected_paths": ["docs/decisions/", "docs/architecture/", ".github/", ".claude/", "AGENTS.md", "CLAUDE.md",
                        "tools/fitness/",
                        "src/alienintent/execution_coordination/domain/release.py",
                        "src/alienintent/execution_coordination/domain/satisfiability.py",
                        "src/alienintent/execution_coordination/domain/plan_authority.py",
                        "src/alienintent/execution_coordination/application/release_admission.py",
                        "src/alienintent/execution_coordination/adapters/release_admission.py",
                        "src/alienintent/context_assembly/application/work_authorization.py",
                        "src/alienintent/context_assembly/application/plan_approval.py",
                        "src/alienintent/context_assembly/application/inherited_release.py",
                        "src/alienintent/invocation_runtime/application/regression_gate.py",
                        "src/alienintent/composition/landing_authority.py",
                        "tests/execution_coordination/domain/test_plan_authority.py",
                        "tests/execution_coordination/domain/test_satisfiability.py",
                        "tests/context_assembly/test_plan_approval.py",
                        "tests/context_assembly/test_inherited_release.py",
                        "tests/context_assembly/test_work_authorization.py"],
    "obligations": [
     {"label": "AUTOMATIC-RUNNER", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
      "allowed_paths": ["src/alienintent/composition/", "src/alienintent/control_plane/", "config/", "scripts/",
                        "tests/composition/", "tests/control_plane/"]},
     {"label": "BOUNDED-ROUTINE-LAUNCH", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
      "allowed_paths": ["src/alienintent/invocation_runtime/", "src/alienintent/execution_coordination/",
                        "src/alienintent/composition/", "tests/invocation_runtime/", "tests/execution_coordination/",
                        "tests/composition/"]},
     {"label": "BOARD-PROJECTION", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
      "allowed_paths": ["src/alienintent/composition/", "src/alienintent/execution_coordination/adapters/",
                        "tests/composition/", "tests/execution_coordination/"]},
     {"label": "WORK-PREPARATION-REFILL", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
      "allowed_paths": ["src/alienintent/context_assembly/", "src/alienintent/composition/",
                        "src/alienintent/control_plane/", "tests/context_assembly/", "tests/composition/",
                        "tests/control_plane/"]},
     {"label": "AUTONOMY-PROOF", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
      "allowed_paths": ["docs/evidence/", "tests/", "tools/"]}]}
   ```
   The block is part of the plan's bytes, so the approved content digest covers the obligations, their paths and
   every limit. A protected path is never inheritable, even inside an obligation's paths.
2. **The pure domain rule** (`execution_coordination/domain/plan_authority.py`, new):
   - `PlanScope` (frozen) holds the parsed block; `parse_scope(text: str) -> PlanScope` raises `PlanScopeInvalid`
     unless the plan holds exactly one block with exactly the keys of 2.1 and well-formed values.
   - `PlanAuthority` (frozen): `plan_path`, `commit`, `content_digest` (`sha256:` of the plan file's bytes at `commit`),
     `record_ref` (the approval's evidence reference), `approver`, `quote`, `scope: PlanScope`.
   - `ISSUER_PREFIX = "plan-authority:"`. A plan-derived contract has `release_policy` `automatic-on`,
     `authority_issuer` `plan-authority:<content_digest>`, and exactly one `authority_references` entry of the form
     `docs/decisions/alienintent-v2-canonical-project-plan.md obligation:<LABEL>` (the first word is a path that
     satisfiability already checks at the pointer; the second names the obligation).
   - Paths are compared normalized: each `authorized_scope` entry must be relative and POSIX, with no `..` or `.`
     part, no leading `/`, no `\`, and no `*`, `?` or `[`; comparison is case-folded with any trailing `/` removed.
     `A` is under `B` when they are equal or `A` starts with `B` + `/`.
   - `outside_authority(contract, authority) -> tuple[str, ...]`: one reason per failing rule, each starting with
     `owner-decision-required:`, in this order: the issuer does not name `authority.content_digest`; there is not
     exactly one obligation reference, or its label is not in `scope.obligations`; `target_repositories` not within
     scope; `required_capabilities` not within scope; `satisfied_requirement_ids` not within the obligation's; a
     `budget_policy` field above its cap, `hard_wall_clock_seconds` or `cancellation_limit` absent, or a
     `hard_required_dimensions` entry outside the cap list; an `authorized_scope` entry malformed, or not under any
     of the obligation's `allowed_paths`; an `authorized_scope` entry and a `protected_paths` entry where either is
     under the other. An empty tuple means the contract inherits, and its priority is the obligation's `priority`.
   - "Derived from the plan" therefore means: it names an obligation the Founder approved in these exact bytes and
     stays inside it. Work outside every obligation is ad hoc and keeps the explicit Founder release.
3. **Satisfiability accepts inherited release** (`satisfiability.py` lines 23-24). `unsatisfiable` gains a keyword
   argument `plan_authority: Callable[[BiuContract], tuple[str, ...]] | None = None`. The release-policy rule becomes:
   `explicit-human-off` passes as today; `automatic-on` passes only when `plan_authority` is given and returns no
   reasons, otherwise it adds those reasons, or `release_policy: automatic-on requires an approved plan authority`
   when `plan_authority` is `None`; any other value fails as today. Every other rule is unchanged.
   `WorkRegistry._satisfiable` (`work_registry.py` lines 924-949) passes
   `plan_authority=lambda contract: outside_authority(contract, current)` when a current authority exists (2.4), and
   `None` otherwise.
4. **One Founder approval of one plan revision** (`context_assembly/application/plan_approval.py`, new; command
   `work approve-plan --commit <sha> --quote <words>`):
   - Reads `docs/decisions/alienintent-v2-canonical-project-plan.md` at `<sha>` from the packets repository's clone,
     refusing `PLAN_NOT_ON_MAIN` unless `<sha>` is reachable from its default branch. `parse_scope` failing answers
     `PLAN_SCOPE_INVALID`. An empty quote is refused.
   - Writes one evidence record (header and definition as in `work_authorization.py` lines 116-130, kind
     `plan-authority`) holding the plan path, commit, content digest, the parsed scope, approver `Founder` and the
     quote, and a create-only store aggregate `plan-authority:<content_digest>` with that record's reference. The same
     digest approved again is a repeat and writes no second record.
   - The current authority is the store aggregate `plan-authority:current`, holding `content_digest` and `record_ref`,
     committed with the store's expected-version write. Each approval, including a re-approval of an older digest,
     sets it to that approval's digest. Nothing else is current: an item issued under another digest fails the issuer
     rule of 2.2 and stops as owner-decision-required.
5. **The control plane releases inherited work** (`context_assembly/application/inherited_release.py`, new; command
   `work release <id>`, no quote). In this order, refusing with the named answer and writing nothing on refusal:
   - the item exists, is not retired, is at CAPTURE, has a pointer and no release record (`NOT_RELEASABLE`);
   - its retained assessment of the current pointer is READY (`ASSESSMENT_MISSING`);
   - its contract has `release_policy` `automatic-on` (`NOT_PLAN_DERIVED`; the `work authorize` path applies);
   - a current plan authority exists and `unsatisfiable(...)` with it gives no reasons (`OWNER_DECISION_REQUIRED`,
     detail the reasons joined with `; `). On this answer the composition also ensures one attention item through
     the existing attention service, as `WorkRegistry._ensure` does (`work_registry.py` lines 880-894): kind
     `JUDGMENT`, work ref the item id, owner `OPERATOR` until a Founder lane exists. This is the durable typed
     owner-decision requirement.
   - Then it writes, copying `WorkAuthorization.authorize` (lines 116-156) and changing nothing in that file:
     the evidence record with exactly the fields of lines 120-124 (`identity`, `pointer`, `attempt_id`,
     `assessment_ref`, `contract_digest`, `baseline`, `approver` = the contract's `authority_issuer`, `quote` = the
     plan approval's `record_ref` revision digest); the release record
     `ReleaseAuthorization(item.id, reference.revision_digest, True, baseline, text)` through `ReleaseRecords.record`
     with read-back, where `baseline` is the default branch's current head and `text` is
     `inherited from plan authority <content_digest> (<record_ref revision digest>)`; and
     `identities.set_evidence(item.id, "approval", reference)`, so `work context` finds its approval
     (`work_context.py` lines 144-155). The release precondition gate (`release.py` lines 151-171) is unchanged.
   - Then it links the item if it has no card (the existing `work link` service), writes the card text (the existing
     `work display` service), writes Status `READY` and Priority (the obligation's `priority`) on the card, and reads
     both back. `github_projects_v2.py` gains `write_priority(item_id, priority, expected_revision)`, written like
     `write_status` (lines 126-146) on the Priority field.
6. **The release flag follows each contract** (`work_registry.py`). The coordinator is built with
   `automatic_release=True` (line 516). The READY view handed to it is wrapped in `work_registry.py` so that
   `import_ready_snapshot()` returns each item as
   `replace(item, automatic_release=item.contract.release_policy == "automatic-on")`, and `_started_item` (line 542)
   uses the same expression. An `explicit-human-off` item is therefore never automatic: unreleased, it is not
   eligible (`factory_coordinator.py` line 347); released by the Founder, it is admitted as `EXPLICIT_HUMAN` exactly
   as today. `factory_coordinator.py` is not changed. Known and unchanged: `launch()` labels every item's coordinator
   release aggregate `EXPLICIT_HUMAN` (`factory_coordinator.py` lines 172-174); admission takes its source from the
   contract flag (line 360), not from that label.
7. **Commands** (`cli.py`, `operator.py`): `work approve-plan` and `work release` are added next to `work authorize`,
   with the same `--json` answers and argument errors. The read-only worker profile refuses both, like the other
   writing commands.
8. **After landing, one genuine owner decision remains:** approving the landed plan revision. The Founder gives the
   approval words once; the coordinator runs `work approve-plan --commit <landed main> --quote <those words>`. From
   then on, plan-derived items need no Founder action.

## 3. Acceptance checks

1. **The rule** (`tests/execution_coordination/domain/test_plan_authority.py`): `outside_authority` returns no reasons
   for a contract inside a sample obligation, and exactly one `owner-decision-required:` reason for each single
   change: a wrong issuer digest; no obligation reference; two references; an unknown label; another repository; a
   capability outside scope; a requirement id outside the obligation's; each budget field above its cap;
   `hard_wall_clock_seconds` absent; a dimension outside the cap list; an `authorized_scope` entry outside the
   obligation's paths; entries `docs/decisions` (no slash), `src/alienintent/execution_coordination/` (an ancestor of
   a protected file), `Docs/Decisions/x.md` (case), `src/*.py` (a glob), `a/../docs/decisions/x` (`..`) and
   `/src/x.py` (absolute). `parse_scope` refuses a missing, duplicate or malformed block and wrong keys.
2. **Satisfiability** (`tests/execution_coordination/domain/test_satisfiability.py`): every existing case gives the
   same reasons as before; `automatic-on` with no authority gives
   `release_policy: automatic-on requires an approved plan authority`; with an authority it gives exactly the
   authority's reasons.
3. **Plan approval** (`tests/context_assembly/test_plan_approval.py`): with a fixture plan committed on the default
   branch, the command records the exact commit, the `sha256:` of the file bytes and the parsed scope, and sets
   `plan-authority:current`; the same digest again answers repeated and writes nothing new; approving a second
   revision then the first again leaves the first current; a commit not on the default branch answers
   `PLAN_NOT_ON_MAIN`; a bad block answers `PLAN_SCOPE_INVALID`; an empty quote is refused; each refusal writes
   nothing.
4. **Inherited release** (`tests/context_assembly/test_inherited_release.py`), with a fixture board:
   - a plan-derived item assessed READY gets a release record whose `text` names the plan digest, its row's
     `approval_ref` is set, its card reads back Status READY and Priority P0, and `work context` for its PRODUCER
     assembles with no hold; no quote is given anywhere;
   - each refusal of 2.5 answers its named code and writes nothing (no release record, no `approval_ref`, no card
     change); `OWNER_DECISION_REQUIRED` also leaves exactly one attention item for the item;
   - an item issued under the first plan digest, after a second revision is approved, answers
     `OWNER_DECISION_REQUIRED`.
5. **The explicit path is unchanged**: every existing test in `tests/context_assembly/test_work_authorization.py` and
   `tests/control_plane/test_cli.py` passes unchanged, and `work release` on an `explicit-human-off` item answers
   `NOT_PLAN_DERIVED`.
6. **Through the coordinator** (`tests/composition/test_work_registry.py`):
   - a plan-derived item goes `work assess` → `work release` → `work launch` to its PRODUCER with no `work authorize`
     call and no test code writing a card Status;
   - the existing `test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store` (line 626) passes
     unchanged: an `explicit-human-off` item with a Founder release reaches its PRODUCER;
   - an `explicit-human-off` item whose card is READY but which has no release record is never dispatched by
     `start()`, and no attention item or escalation is raised for it.
7. **The canonical plan** at the candidate contains the new section 2.2 sentence exactly as fixed decision 5, no
   longer contains the old one, has section `2.2.1 Plan authority` with exactly one block equal to 2.1's, and its
   other section numbers are unchanged.
8. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each):
   - **M1:** in `outside_authority`, compare paths with a plain `startswith` on the raw entries, without
     normalization. The check-1 cases `docs/decisions`, `Docs/Decisions/x.md`, `a/../docs/decisions/x` and the
     ancestor case must fail.
   - **M2:** in `unsatisfiable`, let `automatic-on` pass when `plan_authority` is `None`. The check-2 no-authority case
     must fail.
   - **M3:** in `work release`, skip `identities.set_evidence(..., "approval", ...)`. The check-4 `work context` case
     must fail.
   - **M4:** in the `work_registry.py` wrapper, set every item's `automatic_release` to `True`. The check-6
     `test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store` and the never-dispatched case must
     fail.
   Revert each, and its tests must pass.
9. **The suite stays green:** the regression gate's own run at the candidate (as the worker) has no failed and no
   error test case, `tools/fitness/check_architecture.py --root src/alienintent --check all` passes, and
   `git diff --name-only <starting revision> <candidate>` lists only files in authorized_scope. `release.py`,
   `release_admission.py` (both), `regression_gate.py`, `factory_coordinator.py`, `work_authorization.py` and
   `github_work_management.py` are byte-identical.

## 4. Review record

**Revision 2 (2026-10-08).** REVIEWER of `11d9973` (FAIL; P1-P13).
- Derivation is now an obligation named in the approved plan bytes, with an allow-list of paths per obligation and a
  global protected list; paths are normalized and compared by ancestry (P3, P4, P5).
- Every `BudgetPolicy` field is capped (P6); `plan-authority:current` defines the current approval (P7); the new
  plan section is `2.2.1`, nothing is renumbered (P8).
- An owner-decision stop leaves a durable attention item (P9); inherited release copies the exact evidence fields and
  sets `approval_ref`, so `work context` does not hold (P1, P10); `work_context.py` is not changed.
- The release flag is set per item by a wrapper in `work_registry.py`; M4 and check 6 now discriminate (P2).
- The `launch()` label is stated (P11); line numbers corrected (P12); the one remaining owner decision after landing
  is stated (P13).

**Revision 1 (2026-10-08).** First draft, from the Founder's decisions of 2026-10-08
(`manual/path-to-done/founder-decisions-2026-10-08-autonomy.md`) and a code map of the Founder's gates at `a632147`.
