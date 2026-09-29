# SF-REQ-057 producer proof — Issue #147

Invocation: `AlienLogicLab/alienintent#147:PRODUCER:502ac464-17ea-4a94-94e0-d5ccbc933f9a`.
Scope: `docs/work-units/SF-REQ-057.md`; isolated branch
`b-disp/5452beaf-e2ea-45ea-8fba-493cc7567f18`. Release baseline:
`b8cd375bdf2a9519e90d44641c317db610aa656b`. Worktree was clean at admission;
HEAD and fetched `origin/main` were `c74baf2699c5614b084d7c354290e0a5e148bf27`.

## Pinned source and backlog

- The complete 1,326 source bytes at
  `~/.local/state/alienintent/factory-director/inbox/founder-requirement-intake-durability-live-proof-20260929.json`
  hashed to SHA-256 `e0f3f2cfdb2468b4b42c155e32f8c2d4a86cbfff5cc7bbf5fec45a34a31f3792`.
  The source names title, requirement, all three acceptance strings, authority and P0.
- The old processed receipt has the correct artifact, revision, Issue, Project, item and
  P0 tuple, but no source digest or title/authority provenance binding. It was read only;
  no worker change to that operational file was made.
- `git fetch origin main` exited 0. `git merge-base --is-ancestor
  45891e43d7ff14253fe2c38a0af736b981135214 origin/main` exited 0.
  `git show 45891e43d7ff14253fe2c38a0af736b981135214:docs/decisions/alienintent-software-factory-plan.md`
  showed SF-REQ-057's exact requirement and three acceptance strings.
- Configured GitHub App read 136 complete Project items. Issue #147 appeared exactly once,
  item `PVTI_lADOEcrpC84Bj5i_zg9UCCU`, status IMPLEMENT, priority P0, repository
  `AlienLogicLab/alienintent`. The App's canonical remote comparison, artifact and Issue
  reads passed the deterministic migration preparation. Preparation preserved every old
  receipt field and added only `sourceSha256` and `provenance`; no receipt write followed.
- A read-only `AuthoritativeDirectorInputs.evaluate()` using the installed configuration
  returned `authoritative_state=True`, `pending_director_inbox=True`, and listed this exact
  entry in `unprocessedInboxEntries`. Its `inboxFailures` named the old receipt's absent
  materialization/provenance chain. This is the expected active migration state; it is not
  a DONE or installed-service result.

## Deterministic controls

`python3 -m pytest tools/orchestration/test_factory_director_inputs.py -q -k founder_receipt`
before the implementation exited 1: 10 expected failures and 1 pass. A DONE item could
clear forged digest, revision, Issue/item identity, priority and content receipts. The
external-read fault also cleared the old predicate. A migration test then failed with
`AttributeError` before its implementation.

After implementation, `python3 -m pytest tools/orchestration/test_factory_director_inputs.py -q`
exited 0: 134 passed. The fixture covers acknowledgement-only, all ten lifecycle states,
valid DONE, invalid source digest, revision, Issue, item, priority, title, authority,
requirement, acceptance, duplicate Project item, unpublished revision, missing artifact,
missing Issue, unavailable remote, repeatable interrupted migration and changed source
bytes. Invalid local receipt evidence remains pending with `inboxFailures`; unavailable
external provenance yields a non-authoritative projection and a named failure.

`python3 -m pytest tools/orchestration/test_factory_director_inputs.py
tools/orchestration/test_factory_director_host.py -q` exited 0: 216 passed.
`ruff check --select F --ignore F401` on the two changed Python files exited 0.

`python3 -m compileall -q tools/orchestration/factory_director_inputs.py` and
`git diff --check` exited 0. The implementation makes read-only GitHub App requests,
bounded by the existing transport timeout, and caps each Founder source/receipt read at
4 MiB. The inbox source, current receipt, credentials, Node runtime, installed service
and Project state remain under their existing owners. The Director owns atomic migration
of #147's operational receipt after its own readback. Candidate publication does not
claim that migration or Project DONE.
