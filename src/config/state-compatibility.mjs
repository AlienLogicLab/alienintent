import { readFileSync } from "node:fs";

const unresolvedOutcomes = new Set(["COMPLETION_ERROR", "DURABLE_RESULT_MISSING", "WORKER_IDENTITY_MISMATCH", "FOUNDER_EXCEPTION"]);
const incompatible = () => { throw new Error("AlienIntent: state compatibility requires unchanged role/identity or an explicit legacy identity handoff"); };

// Read-only installation boundary. Completed history is not renamed or reattributed.
export function verifyStateCompatibility(config) {
  let state;
  try { state = JSON.parse(readFileSync(config.statePath, "utf8")); }
  catch (error) { if (error.code === "ENOENT") return; incompatible(); }
  if (!state || typeof state !== "object" || !state.active || typeof state.active !== "object" || Array.isArray(state.active)) incompatible();
  const claims = Object.entries(state.active);
  for (const [lane, claim] of Object.entries(state.diagnostics ?? {})) {
    if (!state.active[lane] && unresolvedOutcomes.has(claim?.outcome)) claims.push([lane, claim]);
  }
  for (const [lane, claim] of claims) {
    const parsed = /^([^/#\s]+\/[^/#\s]+)#([1-9][0-9]*):([^:\s]+)$/.exec(lane);
    if (!parsed) incompatible();
    const [, repository, issue, role] = parsed;
    const worker = config.workers[role];
    if (!worker || !claim?.invocationId || repository !== config.repository
        || (claim.role !== undefined && claim.role !== role)
        || (claim.item?.repository !== undefined && claim.item.repository !== repository)
        || (claim.item?.issue !== undefined && String(claim.item.issue) !== issue)) incompatible();
    const recordedLogin = claim.workerLogin ?? claim.signalEvidence?.author ?? claim.evidence?.expectedLogin;
    if (recordedLogin !== undefined) {
      if (recordedLogin !== worker.githubLogin) incompatible();
      continue;
    }
    // Legacy records did not persist the expected author. Never invent it from
    // the new login: require an operator's exact invocation-bound attribution.
    const binding = worker.legacyInvocationIdentities.find(entry => entry.invocationId === claim.invocationId);
    if (!binding || binding.githubLogin !== worker.githubLogin) incompatible();
  }
}
