# RECORD-COMPLETED-WORK landing record (067f31f)

`work record-completed`: record the actual approval, accepted candidate, verification and verified landing for an existing registered work item, keeping its identity, and move the row straight to DONE. Work item `cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `067f31fb51cfa20a029b1632ecd0d1d131d57807` (branch `producer/record-completed-work-cfd57b7e`). One commit, built on base `a824998f883bd4d8c25d26a5a0e358d01148ee96`.
- Merge base: `origin/main` `a824998f883bd4d8c25d26a5a0e358d01148ee96`, the same commit as the candidate's base. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/record-completed-work.md`, revision 2b (the packet text names its contract `revision-2`). It reached `main` in docs-only commit `a824998`, byte-for-byte equal to packets-branch commit `71eb20c` (`71eb20cf3fc4c90a2ea55e536edef33da475f972`, sha256 `06d342eeb545e8509cc815c8d9e6d6702128bfda0d63c574c6633b8e4405a955`). Its handoff `docs/work-units/python/record-completed-work-handoff.md` is byte-for-byte equal to the copy in the registry approvals (sha256 `ced0b2923ca6ed8b87da4075776d8d46c0ad812e699ec978de9615361740a69a`). The candidate changes neither.
- Scope: 13 files (7 production, 4 test, 1 tool script `tools/live/record_completed_work_6c1.sh`; 859 insertions, 9 deletions), all inside the packet's authorized scope. No new store, table, state or configuration source; no schema change.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0` (`~/.local/state/alienintent/registry/`).
- Agent Ready, packets commit `71eb20c`: READY with `work assess`, attempt `176e3429-f60d-49b9-915d-ad57a529192c` (`readiness/cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0/176e3429-f60d-49b9-915d-ad57a529192c/raw`).
- Founder implementation approval: `~/.local/state/alienintent/registry/approvals/cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0.json` (item and commit `71eb20cf3fc4c90a2ea55e536edef33da475f972` bound; recorded 2026-10-03T03:55:05Z). Implementation approval only; the work item stays at CAPTURE.
- Handoff binding both roles: `~/.local/state/alienintent/registry/approvals/cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0-handoff.md`. It fixes the sequence: registry-copy proof before acceptance, landing, the permanent 6c-1 completion record only after landing, then 6c-2's real-provider check.

## Independent verification

| Round | Candidate | Packet | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `067f31f` | revision 2b | ACCEPT | No blocking findings. Four test files 196 passed; fitness PASS. 31 of 33 own mutations caught across checks 1-4 and the CLI (M17 and M33 survive as defence in depth; a direct probe confirmed the in-transaction re-checks). Check 5 output reviewed read-only. | `~/.local/state/alienintent/manual/record-completed-work-verification/round1-067f31f/verdict.md` |

## Real use on a registry copy (check 5, Founder-run)

- Output: `~/.local/state/alienintent/manual/record-completed-work-real-use/run-20261003T050127Z/output.txt`, against candidate `067f31fb51cfa20a029b1632ecd0d1d131d57807`, using `tools/live/record_completed_work_6c1.sh`.
- On the copy, work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b` (WORK-CONTEXT-PACKAGE, unit 6c-1) moved from CAPTURE to DONE with the same id, label and pointer. Its `verification_ref` is `work-completion/5befff2f-a0dd-4cea-9556-54c33ed86c1b` at `objects/21234de03feef42a0ef0100818f913caa161d8a14db0303c645dda0be466584f`; `approval_ref` stayed null.
- The repeat answered `repeated: true` with the same reference and wrote nothing (copy hash `705c4322…` before and after).
- Every summary line said yes. Permanent registry unchanged: yes (work.sqlite `e4386d86…`, readiness.sqlite `4946d9bd…`, readiness-evidence tree `4aba5639…`, byte-identical before and after).

## Landing checks

- Candidate fetched from the PRODUCER worktree into a fresh closure clone; `git rev-parse` gave `067f31fb51cfa20a029b1632ecd0d1d131d57807`.
- `origin/main` was still `a824998` at landing time, so no change on `main` since the candidate's base.
- Merge commit: `bfe8ee2fc9f3b95b9f2219ca0e520e0e688ea8a0` (first parent `a824998`, second parent `067f31f`).
- `git diff 067f31f HEAD -- src tests tools` on the merged tree: empty. The whole merged tree equals the verified candidate's tree.

Read-back on the merged tree (not a re-verification):

`python3 -m pytest -q tests/context_assembly/test_work_completion.py tests/composition/test_work_registry.py tests/execution_coordination/test_factory_coordinator.py tests/control_plane/test_cli.py`

Result: 196 passed, 0 failed.

Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.

## Next steps

- N1: the Founder records 6c-1's completion in the permanent work registry with `work record-completed`, run from the registry clone's code, and only after this landing.
- N2: then unit 6c-2's implementation decision and its real-provider check.

## Follow-ups

- F1 (Founder 2026-10-03; path plan 4A): an evidence-retention policy for unused evidence records is a later unit. Unused records are never completed-work evidence.
- F2 (round 1, N1): two defensive guards inside the same write transaction survive mutation: M17 (`retired_at IS NULL` in the WHERE clause) and M33 (the repository's own DONE repeat/conflict re-check in `record_completed`). A future test could call the repository method directly on a DONE row.
- F3 (round 1, N2): the check 4 coordinator tests use a stand-in reader. There is no end-to-end test through the composed registry coordinator; the pieces are each pinned by a mutation.
- F4 (round 1, N3): a verdict whose first line is `ACCEPT\r` (CRLF) is refused.
- F5: a missing or unreadable `--verification` or `--approval` file gives a general CLI error rather than a named code.
