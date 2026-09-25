# AlienIntent agent instructions

Follow the [governing directive](docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md).
Direct user instructions take priority. Use the [work packet template](docs/templates/work-packet.md)
and [operator guidance](docs/operations/forward-momentum.md).

Classify working changes by authority and provenance. Known authorized work may
proceed; investigate unexplained changes and resolve actual conflicts. Preserve
baseline, identity, credential and publication boundaries. Do not infer unseen
concurrent actors or treat a nonempty Git status as an automatic admission failure.

Repository-changing agent work must not edit the shared main checkout directly. It
must run in an isolated worktree or workspace with one durable mutation owner,
coordinated by the Factory Director. Reviewers use read-only state or separate
isolated state. Conflicting ownership refuses mutation before any file change.

Continue authorized edits, tests, independent review, repairs and meaningful local
commits without routine confirmation. Stop at a concrete authority gap, conflicting
baseline, destructive action or unavailable external prerequisite. A local commit
does not authorize publication or live operation.

**Candidate publication is required before VERIFY.** A PRODUCER must push its
candidate branch to the configured remote before signalling `RESULT=VERIFY`, and
must state the exact branch and commit SHA in its result comment. A verifier is a
fresh, independent invocation in its own worktree: it can only review what it can
both identify and retrieve. A candidate that exists solely as a local commit, or
whose identity is not recorded on the Issue, is not verifiable and must not be
advanced.

Publishing a candidate branch is part of completing IMPLEMENT. It is not
publication in the release sense and does not authorize merge, deployment, live
operation, or any change to a protected branch. Those remain separately
authorized.

**VERIFY accumulates feature regressions.** Before a VERIFIER process is allowed
to spend model cognition, the invocation runtime runs every registered
feature-regression pack applicable to the candidate's changed paths via
`tools/verification/run_feature_regressions.py`. Failure prevents verifier
launch. A verifier verdict is inadmissible unless the exact candidate carries a
valid passing `.alienintent/feature-regressions.json` receipt. Do not delete,
weaken, bypass, or omit an applicable regression pack to make a candidate pass;
change or supersede a regression only under the same authority that owns the
feature behavior it protects.

Every repository-changing task also has a closure obligation, including work
outside the BIU lifecycle. Before declaring such a task complete, validate and
disposition its temporary branch/worktree as LANDED, DISCARDED, or PARKED with a
durable blocker record. The actor who creates it owns closure; “commit created,
not pushed” is not a stopping point. For bounded non-BIU docs/evidence/research/
maintenance tasks whose authorized disposition is LAND, continue through
validate → integrate to the canonical target → push remote → verify remote →
clean temporary state. Do not stop at “committed locally, not pushed”; if push
authority is genuinely missing, PARK the work with that blocker recorded.
Factory implementation/verifier candidate workers remain governed by BIU
candidate/closure policy and must not bypass it by pushing directly to `main`.
After landing or discard, remove temporary worktrees/branches. Create isolation
only when needed, and reconcile temporary branches/worktrees from the same actor
before starting another isolated non-BIU task. Existing BIU closure policy and
runtime-managed `b-disp/<uuid>` ownership/retention rules remain authoritative.

Prefix shell commands with `rtk`; use `rtk proxy` for unfiltered output.
RAI remains unwired. Keep installation secrets and operational state outside the
repository. Preserve compatibility markers and persisted resource identities.
