import { execFileSync } from "node:child_process";
import { createPrivateKey, createSign } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { isAbsolute } from "node:path";
import { lifecycleStatuses } from "../domain/lifecycle.mjs";

const permissions = { issues: "read", metadata: "read", organization_projects: "write" };
const events = ["issue_comment", "projects_v2_item"];
const defaultRuntimePath = "/usr/local/bin:/usr/bin:/bin";
const refreshWindowMs = 60_000;

function minimalPermissions(actual) {
  return actual && Object.keys(actual).length === Object.keys(permissions).length
    && Object.entries(permissions).every(([key, value]) => actual[key] === value);
}

function requiredEvents(actual) {
  return Array.isArray(actual) && events.every((event) => actual.includes(event));
}

// This adapter is the sole control-plane credential boundary. It preserves the
// synchronous gh contract consumed by GitHubAuthority; nothing is put in env globally.
export function createGitHubAppClient(config, {
  execute = execFileSync, readKey = readFileSync, keyStat = statSync, now = Date.now,
} = {}) {
  if (config?.ghCommand !== undefined) throw new Error("AlienIntent: remove legacy config.ghCommand; GitHub App authentication is required");
  const runtimePath = config?.runtimePath ?? defaultRuntimePath;
  const githubCli = config?.executables?.githubCli ?? "gh";
  const curl = config?.executables?.curl ?? "curl";
  const app = config?.githubApp;
  if (!app || Object.keys(app).some((key) => !["appId", "installationId", "privateKeyPath"].includes(key))) {
    throw new Error("AlienIntent: config.githubApp requires only appId, installationId and privateKeyPath");
  }
  for (const key of ["appId", "installationId"]) {
    if (!Number.isSafeInteger(app[key]) || app[key] <= 0) throw new Error(`AlienIntent: invalid config.githubApp.${key}`);
  }
  if (typeof app.privateKeyPath !== "string" || !isAbsolute(app.privateKeyPath)) throw new Error("AlienIntent: privateKeyPath must be absolute");
  const repository = config.repository;
  const parts = typeof repository === "string" ? repository.split("/") : [];
  if (parts.length !== 2 || !parts.every((part) => /^[A-Za-z0-9_.-]+$/.test(part))
    || parts[0] !== config.projectOwner || !Number.isSafeInteger(config.projectNumber) || config.projectNumber <= 0) {
    throw new Error("AlienIntent: invalid repository or organization Project configuration");
  }
  let privateKey;
  try {
    const info = keyStat(app.privateKeyPath);
    if (!info.isFile() || ![0o600, 0o400].includes(info.mode & 0o7777) || (process.getuid && info.uid !== process.getuid())) {
      throw new Error("unsafe key file");
    }
    privateKey = createPrivateKey(readKey(app.privateKeyPath));
    if (privateKey.asymmetricKeyType !== "rsa") throw new Error("RSA key required");
  } catch {
    throw new Error("AlienIntent: App key unavailable or invalid; require an owned RSA private-key file with mode 0600 or 0400");
  }
  let cached = null;

  function jwt() {
    try {
      const seconds = Math.floor(now() / 1000);
      const encode = (value) => Buffer.from(JSON.stringify(value)).toString("base64url");
      const unsigned = `${encode({ alg: "RS256", typ: "JWT" })}.${encode({ iat: seconds - 60, exp: seconds + 540, iss: String(app.appId) })}`;
      return `${unsigned}.${createSign("RSA-SHA256").update(unsigned).sign(privateKey, "base64url")}`;
    } catch {
      throw new Error("AlienIntent: App JWT signing failed");
    }
  }

  function transport(command, args, options, operation) {
    let value;
    try {
      const output = execute(command, args, {
        encoding: "utf8", timeout: 30_000, maxBuffer: 16 * 1024 * 1024,
        stdio: ["ignore", "pipe", "pipe"], ...options,
      });
      value = JSON.parse(output);
      if (value?.errors?.length) throw new Error("GraphQL rejected request");
      return { output, value };
    } catch (error) {
      // Project only known classifications and bounded numbers. Never copy free
      // text, command arguments, headers, response bodies, or the original cause.
      if (!value) { try { value = JSON.parse(error.stdout); } catch {} }
      const stderr = typeof error.stderr === "string" || Buffer.isBuffer(error.stderr) ? String(error.stderr) : "";
      const http = stderr.match(/(?:HTTP(?:\/\d(?:\.\d)?)?\s+|returned error:\s*)([45]\d{2})\b/)?.[1];
      const graphql = Array.isArray(value?.errors) ? value.errors : [];
      const knownTypes = new Set(["FORBIDDEN", "UNAUTHENTICATED", "NOT_FOUND", "RATE_LIMITED", "INTERNAL", "INTERNAL_SERVER_ERROR", "SERVICE_UNAVAILABLE", "GRAPHQL_VALIDATION_FAILED", "MAX_NODE_LIMIT_EXCEEDED"]);
      const types = [...new Set(graphql.flatMap((entry) => [entry?.type, entry?.extensions?.code]).filter((type) => knownTypes.has(type)))];
      const knownCodes = new Set(["ETIMEDOUT", "ECONNRESET", "ECONNREFUSED", "ENOTFOUND", "EAI_AGAIN", "ENETUNREACH", "EHOSTUNREACH", "ENOENT", "EACCES", "ENOBUFS"]);
      let code = knownCodes.has(error.code) ? error.code : null;
      if (!code && /no such host|could not resolve host/i.test(stderr)) code = "DNS";
      if (!code && /connection refused|failed to connect/i.test(stderr)) code = "CONNECTION_FAILED";
      if (!code && /timed out|timeout/i.test(stderr)) code = "ETIMEDOUT";
      if (!code && /certificate|TLS handshake/i.test(stderr)) code = "TLS";
      const rateLimited = http === "429" || types.includes("RATE_LIMITED") || /(?:rate limit|secondary rate|abuse detection)/i.test(stderr);
      const category = rateLimited ? "RATE_LIMIT" : graphql.length ? "GRAPHQL" : http ? "HTTP" : code ? "NETWORK" : error instanceof SyntaxError ? "INVALID_JSON" : "TRANSPORT";
      const detail = [`category=${category}`];
      if (http) detail.push(`http_status=${Number(http)}`);
      if (types.length) detail.push(`graphql=${types.join(",")}`);
      if (code) detail.push(`code=${code}`);
      if (Number.isInteger(error.status) && error.status >= 0 && error.status <= 255) detail.push(`exit_status=${error.status}`);
      for (const [header, field] of [["x-ratelimit-limit", "rate_limit"], ["x-ratelimit-remaining", "rate_remaining"], ["x-ratelimit-reset", "rate_reset"], ["retry-after", "retry_after"]]) {
        const match = stderr.match(new RegExp(`^${header}:\\s*(\\d{1,12})\\s*$`, "im"));
        if (match) detail.push(`${field}=${Number(match[1])}`);
      }
      throw new Error(`AlienIntent: ${operation} failed; ${detail.join("; ")}; check App installation, permissions, connectivity and GitHub quota`);
    }
  }

  function request(args, credential, operation) {
    return transport(githubCli, [...args, "--hostname", "github.com"], {
      env: { PATH: runtimePath, GH_CONFIG_DIR: "/proc/self/fd", GH_TOKEN: credential,
        GH_PROMPT_DISABLED: "1", GH_PAGER: "cat", LANG: "C.UTF-8" },
    }, operation);
  }

  function appRequest(path, operation, body) {
    // gh sends GH_TOKEN with the token scheme, which GitHub rejects for App
    // JWTs. curl receives Bearer over stdin, never argv or inherited config.
    const args = ["--disable", "--fail", "--silent", "--show-error", "--max-time", "30",
      "--request", body ? "POST" : "GET", "--url", `https://api.github.com${path}`, "--header", "@-"];
    if (body) args.push("--data", JSON.stringify(body));
    return transport(curl, args, {
      env: { PATH: runtimePath, LANG: "C.UTF-8" }, stdio: ["pipe", "pipe", "pipe"],
      input: `Authorization: Bearer ${jwt()}\nAccept: application/vnd.github+json\nContent-Type: application/json\nX-GitHub-Api-Version: 2022-11-28\n`,
    }, operation);
  }

  function installationToken() {
    if (cached && cached.expiresAt - now() > refreshWindowMs) return cached.token;
    cached = null;
    const { value } = appRequest(`/app/installations/${app.installationId}/access_tokens`,
      "App installation-token mint", { repositories: [parts[1]], permissions });
    const expiresAt = Date.parse(value?.expires_at);
    if (typeof value?.token !== "string" || !value.token || !Number.isFinite(expiresAt)
      || expiresAt - now() <= refreshWindowMs || expiresAt - now() > 3_660_000 || !minimalPermissions(value.permissions)) {
      throw new Error("AlienIntent: invalid installation-token expiry or permissions");
    }
    cached = { token: value.token, expiresAt };
    return cached.token;
  }

  function gh(args) {
    if (!Array.isArray(args) || args[0] !== "api" || typeof args[1] !== "string") {
      throw new Error("AlienIntent: control-plane client supports only bounded gh api calls");
    }
    const endpoint = args[1].replace(/^\//, "");
    const issueRoot = `repos/${repository}/issues`;
    const issuePath = endpoint === issueRoot || (endpoint.startsWith(`${issueRoot}/`)
      && /^\d+(?:\/comments)?$/.test(endpoint.slice(issueRoot.length + 1)));
    if (endpoint !== "graphql" && endpoint !== "installation/repositories" && !issuePath) {
      throw new Error("AlienIntent: control-plane endpoint is outside the configured authority");
    }
    for (let index = 2; index < args.length; index++) {
      if (args[index] === "--paginate" && issuePath) continue;
      if (endpoint === "graphql" && ["-f", "-F"].includes(args[index])) {
        const field = args[++index];
        if (typeof field === "string" && /^[A-Za-z][A-Za-z0-9_]*=(?!@)/.test(field)) continue;
      }
      throw new Error("AlienIntent: unsupported control-plane API option");
    }
    // The canonical authority uses GraphQL JSON (including its sole mutation)
    // and Issue-comment JSON; preflight adds installation/repositories JSON.
    // Non-JSON/204 mutation endpoints are deliberately outside this contract.
    // gh --paginate emits one document per page; --slurp makes that strict JSON.
    if (args.includes("--paginate")) {
      const { value: pages } = request([...args, "--slurp"], installationToken(), "App paginated Issue read");
      if (!Array.isArray(pages) || !pages.every(Array.isArray)) throw new Error("AlienIntent: invalid paginated Issue response");
      return JSON.stringify(pages.flat());
    }
    return request(args, installationToken(), "App control-plane API request").output;
  }

  function preflight() {
    const registration = appRequest("/app", "App registration read").value;
    const installation = appRequest(`/app/installations/${app.installationId}`, "App installation read").value;
    if (registration.id !== app.appId || registration.owner?.login !== config.projectOwner || !registration.slug
      || installation.id !== app.installationId || installation.app_id !== app.appId
      || installation.account?.login !== config.projectOwner || installation.target_type !== "Organization"
      || installation.repository_selection !== "selected" || installation.suspended_at
      || !minimalPermissions(registration.permissions) || !minimalPermissions(installation.permissions)
      || !requiredEvents(registration.events) || !requiredEvents(installation.events)) {
      throw new Error("AlienIntent: App installation identity, least-privilege permissions or webhook subscriptions do not match configuration");
    }
    const accessible = JSON.parse(gh(["api", "/installation/repositories"]));
    if (accessible.total_count !== 1 || accessible.repositories?.length !== 1 || accessible.repositories[0].full_name !== repository) {
      throw new Error("AlienIntent: installation token must access only the configured repository");
    }
    const query = "query($owner: String!, $name: String!, $number: Int!) { viewer { login } organization(login: $owner) { projectV2(number: $number) { id viewerCanUpdate fields(first: 100) { pageInfo { hasNextPage } nodes { ... on ProjectV2SingleSelectField { name options { name } } } } } } repository(owner: $owner, name: $name) { nameWithOwner issues(first: 1) { nodes { number comments(first: 1) { nodes { id } } } } } }";
    const response = JSON.parse(gh(["api", "graphql", "-f", `query=${query}`, "-F", `owner=${config.projectOwner}`, "-F", `name=${parts[1]}`, "-F", `number=${config.projectNumber}`]));
    const project = response.data?.organization?.projectV2;
    const statusFields = Array.isArray(project?.fields?.nodes) ? project.fields.nodes.filter((field) => field?.name === "Status") : [];
    const status = statusFields.length === 1 ? statusFields[0] : null;
    if (response.data?.viewer?.login !== `${registration.slug}[bot]` || !project?.id || project.viewerCanUpdate !== true
      || response.data?.repository?.nameWithOwner !== repository || !Array.isArray(response.data?.repository?.issues?.nodes)
      || project?.fields?.pageInfo?.hasNextPage !== false
      || !Array.isArray(status?.options) || status.options.length !== lifecycleStatuses.length
      || !lifecycleStatuses.every((name, index) => typeof status.options[index]?.name === "string"
        && status.options[index].name.toUpperCase() === name)) {
      throw new Error("AlienIntent: App Project/Issue read or transition capability preflight failed");
    }
    return { identity: `${registration.slug}[bot]`, appId: app.appId, installationId: app.installationId,
      repository, projectId: project.id, projectCanUpdate: true, tokenExpiresAt: new Date(cached.expiresAt).toISOString() };
  }

  return { gh, preflight };
}
