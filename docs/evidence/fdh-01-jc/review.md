# FDH-01 independent verification — JC

Invocation: `AlienLogicLab/alienintent#89:VERIFIER:d40329ce-1fee-4807-b2f6-490fbde3da7a`.
Disposition: **REJECT**, localized repairs and Director decisions required.

## Authority and custody

Reconstructed from Issue #89 body, native READY receipt, RELEASED comment
<https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5809045656>,
and producer publication receipt
<https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5809820286>.
The release pins admission baseline `70fa7148939dfcebbcef73d858f9f481869d7214`.
Candidate branch `b-disp/b823a326-c2d8-46f2-9831-207832d4ae6f`, candidate SHA
`8da68f73303f1d6928a152cc322be756e718877c`; fetched and remote head read back equal.
JC's initially clean, runtime-managed worktree was fast-forwarded to that exact SHA.
Git identity JC / jc-github@factorychecks.com; GitHub API identity `jc-worker`.

Contract SHA-256 matches the native assessment:
`01a0ab5961dd5877531c4527620c2f2b905763f454af7dbdefb5d29ba24187d1`.
The operator chat source was read locally at the producer-recorded absolute path;
its SHA-256 matches `8c35ff8b2eb023557271b07413114122b2db94f1ed664928d61cb7d132c613a0`.
Sections 13–17 were compared directly; the private source was not copied into this review.

No implementation was changed. This branch adds review evidence only. No live proof,
installation, service changes, baseline push, PR, or changes to another repository.

## Findings

### F1 — medium: exit-before-wait delays mandatory immediate reconciliation

`tools/orchestration/factory_director_host.py:597` puts both an absent active lease
and an already-exited active episode through `sleep(interval)`. A finishes after
`reconcile()` returns but before `wait_for_change()` checks liveness: the host
requests a full default 60-second sleep, returning `INTERVAL_ELAPSED`, even though
it already knows A exited and control remains required. This contradicts FDH-01's
intent and chat section 13's immediate re-evaluation, and the live-proof step 5
claim that successor activation occurs within seconds.

Reproduction: `test_exit_before_wait_reconciles_without_interval_delay` below.
Observed `('INTERVAL_ELAPSED', [60])`; expected immediate `EPISODE_EXITED` and no sleep.
Repair must distinguish an observed exit from a genuinely idle host; retain normal
idle waiting, unknown-liveness refusal, and the crash-loop backoff.

### F2 — medium: incomplete realistic lease crashes instead of refusing

`tools/orchestration/factory_director_host.py:373` uses `set(value) < required`.
A normal generated lease contains additional metadata, so removing `pid` does not
make its keys a strict subset of `required`. The check passes and line 377 raises
uncaught `KeyError('pid')`. `reconcile()` and `inspect()` cannot produce the promised
`AMBIGUOUS_LEASE` refusal; under the supplied service the persistent malformed record
would repeatedly fail on restart. No duplicate launch was observed in this probe.

Reproduction: `test_missing_required_key_with_extra_metadata_refuses_without_crash`.
Repair must validate required-key containment independently of extra keys and retain
the lease without launching a successor. Cover missing required fields on realistic
extended records through both reconciliation and inspection.

### F3 — unresolved acceptance evidence: actual model for Codex

Scope 2 and criterion 5 require recording the model actually used. Launch history
records only `requested_model`; `codex_usage()` unconditionally returns
`observed_models: None` (line 323). Explicitly requesting a model is useful evidence
of intent but does not establish the model actually used. Existing launcher tests
prove argv and requested-model recording. They do not prove this part of criterion 5.
Obtain supported actual-model evidence or a durable Director disposition of this
acceptance gap; do not replace UNKNOWN with the configured model.

### D1 — Director decision pending, not a Founder exception

Runtime contract section 9 explicitly says the producer's DONE/acknowledgement
resolution rule for `limitEscalations` awaits Factory Director sanction. The producer
also asks for it on the Issue; no subsequent sanction was present at review. Resolve
this with a durable Director decision before acceptance and align tests/docs with it.
This review neither silently sanctions it nor invents Founder-only authority.

## Fresh verification

All shell commands were prefixed `rtk proxy`.

| Command | Observed result |
|---|---|
| `python3 -m pytest -q tools/orchestration/test_factory_director_inputs.py tools/orchestration/test_factory_director_host.py tools/orchestration/test_factory_director_docs.py` | exit 0; 194 passed (87 adapter, 68 host, 39 docs) |
| `node scripts/check.mjs all` | exit 0; runtime 340/340, preflight PASS, RAI 18/18, policy 3/3 |
| `python3 -m pytest -q tests` | exit 0; 526 passed |
| `python3 -m pytest -q tools/orchestration tools/live` | exit 1; 307 passed, 1 known baseline failure: `test_substantial_technical_analysis_routes_to_codex_primary` expects gpt-6-astra, reads gpt-5.6-terra; out of scope and unmodified |
| `env PYTHONPATH=src python3 tools/evidence/fdh01_evidence.py --output /tmp/fdh89-jc-negative-controls --invocation AlienLogicLab/alienintent#89:VERIFIER:d40329ce-1fee-4807-b2f6-490fbde3da7a` | exit 0; 32/32 controls discriminated, 96 observations, 32 fault applications; every intact/restored exit 0, every fault exit 1 |
| `python3 -m pytest -q docs/evidence/fdh-01-jc/reproduce.py` | exit 1; 2 independent regression tests failed, as detailed above |
| `git diff --check 70fa714 8da68f7` | exit 0 |
| `git diff --quiet 8da68f73303f1d6928a152cc322be756e718877c -- tools src config` | exit 0; reviewed implementation unchanged |

Initial environment attempts (`python`, absent; harness without `PYTHONPATH=src`,
import failure) exited 1 and are not counted as test outcomes. Corrected commands above
completed. The negative controls include all seven criterion-2 malformed/unavailable
sources; both normal and deliberately broken adapter tests ran. Condensed fresh
control evidence is in `negative-controls.json`; raw temporary logs and report are
at `/tmp/fdh89-jc-negative-controls` on the worker host. The harness hardcodes producer
actor metadata in its observation objects; those objects are not asserted to be JC
receipts here. The actual runner and invocation are recorded by this review.

Criteria 1–3 fixture mapping and failure discrimination pass. Criterion 4's tested
A-to-B sequence passes, but the untested main-loop boundary fails F1. Criterion 5
argv/isolation checks pass with the actual-model evidence gap F3. Criterion 6 document
coverage and shell parsing pass; the step 5 timing assertion is blocked by F1.
Criterion 7 required suites pass. Passing checks do not override the findings.

Read-only audit: adapter call paths use GraphQL queries and read source files; its
only writes are the configured projection/diagnostics. The shared materialization
module change adds repository identity to query/projection only; existing mutation
functions are not called by the adapter. Host writes lease/history/output as required;
no new GitHub write, Issue transition, runtime-state write or Node-config write was found.
Prior branch dispositions are retained in `fdh-01-execution.md`; review does not
invalidate the prior published evidence or permit unrelated baseline-debt repair.

## Repair and retention

Preserve the previously passing predicate, hold/inbox, continuity, isolation and
negative-control evidence. Repair F1/F2 and add the boundary tests to the maintained
host suite. Resolve F3 and D1 durably with the Director. Re-run relevant checks and
publish a new candidate SHA for a fresh independent review. No live proof is needed
or authorized to repair these offline gaps.

Tokens/cost for this verifier invocation: UNKNOWN (billing telemetry unavailable),
not zero. Live Project read-back and live installation/proof remain unperformed and
outside this verification grant.

Review branch: `b-disp/17987c5d-5a5c-44e4-bab5-ac5dd8e3bcdc`, owner JC for this invocation.
Disposition: PARKED for BIU repair/closure, containing this review evidence atop the
rejected producer candidate. Missing prerequisite: repaired, independently accepted
candidate and authorized lifecycle closure. Runtime-managed branch/worktree retention
applies; the worker does not manually delete its active dispatcher-owned workspace.
