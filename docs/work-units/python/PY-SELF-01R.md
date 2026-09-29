# Python self-building 01R — read the exact saved work contract

**Status:** Candidate reader task after fixed-contract publication. Founder design review and a new Agent Ready assessment of this exact packet are pending. No PRODUCER has been released.
**Source:** The self-building plan's handoff from assessed preparation to a real queue. The independent review of [the larger publication proposal](PY-SELF-01.md) found that the current reader ignores the stated contract version.
**Starting code:** `src/alienintent/composition/sandbox_run_profile.py`, `src/alienintent/execution_coordination/adapters/github_repository_api.py`, and `tests/composition/test_sandbox_run_profile.py`. Pin the actual `main` commit when assigning the work; the observed starting revision during design was `734d65bb5b9ef46c69fd22d1be7756188a3dc083`.

## One result

For a Project entry already marked READY, the Python reader must retrieve the task contract from the exact repository commit named in that entry. It refuses an entry without a valid fixed commit identity. A later change to the default branch must not silently change the contract it imports. This unit reads existing records; it creates no Issues, Project entries, assessments or workers and changes no external state.

## Input and behavior

- Keep the existing line-based descriptor fields `biu`, `contract`, `readiness_digest` and `depends_on`. Add required `contract_revision`: exactly 40 hexadecimal characters naming a Git commit in the configured repository. Accept uppercase hex as input only if it is normalized consistently to lowercase. A branch name, tag, empty value or arbitrary URL is refused.
- Reject a missing or repeated `contract_revision`. Reject repeated instances of any other recognized descriptor field when values could conflict; silently taking the last value is unsafe. Unknown lines may retain current handling. Report a typed `BacklogRejected` without credentials or raw response bodies.
- Carry the revision from the parsed descriptor through the Project snapshot to the existing contract reader. Fetch with `GitHubRepositoryApi.contents(path, ref=revision)`; this method already supports an exact reference. Do not fetch the default branch as a fallback on failure. Preserve the existing checks for work identity and dependency agreement and the existing readiness digest check at release.
- Key any in-memory contract cache by both path and revision. Clear or bound it per snapshot so repeated reads do not retain an ever-growing set of old versions. Do not introduce new durable storage or a second source of contract truth.
- Keep this change inside the existing composition and its recorded transport/tests. Update recorded READY fixtures to include an exact commit reference and to answer the versioned repository request. Do not change generic GitHub authentication, scheduling, release authorization, model assignments or Project pagination in this unit.
## Observable checks

1. Given different bytes at the named commit and the default branch for the same path, import the contract at the named commit. The recorded transport must prove the exact requested repository, path and `ref` value. If the exact reference is unavailable, import refuses; no default-branch request follows.
2. Missing, repeated or malformed `contract_revision` refuses before a contract fetch. A repeated work identity, contract path, digest or dependency field must not be silently overwritten.
3. Two entries naming the same path at different commits cannot receive one another's cached contract. A refreshed snapshot has a bounded cache. Existing identity, dependency and digest mismatch tests continue to refuse the wrong work.
4. The normal six-task recorded run still imports and progresses once its fixtures name fixed commits. No live GitHub write or worker launch is needed to prove this unit. Run the focused composition tests and the applicable registered feature regressions.

## Boundaries and evidence

The PRODUCER may edit the reader composition, narrow recorded transport fixtures and their tests. Do not change this assessed packet during implementation. If a change outside that boundary is required, report the exact dependency for design review; do not broaden this task into publication, assessment freshness, authorization or the 50-entry Project reader defect. The existing Project limit remains a separately recorded defect and must not be represented as solved.

Use an isolated working directory based on the assigned commit. Publish the exact candidate branch and revision with test results and any cache-growth measurement. A separate REVIEWER instance retrieves that revision and checks the exact-reference behavior, refusal cases, resource bounds, Python quality, duplicated code, and relevant known agent-error patterns. A different CLOSURE instance acts only after an accepted review and proves the accepted change on its final repository revision. Role names do not choose models; assignments come from the separate role-configuration source.

No new temporary object is needed beyond the bounded candidate and review directories. Their owners retain necessary evidence and remove them when closure or a recorded cancellation permits. A repair preserves previously passing checks and records any superseded evidence.
