# FX-U10 candidate adoption record (WO-220210, Issue #111)

`FX-U10.md` is digest-pinned in `proof/execution-record.json`
(`sha256:5d3efc7c…aa0a4`), so it is left unchanged. This note records custody after it was written and corrects one
statement in it.

## Custody chain

| PRODUCER invocation | Branch | Outcome |
|---|---|---|
| `AlienLogicLab/alienintent#111:PRODUCER:1ad8a070-67f1-4d68-94d5-8c3f434474c8` | `b-disp/2be43995-e898-4b49-8345-91f49cd7dcd9` | Authored `2d7e135` and `3b8437f`. Ended `DURABLE_RESULT_MISSING`; nothing published. |
| `AlienLogicLab/alienintent#111:PRODUCER:3dc6d26a-05e7-4e4f-806d-9db6084e2983` | `b-disp/4e175835-044f-4bed-b9cb-87c01c0c8ba1` | Adopted both by fast-forward, committed `9cff5a8`, then ran the evidence runner to completion (exit 0) at clean `9cff5a8`. It left the output uncommitted and ended **without publishing a branch or posting a result**. |
| `AlienLogicLab/alienintent#111:PRODUCER:aaf89c50-a504-422c-a0e2-eb658e74c59b` | `b-disp/77998cd4-b2b4-448c-947d-e62cfe862109` | Adopted `9cff5a8` unchanged by fast-forward from the RELEASED baseline `1163caf`. Retained the runner output and published the candidate. |

**Correction.** `FX-U10.md` says invocation `3dc6d26a` "published the candidate". It did not: no remote branch and
no Issue result exist for it. This invocation (`aaf89c50`) publishes it.

## Retained proof: `proof/`

- Copied byte-for-byte from the `3dc6d26a` worktree; `diff -r` found no differences.
- Every file in `proof/observations/` hashes to its own name.
- `execution-record.json`:
  - `source_revision` is `9cff5a8d7e4aefa8a63cc15d14a9889d140bf076` with clean `source_status`;
  - `invocation` is `…3dc6d26a…`;
  - `holds` is empty and `exit_status` is 0.
- The focused, native credential-free, native assessment, U9 consumer, architecture, architecture fitness and Node
  commands all exited 0.
- Full Python regression: exit 1 with 25 failures, the same 25 as at the baseline. `new_failures=0`, disposition
  `PRE_EXISTING_BASELINE_FAILURES_ONLY` (see `FX-U10.md`, "Baseline regression failures").
- `proven-red.json`: C1–C5 each applied once, intact 0 → fault 1 → restored 0, `discriminates=true`, no holds.

The candidate adds only documentation and evidence on top of `9cff5a8`. `git diff --stat 9cff5a8..<candidate>`
touches only `docs/evidence/wave2-proof-fixtures/FX-U10/`, so the run applies to the candidate's code unchanged.

## Re-checks by this invocation at `9cff5a8` (not retained as runner observations)

- Every path-keyed `input_digests` entry in `execution-record.json` matches the file in this worktree.
- `python3 -B -m pytest -q tests/context_assembly/test_readiness_transport.py tests/context_assembly/test_readiness_consumer.py`
  gave 129 passed and 4 skipped (the native opt-in probes).
- `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all` passed all architecture fitness
  checks.
- `FX_U10_AGENT_READY_BIN=/mnt/d/Projects/agent-ready/.venv/bin … -k "native and not assessment"` gave 2 passed.

The independent verdict is still `PENDING_FRESH_BIU_VERIFIER`. Proof is `LOCAL_COMPOSED_OR_MECHANICAL`. Nothing here
authorizes release, lifecycle transition or live operation.
