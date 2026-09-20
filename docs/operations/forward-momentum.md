# Repository-state admission

Follow the [governing directive](../migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md).
Compare the baseline and observed changes with the authorized bounded work.
Known authorized edits, task packets and outputs can proceed while uncommitted.
Investigate unexplained work; resolve actual conflicts within authority.

Deterministic admission requires exact paths/content, observed status, authority
and staged-content evidence where applicable. A previous classification does not
cover new or unexpected bytes. Reclassify them before proceeding. Git identity,
GitHub identity, upstream and baseline protections remain required.

Continue through checks, independent review, in-scope repairs and meaningful local
commits without routine confirmation. Keep live actions and public delivery within
their authorized scope. For any genuine blocker, identify the concrete protected
resource, the plausible failure and the external action needed to proceed.

## Repository change closure

Every task that creates repository state has a disposition obligation, whether or
not it is a BIU. Creating a temporary branch or worktree creates a closure
obligation. A repository-changing task is not complete until its state is:

- **LANDED** — authorized content is validated and integrated into its target
  branch; its temporary worktree is removed, and its temporary branch is deleted
  when no longer needed.
- **DISCARDED** — no useful unique content remains; its temporary worktree and
  branch are removed.
- **PARKED** — only when missing authority or an unresolved dependency prevents
  landing. The durable record names the branch, owner, unique content, reason,
  missing authority/dependency, and next action.

The actor who creates a temporary branch/worktree owns its disposition before
declaring the task complete. For bounded documentation, evidence, research,
proposal, audit, or maintenance work, use **validate → land → remove worktree →
delete temporary branch**, unless a genuine authority/dependency blocker requires
PARKED. “Task analysis complete” is not completion while an unowned temporary
branch/worktree remains. Already-merged temporary branches are routine
housekeeping and should be deleted.

Create isolation only when concurrency, risk, or independent review requires it;
do not create branches/worktrees by habit. Before beginning another isolated
non-BIU task, reconcile temporary branches/worktrees created by the same actor.
Temporary branches are not durable state stores; disposition must be observable
from durable repository/project state rather than model conversation memory.
Repository mutation outside the BIU lifecycle remains subject to this closure
rule. For BIU work, existing BIU closure and source-control policy remains
authoritative and is not replaced by this rule. Runtime-managed `b-disp/<uuid>`
resources and their ownership metadata continue to follow the separate cleanup
and retention rules in [operations](../operations.md#worktrees-and-recovery); do
not treat them as manually owned temporary task branches.

### Post-cleanup validation follow-up — 2026-09-20

The post-cleanup validation concern was investigated and did not reproduce as a
product regression. The initial subprocess-test anomalies were transient or
environmental; no implementation or test-runner changes were made. Bounded
confirmation: `rtk proxy timeout 60s node scripts/check.mjs all` exited 0 in
17.4 seconds (runtime 310/310, preflight PASS, RAI 18/18, policy 2/2). No
remediation was required.

### PARKED — `origin/feat/rai-foundations`

- **Owner:** `netmarine` (commit author; no separate task owner is recorded).
- **Unique content:** commits `c8a676b` through `3c0b5f6`; RAI iteration/evidence
  primitives, tests, review records, and the RAI development-discipline document.
- **Reason:** this unique implementation is not in `main`; the branch's own design
  defers product automation, and current `main` says RAI remains unwired.
- **Missing authority/dependency:** no canonical Product Requirement, BIU, or
  work packet authorizing this source change was found in the repository. GitHub
  PR status could not be verified in this audit.
- **Next action:** the owner must identify or obtain the canonical authority and
  confirm any remote review state before deciding to land or discard. Do not
  create a requirement or BIU as part of this parked record.
