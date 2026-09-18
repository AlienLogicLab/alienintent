import assert from "node:assert/strict";
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { syntheticProfile } from "./helpers/profile.mjs";
import { generateKeyPairSync } from "node:crypto";
const source = readFileSync(new URL("../bin/alienintent.mjs", import.meta.url), "utf8");
test("webhook CLI verifies HMAC and acknowledges asynchronously", () => { assert.match(source, /verifyWebhookSignature/); assert.match(source, /response\.writeHead\(202\)/); assert.doesNotMatch(source, /setInterval|LeaseStore|WorkerProcessRegistry/); });
test("preflight executes the canonical repository script from each disposable worker cwd", () => {
  assert.match(source, /config\.executables\.preflight/);
  assert.match(source, /execFileSync\(config\.executables\.node, \[preflightScript,/);
  assert.match(source, /cwd: worker\.worktree/);
  assert.match(source, /env: workerEnvironment\(\{ role, worker \}\)/);
});
test("preflight receives the dispatched item issue", () => {
  assert.match(source, /const preflight = async \(\{ role, item, invocationId, worktree, resource \}\)/);
  assert.match(source, /"--issue", String\(item\.issue\)/);
  assert.match(source, /input: JSON\.stringify\(worker\)/);
  assert.doesNotMatch(source, /config\.preflightIssue \?\? 11/);
});

test("operator documents invocation-correlated markers, Accept routing, and dry-run limits", () => {
  const operator = readFileSync(new URL("../docs/operations.md", import.meta.url), "utf8");
  assert.match(operator, /<!-- B-DISP: INVOCATION=<exact-id> RESULT=VERIFY -->/);
  assert.doesNotMatch(operator, /<!-- B-DISP: RESULT=/);
  assert.match(operator, /Verifier `ACCEPT` routes to.*`Accept`/);
  assert.match(operator, /does not run.*preflight/);
});

test("production CLI dry-run reports actionable item without worker/preflight or ledger config", () => {
  const dir = mkdtempSync(join(tmpdir(), "b-disp-cli-repair-"));
  try {
    const keyPath = join(dir, "key.pem");
    const { privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
    writeFileSync(keyPath, privateKey.export({ type: "pkcs8", format: "pem" }), { mode: 0o600 });
    // Replace only subprocess transport; execute the real CLI, App provider and relay offline.
    const transport = join(dir, "transport.mjs");
    writeFileSync(transport, `
      import childProcess from "node:child_process";
      import { syncBuiltinESMExports } from "node:module";
      const permissions = { issues: "read", metadata: "read", organization_projects: "write" };
      const events = ["issue_comment", "projects_v2_item"];
      childProcess.execFileSync = (command, args) => {
        const endpoint = command.endsWith("curl") ? new URL(args[args.indexOf("--url") + 1]).pathname : args[1];
        if (command.endsWith("curl") && endpoint === "/app") return JSON.stringify({ id: 1, slug: "test-app", owner: { login: "ExampleOrg" }, permissions, events });
        if (command.endsWith("curl") && endpoint === "/app/installations/2") return JSON.stringify({ id: 2, app_id: 1, account: { login: "ExampleOrg" }, target_type: "Organization", repository_selection: "selected", permissions, events });
        if (command.endsWith("curl") && endpoint === "/app/installations/2/access_tokens") return JSON.stringify({ token: "test-token", expires_at: new Date(Date.now() + 3600000).toISOString(), permissions });
        if (command.endsWith("gh") && endpoint === "/installation/repositories") return JSON.stringify({ total_count: 1, repositories: [{ full_name: "ExampleOrg/sample-project" }] });
        if (command.endsWith("gh") && endpoint === "graphql") {
          const query = args.find(arg => arg.startsWith("query="));
          if (query.includes("viewerCanUpdate")) return JSON.stringify({ data: {
            viewer: { login: "test-app[bot]" }, repository: { nameWithOwner: "ExampleOrg/sample-project", issues: { nodes: [] } },
            organization: { projectV2: { id: "project", viewerCanUpdate: true, fields: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Status", options: ["Implement", "Verify", "Accept", "Done"].map(name => ({ name })) }] } } }
          } });
          if (query.includes("items(first:")) return JSON.stringify({data:{organization:{projectV2:{items:{pageInfo:{hasNextPage:false},nodes:[{id:"item",content:{__typename:"Issue",number:1041,repository:{nameWithOwner:"ExampleOrg/sample-project"}},fieldValues:{pageInfo:{hasNextPage:false},nodes:[{name:"Implement",field:{name:"Status"}}]}}]}}}}});
        }
        throw new Error("unexpected subprocess in offline CLI test");
      };
      syncBuiltinESMExports();
    `);
    const config = join(dir, "config.json");
    writeFileSync(config, JSON.stringify(syntheticProfile(dir, { keyPath })));
    const run = spawnSync(process.execPath, ["--import", transport, new URL("../bin/alienintent.mjs", import.meta.url).pathname, "--config", config, "--once"], { encoding: "utf8", timeout: 10000 });
    assert.equal(run.status, 0, run.stderr);
    assert.match(run.stdout, /AlienIntent App preflight:/);
    assert.match(run.stdout, /DRY_RUN_ACTIONABLE/);
    assert.doesNotMatch(run.stdout, /PREFLIGHT_FAILED|WORKER_TECHNICAL_FAILURE/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("CLI service shutdown reaches relay timer cancellation", () => {
  assert.match(source, /process\.once\("SIGTERM", shutdown\)/);
  assert.match(source, /process\.once\("SIGINT", shutdown\)/);
  assert.match(source, /const shutdown = \(\) => \{ relay\.stop\(\)/);
  assert.match(source, /server\.once\("close", \(\) => relay\.stop\(\)\)/);
});


test("public executable and temporary compatibility alias share help and validation", () => {
  const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
  assert.equal(pkg.name, "alienintent");
  const outputs = [];
  for (const name of ["alienintent", "b-disp"]) {
    const executable = new URL(`../${pkg.bin[name]}`, import.meta.url).pathname;
    const help = spawnSync(process.execPath, [executable, "--help"], { encoding: "utf8" });
    assert.equal(help.error, undefined);
    assert.equal(help.status, 0, help.stderr);
    assert.match(help.stdout, /^Usage: alienintent /);
    outputs.push(help.stdout);
    const invalid = spawnSync(process.execPath, [executable], { encoding: "utf8" });
    assert.notEqual(invalid.status, 0);
    assert.match(invalid.stderr, /--config is required/);
  }
  assert.equal(outputs[0], outputs[1]);
});
