import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("future agents and new work packets reach the durable repository-state authority", () => {
  const instructions = read("AGENTS.md");
  const template = read("docs/templates/work-packet.md");
  for (const surface of [instructions, template]) {
    const path = surface.match(/(?:\.\.\/)*docs\/migration\/agent-packages\/GOVERNING_AGENT_DIRECTIVE\.md|(?:\.\.\/)*migration\/agent-packages\/GOVERNING_AGENT_DIRECTIVE\.md/);
    assert.ok(path, "active surface must link the canonical directive");
  }
  assert.match(read("docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md"), /KNOWN_AUTHORIZED/);
});

test("active operator admission distinguishes authorized changes from conflicting changes", () => {
  const guidance = read("docs/operations/forward-momentum.md");
  assert.match(guidance, /known.*authorized/i);
  assert.match(guidance, /conflict/i);
  assert.match(guidance, /baseline/i);
  assert.match(guidance, /exact path.*content/i);
  assert.match(guidance, /new or unexpected bytes/i);
});

test("repository-changing work has isolated, non-conflicting mutation ownership", () => {
  const contract = read("AGENTS.md").replace(/\s+/g, " ");
  assert.match(contract, /must not edit the shared main checkout directly/i);
  assert.match(contract, /isolated worktree or workspace/i);
  assert.match(contract, /one durable mutation owner, coordinated by the Factory Director/i);
  assert.match(contract, /Reviewers use read-only state or separate isolated state/i);
  assert.match(contract, /Conflicting ownership refuses mutation before any file change/i);
});
