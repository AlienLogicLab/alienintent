# WORKER-LAUNCH landing record (754c417)

`work launch`: run one role step (PRODUCER or VERIFIER) of one named, released work item through the existing provider contract, with the 6c-1 work context package, the injected model route, the authorized starting revision and an allowlisted environment. Unit 6c-2. Work item `621b0120-9fd2-41a0-b816-0b30ecf14281`. Landed by direct merge into `main`. No pull request.

## Status

Worker launch is operational for the configured codex route (check 10 passed). Read-only context access is implemented; operating-system containment is not (accepted by the Founder).

## What landed

- Accepted candidate: `754c41789242afe46397aa1f94b301ef2581cfd0` (branch `producer/worker-launch-621b0120`), built on base `64b334b37289b66179cd19274f561c611c9073de`.
- Merge base: `origin/main` `64b334b37289b66179cd19274f561c611c9073de`, the same commit as the candidate's base. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/worker-launch.md`, revision 2. It reached `main` in docs-only commit `64b334b`, byte-for-byte equal to packets-branch commit `7a2c08b` (`7a2c08bb27d61a1eeedcec9374f8f7da942b4ae5`, sha256 `cb40e0cdb421d88c48246551421e4b91a5d72f3e62d664dd6990474af2843ee1`). Its handoff `docs/work-units/python/worker-launch-handoff.md` is byte-for-byte equal to the copy in the registry approvals (sha256 `dd0c13fa7c1c7f1802547f7112225353408eb0b390d1f26f4424593f4fefd529`). The candidate changes neither.
- Scope: 19 files (8 production, 7 test, 4 tool files including the check 10 script `tools/live/worker_launch_provider_check.py`; 1327 insertions, 55 deletions), all inside the packet's authorized scope. No new store, record kind or configuration source; no schema change. The model routing reader moved to `src/alienintent/composition/model_routing.py`; the Director host keeps a standalone copy loaded by file path.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `621b0120-9fd2-41a0-b816-0b30ecf14281` (`~/.local/state/alienintent/registry/`).
- Agent Ready, packets commit `7a2c08b`: READY with `work assess`, attempt `f42aa5ef-ae68-4dec-b84c-5cf8279aec93` (`readiness/621b0120-9fd2-41a0-b816-0b30ecf14281/f42aa5ef-ae68-4dec-b84c-5cf8279aec93/raw`).
- Founder implementation approval: `~/.local/state/alienintent/registry/approvals/621b0120-9fd2-41a0-b816-0b30ecf14281.json` (item and commit `7a2c08bb27d61a1eeedcec9374f8f7da942b4ae5` bound; recorded 2026-10-03T05:46:40Z). The containment risk was explicitly accepted: there is no operating-system containment; workers run as the Founder's user with HOME, provider logins, git/gh credentials, SSH keys and the registry GitHub App key reachable; "only the control plane publishes" is a workflow rule; the permission mode is not isolation. Implementation approval only; the work item stays at CAPTURE.
- Handoff binding both roles: `~/.local/state/alienintent/registry/approvals/621b0120-9fd2-41a0-b816-0b30ecf14281-handoff.md`. It requires check 10 to pass before acceptance and closure.

## Dependency

- Unit 6c-1 (WORK-CONTEXT-PACKAGE, work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`) was recorded DONE in the permanent work registry with `work record-completed` before this unit was approved. Completion evidence: `work-completion/5befff2f-a0dd-4cea-9556-54c33ed86c1b` at `objects/8a1f8289b063ec12e5997b86eb20882d8a362ba8d50805219c6ba5b0507734be` (answer in `~/.local/state/alienintent/registry/record-6c1-completed.json`).

## Independent verification

| Round | Candidate | Packet | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `754c417` | revision 2 | ACCEPT | No blocking findings. Eight in-scope test files 259 passed; Director host 82 passed; Node 21/21; fitness PASS. Checks 1-9 each pinned by VERIFIER mutations; the survivors (M2, M16c, M23, M24, M26) change nothing observable today or are coverage notes (N1-N3). Check 9 standalone install done by hand. Check 10 output reviewed read-only. | `~/.local/state/alienintent/manual/worker-launch-verification/round1-754c417/verdict.md` |

## Real-provider check (check 10, Founder-run)

- Output: `~/.local/state/alienintent/manual/worker-launch-real-provider/run-754c417/report.txt` (with `report.json`, `routes.json`, `producer/` and throwaway `state/`), against candidate `754c41789242afe46397aa1f94b301ef2581cfd0`, using `tools/live/worker_launch_provider_check.py`.
- Result: `CHECK 10: PASS`.
- Route used, from `~/.config/alienintent/model-routing.json`: codex `gpt-6-sol`, `danger-full-access`, `/home/netmarine/.local/bin/codex`, for both PRODUCER and VERIFIER. The routes are identical, so one PRODUCER run was made and counts for both roles, as the packet and handoff allow; the VERIFIER-specific parts are covered offline by checks 1, 5 and 6.
- The provider started with the existing provider command (`codex exec --ephemeral --json --sandbox danger-full-access -C <workspace> --model gpt-6-sol -`, instruction text on standard input), exit 0. The worker read its package (committed nonce), ran its read-only context command (named HOLD `MISSING_RECORD` from a loaded profile), and made commit `bc70ca9` on top of baseline `b31d680` plus its self-review file.
- Authentication: the provider ran with a temporary HOME holding only `.codex/auth.json`, with no API key or token variable. The temporary HOME was removed after the run. All data was throwaway; the permanent registry was not opened.

## Landing checks

- Candidate fetched from the PRODUCER worktree into a fresh closure clone of `origin`; `git rev-parse` gave `754c41789242afe46397aa1f94b301ef2581cfd0`.
- `origin/main` was still `64b334b` at landing time, so no change on `main` since the candidate's base.
- Merge commit: `32b52697d94c1b1f155603f66e6b0f3f09875a19` (first parent `64b334b`, second parent `754c417`).
- `git diff 754c417 HEAD -- src tests tools test` on the merged tree: empty. The whole merged tree equals the verified candidate's tree.

Read-back on the merged tree (not a re-verification; no full suite):

- `python3 -m pytest -q tests/composition/test_worker_launch.py tests/composition/test_work_registry.py tests/execution_coordination/test_factory_coordinator.py tests/invocation_runtime/test_runtime.py tests/invocation_runtime/test_real_worker_outcome.py tests/context_assembly/test_work_context.py tests/control_plane/test_cli.py tools/orchestration/test_model_routing.py`: 259 passed, 0 failed.
- `python3 -m pytest -q tools/orchestration/test_factory_director_host.py`: 82 passed, 0 failed.
- `node --test test/worker-runner.test.mjs`: 21 tests, 21 pass, 0 fail.
- Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.

## Follow-ups

- F1 (PRODUCER open point 2; round 1, N10): before the first real `work launch`, an `alienintent` console script must be installed for the interpreter that runs it, for example `pip install -e .` in a venv. The package's `context_command` points at it, and none is installed on this machine today.
- F2 (PRODUCER open point 3; round 1, N7): under codex `workspace-write`, the PRODUCER's self-review write outside its worktree would fail, and the VERIFIER would then be held `MISSING_RECORD` (fail-closed). The live mode is `danger-full-access`.
- F3: a provider token refresh during a launch is written only into the temporary HOME copy, so a fresh provider login may be needed afterwards.
- F4: a held launch keeps its WIP slot. Resolving held launches is not this unit.
- F5 (round 1, N1-N10): the VERIFIER's non-blocking notes. The main ones: a regression test for the paths without a preparation hook (N2: M23 default starting revision, M24 fixed-tuple command given a standard-input pipe), and a per-instance route cache test if one launcher is ever reused for several invocations (N1). Also N4 (unpruned in-memory `outputs` and `kept`; package file left by an ineligible launch), N5 (VERIFIER clone left after a `prepare` refusal), N6 (self-review recorded before the coordinator's custody check), N8 (the temporary HOME limits default credentials but does not contain the worker), N9 (release-evidence mismatch caught by 6c-1 assembly, not the release gate).
- F6: the 6c-1 follow-ups F2 and F3 still stand: the evidence folder can `mkdir`, and a self-review race can leave an unused evidence object.
- F7 (Founder 2026-10-03; path plan 4A): an evidence-retention policy for unused evidence records is a later unit. Unused records are never completed-work evidence.
