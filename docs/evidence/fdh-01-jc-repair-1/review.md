# FDH-01 independent repair verification

Verdict: **ACCEPT** candidate `b0c66a72aaa799c865ffe759749395a2ddff0e6a`
on producer branch `b-disp/049ea6cb-8aff-49bb-a965-dad07ffad99a`.

Reviewer: JC (`jc-worker`), invocation
`AlienLogicLab/alienintent#89:VERIFIER:fd9c0f9a-bd8a-4363-9a79-f7c3bb2ca15d`.
This is fresh independent verification, not the prior producer or verifier invocation.

## Authority and custody

Authority was reconstructed from Issue #89, including its RELEASED record,
the FDH-01 contract, the prior rejection, the producer repair result, and the
Director's dispositions and subsequent clarification:

- [Release](https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5809045656).
- [F3/D1 disposition](https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5809931372).
- [Candidate](https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810043775).
- [Candidate-specific clarification](https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810060408).
- [Director's real CLI diagnostic](https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810085488).

Admission baseline: `70fa7148939dfcebbcef73d858f9f481869d7214`.
The initially clean runtime-managed JC worktree was fast-forwarded to the fetched
candidate. `git ls-remote` returned the exact candidate SHA on the producer branch.
Git identity: `JC <jc-github@factorychecks.com>`; GitHub identity: `jc-worker`.
Origin: `https://github.com/AlienLogicLab/alienintent.git`.

The contract hash is unchanged:
`01a0ab5961dd5877531c4527620c2f2b905763f454af7dbdefb5d29ba24187d1`.
Chat record sections 13–17 were read from the operator's existing file under
`/mnt/d/Projects/alienintent/docs/operations/`; its SHA-256 matches the documented
`8c35ff8b2eb023557271b07413114122b2db94f1ed664928d61cb7d132c613a0`.
The private operator record was not copied into the review branch.

## Findings and final dispositions

- **F1 closed.** An episode already exited at entry to `wait_for_change` returns
  `EPISODE_EXITED` without sleeping. The successor has a fresh identity. Crash-loop
  backoff, unknown-liveness waiting, and non-owner waiting remain covered and pass.
- **F2 closed.** Required-key containment rejects extended leases missing any of
  the six required keys. Reconcile, inspect and wait refuse safely; no duplicate
  launch or uncaught `KeyError` in the regression checks.
- **F3 closed under the Director's durable disposition.** The candidate never
  substitutes requested/configured model for observed model. Claude retains
  `modelUsage` evidence. Codex records null observed model with
  `NOT_EXPOSED_BY_PROVIDER`, explicitly accepted as equivalent by the Director.
  The Director's real-CLI diagnostic with a loopback provider is durable Issue
  evidence; this verifier did not independently rerun that diagnostic or call a
  paid provider. Separately, the local producer capture
  `/tmp/fdh89-codex-probe2.jsonl` was inspected and retained as `codex-capture.jsonl`.
  It contains four events, no model field, and measured token usage. Its hash is
  in `checks.json`. A fresh offline test feeds these captured bytes to the
  candidate parser and passes. This supplements the candidate's fake-executable
  tests; it does not claim that those tests originally exercised the real CLI.
- **D1 closed by Director sanction.** DONE or the exact escalation acknowledgement
  resolves the entry; processed inbox receipts do not, and a newer `at` needs a
  new acknowledgement. Relevant tests and negative controls pass. The Director
  explicitly owns the stale section-9 sentence update after landing. That wording
  is a tracked Director follow-up, not a pending sanction or rejection ground.

During review a literal-value probe exited 1 (`UNAVAILABLE_FROM_PROVIDER` versus
`NOT_EXPOSED_BY_PROVIDER`). The subsequent Issue refresh revealed the explicit
equivalence ruling; the probe is superseded by that authority, not hidden or
treated as a current defect. The same clarification dispositions the stale
section-9 wording. Neither changes runtime behavior.

## Fresh checks

All shell commands were prefixed `rtk proxy` (Git fetch/merge used `rtk git`).

| Command | Observed result |
|---|---|
| `python3 -m pytest -q tools/orchestration/test_factory_director_inputs.py tools/orchestration/test_factory_director_host.py tools/orchestration/test_factory_director_docs.py docs/evidence/fdh-01-jc/reproduce.py` | exit 0; 206 passed: 87 adapter, 78 host, 39 docs, 2 prior JC reproducers |
| `node scripts/check.mjs all` | exit 0; required canonical groups completed |
| `python3 -m pytest -q tests` | exit 0; 526 passed |
| `python3 -m pytest -q tools/orchestration tools/live` | exit 1; 317 passed, 1 declared baseline failure |
| `env PYTHONPATH=src python3 tools/evidence/fdh01_evidence.py --output /tmp/fdh89-jc-fd9c-negative-controls --invocation AlienLogicLab/alienintent#89:VERIFIER:fd9c0f9a-bd8a-4363-9a79-f7c3bb2ca15d` | exit 0; 35/35 controls discriminated, 105 observations, 35 fault applications; intact/fault/restored exit sets 0/1/0 |
| `python3 -m pytest -q docs/evidence/fdh-01-jc-repair-1/test_capture.py` | exit 0; 1 passed |
| `git diff --check 70fa714 HEAD` at candidate | exit 0 |
| `git diff --quiet 8da68f7 HEAD -- docs/evidence/fdh-01 tools/orchestration/test_director.py` | exit 0; earlier proof and declared debt unchanged |
| `git diff --quiet 6c38427 HEAD -- docs/evidence/fdh-01-jc` | exit 0; prior review retained unchanged |

The sole broad-suite failure is
`test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`:
it expects `gpt-6-astra` but reads `gpt-5.6-terra` from host configuration. The
release explicitly excludes this known non-hermetic baseline test from repair.
It was not changed. This is not an all-tests-green claim.

The negative controls include all seven criterion-2 source failures and the three
new repair controls. `checks.json` retains their test identities and results.
Raw logs/report are at `/tmp/fdh89-jc-fd9c-negative-controls` on the worker host.
The harness hardcodes Morty as its observation actor; those actor fields are not
JC attestations. This review and its summary identify the actual JC runner.

Criteria 1–4 pass their mapping, fail-closed, hold/inbox and continuity checks.
Criterion 5 passes fresh-session argv/isolation and the dispositioned model-evidence
requirement. Criterion 6 covers the runtime contract, pointer prompt and twelve-step
procedure against chat sections 13–17. The document suite also checks shell syntax.
The procedure has not been executed live. Criterion 7 passes the required suites.

Read-only audit: the adapter reads board/comments, runtime/configuration and
hold/inbox/pause sources; its writes are its projection and diagnostics only.
The shared Project reader change adds repository identity to a query/projection.
No new GitHub mutation, Issue transition, runtime-state or Node-config write was
found in the adapter path. The host's lease/history/output writes are intentional.
Prior-branch disposition remains documented in the producer execution record.

## Boundaries and closure

Review-only additions are under `docs/evidence/fdh-01-jc-repair-1/`. Candidate
implementation is unchanged. No PR, baseline push, merge, service action,
live proof or other-repository change was performed. No live board success is
claimed. Tokens/cost for this verifier invocation are UNKNOWN, not zero.

Review branch: `b-disp/a87c7bb5-148a-4f26-b23d-6d998f81d9d6`, owner JC for this
invocation. Disposition: **PARKED for authorized BIU closure**, with unique review
evidence atop the accepted candidate. The outstanding prerequisite is Director
landing/closure under SWF-19, including the Director-owned section-9 update.
Runtime-managed retention applies; this worker does not delete its active workspace.
The accepted implementation SHA is the producer SHA above, not the later review
evidence commit. Remote review-branch readback and the evidence SHA are recorded
in the single final Issue comment.
