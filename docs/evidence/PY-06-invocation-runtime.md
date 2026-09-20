# PY-06 invocation-runtime executable evidence

This record retains observable engineering facts for the PY-06 repair cycle.
It contains no provider credentials, private reasoning, or raw remote URLs.

## Local executable checks

- `python3 -m pytest -q`: 103 passed.
- `python3 tools/fitness/check_architecture.py --root src/alienintent`: PASS.
- `npm test`: 310 Node tests passed, exit 0.
- `codex exec --ephemeral --json --sandbox read-only 'Reply with exactly
  PY06_PROVIDER_SMOKE.'`: exit 0; response `PY06_PROVIDER_SMOKE`; provider
  reported 21,039 input tokens, 9,984 cached input tokens, and 48 output tokens.

## Runtime proof retained by tests

- Published source revisions are read back from a fresh clone before custody is
  admitted; unpublished candidates are rejected.
- Grant target, expiry and revocation are enforced; missing hard provider
  dimensions are ineligible and unreported token/monetary cost stays unknown.
- Timeout and live cancellation use real child processes. Unknown process
  identity is `unresolved-recovery`, not asserted quiescence.
- Producer retries record attempts and next eligibility. Verifiers reserve only
  global capacity, own a separate workspace and provenance record, then clean
  and release their reservation.
- Git diagnostics and candidate evidence redact remote URL userinfo.

Candidate branch, immutable commit, and remote read-back evidence are recorded
in the producer's exact invocation comment after publication.
