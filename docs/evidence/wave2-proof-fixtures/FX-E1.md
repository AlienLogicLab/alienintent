# FX-E1 — Existing canonical live transport prerequisite (WO-220502, DAG node E1)

**Disposition of the accepted run: PASS (10/10 predicates), run `20260926T101450Z`.**
This result is a PRODUCER result. It awaits an independent verifier and is not a
verdict. Two earlier runs held and are retained unchanged; see [runs](#runs-and-repairs).

Authority: EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY (Director inbox
`founder-live-transport-proof-authority-20260926T070519Z`, recorded in
[`docs/work-units/wave2/WO-220502.md`](../../work-units/wave2/WO-220502.md)). The BIU was released
READY → IMPLEMENT under SWF-35 on Issue #122. The proof used only the authorized target.
It performed no release, cutover, Node/bootstrap retirement or sibling-BIU work, and touched
neither `AlienLogicLab/alienintent` nor Project #1.

## 1. Identification, before any live call

[`FX-E1/identification.json`](FX-E1/identification.json) was produced offline with zero network calls by
`tools/live/fx_e1_identify.py`. It was committed with [`FX-E1/fixture-plan.json`](FX-E1/fixture-plan.json) in
`dc56851`, before the first live call.

| | Identified |
|---|---|
| Profile | `py10-sandbox`, `~/.config/alienintent-sandbox/profile.json` (mode 600, digest recorded) |
| Production path | `python3 -m alienintent --profile-factory alienintent.composition.sandbox_run_profile:profile`, with 18 module digests pinned at `2715bec` |
| Scoped resources | repository `AlienLogicLab/alienintent-sandbox` · Project #2 `PVT_kwDOEcrpC84BkIEX` · ingress `127.0.0.1:8789` · tunnel `alienintent-sandbox` (connector: `cloudflared`, not Node) · App `alienintent-py-10-sandbox` |
| Custody | provisioning SWF-08 ([py10-sandbox.md](../../operations/py10-sandbox.md)), isolation SWF-34, secrets present with mode 600, key and secret paths redacted |
| Live Node writer (kept off) | `AlienLogicLab/alienintent`, Project #1, port 8788, one `bin/alienintent.mjs` process; all on the profile's must-not-touch list |

The only configured Python live profile is `py10-sandbox`. Its production path is the
shipped control plane bound to the real App installation, repository, Project, tunnel and
resident ingress. The AlienIntent repository and Project #1 belong to the Node writer.
Exercising them from Python would breach one-writer ownership.

## 2. What the accepted run did

Sandbox seed commit `869d9a4`: two fresh READY BIUs, `E1-261014-A` (P0, worker holds 45 s)
and `E1-261014-B` (P1). The operator wrote only `READY`; every other status was projected
by the factory.

1. `doctor`: exit 0 (transport probe through the public route).
2. Process **A** (`run service`) dispatched A. With the repository reservation held and
   `launch:E1-261014-A:0` unresolved, the whole process group was **SIGKILLed** (exit -9).
3. Process **B** (restart) held A for a decision (external effect outcome unknown),
   dispatched B through PRODUCER → VERIFIER → CLOSURE, and exited 0.
4. `decisions decide E1-261014-A --choice authorize`, recorded by the FX-E1 operator under the authority above.
5. Process **C** drained A to DONE: `eligible-backlog-exhausted`.
6. Process **D** restarted the resident ingress. GitHub redelivered a delivery that process B
   had admitted. It was accepted (202), and its durable receipt, `ingress:<guid>` effect and
   notification count were unchanged.
7. Readback: store `DONE`/`closed` for both BIUs; Project Status `DONE` for both; candidates
   `candidate/launch-E1-261014-A-3@19b490c` and `candidate/launch-E1-261014-B-0@f6b1a80`,
   each read back from a fresh clone. GitHub's delivery log was read with receipts joined.

## 3. Predicates (accepted run)

| | Predicate | Basis |
|---|---|---|
| E1-1 | pinned before any live call | plan and identification committed before the run; source clean at `08d91b6` |
| E1-2 | no-Node instrument discriminates | intact clean; Node by name (shim), by absolute path, and detached under a stated environment each detected; restored clean |
| E1-3 | no Node process or dependency | **203 processes / 3694 samples, 0 Node, 0 shim invocations**. Import closure: 147 modules, all stdlib or `alienintent`. No Node invocation in `src/alienintent`. Port 8789 held by the Python control-plane process (A) and by the resident (D) |
| E1-4 | real ingress, durable receipt | 5 real GitHub deliveries accepted (202), each with a durable receipt, all inside a control-plane process window |
| E1-5 | effect dispatch | each BIU's dispatch effect `confirmed`; each candidate published and independently read back |
| E1-6 | durable consumer outcome read back | store DONE, Project DONE, candidate content from a fresh clone, for both BIUs |
| E1-7 | restart with readback | A killed in flight, reconciled by decision and DONE; the redelivery to a restarted ingress left receipt, effect and notifications unchanged |
| E1-8 | invalid scope holds | unsigned, wrong-secret and correctly-signed-foreign-Project deliveries each got 401 with no receipt (LOCAL controls on the real resident); foreign Project address refused; installation scope is exactly the sandbox repository |
| E1-9 | one writer undisturbed | Node writer PID set `[2040299]`, ports 8787/8788 answers and root tunnel configuration mtime unchanged before and after |
| E1-10 | substitutions labelled | one substitution declared; local controls labelled |

Mechanical controls: [`FX-E1/negative-controls.json`](FX-E1/negative-controls.json). Each of K1–K10 applied one fault to a
copy of the accepted record (application count ≥ 1). Each held exactly its named predicate and restored to PASS.

Effect ledger per BIU: exactly one producer, one verifier and one closure effect `confirmed`, and one
published candidate branch. The killed `launch:E1-261014-A:0` is `authority-authorized`,
not re-executed as a second candidate.

## Runs and repairs

| Run | Source | Disposition | Record |
|---|---|---|---|
| `20260926T100158Z` | `dc56851` | HOLD (E1-3, E1-6, E1-7) | [record](FX-E1/runs/20260926T100158Z/proof-run.json) · [repair 1](FX-E1/repair-1.md) |
| `20260926T100920Z` | `4fb01d7` | HOLD (E1-6, E1-7) | [record](FX-E1/runs/20260926T100920Z/proof-run.json) · [repair 2](FX-E1/repair-2.md) |
| `20260926T101450Z` | `08d91b6` | **PASS** | [record](FX-E1/runs/20260926T101450Z/proof-run.json) |

Both holds were harness or sandbox-fixture causes. `src/` was not changed.

- **Repair 1.** The worker substitute knew only the PRODUCER role. The dependency probe counted host
  start-up `.pth` hooks and a GraphQL `"node"` field as false positives.
- **Repair 2.** The shipped `CliWorkerProvider` runs the *target repository's*
  `tools/verification/run_feature_regressions.py` before any verifier starts. The Wave 1 sandbox predates that gate
  and has no runner, so verification could not start there. FX-E1 seeding now installs the shipped runner
  byte-for-byte, plus one real sandbox pack. In both held runs the coordinator correctly refused to accept
  unverified work.

## Substitutions and non-claims

- **Worker note author** (labelled). `tools/live/fx_e1_worker.sh` writes the note as PRODUCER and
  judges it as VERIFIER instead of a provider CLI. It is launched by the shipped `CliWorkerProvider` via
  `RealWorkerProvider` and `RoleBindingGuard`. The control plane publishes and reads back with the installation
  credential. **No claim about provider behaviour, spend or helper processes.** A provider CLI on
  this host also starts MCP helpers, some of them Node, which are unrelated to AlienIntent.
- Sandbox operator setup: seed contracts and the verification kit were committed to sandbox `main`
  (`e1ac2ec`, `f71cea2`, `869d9a4`), and seed items were created READY in Project #2. The
  held runs' items remain at `VERIFY` in the sandbox Project. All candidate branches are retained as
  immutable observation references.
- Not claimed: release, operational use, sovereignty cutover, Node/bootstrap retirement, or
  token-level Project isolation (SWF-34). This is not operational-release authority.
- Tokens/cost: UNKNOWN. No provider was invoked by the run; the PRODUCER session's own usage is not exposed.

## Observations for their owners (not repaired here)

- **Deliveries between resident processes are lost.** GitHub recorded 502 with no durable receipt
  for two deliveries that landed at the edges of CLI process windows (within the ±2 s attribution slack). This is
  consistent with no process holding port 8789 at that moment: each CLI process is resident only for its own
  lifetime, and GitHub does not retry automatically. E1 proves transport per process and across restart. Continuous residency
  belongs to the resident-coordinator tenure scope (SF-REQ-053 / POSTW1-DECIDE-006A), not to E1.
- **The Wave 1 sandbox worker protocol is stale.** `worker/run.sh` in the sandbox knows only the PRODUCER role and
  would fail the current VERIFY protocol with a real provider as well.
- **Pre-existing baseline failures, unrelated to E1.** At `2715bec`, `python3 -m pytest -q` shows **25 failed, 1150
  passed, 4 skipped**. All 25 failures are in `tests/evidence_learning/test_proof_planning.py` (FX-U4 proof planning,
  `PlanHold DESIGN_MISMATCH`). This BIU changes no file on that path; route to its owner (WO-220204).
  At the candidate, `python3 -m pytest -q tests tools` shows 27 failed, 1960 passed, 4 skipped: the same 25,
  plus `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`
  and `tools/orchestration/test_factory_director_inputs.py::test_board_rows_from_the_read_path_carry_the_issue_repository`.
  Both also fail on a clean `git archive 2715bec`. The candidate changes nothing under `src/`, `tests/` or
  `tools/orchestration/`. The applicable feature-regression pack (`live-transport-proof-fx-e1`) passes.

## Re-running

On the provisioned host, with the sandbox tunnel active and port 8789 free:

```
python3 tools/live/fx_e1_no_node.py --self-test --json
python3 tools/live/fx_e1_live_proof.py --apply --output <dir>
python3 tools/live/fx_e1_evaluate.py <dir>/runs/<run-id>/proof-run.json --controls
python3 -m pytest -q tools/live/test_fx_e1.py      # offline; replays every retained run's disposition
```

A verifier without live authority can judge the retained records offline with the evaluator and the
regression test. It can also retrieve the sandbox candidate branches named above.

## Feature-regression receipt custody

`.alienintent/feature-regressions.json` binds the exact candidate SHA it was run against. A commit cannot
contain a receipt naming its own SHA, so the receipt is not a tracked file (the landed rule in
[FX-C.md](FX-C/FX-C.md#feature-regression-receipt-custody), present at baseline `2715bec`). The shipped
`CliWorkerProvider._feature_regressions` writes it into the verifier's checkout of the exact candidate before
launching the verifier, and `read_verdict` reads it there. When the runtime is not the launcher, the verifier
produces it in its own worktree at the retrieved SHA:

```
python3 tools/verification/run_feature_regressions.py --base 2715bec1094e8c85a81e56d2b69c115c7451f688 \
  --candidate HEAD --receipt .alienintent/feature-regressions.json
```

Candidate `bfab722` tracked a receipt for its parent `4e55623`. That receipt could never validate against the
commit carrying it, and the runtime would overwrite it in the verifier checkout. The superseding candidate removes
it. The PRODUCER records its own receipt for the published SHA on the Issue for comparison; it does not replace
the verifier-side receipt.
