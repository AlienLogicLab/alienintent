# Work unit: worker sessions carry the worker's own user name; AGENTS.md states the factory's receipt rule

**Label:** `WORKER-SESSION-IDENTITY` (a document label; permanent id `e0cffbb5-4037-4604-bb92-fef989661ae5`).
**Status:** Draft revision 1 (work item `e0cffbb5-4037-4604-bb92-fef989661ae5`, at CAPTURE) for independent review, 2026-10-06. Not approved, not assessed, not released.
**Position on the path:** repairs the execution and verification environment needed to evaluate BOARD-FOLLOWS-WORK-STATE
correctly. **This work item does not change BOARD-FOLLOWS-WORK-STATE behaviour.** Built outside the factory (its own
VERIFIER session would hit the user-name defect it fixes): one PRODUCER, one fresh VERIFIER on the exact candidate,
direct merge to `main`.
**Roles:** PRODUCER (self-reviews the complete diff); fresh VERIFIER on the exact candidate; CLOSURE by direct merge.

## Contract

```json alienintent-contract
{
 "identity": "e0cffbb5-4037-4604-bb92-fef989661ae5",
 "version": "revision-1",
 "intent": "With a worker user, every command the factory runs as that user gets USER and LOGNAME equal to the worker user instead of the Founder's inherited values; and AGENTS.md and docs/operations.md state where the factory's feature-regression receipt actually lives, so a VERIFIER never requires a receipt committed inside the candidate when the invocation runtime keeps and hands over that receipt itself.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: c6814e01 stays FAILED after 3 attempts; it is not revived.",
  "Founder 2026-10-06: this work item does not change BOARD-FOLLOWS-WORK-STATE behaviour; it repairs the execution and verification environment.",
  "Founder 2026-10-06: any pre-verification reproduction of worker behaviour runs through the same worker session construction the factory uses; no hand-built env -i approximations."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_registry.py",
  "AGENTS.md",
  "docs/operations.md",
  "tests/composition/test_worker_launch.py"
 ],
 "excluded_scope": [
  "sandbox_run_profile.worker_environment and the non-worker path (without a worker user USER stays inherited)",
  "tools/live scripts, the regression runner and its receipt format",
  "the coordinator, the board and the landing path",
  "any other environment variable"
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
  "check 1 fails on the starting revision and passes on the candidate",
  "check 4 runs through the factory's own worker session construction"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "renaming the worker user or changing its uid"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-credential-boundary.md"
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
  "another place builds an environment for commands run as the worker user and does not get the change",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

`WorkRegistry._launch_chain` (`work_registry.py` about lines 640-650) builds the one environment every worker command
uses: `worker_environment(root)` (which copies `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM`, `SHELL` and `USER` from the
launching process, `sandbox_run_profile.py` about line 402) plus `HOME`, `TMPDIR` and `CODEX_HOME` for the worker. `USER`
stays the Founder's (`netmarine`) and there is no `LOGNAME`. So a VERIFIER session runs as uid 997 with `USER=netmarine`,
and test fixtures that use `getpass.getuser()` expect uid 1000: in work item `c6814e01` two tests in
`tests/composition/test_worker_launch.py` failed inside the VERIFIER's session for that reason.

`AGENTS.md` (about line 52) says a verdict is inadmissible "unless the exact candidate carries a valid passing
`.alienintent/feature-regressions.json` receipt". With a worker user the invocation runtime writes the receipt to
`<launch>/results/<invocation>/feature-regressions.json` (`cli_worker.py` about line 140) and hands it to the coordinator;
the candidate does not carry it. The VERIFIER of `c6814e01` rejected on that instruction. `docs/operations.md` (about
line 93) has the same one-sided statement.

## 2. The change

1. **`work_registry.py`, `_launch_chain`, worker branch** (the `environment = environment | {"HOME": ..., "TMPDIR": ...,
   "CODEX_HOME": ...}` line): add `"USER": user, "LOGNAME": user`. Nothing else in the environment changes, and the
   non-worker branch is unchanged.
2. **`AGENTS.md`**: replace the sentence "A verifier verdict is inadmissible unless the exact candidate carries a valid
   passing `.alienintent/feature-regressions.json` receipt." with: "A verifier verdict is inadmissible unless the
   invocation runtime holds a valid passing feature-regression receipt for the exact candidate. Without a worker user
   the runtime writes it to `.alienintent/feature-regressions.json` in the workspace; with a worker user it writes it
   to the launch results folder and hands it to the coordinator. A VERIFIER never requires the receipt to be committed
   in the candidate."
3. **`docs/operations.md`** (about line 93): replace "A passing run writes `.alienintent/feature-regressions.json`, bound
   to the exact candidate revision" with "A passing run writes the receipt (`.alienintent/feature-regressions.json` in
   the workspace, or with a worker user `<launch>/results/<invocation>/feature-regressions.json`), bound to the exact
   candidate revision".
4. **Tests** (`test_worker_launch.py`): `WORKER_ALLOWED` gains `"LOGNAME"`; the worker-user tests assert
   `env["USER"] == env["LOGNAME"] == <the configured worker user>`.

## 3. Acceptance checks

1. **The worker's name in its environment** (`test_worker_launch.py`): with a worker user configured and the launching
   process's `USER` set to another name, every command recorded by the fake sudo (session, regression runner, clone)
   carries `USER` and `LOGNAME` equal to the worker user. Fails on the starting revision.
2. **Nothing else changes** (`test_worker_launch.py`): the recorded worker environment's names are exactly
   `WORKER_ALLOWED`, and without a worker user `USER` is the inherited value and there is no `LOGNAME`.
3. **The receipt rule cannot drift back** (`test_worker_launch.py`): `AGENTS.md` does not contain "exact candidate
   carries a valid passing", and its VERIFY paragraph names both receipt locations; `docs/operations.md` names the
   results-folder location.
4. **Through the factory's own construction, as the real worker** (run by the VERIFIER):
   - `env = WorkRegistry(load_project_configuration(<projects.json>, "AlienLogicLab/alienintent"))._launch_chain()[1]._process._environment`
     (the exact environment the factory launches with), using the candidate's `src` on `PYTHONPATH`;
   - `run_as_worker("alienintent-worker", env, ["sh", "-c", "id -un; id -u; echo $USER $LOGNAME"])` prints
     `alienintent-worker`, `997`, and `alienintent-worker alienintent-worker`;
   - in a clone of the candidate at `<launch>/worker/verifier-launch-<this work item id>-99`, `run_as_worker` with the same
     `env` runs `python3 -m pytest -q tests/composition/test_worker_launch.py`, which passes; the folder is removed afterwards.
   Plus `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Review record

**Revision 1 (2026-10-06).** First draft, from the VERIFIER findings of `c6814e01` and the Founder's direction of 2026-10-06.
