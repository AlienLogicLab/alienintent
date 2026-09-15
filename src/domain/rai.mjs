const SEVERITIES = new Set(["BLOCKING", "MATERIAL", "ADVISORY"]);
const FINDING_STATUSES = new Set(["OPEN", "RESOLVED", "REJECTED", "SUPERSEDED"]);
const EVALUATION_OUTCOMES = new Set(["PASS", "CHANGES_REQUIRED", "ESCALATE"]);

function requiredString(value, name) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${name} must be a non-empty string`);
  return value.trim();
}
function optionalString(value, name) { return value == null ? null : requiredString(value, name); }
function integer(value, name, minimum = 0) {
  if (!Number.isInteger(value) || value < minimum) throw new TypeError(`${name} must be an integer >= ${minimum}`);
  return value;
}
function isoTimestamp(value, name) {
  requiredString(value, name);
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new TypeError(`${name} must be an ISO timestamp`);
  return new Date(parsed).toISOString();
}
function stringArray(value, name) {
  if (!Array.isArray(value) || value.some(v => typeof v !== "string" || !v.trim())) throw new TypeError(`${name} must be an array of non-empty strings`);
  return Object.freeze(value.map(v => v.trim()));
}
function enumValue(value, allowed, name) {
  if (!allowed.has(value)) throw new TypeError(`${name} must be one of ${[...allowed].join(", ")}`);
  return value;
}
const immutable = record => Object.freeze(record);

export function createCapabilityEpoch({provider, model, modelVersion = null, harnessVersion = null, promptSetVersion = null}) {
  return immutable({
    provider: requiredString(provider, "provider"),
    model: requiredString(model, "model"),
    modelVersion: optionalString(modelVersion, "modelVersion"),
    harnessVersion: optionalString(harnessVersion, "harnessVersion"),
    promptSetVersion: optionalString(promptSetVersion, "promptSetVersion"),
  });
}

export function createIteration({id, artifactId, ordinal, candidateRef, createdAt, capabilityEpoch, parentIterationId = null}) {
  if (!capabilityEpoch || typeof capabilityEpoch !== "object") throw new TypeError("capabilityEpoch is required");
  const normalizedOrdinal = integer(ordinal, "ordinal", 0);
  const normalizedParent = optionalString(parentIterationId, "parentIterationId");
  if (normalizedOrdinal === 0 && normalizedParent !== null) throw new TypeError("iteration 0 cannot have a parentIterationId");
  if (normalizedOrdinal > 0 && normalizedParent === null) throw new TypeError("iterations after 0 require parentIterationId");
  return immutable({
    id: requiredString(id, "id"), artifactId: requiredString(artifactId, "artifactId"), ordinal: normalizedOrdinal,
    candidateRef: requiredString(candidateRef, "candidateRef"), createdAt: isoTimestamp(createdAt, "createdAt"),
    capabilityEpoch, parentIterationId: normalizedParent,
  });
}

export function createFinding({id, iterationId, evaluatorId, severity, summary, evidenceRefs, status = "OPEN", createdAt, supersedesFindingId = null}) {
  return immutable({
    id: requiredString(id, "id"), iterationId: requiredString(iterationId, "iterationId"), evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    severity: enumValue(severity, SEVERITIES, "severity"), summary: requiredString(summary, "summary"),
    evidenceRefs: stringArray(evidenceRefs, "evidenceRefs"), status: enumValue(status, FINDING_STATUSES, "status"),
    createdAt: isoTimestamp(createdAt, "createdAt"), supersedesFindingId: optionalString(supersedesFindingId, "supersedesFindingId"),
  });
}

export function createEvaluation({id, iterationId, evaluatorId, capabilityEpoch, outcome, findingIds, completedAt, critique}) {
  if (!capabilityEpoch || typeof capabilityEpoch !== "object") throw new TypeError("capabilityEpoch is required");
  return immutable({
    id: requiredString(id, "id"), iterationId: requiredString(iterationId, "iterationId"), evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    capabilityEpoch, outcome: enumValue(outcome, EVALUATION_OUTCOMES, "outcome"), findingIds: stringArray(findingIds, "findingIds"),
    completedAt: isoTimestamp(completedAt, "completedAt"), critique: requiredString(critique, "critique"),
  });
}

export function validateIterationLineage(iterations) {
  if (!Array.isArray(iterations) || iterations.length === 0) throw new TypeError("iterations must be a non-empty array");
  const byId = new Map();
  for (const iteration of iterations) {
    if (byId.has(iteration.id)) throw new Error(`duplicate iteration id: ${iteration.id}`);
    byId.set(iteration.id, iteration);
  }
  const roots = iterations.filter(i => i.ordinal === 0);
  if (roots.length !== 1) throw new Error("exactly one iteration 0 is required");
  const artifactId = roots[0].artifactId;
  for (const iteration of iterations) {
    if (iteration.artifactId !== artifactId) throw new Error("all iterations in one lineage must share artifactId");
    if (iteration.ordinal === 0) continue;
    const parent = byId.get(iteration.parentIterationId);
    if (!parent) throw new Error(`missing parent iteration: ${iteration.parentIterationId}`);
    if (parent.artifactId !== iteration.artifactId) throw new Error("parent iteration belongs to a different artifact");
    if (parent.ordinal !== iteration.ordinal - 1) throw new Error("iteration ordinal must be exactly parent ordinal + 1");
  }
  return true;
}

export function classifyEvaluation({findings, authorityAllowsRepair = true}) {
  if (!Array.isArray(findings)) throw new TypeError("findings must be an array");
  const openActionable = findings.filter(f => f.status === "OPEN" && (f.severity === "BLOCKING" || f.severity === "MATERIAL"));
  if (openActionable.length === 0) return immutable({decision: "STOP", reason: "NO_OPEN_BLOCKING_OR_MATERIAL_FINDINGS", actionableFindingIds: Object.freeze([])});
  if (!authorityAllowsRepair) return immutable({decision: "ESCALATE", reason: "REPAIR_EXCEEDS_CURRENT_AUTHORITY", actionableFindingIds: Object.freeze(openActionable.map(f => f.id))});
  return immutable({decision: "CONTINUE", reason: "OPEN_BLOCKING_OR_MATERIAL_FINDINGS", actionableFindingIds: Object.freeze(openActionable.map(f => f.id))});
}

export function enforceManualRaiReviewPolicy({findings, maxActionableFindings = 3}) {
  integer(maxActionableFindings, "maxActionableFindings", 1);
  if (!Array.isArray(findings)) throw new TypeError("findings must be an array");
  const actionable = findings.filter(f => f.status === "OPEN" && (f.severity === "BLOCKING" || f.severity === "MATERIAL"));
  if (actionable.length > maxActionableFindings) throw new Error(`manual RAI review may surface at most ${maxActionableFindings} open BLOCKING/MATERIAL findings per pass`);
  return true;
}

export const RAI_CRITIQUE_PROMPT = "What did the previous iteration add or retain that is unnecessary, speculative, redundant, or more complex than the simplest correct solution?";
