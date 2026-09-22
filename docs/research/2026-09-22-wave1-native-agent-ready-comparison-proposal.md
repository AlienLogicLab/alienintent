# Proposal — native Agent Ready re-assessment of a Wave 1 sample (not executed)

Status: **proposal, prepared 2026-09-22 at Founder request; not executed and not authorized by
this document.** Owner on approval: Requirements / Planning context (SF-REQ-015 integration) for
execution; Evidence and Learning (SF-REQ-030) for the resulting observations.

## Purpose

Wave 1's eleven readiness assessments (PY-01…PY-10, PY-09B) were produced by a surrogate — raw
Codex/Claude prompts shaped to the Agent Ready contract — not by the Agent Ready product
(`docs/evidence/2026-09-22-wave1-authoritative-capability-substitution.md`). Nothing measures how
far those surrogate dispositions diverge from what Agent Ready itself would have returned. This
study would:

1. compare surrogate dispositions to native Agent Ready dispositions on the same inputs;
2. measure protocol and rubric drift between the surrogate prompt and Agent Ready's frozen
   readiness prompt and schema;
3. identify cases worth contributing to Agent Ready's feedback / research corpus, under its
   consent rules.

## What must remain separate

Historical surrogate results are immutable evidence. New native results are **new observations**
recorded beside them, never as corrections of them. No historical assessment file, trajectory
event, closure manifest or Wave 1 decision record is rewritten. A disagreement between a
surrogate and a native disposition is a finding about the surrogate, not a retroactive change to
what Wave 1 did.

## Sample

Representative, not exhaustive. Selection criterion: one input per distinct historical
disposition and one per distinct surrogate provider, plus the two BIUs whose surrogate history
changed disposition:

| BIU | Surrogate history | Why sampled |
|---|---|---|
| PY-02 | READY (codex 0.155.1) | first surrogate with a recorded invocation; baseline shape |
| PY-05 | READY (codex) | mid-wave, largest contract |
| PY-08 | READY (codex) | most repair cycles after READY — the outcome-feedback case |
| PY-09B | NEEDS_CLARIFICATION → READY (claude) | disposition changed; provider failover |
| PY-10 | BLOCKED → SPLIT_RECOMMENDED → READY (codex then claude) | full non-READY sequence |

Inputs: the retained `PY-NN.request.md` files, at the git revision each surrogate assessment
recorded (`assessment_sha256` in the trajectory pins the assessment; the request's revision is
recorded in `provider_evidence.baseline`). The request files embed the surrogate's own
instructions (including its non-Agent-Ready disposition enum) — the study submits the **BIU
contract text** (`PY-NN.md` at that revision) as the work unit, not the surrogate prompt.

## Method

- Invoke the actual product: `agent-ready assess <contract.md> --provider codex --json` and,
  separately, `--provider claude --json`, from the published Agent Ready version, recording
  package version, schema identity (once available — see agent-ready issue #1), provider
  evidence and timestamp.
- Map for comparison only: surrogate `BLOCKED → HOLD`, `NEEDS_CLARIFICATION → CLARIFY`,
  `SPLIT_RECOMMENDED → SPLIT`. The mapping is recorded as an interpretation, not applied to the
  historical files.
- Drift measures: disposition agreement; owner-clarification count and overlap;
  `expected_rework_locality` agreement; presence of Agent Ready dimensions the surrogate prompt
  did not ask for (governing-intent coherence, verification coherence); provenance fields the
  surrogate asserted that Agent Ready generates host-side.
- Compare against downstream reality where it exists: PY-08's repair count, PY-10's later split.

## Constraints

- Provider versions must satisfy Agent Ready's fail-closed pins at run time; a refusal is a
  result, not a failure to run the study.
- Inference incurs provider charges; token and cost are recorded or `UNKNOWN`, never zero.
- Contribution of any case to Agent Ready's corpus follows its assessment-case template and
  consent checkbox; contract text that is AlienIntent-private is not contributed.
- No lifecycle, Project or Wave 1 evidence state changes. No Wave 2 execution.

## Outputs

`docs/evidence/wave1-native-agent-ready-comparison.json` (+ `.md`): per-sample native results,
surrogate results by reference, drift measures, and a stated conclusion labelled FACT /
INFERENCE / HYPOTHESIS. n = 5 supports drift *measurement*, not a causal claim about Wave 1 yield.

## Decision required to execute

Founder authorization of provider spend and of the sample, and confirmation that the comparison
is recorded as new observations under SF-REQ-030.
