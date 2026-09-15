import test from "node:test";
import assert from "node:assert/strict";
import {
  RAI_CRITIQUE_PROMPT,
  classifyEvaluation,
  createCapabilityEpoch,
  createEvaluation,
  createFinding,
  createFindingDisposition,
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

function finding(id, severity = "MATERIAL", iterationId = t1.id) {
  return createFinding({
    id,
    iterationId,
    evaluatorId: "jc",
    severity,
    summary: `${severity} ${id}`,
    evidenceRefs: [`evidence:${id}`],
    createdAt: "2026-09-15T01:15:00Z",
  });
}

function disposition(findingId, decision = "RESOLVED", replacementFindingId = null) {
  return createFindingDisposition({
    id: `disposition-${findingId}`,
    findingId,
    decidedBy: "founder",
    decision,
    evidenceRefs: [`resolution:${findingId}`],
    decidedAt: "2026-09-15T01:18:00Z",
    replacementFindingId,
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

test("persisted timestamps must be canonical ISO", () => {
  assert.throws(
    () => validateIterationLineage([{ ...t0, createdAt: "2026-09-15" }]),
    /canonical ISO timestamp/,
  );
});

test("constructors normalize timestamps into canonical ISO", () => {
  const created = createIteration({
    id: "timestamp",
    artifactId: "artifact-2",
    ordinal: 0,
    candidateRef: "commit:t",
    createdAt: "2026-09-15T07:00:00+07:00",
    capabilityEpoch: epoch,
  });
  assert.equal(created.createdAt, "2026-09-15T00:00:00.000Z");
});

test("findings are immutable observations without lifecycle status", () => {
  const material = finding("material-1");
  assert.equal("status" in material, false);
  assert.ok(Object.isFrozen(material));

  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [{ ...material, status: "RESOLVED" }],
        dispositions: [],
        authorityAllowsRepair: true,
      }),
    /separate disposition/,
  );
});

test("finding dispositions require evidence", () => {
  assert.throws(
    () =>
      createFindingDisposition({
        id: "d1",
        findingId: "f1",
        decidedBy: "founder",
        decision: "RESOLVED",
        evidenceRefs: [],
        decidedAt: "2026-09-15T01:18:00Z",
      }),
    /at least one item/,
  );
});

test("SUPERSEDED dispositions require a different replacement finding", () => {
  assert.throws(
    () => disposition("f1", "SUPERSEDED", null),
    /require replacementFindingId/,
  );
  assert.throws(
    () => disposition("f1", "SUPERSEDED", "f1"),
    /cannot supersede itself/,
  );
});

test("classification rejects dispositions for missing findings", () => {
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [finding("f1")],
        dispositions: [disposition("missing")],
        authorityAllowsRepair: true,
      }),
    /missing finding/,
  );
});

test("one finding cannot have multiple dispositions", () => {
  const f1 = finding("f1");
  assert.throws(
    () =>
      classifyEvaluation({
        iterationId: t1.id,
        findings: [f1],
        dispositions: [
          disposition("f1"),
          createFindingDisposition({
            id: "d2",
            findingId: "f1",
            decidedBy: "founder",
            decision: "REJECTED",
            evidenceRefs: ["resolution:2"],
            decidedAt: "2026-09-15T01:19:00Z",
          }),
        ],
        authorityAllowsRepair: true,
      }),
    /multiple dispositions/,
  );
});

test("evaluation must account for the entire provided finding set", () => {
  const material = finding("material-1");
  const advisory = finding("advisory-1", "ADVISORY");

  assert.throws(
    () =>
      validateEvaluationEvidence(
        evaluation("PASS", [advisory.id]),
        [material, advisory],
        [],
      ),
    /exactly match/,
  );
});

test("PASS cannot coexist with active actionable findings", () => {
  const material = finding("material-1");
  assert.throws(
    () =>
      validateEvaluationEvidence(
        evaluation("PASS", [material.id]),
        [material],
        [],
      ),
    /cannot coexist/,
  );
});

test("PASS is valid after actionable finding has evidence-backed disposition", () => {
  const material = finding("material-1");
  assert.equal(
    validateEvaluationEvidence(
      evaluation("PASS", [material.id]),
      [material],
      [disposition(material.id)],
    ),
    true,
  );
});

test("CHANGES_REQUIRED requires an active actionable finding", () => {
  const advisory = finding("advisory-1", "ADVISORY");
  assert.throws(
    () =>
      validateEvaluationEvidence(
        evaluation("CHANGES_REQUIRED", [advisory.id]),
        [advisory],
        [],
      ),
    /requires an active BLOCKING\/MATERIAL/,
  );
});

test("STOP requires all actionable findings to be dispositioned", () => {
  const material = finding("material-1");

  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [material],
      dispositions: [disposition(material.id)],
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

test("CONTINUE for active actionable findings within explicit authority", () => {
  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [finding("m")],
      authorityAllowsRepair: true,
    }).decision,
    "CONTINUE",
  );
});

test("ESCALATE when active repair explicitly exceeds authority", () => {
  assert.equal(
    classifyEvaluation({
      iterationId: t1.id,
      findings: [finding("b", "BLOCKING")],
      authorityAllowsRepair: false,
    }).decision,
    "ESCALATE",
  );
});

test("manual review pass is bounded to three active actionable findings", () => {
  const findings = [finding("1"), finding("2"), finding("3"), finding("4")];

  assert.equal(
    enforceManualRaiReviewPolicy({
      iterationId: t1.id,
      findings,
      dispositions: [disposition("4")],
    }),
    true,
  );

  assert.throws(
    () =>
      enforceManualRaiReviewPolicy({
        iterationId: t1.id,
        findings,
      }),
    /at most 3/,
  );
});
