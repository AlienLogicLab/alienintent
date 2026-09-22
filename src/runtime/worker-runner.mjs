import { createSystemdSupervisor } from "./systemd-supervision.mjs";
import { spawn, execFileSync } from "node:child_process";
import { appendFileSync, mkdirSync } from "node:fs";
import { join, isAbsolute } from "node:path";
import { codexArguments } from "../providers/codex.mjs";
import { claudeArguments } from "../providers/claude.mjs";
// A bounded snapshot only when an owned-child inspection timer fires. Failure
// to inspect is unknown, never evidence that the child exited or is stuck.
export function inspectWorker(child, { executable = "ps" } = {}) {
  if (!Number.isInteger(child.pid) || child.pid <= 0) return {};
  try {
    const [state, waitChannel] = execFileSync(executable, ["-o", "stat=,wchan=", "-p", String(child.pid)], { encoding: "utf8", timeout: 1000 }).trim().split(/\s+/);
    return { state, waitChannel };
  } catch { return {}; }
}
const safeNames = ["HOME", "USER", "LOGNAME", "LANG", "SHELL", "TERM"];
export function workerEnvironment({ worker, environment = process.env }) {
  if (!worker?.ghShimDir || !worker.ghConfigDir || !worker.runtimePath || !worker.executables?.githubCli) throw new Error("WORKER_ENVIRONMENT_REQUIRED");
  const safe = {};
  for (const key of worker.environment?.inheritNames ?? safeNames) {
    if (!safeNames.includes(key)) throw new Error(`UNSAFE_INHERITED_ENVIRONMENT: ${key}`);
    if (environment[key] !== undefined) safe[key] = environment[key];
  }
  for (const [key, value] of Object.entries(worker.environment?.values ?? {})) {
    if (!safeNames.includes(key) || typeof value !== "string") throw new Error(`UNSAFE_WORKER_ENVIRONMENT: ${key}`);
    safe[key] = value;
  }
  return { ...safe, PATH: `${worker.ghShimDir}:${worker.runtimePath}`, GH_CONFIG_DIR: worker.ghConfigDir, B_DISP_GH_CONFIG_DIR: worker.ghConfigDir, B_DISP_GH_EXECUTABLE: worker.executables.githubCli };
}
export function workerLogPath(invocationId, logDirectory) { return join(logDirectory, `${encodeURIComponent(invocationId)}.log`); }
function subscriptionStatus(command, options) {
  try { return JSON.parse(execFileSync(command, ["auth", "status", "--json"], { ...options, encoding: "utf8", timeout: 10000, stdio: ["ignore", "pipe", "pipe"] })); }
  catch { throw new Error("CLAUDE_SUBSCRIPTION_AUTH_REQUIRED"); }
}
export function spawnWorker({ role, worker, item, invocationId, bootstrap, resource, supervisor, authenticate = subscriptionStatus, execute = spawn, environment = process.env, logDirectory = worker.logDirectory }) {
  const options = { cwd: worker.worktree, env: workerEnvironment({ role, worker, environment }), stdio: ["ignore", "pipe", "pipe"] };
  if (worker.fundingProfile === "claude-subscription") {
    const auth = authenticate(worker.command, options);
    if (auth?.loggedIn !== true || auth.authMethod !== "claude.ai" || !["max", "pro", "team", "enterprise"].includes(auth.subscriptionType)) throw new Error("CLAUDE_SUBSCRIPTION_AUTH_REQUIRED");
  }
  const adapter = { codex: codexArguments, claude: claudeArguments }[worker.adapter];
  if (!adapter) throw new Error(`UNKNOWN_PROVIDER: ${worker.adapter}`);
  const args = adapter(worker, bootstrap);
  const logPath = workerLogPath(invocationId, logDirectory);
  mkdirSync(logDirectory, { recursive: true });
  appendFileSync(logPath, "");
  let child;
  if (worker.supervision) {
    if (resource?.supervision?.invocationId !== invocationId || !supervisor) throw new Error("SUPERVISION_INTENT_REQUIRED");
    child = supervisor.launch(resource.supervision, worker.command, args, options, logPath);
  } else child = execute(worker.command, args, options);
  // Persist each chunk immediately, including when no close event can arrive.
  const append = (data) => { try { appendFileSync(logPath, data); } catch {} };
  child.stdout?.on("data", append); child.stderr?.on("data", append);
  return child;
}
export function createWorkerLauncher({ workers, runner = spawnWorker, supervisorFactory = createSystemdSupervisor }) {
  const supervisors = Object.fromEntries(Object.entries(workers).filter(([, worker]) => worker.supervision).map(([role, worker]) => [role, supervisorFactory(worker.supervision)]));
  const launch = ({ role, item, invocationId, bootstrap, worktree, resource }) => {
    if (typeof worktree !== "string" || !isAbsolute(worktree) || worktree.includes("\0")) throw new Error("INVOCATION_WORKTREE_REQUIRED");
    if (!workers[role]) throw new Error("UNKNOWN_WORKER_ROLE");
    return runner({ role, worker: { ...workers[role], worktree }, item, invocationId, bootstrap, ...(resource ? { resource } : {}), ...(supervisors[role] ? { supervisor: supervisors[role] } : {}) });
  };
  launch.plan = request => supervisors[request.role]?.plan(request);
  launch.observe = (resource, persist) => {
    if (!supervisors[resource.role]) throw new Error("SUPERVISION_CONFIGURATION_REQUIRED");
    return supervisors[resource.role].observe(resource.supervision, persist);
  };
  return launch;
}
