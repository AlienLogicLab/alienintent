# Work unit: the board card follows canonical work state through a durable projection outbox

**Label:** `CARD-FOLLOWS-STAGE` (a document label; permanent id `3e139902-d526-45e6-8187-46be75b5c366`).
**Status:** Revision 5 (work item `3e139902-d526-45e6-8187-46be75b5c366`, at CAPTURE), 2026-10-09. Reviewed (follow-up check PASS). Not approved, not assessed, not released.
**Position on the path (Founder 2026-10-09, decisions sections 10 and 12):** VERIFIER-RETRY (done, `2b47f21`) ->
CARD-FOLLOWS-STAGE -> NO-CHANGE -> PLAN-AUTHORITY-INHERITANCE -> BOUNDED-ROUTINE-LAUNCH -> Work Preparation / READY
refill -> three-item autonomy proof.
**Starting revision:** main `2b47f21`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

**The board reflects canonical Work state; it does not determine canonical Work state. Canonical Work state owns
truth; projection is eventually consistent, revision-fenced and non-blocking.**

## Contract

```json alienintent-contract
{
 "identity": "3e139902-d526-45e6-8187-46be75b5c366",
 "version": "revision-5",
 "intent": "Each registry work item's GitHub Project card shows its canonical stage through a durable projection outbox: every committed state of a work item's execution aggregate leaves a projection obligation in the same store transaction; a card projector, running beside each launch and on its own (`work project`), projects the item's CURRENT canonical stage to its linked card, reads it back and retires the obligation; an attempted projection overtaken by a newer commit while in flight is owed again, so the card converges to the current canonical stage. The coordinator never calls GitHub; projection is eventually consistent, revision-fenced and non-blocking. A started work item launches from its registry record at any stage, so execution never depends on the card staying READY. The board reflects canonical Work state; it does not determine canonical Work state.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-09: The board reflects canonical Work state; it does not determine canonical Work state.",
  "Founder 2026-10-09: canonical state transition -> durable bounded projection obligation (committed with the state) -> asynchronous, idempotent GitHub projection -> independent read-back -> obligation retired. The board may lag canonical Work state, but it must never run ahead of it and must never determine it.",
  "Founder 2026-10-09: no external broker; a durable local outbox in the existing control-plane store; one outstanding obligation per work item (latest revision); acknowledged obligations are retired without scanning history; stale obligations are fenced by revision; successful projection requires read-back; GitHub failures never block execution.",
  "Founder 2026-10-09: the projector projects the CURRENT canonical stage at projection time, never a status carried by an obligation; an obligation carries only the work item and a revision.",
  "Founder 2026-10-09: the projection outbox is separate from the worker effect ledger: worker effects and downstream UI projection have different failure semantics (an unknown effect blocks its aggregate; a pending effect is parked for a decision).",
  "Founder 2026-10-09: while building, run only the affected tests; the factory's regression gate owns the whole-suite run."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/adapters/sqlite_store.py",
  "src/alienintent/execution_coordination/ports/operational_store.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/installation/application/doctor.py",
  "src/alienintent/composition/offline_proof.py",
  "tools/fitness/coupling_register.json",
  "tests/execution_coordination/test_operational_store.py",
  "tests/composition/test_worker_launch.py",
  "tests/control_plane/test_cli.py",
  "tests/installation/test_doctor_evidence.py"
 ],
 "excluded_scope": [
  "the GitHub adapters (github_work_management.py, github_projects_v2.py) and any redesign of the GitHub integration",
  "the coordinator's own projection calls (project_execution_state) and the registry board view's projection fields, which stay empty",
  "the READY snapshot as the source of a first launch and of priority (plan authority's item), and READY/HOLD card states",
  "guard_account, _block_dependents and record_decision, which still read the READY snapshot",
  "the worker effect ledger (effects table, EffectExecutor) and its recovery semantics"
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
  "acceptance checks 1-12 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff from the starting revision equals section 2's diff",
  "the VERIFIER runs mutations P1-P9 of check 12 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a REVIEW, READY or HOLD card state",
  "removing a retired or failed item's card",
  "a generic messaging framework"
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

Founder-reported and live: a registry work item's card stays READY while the item is at IMPLEMENT, VERIFY and ACCEPT.
Revisions 1-2 of this item called GitHub synchronously from the coordinator; review proved there is no safe place for
that inside the launch transaction (before the commit the card leads canonical truth and a crash loses the item;
between commit and claim, or after the claim, a crash parks a decision for the Founder). Founder decision (section
12): a durable projection outbox. Separately, `launch` resolved a started item from its registry record only at
ACCEPT and `start` read only the READY snapshot, so an item whose card left READY could not launch at IMPLEMENT or
VERIFY; a recorded decision drops the item's `correlation`, so resolution falls back to `producer_correlation`.

## 2. The change: exactly this diff at `2b47f21`

Invariants the diff implements:

1. **Durable together.** `SQLiteOperationalStore._commit` (every state write goes through it) upserts, in the same
   transaction, one row of the new `projections` table for every `factory:` aggregate: (profile, aggregate,
   revision). Schema 3; 1 -> 3 and 2 -> 3 migrations (2 -> 3 owes an obligation to every existing work item).
2. **Outstanding obligations only.** `pending_projections(profile)` reads only that table; `retire_projection`
   deletes a row only if it is still for the given revision, so a newer commit's obligation stays outstanding.
3. **Current canonical stage.** An obligation carries no status. `WorkRegistry.project_cards` reads the item's
   current state and projects its current stage (IMPLEMENT, VERIFY, ACCEPT, DONE) at its current revision.
4. **Converges; never projects an older stage it read.** An obligation is retired only after its card reads back the
   then-current stage. If the item's canonical revision moved while an attempted write was in flight (another projector
   may already have written and retired the newer stage; the write may have landed although its read-back failed),
   `owe_projection` owes it again (never lowering an outstanding obligation), so the next pass writes the newest stage.
   A late obligation for an old revision still projects the current stage; a write is repeated safely (the same status
   again) until its obligation is retired. GitHub has no compare-and-set: see the stated limits for the one case this
   cannot repair before the item's next commit.
5. **Read-back.** `_project_card` writes through the existing `write_status`, which reads the Status back; anything
   else appends one line per distinct failure to `launch/projection-diagnostics.jsonl`: an exception or another status
   read back leaves the obligation outstanding; an item with no linked card is retired (nothing to project).
6. **Non-blocking and restartable.** `work launch` runs inside `card_projection`: a pass at once, a pass every
   `CARD_PROJECTION_SECONDS` (5) in a daemon thread while the launch runs (so a first PRODUCER's IMPLEMENT shows while
   it works), and, if that thread has finished, a final pass bounded by `CARD_FINAL_PASS_SECONDS` (30); a failing pass
   is a diagnostic. `work project` runs one pass on its own. The
   coordinator never calls GitHub.
7. **Execution never needs the card.** `launch` resolves a started item at every stage through `_resolve`, which tries
   `correlation`, then `producer_correlation`; `start` adds every recorded, non-final started item through
   `_with_started`.
8. **One schema truth.** The doctor's persistence check and the offline proof's P1 no longer hardcode schema 2: the
   doctor asks the store's preflight whether anything is left to migrate, P1 compares with `SCHEMA_VERSION`; the
   coupling register declares the `projections` table.

```diff
diff --git a/src/alienintent/composition/offline_proof.py b/src/alienintent/composition/offline_proof.py
index 2a19ee7..3df94f9 100644
--- a/src/alienintent/composition/offline_proof.py
+++ b/src/alienintent/composition/offline_proof.py
@@ -22,7 +22,7 @@ import time
 from typing import Mapping
 
 from alienintent.composition.offline_profile import OfflineProofSubstrate, ProofManifest, credential_findings, load_manifest
-from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
+from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore, SCHEMA_VERSION
 from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
 from alienintent.invocation_runtime.adapters.scripted_worker import SCRIPTED_PROVIDER, ScriptedWorkerProcess, journal_outcome, journal_provider_calls, journal_records
 from alienintent.invocation_runtime.domain.runtime import workspace_folder
@@ -136,7 +136,7 @@ def evaluate(substrate: OfflineProofSubstrate, summary, kernel: dict[str, object
     facts["stages"] = stages
     facts["correlations"] = {identity: None if state is None else substrate.store.read_state(manifest.profile, f"factory:{identity}")[1].get("correlation") for identity, state in states.items()}
     all_done = bool(states) and all(state is not None and state.stage is LifecycleStage.DONE and state.candidate is not None and state.candidate.independent_read_back_proven for state in states.values())
-    checks.append(check("P1", "real temporary SQLite", substrate.database.exists() and preflight.current_version == 2 and all_done, "state.sqlite at schema 2 holds every seeded aggregate at DONE with an independently read-back candidate", {"path": str(substrate.database), "schema_version": preflight.current_version, "stages": stages}))
+    checks.append(check("P1", "real temporary SQLite", substrate.database.exists() and preflight.current_version == SCHEMA_VERSION and all_done, f"state.sqlite at schema {SCHEMA_VERSION} holds every seeded aggregate at DONE with an independently read-back candidate", {"path": str(substrate.database), "schema_version": preflight.current_version, "stages": stages}))
 
     bare = subprocess.run(["git", "-C", str(substrate.remote), "rev-parse", "--is-bare-repository"], capture_output=True, text=True, check=False).stdout.strip() == "true"
     main = substrate.remote_advertises("main")
diff --git a/src/alienintent/composition/work_registry.py b/src/alienintent/composition/work_registry.py
index 6daec18..7ba7572 100644
--- a/src/alienintent/composition/work_registry.py
+++ b/src/alienintent/composition/work_registry.py
@@ -77,6 +77,7 @@ import shutil
 import signal
 import subprocess
 import sysconfig
+import threading
 import time
 from types import SimpleNamespace
 from uuid import uuid4
@@ -121,7 +122,7 @@ from alienintent.execution_coordination.adapters.github_repository_api import Gi
 from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
 from alienintent.execution_coordination.adapters.release_admission import (
     GitRevisionResolver, StoredReleaseAuthorizations)
-from alienintent.execution_coordination.adapters.sqlite_store import SCHEMA_VERSION, SQLiteOperationalStore
+from alienintent.execution_coordination.adapters.sqlite_store import PROJECTED, SCHEMA_VERSION, SQLiteOperationalStore
 from alienintent.execution_coordination.application.factory_coordinator import NEVER_STARTED, FactoryCoordinator
 from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
 from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
@@ -172,6 +173,12 @@ OWNERS = {NO_LINK: WORK_PREPARATION, NOT_ELIGIBLE: WORK_PREPARATION, ASSESSMENT_
           CONTRACT_INVALID: WORK_PREPARATION, DISPLAY_DIFFERS: WORK_PREPARATION, ROW_REFUSED: OPERATOR}
 # The shared Factory Director host configuration whose `wipLimit` is the WIP limit (bin/alienintent.mjs reads it too).
 HOST_CONFIGURATION = Path("~/.config/alienintent/factory-director-host.json")
+# The canonical stages a work item's card shows, where a failed card write is recorded, and how often a running launch
+# catches the board up. The board reflects canonical work state; it does not determine it.
+CARD_STAGES = frozenset({"IMPLEMENT", "VERIFY", "ACCEPT", "DONE"})
+PROJECTION_DIAGNOSTICS = "projection-diagnostics.jsonl"
+CARD_PROJECTION_SECONDS = 5.0
+CARD_FINAL_PASS_SECONDS = 30.0
 # Every registry token is scoped: `work link`, `work display` and the READY view need these, for the one repository.
 DISPLAY_PERMISSIONS = dict(REQUIRED_PERMISSIONS) | {"metadata": "read"}
 MAX_SAFE_INTEGER = 2 ** 53 - 1  # the Number.isSafeInteger bound of bin/alienintent.mjs; a JSON 1.0 is not an integer here
@@ -463,6 +470,7 @@ class WorkRegistry:
         self.authorization = self._authorization(configuration) if self.assessment is not None else None
         self.completion = self._completion(configuration) if self.assessment is not None else None
         self.links = self._links(configuration.github, transport) if configuration.github is not None else None
+        self._diagnosed: set[tuple[object, ...]] = set()  # card projection failures already recorded, once each
         self.ready_view = self._ready_view(configuration) if self.links is not None and self.assessment is not None \
             else None
         # Each role's context package (unit 6c-1) over the `readiness` store and evidence folder; its command names
@@ -570,6 +578,99 @@ class WorkRegistry:
         configuration is read; the model routing file is read by `prepare` at every launch."""
         return self._launch_chain()[0]
 
+    def project_cards(self, deadline: float | None = None) -> int:
+        """One pass of the card projector over the outstanding projection obligations only: each work item's card is
+        set to the item's CURRENT canonical stage (IMPLEMENT, VERIFY, ACCEPT, DONE) and read back, then the obligation
+        is retired. An obligation carries no status, so a late one never writes an older stage. If a newer commit
+        landed while an attempted write was in flight (another projector may have written and retired the newer stage
+        first; the write may have landed although its read-back failed), the projection is owed again, so the next pass
+        writes the newest stage. A change GitHub applies only after its answer was lost (a client timeout) and after a
+        newer stage was retired can leave an older status until the item's next commit: GitHub has no compare-and-set.
+        A failed write stays outstanding; an item with no linked card is retired after one diagnostic. Stops at
+        `deadline` (time.monotonic), leaving the rest outstanding. Never changes canonical state; answers the number
+        of obligations retired."""
+        if self.links is None or self.assessment is None:
+            return 0
+        store, retired = self.store, 0
+        for aggregate, revision in store.pending_projections("registry"):
+            if deadline is not None and time.monotonic() > deadline:
+                break
+            identity = aggregate.removeprefix(PROJECTED)
+            version, raw = store.read_state("registry", aggregate)
+            stage = raw.get("stage")
+            if stage in CARD_STAGES:
+                written = self._project_card(identity, str(stage), version)
+                now, _ = store.read_state("registry", aggregate)
+                if written is not None and now != version:
+                    store.owe_projection("registry", aggregate, now)  # an attempted write overtaken while in flight
+                    continue
+                if written is False:
+                    continue  # outstanding: the next pass writes the then-current stage
+            retired += store.retire_projection("registry", aggregate, revision)
+        return retired
+
+    @contextmanager
+    def card_projection(self, interval: float = CARD_PROJECTION_SECONDS):
+        """The card projector around one launch: a pass now, a pass every `interval` seconds while the launch runs (so a
+        PRODUCER's IMPLEMENT shows while it works), and, if the running pass has finished, a pass at the end that stops
+        starting items after CARD_FINAL_PASS_SECONDS (the thread wait and an item already in flight add their own
+        transport timeouts). A pass that fails is recorded and the next one retries; nothing here reaches the launch."""
+        stop = threading.Event()
+
+        def passes() -> None:
+            while True:
+                self._card_pass()
+                if stop.wait(interval):
+                    return
+        runner = threading.Thread(target=passes, name="card-projection", daemon=True)
+        runner.start()
+        try:
+            yield
+        finally:
+            stop.set()
+            runner.join(interval + 30)
+            if not runner.is_alive():
+                self._card_pass(time.monotonic() + CARD_FINAL_PASS_SECONDS)
+
+    def _card_pass(self, deadline: float | None = None) -> None:
+        try:
+            self.project_cards(deadline)
+        except Exception as error:  # noqa: BLE001 - the board lags canonical state; it never stops a launch
+            self._projection_diagnostic(None, None, None, None, -1, f"pass failed: {type(error).__name__}: {error}")
+
+    def _project_card(self, identity: str, stage: str, revision: int) -> bool | None:
+        """`stage` written to the card linked to `identity` and read back by `write_status`: True when it reads back,
+        None when the item has no linked card (nothing to project), False otherwise (an exception, another status read
+        back). Each distinct failure is appended once to `launch/projection-diagnostics.jsonl`."""
+        card, answered, error = None, -1, None
+        try:
+            record = self.records.show(identity)
+            card = None if record is None else record.item.card_id
+            if card is not None:
+                answered = self.links.board.write_status(card, stage, revision)
+        except Exception as raised:  # noqa: BLE001 - a projection failure is a diagnostic, never a launch failure
+            error = f"{type(raised).__name__}: {raised}"
+        if answered == revision:
+            return True
+        self._projection_diagnostic(identity, card, stage, revision, answered, error if error is not None else
+                                    "no linked card" if card is None else "read back another status")
+        return None if card is None and error is None else False
+
+    def _projection_diagnostic(self, identity, card, stage, revision, answered, error) -> None:
+        key = (identity, revision, error)
+        if key in self._diagnosed:
+            return
+        self._diagnosed.add(key)
+        try:
+            folder = launch_root(self.configuration)
+            folder.mkdir(parents=True, exist_ok=True)
+            with (folder / PROJECTION_DIAGNOSTICS).open("a", encoding="utf-8") as log:
+                log.write(json.dumps({"at": datetime.now(UTC).isoformat(), "identity": identity, "card": card,
+                                      "state": stage, "revision": revision, "answered": answered,
+                                      "error": error}) + "\n")
+        except OSError:
+            pass  # a diagnostic that cannot be written is not a launch failure either
+
     @property
     def store(self) -> OperationalStore:
         """The `readiness` store the `registry` coordinator and the exclusive `work launch` reservation live in."""
diff --git a/src/alienintent/control_plane/adapters/cli.py b/src/alienintent/control_plane/adapters/cli.py
index 60ba489..61a266d 100644
--- a/src/alienintent/control_plane/adapters/cli.py
+++ b/src/alienintent/control_plane/adapters/cli.py
@@ -1,6 +1,7 @@
 """Sanitized command-line presentation adapter for the operator control plane."""
 from __future__ import annotations
 
+from contextlib import nullcontext
 import argparse
 from datetime import UTC, datetime
 import importlib
@@ -120,6 +121,7 @@ def _parser() -> argparse.ArgumentParser:
     context.add_argument("--correlation"); context.add_argument("--candidate")
     context.add_argument("--contract-digest")
     launch = _sanitized(work.add_parser("launch")); launch.add_argument("target")
+    _sanitized(work.add_parser("project"))
     work_decide = _sanitized(work.add_parser("decide")); work_decide.add_argument("target")
     work_decide.add_argument("--choice", choices=("authorize", "defer"), required=True)
     work_decide.add_argument("--quote", required=True)
@@ -201,8 +203,17 @@ def main(argv: list[str] | None = None) -> int:
                 if getattr(registry, "launcher", None) is None:
                     _render({"error": "readiness-not-configured"}, args.json)
                     return 1
-                _render(exclusive_launch_work(registry.launcher, args.target, registry.store, registry.ownership),
-                        args.json)
+                # The card projector runs beside the launch: the board lags canonical state, never leads or blocks it.
+                projection = getattr(registry, "card_projection", None)
+                with projection() if projection is not None else nullcontext():
+                    value = exclusive_launch_work(registry.launcher, args.target, registry.store, registry.ownership)
+                _render(value, args.json)
+                return 0
+            if args.work_command == "project":
+                if getattr(registry, "project_cards", None) is None:
+                    _render({"error": "readiness-not-configured"}, args.json)
+                    return 1
+                _render({"retired": registry.project_cards()}, args.json)
                 return 0
             if args.work_command == "decide":
                 if getattr(registry, "decide", None) is None:
diff --git a/src/alienintent/execution_coordination/adapters/sqlite_store.py b/src/alienintent/execution_coordination/adapters/sqlite_store.py
index 061a2bb..e4cb49a 100644
--- a/src/alienintent/execution_coordination/adapters/sqlite_store.py
+++ b/src/alienintent/execution_coordination/adapters/sqlite_store.py
@@ -21,7 +21,11 @@ from alienintent.execution_coordination.ports.fenced_store import (
     ConsumerReceipt, EffectConfirmation, FencedOperationalStore, GuardVector,
 )
 
-SCHEMA_VERSION = 2
+SCHEMA_VERSION = 3
+# The work items' execution aggregates: each committed state of one leaves a projection obligation (its revision) in
+# the same transaction, so a downstream display is caught up from the outstanding obligations alone.
+PROJECTED = "factory:"
+_PROJECTIONS = "CREATE TABLE projections (profile TEXT NOT NULL, aggregate TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(profile, aggregate));"
 _FENCED = "__fenced__:"
 
 
@@ -87,7 +91,8 @@ class SQLiteOperationalStore(FencedOperationalStore):
                 CREATE TABLE fences (profile TEXT NOT NULL, scope TEXT NOT NULL, resource_key TEXT NOT NULL, fence INTEGER NOT NULL, PRIMARY KEY(profile, scope, resource_key));
                 CREATE TABLE effects (profile TEXT NOT NULL, identity TEXT NOT NULL, aggregate TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, receipt TEXT, PRIMARY KEY(profile, identity));
                 CREATE TABLE schema_migrations (from_version INTEGER NOT NULL, to_version INTEGER NOT NULL, reversible INTEGER NOT NULL, PRIMARY KEY(from_version, to_version));
-                INSERT INTO operational_schema VALUES (2);
+                """ + _PROJECTIONS + """
+                INSERT INTO operational_schema VALUES (3);
                 COMMIT;
             """)
 
@@ -113,20 +118,24 @@ class SQLiteOperationalStore(FencedOperationalStore):
             raise SchemaIncompatible(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
         if version == SCHEMA_VERSION:
             return SchemaPreflight(version, None)
-        if version == 1:
-            return SchemaPreflight(version, (1, 2))
+        if version in (1, 2):
+            return SchemaPreflight(version, (version, SCHEMA_VERSION))
         raise SchemaIncompatible(f"database schema {version} has no safe migration to {SCHEMA_VERSION}")
 
     @staticmethod
     def _migrate(connection: sqlite3.Connection, from_version: int, to_version: int) -> None:
-        if (from_version, to_version) != (1, 2):
+        if from_version not in (1, 2) or to_version != 3:
             raise SchemaIncompatible(f"database schema {from_version} has no safe migration to {to_version}")
-        connection.executescript("""
-            BEGIN IMMEDIATE;
+        to_two = """
             ALTER TABLE receipts ADD COLUMN status TEXT NOT NULL DEFAULT 'applied';
             CREATE TABLE schema_migrations (from_version INTEGER NOT NULL, to_version INTEGER NOT NULL, reversible INTEGER NOT NULL, PRIMARY KEY(from_version, to_version));
             INSERT INTO schema_migrations VALUES (1, 2, 0);
-            UPDATE operational_schema SET version=2;
+        """ if from_version == 1 else ""
+        # 2 -> 3 only adds the projection obligations; every existing state is owed one, so a display catches up.
+        connection.executescript("BEGIN IMMEDIATE;" + to_two + _PROJECTIONS + """
+            INSERT INTO projections SELECT profile, identity, version FROM aggregates WHERE identity LIKE 'factory:%';
+            INSERT INTO schema_migrations VALUES (2, 3, 0);
+            UPDATE operational_schema SET version=3;
             COMMIT;
         """)
 
@@ -194,8 +203,26 @@ class SQLiteOperationalStore(FencedOperationalStore):
             raise VersionConflict(f"expected version {expected_version}, found {actual}")
         version = actual + 1
         connection.execute("INSERT INTO aggregates VALUES (?, ?, ?, ?) ON CONFLICT(profile, identity) DO UPDATE SET version=excluded.version, state=excluded.state", (profile, aggregate, version, json.dumps(state, sort_keys=True)))
+        if aggregate.startswith(PROJECTED):  # the projection obligation, durable together with the state
+            connection.execute("INSERT INTO projections VALUES (?, ?, ?) ON CONFLICT(profile, aggregate) DO UPDATE SET revision=excluded.revision", (profile, aggregate, version))
         return version
 
+    def pending_projections(self, profile: str) -> tuple[tuple[str, int], ...]:
+        """The outstanding projection obligations (aggregate, revision), from the obligations alone (no history)."""
+        with self._read() as connection:
+            rows = connection.execute("SELECT aggregate, revision FROM projections WHERE profile=? ORDER BY aggregate", (profile,)).fetchall()
+            return tuple((row["aggregate"], row["revision"]) for row in rows)
+
+    def owe_projection(self, profile: str, aggregate: str, revision: int) -> None:
+        """An obligation owed again (a projection overtaken by a newer commit), never lowering an outstanding one."""
+        with self._transaction() as connection:
+            connection.execute("INSERT INTO projections VALUES (?, ?, ?) ON CONFLICT(profile, aggregate) DO UPDATE SET revision=MAX(revision, excluded.revision)", (profile, aggregate, revision))
+
+    def retire_projection(self, profile: str, aggregate: str, revision: int) -> bool:
+        """Retire the obligation only if it is still for `revision`: a newer commit's obligation stays outstanding."""
+        with self._transaction() as connection:
+            return connection.execute("DELETE FROM projections WHERE profile=? AND aggregate=? AND revision=?", (profile, aggregate, revision)).rowcount == 1
+
     def read_state(self, profile: str, aggregate: str) -> tuple[int, dict[str, object]]:
         with self._read() as connection:
             row = connection.execute("SELECT version, state FROM aggregates WHERE profile=? AND identity=?", (profile, aggregate)).fetchone()
diff --git a/src/alienintent/execution_coordination/application/factory_coordinator.py b/src/alienintent/execution_coordination/application/factory_coordinator.py
index 86b822c..4e1db88 100644
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
@@ -160,23 +160,25 @@ class FactoryCoordinator:
         """One role step for exactly the named work item: the PRODUCER at IMPLEMENT, the VERIFIER at VERIFY or
         CLOSURE at ACCEPT.
 
-        At ACCEPT, writing nothing before the last step: the item is resolved from the READY snapshot, or else
-        `started_item`; a contract whose closure actions are not exactly the five fixed names answers
+        A started item is resolved from the READY snapshot, or else `started_item` at any stage (the board reflects
+        canonical work state; it does not determine it). At ACCEPT, writing nothing before the last step, a contract
+        whose closure actions are not exactly the five fixed names answers
         CLOSURE_NOT_AUTOMATED; an item at `ready-to-land` while landing is not enabled answers READY_TO_LAND.
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
+            started = self._resolve(identity, self._work.import_ready_snapshot(), projected.record or {})
         if projected is not None and projected.stage is LifecycleStage.ACCEPT:
-            accepted = self._resolve(identity, self._work.import_ready_snapshot(), projected.record or {})
-            if accepted is None or not is_fixed(accepted.contract.required_closure_actions):
+            if started is None or not is_fixed(started.contract.required_closure_actions):
                 return CLOSURE_NOT_AUTOMATED
             if projected.outcome == READY_TO_LAND and not self._landing_enabled():
                 return READY_TO_LAND
@@ -188,7 +190,7 @@ class FactoryCoordinator:
         if not self._recover(items):
             return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
         self._project_done()
-        item = next((ready for ready in items if ready.identity == identity), accepted)
+        item = next((ready for ready in items if ready.identity == identity), started)
         if item is None or not self._eligible(item):
             return NOT_ELIGIBLE
         producing = self._role(identity) == PRODUCER
@@ -725,12 +727,32 @@ class FactoryCoordinator:
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
diff --git a/src/alienintent/execution_coordination/ports/operational_store.py b/src/alienintent/execution_coordination/ports/operational_store.py
index 071206b..e771178 100644
--- a/src/alienintent/execution_coordination/ports/operational_store.py
+++ b/src/alienintent/execution_coordination/ports/operational_store.py
@@ -70,6 +70,9 @@ class OperationalStore(Protocol):
     def release(self, profile: str, scope: str, key: str, owner: str, fence: int) -> None: ...
     def read_state(self, profile: str, aggregate: str) -> tuple[int, dict[str, object]]: ...
     def list_states(self, profile: str, prefix: str = "") -> tuple[tuple[str, int, dict[str, object]], ...]: ...
+    def pending_projections(self, profile: str) -> tuple[tuple[str, int], ...]: ...
+    def owe_projection(self, profile: str, aggregate: str, revision: int) -> None: ...
+    def retire_projection(self, profile: str, aggregate: str, revision: int) -> bool: ...
     def commit_with_effect(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int: ...
     def mark_effect_unknown(self, profile: str, effect_id: str) -> None: ...
     def park_unknown_effect(self, profile: str, effect_id: str, expected_version: int, state: Mapping[str, object]) -> int: ...
diff --git a/src/alienintent/installation/application/doctor.py b/src/alienintent/installation/application/doctor.py
index 9001613..5354446 100644
--- a/src/alienintent/installation/application/doctor.py
+++ b/src/alienintent/installation/application/doctor.py
@@ -195,7 +195,8 @@ class InstallationDoctor:
                 raise DoctorFailure("persistence location is unavailable")
             observed = preflight()
             current_version, migration = getattr(observed, "current_version", None), getattr(observed, "migration", None)
-            if current_version != 2 or migration is not None:
+            # Settled is the store's own answer: a schema exists and its preflight names no migration to run.
+            if current_version is None or migration is not None:
                 raise DoctorFailure("persistence schema is incompatible or unsettled")
             return CheckEvidence.passed()
         raise DoctorFailure("persistence evidence is unavailable")
diff --git a/tests/composition/test_worker_launch.py b/tests/composition/test_worker_launch.py
index bb5df85..b107574 100644
--- a/tests/composition/test_worker_launch.py
+++ b/tests/composition/test_worker_launch.py
@@ -25,6 +25,7 @@ from alienintent.composition import work_registry
 from alienintent.composition.model_routing import provider_command
 from alienintent.composition.work_registry import WorkRegistry, launch_root, load_project_configuration
 from alienintent.control_plane.application.operator import exclusive_launch_work
+from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
 from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
 from alienintent.execution_coordination.domain.release import ReleaseSource
 from alienintent.invocation_runtime.adapters.git_worktree import ref_safe
@@ -2126,3 +2127,167 @@ def test_a_new_candidate_starts_with_no_verifier_retries(fx):
         fx.launch(item.id)
         state = fx.loaded().coordinator(None, None).state(item.id)
         assert (state.outcome, state.record["verifier_retries"]) == ("verifier-retry", retries)
+
+
+# --- CARD-FOLLOWS-STAGE: canonical state -> durable obligation -> card projector -> read-back -> retired ----------
+# The board reflects canonical Work state; it does not determine canonical Work state.
+
+def _card_writes(monkeypatch) -> list[str]:
+    written: list[str] = []
+    project = work_registry.WorkRegistry._project_card
+
+    def recording(self, identity, stage, revision):
+        written.append(stage)
+        return project(self, identity, stage, revision)
+    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", recording)
+    return written
+
+
+def _pending(closing: Closing) -> tuple:
+    return closing.fx.store.pending_projections("registry")
+
+
+def test_the_card_follows_the_canonical_stage_and_launch_never_needs_it_ready(closing, monkeypatch):
+    """IMPLEMENT is projectable while the PRODUCER works (its obligation is committed before the worker starts); the
+    next launches run although the card is no longer READY."""
+    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
+    item = closing.fx.authorized("UNIT", **FIXED)
+    written = _card_writes(monkeypatch)
+    start = RealWorkerProvider.start
+    mid_run = []
+
+    def projected_first(self, invocation, *args, **kwargs):  # the projector's pass while the worker runs
+        if invocation.role == "PRODUCER":
+            closing.fx.loaded().project_cards()
+            mid_run.append(closing.card(item.id))
+        return start(self, invocation, *args, **kwargs)
+    monkeypatch.setattr(RealWorkerProvider, "start", projected_first)
+    with closing.fx.loaded().card_projection(interval=60):
+        closing.fx.launch(item.id)
+    assert mid_run == ["IMPLEMENT"] and closing.card(item.id) == "VERIFY" and _pending(closing) == ()
+    with closing.fx.loaded().card_projection(interval=60):
+        closing.fx.launch(item.id)  # the card says VERIFY: resolved from the registry record
+    assert closing.state(item.id).stage is LifecycleStage.ACCEPT and closing.card(item.id) == "ACCEPT"
+    closing.close(item.id)
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "DONE" and written == ["IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]
+
+
+def test_a_crash_after_the_commit_and_before_any_projection_is_caught_up(closing):
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)  # no projector ran: the process "crashed" after its commits
+    assert closing.card(item.id) == "READY" and [a for a, _ in _pending(closing)] == [f"factory:{item.id}"]
+    assert closing.fx.loaded().project_cards() == 1  # a fresh projector
+    assert closing.card(item.id) == "VERIFY" and _pending(closing) == ()
+
+
+def test_a_crash_after_the_card_write_and_before_its_acknowledgement_replays_safely(closing, monkeypatch):
+    """The obligation is retired only after the card reads back; a crash in between leaves it outstanding and the
+    next pass writes the same status again."""
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)
+    written = _card_writes(monkeypatch)
+    retire = SQLiteOperationalStore.retire_projection
+
+    def crashing(self, profile, aggregate, revision):
+        raise RuntimeError("crash before the acknowledgement")
+    monkeypatch.setattr(SQLiteOperationalStore, "retire_projection", crashing)
+    with pytest.raises(RuntimeError):
+        closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1  # written, not acknowledged
+    monkeypatch.setattr(SQLiteOperationalStore, "retire_projection", retire)
+    assert closing.fx.loaded().project_cards() == 1
+    assert written == ["VERIFY", "VERIFY"] and closing.card(item.id) == "VERIFY" and _pending(closing) == ()
+
+
+def test_a_late_older_obligation_never_moves_the_card_backward(closing, monkeypatch):
+    """An obligation carries no status: a late one for an old revision projects the CURRENT canonical stage."""
+    item = closing.accepted()
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
+    with sqlite3.connect(closing.fx.store.path) as connection:  # a late obligation for the PRODUCER's revision
+        connection.execute("INSERT INTO projections VALUES ('registry', ?, 1)", (f"factory:{item.id}",))
+    written = _card_writes(monkeypatch)
+    assert closing.fx.loaded().project_cards() == 1
+    assert written == ["ACCEPT"] and closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
+
+
+def test_a_card_write_that_does_not_read_back_stays_outstanding_with_a_durable_diagnostic(closing):
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)
+    closing.ignore_status = True  # the board answers the write but keeps its Status
+    assert closing.fx.loaded().project_cards() == 0
+    assert closing.card(item.id) == "READY" and len(_pending(closing)) == 1
+    path = launch_root(closing.fx.loaded().configuration) / "projection-diagnostics.jsonl"
+    [record] = [json.loads(line) for line in path.read_text().splitlines()]
+    assert (record["identity"], record["state"], record["answered"], record["error"]) == (
+        item.id, "VERIFY", -1, "read back another status")
+    closing.ignore_status = False
+    assert closing.fx.loaded().project_cards() == 1 and closing.card(item.id) == "VERIFY"
+
+
+def test_after_a_decision_a_started_item_launches_without_a_ready_card(closing, monkeypatch):
+    """A recorded decision drops the item's `correlation`; it is resolved from its PRODUCER's launch."""
+    item = closing.accepted()
+    monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "refused:fixture")
+    closing.close(item.id)
+    closing.fx.loaded().project_cards()
+    assert closing.state(item.id).outcome == "authority-block" and closing.card(item.id) == "ACCEPT"
+    assert closing.fx.loaded().decide(item.id, "authorize", QUOTE)["answer"] is None
+    assert closing.state(item.id).record.get("correlation") is None
+    sessions = len(closing.fx.runs("CLOSURE"))
+    closing.close(item.id)
+    assert len(closing.fx.runs("CLOSURE")) == sessions + 1
+
+
+def test_start_runs_a_started_item_whose_card_has_moved_on(closing):
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "VERIFY"  # not on the READY board any more
+    closing.fx.loaded(Owners("terminated")).launcher().start()  # VERIFIER, then CLOSURE, in one call
+    assert closing.state(item.id).stage is LifecycleStage.DONE
+
+
+def test_a_projector_overtaken_by_a_newer_commit_reowes_and_the_card_converges(closing, monkeypatch):
+    """Two projectors overlap: B writes and retires the newer stage while A's older write is still in flight; A's
+    write lands last, so A re-owes the projection and the next pass shows the newest canonical stage."""
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)  # VERIFY, not yet projected
+    project = work_registry.WorkRegistry._project_card
+    overtaken = []
+
+    def in_flight(self, identity, stage, revision):
+        if not overtaken:
+            overtaken.append(stage)
+            closing.fx.launch(item.id)  # a newer commit: ACCEPT
+            assert closing.fx.loaded().project_cards() == 1  # projector B: ACCEPT written, obligation retired
+        return project(self, identity, stage, revision)  # A's VERIFY lands last
+    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", in_flight)
+    closing.fx.loaded().project_cards()  # projector A
+    assert overtaken == ["VERIFY"] and closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1
+    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", project)
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
+
+
+def test_an_overtaken_write_whose_read_back_fails_is_still_reowed(closing, monkeypatch):
+    """A's VERIFY change lands after B wrote and retired ACCEPT, then A's read-back fails: A still re-owes."""
+    item = closing.fx.authorized("UNIT", **FIXED)
+    closing.fx.launch(item.id)
+    project = work_registry.WorkRegistry._project_card
+    overtaken = []
+
+    def in_flight(self, identity, stage, revision):
+        if not overtaken:
+            overtaken.append(stage)
+            closing.fx.launch(item.id)  # ACCEPT
+            assert closing.fx.loaded().project_cards() == 1  # projector B
+            project(self, identity, stage, revision)  # A's change lands ...
+            return False  # ... and its read-back fails
+        return project(self, identity, stage, revision)
+    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", in_flight)
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1
+    closing.fx.loaded().project_cards()
+    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
diff --git a/tests/control_plane/test_cli.py b/tests/control_plane/test_cli.py
index 96c71a8..acc63ee 100644
--- a/tests/control_plane/test_cli.py
+++ b/tests/control_plane/test_cli.py
@@ -681,6 +681,32 @@ def test_work_launch_renders_one_step_and_work_context_passes_the_contract_diges
     assert calls == [("launch", "ITEM"), ("launch", "ITEM"), ("assemble", "sha256:abc"), ("assemble", None)]
 
 
+
+def test_work_launch_runs_inside_the_card_projector_and_work_project_runs_one_pass(monkeypatch, capsys, tmp_path) -> None:
+    """CARD-FOLLOWS-STAGE: the launch runs inside `card_projection`; `work project` is the projector on its own."""
+    from contextlib import contextmanager
+    from types import SimpleNamespace
+    from alienintent.control_plane.adapters import cli
+    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
+    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
+    calls = []
+
+    @contextmanager
+    def card_projection():
+        calls.append("projection-start")
+        yield
+        calls.append("projection-end")
+    launcher = SimpleNamespace(launch=lambda identity: calls.append("launch") or "closure-not-automated")
+    registry = SimpleNamespace(launcher=lambda: launcher, card_projection=card_projection,
+                               project_cards=lambda: calls.append("pass") or 2,
+                               store=SQLiteOperationalStore(tmp_path / "launch.sqlite"), ownership=ProcOwnership())
+    monkeypatch.setattr(cli, "_factory", lambda _: SimpleNamespace(work_registry=registry))
+    assert cli.main(["--json", "--profile-factory", "x:y", "work", "launch", "ITEM"]) == 0
+    assert calls == ["projection-start", "launch", "projection-end"]
+    capsys.readouterr()
+    assert cli.main(["--json", "--profile-factory", "x:y", "work", "project"]) == 0
+    assert json.loads(capsys.readouterr().out) == {"retired": 2} and calls[-1] == "pass"
+
 def test_two_launchers_taking_over_one_stale_launch_reservation_exactly_one_wins(tmp_path) -> None:
     """RESTART-CONTINUATION check 0: the loser of a takeover race (its release meets a stale fence) answers
     LAUNCH_IN_PROGRESS and launches nothing; the winner launches once and releases the reservation."""
diff --git a/tests/execution_coordination/test_operational_store.py b/tests/execution_coordination/test_operational_store.py
index d0e1f65..696dc38 100644
--- a/tests/execution_coordination/test_operational_store.py
+++ b/tests/execution_coordination/test_operational_store.py
@@ -223,11 +223,11 @@ def test_v1_schema_is_preflighted_then_migrated_with_durable_evidence(tmp_path:
     """)
     connection.close()
 
-    assert SQLiteOperationalStore.preflight(path).migration == (1, 2)
+    assert SQLiteOperationalStore.preflight(path).migration == (1, 3)
     SQLiteOperationalStore(path)
     with sqlite3.connect(path) as migrated:
-        assert migrated.execute("SELECT version FROM operational_schema").fetchone() == (2,)
-        assert migrated.execute("SELECT from_version, to_version, reversible FROM schema_migrations").fetchone() == (1, 2, 0)
+        assert migrated.execute("SELECT version FROM operational_schema").fetchone() == (3,)
+        assert migrated.execute("SELECT from_version, to_version, reversible FROM schema_migrations ORDER BY from_version").fetchall() == [(1, 2, 0), (2, 3, 0)]
 
 
 def test_outbox_executor_marks_unknown_before_send_and_confirms_readback(tmp_path: Path) -> None:
@@ -429,3 +429,24 @@ def test_a_read_only_open_refuses_a_missing_or_other_schema_database(tmp_path: P
     with pytest.raises(SchemaIncompatible):
         SQLiteOperationalStore(empty, read_only=True)
     assert empty.read_bytes() == b""
+
+
+@pytest.mark.parametrize("table", ["projections", "aggregates"])
+def test_a_crash_before_the_state_and_its_projection_obligation_commit_leaves_neither(tmp_path: Path, table) -> None:
+    """CARD-FOLLOWS-STAGE: the obligation is durable together with the state, or neither is (whichever write fails)."""
+    store = SQLiteOperationalStore(tmp_path / "outbox.sqlite")
+    with sqlite3.connect(tmp_path / "outbox.sqlite") as connection:
+        connection.execute(f"CREATE TRIGGER crash BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT, 'crash'); END")
+    with pytest.raises(Exception):
+        store.commit("registry", "factory:item", 0, {"stage": "IMPLEMENT"})
+    assert store.read_state("registry", "factory:item") == (0, {}) and store.pending_projections("registry") == ()
+
+
+def test_projection_obligations_are_one_per_work_item_and_retire_only_at_their_revision(tmp_path: Path) -> None:
+    store = SQLiteOperationalStore(tmp_path / "outbox.sqlite")
+    store.commit("registry", "factory:item", 0, {"stage": "IMPLEMENT"})
+    store.commit("registry", "factory:item", 1, {"stage": "VERIFY"})
+    store.commit("registry", "decision-inbox", 0, {"open": {}})
+    assert store.pending_projections("registry") == (("factory:item", 2),)
+    assert store.retire_projection("registry", "factory:item", 1) is False  # a newer commit's obligation stays
+    assert store.retire_projection("registry", "factory:item", 2) is True and store.pending_projections("registry") == ()
diff --git a/tests/installation/test_doctor_evidence.py b/tests/installation/test_doctor_evidence.py
index 0278663..8b31d3d 100644
--- a/tests/installation/test_doctor_evidence.py
+++ b/tests/installation/test_doctor_evidence.py
@@ -59,7 +59,7 @@ def test_doctor_rejects_persistence_whose_migration_has_not_settled(tmp_path: Pa
         connection.execute("CREATE TABLE operational_schema (version INTEGER NOT NULL)")
         connection.execute("INSERT INTO operational_schema VALUES (1)")
     observed = _preflight(database)
-    assert (observed.current_version, observed.migration) == (1, (1, 2))
+    assert (observed.current_version, observed.migration) == (1, (1, 3))
 
     report = _doctor(tmp_path, persistence_database=database)
 
diff --git a/tools/fitness/coupling_register.json b/tools/fitness/coupling_register.json
index 50fcc5d..68f93b2 100644
--- a/tools/fitness/coupling_register.json
+++ b/tools/fitness/coupling_register.json
@@ -233,6 +233,7 @@
         "effects",
         "fences",
         "operational_schema",
+        "projections",
         "receipts",
         "reservations",
         "schema_migrations"
```

## 3. Acceptance checks

The Founder's crash proof:

1. **Crash before the state and its obligation commit: neither exists, whichever write fails**
   (`tests/execution_coordination/test_operational_store.py::test_a_crash_before_the_state_and_its_projection_obligation_commit_leaves_neither`).
2. **Crash after the commit, before any projection: a fresh projector catches up**
   (`tests/composition/test_worker_launch.py::test_a_crash_after_the_commit_and_before_any_projection_is_caught_up`).
3. **Crash after the card write, before its acknowledgement: safe replay**
   (`tests/composition/test_worker_launch.py::test_a_crash_after_the_card_write_and_before_its_acknowledgement_replays_safely`): the card shows VERIFY,
   the obligation stays; the next pass writes VERIFY again and retires it.
4. **A late, older obligation never moves the card backward**
   (`tests/composition/test_worker_launch.py::test_a_late_older_obligation_never_moves_the_card_backward`): the card at ACCEPT, a late obligation for the
   PRODUCER's revision; the pass writes ACCEPT.

And:

5. **One obligation per work item; retired only at its revision**
   (`tests/execution_coordination/test_operational_store.py::test_projection_obligations_are_one_per_work_item_and_retire_only_at_their_revision`).
6. **The card follows the stage; IMPLEMENT shows while the PRODUCER works; launch never needs READY**
   (`tests/composition/test_worker_launch.py::test_the_card_follows_the_canonical_stage_and_launch_never_needs_it_ready`).
7. **A write that does not read back stays outstanding with a durable diagnostic**
   (`tests/composition/test_worker_launch.py::test_a_card_write_that_does_not_read_back_stays_outstanding_with_a_durable_diagnostic`).
8. **Started items off the READY board run** (`tests/composition/test_worker_launch.py::test_start_runs_a_started_item_whose_card_has_moved_on`,
   `tests/composition/test_worker_launch.py::test_after_a_decision_a_started_item_launches_without_a_ready_card`).
9. **`work launch` runs inside the projector; `work project` runs one pass**
   (`tests/control_plane/test_cli.py::test_work_launch_runs_inside_the_card_projector_and_work_project_runs_one_pass`).
10. **Overlapping projectors converge** (`tests/composition/test_worker_launch.py::test_a_projector_overtaken_by_a_newer_commit_reowes_and_the_card_converges`):
   projector A's VERIFY write is overtaken by a commit to ACCEPT that projector B writes and retires; A's write lands
   last, A owes the projection again, and the next pass shows ACCEPT.
11. **An overtaken write whose read-back fails is still owed**
   (`tests/composition/test_worker_launch.py::test_an_overtaken_write_whose_read_back_fails_is_still_reowed`): as check 10, but A's change lands and its
   read-back fails; A still owes the projection and the next pass shows ACCEPT.
12. **Mutations, run exactly by the VERIFIER** (each must fail its named test and pass when reverted):
   - **P1:** in `_commit`, `if aggregate.startswith(PROJECTED):` made `if False:` -> check 2's test.
   - **P2:** `retire_projection`'s `DELETE ... AND revision=?` without the revision condition -> check 5's test.
   - **P3:** in `project_cards`, the `store.owe_projection(...)` line deleted -> check 10's test.
   - **P9:** `if written is not None and now != version:` made `if written and now != version:` -> check 11's test.
   - **P4:** in the CLI, `with projection() if projection is not None else nullcontext():` made
     `with nullcontext():` -> check 9's test.
   - **P5:** in `launch`, `projected.stage in ROLE_BY_STAGE` made `projected.stage is LifecycleStage.ACCEPT` ->
     check 6's test.
   - **P6:** `for correlation in (raw.get("correlation"), raw.get("producer_correlation")):` made
     `for correlation in (raw.get("correlation"),):` -> `test_after_a_decision_a_started_item_launches_without_a_ready_card`.
   - **P7:** in `start`, `self._with_started(self._work.import_ready_snapshot())` made
     `self._work.import_ready_snapshot()` -> `test_start_runs_a_started_item_whose_card_has_moved_on`.
   - **P8:** in `_project_card`, the `self._projection_diagnostic(...)` call replaced by a no-op -> check 7's test.

The whole suite at the candidate has no failed or error test case (proven by the factory's regression gate; Founder:
no extra whole-suite runs), and `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (not in this item)

- READY is still read from the board for a work item's first launch and its priority; no READY or HOLD card state is
  projected (plan authority's item and a later decision).
- `guard_account`, `_block_dependents` and `record_decision` still read only the READY snapshot.
- Overlapping projectors (a `work project` beside a launch, a refused second launch) can leave an older status on a
  card until the next pass (checks 10-11). A change whose answer is lost (a client timeout, 20 s, no retry) and that
  GitHub applies only after a newer stage was written and retired can leave an older status until the item's next
  commit; GitHub offers no compare-and-set to prevent it. CLOSURE's own `board-updated` DONE write stays as it is.
- `work launch` returns after waiting up to `CARD_PROJECTION_SECONDS + 30` s for the projector thread, then a final pass
  that stops starting items after `CARD_FINAL_PASS_SECONDS` (30 s); an item already in flight can add its transport
  timeouts (up to 3 x 20 s) while GitHub is down.
- `projection-diagnostics.jsonl` is not rotated (one line per distinct failure per process); `_with_started` reads
  the invocation journal once per started item on every `start()`.
- The 2 -> 3 migration owes an obligation to every existing `factory:` aggregate of every profile; only `registry`
  obligations are consumed (one row per item elsewhere, never growing). The 2 -> 3 migration is not reversible.
- After landing, the first writable open of the registry store migrates it to schema 3 (a read-only open before that
  refuses the old schema, as today for any schema change).

## 4. Evidence and review record

A prototype that is exactly section 2's diff, on `2b47f21` (not the candidate):
`manual/path-to-done/card-follows-stage/prototype-outbox-on-2b47f21.diff`, sha256 `c6618a79…2ff6a`. With it
the touched test files pass, the architecture fitness check passes, and P1-P8 each fail their named test and pass when
reverted (`mutations-and-targeted-run.log` for revision 4; `mutations-rev5.log` for P1-P9 after the revision 5 fix,
with the projection tests re-run). The
superseded synchronous design is kept as `rev2-synchronous-superseded.diff`.

**Revision 5 (2026-10-09).** Follow-up REVIEWER of `30ce7aa` (FAIL; R1-R3). R1: an overtaken write whose read-back
failed returned before the overtaken check, leaving a stale card with nothing owed; the check now runs for any
attempted write (check 11, P9). R2: invariant 4 no longer claims "always repaired"; the lost-answer case is a stated
limit. R3: the real shutdown bound is stated.

**Revision 4 (2026-10-09).** REVIEWER of `172a513` (FAIL; D1-D7). D1: overlapping projectors could leave a card
behind with nothing owed (the acknowledgement fence did not fence the GitHub write); the acknowledgement record is
gone and a projection overtaken while in flight is owed again (check 10, P3). D2: an item with no linked card is
retired; diagnostics are written once per distinct failure. D3: the final pass is bounded and skipped while the
thread still runs. D4: check 1 aborts either write. D5: check 4 uses a realistic late obligation. D6: 2 -> 3 is
recorded not reversible; unconsumed profiles stated. D7: fresh evidence log.

**Revision 3 (2026-10-09).** Rebuilt on the Founder's outbox decision (section 12) after the follow-up review of
revision 2 (FAIL: a projection before the commit loses a crashed first launch; no placement inside the launch window
is safe). The coordinator no longer projects; the obligation, projector, fence, read-back, CLI wiring and the four
crash checks are new; two hardcoded schema-2 checks found by the targeted run are fixed at their source.

**Revision 2 (2026-10-09).** Synchronous projection moved before the effect (superseded).

**Revision 1 (2026-10-09).** Synchronous projection from the coordinator (superseded).
