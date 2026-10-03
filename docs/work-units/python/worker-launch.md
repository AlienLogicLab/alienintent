# Work unit: worker launch for a registered work item

**Label:** `WORKER-LAUNCH` (a document label; permanent id `621b0120-9fd2-41a0-b816-0b30ecf14281`).
**Status:** Draft revision 2 (work item `621b0120-9fd2-41a0-b816-0b30ecf14281`, at CAPTURE) for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6c-2, the second of the two units the Founder split unit 6c into on 2026-10-03. 6c-1 assembles each role's context package; this unit launches the PRODUCER and the VERIFIER with it. Builds on units 6a, 6b and 6c-1.
**Dependency:** unit 6c-1, work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b` (in the contract block). Evidence that it is complete: its accepted candidate `c36688492487c41aa41aebd4778d54aec7ceeece` is landed on `main` by merge `81cd23c`, with landing record `docs/evidence/work-context-package-landing-c366884.md` at `a5087d7`. Its work registry row still shows CAPTURE. That is a bookkeeping gap: packet work items are not yet moved through the workflow states. It does not mean the dependency is incomplete. It does matter to the coordinator: `_eligible` needs the dependency's `factory:` record at DONE, so this work item cannot pass `work launch` until that gap is closed. It is built by the manual workflow.
This packet is built by the manual workflow, not by `work launch`, so its budget carries no launch limits.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "621b0120-9fd2-41a0-b816-0b30ecf14281",
 "version": "revision-2",
 "intent": "Launch exactly one role step (PRODUCER at IMPLEMENT or VERIFIER at VERIFY) for one named registered work item through the existing release gate and WIP admission: each role receives its 6c-1 context package assembled at launch, the PRODUCER starts from the release record's starting revision, the model, executable and permission mode are injected from the shared routing file at every launch through the existing provider command builder, the worker's own later context calls check the launched contract fingerprint, the PRODUCER's self-review is recorded against the exact stored candidate, and missing or mismatched facts prevent launch; reuse the existing worker chain, process ownership and cleanup.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-03: separate PRODUCER and VERIFIER processes with the exact registered instructions, the deterministic context, runtime-injected model assignments from ~/.config/alienintent/model-routing.json; reuse the existing process ownership and cleanup; missing context, invalid authorization or unavailable model configuration prevents launch; no new configuration source or context mechanism.",
  "Founder 2026-10-03: proof shows both roles receiving the correct package and injected model assignment, the PRODUCER starting from the authorized revision, and later context calls checking the launched contract fingerprint; missing or mismatched facts prevent launch.",
  "Founder 2026-10-03: one command per role step; restart continuation, closure automation and automatic selection of the next item stay in their later planned units.",
  "Founder 2026-10-03: every packet launched this way states explicit execution and shutdown limits (budget_policy hard_wall_clock_seconds and cancellation_limit), approved with that packet; no hidden defaults.",
  "Founder 2026-10-03: only the control plane publishes is a workflow rule, not enforced, while workers keep their user's filesystem access; a permission mode is not operating-system isolation; no stronger protection is claimed.",
  "Founder 2026-10-03: reuse the existing provider-contract tests; a real-provider check is required before worker launch is called operational."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/composition/model_routing.py",
  "tools/orchestration/model_routing.py",
  "tools/orchestration/factory_director_host.py",
  "tools/orchestration/install_factory_director_host.sh",
  "tools/live/worker_launch_provider_check.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_work_registry.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_real_worker_outcome.py",
  "tests/context_assembly/test_work_context.py",
  "tests/control_plane/test_cli.py",
  "tools/orchestration/test_model_routing.py"
 ],
 "excluded_scope": [
  "restart continuation of an interrupted launch",
  "closure automation",
  "automatic selection of the next work item",
  "an operating-system sandbox",
  "changing the release gate, WIP admission or the 6c-1 holds",
  "a new store, record kind or configuration source",
  "changing earlier packets"
 ],
 "dependencies": [
  "5befff2f-a0dd-4cea-9556-54c33ed86c1b"
 ],
 "required_capabilities": [
  "python",
  "git",
  "sqlite",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-10 pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "VERIFIER reviews the Founder-run real-provider check evidence"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "real-provider check output",
  "landing record on main"
 ],
 "non_goals": [
  "restart continuation",
  "closure automation",
  "next-item selection"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/work-context-package.md",
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
  "scope outside the authorized files",
  "the real-provider check fails"
 ]
}
```

## 0. The whole design (plain English)

Today nothing launches a real PRODUCER or VERIFIER for a registered work item. `WorkRegistry.coordinator(worker, artifacts)` (unit 6b) exists, but only tests give it a worker. The existing worker classes have three gaps for this use:
- the PRODUCER's workspace always starts at `HEAD`, not at the release record's starting revision (`real_worker.py` line 295);
- the worker command is one fixed command line, so no model is chosen per role, the Python worker never reads the routing file, and `CliWorkerProvider` validates its permission mode argument but never passes it on (`cli_worker.py` lines 24-33);
- no worker receives its instructions or context package, and no PRODUCER self-review is captured.

This unit closes those gaps. It reuses the existing worker chain, process ownership and cleanup, the 6c-1 context package and the existing shared routing file. It adds one command that launches exactly one step for one named work item.

1. **One command, one step.** `work launch <id>` runs one coordinator step for the named work item: the PRODUCER launch at IMPLEMENT or the VERIFIER launch at VERIFY. The work item's stage decides which. It goes through the existing release gate and WIP admission (unit 6b), launches one worker, records the outcome and stops. It never picks another item, never goes on to the next role by itself, and never runs CLOSURE. At ACCEPT it answers `closure-not-automated`, because CLOSURE stays the separate manual role.
2. **The context package is built at launch.** Inside the worker launch, after the coordinator has saved the launch, the existing `WorkContext.assemble` builds the role's package. For the VERIFIER this happens in its fresh candidate clone. That is the only point where the 6c-1 attempt check passes. A hold means the worker is not started: the launch is recorded as an authority block naming the hold, and the work item keeps its WIP slot.
3. **The PRODUCER starts from the authorized revision.** Its worktree is created at the package's `starting_revision`, the release record's baseline, never at `HEAD`.
4. **The model is injected at launch.** The role's route (provider, model, executable, permission mode) is read from `~/.config/alienintent/model-routing.json` at every launch, with no cache and no default. The worker command is built from it by the existing provider command builder, the one the Factory Director host uses, so it follows the existing provider contract. Missing or invalid routing means the worker is not started.
5. **Later context calls check the launched fingerprint** (6c-1 follow-up F1). The package's `context_command` carries the launched invocation's contract digest. `work context` gains `--contract-digest`, and a different digest is held as `DIGEST_MISMATCH`.
6. **The self-review is captured.** The PRODUCER writes its self-review to a stated file outside its worktree. After the candidate is published and read back, the launch records it with the existing `record_self_review`, using the exact candidate the coordinator stores (6c-1 follow-up F4).

Nothing else changes: no new store, record kind, configuration source or context mechanism.

## 1. The changes

**1. `work launch <id>`** (`control_plane/adapters/cli.py`, `control_plane/application/operator.py`) calls a new `FactoryCoordinator.launch(identity)` (`execution_coordination/application/factory_coordinator.py`). It:
- reads the work item's state; at ACCEPT (the CLOSURE role's stage) it answers `closure-not-automated` with no write;
- writes the explicit human release as `release_and_start` does today;
- runs the existing `_recover` once; `_recover` may record already-durable outcomes of other launches, as `start()` does; it starts no worker;
- if `_eligible` does not admit the item, answers `not-eligible` (the release record stays, as with `release_and_start`); otherwise runs `_run` once for that item and returns its `RunSummary`, a WIP skip answering `wip-refused` or `wip-limit-unavailable`.

The named work item must be in the READY view; otherwise `not-eligible`. It does not call `start()`, so no other released work item runs. `release_and_start` and `start()` are unchanged.

Unchanged existing behaviour: a contract whose `required_capabilities` go beyond `python`, `filesystem` and `process-control` is held at release admission until a recorded `authorize` decision; `work launch` reports that hold like any other.

**2. The registry launch composition** (`composition/work_registry.py`), `WorkRegistry.launcher()`, follows the existing `SandboxRunProfile` chain (`composition/sandbox_run_profile.py` lines 304-332):
- `CliWorkerProvider` with the `worker_environment` allowlist, plus `ALIENINTENT_PROJECT_CONFIGURATION` and `ALIENINTENT_PROJECT` (the two the `context_command` names);
- `RealWorkerProvider` with the pointer repository's clone, the invocation journal, `GitWorktreeAdapter` and `ProcOwnership`, and one grant per dispatch;
- `RoleBindingGuard`;
- `WorkRegistry.coordinator(worker, artifacts)`.

Its state (journal, workspaces, verifier clones, context root) lives under the existing registry folder, in `launch/`. No new configuration is read.

**3. One preparation hook on `RealWorkerProvider`** (`invocation_runtime/application/real_worker.py`). It follows the existing style of the `branch` and `grant` hooks: an optional `preparation` object with two calls.
- `prepare(invocation, clone)` is called first in `_produce`, before the existing budget, grant and reservation checks, and in `_evaluate` right after the fresh candidate clone is made. For the VERIFIER it is given that clone. It returns either the starting revision, or a refusal.
- A refusal is a complete `WorkerOutcome` of kind `authority-block`, built by the registry preparation (composition), with an escalation naming the hold reason and field and the same text as its one finding. `RealWorkerProvider` returns it unchanged, so the journal keeps the reason as a finding. Nothing is started.
- The PRODUCER worktree is allocated at the returned starting revision instead of `"HEAD"`.
- `published(invocation, candidate)` is called after a PRODUCER candidate is published and read back.

Without a `preparation`, behaviour is unchanged.

**4. A per-invocation command on `CliWorkerProvider`** (`invocation_runtime/adapters/cli_worker.py`). The worker command may be a callable of `(invocation_id, role, workspace)`, evaluated at `run`, as `branch` and `grant` already are on `RealWorkerProvider`. It returns the command line and the text for the worker's standard input; the Director host passes its prompt the same way, on standard input. A fixed tuple keeps today's behaviour, with standard input unchanged. The registry composition passes a callable that builds the command line with `provider_command(route, workspace)` from the route and instruction text `prepare` kept for that invocation.

**5. The registry preparation** (`composition/work_registry.py`) implements the hook. For one invocation, `prepare`:
1. Checks the contract's `budget_policy` states `hard_wall_clock_seconds` and `cancellation_limit`. Otherwise it refuses with `MISSING_RECORD` naming `budget_policy`; today `RealWorkerProvider` would answer `ineligible` instead.
2. Calls `WorkContext.assemble(identity, role, invocation.correlation_id, invocation.contract_digest, candidate, clone)`. A `ContextHold` is a refusal naming its reason and fields.
3. Reads the role's route from `model-routing.json` through the existing reader (change 6). An unreadable file or `MODEL_ROUTING_INVALID` refuses with `model-routing-unavailable`.
4. Writes the package as JSON to `<context root>/<invocation id>.json`, outside any worktree.
5. Keeps the route and one fixed instruction text for the invocation; the command is built at `run` with `provider_command(route, workspace)` (change 6), and the instruction text is given on standard input. The text tells the worker where its package is, to do only what the package states, how to call `context_command`, and where to write its result: the PRODUCER commits in its worktree and writes its self-review to `<context root>/<invocation id>.self-review.md`; the VERIFIER writes `.alienintent/verdict.json` in the existing verdict format.
6. Returns the package's `starting_revision`.

`published` reads the self-review file and calls `record_self_review(identity, candidate, text)` with the published, read-back candidate. If the file is missing or empty, or recording fails for any reason, nothing is recorded and `published` does not raise, and the VERIFIER's launch is later held `MISSING_RECORD` (6c-1 step 8).

**6. One routing reader and one provider command builder.** The existing Python reader `tools/orchestration/model_routing.py` (`routing_path`, `resolve_route`) moves unchanged to `src/alienintent/composition/model_routing.py`, because the architecture check allows configuration reads only in composition. The existing provider command builder, `ProcessDirectorLauncher.command` in `tools/orchestration/factory_director_host.py` (lines 203-209: claude `-p --no-session-persistence --output-format json --permission-mode <mode> --model <model>`; codex `exec --ephemeral --json --sandbox <mode> -C <workdir> --model <model> -`), moves to the same module as `provider_command(route, workdir)`. The moved module uses only the standard library. The Director host is installed as standalone files and run by plain `python3` (`install_factory_director_host.sh` lines 14-18 and 40), so `install_factory_director_host.sh` installs `src/alienintent/composition/model_routing.py` as `model_routing.py` in place of the tools copy. `tools/orchestration/model_routing.py` re-exports it by file path, without importing the `alienintent` package. `ProcessDirectorLauncher.command` stays as a method and calls `provider_command(route, self.workdir)`. The schema, the error and the `ALIENINTENT_MODEL_ROUTING` override are unchanged.

**7. The launched fingerprint on later context calls** (6c-1 follow-up F1). `ContextCommand` (`context_assembly/application/work_context.py`) adds `--contract-digest <digest>` when assembly was given one. `work context` accepts `--contract-digest` and passes it to `assemble`, which already compares it (6c-1 step 5).

## 2. Access restrictions (what is enforced, and what is not)

Enforced by existing code:
- the worker's environment is the stated allowlist, not the inherited one, so no API key, publication token or `GIT_CONFIG_*` credential in the operator's environment is passed on;
- each PRODUCER is given its own worktree, and each VERIFIER a fresh clone (a starting place, not a confinement);
- the worker's process group is owned, stopped at its wall clock and cleaned up through the existing ownership and cleanup.

Workflow rules, not enforced:
- **Only the control plane publishes.** This is a workflow rule. The allowlist keeps `HOME`, and the worker runs as the same user, so it can still reach that user's files: provider logins, `gh` and git credentials, SSH keys and the registry's GitHub App key. No existing credential restriction stops a worker pushing. The instruction text states the rule. Nothing prevents a worker breaking it, and nothing reliably detects it afterwards: the VERIFIER's independent read-back confirms one particular candidate commit, not that no other push or outside change happened.
- **The registry clone.** The PRODUCER worktree is a linked worktree of the pointer repository's clone, so it shares that clone's refs and objects, which the release gate and packet reads use. A worker can change that clone's local branches. Nothing prevents it.
- **The permission mode** from the routing file is now passed to the worker's provider, as the Director host already does (today the Python worker passes none). It is the provider's own setting, not operating-system isolation. The live modes (`danger-full-access`, `bypassPermissions`) let a worker write wherever its user can.

No operating-system sandbox exists in Python, and none is claimed. This is the limit the Founder accepted in 6c-1. Changing it is separate work.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/application/factory_coordinator.py` (`launch`)
- `src/alienintent/composition/work_registry.py` (launcher and preparation)
- `src/alienintent/composition/model_routing.py` (new, moved reader)
- `tools/orchestration/model_routing.py` (re-export), `tools/orchestration/factory_director_host.py` (call the moved command builder), `tools/orchestration/install_factory_director_host.sh` (install the moved module)
- `tools/live/worker_launch_provider_check.py` (new, the real-provider check script)
- `src/alienintent/invocation_runtime/application/real_worker.py` (preparation hook, starting revision)
- `src/alienintent/invocation_runtime/adapters/cli_worker.py` (per-invocation command)
- `src/alienintent/context_assembly/application/work_context.py` (`--contract-digest` in `context_command`)
- `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py` (`work launch`, `work context --contract-digest`)

Tests:
- `tests/composition/test_worker_launch.py` (new)
- `tests/composition/test_work_registry.py`
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/invocation_runtime/test_runtime.py`, `tests/invocation_runtime/test_real_worker_outcome.py`
- `tests/context_assembly/test_work_context.py`
- `tests/control_plane/test_cli.py`
- `tools/orchestration/test_model_routing.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The worker executables come from a test routing file and are fake scripts that record what they receive. No model is called.

1. **Each role receives the correct package.** A launched PRODUCER and a launched VERIFIER each find, at their stated path, exactly the package `assemble` gives for that work item, role and attempt. The VERIFIER's comes from its fresh candidate clone and includes its diff and the labelled self-review. Catches a missing, wrong-role or stale package.
2. **The injected model assignment, through the existing provider contract.** Each role's command is the existing provider command for the route chosen for that role at launch time: for claude and codex exactly the Director host's command, which has the same flags in the same order as `src/providers/claude.mjs` and `src/providers/codex.mjs`; only the last argument differs: Node passes the prompt as that argument, while the Director host and this unit pass it on standard input (codex `-`, claude no prompt argument). The instruction text arrives on standard input. Changing the routing file between two launches changes the next command. The existing provider-contract tests are reused unchanged and still pass: `tools/orchestration/test_factory_director_host.py` and `test/worker-runner.test.mjs`. Catches a fixed command, a cached route, a dropped permission mode and a command that drifts from the provider contract.
3. **The PRODUCER starts from the authorized revision.** The PRODUCER's worktree is at the release record's baseline. A commit added on top of the default branch afterwards is not in it. Catches a launch at `HEAD`.
4. **Later context calls check the launched fingerprint.** The worker running its own `context_command` gets its package. The same call with another contract digest is held `DIGEST_MISMATCH`. Catches a command without the digest and a digest that is not compared.
5. **Missing or mismatched facts prevent launch.** Each case below ends as an authority block naming the reason: a release-gate refusal as the coordinator's existing `release-precondition:<check>` record, every other case as a journaled worker outcome. No worker process is started, the work item keeps any WIP slot it already holds (a release-gate refusal comes before WIP admission, so a first launch holds none), and a further `work launch` answers `not-eligible`:
   - no release record;
   - a release record whose evidence no longer matches the work item;
   - a context hold, for example no READY assessment of the current pointer;
   - for the PRODUCER, a missing budget field (a VERIFIER launch only follows a PRODUCER launch of the same contract);
   - a missing routing file, invalid routing, or a role with no usable route;
   - for the VERIFIER, no self-review.
   Catches a launch on guessed facts and a hold that re-dispatches.
6. **One step, one item.** `work launch` runs one role launch for the named work item. A second released work item is not run. After the PRODUCER's success the item waits at VERIFY until the next `work launch`. At ACCEPT the answer is `closure-not-automated`, with no write. Catches automatic next-item selection, automatic continuation and closure automation.
7. **The self-review reaches the VERIFIER.** The PRODUCER's self-review file is recorded against the exact stored candidate. The VERIFIER's package carries it under `producer_self_review`, never in findings. A PRODUCER marker in its output does not reach the VERIFIER. Catches a self-review keyed to another candidate value and a leak of PRODUCER output.
8. **Reused ownership and cleanup.** The worker is started in an owned process group with the allowlisted environment, and its workspace is cleaned up on the existing paths. No publication credential, API key or inherited `ALIENINTENT_*` value is in the worker's environment, apart from the two stated ones and the existing ownership markers `ALIENINTENT_INVOCATION_ID`, `ALIENINTENT_ROLE` and `ALIENINTENT_INVOCATION_OWNER`. Catches an inherited environment and a new cleanup path.
9. **Fitness.** The changed test files pass when run together in one run, which avoids the known import-order failure of `tests/control_plane/test_cli.py` run alone (6c-1 F5); no full suite is run; and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes. An install of the Director host into a temporary target imports and builds its command with plain `python3`, with no `PYTHONPATH`. The Factory Director host's routing and command tests still pass through the moved code.
10. **Real-provider check (must pass before acceptance and closure).** Offline programs prove the wiring, not that the real providers accept the command. The existing tests cover the flags, not a real run. The PRODUCER prepares one script, and the Founder runs it in a separate terminal, because a nested provider call hangs inside Claude Code. The script covers only the routes configured for PRODUCER and VERIFIER in the live routing file. For each, it runs the role through `CliWorkerProvider.run` with the registry composition's command callable and `worker_environment`, on a throwaway local repository (for the VERIFIER, one that holds the feature-regression runner files), with a tiny fixed context package. The packet's handoff states the exact command the Founder runs and where its output is written. When both roles resolve to the same route, it runs once, as PRODUCER, and that evidence also counts for the VERIFIER route; the VERIFIER's verdict format is already covered offline. It shows:
    - the provider starts with the routed model and permission mode, with no flag error;
    - the worker reads its package from the stated path, given only the instruction text;
    - the worker runs its `context_command` and records the read-only profile's answer (a package or a named hold; a crash or a missing configuration fails);
    - the PRODUCER leaves a commit and a self-review file;
    - a separate VERIFIER run, when its route differs, writes `.alienintent/verdict.json` in the existing verdict format;
    - authentication works with the allowlisted environment and no API key.
    The output is kept as evidence and reviewed by the VERIFIER. The VERIFIER cannot ACCEPT, and CLOSURE cannot start, until it passes; a failure is a finding. Catches a command or input form that real providers reject.

## 5. Excluded

- restart continuation of an interrupted launch (a later planned unit);
- closure automation (CLOSURE stays manual);
- automatic selection of the next work item;
- an operating-system sandbox;
- changing the release gate, WIP admission or the 6c-1 holds;
- a new store, record kind or configuration source;
- a real model call in tests (the only real call is the Founder-run real-provider check, acceptance check 10); a real launch of a registered work item is the first self-build assignment;
- changing earlier packets.

## 6. Review record

**Revision 2 (2026-10-03).** The REVIEWER's review of `ede3c85` (FAIL, text only), fixes applied in its wording:
- H1: the moved routing module is standard-library only and installed with the Director host; the command builder stays a method.
- H2: the command is built at `run`, with the workspace, for codex `-C`.
- H3: the test files that exist.
- M1: release-gate refusals are the coordinator's own record, before WIP admission.
- M2: the budget hold is for the PRODUCER, with `prepare` first in `_produce`.
- M3: the refusal is built in composition and keeps its reason as a finding.
- M4: the worktree is a starting place, not a confinement; the shared registry clone refs.
- M5: the permission-mode fact.
- M6: the existing capability hold before a recorded `authorize` decision.
- M7: check 10 runs through `CliWorkerProvider.run`, with a stated command and pass rule.
- REVIEWER recheck of `2e54c7f`: PASS, with two wording points applied (change 3 and change 4).
- L1 to L7: ownership markers; no context-root variable; `launch` answers and order; the prompt position; the dependency's effect on `_eligible`; `published` never raises; tests are run together, not as a full suite.

**Revision 1 (2026-10-03).** First draft, against `main` `a5087d7`, with the Founder's scope. The Founder agreed the design direction (not implementation approval) and accepted: one command per role step; explicit per-packet execution and shutdown limits approved with the packet. Founder corrections folded in: "only the control plane publishes" is a workflow rule, not enforced, and the permission mode is not operating-system isolation (section 2); the existing provider-contract tests are reused, and a Founder-run real-provider check is required (acceptance checks 2 and 10). Further Founder corrections during the first review: the 6c-1 dependency stays explicit, with its landed commit as evidence; the read-back is not claimed to catch unauthorized publishing; check 10 covers only the configured PRODUCER and VERIFIER routes, reuses evidence when both use the same route, and must pass before acceptance and closure.
- Proof: both roles get the correct package and injected model assignment; the PRODUCER starts from the authorized revision; later context calls check the launched contract fingerprint; missing or mismatched facts prevent launch.
- Reuse the existing process ownership and cleanup.
- Restart continuation, closure automation and automatic next-item selection stay in their later planned units.
