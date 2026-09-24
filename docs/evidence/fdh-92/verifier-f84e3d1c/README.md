# FDH-92 independent verification — JC

Invocation: `AlienLogicLab/alienintent#92:VERIFIER:f84e3d1c-e9fd-4ff1-8423-ef4d29c0c3d1`.

## Authority and candidate

Authority was reconstructed from Issue #92, its release comment
https://github.com/AlienLogicLab/alienintent/issues/92#issuecomment-5812645946,
the work packet `docs/work-units/wave2/FDH-92.md`, and producer publication
https://github.com/AlienLogicLab/alienintent/issues/92#issuecomment-5812766015.

- Admission baseline: `3a80e9ffcd04a972daa3903fa68088048fe7d330`.
- Code baseline: `0eda915`; comparison of the orchestration code and runtime contract against admission baseline was empty.
- Reviewed candidate: `93e4e7e0471095d3a0b7fedea7fcb58735d37693`.
- Candidate remote branch: `b-disp/9886ba7b-7bbe-467a-9676-a9f6bdcd807a`; fetched and independently confirmed with `git ls-remote`.
- Fresh isolated verifier worktree: `b-disp/6d430c7c-16a2-4c42-a895-e6aeff23e4ce`, initially clean at admission baseline, fast-forwarded to the exact candidate.
- Git author JC / jc-github@factorychecks.com; authenticated GitHub login `jc-worker`.
- This branch adds verifier evidence only; it does not replace the reviewed implementation SHA.

## Review

The only executable production change is `claims == wip_limit` to `claims >= wip_limit`.
`executable_capacity` remains `<`. Host precedence and the Director-only guard are unchanged.
The compatibility reason remains recognized; comments and contract section 10 correctly describe its
unreachability for adapter-derived inputs. Contract version remains 1. Existing synthetic coverage for
that compatibility reason is retained with a corrected test name. Consumer search found the host,
adapter, tests, contract and FDH-01 mutation helper; the helper's mutation target is unchanged.
No limit, Node claim, live installation or #91 env-file change appears in the candidate.

## Fresh results

Commands and exit codes are in `results.json`; full output is in the matching `.txt` files (trailing whitespace normalized for Git checks).
`verify.py` independently constructs the variants; it does not invoke the producer's control script.
Run from the candidate root: `rtk proxy python3 docs/evidence/fdh-92/verifier-f84e3d1c/verify.py`
(after retrieving this evidence script). Temporary variant trees and the detached baseline worktree
are removed after use.

| Acceptance | Run | Count | Exit |
|---|---|---|---|
| AC1–2 / AC5 | Baseline code plus candidate tests | 5 failed | 1, expected |
| AC3 / AC5 | Baseline code plus candidate regression guards | 6 passed | 0 |
| AC1–2 / AC5 | Candidate with `==` restored | 5 failed | 1, expected |
| AC3 / AC5 | Candidate with Director-only WIP guard removed | 6 failed | 1, expected |
| AC1–3 | Exact candidate targeted tests | 11 passed | 0 |
| AC4 / AC6 | All adapter, host and docs tests | 215 passed | 0 |
| AC7 | `node scripts/check.mjs all` | runtime 340/340; preflight PASS; RAI 18/18; policy 3/3 | 0 |
| AC7 | Candidate full `pytest tools` | 774 passed, 1 known failure | 1 |
| AC7 | Unmodified baseline full `pytest tools` in Git worktree | 763 passed, 1 known failure | 1 |

AC3's tests establish that a Director is actually launched. The host records
`DIRECTOR_CONTINUITY_FAULT` as its activation reason; that does not mean the idle reason is non-null.
An additional direct call to `FactoryDirectorHost._idle_reason(None, values)` for each candidate
`overlap_inputs` scenario (inbox, escalation and selection; claims=2, limit=1) returned `None`.
The three assertions and exit 0 are recorded in `direct-ac3.txt`.

The known failure is `test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`:
expected `gpt-6-astra`, observed live-config value `gpt-5.6-terra`. No change to that test or config.

The initial full baseline attempt used an archive. It also failed the installer executable-bit test
because that test invokes `git ls-files` and an archive lacks Git metadata. That harness failure is
retained as `baseline-archive-pytest-tools.txt`, and superseded for comparison by a fresh unmodified
baseline Git worktree run. Archive-based negative controls do not depend on Git metadata.

## Verdict

ACCEPT the exact producer candidate `93e4e7e0471095d3a0b7fedea7fcb58735d37693`.
AC1–7 are satisfied; both required mutations discriminate and no new full-suite failure was found.
The baseline and candidate share only the explicitly excluded non-hermetic routing failure.

## Disposition

Verifier evidence is published on the verifier's own branch. Both candidate and verifier evidence
remain in runtime-managed BIU custody pending SWF-19 closure; the worker does not delete those
resources or merge/push the baseline. No PR, deployment, restart or live reconfiguration was performed.
The Factory Director owns post-landing deployment and live overlap proof.
