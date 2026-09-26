# FX-E1 repair 1 — harness repair after run `20260926T100158Z` held

Run `20260926T100158Z` (candidate source `dc56851`, the pinned fixture) is
retained unchanged at [`runs/20260926T100158Z/proof-run.json`](runs/20260926T100158Z/proof-run.json).
Its disposition is **HOLD**: E1-3, E1-6 and E1-7 held. This record states why
each hold happened, what was repaired and what was deliberately not changed. It
is committed before the next live run.

## Causes

| Predicate | Held because | Class |
|---|---|---|
| E1-6, E1-7 | Both BIUs reached `VERIFY` with `outcome=failure`. The shipped `RealWorkerProvider` (since WO-220404/K3 and the feature-regression gate) requires the VERIFIER process to leave `.alienintent/verdict.json` bound to the candidate revision, plus a `FeatureRegressionReceipt` at `.alienintent/feature-regressions.json`. The FX-E1 worker knew only the PRODUCER role, so its verifier invocation exited non-zero and the coordinator held the work, as designed. The sandbox's own Wave 1 `worker/run.sh` has the same gap. | Harness (worker substitute). No defect in the Python transport or control plane: the coordinator refused to accept an unverified candidate. |
| E1-3 | The dependency probe counted interpreter start-up `.pth` hooks from the host's site-packages (`apport_python_hook`, `_distutils_hack`, `zope` namespace, two editable finders for unrelated packages) as production-path modules. The Node-reference pattern also matched a GraphQL `.get("node")` field. The sampler observed **0 Node processes and 0 shim invocations across 173 processes and 3539 samples**. | Measurement defect (false positives) |

The rest of run 1 is retained as observed. Real deliveries were admitted with durable receipts. A delivery admitted by the
restarted process B was redelivered by GitHub to a further restarted resident
ingress (process D) and accepted (202), and its durable receipt, effect and
notification count were unchanged. All three out-of-scope local deliveries were refused (401) without a
receipt. The Node writer and its ports were undisturbed.

## Repair (harness only; no `src/` change)

1. `tools/live/fx_e1_worker.sh` is now role-aware. As VERIFIER it checks the retrieved
   candidate against the contract's completion criterion: heading, exactly one bullet, and exactly
   the named path changed. It then writes the verdict and a receipt in the shipped
   `FeatureRegressionReceipt` schema. The sandbox registers no regression packs, so
   the receipt carries `packs: []` and says so. It remains a labelled substitution for
   a provider.
2. `dependency_path` measures the closure that importing the control plane and the
   sandbox composition adds. The interpreter start-up set is recorded separately as
   `interpreter_startup_modules_outside_stdlib`. The Node-reference pattern now matches
   a Node executable as an argument-vector element or a quoted `.mjs` path.
3. Delivery attribution covers every resident control-plane process window
   (`decisions`, `status` and `explain` processes are resident too). E1-4 now requires
   *every* accepted delivery to fall in some control-plane process window.
4. Each run writes `runs/<run-id>/proof-run.json`, so a held run is never
   overwritten. `manifest.json` names every run and the accepted one. The regression
   test replays every retained run's disposition.

Unchanged: every predicate's meaning, the pinned identification, the authority
scope, the seeded-work shape, and the live target.
