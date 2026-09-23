# FX-C1 — durable attention identity and resolution

**Owner:** `WO-220301` / DAG node `C1`.  **Status:** `PLANNED_NOT_EXECUTED`.

This is the proof contract for the bounded C1 implementation. It is a disposable local composed/mechanical fixture. It neither authorizes nor demonstrates live operation, deployment, unattended activation, a Factory Director Host cutover, or retirement of any existing protection.

## Fixed inputs and environment

- exact C1 candidate contract: `docs/evidence/wave2-candidate-bius.json#/bius/14`, source revision `fcb65fffda65fc2a01516aed38d8d5a662cbaba8`, blob `64c113e6788728be3930e1f5a300f83a96f5ec70`;
- exact admission packet and allocation: `docs/evidence/wave2-execution-packets/WO-220301.{packet,allocation}.json`;
- retained predecessors: S1 `b80d0cb502d68589a3907331f1db802280c67c5f` and S2 `8e2547980ca1d95849460b9abf0c08857a6671b9`, with the independent verdict and closure links recorded in the packet;
- disposable local store/profile, injected clock/IDs, recorded notification-channel failure, and a model-launch spy that fails if called. No production profile, service, webhook, provider call, or external model launch is permitted.

## Required probes

| Probe | Command / input | Intact result | Fault result | Restored result |
| --- | --- | --- | --- | --- |
| `attention_identity_restart` | `python3 -m pytest -q tests/**/test_*attention*.py -k 'restart or dedupe or origin'` against duplicate DONE and judgment events before/after store re-open | one preserved origin identity and attributed history; no duplicate attention | remove identity/dedupe guard: assertion fails | original guard restored: focused suite passes |
| `attention_delivery_pending` | same focused suite against a forced channel failure | pending item retained with failed-attempt diagnostic; fresh authorized consumer can inspect it | bypass durable creation/consumer bridge: assertion fails | pending item and history read back |
| `attention_resolution_authority` | same focused suite against SEEN, wrong actor, wrong revision, and wrong lane attempts | each attempt refuses to resolve; DecisionInbox remains distinct | remove actor/revision/lane guard: assertion fails | only matching authorized resolver can resolve |
| `attention_unbound_activation` | same focused suite with activation authority absent and model-launch spy installed | notification/attention only; spy count exactly zero | bypass unbound-activation refusal: assertion fails because spy records a launch | restored refusal yields zero launches |
| `fx_c1_evidence` | `python3 tools/evidence/fx_c1_evidence.py --output <retained-fixture-dir> --invocation <exact-invocation>` | every probe records command, inputs, exit status, immutable observation references, mutation count, and readback | each injected fault exits nonzero at its corresponding assertion | restored probes exit zero and retain the original fault observations |
| regression | `python3 -m pytest -q`; `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`; `node scripts/check.mjs all` | all pass on the candidate | not applicable | rerun only after a repair affecting this surface |

The producer may add a narrower named test module or glob only if it covers every listed probe; the final retained record names the exact path and command. A missing command, unavailable fixture, non-discriminating mutation, absent readback, or model-launch measurement that is not exactly zero is a hold, not a pass.

## Evidence contract

Retain in `docs/evidence/wave2-proof-fixtures/FX-C1/`:

1. `execution-record.json`: exact candidate, fixture/profile/input digests, invocation, command, exit status, observed result, model-launch count, and measurement values. Tokens/cost are actual provider values where reported, otherwise `null` plus `UNKNOWN` reason—never zero by inference.
2. `run-report.json`: acceptance-to-probe mapping for `SF-REQ-053-AC-05` and `SF-REQ-053-AC-06`, including restart, failed delivery, fresh-consumer readback, resolution refusal, DecisionInbox separation, and unbound activation.
3. `proven-red.json`: one independently applied fault and nonzero assertion outcome per mechanical guard, then restored success, with mutation application count.
4. immutable raw observation objects and their digest manifest; preserve prior observations on repair rather than overwriting them.

An independent verifier retrieves the producer’s published candidate and reruns the focused fixture, evidence generator, architecture check, and relevant regression commands in a fresh worktree. Local evidence remains local-composed proof only.
