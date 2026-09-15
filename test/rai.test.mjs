import test from "node:test";
import assert from "node:assert/strict";
import {RAI_CRITIQUE_PROMPT, classifyEvaluation, createCapabilityEpoch, createEvaluation, createFinding, createIteration, enforceManualRaiReviewPolicy, validateIterationLineage} from "../src/domain/rai.mjs";

const epoch = createCapabilityEpoch({provider:"openai", model:"example-model", modelVersion:"2026-09", harnessVersion:"b-disp-test", promptSetVersion:"manual-rai-v1"});
const t0 = createIteration({id:"iter-0", artifactId:"artifact-1", ordinal:0, candidateRef:"commit:a", createdAt:"2026-09-15T00:00:00Z", capabilityEpoch:epoch});
const t1 = createIteration({id:"iter-1", artifactId:"artifact-1", ordinal:1, candidateRef:"commit:b", createdAt:"2026-09-15T01:00:00Z", capabilityEpoch:epoch, parentIterationId:"iter-0"});
const finding = (id, severity="MATERIAL", status="OPEN") => createFinding({id, iterationId:t1.id, evaluatorId:"jc", severity, summary:`${severity} ${id}`, evidenceRefs:[`evidence:${id}`], status, createdAt:"2026-09-15T01:15:00Z"});

test("iteration zero is the only parentless iteration", () => {
  assert.throws(() => createIteration({id:"bad", artifactId:"artifact-1", ordinal:1, candidateRef:"commit:x", createdAt:"2026-09-15T00:00:00Z", capabilityEpoch:epoch}), /require parentIterationId/);
});
test("lineage is adjacent and artifact-scoped", () => {
  assert.equal(validateIterationLineage([t0,t1]), true);
  assert.throws(() => validateIterationLineage([t0,{...t1, ordinal:2}]), /parent ordinal \+ 1/);
});
test("findings are immutable structured evidence", () => {
  const f = finding("f1");
  assert.equal(f.severity,"MATERIAL");
  assert.ok(Object.isFrozen(f));
});
test("evaluation records capability epoch and anti-slop critique", () => {
  const e = createEvaluation({id:"e1", iterationId:t1.id, evaluatorId:"jc", capabilityEpoch:epoch, outcome:"CHANGES_REQUIRED", findingIds:["f1"], completedAt:"2026-09-15T01:20:00Z", critique:RAI_CRITIQUE_PROMPT});
  assert.equal(e.capabilityEpoch.model,"example-model");
  assert.equal(e.critique,RAI_CRITIQUE_PROMPT);
});
test("STOP when only advisory findings remain", () => {
  assert.equal(classifyEvaluation({findings:[finding("a1","ADVISORY")]}).decision,"STOP");
});
test("CONTINUE for actionable findings within authority", () => {
  assert.equal(classifyEvaluation({findings:[finding("m1")], authorityAllowsRepair:true}).decision,"CONTINUE");
});
test("ESCALATE when repair exceeds authority", () => {
  assert.equal(classifyEvaluation({findings:[finding("b1","BLOCKING")], authorityAllowsRepair:false}).decision,"ESCALATE");
});
test("manual review pass is bounded to three actionable findings", () => {
  const three=[finding("1"),finding("2"),finding("3")];
  assert.equal(enforceManualRaiReviewPolicy({findings:three}),true);
  assert.throws(() => enforceManualRaiReviewPolicy({findings:[...three,finding("4")]}),/at most 3/);
});
