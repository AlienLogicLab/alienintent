# FX-S0 — proof fixture for the reusable isolated proof substrate (WO-220101)

Owner node S0 · Issue [#69](https://github.com/AlienLogicLab/alienintent/issues/69) · release SWF-35,
baseline `ade44cb93f3f33a570e1cf1b4bda500a79cd95bb` · proof level `LOCAL_COMPOSED_OR_MECHANICAL`.

## Order of work, as the release record required

1. **Pinned before implementation** — [`FX-S0/fixture-plan.json`](FX-S0/fixture-plan.json) and the
   pinned input [`FX-S0/manifest.json`](FX-S0/manifest.json) were committed first (commit
   `3b7fcc9`), fixing commands, controlled inputs, expected observables, negative controls and the
   evidence schema for predicates P1–P13, and the blob ids of the seven kernel paths that must stay
   unchanged.
2. **Implemented at current interfaces** (commit `37f09a6`): `ScriptedWorkerProcess` behind the
   unchanged `RealWorkerProvider`, `ScriptedWorkerProvider` with a durable journal,
   `LocalWorkManagement` with durable receipts, `OfflineProofSubstrate` in the existing offline
   composition, and the `python -m alienintent.composition.offline_proof` runner. No role router, no
   kernel change, no scripted lifecycle transition.
3. **Executed and retained** — `tools/evidence/fx_s0_evidence.py` ran the pinned commands and wrote
   the artifacts below; [`FX-S0/execution-record.json`](FX-S0/execution-record.json) names the
   source revision, platform, every command's exit status and each artifact's digest.

## What the intact run observed (C2, inside `unshare -rn`, environment stated in full)

| Predicate | Observed |
|---|---|
| P1 real temporary SQLite | `state.sqlite` at schema 2; `factory:S0-PROBE` at `DONE` with an independently read-back candidate |
| P2 disposable bare remote | `remote.git` bare; `main` = baseline `244000c8…`; `candidate/launch-S0-PROBE-0` = `0af156cb…` |
| P3 fresh verifier worktree | producer read-back clone and the kernel's custody clone both resolve `0af156cb…` |
| P4 local work management | receipts `release-proposed` → `execution-state-projected DONE`, each read back |
| P5 local provider transport | `ScriptedWorkerProcess`, provider `scripted`, no executable configured |
| P6 injected clock/IDs | every journal/receipt stamp and both commit dates = `1758542400`; same manifest reproduces the revision in an isolated root, a different clock changes it |
| P7 durable journal | `invocation-started`, `process-run`, `invocation-outcome`, `workspace-finalized`; read back from the file alone |
| P8 credentials absent | `credentials_present: []` (observed empty, not assumed) |
| P9 network denial | `connect 192.0.2.1:9` → `ENETUNREACH`; `git ls-remote https://198.51.100.1/…` exit 128; net-namespace inode differs from the launcher's; status `ENFORCED` |
| P10 zero provider calls | `0`, summed over the journal |
| P11 kernel unchanged | `git diff --quiet ade44cb -- <7 paths>` exit 0; blob ids equal the pinned ones |
| P12 success-collapse limitation | IMPLEMENT→DONE under `launch:S0-PROBE:0` in one kernel step; no VERIFY/REVIEW/ACCEPT projection; `independent_verifier_invocation` and `live_proof` both `NOT_ESTABLISHED` |
| P13 no scripted transitions | journal carries no lifecycle field; the only lifecycle receipts are the kernel's projections; adapters hold no store |

## Negative controls (intact / fault / restored)

[`FX-S0/proven-red.json`](FX-S0/proven-red.json): without the namespace the runner **holds** (C3,
exit 2, `NOT_ESTABLISHED`); with `GITHUB_TOKEN` set it **holds** (C4, exit 2,
`credentials_present: ["GITHUB_TOKEN"]`); with a scripted `provider-call` step it **fails** (C5, exit 1,
`provider_calls_observed: 1`, item left at `IMPLEMENT`). Determinism, journal read-back and seed
mismatch are discriminated by named tests in C1. Fault-case reports are under
[`FX-S0/negative-controls/`](FX-S0/negative-controls/).

## Suites

C1 30 passed · C7a architecture fitness PASS · C7b `python3 -m pytest -q` 374 passed
([`FX-S0/offline-suite.json`](FX-S0/offline-suite.json)) · C7c `node scripts/check.mjs all` exit 0
(runtime 310, RAI 18, policy 2, preflight PASS).

## Substituted boundaries and what is not claimed

Substituted: provider transport (scripted process), worker journal, Work Management transport, the
Git remote (local bare path), decision notification. Not substituted: the operational store, the
coordinator and lifecycle domain, release admission, `RealWorkerProvider`, `GitSourceControl`,
`GitWorktreeAdapter`, custody read-back.

Not claimed: multi-role producer/verifier/closure proof (K1/K2/K3/O), rework, restart-after-crash,
duplicate or delayed outcome scenarios, live GitHub or provider proof, any lifecycle transition by a
script. The success-collapse path is **reported as a limitation**, not repaired; R1-GAP-039 holds stand.

**Platform sensitivity.** P9 depends on an unprivileged user+network namespace. Where the platform
cannot create one, the runner reports `HOLD` and the namespace tests skip with that reason; the CI run
on the candidate branch is the durable observation of that platform. Schema additions are documented in
[`../schema/v1-extensions-from-FX-S0.md`](../schema/v1-extensions-from-FX-S0.md).
