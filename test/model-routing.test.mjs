import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveRoute } from '../src/config/model-routing.mjs';

const doc = model => ({ schemaVersion:1, default:{provider:'codex',model}, providers:{codex:{executable:'/bin/codex',permissionMode:'danger-full-access'},claude:{executable:'/bin/claude',permissionMode:'bypassPermissions'}}, roles:{} });

test('model routing is reread on every resolution', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'alienintent-model-routing-')), 'routing.json');
  writeFileSync(path, JSON.stringify(doc('model-a')));
  assert.equal(resolveRoute('DIRECTOR', { path }).model, 'model-a');
  writeFileSync(path, JSON.stringify(doc('model-b')));
  assert.equal(resolveRoute('DIRECTOR', { path }).model, 'model-b');
});
