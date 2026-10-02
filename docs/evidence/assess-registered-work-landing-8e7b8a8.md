# Assess registered work landing record (8e7b8a8)

Unit: ASSESS-REGISTERED-WORK. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `8e7b8a8382fde577b008aa292c721d95b3a6e4b2` (branch `producer/assess-registered-work-e64ef7b`, commits `93bc60d` and `8e7b8a8`).
- Merge base: `origin/main` `17e15bac3e98d21971b8060e2964674d6a872338`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/assess-registered-work.md`, assessed at `e64ef7b`. The file was already on `main` at `17e15ba`, byte-for-byte equal to the assessed revision (blob `1d3feb97aab16b5113dcb3784293d854c5438712`). The candidate does not change it.

## Approvals (private records, outside the repo; paths only)

- Agent Ready: READY for packet `e64ef7b`. Record directory: `~/.local/state/alienintent/manual/assess-registered-work-agent-ready-e64ef7b/` (`native-result.json`, `owner.json`).
- Founder implementation approval: `~/.local/state/alienintent/manual/assess-registered-work-agent-ready-e64ef7b/implementation-approval.json`.
- Design reviews: `~/.local/state/alienintent/manual/assess-registered-work-agent-ready-e64ef7b/independent-review-*.md` and `process-ownership-fix.md`.

## Real use (acceptance check 7)

Run by the Founder on the exact candidate before acceptance, in a separate terminal, against new private stores and a dedicated clone whose remote is a local bare repository. Record directory: `~/.local/state/alienintent/manual/assess-real-use/` (`RUN.md`, `register.json`, `assess-1.json`, `assess-2.json`, `show.json`).

- Work item `f5e34ec9-1959-4e12-afc7-0d9a934eac46` (label `assess-registered-work`) was registered from `main` `17e15ba`, path `docs/work-units/python/assess-registered-work.md`.
- First `work assess`: ran Agent Ready once. Disposition READY, attempt `73aab5fb-632f-40c0-b26b-0fc7f61f55ad`, `reused: false`.
- Second `work assess`: ran nothing. Same attempt, `reused: true`.
- `work show`: `assessment_ref` is `readiness/f5e34ec9-1959-4e12-afc7-0d9a934eac46/73aab5fb-632f-40c0-b26b-0fc7f61f55ad/raw`; the item state stayed `CAPTURE`.

## Independent verification

| Round | Candidate | Verdict | Tests (five named files) | Fitness | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `8e7b8a8` | ACCEPT (all FX-U9 controls match; 21 wrong implementations caught; no blocking findings) | 215 passed | PASS | `~/.local/state/alienintent/manual/assess-registered-work-verification/round1-8e7b8a8/verdict-8e7b8a8.md` |

The five named test files:

- `tests/context_assembly/test_packet_assessment.py`
- `tests/context_assembly/test_work_identity_service.py`
- `tests/composition/test_work_registry.py`
- `tests/control_plane/test_cli.py`
- `tests/context_assembly/test_readiness_consumer.py`

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

## Follow-ups (all non-blocking)

- No test covers the path where the owner cannot be observed during a normal run.
- The `TransactionHeld` message says "register with a pointer" even when raised from `set_pointer`.
- One line of the application module mixes `and`/`or` without brackets.
- After a failed tag publish during `--file --commit`, a plain `assess` uses the moved pointer before the tag is published (same behaviour as `register`).
- Open product question: whether hand-written work should enter the requirements inventory (design record, proof plan, READY validation).
- Open product question: a provider can outlive the exit check, but only if Agent Ready is killed from outside.

## Landing checks

`origin/main` had not moved since `17e15ba` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet 8e7b8a8 HEAD` before this record was added), so the verifier's round 1 results apply to it unchanged. No tests were run again.
