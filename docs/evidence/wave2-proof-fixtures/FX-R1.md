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
not made, implied or recommended here. On Issue #89 the Factory Director reported that the retirement threshold
was met. In the same comment it recorded the Founder's decision to keep the old mechanism "available but inactive,
as rollback insurance", with nothing retired
(https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5815939064). This record neither relies on
nor extends that threshold statement, and it changes nothing about that decision. No release, cutover or production mutation is authorized or performed.

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

`tools/evidence/fx_r1_evidence.py` re-checks the **integrity** of the retained evidence this record cites. It
does not check Issue comments, `README.md` wording, or whether the step mapping below is right; those are for the
independent verifier. It reads the repository and writes only under `FX-R1/`. The script was run against the
clean committed record and script.

```
rtk proxy python3 -B tools/evidence/fx_r1_evidence.py \
  --baseline 98dddaea8783b6e482364122751dd1e72647361b \
  --invocation "AlienLogicLab/alienintent#130:PRODUCER:6ec08ebe-d2b4-462e-976d-6284d6be5b36" \
  --output docs/evidence/wave2-proof-fixtures/FX-R1
```

Observed: exit 0, 34 of 34 checks PASS, 0 failed. The result is retained in the existing v1 fixture form as
`FX-R1/execution-record.json` (`ProofFixtureExecution`), with source revision, input digests, labels, holds,
residuals and verdict status. The per-check report is a content-addressed observation under `FX-R1/observations/`,
recording each check's command, expected result, observed result and exit status. Re-running from the same
revision reproduces the same observation digest. A fault/restore probe was run before retention: deleting one
FX-C2 observation failed 3 checks, and appending a byte to the FDH-01 `README.md` failed 1. Restoring both
reproduced the passing digest.

The packet's two bounded commands, with the deviations stated:

- `sha256sum -c SHA256SUMS`: exit 0, 44 of 44 listed files OK. The packet writes it as
  `sha256sum -c docs/evidence/fdh-01-live-proof/20260924T080401Z/SHA256SUMS`, but the entries are `./`-relative,
  so that form exits 1 from the repository root. The script runs it from inside the directory instead.
  `SHA256SUMS` does **not** list `README.md` or itself. Those two files, and the whole directory, are covered by
  a separate check: the directory must be byte-identical in Git from the retaining commit `59db3c5` to the
  checked revision, with no working-tree changes and no untracked files.
- `git merge-base --is-ancestor a233e9e47fae… 98dddaea8783…`, run with full SHAs: exit 0. The FDH-01 landed SHA is
  an ancestor of the release baseline. The evidence commit `59db3c5`, both procedure revisions, and every cited
  C2/C3 source, retained-evidence and merge commit are also ancestors.

It also checks the following:

- **Pin before run.** The procedure was authored at `a2bf163`, committed 2026-09-24T06:56:25Z. The revision the
  run followed is `06e7e0c`, committed 08:02:58Z; its procedure text last changed at `c09a785` (07:22:15Z). All
  three precede the run start, 2026-09-24T08:04:01Z. These are committer timestamps. The run's own
  `00-origin-main.sha` independently records `06e7e0c` as the `origin/main` it ran from.
  **Precision note (R1-F2):** the execution packet (`owner_clarifications_disposed.fx_r1_retroactive_pin`) calls
  `a2bf163` "the exact pinned fixture commands…". The exact text the run followed is the `06e7e0c` blob
  (`c9977a26…`), as the run's `README.md`, its `00-origin-main.sha` and the #89 authorization
  (https://github.com/AlienLogicLab/alienintent/issues/89#issuecomment-5810275846) all state. `a2bf163` is the
  first authored version and differs from that text. The pin-before-run conclusion holds for both revisions.
- **Cited records unchanged.** `FX-C2/` and `FX-C3/` are byte-identical from their retaining commits (`4692004`,
  `d69c004`) to the checked revision.
- **Cited observations.** There are exactly 31 FX-C2 and 73 FX-C3 observations. Each is content-addressed, and
  every file's sha256 equals its name. Every intact/fault/restored ref in `proven-red.json` resolves to a
  retained file.
- **Cited controls.** FX-C2 has exactly 13 controls and FX-C3 exactly 23. Every one discriminates and is
  applied exactly once. The control cited for each probe (`mismatch_as_failure`, `vector_check_removed`) runs
  that probe. Both records exit 0 with no holds, and their source revisions match the values cited below.

## Predicate mapping

### Reconstructs scope, unresolved decisions, effects and authorized next actions without prior conversation

Discharged at the **R1 integration level, operationally**, by FDH-01 steps 7-10 and 12. The evidence files live in
`docs/evidence/fdh-01-live-proof/20260924T080401Z/`. Every file cited below is listed in `SHA256SUMS`; the directory as a
whole, including `README.md`, is covered by the Git immutability check.

| Element | FDH-01 step | Observation |
|---|---|---|
| Without prior conversation | 6, 7, 8 | `07-cmdline-B.txt`: `claude -p --no-session-persistence`, no resume/continue flag (same argv as A, `02-cmdline-A.txt`). `06-lease-diff.txt`: new episode id `factory-director-7e7fbb7b…` and pid 178549, versus A's `factory-director-eeb12163…` and pid 144911. `08-output-A.json` / `08-output-B.json`: session ids `a94d236a…` and `e10b26fd…` differ. |
| Scope | 8 | `08-output-B.json`: B re-derived its objective from durable records. That covered the Founder's #81→#83 order from the processed inbox entry `founder-queue-order-20260924T080442Z`, #83's pinned work-unit hash, and the release-gate file hashes BRD-83 pins. It named `project_materialization.py` as out of BRD-83's scope. |
| Unresolved decisions | 4, 8 | `08-output-B.json`: no Founder holds, unprocessed inbox entries, escalations or pause. It also recorded what stays open for a successor: 13 TASKS Issues without an assessment, 42 at CAPTURE, and the separate gate-switch Director action. `04-holds.sha256` (step 4) shows the hold record byte-identical to `0a-founder-holds.json`. |
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
not edit the C2/C3 records. The #99 VERIFIER comment is partly corrupted: its invocation, branch, commit and
baseline fields render blank, and it contains literal `\n` sequences. Only its trailing marker
`#99:VERIFIER:044175c7-6af9-47c7-aa43-e085416a068a RESULT=ACCEPT` identifies the verdict. The accepted SHA `d69c004`
is established by the #99 PRODUCER DONE comment
(https://github.com/AlienLogicLab/alienintent/issues/99#issuecomment-5830800548) and merge `fc5c0a7`, not by that
comment's body. The same comment also reports 27 full-suite failures, present identically at candidate and baseline,
as recorded in FX-C3.md. B0 (WO-220501, #116) is a DONE dependency and contributes no evidence to this mapping.

## Findings for the verifier (recorded, not repaired here)

- **R1-F1, disposition wording.** WO-220601.md says R1's `proof_requires_capabilities` are "exactly" C2 and C3.
  In `docs/evidence/wave2-dependency-dag.json`, R1 lists 14 capabilities, owned by S0, S1, S2, U1–U5, B0, C1, C2
  and C3. C2 and C3 are the two that own reconstruction and tenure/state-vector mismatch, which is the scope the
  packet's acceptance criteria cite. This record does not establish proof or DONE status for the other twelve
  capabilities, and it does not claim to. The "exactly" wording is inaccurate. Correcting the disposition text belongs to the Factory
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
