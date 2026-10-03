# Handoff for unit 6c-1 (work item 5befff2f-a0dd-4cea-9556-54c33ed86c1b)

Attached to the assessed packet `docs/work-units/python/work-context-package.md` at
`85f0b4e3e508c13466a432cdc9bde7950e2b2685` (sha256 29bf6e6b…), assessment
`readiness/5befff2f-a0dd-4cea-9556-54c33ed86c1b/c646d602-8f72-4d79-ad7e-d3b2f4032731/raw` (READY).
Binding on both the PRODUCER and the VERIFIER. The packet text is not changed.

## 1. Error-code clarification (Founder, 2026-10-03)

Section 2, hold step 8, groups "no candidate in the state" with `DIGEST_MISMATCH`.
Follow the REVIEWER's mapping (independent-review-83509db.md, hold table): a missing record is `MISSING_RECORD`.
Step 8 is therefore read as:

| VERIFIER case | Hold reason |
|---|---|
| no candidate in the coordinator state | `MISSING_RECORD` (detail names the candidate) |
| `--candidate` locator differs from the state candidate's locator | `DIGEST_MISMATCH` |
| no self-review record for that candidate | `MISSING_RECORD` |

Acceptance check 3 covers only the mismatch; the no-candidate case is tested as `MISSING_RECORD`.
The VERIFIER rejects a candidate that returns `DIGEST_MISMATCH` for a missing candidate.

## 2. The important acceptance checks (Founder, 2026-10-03)

- **Worker environment.** `work context` runs with only the worker's environment: the read-only worker profile,
  `ALIENINTENT_PROJECT_CONFIGURATION` and `ALIENINTENT_PROJECT`, and the command line given in `context_command`.
- **Read-only, including WAL.** The read-only open uses SQLite `mode=ro`. Test it on a database in WAL mode with its
  `-wal` and `-shm` files present, and show that the database bytes are unchanged after assembly.
- **VERIFIER isolation.** The planted-marker test: a marker in the PRODUCER's transcript, invocation output and
  journal never appears in the VERIFIER's package. The self-review appears only under `producer_self_review` with its
  fixed label, never in `findings`.

## 3. Assessment notes passed on

- Repeatable output: two assemblies with unchanged records are byte-identical, including the executable path and the
  git output.
- Self-review lookup: the record key uses the candidate digest, the VERIFIER compares by locator. Take both from the
  same candidate value in the coordinator state.
- The HoldReason values used already exist (`context_assembly/domain/reconstruction.py`). No new reason.
- Test fixtures for the diff need a fresh candidate clone.
- Stay inside `authorized_scope`; anything outside is a stop condition, reported, not done.
- Accepted limit: the read-only profile protects only this API. Real isolation is unit 6c-2.

## 4. Revision 4b (Founder re-approval, 2026-10-03)

Re-approved packet: revision 4b at packets `5b25c8390a9fcf672ec6bc6a1ba85547685a8186` (sha256 544be3fe…),
assessment `readiness/5befff2f-a0dd-4cea-9556-54c33ed86c1b/ee1d9eba-9299-41ed-9d13-36767f4c7170/raw` (READY).
Sections 1-3 above still apply.

- **Repair only.** The repair on candidate `4580d5b` changes only the attempt check (section 2 step 5) and its tests
  (acceptance checks 4 and 7). The VERIFIER confirms the repair diff stays there and rechecks only it, plus the
  three key checks of section 2. The round 1 verdict is kept.
- **Later calls stay bound to the approved instructions, not merely the same launch.** Every call, including the
  running worker's own `context_command`, re-reads the work item row and checks the READY assessment of its pointer
  (step 3) and the release record's evidence pointer commit, assessment attempt and contract digest against it
  (step 4). The release record is create-only and `work assess` refuses pointer moves after authorization. Prove it
  with one test in the running-launch fixture (after `commit_with_effect` and `claim_effect`): when the row's pointer
  or contract no longer matches the release record, the running worker's own call is held (`DIGEST_MISMATCH`, or
  `MISSING_RECORD` for the assessment), never given a package for other instructions.
- **Carried into unit 6c-2 (not this unit).** The `work context` command line has no contract fingerprint, so a
  worker's own call does not compare against the fingerprint of the invocation it was launched with. Unit 6c-2 must
  close this explicitly: the delivered `context_command` carries the launched invocation's contract digest and the
  call checks it (step 5 `DIGEST_MISMATCH`), with a test.
