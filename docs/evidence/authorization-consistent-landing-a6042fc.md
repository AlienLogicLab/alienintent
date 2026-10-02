# Authorization consistent with launch landing record (a6042fc)

Unit: AUTHORIZATION-CONSISTENT-WITH-LAUNCH. Work item `2232453f-9855-46cd-b155-34c11d88e43c`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `a6042fccb26b153474a4d17674d628505f245f50` (branch `producer/authorization-consistent-2232453f`, commits `6350009` and `a6042fc`).
- Merge base: `origin/main` `ae48480acea39d206ae9c4a325e3e3400e85c914`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/authorization-consistent-with-launch.md`. The file was already on `main` at `ae48480`, byte-for-byte equal to packets-branch commit `2c1fbfb` (sha256 `88b12e482768f4ebd6e97448fa8ebeb6dcaad51e5f95132198dc532070acbd55`). The candidate does not change it.
- Scope: 6 files (4 production, `tests/context_assembly/test_work_authorization.py`, `tests/execution_coordination/domain/test_policy.py`), all inside the packet's authorized scope. No timeout changed.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `2232453f-9855-46cd-b155-34c11d88e43c` (`~/.local/state/alienintent/registry/`).
- Agent Ready: READY with `work assess`, attempt `410b7e77-eb97-46cd-b437-1f6ad5640f15` (provider limit 180 s).
- Founder approval: `~/.local/state/alienintent/registry/approvals/2232453f-9855-46cd-b155-34c11d88e43c.json`.
- Design review: `~/.local/state/alienintent/registry/independent-review-c16a789.md`.

## Real use

None. The packet's proof is the deterministic race and crash tests.

## Independent verification

| Round | Candidate | Verdict | Tests | Fitness | Wrong implementations | Record |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `6350009` | REJECT | 108 passed | PASS | B1 (comparison after a conflict weaker than the whole release record) and B2 (`approval_ref` repair after a conflict) not caught | `~/.local/state/alienintent/manual/authorization-consistent-verification/round1-6350009/verdict-6350009.md` |
| 2 | `a6042fc` | ACCEPT | 111 passed | PASS | all caught except M9 (accepted, non-blocking) | `~/.local/state/alienintent/manual/authorization-consistent-verification/round2-a6042fc/verdict-a6042fc.md` |

Round 2 repair was test-only: three tests added to `tests/context_assembly/test_work_authorization.py`; production code unchanged from `6350009`.

Tests run: `tests/context_assembly/test_work_authorization.py`, `tests/execution_coordination/domain/test_policy.py`, `tests/composition/test_release_admission_wiring.py`, `tests/execution_coordination/test_factory_coordinator.py`.

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

## Notes (all non-blocking)

- N1: empty readiness evidence in `work authorize` (M9) is covered only by the `release_wording` unit test. Readiness is always a system value.
- N2: check 3's launch helper builds the READY row by hand with the READY view's keys, rather than going through the READY view itself.

## Landing checks

`origin/main` had not moved since `ae48480` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet a6042fc HEAD` before this record was added), so the VERIFIER's round 2 results apply to it unchanged. No tests were run again.
