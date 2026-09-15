const SEVERITIES = new Set(["BLOCKING", "MATERIAL", "ADVISORY"]);
const DISPOSITIONS = new Set(["RESOLVED", "REJECTED", "SUPERSEDED"]);
const EVALUATION_OUTCOMES = new Set(["PASS", "CHANGES_REQUIRED", "ESCALATE"]);

function requiredString(value, name) {
  if (typeof value !== "string" || !value.trim()) {
    throw new TypeError(`${name} must be a non-empty string`);
  }
  return value.trim();
}

function canonicalString(value, name) {
  const normalized = requiredString(value, name);
  if (value !== normalized) {
    throw new TypeError(`${name} must not contain leading or trailing whitespace`);
  }
  return value;
}

function optionalString(value, name) {
  return value == null ? null : requiredString(value, name);
}

function optionalCanonicalString(value, name) {
  return value == null ? null : canonicalString(value, name);
}

function integer(value, name, minimum = 0) {
  if (!Number.isInteger(value) || value < minimum) {
    throw new TypeError(`${name} must be an integer >= ${minimum}`);
  }
  return value;
}

function boolean(value, name) {
  if (typeof value !== "boolean") {
    throw new TypeError(`${name} must be a boolean`);
  }
  return value;
}

function normalizedIsoTimestamp(value, name) {
  requiredString(value, name);
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    throw new TypeError(`${name} must be a valid timestamp`);
  }
  return new Date(parsed).toISOString();
}

function canonicalIsoTimestamp(value, name) {
  const normalized = normalizedIsoTimestamp(value, name);
  if (value !== normalized) {
    throw new TypeError(`${name} must be a canonical ISO timestamp`);
  }
  return value;
}

function enumValue(value, allowed, name) {
  if (!allowed.has(value)) {
    throw new TypeError(`${name} must be one of ${[...allowed].join(", ")}`);
  }
  return value;
}

function uniqueStringArray(value, name, { allowEmpty = true } = {}) {
  if (!Array.isArray(value) || value.some(item => typeof item !== "string" || !item.trim())) {
    throw new TypeError(`${name} must be an array of non-empty strings`);
  }

  const normalized = value.map(item => item.trim());
  if (!allowEmpty && normalized.length === 0) {
    throw new TypeError(`${name} must contain at least one item`);
  }
  if (new Set(normalized).size !== normalized.length) {
    throw new TypeError(`${name} must not contain duplicates`);
  }

  return Object.freeze(normalized);
}

function validateUniqueCanonicalStringArray(value, name, { allowEmpty = true } = {}) {
  if (!Array.isArray(value)) {
    throw new TypeError(`${name} must be an array`);
  }
  if (!allowEmpty && value.length === 0) {
    throw new TypeError(`${name} must contain at least one item`);
  }

  const seen = new Set();
  for (const item of value) {
    const canonical = canonicalString(item, `${name} item`);
    if (seen.has(canonical)) {
      throw new TypeError(`${name} must not contain duplicates`);
    }
    seen.add(canonical);
  }

  return value;
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

function validateCapabilityEpochRecord(epoch) {
  if (!epoch || typeof epoch !== "object" || Array.isArray(epoch)) {
    throw new TypeError("capabilityEpoch is required");
  }

  canonicalString(epoch.provider, "capabilityEpoch.provider");
  canonicalString(epoch.model, "capabilityEpoch.model");
  optionalCanonicalString(epoch.modelVersion, "capabilityEpoch.modelVersion");
  optionalCanonicalString(epoch.harnessVersion, "capabilityEpoch.harnessVersion");
  optionalCanonicalString(epoch.promptSetVersion, "capabilityEpoch.promptSetVersion");

  return epoch;
}

function validateIterationRecord(iteration) {
  if (!iteration || typeof iteration !== "object" || Array.isArray(iteration)) {
    throw new TypeError("each iteration must be an object");
  }

  canonicalString(iteration.id, "iteration.id");
  canonicalString(iteration.artifactId, "iteration.artifactId");
  integer(iteration.ordinal, "iteration.ordinal", 0);
  canonicalString(iteration.candidateRef, "iteration.candidateRef");
  canonicalIsoTimestamp(iteration.createdAt, "iteration.createdAt");
  validateCapabilityEpochRecord(iteration.capabilityEpoch);

  if (iteration.ordinal === 0) {
    if (iteration.parentIterationId != null) {
      throw new TypeError("iteration 0 cannot have a parentIterationId");
    }
  } else {
    canonicalString(iteration.parentIterationId, "iteration.parentIterationId");
  }

  return iteration;
}

function validateFindingRecord(finding) {
  if (!finding || typeof finding !== "object" || Array.isArray(finding)) {
    throw new TypeError("each finding must be an object");
  }

  canonicalString(finding.id, "finding.id");
  canonicalString(finding.iterationId, "finding.iterationId");
  canonicalString(finding.evaluatorId, "finding.evaluatorId");
  enumValue(finding.severity, SEVERITIES, "finding.severity");
  requiredString(finding.summary, "finding.summary");
  validateUniqueCanonicalStringArray(finding.evidenceRefs, "finding.evidenceRefs", {
    allowEmpty: false,
  });
  canonicalIsoTimestamp(finding.createdAt, "finding.createdAt");

  if ("status" in finding || "supersedesFindingId" in finding) {
    throw new TypeError("finding lifecycle state must be recorded as a separate disposition");
  }

  return finding;
}

function validateFindingSet(iterationId, findings) {
  const target = canonicalString(iterationId, "iterationId");
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

function validateDispositionRecord(disposition) {
  if (!disposition || typeof disposition !== "object" || Array.isArray(disposition)) {
    throw new TypeError("each disposition must be an object");
  }

  canonicalString(disposition.id, "disposition.id");
  canonicalString(disposition.findingId, "disposition.findingId");
  canonicalString(disposition.decidedBy, "disposition.decidedBy");
  enumValue(disposition.decision, DISPOSITIONS, "disposition.decision");
  validateUniqueCanonicalStringArray(disposition.evidenceRefs, "disposition.evidenceRefs", {
    allowEmpty: false,
  });
  canonicalIsoTimestamp(disposition.decidedAt, "disposition.decidedAt");

  if (disposition.decision === "SUPERSEDED") {
    canonicalString(disposition.replacementFindingId, "disposition.replacementFindingId");
    if (disposition.replacementFindingId === disposition.findingId) {
      throw new TypeError("a finding cannot supersede itself");
    }
  } else if (disposition.replacementFindingId != null) {
    throw new TypeError("replacementFindingId is only valid for SUPERSEDED dispositions");
  }

  return disposition;
}

function validateDispositionSet(findings, dispositions) {
  if (!Array.isArray(dispositions)) {
    throw new TypeError("dispositions must be an array");
  }

  const findingsById = new Map(findings.map(finding => [finding.id, finding]));
  const ids = new Set();
  const disposedFindingIds = new Set();

  for (const disposition of dispositions) {
    validateDispositionRecord(disposition);

    if (ids.has(disposition.id)) {
      throw new Error(`duplicate disposition id: ${disposition.id}`);
    }
    ids.add(disposition.id);

    if (disposedFindingIds.has(disposition.findingId)) {
      throw new Error(`finding ${disposition.findingId} has multiple dispositions`);
    }
    disposedFindingIds.add(disposition.findingId);

    if (!findingsById.has(disposition.findingId)) {
      throw new Error(`disposition references missing finding: ${disposition.findingId}`);
    }

    if (
      disposition.decision === "SUPERSEDED" &&
      !findingsById.has(disposition.replacementFindingId)
    ) {
      throw new Error(
        `SUPERSEDED disposition references missing replacement finding: ${disposition.replacementFindingId}`,
      );
    }
  }

  return dispositions;
}

function activeFindings(findings, dispositions) {
  const disposed = new Set(dispositions.map(disposition => disposition.findingId));
  return findings.filter(finding => !disposed.has(finding.id));
}

function validateEvaluationRecord(evaluation) {
  if (!evaluation || typeof evaluation !== "object" || Array.isArray(evaluation)) {
    throw new TypeError("evaluation must be an object");
  }

  canonicalString(evaluation.id, "evaluation.id");
  canonicalString(evaluation.iterationId, "evaluation.iterationId");
  canonicalString(evaluation.evaluatorId, "evaluation.evaluatorId");
  validateCapabilityEpochRecord(evaluation.capabilityEpoch);
  enumValue(evaluation.outcome, EVALUATION_OUTCOMES, "evaluation.outcome");
  validateUniqueCanonicalStringArray(evaluation.findingIds, "evaluation.findingIds");
  canonicalIsoTimestamp(evaluation.completedAt, "evaluation.completedAt");
  requiredString(evaluation.critique, "evaluation.critique");

  if (
    (evaluation.outcome === "CHANGES_REQUIRED" || evaluation.outcome === "ESCALATE") &&
    evaluation.findingIds.length === 0
  ) {
    throw new TypeError(`${evaluation.outcome} evaluations require at least one findingId`);
  }

  return evaluation;
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
    createdAt: normalizedIsoTimestamp(createdAt, "createdAt"),
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
  createdAt,
}) {
  return immutable({
    id: requiredString(id, "id"),
    iterationId: requiredString(iterationId, "iterationId"),
    evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    severity: enumValue(severity, SEVERITIES, "severity"),
    summary: requiredString(summary, "summary"),
    evidenceRefs: uniqueStringArray(evidenceRefs, "evidenceRefs", { allowEmpty: false }),
    createdAt: normalizedIsoTimestamp(createdAt, "createdAt"),
  });
}

export function createFindingDisposition({
  id,
  findingId,
  decidedBy,
  decision,
  evidenceRefs,
  decidedAt,
  replacementFindingId = null,
}) {
  const normalizedDecision = enumValue(decision, DISPOSITIONS, "decision");
  const normalizedFindingId = requiredString(findingId, "findingId");
  const normalizedReplacement = optionalString(replacementFindingId, "replacementFindingId");

  if (normalizedDecision === "SUPERSEDED") {
    if (normalizedReplacement == null) {
      throw new TypeError("SUPERSEDED dispositions require replacementFindingId");
    }
    if (normalizedReplacement === normalizedFindingId) {
      throw new TypeError("a finding cannot supersede itself");
    }
  } else if (normalizedReplacement != null) {
    throw new TypeError("replacementFindingId is only valid for SUPERSEDED dispositions");
  }

  return immutable({
    id: requiredString(id, "id"),
    findingId: normalizedFindingId,
    decidedBy: requiredString(decidedBy, "decidedBy"),
    decision: normalizedDecision,
    evidenceRefs: uniqueStringArray(evidenceRefs, "evidenceRefs", { allowEmpty: false }),
    decidedAt: normalizedIsoTimestamp(decidedAt, "decidedAt"),
    replacementFindingId: normalizedReplacement,
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
  const normalizedOutcome = enumValue(outcome, EVALUATION_OUTCOMES, "outcome");
  const normalizedFindingIds = uniqueStringArray(findingIds, "findingIds");

  if (
    (normalizedOutcome === "CHANGES_REQUIRED" || normalizedOutcome === "ESCALATE") &&
    normalizedFindingIds.length === 0
  ) {
    throw new TypeError(`${normalizedOutcome} evaluations require at least one findingId`);
  }

  return immutable({
    id: requiredString(id, "id"),
    iterationId: requiredString(iterationId, "iterationId"),
    evaluatorId: requiredString(evaluatorId, "evaluatorId"),
    capabilityEpoch: snapshotCapabilityEpoch(capabilityEpoch),
    outcome: normalizedOutcome,
    findingIds: normalizedFindingIds,
    completedAt: normalizedIsoTimestamp(completedAt, "completedAt"),
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

export function validateEvaluationEvidence(evaluation, findings, dispositions = []) {
  validateEvaluationRecord(evaluation);
  validateFindingSet(evaluation.iterationId, findings);
  validateDispositionSet(findings, dispositions);

  const providedFindingIds = new Set(findings.map(finding => finding.id));
  const referencedFindingIds = new Set(evaluation.findingIds);

  if (
    providedFindingIds.size !== referencedFindingIds.size ||
    [...providedFindingIds].some(id => !referencedFindingIds.has(id))
  ) {
    throw new Error("evaluation findingIds must exactly match the provided finding set");
  }

  const active = activeFindings(findings, dispositions);
  const openActionable = active.filter(
    finding => finding.severity === "BLOCKING" || finding.severity === "MATERIAL",
  );

  if (evaluation.outcome === "PASS" && openActionable.length > 0) {
    throw new Error("PASS evaluation cannot coexist with active BLOCKING/MATERIAL findings");
  }

  if (
    (evaluation.outcome === "CHANGES_REQUIRED" || evaluation.outcome === "ESCALATE") &&
    openActionable.length === 0
  ) {
    throw new Error(`${evaluation.outcome} evaluation requires an active BLOCKING/MATERIAL finding`);
  }

  return true;
}

export function classifyEvaluation({
  iterationId,
  findings,
  dispositions = [],
  authorityAllowsRepair,
}) {
  validateFindingSet(iterationId, findings);
  validateDispositionSet(findings, dispositions);

  const actionable = activeFindings(findings, dispositions).filter(
    finding => finding.severity === "BLOCKING" || finding.severity === "MATERIAL",
  );

  if (actionable.length === 0) {
    return immutable({
      decision: "STOP",
      reason: "NO_ACTIVE_BLOCKING_OR_MATERIAL_FINDINGS",
      actionableFindingIds: Object.freeze([]),
    });
  }

  const authorized = boolean(authorityAllowsRepair, "authorityAllowsRepair");

  if (!authorized) {
    return immutable({
      decision: "ESCALATE",
      reason: "REPAIR_EXCEEDS_CURRENT_AUTHORITY",
      actionableFindingIds: Object.freeze(actionable.map(finding => finding.id)),
    });
  }

  return immutable({
    decision: "CONTINUE",
    reason: "ACTIVE_BLOCKING_OR_MATERIAL_FINDINGS",
    actionableFindingIds: Object.freeze(actionable.map(finding => finding.id)),
  });
}

export function enforceManualRaiReviewPolicy({
  iterationId,
  findings,
  dispositions = [],
  maxActionableFindings = 3,
}) {
  integer(maxActionableFindings, "maxActionableFindings", 1);
  validateFindingSet(iterationId, findings);
  validateDispositionSet(findings, dispositions);

  const actionable = activeFindings(findings, dispositions).filter(
    finding => finding.severity === "BLOCKING" || finding.severity === "MATERIAL",
  );

  if (actionable.length > maxActionableFindings) {
    throw new Error(
      `manual RAI review may surface at most ${maxActionableFindings} active BLOCKING/MATERIAL findings per pass`,
    );
  }

  return true;
}

export const RAI_CRITIQUE_PROMPT =
  "What did the previous iteration add or retain that is unnecessary, speculative, redundant, or more complex than the simplest correct solution?";
