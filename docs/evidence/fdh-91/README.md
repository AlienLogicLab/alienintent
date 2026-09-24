# FDH-91 evidence: the host env file must set a PATH that resolves the host's tools

- Issue: #91. Contract: `docs/work-units/wave2/FDH-91.md` (sha256 `54e6d99dd7a39a86f93fa3df9914648423804963cf2d3bc20d14da4df4f0aaa1`,
  equal to the Agent Ready input).
- Invocation: `AlienLogicLab/alienintent#91:PRODUCER:31975474-e114-4fdf-a7e8-fcc5d338427f` (PRODUCER Morty, Claude `claude-opus-5-5`).
- Admission baseline: `669e5f1cf8e759e1b88beacd194650ab0f6a88d8`. Contract code baseline: `0eda915`. The discriminating
  proof was run against **both**.
- Candidate branch: `b-disp/b0bf79df-c3a3-476b-87a1-062c087f6f54`.
- Implementation commit: `cba31f9f1c1756979935e0b7e34e7064d32e45c0`. This evidence is committed on top of it, and the
  exact candidate SHA is recorded on Issue #91. Every run below was taken on a tree whose files match these hashes:

| File | sha256 |
|---|---|
| `tools/orchestration/factory_director_inputs.py` | `8adb3aa6b779c2b84bc728cbb05f53f6aab1de8db4adc1e1e22c3870c79e8181` |
| `tools/orchestration/install_factory_director_host.sh` | `7be202af370f99d5a5b6dd8a36b9dccfd6289490fa3e146ec368b642386a1af7` |
| `tools/orchestration/test_factory_director_inputs.py` | `e76b865a3385346295e6641e4b2bb766f6ee4e2404db34a6fef9a0aa1143bb09` |
| `tools/orchestration/test_factory_director_docs.py` | `27327b6b40a0733ab8043c112535af0a6041863d2644b0714e81196b7aa65ed2` |
| `docs/operations/factory-director-host-live-proof.md` | `6695e276b7bcca8500e2e46d15bad3c0aac0f854a6a363c95e6946d7ab778701` |
| `docs/operations/factory-director-host.md` | `1fde0b92a3882a700b34764aa461afbcdc8d6d49dc33dd0e467df1a136b1fdc0` |

## Change

1. **Procedure (scope 1, criterion 1).** Live-proof step 0a adds `PATH=/home/netmarine/.local/bin:/usr/local/bin:/usr/bin:/bin`
   to the env-file example (the live installation's value, as the contract allows in documentation). It says `PATH` is
   required, why (the systemd user unit does not inherit the login shell's `PATH`, and its default lacks
   `~/.local/bin`), which tools it must resolve (`gh`, `python3`, `git`, the provider CLI `claude` or `codex`), that the
   directories must be absolute because systemd does not expand `$HOME` or `~` in an `EnvironmentFile`, and what the
   failure looks like. `docs/operations/factory-director-host.md` (Installation and inspection) now describes the env
   file and carries the same requirement.
2. **Installer (scope 2, criterion 2).** When `install_factory_director_host.sh` creates a new env file, it also seeds
   two comment lines of PATH guidance and a commented example `# PATH=${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin`,
   with `${HOME}` expanded at install time. No user path is hard-coded. The seeded file sets nothing. An existing
   env file is still never touched, and the installer still only runs `systemctl --user daemon-reload`.
3. **Preflight (scope 3, criterion 3, `DETERMINISTIC_PREFLIGHT`).** New `require_gh()` in
   `factory_director_inputs.py` resolves `gh` with `shutil.which` on the effective `PATH` (`os.defpath` when unset). If
   it cannot resolve `gh`, it raises `SourceUnavailable("required executable 'gh' is not resolvable on PATH='…'; set PATH in
   factory-director-host.env")`. `AuthoritativeDirectorInputs.read_board` calls it first whenever a default (gh-backed)
   reader is in use. Both `gh` call sites (`materialization.read_board` and `read_issue_comments`) run only after
   `read_board`, so the one check covers them. It fails at the same point in `evaluate()` where the raw
   `FileNotFoundError` used to surface, and through the same path (`Evaluation(UNAVAILABLE, failure)`, `last_failure`,
   diagnostics file, host `failure` in `history.jsonl`). Exit code, `authoritative_state` and ordering are unchanged.
   Injected readers (the existing test fixtures) skip the check, so they need no `gh`.

Non-goals held: no predicate, idle reason or launch behaviour changed. `project_materialization.py` is unchanged.

**Baseline behaviour, recorded honestly.** On the baseline, a missing `gh` already failed closed without a printed
traceback, because `read_board` wraps every exception. The failure was
`Project board read failed: [Errno 2] No such file or directory: 'gh'`. It named `gh` but not the `PATH` searched,
and it came from an unplanned `FileNotFoundError`. The criterion-3 tests therefore discriminate on the `PATH` in the
failure. See the `E` lines in `3-*-ac3-gh.log`.

## New tests

| Criterion | Test |
|---|---|
| 1 | `test_factory_director_docs.py::test_env_file_guidance_requires_a_path_that_resolves_every_host_tool[live-proof-0a,host-doc]` |
| 2 (seed) | `test_factory_director_docs.py::test_installer_seeds_a_new_env_file_with_commented_path_guidance`: temporary `HOME`, stubbed `systemctl` that logs its arguments. Every seeded line is a comment, the expanded example PATH line is present, mode is 0600, and the only `systemctl` call is `--user daemon-reload`. |
| 2 (keep) | `test_factory_director_docs.py::test_installer_leaves_an_existing_env_file_byte_identical`: bytes, mode, mtime and inode are unchanged. |
| 3 | `test_factory_director_inputs.py::test_unresolvable_gh_fails_closed_naming_gh_and_the_searched_path`: runs the real CLI in a subprocess with `PATH` set to an empty directory. It checks for a non-zero exit, all nine predicates false, a failure naming `'gh'` and `PATH='<dir>'`, no `Traceback` on stdout or stderr, and the same failure in the diagnostics file. |
| 3 (host) | `test_factory_director_inputs.py::test_host_records_the_unresolvable_gh_failure_with_the_refusal`: the real host refuses with `AUTHORITATIVE_STATE_UNAVAILABLE`, and `history.jsonl` records the failure. |
| 4 | `test_factory_director_inputs.py::test_resolvable_gh_leaves_adapter_behaviour_unchanged`: a fake `gh` is the only thing on `PATH` and answers the board and comment queries. The CLI exits 0 with the expected projection, and it equals the projection from the same sources through injected readers. |

## Discriminating proof (criterion 5)

Command: `bash docs/evidence/fdh-91/controls.sh`, run from the repository root. For each baseline (`0eda915` and
`669e5f1`), it builds a scratch tree under `/tmp` with that baseline's `tools`, `docs/operations` and `config`, plus the
candidate's two test files. It also builds a no-preflight variant: the candidate with only the `require_gh()` call
replaced by `pass` (`nopreflight-vs-669e5f1.diff`). Scratch trees are removed afterwards. Each log ends with the pytest
exit status.

| Run | Tree | Tests | Result | Exit | Expected |
|---|---|---|---|---|---|
| `1-0eda915-ac1-docs.log` | `0eda915` + candidate tests | criterion 1 | 2 failed | 1 | fail ✔ |
| `2-0eda915-ac2-seed.log` | `0eda915` + candidate tests | criterion 2 seed | 1 failed | 1 | fail ✔ |
| `3-0eda915-ac3-gh.log` | `0eda915` + candidate tests | criterion 3 | 2 failed | 1 | fail ✔ |
| `4-0eda915-guards.log` | `0eda915` + candidate tests | criterion 2 keep, criterion 4 | 2 passed | 0 | pass ✔ (regression guards) |
| `1-669e5f1-ac1-docs.log` | `669e5f1` + candidate tests | criterion 1 | 2 failed | 1 | fail ✔ |
| `2-669e5f1-ac2-seed.log` | `669e5f1` + candidate tests | criterion 2 seed | 1 failed | 1 | fail ✔ |
| `3-669e5f1-ac3-gh.log` | `669e5f1` + candidate tests | criterion 3 | 2 failed | 1 | fail ✔ |
| `4-669e5f1-guards.log` | `669e5f1` + candidate tests | criterion 2 keep, criterion 4 | 2 passed | 0 | pass ✔ (regression guards) |
| `5-nopreflight-ac3.log` | candidate, preflight call disabled | criterion 3 | 2 failed | 1 | fail ✔ |
| `6-candidate-ac1-4.log` | candidate | criteria 1–4 new tests | 7 passed | 0 | pass ✔ |
| `7-candidate-fdh-suites.log` | candidate | inputs, host and docs suites | 222 passed | 0 | pass ✔ |

The byte-identity test (criterion 2, keep) and the fake-`gh` test (criterion 4) pass on the baseline by design. They
guard behaviour that must not change. They are not discriminating tests.

## Full suites (criteria 4 and 6)

| Run | Command | Result | Exit |
|---|---|---|---|
| `8-candidate-check-all.log` | `node scripts/check.mjs all` | all checks pass | 0 |
| `9-candidate-pytest-tools.log` | `python3 -m pytest -q -p no:cacheprovider -rfE tools` (candidate) | 781 passed, 1 failed | 1 |
| `10-baseline-669e5f1-pytest-tools.log` | the same command in a temporary detached worktree at `669e5f1` (removed afterwards) | 774 passed, 1 failed | 1 |

The one failure on both trees is the known non-hermetic
`tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`. It reads the
live `~/.codex/config.toml`, it is dispositioned as in ARP-01, and it was not modified. There is no new failure. The
difference of 7 passed tests is the 7 new test cases.

## Not done by the worker

The live host was not installed, restarted or reconfigured. The live `~/.config/alienintent/factory-director-host.env`
was not edited. Deployment of the landed installer and procedure is a separate Factory Director
step after DONE.
