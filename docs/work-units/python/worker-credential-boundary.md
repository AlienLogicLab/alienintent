# Work unit: the worker credential boundary

**Label:** `WORKER-CREDENTIAL-BOUNDARY` (a document label; permanent id `7efccee9-13f0-4905-a0a1-e80bc2faa748`).
**Status:** Draft revision 4 (work item `7efccee9-13f0-4905-a0a1-e80bc2faa748`, at CAPTURE) for independent review, 2026-10-04. Not approved, not assessed, not released.
**Position on the path:** the prerequisite for the real protected-main proof of row 8 (AUTOMATED-CLOSURE, check 17). It comes after row 8 lands and before the Founder grants the factory App any landing permission.
**Scope (Founder, 2026-10-04):** a specific credential boundary, not a claim that workers are fully contained. It must fit the existing launcher, with no elaborate new security framework. Its proof must show four things:
- PRODUCER and VERIFIER cannot read the App key;
- they cannot obtain equivalent landing credentials through another file or credential helper;
- CLOSURE (through the deterministic Landing Authority) can obtain the credential it needs;
- the normal worker context and provider login still work.

**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "7efccee9-13f0-4905-a0a1-e80bc2faa748",
 "version": "revision-4",
 "intent": "Establish a specific credential boundary for cognitive sessions: PRODUCER, VERIFIER and CLOSURE sessions run as a separate Unix user through one sudo rule, with a HOME holding only the provider login, so they cannot read the App key or reach any landing credential, while the control plane and deterministic Landing Authority keep the credential, process ownership and stopping still work across users, and the worker context and provider login still work.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-04: keep a clean separation between workers; the arrangement must fit the existing launcher; no elaborate new security framework merely to protect one key.",
  "Founder 2026-10-04: the proof shows PRODUCER and VERIFIER cannot read the App key, cannot obtain equivalent landing credentials through another accessible file or credential helper, CLOSURE can obtain the required credentials (through the deterministic Landing Authority) and land the exact accepted candidate, and the normal worker context and provider login still function.",
  "Founder 2026-10-04: this is a specific credential boundary, not a claim that workers are completely contained.",
  "Founder 2026-10-04: do not grant the App protected-main bypass until this separation proof passes and the Founder explicitly authorizes the permission change."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/invocation_runtime/adapters/process_ownership.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "tools/live/setup_worker_user.sh",
  "tools/live/worker_boundary_check.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_owned_work.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_offline_proof.py"
 ],
 "excluded_scope": [
  "containment beyond the credential boundary",
  "the factory App permission change and the landing flag",
  "the Factory Director's own process",
  "a new store or configuration source beyond the optional worker_user entry",
  "changing earlier packets"
 ],
 "dependencies": [
  "0677f8bb-71c2-4c62-8b4a-d0e5318ba689"
 ],
 "required_capabilities": [
  "python",
  "git",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-5 pass",
  "architecture fitness passes",
  "acceptance check 6 recorded from the Founder-run proof"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file whose first line is exactly ACCEPT or REJECT",
  "Founder-run boundary proof output",
  "landing record on main"
 ],
 "non_goals": [
  "containment",
  "the App permission change"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/automated-closure.md",
  "docs/work-units/python/worker-launch.md"
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
  "scope outside the authorized files",
  "read-only SQLite access by the worker user is impossible without write access to the registry folder"
 ]
}
```

## 0. The whole design (plain English)

Today every cognitive session runs as the Founder's Unix user. That user can read the registry configuration, the App key file it names, and the Founder's `gh` login, git credentials and SSH keys. A token broker or key-holding helper would not change this: anything the control plane can do, a session running as the same user can do too. So the boundary is a different Unix user for the cognitive sessions.

1. **Cognitive sessions run as `alienintent-worker`.** PRODUCER, VERIFIER and CLOSURE sessions are started through one `sudo -n -u alienintent-worker` rule. The rule lets the Founder's user start that user's processes; it never works the other way. The control plane, the coordinator and the deterministic Landing Authority keep running as the Founder's user, so only they can read the key.
2. **The worker user's `HOME` holds only the provider login.** The configured provider's own login file is copied in, as check 10 of unit 6c-2 did. It also holds one `.gitconfig` whose only entries are `safe.directory` for the packets clone and for the launched worktree's or clone's exact path, written when that launch prepares the HOME. It holds no `gh` login, no git credential helper, no SSH key, no registry configuration and no App key.
3. **The worker user gets only the file access its job needs.** It gets write access to its own worktree or clone, read access to what the read-only context command reads, and nothing else in the Founder's `HOME`. In the shared git directory the worker may write only `objects/`, `refs/`, `logs/`, `worktrees/<its id>/` and its own worktree. `config`, `hooks/`, `info/` and `packed-refs` stay writable only by the Founder's user. Every control-plane and Landing Authority git call in a worker-written repository sets `GIT_DIR=<common git directory>/worktrees/<id>`, `GIT_COMMON_DIR=<common git directory>` and `GIT_WORK_TREE=<worktree>` explicitly, from the control plane's own record and never from the worktree's `.git` file or `commondir`. It passes `-c core.hooksPath=/dev/null -c core.fsmonitor=false`. It sets `GIT_NO_REPLACE_OBJECTS=1`. Any call that reaches the remote runs against the common git directory, not in the worktree. The Founder's own git configuration has no `safe.directory` entry that covers the workspace root. `extensions.worktreeConfig` stays unset in the common `config`. The setup gives `alienintent-worker` traverse only (`x`, no read) on each folder from `/home/<founder>` down to the paths it needs, and read on the named install folders of the interpreter and the provider CLI. Every credential file in the Founder's HOME (`~/.git-credentials`, `~/.netrc`, `~/.gitconfig`, `~/.config/gh`, `~/.ssh`, the App key's folder) has no read for others.
4. **Ownership and stopping still work across users.** Today `ProcOwnership.owned_work` reads each process's environment from `/proc/<pid>/environ`, which Linux allows only for the same user, and skips any other user's process (`process_ownership.py`, the `except` around the read). `CliWorkerProvider` stops a worker with `os.killpg`, which Linux refuses across users. So:
   - `owned_work` also finds the worker user's processes by their **session id**, read from `/proc/<pid>/stat` (readable by every user). It matches the session the launcher started (`start_new_session=True`). A worker-user process whose environment cannot be read and whose session cannot be matched is reported, never assumed gone;
   - stopping a worker sends the signal through the same single `sudo` rule (`sudo -n -u alienintent-worker kill -<signal> -- -<pgid>`).
5. **Nothing changes when the worker user is not configured.** The registry configuration gains one optional entry, `worker_user`. Without it, sessions run as today. The real protected-main proof requires it.

This is a credential boundary, not containment. The worker user can still do anything any local user can do.

## 1. The one-time setup (Founder-run, needs root)

`tools/live/setup_worker_user.sh` prints, then runs only after confirmation:
- create the system user `alienintent-worker`, with its own home and no login shell;
- add one sudoers drop-in (`/etc/sudoers.d/alienintent-worker`), checked with `visudo -c`. The drop-in is exactly `<founder> ALL=(alienintent-worker) NOPASSWD: /usr/bin/env, /usr/bin/kill`. It grants nothing to `alienintent-worker` and nothing as root or as the Founder's user. The drop-in sets `Defaults>alienintent-worker !use_pty, !log_output`;
- give `alienintent-worker` access, with POSIX ACLs, to the launch workspace roots (read, write) and to the paths the read-only context command needs (read only), with default ACLs giving both users `rwx` on the workspace root and the writable git paths;
- check that the App key file is not readable and that the registry configuration is readable but holds no secret value.

Nothing else needs root.

## 2. The changes

1. **The worker command as another user** (`invocation_runtime/adapters/cli_worker.py`). With a configured worker user, `run` starts `["sudo", "-n", "-u", <user>, "--", "env", "-i", <the allowlisted variables>, *argv]` with `start_new_session=True`. Without one, today's command is used. Stopping goes through `sudo -n -u <user> kill`. With a configured worker user, `_feature_regressions` starts its runner with the same `sudo -n -u <user> -- env -i <the allowlisted variables>` prefix and stops it through `sudo -n -u <user> kill`. No command from a candidate tree runs as the Founder's user. `_signal`'s per-pid kills for a worker-user pid also go through `sudo -n -u <user> kill`.
2. **Ownership across users** (`invocation_runtime/adapters/process_ownership.py`). With a configured worker user, `owned_work` considers only processes whose real uid (from `/proc/<pid>/status`, readable by every user) is the worker user. Of those, a process whose environment cannot be read is owned if its session id is the launched session. Any other unreadable worker-user process makes the answer None. Other users' processes are skipped as today. `_owned` and `_signal` treat None as owned work still alive. Without one, `owned_work` is unchanged.
3. **The worker HOME** (`composition/work_registry.py`). With `worker_user`, each launch prepares that user's `HOME` with only the routed provider's own login file, and passes it in the allowlisted environment. The HOME is recreated empty at each launch, without following symbolic links.
4. **The configuration** (`composition/work_registry.py`). The optional `worker_user` entry. No other configuration is read.

## 3. Exact permitted files

Production:
- `src/alienintent/invocation_runtime/adapters/cli_worker.py`
- `src/alienintent/invocation_runtime/adapters/process_ownership.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/invocation_runtime/adapters/git_worktree.py`, `src/alienintent/invocation_runtime/adapters/git_source_control.py` (hooks and fsmonitor off on control-plane git calls)
- `tools/live/setup_worker_user.sh` (new)
- `tools/live/worker_boundary_check.py` (new, the real-use proof script)

Tests:
- `tests/invocation_runtime/test_runtime.py`
- `tests/invocation_runtime/test_owned_work.py`
- `tests/composition/test_worker_launch.py`
- `tests/composition/test_offline_proof.py` (only: add `src/alienintent/invocation_runtime/adapters/git_worktree.py` to the frozen-kernel guard's expected changed-file list; nothing else in that test may change)

## 4. Acceptance checks (each names the wrong implementation it catches)

Offline, with a fake `sudo` on the test `PATH` that records its arguments and runs the command as the test's own user:
1. **The worker command goes through the one rule.** With `worker_user`, every PRODUCER and VERIFIER command, and every CLOSURE session command once row 8 has landed, starts with exactly `sudo -n -u <user> -- env -i`, followed by the allowlisted variables only. The control plane's own git calls and the Landing Authority's push never do. Without `worker_user`, commands are unchanged. The VERIFIER's feature-regression runner also starts with that prefix. Catches a session left running as the Founder's user, the candidate's runner left running as the Founder's user, and an Authority moved into the worker user.
2. **Ownership survives an unreadable environment.** A process in the launched session whose environment cannot be read is found by its session id. An unreadable worker-user process outside the launched session gives None, never an empty tuple, so cleanup keeps the workspace and `authorize` is refused. A fake /proc with an unreadable root process gives (), not None. `_owned` returns True when `owned_work` is None. Without `worker_user`, the existing ownership tests pass unchanged. Catches the existing "skip other users" behaviour treated as "nothing is running", a scan that is unknown forever, and `bool(None)` read as quiescent.
3. **Stopping crosses users.** `cancel` and the wall-clock stop go through `sudo -n -u <user> kill`. The recorded fake-sudo calls include each owned pid found by session id. Catches a `killpg` that silently fails.
4. **The worker HOME holds only the provider login.** It lists exactly the routed provider's login file and that `.gitconfig`, whose only key is `safe.directory`. Catches a widened HOME and a credential, `url.*`, `include` or `core.*` entry.
5. **Fitness.** The changed test files pass when run together (no full suite), with the existing check-10 and K2 tests unchanged. `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
6. **Real-use proof (Founder-run, after the setup).** `tools/live/worker_boundary_check.py` records, as `alienintent-worker`:
   - (a) reading the App key file fails. The registry configuration is readable, because the context command loads it. It names the key path, which is not a secret;
   - (b) no `gh` login, git credential helper, SSH key or token variable is reachable, including each named credential file read by its name, an attempt to mint an installation token fails, and `sudo -n -l` as `alienintent-worker` fails;
   - (c) a real provider session starts with only its own login file, and its `context_command` returns a real context package for a registered test work item (this also closes the open proof gap from unit 6c-2's check 10, which showed only a named hold);
   - (d) as the Founder's user, the Landing Authority mints a landing-scoped token and runs its landing path on the exact accepted candidate up to the push. The real push is row 8's check 17;
   - (e) a hook and a `core.fsmonitor` value planted by `alienintent-worker` in the worktree and in the common git directory are refused, or do not run, when the control plane's next git call runs as the Founder's user; and a `worktrees/<id>/commondir` and a worktree `.git` file rewritten by `alienintent-worker` to point at a worker-owned git directory whose `config` sets `credential.helper` and `core.sshCommand`, whose commands do not run when the control plane's next git call runs as the Founder's user;
   - (f) the worker's session id and process group equal the sudo process's pid, and `cancel` leaves no `alienintent-worker` process of that session;
   - (g) the workspace of a finished worker is removed by the normal cleanup.

## 5. Excluded

- containment beyond the credential boundary;
- the factory App's permission change and `"landing": true` (the Founder's actions);
- the Factory Director's own process (it runs no cognitive worker today through this launcher; covering it is later work);
- a new store or configuration source beyond the optional `worker_user` entry.

## 6. Review record

**Revision 4 (2026-10-04).** Narrow scope extension authorized by the Founder after the PRODUCER's stop condition: the frozen-kernel guard (`tests/composition/test_offline_proof.py:213`) correctly detects that `git_worktree.py` changed for this unit's control-plane git hardening. `tests/composition/test_offline_proof.py` is added to the scope solely to add `src/alienintent/invocation_runtime/adapters/git_worktree.py` to that guard's expected changed-file list. Nothing else in that test changes, and the guard's semantics are unchanged. The `git_worktree.py` hardening is kept.

**Revision 3 (2026-10-04).** Recheck of `7380ebd` (FAIL: BLOCKING N1, MATERIAL N2-N3), fixes in its wording:
- N1: control-plane git calls set `GIT_DIR`, `GIT_COMMON_DIR` and `GIT_WORK_TREE` explicitly, never following a worker-writable `.git` file or `commondir`, with replace objects off.
- N2: the uid rule applies only with a configured worker user.
- N3: `safe.directory` names each launched worktree exactly.
- Minor: the worker HOME is recreated empty at each launch.

**Revision 2 (2026-10-04).** REVIEWER of `0c261a7` (FAIL: BLOCKING B1-B6, MATERIAL M1-M6), fixes applied in its wording:
- B1: the VERIFIER's regression runner also runs as the worker user.
- B2: the shared git directory's config, hooks, info and packed-refs stay the Founder's; control-plane git calls run with hooks and fsmonitor off.
- B3: the registry configuration is readable and holds no secret.
- B4: traverse-only access and named install folders.
- B5: a `safe.directory`-only `.gitconfig`.
- B6: ownership by real uid, with None treated as alive.
- M1: no pty.
- M2: per-pid kills through sudo.
- M3: the exact sudoers line.
- M4: default ACLs for cleanup.
- M5: check 6(d) runs the landing path up to the push.
- M6: CLOSURE sessions are covered once row 8 lands.

**Revision 1 (2026-10-04).** First draft, with the Founder's scope: a specific credential boundary, fitted to the existing launcher, with no elaborate security framework, proving that PRODUCER and VERIFIER cannot reach the landing credential while CLOSURE's Landing Authority, the worker context and the provider login still work.
