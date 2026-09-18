import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, verify } from 'node:crypto';
import { workerEnvironment } from '../src/runtime/worker-runner.mjs';
import * as provider from '../src/github/app-client.mjs';
import { EventEmitter } from 'node:events';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { GitHubAuthority } from '../src/github/authority.mjs';
import { EventRelay } from '../src/runtime/dispatcher.mjs';

const { privateKey, publicKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const pem = privateKey.export({ type: 'pkcs8', format: 'pem' });
const initialTime = Date.parse('2026-09-08T00:00:00Z');
const permissions = { issues: 'read', metadata: 'read', organization_projects: 'write' };
const config = () => ({ repository: 'ExampleOrg/sample-project', projectOwner: 'ExampleOrg', projectNumber: 1, githubApp: { appId: 10101, installationId: 20202, privateKeyPath: '/outside/repo/key.pem' } });

const fullLifecycle = ['CAPTURE', 'SPECIFY', 'PLAN', 'TASKS', 'READY', 'IMPLEMENT', 'VERIFY', 'REVIEW', 'ACCEPT', 'DONE'];
test('preflight accepts a complete lifecycle independently of dispatch lanes', () => {
  const fixtures = preflightFixture();
  const { client } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
  assert.equal(client.preflight().projectCanUpdate, true);
  fixtures.graphql.data.organization.projectV2.fields.nodes[0].options.forEach(option => { option.name = option.name.toLowerCase(); });
  assert.equal(client.preflight().projectCanUpdate, true);
});
for (const missing of fullLifecycle) test(`preflight rejects lifecycle missing ${missing}`, () => {
  const fixtures = preflightFixture();
  const fields = fixtures.graphql.data.organization.projectV2.fields;
  fields.nodes[0].options = fields.nodes[0].options.filter(option => option.name !== missing);
  const { client } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
  assert.throws(() => client.preflight(), /preflight failed/);
});
test('preflight rejects ambiguous or unsupported lifecycle options', () => {
  for (const mutate of [
    fields => fields.nodes.push(structuredClone(fields.nodes[0])),
    fields => fields.nodes[0].options.push({ name: 'MERGE' }),
    fields => fields.nodes[0].options.reverse(),
    fields => { fields.nodes[0].options = null; },
    fields => fields.nodes[0].options.push({ name: 'IMPLEMENT' }),
    fields => { fields.nodes[0].options[0] = { name: null }; },
  ]) {
    const fixtures = preflightFixture();
    mutate(fixtures.graphql.data.organization.projectV2.fields);
    const { client } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
    assert.throws(() => client.preflight(), /preflight failed/);
  }
});

for (const pageInfo of [{ hasNextPage: true }, undefined, { hasNextPage: null }]) {
  test(`preflight rejects unproven Project field completeness: ${JSON.stringify(pageInfo)}`, () => {
    const fixtures = preflightFixture();
    fixtures.graphql.data.organization.projectV2.fields.pageInfo = pageInfo;
    const { client } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
    assert.throws(() => client.preflight(), /preflight failed/);
  });
}

function harness({ response, keyStat, readKey, configuration = config() } = {}) {
  assert.equal(typeof provider.createGitHubAppClient, 'function', 'GitHub App provider must exist');
  let time = initialTime;
  let minted = 0;
  const calls = [];
  const client = provider.createGitHubAppClient(configuration, {
    now: () => time,
    readKey: readKey ?? (() => pem),
    keyStat: keyStat ?? (() => ({ mode: 0o100600, uid: process.getuid(), isFile: () => true })),
    execute(command, args, options) {
      const endpoint = args.includes('--url') ? new URL(args[args.indexOf('--url') + 1]).pathname : args[1];
      const call = { command, args, options, endpoint };
      calls.push(call);
      if (response) {
        const custom = response(call, calls);
        if (custom !== undefined) return typeof custom === 'string' ? custom : JSON.stringify(custom);
      }
      if (endpoint === '/app/installations/20202/access_tokens') {
        minted++;
        return JSON.stringify({ token: `fake-installation-token-${minted}`, expires_at: new Date(time + 3600000).toISOString(), permissions });
      }
      return JSON.stringify({ ok: true });
    },
  });
  return { client, calls, advance: ms => { time += ms; } };
}

test('rejects invalid authority configuration before accessing key or GitHub', () => {
  for (const mutate of [
    c => { delete c.githubApp; },
    c => { c.ghCommand = '/opt/b-disp/unsupported-personal-gh'; },
    c => { c.githubApp.appId = 0; },
    c => { c.githubApp.installationId = -1; },
    c => { c.githubApp.privateKeyPath = 'relative.pem'; },
    c => { c.repository = 'different/repository'; },
    c => { c.projectOwner = 'different'; },
    c => { c.projectNumber = 0; },
  ]) {
    const configuration = config(); mutate(configuration);
    assert.equal(typeof provider.createGitHubAppClient, 'function', 'GitHub App provider must exist');
    let accessed = false;
    assert.throws(() => provider.createGitHubAppClient(configuration, { readKey: () => { accessed = true; }, execute: () => { accessed = true; } }));
    assert.equal(accessed, false);
  }
});

test('signs a bounded RS256 JWT and requests only selected repository permissions', () => {
  const { client, calls } = harness();
  assert.deepEqual(JSON.parse(client.gh(['api', '/repos/ExampleOrg/sample-project/issues'])), { ok: true });
  const mint = calls[0];
  assert.equal(mint.command, 'curl');
  assert.equal(mint.args[0], '--disable', 'disable default curlrc before parsing other flags');
  assert.equal(mint.endpoint, '/app/installations/20202/access_tokens');
  assert.equal(mint.args[mint.args.indexOf('--url') + 1], 'https://api.github.com/app/installations/20202/access_tokens');
  assert.equal(mint.args[mint.args.indexOf('--request') + 1], 'POST');
  assert.deepEqual(JSON.parse(mint.args[mint.args.indexOf('--data') + 1]), { repositories: ['sample-project'], permissions: { issues: 'read', metadata: 'read', organization_projects: 'write' } });
  assert.equal(mint.args[mint.args.indexOf('--header') + 1], '@-');
  for (const flag of ['--fail', '--silent', '--show-error']) assert.ok(mint.args.includes(flag), flag);
  assert.equal(mint.args[mint.args.indexOf('--max-time') + 1], '30');
  assert.match(mint.options.input, /^Authorization: Bearer [^\n]+\n/);
  assert.match(mint.options.input, /Accept: application\/vnd.github\+json\n/);
  assert.match(mint.options.input, /X-GitHub-Api-Version: 2022-11-28\n/);
  const jwt = mint.options.input.match(/^Authorization: Bearer ([^\n]+)/)[1];
  assert.equal(mint.options.env.GH_TOKEN, undefined);
  assert.ok(!JSON.stringify(mint.args).includes(jwt), 'JWT must travel only over stdin');
  const [header, payload, signature] = jwt.split('.');
  assert.equal(JSON.parse(Buffer.from(header, 'base64url')).alg, 'RS256');
  const claims = JSON.parse(Buffer.from(payload, 'base64url'));
  assert.equal(String(claims.iss), '10101');
  assert.ok(claims.iat <= initialTime / 1000);
  assert.ok(claims.iat >= initialTime / 1000 - 60);
  assert.ok(claims.exp > initialTime / 1000 && claims.exp <= initialTime / 1000 + 600);
  assert.equal(verify('RSA-SHA256', Buffer.from(`${header}.${payload}`), publicKey, Buffer.from(signature, 'base64url')), true);
  assert.equal(calls[1].options.env.GH_TOKEN, 'fake-installation-token-1');
  assert.equal(calls[1].command, 'gh');
  assert.ok(!JSON.stringify(calls[1].args).includes('fake-installation-token-1'));
});

test('reuses an in-memory token until its refresh window then replaces it', () => {
  const { client, calls, advance } = harness();
  client.gh(['api', '/installation/repositories']);
  advance(3539000);
  client.gh(['api', '/installation/repositories']);
  assert.equal(calls.length, 3);
  assert.equal(calls[2].options.env.GH_TOKEN, 'fake-installation-token-1');
  advance(1000);
  client.gh(['api', '/installation/repositories']);
  assert.equal(calls.length, 5);
  assert.equal(calls[4].options.env.GH_TOKEN, 'fake-installation-token-2');
});

test('fails closed on expired, malformed, or over-permissioned mint responses', () => {
  for (const minted of [
    { token: 'fake-token', expires_at: 'invalid', permissions },
    { token: 'fake-token', expires_at: new Date(initialTime - 1000).toISOString(), permissions },
    { expires_at: new Date(initialTime + 3600000).toISOString(), permissions },
    { token: 'fake-token', expires_at: new Date(initialTime + 3600000).toISOString(), permissions: { ...permissions, contents: 'write' } },
  ]) {
    const { client, calls } = harness({ response: () => minted });
    assert.throws(() => client.gh(['api', '/installation/repositories']));
    assert.equal(calls.length, 1, 'invalid tokens must never reach a protected call');
  }
});

test('does not fall back to cached token when refresh fails', () => {
  let fail = false;
  const { client, calls, advance } = harness({ response: call => {
    if (fail && call.endpoint === '/app/installations/20202/access_tokens') throw new Error('fake-sensitive-refresh-stderr');
  } });
  client.gh(['api', '/installation/repositories']);
  advance(3540000); fail = true;
  assert.throws(() => client.gh(['api', '/installation/repositories']), error => !String(error).includes('fake-sensitive-refresh-stderr'));
  assert.equal(calls.length, 3);
});

test('scrubs inherited credentials, command overrides and debugging from gh child environment', () => {
  const poisoned = { GH_TOKEN: 'fake-personal', GITHUB_TOKEN: 'fake-github', GH_DEBUG: 'api', GH_HOST: 'evil.invalid', GH_CONFIG_DIR: '/unsafe/config', PATH: '/unsafe/path', CLAUDE_API_KEY: 'fake-worker', BASH_ENV: '/unsafe/env', NODE_OPTIONS: '--inspect', GIT_CONFIG_GLOBAL: '/unsafe/gitconfig' };
  const previous = Object.fromEntries(Object.keys(poisoned).map(key => [key, process.env[key]]));
  try {
    Object.assign(process.env, poisoned);
    const { client, calls } = harness(); client.gh(['api', '/installation/repositories']);
    for (const { command, args, options } of calls) {
      if (command === 'gh') {
        assert.equal(args[args.indexOf('--hostname') + 1], 'github.com');
        assert.equal(options.env.GH_CONFIG_DIR, '/proc/self/fd');
      } else {
        assert.equal(command, 'curl');
        assert.equal(args[0], '--disable');
        assert.equal(options.env.GH_TOKEN, undefined);
        assert.ok(args[args.indexOf('--url') + 1].startsWith('https://api.github.com/'));
      }
      assert.ok(!options.env.PATH.includes('/unsafe'));
      for (const key of Object.keys(poisoned).filter(key => !['GH_TOKEN', 'GH_CONFIG_DIR', 'PATH'].includes(key))) assert.equal(options.env[key], undefined, key);
      assert.ok(!JSON.stringify(args).includes('fake-personal'));
    }
    assert.equal(process.env.GH_TOKEN, 'fake-personal', 'parent credentials must not be overwritten');
  } finally {
    for (const [key, value] of Object.entries(previous)) value === undefined ? delete process.env[key] : process.env[key] = value;
  }
});

test('redacts key-read and gh errors without exposing nested stderr or causes', () => {
  assert.equal(typeof provider.createGitHubAppClient, 'function', 'GitHub App provider must exist');
  const leak = 'FAKE-SECRET-DO-NOT-LOG';
  const thrown = Object.assign(new Error(leak), { stderr: leak, stdout: leak });
  for (const overrides of [{ readKey: () => { throw thrown; } }, { response: () => { throw thrown; } }]) {
    assert.throws(() => { harness(overrides).client.gh(['api', '/installation/repositories']); }, error => {
      assert.ok(!String(error).includes(leak));
      assert.ok(!JSON.stringify(error).includes(leak));
      assert.equal(error.cause, undefined);
      return true;
    });
  }
});

test('worker subprocess environment excludes App, installation and personal credentials', () => {
  const environment = { HOME: '/safe/home', GH_TOKEN: 'fake-installation', GITHUB_TOKEN: 'fake-personal', GITHUB_APP_PRIVATE_KEY: pem, GITHUB_APP_ID: '10101', GH_DEBUG: 'api', GH_HOST: 'evil.invalid', PATH: '/unsafe' };
  const actual = workerEnvironment({ role: 'PRODUCER', worker: { ghConfigDir: '/opt/b-disp/auth/producer', ghShimDir: '/opt/b-disp/shims/producer', runtimePath: '/usr/bin:/bin', executables: { githubCli: '/usr/bin/gh' } }, environment });
  for (const key of ['GH_TOKEN', 'GITHUB_TOKEN', 'GITHUB_APP_PRIVATE_KEY', 'GITHUB_APP_ID', 'GH_DEBUG', 'GH_HOST']) assert.equal(actual[key], undefined);
  assert.ok(!JSON.stringify(actual).includes('PRIVATE KEY'));
});

function preflightFixture() {
  return {
    '/app': { id: 10101, slug: 'b-disp-example', owner: { login: 'ExampleOrg' }, permissions: { ...permissions }, events: ['projects_v2_item', 'issue_comment'] },
    '/app/installations/20202': { id: 20202, app_id: 10101, app_slug: 'b-disp-example', account: { login: 'ExampleOrg' }, target_type: 'Organization', repository_selection: 'selected', suspended_at: null, permissions: { ...permissions }, events: ['projects_v2_item', 'issue_comment'] },
    '/installation/repositories': { total_count: 1, repositories: [{ full_name: 'ExampleOrg/sample-project' }] },
    graphql: { data: { viewer: { login: 'b-disp-example[bot]' }, organization: { projectV2: { id: 'PVT_project', viewerCanUpdate: true, fields: { pageInfo: { hasNextPage: false }, nodes: [{ name: 'Status', options: fullLifecycle.map(name => ({ name })) }] } } }, repository: { nameWithOwner: 'ExampleOrg/sample-project', issues: { nodes: [{ number: 302, comments: { nodes: [] } }] } } } },
  };
}

test('preflight verifies App installation, repository scope and bot project authority without leaking credentials', () => {
  const fixtures = preflightFixture();
  const { client, calls } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
  const summary = client.preflight();
  assert.match(calls.find(call => call.endpoint === 'graphql').args.find(arg => arg.startsWith('query=')), /fields\(first: 100\) \{ pageInfo \{ hasNextPage \}/);
  assert.ok(summary && typeof summary === 'object');
  const serialized = JSON.stringify(summary);
  assert.ok(!serialized.includes('fake-installation-token'));
  assert.ok(!serialized.includes('PRIVATE KEY'));
  assert.ok(!serialized.includes('/outside/repo/key.pem'));
  for (const endpoint of ['/app', '/app/installations/20202', '/installation/repositories', 'graphql']) assert.ok(calls.some(call => call.endpoint === endpoint), endpoint);
  for (const endpoint of ['/app', '/app/installations/20202']) {
    const call = calls.find(call => call.endpoint === endpoint);
    assert.equal(call.command, 'curl');
    assert.equal(call.args[0], '--disable');
    assert.equal(call.args[call.args.indexOf('--request') + 1], 'GET');
    assert.equal(call.options.env.GH_TOKEN, undefined);
    const jwt = call.options.input.match(/^Authorization: Bearer ([^\n]+)/)[1];
    assert.equal(jwt.split('.').length, 3, 'App metadata must use App JWT with Bearer scheme');
    assert.ok(!JSON.stringify(call.args).includes(jwt));
  }
  for (const endpoint of ['/installation/repositories', 'graphql']) {
    const call = calls.find(call => call.endpoint === endpoint);
    assert.equal(call.options.env.GH_TOKEN, 'fake-installation-token-1');
  }
});

test('preflight rejects mismatched identity, installation drift and missing project capabilities', () => {
  assert.equal(typeof provider.createGitHubAppClient, 'function', 'GitHub App provider must exist');
  for (const mutate of [
    f => { f['/app'].id = 1; },
    f => { f['/app'].owner.login = 'other-org'; },
    f => { f['/app'].permissions.contents = 'write'; },
    f => { f['/app'].events = ['projects_v2_item']; },
    f => { f['/app/installations/20202'].app_id = 1; },
    f => { f['/app/installations/20202'].account.login = 'other-org'; },
    f => { f['/app/installations/20202'].target_type = 'User'; },
    f => { f['/app/installations/20202'].repository_selection = 'all'; },
    f => { f['/app/installations/20202'].suspended_at = '2026-09-07T00:00:00Z'; },
    f => { f['/app/installations/20202'].permissions.issues = 'write'; },
    f => { f['/app/installations/20202'].events = ['issue_comment']; },
    f => { f['/installation/repositories'].repositories[0].full_name = 'ExampleOrg/other'; },
    f => { f['/installation/repositories'].total_count = 2; f['/installation/repositories'].repositories.push({ full_name: 'ExampleOrg/other' }); },
    f => { f.graphql.data.viewer.login = 'human-user'; },
    f => { f.graphql.data.organization.projectV2.viewerCanUpdate = false; },
    f => { f.graphql.data.organization.projectV2.fields.nodes[0].options.splice(2, 1); },
    f => { f.graphql.data.repository = null; },
    f => { f.graphql.errors = [{ message: 'FAKE-SECRET-GRAPHQL-ERROR' }]; },
  ]) {
    const fixtures = preflightFixture(); mutate(fixtures);
    const { client } = harness({ response: ({ endpoint }) => fixtures[endpoint] });
    assert.throws(() => client.preflight(), error => {
      assert.ok(!String(error).includes('FAKE-SECRET-GRAPHQL-ERROR'));
      return true;
    }, mutate.toString());
  }
});

test('rejects unsafe private-key permissions, non-files and other owners before reading key', () => {
  for (const unsafe of [
    { mode: 0o100644, uid: process.getuid(), isFile: () => true },
    { mode: 0o100620, uid: process.getuid(), isFile: () => true },
    { mode: 0o040700, uid: process.getuid(), isFile: () => false },
    { mode: 0o100600, uid: process.getuid() + 1, isFile: () => true },
  ]) {
    let read = false;
    assert.throws(() => harness({ keyStat: () => unsafe, readKey: () => { read = true; return pem; } }));
    assert.equal(read, false, 'unsafe files must be rejected before any key read');
  }
});

test('rejects installation tokens with a lifetime exceeding one hour plus clock tolerance', () => {
  const { client, calls } = harness({ response: () => ({ token: 'fake-overlong-token', expires_at: new Date(initialTime + 3661000).toISOString(), permissions }) });
  assert.throws(() => client.gh(['api', '/installation/repositories']));
  assert.equal(calls.length, 1, 'overlong token must not authenticate a protected call');
});

test('sanitizes malformed JSON and GraphQL errors from mint and protected API responses', () => {
  const secret = 'FAKE-RAW-RESPONSE-SECRET';
  for (const body of [`invalid json ${secret}`, { errors: [{ message: secret, extensions: { token: secret } }] }]) {
    for (const phase of ['mint', 'protected']) {
      const { client, calls } = harness({ response: ({ endpoint }) => {
        const mint = endpoint === '/app/installations/20202/access_tokens';
        if ((phase === 'mint') === mint) return body;
      } });
      assert.throws(() => client.gh(['api', 'graphql', '-f', 'query={viewer{login}}']), error => {
        assert.ok(!String(error).includes(secret));
        assert.ok(!JSON.stringify(error).includes(secret));
        assert.equal(error.cause, undefined);
        assert.equal(error.stderr, undefined);
        assert.equal(error.stdout, undefined);
        return true;
      });
      assert.equal(calls.length, phase === 'mint' ? 1 : 2);
    }
  }
});


test('rejects owner-executable key files despite no group or other access', () => {
  assert.throws(() => harness({ keyStat: () => ({ mode: 0o100700, uid: process.getuid(), isFile: () => true }) }));
});

test('App-authenticated startup reconciles exact Producer result and waits for VERIFY event before VERIFIER launch', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'b-disp-app-integration-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const statePath = join(directory, 'state.json');
  const repository = 'ExampleOrg/sample-project';
  const invocationId = 'ExampleOrg/sample-project#302:PRODUCER:synthetic-completed-invocation';
  const lane = `${repository}#302:PRODUCER`;
  const item = { repository, issue: 302, itemId: 'PVTI_302', status: 'IMPLEMENT' };
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { [lane]: { invocationId, item, role: 'PRODUCER', startedAt: '2026-09-08T00:00:00.000Z', pid: 987654 } } }));
  let status = 'IMPLEMENT';
  const mutations = [];
  const { client, calls } = harness({ response: ({ command, args, endpoint }) => {
    if (command === 'curl') return undefined;
    if (endpoint === 'repos/ExampleOrg/sample-project/issues/302/comments') return [[
      { id: 100, body: '<!-- B-DISP: INVOCATION=older-invocation RESULT=VERIFY -->', user: { login: 'producer-bot' }, created_at: '2026-09-08T00:00:30.000Z' },
      { id: 101, body: `<!-- B-DISP: INVOCATION=${invocationId} RESULT=VERIFY -->`, user: { login: 'producer-bot' }, created_at: '2026-09-08T00:01:00.000Z' },
    ]];
    assert.equal(endpoint, 'graphql');
    const query = args.find(arg => arg.startsWith('query='));
    if (query.includes('updateProjectV2ItemFieldValue')) {
      assert.ok(args.includes('projectId=PVT_project'));
      assert.ok(args.includes('itemId=PVTI_302'));
      assert.ok(args.includes('fieldId=STATUS_FIELD'));
      assert.ok(args.includes('optionId=VERIFY_OPTION'));
      status = 'VERIFY'; mutations.push(status);
      return { data: { updateProjectV2ItemFieldValue: { projectV2Item: { id: 'PVTI_302' } } } };
    }
    if (query.includes('projectItems(')) {
      const issue = { number: 302, repository: { nameWithOwner: repository }, projectItems: { pageInfo: { hasNextPage: false }, nodes: [{ id: 'PVTI_302', databaseId: 900001, project: { number: 1, owner: { login: 'ExampleOrg' } } }] } };
      return { data: query.includes('node(id:') ? { node: issue } : { repository: { issue } } };
    }
    if (query.includes('items(first:')) return { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: false }, nodes: [{ id: 'PVTI_302', content: { __typename: 'Issue', number: 302, repository: { nameWithOwner: repository } }, fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: status, field: { name: 'Status' } }] } }] } } } } };
    if (query.includes('fields(first:')) return { data: { organization: { projectV2: { id: 'PVT_project', fields: { pageInfo: { hasNextPage: false }, nodes: [{ id: 'STATUS_FIELD', name: 'Status', options: [{ id: 'VERIFY_OPTION', name: 'VERIFY' }] }] } } } } };
    if (query.includes('fieldValueByName')) return { data: { node: { id: 'PVTI_302',
      project: { number: 1, owner: { login: 'ExampleOrg' } },
      content: { __typename: 'Issue', number: 302, repository: { nameWithOwner: repository } }, fieldValueByName: { name: status } } } };
    if (query.includes('node(id:')) {
      assert.ok(args.includes('id=I_302'));
      return { data: { node: { number: 302, repository: { nameWithOwner: repository } } } };
    }
    throw new Error('unexpected GraphQL operation in integration fixture');
  } });
  const authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, gh: client.gh, owner: 'ExampleOrg', projectNumber: 1, repository });
  const launches = [], preflights = [];
  const child = new EventEmitter();
  child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); child.pid = 987655; child.exitCode = null;
  const relay = new EventRelay({ statePath, repository, projectOwner: 'ExampleOrg', executionEnabled: true, authority,
    isProcessAlive: pid => {
      assert.equal(pid, 987654);
      assert.deepEqual(mutations, ['VERIFY'], 'durable completion must be routed before worker liveness');
      return false; // Main releases a completed claim only after confirming its child exited.
    },
    preflight: async request => { preflights.push(request); return { ok: true }; },
    launch: request => { launches.push(request); return child; },
  });
  t.after(() => relay.stop());
  await relay.startupReconcile();
  assert.deepEqual(mutations, ['VERIFY']);
  assert.equal(relay.state().active[lane], undefined);
  assert.deepEqual(launches, [], 'startup transition must not directly launch either worker');
  assert.deepEqual(preflights, []);
  assert.equal(relay.events.at(-1).outcome, 'VERIFY_TO_VERIFY');
  assert.equal(relay.events.at(-1).invocationId, invocationId);
  const event = { headers: { 'x-github-event': 'projects_v2_item', 'x-github-delivery': 'synthetic-verify-delivery' }, payload: { action: 'edited', organization: { login: 'ExampleOrg' }, projects_v2_item: { id: 900001, node_id: 'PVTI_302', content_node_id: 'I_302' }, changes: { field_value: { field_name: 'Status', to: 'VERIFY' } } } };
  assert.deepEqual(await relay.acceptEvent(event), { accepted: true });
  assert.deepEqual(launches.map(request => request.role), ['VERIFIER']);
  assert.deepEqual(preflights.map(request => request.role), ['VERIFIER']);
  assert.equal(launches[0].item.itemId, 'PVTI_302');
  assert.equal(launches[0].item.issue, 302);
  assert.equal(launches[0].item.repository, repository);
  assert.ok(launches[0].bootstrap.includes(`INVOCATION=${launches[0].invocationId} RESULT=ACCEPT`));
  assert.equal(relay.state().active[`${repository}#302:VERIFIER`].pid, 987655);
  assert.deepEqual(await relay.acceptEvent(event), { accepted: true, duplicate: true });
  assert.equal(launches.length, 1);
  const protectedCalls = calls.filter(call => call.command === 'gh');
  assert.ok(protectedCalls.length >= 5);
  for (const call of protectedCalls) {
    assert.equal(call.options.env.GH_TOKEN, 'fake-installation-token-1');
    assert.ok(!JSON.stringify(call.args).includes('fake-installation-token-1'));
    assert.equal(call.options.input, undefined, 'App JWT headers must not enter installation-token calls');
  }
  assert.equal(calls.filter(call => call.command === 'curl').length, 1, 'one cached installation token serves startup and event');
  const persisted = readFileSync(statePath, 'utf8');
  assert.ok(!persisted.includes('fake-installation-token'));
  assert.ok(!persisted.includes('PRIVATE KEY'));
});

test('rejects endpoints and gh options outside the bounded authority before minting credentials', () => {
  for (const args of [
    ['api', 'https://outside.invalid/capture'],
    ['api', '//outside.invalid/capture'],
    ['api', '/installation/token', '--method', 'DELETE'],
    ['api', '/repos/Other/repository/issues/302/comments'],
    ['api', '/repos/ExampleOrg/sample-project/issues/../../outside'],
    ['api', 'graphql', '--hostname', 'outside.invalid'],
    ['api', 'graphql', '--header', 'Authorization: fake-override'],
    ['api', 'graphql', '--input', '/private/file'],
    ['api', 'graphql', '--cache', '1h'],
    ['api', 'graphql', '-F', 'query=@/private/file'],
    ['api', '/installation/repositories', '-f', 'unexpected=write'],
    ['api', 'graphql', '-f'],
  ]) {
    const { client, calls } = harness();
    assert.throws(() => client.gh(args));
    assert.equal(calls.length, 0, 'reject before issuing a JWT or installation token');
  }
});

test('normalizes multiple gh comment pages so durable results beyond page one are reachable', () => {
  const marker = '<!-- B-DISP: INVOCATION=bounded-invocation RESULT=VERIFY -->';
  const { client, calls } = harness({ response: call => {
    if (call.args[1] === 'repos/ExampleOrg/sample-project/issues/302/comments') {
      const pages = [Array.from({ length: 30 }, (_, index) => ({ id: index, body: 'ordinary comment', created_at: '2026-09-08T00:01:00Z', user: { login: 'someone' } })),
        [{ id: 31, body: marker, created_at: '2026-09-08T00:02:00Z', user: { login: 'producer-bot' } }]];
      return call.args.includes('--slurp') ? pages : pages.map(page => JSON.stringify(page)).join('\n');
    }
  } });
  const authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, gh: client.gh, owner: 'ExampleOrg', projectNumber: 1, repository: 'ExampleOrg/sample-project' });
  assert.equal(authority.durableResult({ role: 'PRODUCER', item: { repository: 'ExampleOrg/sample-project', issue: 302 }, startedAt: '2026-09-08T00:00:00Z', invocationId: 'bounded-invocation' }), 'VERIFY');
  assert.ok(calls[1].args.includes('--slurp'));
});

for (const [label, failure, expected] of [
  ['HTTP permissions', { status: 1, stderr: 'gh: Resource not accessible by integration (HTTP 403)' }, ['category=HTTP', 'http_status=403']],
  ['HTTP quota', { status: 1, stderr: 'gh: API rate limit exceeded (HTTP 429)\nx-ratelimit-remaining: 0\nx-ratelimit-reset: 1790000000\nretry-after: 60' }, ['category=RATE_LIMIT', 'http_status=429', 'rate_remaining=0', 'rate_reset=1790000000', 'retry_after=60']],
  ['curl HTTP', { status: 22, stderr: 'curl: (22) The requested URL returned error: 401' }, ['category=HTTP', 'http_status=401', 'exit_status=22']],
  ['network timeout', { code: 'ETIMEDOUT', status: null, stderr: '' }, ['category=NETWORK', 'code=ETIMEDOUT']],
  ['DNS', { status: 1, stderr: 'dial tcp: lookup api.github.com: no such host' }, ['category=NETWORK', 'code=DNS']],
  ['GraphQL quota on nonzero exit', { status: 1, stdout: JSON.stringify({ errors: [{ type: 'RATE_LIMITED', message: 'private response' }] }) }, ['category=RATE_LIMIT', 'graphql=RATE_LIMITED']],
]) test(`App transport preserves sanitized ${label} evidence`, () => {
  const { client } = harness({ response: ({ command }) => {
    if (command === 'gh') throw Object.assign(new Error('raw private command'), failure);
  } });
  assert.throws(() => client.gh(['api', 'graphql', '-f', 'query={viewer{login}}']), error => {
    assert.match(error.message, /App control-plane API request failed/);
    for (const part of expected) assert.ok(error.message.includes(part), error.message);
    assert.equal(error.cause, undefined); assert.equal(error.stdout, undefined); assert.equal(error.stderr, undefined);
    assert.doesNotMatch(error.message, /raw private command|private response/);
    return true;
  });
});

test('GraphQL successful-exit rejection retains classification and malformed JSON stays distinct', () => {
  for (const [response, expected] of [
    [{ errors: [{ type: 'FORBIDDEN', message: 'secret' }] }, ['category=GRAPHQL', 'graphql=FORBIDDEN']],
    [{ errors: [{ extensions: { code: 'UNAUTHENTICATED' }, message: 'secret' }] }, ['category=GRAPHQL', 'graphql=UNAUTHENTICATED']],
    ['not JSON secret', ['category=INVALID_JSON']],
  ]) {
    const { client } = harness({ response: ({ command }) => command === 'gh' ? response : undefined });
    assert.throws(() => client.gh(['api', 'graphql']), error => {
      for (const part of expected) assert.ok(error.message.includes(part), error.message);
      assert.doesNotMatch(error.message, /secret/);
      return true;
    });
  }
});

test('diagnostic projection never exposes credential-bearing errors or unknown classifications', () => {
  for (const phase of ['mint', 'protected']) {
    let secrets;
    const { client } = harness({ response: ({ command, options }) => {
      if ((phase === 'mint') !== (command === 'curl')) return undefined;
      secrets = ['ghp_FAKESECRET', 'ghs_FAKEINSTALLATION', options.env.GH_TOKEN, options.input, pem.toString(), 'opaque-secret-value'].filter(Boolean);
      const raw = secrets.join('\n');
      throw Object.assign(new Error(raw), { status: 1, code: raw, stderr: raw,
        stdout: JSON.stringify({ errors: [{ type: raw, message: raw, extensions: { code: raw } }], token: raw }),
        cause: new Error(raw), headers: { Authorization: raw, 'x-ratelimit-remaining': raw } });
    } });
    assert.throws(() => client.gh(['api', 'graphql']), error => {
      for (const secret of secrets) {
        assert.ok(!String(error).includes(secret));
        assert.ok(!JSON.stringify(error).includes(secret));
        assert.ok(!error.stack.includes(secret));
      }
      assert.match(error.message, /category=GRAPHQL/);
      assert.equal(error.cause, undefined); assert.equal(error.stdout, undefined); assert.equal(error.stderr, undefined);
      return true;
    });
  }
});


test('App failure diagnostics remain sanitized in relay state and event logs and block successor work', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'b-disp-diagnostic-integration-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const statePath = join(directory, 'state.json');
  const item = { repository: 'ExampleOrg/sample-project', issue: 16, itemId: 'synthetic-item' };
  const lane = `${item.repository}#16:PRODUCER`;
  const invocationId = `${lane}:synthetic-failure`;
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {}, diagnostics: {
    [lane]: { item, role: 'PRODUCER', invocationId, startedAt: '2026-09-01T00:00:00Z', outcome: 'COMPLETION_ERROR' },
  } }));
  const { client } = harness({ response: ({ command, options }) => {
    if (command === 'gh') throw Object.assign(new Error(options.env.GH_TOKEN), {
      stderr: `gh: API rate limit exceeded (HTTP 429)\nAuthorization: Bearer ${options.env.GH_TOKEN}\n${pem}`,
      status: 1,
    });
  } });
  const authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, gh: client.gh, repository: item.repository });
  let launches = 0;
  const logged = [];
  const relay = new EventRelay({ statePath, authority, repository: item.repository, executionEnabled: true,
    launch: () => { launches++; throw new Error('unexpected worker launch'); },
    preflight: async () => ({ ok: true }), onEvent: event => logged.push(event) });
  t.after(() => relay.stop());
  await relay.start(item, 'PRODUCER', 'IMPLEMENT');
  assert.equal(launches, 0);
  const persisted = readFileSync(statePath, 'utf8');
  for (const output of [persisted, JSON.stringify(logged)]) {
    assert.match(output, /category=RATE_LIMIT/);
    assert.match(output, /http_status=429/);
    assert.doesNotMatch(output, /fake-installation-token|Authorization|PRIVATE KEY/);
  }
  assert.equal(relay.state().diagnostics[lane].invocationId, invocationId);
});


test('configured GitHub and curl executables and runtime PATH reach isolated transports', () => {
  const configuration = { ...config(), executables: { githubCli: '/opt/b-disp/bin/gh', curl: '/opt/b-disp/bin/curl' }, runtimePath: '/opt/b-disp/bin:/usr/bin:/bin' };
  const h = harness({ configuration });
  h.client.gh(['api', '/installation/repositories']);
  assert.deepEqual(h.calls.map(call => call.command), [configuration.executables.curl, configuration.executables.githubCli]);
  for (const call of h.calls) assert.equal(call.options.env.PATH, configuration.runtimePath);
});
