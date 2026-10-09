# Work unit: the VERIFIER consumes the regression gate's whole-suite result and never reruns the suite

**Label:** `VERIFIER-CONSUMES-REGRESSION-GATE-EVIDENCE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-09, for independent review. Not registered, not assessed, not released.
**Position on the path (Founder 2026-10-09, decisions sections 13 and 15):** VERIFIER-CONSUMES-REGRESSION-GATE-EVIDENCE
-> NO-CHANGE -> PLAN-AUTHORITY-INHERITANCE -> BOUNDED-ROUTINE-LAUNCH -> terminal board statuses + schema hardening ->
Work Preparation / READY refill -> three-item autonomy proof.
**Starting revision:** main `b097ee3`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

**The whole-suite regression gate is the sole owner of whole-suite execution.**

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "The REGRESSION-GATE is the sole owner of whole-suite execution. When it passes for a VERIFIER invocation, its result (baseline, candidate, no regression, receipt) is added to the VERIFIER session's instructions before the session starts, with the rule not to run the whole suite and to run only the package's acceptance tests and mutations and narrowly targeted tests a finding needs. When the gate produces no result (`feature-regressions-missing`), no session starts and the item takes the typed, bounded VERIFIER infrastructure retry; a missing result is never compensated by a whole-suite run.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-09: The whole-suite regression gate is the sole owner of whole-suite execution. The VERIFIER consumes that result as trusted control-plane evidence and must not rerun the whole suite.",
  "Founder 2026-10-09: the VERIFIER runs only work-item acceptance tests, required mutations/negative controls, and narrowly targeted investigation justified by a finding; an absent or invalid gate result is a typed infrastructure failure, never silently compensated by running the whole suite.",
  "Founder 2026-10-09: the baseline cache (regression_gate.py, <baselines>/<sha>.json) already works and stays untouched; no pytest-xdist; broader-than-needed targeted runs are a separate optimisation, not in this item.",
  "The VERIFIER package is assembled before the gate runs (the gate's baseline comes from that assembly), so the gate result reaches the session through its instructions, which are read when the session starts, after the gate."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "tests/composition/test_worker_launch.py"
 ],
 "excluded_scope": [
  "the regression gate itself (regression_gate.py) and its baseline cache",
  "the VERIFIER package's fields and the context assembly",
  "pytest-xdist or any test parallelism",
  "the PRODUCER and CLOSURE paths"
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
  "the VERIFIER runs mutations G1-G3 of check 3 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "narrowing which targeted tests a VERIFIER chooses"
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
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

A VERIFIER cost up to three whole-suite runs (~10 min each): the gate at the baseline (only when main moved; cached by
commit), the gate at the candidate, and the VERIFIER session's own run, because the session was never given the gate's
result (`RealWorkerProvider._evaluate`: `prepare` builds the package, `_gate` runs, then the session starts, and only
the receipt digest reaches `read_verdict`). A gate that produced no result (`feature-regressions-missing`) was an
untyped "not attributable" hold needing the Founder.

## 2. The change: exactly this diff at `b097ee3`

- `real_worker.py`: after `_gate` passes, `_evaluate` calls the preparation hook's `gated(invocation, baseline,
  revision, receipt)` when it has one (documented on `WorkerPreparation`).
- `work_registry.py`: `LaunchPreparation.gated` appends `GATE_PASSED` (the gate's baseline, candidate, no-regression
  statement and receipt; "Do not run the whole suite"; what to run instead) to the kept instruction text, which
  `command` hands to the session when it starts.
- `worker_provider.py`: `feature-regressions-missing` joins `VERIFIER_INFRASTRUCTURE`, so it takes the typed, bounded
  VERIFIER retry and then the typed hold `verifier-infrastructure-exhausted:feature-regressions-missing`.

```diff
diff --git a/src/alienintent/composition/work_registry.py b/src/alienintent/composition/work_registry.py
index 7ba7572..08514b7 100644
--- a/src/alienintent/composition/work_registry.py
+++ b/src/alienintent/composition/work_registry.py
@@ -1216,6 +1216,12 @@ nothing there. Read the package and decide which of its closure_actions to reque
 as {{"identity": "<the work item id>", "revision": "<the candidate commit, git rev-parse HEAD>",
 "actions": ["<some of the five names>"], "findings": ["<finding>", ...]}}. The revision is the bare 40-hex commit
 alone, never the package's candidate identity. The control plane performs and checks every effect; nothing else you write is read."""
+GATE_PASSED = """
+
+REGRESSION-GATE, control-plane evidence already established for you: the whole suite (`tests` and `tools`) ran at the
+baseline {baseline} and at this candidate {revision}; no test that passed at the baseline fails here and no new test
+fails ({receipt}). Do not run the whole suite. Run only the acceptance tests and mutations the package names, and
+narrowly targeted tests when a finding needs them."""
 VERIFIER_RESULT = """Your current working directory is a fresh clone of the candidate. Verify it against the package.
 Then write .alienintent/verdict.json in that directory as {{"revision": "<the candidate commit, git rev-parse HEAD>",
 "verdict": "accept" or "reject", "findings": ["<finding>", ...]}}; a reject needs at least one finding."""
@@ -1402,6 +1408,15 @@ class LaunchPreparation:
             temporary.unlink(missing_ok=True)
             raise
 
+    def gated(self, invocation: WorkerInvocation, baseline: str, revision: str, receipt: str) -> None:
+        """The REGRESSION-GATE passed for this VERIFIER invocation: its result is added to the session's instructions,
+        which are read when the session starts. The gate owns whole-suite execution; the VERIFIER never reruns it."""
+        kept = self.kept.get(invocation.correlation_id)
+        if kept is not None:
+            route, text = kept
+            self.kept[invocation.correlation_id] = (route, text + GATE_PASSED.format(
+                baseline=baseline, revision=revision, receipt=receipt))
+
     def command(self, invocation_id: str, role: object, workspace: Path) -> tuple[list[str], str]:
         """CliWorkerProvider's per-invocation command: the provider command for the kept route and this workspace,
         and the instruction text for standard input."""
diff --git a/src/alienintent/execution_coordination/ports/worker_provider.py b/src/alienintent/execution_coordination/ports/worker_provider.py
index aaccd80..bf02c41 100644
--- a/src/alienintent/execution_coordination/ports/worker_provider.py
+++ b/src/alienintent/execution_coordination/ports/worker_provider.py
@@ -16,10 +16,13 @@ PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"
 # re-dispatched once under the composed replacement allowance.
 MISSING_TERMINAL_RESULT = "missing-terminal-result"
 # VERIFIER outcomes that carry no engineering judgment: the session ended without a valid verdict (its process failed
-# or timed out, or it left no verdict, a malformed one or one for another revision). The coordinator retries the
-# VERIFIER on the same candidate; only a valid REJECT is a rejection. A candidate that cannot be retrieved
-# (`candidate-unavailable`) is a custody refusal, not infrastructure: it still holds.
-VERIFIER_INFRASTRUCTURE = frozenset({"failure", "timeout", "verdict-missing", "verdict-malformed", "verdict-miscorrelated"})
+# or timed out, or it left no verdict, a malformed one or one for another revision), or the REGRESSION-GATE produced
+# no whole-suite result (`feature-regressions-missing`): the gate alone owns whole-suite execution, so a missing result
+# is never compensated by a session running the suite. The coordinator retries the VERIFIER on the same candidate; only
+# a valid REJECT is a rejection. A candidate that cannot be retrieved (`candidate-unavailable`) is a custody refusal,
+# not infrastructure: it still holds.
+VERIFIER_INFRASTRUCTURE = frozenset({"failure", "timeout", "verdict-missing", "verdict-malformed", "verdict-miscorrelated",
+                                     "feature-regressions-missing"})
 
 
 @dataclass(frozen=True)
diff --git a/src/alienintent/invocation_runtime/application/real_worker.py b/src/alienintent/invocation_runtime/application/real_worker.py
index 7e49a17..cfc0440 100644
--- a/src/alienintent/invocation_runtime/application/real_worker.py
+++ b/src/alienintent/invocation_runtime/application/real_worker.py
@@ -194,7 +194,9 @@ class WorkerPreparation(Protocol):
     `prepare` is called first in `_produce` (`clone` None) and in `_evaluate` right after the fresh candidate clone
     is made (`clone` that clone). It returns the PRODUCER's starting revision (ignored for the VERIFIER) or a complete
     refusal outcome, returned unchanged with nothing started. `published` is called after a PRODUCER candidate is
-    published and read back, with that candidate; it must not raise.
+    published and read back, with that candidate; it must not raise. `gated`, when the hook has it, is called in
+    `_evaluate` after the REGRESSION-GATE passed and before the session starts, with the baseline, the candidate
+    revision and the gate's receipt; it must not raise.
     """
 
     def prepare(self, invocation: WorkerInvocation, clone: Path | None) -> str | WorkerOutcome: ...
@@ -366,6 +368,10 @@ class RealWorkerProvider(WorkerProvider):
                 if isinstance(gated, WorkerOutcome):
                     return gated
                 gate_receipt = gated
+                passed = getattr(self._preparation, "gated", None)
+                if passed is not None and self._regression_base is not None:
+                    # The session is told the whole suite is proven, so it never runs it again.
+                    passed(invocation, self._regression_base(invocation.correlation_id), _revision_of(candidate), gated)
             result = self._process.run(invocation.correlation_id, InvocationRole.VERIFIER, workspace, budget.hard_wall_clock_seconds)
             if result.kind != "success":
                 return WorkerOutcome(result.kind)
diff --git a/tests/composition/test_worker_launch.py b/tests/composition/test_worker_launch.py
index b107574..267fdcc 100644
--- a/tests/composition/test_worker_launch.py
+++ b/tests/composition/test_worker_launch.py
@@ -2291,3 +2291,35 @@ def test_an_overtaken_write_whose_read_back_fails_is_still_reowed(closing, monke
     assert closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1
     closing.fx.loaded().project_cards()
     assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
+
+
+# --- VERIFIER-CONSUMES-REGRESSION-GATE-EVIDENCE: the gate is the sole owner of whole-suite execution ----------------
+
+def test_the_verifier_is_told_the_gate_result_and_not_to_run_the_whole_suite(fx):
+    item = fx.authorized("UNIT")
+    baseline = fx.main()
+    fx.launch(item.id)
+    revision = fx.loaded().coordinator(None, None).state(item.id).candidate.locator.rpartition("@")[2]
+    fx.launch(item.id)
+    [session] = fx.runs("VERIFIER")
+    text = session["stdin"]
+    assert "REGRESSION-GATE, control-plane evidence already established for you" in text
+    assert f"at the\nbaseline {baseline} and at this candidate {revision}" in text and "feature-regressions:sha256:" in text
+    assert "Do not run the whole suite." in text
+
+
+def test_a_missing_gate_result_is_typed_infrastructure_never_a_session(fx, monkeypatch):
+    """No whole-suite result: no VERIFIER session starts to compensate; the same candidate waits for a retry."""
+    from alienintent.invocation_runtime.application.regression_gate import RegressionGate, SuiteUnrunnable
+
+    def unrunnable(self, *args):
+        raise SuiteUnrunnable("the suite could not run")
+    monkeypatch.setattr(RegressionGate, "check", unrunnable)
+    item = fx.authorized("UNIT")
+    fx.launch(item.id)
+    before = fx.loaded().coordinator(None, None).state(item.id)
+    fx.launch(item.id)
+    state = fx.loaded().coordinator(None, None).state(item.id)
+    assert (state.stage, state.outcome, state.record["verifier_failure"]) == (
+        LifecycleStage.VERIFY, "verifier-retry", "feature-regressions-missing")
+    assert state.candidate == before.candidate and fx.runs("VERIFIER") == []
```

## 3. Acceptance checks

1. **The VERIFIER is told the gate result and not to run the whole suite**
   (`tests/composition/test_worker_launch.py::test_the_verifier_is_told_the_gate_result_and_not_to_run_the_whole_suite`): the session's instructions carry
   the release baseline and the candidate commit, the receipt and "Do not run the whole suite."
2. **A missing gate result is typed infrastructure, never a session**
   (`tests/composition/test_worker_launch.py::test_a_missing_gate_result_is_typed_infrastructure_never_a_session`): the suite cannot run; no VERIFIER session
   starts; the item stays at VERIFY on the same candidate with `verifier-retry`, `verifier_failure`
   `feature-regressions-missing`.
3. **Mutations, run exactly by the VERIFIER** (each must fail its named test and pass when reverted):
   - **G1:** the `passed(invocation, ...)` call in `_evaluate` replaced by `pass` -> check 1's test.
   - **G2:** `"feature-regressions-missing"` removed from `VERIFIER_INFRASTRUCTURE` -> check 2's test.
   - **G3:** "Do not run the whole suite. " removed from `GATE_PASSED` -> check 1's test.

The whole suite at the candidate has no failed or error test case: proven by the factory's REGRESSION-GATE. This item's
own VERIFIER follows this item's rule and does not rerun it. `python3 tools/fitness/check_architecture.py --root
src/alienintent --check all` passes.

### Stated limits

- The rule is an instruction to the VERIFIER session; nothing technically stops a session from running the suite.
- A gate that cannot run for a reason in the candidate itself is retried like any infrastructure failure (the gate
  reruns the candidate suite; the baseline is cached) before the typed hold.

## 4. Evidence and review record

A prototype that is exactly section 2's diff, on `b097ee3`: `manual/path-to-done/verifier-gate-evidence/
prototype-on-b097ee3.diff`, sha256 `ee4ed86a…825fc`. The touched test files (`test_worker_launch.py`,
`test_regression_gate.py`, `test_runtime.py`, `test_role_orchestration.py`, `test_factory_coordinator.py`,
`test_lifecycle_capstone.py`) pass (264), the architecture fitness check passes, and G1-G3 each fail their named test and
pass when reverted (`mutations-and-targeted-run.log`).

**Revision 1 (2026-10-09).** First draft, from the Founder's decisions (sections 13 and 15).
