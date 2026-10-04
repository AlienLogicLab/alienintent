# Work unit: the worker credential boundary

**Label:** `WORKER-CREDENTIAL-BOUNDARY` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-04. Not approved, not assessed, not released.
**Position on the path:** the prerequisite for the real protected-main proof of row 8 (AUTOMATED-CLOSURE, check 17). It comes after row 8 lands and before the Founder grants the factory App any landing permission.
**Scope (Founder, 2026-10-04):** a specific credential boundary, not a claim that workers are fully contained. It must fit the existing launcher, with no elaborate new security framework. Its proof must show four things:
- PRODUCER and VERIFIER cannot read the App key;
- they cannot obtain equivalent landing credentials through another file or credential helper;
- CLOSURE (through the deterministic Landing Authority) can obtain the credential it needs;
- the normal worker context and provider login still work.

**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

Today every cognitive session runs as the Founder's Unix user. That user can read the registry configuration, the App key file it names, and the Founder's `gh` login, git credentials and SSH keys. A token broker or key-holding helper would not change this: anything the control plane can do, a session running as the same user can do too. So the boundary is a different Unix user for the cognitive sessions.

1. **Cognitive sessions run as `alienintent-worker`.** PRODUCER, VERIFIER and CLOSURE sessions are started through one `sudo -n -u alienintent-worker` rule. The rule lets the Founder's user start that user's processes; it never works the other way. The control plane, the coordinator and the deterministic Landing Authority keep running as the Founder's user, so only they can read the key.
2. **The worker user's `HOME` holds only the provider login.** The configured provider's own login file is copied in, as check 10 of unit 6c-2 did. It holds no `gh` login, no git credential helper, no SSH key, no registry configuration and no App key.
3. **The worker user gets only the file access its job needs.** It gets write access to its own worktree or clone, read access to what the read-only context command reads, and nothing in the Founder's `HOME`. The Founder's `HOME` stays mode 750 and `.config` and `.ssh` mode 700.
4. **Ownership and stopping still work across users.** Today `ProcOwnership.owned_work` reads each process's environment from `/proc/<pid>/environ`, which Linux allows only for the same user, and skips any other user's process (`process_ownership.py`, the `except` around the read). `CliWorkerProvider` stops a worker with `os.killpg`, which Linux refuses across users. So:
   - `owned_work` also finds the worker user's processes by their **session id**, read from `/proc/<pid>/stat` (readable by every user). It matches the session the launcher started (`start_new_session=True`). A process whose environment cannot be read and whose session cannot be matched is reported, never assumed gone;
   - stopping a worker sends the signal through the same single `sudo` rule (`sudo -n -u alienintent-worker kill -<signal> -- -<pgid>`).
5. **Nothing changes when the worker user is not configured.** The registry configuration gains one optional entry, `worker_user`. Without it, sessions run as today. The real protected-main proof requires it.

This is a credential boundary, not containment. The worker user can still do anything any local user can do.

## 1. The one-time setup (Founder-run, needs root)

`tools/live/setup_worker_user.sh` prints, then runs only after confirmation:
- create the system user `alienintent-worker`, with its own home and no login shell;
- add one sudoers drop-in (`/etc/sudoers.d/alienintent-worker`), checked with `visudo -c`: the Founder's user may run, as `alienintent-worker` and without a password, only the launcher's worker command and `kill`;
- give `alienintent-worker` access, with POSIX ACLs, to the launch workspace roots (read, write) and to the paths the read-only context command needs (read only);
- check that the App key file and the registry configuration are not readable by `alienintent-worker`.

Nothing else needs root.

## 2. The changes

1. **The worker command as another user** (`invocation_runtime/adapters/cli_worker.py`). With a configured worker user, `run` starts `["sudo", "-n", "-u", <user>, "--", "env", "-i", <the allowlisted variables>, *argv]` with `start_new_session=True`. Without one, today's command is used. Stopping goes through `sudo -n -u <user> kill`.
2. **Ownership across users** (`invocation_runtime/adapters/process_ownership.py`). `owned_work` also matches by session id when the environment cannot be read. An unreadable process that cannot be matched makes the answer None (unknown), never an empty tuple.
3. **The worker HOME** (`composition/work_registry.py`). With `worker_user`, each launch prepares that user's `HOME` with only the routed provider's own login file, and passes it in the allowlisted environment.
4. **The configuration** (`composition/work_registry.py`). The optional `worker_user` entry. No other configuration is read.

## 3. Exact permitted files

Production:
- `src/alienintent/invocation_runtime/adapters/cli_worker.py`
- `src/alienintent/invocation_runtime/adapters/process_ownership.py`
- `src/alienintent/composition/work_registry.py`
- `tools/live/setup_worker_user.sh` (new)
- `tools/live/worker_boundary_check.py` (new, the real-use proof script)

Tests:
- `tests/invocation_runtime/test_runtime.py`
- `tests/invocation_runtime/test_owned_work.py`
- `tests/composition/test_worker_launch.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

Offline, with a fake `sudo` on the test `PATH` that records its arguments and runs the command as the test's own user:
1. **The worker command goes through the one rule.** With `worker_user`, every PRODUCER, VERIFIER and CLOSURE command starts with exactly `sudo -n -u <user> -- env -i`, followed by the allowlisted variables only. The control plane's own git calls and the Landing Authority's push never do. Without `worker_user`, commands are unchanged. Catches a session left running as the Founder's user, and an Authority moved into the worker user.
2. **Ownership survives an unreadable environment.** A process in the launched session whose environment cannot be read is found by its session id. An unreadable process that matches nothing gives None, never an empty tuple, so cleanup keeps the workspace and `authorize` is refused. Catches the existing "skip other users" behaviour treated as "nothing is running".
3. **Stopping crosses users.** `cancel` and the wall-clock stop go through `sudo -n -u <user> kill`. Catches a `killpg` that silently fails.
4. **The worker HOME holds only the provider login.** It lists exactly the routed provider's login file. It holds no `gh`, git, SSH or registry file. Catches a widened HOME.
5. **Fitness.** The changed test files pass when run together (no full suite), with the existing check-10 and K2 tests unchanged. `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
6. **Real-use proof (Founder-run, after the setup).** `tools/live/worker_boundary_check.py` records, as `alienintent-worker`:
   - (a) reading the App key file fails, and so does reading the registry configuration;
   - (b) no `gh` login, git credential helper, SSH key or token variable is reachable, and an attempt to mint an installation token fails;
   - (c) a real provider session starts with only its own login file, and its `context_command` returns a real context package for a registered test work item (this also closes the open proof gap from unit 6c-2's check 10, which showed only a named hold);
   - (d) as the Founder's user, the Landing Authority's credentials mint a landing-scoped token in a dry run that pushes nothing.

## 5. Excluded

- containment beyond the credential boundary;
- the factory App's permission change and `"landing": true` (the Founder's actions);
- the Factory Director's own process (it runs no cognitive worker today through this launcher; covering it is later work);
- a new store or configuration source beyond the optional `worker_user` entry.

## 6. Review record

**Revision 1 (2026-10-04).** First draft, with the Founder's scope: a specific credential boundary, fitted to the existing launcher, with no elaborate security framework, proving that PRODUCER and VERIFIER cannot reach the landing credential while CLOSURE's Landing Authority, the worker context and the provider login still work.
