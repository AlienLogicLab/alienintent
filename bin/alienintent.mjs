#!/usr/bin/env node
import { createServer } from "node:http";
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { EventRelay, verifyWebhookSignature } from "../src/runtime/dispatcher.mjs";
import { GitHubAuthority } from "../src/github/authority.mjs";
import { createGitHubAppClient } from "../src/github/app-client.mjs";
import { createWorkerLauncher, workerEnvironment, inspectWorker } from "../src/runtime/worker-runner.mjs";
import { createWorktreeManager } from "../src/runtime/worktree-manager.mjs";
import { loadProfile } from "../src/config/profile.mjs";
import { assertExecutionConformance } from "../src/runtime/execution-conformance.mjs";

if (process.argv.includes("--help")) {
  console.log("Usage: alienintent --config <profile.json> [--preflight-only | --once]\nExecution disabled suppresses launches, not reconciliation mutations.");
  process.exit(0);
}
const i = process.argv.indexOf("--config");
if (i < 0 || !process.argv[i + 1]) throw new Error("--config is required");
const config = loadProfile(process.argv[i + 1]);
if (config.executionEnabled) assertExecutionConformance({ controls: config.executionControls, runtime: { dispatcherControls: config.executionControls, supervision: config.supervision, workersSupervised: Object.values(config.workers).every(worker => worker.supervision === config.supervision) } });
const appClient = createGitHubAppClient(config);
const appEvidence = appClient.preflight();
console.log(`AlienIntent App preflight: ${JSON.stringify(appEvidence)}`);
if (process.argv.includes("--preflight-only")) process.exit(0);
mkdirSync(dirname(config.statePath), { recursive: true });
const authority = new GitHubAuthority({ gh: appClient.gh, owner: config.projectOwner,
  projectNumber: config.projectNumber, repository: config.repository,
  workerLogins: config.workerLogins, roleNames: config.roleNames });
const preflightScript = config.executables.preflight;
const preflight = async ({ role, item, invocationId, worktree, resource }) => {
  try {
    if (!worktree || resource?.path !== worktree || resource?.invocationId !== invocationId) return { ok: false };
    const worker = { ...config.workers[role], role, worktree, resource, invocationId };
    const value = JSON.parse(execFileSync(config.executables.node, [preflightScript,
      "--repository", config.repository, "--issue", String(item.issue), "--json"], {
      cwd: worker.worktree, encoding: "utf8", input: JSON.stringify(worker),
      env: workerEnvironment({ role, worker }),
    }));
    return { ok: value.safe_to_start === true };
  } catch { return { ok: false }; }
};
const relay = new EventRelay({ onEvent: event => console.info(JSON.stringify(event)),
  statePath: config.statePath, repository: config.repository, projectOwner: config.projectOwner,
  workerLogins: config.workerLogins, roleNames: config.roleNames,
  authorizedOperatorLogins: config.authorizedOperatorLogins, appIdentity: appEvidence.identity,
  workerDisplayNames: Object.fromEntries(Object.entries(config.workers).map(([role, worker]) => [role, worker.displayName])),
  executionEnabled: config.executionEnabled, requireExecutionControls: config.executionEnabled, executionControls: config.executionControls, authority, workers: config.workers,
  worktreeManager: config.executionEnabled ? createWorktreeManager({ repository: config.repository,
    repositoryStore: config.repositoryStore, worktreeRoot: config.worktreeRoot,
    baselineRef: config.baselineRef, git: config.executables.git }) : undefined,
  inspectionIntervalMs: config.inspectionIntervalMs, preflight,
  inspectWorker: child => inspectWorker(child, { executable: config.executables.processInspector }),
  launch: createWorkerLauncher({ workers: config.workers }) });
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
const shutdown = () => { relay.stop(); server.close(); server.closeIdleConnections(); };
process.once("SIGTERM", shutdown);
process.once("SIGINT", shutdown);
server.once("close", () => relay.stop());
