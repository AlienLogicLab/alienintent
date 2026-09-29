# Shortest path to a self-building Python factory

**Decision, 2026-09-29:** The first milestone is a Python AlienIntent factory that can continue building AlienIntent. This plan uses the current Python codebase. It does not require completing the full v2 roadmap or retiring every Node ancillary duty first. The old Node dispatcher must not write the same profile.

## What exists

The Python tree already contains a SQLite-backed `FactoryCoordinator`, local end-to-end Producer/Verifier proofs, real Git worktree and worker adapters, GitHub Project adapters, a sandbox run composition, release admission, and doctor probes. These are a useful substrate, not yet proof of an unattended live factory. The missing work is to wire one supported operational profile to the real backlog and worker, close quality/custody gaps, and prove it can continue after a BIU and restart.

## Minimum build sequence

| Packet | Work | Done when |
|---|---|---|
| 0. Establish a safe target | Pin code and one real AlienIntent BIU; read back active claims/effects and confirm one Python writer for an isolated profile. Identify the start command, worker, Git checkout, Project and recovery checkpoint. | No competing writer or unresolved effect can be silently overwritten. |
| 1. Connect the live loop | Choose one of the existing Python compositions; wire real Project READY intake/readback, `FactoryCoordinator`, `RealWorkerProvider`, worktrees, invocation journal, release admission and doctor. Add only the missing seams, with an operator start/status/stop command. | A clean Python start discovers an authorized READY BIU and launches its Producer without manual Project edits or fixture callbacks. |
| 2. Make one BIU trustworthy | Producer publishes a precise candidate SHA; a separate Verifier retrieves it into a fresh workspace, runs declared mechanical checks and judges the source intent, design, obligations, reuse, simplicity and regression risk. Bounded repair or a real decision handles rejection. Guard landing and read back the actual result before DONE. | One real repository-changing AlienIntent BIU reaches DONE with exact candidate, independent verdict, landing and outcome receipts. Wrong target, missing obligation, duplicate mechanism, stale/fake PASS, self-review and failed outcome each block closure. |
| 3. Keep building | Add durable wake/refill, crash and unknown-effect reconciliation, liveness/status, decision delivery, and bounded worktree/journal/evidence retention. | After a controlled restart, the profile resumes or honestly blocks the first BIU and takes a second eligible real BIU without the Founder relaying messages. No duplicate effect or silent idle. |

These are **planning packets**, not existing Issue numbers. Turn each missing seam into a bounded BIU under the current work-packet and Agent Ready process. Use existing Python implementations when they satisfy the contract; avoid rebuilding a component because an old milestone lists it. WIP stays at one mutating BIU.

## First-milestone acceptance

Run two consecutive real AlienIntent BIUs against the chosen Python profile. One must change this codebase and exercise a meaningful product behavior; the other proves automatic continuation. Kill/restart at a worker or effect boundary. Record source/BIU identity, candidate SHA, fresh verifier workspace and verdict, mechanical results, landing SHA, outcome readback, Project/local state, claims/effects, recovery behavior and resource high-water. The factory must either finish truthfully or expose a typed blocker; a DONE label alone is insufficient.

The minimum slop gate is mandatory now: conserve requirements through the BIU, reject an unauthorized or duplicate design, verify independently against exact code, refuse fabricated proof, preserve prior behavior during repair and test the landed outcome. Broader REST/MCP interfaces, multiple projects, parallel WIP, dashboards, adaptive Director cognition and a clean-room rewrite are outside this first milestone.

**Next action:** inspect the current `SandboxRunProfile` and `GitHubProfileComposition` seams, select one operational entry point, and draft the smallest BIU needed to connect a real READY AlienIntent item to that profile. Then implement packets 1–3 and execute the acceptance run.

Full Node retirement remains a later, separate proof: liveness, observation, admission, attention/mailbox, aliases and bootstrap/launch duties need Python successor readbacks under the existing cutover decision. A successful first milestone does not claim those duties are retired.

Sources: `docs/architecture/alienintent-factory-v2-formal-design.md`, `docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`, `docs/evidence/wave2-dependency-dag.json`, and the companion agent-slop problem/gap documents. Prior Project/runtime observations are snapshots; refresh custody before a live claim.
