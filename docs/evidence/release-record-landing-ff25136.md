# Release record landing record (ff25136)

Unit: RELEASE-RECORD-FROM-AUTHORIZATION. Work item `ae458d9b-4de1-4c67-a333-8eb982248b09`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `ff251368c36c75ca5886bc4b2c2c56260cbe2870` (branch `producer/release-record-ae458d9b`).
- Merge base: `origin/main` `cc17a79f3e531b3d9aa44a557d81c8aa4f99950f`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/release-record-from-authorization.md`. The file was already on `main` at `cc17a79`, byte-for-byte equal to packets-branch commit `eea4c5a` (sha256 `b451e6f6f03bfa2165e3b3bb9df0351c6bd5f2597282c26fe079e0cbefeaa9e9`). The candidate does not change it.
- Scope: 10 files (5 production, 4 tests, `tools/fitness/coupling_register.json`), exactly the packet's authorized scope. `StoredReleaseAuthorizations`, `GitRevisionResolver`, `ReleaseAuthorization` and `admit_release_preconditions` reused unchanged. No timeout changed.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `ae458d9b-4de1-4c67-a333-8eb982248b09` (`~/.local/state/alienintent/registry/`).
- Agent Ready: READY with `work assess`, attempt `d3f5f8d1-7851-4b8a-a352-6eb193b0cc4f` (provider limit 180 s).
- Founder approval: `~/.local/state/alienintent/registry/approvals/ae458d9b-4de1-4c67-a333-8eb982248b09.json`.
- Design review: `~/.local/state/alienintent/registry/independent-review-b994de7.md`.

## Real use (acceptance check 8)

Run by the Founder on a registry copy. Records: `~/.local/state/alienintent/manual/release-record-real-use/` (`run.sh`, `copy-20261002T155610Z/`).

- `work authorize` wrote the release record: baseline `cc17a79`, quote "I approve", `record_ref` `sha256:e829971d97e23e522d288282c93875b1401afb9d78c25f3658d62692d241837f`, equal to the exact evidence digest.
- The repeat run changed nothing.
- `admit_release_preconditions` accepts the record.

## Independent verification

| Round | Candidate | Verdict | Tests | Fitness | Wrong implementations caught | Record |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `ff25136` | ACCEPT | 112 passed | PASS | 27 of 27 | `~/.local/state/alienintent/manual/release-record-verification/round1-ff25136/verdict-ff25136.md` |

Tests run: `tests/context_assembly/test_work_authorization.py`, `tests/context_assembly/test_packet_assessment.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`.

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

## Follow-ups (all non-blocking)

- N1: two concurrent `work authorize` runs can race in the reused `StoredReleaseAuthorizations.record` (no expected version). Fix before unit 6 relies on it.
- N2: two invariant failures raise plain `RuntimeError`; they should be named errors.
- N3: two results are typed as plain `dict`.
- N4: real-use scripts should not reference the real sandbox `state.sqlite`.

## Landing checks

`origin/main` had not moved since `cc17a79` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet ff25136 HEAD` before this record was added), so the verifier's round 1 results apply to it unchanged. No tests were run again.
