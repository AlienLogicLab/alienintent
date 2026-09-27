# Python-only cutover — Node/bootstrap surface inventory audit, 2026-09-27

Status: **inventory audit, no release action taken**. Performed under Director inbox
handoff `director-followthrough-python-cutover-audit-20260927T0340Z`, which itself carried
forward the audit portion of `founder-full-python-only-factory-20260927T0306Z`
(Founder decision `docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`).
Investigated by Factory Director episode `factory-director-ffa765583b8c4e50b020466aad3a3369`.

This is inventory only, per the handoff's own boundary: no AlienIntent Node service,
alias or scheduled launcher was stopped, restarted or reconfigured while producing this
record.

## Precondition check (required before any release action)

- `~/.local/state/alienintent/state.json` `active` map read directly: one non-terminal
  claim (`AlienLogicLab/alienintent#127:PRODUCER`, started `2026-09-27T03:22:33.874Z`,
  worktree `.../e66ba71f-...`). A second entry (`#127:VERIFIER`) carries a terminal
  `"result": "REJECT"` and is not counted as active capacity — consistent with the
  factory-director-host adapter's `activeClaims: 1` in `inputs.diagnostics.json`. This
  matches the already-documented WO-220601/WO-220507 overlap incident
  (`docs/evidence/wave2-wip-overlap-incident-20260927.md`), not a new incident.
- `wipLimit` in `~/.config/alienintent/factory-director-host.json` is `1`. Active claims
  (1) are at, not above, the limit.
- `tools/live/release_admission.py`'s global active-claim guard (`admit()`,
  `tools/live/release_admission.py:81-91`) is present at current `HEAD`/`origin/main`
  (`b23f6eb`) and refuses admission whenever `active_total >= wip_limit`.
- No release action (READY -> IMPLEMENT/VERIFY/ACCEPT) was attempted or is proposed by
  this audit for R7/R8/R9/B9 or any other Issue; this satisfies the handoff's
  precondition and its instruction not to release anything as part of the audit itself.

## 1. Installed AlienIntent `systemd --user` units (ALIENLAPTOP, observed 2026-09-27)

| Unit | Enablement | Running now | ExecStart | Role |
|---|---|---|---|---|
| `alienintent.service` | disabled (but manually started; active) | yes, pid `2422840` | `node bin/alienintent.mjs --config ~/.config/alienintent/self-hosting.json` | **The only persistent Node.js AlienIntent process on this host** — the dispatcher/webhook relay/worker-launcher (`src/runtime/dispatcher.mjs`, `src/runtime/worker-runner.mjs`, `src/runtime/worktree-manager.mjs`, `src/github/*`). |
| `alienintent-factory-director-host.service` | enabled, active | yes, pid `1593754` | `factory-director-host/factory_director_host...` (Python) | Non-cognizant host that launches Director episodes (FDH-01, Issue #89). Already Python. |
| `alienintent-liveness.service` | enabled, active | yes, pid `2453523` | `python3 .../liveness.py` | SWF-29 temporary bootstrap liveness reconciliation. Already Python. |
| `alienintent-observer.service` | enabled, loaded/active | yes (per `systemctl`, though `ExecStart` shows no live pid at query time) | `python3 .../observer.py` | SWF-27 bootstrap lifecycle observer, observation only. Already Python. |
| `alienintent-sandbox-tunnel.service` | enabled, active | reported active by `systemctl`, no live pid at query time | `cloudflared ... tunnel run` | PY-10 sandbox ingress tunnel, SWF-08, Wave 1 temporary infra. Not Node; not Python either — a separate binary. |
| `alienintent-project-add-probe.service` / `.timer` | static / disabled | not running at query time | `project_add_recovery_probe.sh` | Shell probe/recovery script; unrelated to Node/Python execution authority. |
| `alienintent-73e88e71...service` (transient) | transient, created per-invocation | ephemeral | `systemd-run --user --wait --unit=... ` wrapping a worker CLI invocation | Created dynamically by `alienintent.service`'s `worker-runner.mjs` for each PRODUCER/VERIFIER invocation; not an independent persistent surface, and not itself Node — it supervises the (non-Node) `claude`/`codex` worker CLI processes. |

## 2. Running Node.js processes (ALIENLAPTOP, observed 2026-09-27), classified

AlienIntent factory dependency:
- pid `2422840` — `node bin/alienintent.mjs --config ...` (`alienintent.service`). **The sole
  AlienIntent Node.js process.**
- pid `2524448` — `systemd-run --user --wait --unit=alienintent-73e88e71...`, spawned by
  `2422840`; not itself Node, but part of the same dispatcher's worker-supervision path.

Unrelated developer tools (not touched, not in scope):
- pid `2524495`, `2523541`, `1197467` — `node .../gitnexus mcp` (GitNexus MCP server
  instances attached to separate Claude Code sessions, including this episode's own and a
  worker's).
- pid `2640` — `node .../desktop-commander remote` (unrelated dev tool via npx).
- pid `1197392` — `claude --resume ...` (a separate, unrelated Claude Code session; not
  AlienIntent).
- pid `2524449` — a worker CLI (`claude -p --no-session-persistence ...`) currently doing
  the PRODUCER rework for Issue #127; not itself Node (the worker adapters are `claude`/
  `codex` binaries, not Node processes), and already accounted for as the active claim
  above.

**Finding: exactly one Node.js-backed AlienIntent surface is running on this host —
`bin/alienintent.mjs` / `alienintent.service`.** No other persistent AlienIntent Node
process exists to inventory.

## 3. Node-backed surface -> predecessor replacement BIU mapping

| Node-backed surface | Predecessor replacement BIU | Proof status | Intended final state |
|---|---|---|---|
| `bin/alienintent.mjs` / `alienintent.service` (dispatcher, webhook relay, worker launcher, worktree manager, GitHub authority) | **R7 / WO-220607** ("Replacement gate: Node/bootstrap execution authority") | Candidate-only (`docs/evidence/wave2-candidate-bius.md`: `GAP_BLOCKED`; `completion_status: SEPARATE_AUTHORITY_REQUIRED` in the DAG). No GitHub Issue materialized yet — `docs/work-units/wave2/WO-220607.md` exists but has no Issue number. Depends on `R6, R3, R4, R5, B6` (none of which are yet DONE). | `M-R7` (`retire_by_proven_replacement`, `source_transition_step: 15`): retain existing Node dispatcher and its protections; require every upstream replacement's proof and authority; consider Node retirement only after full sovereignty proof and an explicit cutover decision; read back protection continuity before ending the mechanism. `DAG scope: KEEP_UNTIL_REPLACED` — this is a future gate, not a scheduled removal. |

No other currently-running AlienIntent surface is Node-backed, so no other surface needs a
predecessor mapping for *this* audit's purpose. (`alienintent-project-add-probe.*` and
`alienintent-sandbox-tunnel.service` are non-Node and outside R7's own "Node/bootstrap
execution authority" scope; they map to other transition-plan steps, see below.)

## 4. Does R7 + R8 + R9 + B9 exhaust factory Node/bootstrap retirement?

**No.** Cross-referencing `docs/evidence/wave1-bootstrap-retirement-matrix.json`'s full
17-step `transition_plan` against `docs/evidence/wave2-dependency-dag.json`'s
`bootstrap_replacement_sequence` (which assigns a gate node to exactly 9 of the 17 steps):

| Step | Mechanism | Gate node | Covered by R7/R8/R9/B9? |
|---|---|---|---|
| 1 | SWF-26 PY-04 mutation gate | none | no — **no BIU or authority-gate linkage anywhere** |
| 2 | eighteen external bootstrap modules | none | no — **no BIU or authority-gate linkage anywhere**; the Founder's own cutover decision doc separately flags per-component custody/replacement/consumer disposition for these as still needed |
| 3 | SWF-21 release authority | none (authority-gate ref only, `SWF-21_SCOPE_DISPOSITION`, inherited by R7) | partially — disposed as an authority question for Wave 2 successor use via SWF-35 (see WO-220506.md "Authority disposition"), but no dedicated BIU |
| 4 | PRODUCER-on-Claude temporary profile change | none | no — **no BIU or authority-gate linkage anywhere** |
| 5 | sandbox ingress tunnel (`alienintent-sandbox-tunnel.service`, still running) | none | no — **no BIU or authority-gate linkage anywhere** |
| 6 | coordinator checkpoint | R1 / WO-220601 | yes, but not by R7/R8/R9/B9 (by R1) |
| 7 | Program Director mailbox bridge waiter | R2 / WO-220602 | yes, but not by R7/R8/R9/B9 (by R2) |
| 8 | Windows notification | none (authority-gate ref only, `WINDOWS_NOTIFICATION_DISPOSITION`, inherited by R7) | partially — authority question referenced, no dedicated BIU |
| 9 | session-bound attention waiter | none (authority-gate ref only, `ATTENTION_ACTIVATION_AUTHORITY`, inherited by R7/B9/R9) | partially — authority question referenced, no dedicated BIU |
| 10 | resident coordinator multi-BIU tenure | none (authority-gate ref only, `RESIDENT_TENURE_DECISION`, inherited by R7) | partially — authority question referenced, no dedicated BIU |
| 11 | bootstrap release-admission gate | R6 / WO-220606 | yes, but not by R7/R8/R9/B9 (by R6) |
| 12 | SWF-29 liveness reconciliation (`alienintent-liveness.service`, still running) | R3 / WO-220603 | yes, but not by R7/R8/R9/B9 (by R3) |
| 13 | SWF-27 observer (`alienintent-observer.service`, still running) | R4 / WO-220604 | yes, but not by R7/R8/R9/B9 (by R4) |
| 14 | attention queue | R5 / WO-220605 | yes, but not by R7/R8/R9/B9 (by R5) |
| 15 | Node/bootstrap execution authority (`bin/alienintent.mjs`, still running) | **R7 / WO-220607** | **yes** |
| 16 | b-disp command compatibility alias | **R8 / WO-220608** | **yes** |
| 17 | Local Program Director bootstrap orchestration role | **R9 / WO-220609** (B9/WO-220512 is a co-dependency, "programme completion or bounded successor custody", not itself a retirement gate for this step) | **yes** |

R7+R8+R9+B9 directly gate only steps 15, 16 and 17. Together with R1-R6 (steps 6, 7, 11,
12, 13, 14), the full Wave 2 DAG's 9 assigned gate nodes cover 9 of the 17 steps. **Eight
steps (1, 2, 3, 4, 5, 8, 9, 10) have no dedicated retirement-gate BIU at all.** Four of
those (3, 8, 9, 10) at least surface as named authority-gate references inherited by
R7/R9/B9 (`SWF-21_SCOPE_DISPOSITION`, `WINDOWS_NOTIFICATION_DISPOSITION`,
`ATTENTION_ACTIVATION_AUTHORITY`, `RESIDENT_TENURE_DECISION`) — i.e. R7/R9 cannot
themselves close until those authority questions are disposed, even though no BIU
implements them. The other four (1, 2, 4, 5) have **no linkage of any kind** — no gate
node and no authority-gate reference — anywhere in the reviewed DAG/matrix text.

This finding is consistent with, not a contradiction of, the Founder's own cutover
decision doc (`docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`),
which already states R7 alone is not the finish line, names R8/R9/B9 as required
additions, and explicitly records that this exact gap-exhaustion audit had not yet been
performed ("What this episode did and did not do").

## Revised critical path

1. **R7 (WO-220607)** remains the only BIU gating the one Node process actually running on
   this host (`bin/alienintent.mjs`). It depends on R6, R3, R4, R5, B6 — none yet DONE —
   so it is not independently accelerable ahead of them.
2. **R8/WO-220608** and **R9/WO-220609 + B9/WO-220512** are real, already-identified
   candidate BIUs (candidate-only, no Issue yet) gating steps 16 and 17 respectively; they
   are additive to R7, not alternatives to it, consistent with the Founder decision doc.
3. **Steps 1, 2, 4, 5 are a genuine, previously unrecorded gap**: no BIU and no authority
   gate reference exists for the SWF-26 PY-04 mutation gate, the eighteen external
   bootstrap modules, the PRODUCER-on-Claude temporary profile change, or the sandbox
   ingress tunnel (all four still-observable, still-running or still-installed mechanisms
   per section 1 above). Designing whether these need one bounded prerequisite BIU each,
   one combined BIU, or a Founder authority disposition (some of them may be intentionally
   out of Wave 2's scope, e.g. Wave 1 temporary infra already covered by its own SWF
   decision) is itself a non-trivial SPECIFY-shape question — it deserves the same kind of
   dedicated, focused episode previously recommended for Issue #126's isolation design,
   rather than being decided inline in this inventory audit. **Not attempted this
   episode**; recorded here as the concrete next step for a successor.
4. **Steps 3, 8, 9, 10** are narrower: each already has a named authority-gate reference
   inherited by an existing gate node (R7/R9/B9), so the missing piece is a Founder/SPECIFY
   disposition of that named authority question, not a new BIU design from scratch. Step 3
   (SWF-21) is already substantially disposed for Wave 2 successor use per WO-220506.md's
   "Authority disposition" section; 8, 9 and 10 remain open.

## Boundaries observed

No AlienIntent Node service, alias or scheduled launcher was stopped, restarted, enabled,
disabled or reconfigured while producing this record. No unrelated non-AlienIntent Node
tool (GitNexus, Desktop Commander, other Claude Code sessions) was touched. No DAG or
candidate-BIU count was changed by this audit — the gap it identifies is reported for a
successor's SPECIFY-shape decision, not resolved unilaterally here.
