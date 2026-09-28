# FX-R6 — Release-admission preparation pin

Status: preparation only; the existing release-admission protection remains in force.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

## Bound target

The proof target is the existing canonical live-profile prelaunch boundary exercised by the real AlienLogicLab/
alienintent Project #1 path. The fixture must use a disposable labelled probe and the configured execution profile,
with read-back of the Project item and host runtime state. It must not retire or bypass
`tools/live/release_admission.py`, launch a worker on an invalid case, or alter unrelated Project items.

## Pinned cases

For each case, the producer records the gate decision before any actor launch and the exact application count:

1. intact valid release preconditions: admission may proceed only for the labelled probe;
2. each of the six existing release preconditions absent or invalid: refusal and zero actor launches;
3. eligibility absent or invalid: refusal and zero actor launches;
4. formal release-authority closure without the required preconditions: refusal and zero actor launches;
5. restored valid probe: the exact Project and runtime read-back is reconciled, with old protection still present.

No case permits old-mechanism retirement. A missing precondition, target readback, budget dimension, or actor
count is `UNKNOWN`/HOLD rather than PASS.

## Evidence shape

The output directory is `docs/evidence/wave2-proof-fixtures/FX-R6/<run-id>/` and contains
`execution-record.json`, `observations/<sha256>`, `digest-manifest.json`, `proven-red.json`, `readback.json`, and
an independent verdict receipt. The record must bind the candidate SHA, profile/config digest, Project item,
runtime-state digest, command, exit status, and old-protection readback separately.

## Executable fixture pin — 2026-09-28

Source: `tools/live/fx_r6_release_gate.py` reuses the proven B3 canonical Project #1
fixture. It runs through `GitHubProfileComposition` with only the worker process
scripted to `authority-block`. Its own disposable draft Project items are deleted
and read back; unrelated items must have identical before/after digests. The
existing `tools/live/release_admission.py` remains present and unchanged.

Before the live run, execute:

```bash
rtk proxy pytest -q tools/live/test_fx_r6_release_gate.py tools/live/test_fx_b3_release_admission_proof.py
```

With the configured `~/.config/alienintent/self-hosting.json` profile, run once:

```bash
rtk proxy python3 tools/live/fx_r6_release_gate.py --out docs/evidence/wave2-proof-fixtures/FX-R6/<run-id>
```

The wrapper invokes `python3 tools/live/fx_b3_release_admission_proof.py --target production
--out <run-dir>/live`. The exact executed argv and exit code go in `execution-record.json`.
Inputs are the configured profile (digest only), current host runtime state (before/after
digests), source HEAD, `origin/main`, the B3 case table, and the old gate's committed
source. The valid case must yield one scripted launch; every named negative case must
yield zero launches. The old gate control must pass intact, refuse with Agent Ready
missing despite formal release authority, and pass again restored. Both checks and
the committed file digest must read back unchanged after the run.

The run directory retains `execution-record.json`, `readback.json`, `proven-red.json`,
`digest-manifest.json`, `independent-verdict.json`, the raw `live/` fixture observations,
and command stdout/stderr. `independent-verdict.json` records PENDING until the fresh
verifier issues its own verdict. The candidate commit SHA is recorded on Issue #138
after the evidence commit because a commit cannot embed its own SHA. A missing case,
counter, profile, state, readback or cleanup is a failure, never inferred zero or PASS.

The installed bootstrap gate is `~/.local/share/alienintent-bootstrap/release_admission.py`.
Read its digest and run the intact/fault/restored control before and after the live
probe, separately from the repository copy. Retain any difference between those
files as an observed installation gap. Neither file is retired by this fixture.

## Producer execution — invocation `5bd7c385-7f0b-4c3e-b4c2-c08d5365d994`

The source revision for the final run is `4bc01d9b5a45b15fae8d0fdf1559e4eec490de42`;
its Project #1 release point was `a8869f4b7169951ef1bc523e6b6ea4bcd0adc1be`.
The profile digest is `4b26fae49943f984b693457e565f18764be2260d0315321ceb032250f3b88d87`.
The exact commands and exit statuses are in each run's `execution-record.json`.

| Run | Status | Cases | Invalid launches | Valid scripted launches | Cleanup | Installed gate readback |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `20260928-r6-5bd7c385` | PASS for canonical admission; partial R6 readback | 15 | 0 | 1 | 14/14 deleted and absent | UNKNOWN before live probe |
| `20260928-r6-5bd7c385-installed-readback` | PASS for the pinned R6 probe and readback | 15 | 0 | 1 | 14/14 deleted and absent | before/after identical; intact/fault/restored control passed |

Both live runs exited 0 and report zero provider calls or publications. All 16 files
in each digest manifest matched their retained SHA-256 digests on producer inspection.
The second run's runtime state digest was identical before and after. The raw Project
item facts, admission answers, journal counts, mutation scope and board snapshots
remain under each run's `live/` directory. The first run is retained as interim
evidence; it is not used to claim installed-gate continuity.

The installed bootstrap file (`fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b`)
differs from the repository file (`84b2e2e72cb1cbcad20203726a7d5957faedac31ee0dfe314502c9b466a7d995`).
The installed copy predates the repository's WIP-capacity and priority-reconciliation
checks. This is an installation discrepancy for the named bootstrap owner to
disposition; this R6 producer did not edit the installed copy or retire it. The
canonical Project #1 prelaunch path is proven in the labelled probe, but a live
cutover/retirement is not claimed. `independent-verdict.json` remains PENDING for a
fresh verifier invocation.
