# WO-220203 independent verification — JC

Invocation: `AlienLogicLab/alienintent#81:VERIFIER:ae92c58f-a092-49db-9235-5ce338b607c1`.
Reviewed candidate: `dcdc4aaa14640fe631bb363f8fe91a615d7e2476`, published on
`b-disp/7603a51e-bcd3-4f98-b44a-45bd7cf7b205`.
Admission baseline: `06e7e0c1f384e29c304788b11e0e559d8bdacc73`.
Verdict: **REJECT — incomplete published proof custody**, not a failing functional battery.

## Authority and retrieval

Reconstructed from Issue #81 body, the READY receipt, the Director RELEASED comment
5810383359 and producer comment 5810890256, plus the merged work order, packet,
allocation, governing directive and SWF-34. The release comment updates the earlier
packet baseline and producer selection. Scope remains U3 / FX-U3 only.
JC authenticated as `jc-worker`. The runtime-provided isolated worktree was clean at
baseline; Git identity was JC / jc-github@factorychecks.com. `git fetch origin
b-disp/7603a51e-bcd3-4f98-b44a-45bd7cf7b205` retrieved the candidate, and
`git ls-remote origin refs/heads/b-disp/7603a51e-bcd3-4f98-b44a-45bd7cf7b205`
returned that full SHA. The verifier branch was fast-forwarded to it for review.

## Blocking finding R1 — publish the referenced raw evidence

`docs/evidence/wo-220203-fx-u3/report.json` references 66 phase logs through
`observations[].raw_output`. **0 of 66 exist in the candidate tree.** The six
regression logs cited in `wo-220203-execution.md` are also absent; there is no
published `wo-220203-fx-u3/regression/` directory. `git check-ignore` confirms that
phase `.log` files match an ignore rule.

The 66 S1 observation objects are present and their content hashes are valid, but
inspection shows that their payloads retain structured summaries and raw-output
hashes, not the raw stdout/stderr. They cannot reconstruct the missing bytes or
independently substantiate the original fault assertion and regression receipts.
The report digest is `f625b7e8203c8b16d8421a20103938bd619939fc5d5b9f31e9982df798470e5b`.
See `wo-220203-jc-custody-audit.json` for the complete missing-path inventory.

This violates the work order's raw-observation/custody obligations and its rule to
hold on unavailable evidence. The producer's Issue comment explicitly claims 66
retained logs, so this is a concrete publication omission.

Repair: publish the original 66 phase logs and six cited regression logs, verify
all bytes against their recorded SHA-256 values, and check availability from an
independent remote retrieval. Preserve the existing report and immutable objects.
Use explicit staging or a narrowly scoped ignore exception. If originals cannot
be recovered, record that gap and obtain the required explicit supersession;
do not overwrite old receipts with a new run. Publish a new candidate SHA and
return through normal independent verification. No product redesign is requested.

Reproduction from the exact candidate:

```python
import json
from pathlib import Path
root = Path("docs/evidence/wo-220203-fx-u3")
r = json.loads((root / "report.json").read_text())
missing = [o["raw_output"] for o in r["observations"]
           if not (root / o["raw_output"]).is_file()]
assert len(missing) == 66
assert not (root / "regression").exists()
```

## Fresh observations and preserved proof

Commands below were run through `rtk proxy`; all exited 0.

- `PYTHONPATH=src python3 -m pytest -q tests`: **551 passed in 63.85s**.
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`:
  **PASS: all architecture fitness checks**.
- `node scripts/check.mjs all`: **340 runtime, preflight PASS, 18 RAI, 3 policy**.
- `PYTHONPATH=src python3 tools/evidence/fx_u3_evidence.py --output /tmp/wo-220203-jc-fx-u3`:
  **22/22 controls discriminated, 66 phases**, including composition disconnection.
  Each intact/restored phase exited 0; each fault exited 1 and contained `FAIL:`.
  These are fresh JC observations, not replacements for missing producer logs.
  Harness caveat: its default invocation and hardcoded observer label identify the
  producer/Morty; this JC rerun is explicitly attributed here and its generated
  objects are not published as producer receipts. Its local output is in `/tmp`.

The current implementation digests match the producer report. The mapping's two
authority digests match their retained source files. S1's execution record still
hashes to `e4b0c3956226d8fbc1211a53e6cfbbb986914274f8280fb49bee83fe9ae3fe8f`;
S1 source and receipts are untouched by this candidate. All tests under `tests`,
including S1 regression and the 25 new premise tests, passed. The separate `tools`
suite was not rerun; its disclosed baseline debt remains a producer observation.

## Semantic review and boundaries

The mapping follows SWF-34's separation of repository permission, Project
addressing, application refusal and outside-state readback. Retained positive
access and doctor details identify the sandbox; refusal patterns match literal
retained observations; the six readback pointers contain equal, nonempty,
type-exact values. Missing evidence routes to InfeasibleProof rather than invented
credential denial. Neutral premise modules do not import installation/composition.

The retained Project-operation check covers exactly **one observed operation**.
It cannot certify every later write or a future deployment. Neither green fitness
checks nor this review upgrade that limited historical observation into a general
isolation guarantee. The frozen sandbox inputs and all existing passing mechanical
proof must be preserved on repair. No operational success is inferred.

## Custody and next action

This verifier adds only this receipt and its custody audit on runtime-owned branch
`b-disp/85396df3-dad0-4924-81ba-0b155b4ae3e0`. Those artifacts are published before
the result comment. Candidate acceptance/landing is blocked by R1; return to the
producer for evidence repair. The runtime-managed branch/worktree remains subject
to BIU retention/cleanup policy; no manual ownership transfer or baseline push.
No pull request, deployment, live probe, provider call, sibling implementation or
other-repository change was performed. Tokens and cost are UNKNOWN.
