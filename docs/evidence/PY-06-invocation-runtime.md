# PY-06 invocation-runtime executable evidence

This record retains observable engineering facts for the PY-06 repair cycle.
It contains no provider credentials, private reasoning, or raw remote URLs.

## Local executable checks

- `python3 -m pytest -q`: 107 passed.
- `python3 tools/fitness/check_architecture.py --root src/alienintent`: PASS.
- `npm test`: 310 Node tests passed, exit 0.
- The `CliWorkerProvider` adapter invoked `codex exec --ephemeral --json
  --sandbox read-only 'Reply exactly PY06_PROVIDER_SMOKE'`: adapter outcome
  `success`, exit status 0, and confirmed quiescence. The adapter did not
  report token or monetary cost, so both are retained as unknown, never zero.

## Runtime proof retained by tests

- Published source revisions are read back from a fresh clone before custody is
  admitted; unpublished candidates are rejected.
- Grant target, expiry and revocation are enforced; missing hard provider
  dimensions are ineligible and unreported token/monetary cost stays unknown.
- Timeout and live cancellation use real child processes. Unknown process
  identity is `unresolved-recovery`, not asserted quiescence.
- Producer retries wait for exponential, jittered eligibility and record the
  next event. Verifiers retrieve immutable candidates into their own fresh
  workspace, reserve only global capacity, and retain separate provenance.
- Cancellation fences the live child, releases its reservation after quiescence,
  and leaves owned-workspace cleanup to the invocation runner.
- Git diagnostics and candidate evidence redact remote URL userinfo.

Candidate branch, immutable commit, and remote read-back evidence are recorded
in the producer's exact invocation comment after publication.
