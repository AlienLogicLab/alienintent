# Handoff for unit 6c-2 (work item 621b0120-9fd2-41a0-b816-0b30ecf14281)

Attached to the assessed packet `docs/work-units/python/worker-launch.md` at packets
`7a2c08bb27d61a1eeedcec9374f8f7da942b4ae5` (sha256 cb40e0cd…), assessment
`readiness/621b0120-9fd2-41a0-b816-0b30ecf14281/f42aa5ef-ae68-4dec-b84c-5cf8279aec93/raw` (READY).
Founder implementation approval 2026-10-03, recorded in the work registry. Binding on both the PRODUCER and the VERIFIER.
The packet text is not changed.

## 1. Founder conditions (2026-10-03)
- **Check 10 before acceptance.** The real-provider check must pass before the VERIFIER may ACCEPT and before CLOSURE.
- **Check 10 on isolated data, with only the needed credentials.** The check-10 script uses a throwaway local
  repository and its own temporary state, never the permanent work registry. The worker gets a temporary `HOME` that
  holds only the login files the configured provider itself needs (reuse the existing explicit-authentication-home
  pattern of `src/providers` and `test/worker-runner.test.mjs`); no `gh` or git credentials, no SSH keys, no registry
  GitHub App key, no API key. If a configured provider cannot run that way, stop and report; do not widen it.
- **Containment.** Read-only context access is implemented (6c-1). Operating-system containment is not. The Founder
  accepted this risk explicitly with this approval. Do not claim more in code comments, tests or records.
- **Dependency.** 6c-1 (work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`) is recorded DONE in the permanent work
  registry from its actual evidence (`work record-completed`, landed `0936a9b`). The coordinator's dependency check
  counts it through the injected reader; never bypass that check.

## 2. Base drift
The packet was written against `main` `a5087d7`. `main` now also holds RECORD-COMPLETED-WORK (`0936a9b`), which changed
`factory_coordinator.py` (`_dependency_done`, injected `recorded_completion`), `composition/work_registry.py`,
`control_plane/adapters/cli.py` and `control_plane/application/operator.py`. Line references in the packet may have
moved. First confirm every cited interface on the current `main`; moved lines are not a stop condition, a changed
interface is.

## 3. Assessment notes passed on
- Confirm the 6c-1 interfaces (`WorkContext.assemble`, holds) on `main`.
- `launch(identity)`: exactly the named work item; `_recover` may record other launches' durable outcomes; never
  call `start()`.
- `prepare` first in `_produce`, before the budget, grant and reservation checks; the refusal outcome built in
  composition keeps its reason as a finding.
- `CliWorkerProvider.run` standard input: extend so the fixed-tuple path is unchanged.
- The moved routing module: standard library only, re-exported by file path, Director host install and tests still
  work with plain `python3`.
- Fake test executables record argv, standard input and environment for checks 2 and 8.
- Deterministic `launch/` state and context root in tests.
- A held launch keeps its WIP slot; resolving it is not this unit.
