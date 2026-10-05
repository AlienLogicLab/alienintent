# Work unit: correct the worker-boundary documentation to match main

**Label:** `WORKER-RUNTIME-DOC-CORRECTION` (a document label; permanent id `c5200bcd-b2d4-4789-a1cb-90b6336f3f54`).
**Status:** Draft revision 1 (work item `c5200bcd-b2d4-4789-a1cb-90b6336f3f54`, at CAPTURE) for independent review, 2026-10-05. Not approved, not assessed, not released.
**Position on the path:** the genuine work item for check 8(c2) of WORKER-CREDENTIAL-BOUNDARY (`7efccee9-13f0-4905-a0a1-e80bc2faa748`, its parent). The Founder decided on 2026-10-05: use the documentation mismatch the VERIFIER already found as real work, launched through the normal path, so the launched PRODUCER's `context_command` reads its bounded per-invocation export. Builds on `main` `723f162`.
**Roles:** one PRODUCER (a real launched worker session); one fresh VERIFIER on the exact candidate; CLOSURE through the normal launch path (landing is off, so it ends at a verified ready-to-land result; the merge to main is done separately).

## Contract

```json alienintent-contract
{
 "identity": "c5200bcd-b2d4-4789-a1cb-90b6336f3f54",
 "version": "revision-1",
 "intent": "Bring the WORKER-CREDENTIAL-BOUNDARY packet and its handoff into exact agreement with the implementation landed on main at 723f162: the worker clone uses --no-local with git's ownership exception given to upload-pack, the VERIFIER and CLOSURE fetch gives the same exception to upload-pack, and the worker HOME's safe.directory .gitconfig is stated to have no effect on any worker git operation. Documentation only.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: use the already-identified --no-local / stale .gitconfig documentation correction as the genuine work item for check 8(c2); keep the contract deliberately narrow.",
  "Founder 2026-10-05: no production-code changes; no workflow, authority, credential, context-export or landing changes; no unrelated documentation edits.",
  "Founder 2026-10-05: the App contents: write decision is not made by this unit; it follows 8(c2)."
 ],
 "authorized_scope": [
  "docs/work-units/python/worker-credential-boundary.md",
  "docs/work-units/python/worker-credential-boundary-handoff.md"
 ],
 "excluded_scope": [
  "any file outside the two authorized documents",
  "production code, tests and tools, including the docstrings in src/alienintent/composition/work_registry.py and src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "the review records in section 6 of the packet (history)",
  "any change to the packet's contract block",
  "workflow, authority, credential, context-export or landing changes"
 ],
 "dependencies": [],
 "required_capabilities": [
  "git"
 ],
 "budget_policy": {
  "maximum_attempts": 2
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 2 cycles",
 "completion_criteria": [
  "acceptance checks 1-3 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff against its starting revision is exactly the five replacements of section 2, nothing else"
 ],
 "required_evidence": [
  "VERIFIER verdict",
  "the launch's bounded export path <launch>/exports/<invocation>/context.json, kept for the Founder-run check 8(c2)"
 ],
 "non_goals": [
  "fixing the .gitconfig entry in code",
  "rewording any other part of the packet"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-credential-boundary.md",
  "docs/evidence/worker-credential-boundary/landing-2078b37.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "a text to replace is not found exactly once at the starting revision",
  "the implementation on main does not match a replacement text",
  "scope outside the two authorized documents"
 ]
}
```

## 1. Why

The VERIFIER of `156ef20` found that the packet still says the PRODUCER clone uses `--no-hardlinks`. The code on main (`src/alienintent/invocation_runtime/adapters/git_worktree.py`, `WorkerCloneAdapter.allocate`, `candidate_clone` and `_upload_pack`) uses `--no-local` for the clone and gives git's ownership exception to upload-pack for both the clone and the fetch, because `git -c safe.directory=...` on the worker's command line never reaches git's ownership check (live finding of check 8(e)). The worker HOME's `.gitconfig` (`prepare_worker_session` in `src/alienintent/composition/work_registry.py`) is still written, but no worker git operation depends on it, and its packets-clone entry names the working-tree path, which git does not match for that repository (git checks `<packets clone>/.git`).

## 2. The changes (exact; each "old" text occurs exactly once at the starting revision)

In `docs/work-units/python/worker-credential-boundary.md`:

1. Section 0.3. Old: `` `git clone --no-hardlinks <packets clone> <launch>/worker/producer-<c>` (reading the Founder-owned packets clone is harmless to the Founder)``
   New: `` `git clone -q --no-local --no-checkout --upload-pack='git -c safe.directory=<packets clone>/.git upload-pack' -- <packets clone> <launch>/worker/producer-<c>` (objects come through the transport as a pack, with no alternates or hardlinks; git's ownership exception for the one Founder-owned source is given to upload-pack itself, because `git -c safe.directory=...` on the worker's command line never reaches git's ownership check, live finding of check 8(e); reading the Founder-owned packets clone is harmless to the Founder)``
2. Section 0.5. Old: `` by `git init` and `git fetch <launch>/intake.git refs/intake/<c>`,``
   New: `` by `git init` and `git fetch -q --no-tags --upload-pack='git -c safe.directory=<launch>/intake.git upload-pack' -- <launch>/intake.git refs/intake/<c>`,``
3. Change 5. Old: ``holding only a `.gitconfig` whose only entries are `safe.directory` for the packets clone and the intake repository);``
   New: ``holding only a `.gitconfig` whose only entries are `safe.directory` for the packets clone and the intake repository; no worker git operation depends on it, because the clone and the fetch give their exception to upload-pack (sections 0.3 and 0.5), and its packets-clone entry names the working-tree path, which git does not match for that repository);``
4. Check 6. Old: ``The HOME holds exactly the `safe.directory`-only `.gitconfig`, recreated empty each launch.``
   New: ``The HOME holds exactly the `safe.directory`-only `.gitconfig` (on which no worker git operation depends, change 5), recreated empty each launch.``

In `docs/work-units/python/worker-credential-boundary-handoff.md`:

5. Old (two bullets, four lines):
   ```
   - Packet wording to correct at the next packet revision: section at worker-credential-boundary.md:150 still says
     `--no-hardlinks`; the code uses `--no-local` with the upload-pack exception.
   - Known, not fixed: prepare_home's `.gitconfig` names the packets clone without `/.git`. It is unused now that the
     clone carries its own exception.
   ```
   New:
   ```
   - Corrected by WORKER-RUNTIME-DOC-CORRECTION: sections 0.3 and 0.5 of the packet now give the clone's and the
     fetch's upload-pack exception, and `--no-local` replaces `--no-hardlinks`.
   - The worker HOME's `.gitconfig` (written by `prepare_worker_session`) has no effect on any worker git operation;
     the packet now says so. The code is unchanged.
   ```

Nothing else changes. The PRODUCER uses its `context_command` for any further fact.

## 3. Acceptance checks

1. **Exact diff.** `git diff <starting revision> <candidate>` touches only the two authorized files, and is exactly replacements 1-5. Catches an unrelated edit or a paraphrase.
2. **Agreement with main.** Each new text matches main's code: `WorkerCloneAdapter.allocate`, `candidate_clone` and `_upload_pack` in `git_worktree.py`, and `prepare_worker_session` in `work_registry.py`. Catches a correction that is itself wrong.
3. **Contract unchanged.** The packet's contract block and section 6 are byte-identical to the starting revision. Catches an edit to history or to the approved contract.

The launch itself is the evidence for check 8(c2) of the parent unit: the PRODUCER runs as `alienintent-worker`, its `context_command` reads `<launch>/exports/<invocation>/context.json`, and the Founder then runs the boundary proof with `--package` on that file. That proof, not this unit's VERIFIER, decides 8(c2).

## 4. Review record

**Revision 1 (2026-10-05).** First draft, from the Founder's decision of 2026-10-05.
