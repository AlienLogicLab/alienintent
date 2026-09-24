# Independent FDH-91 verification — JC

Invocation: `AlienLogicLab/alienintent#91:VERIFIER:b0ced174-5d5b-495b-a1d5-a57712ecab58`.
Reviewed candidate: `8cb63ffb1b5948980ef4ad3698f916049f6f430d`, remote branch
`b-disp/b0bf79df-c3a3-476b-87a1-062c087f6f54`.
Admission baseline: `669e5f1cf8e759e1b88beacd194650ab0f6a88d8`.
Verifier branch: `b-disp/894c4d71-2b8b-45c0-bdb9-448f26463cd8`.
Identity verified: Git JC <jc-github@factorychecks.com>; GitHub jc-worker.

## Authority and review

Reconstructed from Issue #91 body, contract `docs/work-units/wave2/FDH-91.md`,
release comment https://github.com/AlienLogicLab/alienintent/issues/91#issuecomment-5812990253,
and producer comment https://github.com/AlienLogicLab/alienintent/issues/91#issuecomment-5813106199.
Fetched the published candidate and fast-forwarded this separate runtime-owned verifier
worktree from the admission baseline to its exact SHA before testing. Remote readback
confirmed the candidate SHA and baseline main SHA. Initial worktree was clean.

Reviewed the entire baseline-to-candidate diff and the installer, adapter call ordering,
exception handling, and new test assertions. Docs require an absolute PATH, explain why,
and name gh, python3, git and provider CLIs. Installer changes only the new-file comment
block, expands HOME at install time, preserves existing env bytes and metadata, and calls
only daemon-reload. The adapter checks gh resolution before GitHub reads and propagates
SourceUnavailable through the existing unavailable projection and host failure record.
No predicate, idle reason, launch behavior or live configuration changes were introduced.
No blocking findings.

## Fresh checks

All commands were run through `rtk proxy`. Full outputs are retained beside this report.
The controls script was copied from the candidate with only the evidence destination
changed; after execution its output suffix was changed from .log to .txt to retain logs
under the repository ignore policy. Trailing whitespace in retained output was normalized for diff hygiene. Each control output records its own pytest exit code;
the script overall exit alone is not a test verdict.

| Command / check | Result | Exit |
| --- | --- | --- |
| `bash docs/evidence/fdh-91/verifier-jc/controls.sh`: docs, each of 0eda915 and 669e5f1 + candidate tests | 2 failed each, required PATH assertion | 1 each |
| same: new env seed, each baseline | 1 failed each, missing PATH comment | 1 each |
| same: missing gh, each baseline | 2 failed each, missing searched PATH diagnostic | 1 each |
| same: preservation and fake-gh guards, each baseline | 2 passed each | 0 each |
| same: candidate with require_gh call disabled | 2 failed, missing searched PATH diagnostic | 1 |
| same: candidate new criteria 1–4 cases | 7 passed | 0 |
| same: complete adapter, host and docs suites | 222 passed | 0 |
| `node scripts/check.mjs all` | runtime 340/340; preflight PASS; RAI 18/18; policy 3/3 | 0 |
| `python3 -m pytest -q -p no:cacheprovider -rfE tools`, candidate | 781 passed, 1 failed | 1 |
| same command, detached temporary worktree at 669e5f1 | 774 passed, 1 failed | 1 |

Both full Python runs fail only at the pre-dispositioned non-hermetic
`tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`:
observed model gpt-5.6-terra versus expected gpt-6-astra. That file and configuration were
not modified. The baseline scratch worktree was removed after the run. Controls scratch
trees were removed by their trap. The seven added tests account for the pass-count delta.

## Verdict and disposition

ACCEPT the exact producer candidate above: criteria 1–6 satisfied with the documented
criterion-6 baseline exception. This verifier commit adds evidence only; it does not alter
the candidate implementation. Publish this evidence on the verifier branch and retain it
for runtime-managed BIU closure. No PR, baseline push, live env edit, host install or restart.
SWF-19 landing and branch/worktree cleanup remain the lifecycle closure action; the direct
invocation prohibits pushing the baseline branch. Runtime-owned verifier state remains
retained pending that closure, not a manually abandoned temporary worktree.
