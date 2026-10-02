# WIP admission landing record (9e2e35d)

Unit 6b: READY selection, release gate and WIP admission. Work item `cbfd45ee-3020-40ca-853e-d15d3baf82b4`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `9e2e35dd1313ba365157a2dac4a33cee79fd1625` (branch `producer/wip-admission-cbfd45ee`, commits `1ee87eb` and `9e2e35d`), built on base `f0752fbaad9e46701e6d88e0a53c11fc2af1ea03`.
- Merge base: `origin/main` `b29ca37b2fcf9f0e7530686015be1721f7661852`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/ready-selection-release-gate-wip-admission.md`, revision 3. It reached `main` in docs-only commit `b29ca37`, byte-for-byte equal to packets-branch commit `f7ccf89` (sha256 `8ea87655486d84758041542bf0ba92401313e2e9b89ef0faf06e9a2d1c95addf`). The candidate does not change it.
- Scope: 12 files (7 production, 5 test), all inside the packet's authorized scope. No timeout changed.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `cbfd45ee-3020-40ca-853e-d15d3baf82b4` (`~/.local/state/alienintent/registry/`).
- Agent Ready, revision 3: READY with `work assess`, attempt `bfdc8267-d031-4f7f-81f9-54249547a396`. An earlier attempt `1f7b8ea5` on the same revision failed with PROVIDER_FAILURE (empty output); it gave no verdict.
- Agent Ready, earlier revision 2f: READY, attempt `44f8888e`.
- Founder approval and re-approval: `~/.local/state/alienintent/registry/approvals/cbfd45ee-3020-40ca-853e-d15d3baf82b4.json`.
- REVIEWER record: `~/.local/state/alienintent/registry/independent-review-a4812b4.md`.

## Independent verification

| Round | Candidate | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- |
| 1 | `1ee87eb` | REJECT | Only blocker: the S0 frozen-kernel guard in `tests/composition/test_offline_proof.py` did not list the authorized `lifecycle.py` change. Everything else proven: 203 scoped tests, 767 coordinator tests, the two-store race test, 47 of 48 wrong implementations caught. | `~/.local/state/alienintent/manual/wip-admission-verification/round1-1ee87eb/verdict-1ee87eb.md` |
| 2 | `9e2e35d` | ACCEPT | One-line guard entry added. Guard 15/15 locally with `unshare`; fitness PASS. | `~/.local/state/alienintent/manual/wip-admission-verification/round2-9e2e35d/verdict-9e2e35d.md` |

Restart confirmation (Founder requirement): on restart, slots held by completed work are freed and slots held by active work are kept. Proven in round 1 and unchanged in round 2.

## Notes (all non-blocking)

- N1: `wipLimit` `1.0` is refused by Python but accepted by Node. This fails safe.
- N2: a lock held for more than 5 s surfaces as `StoreUnavailable`, as `acquire` does today.
- N3: a repeated cancel after a crash frees the slot at the next start.
- N4: the "pointer in another repository" stop condition is enforced by the release gate, not detected separately.
- N5: a work item skipped for WIP can still set the requirement focus.

## Landing checks

`origin/main` moved from `f0752fb` to `b29ca37` after the candidate was built. That one commit changes only the packet document, which no candidate file touches. The merged tree differs from the verified candidate tree only in that packet document (`git diff 9e2e35d HEAD` before this record was added).

Because `main` moved, the candidate's test files were run again on the merged tree:

`python3 -m pytest -q tests/execution_coordination/test_operational_store.py tests/execution_coordination/test_factory_coordinator.py tests/composition/test_work_registry.py tests/context_assembly/test_work_link.py tests/composition/test_offline_proof.py`

Result: 200 passed, 0 failed, 0 skipped.

Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.
