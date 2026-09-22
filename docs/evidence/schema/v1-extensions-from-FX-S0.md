# v1 extensions observed from FX-S0

**No v1 schema change is made here.** Both v1 schemas allow additional properties; the FX-S0 records
(WO-220101, DAG node S0) use that allowance and this file lists every addition so it is explicit rather
than silent. It extends, and does not supersede, [`v1-observed-gaps-from-PY-04.md`](v1-observed-gaps-from-PY-04.md),
[`v1-extensions-from-PY-05-to-PY-09.md`](v1-extensions-from-PY-05-to-PY-09.md) and
[`v1-extensions-from-PY-10.md`](v1-extensions-from-PY-10.md).

FX-S0's records describe a **local proof run over a disposable root**, not the lifecycle of WO-220101
itself. As PY-10 did for the sandbox, `biu_id` names the seeded probe item (`S0-PROBE`) for lifecycle
facts and `WO-220101` for fixture-level facts; `scope` on the derived report states the distinction.

## Execution Trajectory — added event type

| Event type | Records |
|---|---|
| `SUCCESS_COLLAPSE_OBSERVED` | the unchanged kernel carried a successful producer outcome from IMPLEMENT to DONE in one step (`FactoryCoordinator._completed_for_outcome`), with no separate VERIFY/REVIEW/ACCEPT projection and no independent verifier invocation. A factual observation of a known limitation; it is not a verdict and not a repair. |

`ISOLATION_OBSERVED` (PY-10) is reused for the network-denial and credential-absence observations.

## Quality Evidence — added fields (the FX run report)

| Field | Meaning |
|---|---|
| `fixture_id` | the proof fixture this report was produced for |
| `verdict` | `PASS`, `FAIL` or `HOLD`. `HOLD` means a required measurement could not be taken; it is never a pass and never a zero. |
| `hold_reasons` | why the verdict is `HOLD`, one entry per untaken measurement |
| `checks[]` | one entry per pinned predicate: `id`, `name`, `status` (`PASS`/`FAIL`/`HOLD`), `expected`, `observed` |
| `network_denial` | the attempted-network observation: socket errno and name, `git ls-remote` exit status, the process's net-namespace inode, and `status` `ENFORCED` or `NOT_ESTABLISHED` |
| `credentials_present` | environment variable names that carry or route a credential; an empty list is an observed empty list |
| `provider_calls_observed` | `{value, definition}`: attempts by the worker process adapter to execute a provider executable, summed over the durable journal |
| `kernel_unchanged` | `git diff --quiet <baseline> -- <paths>` result and the blob ids at the running source revision |
| `success_collapse_limitation` | the statement of the limitation, with `independent_verifier_invocation` and `live_proof` both `NOT_ESTABLISHED` |
| `lifecycle_terminal_stage` | stage per seeded item as read back from the store |
| `candidates` | per item: branch, revision, locator, correlation, the two fresh-clone paths and what each resolved, author/committer dates |
| `injected_clock` | the epoch every substrate clock read returns, with its definition; artifact `recorded_at` uses the real clock |
| `substituted_boundaries` | the boundaries the substrate replaces, so offline success is not read as live proof |
| `live_proof` | always `NOT_ESTABLISHED` for an FX run |
| `reopened_root`, `baseline_revision`, `coordinator_summary`, `manifest`, `root`, `recorder` | run provenance |

`token_usage` and `cost` are `NOT_APPLICABLE` (no provider ran); `unknown_metrics` says so.

## New record kinds

| Record | Where |
|---|---|
| `OfflineProofManifest` schema 1 | `docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json` — the pinned input |
| `ProofFixturePlan` schema 1 | `docs/evidence/wave2-proof-fixtures/FX-S0/fixture-plan.json` — pinned before implementation |
| `ProofFixtureExecution` schema 1 | `docs/evidence/wave2-proof-fixtures/FX-S0/execution-record.json` — commands run, exit statuses, artifact digests, platform, holds |

`proven-red.json` and `offline-suite.json` reuse the PY-10 shapes unchanged.

## Still open for a future schema review

1. The three open items from PY-05–PY-09 and the PY-10 items remain open. FX-S0 adds no evidence on
   repair cycles; it has none.
2. `checks[].id` is a per-fixture predicate numbering (`P1`…`P13` of *this* plan), the same
   limitation PY-10 noted for `acceptance_criteria`.
3. A proof run is still not a first-class entity; FX-S0 binds its events by `recorder` and the
   execution record's artifact digests.
