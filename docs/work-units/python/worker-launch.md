# Work unit: worker launch for a registered work item

**Label:** `WORKER-LAUNCH` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6c-2, the second of the two units the Founder split unit 6c into on 2026-10-03. 6c-1 (`main` `a5087d7`) assembles each role's context package; this unit launches the PRODUCER and the VERIFIER with it. Builds on units 6a, 6b and 6c-1.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

Today nothing launches a real PRODUCER or VERIFIER for a registered work item. `WorkRegistry.coordinator(worker, artifacts)` (unit 6b) exists, but only tests give it a worker. The existing worker classes have three gaps for this use:
- the PRODUCER's workspace always starts at `HEAD`, not at the release record's starting revision (`real_worker.py` line 295);
- the worker command is one fixed command line, so no model is chosen per role, and the routing file's permission mode is checked but never used (`cli_worker.py`);
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
- writes the explicit human release as `release_and_start` does today;
- runs the existing `_recover` once;
- runs the existing `_run` once for that work item only, and only if `_eligible` admits it.

It returns the same `RunSummary` shape. It does not call `start()`, so no other released work item runs. A work item at the CLOSURE stage answers `closure-not-automated` without any write. One that is not eligible answers `not-eligible`, also without any write. `release_and_start` and `start()` are unchanged.

**2. The registry launch composition** (`composition/work_registry.py`), `WorkRegistry.launcher()`, follows the existing `SandboxRunProfile` chain (`composition/sandbox_run_profile.py` lines 304-332):
- `CliWorkerProvider` with the `worker_environment` allowlist, plus `ALIENINTENT_PROJECT_CONFIGURATION`, `ALIENINTENT_PROJECT` and `ALIENINTENT_CONTEXT_ROOT`;
- `RealWorkerProvider` with the pointer repository's clone, the invocation journal, `GitWorktreeAdapter` and `ProcOwnership`, and one grant per dispatch;
- `RoleBindingGuard`;
- `WorkRegistry.coordinator(worker, artifacts)`.

Its state (journal, workspaces, verifier clones, context root) lives under the existing registry folder, in `launch/`. No new configuration is read.

**3. One preparation hook on `RealWorkerProvider`** (`invocation_runtime/application/real_worker.py`). It follows the existing style of the `branch` and `grant` hooks: an optional `preparation` object with two calls.
- `prepare(invocation, clone)` is called at the start of the PRODUCER and VERIFIER paths, before any workspace is made or process started. For the VERIFIER it is called right after the fresh candidate clone is made, with that clone. It returns either the starting revision and the role's command, or a refusal.
- A refusal becomes a journaled `WorkerOutcome.authority_block(...)` whose escalation names the hold reason and field. Nothing is started.
- The PRODUCER worktree is allocated at the returned starting revision instead of `"HEAD"`.
- `published(invocation, candidate)` is called after a PRODUCER candidate is published and read back.

Without a `preparation`, behaviour is unchanged.

**4. A per-invocation command on `CliWorkerProvider`** (`invocation_runtime/adapters/cli_worker.py`). The worker command may be a callable of `(invocation_id, role)`, evaluated at `run`, as `branch` and `grant` already are on `RealWorkerProvider`. It returns the command line and the text for the worker's standard input; the Director host passes its prompt the same way, on standard input. A fixed tuple keeps today's behaviour, with standard input unchanged. The registry composition passes a callable that returns what `prepare` built for that invocation.

**5. The registry preparation** (`composition/work_registry.py`) implements the hook. For one invocation, `prepare`:
1. Checks the contract's `budget_policy` states `hard_wall_clock_seconds` and `cancellation_limit`. Otherwise it refuses with `MISSING_RECORD` naming `budget_policy`; today `RealWorkerProvider` would answer `ineligible` instead.
2. Calls `WorkContext.assemble(identity, role, invocation.correlation_id, invocation.contract_digest, candidate, clone)`. A `ContextHold` is a refusal naming its reason and fields.
3. Reads the role's route from `model-routing.json` through the existing reader (change 6). An unreadable file or `MODEL_ROUTING_INVALID` refuses with `model-routing-unavailable`.
4. Writes the package as JSON to `<context root>/<invocation id>.json`, outside any worktree.
5. Builds the role's command from the route with the moved provider command builder (change 6), and one fixed instruction text for the role, given on standard input. The text tells the worker where its package is, to do only what the package states, how to call `context_command`, and where to write its result: the PRODUCER commits in its worktree and writes its self-review to `<context root>/<invocation id>.self-review.md`; the VERIFIER writes `.alienintent/verdict.json` in the existing verdict format.
6. Returns the package's `starting_revision` and the command.

`published` reads the self-review file and calls `record_self_review(identity, candidate, text)` with the published, read-back candidate. If the file is missing or empty, nothing is recorded, and the VERIFIER's launch is later held `MISSING_RECORD` (6c-1 step 8).

**6. One routing reader and one provider command builder.** The existing Python reader `tools/orchestration/model_routing.py` (`routing_path`, `resolve_route`) moves unchanged to `src/alienintent/composition/model_routing.py`, because the architecture check allows configuration reads only in composition. The existing provider command builder, `ProcessDirectorLauncher.command` in `tools/orchestration/factory_director_host.py` (lines 203-209: claude `-p --no-session-persistence --output-format json --permission-mode <mode> --model <model>`; codex `exec --ephemeral --json --sandbox <mode> -C <workdir> --model <model> -`), moves to the same module as `provider_command(route, workdir)`. The Director host calls it there, and `tools/orchestration/model_routing.py` re-exports the reader, so the host keeps working unchanged. The schema, the error and the `ALIENINTENT_MODEL_ROUTING` override are unchanged.

**7. The launched fingerprint on later context calls** (6c-1 follow-up F1). `ContextCommand` (`context_assembly/application/work_context.py`) adds `--contract-digest <digest>` when assembly was given one. `work context` accepts `--contract-digest` and passes it to `assemble`, which already compares it (6c-1 step 5).

## 2. Access restrictions (what is enforced, and what is not)

Enforced by existing code:
- the worker's environment is the stated allowlist, not the inherited one, so no API key, publication token or `GIT_CONFIG_*` credential in the operator's environment is passed on;
- each PRODUCER has its own worktree, and each VERIFIER a fresh clone;
- the worker's process group is owned, stopped at its wall clock and cleaned up through the existing ownership and cleanup.

Workflow rules, not enforced:
- **Only the control plane publishes.** This is a workflow rule. The allowlist keeps `HOME`, and the worker runs as the same user, so it can still reach that user's files: provider logins, `gh` and git credentials, SSH keys and the registry's GitHub App key. No existing credential restriction stops a worker pushing. The instruction text states the rule, and the release record and the VERIFIER's independent read-back of the exact candidate detect a candidate that did not come through the control plane; nothing prevents the attempt.
- **The permission mode** from the routing file is now passed to the provider (today it is dropped). It is the provider's own setting, not operating-system isolation. The live modes (`danger-full-access`, `bypassPermissions`) let a worker write wherever its user can.

No operating-system sandbox exists in Python, and none is claimed. This is the limit the Founder accepted in 6c-1. Changing it is separate work.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/application/factory_coordinator.py` (`launch`)
- `src/alienintent/composition/work_registry.py` (launcher and preparation)
- `src/alienintent/composition/model_routing.py` (new, moved reader)
- `tools/orchestration/model_routing.py` (re-export), `tools/orchestration/factory_director_host.py` (call the moved command builder)
- `tools/live/worker_launch_provider_check.py` (new, the real-provider check script)
- `src/alienintent/invocation_runtime/application/real_worker.py` (preparation hook, starting revision)
- `src/alienintent/invocation_runtime/adapters/cli_worker.py` (per-invocation command)
- `src/alienintent/context_assembly/application/work_context.py` (`--contract-digest` in `context_command`)
- `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py` (`work launch`, `work context --contract-digest`)

Tests:
- `tests/composition/test_worker_launch.py` (new)
- `tests/composition/test_work_registry.py`
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/invocation_runtime/test_real_worker.py`, `tests/invocation_runtime/test_cli_worker.py` (or the existing files that test these classes)
- `tests/context_assembly/test_work_context.py`
- `tests/control_plane/test_cli.py`
- `tools/orchestration/test_model_routing.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The worker executables come from a test routing file and are fake scripts that record what they receive. No model is called.

1. **Each role receives the correct package.** A launched PRODUCER and a launched VERIFIER each find, at their stated path, exactly the package `assemble` gives for that work item, role and attempt. The VERIFIER's comes from its fresh candidate clone and includes its diff and the labelled self-review. Catches a missing, wrong-role or stale package.
2. **The injected model assignment, through the existing provider contract.** Each role's command is the existing provider command for the route chosen for that role at launch time: for claude exactly the flags of `src/providers/claude.mjs` and of the Director host, and for codex exactly those of `src/providers/codex.mjs` and of the Director host. The instruction text arrives on standard input. Changing the routing file between two launches changes the next command. The existing provider-contract tests are reused unchanged and still pass: `tools/orchestration/test_factory_director_host.py` and `test/worker-runner.test.mjs`. Catches a fixed command, a cached route, a dropped permission mode and a command that drifts from the provider contract.
3. **The PRODUCER starts from the authorized revision.** The PRODUCER's worktree is at the release record's baseline. A commit added on top of the default branch afterwards is not in it. Catches a launch at `HEAD`.
4. **Later context calls check the launched fingerprint.** The worker running its own `context_command` gets its package. The same call with another contract digest is held `DIGEST_MISMATCH`. Catches a command without the digest and a digest that is not compared.
5. **Missing or mismatched facts prevent launch.** Each case below gives a journaled authority block naming the reason. No worker process is started, the work item keeps its WIP slot, and a further `work launch` does not loop:
   - no release record;
   - a release record whose evidence no longer matches the work item;
   - a context hold, for example no READY assessment of the current pointer;
   - a missing budget field;
   - a missing routing file, invalid routing, or a role with no usable route;
   - for the VERIFIER, no self-review.
   Catches a launch on guessed facts and a hold that re-dispatches.
6. **One step, one item.** `work launch` runs one role launch for the named work item. A second released work item is not run. After the PRODUCER's success the item waits at VERIFY until the next `work launch`. At ACCEPT the answer is `closure-not-automated`, with no write. Catches automatic next-item selection, automatic continuation and closure automation.
7. **The self-review reaches the VERIFIER.** The PRODUCER's self-review file is recorded against the exact stored candidate. The VERIFIER's package carries it under `producer_self_review`, never in findings. A PRODUCER marker in its output does not reach the VERIFIER. Catches a self-review keyed to another candidate value and a leak of PRODUCER output.
8. **Reused ownership and cleanup.** The worker is started in an owned process group with the allowlisted environment, and its workspace is cleaned up on the existing paths. No publication credential, API key or inherited `ALIENINTENT_*` value is in the worker's environment, apart from the three stated ones. Catches an inherited environment and a new cleanup path.
9. **Fitness.** The changed test files and `tools/fitness/check_architecture.py --root src/alienintent --check all` pass. The Factory Director host's routing and command tests still pass through the moved code.
10. **Real-provider check (before worker launch is called operational).** Offline programs prove the wiring, not that the real providers accept the command. The existing tests cover the flags, not a real run. The PRODUCER prepares one script, and the Founder runs it in a separate terminal, because a nested provider call hangs inside Claude Code. For each provider in the live routing file, once as PRODUCER and once as VERIFIER, it runs the exact launch command on a throwaway local repository, with a tiny fixed context package and the allowlisted environment. It shows:
    - the provider starts with the routed model and permission mode, with no flag error;
    - the worker reads its package from the stated path, given only the instruction text on standard input;
    - the worker runs its `context_command` and gets an answer;
    - the PRODUCER leaves a commit and a self-review file;
    - the VERIFIER writes `.alienintent/verdict.json` in the existing verdict format;
    - authentication works with the allowlisted environment and no API key.
    The output is kept as evidence. The VERIFIER reviews it, and a failure is a finding. Until it passes, worker launch is wired but not operational. Catches a command or input form that real providers reject.

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

**Revision 1 (2026-10-03).** First draft, against `main` `a5087d7`, with the Founder's scope. The Founder agreed the design direction (not implementation approval) and accepted: one command per role step; explicit per-packet execution and shutdown limits approved with the packet. Founder corrections folded in: "only the control plane publishes" is a workflow rule, not enforced, and the permission mode is not operating-system isolation (section 2); the existing provider-contract tests are reused, and a Founder-run real-provider check is required before worker launch is called operational (acceptance checks 2 and 10).
- Proof: both roles get the correct package and injected model assignment; the PRODUCER starts from the authorized revision; later context calls check the launched contract fingerprint; missing or mismatched facts prevent launch.
- Reuse the existing process ownership and cleanup.
- Restart continuation, closure automation and automatic next-item selection stay in their later planned units.
