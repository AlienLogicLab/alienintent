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
