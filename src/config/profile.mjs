import { readFileSync } from "node:fs";
import { isAbsolute } from "node:path";
import { fileURLToPath } from "node:url";
import { verifyStateCompatibility } from "./state-compatibility.mjs";

const roles = ["PRODUCER", "VERIFIER"];
const statuses = ["IMPLEMENT", "VERIFY", "REVIEW", "ACCEPT", "DONE"];
const inherited = ["HOME", "USER", "LOGNAME", "LANG", "SHELL", "TERM"];
const fail = field => { throw new Error(`AlienIntent: invalid config.${field}`); };
function object(value, field, keys) {
  if (!value || typeof value !== "object" || Array.isArray(value)
      || Object.keys(value).some(key => !keys.includes(key))) fail(field);
  return value;
}
function text(value, field) {
  if (typeof value !== "string" || !value.trim() || value.includes("\0")) fail(field);
  return value;
}
function path(value, field) {
  if (!isAbsolute(text(value, field))) fail(field);
  return value;
}
function positive(value, field) {
  if (!Number.isSafeInteger(value) || value <= 0) fail(field);
  return value;
}
function strings(value, field) {
  if (!Array.isArray(value) || value.some(v => typeof v !== "string" || !v.trim() || v.includes("\0"))) fail(field);
  return value;
}

export function loadProfile(profilePath) {
  let p;
  try { p = JSON.parse(readFileSync(profilePath, "utf8")); }
  catch { throw new Error("AlienIntent: configuration file unavailable or invalid JSON"); }
  object(p, "profile", ["repository", "project", "githubApp", "webhook", "execution", "operator", "paths", "executables", "environment", "workers"]);
  object(p.githubApp, "githubApp", ["applicationId", "installationId", "privateKeyPath"]);
  const githubApp = {
    appId: positive(p.githubApp.applicationId, "githubApp.applicationId"),
    installationId: positive(p.githubApp.installationId, "githubApp.installationId"),
    privateKeyPath: path(p.githubApp.privateKeyPath, "githubApp.privateKeyPath"),
  };
  object(p.repository, "repository", ["owner", "name", "baselineRef"]);
  for (const key of ["owner", "name"]) if (!/^[A-Za-z0-9_.-]+$/.test(text(p.repository[key], `repository.${key}`))) fail("repository");
  if (p.execution?.enabled || p.repository.baselineRef !== undefined) text(p.repository.baselineRef, "repository.baselineRef");
  object(p.project, "project", ["owner", "number", "statusFieldName", "statusNames"]);
  if (p.project.owner !== p.repository.owner || p.project.statusFieldName !== "Status") fail("project");
  positive(p.project.number, "project.number");
  object(p.project.statusNames, "project.statusNames", statuses);
  for (const status of statuses) if (typeof p.project.statusNames[status] !== "string" || p.project.statusNames[status].toUpperCase() !== status) fail("project.statusNames");
  object(p.webhook, "webhook", ["listenAddress", "listenPort", "secretFile"]);
  const host = text(p.webhook.listenAddress, "webhook.listenAddress");
  const port = positive(p.webhook.listenPort, "webhook.listenPort");
  if (port > 65535) fail("webhook.listenPort");
  path(p.webhook.secretFile, "webhook.secretFile");
  object(p.execution, "execution", ["enabled", "inspectionIntervalMilliseconds"]);
  if (typeof p.execution.enabled !== "boolean") fail("execution.enabled");
  const inspectionIntervalMs = p.execution.inspectionIntervalMilliseconds ?? 60000;
  if (!Number.isSafeInteger(inspectionIntervalMs) || inspectionIntervalMs < 1000 || inspectionIntervalMs > 300000) fail("execution.inspectionIntervalMilliseconds");
  object(p.operator, "operator", ["authorizedGithubLogins"]);
  const authorizedOperatorLogins = strings(p.operator.authorizedGithubLogins, "operator.authorizedGithubLogins");
  if (!authorizedOperatorLogins.length || new Set(authorizedOperatorLogins).size !== authorizedOperatorLogins.length) fail("operator.authorizedGithubLogins");
  object(p.paths, "paths", ["stateFile", "workerLogDirectory", "worktreeRoot", "temporaryDirectory", "evidenceDirectory", "repositoryStore"]);
  for (const key of ["stateFile", "workerLogDirectory", "worktreeRoot"]) path(p.paths[key], `paths.${key}`);
  for (const key of ["temporaryDirectory", "evidenceDirectory", "repositoryStore"]) if (p.paths[key] !== undefined) path(p.paths[key], `paths.${key}`);
  if (p.execution.enabled) path(p.paths.repositoryStore, "paths.repositoryStore");
  object(p.executables, "executables", ["node", "githubCli", "curl", "processInspector", "preflight", "git"]);
  const executables = { git: "/usr/bin/git", ...p.executables };
  path(executables.git, "executables.git");
  for (const key of ["node", "githubCli", "curl", "processInspector"]) path(executables[key], `executables.${key}`);
  executables.preflight ??= fileURLToPath(new URL("../../scripts/worker-preflight", import.meta.url));
  path(executables.preflight, "executables.preflight");
  object(p.environment, "environment", ["executableSearchPath"]);
  const runtimePath = text(p.environment.executableSearchPath, "environment.executableSearchPath");
  for (const component of runtimePath.split(":")) path(component, "environment.executableSearchPath");
  object(p.workers, "workers", roles);
  if ((p.execution.enabled || Object.keys(p.workers).length) && roles.some(role => !p.workers[role])) fail("workers");
  const roleNames = {}, workers = {}, workerLogins = {};
  const logins = new Set(authorizedOperatorLogins);
  for (const role of roles) {
    const w = p.workers[role];
    if (!w) { roleNames[role] = role; continue; }
    object(w, `workers.${role}`, ["displayName", "githubLogin", "gitIdentity", "provider", "githubAuthentication", "environment", "compatibility", "knownChanges"]);
    const displayName = text(w.displayName, "worker.displayName");
    const githubLogin = text(w.githubLogin, "worker.githubLogin");
    if (logins.has(githubLogin) || githubLogin.endsWith("[bot]")) fail("worker.githubLogin");
    logins.add(githubLogin);
    object(w.gitIdentity, "worker.gitIdentity", ["name", "email"]);
    const gitName = text(w.gitIdentity.name, "worker.gitIdentity.name");
    const gitEmail = text(w.gitIdentity.email, "worker.gitIdentity.email");
    object(w.provider, "worker.provider", ["adapter", "executablePath", "arguments", "permissionMode", "authenticationProfile", "fundingProfile"]);
    if (!["codex", "claude"].includes(w.provider.adapter)) fail("worker.provider.adapter");
    const command = path(w.provider.executablePath, "worker.provider.executablePath");
    const args = strings(w.provider.arguments, "worker.provider.arguments");
    const modes = w.provider.adapter === "codex" ? ["read-only", "workspace-write", "danger-full-access"] : ["manual"];
    if (!modes.includes(w.provider.permissionMode)) fail("worker.provider.permissionMode");
    object(w.provider.authenticationProfile, "worker.provider.authenticationProfile", ["name", "homeDirectory"]);
    const home = path(w.provider.authenticationProfile.homeDirectory, "worker.provider.authenticationProfile.homeDirectory");
    if (!["provider-default", "claude-subscription"].includes(w.provider.fundingProfile)
        || (w.provider.fundingProfile === "claude-subscription" && w.provider.adapter !== "claude")) fail("worker.provider.fundingProfile");
    object(w.githubAuthentication, "worker.githubAuthentication", ["configDirectory", "shimDirectory"]);
    const ghConfigDir = path(w.githubAuthentication.configDirectory, "worker.githubAuthentication.configDirectory");
    const ghShimDir = path(w.githubAuthentication.shimDirectory, "worker.githubAuthentication.shimDirectory");
    object(w.environment, "worker.environment", ["inheritNames", "values"]);
    const inheritNames = strings(w.environment.inheritNames, "worker.environment.inheritNames");
    if (inheritNames.some(name => !inherited.includes(name))) fail("worker.environment.inheritNames");
    object(w.environment.values, "worker.environment.values", inherited);
    for (const [key, value] of Object.entries(w.environment.values)) text(value, `worker.environment.values.${key}`);
    if (w.environment.values.HOME !== undefined && w.environment.values.HOME !== home) fail("worker.environment.values.HOME");
    object(w.compatibility, "worker.compatibility", ["persistedRoleValue", "legacyInvocationIdentities"]);
    const storedRole = text(w.compatibility.persistedRoleValue, "worker.compatibility.persistedRoleValue");
    if (!/^[A-Z][A-Z0-9_]*$/.test(storedRole) || Object.values(roleNames).includes(storedRole)
        || roles.some(other => other !== role && other === storedRole)) fail("worker.compatibility.persistedRoleValue");
    roleNames[role] = storedRole;
    const legacyInvocationIdentities = w.compatibility.legacyInvocationIdentities ?? [];
    if (!Array.isArray(legacyInvocationIdentities)) fail("worker.compatibility.legacyInvocationIdentities");
    const invocations = new Set();
    for (const entry of legacyInvocationIdentities) {
      object(entry, "worker.compatibility.legacyInvocationIdentities", ["invocationId", "githubLogin", "authority"]);
      text(entry.invocationId, "worker.compatibility.invocationId");
      text(entry.githubLogin, "worker.compatibility.githubLogin");
      text(entry.authority, "worker.compatibility.authority");
      if (invocations.has(entry.invocationId)) fail("worker.compatibility.legacyInvocationIdentities");
      invocations.add(entry.invocationId);
    }
    if (w.knownChanges !== undefined && !Array.isArray(w.knownChanges)) fail("worker.knownChanges");
    workerLogins[storedRole] = githubLogin;
    workers[storedRole] = { displayName, githubLogin, gitName, gitEmail, command,
      adapter: w.provider.adapter, arguments: args, permissionMode: w.provider.permissionMode,
      authenticationProfile: w.provider.authenticationProfile, fundingProfile: w.provider.fundingProfile,
      ghConfigDir, ghShimDir, runtimePath, logDirectory: p.paths.workerLogDirectory, executables,
      environment: { inheritNames, values: { ...w.environment.values, HOME: home } },
      knownChanges: w.knownChanges ?? [], legacyInvocationIdentities };
  }
  let webhookSecret;
  try { webhookSecret = readFileSync(p.webhook.secretFile, "utf8").trim(); if (!webhookSecret) throw new Error(); }
  catch { throw new Error("AlienIntent: webhook secret unavailable or empty"); }
  const config = { repository: `${p.repository.owner}/${p.repository.name}`, projectOwner: p.project.owner,
    projectNumber: p.project.number, githubApp, host, port, webhookSecret,
    repositoryStore: p.paths.repositoryStore, worktreeRoot: p.paths.worktreeRoot, baselineRef: p.repository.baselineRef,
    statePath: p.paths.stateFile, executionEnabled: p.execution.enabled, inspectionIntervalMs,
    roleNames, workers, workerLogins, authorizedOperatorLogins, executables, runtimePath };
  verifyStateCompatibility(config);
  return config;
}
