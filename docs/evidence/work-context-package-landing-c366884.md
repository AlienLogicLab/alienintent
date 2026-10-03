# WORK-CONTEXT-PACKAGE landing record (c366884)

Unit 6c-1: each role's context package for a registered work item. Work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `c36688492487c41aa41aebd4778d54aec7ceeece` (branch `producer/work-context-5befff2f`). Chain: `4580d5b` (round 1 build against revision 3) then `c366884` (one repair commit for revision 4b). Built on base `9fc2f13efac5c1874139ab11e24d51d4c2911c49`.
- Merge base: `origin/main` `2718779bc4ec6a5561fadcc1a68bda246d4e282c`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/work-context-package.md`, revision 4b. It reached `main` in docs-only commit `2718779`, byte-for-byte equal to packets-branch commit `5b25c83` (sha256 `544be3fea4e1edca405da16805e1bd93360bfc6012e343b9fed4190fcffa3ed0`). Its handoff `docs/work-units/python/work-context-package-handoff.md` (sections 1-4) is byte-for-byte equal to the copy in the registry approvals (sha256 `27e8f61841c534242598a20330da2c4eab2b84966c32e5649d1d2f6732bd5f1c`). The candidate changes neither.
- Scope: 12 files (7 production, 5 test), all inside the packet's authorized scope. No new store, table or configuration source.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `5befff2f-a0dd-4cea-9556-54c33ed86c1b` (`~/.local/state/alienintent/registry/`).
- Agent Ready, revision 3 (packets commit `85f0b4e`): READY with `work assess`, attempt `c646d602-8f72-4d79-ad7e-d3b2f4032731`.
- Agent Ready, revision 4b (packets commit `5b25c83`): READY with `work assess`, attempt `ee1d9eba-9299-41ed-9d13-36767f4c7170`.
- Founder approval (revision 3) and re-approval (revision 4b): `~/.local/state/alienintent/registry/approvals/5befff2f-a0dd-4cea-9556-54c33ed86c1b.json`. The re-approval supersedes the first and carries the contract-fingerprint check into unit 6c-2.
- Handoff binding both roles: `~/.local/state/alienintent/registry/approvals/5befff2f-a0dd-4cea-9556-54c33ed86c1b-handoff.md`.

## Independent verification

| Round | Candidate | Packet | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `4580d5b` | revision 3 | ACCEPT | No blocking findings. Five test files 191 passed; fitness PASS; 20 of 20 own mutations caught, covering worker environment, read-only WAL and VERIFIER isolation. Found the packet-level VERSION_DRIFT issue: once launched, the store is at v+1, so a running worker's own call would hold. This led to revision 4b. | `~/.local/state/alienintent/manual/work-context-verification/round1-4580d5b/verdict.md` |
| 2 | `c366884` | revision 4b | ACCEPT | Repair only (3 files). The attempt check accepts store version v, or v+1 with this exact `launch:` effect `pending` or `unknown`; everything else is VERSION_DRIFT. A running worker's later call stays bound to the approved instructions. Five test files 197 passed; fitness PASS; 8 of 8 own mutations caught. Round 1 evidence kept. | `~/.local/state/alienintent/manual/work-context-verification/round2-c366884/verdict.md` |

## Landing checks

- Candidate fetched from the PRODUCER worktree into a fresh closure clone; `git rev-parse` gave `c36688492487c41aa41aebd4778d54aec7ceeece`.
- `git diff --stat 9fc2f13 origin/main`: only the packet and its handoff (docs only).
- Merge commit: `81cd23c1f52b6d218556399c94d01f2d89ae1842` (first parent `2718779`, second parent `c366884`).
- `git diff c366884 HEAD -- src tests` on the merged tree: empty. The merged tree differs from the verified candidate only in the two packet documents.

Read-back on the merged tree (not a re-verification):

`python3 -m pytest -q tests/context_assembly/test_work_context.py tests/composition/test_work_registry.py tests/control_plane/test_cli.py tests/execution_coordination/test_operational_store.py tests/context_assembly/test_work_identity_service.py`

Result: 197 passed, 0 failed, 0 skipped.

Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.

## Follow-ups

- F1 (Founder 2026-10-03; path plan 4A): unit 6c-2 must make the worker's own context call check the launched contract fingerprint. `work context` has no contract-digest option today.
- F2 (round 1): the worker profile's evidence folder is not read-only; `LocalEvidenceRepository` may create an absent folder.
- F3 (round 1): a self-review race with different text can leave an orphan evidence object before `SelfReviewExists`. The store record stays create-only.
- F4 (round 1): unit 6c-2 must record the self-review with the coordinator state's exact candidate value (including `independent_read_back_proven`), or the VERIFIER gets MISSING_RECORD.
- F5 (round 2): `tests/control_plane/test_cli.py` tests that import `tests.context_assembly` fail when run alone (pre-existing). Fix later with a shared fixture module.
- F6 (round 2): the attempt check does not check the effect's aggregate. No practical gap: the correlation names the identity and only the coordinator creates `launch:` effects.
- F7 (round 2): `effect_ledger` is called through `# type: ignore[attr-defined]`, as in `cutover.py`. It is not on the `OperationalStore` port.
