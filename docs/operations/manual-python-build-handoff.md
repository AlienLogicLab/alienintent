# Hand-fed Python build period and cleanup

**Status:** operating plan for the interval after issue 125 finishes and before Python runs its own full work cycle. This document does not stop a service or authorize deletion of an active object.

## Start boundary

1. Let issue 125 finish through the existing Node factory. Read back its actual completed state, exact accepted revision, landing, Project state, pending effects, active claims and any retained candidate. A label alone is insufficient.
2. The separate shutdown owner stops the Node factory and its managed background services. Read back that no Node writer or worker is still able to dispatch AlienIntent work, and preserve a recoverable record of unsettled effects. Do not launch Python as a second writer for the same work.
3. Pin the repository revision and the first **Founder-approved design**. After that, obtain a fresh Agent Ready assessment of the exact work-unit text and release only a READY result through the normal admission checks. Hand-fed work stays at one implementation unit at a time until the new factory proves its own control.

## One unit from assignment to completion

| Owner | Action and proof |
|---|---|
| Readiness check | Assess the exact work-unit text. Record the native assessment and its input fingerprint. A changed work unit needs a new assessment. |
| Claude | Create a separate working directory and candidate branch at the pinned revision, with one named owner and bounded time, disk and process budget. Implement only the assessed work, record changed files and checks, publish the candidate, and give its exact branch and revision. |
| Codex reviewer | A new Codex instance retrieves the exact published revision into a fresh, separate review directory. It checks source intent, approved design, domain responsibilities, inward dependency direction, Python practices, duplicated mechanisms, unnecessary complexity, resource lifetime, secrets, negative tests and observed behavior. It records findings and independent evidence. It does not edit the candidate or close the work. |
| Repair | Claude addresses specific findings on the same bounded task. Preserve previously passing behavior and evidence, publish a new revision and request a fresh Codex verdict. |
| Codex closure owner | A **different new Codex instance**, with a separate directory and identity, consumes the independent review verdict. It confirms the accepted revision is still published and no competing claim or unknown effect exists, lands exactly that content, runs required checks on the landed result, verifies the actual product outcome, and only then moves the item to completed. It records revisions and external readbacks. It cannot review its own closure change into acceptance; a material change returns to Claude and a new reviewer. |
| Cleanup owner | After closure and required retention, prove all processes have ended, preserve evidence, remove the temporary review and implementation directories through the repository's supported worktree commands, remove only eligible branches, and record what remains. A rejected or interrupted unit is retained with a named owner and expiry or explicit blocker. |

Each new temporary directory, branch, process, journal and evidence file gets an owner, maximum size or duration, retention rule, cleanup trigger, crash-recovery behavior and response when storage fills. Routine dispatch must not scan or replay the whole old history.

## Existing leftovers: separate inventory and controlled cleanup

The read-only count on 2026-09-29 was **41 registered working directories** and **346 local branches**, of which **312** used the old factory branch naming pattern. These are inventory totals, not deletion candidates. Issue 125 and other pending work may still own some of them.

After issue 125 and shutdown are read back, produce a machine-readable inventory joining each directory and branch to its work item, claim, candidate, remote reference, accepted revision, running process, uncommitted files, pending effect and retention rule. Sort each entry into active, evidence-retained, abandoned but recoverable, or safely removable. Unknown ownership stays retained. Review the proposed removals and capture a recovery reference before any deletion.

Remove only entries proven to have no active owner or needed evidence, no uncommitted unique content, no pending or unknown effect, and no required candidate reference. Use normal repository removal for registered working directories, then prune stale registration; delete local or remote branches only after exact reachability and custody checks. Recount and retain a before/after receipt. Do not use a wildcard branch deletion or delete a directory just because it looks old.

The factory itself must later automate this same ownership and cleanup rule for every new unit, including cancellation, failed verification, crash recovery and successful closure. The backlog cleanup is a finite maintenance task; automatic cleanup is a continuing product requirement.
