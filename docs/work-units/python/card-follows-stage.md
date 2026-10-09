# Work unit: the board card follows canonical work state; launch never needs the card READY

**Label:** `CARD-FOLLOWS-STAGE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-09, for independent review. Not registered, not assessed, not released.
**Position on the path (Founder 2026-10-09, decisions section 10):** VERIFIER-RETRY (done, `2b47f21`) ->
CARD-FOLLOWS-STAGE -> NO-CHANGE -> PLAN-AUTHORITY-INHERITANCE -> BOUNDED-ROUTINE-LAUNCH -> Work Preparation / READY
refill -> three-item autonomy proof.
**Starting revision:** main `2b47f21`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

**The board reflects canonical Work state; it does not determine canonical Work state.**

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "The GitHub Project card of each registry work item shows its canonical stage: IMPLEMENT when its PRODUCER starts, then VERIFY, IMPLEMENT on rework, ACCEPT and DONE, each written to the linked card and read back. A started work item launches from its registry record at any stage, so execution never depends on the card staying READY. A card write that fails or does not read back is a durable diagnostic, never a launch failure. The board reflects canonical Work state; it does not determine canonical Work state.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-09: The board reflects canonical Work state; it does not determine canonical Work state.",
  "Founder 2026-10-09: project IMPLEMENT, VERIFY, ACCEPT, DONE from canonical Work state to the linked card; use the existing started_item path so execution does not depend on the card remaining READY; projection failure becomes a durable diagnostic, never a launch blocker; independent read-back confirms the board state; do not redesign GitHub integration.",
  "Founder 2026-10-09: READY becomes a projection too once plan authority removes the board as source of truth; until then the READY snapshot still admits a work item's first launch.",
  "Founder 2026-10-09: while building, run only the affected tests; the factory's regression gate owns the whole-suite run."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/composition/lifecycle_capstone.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_work_registry.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/execution_coordination/test_role_orchestration.py"
 ],
 "excluded_scope": [
  "the GitHub adapters (github_work_management.py, github_projects_v2.py) and any redesign of the GitHub integration",
  "the READY snapshot as the source of a first launch and of priority (plan authority's item)",
  "guard_account, _block_dependents and record_decision, which still read the READY snapshot",
  "the lifecycle transition rules and the closure actions"
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
  "the VERIFIER runs mutations C1-C5 of check 4 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a REVIEW card state (REVIEW is never a recorded stage)",
  "removing a retired or failed item's card from the board"
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

## 1. Why

Founder-reported and live: a registry work item's card stays READY while the item is at IMPLEMENT, VERIFY and ACCEPT
(#169 showed READY at VERIFY on 2026-10-09). The registry's board view is built with no projection fields and no
writer (`work_registry.py` `_ready_view`), so every `project_execution_state` call answers "unconfirmed unsupported
projection"; only READY is read from the board and DONE written by CLOSURE. Making the card truthful has one real
consequence: `launch` takes an item at IMPLEMENT or VERIFY only from the READY snapshot (cards whose Status is READY),
and resolves a started item from its registry record (`started_item`) only at ACCEPT; `start` reads only the snapshot.
So the card can only follow the stage if a started item launches from its registry record at every stage. A recorded
decision drops the item's `correlation` (it is not carried), so that resolution falls back to the carried
`producer_correlation`, whose `invocation-started` record always exists.

## 2. The change: exactly this diff at `2b47f21`

The candidate's diff from `2b47f21` is exactly this (`git apply` applies it at the starting revision):

- `factory_coordinator.py`: `launch` resolves a started item through `_resolve` at every stage in `ROLE_BY_STAGE`
  (the ACCEPT checks are unchanged); `_resolve` tries the record's `correlation`, then `producer_correlation`; new
  `_with_started` adds every recorded, non-final started item the snapshot does not show, and `start` uses it; a
  PRODUCER dispatch projects IMPLEMENT just before the worker starts.
- `work_registry.py`: `CARD_STAGES` (IMPLEMENT, VERIFY, ACCEPT, DONE -> Status) and `PROJECTION_DIAGNOSTICS`; the
  registry board view gets `CARD_STAGES` and `projection_write=self._project_card`; `_project_card` writes the Status
  to the work item's linked card through the existing `write_status` (which reads it back) and, when the answer is not
  the revision (no linked card, an exception, or another status read back), appends one JSON line to
  `launch/projection-diagnostics.jsonl` and answers -1. It never raises.
- `lifecycle_capstone.py`: check L6's expected receipts gain IMPLEMENT at each PRODUCER start.
- Tests that change because the card now tells the truth: the registry view test (projection fields and writer),
  the coordinator's projected revisions (`[0, 1, 3, 4]`), four orchestration projection lists (IMPLEMENT at
  dispatch), and four launch assertions where the card is ACCEPT, not READY, at ACCEPT (one of them was DONE: CLOSURE
  wrote DONE, then cleanup failed, so the item is canonically still ACCEPT and the card now says so). Three new tests.

```diff
diff --git a/src/alienintent/composition/lifecycle_capstone.py b/src/alienintent/composition/lifecycle_capstone.py
index 5bc6b5a..8d1d950 100644
--- a/src/alienintent/composition/lifecycle_capstone.py
+++ b/src/alienintent/composition/lifecycle_capstone.py
@@ -387,8 +387,8 @@ def lifecycle(root: Path, document, manifest_path: Path, environment) -> tuple[l
               "each verifier invocation is distinct from every producer and judged a fresh clone at exactly the candidate it was given", {"verifier_heads": verifier_heads, "judged": [revision_of(v.locator) if v else None for v in verified]}),
         check("L5", "rejection recorded and reworked into a fresh candidate", record.get("rejections") == 1 and len(findings) == 1 and findings[0].get("source") == "verifier" and findings[0].get("correlation") == verifiers[0][0] and findings[0].get("findings"),
               "one attributable verifier finding under the rejecting invocation; rejections = 1", {"findings": findings, "rejections": record.get("rejections")}),
-        check("L6", "no success-collapse projection", receipts == [("release-proposed", None), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "IMPLEMENT"), ("release-proposed", None), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "ACCEPT"), ("execution-state-projected", "DONE")],
-              "each producer run passes release admission; the kernel projects VERIFY, IMPLEMENT (rework), VERIFY, ACCEPT and DONE, each after its own role outcome", {"receipts": receipts}),
+        check("L6", "no success-collapse projection", receipts == [("release-proposed", None), ("execution-state-projected", "IMPLEMENT"), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "IMPLEMENT"), ("release-proposed", None), ("execution-state-projected", "IMPLEMENT"), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "ACCEPT"), ("execution-state-projected", "DONE")],
+              "each producer run passes release admission and projects IMPLEMENT as it starts; the kernel projects VERIFY, IMPLEMENT (rework), VERIFY, ACCEPT and DONE, each after its own role outcome", {"receipts": receipts}),
         check("L7", "actual closure receipts", closures and record.get("receipts") == ["candidate-published"] and record.get("closure") == ["candidate-published"] and closure_head == revisions[-1],
               "closure performed and read back candidate-published by re-retrieving the accepted revision into a fresh clone", {"receipts": record.get("receipts"), "closure_clone_head": closure_head}),
         check("L8", "exactly one effect per invocation, each confirmed", [e[0] for e in ledger] == sorted(launches) and all(status == "confirmed" and receipt == f"outcome:{kind}" for (identity, status, receipt), (_, _, kind) in zip(ledger, sorted(observed, key=lambda o: o[1]))),
diff --git a/src/alienintent/composition/work_registry.py b/src/alienintent/composition/work_registry.py
index 6daec18..e9ef905 100644
--- a/src/alienintent/composition/work_registry.py
+++ b/src/alienintent/composition/work_registry.py
@@ -172,6 +172,9 @@ OWNERS = {NO_LINK: WORK_PREPARATION, NOT_ELIGIBLE: WORK_PREPARATION, ASSESSMENT_
           CONTRACT_INVALID: WORK_PREPARATION, DISPLAY_DIFFERS: WORK_PREPARATION, ROW_REFUSED: OPERATOR}
 # The shared Factory Director host configuration whose `wipLimit` is the WIP limit (bin/alienintent.mjs reads it too).
 HOST_CONFIGURATION = Path("~/.config/alienintent/factory-director-host.json")
+# The canonical stages each work item's card shows (its board Status), and where a failed card write is recorded.
+CARD_STAGES = {"IMPLEMENT": "Status", "VERIFY": "Status", "ACCEPT": "Status", "DONE": "Status"}
+PROJECTION_DIAGNOSTICS = "projection-diagnostics.jsonl"
 # Every registry token is scoped: `work link`, `work display` and the READY view need these, for the one repository.
 DISPLAY_PERMISSIONS = dict(REQUIRED_PERMISSIONS) | {"metadata": "read"}
 MAX_SAFE_INTEGER = 2 ** 53 - 1  # the Number.isSafeInteger bound of bin/alienintent.mjs; a JSON 1.0 is not an integer here
@@ -795,8 +798,9 @@ class WorkRegistry:
                                 github.repository, packets.default_branch, accepted, ordered)
 
     def _ready_view(self, configuration: ProjectConfiguration) -> GitHubProjectsWorkManagement:
-        """The READY view of board #1: profile `registry`, each formal workflow state mapped to itself, no projection
-        fields or writes; rows from `_ready_snapshot` and each row's contract the one that snapshot read for it.
+        """The READY view of board #1: profile `registry`, each formal workflow state mapped to itself, and each stage
+        of CARD_STAGES projected to the work item's card by `_project_card`; rows from `_ready_snapshot` and each row's
+        contract the one that snapshot read for it.
         Attention items live in the `readiness` store and evidence folder, under the assessment profile."""
         consumer = self.assessment.consumer
         project, profile = configuration.project, consumer.profile
@@ -814,8 +818,31 @@ class WorkRegistry:
         self._contracts: dict[str, BiuContract] = {}
         self._board_read = False  # Whether the last snapshot read the whole board; only then can a defect clear.
         return GitHubProjectsWorkManagement("registry", configuration.github.repository,
-                                            {state: state for state in STATES}, {}, self._ready_snapshot,
-                                            lambda row: self._contracts[str(row["card"])])
+                                            {state: state for state in STATES}, CARD_STAGES, self._ready_snapshot,
+                                            lambda row: self._contracts[str(row["card"])],
+                                            projection_write=self._project_card)
+
+    def _project_card(self, identity: str, field: str, state: str, revision: int) -> int:
+        """The work item's card shows its canonical stage: Status `state` written to the card linked to `identity`
+        and read back (the revision when it reads back `state`, else -1). The board reflects canonical work state; it
+        does not determine it. Any failure is appended to `launch/projection-diagnostics.jsonl` and answered -1, never
+        raised into a launch."""
+        card, error = None, None
+        try:
+            record = self.records.show(identity)
+            card = None if record is None else record.item.card_id
+            answered = -1 if card is None else self.links.board.write_status(card, state, revision)
+        except Exception as raised:  # noqa: BLE001 - a projection failure is a diagnostic, never a launch failure
+            answered, error = -1, f"{type(raised).__name__}: {raised}"
+        if answered != revision:
+            folder = launch_root(self.configuration)
+            folder.mkdir(parents=True, exist_ok=True)
+            with (folder / PROJECTION_DIAGNOSTICS).open("a", encoding="utf-8") as log:
+                log.write(json.dumps({"at": datetime.now(UTC).isoformat(), "identity": identity, "card": card,
+                                      "state": state, "revision": revision, "answered": answered,
+                                      "error": error if error is not None else
+                                      "no linked card" if card is None else "read back another status"}) + "\n")
+        return answered
 
     def _ready_snapshot(self) -> tuple[dict[str, object], ...]:
         """The READY column of the whole board in the sandbox reader's order (READY-entry time, then card id), one
diff --git a/src/alienintent/execution_coordination/application/factory_coordinator.py b/src/alienintent/execution_coordination/application/factory_coordinator.py
index 86b822c..d149504 100644
--- a/src/alienintent/execution_coordination/application/factory_coordinator.py
+++ b/src/alienintent/execution_coordination/application/factory_coordinator.py
@@ -117,7 +117,7 @@ class FactoryCoordinator:
         self.projection_diagnostics: dict[str, str] = {}
 
     def start(self) -> RunSummary:
-        items = self._work.import_ready_snapshot()
+        items = self._with_started(self._work.import_ready_snapshot())
         if not self._recover(items):
             return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
         dispatched: list[str] = []
@@ -160,23 +160,26 @@ class FactoryCoordinator:
         """One role step for exactly the named work item: the PRODUCER at IMPLEMENT, the VERIFIER at VERIFY or
         CLOSURE at ACCEPT.
 
-        At ACCEPT, writing nothing before the last step: the item is resolved from the READY snapshot, or else
-        `started_item`; a contract whose closure actions are not exactly the five fixed names answers
-        CLOSURE_NOT_AUTOMATED; an item at `ready-to-land` while landing is not enabled answers READY_TO_LAND.
+        A started item is resolved from the READY snapshot, or else `started_item` at any stage (the board reflects
+        canonical work state; it does not determine it). At ACCEPT, writing nothing before the last step, a contract
+        whose closure actions are not exactly the five fixed names answers CLOSURE_NOT_AUTOMATED; an item at `ready-to-land` while landing is not enabled answers READY_TO_LAND.
         Otherwise it writes the explicit human release as `release_and_start` does, runs the existing recovery once
         (which may record already-durable outcomes of other launches and starts no worker), projects every recorded
-        DONE through `completed`, and, only if the item is in the READY snapshot (or, at ACCEPT, resolved by
+        DONE through `completed`, and, only if the item is in the READY snapshot (or, once started, resolved by
         `started_item`) and `_eligible` admits it, runs `_run` once for it. It never calls `start()`, so no other
         work item runs and the next role waits for the next `launch`.
         """
-        accepted: ReadyWorkItem | None = None
+        started: ReadyWorkItem | None = None
         try:
             projected = self.state(identity)
         except KeyError:
             projected = None
+        if projected is not None and projected.stage in ROLE_BY_STAGE:
+            # A started item is resolved from its registry record when the board no longer shows it READY: the board
+            # reflects canonical work state, it does not determine it.
+            started = self._resolve(identity, self._work.import_ready_snapshot(), projected.record or {})
         if projected is not None and projected.stage is LifecycleStage.ACCEPT:
-            accepted = self._resolve(identity, self._work.import_ready_snapshot(), projected.record or {})
-            if accepted is None or not is_fixed(accepted.contract.required_closure_actions):
+            if started is None or not is_fixed(started.contract.required_closure_actions):
                 return CLOSURE_NOT_AUTOMATED
             if projected.outcome == READY_TO_LAND and not self._landing_enabled():
                 return READY_TO_LAND
@@ -188,7 +191,7 @@ class FactoryCoordinator:
         if not self._recover(items):
             return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
         self._project_done()
-        item = next((ready for ready in items if ready.identity == identity), accepted)
+        item = next((ready for ready in items if ready.identity == identity), started)
         if item is None or not self._eligible(item):
             return NOT_ELIGIBLE
         producing = self._role(identity) == PRODUCER
@@ -423,6 +426,8 @@ class FactoryCoordinator:
             prepared = self._encode(current) | self._carried(raw) | {"role": role, "invocation_candidate": self._encode_candidate(invocation.candidate)}
             self._store.commit_with_effect(self._profile, self._aggregate(item.identity), version, prepared, correlation, {"correlation": correlation, "work": item.identity, "role": role})
             self._store.claim_effect(self._profile, correlation)
+            if role == PRODUCER:
+                self._work.project_execution_state(item.identity, LifecycleStage.IMPLEMENT, current.version)
             outcome = self._worker.start(invocation, item.contract, frozenset(item.contract.required_capabilities), item.contract.budget_policy)
             if not self._correlated(invocation, outcome):
                 return StopReason.BLOCKED if self._park_unknown_effect(item, reservation) else StopReason.CAPACITY_UNAVAILABLE
@@ -725,12 +730,32 @@ class FactoryCoordinator:
         return True
 
     def _resolve(self, identity: str, items: Iterable[ReadyWorkItem], raw: Mapping[str, object]) -> ReadyWorkItem | None:
-        """The READY row of a work item at ACCEPT, else the item built from its registry record (`started_item`)."""
+        """The READY row of a started work item, else the item built from its registry record (`started_item`) for its
+        last launch, or for its PRODUCER's launch when a recorded decision left no `correlation`."""
         item = next((ready for ready in items if ready.identity == identity), None)
-        correlation = raw.get("correlation")
-        if item is None and self._started_item is not None and isinstance(correlation, str):
-            item = self._started_item(identity, correlation)
-        return item
+        if item is not None or self._started_item is None:
+            return item
+        for correlation in (raw.get("correlation"), raw.get("producer_correlation")):
+            if isinstance(correlation, str) and (item := self._started_item(identity, correlation)) is not None:
+                return item
+        return None
+
+    def _with_started(self, items: tuple[ReadyWorkItem, ...]) -> tuple[ReadyWorkItem, ...]:
+        """The READY snapshot plus every started work item it does not show (its card moved on with its state),
+        resolved from the registry: only recorded, non-final items at a stage some role advances."""
+        if self._started_item is None:
+            return items
+        shown = {item.identity for item in items}
+        started = []
+        for aggregate, _, raw in self._store.list_states(self._profile, "factory:"):
+            identity = aggregate.removeprefix("factory:")
+            if identity in shown or raw.get("stage") not in {str(stage) for stage in ROLE_BY_STAGE} \
+                    or raw.get("outcome") in FINAL_OUTCOMES:
+                continue
+            item = self._resolve(identity, (), raw)
+            if item is not None:
+                started.append(item)
+        return (*items, *started)
 
     def _project(self, identity: str) -> None:
         """The DONE projection hook; a refusal or error is a diagnostic, never raised into the coordinator."""
diff --git a/tests/composition/test_work_registry.py b/tests/composition/test_work_registry.py
index f0eeba2..f181fc5 100644
--- a/tests/composition/test_work_registry.py
+++ b/tests/composition/test_work_registry.py
@@ -14,7 +14,7 @@ from pathlib import Path
 import pytest
 
 from alienintent.composition.work_registry import (
-    ConfigurationInvalid, WorkRegistry, load_project_configuration, project_configuration, read_only_store)
+    CARD_STAGES, ConfigurationInvalid, WorkRegistry, load_project_configuration, project_configuration, read_only_store)
 from alienintent.evidence_learning.domain.records import ref_from_document
 from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
 from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
@@ -392,9 +392,11 @@ def test_the_view_exists_only_with_both_the_github_and_readiness_entries(tmp_pat
     SQLiteOperationalStore(tmp_path / "fx.sqlite")
     for changes in ({}, {"github": github(tmp_path)}, {"readiness": readiness(tmp_path)}):
         assert WorkRegistry(project_configuration(entry(tmp_path, **changes), PROJECT)).ready_view is None
-    view = WorkRegistry(project_configuration(entry(tmp_path, github=github(tmp_path), readiness=readiness(tmp_path)),
-                                              PROJECT)).ready_view
-    assert view._profile == "registry" and view._projection_fields == {} and view._projection_write is None
+    registry = WorkRegistry(project_configuration(entry(tmp_path, github=github(tmp_path), readiness=readiness(tmp_path)),
+                                                  PROJECT))
+    view = registry.ready_view
+    assert view._profile == "registry" and view._projection_fields == CARD_STAGES
+    assert view._projection_write == registry._project_card
     assert view._status_mapping["READY"] == "READY" and view._repository == "AlienLogicLab/alienintent-sandbox"
 
 
diff --git a/tests/composition/test_worker_launch.py b/tests/composition/test_worker_launch.py
index bb5df85..2d2b0e0 100644
--- a/tests/composition/test_worker_launch.py
+++ b/tests/composition/test_worker_launch.py
@@ -794,7 +794,7 @@ def test_without_landing_closure_is_ready_to_land_and_never_blocks_other_work(fx
     closing.close(item.id)
     state = closing.state(item.id)
     assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, "ready-to-land")
-    assert closing.head() == base and closing.orders(item.id) == [] and closing.card(item.id) == "READY"
+    assert closing.head() == base and closing.orders(item.id) == [] and closing.card(item.id) == "ACCEPT"
     [session] = fx.runs("CLOSURE")
     clone = Path(session["cwd"])
     assert clone.is_dir() and not fx.wip_held(item.id)
@@ -853,7 +853,7 @@ def test_the_bounded_request_alone_steers_nothing(closing, plan, landed, outcome
     if landed:
         expected += [receipt(a, item.id, revision) for a in ("merged-to-main", "landing-record")]
     assert state.record["receipts"] == sorted(expected)
-    assert (closing.head() != base) is landed and closing.card(item.id) == "READY"
+    assert (closing.head() != base) is landed and closing.card(item.id) == "ACCEPT"
     for finding in plan.get("request", {}).get("findings", []):
         if len(finding) <= 500:  # a refused request carries none of its findings
             assert f"closure-finding: {finding}" in closing.fx.journal_findings(item.id)
@@ -1039,7 +1039,7 @@ def test_a_request_without_board_update_crashing_after_the_push_recovers_without
     monkeypatch.setattr(LandingAuthority, "land", original)
     closing.close(other.id)
     state = closing.state(item.id)
-    assert state.outcome == "authority-block" and closing.card(item.id) == "READY"
+    assert state.outcome == "authority-block" and closing.card(item.id) == "ACCEPT"
     assert {r.split(":", 1)[0] for r in state.record["receipts"]} == {
         "candidate-published", "merged-to-main", "landing-record"}
 
@@ -1152,7 +1152,7 @@ def test_cleanup_keeps_live_or_foreign_workspaces_and_then_issues_no_receipt(clo
             setattr(ownership, "work", (1,)), cleanup(self, invocation))[1])
     closing.close(item.id, ownership=ownership)
     state = closing.state(item.id)
-    assert state.outcome == "authority-block" and closing.card(item.id) == "DONE"
+    assert state.outcome == "authority-block" and closing.card(item.id) == "ACCEPT"  # canonical: not DONE
     assert receipt("workspaces-cleaned", item.id, revision_of(state)) not in state.record["receipts"]
     [session] = closing.fx.runs("CLOSURE")
     verifier_clone = next(p for p in verifier.iterdir() if p.name.startswith(f"verifier-launch-{workspace_folder(item.id)}-"))
@@ -2126,3 +2126,53 @@ def test_a_new_candidate_starts_with_no_verifier_retries(fx):
         fx.launch(item.id)
         state = fx.loaded().coordinator(None, None).state(item.id)
         assert (state.outcome, state.record["verifier_retries"]) == ("verifier-retry", retries)
+
+
+# --- CARD-FOLLOWS-STAGE: the board reflects canonical work state; it does not determine it -------------------------
+
+def _card_writes(monkeypatch) -> list[tuple[str, str]]:
+    written: list[tuple[str, str]] = []
+    project = work_registry.WorkRegistry._project_card
+
+    def recording(self, identity, field, state, revision):
+        written.append((identity, state))
+        return project(self, identity, field, state, revision)
+    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", recording)
+    return written
+
+
+def test_the_card_follows_the_canonical_stage_and_launch_never_needs_it_ready(closing, monkeypatch):
+    item = closing.fx.authorized("UNIT", **FIXED)
+    written = _card_writes(monkeypatch)
+    assert closing.card(item.id) == "READY"
+    closing.fx.launch(item.id)
+    assert written == [(item.id, "IMPLEMENT"), (item.id, "VERIFY")]
+    assert closing.state(item.id).stage is LifecycleStage.VERIFY and closing.card(item.id) == "VERIFY"
+    closing.fx.launch(item.id)  # no longer on the READY board: resolved from its registry record
+    assert closing.state(item.id).stage is LifecycleStage.ACCEPT and closing.card(item.id) == "ACCEPT"
+    closing.close(item.id)
+    assert closing.state(item.id).stage is LifecycleStage.DONE and closing.card(item.id) == "DONE"
+
+
+def test_a_card_write_that_does_not_read_back_is_a_durable_diagnostic_never_a_launch_failure(closing):
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.ignore_status = True  # the board answers the write but keeps its Status
+    closing.fx.launch(item.id)
+    assert closing.state(item.id).stage is LifecycleStage.VERIFY and closing.card(item.id) == "READY"
+    path = launch_root(closing.fx.loaded().configuration) / "projection-diagnostics.jsonl"
+    records = [json.loads(line) for line in path.read_text().splitlines()]
+    assert [(r["identity"], r["state"], r["answered"], r["error"]) for r in records] == [
+        (item.id, "IMPLEMENT", -1, "read back another status"), (item.id, "VERIFY", -1, "read back another status")]
+
+
+def test_after_a_decision_a_started_item_launches_without_a_ready_card(closing, monkeypatch):
+    """A recorded decision drops the item's `correlation`; it is resolved from its PRODUCER's launch."""
+    item = closing.accepted()
+    monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "refused:fixture")
+    closing.close(item.id)
+    assert closing.state(item.id).outcome == "authority-block" and closing.card(item.id) == "ACCEPT"
+    assert closing.fx.loaded().decide(item.id, "authorize", QUOTE)["answer"] is None
+    assert "correlation" not in closing.state(item.id).record or closing.state(item.id).record["correlation"] is None
+    sessions = len(closing.fx.runs("CLOSURE"))
+    closing.close(item.id)
+    assert len(closing.fx.runs("CLOSURE")) == sessions + 1
diff --git a/tests/execution_coordination/test_factory_coordinator.py b/tests/execution_coordination/test_factory_coordinator.py
index 1b5b895..ce13942 100644
--- a/tests/execution_coordination/test_factory_coordinator.py
+++ b/tests/execution_coordination/test_factory_coordinator.py
@@ -152,8 +152,8 @@ def test_projection_type_error_does_not_retry_without_the_execution_revision(tmp
 
     with pytest.raises(TypeError, match="provider implementation fault"):
         coordinator.start()
-    # VERIFY (1) and ACCEPT (3) project first; the fault at DONE (4) is not retried.
-    assert work.revisions == [1, 3, 4]
+    # IMPLEMENT at dispatch (0), VERIFY (1) and ACCEPT (3) project first; the fault at DONE (4) is not retried.
+    assert work.revisions == [0, 1, 3, 4]
 
 
 def test_unavailable_projection_does_not_change_internal_execution_truth(tmp_path: Path) -> None:
diff --git a/tests/execution_coordination/test_role_orchestration.py b/tests/execution_coordination/test_role_orchestration.py
index 08b41c3..8bb393f 100644
--- a/tests/execution_coordination/test_role_orchestration.py
+++ b/tests/execution_coordination/test_role_orchestration.py
@@ -56,7 +56,7 @@ def test_producer_success_advances_only_to_verify(tmp_path: Path) -> None:
     assert summary.dispatched == (WORK,)
     assert state.stage is LifecycleStage.VERIFY and not state.accepted and state.completed_closure_actions == frozenset()
     assert state.candidate is not None and state.candidate.independent_read_back_proven
-    assert fixture.projections() == ["VERIFY", "VERIFY"]
+    assert fixture.projections() == ["IMPLEMENT", "VERIFY", "VERIFY"]
     assert [(role, kind) for role, _, kind in fixture.invocations()] == [(PRODUCER, "success"), (VERIFIER, "verdict-missing")]
     _retried(fixture, "verdict-missing")
 
@@ -69,7 +69,7 @@ def test_the_full_lifecycle_is_three_distinct_role_invocations_with_exact_custod
     state = fixture.state()
     assert summary.dispatched == (WORK,) and summary.stop_reason.value == "eligible-backlog-exhausted"
     assert state.stage is LifecycleStage.DONE and state.accepted and state.outcome == "closed"
-    assert fixture.projections() == ["VERIFY", "ACCEPT", "DONE"]
+    assert fixture.projections() == ["IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]
     roles = fixture.invocations()
     assert [(role, kind) for role, _, kind in roles] == [(PRODUCER, "success"), (VERIFIER, "accept"), (CLOSURE, "closed")]
     correlations = [correlation for _, correlation, _ in roles]
@@ -106,7 +106,7 @@ def test_verifier_rejection_records_findings_and_repairs_through_implement(tmp_p
     assert finding["findings"] == [f"{WORK}: scripted rejection under {roles[1][1]}"]
     # The repair is a new candidate on its own branch; the rejected one is not what was accepted.
     assert state.candidate.identity != rejected["identity"]
-    assert fixture.projections() == ["VERIFY", "IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]
+    assert fixture.projections() == ["IMPLEMENT", "VERIFY", "IMPLEMENT", "IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]
 
 
 def test_rejection_beyond_the_attempt_budget_is_terminal_failure(tmp_path: Path) -> None:
@@ -146,7 +146,7 @@ def test_closure_records_only_actions_actually_read_back(tmp_path: Path) -> None
     state = fixture.state()
     assert state.accepted and state.completed_closure_actions == frozenset()
     assert state.record["hold_reason"] == "closure-receipts-incomplete" and state.record["receipts"] == ["candidate-published"]
-    assert fixture.projections() == ["VERIFY", "ACCEPT", "ACCEPT"]
+    assert fixture.projections() == ["IMPLEMENT", "VERIFY", "ACCEPT", "ACCEPT"]
     _held(fixture, LifecycleStage.ACCEPT)
 
 
```

## 3. Acceptance checks

1. **The card follows the stage, and launch never needs it READY**
   (`test_the_card_follows_the_canonical_stage_and_launch_never_needs_it_ready`): the first launch writes IMPLEMENT
   then VERIFY to the card; the second launch runs the VERIFIER although the card is VERIFY; ACCEPT, then DONE after
   CLOSURE.
2. **A card write that does not read back is a durable diagnostic, never a launch failure**
   (`test_a_card_write_that_does_not_read_back_is_a_durable_diagnostic_never_a_launch_failure`): with the board keeping
   its Status, the launch still reaches VERIFY, and `projection-diagnostics.jsonl` holds IMPLEMENT and VERIFY, each
   answered -1, "read back another status".
3. **After a decision, a started item launches without a READY card**
   (`test_after_a_decision_a_started_item_launches_without_a_ready_card`): an authority hold at ACCEPT, `work decide`
   authorize (no `correlation` left), and the next launch runs CLOSURE.
4. **Mutations, run exactly by the VERIFIER** (each must fail its named test in
   `tests/composition/test_worker_launch.py` and pass when reverted):
   - **C1:** `if projected is not None and projected.stage in ROLE_BY_STAGE:` (the `started` resolution in `launch`)
     made `... is LifecycleStage.ACCEPT:` -> check 1's test.
   - **C2:** `for correlation in (raw.get("correlation"), raw.get("producer_correlation")):` made
     `for correlation in (raw.get("correlation"),):` -> check 3's test.
   - **C3:** the two lines `if role == PRODUCER:` / `self._work.project_execution_state(item.identity,
     LifecycleStage.IMPLEMENT, current.version)` deleted -> check 1's test.
   - **C4:** in `_project_card`, `if answered != revision:` made `if False:` -> check 2's test.
   - **C5:** `CARD_STAGES,` in `_ready_view` made `{},` -> check 1's test.

The whole suite at the candidate has no failed or error test case (proven by the factory's regression gate; Founder:
no extra whole-suite runs), and `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (not in this item)

- READY is still read from the board for a work item's first launch and its priority, until plan authority.
- `guard_account`, `_block_dependents` and `record_decision` still read only the READY snapshot: `explain` reports a
  started item as not in the READY snapshot, and a dependent no longer on the READY board is not marked blocked.
- A card write is not fenced against GitHub beyond the adapter's in-memory revision fence; a failed write is recorded
  and the next stage change writes again.

## 4. Evidence and review record

A prototype that is exactly section 2's diff, on `2b47f21` (not the candidate):
`manual/path-to-done/card-follows-stage/prototype-on-2b47f21.diff`, sha256 `7cad0a00…022e3`. With it the
touched test files (`test_work_registry.py`, `test_factory_coordinator.py`, `test_worker_launch.py`,
`test_role_orchestration.py`, `test_lifecycle_capstone.py`, `test_role_binding.py`) pass, the architecture fitness
check passes, and C1-C5 each fail their named test and pass when reverted
(`manual/path-to-done/card-follows-stage/mutations.log`). Code map: `.../card-follows-stage/code-map-bc9a9d8.md`.

**Revision 1 (2026-10-09).** First draft, from the Founder's decisions of 2026-10-09 (sections 9-10).
