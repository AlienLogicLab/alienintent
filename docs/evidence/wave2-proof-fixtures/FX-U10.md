# FX-U10 — Agent Ready CLI/MCP transport boundary (WO-220210, U10)

Authority: the Issue #111 RELEASED record (Factory Director episode
`factory-director-311c232516784569bb9d2e814a42ad5f`, 2026-09-25T22:36:34Z). It authorizes IMPLEMENT for WO-220210
and pins baseline `1163caf4c6844d2f41dbe3ad24ee6040e202de11`. It also corrects the earlier unreleased transition that
PRODUCER invocation `…#111:PRODUCER:d39380a8-…` refused.

The pinned proof packet is `docs/evidence/wave2-execution-packets/WO-220210.proof-packet.md`. The work unit is
SF-REQ-015, node U10, capability `assigned_assessment_binding`. Worker Morty authored this through PRODUCER invocation
`AlienLogicLab/alienintent#111:PRODUCER:1ad8a070-67f1-4d68-94d5-8c3f434474c8`, on branch
`b-disp/2be43995-e898-4b49-8345-91f49cd7dcd9` (commits `2d7e135`, `3b8437f`).

That invocation ended at runtime outcome `DURABLE_RESULT_MISSING`: its session finished while the evidence runner
was still going, so it published no branch and no result. Its partial proof output was never committed and is not
evidence. The next PRODUCER invocation, `AlienLogicLab/alienintent#111:PRODUCER:3dc6d26a-05e7-4e4f-806d-9db6084e2983`
(Morty, branch `b-disp/4e175835-044f-4bed-b9cb-87c01c0c8ba1`), adopted both commits unchanged by fast-forward from the
same RELEASED baseline. It re-ran the probes, ran the evidence runner to completion and published the candidate.

Proof level is `LOCAL_COMPOSED_OR_MECHANICAL`. Nothing here authorizes release, lifecycle transition or live
operation.

## Admission (verified before implementation)

- **Baseline.** HEAD was `1163caf` (`origin/main`), which equals the RELEASED baseline.
- **Contract.** `docs/work-units/wave2/WO-220210.md` has sha256 `f545ad4b…09cbc`. This equals `input_sha256` on the
  native READY receipt `WO-220210.2026-09-25T090303.988150Z.assessment.json`, producer `agent-ready-cli` 0.1.0rc1 at
  `7fbe821`.
- **Dependency.** WO-220209 (#105) is DONE.
- **Authority.** No authority gap or gate is recorded. The runner re-measures the pinned digests at the baseline and
  at the candidate, and a mismatch holds with exit 2.

## Ownership (C#/contracts/4/ownership_statement, DV-5)

The Agent Ready product owns assessment semantics, its implementation, its public schema, the CLI and the local MCP.
U10 owns only the integration: the transport adapters and their binding at composition.

Nothing is imported from `agent_ready`, and no rubric, prompt or schema is copied. The architecture checker's
`private-product` check still passes. The conformance fixture pins the *published* contract by digest of the public
README, schema and spec at `7fbe821`; it does not restate them as authority.

## Implementation (U10 extent)

- **`execution_coordination/adapters/agent_ready_producer.py` (new).** Both classes implement the existing
  `ReadinessAssessment` port and are constructed from the resolved `ProducerBinding`.
  - **`AgentReadyCliAssessment`** runs `assess <file> --provider <p> --json`:
    - it returns stdout bytes unparsed, with the exit status;
    - custody holds the attempt it launched for, the digest of the submitted file read back, the argv and
      timestamps.
  - **`AgentReadyMcpAssessment`** runs one stdio session per attempt:
    - it sends `initialize`, then `tools/call assess_work_unit {text, provider}` using the attempt ID as the JSON-RPC
      id;
    - it returns the exact response line, **wrapper included**, with no exit status;
    - custody `attempt_id` is the id **the response carries**, so a response to another request is
      `RESPONSE_NOT_CORRELATED`;
    - `serverInfo.version` is recorded as `sdk_version`, never as `product_version` (agent-ready#1).
  - **Both adapters:**
    - text is never truncated, because the limits are the product's;
    - each launch is in its own session, and its process group is killed at the deadline and on return;
    - the MCP deadline is enforced by a watchdog, including during writes.
- **`composition/readiness.py`.** `compose_producer(binding, provider)` selects the CLI or MCP adapter by
  `binding.transport`. The launched executable is therefore exactly the one whose installed metadata established
  `product_version`. The inherited API-key variables Agent Ready must not see are filtered in composition, which is
  the only layer allowed to read the environment. This closes U9 residual
  `PRODUCER_ADAPTER_NOT_CONSTRUCTED_FROM_BINDING_U10`.
- **`composition/upstream_profile.py`.** `readiness_provider` is a compatible addition. When it is set, the producer
  is constructed from the binding. Configuring both it and an injected `readiness_producer` is a `ValueError`. The
  injected path remains for the U9 fixture probes.
- **Domain (`execution_coordination/domain/readiness.py`), additive only.**
  - `_envelope` unwraps a preserved JSON-RPC response. A wrapper with an `error` member is `MCP_ERROR`, even beside a
    `result`. An unknown wrapper member or a `jsonrpc` other than "2.0" is `MALFORMED`.
  - `InvocationCustody` gains the optional `sdk_version`, and it is type-checked.
  - **Deviation from the AC-06 wording "without changing domain code", justified.** "Preserve wrappers" (design
    decision 0) and byte-for-byte raw retention mean the consumer must receive the JSON-RPC line itself. The
    provenance contract requires `sdk_version` to be recorded separately. Both changes are strictly additive: a
    bare tool result still parses exactly as before, and the full U9 suite is unchanged and green.

## Material failure classes → probes (`tests/context_assembly/test_readiness_transport.py`)

| Class | Probes |
|---|---|
| 1. A configured public binding reaches the consumer with raw response and invocation/product provenance | `test_cli_binding_reaches_consumer_with_raw_response_and_custody`, `test_mcp_binding_reaches_consumer_with_raw_response_and_custody`, `test_text_over_the_published_limit_is_submitted_untruncated[cli,mcp]`; native: `test_native_assessment_reaches_consumer[cli,mcp]` |
| 2. Unbound, wrong product/version, surrogate or disconnected response refuses | `test_unestablished_binding_holds_before_launch[unbound,version_unknown,wrong_package × cli,mcp]` (CAPABILITY_PROVENANCE_HOLD, zero launches), `test_disconnected_mcp_response_is_refused`; a schema-perfect surrogate or copied `provider_evidence` stays covered by the U9 probes P21 (K25/K26) |
| 3. Malformed, conflicting, missing or provider-error result is an attempt failure | `test_failed_attempt_is_never_ready[9 cases]`, `test_timeout_is_an_attempt_failure[cli,mcp]`, `test_wedged_mcp_server_cannot_outlive_the_deadline`, `test_json_rpc_wrapper_parity_and_malformed_wrappers`; native: `test_native_mcp_error_reaches_consumer_as_attempt_failure`, `test_native_cli_usage_error_reaches_consumer_as_attempt_failure` |
| 4. READY is eligibility only and cannot bypass the release gate | `test_transport_ready_is_eligibility_only[cli,mcp]` (zero `admit_release` calls, no `factory:`/`release:` writes); native assessment probes assert the same |

The deterministic probes launch a labelled stand-in executable (`FIXTURE_EXECUTABLE_NOT_AGENT_READY`) as a real
subprocess over the pinned contract. They prove transport, custody and refusal mechanics, never native identity.

The native probes launch the configured product itself and are opt-in:
- `FX_U10_AGENT_READY_BIN` enables them;
- the error and usage probes are credential-free;
- the two provider-backed assessments also need `FX_U10_NATIVE_ASSESS=1`.

## Controls (one per material class, plus one review repair)

| Control | Class | Mutation | Probe that must fail |
|---|---|---|---|
| C1 | 1 | MCP adapter retains only the unwrapped `result` | MCP binding probe (raw bytes and wrapper) |
| C2 | 2 | MCP custody trusts its own request id instead of the response's | disconnected-response probe |
| C3 | 3 | a JSON-RPC `error` beside a `result` is admitted | `failed_attempt_is_never_ready[mcp_json_rpc_error_beside_ready]` |
| C4 | 4 | consumer writes `release:` on an applicable READY | `transport_ready_is_eligibility_only[cli,mcp]` |
| C5 | R1-4 | group kill replaced by a direct-child kill | `timeout_leaves_no_descendant_running[cli]` |

Each control is applied exactly once to a disposable copy. It must go intact 0 → fault 1 at the named assertion →
restored 0. The runner holds if any control fails to discriminate.

## Independent pre-candidate review (R1) and repairs

A fresh read-only reviewer (a Claude subagent outside this producer's context) found no path by which a non-native,
disconnected, malformed or error result becomes READY. It confirmed the pinned contract against the live product's
`tools/list`. It returned **REJECT** with three blocking findings:

1. **The MCP deadline was not enforced during request writes.** A server that stopped reading blocked an oversized
   request past `timeout_s` and left the attempt open. This was reproduced first as a failing probe: the run hung and
   was killed with exit 143. The repair is a watchdog that kills the session's process group at the deadline. The
   probe is `test_wedged_mcp_server_cannot_outlive_the_deadline`. It has no mutation control because its fault mode
   hangs rather than failing by assertion; the red run is recorded here instead.
2. **The runner did not copy `tools/fitness`**, so no control could discriminate. Repaired.
3. **This plan file was missing.** Added.

Non-blocking findings:
- **Timeouts orphaned provider descendants.** Repaired with new-session launch and a process-group kill for both
  adapters. The probe `test_timeout_leaves_no_descendant_running[cli,mcp]` was red first, and control C5 covers it.
- **The JSON-RPC id is correlated by the adapter, not the domain.** Recorded as residual
  `JSON_RPC_ID_CORRELATED_BY_ADAPTER_NOT_DOMAIN`. The adapter takes the id from the same message it retains, and
  the domain checks it against the attempt.
- **Domain change versus the AC-06 wording.** Justified above.

## Commands (under `rtk proxy`, `PYTHONPATH=src:.`)

1. `python3 -B -m pytest -q tests/context_assembly/test_readiness_transport.py`
2. `python3 -B tools/evidence/fx_u10_evidence.py --output docs/evidence/wave2-proof-fixtures/FX-U10/proof --invocation <invocation> --agent-ready-bin /mnt/d/Projects/agent-ready/.venv/bin --native-assess`,
   run against the committed candidate. This command:
   - runs the focused, native, U9, full Python, architecture and Node checks;
   - runs the controls;
   - compares the full Python regression against the same run at the baseline, in a temporary worktree.

## Recorded limitations and non-claims

- **Contract version (agent-ready#1).** The contract is bound to the package release. Results carry no product or
  schema version. The CLI has no `--version`. MCP `serverInfo.version` is the SDK version.
- **Model provenance** is `UNKNOWN`. `provider_evidence` is retained unmodified and never trusted.
- **Usage.** Tokens and cost are not exposed by Agent Ready v0.1, so they are recorded as `UNKNOWN`, never zero.
- **Baseline regression failures.** At the baseline, 25 tests in `tests/evidence_learning/test_proof_planning.py`
  already fail, because the `wave2-design-contracts.json` digest drifted at `308188c`. They are outside U10 and are
  returned to their owner. The runner names them from its own baseline run rather than calling them PASS.
- **Not claimed:** U8 split transaction; SF-REQ-029 serialization; the operator surface; release; operational
  acceptance.
