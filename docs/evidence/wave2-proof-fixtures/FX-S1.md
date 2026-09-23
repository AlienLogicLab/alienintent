# FX-S1 — typed immutable evidence and neutral references

WO-220102 / Issue #71. Producer: Morty. Invocation:
`AlienLogicLab/alienintent#71:PRODUCER:c1f15fac-1056-4e6b-8206-ad5d607a277c`.
These are local fixture observations; independent workflow verdict is **PENDING**.

## Authority and source custody

- Admission: `7bd7a6e782d8c4c1562f6f1f6813322870935825`, matching the
  Factory Director's [release comment](https://github.com/AlienLogicLab/alienintent/issues/71#issuecomment-5789648516).
- [Fixture plan](FX-S1/fixture-plan.json) pinned before implementation in
  `16f3e28d48350590b196ea890b75c8e470fa05cc`; unchanged thereafter.
- Product implementation and full-suite source:
  `01b1ca3d8e112a9c149b69a5efa9e7da761930db`.
- Evidence-runner metadata correction and retained FX-S1 run:
  `29f3b8d3641ac0d24fb76fd95b777a5dda59c47a`. This changes only unmeasured usage
  reporting to null/reason. Product code and tests match the full-suite source.
- The final evidence-only candidate commit/branch is recorded on Issue #71 after
  push and remote readback, avoiding a self-referential commit digest here.

The exact assessed work-unit fingerprint and canonical candidate-node digest
match the Issue. Runtime assignment identified this invocation, worker, worktree
and IMPLEMENT phase; active profile readback bound 3 cycles and 1 replacement,
with configured systemd duration enforcement. No configuration was changed.

S0 accepted candidate `761a3cb4d6e24dc24ec370de45e25fe8c505eeda` is ancestral to
admission. All 12 retained S0 artifact hashes match its execution record. The
packet's closure comment ID is stale; the actual same-candidate closure receipt
is [5780228636](https://github.com/AlienLogicLab/alienintent/issues/69#issuecomment-5780228636).
The original assessed packet is preserved. S0's success-collapse and platform
limitations are unchanged and are not reinterpreted as live proof.

## Observed checks

| Command | Result |
|---|---|
| C1: `python3 -m pytest -q tests/evidence_learning tests/execution_coordination/test_evidence_verdict_bridge.py tests/composition/test_evidence_profile.py` | Exit 0, 33 passed |
| C2: `python3 tools/evidence/fx_s1_evidence.py --output /tmp/fx-s1-retained-c1f15fac` | Exit 0, no holds; all four controls discriminate |
| C3: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` | Exit 0, all checks pass |
| C4: `python3 -m pytest -q` | Exit 0, 421 passed |
| C5: `node scripts/check.mjs all` | Exit 0: runtime 332/332, preflight PASS, RAI 18/18, policy 3/3 |

Each kind, definition-authority, revision and evaluator-authority mutation was
applied exactly once in a disposable source copy. Each fault yielded exit 1 and
an acceptance assertion failure (`DID NOT RAISE`); restoration yielded exit 0.
No production control was disabled in the candidate. Exact argv/stdout/stderr,
exit statuses and source revisions are retained as content-addressed observations.

The composed probes cover all four SF-REQ-016 acceptance criteria, direct verdict
admission, conflict arrival between evaluation/admission, actual process death
before/after SQLite CAS, corruption/missing objects, schema refusal, stale CAS,
concurrent identical puts, access/profile/path boundaries, unknown measurements,
caller-container immutability, and preservation of definition/evidence history.
The existing verdict policy, SQLite adapter, S0 evidence and assessed S1 work-unit
remain byte-identical to admission.

## Retained evidence and limits

[Execution record](FX-S1/execution-record.json) names **19 immutable artifacts**:
five typed synthetic objects and fourteen raw command/profile/readback records.
Each is identified by an exact SHA-256 digest. The unknown measurement is null
with `not measured`; its sibling measured Boolean and numeric values retain their
types. The current catalog retains the historical verdict and holds the definition
after appending the conflicting observation.

[Implementation notes](FX-S1/implementation-notes.md) describe the API, additive
M-EVIDENCE migration, rollback retention, local review findings and repairs.
The independent local reviewer found no remaining material issue after repairs;
this is not the allocated BIU VERIFIER verdict.

No operational/live proof, deployment, release, bootstrap retirement, RAI wiring,
garbage collection, source-authority migration or other-repository change is
claimed. FX-S1 does not measure provider usage, tokens or cost: those values are
explicitly unknown. S0's separately retained zero-provider-call receipt remains
its own observation.

Candidate resources remain runtime-managed and retained for independent retrieval
and BIU closure. The producer does not merge, push to main, remove active resources,
or advance Project state directly.
