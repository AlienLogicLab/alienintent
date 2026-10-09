# Work unit: plan-level execution authority, with actual-diff containment

**Label:** `PLAN-AUTHORITY-INHERITANCE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Revision 3, 2026-10-09, for review. Not registered, not assessed, not released.
**Position on the path (Founder 2026-10-09, decisions section 16):** step 3. VERIFIER gate evidence (done) -> NO-CHANGE
(done) -> PLAN-AUTHORITY-INHERITANCE -> BOUNDED-ROUTINE-LAUNCH -> Work Preparation / READY refill -> three-item proof.
**Starting revision:** main `17910f7`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.
**After landing, one genuine owner decision:** the Founder approves the landed plan revision once (`work approve-plan`).

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-3",
 "intent": "The Founder approves an exact revision of the canonical plan once (`work approve-plan`); the plan names its obligations (each with allowed paths), its limits and its protected paths. A Work Item that names one of those obligations, stays inside its paths and the plan's limits, is assessed READY and is satisfiable is released by the control plane (`work release`) with no Founder words: release record, card READY with the obligation's priority, read back. Anything outside stops with a typed owner-decision requirement; ad hoc work keeps the explicit Founder release. A plan-derived candidate may advance only when its actual changed paths, read by the control plane from the trusted start to the candidate, are a subset of the exact assessed scope and touch no protected path; the PRODUCER checks before publication and CLOSURE checks the diff that would land, against the CURRENT approved authority, before any landing effect. A new plan approval stops items released under the old one. The canonical plan's section 2.2 states this rule.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-08 (decision 1): plan-level execution authority binds to an exact canonical-plan revision; a derived item inherits only when traceably derived from the plan, Agent Ready READY, satisfiable, dependencies and priority deterministic, and it introduces no new owner decision; otherwise a typed owner-decision requirement; ad hoc work keeps explicit Founder approval.",
  "Founder 2026-10-08 (decision 2): the authority root is docs/decisions/alienintent-v2-canonical-project-plan.md bound to an exact commit and content digest; a changed plan is not authorized by an old approval.",
  "Founder 2026-10-08 (decision 5): section 2.2 becomes 'After the Founder approves canonical product intent/plan authority, derived Work Items advance without additional Founder approval unless they cross a new owner-decision boundary.'",
  "Founder 2026-10-08 (decision 6): a plan-derived candidate may advance only when its actual changed paths are a subset of the exact assessed Work Item scope, and none of those paths intersect the protected authority surface; trusted inputs only (actual diff start->candidate, scope from the control plane's assessed packet, protected paths from the approved plan digest, evaluation code from the trusted baseline); checked before VERIFY admission (a failure is a PRODUCER rework, no VERIFIER attempt) and confirmed by CLOSURE before landing; core files are not blanket-protected.",
  "Founder 2026-10-09 (section 16): mission - approved canonical plan in, three real Work Items reach DONE automatically, the Founder does nothing except genuine owner decisions; the standing rule.",
  "Founder 2026-10-09: the whole suite is the regression gate's; the VERIFIER does not rerun it."
 ],
 "authorized_scope": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/context_assembly/application/plan_approval.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/execution_coordination/domain/plan_authority.py",
  "src/alienintent/execution_coordination/domain/satisfiability.py",
  "src/alienintent/execution_coordination/domain/scope_containment.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/ports/source_control.py",
  "tests/composition/test_work_registry.py",
  "tests/composition/test_worker_launch.py",
  "tests/context_assembly/test_inherited_release.py",
  "tests/context_assembly/test_plan_approval.py",
  "tests/control_plane/test_cli.py",
  "tests/execution_coordination/domain/test_plan_authority.py",
  "tests/execution_coordination/domain/test_satisfiability.py",
  "tests/execution_coordination/domain/test_scope_containment.py",
  "tests/execution_coordination/test_containment_wiring.py",
  "tools/fitness/coupling_register.json"
 ],
 "excluded_scope": [
  "release.py, release_admission.py (both), regression_gate.py, work_authorization.py and github_work_management.py",
  "the worker effect ledger and the card projection outbox",
  "BASE_MOVED revalidation",
  "the runner (BOUNDED-ROUTINE-LAUNCH) and Work Preparation"
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
  "acceptance checks 1-4 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff from the starting revision equals section 2's diff",
  "the VERIFIER runs the 17 mutations of check 4 exactly and records that each makes its named tests fail and that reverting makes them pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a generic messaging framework",
  "rewriting the coordinator's release labels"
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
  "section 2's diff does not apply exactly at the starting revision",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Every registry Work Item needs the Founder: `explicit-human-off` is the only accepted release policy, a release record
needs `work authorize --quote`, and the card's READY is set by hand. Decisions 1-6 replace this with one approval of an
exact plan revision, inherited by derived items, and containment so that inherited authority cannot reach outside the
assessed scope or touch what releases it.

## 2. The change: exactly this diff at `17910f7`

Invariants the diff implements:
1. **Authority root.** `work approve-plan --commit <sha> --quote <words>` reads the canonical plan at `<sha>` (reachable
   from main), parses exactly one `alienintent-plan-authority` block (target repositories, capabilities, budget caps,
   protected paths, obligations with allowed paths and priority), records it as evidence bound to the commit and the
   `sha256:` of the file bytes, and sets `plan-authority:current`. A changed plan needs a new approval.
2. **Derived means inside an obligation.** `outside_authority(contract, authority)` gives one `owner-decision-required:`
   reason per broken rule (issuer digest, one obligation reference, repositories, capabilities, requirement ids, budget
   caps, scope under the obligation's paths in exact case, no scope entry crossing a protected path, case-folded).
   Satisfiability accepts `automatic-on` only through it.
3. **Release with no Founder words.** `work release <id>` writes the release record (baseline = default branch head),
   `approval_ref`, links the item, writes the card text, Status READY and the obligation's Priority, each read back; on
   any owner-decision reason it writes nothing but one attention item.
4. **Per-contract release, current authority only.** The registry coordinator releases by policy only items whose
   contract is `automatic-on` AND inside the CURRENT authority; `explicit-human-off` items keep the Founder release.
5. **Containment (decision 6).** For `automatic-on` items: the PRODUCER's actual diff (read by the control plane: the
   intake with a worker user, from the trusted `starting_revision`; fail closed without one) must be inside the exact
   scope and off the protected paths (symlinks, submodules, `sitecustomize.py`, `.pth`, `conftest.py` refused anywhere);
   a violation is a typed `scope-violation` PRODUCER rework, nothing published, no VERIFIER attempt. CLOSURE, at the top
   of `_order` (every first order and re-order) and before a journaled re-land, checks the diff from the actual landing
   base against the CURRENT authority (`outside_authority` and protected paths) before any landing effect; a violation is
   a typed `scope-violation` hold with the reasons, plus one owner-decision attention item when outside authority.
6. **The canonical plan** gets decision 5's sentence in section 2.2 and a new section 2.2.1 with the block: obligations
   BOUNDED-ROUTINE-LAUNCH, WORK-PREPARATION-REFILL, TERMINAL-BOARD-STATUSES, STORE-SCHEMA-HARDENING, AUTONOMY-PROOF.

```diff
diff --git a/docs/decisions/alienintent-v2-canonical-project-plan.md b/docs/decisions/alienintent-v2-canonical-project-plan.md
index 7ea6208..52d786c 100644
--- a/docs/decisions/alienintent-v2-canonical-project-plan.md
+++ b/docs/decisions/alienintent-v2-canonical-project-plan.md
@@ -52,7 +52,7 @@ Finish the current accepted work through a separate CLOSURE instance. Then prepa
 
 The Director must read checked current Python work state. Its existing input adapter reads the previous runtime's state, so starting that unchanged adapter does not satisfy this requirement. The existing host's episode-completion behavior is useful code to connect, not a reason to rebuild supervision.
 
-Give the next bounded packet a complete description and independent adversarial review before Agent Ready assessment and Founder inspection. No unapproved candidate is automatically released. After the Founder approves a queue item, ordinary advancement needs no additional prompt or repeated approval.
+Give the next bounded packet a complete description and independent adversarial review before Agent Ready assessment and Founder inspection. No unapproved candidate is automatically released. After the Founder approves canonical product intent/plan authority, derived Work Items advance without additional Founder approval unless they cross a new owner-decision boundary.
 
 A temporary inexpensive monitor may report completion and wake the responsible coordinator while the application connection is built. Its scope, owner, expiry and replacement are explicit. The full CLM-8B and Qwen3.5-9B evaluation and adaptive routing program remains later work; the minimum current-state interface and automatic continuation needed for this proof move onto the immediate path.
 
@@ -60,6 +60,57 @@ The existing reliable-facts design is the model-facing connection described in f
 
 After this proof, connect preparation of new work from requirements to establish complete self-building. Do not describe a manually prepared queue as proof that the factory prepares its own work.
 
+## 2.2.1 Plan authority
+
+Founder decision, 2026-10-08: Founder approval attaches to an exact revision of this plan, never to its mutable path. `work approve-plan --commit <sha>` records that approval once, with the Founder's words, the plan's commit and the `sha256:` content digest of its bytes; if the plan changes, the old approval does not authorize the new content. A Work Item inherits execution authority from the approved revision only when it names one of the obligations below (`authority_issuer` `plan-authority:<digest>`, one `authority_references` entry `docs/decisions/alienintent-v2-canonical-project-plan.md obligation:<LABEL>`, `release_policy` `automatic-on`), stays inside that obligation's paths and the limits below, is assessed READY and is satisfiable. The control plane then releases it (`work release`) with no Founder words and no manual board change. Anything outside stops with a typed owner-decision requirement. Work not derived from an approved plan keeps the explicit Founder release.
+
+Inherited authority never extends to a protected path, even inside an obligation's paths, and a plan-derived candidate advances only when every path it actually changed is inside its assessed scope and outside the protected paths: the control plane checks the actual diff before VERIFY and again at CLOSURE before landing. The block below is part of this plan's bytes, so the approved digest covers every obligation, path and limit.
+
+```json alienintent-plan-authority
+{"target_repositories": ["AlienLogicLab/alienintent"],
+ "capabilities": ["python", "filesystem", "process-control"],
+ "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
+                 "retry_limit": 1, "concurrency_limit": 1,
+                 "hard_required_dimensions": ["wall-clock", "attempts", "retries", "concurrency", "cancellation"]},
+ "protected_paths": ["docs/decisions/", "docs/architecture/", ".github/", ".claude/", "AGENTS.md", "CLAUDE.md",
+                     "tools/fitness/", "conftest.py", "tests/conftest.py", "pyproject.toml", "setup.cfg", "config/",
+                     "src/alienintent/execution_coordination/domain/release.py",
+                     "src/alienintent/execution_coordination/domain/satisfiability.py",
+                     "src/alienintent/execution_coordination/domain/plan_authority.py",
+                     "src/alienintent/execution_coordination/domain/scope_containment.py",
+                     "src/alienintent/execution_coordination/application/release_admission.py",
+                     "src/alienintent/execution_coordination/adapters/release_admission.py",
+                     "src/alienintent/context_assembly/application/work_authorization.py",
+                     "src/alienintent/context_assembly/application/plan_approval.py",
+                     "src/alienintent/context_assembly/application/inherited_release.py",
+                     "src/alienintent/invocation_runtime/application/regression_gate.py",
+                     "src/alienintent/composition/landing_authority.py",
+                     "tests/execution_coordination/domain/test_plan_authority.py",
+                     "tests/execution_coordination/domain/test_satisfiability.py",
+                     "tests/execution_coordination/domain/test_scope_containment.py",
+                     "tests/execution_coordination/test_containment_wiring.py",
+                     "tests/context_assembly/test_plan_approval.py",
+                     "tests/context_assembly/test_inherited_release.py",
+                     "tests/context_assembly/test_work_authorization.py"],
+ "obligations": [
+  {"label": "BOUNDED-ROUTINE-LAUNCH", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+   "allowed_paths": ["src/alienintent/invocation_runtime/", "src/alienintent/execution_coordination/",
+                     "src/alienintent/composition/", "src/alienintent/control_plane/", "tests/invocation_runtime/",
+                     "tests/execution_coordination/", "tests/composition/", "tests/control_plane/"]},
+  {"label": "WORK-PREPARATION-REFILL", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+   "allowed_paths": ["src/alienintent/context_assembly/", "src/alienintent/composition/",
+                     "src/alienintent/control_plane/", "tests/context_assembly/", "tests/composition/",
+                     "tests/control_plane/"]},
+  {"label": "TERMINAL-BOARD-STATUSES", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+   "allowed_paths": ["src/alienintent/composition/", "src/alienintent/execution_coordination/adapters/",
+                     "tests/composition/", "tests/execution_coordination/"]},
+  {"label": "STORE-SCHEMA-HARDENING", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+   "allowed_paths": ["src/alienintent/composition/", "src/alienintent/execution_coordination/adapters/",
+                     "tests/composition/", "tests/execution_coordination/"]},
+  {"label": "AUTONOMY-PROOF", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+   "allowed_paths": ["docs/evidence/", "tests/", "tools/"]}]}
+```
+
 ## 2.3 One work identity and project-lifetime traceability
 
 Every work item and BIU keeps one immutable factory identity from materialization to its final outcome. Its durable record connects the exact origin, every definition version, applicable assessments and approvals, attempts, decisions, candidates, independent findings, external results and closure evidence. DONE, cancellation and cleanup do not erase that record; verified archival preserves its history for the duration of the project.
diff --git a/src/alienintent/composition/work_registry.py b/src/alienintent/composition/work_registry.py
index 08514b7..155748e 100644
--- a/src/alienintent/composition/work_registry.py
+++ b/src/alienintent/composition/work_registry.py
@@ -16,6 +16,10 @@ card's registered work record, and the view's attention items are kept in the `r
 With `readiness`, `work authorize` (`authorization`) records release records on that store under profile `registry`
 and its evidence in that folder; the starting revision is checked in the pointer repository's configured clone
 against its `default_branch`, the values the release gate for registry items is composed with. With `readiness`,
+`work approve-plan` (`plan_approval`) records the Founder's approval of one exact canonical-plan revision on that store
+and folder, and with the READY view `work release` (`release`) releases a plan-derived item under the current plan
+authority (PLAN-AUTHORITY-INHERITANCE); a launch applies actual-diff containment to its candidates before VERIFY and
+CLOSURE confirms it before landing. With `readiness`,
 `work record-completed` (`completion`) records an existing item's completed work: its evidence in that folder,
 landings checked the same way, and the `registry` coordinator's record read from that store. With the READY view,
 `coordinator(worker, artifacts)` composes the existing FactoryCoordinator over it on the `readiness` store (profile
@@ -90,7 +94,10 @@ from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS, wor
 from alienintent.composition.sandbox_profile import APP_KEY_REFERENCE
 from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
 from alienintent.context_assembly.application.initial_compilation_service import PacketLocation, WorkRegistration
+from alienintent.context_assembly.application.inherited_release import INHERITED_RELEASE, OWNER_DECISION_REQUIRED, \
+    InheritedRelease
 from alienintent.context_assembly.application.packet_assessment import PacketAssessment
+from alienintent.context_assembly.application.plan_approval import PlanApproval
 from alienintent.context_assembly.application.work_authorization import WorkAuthorization
 from alienintent.context_assembly.application.work_completion import WorkCompletion
 from alienintent.context_assembly.application.work_context import EXPORT_FILE, ContextCommand, WorkContext
@@ -126,7 +133,9 @@ from alienintent.execution_coordination.adapters.sqlite_store import PROJECTED,
 from alienintent.execution_coordination.application.factory_coordinator import NEVER_STARTED, FactoryCoordinator
 from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
 from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
+from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, PlanAuthority, outside_authority
 from alienintent.execution_coordination.domain.satisfiability import unsatisfiable
+from alienintent.execution_coordination.domain.scope_containment import NO_PLAN_AUTHORITY, SCOPE_VIOLATION, contained
 from alienintent.execution_coordination.domain.closure import (
     BOARD_UPDATED, LANDING_RECORD, MERGED_TO_MAIN, WORKSPACES_CLEANED, hold, is_fixed, parse_request, performable,
     ready_to_land, receipt, rework, session_finding)
@@ -147,7 +156,8 @@ from alienintent.installation.domain.project_identity import ProjectAddress
 from alienintent.installation.ports.github_transport import GitHubTransport
 from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider, kill_as_worker, run_as_worker, \
     worker_prefix
-from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl, IntakeSourceControl
+from alienintent.invocation_runtime.adapters.git_source_control import RAW_DIFF, GitSourceControl, \
+    IntakeSourceControl, raw_changes
 from alienintent.invocation_runtime.adapters.git_worktree import GitWorkspace, GitWorktreeAdapter, WorkerCloneAdapter, \
     ref_safe
 from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
@@ -469,10 +479,14 @@ class WorkRegistry:
         self.assessment = self._assessment(configuration) if configuration.readiness is not None else None
         self.authorization = self._authorization(configuration) if self.assessment is not None else None
         self.completion = self._completion(configuration) if self.assessment is not None else None
+        # `work approve-plan` and the current plan authority, on the `readiness` store beside the release records.
+        self.plan_approval = self._plan_approval(configuration) if self.assessment is not None else None
         self.links = self._links(configuration.github, transport) if configuration.github is not None else None
         self._diagnosed: set[tuple[object, ...]] = set()  # card projection failures already recorded, once each
         self.ready_view = self._ready_view(configuration) if self.links is not None and self.assessment is not None \
             else None
+        # `work release`: the control plane's release of plan-derived work, with the READY view's attention items.
+        self.release = self._release(configuration) if self.ready_view is not None else None
         # Each role's context package (unit 6c-1) over the `readiness` store and evidence folder; its command names
         # the configuration file, so a configuration not loaded from a file has none.
         self.context = _work_context(configuration, self.records, self.items, self.assessment.consumer) \
@@ -508,11 +522,12 @@ class WorkRegistry:
 
     def coordinator(self, worker: WorkerProvider, artifacts: LocalArtifactStore) -> FactoryCoordinator:
         """The existing FactoryCoordinator over the READY view on the `readiness` store under profile `registry`, with
-        the caller's worker and artifacts. Nothing is released automatically: a work item becomes eligible only through
-        `release_and_start`, and the release gate re-checks its release record against the packets repository's clone
-        and default branch (what `work authorize` checks) before every PRODUCER. The WIP limit is read on every
-        admission. Closure: `landing_enabled` is the `github` entry's `landing` flag, `started_item` builds a started
-        item from its registry record (0.9) and `completed` projects the row after DONE (0.8)."""
+        the caller's worker and artifacts. The release flag follows each contract (`_ContractRelease`): only an
+        `automatic-on` (plan-derived) item is released by policy; an `explicit-human-off` item becomes eligible only
+        through `release_and_start`. The release gate re-checks the release record (`work authorize`'s or `work
+        release`'s) against the packets repository's clone and default branch before every PRODUCER. The WIP limit is
+        read on every admission. Closure: `landing_enabled` is the `github` entry's `landing` flag, `started_item`
+        builds a started item from its registry record (0.9) and `completed` projects the row after DONE (0.8)."""
         if self.ready_view is None:
             raise ConfigurationInvalid("the coordinator needs both the github and readiness entries")
         configuration = self.configuration
@@ -520,8 +535,8 @@ class WorkRegistry:
         gate = ReleasePreconditionGate(StoredReleaseAuthorizations(store, "registry"),
                                        GitRevisionResolver({configuration.github.repository: packets.clone}),
                                        packets.default_branch)
-        return FactoryCoordinator(store, self.ready_view, worker, artifacts, "registry",
-                                  automatic_release=False, release_gate=gate,
+        return FactoryCoordinator(store, _ContractRelease(self.ready_view, self.plan_approval.current), worker, artifacts, "registry",
+                                  automatic_release=True, release_gate=gate,
                                   wip_limit=lambda: wip_limit(self.host_configuration),
                                   recorded_completion=self.completion.recorded,
                                   landing_enabled=lambda: configuration.github.landing,
@@ -547,7 +562,8 @@ class WorkRegistry:
                 return None
             return ReadyWorkItem(item.id, 0, self.configuration.github.repository, "registry", None,
                                  tuple(contract.dependencies), contract, contract.content_digest,
-                                 item.assessment_ref.logical_id, automatic_release=False)
+                                 item.assessment_ref.logical_id,
+                                 automatic_release=automatic(contract, self.plan_approval.current()))
         except Exception:  # noqa: BLE001 - an unusable registry record answers None, as recovery expects
             return None
 
@@ -830,7 +846,7 @@ class WorkRegistry:
             workspaces, ReservationBook(1, 2), now=time.time,
             sleep=time.sleep, journal=journal, ownership=ownership, preparation=preparation,
             recovered_workspace=recovered, closure=closure, handover=handover, regression_gate=gate,
-            regression_base=preparation.starting.get)
+            regression_base=preparation.starting.get, protected_paths=self.protected_paths)
         closure.worker = worker
         closure.worker_workspaces = None if user is None else workspaces
         guard = RoleBindingGuard(worker, journal, store, "registry", repository, time.time)
@@ -1048,9 +1064,63 @@ class WorkRegistry:
             return item is not None and not item.retired
 
         github = self.configuration.github
+        current = None if self.plan_approval is None else self.plan_approval.current()
         return unsatisfiable(contract, landing=github is not None and github.landing,
                              present_at_pointer=present_at_pointer, registered=registered,
-                             provider_dimensions=PROVIDER_DIMENSIONS)
+                             provider_dimensions=PROVIDER_DIMENSIONS,
+                             plan_authority=None if current is None
+                             else lambda contract: outside_authority(contract, current))
+
+    def protected_paths(self) -> tuple[str, ...] | None:
+        """The protected paths of the current approved plan authority, or None without one."""
+        current = None if self.plan_approval is None else self.plan_approval.current()
+        return None if current is None else current.scope.protected_paths
+
+    def _plan_approval(self, configuration: ProjectConfiguration) -> PlanApproval:
+        """`work approve-plan`: the canonical plan read at the commit from the packets repository's clone, the commit
+        checked against its default branch; the evidence in the assessment evidence folder, the plan-authority
+        aggregates on the `readiness` store under profile `registry`."""
+        consumer, name = self.assessment.consumer, configuration.packets_repository
+        packets = configuration.repositories[name]
+        return PlanApproval(consumer.repository, consumer.project, consumer.profile, consumer.store, "registry", name,
+                            GitRevisionResolver({name: packets.clone}), packets.default_branch,
+                            lambda commit: self.items.read_packet(StoredPointer(name, PLAN_PATH, commit)))
+
+    def _release(self, configuration: ProjectConfiguration) -> InheritedRelease:
+        """`work release`: what `work authorize` writes, on the same store and evidence folder, with the composed
+        satisfiability check and the current plan authority, the owner-decision attention item of `_owner_decision`
+        and the card written through `work link`, `work display` and the board's Status and Priority writes."""
+        consumer, repositories = self.assessment.consumer, configuration.repositories
+        return InheritedRelease(self.records, self.identities, consumer, consumer.repository, consumer.project,
+                                consumer.profile, self.assessment.authorizations,
+                                GitRevisionResolver({name: location.clone for name, location in repositories.items()}),
+                                {name: location.default_branch for name, location in repositories.items()},
+                                self._head, self.plan_approval.current, self.satisfiable, self._owner_decision,
+                                self.links)
+
+    def _head(self, repository: str) -> str | None:
+        """The default branch's current head in the repository's configured clone, or None."""
+        location = self.configuration.repositories.get(repository)
+        if location is None:
+            return None
+        result = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
+                                 f"refs/heads/{location.default_branch}^{{commit}}"],
+                                cwd=location.clone, capture_output=True, check=False, timeout=60)
+        head = result.stdout.decode(errors="replace").strip()
+        return head if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", head) else None
+
+    def _owner_decision(self, identity: str) -> None:
+        """The durable typed owner-decision requirement of a refused inherited release: one JUDGMENT attention item per
+        work item (owner OPERATOR until a Founder lane exists), its origin the same in every process."""
+        consumer = self.assessment.consumer
+        source = consumer.repository.put(Observation(
+            Header(consumer.repository.project, consumer.repository.profile,
+                   f"{INHERITED_RELEASE}/{OWNER_DECISION_REQUIRED}/{identity}", "1", (self._definition,)),
+            self._definition, INHERITED_RELEASE, INHERITED_RELEASE + "/v1", (),
+            canonical_bytes({"kind": OWNER_DECISION_REQUIRED, "work": identity}).decode(), None, INHERITED_RELEASE,
+            INHERITED_RELEASE))
+        self._attention.ensure(AttentionOrigin(identity, OWNER_DECISION_REQUIRED, "JUDGMENT", INHERITED_RELEASE,
+                                               INHERITED_RELEASE, OPERATOR, INHERITED_RELEASE, source))
 
     def _completion(self, configuration: ProjectConfiguration) -> WorkCompletion:
         """`work record-completed`: the evidence record in the assessment evidence folder, landings checked in each
@@ -1240,6 +1310,31 @@ NO_OPEN_DECISION, OWNER_STILL_RUNNING, START_UNPROVEN = "NO_OPEN_DECISION", "OWN
 REMOTE_UNVERIFIED, REMOTE_CONFLICT, CANDIDATE_PUBLISHED = "REMOTE_UNVERIFIED", "REMOTE_CONFLICT", "CANDIDATE_PUBLISHED"
 
 
+def automatic(contract: BiuContract, current: PlanAuthority | None) -> bool:
+    """A registry item is released by policy only while its own contract is plan-derived (`automatic-on`) and inside
+    the CURRENT approved plan authority: a later approval of another plan revision stops it."""
+    return contract.release_policy == "automatic-on" and current is not None \
+        and not outside_authority(contract, current)
+
+
+class _ContractRelease:
+    """The READY view as the registry coordinator reads it: each item's release flag follows its own contract and the
+    current plan authority (`automatic`, the authority read once per snapshot), so an `explicit-human-off` item, or
+    one released under a plan revision that is no longer current, is never released by policy. Everything else is
+    the view's."""
+
+    def __init__(self, view: GitHubProjectsWorkManagement, current: Callable[[], PlanAuthority | None]) -> None:
+        self._view, self._current = view, current
+
+    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]:
+        current = self._current()
+        return tuple(replace(item, automatic_release=automatic(item.contract, current))
+                     for item in self._view.import_ready_snapshot())
+
+    def __getattr__(self, name: str):
+        return getattr(self._view, name)
+
+
 class _DecisionOnly:
     """The registry coordinator as the DecisionInbox admission of `work decide`: validation and recording only."""
 
@@ -1547,10 +1642,46 @@ class RegistryClosure:
         clone = self._clone(invocation.correlation_id)
         return self._settle(invocation, candidate, clone, orders, retry=own, earlier=not own)
 
+    def _scope_violations(self, clone: Path, identity: str, base: str, revision: str) -> tuple[str, ...]:
+        """CLOSURE's confirmation of the same exact-candidate boundary the PRODUCER's containment checked, for an
+        `automatic-on` item: exactly what would land, the candidate's changes from the landing `base` (the default
+        branch's head it is merged onto, not its release baseline: a candidate that merged main could otherwise undo
+        a protected change main made after its release), read in this landing clone, against the registered
+        contract's `authorized_scope` and the current plan authority's protected paths. Release admission guards
+        only the PRODUCER, so this, the one landing gate, also requires the contract to be inside the CURRENT plan
+        authority (read once here): an item released under a plan revision that is no longer current holds with its
+        `owner-decision-required:` reasons and raises the owner-decision attention item. Anything unreadable is a
+        violation."""
+        try:
+            record = self._registry.records.show(identity)
+            contract = contract_block(record.packet, identity)
+            if contract.release_policy != "automatic-on":
+                return ()
+            current = self._registry.plan_approval.current()
+            if current is None:
+                return (NO_PLAN_AUTHORITY,)
+            outside = outside_authority(contract, current)
+            if outside:
+                self._registry._owner_decision(identity)
+                return outside
+            protected = current.scope.protected_paths
+            result = subprocess.run(["git", "-c", "credential.helper=", "-c", "core.hooksPath=/dev/null", *RAW_DIFF,
+                                     base, revision, "--"], cwd=clone, env=git_environment(clone),
+                                    capture_output=True, check=False, timeout=300)
+            if result.returncode:
+                return (f"{SCOPE_VIOLATION} the candidate's changes cannot be read",)
+            return contained(raw_changes(result.stdout.decode(errors="replace")), contract.authorized_scope, protected)
+        except Exception as error:  # noqa: BLE001 - an unreadable record or diff never lands
+            return (f"{SCOPE_VIOLATION} {type(error).__name__}",)
+
     # --- the landing ----------------------------------------------------------------------------------------------
 
     def _order(self, invocation, candidate, clone, base, attempt, actions, digest, findings):
         identity, revision = invocation.work_identity, candidate.locator.rpartition("@")[2]
+        # Every first order and every re-order at a new head: before the merge is built, journaled or landed.
+        violations = self._scope_violations(clone, identity, base, revision)
+        if violations:
+            return (), (*findings, hold("scope-violation", base, revision), *violations)
         built = self._build(clone, invocation, revision, base, actions, digest)
         if isinstance(built, str):
             return (), (*findings, hold(built, base, revision))
@@ -1595,7 +1726,10 @@ class RegistryClosure:
         if head == order["base"]:
             if self._authority is None:
                 return published, (ready_to_land(order["merge"]),)
-            if retry:
+            if retry:  # a re-land of the journaled order passes the same landing gate first
+                violations = self._scope_violations(clone, identity, order["base"], revision)
+                if violations:
+                    return published, (hold("scope-violation", order["base"], revision), *violations)
                 self._authority.land(self._landing_order(last, clone))
                 return self._settle(invocation, candidate, clone, orders, retry=False, earlier=False)
             return published, (hold("landing-refused", order["base"], order["merge"], order["record"]),)
diff --git a/src/alienintent/context_assembly/application/inherited_release.py b/src/alienintent/context_assembly/application/inherited_release.py
new file mode 100644
index 0000000..461dbdf
--- /dev/null
+++ b/src/alienintent/context_assembly/application/inherited_release.py
@@ -0,0 +1,176 @@
+"""InheritedRelease: the control plane's release of a plan-derived work item (`work release`, no quote).
+
+A work item inherits execution authority from the current approved plan authority only when it is at CAPTURE with a
+pointer and no release record, its retained assessment of that pointer is READY, its contract is `automatic-on`, and
+the composed satisfiability check with that authority gives no reasons. Otherwise it answers the named refusal and
+writes nothing; OWNER_DECISION_REQUIRED also ensures the one durable owner-decision attention item (`owner_decision`).
+Then, as `work authorize` does (its file is not changed): the evidence record with the same fields (approver the
+contract's `authority_issuer`, quote the plan approval record's revision digest), the release record (the commit
+point: create only, read back, its baseline the default branch's current head) and the row's `approval_ref`. Then
+the card: linked if the item has none (`work link`), its text written (`work display`), Status READY and Priority
+the obligation's written and each read back. A rerun after an unconfirmed card writes only the card.
+The release precondition gate is unchanged and re-checks the record before every PRODUCER.
+"""
+from __future__ import annotations
+
+from collections.abc import Callable, Mapping
+from dataclasses import asdict, dataclass
+from hashlib import sha256
+from typing import Protocol
+
+from alienintent.context_assembly.application.work_authorization import ReleaseRecords
+from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
+from alienintent.context_assembly.application.work_registration import WorkRecordService
+from alienintent.context_assembly.domain.packet_assessment import fingerprint
+from alienintent.context_assembly.domain.work_contract import CONTRACT_INVALID, ContractInvalid, contract_block
+from alienintent.context_assembly.domain.work_identity import CAPTURE
+from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref
+from alienintent.evidence_learning.domain.refs import Ref
+from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
+from alienintent.execution_coordination.domain.plan_authority import PlanAuthority, obligation_labels
+from alienintent.execution_coordination.domain.release import (
+    BaselineEvidence, ReleaseAuthorization, ReleasePreconditionRefused, admit_release_preconditions, release_wording)
+from alienintent.execution_coordination.ports.operational_store import VersionConflict
+from alienintent.execution_coordination.ports.readiness import AssessmentConsumer
+from alienintent.execution_coordination.ports.release_admission import RevisionResolver
+
+# Answers `work release` returns instead of writing (CARD_UNCONFIRMED after the release record is written).
+NOT_RELEASABLE, ASSESSMENT_MISSING, NOT_PLAN_DERIVED = "NOT_RELEASABLE", "ASSESSMENT_MISSING", "NOT_PLAN_DERIVED"
+OWNER_DECISION_REQUIRED, GATE_WOULD_REFUSE, CARD_UNCONFIRMED = \
+    "OWNER_DECISION_REQUIRED", "GATE_WOULD_REFUSE", "CARD_UNCONFIRMED"
+INHERITED_RELEASE = "inherited-release"
+INHERITED = "inherited from plan authority"
+
+
+class Board(Protocol):
+    def write_status(self, item_id: str, status: str, expected_revision: int) -> int: ...
+
+    def write_priority(self, item_id: str, priority: str, expected_revision: int) -> int: ...
+
+
+class Links(Protocol):
+    """`work link` and `work display`, and the board they write (bound by composition)."""
+    board: Board
+
+    def link(self, id_or_label: str, issue: int | None = None): ...
+
+    def display(self, id_or_label: str): ...
+
+
+@dataclass(frozen=True)
+class ReleaseResult:
+    """What `work release` answers. `answer` is None when the item is released and its card reads back READY with its
+    priority (`repeated` when the release record already was this release); otherwise the refusal code and `detail`."""
+    identity: str
+    answer: str | None = None
+    evidence_ref: dict | None = None
+    authorization: dict | None = None
+    card_id: str | None = None
+    priority: str | None = None
+    repeated: bool = False
+    detail: str = ""
+
+
+class InheritedRelease:
+    def __init__(self, records: WorkRecordService, identities: WorkIdentityService, consumer: AssessmentConsumer,
+                 evidence: EvidenceRepository, project: str, profile: str, releases: ReleaseRecords,
+                 revisions: RevisionResolver, release_points: Mapping[str, str], head: Callable[[str], str | None],
+                 authority: Callable[[], PlanAuthority | None],
+                 satisfiable: Callable[[bytes, str, str], tuple[str, ...]], owner_decision: Callable[[str], None],
+                 links: Links) -> None:
+        """`head(repository)` answers the default branch's current head in its configured clone; `authority` the
+        current plan authority; `satisfiable` the composed check with it; `owner_decision(identity)` ensures the
+        item's owner-decision attention item."""
+        self.records, self.identities, self.consumer, self.evidence = records, identities, consumer, evidence
+        self.releases, self.revisions, self.release_points, self.head = releases, revisions, dict(release_points), head
+        self.authority, self.satisfiable = authority, satisfiable
+        self.owner_decision, self.links = owner_decision, links
+        self.definition = Ref(project, profile, INHERITED_RELEASE + "/definition",
+                              "sha256:" + sha256(b"alienintent.context_assembly.application.inherited_release:"
+                                                 b"inherited-release").hexdigest(),
+                              "python:alienintent.context_assembly.application.inherited_release")
+
+    def release(self, id_or_label: str) -> ReleaseResult:
+        record = self.records.show(id_or_label)
+        item = None if record is None else record.item
+        if item is None or item.retired or item.state != CAPTURE or item.pointer is None:
+            return ReleaseResult(id_or_label if item is None else item.id, NOT_RELEASABLE, detail=(
+                "no work item" if item is None else "retired" if item.retired else f"state {item.state}"
+                if item.state != CAPTURE else "no packet pointer"))
+        existing = self.releases.release_authorization(item.id)
+        if existing is not None and not (existing.text.startswith(INHERITED) and item.approval_ref is not None
+                                         and existing.record_ref == item.approval_ref.revision_digest):
+            return ReleaseResult(item.id, NOT_RELEASABLE, detail="a release record exists")
+        history = self.consumer.history(item.id)
+        entry = next((a for a in history if item.assessment_ref is not None
+                      and a["raw_ref"] == asdict(item.assessment_ref)), None)
+        outcome = (entry or {}).get("outcome") or {}
+        if entry is None or entry["input_fingerprint"] != fingerprint(item.id, item.pointer) \
+                or outcome.get("failure_class") or outcome.get("disposition") != "READY":
+            return ReleaseResult(item.id, ASSESSMENT_MISSING, detail="no READY assessment of the current pointer")
+        try:
+            contract = contract_block(record.packet, item.id)
+        except ContractInvalid as error:
+            return ReleaseResult(item.id, CONTRACT_INVALID, detail=str(error))
+        if contract.release_policy != "automatic-on":
+            return ReleaseResult(item.id, NOT_PLAN_DERIVED, detail=f"release_policy {contract.release_policy}")
+        authority = self.authority()
+        reasons = ("no approved plan authority",) if authority is None \
+            else self.satisfiable(record.packet, item.pointer.commit, item.id)
+        if reasons:
+            self.owner_decision(item.id)
+            return ReleaseResult(item.id, OWNER_DECISION_REQUIRED, detail="; ".join(reasons))
+        priority = authority.scope.obligation(obligation_labels(contract)[0]).priority
+        if existing is not None:  # This release was recorded; only its card was unconfirmed.
+            return self._card(item.id, priority, ReleaseResult(item.id, None, asdict(item.approval_ref),
+                                                               asdict(existing), repeated=True))
+        repo = item.pointer.repo
+        release_point, baseline = self.release_points.get(repo), self.head(repo)
+        resolves = release_point is not None and baseline is not None and self.revisions.resolves(repo, baseline)
+        reachable = resolves and self.revisions.is_reachable(repo, baseline, release_point)
+        evidence = Observation(
+            Header(self.definition.project, self.definition.profile, f"{INHERITED_RELEASE}/{item.id}", "1",
+                   (self.definition,)),
+            self.definition, INHERITED_RELEASE, INHERITED_RELEASE + "/v1", (),
+            canonical_bytes({"identity": item.id,
+                             "pointer": {"repo": repo, "path": item.pointer.path, "commit": item.pointer.commit},
+                             "attempt_id": entry["attempt_id"], "assessment_ref": entry["raw_ref"],
+                             "contract_digest": contract.content_digest, "baseline": baseline,
+                             "approver": contract.authority_issuer, "quote": authority.record_ref}).decode(),
+            None, INHERITED_RELEASE, INHERITED_RELEASE)
+        reference = record_ref(evidence)
+        authorization = ReleaseAuthorization(item.id, reference.revision_digest, True, baseline,
+                                             f"{INHERITED} {authority.content_digest} ({authority.record_ref})")
+        try:  # The release gate's own check, over the wording it checks at launch (as `work authorize`).
+            admit_release_preconditions(item.id, authorization, BaselineEvidence(str(release_point), resolves,
+                                                                                 reachable),
+                                        release_wording(contract, item.assessment_ref.logical_id, {}))
+        except ReleasePreconditionRefused as refused:
+            return ReleaseResult(item.id, GATE_WOULD_REFUSE, detail=refused.check)
+        if self.evidence.put(evidence) != reference:
+            raise RuntimeError("the evidence repository answered another reference")
+        try:
+            self.releases.record(authorization)
+        except VersionConflict:  # Another run recorded first: nothing of this run is referenced.
+            return ReleaseResult(item.id, NOT_RELEASABLE, detail="a release record exists")
+        if self.releases.release_authorization(item.id) != authorization:
+            raise RuntimeError("the release record did not read back as written")
+        self.identities.set_evidence(item.id, "approval", reference)
+        return self._card(item.id, priority, ReleaseResult(item.id, None, asdict(reference), asdict(authorization)))
+
+    def _card(self, identity: str, priority: str, released: ReleaseResult) -> ReleaseResult:
+        """Link (when unlinked), display, then Status READY and the priority, each read back."""
+        try:
+            linked = self.links.link(identity)
+            shown = self.links.display(identity) if linked.answer is None else linked
+            if shown.answer is not None or linked.card_id is None:
+                raise RuntimeError(f"{shown.answer}: {shown.detail}")
+            card = linked.card_id
+            if self.links.board.write_status(card, "READY", 0) != 0 \
+                    or self.links.board.write_priority(card, priority, 0) != 0:
+                raise RuntimeError("the card did not read back READY with its priority")
+        except Exception as error:  # noqa: BLE001 - the release stands; a rerun writes only the card
+            return ReleaseResult(identity, CARD_UNCONFIRMED, released.evidence_ref, released.authorization,
+                                 priority=priority, detail=f"{type(error).__name__}: {error}")
+        return ReleaseResult(identity, None, released.evidence_ref, released.authorization, card, priority,
+                             released.repeated)
diff --git a/src/alienintent/context_assembly/application/plan_approval.py b/src/alienintent/context_assembly/application/plan_approval.py
new file mode 100644
index 0000000..2fc3b6a
--- /dev/null
+++ b/src/alienintent/context_assembly/application/plan_approval.py
@@ -0,0 +1,119 @@
+"""PlanApproval: record the Founder's approval of one exact canonical-plan revision (`work approve-plan`).
+
+The command records the Founder's approval; it does not grant it. It reads the canonical plan at the exact commit
+from the packets repository's clone, only when that commit is reachable from the default branch, and parses its one
+plan-authority block. One evidence record binds the plan path, the commit, the content digest (`sha256:` of the file's
+bytes), the parsed scope, the approver and the Founder's words; the store aggregate `plan-authority:<digest>` (create
+only) names that record, so the same bytes approved again are a repeat and write no second record. The aggregate
+`plan-authority:current`, written with the store's expected version, names the one current approval: each approval,
+a re-approval of an older digest included, makes its digest current. Nothing else is current, so an item issued under
+another digest fails the issuer rule and stops as owner-decision-required. Nothing here releases, launches or writes
+to GitHub.
+"""
+from __future__ import annotations
+
+from collections.abc import Callable
+from dataclasses import asdict, dataclass
+from hashlib import sha256
+import json
+import re
+
+from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref, \
+    ref_from_document
+from alienintent.evidence_learning.domain.refs import Ref
+from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
+from alienintent.execution_coordination.domain.plan_authority import (
+    PLAN_PATH, PlanAuthority, PlanScopeInvalid, parse_scope, scope_from)
+from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict
+from alienintent.execution_coordination.ports.release_admission import RevisionResolver
+
+# Answers `work approve-plan` returns instead of writing.
+PLAN_NOT_ON_MAIN, PLAN_SCOPE_INVALID = "PLAN_NOT_ON_MAIN", "PLAN_SCOPE_INVALID"
+PLAN_AUTHORITY, CURRENT = "plan-authority", "plan-authority:current"
+APPROVER = "Founder"
+COMMIT = re.compile(r"[0-9a-f]{40}")
+
+
+@dataclass(frozen=True)
+class PlanApprovalResult:
+    """What `work approve-plan` answers. `answer` is None when the approval is recorded and current (`repeated` when
+    these bytes were already approved); otherwise it is the refusal code and `detail` names which check refused."""
+    commit: str
+    answer: str | None = None
+    content_digest: str | None = None
+    evidence_ref: dict | None = None
+    repeated: bool = False
+    detail: str = ""
+
+
+class PlanApproval:
+    def __init__(self, evidence: EvidenceRepository, project: str, profile: str, store: OperationalStore,
+                 store_profile: str, repository: str, revisions: RevisionResolver, release_point: str,
+                 read: Callable[[str], bytes]) -> None:
+        """`read(commit)` answers the plan file's bytes at `commit` from the packets repository's clone;
+        `repository` and `release_point` are that clone's name and default branch."""
+        self.evidence, self.store, self.store_profile = evidence, store, store_profile
+        self.repository, self.revisions, self.release_point, self.read = repository, revisions, release_point, read
+        self.definition = Ref(project, profile, PLAN_AUTHORITY + "/definition",
+                              "sha256:" + sha256(b"alienintent.context_assembly.application.plan_approval:"
+                                                 b"plan-authority").hexdigest(),
+                              "python:alienintent.context_assembly.application.plan_approval")
+
+    def approve(self, commit: str, quote: str) -> PlanApprovalResult:
+        if not isinstance(quote, str) or not quote.strip():
+            raise ValueError("the Founder's exact words are required")
+        if COMMIT.fullmatch(commit or "") is None or not self.revisions.resolves(self.repository, commit) \
+                or not self.revisions.is_reachable(self.repository, commit, self.release_point):
+            return PlanApprovalResult(commit, PLAN_NOT_ON_MAIN, detail=f"not reachable from {self.release_point}")
+        try:
+            data = self.read(commit)
+            scope = parse_scope(data.decode("utf-8"))
+        except PlanScopeInvalid as error:
+            return PlanApprovalResult(commit, PLAN_SCOPE_INVALID, detail=str(error))
+        except Exception as error:  # noqa: BLE001 - a plan that cannot be read at the commit has no block to approve
+            return PlanApprovalResult(commit, PLAN_SCOPE_INVALID, detail=f"{type(error).__name__}: {error}")
+        digest = "sha256:" + sha256(data).hexdigest()
+        evidence = Observation(
+            Header(self.definition.project, self.definition.profile, f"{PLAN_AUTHORITY}/{digest}", "1",
+                   (self.definition,)),
+            self.definition, PLAN_AUTHORITY, PLAN_AUTHORITY + "/v1", (),
+            canonical_bytes({"plan_path": PLAN_PATH, "commit": commit, "content_digest": digest,
+                             "scope": scope.document(), "approver": APPROVER, "quote": quote}).decode(),
+            None, PLAN_AUTHORITY, PLAN_AUTHORITY)
+        aggregate = f"{PLAN_AUTHORITY}:{digest}"
+        _, existing = self.store.read_state(self.store_profile, aggregate)
+        if not existing:
+            reference = record_ref(evidence)
+            if self.evidence.put(evidence) != reference:
+                raise RuntimeError("the evidence repository answered another reference")
+            try:
+                self.store.commit(self.store_profile, aggregate, 0,
+                                  {"content_digest": digest, "record_ref": asdict(reference)})
+            except VersionConflict:  # Another run approved the same bytes first: its record stands.
+                pass
+            _, recorded = self.store.read_state(self.store_profile, aggregate)
+        else:
+            recorded = existing
+        if recorded.get("content_digest") != digest:
+            raise RuntimeError("the plan authority record did not read back as written")
+        version, current = self.store.read_state(self.store_profile, CURRENT)
+        if current.get("content_digest") != digest:
+            self.store.commit(self.store_profile, CURRENT, version, dict(recorded))
+        return PlanApprovalResult(commit, None, digest, dict(recorded["record_ref"]), bool(existing))
+
+    def current(self) -> PlanAuthority | None:
+        """The current approved plan authority, rebuilt from its evidence record; None when none is current or its
+        record cannot be read back exactly (no authority is inherited from an unreadable record)."""
+        _, current = self.store.read_state(self.store_profile, CURRENT)
+        if not current:
+            return None
+        try:
+            reference = ref_from_document(current["record_ref"])
+            values = json.loads(self.evidence.get(reference, frozenset({"private"})).value)
+            if values["content_digest"] != current["content_digest"]:
+                return None
+            return PlanAuthority(values["plan_path"], values["commit"], values["content_digest"],
+                                 reference.revision_digest, values["approver"], values["quote"],
+                                 scope_from(values["scope"]))
+        except Exception:  # noqa: BLE001 - an unreadable record is no authority
+            return None
diff --git a/src/alienintent/control_plane/adapters/cli.py b/src/alienintent/control_plane/adapters/cli.py
index 61a266d..9443307 100644
--- a/src/alienintent/control_plane/adapters/cli.py
+++ b/src/alienintent/control_plane/adapters/cli.py
@@ -12,10 +12,10 @@ from dataclasses import asdict, is_dataclass
 from typing import Any
 
 from alienintent.control_plane.application.operator import (
-    NOT_AVAILABLE_IN_WORKER_PROFILE, NOT_IN_EXPORT, OperatorControlPlane, OperatorDenied, assess_work, authorize_work,
-    context_work,
+    NOT_AVAILABLE_IN_WORKER_PROFILE, NOT_IN_EXPORT, OperatorControlPlane, OperatorDenied, approve_plan_work,
+    assess_work, authorize_work, context_work,
     decide_work, display_work, exclusive_launch_work, import_work, link_work, migrate_work, record_completed_work,
-    register_work, show_work)
+    register_work, release_work, show_work)
 from alienintent.execution_coordination.application.factory_coordinator import TerminalWork
 from alienintent.execution_coordination.domain.escalation import SupersededDecision
 from alienintent.execution_coordination.ports.operational_store import VersionConflict
@@ -110,6 +110,10 @@ def _parser() -> argparse.ArgumentParser:
     authorize = _sanitized(work.add_parser("authorize")); authorize.add_argument("target")
     for name in ("commit", "attempt", "baseline", "quote"):
         authorize.add_argument("--" + name, required=True)
+    approve_plan = _sanitized(work.add_parser("approve-plan"))
+    for name in ("commit", "quote"):
+        approve_plan.add_argument("--" + name, required=True)
+    release = _sanitized(work.add_parser("release")); release.add_argument("target")
     completed = _sanitized(work.add_parser("record-completed")); completed.add_argument("target")
     for name in ("candidate", "landing", "record", "approval", "quote"):
         completed.add_argument("--" + name, required=True)
@@ -240,6 +244,18 @@ def main(argv: list[str] | None = None) -> int:
                 _render(authorize_work(registry.authorization, args.target, args.commit, args.attempt, args.baseline,
                                        args.quote), args.json)
                 return 0
+            if args.work_command == "approve-plan":
+                if getattr(registry, "plan_approval", None) is None:
+                    _render({"error": "readiness-not-configured"}, args.json)
+                    return 1
+                _render(approve_plan_work(registry.plan_approval, args.commit, args.quote), args.json)
+                return 0
+            if args.work_command == "release":
+                if getattr(registry, "release", None) is None:
+                    _render({"error": "readiness-not-configured"}, args.json)
+                    return 1
+                _render(release_work(registry.release, args.target), args.json)
+                return 0
             if args.work_command == "record-completed":
                 if getattr(registry, "completion", None) is None:
                     _render({"error": "readiness-not-configured"}, args.json)
diff --git a/src/alienintent/control_plane/application/operator.py b/src/alienintent/control_plane/application/operator.py
index df2706d..6a8eaa4 100644
--- a/src/alienintent/control_plane/application/operator.py
+++ b/src/alienintent/control_plane/application/operator.py
@@ -108,6 +108,31 @@ def authorize_work(authorization: WorkAuthorizations, id_or_label: str, commit:
     return asdict(authorization.authorize(id_or_label, commit, attempt, baseline, quote))
 
 
+class PlanApprovals(Protocol):
+    """The project's plan approval as `work approve-plan` uses it (bound by the profile's composition)."""
+
+    def approve(self, commit: str, quote: str) -> Any: ...
+
+
+def approve_plan_work(approval: PlanApprovals, commit: str, quote: str) -> dict[str, object]:
+    """`work approve-plan`: the approved plan revision's digest and evidence reference, now the current plan
+    authority, or a refusal returned as the read answer naming its code. It records the Founder's approval of one exact
+    plan revision; it does not grant it."""
+    return asdict(approval.approve(commit, quote))
+
+
+class InheritedReleases(Protocol):
+    """The project's inherited release as `work release` uses it (bound by the profile's composition)."""
+
+    def release(self, id_or_label: str) -> Any: ...
+
+
+def release_work(release: InheritedReleases, id_or_label: str) -> dict[str, object]:
+    """`work release`: the plan-derived item's evidence reference, release record and card, or a refusal returned as
+    the read answer naming its code. No Founder words: the authority is the current approved plan's."""
+    return asdict(release.release(id_or_label))
+
+
 class WorkCompletions(Protocol):
     """The project's completed-work recording as `work record-completed` uses it (bound by the profile's
     composition)."""
diff --git a/src/alienintent/execution_coordination/adapters/github_projects_v2.py b/src/alienintent/execution_coordination/adapters/github_projects_v2.py
index e0ca21c..954731b 100644
--- a/src/alienintent/execution_coordination/adapters/github_projects_v2.py
+++ b/src/alienintent/execution_coordination/adapters/github_projects_v2.py
@@ -143,6 +143,21 @@ class GitHubProjectsV2Directory(ProjectDirectory):
         self._resolve(written["projectV2Item"].get("project"))
         return expected_revision if self.read_status(item_id).status == status else -1
 
+    def write_priority(self, item_id: str, priority: str, expected_revision: int) -> int:
+        """Set the card's Priority, confirmed by independent read-back exactly as `write_status` confirms Status."""
+        option = self.schema().priority_options.get(priority)
+        if option is None:
+            raise ProjectRejected("priority has no configured Priority option")
+        answer = self._graphql(_WRITE_MUTATION, {
+            "project": self._address.project_id, "item": item_id,
+            "field": self._address.field_for("Priority"), "option": option,
+        })
+        written = answer.get("updateProjectV2ItemFieldValue")
+        if not isinstance(written, Mapping) or not isinstance(written.get("projectV2Item"), Mapping):
+            raise ProjectUnavailable("Project refused the priority write")
+        self._resolve(written["projectV2Item"].get("project"))
+        return expected_revision if self.read_status(item_id).priority == priority else -1
+
     # --- transient probe subject --------------------------------------------
 
     def add_draft_item(self, title: str, body: str = "") -> str:
diff --git a/src/alienintent/execution_coordination/application/factory_coordinator.py b/src/alienintent/execution_coordination/application/factory_coordinator.py
index 4b5d2ab..b12095e 100644
--- a/src/alienintent/execution_coordination/application/factory_coordinator.py
+++ b/src/alienintent/execution_coordination/application/factory_coordinator.py
@@ -20,7 +20,7 @@ from alienintent.execution_coordination.domain.verdict import EvidenceDefinition
 from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected, VersionConflict
 from alienintent.execution_coordination.ports.release_admission import ExecutionAllocation
 from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
-from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, NO_CHANGE, PRODUCER, VERIFIER, VERIFIER_INFRASTRUCTURE, WorkerInvocation, WorkerOutcome, WorkerProvider
+from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, NO_CHANGE, PRODUCER, SCOPE_VIOLATION, VERIFIER, VERIFIER_INFRASTRUCTURE, WorkerInvocation, WorkerOutcome, WorkerProvider
 from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth
 
 # K2: each nonterminal stage is advanced by exactly one canonical role.
@@ -503,7 +503,7 @@ class FactoryCoordinator:
             # own role on the same custodied candidate, bounded at launch.
             return _Advance(current, outcome.kind, {})
         if invocation.role == PRODUCER:
-            if outcome.kind == NO_CHANGE:
+            if outcome.kind in {NO_CHANGE, SCOPE_VIOLATION}:
                 return self._rework(item, current, prior, invocation, "producer", tuple(outcome.findings))
             if outcome.kind != "success" or outcome.candidate is None:
                 return _Advance(current, outcome.kind, {})
diff --git a/src/alienintent/execution_coordination/domain/plan_authority.py b/src/alienintent/execution_coordination/domain/plan_authority.py
new file mode 100644
index 0000000..890ab08
--- /dev/null
+++ b/src/alienintent/execution_coordination/domain/plan_authority.py
@@ -0,0 +1,209 @@
+"""Plan authority: the scope an approved canonical-plan revision grants to the Work Items derived from it. Pure.
+
+The canonical plan holds exactly one block fenced as ```json alienintent-plan-authority: the target repositories,
+capabilities and budget caps derived work may use, the protected paths no derived work may touch, and the obligations,
+each with its priority, the requirement ids it satisfies and the paths it may change. The block is part of the plan's
+bytes, so the approved content digest covers every limit. A plan-derived contract has `release_policy` automatic-on,
+`authority_issuer` `plan-authority:<content digest>` and exactly one `authority_references` entry
+`<plan path> obligation:<LABEL>`; `outside_authority` answers one `owner-decision-required:` reason per rule it fails.
+Paths are compared normalized: relative POSIX, no `.`/`..`/empty part, no leading `/`, no `\\`, no glob character,
+any trailing `/` removed; scope paths in their exact case, both sides of a comparison with a protected path
+case-folded. `A` is under `B` when they are equal or `A` starts with `B/`.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+import json
+
+from alienintent.execution_coordination.domain.contract import BiuContract
+
+PLAN_PATH = "docs/decisions/alienintent-v2-canonical-project-plan.md"
+ISSUER_PREFIX = "plan-authority:"
+OPEN, CLOSE = "```json alienintent-plan-authority", "```"
+OBLIGATION = "obligation:"
+OWNER_DECISION = "owner-decision-required: "
+SCOPE_KEYS = frozenset({"target_repositories", "capabilities", "budget_caps", "protected_paths", "obligations"})
+CAP_KEYS = frozenset({"maximum_attempts", "hard_wall_clock_seconds", "cancellation_limit", "retry_limit",
+                      "concurrency_limit", "hard_required_dimensions"})
+OBLIGATION_KEYS = frozenset({"label", "priority", "satisfied_requirement_ids", "allowed_paths"})
+# The budget fields capped by the plan, in the order their reasons are named.
+CAPPED = ("maximum_attempts", "hard_wall_clock_seconds", "cancellation_limit", "retry_limit", "concurrency_limit")
+
+
+class PlanScopeInvalid(ValueError):
+    """The plan holds no, more than one, or a malformed plan-authority block."""
+
+
+@dataclass(frozen=True)
+class Obligation:
+    label: str
+    priority: str
+    satisfied_requirement_ids: tuple[str, ...]
+    allowed_paths: tuple[str, ...]
+
+
+@dataclass(frozen=True)
+class PlanScope:
+    target_repositories: tuple[str, ...]
+    capabilities: tuple[str, ...]
+    budget_caps: tuple[tuple[str, object], ...]  # (name, cap) in CAP_KEYS order; hard_required_dimensions a tuple
+    protected_paths: tuple[str, ...]
+    obligations: tuple[Obligation, ...]
+
+    def cap(self, name: str) -> object:
+        return dict(self.budget_caps)[name]
+
+    def obligation(self, label: str) -> Obligation | None:
+        return next((obligation for obligation in self.obligations if obligation.label == label), None)
+
+    def document(self) -> dict[str, object]:
+        """The block's JSON value, as `scope_from` reads it back."""
+        return {"target_repositories": list(self.target_repositories), "capabilities": list(self.capabilities),
+                "budget_caps": {name: list(value) if isinstance(value, tuple) else value
+                                for name, value in self.budget_caps},
+                "protected_paths": list(self.protected_paths),
+                "obligations": [{"label": o.label, "priority": o.priority,
+                                 "satisfied_requirement_ids": list(o.satisfied_requirement_ids),
+                                 "allowed_paths": list(o.allowed_paths)} for o in self.obligations]}
+
+
+@dataclass(frozen=True)
+class PlanAuthority:
+    """One approved plan revision: `content_digest` is `sha256:` of the plan file's bytes at `commit`; `record_ref`
+    the approval's evidence reference (its revision digest)."""
+    plan_path: str
+    commit: str
+    content_digest: str
+    record_ref: str
+    approver: str
+    quote: str
+    scope: PlanScope
+
+
+def normalized(path: object, fold: bool = False) -> str | None:
+    """The comparable form of a path, or None when it is malformed: exact case for scope (a candidate's paths must lie in
+    the exact assessed scope), case-folded (`fold`) on both sides of any comparison with a protected path."""
+    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or any(c in path for c in "*?["):
+        return None
+    stripped = path[:-1] if path.endswith("/") else path
+    parts = stripped.split("/")
+    if any(part in {"", ".", ".."} for part in parts):
+        return None
+    return stripped.casefold() if fold else stripped
+
+
+def under(path: str, ancestor: str) -> bool:
+    """`path` equals `ancestor` or lies beneath it; both already normalized."""
+    return path == ancestor or path.startswith(ancestor + "/")
+
+
+def parse_scope(text: str) -> PlanScope:
+    """The plan's one plan-authority block; PlanScopeInvalid unless exactly one well-formed block is present."""
+    lines = text.split("\n")
+    opens = [index for index, line in enumerate(lines) if line == OPEN]
+    if len(opens) != 1:
+        raise PlanScopeInvalid("no plan-authority block" if not opens else "more than one plan-authority block")
+    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
+    if close is None:
+        raise PlanScopeInvalid("the plan-authority block is not closed")
+    try:
+        document = json.loads("\n".join(lines[opens[0] + 1:close]))
+    except ValueError as error:
+        raise PlanScopeInvalid(f"the plan-authority block is not JSON: {error}") from None
+    return scope_from(document)
+
+
+def _strings(value: object, name: str, *, paths: bool = False) -> tuple[str, ...]:
+    if not isinstance(value, list) or not value or not all(isinstance(entry, str) and entry for entry in value) \
+            or len(set(value)) != len(value) or (paths and any(normalized(entry) is None for entry in value)):
+        kind = "well-formed paths" if paths else "strings"
+        raise PlanScopeInvalid(f"{name} must be a non-empty list of distinct {kind}")
+    return tuple(value)
+
+
+def scope_from(document: object) -> PlanScope:
+    """A PlanScope from the block's JSON value, with exactly the keys of the block."""
+    if not isinstance(document, dict) or set(document) != SCOPE_KEYS:
+        raise PlanScopeInvalid(f"the block needs exactly the keys {', '.join(sorted(SCOPE_KEYS))}")
+    caps = document["budget_caps"]
+    if not isinstance(caps, dict) or set(caps) != CAP_KEYS \
+            or not all(type(caps[name]) is int and caps[name] >= 1 for name in CAPPED):
+        raise PlanScopeInvalid(f"budget_caps needs exactly {', '.join(sorted(CAP_KEYS))}, each cap a positive integer")
+    dimensions = _strings(caps["hard_required_dimensions"], "hard_required_dimensions")
+    listed = document["obligations"]
+    if not isinstance(listed, list) or not listed:
+        raise PlanScopeInvalid("obligations must be a non-empty list")
+    obligations = []
+    for entry in listed:
+        if not isinstance(entry, dict) or set(entry) != OBLIGATION_KEYS or not isinstance(entry["label"], str) \
+                or not entry["label"] or not isinstance(entry["priority"], str) or not entry["priority"]:
+            raise PlanScopeInvalid(f"each obligation needs exactly {', '.join(sorted(OBLIGATION_KEYS))}")
+        obligations.append(Obligation(entry["label"], entry["priority"],
+                                      _strings(entry["satisfied_requirement_ids"], "satisfied_requirement_ids"),
+                                      _strings(entry["allowed_paths"], "allowed_paths", paths=True)))
+    if len({obligation.label for obligation in obligations}) != len(obligations):
+        raise PlanScopeInvalid("obligation labels must be distinct")
+    return PlanScope(_strings(document["target_repositories"], "target_repositories"),
+                     _strings(document["capabilities"], "capabilities"),
+                     tuple((name, dimensions if name == "hard_required_dimensions" else caps[name])
+                           for name in (*CAPPED, "hard_required_dimensions")),
+                     _strings(document["protected_paths"], "protected_paths", paths=True), tuple(obligations))
+
+
+def obligation_labels(contract: BiuContract) -> tuple[str, ...]:
+    """The labels of every `<plan path> obligation:<LABEL>` entry of the contract's authority references."""
+    labels = []
+    for entry in contract.authority_references:
+        words = entry.split()
+        if len(words) == 2 and words[0] == PLAN_PATH and words[1].startswith(OBLIGATION):
+            labels.append(words[1][len(OBLIGATION):])
+    return tuple(labels)
+
+
+def outside_authority(contract: BiuContract, authority: PlanAuthority) -> tuple[str, ...]:
+    """One `owner-decision-required:` reason per failing rule, in rule order; empty when the contract inherits the
+    authority, its priority then the obligation's."""
+    scope, reasons = authority.scope, []
+    if contract.authority_issuer != ISSUER_PREFIX + authority.content_digest:
+        reasons.append(f"authority_issuer: not the approved plan authority {ISSUER_PREFIX}{authority.content_digest}")
+    labels = obligation_labels(contract)
+    obligation = scope.obligation(labels[0]) if len(labels) == 1 else None
+    if len(labels) != 1:
+        reasons.append(f"authority_references: exactly one '{PLAN_PATH} {OBLIGATION}<LABEL>' entry is required")
+    elif obligation is None:
+        reasons.append(f"authority_references: obligation {labels[0]} is not in the approved plan")
+    foreign = sorted(set(contract.target_repositories) - set(scope.target_repositories))
+    if foreign:
+        reasons.append(f"target_repositories: outside the plan: {', '.join(foreign)}")
+    capabilities = sorted(set(contract.required_capabilities) - set(scope.capabilities))
+    if capabilities:
+        reasons.append(f"required_capabilities: outside the plan: {', '.join(capabilities)}")
+    if obligation is not None:
+        requirements = sorted(set(contract.satisfied_requirement_ids) - set(obligation.satisfied_requirement_ids))
+        if requirements:
+            reasons.append(f"satisfied_requirement_ids: outside obligation {obligation.label}: "
+                           f"{', '.join(requirements)}")
+    budget, details = contract.budget_policy, []
+    for name in CAPPED:
+        value = getattr(budget, name)
+        if value is None and name in ("hard_wall_clock_seconds", "cancellation_limit"):
+            details.append(f"{name} is required")
+        elif value is not None and value > scope.cap(name):
+            details.append(f"{name} {value} above the cap {scope.cap(name)}")
+    dimensions = set(budget.hard_required_dimensions) - set(scope.cap("hard_required_dimensions"))
+    details.extend(f"dimension {name} outside the cap list" for name in sorted(dimensions))
+    if details:
+        reasons.append(f"budget_policy: {', '.join(details)}")
+    entries = [(entry, normalized(entry)) for entry in contract.authorized_scope]
+    if obligation is not None:
+        allowed = [normalized(path) for path in obligation.allowed_paths]
+        refused = [f"{entry} is malformed" if path is None else f"{entry} is outside obligation {obligation.label}"
+                   for entry, path in entries if path is None or not any(under(path, a) for a in allowed)]
+        if refused:
+            reasons.append(f"authorized_scope: {'; '.join(refused)}")
+    protected = [normalized(path, fold=True) for path in scope.protected_paths]
+    crossing = [entry for entry, path in entries if path is not None
+                and any(under(path.casefold(), p) or under(p, path.casefold()) for p in protected)]
+    if crossing:
+        reasons.append(f"authorized_scope: crosses a protected path: {', '.join(crossing)}")
+    return tuple(OWNER_DECISION + reason for reason in reasons)
diff --git a/src/alienintent/execution_coordination/domain/satisfiability.py b/src/alienintent/execution_coordination/domain/satisfiability.py
index 56abbf3..9c79172 100644
--- a/src/alienintent/execution_coordination/domain/satisfiability.py
+++ b/src/alienintent/execution_coordination/domain/satisfiability.py
@@ -14,13 +14,20 @@ BASE_CAPABILITIES = frozenset({"python", "filesystem", "process-control"})
 
 
 def unsatisfiable(contract: BiuContract, *, landing: bool, present_at_pointer: Callable[[str], bool],
-                  registered: Callable[[str], bool], provider_dimensions: frozenset[str]) -> tuple[str, ...]:
-    """Return one reason per failing deterministic lifecycle rule, in gate order."""
+                  registered: Callable[[str], bool], provider_dimensions: frozenset[str],
+                  plan_authority: Callable[[BiuContract], tuple[str, ...]] | None = None) -> tuple[str, ...]:
+    """Return one reason per failing deterministic lifecycle rule, in gate order. `automatic-on` passes only through
+    `plan_authority` (the current approved plan authority's `outside_authority`), adding its reasons."""
     reasons: list[str] = []
     unknown_evidence = sorted(set(contract.required_evidence) - OBSERVABLE_EVIDENCE)
     if unknown_evidence:
         reasons.append(f"required_evidence: unobservable evidence ids: {', '.join(unknown_evidence)}")
-    if contract.release_policy != "explicit-human-off":
+    if contract.release_policy == "automatic-on":
+        if plan_authority is None:
+            reasons.append("release_policy: automatic-on requires an approved plan authority")
+        else:
+            reasons.extend(plan_authority(contract))
+    elif contract.release_policy != "explicit-human-off":
         reasons.append("release_policy: registry releases require explicit-human-off")
     unavailable = sorted(set(contract.required_capabilities) - BASE_CAPABILITIES)
     if unavailable:
diff --git a/src/alienintent/execution_coordination/domain/scope_containment.py b/src/alienintent/execution_coordination/domain/scope_containment.py
new file mode 100644
index 0000000..754a82f
--- /dev/null
+++ b/src/alienintent/execution_coordination/domain/scope_containment.py
@@ -0,0 +1,47 @@
+"""Actual-diff containment of a plan-derived candidate (Founder decision 6, 2026-10-08). Pure.
+
+A plan-derived candidate may advance only when every path it actually changed is under its assessed
+`authorized_scope` and none touches a protected path of the approved plan authority. `changes` are the
+`(mode, path)` pairs of `git diff --raw --no-renames <start> <candidate>` as the control plane reads them (the new
+mode of an added or modified path, the old mode of a deleted one); paths are compared with the same normalization as
+`plan_authority`: exact case against the scope, case-folded against protected paths. One `scope-violation:` reason
+per violation; an empty tuple means contained.
+"""
+from __future__ import annotations
+
+from collections.abc import Iterable
+
+from alienintent.execution_coordination.domain.plan_authority import normalized, under
+
+SCOPE_VIOLATION = "scope-violation:"
+# The refusal of an automatic-on candidate when no approved plan authority names its protected paths.
+NO_PLAN_AUTHORITY = SCOPE_VIOLATION + "no-plan-authority"
+# The refusal of an automatic-on candidate when the control plane holds no exact starting revision to diff from.
+NO_TRUSTED_START = SCOPE_VIOLATION + "no-trusted-start"
+# Modes a candidate may never introduce, keep or remove: a symbolic link and a submodule (gitlink).
+FORBIDDEN_MODES = {"120000": "a symbolic link", "160000": "a submodule"}
+# Interpreter start-up hooks the suite or a tool would execute wherever they sit, and pytest's per-folder hook file,
+# which the regression gate's suite run would execute.
+STARTUP_NAME, STARTUP_SUFFIX, CONFTEST = "sitecustomize.py", ".pth", "conftest.py"
+
+
+def contained(changes: Iterable[tuple[str, str]], authorized_scope: Iterable[str],
+              protected_paths: Iterable[str]) -> tuple[str, ...]:
+    """One `scope-violation:` reason per violation of every changed path, in change order."""
+    allowed = [path for path in (normalized(entry) for entry in authorized_scope) if path is not None]
+    protected = [path for path in (normalized(entry, fold=True) for entry in protected_paths) if path is not None]
+    reasons: list[str] = []
+    for mode, path in changes:
+        compared = normalized(path)
+        if compared is None or not any(under(compared, entry) for entry in allowed):
+            reasons.append(f"{SCOPE_VIOLATION} {path} is outside the authorized scope")
+        if compared is not None and any(under(compared.casefold(), entry) for entry in protected):
+            reasons.append(f"{SCOPE_VIOLATION} {path} is a protected path")
+        if mode in FORBIDDEN_MODES:
+            reasons.append(f"{SCOPE_VIOLATION} {path} is {FORBIDDEN_MODES[mode]} (mode {mode})")
+        name = path.rpartition("/")[2].casefold()
+        if name == STARTUP_NAME or name.endswith(STARTUP_SUFFIX):
+            reasons.append(f"{SCOPE_VIOLATION} {path} is an interpreter start-up file")
+        if name == CONFTEST:
+            reasons.append(f"{SCOPE_VIOLATION} {path} is a pytest conftest file")
+    return tuple(reasons)
diff --git a/src/alienintent/execution_coordination/ports/worker_provider.py b/src/alienintent/execution_coordination/ports/worker_provider.py
index d2de130..a05e659 100644
--- a/src/alienintent/execution_coordination/ports/worker_provider.py
+++ b/src/alienintent/execution_coordination/ports/worker_provider.py
@@ -16,6 +16,9 @@ PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"
 # re-dispatched once under the composed replacement allowance.
 MISSING_TERMINAL_RESULT = "missing-terminal-result"
 NO_CHANGE = "no-change"
+# A plan-derived PRODUCER candidate whose actual diff leaves its assessed scope or touches a protected path: nothing
+# was published, and the coordinator reworks it exactly like NO_CHANGE, using no VERIFIER attempt.
+SCOPE_VIOLATION = "scope-violation"
 # VERIFIER outcomes that carry no engineering judgment: the session ended without a valid verdict (its process failed
 # or timed out, or it left no verdict, a malformed one or one for another revision), or the feature-regression
 # receipt is absent or invalid (`feature-regressions-missing`: the REGRESSION-GATE produced no whole-suite result, or,
diff --git a/src/alienintent/invocation_runtime/adapters/git_source_control.py b/src/alienintent/invocation_runtime/adapters/git_source_control.py
index 4fc388b..e7ea020 100644
--- a/src/alienintent/invocation_runtime/adapters/git_source_control.py
+++ b/src/alienintent/invocation_runtime/adapters/git_source_control.py
@@ -28,6 +28,27 @@ _DISCOVERY = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "G
               "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS")
 
 
+# The one diff form actual-diff containment reads: every changed path with its mode, NUL-separated, no rename pairing.
+RAW_DIFF = ("diff", "--raw", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", "--abbrev=40")
+
+
+def raw_changes(output: str) -> tuple[tuple[str, str], ...]:
+    """`(mode, path)` of each entry of `git diff --raw -z --no-renames`: the new mode of an added or modified path,
+    the old mode of a deleted one. Anything else is CandidateUnavailable."""
+    fields = output.split("\0")
+    if fields and fields[-1] == "":
+        fields.pop()
+    if len(fields) % 2:
+        raise CandidateUnavailable("unreadable raw diff")
+    changes = []
+    for header, path in zip(fields[0::2], fields[1::2]):
+        parts = header.lstrip(":").split()
+        if not header.startswith(":") or len(parts) != 5 or not path:
+            raise CandidateUnavailable("unreadable raw diff")
+        changes.append((parts[0] if parts[4] == "D" else parts[1], path))
+    return tuple(changes)
+
+
 def open_worker_file(path: Path, owner_uid: int) -> int:
     """An open descriptor of `path`, a regular file owned by `owner_uid` (checked by `fstat` on the descriptor), or
     OSError. The caller reads only from this descriptor and closes it."""
@@ -81,6 +102,16 @@ class GitSourceControl(SourceControl):
     def tree(self, workspace: Path, revision: str) -> str:
         return self._git("rev-parse", "--verify", f"{revision}^{{tree}}", cwd=workspace)
 
+    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]:
+        """Every path the candidate changed from `starting`, with its mode (`raw_changes`), read in the workspace."""
+        if not _FULL_SHA.fullmatch(starting) or not _FULL_SHA.fullmatch(revision):
+            raise CandidateUnavailable("candidate or starting revision is not a full SHA")
+        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *RAW_DIFF, starting, revision, "--"],
+                                cwd=workspace, capture_output=True, check=False)
+        if result.returncode:
+            raise CandidateUnavailable("git operation failed")
+        return raw_changes(result.stdout.decode(errors="replace"))
+
     def read_back_candidate(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
         remote_url = self._git("remote", "get-url", remote, cwd=workspace)
         return self._read_back(remote_url, branch, revision, verifier_workspace, workspace)
@@ -274,6 +305,16 @@ class IntakeSourceControl(GitSourceControl, SourceControl):
             raise CandidateUnavailable("candidate tree is not immutable")
         return tree
 
+    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]:
+        """Every path the imported candidate changed from `starting` (`raw_changes`), read in the intake repository
+        only, after `hand_over`; the worker's workspace is never read."""
+        if not _FULL_SHA.fullmatch(starting) or not _FULL_SHA.fullmatch(revision):
+            raise CandidateUnavailable("candidate or starting revision is not a full SHA")
+        result = self._intake_git(*RAW_DIFF, starting, revision, "--")
+        if result.returncode:
+            raise CandidateUnavailable("intake git operation failed")
+        return raw_changes(result.stdout.decode(errors="replace"))
+
     def intake_ref(self, correlation: str) -> str:
         return f"refs/intake/{ref_safe(correlation)}"
 
diff --git a/src/alienintent/invocation_runtime/application/real_worker.py b/src/alienintent/invocation_runtime/application/real_worker.py
index 7b79ae6..e027f94 100644
--- a/src/alienintent/invocation_runtime/application/real_worker.py
+++ b/src/alienintent/invocation_runtime/application/real_worker.py
@@ -15,8 +15,9 @@ from typing import Protocol
 
 from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
 from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
+from alienintent.execution_coordination.domain.scope_containment import NO_PLAN_AUTHORITY, NO_TRUSTED_START, contained
 from alienintent.execution_coordination.ports.worker_provider import (
-    MISSING_TERMINAL_RESULT, NO_CHANGE, WorkerInvocation, WorkerOutcome, WorkerProvider)
+    MISSING_TERMINAL_RESULT, NO_CHANGE, SCOPE_VIOLATION, WorkerInvocation, WorkerOutcome, WorkerProvider)
 from alienintent.invocation_runtime.application.regression_gate import RegressionGate, SuiteUnrunnable
 from alienintent.invocation_runtime.domain.diagnostics import cause
 from alienintent.invocation_runtime.domain.runtime import FEATURE_REGRESSION_RECEIPT_PATH, VERDICT_PATH, BudgetIneligible, BudgetRecord, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable, ProcessResult, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, owner_token, require_eligible, workspace_folder
@@ -221,6 +222,8 @@ class CandidateHandover(Protocol):
 
     def tree(self, workspace: Path, revision: str) -> str: ...
 
+    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]: ...
+
     def hand_over(self, correlation: str, workspace: Path, claimed: str, starting: str) -> str: ...
 
     def publish_intake(self, correlation: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
@@ -246,7 +249,7 @@ class ClosureActions(Protocol):
 
 
 class RealWorkerProvider(WorkerProvider):
-    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str | Callable[[WorkerInvocation], str], verifier_root: Path, grant: CapabilityGrant | Callable[[WorkerInvocation], CapabilityGrant], target: str, workspaces: WorkspaceManager | None, reservations: ReservationBook | None = None, *, now: Callable[[], float], sleep: Callable[[float], None], journal: InvocationJournal | None = None, ownership: ProcessOwnership | None = None, preparation: WorkerPreparation | None = None, recovered_workspace: Callable[[WorkerInvocation], Workspace | None] | None = None, closure: ClosureActions | None = None, handover: CandidateHandover | None = None, regression_gate: RegressionGate | None = None, regression_base: Callable[[str], str | None] | None = None) -> None:
+    def __init__(self, process: WorkerProcess, source_control: SourceControl, workspace: Path, remote: str, branch: str | Callable[[WorkerInvocation], str], verifier_root: Path, grant: CapabilityGrant | Callable[[WorkerInvocation], CapabilityGrant], target: str, workspaces: WorkspaceManager | None, reservations: ReservationBook | None = None, *, now: Callable[[], float], sleep: Callable[[float], None], journal: InvocationJournal | None = None, ownership: ProcessOwnership | None = None, preparation: WorkerPreparation | None = None, recovered_workspace: Callable[[WorkerInvocation], Workspace | None] | None = None, closure: ClosureActions | None = None, handover: CandidateHandover | None = None, regression_gate: RegressionGate | None = None, regression_base: Callable[[str], str | None] | None = None, protected_paths: Callable[[], tuple[str, ...] | None] | None = None) -> None:
         self._process, self._source, self._workspace = process, source_control, workspace
         self._remote, self._branch, self._verifier_root, self._grant, self._target, self._workspaces = remote, branch, verifier_root, grant, target, workspaces
         self._outcomes: dict[str, WorkerOutcome] = {}
@@ -271,6 +274,10 @@ class RealWorkerProvider(WorkerProvider):
         # REGRESSION-GATE: the control plane's whole-suite comparison before each VERIFIER session, against the
         # baseline `regression_base(invocation id)` (the release record's starting revision). None: unchanged.
         self._regression_gate, self._regression_base = regression_gate, regression_base
+        # Actual-diff containment of an automatic-on PRODUCER candidate, composed by a profile that releases
+        # plan-derived work: the protected paths of its current approved plan authority (answering None or nothing:
+        # no authority, so no automatic-on candidate is published). None: a profile with no plan authority.
+        self._protected_paths = protected_paths
 
     def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
         """Run one role invocation; with a journal, retain its attributable outcome durably first."""
@@ -576,17 +583,22 @@ class RealWorkerProvider(WorkerProvider):
                     outcome = WorkerOutcome(NO_CHANGE, None, findings=(
                         f"no-change-candidate:{revision}: the PRODUCER's revision has the starting revision's tree; IMPLEMENT requires a repository change",))
                 else:
-                    if self._journal is not None:
-                        self._journal.append({"event": PUBLICATION_STARTED, "correlation_id": invocation.correlation_id,
-                                              "work_identity": invocation.work_identity, "role": invocation.role, "revision": revision})
-                    if self._handover is not None:
+                    if self._handover is not None:  # imported first: containment reads only the control plane's copy
                         self._handover.hand_over(invocation.correlation_id, workspace.path, revision, starting_revision)
-                        candidate = self._handover.publish_intake(invocation.correlation_id, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                    violations = self._scope_violations(context, reader, workspace.path, starting_revision, revision)
+                    if violations:
+                        outcome = WorkerOutcome(SCOPE_VIOLATION, None, findings=violations)
                     else:
-                        candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
-                    if self._preparation is not None:
-                        self._preparation.published(invocation, candidate)
-                    outcome = WorkerOutcome.success(candidate)
+                        if self._journal is not None:
+                            self._journal.append({"event": PUBLICATION_STARTED, "correlation_id": invocation.correlation_id,
+                                                  "work_identity": invocation.work_identity, "role": invocation.role, "revision": revision})
+                        if self._handover is not None:
+                            candidate = self._handover.publish_intake(invocation.correlation_id, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                        else:
+                            candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                        if self._preparation is not None:
+                            self._preparation.published(invocation, candidate)
+                        outcome = WorkerOutcome.success(candidate)
         finally:
             if outcome.kind in {"success", "authority-block"}:
                 self._finished_workspaces[invocation.correlation_id] = workspace
@@ -601,6 +613,23 @@ class RealWorkerProvider(WorkerProvider):
         self._outcomes[invocation.correlation_id] = outcome
         return outcome
 
+    def _scope_violations(self, context: BiuContract | None, reader, workspace: Path, starting: str,
+                          revision: str) -> tuple[str, ...]:
+        """Actual-diff containment (Founder decision 6), for an `automatic-on` contract only: every path the candidate
+        changed from `starting`, the control plane's own starting revision (the release baseline the preparation
+        named, never one the worker reports), as the control plane reads it (the intake import with a worker user,
+        the workspace without one), must be under the coordinator's contract `authorized_scope` and outside the
+        current plan authority's protected paths. Without a plan authority or an exact starting revision every such
+        candidate is refused."""
+        if self._protected_paths is None or context is None or context.release_policy != "automatic-on":
+            return ()
+        protected = self._protected_paths()
+        if not protected:
+            return (NO_PLAN_AUTHORITY,)
+        if not _FULL_SHA.fullmatch(starting):
+            return (NO_TRUSTED_START,)
+        return contained(reader.changes(workspace, starting, revision), context.authorized_scope, protected)
+
     @property
     def journal(self) -> InvocationJournal | None:
         """The durable journal this provider writes and reads back, read-only."""
diff --git a/src/alienintent/invocation_runtime/ports/source_control.py b/src/alienintent/invocation_runtime/ports/source_control.py
index 632fc2a..8a18b01 100644
--- a/src/alienintent/invocation_runtime/ports/source_control.py
+++ b/src/alienintent/invocation_runtime/ports/source_control.py
@@ -40,6 +40,7 @@ class PublishRef:
 class SourceControl(Protocol):
     def revision(self, workspace: Path) -> str: ...
     def tree(self, workspace: Path, revision: str) -> str: ...
+    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]: ...
     def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
     def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef: ...
     def publish_refs(self, clone: Path, remote: str, refs: tuple[PublishRef, ...]) -> None: ...
diff --git a/tests/composition/test_work_registry.py b/tests/composition/test_work_registry.py
index f0eeba2..3942e1a 100644
--- a/tests/composition/test_work_registry.py
+++ b/tests/composition/test_work_registry.py
@@ -625,7 +625,7 @@ def test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store(b
     """The release gate reads the release record from the readiness store (profile `registry`) and checks the starting
     revision in the packets repository's clone against its default branch; WIP admission and the launch follow."""
     registry, coordinator, worker, summary, item = _registry_run(board, tmp_path, "RV-OK", record={})
-    assert (coordinator._profile, coordinator._automatic_release) == ("registry", False)
+    assert (coordinator._profile, coordinator._automatic_release) == ("registry", True)
     assert coordinator._store is registry.assessment.consumer.store and worker.dispatched == [item.id]
     state = coordinator.state(item.id)
     # contract_payload allows one attempt and requires evidence no verifier gives: REVIEW reworks into `failure`.
@@ -745,3 +745,139 @@ def test_the_launcher_needs_the_ready_view_and_a_configuration_file(board, tmp_p
     path.write_text(json.dumps(entry(tmp_path, readiness=readiness(tmp_path))))
     with pytest.raises(ConfigurationInvalid):
         WorkRegistry(load_project_configuration(path, PROJECT)).launcher()
+
+
+# --- PLAN-AUTHORITY-INHERITANCE: plan-derived work through the coordinator (check 6) ---------------------------------
+
+from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH  # noqa: E402
+from tests.context_assembly.test_work_contract import satisfiable_payload  # noqa: E402
+from tests.support.live_github import PRIORITY_OPTIONS, STATUS_OPTIONS  # noqa: E402
+
+PLAN_QUOTE = "I approve this exact plan revision."  # TEST DATA
+PLAN_SCOPE = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python", "filesystem",
+                                                                                    "process-control"],
+              "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
+                              "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
+              "protected_paths": ["docs/decisions/", "src/alienintent/execution_coordination/domain/release.py"],
+              "obligations": [{"label": "FIXTURE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+                               "allowed_paths": ["src/", "tests/", "launch-candidate.txt"]}]}
+
+
+def plan_text(scope: dict | None = None, note: str = "") -> bytes:
+    """A fixture canonical plan holding one plan-authority block (TEST DATA)."""
+    return (f"# Fixture plan{note}\n\n```json alienintent-plan-authority\n{json.dumps(scope or PLAN_SCOPE, indent=1)}"
+            "\n```\n").encode()
+
+
+class FieldBoard(Board):
+    """The READY-view board that also answers the schema read and keeps each card's Status and Priority as written
+    through `updateProjectV2ItemFieldValue`, read back through the card read."""
+
+    def _board(self, query: str, variables: dict) -> object:
+        project = {"id": SANDBOX_PROJECT, "number": 2}
+        if "fields(first:50)" in query:
+            return {"data": {"node": project | {"title": "board", "fields": {"nodes": [
+                {"id": STATUS_FIELD, "name": "Status", "options": STATUS_OPTIONS},
+                {"id": PRIORITY_FIELD, "name": "Priority", "options": PRIORITY_OPTIONS}]}}}}
+        if "updateProjectV2ItemFieldValue" in query:
+            name = "Status" if variables["field"] == STATUS_FIELD else "Priority"
+            options = STATUS_OPTIONS if name == "Status" else PRIORITY_OPTIONS
+            self.log.append(f"write-{name}")
+            self.fields.setdefault(variables["item"], {})[name] = next(
+                o["name"] for o in options if o["id"] == variables["option"])
+            return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": variables["item"],
+                                                                                 "project": project}}}}
+        answer = super()._board(query, variables)
+        node = (answer.get("data") or {}).get("node") if isinstance(answer, dict) else None
+        if "ProjectV2Item { id project" in query and isinstance(node, dict):
+            fields = self.fields.get(variables["item"], {})
+            node["fieldValues"] = {"nodes": [{"name": fields[name], "field": {"id": field, "name": name}}
+                                             for name, field in (("Status", STATUS_FIELD), ("Priority", PRIORITY_FIELD))
+                                             if fields.get(name)]}
+        return answer
+
+
+class PlanBoard(ReadyBoard):
+    """The READY-view fixture with landing enabled, its configuration in a file (so the registry has `work context`),
+    the composed satisfiability check on and a fixture canonical plan on `main` to approve."""
+
+    def __init__(self, root: Path) -> None:
+        super().__init__(root)
+        self.root, self.github = root, FieldBoard()
+        self.document["projects"][PROJECT]["github"]["landing"] = True
+        self.configuration_file = root / "project.json"
+        self.configuration_file.write_text(json.dumps(self.document))
+        self.registry = self.loaded()
+        self.links = self.registry.links
+
+    def loaded(self, host: Path | None = None) -> WorkRegistry:
+        """A registry as a command builds it in its own process: every check composed."""
+        return WorkRegistry(load_project_configuration(self.configuration_file, PROJECT), transport=self.github,
+                            suite_run=passing_suite, **({} if host is None else {"host_configuration": host}))
+
+    def approve(self, plan: bytes | None = None) -> str:
+        """Commit `plan` as the canonical plan on `main` and approve it; answers its content digest."""
+        commit = commit_file(self.clone, "main", PLAN_PATH, plan or plan_text())
+        result = self.registry.plan_approval.approve(commit, PLAN_QUOTE)
+        assert result.answer is None, result
+        return result.content_digest
+
+    def derived(self, label: str, digest: str, **changes):
+        """A plan-derived item naming the FIXTURE obligation, assessed READY and not linked to any card."""
+        return self.ready(label, at="2026-10-09T10:00:00Z", link=False, payload=lambda item: satisfiable_payload(
+            item.id, **({"release_policy": "automatic-on", "authority_issuer": "plan-authority:" + digest,
+                         "authority_references": [f"{PLAN_PATH} obligation:FIXTURE"],
+                         "authorized_scope": ["src/alienintent/composition/fixture.py"]} | changes)))
+
+
+@pytest.fixture
+def plan_board(tmp_path) -> PlanBoard:
+    return PlanBoard(tmp_path / "fx")
+
+
+def test_check6_a_plan_derived_item_reaches_its_producer_with_no_authorize_and_no_card_write_by_the_test(
+        plan_board, tmp_path):
+    from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
+    from tests.execution_coordination.test_factory_coordinator import ScriptedWorker
+    item = plan_board.derived("PD-RUN", plan_board.approve())
+    assert plan_board.registry.release.release(item.id).answer is None
+    host = tmp_path / "factory-director-host.json"
+    host.write_text(json.dumps({"wipLimit": 1}))
+    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
+    worker = ScriptedWorker(artifacts, {item.id: ["success"]})
+
+    plan_board.loaded(host).coordinator(worker, artifacts).launch(item.id)
+
+    assert worker.dispatched == [item.id]
+    released = plan_board.registry.assessment.authorizations.release_authorization(item.id)
+    assert released.text.startswith("inherited from plan authority")
+
+
+def test_check6_an_explicit_item_with_a_ready_card_and_no_release_record_is_never_dispatched(board, tmp_path):
+    registry, coordinator, worker, summary, item = _registry_run(board, tmp_path, "RV-NONE", record=None,
+                                                                 release=False)
+    assert worker.invocations == [] and summary.authority_blocked == ()
+    with pytest.raises(KeyError):
+        coordinator.state(item.id)
+    assert not registry.assessment.consumer.store.read_state("registry", "decision-inbox")[1].get("open")
+    assert [i for i in registry._attention.list_pending() if i.origin.work_ref in (item.id, item.card_id)] == []
+
+
+def test_a_new_plan_approval_stops_an_item_released_under_the_old_one(plan_board, tmp_path):
+    """Released under plan D1, then the Founder approves D2: the item's issuer no longer names the current authority,
+    so it is not released by policy and neither `start()` nor `launch()` dispatches it."""
+    from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
+    from tests.execution_coordination.test_factory_coordinator import ScriptedWorker
+    item = plan_board.derived("PD-OLD", plan_board.approve())
+    assert plan_board.registry.release.release(item.id).answer is None
+    plan_board.approve(plan_text(note=" revision 2"))
+    host = tmp_path / "factory-director-host.json"
+    host.write_text(json.dumps({"wipLimit": 1}))
+    artifacts = LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
+    worker = ScriptedWorker(artifacts, {item.id: ["success"]})
+    coordinator = plan_board.loaded(host).coordinator(worker, artifacts)
+
+    coordinator.start()
+    coordinator.launch(item.id)
+
+    assert worker.dispatched == []
diff --git a/tests/composition/test_worker_launch.py b/tests/composition/test_worker_launch.py
index 267fdcc..cded158 100644
--- a/tests/composition/test_worker_launch.py
+++ b/tests/composition/test_worker_launch.py
@@ -720,6 +720,33 @@ def revision_of(state) -> str:
     return state.candidate.locator.rpartition("@")[2]
 
 
+def test_an_item_released_under_one_plan_revision_does_not_land_after_another_is_approved(closing):
+    """PLAN-AUTHORITY-INHERITANCE: released under plan D1 and taken to ACCEPT, then the Founder approves D2. Release
+    admission guards only the PRODUCER, so CLOSURE's landing gate checks the contract against the CURRENT authority:
+    held as a scope violation carrying the owner-decision reason, no order journaled, nothing pushed, and the one
+    owner-decision attention item raised."""
+    from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH
+    from tests.composition.test_work_registry import PLAN_QUOTE, plan_text
+    fx = closing.fx
+    approval = fx.registry.plan_approval
+    first = approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text()), PLAN_QUOTE).content_digest
+    item = closing.accepted(release_policy="automatic-on", authority_issuer="plan-authority:" + first,
+                            authority_references=["README.md", f"{PLAN_PATH} obligation:FIXTURE"],
+                            authorized_scope=["launch-candidate.txt"])
+    git(fx.clone, "push", "-q", "origin", "main")  # the landing base: the release baseline, so nothing else differs
+    assert approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text(note=" revision 2")),
+                            PLAN_QUOTE).answer is None
+
+    closing.close(item.id)
+
+    state = closing.state(item.id)
+    assert (state.stage, state.record["hold_reason"]) == (LifecycleStage.ACCEPT, "closure-hold:scope-violation")
+    [outcome] = [r for r in closing.journal() if r.get("event") == "invocation-outcome" and r["role"] == "CLOSURE"]
+    assert any(finding.startswith("owner-decision-required: authority_issuer") for finding in outcome["findings"])
+    assert closing.orders(item.id) == [] and closing.pushes == []
+    assert len([i for i in fx.registry._attention.list_pending() if i.origin.work_ref == item.id]) == 1
+
+
 def test_closure_lands_through_the_authority_with_five_exact_receipts_and_the_row_projected(closing, monkeypatch):
     """Checks 1, 4, 6, 7, 10, 13 and 14 over one real CLOSURE launch."""
     fx = closing.fx
diff --git a/tests/context_assembly/test_inherited_release.py b/tests/context_assembly/test_inherited_release.py
new file mode 100644
index 0000000..c3fae0b
--- /dev/null
+++ b/tests/context_assembly/test_inherited_release.py
@@ -0,0 +1,80 @@
+"""`work release` (PLAN-AUTHORITY-INHERITANCE acceptance checks 4 and 5): the control plane releases a plan-derived
+item with no Founder words and no manual card change, or refuses with its named code writing nothing.
+
+Every case runs the composed WorkRegistry over the fixture project of test_work_registry (PlanBoard): a local clone,
+the `readiness` store and evidence folder, a fixture Agent Ready and a recorded board that keeps each card's Status
+and Priority. Plans, labels and quotes are TEST DATA.
+"""
+from __future__ import annotations
+
+from dataclasses import asdict
+
+import pytest
+
+from alienintent.context_assembly.application.inherited_release import (
+    ASSESSMENT_MISSING, NOT_PLAN_DERIVED, NOT_RELEASABLE, OWNER_DECISION_REQUIRED)
+from alienintent.context_assembly.domain.work_context import PRODUCER, ContextPackage
+from alienintent.execution_coordination.domain.release import ReleaseAuthorization
+from tests.composition.test_work_registry import PlanBoard, plan_text
+
+
+@pytest.fixture
+def fx(tmp_path) -> PlanBoard:
+    return PlanBoard(tmp_path / "fx")
+
+
+def state(fx: PlanBoard, identity: str) -> tuple:
+    """What a release writes for the item: its release record, its approval_ref and its card's fields."""
+    item = fx.registry.identities.find(identity)
+    return (fx.registry.assessment.authorizations.release_authorization(identity), item.approval_ref,
+            fx.github.fields.get(item.card_id) if item.card_id else None)
+
+
+def owner_decisions(fx: PlanBoard, identity: str) -> list:
+    return [i for i in fx.registry._attention.list_pending() if i.origin.work_ref == identity]
+
+
+def test_a_plan_derived_item_is_released_its_card_reads_back_ready_p0_and_its_producer_context_assembles(fx):
+    digest = fx.approve()
+    item = fx.derived("PD-OK", digest)
+
+    result = fx.loaded().release.release(item.id)
+
+    assert result.answer is None and result.priority == "P0"
+    release, approval, fields = state(fx, item.id)
+    assert release.text.startswith(f"inherited from plan authority {digest}") and release.authorizes_implement
+    assert approval is not None and approval.revision_digest == release.record_ref
+    assert (fields["Status"], fields["Priority"]) == ("READY", "P0")
+    store, correlation = fx.registry.store, f"launch:{item.id}:0"
+    store.acquire_within("registry", "wip", item.id, f"work:{item.id}", 10)
+    store.acquire("registry", "repository", f"repository-{item.label}", correlation)
+    package = fx.registry.context.assemble(item.id, PRODUCER, correlation, None)
+    assert isinstance(package, ContextPackage), package
+    assert package.fields["release_record"]["evidence"]["approver"] == "plan-authority:" + digest
+
+
+@pytest.mark.parametrize("case", ["released", "held", "explicit", "older-plan"])
+def test_each_refusal_answers_its_code_and_writes_nothing(fx, case):
+    digest = fx.approve()
+    if case == "held":
+        fx.answer.write_text("HOLD")
+    item = fx.derived("PD-NO", digest, **({"release_policy": "explicit-human-off", "authority_issuer": "Founder"}
+                                          if case == "explicit" else {}))
+    if case == "released":  # a Founder release already recorded
+        fx.registry.assessment.authorizations.record(ReleaseAuthorization(
+            item.id, "sha256:" + "e" * 64, True, item.pointer.commit, "IMPLEMENT is authorized."))
+    if case == "older-plan":  # the item was issued under the first digest; a second revision is approved after it
+        fx.approve(plan_text(note=" revision 2"))
+    before = state(fx, item.id)
+
+    result = fx.loaded().release.release(item.id)
+
+    assert result.answer == {"released": NOT_RELEASABLE, "held": ASSESSMENT_MISSING, "explicit": NOT_PLAN_DERIVED,
+                             "older-plan": OWNER_DECISION_REQUIRED}[case]
+    assert state(fx, item.id) == before and fx.github.fields == {}
+    assert len(owner_decisions(fx, item.id)) == (1 if case == "older-plan" else 0)
+    if case == "older-plan":
+        assert "authority_issuer: not the approved plan authority" in result.detail
+        fx.loaded().release.release(item.id)  # a rerun keeps the one durable owner-decision item
+        [decision] = owner_decisions(fx, item.id)
+        assert (decision.origin.kind, decision.origin.event_identity) == ("JUDGMENT", OWNER_DECISION_REQUIRED)
diff --git a/tests/context_assembly/test_plan_approval.py b/tests/context_assembly/test_plan_approval.py
new file mode 100644
index 0000000..54f9d4f
--- /dev/null
+++ b/tests/context_assembly/test_plan_approval.py
@@ -0,0 +1,69 @@
+"""`work approve-plan` (PLAN-AUTHORITY-INHERITANCE acceptance check 3): the Founder's approval of one exact
+canonical-plan revision, on the composed WorkRegistry over a temporary project with a local clone. Plans and quotes
+are TEST DATA.
+"""
+from __future__ import annotations
+
+from hashlib import sha256
+
+import pytest
+
+from alienintent.context_assembly.application.plan_approval import CURRENT, PLAN_NOT_ON_MAIN, PLAN_SCOPE_INVALID
+from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, parse_scope
+from tests.composition.test_work_registry import PLAN_QUOTE, PlanBoard, plan_text
+from tests.context_assembly.test_work_authorization import dump
+from tests.context_assembly.test_work_identity_service import commit_file
+
+
+@pytest.fixture
+def fx(tmp_path) -> PlanBoard:
+    return PlanBoard(tmp_path / "fx")
+
+
+def written(fx: PlanBoard) -> tuple:
+    """Everything the command could write: the `readiness` database and the evidence folder."""
+    objects = fx.root / "evidence" / "objects"
+    return dump(fx.root / "readiness.sqlite"), sorted(p.name for p in objects.iterdir()) if objects.is_dir() else []
+
+
+def test_an_approval_records_the_exact_revision_and_becomes_current(fx):
+    data = plan_text()
+    commit = commit_file(fx.clone, "main", PLAN_PATH, data)
+    result = fx.registry.plan_approval.approve(commit, PLAN_QUOTE)
+    assert (result.answer, result.repeated, result.content_digest) == (None, False,
+                                                                       "sha256:" + sha256(data).hexdigest())
+    current = fx.loaded().plan_approval.current()  # read back by another process
+    assert (current.commit, current.content_digest, current.quote, current.approver) == (
+        commit, result.content_digest, PLAN_QUOTE, "Founder")
+    assert current.scope == parse_scope(data.decode()) and current.record_ref == result.evidence_ref["revision_digest"]
+
+    before = written(fx)
+    again = fx.registry.plan_approval.approve(commit, PLAN_QUOTE)
+    assert (again.answer, again.repeated, again.evidence_ref) == (None, True, result.evidence_ref)
+    assert written(fx) == before
+
+
+def test_re_approving_an_older_revision_makes_it_current_again(fx):
+    first = fx.approve()
+    second = fx.approve(plan_text(note=" revision 2"))
+    assert fx.registry.plan_approval.current().content_digest == second
+    commit = commit_file(fx.clone, "main", PLAN_PATH, plan_text())
+    assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).repeated is True
+    assert fx.registry.plan_approval.current().content_digest == first
+    _, current = fx.registry.store.read_state("registry", CURRENT)
+    assert current["content_digest"] == first
+
+
+@pytest.mark.parametrize("case", ["side-branch", "bad-block", "empty-quote"])
+def test_each_refusal_writes_nothing(fx, case):
+    before = written(fx)
+    if case == "side-branch":
+        commit = commit_file(fx.clone, "side", PLAN_PATH, plan_text())
+        assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).answer == PLAN_NOT_ON_MAIN
+    elif case == "bad-block":
+        commit = commit_file(fx.clone, "main", PLAN_PATH, b"# plan\n\n```json alienintent-plan-authority\n{}\n```\n")
+        assert fx.registry.plan_approval.approve(commit, PLAN_QUOTE).answer == PLAN_SCOPE_INVALID
+    else:
+        with pytest.raises(ValueError):
+            fx.registry.plan_approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text()), " ")
+    assert written(fx) == before and fx.registry.plan_approval.current() is None
diff --git a/tests/control_plane/test_cli.py b/tests/control_plane/test_cli.py
index acc63ee..ae5daf2 100644
--- a/tests/control_plane/test_cli.py
+++ b/tests/control_plane/test_cli.py
@@ -621,6 +621,8 @@ def test_work_context_runs_with_only_the_worker_environment(tmp_path: Path) -> N
 @pytest.mark.parametrize("argv", [
     ["work", "assess", "UNIT"],
     ["work", "authorize", "UNIT", "--commit", "c", "--attempt", "a", "--baseline", "b", "--quote", "q"],
+    ["work", "approve-plan", "--commit", "c", "--quote", "q"],
+    ["work", "release", "UNIT"],
     ["work", "record-completed", "UNIT", "--candidate", "c", "--landing", "l", "--record", "r", "--verification", "v",
      "--approval", "a", "--quote", "q"],
     ["work", "link", "UNIT"],
diff --git a/tests/execution_coordination/domain/test_plan_authority.py b/tests/execution_coordination/domain/test_plan_authority.py
new file mode 100644
index 0000000..825deb4
--- /dev/null
+++ b/tests/execution_coordination/domain/test_plan_authority.py
@@ -0,0 +1,105 @@
+"""PLAN-AUTHORITY-INHERITANCE acceptance checks 1 and 7: the pure plan-authority rule and the canonical plan's block.
+
+`outside_authority` answers nothing for a contract inside a sample obligation and exactly one owner-decision reason
+for each single change; `parse_scope` refuses a missing, duplicate or malformed block and wrong keys. Sample plans,
+labels and digests are TEST DATA.
+"""
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+import pytest
+
+from alienintent.context_assembly.domain.compilation import contract_from_payload
+from alienintent.execution_coordination.domain.plan_authority import (
+    PLAN_PATH, PlanAuthority, PlanScopeInvalid, outside_authority, parse_scope)
+from tests.context_assembly.test_work_contract import satisfiable_payload
+
+ROOT = Path(__file__).resolve().parents[3]
+DIGEST = "sha256:" + "a" * 64
+SCOPE = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python", "filesystem"],
+         "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
+                         "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
+         "protected_paths": ["docs/decisions/", "src/alienintent/execution_coordination/domain/release.py"],
+         "obligations": [{"label": "SAMPLE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+                          "allowed_paths": ["docs/", "src/", "tests/"]}]}
+
+
+def plan(scope: object = SCOPE, blocks: int = 1) -> str:
+    block = f"```json alienintent-plan-authority\n{scope if isinstance(scope, str) else json.dumps(scope)}\n```\n"
+    return "# Sample plan\n\n" + block * blocks
+
+
+AUTHORITY = PlanAuthority(PLAN_PATH, "c" * 40, DIGEST, "sha256:" + "b" * 64, "Founder", "approved", parse_scope(plan()))
+
+
+def contract(**changes):
+    return contract_from_payload(satisfiable_payload(**({
+        "release_policy": "automatic-on", "authority_issuer": "plan-authority:" + DIGEST,
+        "authority_references": [f"{PLAN_PATH} obligation:SAMPLE", "README.md"],
+        "authorized_scope": ["src/alienintent/composition/", "tests/composition/test_x.py"]} | changes)))
+
+
+def test_a_contract_inside_its_obligation_inherits():
+    assert outside_authority(contract(), AUTHORITY) == ()
+
+
+BUDGET = {"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1}
+
+
+@pytest.mark.parametrize(("change", "words"), [
+    ({"authority_issuer": "plan-authority:sha256:" + "f" * 64}, "authority_issuer: not the approved"),
+    ({"authority_references": ["README.md"]}, "exactly one"),
+    ({"authority_references": [f"{PLAN_PATH} obligation:SAMPLE", f"{PLAN_PATH} obligation:SAMPLE"]}, "exactly one"),
+    ({"authority_references": [f"{PLAN_PATH} obligation:OTHER"]}, "obligation OTHER is not in the approved plan"),
+    ({"target_repositories": ["AlienLogicLab/other"]}, "target_repositories: outside the plan"),
+    ({"required_capabilities": ["process-control"]}, "required_capabilities: outside the plan"),
+    ({"satisfied_requirement_ids": ["SF-REQ-009"]}, "satisfied_requirement_ids: outside obligation SAMPLE"),
+    ({"budget_policy": BUDGET | {"maximum_attempts": 4}}, "maximum_attempts 4 above the cap 3"),
+    ({"budget_policy": BUDGET | {"hard_wall_clock_seconds": 3601}}, "hard_wall_clock_seconds 3601 above"),
+    ({"budget_policy": BUDGET | {"cancellation_limit": 2}}, "cancellation_limit 2 above"),
+    ({"budget_policy": BUDGET | {"retry_limit": 2}}, "retry_limit 2 above"),
+    ({"budget_policy": BUDGET | {"concurrency_limit": 2}}, "concurrency_limit 2 above"),
+    ({"budget_policy": {"maximum_attempts": 1, "cancellation_limit": 1}}, "hard_wall_clock_seconds is required"),
+    ({"budget_policy": BUDGET | {"hard_required_dimensions": ["tokens"]}}, "dimension tokens outside the cap list"),
+    ({"authorized_scope": ["config/x.json"]}, "config/x.json is outside obligation SAMPLE"),
+    ({"authorized_scope": ["docs/decisions"]}, "crosses a protected path: docs/decisions"),
+    ({"authorized_scope": ["src/alienintent/execution_coordination/"]}, "crosses a protected path: src/alienintent"),
+    ({"authorized_scope": ["src/alienintent/execution_coordination/domain/Release.py"]},
+     "crosses a protected path: src/alienintent/execution_coordination/domain/Release.py"),
+    ({"authorized_scope": ["SRC/x.py"]}, "SRC/x.py is outside obligation SAMPLE"),
+    ({"authorized_scope": ["src/*.py"]}, "src/*.py is malformed"),
+    ({"authorized_scope": ["a/../docs/decisions/x"]}, "a/../docs/decisions/x is malformed"),
+    ({"authorized_scope": ["/src/x.py"]}, "/src/x.py is malformed"),
+], ids=lambda value: value if isinstance(value, str) else None)
+def test_each_single_change_is_exactly_one_owner_decision(change, words):
+    [reason] = outside_authority(contract(**change), AUTHORITY)
+    assert reason.startswith("owner-decision-required: ") and words in reason
+
+
+@pytest.mark.parametrize("text", [
+    "# no block\n", plan(blocks=2), plan("{not json"), plan(dict(SCOPE, extra=1)),
+    plan({key: value for key, value in SCOPE.items() if key != "protected_paths"}),
+    plan(dict(SCOPE, obligations=[dict(SCOPE["obligations"][0], allowed_paths=["../x"])]))],
+    ids=["missing", "duplicate", "malformed", "extra-key", "missing-key", "malformed-path"])
+def test_parse_scope_refuses_a_missing_duplicate_or_malformed_block(text):
+    with pytest.raises(PlanScopeInvalid):
+        parse_scope(text)
+
+
+def test_check7_the_canonical_plan_states_the_rule_and_holds_one_block():
+    text = (ROOT / PLAN_PATH).read_text(encoding="utf-8")
+    assert "After the Founder approves canonical product intent/plan authority, derived Work Items advance without " \
+           "additional Founder approval unless they cross a new owner-decision boundary." in text
+    assert "After the Founder approves a queue item" not in text
+    headings = [line for line in text.splitlines() if line.startswith("## 2.")]
+    assert headings[headings.index("## 2.2.1 Plan authority") - 1].startswith("## 2.2 ")
+    assert headings[headings.index("## 2.2.1 Plan authority") + 1].startswith("## 2.3 One work identity")
+    scope = parse_scope(text)
+    assert [o.label for o in scope.obligations] == ["BOUNDED-ROUTINE-LAUNCH", "WORK-PREPARATION-REFILL",
+                                                    "TERMINAL-BOARD-STATUSES", "STORE-SCHEMA-HARDENING",
+                                                    "AUTONOMY-PROOF"]
+    assert {"conftest.py", "pyproject.toml", "config/", "tools/fitness/",
+            "src/alienintent/execution_coordination/domain/scope_containment.py",
+            "tests/execution_coordination/test_containment_wiring.py"} <= set(scope.protected_paths)
diff --git a/tests/execution_coordination/domain/test_satisfiability.py b/tests/execution_coordination/domain/test_satisfiability.py
index 7bafa46..323042e 100644
--- a/tests/execution_coordination/domain/test_satisfiability.py
+++ b/tests/execution_coordination/domain/test_satisfiability.py
@@ -55,6 +55,17 @@ def test_each_contract_rule_fails_alone(change, field):
     assert len(answer) == 1 and answer[0].startswith(field + ":")
 
 
+def test_automatic_on_passes_only_through_an_approved_plan_authority():
+    base = valid_contract().canonical_payload()
+    base.update(release_policy="automatic-on")
+    contract = contract_from_payload(base)
+    assert reasons(contract) == ("release_policy: automatic-on requires an approved plan authority",)
+    outside = ("owner-decision-required: one", "owner-decision-required: two")
+    for answer in (outside, ()):
+        assert unsatisfiable(contract, landing=True, present_at_pointer=lambda _: True, registered=lambda _: True,
+                             provider_dimensions=PROVIDER_DIMENSIONS, plan_authority=lambda _: answer) == answer
+
+
 def test_landing_rule_fails_alone():
     assert len(answer := reasons(valid_contract(), landing=False)) == 1
     assert answer[0].startswith("landing:") and "ready-to-land" in answer[0]
diff --git a/tests/execution_coordination/domain/test_scope_containment.py b/tests/execution_coordination/domain/test_scope_containment.py
new file mode 100644
index 0000000..5330bf9
--- /dev/null
+++ b/tests/execution_coordination/domain/test_scope_containment.py
@@ -0,0 +1,41 @@
+"""Actual-diff containment (PLAN-AUTHORITY-INHERITANCE revision 3, change 3): the pure rule.
+
+Every changed path of a plan-derived candidate must be under its assessed scope and outside the protected paths;
+symbolic links, submodules and interpreter start-up files are refused wherever they sit. Paths are TEST DATA.
+"""
+from __future__ import annotations
+
+import pytest
+
+from alienintent.execution_coordination.domain.scope_containment import contained
+
+SCOPE = ("src/alienintent/composition/", "tests/composition/test_x.py")
+PROTECTED = ("docs/decisions/", "src/alienintent/composition/landing_authority.py")
+
+
+def test_changes_inside_the_scope_are_contained():
+    assert contained((("100644", "src/alienintent/composition/a.py"), ("100755", "tests/composition/test_x.py")),
+                     SCOPE, PROTECTED) == ()
+
+
+@pytest.mark.parametrize(("change", "words"), [
+    (("100644", "src/alienintent/composition_extra.py"), "outside the authorized scope"),
+    (("100644", "docs/decisions/plan.md"), "outside the authorized scope"),
+    (("100644", "src/alienintent/composition/landing_authority.py"), "is a protected path"),
+    (("120000", "src/alienintent/composition/link.py"), "a symbolic link (mode 120000)"),
+    (("160000", "src/alienintent/composition/vendor"), "a submodule (mode 160000)"),
+    (("100644", "src/alienintent/composition/sitecustomize.py"), "interpreter start-up file"),
+    (("100644", "src/alienintent/composition/hook.pth"), "interpreter start-up file"),
+    (("100644", "SRC/alienintent/composition/b.py"), "outside the authorized scope"),
+    (("100644", "src/alienintent/composition/Landing_Authority.py"), "is a protected path"),
+    (("100644", "src/alienintent/composition/conftest.py"), "a pytest conftest file"),
+], ids=["outside", "outside-and-protected-folder", "protected", "symlink", "submodule", "sitecustomize", "pth",
+        "scope-is-exact-case", "protected-ignores-case", "conftest"])
+def test_each_violation_is_named(change, words):
+    reasons = contained((change,), SCOPE, PROTECTED)
+    assert reasons and all(reason.startswith("scope-violation:") for reason in reasons)
+    assert any(words in reason and change[1] in reason for reason in reasons)
+
+
+def test_nothing_is_contained_without_a_scope():
+    assert contained((("100644", "src/alienintent/composition/a.py"),), (), PROTECTED) != ()
diff --git a/tests/execution_coordination/test_containment_wiring.py b/tests/execution_coordination/test_containment_wiring.py
new file mode 100644
index 0000000..6640b84
--- /dev/null
+++ b/tests/execution_coordination/test_containment_wiring.py
@@ -0,0 +1,315 @@
+"""Actual-diff containment is wired where it must run (PLAN-AUTHORITY-INHERITANCE revision 3, change 3).
+
+By source inspection and by behaviour: `RealWorkerProvider._produce` applies the containment rule to an automatic-on
+candidate before `publication-started`, publishing nothing on a violation; `RegistryClosure.close` refuses a scope
+violation with a closure hold before any order is journaled or landed. A candidate that removes either call fails
+here, in the factory's regression gate. Repositories, paths and contracts are TEST DATA.
+"""
+from __future__ import annotations
+
+import ast
+from hashlib import sha256
+import json
+from pathlib import Path
+import subprocess
+import sys
+import time
+from types import SimpleNamespace
+
+import pytest
+
+from alienintent.composition.work_registry import RegistryClosure
+from alienintent.context_assembly.domain.compilation import contract_from_payload
+from alienintent.context_assembly.ports.work_item_repository import RepositoryLocation
+from alienintent.execution_coordination.domain.closure import ACTIONS, hold
+from alienintent.execution_coordination.domain.contract import BudgetPolicy
+from alienintent.execution_coordination.domain.custody import CandidateRef
+from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, PlanAuthority, parse_scope
+from alienintent.execution_coordination.domain.release import ReleaseAuthorization
+from alienintent.execution_coordination.domain.scope_containment import NO_PLAN_AUTHORITY, NO_TRUSTED_START
+from alienintent.execution_coordination.ports.worker_provider import CLOSURE, WorkerInvocation
+from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
+from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
+from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
+from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
+from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
+from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole
+from tests.context_assembly.test_work_contract import satisfiable_payload
+
+SRC = Path(__file__).resolve().parents[2] / "src" / "alienintent"
+PROTECTED = ("docs/decisions/", "src/protected.py")
+
+
+def plan_at(digest: str) -> PlanAuthority:
+    """A current plan authority with PROTECTED and one obligation FIXTURE over `src/` (TEST DATA)."""
+    scope = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python"],
+             "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
+                             "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
+             "protected_paths": list(PROTECTED),
+             "obligations": [{"label": "FIXTURE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
+                              "allowed_paths": ["src/"]}]}
+    text = f"```json alienintent-plan-authority\n{json.dumps(scope)}\n```\n"
+    return PlanAuthority(PLAN_PATH, "c" * 40, digest, "sha256:" + "b" * 64, "Founder", "approved", parse_scope(text))
+
+
+D1, D2 = "sha256:" + "1" * 64, "sha256:" + "2" * 64
+
+
+def _method(path: Path, cls: str, name: str) -> ast.FunctionDef:
+    module = ast.parse(path.read_text(encoding="utf-8"))
+    owner = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == cls)
+    return next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == name)
+
+
+def _calls(function: ast.FunctionDef, name: str) -> list[int]:
+    """Lines of every call of `name` or `self.name` in `function`."""
+    return [node.lineno for node in ast.walk(function) if isinstance(node, ast.Call) and (
+        isinstance(node.func, ast.Name) and node.func.id == name
+        or isinstance(node.func, ast.Attribute) and node.func.attr == name)]
+
+
+def _uses(function: ast.FunctionDef, name: str) -> list[int]:
+    return [node.lineno for node in ast.walk(function) if isinstance(node, ast.Name) and node.id == name]
+
+
+def test_source_the_producer_checks_containment_before_publication():
+    worker = SRC / "invocation_runtime" / "application" / "real_worker.py"
+    produce = _method(worker, "RealWorkerProvider", "_produce")
+    checked, published = _calls(produce, "_scope_violations"), _uses(produce, "PUBLICATION_STARTED")
+    assert len(checked) == 1 and published and checked[0] < min(published)
+    assert _calls(_method(worker, "RealWorkerProvider", "_scope_violations"), "contained")
+
+
+def test_source_closure_checks_containment_against_the_landing_base_before_every_order():
+    """In `_order`, which every first order and every re-order at a new head runs through: the check on the diff
+    from the landing `base`, before the merge is built and before the order is journaled."""
+    registry = SRC / "composition" / "work_registry.py"
+    order = _method(registry, "RegistryClosure", "_order")
+    calls = [node for node in ast.walk(order) if isinstance(node, ast.Call)
+             and isinstance(node.func, ast.Attribute) and node.func.attr == "_scope_violations"]
+    assert len(calls) == 1 and any(isinstance(arg, ast.Name) and arg.id == "base" for arg in calls[0].args)
+    assert calls[0].lineno < min(_calls(order, "_build")) and calls[0].lineno < min(_calls(order, "append"))
+    assert _calls(_method(registry, "RegistryClosure", "_scope_violations"), "contained")
+
+
+# --- behaviour: the PRODUCER ----------------------------------------------------------------------------------------
+
+
+def git(path: Path, *args: str) -> str:
+    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()
+
+
+def change(path: str, link: bool = False) -> str:
+    """A PRODUCER process that commits one new file (or symbolic link) at `path`."""
+    make = "p.symlink_to('base.txt')" if link else "p.write_text('change')"
+    return (f"import pathlib, subprocess; p = pathlib.Path({path!r}); p.parent.mkdir(parents=True, exist_ok=True); "
+            f"{make}; subprocess.run(['git', 'add', {path!r}], check=True); "
+            "subprocess.run(['git', 'commit', '-qm', 'change'], check=True)")
+
+
+class Forged(GitSourceControl):
+    """A reader whose first answer (the starting revision the worker reports) is `claim`."""
+
+    def __init__(self, claim: str) -> None:
+        self.claim, self.calls = claim, 0
+
+    def revision(self, workspace: Path) -> str:
+        self.calls += 1
+        return self.claim if self.calls == 1 else super().revision(workspace)
+
+
+def produce(tmp_path: Path, command: str, policy: str, protected=lambda: PROTECTED, *, trusted: bool = True,
+            forge=None):
+    """One PRODUCER run; with `trusted` the preparation names the starting revision (as `work context` does), and
+    `forge(source)` may add history and answer the start the worker will claim."""
+    remote, source = tmp_path / "remote.git", tmp_path / "source"
+    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
+    subprocess.run(["git", "init", "-q", str(source)], check=True)
+    git(source, "config", "user.email", "test@example.invalid")
+    git(source, "config", "user.name", "Test")
+    (source / "base.txt").write_text("base")
+    git(source, "add", "base.txt")
+    git(source, "commit", "-qm", "base")
+    git(source, "remote", "add", "origin", str(remote))
+    starting = git(source, "rev-parse", "HEAD")
+    reader = GitSourceControl() if forge is None else Forged(forge(source))
+    preparation = SimpleNamespace(prepare=lambda *_: starting, published=lambda *_: None) if trusted else None
+    process = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit",
+                                frozenset({"wall-clock", "cancellation"}))
+    invocation = WorkerInvocation("work", "producer-1")
+    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
+                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
+    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
+    worker = RealWorkerProvider(process, reader, source, "origin", "candidate/producer-1",
+                                tmp_path / "verifier", grant, "repo",
+                                GitWorktreeAdapter(source, tmp_path / "worktrees"),
+                                now=time.time, sleep=time.sleep, journal=journal, protected_paths=protected,
+                                preparation=preparation)
+    contract = contract_from_payload(satisfiable_payload("work", release_policy=policy, authorized_scope=["src/"]))
+    outcome = worker.start(invocation, contract, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5,
+                                                                           cancellation_limit=1))
+    published = git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/candidate")
+    started = [r for r in journal.records() if r.get("event") == "publication-started"]
+    return outcome, published, started
+
+
+@pytest.mark.parametrize(("command", "words"), [
+    (change("docs/notes.md"), "docs/notes.md is outside the authorized scope"),
+    (change("src/protected.py"), "src/protected.py is a protected path"),
+    (change("src/link", link=True), "src/link is a symbolic link (mode 120000)"),
+], ids=["outside", "protected", "symlink"])
+def test_an_automatic_on_candidate_outside_its_boundary_is_never_published(tmp_path, command, words):
+    outcome, published, started = produce(tmp_path, command, "automatic-on")
+    assert outcome.kind == "scope-violation" and outcome.candidate is None
+    assert any(words in finding for finding in outcome.findings), outcome.findings
+    assert (published, started) == ("", [])
+
+
+def test_without_a_plan_authority_no_automatic_on_candidate_is_published(tmp_path):
+    outcome, published, started = produce(tmp_path, change("src/a.py"), "automatic-on", protected=lambda: None)
+    assert (outcome.kind, outcome.findings, published, started) == ("scope-violation", (NO_PLAN_AUTHORITY,), "", [])
+
+
+def test_without_a_trusted_starting_revision_no_automatic_on_candidate_is_published(tmp_path):
+    outcome, published, started = produce(tmp_path, change("src/a.py"), "automatic-on", trusted=False)
+    assert (outcome.kind, outcome.findings, published, started) == ("scope-violation", (NO_TRUSTED_START,), "", [])
+
+
+def test_a_worker_reported_start_cannot_narrow_the_diff(tmp_path):
+    """The worker fast-forwards to a side commit that adds a file outside the scope, then commits inside it, and
+    reports the side commit as its start: the diff still runs from the trusted starting revision."""
+    def side(source: Path) -> str:
+        git(source, "checkout", "-q", "-b", "side")
+        (source / "docs").mkdir()
+        (source / "docs" / "notes.md").write_text("side")
+        git(source, "add", "docs/notes.md")
+        git(source, "commit", "-qm", "side")
+        claim = git(source, "rev-parse", "HEAD")
+        git(source, "checkout", "-q", "-")
+        return claim
+    prefix = "import pathlib, subprocess; "
+    command = prefix + "subprocess.run(['git', 'merge', '-q', '--ff-only', 'side'], check=True); " + \
+        change("src/a.py").removeprefix(prefix)
+    outcome, published, started = produce(tmp_path, command, "automatic-on", forge=side)
+    assert outcome.kind == "scope-violation" and (published, started) == ("", [])
+    assert any("docs/notes.md is outside the authorized scope" in finding for finding in outcome.findings)
+
+
+@pytest.mark.parametrize(("command", "policy"), [(change("src/a.py"), "automatic-on"),
+                                                 (change("docs/notes.md"), "explicit-human-off")],
+                         ids=["contained", "explicit"])
+def test_a_contained_or_explicit_candidate_is_published(tmp_path, command, policy):
+    outcome, published, started = produce(tmp_path, command, policy)
+    assert outcome.kind == "success" and published == "refs/heads/candidate/producer-1" and len(started) == 1
+
+
+# --- behaviour: CLOSURE ---------------------------------------------------------------------------------------------
+
+
+def close(tmp_path: Path, path: str, policy: str, *, revert_main: bool = False, authority=None, current=None,
+          reconcile_under=None, decisions: list | None = None):
+    """CLOSURE of a candidate that adds `path` on top of its release baseline; with `revert_main`, main then changes
+    the protected `docs/decisions/plan.md` and the candidate merges main and reverts that file. Without a Landing
+    Authority a landing that may proceed ends at `ready-to-land`."""
+    remote, clone = tmp_path / "remote.git", tmp_path / "clone"
+    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
+    subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True)
+    for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test")):
+        git(clone, "config", key, value)
+    (clone / "base.txt").write_text("base")
+    (clone / "docs" / "decisions").mkdir(parents=True)
+    (clone / "docs" / "decisions" / "plan.md").write_text("approved")
+    git(clone, "add", "base.txt", "docs/decisions/plan.md")
+    git(clone, "commit", "-qm", "base")
+    git(clone, "remote", "add", "origin", str(remote))
+    git(clone, "push", "-q", "origin", "main")
+    baseline = git(clone, "rev-parse", "HEAD")
+    git(clone, "checkout", "-q", "-b", "candidate/c-1")
+    (clone / path).parent.mkdir(parents=True, exist_ok=True)
+    (clone / path).write_text("change")
+    git(clone, "add", path)
+    git(clone, "commit", "-qm", "candidate")
+    if revert_main:
+        git(clone, "checkout", "-q", "main")
+        (clone / "docs" / "decisions" / "plan.md").write_text("changed on main after the release")
+        git(clone, "commit", "-qam", "main changes the plan")
+        git(clone, "push", "-q", "origin", "main")
+        git(clone, "checkout", "-q", "candidate/c-1")
+        git(clone, "merge", "-q", "--no-edit", "main")
+        git(clone, "checkout", baseline, "--", "docs/decisions/plan.md")
+        git(clone, "commit", "-qm", "revert the plan to the release baseline")
+    git(clone, "push", "-q", "origin", "candidate/c-1")
+    revision = git(clone, "rev-parse", "HEAD")
+    # The scope never crosses PROTECTED (`src/` would be an ancestor of `src/protected.py`): inside the authority.
+    payload = satisfiable_payload("work", release_policy=policy, authorized_scope=["src/a.py"],
+                                  authority_issuer="plan-authority:" + D1 if policy == "automatic-on" else "Founder",
+                                  authority_references=[f"{PLAN_PATH} obligation:FIXTURE"])
+    packet = f"# Work unit\n\n```json alienintent-contract\n{json.dumps(payload)}\n```\n".encode()
+    plans = [plan_at(D1) if current is None else current]
+    registry = SimpleNamespace(
+        configuration=SimpleNamespace(packets_repository="repo", repositories={
+            "repo": RepositoryLocation(clone, "origin", "main", "alienintent/work-packets")}),
+        records=SimpleNamespace(show=lambda _: SimpleNamespace(packet=packet, item=SimpleNamespace(label="UNIT"))),
+        assessment=SimpleNamespace(authorizations=SimpleNamespace(release_authorization=lambda identity: (
+            ReleaseAuthorization(identity, "sha256:" + "e" * 64, True, baseline, "inherited")))),
+        plan_approval=SimpleNamespace(current=lambda: plans[-1]), store=SimpleNamespace(read_state=lambda *_: (0, {})),
+        _owner_decision=(decisions if decisions is not None else []).append)
+    request = json.dumps({"identity": "work", "revision": revision, "actions": list(ACTIONS), "findings": []})
+    preparation = SimpleNamespace(read=lambda _: request.encode(), closure_request_path=lambda _: tmp_path / "r.json")
+    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
+    candidate = CandidateRef.source_revision("sha256:" + sha256(revision.encode()).hexdigest(),
+                                             f"git:{remote}#candidate/c-1@{revision}")
+    closure = RegistryClosure(registry, tmp_path / "launch", journal, preparation, authority)
+    invocation = WorkerInvocation("work", "closure-1", role=CLOSURE)
+    receipts, findings = closure.close(invocation, candidate, journal)
+    if reconcile_under is not None:  # another plan revision becomes current, then the journaled order is re-landed
+        plans.append(reconcile_under)
+        receipts, findings = closure.reconcile(invocation, candidate, tuple(
+            r for r in journal.records() if r.get("event") == "closure-ordered"))
+    return revision, findings, [r for r in journal.records() if r.get("event") == "closure-ordered"], \
+        git(clone, "rev-parse", "main")
+
+
+def test_closure_refuses_an_automatic_on_candidate_outside_its_boundary_before_any_order(tmp_path):
+    revision, findings, orders, head = close(tmp_path, "docs/decisions/x.md", "automatic-on")
+    assert findings[0] == hold("scope-violation", head, revision) and orders == []
+    assert any("docs/decisions/x.md is outside the authorized scope" in finding for finding in findings[1:])
+
+
+def test_closure_refuses_a_candidate_outside_the_current_plan_authority_and_raises_one_owner_decision(tmp_path):
+    """Released under D1, D2 is current at CLOSURE: the contract is checked against the current authority at the
+    landing gate, held before any order, with an owner-decision reason and the owner-decision attention item."""
+    landed, decisions = [], []
+    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", current=plan_at(D2),
+                                             authority=SimpleNamespace(land=landed.append), decisions=decisions)
+    assert findings[0] == hold("scope-violation", head, revision) and (orders, landed) == ([], [])
+    assert any(finding.startswith("owner-decision-required: authority_issuer") for finding in findings[1:])
+    assert decisions == ["work"]
+
+
+def test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced(tmp_path):
+    """The order was journaled and handed over under D1 (the push did not land); D2 is current when the order is
+    re-landed at the same base: held, the Landing Authority is not called again."""
+    landed = []
+    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", reconcile_under=plan_at(D2),
+                                             authority=SimpleNamespace(land=landed.append))
+    assert len(orders) == 1 and len(landed) == 1
+    assert findings[0] == hold("scope-violation", head, revision)
+    assert any(finding.startswith("owner-decision-required:") for finding in findings[1:])
+
+
+def test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release(tmp_path):
+    """The release-baseline diff lists only `src/a.py`; what would land is the diff from the landing base (main's
+    head), which reverts the protected plan: held before any order is journaled and before the Landing Authority."""
+    landed = []
+    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", revert_main=True,
+                                             authority=SimpleNamespace(land=landed.append))
+    assert findings[0] == hold("scope-violation", head, revision) and (orders, landed) == ([], [])
+    assert any("docs/decisions/plan.md is a protected path" in finding for finding in findings[1:])
+
+
+@pytest.mark.parametrize(("path", "policy"), [("src/a.py", "automatic-on"), ("docs/notes.md", "explicit-human-off")],
+                         ids=["contained", "explicit"])
+def test_closure_lets_a_contained_or_explicit_candidate_reach_its_landing(tmp_path, path, policy):
+    _, findings, _, _ = close(tmp_path, path, policy)
+    assert [finding.split(":", 1)[0] for finding in findings] == ["ready-to-land"]
diff --git a/tools/fitness/coupling_register.json b/tools/fitness/coupling_register.json
index 68f93b2..db3bc74 100644
--- a/tools/fitness/coupling_register.json
+++ b/tools/fitness/coupling_register.json
@@ -97,6 +97,13 @@
       "classification": "DOMAIN_LEAKAGE_HELD",
       "basis": "No pinned Phase 9 shared contract names this as a deliberately shared value or port contract. Held as possible domain leakage pending bounded-context ownership review; present at baseline, not refactored (no broad refactor is authorized)."
     },
+    {
+      "consumer": "context_assembly",
+      "target": "alienintent.execution_coordination.domain.plan_authority",
+      "owner": "execution_coordination",
+      "classification": "PORT_CONTRACT",
+      "basis": "PlanAuthority and parse_scope are the plan-authority rule's values: work approve-plan records an approved plan revision with them and work release reads the current one (docs/work-units/python/plan-authority-inheritance.md revision 3, sections 2.2, 2.4 and 2.5)."
+    },
     {
       "consumer": "context_assembly",
       "target": "alienintent.execution_coordination.domain.readiness",
@@ -222,6 +229,13 @@
       "owner": "execution_coordination",
       "classification": "DOMAIN_LEAKAGE_HELD",
       "basis": "No pinned Phase 9 shared contract names this as a deliberately shared value or port contract. Held as possible domain leakage pending bounded-context ownership review; present at baseline, not refactored (no broad refactor is authorized)."
+    },
+    {
+      "consumer": "invocation_runtime",
+      "target": "alienintent.execution_coordination.domain.scope_containment",
+      "owner": "execution_coordination",
+      "classification": "PORT_CONTRACT",
+      "basis": "contained is the control plane's actual-diff containment rule, the same rule CLOSURE re-checks: RealWorkerProvider applies it to an automatic-on PRODUCER candidate before publication (Founder decision 6, 2026-10-08; plan-authority-inheritance.md revision 3, change 3)."
     }
   ],
   "persistence": [
```

## 3. Acceptance checks

1. **The rules**: `tests/execution_coordination/domain/test_plan_authority.py`,
   `tests/execution_coordination/domain/test_scope_containment.py`, `tests/execution_coordination/domain/test_satisfiability.py`.
2. **Approval and release**: `tests/context_assembly/test_plan_approval.py`, `tests/context_assembly/test_inherited_release.py`;
   the existing `tests/context_assembly/test_work_authorization.py` passes unchanged.
3. **Wiring and the factory path**: `tests/execution_coordination/test_containment_wiring.py` (containment before
   publication, from the trusted start; CLOSURE at the landing base before any order; current authority at the gate;
   re-land re-check), `tests/composition/test_work_registry.py` (plan-derived item assess -> release -> PRODUCER with no
   `work authorize`; an explicit item without a release never dispatched; a new approval stops an item released under
   the old one), `tests/composition/test_worker_launch.py::test_an_item_released_under_one_plan_revision_does_not_land_after_another_is_approved`.
4. **Mutations, run exactly by the VERIFIER** (each must fail its named tests and pass when reverted):
- **M1 raw startswith, no normalization (outside_authority)** (`src/alienintent/execution_coordination/domain/plan_authority.py`): `entries = [(entry, normalized(entry)) for entry in contract.authorized_scope]` -> `entries = [(entry, entry) for entry in contract.authorized_scope]`; `allowed = [normalized(path) for path in obligation.allowed_paths]` -> `allowed = list(obligation.allowed_paths)`; `for entry, path in entries if path is None or not any(under(path, a) for a in allowed)]` -> `for entry, path in entries if path is None or not any(path.startswith(a) for a in allowed)]`; `protected = [normalized(path, fold=True) for path in scope.protected_paths]` -> `protected = list(scope.protected_paths)`; `and any(under(path.casefold(), p) or under(p, path.casefold()) for p in protected)]` -> `and any(path.startswith(p) for p in protected)]` -> must fail: `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change15-crosses a protected path: docs/decisions]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change16-crosses a protected path: src/alienintent]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change17-crosses a protected path: src/alienintent/execution_coordination/domain/Release.py]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change20-a/../docs/decisions/x is malformed]`
- **M2 automatic-on passes with no plan authority** (`src/alienintent/execution_coordination/domain/satisfiability.py`): `reasons.append("release_policy: automatic-on requires an approved plan authority")` -> `pass` -> must fail: `tests/execution_coordination/domain/test_satisfiability.py::test_automatic_on_passes_only_through_an_approved_plan_authority`
- **M3 work release skips set_evidence(approval)** (`src/alienintent/context_assembly/application/inherited_release.py`): `self.identities.set_evidence(item.id, "approval", reference)` -> `(deleted)` -> must fail: `tests/context_assembly/test_inherited_release.py::test_a_plan_derived_item_is_released_its_card_reads_back_ready_p0_and_its_producer_context_assembles`
- **M4 wrapper sets every item automatic** (`src/alienintent/composition/work_registry.py`): `return tuple(replace(item, automatic_release=automatic(item.contract, current))` -> `return tuple(replace(item, automatic_release=True)` -> must fail: `tests/composition/test_work_registry.py::test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store`, `tests/composition/test_work_registry.py::test_check6_an_explicit_item_with_a_ready_card_and_no_release_record_is_never_dispatched`
- **C1 containment call removed from _produce** (`src/alienintent/invocation_runtime/application/real_worker.py`): `violations = self._scope_violations(context, reader, workspace.path, starting_revision, revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_source_the_producer_checks_containment_before_publication`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published`
- **C2 CLOSURE recheck removed** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, base, revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_source_closure_checks_containment_against_the_landing_base_before_every_order`, `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_an_automatic_on_candidate_outside_its_boundary_before_any_order`, `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release`
- **C3 symlink mode allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `FORBIDDEN_MODES = {"120000": "a symbolic link", "160000": "a submodule"}` -> `FORBIDDEN_MODES = {"160000": "a submodule"}` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[symlink]`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published[symlink]`
- **C4 protected path allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if compared is not None and any(under(compared.casefold(), entry) for entry in protected):` -> `if False:` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[protected]`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published[protected]`
- **C5 containment skipped for automatic-on** (`src/alienintent/invocation_runtime/application/real_worker.py`): `or context.release_policy != "automatic-on":` -> `or context.release_policy == "automatic-on":` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published`, `tests/execution_coordination/test_containment_wiring.py::test_without_a_plan_authority_no_automatic_on_candidate_is_published`
- **C6 scope compared case-folded** (`src/alienintent/execution_coordination/domain/plan_authority.py`): `return stripped.casefold() if fold else stripped` -> `return stripped.casefold()` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[scope-is-exact-case]`
- **C7 protected paths compared with exact case** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if compared is not None and any(under(compared.casefold(), entry) for entry in protected):` -> `if compared is not None and any(under(compared, entry) for entry in protected):`; `protected = [path for path in (normalized(entry, fold=True) for entry in protected_paths) if path is not None]` -> `protected = [path for path in (normalized(entry) for entry in protected_paths) if path is not None]` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[protected-ignores-case]`
- **B1 CLOSURE checks the release-baseline diff, not the landing base** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, base, revision)` -> `violations = self._scope_violations(clone, identity, self._registry.assessment.authorizations.release_authorization(identity).baseline, revision)` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release`
- **B2 worker-reported start used as the diff start** (`src/alienintent/invocation_runtime/application/real_worker.py`): `starting_tree = reader.tree(workspace.path, reader.revision(workspace.path))` -> `starting_revision = reader.revision(workspace.path)
            starting_tree = reader.tree(workspace.path, starting_revision)` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_a_worker_reported_start_cannot_narrow_the_diff`, `tests/execution_coordination/test_containment_wiring.py::test_without_a_trusted_starting_revision_no_automatic_on_candidate_is_published`
- **B3 current-authority condition removed from release-by-policy** (`src/alienintent/composition/work_registry.py`): `return contract.release_policy == "automatic-on" and current is not None \
        and not outside_authority(contract, current)` -> `return contract.release_policy == "automatic-on"` -> must fail: `tests/composition/test_work_registry.py::test_a_new_plan_approval_stops_an_item_released_under_the_old_one`
- **CD1 conftest.py allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if name == CONFTEST:` -> `if False:` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[conftest]`
- **BL1 outside_authority check removed from the landing gate** (`src/alienintent/composition/work_registry.py`): `outside = outside_authority(contract, current)` -> `outside = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_outside_the_current_plan_authority_and_raises_one_owner_decision`, `tests/execution_coordination/test_containment_wiring.py::test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced`, `tests/composition/test_worker_launch.py::test_an_item_released_under_one_plan_revision_does_not_land_after_another_is_approved`
- **SR settle-retry re-land check removed** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, order["base"], revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced`

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (can defer, recorded in decisions section 19)
- Code that drives containment but is not on the protected list (the raw-diff parser, the intake reader, the
  satisfiability wiring) can be edited by a later obligation; the wiring tests and the regression gate catch removal.
- Without a worker user, the PRODUCER diff is read in the worker's workspace (CLOSURE's fresh clone is the backstop).
- Items stopped by a new approval in `start()` get no per-item signal (they are not eligible; `launch()` holds them typed).
- An approved plan with no protected paths cannot run automatic work (fails closed).
- The NO-CHANGE tree check still reads the starting tree through the worker (pre-existing).

## 4. Evidence and review record

The prototype is exactly section 2's diff on `17910f7`:
`manual/path-to-done/plan-authority/prototype-on-17910f7.diff`, sha256 `35686536…a2b95`. 548 targeted tests
pass across 18 files; the fitness check passes; the 17 mutations behave as stated (`mutations.log`, run independently by
the main session). Reviews: adversarial review FAIL (B1 CLOSURE checked the release-baseline diff, B2 worker-reported
start, B3 old approvals kept running) -> fixed test-first; follow-up FAIL (BL-1: VERIFY/ACCEPT items under an old
approval could land) -> fixed at the landing gate with the re-land re-check.

**Revision 3 (2026-10-09).** Rebuilt on `17910f7` from revision 2 plus the design delta
(`manual/path-to-done/plan-authority/rev3-design-delta.md`).
