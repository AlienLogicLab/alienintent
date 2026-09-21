# POSTW1-SMOKE-000 — read-only orchestration smoke test

Bounded, read-only verification that the local Program Director can launch and capture a
fresh Codex session. This is infrastructure validation, not program work.

Task: read `docs/evidence/wave1-yield-snapshot.md` and report exactly three facts it states:

1. the number of executed Wave 1 BIUs;
2. the number of first-pass accepted BIUs;
3. one metric the document explicitly records as UNKNOWN.

Do not modify any file. Do not run git write commands. Do not interpret or draw conclusions.

Return a terminal report in exactly this form:

    BIUS=<n>
    FIRST_PASS=<n>
    UNKNOWN_EXAMPLE=<short phrase>
