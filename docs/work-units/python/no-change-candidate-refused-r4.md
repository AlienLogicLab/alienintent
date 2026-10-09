# Work unit: a PRODUCER that changes nothing does not produce a candidate

**Label:** `NO-CHANGE-CANDIDATE-REFUSED-R4` (a document label; permanent id `70fb98d1-c94b-40e4-88f7-d44a8cbc612c`).
**Status:** R4 revision 1 (work item `70fb98d1-c94b-40e4-88f7-d44a8cbc612c`, at CAPTURE), 2026-10-09. Reviewed (PASS). Not approved, not assessed, not released.
**Re-issue:** the same approved requirement as NO-CHANGE-CANDIDATE-REFUSED revision 5 (`77d48c83`), R2 (`c15a52f6`) and
R3 (`fe2db2d3`). R3 is terminal under the old implementation with no engineering verdict (its VERIFIER lost the network
after the gate passed: 2913 tests, 0 failures). Critical path step 2 (Founder 2026-10-09, decisions section 16): no more
work on this requirement once it lands.
**Starting revision:** main `4dff19e`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "70fb98d1-c94b-40e4-88f7-d44a8cbc612c",
 "version": "r4-revision-1",
 "intent": "When a PRODUCER's process succeeds but its claimed revision has the same git tree as the starting revision (the same commit, an empty commit, or a commit that is later reverted), the factory publishes no candidate. It records a typed no-change PRODUCER result with a finding, and the work item stays in IMPLEMENT as a rework within its attempt budget. No VERIFIER attempt is used. A descendant commit with a different tree is admitted as today.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: a PRODUCER assigned to IMPLEMENT must produce a repository change. If it returns the starting revision unchanged, implementation did not occur.",
  "Founder 2026-10-06: candidate == starting revision -> typed no-change PRODUCER result -> finding -> _rework -> remains IMPLEMENT -> no VERIFIER attempt consumed.",
  "Founder 2026-10-06: the current work item contract has no authorized no-repository-change execution mode. This repair therefore refuses unchanged candidates. Introducing such a mode requires a separate contract and schema decision and is out of scope.",
  "Founder 2026-10-06: the rejection test is discriminating: restoring the ancestor-only check makes it fail.",
  "Founder 2026-10-08: 'changed the repository' means the candidate's git tree differs from the starting revision's git tree (`<revision>^{tree}`). Commit identity is not enough: an empty commit, a commit then its revert, or any other commit whose contents equal the starting revision's is no-change. The check is made in `_produce` (so the coordinator sees the no-change result at once) and in `hand_over` (the custody backstop).",
  "Founder 2026-10-08: tests cover the same commit, an empty descendant commit and a commit-then-revert (each refused), and a descendant commit with a different tree (accepted).",
  "Founder 2026-10-09: this item re-issues work item 77d48c83 (packet 4dd5c48, revision 5) against baseline bc9a9d8 with the same approved requirement; its candidate is independently assessed and verified, and the ratification of candidate 6c16563 does not transfer.",
  "Founder 2026-10-09: R3 re-issues R2 (work item c15a52f6, VERIFIER process failure with cause UNKNOWN) against the same baseline bc9a9d8; R2's candidate 76c5795 is not reused.",
  "Founder 2026-10-09: R4 re-issues NO-CHANGE on main 4dff19e as the critical path's step 2 ('Re-issue and land NO-CHANGE-CANDIDATE-REFUSED ... no more work on this requirement once it lands'); R3 (fe2db2d3) is terminal under the old implementation with no engineering verdict (network outage); the exact change is R3's gate-passing candidate 105ecc8 carried onto 4dff19e."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/ports/source_control.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "tests/invocation_runtime/test_no_change_candidate.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/execution_coordination/test_factory_coordinator.py"
 ],
 "excluded_scope": [
  "any contract or schema field that allows a no-change work item",
  "the lifecycle transition rules in execution_coordination/domain/lifecycle.py",
  "the VERIFIER, CLOSURE and Landing Authority paths",
  "the regression gate (invocation_runtime/application/regression_gate.py) and its call in RealWorkerProvider._evaluate",
  "BOUNDED-ROUTINE-LAUNCH and BOARD-FOLLOWS-WORK-STATE changes"
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
  "acceptance checks 1-3 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff from the starting revision equals section 2's diff",
  "the VERIFIER runs mutations M1, M2, M3 and M5 of check 3 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "keeping the worker session's text: the durable evidence is the journal, the workspace and the coordinator record"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/automated-closure.md"
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
  "the change would need a lifecycle transition rule change",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. What it does

When a PRODUCER's process succeeds but its claimed revision has the same git tree as the starting revision (the same
commit, an empty commit, or a commit that is later reverted), the factory publishes no candidate: `_produce` records a
typed `no-change` result with a finding, the item stays at IMPLEMENT as a rework within its attempt budget, and no
VERIFIER attempt is used. The intake hand-over refuses a candidate with the starting tree as a custody backstop. A
descendant commit with a different tree is admitted as today.

## 2. The change: exactly this diff at `4dff19e`

R3's gate-passing candidate `105ecc8` carried onto `4dff19e` (two import/constant unions with the VERIFIER-retry lines
that landed meanwhile). Line numbers are in the diff.

```diff
diff --git a/src/alienintent/execution_coordination/application/factory_coordinator.py b/src/alienintent/execution_coordination/application/factory_coordinator.py
index 4e1db88..4b5d2ab 100644
--- a/src/alienintent/execution_coordination/application/factory_coordinator.py
+++ b/src/alienintent/execution_coordination/application/factory_coordinator.py
@@ -20,7 +20,7 @@ from alienintent.execution_coordination.domain.verdict import EvidenceDefinition
 from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected, VersionConflict
 from alienintent.execution_coordination.ports.release_admission import ExecutionAllocation
 from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
-from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, PRODUCER, VERIFIER, VERIFIER_INFRASTRUCTURE, WorkerInvocation, WorkerOutcome, WorkerProvider
+from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, NO_CHANGE, PRODUCER, VERIFIER, VERIFIER_INFRASTRUCTURE, WorkerInvocation, WorkerOutcome, WorkerProvider
 from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth
 
 # K2: each nonterminal stage is advanced by exactly one canonical role.
@@ -503,6 +503,8 @@ class FactoryCoordinator:
             # own role on the same custodied candidate, bounded at launch.
             return _Advance(current, outcome.kind, {})
         if invocation.role == PRODUCER:
+            if outcome.kind == NO_CHANGE:
+                return self._rework(item, current, prior, invocation, "producer", tuple(outcome.findings))
             if outcome.kind != "success" or outcome.candidate is None:
                 return _Advance(current, outcome.kind, {})
             # The custody gate is control-plane enforcement: it always rechecks
@@ -607,7 +609,7 @@ class FactoryCoordinator:
             "source": source, "correlation": invocation.correlation_id,
             "candidate": None if state.candidate is None else state.candidate.identity, "findings": list(findings),
         }]
-        reworked = transition(state, state.version, "rework")
+        reworked = state if source == "producer" else transition(state, state.version, "rework")
         fields: dict[str, object] = {"rejections": rejections, "findings": recorded}
         if rejections >= item.contract.budget_policy.maximum_attempts:
             return _Advance(reworked, "failure", fields | {"hold_reason": "attempt-budget-exhausted"})
diff --git a/src/alienintent/execution_coordination/ports/worker_provider.py b/src/alienintent/execution_coordination/ports/worker_provider.py
index 3d1a824..d2de130 100644
--- a/src/alienintent/execution_coordination/ports/worker_provider.py
+++ b/src/alienintent/execution_coordination/ports/worker_provider.py
@@ -15,6 +15,7 @@ PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"
 # verdict, candidate or failure: the stage is unchanged and its role may be
 # re-dispatched once under the composed replacement allowance.
 MISSING_TERMINAL_RESULT = "missing-terminal-result"
+NO_CHANGE = "no-change"
 # VERIFIER outcomes that carry no engineering judgment: the session ended without a valid verdict (its process failed
 # or timed out, or it left no verdict, a malformed one or one for another revision), or the feature-regression
 # receipt is absent or invalid (`feature-regressions-missing`: the REGRESSION-GATE produced no whole-suite result, or,
diff --git a/src/alienintent/invocation_runtime/adapters/git_source_control.py b/src/alienintent/invocation_runtime/adapters/git_source_control.py
index 95b2064..4fc388b 100644
--- a/src/alienintent/invocation_runtime/adapters/git_source_control.py
+++ b/src/alienintent/invocation_runtime/adapters/git_source_control.py
@@ -78,6 +78,9 @@ class GitSourceControl(SourceControl):
             raise CandidateUnavailable("candidate revision is not immutable")
         return revision
 
+    def tree(self, workspace: Path, revision: str) -> str:
+        return self._git("rev-parse", "--verify", f"{revision}^{{tree}}", cwd=workspace)
+
     def read_back_candidate(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
         remote_url = self._git("remote", "get-url", remote, cwd=workspace)
         return self._read_back(remote_url, branch, revision, verifier_workspace, workspace)
@@ -265,6 +268,12 @@ class IntakeSourceControl(GitSourceControl, SourceControl):
             raise CandidateUnavailable("candidate revision is not immutable")
         return claimed
 
+    def tree(self, workspace: Path, revision: str) -> str:
+        tree = self._as_worker(workspace, "git", "rev-parse", "--verify", f"{revision}^{{tree}}")
+        if not _FULL_SHA.fullmatch(tree):
+            raise CandidateUnavailable("candidate tree is not immutable")
+        return tree
+
     def intake_ref(self, correlation: str) -> str:
         return f"refs/intake/{ref_safe(correlation)}"
 
@@ -290,7 +299,9 @@ class IntakeSourceControl(GitSourceControl, SourceControl):
             raise CandidateUnavailable("imported candidate differs from the claim")
         if self._intake_git("merge-base", "--is-ancestor", starting, claimed).returncode:
             raise CandidateUnavailable("candidate does not descend from the starting revision")
-        self._intake_out("rev-parse", "--verify", f"{claimed}^{{tree}}")  # custody facts, read in the intake only
+        tree = self._intake_out("rev-parse", "--verify", f"{claimed}^{{tree}}")
+        if tree == self._intake_out("rev-parse", "--verify", f"{starting}^{{tree}}"):
+            raise CandidateUnavailable("candidate tree equals the starting revision's tree")
         return ref
 
     def _copy_bundle(self, source: Path, target: Path) -> Path:
diff --git a/src/alienintent/invocation_runtime/application/real_worker.py b/src/alienintent/invocation_runtime/application/real_worker.py
index cfc0440..7b79ae6 100644
--- a/src/alienintent/invocation_runtime/application/real_worker.py
+++ b/src/alienintent/invocation_runtime/application/real_worker.py
@@ -1,4 +1,8 @@
-"""PY-06 composition bridge: a real CLI can yield only custodied source revisions."""
+"""PY-06 composition bridge: a real CLI can yield only custodied source revisions.
+
+The current work item contract has no no-repository-change mode: every successful
+PRODUCER must change the starting revision's git tree.
+"""
 
 from __future__ import annotations
 
@@ -12,7 +16,7 @@ from typing import Protocol
 from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
 from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
 from alienintent.execution_coordination.ports.worker_provider import (
-    MISSING_TERMINAL_RESULT, WorkerInvocation, WorkerOutcome, WorkerProvider)
+    MISSING_TERMINAL_RESULT, NO_CHANGE, WorkerInvocation, WorkerOutcome, WorkerProvider)
 from alienintent.invocation_runtime.application.regression_gate import RegressionGate, SuiteUnrunnable
 from alienintent.invocation_runtime.domain.diagnostics import cause
 from alienintent.invocation_runtime.domain.runtime import FEATURE_REGRESSION_RECEIPT_PATH, VERDICT_PATH, BudgetIneligible, BudgetRecord, CandidateUnavailable, CapabilityGrant, InvocationRole, JournalUnreadable, ProcessResult, ReservationBook, RetryEvidence, RetrySchedule, VerifierIndependence, owner_token, require_eligible, workspace_folder
@@ -215,6 +219,8 @@ class CandidateHandover(Protocol):
 
     def revision(self, workspace: Path) -> str: ...
 
+    def tree(self, workspace: Path, revision: str) -> str: ...
+
     def hand_over(self, correlation: str, workspace: Path, claimed: str, starting: str) -> str: ...
 
     def publish_intake(self, correlation: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
@@ -547,6 +553,8 @@ class RealWorkerProvider(WorkerProvider):
         self._active_workspaces[invocation.correlation_id] = workspace
         outcome = WorkerOutcome("failure")
         try:
+            reader = self._source if self._handover is None else self._handover
+            starting_tree = reader.tree(workspace.path, reader.revision(workspace.path))
             schedule = RetrySchedule(budget.maximum_attempts, budget.retry_limit, .01, .001)
             attempts, next_eligible = 0, None
             while True:
@@ -563,18 +571,22 @@ class RealWorkerProvider(WorkerProvider):
                 outcome = WorkerOutcome(result.kind)
             else:
                 # With a worker user the claim is the worker's and the candidate comes only from the intake import.
-                revision = (self._source if self._handover is None else self._handover).revision(workspace.path)
-                if self._journal is not None:
-                    self._journal.append({"event": PUBLICATION_STARTED, "correlation_id": invocation.correlation_id,
-                                          "work_identity": invocation.work_identity, "role": invocation.role, "revision": revision})
-                if self._handover is not None:
-                    self._handover.hand_over(invocation.correlation_id, workspace.path, revision, starting_revision)
-                    candidate = self._handover.publish_intake(invocation.correlation_id, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                revision = reader.revision(workspace.path)
+                if reader.tree(workspace.path, revision) == starting_tree:
+                    outcome = WorkerOutcome(NO_CHANGE, None, findings=(
+                        f"no-change-candidate:{revision}: the PRODUCER's revision has the starting revision's tree; IMPLEMENT requires a repository change",))
                 else:
-                    candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
-                if self._preparation is not None:
-                    self._preparation.published(invocation, candidate)
-                outcome = WorkerOutcome.success(candidate)
+                    if self._journal is not None:
+                        self._journal.append({"event": PUBLICATION_STARTED, "correlation_id": invocation.correlation_id,
+                                              "work_identity": invocation.work_identity, "role": invocation.role, "revision": revision})
+                    if self._handover is not None:
+                        self._handover.hand_over(invocation.correlation_id, workspace.path, revision, starting_revision)
+                        candidate = self._handover.publish_intake(invocation.correlation_id, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                    else:
+                        candidate = self._source.publish_and_read_back(workspace.path, self._remote, self._candidate_branch(invocation), revision, self._producer_read_back(invocation))
+                    if self._preparation is not None:
+                        self._preparation.published(invocation, candidate)
+                    outcome = WorkerOutcome.success(candidate)
         finally:
             if outcome.kind in {"success", "authority-block"}:
                 self._finished_workspaces[invocation.correlation_id] = workspace
diff --git a/src/alienintent/invocation_runtime/ports/source_control.py b/src/alienintent/invocation_runtime/ports/source_control.py
index abd5dd3..632fc2a 100644
--- a/src/alienintent/invocation_runtime/ports/source_control.py
+++ b/src/alienintent/invocation_runtime/ports/source_control.py
@@ -39,6 +39,7 @@ class PublishRef:
 
 class SourceControl(Protocol):
     def revision(self, workspace: Path) -> str: ...
+    def tree(self, workspace: Path, revision: str) -> str: ...
     def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
     def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef: ...
     def publish_refs(self, clone: Path, remote: str, refs: tuple[PublishRef, ...]) -> None: ...
diff --git a/tests/execution_coordination/test_factory_coordinator.py b/tests/execution_coordination/test_factory_coordinator.py
index 1b5b895..9ee72e3 100644
--- a/tests/execution_coordination/test_factory_coordinator.py
+++ b/tests/execution_coordination/test_factory_coordinator.py
@@ -118,6 +118,40 @@ def _coordinator(tmp_path: Path, items, outcomes):
     return coordinator.FactoryCoordinator(SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement(items), worker, artifacts, "offline"), worker, artifacts
 
 
+def test_no_change_producer_result_reworks_without_a_verifier(tmp_path: Path) -> None:
+    coordinator_module, custody, _, provider = _api()
+    item = _attempts("unchanged", 0, 0, maximum_attempts=3)
+    artifacts = custody.LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier")
+
+    class NoChangeWorker(ScriptedWorker):
+        def start(self, invocation, context, grants, budget):
+            assert invocation.role == provider.PRODUCER
+            self.invocations.append((invocation.work_identity, invocation.role, invocation.correlation_id))
+            outcome = provider.WorkerOutcome(provider.NO_CHANGE, findings=("no-change-candidate:unchanged",))
+            self.observed[invocation.correlation_id] = outcome
+            return outcome
+
+    worker = NoChangeWorker(artifacts, {})
+    coordinator = coordinator_module.FactoryCoordinator(
+        SQLiteOperationalStore(tmp_path / "run.sqlite"), MemoryWorkManagement([item]), worker, artifacts, "offline")
+    for count in (1, 2, 3):
+        coordinator.launch(item.identity)
+        state = coordinator.state(item.identity)
+        assert state.stage is LifecycleStage.IMPLEMENT and state.candidate is None
+        assert (state.implement_cycles, state.verify_cycles) == (1, 0)
+        assert state.record["rejections"] == count
+        assert len(state.record["findings"]) == count
+        assert all(entry["source"] == "producer" for entry in state.record["findings"])
+        assert all(role == provider.PRODUCER for _, role, _ in worker.invocations)
+        if count == 1:
+            version = state.version
+        assert state.version == version == 0
+        assert len(worker.invocations) == count
+        assert state.outcome == ("failure" if count == 3 else "rework")
+        if count == 3:
+            assert state.record["hold_reason"] == "attempt-budget-exhausted"
+
+
 def test_loop_drains_priority_backlog_and_skips_failure_and_timeout(tmp_path: Path) -> None:
     coordinator, worker, _ = _coordinator(tmp_path, [_item("bad", 0, 1), _item("slow", 1, 2), _item("good", 2, 3)], {"bad": ["failure"], "slow": ["timeout"], "good": ["success"]})
     summary = coordinator.start()
diff --git a/tests/invocation_runtime/test_git_source_control.py b/tests/invocation_runtime/test_git_source_control.py
index 828461d..a9d092f 100644
--- a/tests/invocation_runtime/test_git_source_control.py
+++ b/tests/invocation_runtime/test_git_source_control.py
@@ -447,6 +447,21 @@ def test_a_candidate_that_does_not_descend_from_the_starting_revision_is_refused
         handover.source.hand_over("c2", workspace, sibling, first)
 
 
+@pytest.mark.parametrize("kind", ["same-sha", "empty-commit", "commit-then-revert"])
+def test_hand_over_refuses_a_candidate_with_the_starting_tree(handover, kind):
+    workspace = handover.workspaces.allocate("c1", "owner", handover.base).path
+    if kind == "empty-commit":
+        git(workspace, *IDENTITY, "commit", "-qm", "empty", "--allow-empty")
+    elif kind == "commit-then-revert":
+        (workspace / "new.txt").write_text("change")
+        git(workspace, "add", "new.txt")
+        git(workspace, *IDENTITY, "commit", "-qm", "change")
+        git(workspace, *IDENTITY, "revert", "--no-edit", "HEAD")
+    claimed = git(workspace, "rev-parse", "HEAD")
+    with pytest.raises(CandidateUnavailable, match="candidate tree equals the starting revision's tree"):
+        handover.source.hand_over("c1", workspace, claimed, handover.base)
+
+
 def test_a_hand_over_file_not_owned_by_the_worker_is_refused(handover, monkeypatch):
     """Check 3: a regular hand-over file whose `fstat` owner is not the worker uid is refused; nothing is imported."""
     workspace, claimed = handover.produce()
diff --git a/tests/invocation_runtime/test_no_change_candidate.py b/tests/invocation_runtime/test_no_change_candidate.py
new file mode 100644
index 0000000..244b229
--- /dev/null
+++ b/tests/invocation_runtime/test_no_change_candidate.py
@@ -0,0 +1,101 @@
+"""A PRODUCER must change the starting tree before a candidate is published."""
+
+from __future__ import annotations
+
+from pathlib import Path
+import subprocess
+import sys
+import time
+
+import pytest
+
+from alienintent.execution_coordination.domain.contract import BudgetPolicy
+from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
+from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
+from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
+from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
+from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
+from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
+from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole
+
+
+def git(path: Path, *args: str) -> str:
+    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()
+
+
+def produce(tmp_path: Path, command: str):
+    remote, source = tmp_path / "remote.git", tmp_path / "source"
+    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
+    subprocess.run(["git", "init", "-q", str(source)], check=True)
+    git(source, "config", "user.email", "test@example.invalid")
+    git(source, "config", "user.name", "Test")
+    (source / "base.txt").write_text("base")
+    git(source, "add", "base.txt")
+    git(source, "commit", "-qm", "base")
+    starting = git(source, "rev-parse", "HEAD")
+    git(source, "remote", "add", "origin", str(remote))
+    process = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit", frozenset({"wall-clock", "cancellation"}))
+    invocation = WorkerInvocation("work", "producer-1")
+    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
+                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
+    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
+    worker = RealWorkerProvider(process, GitSourceControl(), source, "origin", "candidate/producer-1",
+                                tmp_path / "verifier", grant, "repo", GitWorktreeAdapter(source, tmp_path / "worktrees"),
+                                now=time.time, sleep=time.sleep, journal=journal)
+    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
+    return outcome, worker, invocation, journal.records(), remote, starting
+
+
+_EMPTY = "import subprocess; subprocess.run(['git', 'commit', '-qm', 'empty', '--allow-empty'], check=True)"
+_CHANGE = "import pathlib, subprocess; pathlib.Path('new.txt').write_text('change'); subprocess.run(['git', 'add', 'new.txt'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True)"
+_REVERT = _CHANGE + "; subprocess.run(['git', 'revert', '--no-edit', 'HEAD'], check=True)"
+
+
+@pytest.mark.parametrize("command", ["pass", _EMPTY, _REVERT], ids=["same-sha", "empty-commit", "commit-then-revert"])
+def test_a_revision_with_the_starting_tree_is_no_change(tmp_path: Path, command: str) -> None:
+    outcome, worker, invocation, records, remote, _ = produce(tmp_path, command)
+    assert outcome.kind == "no-change" and outcome.candidate is None
+    assert len(outcome.findings) == 1 and outcome.findings[0].startswith("no-change-candidate:")
+    assert git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/candidate") == ""
+    own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
+    assert not any(record["event"] == "publication-started" for record in own)
+    finished = [record for record in own if record["event"] == "invocation-outcome"]
+    assert len(finished) == 1
+    assert (finished[0]["kind"], finished[0]["candidate"], finished[0]["findings"]) == (
+        "no-change", None, list(outcome.findings))
+    assert worker.read_back(invocation) == outcome
+
+
+def test_a_revision_with_a_different_tree_is_admitted(tmp_path: Path) -> None:
+    outcome, _, _, _, remote, starting = produce(tmp_path, _CHANGE)
+    assert outcome.kind == "success" and outcome.candidate is not None
+    revision = git(remote, "rev-parse", "refs/heads/candidate/producer-1")
+    assert revision != starting and outcome.candidate.locator.endswith("@" + revision)
+
+
+def test_a_handover_revision_with_the_starting_tree_is_never_handed_over(tmp_path: Path) -> None:
+    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, ProcessResult
+
+    class Process:
+        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
+        def run(self, *_): return ProcessResult("success", 0, True, BudgetRecord.unknown())
+
+    class Workspaces:
+        def allocate(self, invocation_id, owner, baseline):
+            return type("Workspace", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
+        def cleanup(self, *_): pass
+
+    class Handover:
+        def revision(self, _): return "a" * 40
+        def tree(self, _, revision): return "b" * 40
+        def hand_over(self, *_): raise AssertionError("hand_over was called")
+        def publish_intake(self, *_): raise AssertionError("publish_intake was called")
+
+    invocation = WorkerInvocation("work", "producer-1")
+    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
+                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
+    worker = RealWorkerProvider(Process(), GitSourceControl(), tmp_path, "origin", "candidate/producer-1",
+                                tmp_path / "verifier", grant, "repo", Workspaces(), now=time.time, sleep=time.sleep,
+                                handover=Handover())
+    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
+    assert outcome.kind == "no-change" and outcome.candidate is None
diff --git a/tests/invocation_runtime/test_runtime.py b/tests/invocation_runtime/test_runtime.py
index 652fe8f..07efbfe 100644
--- a/tests/invocation_runtime/test_runtime.py
+++ b/tests/invocation_runtime/test_runtime.py
@@ -58,6 +58,7 @@ def test_real_worker_retries_a_failed_process_and_records_next_eligible_event(tm
         def cleanup(self, *_): pass
     class Source:
         def revision(self, _): return "a" * 40
+        def tree(self, _, revision): return "1" * 40
         def publish_and_read_back(self, *_): raise AssertionError("not reached")
 
     process = Process()
@@ -86,7 +87,9 @@ def test_real_worker_retains_an_authority_blocked_workspace_while_releasing_capa
         def __init__(self): self.cleaned = []
         def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
         def cleanup(self, workspace, _): self.cleaned.append(workspace.invocation_id)
-    class Source: pass
+    class Source:
+        def revision(self, _): return "0" * 40
+        def tree(self, _, revision): return "1" * 40
 
     spaces, slots = Workspaces(), ReservationBook(1, 1)
     grant = CapabilityGrant("g", "PY-07@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
@@ -115,7 +118,9 @@ def test_real_worker_waits_for_each_exponential_jittered_retry_eligibility(tmp_p
     class Workspaces:
         def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
         def cleanup(self, *_): pass
-    class Source: pass
+    class Source:
+        def revision(self, _): return "0" * 40
+        def tree(self, _, revision): return "1" * 40
 
     sleeps: list[float] = []
     grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
@@ -147,7 +152,9 @@ def test_real_worker_cancel_fences_the_live_process_releases_reservation_and_cle
         def __init__(self): self.cleaned = []
         def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
         def cleanup(self, workspace, _): self.cleaned.append(workspace.invocation_id)
-    class Source: pass
+    class Source:
+        def revision(self, _): return "0" * 40
+        def tree(self, _, revision): return "1" * 40
 
     spaces, slots = Workspaces(), ReservationBook(1, 1)
     grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
@@ -369,7 +376,7 @@ def test_real_worker_returns_only_a_published_independently_read_back_source_can
     subprocess.run(["git", "-C", str(source), "add", "candidate"], check=True)
     subprocess.run(["git", "-C", str(source), "commit", "-m", "candidate"], check=True, capture_output=True)
     subprocess.run(["git", "-C", str(source), "remote", "add", "origin", str(remote)], check=True)
-    cli = CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", frozenset({"wall-clock", "cancellation"}))
+    cli = CliWorkerProvider("python", sys.executable, ("-c", "import pathlib, subprocess; pathlib.Path('change.txt').write_text('c'); subprocess.run(['git', 'add', 'change.txt'], check=True); subprocess.run(['git', 'commit', '-qm', 'c'], check=True)"), "explicit", frozenset({"wall-clock", "cancellation"}))
     grant = CapabilityGrant("grant", "PY-06@1", "producer-1", InvocationRole.PRODUCER, "issue-54", "AlienLogicLab/alienintent", frozenset({"process-control", "git-write"}), int(time.time()) + 100)
     worker = RealWorkerProvider(cli, GitSourceControl(), source, "origin", "candidate/producer-1", tmp_path / "verifier", grant, "AlienLogicLab/alienintent", GitWorktreeAdapter(source, tmp_path / "worktrees"), now=lambda: int(time.time()), sleep=time.sleep)
 
@@ -534,7 +541,11 @@ def _preparing_worker(tmp_path: Path, prepared, *, verifier: bool = False):
             return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
         def cleanup(self, *_): pass
     class Source:
-        def revision(self, _): return "a" * 40
+        calls = 0
+        def revision(self, _):
+            Source.calls += 1
+            return "c" * 40 if Source.calls == 1 else "a" * 40
+        def tree(self, _, revision): return f"tree-of-{revision}"
         def publish_and_read_back(self, *_):
             log.append(("publish",))
             return candidate
```

## 3. Acceptance checks

1. **No-change is refused; a real change is admitted** (`tests/invocation_runtime/test_no_change_candidate.py`):
   `test_a_revision_with_the_starting_tree_is_no_change` (same-sha, empty-commit, commit-then-revert: kind `no-change`,
   no candidate, one `no-change-candidate:` finding, no `publication-started`, the journaled outcome and read-back
   agree), `test_a_revision_with_a_different_tree_is_admitted`, and
   `test_a_handover_revision_with_the_starting_tree_is_never_handed_over`.
2. **The custody backstop and the coordinator rework**
   (`tests/invocation_runtime/test_git_source_control.py::test_hand_over_refuses_a_candidate_with_the_starting_tree`,
   `tests/execution_coordination/test_factory_coordinator.py::test_no_change_producer_result_reworks_without_a_verifier`);
   the existing `test_check1_a_slot_is_a_work_item_kept_from_producer_through_verifier_and_rework` and
   `test_check8_cycle_counts_change_only_with_recorded_transitions` pass unchanged.
3. **Mutations, run exactly by the VERIFIER** (each must fail its named test and pass when reverted):
   - **M1:** `starting_tree = reader.tree(workspace.path, reader.revision(workspace.path))` made
     `starting_tree = reader.revision(workspace.path)` and `if reader.tree(workspace.path, revision) == starting_tree:`
     made `if revision == starting_tree:` -> `test_a_revision_with_the_starting_tree_is_no_change` fails exactly
     `empty-commit` and `commit-then-revert`.
   - **M2:** the two lines of `hand_over` that refuse the starting tree deleted -> all three cases of
     `test_hand_over_refuses_a_candidate_with_the_starting_tree`.
   - **M3:** `reworked = state if source == "producer" else transition(state, state.version, "rework")` made
     `reworked = transition(state, state.version, "rework")` -> `test_no_change_producer_result_reworks_without_a_verifier`.
   - **M5:** the same line made `reworked = state` -> `test_check8_cycle_counts_change_only_with_recorded_transitions`.

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Evidence and review record

The prototype is exactly section 2's diff on `4dff19e`: `manual/path-to-done/no-change-r4/prototype-on-4dff19e.diff`,
sha256 `56d7d328…ee7ed`. Its scope tests pass (139); the runtime, coordinator, orchestration, launch and
capstone test files pass (360); the fitness check passes; M1, M2, M3, M5 behave as stated
(`mutations-and-targeted-run.log`). R3's candidate `105ecc8` passed the gate (2913 tests, 0 failures) on `bc9a9d8`.

**R4 revision 1 (2026-10-09).** Re-issue as an exact diff (the method that gave zero deviations on #169-#171).
