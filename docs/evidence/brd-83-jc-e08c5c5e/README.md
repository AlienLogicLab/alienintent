# JC independent verification — BRD-83 cycle 2

Verdict: **ACCEPT** of producer candidate `1167e79ec89f781d1cd89d3e41c9829534198b10`, branch `b-disp/3dac0d9e-88fc-45cf-a499-e6e298726ebd`.
Invocation: `AlienLogicLab/alienintent#83:VERIFIER:e08c5c5e-e267-48b1-adf1-7dee03a28332`.

## Authority and admission

Reconstructed from Issue #83, Director release comment 5811219183, the retained BRD-83 contract, prior JC rejection comments 5811522023 / 5811761861, and producer result 5811911868. The release comment advances the contract's historical baseline to `474343a4142316941340762a243e965ef44bb15c` and explicitly authorizes offline criteria 1–7 plus the separate read-only landed-code review. No live fixture or live switch is required or authorized in this phase.

Authenticated GitHub login: `jc-worker`; Git identity: `JC <jc-github@factorychecks.com>`. Initial runtime worktree was clean at `59db3c532a004e10dee60eede7a477e8e17545f1`, branch `b-disp/3d782e21-c66d-4cb4-9810-72e0ccebbfc2`. Retrieved the producer branch and read its exact SHA back with `git ls-remote`. This fresh isolated worktree was positioned at the exact candidate for all checks. The candidate diverges from current main only because main additionally has FDH-01 evidence; the merge-base diff adds only BRD-83 files and does not delete that main evidence.

## Fresh acceptance evidence

Commands below were launched via `rtk proxy`; `commands.json` records subprocess arguments and actual exits. Each corresponding `.log` retains raw output.

| Criterion / check | Command or method | Exit / result |
|---|---|---|
| AC1 custody | Extract both `1439457:tools/live/<file>` blobs with `git show`, compare SHA-256 to contract; run `python3 -m pytest -q <temporary import directory>` | 0; exact digests; 23 passed |
| AC2/3/4/5 | `python3 -m pytest -q tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0; 95 passed |
| AC6 | `python3 tools/live/brd83_proven_red.py --json` | 0; 30/30 intact pass, permissive fail, restored pass |
| AC7 tools | `python3 -m pytest -q tools` | 1; 763 passed, only declared baseline failure |
| AC7 Python | `PYTHONPATH=src python3 -m pytest -q tests` | 0; 551 passed |
| AC7 Node | `node scripts/check.mjs all` | 0; runtime 340, RAI 18, policy 3, preflight PASS |
| Landed board review | `python3 -m pytest -q tools/live/test_project_materialization.py` | 0; 12 passed |
| Original JC R1 | `python3 docs/evidence/brd-83-jc-e08c5c5e/original-probe.py` | 0; all three invalid paths refuse, CLI exit 1 |
| Prefix JC R1 | `python3 docs/evidence/brd-83-jc-e08c5c5e/prefix-probe.py` | 0; both prefixed paths refuse, CLI exit 1 |
| Whitespace | `git diff --check` | 0 |

Import digests:
- release_admission.py: `fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b`
- test_release_admission.py: `e8000ad29d07d6a6064a7f4982b760ca957376e9d518991b8c8497a2954e5e4e`

`custody-and-compatibility.log` retains digest, original-test and AST checks. `admit`, `biu_from_body`, both disposition functions and `project_status_from_issue` are AST-identical to the import. Native receipt fallback is exercised intact and deliberately disabled by the negative-control harness.

The sole tools failure is `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`: expected `gpt-6-astra`, observed `gpt-5.6-terra`. This is the exact non-hermetic debt named by the release authority; that file is unchanged. It is not hidden or counted as passing.

The two original JC probes were extracted from `5edbfd13f4debb7520c091bdff891753ff535f8c` and `78782654ba483bcbaaa5c30515de0a36895f81fa` and rerun byte-for-byte. The producer's copy of the first probe differs only in repository-root derivation; both that copy and the original pass. `original-probe-reruns.json` records source and commands.

## Findings and preserved progress

No blocking finding on the exact candidate. Prior R1 is closed: `tools/live/release_admission.py:224–234` requires a full allowed prefix, preserving canonical paths, bare Wave 1 filenames and supported repository blob URLs. Whole-CLI and unit controls restore the rejected suffix-only behavior and fail. The original wrong-directory/stamped/traversal probes continue to refuse. Prior R2 remains closed: explicit-release-point and invalid-outcome controls fail under their permissive variants. All previous evidence is retained.

The offline fixture uses a temporary origin, a stale clone and fake gh: newly landed records are read from the release commit without updating working-tree files; working-tree-only and local-HEAD-only records refuse; ARP-01, FDH-01 and WO-220202 work from body and release comments. The candidate fetches remote-tracking release points, pins the resolved commit, and uses git show; fetch failure is explicitly reported while retaining local-ref behavior. Repository selection is override, script checkout, then cwd; no hard-coded shared checkout remains.

Fresh read-only `gh issue view` checks for #80/#81 confirm neither body nor selected release record resolves an assessment pointer; both have native READY receipts and still need the fallback. No directory discovery was added. This limitation is explicitly anticipated in the retained readiness assessment and does not widen this assignment.

## Separate review of landed 62b85e0 / aa2b263

No blocking finding against Issue #83 AC2/AC4. Reviewed their diffs and current implementation:
- `src/github/authority.mjs:3–28`: broad attempt classification and strict single-marker acceptance are separate; allowed signals remain role/state bound.
- `src/runtime/dispatcher.mjs:168–185`: ordinary Director prose becomes NON_RESULT_COMMENT; attempted malformed results remain INVALID_RESULT_COMMENT; repository, invocation, time and worker identity gates remain.
- `test/dispatcher.test.mjs:1213–1284`: ordinary prose, unknown invocation, wrong identity, malformed/duplicate directives are covered by the passing runtime suite.
- `src/runtime/dispatcher.mjs:10–20`: SWF-19 merge/no-PR instructions remain prompt enforcement, as disclosed; this review does not assert removal of GitHub PR capability.
- `tools/live/project_materialization.py:93–126`: requires a complete board connection with matching total count and no next page; status vocabulary at lines 37–41 is preserved. The 12 materialization tests pass.

This is an independent review of the landed changes, not a claim that GitHub's live add-path fault or live gate switch-over has been repaired.

## Publication and lifecycle custody

Only this evidence directory is added by the verifier. Producer implementation remains unchanged. Publish this evidence on `b-disp/3d782e21-c66d-4cb4-9810-72e0ccebbfc2`; the terminal Issue comment records its exact commit and remote read-back. The accepted implementation SHA remains the producer SHA above.

No PR, baseline push, Project mutation, live gate switch, service change or other-repository change. Runtime-managed candidate/verifier resources remain in BIU custody for SWF-19 merge closure and runtime cleanup; do not remove the active managed worktree. Landing and subsequent authorized operational action belong to closure/Director authority.
