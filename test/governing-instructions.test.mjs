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
