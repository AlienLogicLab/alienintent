# FX-C3 — Bounded episodes and stale-command refusal (WO-220303, SF-REQ-053)

Fixture contract for the pinned packet in `docs/work-units/wave2/WO-220303.md` § "Pinned proof packet (FX-C3)".
Proof level `LOCAL_COMPOSED_OR_MECHANICAL`. Disposable local profile only. No live store, provider, model launch,
network, host or RAI. A local PASS is not operational acceptance.

## Inputs

- Admission baseline `ed0d4ffb3bfa59bf4bf9e966d6651bf4eaa2e707` (RELEASED record, Issue #99). The code baseline is
  current `origin/main`. The pinned C3 inputs are byte-equal to the admission baseline there: `contracts[8]`,
  `shared_contracts`, DAG `nodes[16]`/`proof_fixtures[16]` and `bius[16]` (canonical
  `a1d3d62d…b9adc6`). The whole-file digests of `wave2-design-contracts.json`, `wave2-dependency-dag.json` and
  `wave2-candidate-bius.json` have advanced through planning commit `6ea9284`. That commit only changes other
  contracts/nodes/BIUs and adds `resolution_2026_09_25` to `R1-GAP-MONITOR-HOST` and `R2-GAP-051-EDGE-AUTHORITY`,
  which are resolutions, not new holds. The packet and allocation digests are unchanged (`1248054d…`, `164488d0…`).
- The FX-C2 seed (`tests/context_assembly/test_context_reconstruction.py::seed`) supplies a real SQLite store, S1
  evidence, the decision inbox, attention and the inventory.
- Clocks are injected as integer microseconds, following the FX-C4 precedent: a UTC anchor read once per process
  plus monotonic progress. Pure layers cannot import `datetime` (architecture determinism check).
- An injected `DeadlineTimer` is driven by explicit `tick()` calls with no thread.
- A scripted `ContextUsageObservation` (label `LOCAL_SUBSTITUTE_USAGE_SOURCE`, U-8).
- An `OperatorGrant` table: `director` is authorized and `intruder` is not (label `LOCAL_OPERATOR_GRANT_TABLE`, U-7).
- A model-launch spy, which must stay at 0.
- Two OS processes (`tests/control_plane/episode_process.py`) for the competing-epoch and restart probes.

## Surface

| Module | Role |
|---|---|
| `control_plane/domain/episode.py` | `TenurePolicy` (3600 s, 32, 300 s, 1, UNBOUND or BOUND at 0.8), closed `EndCause`, pure `evaluate_tenure`, `validate_usage`, `admit_contradiction`, and U-3 `blocked` |
| `control_plane/ports/episode.py` | `EpisodeControl`, `ContextUsageObservation`, `ContradictionObservation`, `DeadlineTimer`, `EpisodeRepository`, `ContextSource` |
| `control_plane/application/episode_control.py` | Tenure checks on each result, event and tick. Every authority-bearing result goes through S2 `commit_guarded` over the U-4 vector (the manifest's pinned aggregates plus `episode:<objective>`), then local journal delivery |
| `control_plane/adapters/episode_repository.py` | S1 `episode-history` first, then the `episode:<objective>` pointer. The pointer is the S2 authority record (U-1): `active`, `epoch`, `invocation`, `expires_at`, `deadline_utc_us` |
| `composition/control_plane_profile.py` | Additive `EpisodeContext` (the only C3 `context_assembly` import, U-9) and `EpisodeProfile`. `AttentionProfile` is unchanged |

## Delegated dispositions as implemented

- **U-5/U-6.** Provider, model, authority and objective revision are bound at `begin`. `observe(kind, identity)` ends
  tenure on any difference. An identity whose freshness cannot be checked (`None`) is a typed `SOURCE_UNCHECKABLE`
  hold.
- **U-10.** `admitted_total` and `epochs` carry across an authorized new epoch. Per-epoch tenure counters start at 0.
- **Usage.** An `Unavailable` or prior-check sample yields `CONTEXT_USAGE_UNAVAILABLE`. A wrong invocation,
  non-finite or negative `used`, or a non-finite or non-positive `limit` yields `CONTEXT_USAGE_INVALID`.
- **Refusals.** A stale epoch or invocation is refused as `STALE_EPOCH` before any write. The S2 fence independently
  refuses the same old-epoch vector (`inactive or mismatched epoch/authority`), and the test asserts both.

## Commands (all under `rtk proxy`, `PYTHONPATH=src:.`)

1. `python3 -B -m pytest -q tests/control_plane/test_episode_control.py`
2. `python3 -B tools/evidence/fx_c3_evidence.py --output <new-dir> --invocation <exact-invocation> --baseline <code-baseline>`
3. Regression, recorded by (2): the full pytest suite, `check_architecture.py --check all`,
   `tests/test_architecture_fitness.py` and `node scripts/check.mjs all`. A full-suite failure is admissible only
   when the identical node set already fails at the code baseline, run in its own detached worktree. Any new
   failure is a HOLD.

Probes, the end-cause table and the 19 discriminating controls are in `tools/evidence/fx_c3_evidence.py`
(`CONTROLS`, `END_CAUSES`) and the retained `FX-C3/` records. The six ★ controls (`old_epoch_accepted`,
`context_item_omitted`, `unbound_as_zero`, `unbound_auto_terminates`, `bound_unavailable_ignored`,
`unauthorized_contradiction_accepted`) discharge the `053-tenure-fence` proven-red obligation. `one_biu_removed` is
a producer addition.

## Residuals and boundaries

- The episode counter update after admission is a second transaction. A concurrent authorized `begin` cannot land
  between them, because `begin` refuses while the prior epoch is ACTIVE; a crash between them under-counts at most
  one admission for that epoch.
- The fixture proves admission and termination of a contradiction judgment, never its semantic truth. Neither the
  fixture nor a context-exhausted event closes LRN-023.
- Out of scope: bootstrap handoff or retirement (POSTW1-DECIDE-006A), host activation, C4/C5 monitor work,
  SF-REQ-008/029 amendments, and C1/C2/S2/U5 behaviour changes.
