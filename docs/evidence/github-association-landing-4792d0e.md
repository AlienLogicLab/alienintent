# GitHub association and display landing record (4792d0e)

Unit: GITHUB-ASSOCIATION-AND-DISPLAY. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `4792d0e390d336e7745a1e3f7656e24389d4c4f1` (branch `producer/github-association-84eba5c`, commits `7a5e827` and `4792d0e`).
- Merge base: `origin/main` `ddee35179ffd16d81f07322a05f76209c9badec8`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/github-association-and-display.md`, assessed at `84eba5c`. The file was already on `main` at `ddee351`, byte-for-byte equal to the assessed revision (blob `c1a8f73a64dec1673999189240c56672ab67613e`). The candidate does not change it.

## Approvals (private records, outside the repo; paths only)

- Agent Ready: READY for packet `84eba5c`. Record directory: `~/.local/state/alienintent/manual/github-association-agent-ready-84eba5c/` (`native-result.json`, `owner.json`).
- Founder implementation approval: `~/.local/state/alienintent/manual/github-association-agent-ready-84eba5c/implementation-approval.json`.
- Design review: `~/.local/state/alienintent/manual/github-association-agent-ready-84eba5c/independent-review-d286846.md`.

## Real use (acceptance check 8)

Run by the Founder on `7a5e827` before acceptance, in a separate terminal, against new private stores and a dedicated clone whose remote is a local bare repository (so `work/<id>` tags never reach GitHub). Record directory: `~/.local/state/alienintent/manual/github-real-use/` (`RUN.md`, `run.sh`, `check.sh`, `permissions.txt`, `registered.json`, `link-1.json`, `link-2.json`, `display-1.json`, `display-2.json`, `updated-before.txt`, `updated-after.txt`).

- Founder permission change: before the run, the Founder raised the factory GitHub App (application `4990774`, installation `162769625`) Issues permission from `read` to `write`. The permission check then read `issues: write`, `organization_projects: write`, `metadata: read`, missing none (`permissions.txt`).
- Work item `be958fda-a779-426d-8731-5bf029f8ec1a` was linked: `work link` created Issue #154 on `AlienLogicLab/alienintent` and card `PVTI_lADOEcrpC84Bj5i_zg-IVDY` on board #1, and stored the link.
- Repeat runs of `work link` and `work display` wrote nothing: same Issue and card, display `unchanged`, Issue `updated_at` the same before and after (`2026-10-02T12:46:06Z`).
- Production code is unchanged between `7a5e827` and `4792d0e` (the second commit repairs tests only), so this real use applies to the landed code.

## Independent verification

| Round | Candidate | Verdict | Tests (seven named files) | Fitness | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `7a5e827` | REJECT (B1: four read-backs not proven by tests) | 199 passed | — | `~/.local/state/alienintent/manual/github-association-verification/round1-7a5e827/verdict-7a5e827.md` |
| 2 | `4792d0e` | ACCEPT | 204 passed | PASS | `~/.local/state/alienintent/manual/github-association-verification/round2-4792d0e/verdict-4792d0e.md` |

The seven named test files (packet section 9):

- `tests/context_assembly/test_work_link.py`
- `tests/execution_coordination/test_github_repository_api.py`
- `tests/execution_coordination/test_github_projects_v2.py`
- `tests/composition/test_sandbox_run_profile.py`
- `tests/context_assembly/test_work_identity_service.py`
- `tests/composition/test_work_registry.py`
- `tests/control_plane/test_cli.py`

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

## Follow-ups (all non-blocking)

- N1: an Issue carrying item X's marker but linked to item Y makes X's plain `work link` fail until `--issue` is used.
- N2: a losing run that used `--issue` on an Issue the App did not create leaves its card on the board.
- N3: a missing App key file is reported as `invalid-command-arguments`.
- N4: the duplicate close resends the listed body, so a human edit made in that window is overwritten.
- N5: `_STEP_NOTE` is duplicated in `cli.py`; `app_login` raises a bare `ValueError`.

## Landing checks

`origin/main` had not moved since `ddee351` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet 4792d0e HEAD` before this record was added), so the verifier's round 2 results apply to it unchanged. No tests were run again.
