ACCEPT

# VERIFIER verdict: WORKER-CREDENTIAL-BOUNDARY, revision 8, candidate 2078b37

- Work item: 7efccee9-13f0-4905-a0a1-e80bc2faa748
- Candidate: 2078b37084c6ed11b64f72606101c4d6c1589818, one commit on the accepted 156ef20.
- Worktree: /home/netmarine/.local/state/alienintent/manual/producer-worker-boundary-r7-7efccee9. HEAD was 2078b37. The tree was clean before and after the tests.
- Packet read: /home/netmarine/.local/state/alienintent/registry/clone/docs/work-units/python/worker-credential-boundary.md (revision 8). Checklist read: /home/netmarine/.local/state/alienintent/manual/worker-boundary-verification/round2-checklist.md.
- Claim boundary: a pass proves the worker credential boundary only. It does not prove the Factory Director boundary. It is not the protected-main landing authorization.

## 1. Scope, and nothing else changed

`git diff --stat 156ef20 2078b37` shows 4 files. All 4 are in authorized_scope (packet lines 40-47):
- src/alienintent/composition/work_registry.py (+48/-26)
- tests/composition/test_worker_launch.py
- tools/live/setup_worker_user.sh (+4/-2)
- tools/live/worker_boundary_check.py

What changed is only the persistent login:
- work_registry.py:246-273. `PROVIDER_LOGIN_FILES` is removed. New: `WORKER_PROVIDER = "codex"`, `worker_login_present`, `prepare_worker_session`.
- work_registry.py:646-647. `CODEX_HOME=<launch>/worker/auth/codex` is added to the worker environment, next to HOME and TMPDIR.
- work_registry.py:1074-1078. The `login_source` argument and attribute are removed.
- work_registry.py:1126-1131. `prepare` refuses a route that is not codex, then runs the login check.
- work_registry.py:1186-1187. `command` calls `prepare_worker_session`. The old `prepare_home` is deleted.
- setup_worker_user.sh:126-130. `~/.codex` and `~/.claude` are added to the list of Founder credential files that get o-rwx and lose any worker ACL. This matches packet section 1 (line 201).
- worker_boundary_check.py. 8(b) now also lists `.codex/auth.json` and `.claude/.credentials.json` (line 57-58), as packet 8(b) says. 8(c1) is rewritten. The docstrings and step labels are updated.

What did not change: cli_worker.py, git_source_control.py, git_worktree.py, real_worker.py, process_ownership.py, work_context.py, cli.py and operator.py are not in the diff. So the sudo rule, the bundle hand-over, the result reads, the context export and ownership are untouched. `check_d` is not in the diff, so the 8(d) rule (UNRESOLVED only on the exact 422, never a weaker token) is unchanged. test_offline_proof.py is unchanged.

## 2. No login file is read, written or copied by the control plane

I grepped src/ and tools/ for `auth.json`, `.credentials.json`, `login_source`, `PROVIDER_LOGIN_FILES`, `prepare_home` and `read_bytes`:
- `login_source`, `PROVIDER_LOGIN_FILES` and `prepare_home`: no hits left in src/ or tools/live/worker_boundary_check.py.
- `auth.json` in src/ appears only in the worker-run shell check (work_registry.py:248) and in the worker-run `find ... ! -name auth.json` (line 270), plus docstrings. The control plane never opens it.
- `read_bytes` hits in work_registry.py are line 861 (a module digest) and line 1109 (`read` when there is no worker user). Neither is near a login.
- worker_boundary_check.py: the Founder's `~/.codex/auth.json` is touched only by `os.stat` (lines 149-155), and is never opened. The worker store's auth.json is checked only by `stat -c %U:%a:%F` run as the worker (line 186).
- One old hit outside this unit: tools/live/worker_launch_provider_check.py:56 (`LOGIN_FILES`) and :314 (`args.login_source`). This is an older live tool. It is not in the diff and not on the worker-user path. It is not a finding against this candidate.

## 3. prepare_worker_session and worker_login_present match the packet

- The login check (work_registry.py:248, 251-254) is exactly `test -d <store> && ! test -L <store> && test -f <store>/auth.json && ! test -L <store>/auth.json`. It runs through `run_as_worker`. Only the exit code is read.
- `prepare_worker_session(user, environment, packets_clone, intake)` (lines 257-273) runs these steps, each as the worker:
  1. `rm -rf -- HOME`
  2. `mkdir -m 0700 -- HOME`
  3. `mkdir -p -m 0700 -- TMPDIR`
  4. writes `.gitconfig` with `umask 077`, holding only `[safe] directory = <packets clone>` and `directory = <intake>`
  5. runs exactly `find -P <store> -mindepth 1 -maxdepth 1 ! -name auth.json -exec rm -rf -- {} +`
  Any non-zero exit raises OSError.
- The refusal reasons are `worker provider unsupported: <provider>` (line 1128) and `worker provider login missing: <store>` (line 1131).
- CODEX_HOME reaches every worker command. `worker_prefix` (cli_worker.py:32-43) copies every environment entry after `env -i PATH=/usr/bin:/bin`. The registry adds CODEX_HOME to that environment (work_registry.py:646-647). The test asserts `CODEX_HOME=<store>` on every `env -i` sudo call (test_worker_launch.py:1419-1421).
- Order: the login check runs in `prepare` before `deliver`. Only `deliver` fills `self.kept` (line 1151). `command` needs `self.kept[invocation_id]` (line 1185) before it calls `prepare_worker_session`. So the cleanup can only run for an invocation whose login check passed.
- Symlink safety: every step runs as the worker, so it can only remove what the worker can already remove. `find -P` does not follow a symlinked store. `rm -rf` on a planted link removes the link, not its target. The scratch check below confirmed both.

## 4. 8(c1)

worker_boundary_check.py:158-194:
- It loops twice. Each time it runs `work_registry.worker_login_present(...)`, then `work_registry.prepare_worker_session(...)`, then one provider call as the worker. It has no preparation code of its own.
- It loads the registry configuration only to find the packets clone (line 170). This is the same JSON parse that checks a and b already use. It opens no database.
- The Founder file check uses stat only (inode, size, mtime_ns), before and after.
- The worker-run stat must give owner `alienintent-worker`, mode `600` and type `regular file`. PASS needs both return codes to be 0, that auth result, and the Founder file unchanged.
- An OSError from preparation is caught by `_guarded` and recorded as FAIL.
- A non-codex `--provider-argv` is FAIL.

## 5. Real second-user scratch check (no codex, no provider, no network)

- I made the scratch root `/tmp/wbv8-RrWWwJBe` with mode 0711 and ACL `u:alienintent-worker:--x`.
- One deviation from the brief: with only `--x`, the worker cannot create `<root>/worker` (mkdir gave "Permission denied"). So I briefly set `-wx` on that scratch root only. The worker made `worker` (0711). Then I set the ACL back to `--x` and checked it with getfacl.
- As the worker, through `sudo -n -u alienintent-worker -- env -i PATH=/usr/bin:/bin HOME=/var/lib/alienintent-worker`, I made `worker/auth/codex` (0700) and `auth.json` (`{}`, 0600). Then I planted `config.toml`, `AGENTS.md`, a `sessions/` folder with a file, a symlink to a Founder-owned file, a symlink to a Founder-owned folder, and `home/.git-credentials`.
- Signatures, read first: `worker_login_present(user, environment, store) -> bool` and `prepare_worker_session(user, environment, packets_clone, intake) -> None`.
- Results, from Python with PYTHONPATH=src, using the candidate's own functions:
  - The login check gave True before and after preparation.
  - After `prepare_worker_session`, the store held only `auth.json`. It was owned by alienintent-worker, mode 600, a regular file, 2 bytes.
  - HOME held only `.gitconfig`, with exactly the two safe.directory entries. HOME was 700 and TMPDIR was 700, both owned by the worker. The planted `.git-credentials` was gone.
  - The Founder-owned link targets were intact: the file still read `secret`, and the folder's file still existed.
  - The login check gave False with auth.json missing, and False with auth.json as a symlink.
  - It gave False with the store itself as a symlink. Calling `prepare_worker_session` through that symlinked store did not go into the real store: `config.toml` was still there afterwards.
- Cleanup: as the worker, `rm -rf <root>/worker` emptied the folder. The folder itself could not be removed, because the worker has no write on the root, which is expected. Then my own `rm -rf <root>` removed everything. The root is gone. `pgrep -u alienintent-worker` found no processes. No real `<launch>` folder was touched.

## 6. Tests and fitness

- `python3 -m pytest -q tests/composition/test_worker_launch.py tests/composition/test_offline_proof.py tests/context_assembly/test_work_context.py tests/control_plane/test_cli.py tests/invocation_runtime/test_runtime.py tests/invocation_runtime/test_owned_work.py tests/invocation_runtime/test_git_source_control.py tests/invocation_runtime/test_real_worker_outcome.py`: 237 passed, 0 failed.
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`: "PASS: all architecture fitness checks".
- The tests check what check 6 asks for:
  - no open of the Founder's `~/.codex` or `~/.claude`, using an audit hook;
  - the store holds only auth.json across two launches, with planted config.toml, AGENTS.md and sessions/ removed;
  - the exact login-check and cleanup command lines, once per session;
  - both refusal reasons, including an auth.json that is a symlink to the Founder's login.

## Pending and unchecked

- PENDING: the real 8(c1) run, two consecutive real Codex invocations with the same worker store. This is the Founder's run. It needs the one-time `codex login` as the worker first. 8(c2) and 8(d) are still deferred live proofs, as the checklist says. The work item stays open until they pass.
- Not checked: any real codex or provider behaviour. For example, I did not check whether codex writes anything outside CODEX_HOME, or whether its token refresh really lands in auth.json. Only the live 8(c1) can show that.
- Not checked: that the provider call in 8(c1) runs with the Founder's current folder as its working folder (`as_worker` sets no `cwd`). This is the same as in 156ef20 and is not new here.
- Note: the registry copy of the packet still says "Draft revision 8 ... Not approved" in its Status line (line 4). I treated it as approved, as the brief says. I did not check the approval record.
- I made no change to tracked files, the live setup, `~/.codex`, `~/.claude`, keys, databases or evidence.
