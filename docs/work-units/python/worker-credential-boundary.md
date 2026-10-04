# Work unit: the worker credential boundary

**Label:** `WORKER-CREDENTIAL-BOUNDARY` (a document label; permanent id `7efccee9-13f0-4905-a0a1-e80bc2faa748`).
**Status:** Draft revision 8 (work item `7efccee9-13f0-4905-a0a1-e80bc2faa748`, at CAPTURE) for independent review, 2026-10-05. Not approved, not assessed, not released.
**Position on the path:** the prerequisite for the real protected-main proof of row 8 (AUTOMATED-CLOSURE, check 17). It comes after row 8 lands and before the Founder grants the factory App any landing permission.
**Scope (Founder, 2026-10-04):** a specific credential boundary, not a claim that workers are fully contained. It must fit the existing launcher, with no elaborate new security framework. All cognitive sessions share the one `alienintent-worker` user, so no confidentiality between worker sessions is claimed; the boundary is authority and credential separation, not secrecy between workers. Its proof must show four things:
- PRODUCER and VERIFIER cannot read the App key;
- they cannot obtain equivalent landing credentials through another file or credential helper;
- CLOSURE (through the deterministic Landing Authority) can obtain the credential it needs;
- the normal worker context and provider login still work.

**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "7efccee9-13f0-4905-a0a1-e80bc2faa748",
 "version": "revision-8",
 "intent": "Make the worker credential and authority boundary structural: cognitive sessions run as a separate Unix user in their own worker-owned clones; no repository that can influence control-plane authority, release admission, verification custody or landing is writable by a cognitive worker; candidates are handed over by exact object identity through a bundle imported into a control-plane-owned intake repository; worker-owned repositories are never consumed as authority; process ownership and stopping work across users; the worker context and provider login still work.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-04: keep a clean separation between workers; the arrangement must fit the existing launcher; no elaborate new security framework merely to protect one key.",
  "Founder 2026-10-04: the proof shows PRODUCER and VERIFIER cannot read the App key, cannot obtain equivalent landing credentials through another accessible file or credential helper, CLOSURE can obtain the required credentials (through the deterministic Landing Authority) and land the exact accepted candidate, and the normal worker context and provider login still function.",
  "Founder 2026-10-04: this is a specific credential boundary, not a claim that workers are completely contained.",
  "Founder 2026-10-04: do not grant the App protected-main bypass until this separation proof passes and the Founder explicitly authorizes the permission change.",
  "Founder 2026-10-04 (decision B, structural): no repository that can influence control-plane authority, release admission, verification custody or landing may be writable by a cognitive worker; each cognitive role gets its own disposable worker-owned clone; the packets and release repository stay control-plane-owned; the candidate is handed over by exact object identity and imported into a trusted repository before any privileged use; worker refs, HEAD, config, alternates, .git files, commondir and replace refs never take part; the control plane never runs privileged git inside a worker copy.",
  "Founder 2026-10-04 (live-proof finding): canonical evidence remains control-plane-owned and private; a worker may receive only the bounded evidence and context explicitly exported for its invocation; do not weaken LocalEvidenceRepository, its UNSAFE_ROOT check or evidence-store privacy; check 8(d) must not depend on opening the evidence root.",
  "Founder 2026-10-05 (live-proof finding, option 1): the worker has its own persistent Codex login in worker-owned storage that survives across launches; the Founder's Codex login stays Founder-only and is never read or copied by the worker path; token refreshes persist in the worker's store; worker provider credentials stay completely separate from the GitHub App and landing authority; check 8(c1) runs two consecutive real Codex invocations with the same persistent worker login, and both must succeed.",
  "Founder 2026-10-05: 8(d) UNRESOLVED on the expected GitHub 422 because the Founder has not authorized the App's landing permission is an explicit dependency on the later protected-main authority decision, not evidence of a worker-boundary defect; any response other than the specifically recognized 422 remains FAIL; 8(d) is never redefined to mint a weaker token. 8(c2) is a sequencing dependency: it needs this implementation on main and one genuine launched work item. The work item stays open until both pass."
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
  "tests/composition/test_offline_proof.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tests/context_assembly/test_work_context.py",
  "tests/control_plane/test_cli.py"
 ],
 "excluded_scope": [
  "containment beyond the credential boundary",
  "the factory App permission change and the landing flag",
  "the Factory Director's own process",
  "a new store or configuration source beyond the optional worker_user entry and the worker's own login folder <launch>/worker/auth/codex (Founder 2026-10-05)",
  "changing earlier packets",
  "weakening LocalEvidenceRepository or its UNSAFE_ROOT privacy check"
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
| The canonical work and readiness databases, the readiness evidence repository and the registry configuration | Founder's user only, private (no worker access at all) | the control plane's context assembly |
| The per-invocation context export `<launch>/exports/<c>/context.json` | written by the Founder's user; readable by `alienintent-worker`; folder Founder-owned | the worker's `context_command` |
| The worker's Codex login `<launch>/worker/auth/codex` | `alienintent-worker` only, 0700 | worker sessions as `CODEX_HOME`; never opened by the control plane |
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

### 0.6b Context for workers: bounded export, never the canonical stores

Invariant (Founder, 2026-10-04, after the live proof): canonical evidence remains control-plane-owned and private. A worker may receive only the bounded evidence and context explicitly exported for its invocation. All cognitive sessions share the one `alienintent-worker` user, so no confidentiality between worker sessions is claimed; the boundary is authority and credential separation, not secrecy between workers.
- The control plane assembles each role's context package as the Founder's user (the existing `WorkContext.assemble` in `LaunchPreparation.prepare`), reading the canonical databases and the readiness evidence repository itself.
- It writes exactly that package, and nothing else, to `<launch>/exports/<c>/context.json` (`<launch>/exports` and `<launch>/exports/<c>` owned by the Founder, mode 0711, no write or default ACL for `alienintent-worker`; the file owned by the Founder, mode 0640 with one access ACL entry `u:alienintent-worker:r`, written atomically by rename within `<launch>/exports/<c>`). It holds no credential, key path or token, as today. With a worker user, `deliver` writes the package only to this export, and the instruction text's package path is this export; `<launch>/context` stays Founder-only and is never named to a worker.
- With a worker user, the package's `context_command` is `{"argv": [<installed alienintent>, "--json", "work", "context", "--export", "<launch>/exports/<c>/context.json"], "environment": {"ALIENINTENT_WORK_IDENTITY": <identity>, "ALIENINTENT_ROLE": <PRODUCER|VERIFIER|CLOSURE>, "ALIENINTENT_CORRELATION": <c>}}`, with no `--profile-factory` and no `ALIENINTENT_PROJECT_CONFIGURATION` or `ALIENINTENT_PROJECT`; the sudo allowlist carries those three identity variables and no longer carries the two configuration variables. The CLI dispatches `work context --export` before any profile factory is required or loaded, and refuses `--export` together with a target, `--role`, `--correlation`, `--candidate`, `--contract-digest` or `--profile-factory`. That mode opens only the named export file (with the opened-file rules of 0.5, accepting a regular file owned by the Founder's user), checks that its work item, role and correlation are the ones named in the worker's environment, and prints it. It builds no profile, opens no database, no evidence repository and no registry configuration, and takes no other path argument. A request for any other work item, correlation or evidence object answers `not-in-export` and reads nothing. The identity check is a consistency check of this API, not an isolation boundary: the worker supplies its own environment, and every `alienintent-worker` process can read any invocation's export whose path it learns. The export holds no credential or reusable authority, so this boundary claims no per-worker or per-invocation confidentiality of exported context (credential boundary, not containment).
- The worker therefore needs no access to the canonical databases, the readiness evidence repository or the registry configuration. The setup grants none, and `LocalEvidenceRepository`'s privacy check (`UNSAFE_ROOT`) is unchanged.
- What changes for the worker, stated plainly: with a worker user, `context_command` re-prints the package assembled at this launch; it does not recompute. The 6c-1 attempt check (VERSION_DRIFT after the attempt is confirmed, parked or superseded) and the 6c-2 `--contract-digest` re-check (DIGEST_MISMATCH) are no longer answered through `context_command`. They still hold where they matter: `prepare` assembles after the launch save, so each invocation's export is current at its start, and the control plane's own attempt check refuses a stale attempt's result. The old command never answered any other query, so no further fact is lost. Without a worker user, `work context` keeps every 6c-1 and 6c-2 behaviour. This is a deliberate change under the Founder's invariant of 2026-10-04, not a change to the earlier packets.

### 0.7 Nothing changes without a worker user

The registry configuration gains one optional entry, `worker_user`. Without it, launches behave exactly as today, worktrees included. The real protected-main proof requires it.

This is a credential and authority boundary, not containment. A worker can still do anything any local user can do. It proves nothing about the Factory Director, and it is not the protected-main landing authorization.

## 1. The one-time setup (Founder-run, needs root)

`tools/live/setup_worker_user.sh` prints every action, then runs only after the Founder types `yes`:
- create the system user `alienintent-worker` (home `/var/lib/alienintent-worker`, no login shell);
- write `/etc/sudoers.d/alienintent-worker`, mode 0440, checked with `visudo -c`, exactly: `Defaults>alienintent-worker !use_pty, !log_output` and `<founder> ALL=(alienintent-worker) NOPASSWD: /usr/bin/env, /usr/bin/kill`. It grants nothing to `alienintent-worker`, and nothing as root or as the Founder;
- create `<launch>/worker`, `<launch>/results` and `<launch>/handoff` owned by `alienintent-worker`, mode 0711; create `<launch>/intake.git`, `<launch>/intake-bundles` and `<launch>/landing` owned by the Founder, mode 0700;
- give `alienintent-worker` **read and traverse only** (access and default ACL `r-X`) on the packets clone, the intake repository `<launch>/intake.git` and the named install folders of the interpreter and the provider CLI; traverse only (access ACL `--x`, no default ACL) on `<launch>` and on `<launch>/exports`; traverse only on the folders from `/home/<founder>` down to them. It grants **nothing** on the work and readiness databases, the readiness evidence repository or the registry configuration, and removes any earlier grant there by removing every ACL entry (`setfacl -b`, and `-k` on folders) and restoring mode 0700 on the evidence root and `objects/`, and the databases' owner-only modes;
- remove any write ACL or default ACL for `alienintent-worker` on every control-plane-owned path;
- remove read for others from the Founder's credential files (`~/.git-credentials`, `~/.netrc`, `~/.gitconfig`, `~/.config/gh`, `~/.ssh`, the App key's folder, and the Founder's own provider logins `~/.codex` and `~/.claude`);
- final checks, as the worker: the App key is unreadable; the work and readiness databases, the readiness evidence repository (including `objects/`) and the registry configuration are neither readable nor traversable; the evidence repository's own privacy check still passes; no control-plane-owned repository, no folder or file inside one, and no parent folder of one, is writable by `alienintent-worker`, owned by it, or carries an ACL entry for it beyond read and traverse.

## 2. The changes

1. **Worker commands** (`invocation_runtime/adapters/cli_worker.py`): with a worker user, every session command and the VERIFIER's feature-regression runner start with the sudo prefix; stopping and per-pid kills go through `sudo -n -u <user> kill` (with no `env -i`). The allowlist names `PATH=/usr/bin:/bin`; the registry adds `CODEX_HOME=<launch>/worker/auth/codex` to the worker environment beside `HOME` and `TMPDIR` (change 5). The regression runner's `--base` is the release record's starting revision (full SHA) given by the control plane; `git merge-base HEAD origin/main` is no longer run.
2. **Ownership across users** (`invocation_runtime/adapters/process_ownership.py`): with a worker user, ownership by real uid and session id, with None for an unreadable worker-user process outside the session; `_owned` and `_signal` treat None as alive. Without one, unchanged.
3. **Worker workspaces and candidate import** (`invocation_runtime/adapters/git_source_control.py`, `invocation_runtime/adapters/git_worktree.py`): a worker-run clone for each role; the worker-run `git bundle create`; the control-plane import of 0.4 into the intake repository; publication from the intake repository; VERIFIER and CLOSURE clones made by the worker; workspace removal through sudo. Without a worker user, the existing worktree path is unchanged.
4. **The worker role paths** (`invocation_runtime/application/real_worker.py`): `_produce`, `_evaluate` and `_close` use change 3 when a worker user is configured; the candidate comes only from the intake import.
5. **The registry** (`composition/work_registry.py`): the optional `worker_user` entry; the worker HOME (recreated empty each launch, holding only a `.gitconfig` whose only entries are `safe.directory` for the packets clone and the intake repository); **the worker's own persistent provider login** (revision 8). The session preparation is one module function in `work_registry.py`, `prepare_worker_session(user, environment, packets_clone, intake)`; `LaunchPreparation.command` calls it, and check 8(c1) calls it. `PROVIDER_LOGIN_FILES` and `login_source` are removed. The folder `<launch>/worker/auth/codex`, owned by the worker and mode 0700, is given to every worker session as `CODEX_HOME`, so token refreshes persist there across launches. Before each session, as the worker through the sudo rule, everything in it except `auth.json` is removed: `find -P <store> -mindepth 1 -maxdepth 1 ! -name auth.json -exec rm -rf -- {} +`, so one session cannot leave configuration or instructions (for example `config.toml` or `AGENTS.md`) for the next. This runs after the login check below, so `<store>` is a real folder, not a symlink. A crash mid-session leaves files that this removes next time. If `auth.json` is left broken, the next session fails and the Founder runs `codex login` again; nothing is repaired automatically. The control plane never reads, writes or copies a login file: the Founder's `~/.codex` is never opened by the worker path. In `LaunchPreparation.prepare`, after the route is resolved: a route whose provider is not `codex` is refused under a worker user with the reason `worker provider unsupported: <provider>` (no persistent worker login exists for it yet); then the control plane runs, as the worker through the sudo rule, `test -d <store> && ! test -L <store> && test -f <store>/auth.json && ! test -L <store>/auth.json`, and if that fails the launch is refused with the reason `worker provider login missing: <store>` (the Founder makes the login once, as the worker, check 8 prerequisites). The control plane reads nothing from it but the exit code. The docstrings and the proof's check labels are updated to match. One launch at a time already holds, so two sessions never refresh at once; the VERIFIER `diff` from the intake repository; the landing clone moves to `<launch>/landing/landing-<c>`; `_producer_worktree` recovery names `<launch>/worker/producer-<c>`.

6. **The bounded context export** (`composition/work_registry.py`, `context_assembly/application/work_context.py`, `control_plane/adapters/cli.py`, `control_plane/application/operator.py`): `LaunchPreparation` writes the export of 0.6b; `ContextCommand` names the export mode when a worker user is configured; `work context --export <file>` reads only that file under the opened-file rules and the identity check of 0.6b. Without a worker user, `work context` and the read-only worker profile are unchanged; with one, `context_command` re-prints the launch-time export only (0.6b). In worker-user mode the instruction text's line about `context_command` reads: "To read your package again, run the package's `context_command`: its `argv` exactly, with its `environment` added to yours. It is read-only and prints the package exported for this invocation, or `not-in-export`."
7. **The proof's check 8(d)** (`tools/live/worker_boundary_check.py`): it mints the landing-scoped token by building only the Landing Authority's own `InstallationCredentials` from the `github` entry, without building a `WorkRegistry`, a readiness store or an evidence repository.

## 3. Exact permitted files

Production:
- `src/alienintent/invocation_runtime/adapters/cli_worker.py`
- `src/alienintent/invocation_runtime/adapters/process_ownership.py`
- `src/alienintent/invocation_runtime/adapters/git_source_control.py`
- `src/alienintent/invocation_runtime/adapters/git_worktree.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/context_assembly/application/work_context.py`
- `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py`
- `tools/live/setup_worker_user.sh` (new)
- `tools/live/worker_boundary_check.py` (new)

Tests:
- `tests/invocation_runtime/test_runtime.py`
- `tests/invocation_runtime/test_owned_work.py`
- `tests/invocation_runtime/test_git_source_control.py`
- `tests/invocation_runtime/test_real_worker_outcome.py`
- `tests/composition/test_worker_launch.py`
- `tests/context_assembly/test_work_context.py`
- `tests/control_plane/test_cli.py`
- `tests/composition/test_offline_proof.py` (only: add `src/alienintent/invocation_runtime/adapters/git_worktree.py` to the frozen-kernel guard's expected changed-file list; nothing else in that test may change)

## 4. Acceptance checks (each names the wrong implementation it catches)

Offline, with a fake `sudo` on the test `PATH` that records its arguments and runs the command as the test's own user, and a fake `/proc` where needed:
1. **No privileged git in a worker repository.** With a worker user, every git command run by the control plane or the Landing Authority is recorded with its working directory and `GIT_DIR`. None of them is inside `<launch>/worker/` or `<launch>/handoff/` other than reading the bundle file as data. Catches a privileged command that touches a worker repository.
2. **No worker write to control-plane repositories.** The setup script's plan grants `alienintent-worker` no write and no default ACL on the packets clone, the intake repository, the landing folder or any parent of them. Its final checks assert it. The plan gives `<launch>/worker`, `<launch>/results` and `<launch>/handoff` mode 0711, and the worker read and traverse on the intake repository. Catches a shared mutable authority surface and a layout in which the hand-over cannot work across users.
3. **Exact-identity hand-over.** The import fetches only the claimed SHA from the bundle, refuses when the imported commit differs from the claim, ignores the bundle's ref names, and refuses a bundle whose prerequisite or content fails `bundle verify`. A worker repository with a planted `refs/heads/main`, `refs/replace/*`, `objects/info/alternates`, `.git` file, `commondir` and `config` does not change the imported candidate or any control-plane result. A bundle path replaced by a directory or a symlink after `bundle verify` is refused, and no control-plane git command has a path under `<launch>/worker/` or `<launch>/handoff/` as an argument. Catches trust in worker refs or metadata.
4. **Every worker-side command goes through the one rule.** Session commands, the regression runner, workspace creation, bundle creation and workspace removal start with exactly `sudo -n -u <user> -- env -i` and the allowlisted variables (including `CODEX_HOME`). Without a worker user, commands and the worktree path are unchanged. Catches a worker command left as the Founder.
5. **Ownership and stopping across users.** A fake `/proc` with an unreadable root process gives (), not None; an unreadable worker-user process outside the session gives None; `_owned` returns True on None; kills go through sudo, including each owned pid. Catches "nothing is running" read from unreadable processes.
6b. **Results are never read through a worker-chosen path.** A self-review, verdict, receipt or CLOSURE request that is a symlink is refused and its target is never read. A FIFO, or a `<c>` folder swapped for a symlink to a Founder-owned folder, is refused without blocking and without reading a Founder-owned file. Catches a privileged read through a worker-chosen path.
6c. **Workers never reach the canonical evidence.** The setup plan grants `alienintent-worker` no read, traverse or default ACL on the work and readiness databases, the readiness evidence repository (including `objects/`) or the registry configuration, and removes any earlier grant; its final check asserts that the worker can neither traverse nor read them. Catches an evidence store opened to workers.
6d. **Context comes only from the bounded export.** A worker's `context_command` prints exactly the exported package for its own invocation, with no database, evidence repository or configuration opened (recorded file opens). It refuses another work item, correlation or role (`not-in-export`), an export that is a symlink, FIFO or not owned by the Founder, and any extra path or evidence-object argument, reading nothing. The export folders and file are Founder-owned with the stated modes and no worker write or default ACL, and the exported package's `context_command.environment` names no configuration path. Catches a context command that reads canonical stores or arbitrary evidence, a worker-writable export folder, a world-readable export and a package that still names the configuration.
6. **The worker HOME and the worker's own login.** The HOME holds exactly the `safe.directory`-only `.gitconfig`, recreated empty each launch. The session's `CODEX_HOME` is `<launch>/worker/auth/codex`, which holds only `auth.json` when the session starts. `prepare_worker_session` opens no file, and no file under the Founder's `~/.codex` or `~/.claude` is opened during `prepare` or `command` (recorded file opens). A missing `auth.json` refuses the launch with `worker provider login missing: <store>`; a non-`codex` route under a worker user is refused with `worker provider unsupported: <provider>`. Catches a widened HOME, a copied Founder login, and copy-and-discard of a rotating login.
7. **Fitness.** The changed test files pass when run together (no full suite), with `tests/composition/test_landing_authority.py`, `tests/composition/test_sandbox_run_profile.py` and `tests/execution_coordination/test_role_orchestration.py` unchanged; `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
8. **Real-use proof (Founder-run, after the setup).** `tools/live/worker_boundary_check.py` records:
   - (a) as the worker, reading the App key fails; the registry configuration, the work and readiness databases and the readiness evidence repository (including `objects/`) are neither readable nor traversable, and the evidence repository's own privacy check still passes as the Founder;
   - (b) as the worker, no `gh` login, git credential helper, SSH key or token variable is reachable, each named credential file (including the Founder's `~/.codex/auth.json` and `~/.claude/.credentials.json`) is unreadable, an installation-token mint fails, and `sudo -n -l` fails;
   - (c1) **two consecutive real Codex invocations** as the worker, each with a fresh HOME and the same persistent `CODEX_HOME` `<launch>/worker/auth/codex`, both succeed; each invocation first passes the same worker-run login check as `LaunchPreparation.prepare` and is then prepared by the candidate's `prepare_worker_session`, and the proof tool holds no preparation code of its own; the store's `auth.json` is a regular worker-owned file of mode 0600; the Founder's `~/.codex/auth.json` is never opened by the proof, and its inode, size and modification time are unchanged (stat only; the Founder does not use Codex during the proof). Prerequisite: the Founder's one-time step, as the worker through the sudo rule, outside the candidate: `mkdir -p -m 0700 <launch>/worker/auth <launch>/worker/auth/codex` (Codex refuses a `CODEX_HOME` that does not exist), then `env -i PATH=/usr/bin:/bin HOME=<launch>/worker/home CODEX_HOME=<launch>/worker/auth/codex <absolute codex path> login`;
   - (c2) as the worker, a package's `context_command` returns, from the bounded export only, the real context package of a genuinely registered and approved work item, while the canonical evidence repository stays unreadable to the worker. If none exists, 8(c2) is recorded as unresolved and the proof does not pass;
   - (d) as the Founder, the Landing Authority mints a landing-scoped token through its own `InstallationCredentials` only, without building a `WorkRegistry`, readiness store or evidence repository, and without changing the evidence root's permissions (partial: the landing path itself waits for row 8's check 17). GitHub's answer with HTTP status 422 to this installation-token request, as the credentials' own message `github answered 422 where 201 was required` reports it, is recorded UNRESOLVED: the App has no landing permission until the Founder's later protected-main authority decision. A token is PASS only with exactly the landing permissions, repository selection `selected`, and the evidence root's mode unchanged. Any other answer or token is FAIL. (Founder-confirmed 2026-10-05 and already built in `156ef20`; recorded here, not a new change.);
   - (e) a worker-owned repository with planted refs, replace refs, alternates, `.git` file, `commondir` and config does not affect the next control-plane import, diff or publication;
   - (f) the worker's session and process group match the sudo pid, and `cancel` leaves no worker process of that session;
   - (g) a finished worker's workspace is removed by the normal cleanup through the sudo rule.

## 5. Excluded

- containment beyond the credential and authority boundary;
- the factory App's permission change and `"landing": true`;
- the Factory Director's own process;
- a new store or configuration source beyond the optional `worker_user` entry and the worker's own login folder `<launch>/worker/auth/codex`;
- changing earlier packets.

## 6. Review record

**Revision 8 (2026-10-05).** Live-proof finding on candidate `156ef20`: 8(c1) failed with `refresh token already used`. Codex's ChatGPT login rotates its refresh token, and the design copied the Founder's `~/.codex/auth.json` into a fresh worker HOME for each session and then discarded it, so two holders of one rotating token broke each other. Founder (option 1): the worker gets its own persistent Codex login in `<launch>/worker/auth/codex`, used as `CODEX_HOME`; the Founder's login is never read or copied; check 8(c1) runs two consecutive real invocations with the same store. This is the only substantive change. Also recorded, as the Founder confirmed on 2026-10-05: 8(d) UNRESOLVED on the exact 422 (already built in `156ef20`) and 8(c2) as deferred live proofs. REVIEWER of `a42a8c5` (FAIL, text gaps; design sound): B1 the login check runs as the worker; B2 one shared `prepare_worker_session` used by 8(c1); B3 check 6 narrowed to `~/.codex` and `~/.claude`; B4 the 422 defined; N1-N10 applied. Follow-up of `c1895fd` (PASS): R1-R3 wording applied. Candidate `156ef20` stays unlanded; its other checks passed live (a, b, e, f, g).

**Revision 7b (2026-10-04).** REVIEWER of `d58319c` (FAIL, text fixes; design sound): the old `work context` only re-ran `assemble` and the store does not move during an invocation, so only freshness is lost and nothing depends on it; B1 states that loss; B2 fixes check 8(a); B3 makes the export the only package path named to a worker; M1 states that the identity check is not isolation and that no confidentiality between workers is claimed; M2 specifies the export-mode command, environment and CLI dispatch; M3 fixes export ownership, modes and tests; M4 restores owner-only modes after removing ACLs, so `UNSAFE_ROOT` passes.

**Revision 7 (2026-10-04).** Blocking live-proof finding: the setup granted the worker read on the canonical readiness evidence repository, and `LocalEvidenceRepository` correctly refused it (`UNSAFE_ROOT`). Founder: canonical evidence stays control-plane-owned and private; workers receive only the bounded context exported for their invocation. Changes: section 0.6b (context assembled by the control plane, exported per invocation; `work context --export`); the setup grants nothing on the databases, the evidence repository or the configuration; check 8(d) mints without building evidence infrastructure; new checks 6c and 6d. Candidate `1f1e1e3` is retired. `LocalEvidenceRepository` and its privacy check are unchanged.

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
