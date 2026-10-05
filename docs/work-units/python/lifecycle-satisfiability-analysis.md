# Lifecycle satisfiability of a hand-registered BIU on the registry launch path

> Written by the main session from the analysis agent's report (the agent could not write files).
> Spot-checked against main 759b5db by the main session: work_completion.py:98-102 and 171-173;
> work_registry.py:1294-1295, 1318-1320 and 1380; factory_coordinator.py:247-248, 364-367 and 519-523;
> verdict.py:34. All matched.


- Code authority: /home/netmarine/.local/state/alienintent/registry/clone/src/alienintent at main 759b5db. Paths below are relative to src/alienintent/.
- Example: work item 8427eb3d-401e-4f4a-8d7c-12abd979c211, packet docs/work-units/python/worker-runtime-doc-correction-r5.md (R5).
- Method: reading the code only, plus one read of readiness.sqlite through SQLiteOperationalStore(path, read_only=True). Nothing was written and no provider was called.

## 0. Short answer

- **R5 as written has no path to its declared end.** The VERIFIER accepted, but the coordinator's evidence contract cannot be met.
  - The coordinator only ever observes two evidence ids, "artifact-verified" and "independent-verifier-accepted" (factory_coordinator.py:520).
  - R5's required_evidence holds two free-text sentences, so every VERIFY ends in rework (factory_coordinator.py:521-523, domain/verdict.py:33-36).
  - Store state: rejections 1 of 2, stage IMPLEMENT, outcome rework. The next correct cycle ends in "failure" with attempt-budget-exhausted (factory_coordinator.py:572-573).
  - The contract cannot be changed after authorization (AUTHORIZED_INSTRUCTIONS_FIXED, packet_assessment.py:77-78, 111-112).
- **With landing off, the terminal state is stage ACCEPT with outcome ready-to-land, not DONE.**
  - The coordinator answers ready-to-land and runs nothing (factory_coordinator.py:170-171, 342-344).
  - `work record-completed` refuses any item with a coordinator record (COORDINATOR_OWNED, work_completion.py:98-102).
  - The DONE projection needs coordinator DONE with all five receipts (work_completion.py:171-173).
  - If the merge is done by hand (R5's plan), a later automated landing holds landing-ambiguous (work_registry.py:1294-1295, 1353-1354). DONE is then impossible for good, and so is _dependency_done for any dependent (factory_coordinator.py:762-768).
- **A corrected new item does have a deterministic path to ACCEPT/ready-to-land (section 4).**

## 1. Lifecycle gate table

Column key:
- **Static** = can be known before Founder authorization (yes/no).
- **R5** = does R5 satisfy it (yes / no / runtime).
- **Class** = dependency class: static / runtime-produced / circular / impossible.

| # | Stage | file:function | Predicate | Field/state consumed | Allowed vocabulary (constants) | Producer | Static | R5 | Why not | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CAPTURE | context_assembly/domain/work_contract.py:contract_block (32-56) | Exactly one block opened by ```json alienintent-contract and closed by ```. Valid JSON. Identity equals the item id. | packet bytes at the pointer | OPEN/CLOSE (l.15); NOT_TEXT, MISSING, DUPLICATE, UNCLOSED, INVALID_JSON, REFUSED, OTHER_IDENTITY | author | yes | yes | | static |
| 2 | CAPTURE | context_assembly/domain/compilation.py:contract_from_payload (197-217); execution_coordination/domain/contract.py:__post_init__ (75-92) | No unknown key. All fields present. Scalars non-empty. Every sequence except dependencies is non-empty with non-empty entries (this includes required_evidence, required_capabilities and required_closure_actions). | whole contract | BiuContract field names | author | yes | yes | | static |
| 3 | budget | contract.py:BudgetPolicy (24-45) | maximum_attempts>=1. retry_limit>=0. Limits>=1. Dimensions = hard_required_dimensions + wall-clock + concurrency + cancellation (each only when its limit is set). | budget_policy | hard_required_dimensions, maximum_attempts, hard_wall_clock_seconds, retry_limit, concurrency_limit, cancellation_limit | author | yes | yes (dims = wall-clock, cancellation) | | static |
| 4 | identity/digest | contract.py:90-92 | content_digest = sha256 of the canonical JSON | contract | sha256:<64hex> | computed | yes | yes (sha256:395ee1ae…) | | static |
| 5 | assessed READY | context_assembly/application/packet_assessment.py:assess/_run (55-135) | Registered packet, not retired, text instructions, binding OK, no release record yet. **The contract is not parsed.** | pointer, Agent Ready output | disposition READY; holds UNKNOWN_IDENTITY, NOT_A_REGISTERED_PACKET, IDENTITY_RETIRED, INSTRUCTIONS_NOT_TEXT, CAPABILITY_PROVENANCE_HOLD, AUTHORIZED_INSTRUCTIONS_FIXED, ATTEMPT_IN_PROGRESS, ATTEMPT_FAILURE, NO_ASSESSMENT | Agent Ready | no | yes | | runtime-produced |
| 6 | authorization | context_assembly/application/work_authorization.py:authorize (245-314), _stale (316-331) | State CAPTURE. Commit = pointer. Attempt is the latest, READY, and of the current pointer. Contract parses. Baseline is 40-hex, resolves, and is reachable from the default branch. Gate wording passes. | pointer, history, baseline, quote | NOT_AUTHORIZABLE, AUTHORIZATION_STALE, CONTRACT_INVALID, BASELINE_INVALID, GATE_WOULD_REFUSE, ALREADY_AUTHORIZED | Founder + work authorize | partly | yes | Does NOT check evidence ids, capabilities, policy, closure set, budget, routes or landing | runtime-produced |
| 7 | authorization/gate | execution_coordination/domain/release.py:admit_release_preconditions (151-171), UNAUTHORIZED_WORDING (91-95) | A release record for this item, authorizes_implement, exact baseline that resolves and is reachable, and no "not authorized"/"release refused" wording | release record, contract strings | implementation-authorized, baseline-named, baseline-resolves, baseline-reachable, authority-wording-consistent | work authorize | wording: yes | yes | | static/runtime |
| 8 | READY board | composition/work_registry.py:_ready_snapshot (727-740), _ready_row (742-769) | Card Status READY. Linked item, not retired, has a pointer. assessment_ref is in history, of the current pointer, READY. Contract parses. | card, row, assessment | NO_LINK, NOT_ELIGIBLE, ASSESSMENT_MISSING, CONTRACT_INVALID | Founder | no | yes | | runtime-produced |
| 9 | READY translation | execution_coordination/adapters/github_work_management.py:_translate (175-198) | Complete/membership/repository. Status mapped. Identity/digest/readiness present. **Priority required for READY.** Dependencies are a list of strings. | priority, status, digest | {"P0".."P5"}; STATES (context_assembly/domain/work_identity.py:21) | Founder | knowable | runtime (P0) | | runtime-produced |
| 10 | release/eligibility | factory_coordinator.py:launch (172-175), _is_released (797-801), _eligible (335-347) | An explicit-human release exists. Not DONE. Outcome is none of {authority-block, blocked-by-authority, cancelled-by-operator, cancelled-by-decision, failure, timeout}. Stage is in ROLE_BY_STAGE. Dependencies done. | release:<id>, factory:<id> | ReleaseSource.EXPLICIT_HUMAN | work launch | yes | yes | | runtime-produced |
| 11 | capability | factory_coordinator.py:_run (360-367) → release.py:admit_release (58-80) | Policy matches the source. readiness_digest = digest. Dependencies satisfied. **required_capabilities ⊆ available.** Each dimension >=1. | release_policy, required_capabilities, decision_choice | Available = {"python","filesystem","process-control"}, plus the contract's capabilities only if decision_choice=="authorize" (364-366) | author / work decide | yes | **no at first launch** ("git" → ValueError → authority-block, 373-377); yes after authorize | Only a decision that exists after the block grants it | circular |
| 12 | release policy | release.py:64-69; work_registry.py:464 (automatic_release=False) | The source is always explicit-human, so automatic-on always fails | release_policy | AUTOMATIC_ON="automatic-on", EXPLICIT_HUMAN_OFF="explicit-human-off" | author | yes | yes | (automatic-on is never satisfiable here) | impossible for automatic-on |
| 13 | budget admission | factory_coordinator.py:_available_budget (448-457) | No allocation, so each required dimension = 1 | required_dimensions | — | composition | yes | yes | | static |
| 14 | release gate | execution_coordination/application/release_admission.py:check (24-32) | Row 7 again before every PRODUCER | record, baseline | as 7 | work authorize | partly | yes | | runtime |
| 15 | WIP admission | factory_coordinator.py:_run (378-385); work_registry.py:wip_limit (315-324) | wipLimit is an int >=1 in the host config (no default), and a slot is free | host wipLimit, wip reservations | "wip-limit-unavailable", "wip-refused" | host config | config: yes | yes | | static/runtime |
| 16 | repository reservation | factory_coordinator.py:_run (398-402) | One repository reservation per repository | github.repository | StopReason.CAPACITY_UNAVAILABLE | coordinator | no | runtime | Another in-flight item in the same repository blocks this one | runtime |
| 17 | recovery | factory_coordinator.py:_recover (612-687) | Every non-WIP reservation is a resolvable launch:<id>:<v> repository reservation, otherwise CAPACITY_UNAVAILABLE | reservations, effect ledger | none/pending/confirmed/unknown | store | no | runtime | A foreign stale reservation blocks all launches | runtime |
| 18 | prepare | work_registry.py:LaunchPreparation.prepare (1111-1134), _budget_stated (1206-1216) | hard_wall_clock_seconds and cancellation_limit are stated; at CLOSURE, is_fixed | budget_policy | "MISSING_RECORD: budget_policy: …" | author | yes | yes | | static |
| 19 | context package | context_assembly/application/work_context.py:_assemble (121-241) | Holds, in order: work_item MISSING (126-128); contract MALFORMED (131-134); assessment MISSING (140-142); release_record MISSING (145-147); release evidence DIGEST_MISMATCH for record_ref/pointer/attempt_id/contract_digest (150-157); starting_revision MISSING (158-159); contract_digest MISMATCH (161-162); attempt VERSION_DRIFT (243-258); history MALFORMED (165-171); resources wip/repository MISSING (173-179); dependencies MISSING (288-291); design_rules MISSING (299-306); for VERIFIER/CLOSURE: candidate MISSING/MISMATCH (218-223), producer_self_review MISSING/MALFORMED (310-318), diff MISSING (231-237); STORE_UNAVAILABLE / EVIDENCE_UNAVAILABLE | all records | HoldReason.{MISSING_RECORD, MALFORMED_RECORD, DIGEST_MISMATCH, VERSION_DRIFT, STORE_UNAVAILABLE, EVIDENCE_UNAVAILABLE} | registry, authorize, coordinator, PRODUCER | references, dependencies and contract: yes; rest: no | yes | | mixed |
| 20 | authority references | work_context.py:_reference (299-308) | The first word is a valid path present at the **pointer commit** | authority_references | — | author | yes | yes | (R3 failed here) | static |
| 21 | dependencies | work_context.py:_dependency (288-297); factory_coordinator.py:_dependency_done (762-768) | Registered. Coordinator DONE, or no coordinator record and recorded complete. | dependencies | — | other items | yes | yes (none) | | static/runtime |
| 22 | routing | work_registry.py:prepare (1122-1131); composition/model_routing.py:resolve_route (81-95) | schemaVersion 1, provider, model token, absolute executable, permission mode. With a worker user, provider must be codex and login present. CLOSURE uses the VERIFIER route. | model-routing.json | _PROVIDERS={codex,claude}, _PERMISSIONS, WORKER_PROVIDER="codex"; model-routing-unavailable, worker provider unsupported, worker provider login missing | host | yes | yes | | static |
| 23 | worker runtime | work_registry.py:project_configuration (225-227), worker_uid (276-281), worker_login_present (251-254), prepare_worker_session (257-273) | User name pattern; Unix user exists; auth.json is a real file; session prep commands exit 0 | project config | ConfigurationInvalid, OSError | host | yes | yes | | static |
| 24 | provider executable | invocation_runtime/adapters/cli_worker.py:run (190-227), worker_prefix (32-43) | Runs under env -i PATH=/usr/bin:/bin as the worker; capabilities ⊇ {wall-clock, cancellation} | route executable | WORKER_PATH; PROVIDER_DIMENSIONS (composition/sandbox_run_profile.py:54) | host | yes | yes | (R4 failed here) | static |
| 25 | context command | work_context.py:ContextCommand.document (72-82); work_registry.py:_work_context (916-919) | installed_executable() of the launching interpreter runs as the worker in export mode | sysconfig scripts dir | argv … work context --export <launch>/exports/<c>/context.json | launch interpreter | yes | yes | | static |
| 26 | PRODUCER run | invocation_runtime/application/real_worker.py:_produce (447-518) | Grant includes process-control and git-write. Limits set. Dimensions covered. Workspace allocated at the start revision. Process succeeds. | grant, budget | ROLE_OPERATIONS (composition/role_binding.py:62-66) | composition | yes | yes | | static/runtime |
| 27 | custody/publication | real_worker.py:494-505; factory_coordinator.py:_advance (492-498); domain/lifecycle.py verify (77-81); domain/custody.py:36-37 | Handover by SHA, publish to candidate/<c>, read back; fresh-process recheck; independent_read_back_proven | SHA | source-revision; git:<remote>#<branch>@<sha> | PRODUCER + control plane | no | yes (a82e848) | | runtime |
| 28 | correlation read-back | real_worker.py:correlated_outcome (67-104); factory_coordinator.py:_correlated (464-476) | One start event and one outcome event; same item, role and digest; kind allowed for the role | journal | CANDIDATE_KINDS: PRODUCER {success}, VERIFIER {accept, reject}, CLOSURE {closed} | provider | no | yes | | runtime |
| 29 | self-review | work_registry.py:published (1190-1196); work_context.py:record_self_review (324-353) | Non-empty self-review.md, recorded once per candidate; the VERIFIER package needs it | text | SELF_REVIEW_EXISTS | PRODUCER | no | yes | If empty, the VERIFIER holds on producer_self_review | runtime |
| 30 | VERIFY inputs | real_worker.py:_evaluate (290-340); cli_worker.py:_worker_feature_regressions (131-143) | Candidate clone; package; runner tools/verification/run_feature_regressions.py exits 0 with --base <start> | candidate, base | — | control plane | runner present: yes | yes | | runtime |
| 31 | verdict vocabulary | real_worker.py:read_verdict (145-172) | revision = SHA; findings are strings; "accept", or "reject" with findings | verdict.json | accept, reject, verdict-missing, verdict-malformed, verdict-miscorrelated, feature-regressions-missing | VERIFIER | no | yes (accept) | | runtime |
| 32 | feature regressions | real_worker.py:_feature_regression_receipt (121-142); factory_coordinator.py:511-516 | kind FeatureRegressionReceipt, passed, candidate=SHA, all packs pass, digest OK | feature-regressions.json | "feature-regressions:sha256:<hex>"; hold feature-regressions-missing | runner | no | yes | | runtime |
| 33 | attribution | factory_coordinator.py:502-510 | Same candidate; producer_correlation exists and differs from the VERIFIER's | record | verifier-outcome-not-attributable:<kind> | coordinator | no | yes | | runtime |
| 34 | **required_evidence → evidence id** | factory_coordinator.py:_advance (519-523); domain/verdict.py:evaluate_verdict (32-37) | required = set(required_evidence) ∪ {"independent-verifier-accepted"} must be ⊆ proven = {"artifact-verified" (if verify_admissible), "independent-verifier-accepted"} | required_evidence | ONLY "artifact-verified", "independent-verifier-accepted" (VERIFIER_EVIDENCE l.26). No mapping from free text exists anywhere; otherwise it is only copied into the package (work_context.py:195-196). | author | **yes** | **no** | "VERIFIER verdict" and the export sentence are never observed → REJECT "required trusted evidence is missing" → _rework | **impossible** (static) |
| 35 | attempt budget | factory_coordinator.py:_rework (563-574) | rejections+1 >= maximum_attempts → "failure" (attempt-budget-exhausted) | maximum_attempts, rejections | FINAL_OUTCOMES={cancelled-by-operator, cancelled-by-decision, failure, timeout} | coordinator | yes | rejections 1 of 2 | Follows from 34 | impossible (R5) |
| 36 | ACCEPT | lifecycle.py accept (84-87) | REVIEW + ACCEPT verdict | verdict | LifecycleStage.ACCEPT | coordinator | — | no | Follows from 34 | — |
| 37 | CLOSURE entry | factory_coordinator.py:launch (166-171); domain/closure.py:is_fixed (25-28) | Exactly the five names | required_closure_actions | ACTIONS=(candidate-published, merged-to-main, landing-record, board-updated, workspaces-cleaned); "closure-not-automated" | author | yes | yes | | static |
| 38 | CLOSURE run | real_worker.py:_close_with (366-401) | Grant includes git-read and process-control; full SHA; wall clock set; clone; package; session succeeds | grant | ROLE_OPERATIONS[CLOSURE] | composition | yes | runtime | | runtime |
| 39 | closure request vocabulary | closure.py:parse_request (51-72), performable (75-82); work_registry.py:RegistryClosure.close (1277-1299) | Keys exactly {identity, revision, actions, findings}; ids match; actions ⊆ ACTIONS with no repeats; ≤20 findings of ≤500 chars. **merged-to-main and landing-record must be requested**, otherwise there is no ready-to-land. | closure-request.json | REQUEST_KEYS; request-missing, request-malformed, request-keys, request-identity, request-revision, request-actions, request-findings | CLOSURE session | needed set: yes | runtime | | runtime |
| 40 | landing build | close (1290-1297), _build (1388-1420), _fetch (1551-1560) | Credential-free fetch of the default branch; candidate not already on head (else landing-ambiguous); head is a proper ancestor (else closure-rework:base-moved); merge --no-ff and record commit check out | remote | remote-unreadable, landing-ambiguous, merge-failed, merge-tree, record-unreadable, record-failed, record-changes | git | remote readability: yes | runtime | A hand merge before CLOSURE → landing-ambiguous | runtime |
| 41 | landing disabled | work_registry.py:_landing_authority (683-684), _order (1320-1321); real_worker.py:391, 400-401 | github.landing false → authority None → finding ready-to-land:<merge>; the provider adds candidate-published:<id>:<sha> | github.landing | READY_TO_LAND="ready-to-land" | config | yes | runtime | | static |
| 42 | receipt rule | factory_coordinator.py:_advance_closure (534-557); closure.py:parse_receipt (37-42), parse_finding (103-117) | kept={candidate-published} and kinds==[ready-to-land] → ready-to-land; all five → DONE; closure-rework → _rework; closure-hold → authority-block; else closure-receipts-incomplete | receipts, findings | <action>:<id>:<40hex>; SESSION_FINDING="closure-finding: " | control plane | yes | runtime | | runtime |
| 43 | ready-to-land terminal | factory_coordinator.py:launch (170-171), _eligible (342-344) | ACCEPT + ready-to-land + landing off → answers ready-to-land and runs nothing | record | READY_TO_LAND | coordinator | yes | not reached | | static |
| 44 | DONE | lifecycle.py close (88-93); _advance_closure (542-544) | All five receipts | receipts | ACTIONS | Landing Authority | yes | no | merged-to-main/landing-record come only from _after_landing (1380) | impossible while landing off |
| 45 | DONE row | work_registry.py:_project_completed (494-510); work_completion.py:98-102, 171-173 | Row DONE only after coordinator DONE; record-completed refuses any coordinator record | factory:<id> | COORDINATOR_OWNED, COORDINATOR_INCOMPLETE | coordinator | yes | no | Record exists from the first launch | impossible (permanent after a hand merge) |
| 46 | WIP release | factory_coordinator.py:_release_ended_wip (601-610), _record_result (580-588) | Released at DONE or an outcome in FINAL_OUTCOMES ∪ {ready-to-land} | record | as 35/43 | coordinator | yes | R5 still holds it | | static |
| 47 | attempt/version/correlation | factory_coordinator.py:398, 413-414; work_context.py:_attempt (243-258) | launch:<id>:<v>; package valid at v, or at v+1 with effect pending/unknown | version, ledger | VERSION_DRIFT | coordinator | no | yes | | runtime |
| 48 | replay/idempotency | admit_release (59-63, always called with {}); record_self_review (351-352); cancel (242-248); validate_decision/record_decision (916-964); _recover (670-674) | Repeats and stale calls cannot advance | keys, versions | SupersededDecision, TerminalWork, VersionConflict, SELF_REVIEW_EXISTS | store | yes | yes | **An accepted item at ready-to-land cannot be cancelled** | static |

## 2. Unsatisfiable or unreachable predicates for R5

1. **Evidence ids** (factory_coordinator.py:520-523; verdict.py:33-36). The two free-text required_evidence entries are never in {"artifact-verified","independent-verifier-accepted"}. Observed: launch:8427eb3d…:4, outcome_kind accept → outcome rework, finding "required trusted evidence is missing".
2. **Attempt budget** (factory_coordinator.py:572-573). With rejections 1 of 2, the next correct cycle ends in a final "failure" and the WIP slot is released (line 607).
3. **Contract frozen** (packet_assessment.py:77-78, 111-112). Item 1 cannot be fixed inside R5.
4. **ACCEPT, CLOSURE and ready-to-land are unreachable** because of item 1 (lifecycle.py:84-87).
5. **DONE with landing off** (work_registry.py:467, 683-684, 1320-1321; factory_coordinator.py:170-171, 342-344, 542-544; work_completion.py:98-102, 171-173).
6. **DONE after the planned hand merge** (work_registry.py:1294-1295, 1353-1354). It is permanently impossible:
   - the item cannot be cancelled (factory_coordinator.py:247-248);
   - its dependents are never admitted (factory_coordinator.py:762-768).
7. **Circular: the "git" capability** (factory_coordinator.py:364-367; release.py:75-76). It forces an authority-block, then `work decide authorize`. Observed: launch 20261005T090844Z was authority_blocked, then doc-correction-r5-decide.json recorded authorize.

Free text that is never a rule (only shown in the package): completion_criteria, verification_obligations, retry_policy, non_goals, candidate_custody_requirements, stop_escalation_conditions, excluded_scope, fixed_decisions, target_repositories, baselines. In the files I read, authorized_scope is also only in the package.

## 3. Predicates that could have been checked before authorization

Everything below is a pure function of the packet and the host configuration:

- Rows 1-4: contract parse, identity, digest.
- Row 34: required_evidence ⊆ {"artifact-verified","independent-verifier-accepted"}. This would have caught R5.
- Row 11: required_capabilities ⊆ {"python","filesystem","process-control"}, or else a predicted `work decide` step. This would have flagged R5.
- Row 12: release_policy == "explicit-human-off".
- Rows 3, 18, 24: both limits stated; required_dimensions ⊆ PROVIDER_DIMENSIONS.
- Row 37: is_fixed(required_closure_actions).
- Row 20: authority references present at the pointer commit.
- Row 21: dependencies registered and able to reach DONE.
- Row 7: gate wording.
- Host: wipLimit; routes (PRODUCER, plus VERIFIER, which CLOSURE also uses) on codex with an absolute native executable runnable as the worker; worker login; context command from the runtime install; regression runner at the baseline; remote readable without a credential.
- github.landing, and from it the reachable terminal state. Also that a hand merge makes DONE impossible.

preflight-r5 covered most host items. It did not check rows 34, 11 (it listed the git decision as runtime), 12, 15, 40 or 41-45.

## 4. Reachability proof attempt

Assume the cognitive steps and the infrastructure all succeed.

**R5: no path.** It breaks at REVIEW (factory_coordinator.py:521-523). The observation tuple is built from two constants (line 520), and no runtime value can add "VERIFIER verdict" or the export sentence. So every genuine accept goes to rework, and after maximum_attempts=2 the outcome is failure.

**Corrected new item, landing off: a deterministic path to ACCEPT / ready-to-land exists.**

1. Contract parses. Digest D (author).
2. `work assess` → READY assessment of the current pointer; assessment_ref is set (Agent Ready, _saved).
3. `work authorize` with the pointer commit, the latest READY attempt and a 40-hex baseline B on main → release record (authorizes_implement=True, baseline=B) and approval_ref (work_authorization.py:285-313).
4. Founder sets the card to READY with a priority P0..P5 → row imported with readiness_digest=D.
5. `work launch` → explicit-human release (172-175). _eligible is true.
6. PRODUCER run:
   - the gate passes;
   - admit_release passes: explicit-human-off with source explicit-human, D==D, no dependencies, capabilities ⊆ base, dimensions = 1;
   - WIP acquired; repository reservation launch:<id>:0; commit_with_effect + claim_effect → v1;
   - prepare passes: budget, package (attempt 0 at v1 with effect pending/unknown, WIP and repository held), codex route, login, export;
   - starting revision = B.
7. The worker commits SHA S and writes its self-review. The control plane hands it over, publishes to candidate/launch-<id>-0 and reads it back (independent_read_back_proven=True). The self-review is recorded. Outcome success → correlated → transition verify → stage VERIFY, outcome success, producer_correlation set (492-498). WIP is kept.
8. `work launch` (card still READY) → VERIFIER:
   - clone of S; package with candidate, self-review and diff B..S;
   - regression runner --base B passes → feature-regressions:sha256:…;
   - verdict {revision:S, verdict:"accept", findings:[]};
   - attribution passes → REVIEW;
   - required = {"independent-verifier-accepted"}, which is ⊆ proven → ACCEPT verdict → stage ACCEPT, accepted=True, verdict recorded (519-525).
9. `work launch` → ACCEPT:
   - _resolve uses the READY row, or _started_item when the journal digest = D;
   - is_fixed holds, so CLOSURE runs;
   - grant git-read and process-control; clone of S; package with closure_actions;
   - the session writes {"identity":id, "revision":S, "actions":[all five], "findings":[]};
   - close(): performable = all five; credential-free fetch gives head H; S is not on H; H is a proper ancestor of S; _build gives merge M and record R;
   - authority is None → findings ("ready-to-land:M",), receipts () → the provider adds candidate-published:<id>:S.
10. _advance_closure: kept={candidate-published}, kinds=[ready-to-land] → outcome ready-to-land (547-548). The WIP slot is released (607).
11. Every later `work launch` answers ready-to-land (170-171).

**Terminal state:** stage ACCEPT, outcome ready-to-land, accepted=True, WIP released.

**Is DONE reachable?**
- Not while landing is off.
- It becomes reachable if github.landing is later set to true **without** a hand merge. Then the next launch re-acquires WIP (388-397) and runs a fresh CLOSURE session. No closure-ordered event was journaled earlier, so nothing blocks it. It lands, sets the board to DONE, cleans up, collects all five receipts, closes to DONE, and _project_completed sets the row to DONE.
- After a hand merge, DONE is impossible (section 2, item 6).

## 5. Minimum packet correction (new work item; R5 is frozen)

1. Set required_evidence to ["independent-verifier-accepted"] (and optionally "artifact-verified"). Move the export sentence into fixed_decisions or verification_obligations.
2. Set required_capabilities to ["filesystem"] (or "process-control") instead of "git". If "git" is kept, the packet must say that the first launch blocks and needs `work decide authorize`.
3. Declare the end truthfully: "ACCEPT/ready-to-land; DONE is not reached while landing is off". Do not plan a hand merge if DONE is ever wanted. Otherwise accept that the item stays at ready-to-land for good and that nothing may depend on it.
4. Optional, Founder's choice: maximum_attempts 3.

## 6. Minimum product changes so Work Preparation refuses such a packet before READY

Add one pure check, contract_satisfiability(contract, host). Run it in PacketAssessment.assess before Agent Ready launches (a new hold such as CONTRACT_UNSATISFIABLE that names the field). Run it again in WorkAuthorization.authorize before the release record is written. Rules:

1. required_evidence ⊆ OBSERVABLE_EVIDENCE = {"artifact-verified", VERIFIER_EVIDENCE}. Export this once and use the same constant to build the observations at factory_coordinator.py:520.
2. release_policy == EXPLICIT_HUMAN_OFF on the registry project.
3. required_capabilities ⊆ BASE_CAPABILITIES. Lift the literal at line 364 into a constant. Anything else is refused, or flagged as needing `work decide`.
4. Both limits are stated (_budget_stated) and required_dimensions ⊆ PROVIDER_DIMENSIONS.
5. is_fixed(required_closure_actions).
6. Authority reference paths exist at the pointer commit (reuse _reference).
7. Each dependency is registered and can reach DONE (it is not stuck at ready-to-land with landing off).
8. Report the reachable terminal state from github.landing.

Today, `work assess` never parses the contract (packet_assessment.py:55-135). `work authorize` checks only the gate wording and the baseline (work_authorization.py:260-294).

## 7. Proposed deterministic readiness rule

READY means: from the current recorded state, at least one deterministic path to the declared terminal state exists, using only values a component on this path can produce, and assuming every cognitive step succeeds.

In practice, before READY:
- All static rows (1-4, 7, 11-13, 15 config, 18, 20-25, 34, 37, 41-45) evaluate true against the packet and host configuration.
- Every vocabulary-bound field takes values only from the named constants.
- Every human step on the path (authorize, card READY, any `work decide`) is named in the packet.
- The declared terminal state matches the configuration: ready-to-land if landing is off; DONE only if landing is on and no hand merge is planned.
- A field whose value no producer can make is a refusal, not a warning.

## Gaps

- invocation_runtime/adapters/git_worktree.py (WorkerCloneAdapter, IntakeSourceControl) and RoleBindingGuard were not read in full. So scope and starting-revision enforcement at hand-over is unverified. This does not change the path conclusion.
- That CLOSURE can fetch the remote without a credential is assumed under "infrastructure works".
- I used 24 tool calls of the 70 cap.
