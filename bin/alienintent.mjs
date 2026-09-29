#!/usr/bin/env node
import { createServer } from "node:http";
import { mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { homedir } from "node:os";
import { EventRelay, verifyWebhookSignature } from "../src/runtime/dispatcher.mjs";
import { GitHubAuthority } from "../src/github/authority.mjs";
import { createGitHubAppClient } from "../src/github/app-client.mjs";
import { createWorkerLauncher, createPreflight, inspectWorker } from "../src/runtime/worker-runner.mjs";
import { createWorktreeManager } from "../src/runtime/worktree-manager.mjs";
import { loadProfile } from "../src/config/profile.mjs";
import { resolveRoute } from "../src/config/model-routing.mjs";

if (process.argv.includes("--help")) {
  console.log("Usage: alienintent --config <profile.json> [--preflight-only | --once]\nExecution disabled suppresses launches, not reconciliation mutations.");
  process.exit(0);
}
const i = process.argv.indexOf("--config");
if (i < 0 || !process.argv[i + 1]) throw new Error("--config is required");
const config = loadProfile(process.argv[i + 1]);
const appClient = createGitHubAppClient(config);
const appEvidence = appClient.preflight();
console.log(`AlienIntent App preflight: ${JSON.stringify(appEvidence)}`);
if (process.argv.includes("--preflight-only")) process.exit(0);
mkdirSync(dirname(config.statePath), { recursive: true });
const authority = new GitHubAuthority({ gh: appClient.gh, owner: config.projectOwner,
  projectNumber: config.projectNumber, repository: config.repository,
  workerLogins: config.workerLogins, roleNames: config.roleNames,
  authorizedOperatorLogins: config.authorizedOperatorLogins });
const factoryPolicy = () => {
  try {
    const host = JSON.parse(readFileSync(join(homedir(), ".config/alienintent/factory-director-host.json"), "utf8"));
    if (!Number.isSafeInteger(host.wipLimit) || host.wipLimit < 1 || typeof host.founderHoldRecord !== "string") return null;
    const holds = JSON.parse(readFileSync(host.founderHoldRecord, "utf8"));
    if (holds.schemaVersion !== 1 || !Array.isArray(holds.holds)
        || holds.holds.some(hold => !Number.isSafeInteger(hold.issue) || hold.issue < 1 || hold.kind !== "FOUNDER_DECISION")) return null;
    let paused = false;
    try { statSync(host.pauseFlag); paused = true; }
    catch (error) { if (error.code !== "ENOENT") return null; }
    return { wipLimit: host.wipLimit, holds: holds.holds, paused };
  } catch { return null; }
};
const preflightScript = config.executables.preflight;
const preflight = createPreflight({ repository: config.repository, workers: config.workers,
  node: config.executables.node, script: preflightScript });
const relay = new EventRelay({ onEvent: event => console.info(JSON.stringify(event)),
  statePath: config.statePath, repository: config.repository, projectOwner: config.projectOwner,
  workerLogins: config.workerLogins, roleNames: config.roleNames,
  authorizedOperatorLogins: config.authorizedOperatorLogins, appIdentity: appEvidence.identity,
  workerDisplayNames: Object.fromEntries(Object.entries(config.workers).map(([role, worker]) => [role, worker.displayName])),
  executionEnabled: config.executionEnabled, biuLimits: config.biuLimits, authority, workers: config.workers,
  admissionEvidence: async (item, status) => {
    const policy = factoryPolicy();
    if (!policy || policy.paused || policy.holds.some(hold => hold.issue === item.issue))
      return { eligible: false, reason: "FACTORY_POLICY_UNAVAILABLE_OR_HELD" };
    return authority.admissionEvidence(item, status);
  },
  getWipLimit: () => factoryPolicy()?.wipLimit,
  worktreeManager: config.executionEnabled ? createWorktreeManager({ repository: config.repository,
    repositoryStore: config.repositoryStore, worktreeRoot: config.worktreeRoot,
    baselineRef: config.baselineRef, git: config.executables.git }) : undefined,
  inspectionIntervalMs: config.inspectionIntervalMs, preflight,
  inspectWorker: child => inspectWorker(child, { executable: config.executables.processInspector }),
  launch: createWorkerLauncher({ workers: config.workers, routeResolver: resolveRoute }) });
await relay.startupReconcile();
if (process.argv.includes("--once")) { relay.stop(); process.exit(0); }
const server = createServer(async (request, response) => {
  const chunks = []; let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 1024 * 1024) { response.writeHead(413).end(); return; }
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks);
  if (request.method !== "POST" || !verifyWebhookSignature(config.webhookSecret, raw, request.headers["x-hub-signature-256"])) {
    response.writeHead(401).end(); return;
  }
  try {
    await relay.acceptEvent({ headers: request.headers, payload: JSON.parse(raw) });
    response.writeHead(202).end();
  } catch (error) { console.error(`AlienIntent webhook failed: ${error.message}`); response.writeHead(500).end(); }
}).listen(config.port, config.host);
const admissionTimer = setInterval(() => relay.reconcileAdmissions().catch(error =>
  console.error(`AlienIntent admission reconciliation failed: ${error.message}`)), 60000);
admissionTimer.unref();
server.once("listening", () => relay.reconcileAdmissions().catch(error =>
  console.error(`AlienIntent admission reconciliation failed: ${error.message}`)));
const shutdown = () => { clearInterval(admissionTimer); relay.stop(); server.close(); server.closeIdleConnections(); };
process.once("SIGTERM", shutdown);
process.once("SIGINT", shutdown);
server.once("close", () => { clearInterval(admissionTimer); relay.stop(); });
