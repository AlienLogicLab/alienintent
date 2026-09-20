# Candidate worktree retention — SWF-30

Date: 2026-09-20. Status: **Founder decision — binding and durable**.
Source: direct Founder instruction approving [PROP-2026-0007](../proposals/PROP-2026-0007-candidate-worktree-retention.md) with one clarification.
Applied evidence: [worktree retention audit](../evidence/2026-09-20-worktree-retention-audit.md).

## The rule

A local candidate worktree is **not itself required evidence** once **all** of the following hold:

1. the exact candidate identity is known;
2. the candidate commit/artifact is **durably published** to a remote/repository location;
3. that identity is independently retrievable;
4. read-back confirms the published identity/content;
5. no active invocation uses the worktree;
6. no uncommitted unique content exists;
7. no explicit BIU or evidence policy requires local retention.

When all seven hold the local worktree is **operational cache** and may be removed as routine cleanup.

### Founder clarification to condition 2

> "Durably published" means the candidate remains reachable through a remote reference or other
> repository object whose retention is at least as strong as the applicable evidence-retention
> obligation. A transient remote branch that is about to be deleted does not qualify merely
> because the commit currently exists on the remote.

Publication is therefore a statement about **continuing reachability**, not about a momentary
`git push` having succeeded. A candidate whose only remote reference is scheduled for deletion —
by an auto-delete-on-merge setting, a cleanup job, a retention window shorter than the evidence
obligation, or an operator intending to prune it — is **not** durably published, and its local
worktree remains required evidence.

This composes with the existing domain rule that a **Candidate is an immutable artifact identity,
not a mutable branch name** (`docs/architecture/pre-python-gate/domain-model.md`). The branch is
only the mechanism that keeps the identity reachable. Removing the local worktree while deleting
the remote branch that made it retrievable would satisfy neither condition 2 nor 3.

## What the rule does not do

- It does **not** weaken [SF-REQ-007](alienintent-software-factory-plan.md). Conditions 1–4 are the
  custody proof SF-REQ-007 already requires before VERIFY; this rule consumes that proof, it does
  not relax it.
- It does **not** authorize deleting evidence objects, trajectories or accepted results. Only the
  local working copy is in scope.
- It does **not** authorize deleting the only durable copy of anything. Failing any condition means
  retention.
- The two sole-copy PY-04 worktrees (`5d8fe096`, `62cd4f70`) are reachable from **no** remote ref and
  are excluded entirely. They remain retained until their unique content is separately made durable
  or explicitly discarded by authority ([SWF-22](2026-09-20-py04-custody-transfer.md)).

## Canonicalization — amendment, not a new requirement

Amendment was preferred and is adopted. **SF-REQ-007 candidate custody is the canonical owner** and
carries the rule as an amendment. No new Product Requirement is created.

| Candidate owner | Assessment |
|---|---|
| **SF-REQ-007 — candidate custody invariant** (#9, P0, Wave 1) | **Chosen.** It already owns "durably identifiable and retrievable by a fresh independent verifier". This rule is the converse of the same invariant: once that proof holds *durably*, the local copy is redundant. Same semantic, same owner. |
| Architecture Authority §26 — evidence retention | Not amended. §26 governs retention *policy* (local-first, configurable, immutable accepted evidence). It is not the place that decides whether a particular artifact is evidence at all; SF-REQ-007 defines what candidate custody consists of. §26 is cross-referenced, not rewritten. |
| A new SF-REQ | Rejected — it would duplicate SF-REQ-007's semantic and create two owners for one invariant, the failure mode SWF-28 corrected for SF-REQ-030/054. |

Unlike [SWF-29](2026-09-20-liveness-reconciliation.md), where amendment was rejected because a
Wave 2 obligation would have retrofitted running Wave 1 requirements, this rule **adds no new
implementation obligation to SF-REQ-007**. It narrows what cleanup may remove once the existing
custody proof already holds, so there is no retrofit ambiguity.

Implementation ownership is unchanged: **PY-06 invocation runtime** owns workspace lifecycle and
quiescence-checked cleanup in canonical Python. PY-06 is in flight and is **not** amended; this rule
and the related dirtiness-classification debt are planning input for work after its acceptance
([SWF-20](2026-09-20-wave1-closure-policy.md) forbids expanding a released BIU mid-cycle).

## Application

Applied once, on 2026-09-20, to the retained worktree population. Per-worktree dispositions, the
read-back evidence and the exact failed condition for every retention are recorded in the
[worktree retention audit](../evidence/2026-09-20-worktree-retention-audit.md). Remote references
were preserved: removing a local worktree never removed the branch that keeps its candidate
retrievable.

## Scope

No lifecycle state, Project state, BIU contract, Node source or FactoryChecks content is changed by
this decision. Nothing about the running PY-06 invocation is disturbed.
