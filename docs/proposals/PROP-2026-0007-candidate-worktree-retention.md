---
proposal_id: PROP-2026-0007
title: Candidate Worktree Retention — local worktree as operational cache
submitted_by: coordinator
submitted_at: 2026-09-20
proposal_type: operational_policy
authority_level: unresolved
status: submitted
---

# Candidate Worktree Retention

## Intent

Define when a local candidate worktree stops being required evidence, so routine cleanup can remove operational cache without ever removing the only copy of a candidate.

## Motivating evidence

The [worktree retention audit](../evidence/2026-09-20-worktree-retention-audit.md) found 45 retained worktrees. 25 were removed as landed-in-`main` or coordinator scratch. **17 remain solely because their candidate is published to `origin` but not yet landed**, and no rule says whether remote publication satisfies retention. They are retained pending this decision.

## Proposed rule

A local candidate worktree is **not itself required evidence** once **all** of the following hold:

1. the exact candidate identity is known;
2. the candidate commit/artifact is durably published to a remote/repository location;
3. that identity is independently retrievable;
4. read-back confirms the published identity/content;
5. no active invocation uses the worktree;
6. no uncommitted unique content exists;
7. no explicit BIU or evidence policy requires local retention.

When all seven hold, the local worktree is **operational cache** and may be removed as routine cleanup.

## What the rule does not do

- It does not weaken candidate custody. Conditions 1–4 are the same identity-and-read-back obligations SF-REQ-007 already requires before VERIFY; this rule *consumes* that proof rather than relaxing it.
- It does not authorize removing a worktree whose content exists nowhere else. Failing any condition means retention.
- It does not change retention of evidence objects, trajectories or accepted results — only the local working copy.
- It does not apply to the two sole-copy PY-04 worktrees (`5d8fe09`, `62cd4f7`), whose candidates are reachable from **no** remote ref. Those remain retained until their unique content is separately made durable or explicitly discarded by authority.

## Application if approved

The 17 published-but-unlanded worktrees become removable by routine cleanup. Until approval they stay retained; this proposal changes nothing on its own.

## Relationship to existing authority

- **SF-REQ-007 candidate custody** — supplies conditions 1–4; this rule states when that proof makes the local copy redundant.
- **Architecture Authority §26 evidence retention** — local-first with configurable retention; this narrows "what is evidence" for one artifact class.
- **PY-06 invocation runtime** — owns workspace lifecycle and cleanup in canonical Python.
- No new Product Requirement is proposed. If approved, the smallest durable form is a decision record plus a line in `docs/operations.md`.

## Open question for the Founder

Does remote publication with confirmed read-back satisfy retention for a local candidate worktree, or must the local copy be retained for some period independent of remote durability?
