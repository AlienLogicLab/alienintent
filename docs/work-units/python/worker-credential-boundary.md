# Work unit: the worker credential boundary

**Label:** `WORKER-CREDENTIAL-BOUNDARY` (a document label; permanent id `7efccee9-13f0-4905-a0a1-e80bc2faa748`).
**Status:** Draft revision 6 (work item `7efccee9-13f0-4905-a0a1-e80bc2faa748`, at CAPTURE) for independent review, 2026-10-04. Not approved, not assessed, not released.
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
 "version": "revision-6",
 "intent": "Make the worker credential and authority boundary structural: cognitive sessions run as a separate Unix user in their own worker-owned clones; no repository that can influence control-plane authority, release admission, verification custody or landing is writable by a cognitive worker; candidates are handed over by exact object identity through a bundle imported into a control-plane-owned intake repository; worker-owned repositories are never consumed as authority; process ownership and stopping work across users; the worker context and provider login still work.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-04: keep a clean separation between workers; the arrangement must fit the existing launcher; no elaborate new security framework merely to protect one key.",
  "Founder 2026-10-04: the proof shows PRODUCER and VERIFIER cannot read the App key, cannot obtain equivalent landing credentials through another accessible file or credential helper, CLOSURE can obtain the required credentials (through the deterministic Landing Authority) and land the exact accepted candidate, and the normal worker context and provider login still function.",
  "Founder 2026-10-04: this is a specific credential boundary, not a claim that workers are completely contained.",
  "Founder 2026-10-04: do not grant the App protected-main bypass until this separation proof passes and the Founder explicitly authorizes the permission change.",
  "Founder 2026-10-04 (decision B, structural): no repository that can influence control-plane authority, release admission, verification custody or landing may be writable by a cognitive worker; each cognitive role gets its own disposable worker-owned clone; the packets and release repository stay control-plane-owned; the candidate is handed over by exact object identity and imported into a trusted repository before any privileged use; worker refs, HEAD, config, alternates, .git files, commondir and replace refs never take part; the control plane never runs privileged git inside a worker copy."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/invocation_runtime/adapters/process_ownership.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/composition/work_registry.py",
  "tools/live/setup_worker_user.sh",
  "tools/live/worker_boundary_check.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_owned_work.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/invocation_runtime/test_real_worker_outcome.py",
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
  "acceptance checks 1-7 pass",
  "architecture fitness passes",
  "acceptance check 8 recorded from the Founder-run proof"
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
  "a privileged path needs a file outside the authorized scope"
 ]
}
```

## 0. The whole design (plain English)

Today every cognitive session runs as the Founder's Unix user, and its workspace is a linked worktree of the Founder's packets clone. So a session can read the App key, and it can write git metadata that the Founder's own git later reads. Two review rounds showed the second problem cannot be closed one command at a time: whenever a worker can write a repository that privileged code reads, there is another path.

Revision 5 makes the boundary **structural**. One invariant (Founder, 2026-10-04):

> No repository that can influence control-plane authority, release admission, verification custody or landing may be writable by a cognitive worker.

It has two halves, and the proof checks both:
- **Worker-owned repositories are never consumed as authority by privileged code.** The control plane, the Landing Authority and the Founder's user run no git command inside a worker-owned repository, and never read a worker repository's refs, config, `HEAD`, `.git` file, `commondir`, alternates or replace refs.
- **Control-plane-owned repositories are not writable by workers.** The packets clone, the intake repository, the landing clones, and every repository the release gate, the context reader and the landing read stay writable only by the Founder's user.

### 0.1 Who owns what

| Thing | Owner (writable by) | Used by |
|---|---|---|
| The packets clone (pointers, baselines, `main`, dependency truth) | Founder's user only | the control plane; workers may **read** it |
| The intake repository `<launch>/intake.git` (bare) | Founder's user only | candidate custody, publication, `git diff` |
| Landing clones `<launch>/landing/landing-<c>` (moved from `<launch>/verifier/landing-<c>` by change 5) | Founder's user only | the Landing Authority |
| `<launch>/verifier` (publication read-back clones), `<launch>/context`, `<launch>/custody`, `<launch>/artifacts`, `<launch>/workspaces`, `<launch>/intake-bundles`, the invocation journal | Founder's user only | the control plane |
| PRODUCER, VERIFIER, CLOSURE workspaces `<launch>/worker/<role>-<c>` | `alienintent-worker` only | that one session |
| The candidate hand-over file `<launch>/handoff/<c>.bundle` | written by the worker, then read by the control plane as **data** | candidate import |

### 0.2 Sessions as `alienintent-worker`

PRODUCER, VERIFIER and CLOSURE sessions, and every command that runs on their behalf (the VERIFIER's feature-regression runner, the workspace creation, the bundle creation, the removal of their workspaces), run through one sudo rule: `sudo -n -u alienintent-worker -- env -i <the allowlisted variables> <command>`. The control plane, the coordinator and the Landing Authority keep running as the Founder's user.

### 0.3 The PRODUCER workspace

The worker creates its own clone, as the worker: `git clone --no-hardlinks <packets clone> <launch>/worker/producer-<c>` (reading the Founder-owned packets clone is harmless to the Founder), then checks out the release record's starting revision by its full SHA. The workspace is owned by `alienintent-worker`. The Founder's git never runs in it.

### 0.4 Candidate hand-over by exact object identity

When the PRODUCER session ends, the control plane learns the candidate SHA it claims (from `git rev-parse --verify HEAD^{commit}` run as the worker through the sudo rule in its workspace; the output is data and must be 40 hex characters; `GitSourceControl.revision` is not called with a worker user) and asks the worker, through the sudo rule, to run `git update-ref refs/alienintent/handoff <claimed SHA>` and then `git bundle create <launch>/handoff/<c>.bundle refs/alienintent/handoff`, and nothing else (the ref name is ignored at import). Then the deterministic import, as the Founder, uses only trusted facts:
0. as the Founder, copy `<launch>/handoff/<c>.bundle` into `<launch>/intake-bundles/<c>.bundle` (Founder-owned, mode 0700), opening the source with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC`, then refusing, by `fstat` on that open descriptor (never a path `stat` or `lstat`), anything but a regular file owned by `alienintent-worker`, and copying only from that descriptor; steps 1 and 2 use only that copy, by absolute path, with the working directory set to `<launch>/intake.git`.
1. `GIT_DIR=<launch>/intake.git git bundle verify <bundle>`;
2. `GIT_DIR=<launch>/intake.git git fetch <bundle> <claimed SHA>:refs/intake/<c>`, with hooks and fsmonitor off, `GIT_NO_REPLACE_OBJECTS=1`, `-c transfer.fsckObjects=true`, and transfer limited to the bundle file;
3. `rev-parse refs/intake/<c>` equals the claimed SHA exactly, and the commit's ancestry contains the starting revision;
4. custody facts (tree, parents) are read in the intake repository;
5. publication pushes `refs/intake/<c>` from the intake repository to the candidate branch on the remote (as today, with the existing read-back), so the exact object is durably retrievable;
6. from then on only the intake repository and the remote copy are used.

The control plane creates the intake repository with `git init --bare` if it is missing, and pushes to the packets remote's URL read from the packets clone's config (Founder-owned); it never reads a remote from a worker repository.

No worker branch name, `HEAD`, config, alternate object store, `.git` file, `commondir` or replace ref takes part. The bundle's own ref names are ignored: only the claimed SHA is fetched, and only if it matches.

### 0.5 The VERIFIER and CLOSURE workspaces

Each is a fresh worker-owned clone, created as the worker from the intake repository (read only), by `git init` and `git fetch <launch>/intake.git refs/intake/<c>`, then `git checkout --detach <SHA>`. Before the VERIFIER starts, the control plane keeps its `ls-remote` equality check of the candidate branch, so the custody claim is unchanged. The control plane never runs git inside it. Every worker-written result (self-review, verdict, feature-regression receipt, CLOSURE request) is written under `<launch>/results/<c>/`; the control plane opens each with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC`, refuses, by `fstat` on that open descriptor (never a path `stat` or `lstat`), anything but a regular file owned by `alienintent-worker`, reads only from that descriptor, and treats the bytes as data. The worker creates `<launch>/results/<c>/` with mode 0755 and its files with mode 0644. The VERIFIER package's `diff` is computed in the intake repository (`git diff <starting revision> <candidate SHA>`, both full SHAs).

### 0.6 Cleanup and ownership

Worker workspaces are removed through the sudo rule (`rm -rf` as the worker) only after the existing ownership checks, which now find worker processes by real uid and session id (`/proc/<pid>/status` and `/proc/<pid>/stat`). An unreadable worker-user process outside the launched session gives None, which counts as alive. Stopping goes through `sudo -n -u alienintent-worker kill`. The Founder's git does not run `git status` or `git worktree remove` in worker workspaces any more.

### 0.7 Nothing changes without a worker user

The registry configuration gains one optional entry, `worker_user`. Without it, launches behave exactly as today, worktrees included. The real protected-main proof requires it.

This is a credential and authority boundary, not containment. A worker can still do anything any local user can do. It proves nothing about the Factory Director, and it is not the protected-main landing authorization.

## 1. The one-time setup (Founder-run, needs root)

`tools/live/setup_worker_user.sh` prints every action, then runs only after the Founder types `yes`:
- create the system user `alienintent-worker` (home `/var/lib/alienintent-worker`, no login shell);
- write `/etc/sudoers.d/alienintent-worker`, mode 0440, checked with `visudo -c`, exactly: `Defaults>alienintent-worker !use_pty, !log_output` and `<founder> ALL=(alienintent-worker) NOPASSWD: /usr/bin/env, /usr/bin/kill`. It grants nothing to `alienintent-worker`, and nothing as root or as the Founder;
- create `<launch>/worker`, `<launch>/results` and `<launch>/handoff` owned by `alienintent-worker`, mode 0711; create `<launch>/intake.git`, `<launch>/intake-bundles` and `<launch>/landing` owned by the Founder, mode 0700;
- give `alienintent-worker` **read and traverse only** (access and default ACL `r-X`) on the packets clone, the intake repository `<launch>/intake.git`, traverse only (access ACL `--x`, no default ACL) on `<launch>`, the context command's read paths (the work and readiness databases and their folders, and the evidence root), the registry configuration, and the named install folders of the interpreter and the provider CLI; traverse only on the folders from `/home/<founder>` down to them;
- remove any write ACL or default ACL for `alienintent-worker` on every control-plane-owned path;
- remove read for others from the Founder's credential files (`~/.git-credentials`, `~/.netrc`, `~/.gitconfig`, `~/.config/gh`, `~/.ssh`, the App key's folder);
- final checks, as the worker: the App key is unreadable; the registry configuration is readable and holds no secret value; no control-plane-owned repository, no folder or file inside one, and no parent folder of one, is writable by `alienintent-worker`, owned by it, or carries an ACL entry for it beyond read and traverse.

## 2. The changes

1. **Worker commands** (`invocation_runtime/adapters/cli_worker.py`): with a worker user, every session command and the VERIFIER's feature-regression runner start with the sudo prefix; stopping and per-pid kills go through `sudo -n -u <user> kill` (with no `env -i`). The allowlist names `PATH=/usr/bin:/bin`. The regression runner's `--base` is the release record's starting revision (full SHA) given by the control plane; `git merge-base HEAD origin/main` is no longer run.
2. **Ownership across users** (`invocation_runtime/adapters/process_ownership.py`): with a worker user, ownership by real uid and session id, with None for an unreadable worker-user process outside the session; `_owned` and `_signal` treat None as alive. Without one, unchanged.
3. **Worker workspaces and candidate import** (`invocation_runtime/adapters/git_source_control.py`, `invocation_runtime/adapters/git_worktree.py`): a worker-run clone for each role; the worker-run `git bundle create`; the control-plane import of 0.4 into the intake repository; publication from the intake repository; VERIFIER and CLOSURE clones made by the worker; workspace removal through sudo. Without a worker user, the existing worktree path is unchanged.
4. **The worker role paths** (`invocation_runtime/application/real_worker.py`): `_produce`, `_evaluate` and `_close` use change 3 when a worker user is configured; the candidate comes only from the intake import.
5. **The registry** (`composition/work_registry.py`): the optional `worker_user` entry; the worker HOME (recreated empty each launch, holding only the routed provider's login file and a `.gitconfig` whose only entries are `safe.directory` for the packets clone and the intake repository); the VERIFIER `diff` from the intake repository; the landing clone moves to `<launch>/landing/landing-<c>`; `_producer_worktree` recovery names `<launch>/worker/producer-<c>`.

## 3. Exact permitted files

Production:
- `src/alienintent/invocation_runtime/adapters/cli_worker.py`
- `src/alienintent/invocation_runtime/adapters/process_ownership.py`
- `src/alienintent/invocation_runtime/adapters/git_source_control.py`
- `src/alienintent/invocation_runtime/adapters/git_worktree.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/composition/work_registry.py`
- `tools/live/setup_worker_user.sh` (new)
- `tools/live/worker_boundary_check.py` (new)

Tests:
- `tests/invocation_runtime/test_runtime.py`
- `tests/invocation_runtime/test_owned_work.py`
- `tests/invocation_runtime/test_git_source_control.py`
- `tests/invocation_runtime/test_real_worker_outcome.py`
- `tests/composition/test_worker_launch.py`
- `tests/composition/test_offline_proof.py` (only: add `src/alienintent/invocation_runtime/adapters/git_worktree.py` to the frozen-kernel guard's expected changed-file list; nothing else in that test may change)

## 4. Acceptance checks (each names the wrong implementation it catches)

Offline, with a fake `sudo` on the test `PATH` that records its arguments and runs the command as the test's own user, and a fake `/proc` where needed:
1. **No privileged git in a worker repository.** With a worker user, every git command run by the control plane or the Landing Authority is recorded with its working directory and `GIT_DIR`. None of them is inside `<launch>/worker/` or `<launch>/handoff/` other than reading the bundle file as data. Catches a privileged command that touches a worker repository.
2. **No worker write to control-plane repositories.** The setup script's plan grants `alienintent-worker` no write and no default ACL on the packets clone, the intake repository, the landing folder or any parent of them. Its final checks assert it. The plan gives `<launch>/worker`, `<launch>/results` and `<launch>/handoff` mode 0711, and the worker read and traverse on the intake repository. Catches a shared mutable authority surface and a layout in which the hand-over cannot work across users.
3. **Exact-identity hand-over.** The import fetches only the claimed SHA from the bundle, refuses when the imported commit differs from the claim, ignores the bundle's ref names, and refuses a bundle whose prerequisite or content fails `bundle verify`. A worker repository with a planted `refs/heads/main`, `refs/replace/*`, `objects/info/alternates`, `.git` file, `commondir` and `config` does not change the imported candidate or any control-plane result. A bundle path replaced by a directory or a symlink after `bundle verify` is refused, and no control-plane git command has a path under `<launch>/worker/` or `<launch>/handoff/` as an argument. Catches trust in worker refs or metadata.
4. **Every worker-side command goes through the one rule.** Session commands, the regression runner, workspace creation, bundle creation and workspace removal start with exactly `sudo -n -u <user> -- env -i` and the allowlisted variables. Without a worker user, commands and the worktree path are unchanged. Catches a worker command left as the Founder.
5. **Ownership and stopping across users.** A fake `/proc` with an unreadable root process gives (), not None; an unreadable worker-user process outside the session gives None; `_owned` returns True on None; kills go through sudo, including each owned pid. Catches "nothing is running" read from unreadable processes.
6b. **Results are never read through a worker-chosen path.** A self-review, verdict, receipt or CLOSURE request that is a symlink is refused and its target is never read. A FIFO, or a `<c>` folder swapped for a symlink to a Founder-owned folder, is refused without blocking and without reading a Founder-owned file. Catches a privileged read through a worker-chosen path.
6. **The worker HOME** holds exactly the provider login file and the `safe.directory`-only `.gitconfig`, recreated empty each launch. Catches a widened HOME.
7. **Fitness.** The changed test files pass when run together (no full suite), with `tests/composition/test_landing_authority.py`, `tests/composition/test_sandbox_run_profile.py`, `tests/execution_coordination/test_role_orchestration.py` and `tests/context_assembly/test_work_context.py` unchanged; `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
8. **Real-use proof (Founder-run, after the setup).** `tools/live/worker_boundary_check.py` records:
   - (a) as the worker, reading the App key fails; the registry configuration is readable and holds no secret;
   - (b) as the worker, no `gh` login, git credential helper, SSH key or token variable is reachable, each named credential file is unreadable, an installation-token mint fails, and `sudo -n -l` fails;
   - (c) a real provider session as the worker starts with only its login file, and its `context_command` returns a real context package for a genuinely registered and approved work item. If none exists, 6(c) is recorded as unresolved and the proof does not pass;
   - (d) as the Founder, the Landing Authority mints a landing-scoped token (partial: the landing path itself waits for row 8's check 17);
   - (e) a worker-owned repository with planted refs, replace refs, alternates, `.git` file, `commondir` and config does not affect the next control-plane import, diff or publication;
   - (f) the worker's session and process group match the sudo pid, and `cancel` leaves no worker process of that session;
   - (g) a finished worker's workspace is removed by the normal cleanup through the sudo rule.

## 5. Excluded

- containment beyond the credential and authority boundary;
- the factory App's permission change and `"landing": true`;
- the Factory Director's own process;
- a new store or configuration source beyond the optional `worker_user` entry;
- changing earlier packets.

## 6. Review record

**Revision 6b (2026-10-04).** Recheck of `94ecfd7` (FAIL, MATERIAL M6): the bundle copy and every result read open with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC`, check owner and type by `fstat` on the open descriptor, and read only from it; a FIFO or a swapped folder is refused without blocking. Minor: traverse-only `<launch>` has no default ACL; result modes are stated.

**Revision 6 (2026-10-04).** REVIEWER of `eac3900` (FAIL: BLOCKING B1-B5, MATERIAL M1-M5), fixes in its wording: the bundle is made from a handoff ref; the claimed SHA is read as the worker; the bundle is copied as a regular file into a Founder-only folder before verify and fetch; the worker can read the intake repository and builds its VERIFIER and CLOSURE clones from it; results live under `<launch>/results/<c>/` and are read with `O_NOFOLLOW` as owned regular files; the regression base is the starting revision; all control-plane folders are listed; the landing clone moves to `<launch>/landing/`; intake creation and its remote are specified; the setup's final check is recursive; checks name the swap, symlink and layout defects. Minor: `PATH`, `transfer.fsckObjects`, the custody `ls-remote`, the database read paths, recovery names.

**Revision 5 (2026-10-04).** Founder decision B after the round 2 VERIFIER (`0faf472`, B2 and B3): the shared-repository design is replaced by a structural ownership split. Worker-owned clones per role; control-plane-owned packets, intake and landing repositories that workers cannot write; candidate hand-over by exact object identity through a bundle imported into the intake repository; no privileged git inside a worker copy. Candidates `a388f16`, `71b88a8` and `0faf472` are retired. Proof checks the two structural properties.

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
