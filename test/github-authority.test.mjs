import assert from "node:assert/strict";
import test from "node:test";
import { GitHubAuthority } from "../src/github/authority.mjs";

for (const scope of ["items", "fieldValues", "fields"]) {
  for (const evidence of ["truncated", "missing metadata", "invalid nodes", "GraphQL errors"]) {
    test(`${scope} rejects ${evidence} before returning authority or mutating`, () => {
      const item = { id: "PVTI_1", content: { __typename: "Issue", number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" } },
        fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Implement", field: { name: "Status" } }] } };
      const project = { id: "PVT_1", items: { pageInfo: { hasNextPage: false }, nodes: [item] },
        fields: { pageInfo: { hasNextPage: false }, nodes: [{ id: "status", name: "Status", options: [{ id: "verify", name: "Verify" }] }] } };
      const connection = scope === "fieldValues" ? item.fieldValues : project[scope];
      if (evidence === "truncated") connection.pageInfo.hasNextPage = true;
      if (evidence === "missing metadata") delete connection.pageInfo;
      if (evidence === "invalid nodes") connection.nodes = null;
      const response = { data: { organization: { projectV2: project } } };
      if (evidence === "GraphQL errors") response.errors = [{ message: "partial authority" }];
      const calls = [];
      const { subject } = authority({ gh: args => { calls.push(args); return JSON.stringify(response); } });
      assert.throws(() => scope === "fields" ? subject.transition({ itemId: "PVTI_1" }, "VERIFY") : subject.listItems(), /unavailable or incomplete/);
      assert.equal(calls.length, 1, "no mutation may follow incomplete authority");
    });
  }
}

test("membership resolution rejects partial GraphQL responses despite complete metadata", () => {
  const issue = { number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" },
    projectItems: { pageInfo: { hasNextPage: false }, nodes: [{ id: "PVTI_1", project: { number: 1, owner: { login: "ExampleOrg" } } }] } };
  const { subject } = authority({ gh: () => JSON.stringify({ errors: [{ message: "partial authority" }], data: { node: issue, repository: { issue } } }) });
  assert.throws(() => subject.resolveItem({ repository: "ExampleOrg/sample-project", issue: 301, itemId: "PVTI_1" }), /unavailable or incomplete/);
  assert.throws(() => subject.enrichContentNode("I_301", "PVTI_1"), /unavailable or incomplete/);
});

function authority(overrides = {}) {
  const calls = [];
  const gh = (args) => {
    calls.push(args);
    if (args[1] === "list") return JSON.stringify({ projects: [{ number: 1, id: "PVT_1" }] });
    if (args[0] === "api" && args[1] === "graphql") return JSON.stringify({ data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: false }, nodes: [
      { id: "PVTI_1", content: { __typename: "Issue", number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" } }, fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Verify", field: { __typename: "ProjectV2SingleSelectField", name: "Status" } }] } },
      { id: "PVTI_2", content: { __typename: "PullRequest" }, fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Implement", field: { __typename: "ProjectV2SingleSelectField", name: "Status" } }] } },
      { id: "PVTI_3", content: { __typename: "Issue", number: 42, repository: { nameWithOwner: "elsewhere/repo" } }, fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Review", field: { __typename: "ProjectV2SingleSelectField", name: "Status" } }] } },
    ] } } } } });
    if (args[1] === "field-list") return JSON.stringify({ fields: [{ id: "PVTSSF_status", name: "Status", options: [{ id: "verify", name: "Verify" }, { id: "review", name: "Review" }] }] });
    return JSON.stringify({});
  };
  return { subject: new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, gh, owner: "ExampleOrg", projectNumber: 1, repository: "ExampleOrg/sample-project", ...overrides }), calls };
}


test("listItems paginates the complete Project before returning authority", () => {
  const calls = [];
  const item = (id, issue) => ({ id, content: { __typename: "Issue", number: issue, repository: { nameWithOwner: "ExampleOrg/sample-project" } },
    fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Implement", field: { name: "Status" } }] } });
  const pages = [
    { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: true, endCursor: "cursor-1" }, nodes: [item("PVTI_1", 301)] } } } } },
    { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: false, endCursor: null }, nodes: [item("PVTI_2", 302)] } } } } },
  ];
  const { subject } = authority({ gh: args => { calls.push(args); return JSON.stringify(pages.shift()); } });
  assert.deepEqual(subject.listItems().map(value => value.issue), [301, 302]);
  assert.equal(calls.length, 2);
  assert.equal(calls[0].some(arg => arg.startsWith("cursor=")), false);
  assert.ok(calls[1].includes("cursor=cursor-1"));
});

for (const failure of ["missing cursor", "repeated cursor", "duplicate item"]) {
  test(`listItems rejects ${failure} while paginating`, () => {
    const item = id => ({ id, content: { __typename: "Issue", number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" } },
      fieldValues: { pageInfo: { hasNextPage: false }, nodes: [{ name: "Implement", field: { name: "Status" } }] } });
    let pages;
    if (failure === "missing cursor") pages = [
      { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: true, endCursor: null }, nodes: [item("PVTI_1")] } } } } },
    ];
    else if (failure === "repeated cursor") pages = [
      { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: true, endCursor: "same" }, nodes: [item("PVTI_1")] } } } } },
      { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: true, endCursor: "same" }, nodes: [item("PVTI_2")] } } } } },
    ];
    else pages = [
      { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: true, endCursor: "next" }, nodes: [item("PVTI_1")] } } } } },
      { data: { organization: { projectV2: { items: { pageInfo: { hasNextPage: false, endCursor: null }, nodes: [item("PVTI_1")] } } } } },
    ];
    const { subject } = authority({ gh: () => JSON.stringify(pages.shift()) });
    assert.throws(() => subject.listItems(), /unavailable or incomplete/);
  });
}

test("maps organization Project V2 Issue items through GraphQL while preserving status and item ID", () => {
  const { subject, calls } = authority();
  assert.deepEqual(subject.listItems(), [{ repository: "ExampleOrg/sample-project", issue: 301, itemId: "PVTI_1", status: "VERIFY", dependencies: [], founderException: false }]);
  assert.equal(calls.length, 1);
  assert.equal((calls[0][3].match(/pageInfo \{ hasNextPage/g) ?? []).length, 2);
  assert.equal(calls[0][0], "api"); assert.equal(calls[0][1], "graphql");
  assert.equal(calls.some((args) => args[0] === "project" && args[1] === "item-list"), false);
  assert.match(calls[0].find((argument) => argument.startsWith("query=")), /organization\(login: \$owner\).*projectV2\(number: \$number\)/s);
});

test("enriches a webhook content node and validates its exact Project membership", () => {
  const calls = [];
  const subject = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, gh: (args) => { calls.push(args); return JSON.stringify({ data: {
    node: { number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" }, projectItems: { nodes: [{ id: "PVTI_301", databaseId: 301, project: { number: 1, owner: { login: "ExampleOrg" } } }], pageInfo: { hasNextPage: false } } },
    repository: { issue: { projectItems: { nodes: [{ id: "PVTI_301", databaseId: 301, project: { number: 1, owner: { login: "ExampleOrg" } } }], pageInfo: { hasNextPage: false } } } },
  } }); }, owner: "ExampleOrg", projectNumber: 1, repository: "ExampleOrg/sample-project" });
  assert.deepEqual(subject.enrichContentNode("I_301", 301), { repository: "ExampleOrg/sample-project", issue: 301, itemId: "PVTI_301" });
  assert.equal(calls.length, 1); assert.equal(calls[0][0], "api"); assert.equal(calls[0][1], "graphql");
});

test("reads back the current Project status for the exact Project item", () => {
  const calls = [];
  const { subject } = authority({ gh: args => { calls.push(args); return JSON.stringify({ data: { node: statusNode() } }); } });
  assert.equal(subject.currentStatus({ itemId: "PVTI_1", repository: "ExampleOrg/sample-project", issue: 301 }), "ACCEPT");
  assert.equal(calls.filter((args) => args[0] === "api" && args[1] === "graphql").length, 1);
});

test("transitions the exact Project item through GraphQL project and Status resolution", () => {
  const calls = [];
  const subject = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" },
    gh: (args) => {
      calls.push(args);
      const query = args.find((argument) => argument.startsWith("query=")) ?? "";
      if (query.includes("mutation")) return JSON.stringify({ data: { updateProjectV2ItemFieldValue: { projectV2Item: { id: "PVTI_1" } } } });
      return JSON.stringify({ data: { organization: { projectV2: { id: "PVT_1", fields: { pageInfo: { hasNextPage: false }, nodes: [
        { __typename: "ProjectV2SingleSelectField", id: "PVTSSF_status", name: "Status", options: [{ id: "verify", name: "Verify" }, { id: "review", name: "Review" }] },
      ] } } } } });
    },
    owner: "ExampleOrg", projectNumber: 1, repository: "ExampleOrg/sample-project",
  });
  subject.transition({ itemId: "PVTI_1" }, "review");
  assert.equal(calls.length, 2);
  assert.match(calls[0][3], /fields\(first: 100\) \{ pageInfo \{ hasNextPage \}/);
  assert.ok(calls.every((args) => args[0] === "api" && args[1] === "graphql"));
  assert.equal(calls.some((args) => args[0] === "project"), false);
  assert.match(calls[0].find((argument) => argument.startsWith("query=")), /organization\(login: \$owner\).*projectV2\(number: \$number\).*fields/s);
  assert.deepEqual(calls[1], ["api", "graphql", "-f", `query=${calls[1][3].slice(6)}`, "-F", "projectId=PVT_1", "-F", "itemId=PVTI_1", "-F", "fieldId=PVTSSF_status", "-F", "optionId=review"]);
  assert.match(calls[1][3], /updateProjectV2ItemFieldValue/);
});

test("fails closed when the configured organization Project is unavailable", () => {
  const { subject } = authority({ gh: () => JSON.stringify({ data: { organization: { projectV2: null } } }) });
  assert.throws(() => subject.transition({ itemId: "PVTI_1" }, "REVIEW"), /Project 1 not found/);
});

test("fails closed when the requested Status option is unavailable", () => {
  const { subject } = authority({ gh: () => JSON.stringify({ data: { organization: { projectV2: { id: "PVT_1", fields: { pageInfo: { hasNextPage: false }, nodes: [{ __typename: "ProjectV2SingleSelectField", id: "PVTSSF_status", name: "Status", options: [{ id: "verify", name: "Verify" }] }] } } } } }) });
  assert.throws(() => subject.transition({ itemId: "PVTI_1" }, "REVIEW"), /Project Status option REVIEW not found/);
});

test("accepts only an exact role-authored durable Issue marker after launch", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ body: "<!-- B-DISP: INVOCATION=current RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "verifier-bot" } }]) });
  assert.equal(subject.durableResult({ role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, startedAt: "2026-09-03T01:00:00Z", invocationId: "current" }), "REJECT");
});

test("rejects an unauthored or stale durable marker", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ body: "<!-- B-DISP: INVOCATION=current RESULT=ACCEPT -->", created_at: "2026-09-03T00:59:00Z", user: { login: "someone-else" } }]) });
  assert.equal(subject.durableResult({ role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, startedAt: "2026-09-03T01:00:00Z", invocationId: "current" }), null);
});

test("preserves wrong-author marker evidence as an identity mismatch", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ id: 77, body: "<!-- B-DISP: INVOCATION=current RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "operator-user" } }]) });
  assert.deepEqual(subject.durableResult({ role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, startedAt: "2026-09-03T01:00:00Z", invocationId: "current" }), {
    kind: "WORKER_IDENTITY_MISMATCH",
    evidence: { commentId: 77, author: "operator-user", marker: "REJECT", repository: "ExampleOrg/sample-project", issue: 301, role: "VERIFIER", expectedLogin: "verifier-bot", startedAt: "2026-09-03T01:00:00Z", invocationId: "current", timestamp: "2026-09-03T01:01:00Z" },
  });
});

test("accepts a Producer marker only from producer-bot", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ id: 78, body: "<!-- B-DISP: INVOCATION=current RESULT=VERIFY -->", created_at: "2026-09-03T01:01:00Z", user: { login: "producer-bot" } }]) });
  assert.equal(subject.durableResult({ role: "PRODUCER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, startedAt: "2026-09-03T01:00:00Z", invocationId: "current" }), "VERIFY");
});

test("rejects a marker value invalid for the worker role", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ id: 79, body: "<!-- B-DISP: INVOCATION=current RESULT=ACCEPT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "producer-bot" } }]) });
  assert.equal(subject.durableResult({ role: "PRODUCER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, startedAt: "2026-09-03T01:00:00Z", invocationId: "current" }), null);
});

test("new invocation correlation ignores historical legacy markers regardless of author", () => {
  const { subject } = authority({ gh: () => JSON.stringify([
    { id: 80, body: "<!-- B-DISP: RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "operator-user" } },
    { id: 81, body: "<!-- B-DISP: RESULT=ACCEPT -->", created_at: "2026-09-03T01:02:00Z", user: { login: "verifier-bot" } },
  ]) });
  assert.equal(subject.durableResult({
    role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 },
    startedAt: "2026-09-03T01:00:00Z", invocationId: "issue-301:generation-2",
  }), null);
});

test("accepts only a marker carrying the exact new invocation ID", () => {
  const { subject } = authority({ gh: () => JSON.stringify([
    { id: 82, body: "<!-- B-DISP: INVOCATION=issue-301:generation-1 RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "verifier-bot" } },
    { id: 83, body: "<!-- B-DISP: INVOCATION=issue-301:generation-2 RESULT=ACCEPT -->", created_at: "2026-09-03T01:02:00Z", user: { login: "verifier-bot" } },
  ]) });
  assert.equal(subject.durableResult({
    role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 },
    startedAt: "2026-09-03T01:00:00Z", invocationId: "issue-301:generation-2",
  }), "ACCEPT");
});

test("ignores a marker for a different invocation", () => {
  const { subject } = authority({ gh: () => JSON.stringify([
    { id: 84, body: "<!-- B-DISP: INVOCATION=issue-301:generation-1 RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "verifier-bot" } },
  ]) });
  assert.equal(subject.durableResult({
    role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 },
    startedAt: "2026-09-03T01:00:00Z", invocationId: "issue-301:generation-2",
  }), null);
});

test("classifies the exact invocation marker from the wrong author as an identity mismatch", () => {
  const { subject } = authority({ gh: () => JSON.stringify([
    { id: 85, body: "<!-- B-DISP: INVOCATION=issue-301:generation-2 RESULT=REJECT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "operator-user" } },
  ]) });
  assert.deepEqual(subject.durableResult({
    role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 },
    startedAt: "2026-09-03T01:00:00Z", invocationId: "issue-301:generation-2",
  }), {
    kind: "WORKER_IDENTITY_MISMATCH",
    evidence: {
      commentId: 85, author: "operator-user", marker: "REJECT", repository: "ExampleOrg/sample-project",
      issue: 301, role: "VERIFIER", expectedLogin: "verifier-bot", startedAt: "2026-09-03T01:00:00Z",
      invocationId: "issue-301:generation-2", timestamp: "2026-09-03T01:01:00Z",
    },
  });
});

test("a restarted authority instance preserves exact invocation correlation", () => {
  const gh = () => JSON.stringify([
    { id: 86, body: "<!-- B-DISP: INVOCATION=issue-301:generation-2 RESULT=ACCEPT -->", created_at: "2026-09-03T01:01:00Z", user: { login: "verifier-bot" } },
  ]);
  const first = authority({ gh }).subject;
  const restarted = authority({ gh }).subject;
  const query = {
    role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 },
    startedAt: "2026-09-03T01:00:00Z", invocationId: "issue-301:generation-2",
  };
  assert.equal(first.durableResult(query), "ACCEPT");
  assert.equal(restarted.durableResult(query), "ACCEPT");
});

test("durable reader rejects multiple markers and unavailable expected login", () => {
  const request = { role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, invocationId: "current", startedAt: "2026-09-03T01:00:00Z" };
  const comment = { body: "<!-- B-DISP: INVOCATION=current RESULT=ACCEPT -->", created_at: "2026-09-03T01:01:00Z", user: {} };
  const missing = authority({ workerLogins: {}, gh: () => JSON.stringify([comment]) }).subject;
  assert.notEqual(missing.durableResult(request), "ACCEPT");
  comment.user.login = "verifier-bot"; comment.body += "\n<!-- B-DISP: INVOCATION=current RESULT=REJECT -->";
  assert.equal(authority({ gh: () => JSON.stringify([comment]) }).subject.durableResult(request), null);
});

test("wrong-author comment cannot hide a later valid exact result", () => {
  const body = "<!-- B-DISP: INVOCATION=current RESULT=ACCEPT -->";
  const { subject } = authority({ gh: () => JSON.stringify([
    { body, created_at: "2026-09-03T01:01:00Z", user: { login: "wrong" } },
    { body, created_at: "2026-09-03T01:02:00Z", user: { login: "verifier-bot" } },
  ]) });
  assert.equal(subject.durableResult({ role: "VERIFIER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, invocationId: "current", startedAt: "2026-09-03T01:00:00Z" }), "ACCEPT");
});

test("ACCEPT selects Accept when both Review and Accept are Project options", () => {
  const calls = [];
  const { subject } = authority({ gh: (args) => {
    calls.push(args);
    return JSON.stringify({ data: { organization: { projectV2: { id: "project", fields: { pageInfo: { hasNextPage: false }, nodes: [{ id: "status", name: "Status", options: [{ id: "review-id", name: "Review" }, { id: "accept-id", name: "Accept" }] }] } } } } });
  } });
  subject.transition({ itemId: "PVTI_item" }, "ACCEPT");
  assert.ok(calls[1].includes("optionId=accept-id"));
  assert.ok(!calls[1].includes("optionId=review-id"));
});

test("exact result posted in the launch second respects GitHub timestamp precision", () => {
  const { subject } = authority({ gh: () => JSON.stringify([{ body: "<!-- B-DISP: INVOCATION=current RESULT=VERIFY -->", created_at: "2026-09-08T14:00:00Z", user: { login: "producer-bot" } }]) });
  assert.equal(subject.durableResult({ role: "PRODUCER", item: { repository: "ExampleOrg/sample-project", issue: 301 }, invocationId: "current", startedAt: "2026-09-08T14:00:00.800Z" }), "VERIFY");
});

test("resolves the Issue 302 database ID to its exact Project node ID", () => {
  const calls = [];
  const { subject } = authority({ gh: (args) => {
    calls.push(args);
    return JSON.stringify({ data: { repository: { issue: { projectItems: {
      nodes: [{ id: "PVTI_synthetic", databaseId: 900001, project: { number: 1, owner: { login: "ExampleOrg" } } }],
      pageInfo: { hasNextPage: false },
    } } } } });
  } });
  for (const itemId of [900001, "900001", "PVTI_synthetic"]) {
    assert.deepEqual(subject.resolveItem({ repository: "ExampleOrg/sample-project", issue: 302, itemId }), {
      repository: "ExampleOrg/sample-project", issue: 302, itemId: "PVTI_synthetic",
    });
  }
  assert.equal(calls.length, 3);
  assert.ok(calls.every(args => args.includes("issue=302") && args.includes("name=sample-project")));
  assert.ok(calls.every(args => !args.some(arg => arg.includes("organization(login:"))), "must not scan the Project");
});

test("Project item resolution fails closed for missing, mismatched, ambiguous or incomplete evidence", () => {
  const node = { id: "PVTI_302", databaseId: 900001, project: { number: 1, owner: { login: "ExampleOrg" } } };
  for (const projectItems of [
    null, { nodes: [], pageInfo: { hasNextPage: false } },
    { nodes: [node], pageInfo: { hasNextPage: true } },
    { nodes: [node] },
    { nodes: [node, node], pageInfo: { hasNextPage: false } },
    { nodes: [{ ...node, databaseId: 123 }], pageInfo: { hasNextPage: false } },
    { nodes: [{ ...node, project: { number: 2, owner: { login: "ExampleOrg" } } }], pageInfo: { hasNextPage: false } },
    { nodes: [{ ...node, project: { number: 1, owner: { login: "elsewhere" } } }], pageInfo: { hasNextPage: false } },
  ]) {
    const { subject } = authority({ gh: () => JSON.stringify({ data: { repository: { issue: { projectItems } } } }) });
    assert.throws(() => subject.resolveItem({ repository: "ExampleOrg/sample-project", issue: 302, itemId: 900001 }), /Project item/);
  }
});

test("numeric Project item IDs never reach the GraphQL mutation boundary", () => {
  const calls = [];
  const { subject } = authority({ gh: (args) => { calls.push(args); return "{}"; } });
  assert.throws(() => subject.transition({ itemId: 900001 }, "ACCEPT"), /Project item/);
  assert.equal(calls.length, 0);
});

function statusNode() {
  return { id: "PVTI_1", __typename: "ProjectV2Item", project: { number: 1, owner: { login: "ExampleOrg" } },
    content: { __typename: "Issue", number: 301, repository: { nameWithOwner: "ExampleOrg/sample-project" } },
    fieldValueByName: { __typename: "ProjectV2ItemFieldSingleSelectValue", name: "Accept" } };
}

const closureClaim = { role: "PRODUCER", status: "ACCEPT", item: { repository: "ExampleOrg/sample-project", issue: 301, status: "ACCEPT" }, invocationId: "closure-301", startedAt: "2026-09-03T01:00:00Z" };

test("closure accepts DONE and control handoff through durable authenticated comments", () => {
  for (const [marker, expected] of [["RESULT=DONE", "DONE"], ["CONTROL=RETURN_TO_IMPLEMENT", "RETURN_TO_IMPLEMENT"], ["RESULT=FOUNDER_EXCEPTION", "FOUNDER_EXCEPTION"]]) {
    const { subject } = authority({ gh: () => JSON.stringify([{ body: `<!-- B-DISP: INVOCATION=closure-301 ${marker} -->`, created_at: "2026-09-03T01:00:00Z", user: { login: "producer-bot" } }]) });
    assert.equal(subject.durableResult(closureClaim), expected);
  }
});

test("closure protocol rejects mixed, duplicate, stale invocation and wrong-kind markers", async () => {
  const api = await import("../src/github/authority.mjs");
  assert.equal(typeof api.parseInvocationSignal, "function");
  const done = "<!-- B-DISP: INVOCATION=closure-301 RESULT=DONE -->";
  const control = "<!-- B-DISP: INVOCATION=closure-301 CONTROL=RETURN_TO_IMPLEMENT -->";
  assert.equal(api.parseInvocationSignal(done, closureClaim), "DONE");
  assert.equal(api.parseInvocationSignal(control, closureClaim), "RETURN_TO_IMPLEMENT");
  for (const body of [done + control, done + done, control + control, done + "<!-- B-DISP: INVOCATION=old CONTROL=RETURN_TO_IMPLEMENT -->", "<!-- B-DISP: INVOCATION=closure-301 RESULT=RETURN_TO_IMPLEMENT -->", "<!-- B-DISP: INVOCATION=closure-301 CONTROL=DONE -->", "<!-- B-DISP: INVOCATION=old RESULT=DONE -->", "<!-- B-DISP: INVOCATION=closure-301 RESULT=VERIFY -->"]) assert.equal(api.parseInvocationSignal(body, closureClaim), null, body);
  for (const claim of [{ ...closureClaim, role: "VERIFIER" }, { ...closureClaim, status: "IMPLEMENT" }]) {
    assert.equal(api.parseInvocationSignal(control, claim), null);
    assert.equal(api.parseInvocationSignal(done, claim), null);
  }
  assert.deepEqual([...api.allowedSignals(closureClaim)], ["DONE", "FOUNDER_EXCEPTION", "RETURN_TO_IMPLEMENT"]);
  assert.deepEqual([...api.allowedSignals({ role: "VERIFIER" })], ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"]);
  assert.deepEqual([...api.allowedSignals({ role: "PRODUCER" })], ["VERIFY", "FOUNDER_EXCEPTION"]);
  assert.deepEqual([...api.allowedSignals({ role: "UNKNOWN" })], []);
});

test("closure durable signals preserve timestamp and author checks and fence repository", () => {
  let calls = 0;
  const comment = { id: 901, body: "<!-- B-DISP: INVOCATION=closure-301 CONTROL=RETURN_TO_IMPLEMENT -->", created_at: "2026-09-03T01:00:00Z", user: { login: "wrong-worker" } };
  const { subject } = authority({ gh: () => { calls++; return JSON.stringify([comment]); } });
  assert.equal(subject.durableResult(closureClaim)?.kind, "WORKER_IDENTITY_MISMATCH");
  comment.user.login = "producer-bot";
  comment.created_at = "2026-09-03T00:59:59Z";
  assert.equal(subject.durableResult(closureClaim), null);
  comment.created_at = "2026-09-03T01:00:00Z";
  assert.throws(() => subject.durableResult({ ...closureClaim, item: { ...closureClaim.item, repository: "elsewhere/repo" } }), /repository/);
  assert.equal(calls, 2);
});

test("currentStatus targets one node and fails closed on mismatched identity or missing status", () => {
  let node = statusNode();
  const calls = [];
  const { subject } = authority({ gh: args => { calls.push(args); return JSON.stringify({ data: { node } }); } });
  const item = { itemId: "PVTI_1", repository: "ExampleOrg/sample-project", issue: 301 };
  assert.equal(subject.currentStatus(item), "ACCEPT");
  assert.ok(calls[0].includes("id=PVTI_1"));
  assert.match(calls[0][3], /node\(id: \$id\)/);
  assert.doesNotMatch(calls[0][3], /items\(first/);
  for (const mutate of [n => { n.id = "PVTI_2"; }, n => { n.content.number = 42; }, n => { n.content.repository.nameWithOwner = "elsewhere/repo"; }, n => { n.content.__typename = "PullRequest"; }, n => { n.project.number = 2; }, n => { n.project.owner.login = "other"; }, n => { n.fieldValueByName = null; }, n => { n.fieldValueByName.name = ""; }]) {
    node = statusNode(); mutate(node);
    assert.throws(() => subject.currentStatus(item), /unavailable/);
  }
  const before = calls.length;
  assert.throws(() => subject.currentStatus({ ...item, repository: "elsewhere/repo" }), /repository/);
  assert.equal(calls.length, before);
});

test("persisted closure admission controls recovery even after Project status changes", async () => {
  const { parseInvocationSignal } = await import("../src/github/authority.mjs");
  const control = "<!-- B-DISP: INVOCATION=closure-301 CONTROL=RETURN_TO_IMPLEMENT -->";
  const done = "<!-- B-DISP: INVOCATION=closure-301 RESULT=DONE -->";
  assert.equal(parseInvocationSignal(control, { ...closureClaim, item: { ...closureClaim.item, status: "IMPLEMENT" } }), "RETURN_TO_IMPLEMENT");
  assert.equal(parseInvocationSignal(done, { ...closureClaim, item: { ...closureClaim.item, status: "DONE" } }), "DONE");
  assert.equal(parseInvocationSignal(done, { ...closureClaim, status: "IMPLEMENT" }), null);
});

test("optional durable evidence identifies the exact authenticated comment and its remote timestamp", () => {
  const comments = [
    { id: 910, body: "<!-- B-DISP: INVOCATION=old-closure RESULT=FOUNDER_EXCEPTION -->", created_at: "2026-09-03T01:00:00Z", user: { login: "producer-bot" } },
    { id: 911, body: "<!-- B-DISP: INVOCATION=closure-301 RESULT=FOUNDER_EXCEPTION -->", created_at: "2026-09-03T01:00:00Z", user: { login: "wrong-worker" } },
    { id: 912, body: "<!-- B-DISP: INVOCATION=closure-301 RESULT=FOUNDER_EXCEPTION -->", created_at: "2026-09-03T01:00:01Z", user: { login: "producer-bot" } },
  ];
  let reads = 0;
  const { subject } = authority({ gh: () => { reads++; return JSON.stringify(comments); } });
  const claim = { ...closureClaim, startedAt: "2026-09-03T01:00:00.800Z" };
  assert.deepEqual(subject.durableResult({ ...claim, includeEvidence: true }), {
    value: "FOUNDER_EXCEPTION", evidence: { commentId: 912, createdAt: "2026-09-03T01:00:01Z", author: "producer-bot" },
  });
  assert.equal(reads, 1);
  assert.equal(subject.durableResult(claim), "FOUNDER_EXCEPTION");
  assert.equal(subject.durableResult({ ...claim, includeEvidence: false }), "FOUNDER_EXCEPTION");
  comments[2].created_at = "2026-09-03T01:00:00Z";
  assert.deepEqual(subject.durableResult({ ...claim, includeEvidence: true }), {
    value: "FOUNDER_EXCEPTION", evidence: { commentId: 912, createdAt: "2026-09-03T01:00:00Z", author: "producer-bot" },
  });
  comments.pop();
  assert.deepEqual(subject.durableResult({ ...claim, includeEvidence: true }), subject.durableResult(claim));
  assert.equal(subject.durableResult({ ...claim, includeEvidence: true }).kind, "WORKER_IDENTITY_MISMATCH");
});


test("missing configured worker identities reject exact markers from any synthetic login", () => {
  for (const role of ["PRODUCER", "VERIFIER"]) {
    const result = role === "PRODUCER" ? "VERIFY" : "ACCEPT";
    const subject = new GitHubAuthority({ repository: "ExampleOrg/sample-project", gh: () => JSON.stringify([
      { body: `<!-- B-DISP: INVOCATION=exact RESULT=${result} -->`, created_at: "2030-01-01T00:00:01Z", user: { login: role === "PRODUCER" ? "producer-bot" : "verifier-bot" } },
    ]) });
    assert.equal(subject.durableResult({ role, invocationId: "exact", startedAt: "2030-01-01T00:00:00Z", item: { repository: "ExampleOrg/sample-project", issue: 701 } }), null);
  }
});
