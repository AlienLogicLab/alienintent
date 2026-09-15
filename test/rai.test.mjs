import test from "node:test";
import assert from "node:assert/strict";
import {
  RAI_CRITIQUE_PROMPT,
  classifyEvaluation,
  createCapabilityEpoch,
  createEvaluation,
  createFinding,
  createIteration,
  enforceManualRaiReviewPolicy,
  validateEvaluationEvidence,
  validateIterationLineage,
} from "../src/domain/rai.mjs";

const epoch = createCapabilityEpoch({
  provider: "openai",
  model: "example-model",
  modelVersion: "2026-09",
  harnessVersion: "b-disp-test",
  promptSetVersion: "manual-rai-v1",
});

const t0 = createIteration({
  id: "iter-0",
  artifactId: "artifact-1",
  ordinal: 0,
  candidateRef: "commit:a",
  createdAt: "2026-09-15T00:00:00Z",
  capabilityEpoch: epoch,
});

const t1 = createIteration({
  id: "iter-1",
  artifactId: "artifact-1",
  ordinal: 1,
  candidateRef: "commit:b",
  createdAt: "2026-09-15T01:00:00Z",
  capabilityEpoch: epoch,
  parentIterationId: "iter-0",
});

function finding(id, severity = "MATERIAL", status = "OPEN", iterationId = t1.id) {
  return createFinding({
    id,
    iterationId,
    evaluatorId: "jc",
    severity,
    summary: `${severity} ${id}`,
    evidenceRefs: [`evidence:${id}`],
    status,
    createdAt: "2026-09-15T01:15:00Z",
  });
}

function evaluation(outcome, findingIds, overrides = {}) {
  return createEvaluation({
    id: `eval-${outcome.toLowerCase()}`,
    iterationId: t1.id,
    evaluatorId: "jc",
    capabilityEpoch: epoch,
    outcome,
    findingIds,
    completedAt: "2026-09-15T01:20:00Z",
    critique: RAI_CRITIQUE_PROMPT,
    ...overrides,
  });
}

test("iteration zero is the only parentless iteration", () => {
  assert.throws(
    () =>
      createIteration({
        id: "bad",
        artifactId: "artifact-1",
        ordinal: 1,
        candidateRef: "x",
        createdAt: "2026-09-15T00:00:00Z",
        capabilityEpoch: epoch,
      }),
    /require parentIterationId/,
  );
});

test("lineage is a single contiguous adjacent chain", () => {
  assert.equal(validateIterationLineage([t1, t0]), true);

  const branch = createIteration({
    id: "iter-1b",
    artifactId: "artifact-1",
    ordinal: 1,
    candidateRef: "c",
    createdAt: "2026-09-15T01:01:00Z",
    capabilityEpoch: epoch,
    parentIterationId: "iter-0",
  });
  assert.throws(() => validateIterationLineage([t0, t1, branch]), /duplicate iteration ordinal/);
});

test("lineage validates deserialized iteration records", () => {
  assert.throws(
    () => validateIterationLineage([t0, { ...t1, ordinal: "1" }]),
    /iteration.ordinal/,
  );
});

test("persisted identifiers must already be canonical", () => {
  assert.throws(
    () => validateIterationLineage([{ ...t0, id: " iter-0 " }]),
    /leading or trailing whitespace/,
  );

  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [{ ...finding("f1"), id: " f1 " }],
        authorityAllowsRepair: true,
      }),
    /leading or trailing whitespace/,
  );
});

test("persisted capability epoch provenance must already be canonical", () => {
  assert.throws(
    () =>
      validateIterationLineage([
        {
          ...t0,
          capabilityEpoch: { ...t0.capabilityEpoch, provider: " openai " },
        },
      ]),
    /leading or trailing whitespace/,
  );
});

test("iteration snapshots capability epoch provenance", () => {
  const mutable = { provider: "openai", model: "model-a", modelVersion: "1" };
  const iteration = createIteration({
    id: "s",
    artifactId: "a2",
    ordinal: 0,
    candidateRef: "s",
    createdAt: "2026-09-15T00:00:00Z",
    capabilityEpoch: mutable,
  });
  mutable.model = "mutated";
  assert.equal(iteration.capabilityEpoch.model, "model-a");
});

test("evaluation rejects duplicate finding references", () => {
  assert.throws(
    () =>
      createEvaluation({
        id: "e-duplicate",
        iterationId: t1.id,
        evaluatorId: "jc",
        capabilityEpoch: epoch,
        outcome: "CHANGES_REQUIRED",
        findingIds: ["f1", "f1"],
        completedAt: "2026-09-15T01:20:00Z",
        critique: RAI_CRITIQUE_PROMPT,
      }),
    /must not contain duplicates/,
  );
});

test("non-PASS evaluations require finding evidence", () => {
  for (const outcome of ["CHANGES_REQUIRED", "ESCALATE"]) {
    assert.throws(
      () =>
        createEvaluation({
          id: `e-${outcome}`,
          iterationId: t1.id,
          evaluatorId: "jc",
          capabilityEpoch: epoch,
          outcome,
          findingIds: [],
          completedAt: "2026-09-15T01:20:00Z",
          critique: RAI_CRITIQUE_PROMPT,
        }),
      /require at least one findingId/,
    );
  }
});

test("deserialized evaluation records are validated", () => {
  const valid = evaluation("PASS", []);
  assert.throws(
    () => validateEvaluationEvidence({ ...valid, outcome: "UNKNOWN" }, []),
    /evaluation.outcome/,
  );
  assert.throws(
    () => validateEvaluationEvidence({ ...valid, id: " eval-pass " }, []),
    /leading or trailing whitespace/,
  );
});

test("evaluation references must resolve to findings from its iteration", () => {
  assert.throws(
    () => validateEvaluationEvidence(evaluation("CHANGES_REQUIRED", ["missing"]), []),
    /missing finding/,
  );
});

test("PASS may reference advisory findings", () => {
  const advisory = finding("advisory-1", "ADVISORY");
  assert.equal(
    validateEvaluationEvidence(evaluation("PASS", [advisory.id]), [advisory]),
    true,
  );
});

test("PASS cannot reference open actionable findings", () => {
  const material = finding("material-1", "MATERIAL");
  assert.throws(
    () => validateEvaluationEvidence(evaluation("PASS", [material.id]), [material]),
    /cannot reference open BLOCKING\/MATERIAL/,
  );
});

test("CHANGES_REQUIRED requires an open actionable finding", () => {
  const advisory = finding("advisory-1", "ADVISORY");
  assert.throws(
    () =>
      validateEvaluationEvidence(
        evaluation("CHANGES_REQUIRED", [advisory.id]),
        [advisory],
      ),
    /requires an open BLOCKING\/MATERIAL/,
  );

  const material = finding("material-1", "MATERIAL");
  assert.equal(
    validateEvaluationEvidence(
      evaluation("CHANGES_REQUIRED", [material.id]),
      [material],
    ),
    true,
  );
});

test("classification rejects malformed deserialized findings", () => {
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [{ ...finding("bad"), severity: "CRITICAL" }],
        authorityAllowsRepair: true,
      }),
    /finding.severity/,
  );
});

test("classification rejects findings from another iteration", () => {
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [finding("wrong", "MATERIAL", "OPEN", "iter-0")],
        authorityAllowsRepair: true,
      }),
    /belongs to iteration/,
  );
});

test("classification rejects duplicate finding identities", () => {
  const same = finding("dup");
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [same, same],
        authorityAllowsRepair: true,
      }),
    /duplicate finding id/,
  );
});

test("STOP does not require a repair-authority decision", () => {
  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [finding("a", "ADVISORY")],
    }).decision,
    "STOP",
  );
});

test("actionable findings require explicit repair authority", () => {
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [finding("m")],
      }),
    /authorityAllowsRepair must be a boolean/,
  );
});

test("CONTINUE for actionable findings within explicit authority", () => {
  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [finding("m")],
      authorityAllowsRepair: true,
    }).decision,
    "CONTINUE",
  );
});

test("ESCALATE when repair explicitly exceeds authority", () => {
  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [finding("b", "BLOCKING")],
      authorityAllowsRepair: false,
    }).decision,
    "ESCALATE",
  );
});

test("manual review pass is bounded to three findings from one iteration", () => {
  const three = [finding("1"), finding("2"), finding("3")];
  assert.equal(enforceManualRaiReviewPolicy({ iterationId: t1.id, findings: three }), true);
  assert.throws(
    () =>
      enforceManualRaiReviewPolicy({
        iterationId: t1.id,
        findings: [...three, finding("4")],
      }),
    /at most 3/,
  );
});
