# Codex-primary activation implementation plan

> For agentic workers: execute the Founder-approved bounded plan with test-first changes and independent review. Do not reopen completed work.

**Goal:** Apply Codex-primary routing at new dispatches and resume WO-220101 from ACCEPT only.

**Architecture:** Change local orchestration policy, not the provider-neutral product domain. Restore the installation's supported Codex provider configuration while preserving role identities, credentials, resource history and permissions. The existing dispatcher's startup reconciliation owns the closure retry.

**Tech stack:** Python local Director/tests, existing Node profile loader/dispatcher, systemd user service, GitHub read-back.

## Constraints and authority

Founder approval: bounded activation, including an idle-only dispatcher restart after deterministic confirmation that no active work will be interrupted. Resume WO-220101 from ACCEPT only; preserve prior implementation and verification evidence. No new BIU, reassessment, replan, status toggle, domain routing or coordinator replacement.

Starting HEAD: `175cccff7a52a60cee2c1fe0764faa4f06212cff`. Existing program-state update and two untracked operator reports are unrelated; preserve and exclude from commits. No temporary task worktree is needed for bounded non-overlapping orchestration edits.

## Task 1 — Local routing policy and evidence

Files: `tools/orchestration/director.py`, `director_cli.py`, `test_director.py`; active routing/Director documentation.

- [x] Test first: bounded cognitive extraction defaults to Codex, a historical task name alone does not justify Claude, a nonempty context reason permits coordinator routing, a blank diversity reason cannot select Claude, and known Claude unavailability falls back to Codex unless Claude-specific work is required.
- [x] Implement `route(..., context_reason=None, unavailable_providers=(), claude_required=False)`; add dispatch permission and exception provenance to routing records. Do not mutate task identity, cycles or existing tasks. Do not select local models before canonical Allocation proves capability.
- [x] Expose the same inputs on `director_cli.py route`; test its real CLI without invoking a model.
- [x] Run `rtk proxy python3 -m pytest tools/orchestration -q`; preserve existing checks. Correct active documentation that still mandates Claude review.
- [x] Independent fresh Codex review receives this plan and the diff, not author reasoning. Record provider/model/session provenance honestly, using UNKNOWN where unavailable.

## Task 2 — Idle-only operational activation

Files: external installation profile only; `docs/evidence/2026-09-22-codex-primary-activation.md` records non-secret evidence.

- [x] Read back #69 ACCEPT and accepted candidate `761a3cb4d6e24dc24ec370de45e25fe8c505eeda`; retain invocation `8a8d6385-600b-4cb7-908e-34580067209b` capacity failure separately from task failure.
- [ ] Validate Codex executable/authentication and existing adapter; preserve prior Codex permission mode and worker identity/authentication boundaries. Back up the installation profile outside the repository. Change only the two provider blocks, then load with the existing validator.
- [ ] Before restart, fail closed on any active lane, live resource PID, dispatcher child/preflight, unexpected unresolved work, changed service identity, or #69 no longer at ACCEPT. Repeat the idle check immediately before restart. Never kill or cancel a worker.
- [ ] Restart only `alienintent.service`. Existing startup reconciliation, not a manual model launch or lifecycle toggle, may resume ACCEPT closure. Verify one successor PRODUCER, Codex process/session evidence, unchanged candidate/ACCEPT evidence and no new IMPLEMENT/VERIFY.
- [ ] Record outcome and limitations durably. Do not modify the failed invocation's history. Follow the resumed closure to its result where available; no repeated launch into capacity exhaustion.

## Task 3 — Closure

Operational gate is BLOCKED before profile mutation: PID 933588 remains in the service
cgroup. See [evidence and requested decision](../../evidence/2026-09-22-codex-primary-activation.md).
Land the independently validated routing portion; do not claim live activation or resume.

- [ ] Validate routing tests, profile loading, offline Node checks and diff hygiene. Preserve unrelated files. Commit only task-owned changes, push/read back main under Repository Change Closure, and record final status without claiming the unrelated dirty tree is clean.
