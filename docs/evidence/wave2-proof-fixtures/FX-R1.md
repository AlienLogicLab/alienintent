# FX-R1 — Replacement gate: coordinator checkpoint (WO-220601, SF-REQ-053)

Retained proof record for DAG node R1 (`retirement_gate`, capstone, `owns_capabilities: []`). This record
**cites** existing retained proof. It does not re-execute, extend or supersede the FDH-01 live-proof run.
It adds no new fault-path exercise, and it does not restate the C2/C3 records. Execution packet:
`docs/evidence/wave2-execution-packets/WO-220601.packet.json`. Work unit: `docs/work-units/wave2/WO-220601.md`.

**Completion predicate (R1):** a successor reconstructs scope, unresolved decisions, effects and authorized next
actions without prior conversation; a mismatch blocks tenure change; the checkpoint is preserved until equivalent
canonical continuity works.

## The checkpoint is preserved; nothing is retired

This record retires nothing. The coordinator checkpoint (`wave1-bootstrap-retirement-matrix.md` M07,
`KEEP_UNTIL_REPLACED`) and the session-bound/resident continuity mechanism it protects stay in place.
Retiring either one is a later, separate and explicit decision. That decision is outside this BIU's extent and is
not made, implied or recommended here. On Issue #89 the Founder decided to keep the old mechanism "available but
inactive, as rollback insurance" (https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5815939064).
Nothing in this record changes that. No release, cutover or production mutation is authorized or performed.

## Inputs and identities

| Item | Value |
|---|---|
| Invocation | `AlienLogicLab/alienintent#130:PRODUCER:6ec08ebe-d2b4-462e-976d-6284d6be5b36` |
| Release baseline | `98dddaea8783b6e482364122751dd1e72647361b` (RELEASED record, Issue #130); packet authority baseline `de2f533e2423f92759be73baff88feadc7226a99` is its parent |
| Candidate contract | sha256 `edb243379f55c5965aed63f19605beb6aab6886b79dd5975ef8112f8ac887c53` |
| Operational target | FDH-01 Factory Director Host, Issue #89; bound under `docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md` (see WO-220601.md, "Target binding and operational proof — 2026-09-27") |
| Live-proof evidence | `docs/evidence/fdh-01-live-proof/20260924T080401Z/`, retained at `59db3c532a004e10dee60eede7a477e8e17545f1`, PASS reported at https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5811283523 |
| FDH-01 landed | `a233e9e47fae053e0f789943f6423dbfeb2a8bbe` (accepted candidate `b0c66a72aaa799c865ffe759749395a2ddff0e6a`; VERIFIER ACCEPT https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810163277) |
| Procedure | `docs/operations/factory-director-host-live-proof.md`: authored at `a2bf163` (blob `28756efa…`); run followed the revision at `06e7e0c` (blob `c9977a26…`, last changed at `c09a785`) |

## Integrity check (bounded commands)

`tools/evidence/fx_r1_evidence.py` re-checks everything this record relies on, and nothing more. It reads the
repository and writes only `FX-R1/citation-check.json`.

```
rtk proxy python3 -B tools/evidence/fx_r1_evidence.py \
  --baseline 98dddaea8783b6e482364122751dd1e72647361b \
  --invocation "AlienLogicLab/alienintent#130:PRODUCER:6ec08ebe-d2b4-462e-976d-6284d6be5b36" \
  --output docs/evidence/wave2-proof-fixtures/FX-R1
```

Observed: exit 0, 24 of 24 checks PASS, 0 failed. Retained as `FX-R1/citation-check.json`, which records each
check's command, expected result, observed result and exit status. The script runs the packet's two bounded
commands verbatim:

- `sha256sum -c SHA256SUMS` in the FDH-01 directory: exit 0, 44 of 44 listed files OK.
- `git merge-base --is-ancestor a233e9e 98dddae`: exit 0. The FDH-01 landed SHA is an ancestor of the release
  baseline. The evidence commit `59db3c5`, both procedure revisions, and every cited C2/C3 source, retained-evidence
  and merge commit are also ancestors.

It also checks the following:

- **Pin before run.** The procedure was authored at `a2bf163`, committed 2026-09-24T06:56:25Z. The revision the
  run followed is `06e7e0c`, committed 08:02:58Z; its procedure text last changed at `c09a785` (07:22:15Z). All
  three precede the run start, 2026-09-24T08:04:01Z. **Precision note:** WO-220601.md calls `a2bf163` "the exact
  pinned" procedure. The exact text the run followed is the `06e7e0c` blob (`c9977a26…`), as the run's own
  `README.md` and the #89 authorization (https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810275846)
  state. `a2bf163` is the first authored version and differs from that text. The pin-before-run conclusion
  holds for both revisions.
- **Cited observations.** FX-C2 (31 observations) and FX-C3 (73 observations) are each content-addressed; every
  file's sha256 equals its name.
- **Cited controls.** FX-C2 has 13 of 13 controls discriminating and FX-C3 has 23 of 23, each applied exactly
  once. Both records exit 0 with no holds, and their source revisions match the values cited below.

## Predicate mapping

### Reconstructs scope, unresolved decisions, effects and authorized next actions without prior conversation

Discharged at the **R1 integration level, operationally**, by FDH-01 steps 7-10 and 12. The evidence files live in
`docs/evidence/fdh-01-live-proof/20260924T080401Z/` and are covered by `SHA256SUMS`.

| Element | FDH-01 step | Observation |
|---|---|---|
| Without prior conversation | 6, 7, 8 | `07-cmdline-B.txt`: `claude -p --no-session-persistence`, no resume/continue flag (same argv as A, `02-cmdline-A.txt`). `06-lease-diff.txt`: new episode id `factory-director-7e7fbb7b…` and pid 178549, versus A's `factory-director-eeb12163…` and pid 144911. `08-output-A.json` / `08-output-B.json`: session ids `a94d236a…` and `e10b26fd…` differ. |
| Scope | 8 | `08-output-B.json`: B re-derived its objective from durable records. That covered the Founder's #81→#83 order from the processed inbox entry `founder-queue-order-20260924T080442Z`, #83's pinned work-unit hash, and the release-gate file hashes BRD-83 pins. It named `project_materialization.py` as out of BRD-83's scope. |
| Unresolved decisions | 8 | `08-output-B.json`: no Founder holds, unprocessed inbox entries, escalations or pause. It also recorded what stays open for a successor: 13 TASKS Issues without an assessment, 42 at CAPTURE, and the separate gate-switch Director action. `04-holds.sha256` shows the hold record byte-identical to 0a. |
| Effects | 8, 10 | `08-output-B.json`: B recognized A's effect (#81 DONE, merged `474343a`) and the claim/WIP state. `10-readback.txt`: B's own effect was read back from the Project: "issue #83 is on Project #1 at IMPLEMENT, exactly one item". |
| Authorized next action | 9, 10 | `08-output-B.json`: B chose #83 (BRD-83) as the next authorized action and released it (gate ADMITTED, READY→IMPLEMENT). `10-readback.txt` confirms the result. The run's README also lists `09-issue.txt` for step 9, but that file is empty (0 bytes, checksum-listed), so step 9 rests on `08-output-B.json` and the step-10 read-back alone. |
| Repetition | 12 | `12-diagnostics.json`, `12-history-tail.jsonl`, `12-lease.json`: the host idled correctly as `WIP_INTENTIONALLY_FULL`, consistent with the diagnostics (no control required, 1 active claim), with zero crash-loop or launch-failure records. |

**Limits of this evidence, stated plainly:**

- The run is **positive-path only**.
- The reconstructions are Director LLM episodes reading durable records. The per-element content above comes
  from B's self-reported output, corroborated by the Project read-back (`10-readback.txt`) and the linked #83
  comments. Nothing mechanically compared A's reconstruction against B's; the EQUAL comparison exists only in
  FX-C2's local fixture.
- The workload was two items, #81 and #83. The run shows the continuity mechanism working in this instance. It is
  not a claim of general operational success beyond what the files above show.
- The run's own findings stand as recorded in `FINDINGS.txt`. P1, a deployment PATH problem, is followed up as
  #91. P2, a fail-safe WIP predicate edge, is followed up as #92.

### Mismatch blocks tenure change

This element is discharged **at the capability level only**, by the retained C2/C3 proof cited below. It was
**not re-observed at the R1 integration level**; the FDH-01 run contains no mismatch or fault injection. The owner
clarification disposed 2026-09-27 (WO-220601.md, "Owner clarifications disposed") holds that no new R1
negative-control exercise is authorized or needed. Both records are proof level `LOCAL_COMPOSED_OR_MECHANICAL`.

| Capability | Retained record | Cited proof | Independent verdict / landing |
|---|---|---|---|
| `durable_context_reconstruction` (C2, WO-220302, #95) | `docs/evidence/wave2-proof-fixtures/FX-C2/`; invocation `…#95:PRODUCER:4a2582db-…`; source `459f825`; retained `4692004` | `tests/context_assembly/test_context_reconstruction.py::test_mismatch_is_failure`: a changed reconstruction compares as `MISMATCH` with exit 1, never a started process. Control `mismatch_as_failure` discriminates. 13 of 13 controls. | VERIFIER ACCEPT https://github.com/AlienLogicLab/alienintent/issues/95#issuecomment-5825255314; merged `7b6e19c` |
| `bounded_episode_control` (C3, WO-220303, #99) | `docs/evidence/wave2-proof-fixtures/FX-C3.md` and `FX-C3/`; invocation `…#99:PRODUCER:1965556d-…`; source `aaa16fb`; retained `d69c004` | 23 intact/fault/restored controls, including `vector_check_removed` over `test_state_vector_mismatch` (end cause `STALE_VECTOR`) and `old_epoch_accepted` (a stale epoch cannot act). | VERIFIER ACCEPT https://github.com/AlienLogicLab/alienintent/issues/99#issuecomment-5830589629; merged `fc5c0a7` |

Both retained `execution-record.json` files still read `independent_verdict: PENDING_FRESH_BIU_VERIFIER`, as
produced. The verdicts were given afterwards on the Issues linked above. This record cites them there and does
not edit the C2/C3 records. B0 (WO-220501, #116) is a DONE dependency and contributes no evidence to this mapping.

## Findings for the verifier (recorded, not repaired here)

- **R1-F1, disposition wording.** WO-220601.md says R1's `proof_requires_capabilities` are "exactly" C2 and C3.
  In `docs/evidence/wave2-dependency-dag.json`, R1 lists 14 capabilities, owned by S0, S1, S2, U1–U5, B0, C1, C2
  and C3. C2 and C3 are the two that own reconstruction and tenure/state-vector mismatch, so the evidence mapping
  above is unaffected. The wording is inaccurate, though. Correcting the disposition text belongs to the Factory
  Director, not to this BIU.
- **R1-F2, procedure revision.** This is the precision note under "Integrity check" above.
- The DAG's `proof_fixtures` status for FX-R1 stays `PLANNED_NOT_EXECUTED`, like every other fixture in that
  planning snapshot. Updating the DAG is replanning, which is outside this BIU's extent.

## Non-claims

- No claim that the session-bound/resident continuity mechanism or the coordinator checkpoint is retired, or may
  now be retired.
- No fresh operational mismatch or fault-path observation at the R1 level.
- No release, cutover or broader production mutation. A local result is not presented as operational success.
- The integrity check proves citation integrity only. It does not re-run or re-prove the cited evidence.
