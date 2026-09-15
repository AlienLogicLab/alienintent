const SEVERITIES = new Set(["BLOCKING", "MATERIAL", "ADVISORY"]);
const FINDING_STATUSES = new Set(["OPEN", "RESOLVED", "REJECTED", "SUPERSEDED"]);
const EVALUATION_OUTCOMES = new Set(["PASS", "CHANGES_REQUIRED", "ESCALATE"]);

function requiredString(value, name) {
  if (typeof value !== "string" || !value.trim()) {
    throw new TypeError(`${name} must be a non-empty string`);
  }
  return value.trim();
}

function optionalString(value, name) {
  return value == null ? null : requiredString(value, name);
}

function integer(value, name, minimum = 0) {
  if (!Number.isInteger(value) || value < minimum) {
    throw new TypeError(`${name} must be an integer >= ${minimum}`);
  }
  return value;
}

function isoTimestamp(value, name) {
  requiredString(value, name);
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    throw new TypeError(`${name} must be a valid timestamp`);
  }
  return new Date(parsed).toISOString();
}

function enumValue(value, allowed, name) {
  if (!allowed.has(value)) {
    throw new TypeError(`${name} must be one of ${[...allowed].join(", ")}`);
  }
  return value;
}

function uniqueStringArray(value, name) {
  if (!Array.isArray(value) || value.some(item => typeof item !== "string" || !item.trim())) {
    throw new TypeError(`${name} must be an array of non-empty strings`);
  }

  const normalized = value.map(item => item.trim());
  if (new Set(normalized).size !== normalized.length) {
    throw new TypeError(`${name} must not contain duplicates`);
  }

  return Object.freeze(normalized);
}

const immutable = record => Object.freeze(record);

function snapshotCapabilityEpoch(epoch) {
  if (!epoch || typeof epoch !== "object" || Array.isArray(epoch)) {
    throw new TypeError("capabilityEpoch is required");
  }

  return immutable({
    provider: requiredString(epoch.provider, "capabilityEpoch.provider"),
    model: requiredString(epoch.model, "capabilityEpoch.model"),
    modelVersion: optionalString(epoch.modelVersion, "capabilityEpoch.modelVersion"),
    harnessVersion: optionalString(epoch.harnessVersion, "capabilityEpoch.harnessVersion"),
    promptSetVersion: optionalString(epoch.promptSetVersion, "capabilityEpoch.promptSetVersion"),
  });
}

function validateIterationRecord(iteration) {
  if (!iteration || typeof iteration !== "object" || Array.isArray(iteration)) {
    throw new TypeError("each iteration must be an object");
  }

  requiredString(iteration.id, "iteration.id");
  requiredString(iteration.artifactId, "iteration.artifactId");
  integer(iteration.ordinal, "iteration.ordinal", 0);
  requiredString(iteration.candidateRef, "iteration.candidateRef");
  isoTimestamp(iteration.createdAt, "iteration.createdAt");
  snapshotCapabilityEpoch(iteration.capabilityEpoch);

  if (iteration.ordinal === 0) {
    if (iteration.parentIterationId != null) {
      throw new TypeError("iteration 0 cannot have a parentIterationId");
    }
  } else {
    requiredString(iteration.parentIterationId, "iteration.parentIterationId");
  }

  return iteration;
}

function validateFindingRecord(finding) {
  if (!finding || typeof finding !== "object" || Array.isArray(finding)) {
    throw new TypeError("each finding must be an object");
  }

  requiredString(finding.id, "finding.id");
  requiredString(finding.iterationId, "finding.iterationId");
  requiredString(finding.evaluatorId, "finding.evaluatorId");
  enumValue(finding.severity, SEVERITIES, "finding.severity");
  requiredString(finding.summary, "finding.summary");
  uniqueStringArray(finding.evidenceRefs, "finding.evidenceRefs");
  enumValue(finding.status, FINDING_STATUSES, "finding.status");
  isoTimestamp(finding.createdAt, "finding.createdAt");
  optionalString(finding.supersedesFindingId, "finding.supersedesFindingId");

  return finding;
}

function validateFindingSet(iterationId, findings) {
  const target = requiredString(iterationId, "iterationId");
  if (!Array.isArray(findings)) {
    throw new TypeError("findings must be an array");
  }

  const ids = new Set();
  for (const finding of findings) {
    validateFindingRecord(finding);
    if (ids.has(finding.id)) {
      throw new Error(`duplicate finding id: ${finding.id}`);
    }
    ids.add(finding.id);

    if (finding.iterationId !== target) {
      throw new Error(
        `finding ${finding.id} belongs to iteration ${finding.iterationId}, expected ${target}`,
      );
    }
  }

  return findings;
}

export function createCapabilityEpoch({
  provider,
  model,
  modelVersion = null,
  harnessVersion = null,
  promptSetVersion = null,
}) {
  return snapshotCapabilityEpoch({
    provider,
    model,
    modelVersion,
    harnessVersion,
    promptSetVersion,
  });
}

export function createIteration({
  id,
  artifactId,
  ordinal,
  candidateRef,
  createdAt,
  capabilityEpoch,
  parentIterationId = null,
}) {
  const normalizedOrdinal = integer(ordinal, "ordinal", 0);
  const normalizedParent = optionalString(parentIterationId, "parentIterationId");

  if (normalizedOrdinal === 0 && normalizedParent !== null) {
    throw new TypeError("iteration 0 cannot have a parentIterationId");
  }
  if (normalizedOrdinal > 0 && normalizedParent === null) {
    throw new TypeError("iterations after 0 require parentIterationId");
  }

  return immutable({
    id: requiredString(id, "id"),
    artifactId: requiredString(artifactId, "artifactId"),
    ordinal: normalizedOrdinal,
    candidateRef: requiredString(candidateRef, "candidateRef"),
    createdAt: isoTimestamp(createdAt, "createdAt"),
    capabilityEpoch: snapshotCapabilityEpoch(capabilityEpoch),
    parentIterationId: normalizedParent,
  });
}

export function createFinding({
  id,
  iterationId,
  evaluatorId,
  severity,
  summary,
  evidenceRefs,
  status = "OPEN",
  createdAt,
  supersedesFindingId = null,
}) {
  return immutable({
    id: requiredString(id, "id"),
    iterationId: requiredString(iterationId, "iterationId"),
    evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    severity: enumValue(severity, SEVERITIES, "severity"),
    summary: requiredString(summary, "summary"),
    evidenceRefs: uniqueStringArray(evidenceRefs, "evidenceRefs"),
    status: enumValue(status, FINDING_STATUSES, "status"),
    createdAt: isoTimestamp(createdAt, "createdAt"),
    supersedesFindingId: optionalString(supersedesFindingId, "supersedesFindingId"),
  });
}

export function createEvaluation({
  id,
  iterationId,
  evaluatorId,
  capabilityEpoch,
  outcome,
  findingIds,
  completedAt,
  critique,
}) {
  return immutable({
    id: requiredString(id, "id"),
    iterationId: requiredString(iterationId, "iterationId"),
    evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    capabilityEpoch: snapshotCapabilityEpoch(capabilityEpoch),
    outcome: enumValue(outcome, EVALUATION_OUTCOMES, "outcome"),
    findingIds: uniqueStringArray(findingIds, "findingIds"),
    completedAt: isoTimestamp(completedAt, "completedAt"),
    critique: requiredString(critique, "critique"),
  });
}

export function validateIterationLineage(iterations) {
  if (!Array.isArray(iterations) || iterations.length === 0) {
    throw new TypeError("iterations must be a non-empty array");
  }

  const byId = new Map();
  const byOrdinal = new Map();

  for (const iteration of iterations) {
    validateIterationRecord(iteration);

    if (byId.has(iteration.id)) {
      throw new Error(`duplicate iteration id: ${iteration.id}`);
    }
    if (byOrdinal.has(iteration.ordinal)) {
      throw new Error(`duplicate iteration ordinal: ${iteration.ordinal}`);
    }

    byId.set(iteration.id, iteration);
    byOrdinal.set(iteration.ordinal, iteration);
  }

  const roots = iterations.filter(iteration => iteration.ordinal === 0);
  if (roots.length !== 1) {
    throw new Error("exactly one iteration 0 is required");
  }

  const artifactId = roots[0].artifactId;
  const ordered = [...iterations].sort((a, b) => a.ordinal - b.ordinal);

  for (let index = 0; index < ordered.length; index += 1) {
    const iteration = ordered[index];

    if (iteration.artifactId !== artifactId) {
      throw new Error("all iterations in one lineage must share artifactId");
    }
    if (iteration.ordinal !== index) {
      throw new Error("iteration ordinals must be contiguous from 0");
    }
    if (index === 0) {
      continue;
    }

    const parent = byId.get(iteration.parentIterationId);
    if (!parent) {
      throw new Error(`missing parent iteration: ${iteration.parentIterationId}`);
    }
    if (parent.id !== ordered[index - 1].id) {
      throw new Error("each iteration must directly follow the previous iteration");
    }
  }

  return true;
}

export function classifyEvaluation({
  iterationId,
  findings,
  authorityAllowsRepair = true,
}) {
  validateFindingSet(iterationId, findings);

  const actionable = findings.filter(
    finding =>
      finding.status === "OPEN" &&
      (finding.severity === "BLOCKING" || finding.severity === "MATERIAL"),
  );

  if (actionable.length === 0) {
    return immutable({
      decision: "STOP",
      reason: "NO_OPEN_BLOCKING_OR_MATERIAL_FINDINGS",
      actionableFindingIds: Object.freeze([]),
    });
  }

  if (!authorityAllowsRepair) {
    return immutable({
      decision: "ESCALATE",
      reason: "REPAIR_EXCEEDS_CURRENT_AUTHORITY",
      actionableFindingIds: Object.freeze(actionable.map(finding => finding.id)),
    });
  }

  return immutable({
    decision: "CONTINUE",
    reason: "OPEN_BLOCKING_OR_MATERIAL_FINDINGS",
    actionableFindingIds: Object.freeze(actionable.map(finding => finding.id)),
  });
}

export function enforceManualRaiReviewPolicy({
  iterationId,
  findings,
  maxActionableFindings = 3,
}) {
  integer(maxActionableFindings, "maxActionableFindings", 1);
  validateFindingSet(iterationId, findings);

  const actionable = findings.filter(
    finding =>
      finding.status === "OPEN" &&
      (finding.severity === "BLOCKING" || finding.severity === "MATERIAL"),
  );

  if (actionable.length > maxActionableFindings) {
    throw new Error(
      `manual RAI review may surface at most ${maxActionableFindings} open BLOCKING/MATERIAL findings per pass`,
    );
  }

  return true;
}

export const RAI_CRITIQUE_PROMPT =
  "What did the previous iteration add or retain that is unnecessary, speculative, redundant, or more complex than the simplest correct solution?";
