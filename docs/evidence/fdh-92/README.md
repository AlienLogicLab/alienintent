# FDH-92 evidence: claims at or above the WIP limit are intentionally full

- Issue: #92. Contract: `docs/work-units/wave2/FDH-92.md` (sha256 `f42237e29b2f29992fca8ba2c20a088f306f65399030f928c40b0366160e9183`).
- Invocation: `AlienLogicLab/alienintent#92:PRODUCER:f4694c37-b324-4b45-9762-7466b914b615` (PRODUCER Morty, Claude `claude-opus-5-5`).
- Admission baseline: `3a80e9ffcd04a972daa3903fa68088048fe7d330`. Code baseline: `0eda915`. The code under change is identical at both.
- Candidate branch: `b-disp/9886ba7b-7bbe-467a-9676-a9f6bdcd807a`.
- Implementation commit: `04c77e38406b0c78ac8597e009df8a0fdd06f5ef`. This evidence is committed on top of it, and the
  exact candidate SHA is recorded on Issue #92. Every run below was taken on a tree whose files match these hashes:

| File | sha256 |
|---|---|
| `tools/orchestration/factory_director_inputs.py` | `703a34d95da1afac0100ba9ffbf01315f0d53edb0efd78bbce25363966560049` |
| `tools/orchestration/factory_director_host.py` | `92a4f8392a25bcf92a36cbc9d8a67d90099d799236f10eb12b5d9ef202a3d070` |
| `tools/orchestration/test_factory_director_inputs.py` | `2623b0e81d90cf9d492dac1fda09ba78e6ebef8bcb0fff3cfeac0b1455e99fb0` |
| `tools/orchestration/test_factory_director_host.py` | `ac0bdbbbbd0a4eaa7bdacfddbccf95cf95ad7dea6b91bbd1f3e1be89e2530c1a` |
| `tools/orchestration/test_factory_director_docs.py` | `dd4b0cbd26fdd11df51632dbe0ced44f73efcb8fb6a1a77391f1a1051a5478c0` |
| `docs/operations/factory-director-runtime-contract.md` | `15d6d4b9e1868e12ed8120e7fead3343d3b93a18b00fa7207cd8de782ac81969` |

## Change

1. `derive()` sets `wip_intentionally_full = runtime.claims >= wip_limit`. `executable_capacity` stays
   `runtime.claims < wip_limit`, so the two predicates are exact complements.
2. `_idle_reason` precedence is unchanged. The `not values.director_only_control()` guard on the
   `WIP_INTENTIONALLY_FULL` branch is kept.
3. `EXECUTION_CAPACITY_UNAVAILABLE` is kept as a recognised reason. Because the predicates are complements, it is now
   unreachable from adapter-derived inputs. The host comment and contract §10 item 6 say so. No new condition was
   added for it. `test_overfull_wip_with_only_worker_work_refuses_as_capacity_unavailable` was renamed to
   `test_no_capacity_without_full_wip_refuses_as_capacity_unavailable`, because the adapter no longer derives
   that input combination for overfull WIP. Its inputs and assertions are unchanged.
4. Contract §10: the predicate table now says "active runtime claims ≥ WIP limit (at or above the limit …)", and
   precedence item 6 describes the unreachable reason. Contract version stays 1.
5. Consumer search (`grep` for `wip_intentionally_full|executable_capacity|EXECUTION_CAPACITY_UNAVAILABLE|WIP_INTENTIONALLY_FULL`
   over `tools`, `scripts` and `docs/operations`): the host, the adapter, their tests, the contract, and
   `tools/evidence/fdh01_evidence.py`. That file mutates the host line
   `if not values.executable_capacity and not values.director_only_control():`. The line is unchanged, so the
   FDH-01 control still applies. Diagnostics (`activeClaims`, `wipLimit`) and `history.jsonl` record only values and
   reasons. No reader assumes equality.

## New tests (criteria 1–3, 6)

The claims > wipLimit cases reproduce the live overlaps: two claims (PRODUCER and VERIFIER) on one Issue with wipLimit 1.

| Criterion | Test |
|---|---|
| 1 (worker work pending → `WIP_INTENTIONALLY_FULL`, IDLE) | `test_factory_director_inputs.py::test_overlap_with_only_worker_work_pending_idles_wip_intentionally_full` (real sources → adapter → host), `test_factory_director_host.py::test_claims_above_the_wip_limit_idle_as_wip_intentionally_full[worker-work-pending]` (`derive()` → host) |
| 2 (no control required → `WIP_INTENTIONALLY_FULL`) | `test_factory_director_inputs.py::test_overlap_with_no_control_required_idles_wip_intentionally_full`, `test_factory_director_host.py::test_claims_above_the_wip_limit_idle_as_wip_intentionally_full[no-control-required]` |
| 1–2 predicate | `test_factory_director_inputs.py::test_wip_intentionally_full` (over the limit is now `(executable_capacity, wip_intentionally_full) == (False, True)`) |
| 3 (inbox, escalation and selection → reason `None`, the Director launches) | `test_factory_director_inputs.py::test_overlap_never_suppresses_director_only_control[inbox,escalation,selection]`, `test_factory_director_host.py::test_claims_above_the_wip_limit_never_suppress_director_only_control[inbox,escalation,selection]` |
| 6 (contract agrees with the code) | `test_factory_director_docs.py::test_documented_wip_predicates_are_the_ones_the_adapter_derives` |

## Discriminating proof (criterion 5)

Command: `bash docs/evidence/fdh-92/controls.sh`, run from the repository root. The script builds scratch trees under
`/tmp` and removes them afterwards. `variants.diff` shows the one-line change in each variant. Each log ends with the
pytest exit status.

| Run | Tree | Tests | Result | Exit | Expected |
|---|---|---|---|---|---|
| `1-baseline-ac1-2.log` | `0eda915` code + candidate tests | criteria 1–2 | 5 failed | 1 | fail ✔ |
| `2-baseline-ac3.log` | `0eda915` code + candidate tests | criterion 3 | 6 passed | 0 | pass ✔ (regression guards) |
| `3-eq-variant-ac1-2.log` | candidate with `==` restored | criteria 1–2 | 5 failed | 1 | fail ✔ |
| `3b-eq-variant-ac6.log` | candidate with `==` restored | criterion 6 docs test | 1 failed | 1 | fail ✔ |
| `4-suppress-variant-ac3.log` | candidate with the guard on the `WIP_INTENTIONALLY_FULL` branch removed | criterion 3 | 6 failed | 1 | fail ✔ |
| `5-candidate-ac1-3-6.log` | candidate | criteria 1–3, 6 | 12 passed | 0 | pass ✔ |
| `6-candidate-fdh-suites.log` | candidate | inputs, host and docs suites | 215 passed | 0 | pass ✔ |

The suppressing variant is applied to the candidate code, as the release comment requires. On the baseline, that
branch is not reached when claims exceed the limit, so the variant would not discriminate there.

The first criterion-3 draft asserted `wip_intentionally_full` as a precondition, so it failed on the baseline
(the 6 failures in the first, discarded run). It now asserts `executable_capacity is False` plus the behaviour, so it
is a true regression guard on both trees.

## Full suites (criteria 4 and 7)

| Run | Command | Result | Exit |
|---|---|---|---|
| `7-candidate-check-all.log` | `node scripts/check.mjs all` | all checks pass | 0 |
| `8-candidate-pytest-tools.log` | `python3 -m pytest -q -p no:cacheprovider -rfE tools` (candidate) | 774 passed, 1 failed | 1 |
| `9-baseline-pytest-tools.log` | the same command in a temporary detached worktree at `0eda915` (removed afterwards) | 763 passed, 1 failed | 1 |

The one failure on both trees is the known non-hermetic
`tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`. It reads the
live `~/.codex/config.toml`, it is dispositioned as in ARP-01, and it was not modified. There is no new failure. The
difference of 11 passed tests is the 11 new test cases (the modified `test_wip_intentionally_full` was already counted).

## Not done by the worker

The live host was not installed, restarted or reconfigured, and the host env file (#91) was not touched. Deployment
and the live handoff-overlap observation belong to the Factory Director after DONE.
