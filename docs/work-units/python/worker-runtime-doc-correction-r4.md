# Work unit: correct the worker-boundary documentation to match main

**Label:** `WORKER-RUNTIME-DOC-CORRECTION-R4` (a document label; permanent id `PENDING`).
**Status:** Draft revision 4 (at CAPTURE) for independent review, 2026-10-05. Not approved, not assessed, not released.
**Position on the path:** the genuine work item for check 8(c2) of WORKER-CREDENTIAL-BOUNDARY (`7efccee9-13f0-4905-a0a1-e80bc2faa748`, its parent). The Founder decided on 2026-10-05: use the documentation mismatch the VERIFIER already found as real work, launched through the normal path, so the launched PRODUCER's `context_command` reads its bounded per-invocation export. Builds on `main` `723f162`.
**Roles:** one PRODUCER (a real launched worker session); one fresh VERIFIER on the exact candidate; CLOSURE through the normal launch path (landing is off, so it ends at a verified ready-to-land result; the merge to main is done separately).

## Contract

```json alienintent-contract
{
 "identity": "PENDING",
 "version": "revision-4",
 "intent": "Bring the WORKER-CREDENTIAL-BOUNDARY packet and its handoff into exact agreement with the implementation landed on main at 723f162: the worker clone uses --no-local with git's ownership exception given to upload-pack, the VERIFIER and CLOSURE fetch gives the same exception to upload-pack, and the worker HOME's safe.directory .gitconfig is stated to be something no worker git operation depends on. Documentation only.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: use the already-identified --no-local / stale .gitconfig documentation correction as the genuine work item for check 8(c2); keep the contract deliberately narrow.",
  "Founder 2026-10-05: no production-code changes; no workflow, authority, credential, context-export or landing changes; no unrelated documentation edits.",
  "Founder 2026-10-05: the App contents: write decision is not made by this unit; it follows 8(c2).",
  "Founder 2026-10-05: the launch is the ordinary factory launch, with nothing special-cased for the proof: register, assess, approve and release, work launch, PRODUCER, VERIFIER, automated CLOSURE up to the existing ready-to-land boundary. The PRODUCER receives no context by hand beyond its bounded export and its normal instructions; any manual context voids the 8(c2) evidence.",
  "Founder 2026-10-05: the two stale handoff notes are closed only to the extent the landed implementation resolves them."
 ],
 "authorized_scope": [
  "docs/work-units/python/worker-credential-boundary.md",
  "docs/work-units/python/worker-credential-boundary-handoff.md"
 ],
 "excluded_scope": [
  "any file outside the two authorized documents",
  "tests, configuration, credentials, launcher behaviour, context-export behaviour and landing behaviour",
  "production code and tools, including the docstrings in src/alienintent/composition/work_registry.py and src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "the review records in section 6 of the packet (history)",
  "any change to the packet's contract block",
  "workflow, authority, credential, context-export or landing changes"
 ],
 "dependencies": [],
 "required_capabilities": [
  "git"
 ],
 "budget_policy": {
  "maximum_attempts": 2,
  "hard_wall_clock_seconds": 1800,
  "cancellation_limit": 1
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
  "the launch's bounded export <launch>/exports/<invocation>/context.json, kept by the launch for the Founder-run check 8(c2); not checked by the VERIFIER"
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
  "docs/work-units/python/worker-credential-boundary.md"
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

A text written between double backticks is every character between them, except that in replacements 1 and 2 the one space just after the opening double backticks is not part of the text. The texts in fenced blocks are exact lines.

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
   - The worker HOME's `.gitconfig` (written by `prepare_worker_session`) is still written, but no worker git
     operation depends on it; its packets-clone entry does not match. The packet now says so. The code is unchanged.
   ```

Nothing else changes. The PRODUCER uses its `context_command` for any further fact.

## 3. Acceptance checks

1. **Exact diff.** `git diff <starting revision> <candidate>` touches only the two authorized files, and is exactly replacements 1-5. Catches an unrelated edit or a paraphrase.
2. **Agreement with main.** Each new text matches main's code: `WorkerCloneAdapter.allocate`, `candidate_clone` and `_upload_pack` in `git_worktree.py`, and `prepare_worker_session` in `work_registry.py`. Catches a correction that is itself wrong.
3. **Contract unchanged.** The packet's contract block and section 6 are byte-identical to the starting revision. Catches an edit to history or to the approved contract.

The launch itself is the evidence for check 8(c2) of the parent unit: the PRODUCER runs as `alienintent-worker`, its `context_command` reads `<launch>/exports/<invocation>/context.json`, and the Founder then runs the boundary proof with `--package` on that file. That proof, not this unit's VERIFIER, decides 8(c2).

## 4. Review record

**Revision 4, new work item (2026-10-05).** Launch finding on `c01f6c60-ce6c-42ab-979a-30cd5817b713` (revision 3 at `docs/work-units/python/worker-runtime-doc-correction-r3.md`, authorized at `e19ec30`): `LaunchPreparation.prepare` refused `MISSING_RECORD: design_rules, docs/evidence/worker-credential-boundary/landing-2078b37.md: not a path present at the pointer commit`. Every `authority_references` entry is read at the item's immutable pointer commit on `alienintent/work-packets`, and the landing record exists only on `main`. Revision 4 keeps only `docs/work-units/python/worker-credential-boundary.md`, which is present on the packets branch. `c01f6c60` is kept as an immutable historical attempt (cancelled through `FactoryCoordinator.cancel`, not DONE, not superseded in place; it never launched a worker). Before assessment, revision 4 was preflighted against every launch-preparation predicate that can be evaluated in advance (`preflight-r4` record).

**Earlier new work item (2026-10-05).** This revision 3 is registered as a new child of `7efccee9`. The earlier item `c5200bcd-b2d4-4789-a1cb-90b6336f3f54` (this packet's revisions 1-2, at `docs/work-units/python/worker-runtime-doc-correction.md`) was authorized at `8f41ce6`; its authorized instructions are fixed (`AUTHORIZED_INSTRUCTIONS_FIXED`) and needed the budget correction, so it is kept as an immutable historical attempt: deferred, not DONE, not superseded in place, and it never launched a worker (Founder 2026-10-05).

**Revision 3 (2026-10-05).** Launch finding: the first dispatched PRODUCER launch was refused by `LaunchPreparation.prepare` with `MISSING_RECORD: budget_policy` because the contract stated no `hard_wall_clock_seconds` or `cancellation_limit` (Founder rule of 2026-10-03, worker-launch.md: every launched packet states explicit execution and shutdown limits, approved with that packet; no hidden defaults). Added `hard_wall_clock_seconds: 1800` (each role session's hard time limit) and `cancellation_limit: 1`. Nothing else changes.

**Revision 2 (2026-10-05).** REVIEWER of `0c77e62` (FAIL, one wording fix): F1, the `.gitconfig` is not needed rather than without effect (its intake entry does match). Optional notes applied (backtick spacing, corrected by the follow-up of `1328290`, D1; the export is kept by the launch, not checked by the VERIFIER). Founder constraints added: an ordinary launch with nothing special-cased, no manual context, the full lifecycle, the wider exclusions.

**Revision 1 (2026-10-05).** First draft, from the Founder's decision of 2026-10-05.
