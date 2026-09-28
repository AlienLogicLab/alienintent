import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const TOKEN = /^[a-zA-Z0-9][a-zA-Z0-9._:/-]*$/;
const PROVIDERS = new Set(['codex', 'claude']);

export function modelRoutingPath(environment = process.env) {
  return environment.ALIENINTENT_MODEL_ROUTING || join(environment.HOME || homedir(), '.config', 'alienintent', 'model-routing.json');
}

export function resolveRoute(role, { path = modelRoutingPath(), read = readFileSync } = {}) {
  const doc = JSON.parse(read(path, 'utf8'));
  const base = doc?.default;
  const override = doc?.roles?.[role] ?? {};
  if (doc?.schemaVersion !== 1 || !base || typeof base !== 'object' || typeof override !== 'object') throw new Error('MODEL_ROUTING_INVALID');
  const provider = override.provider ?? base.provider;
  const model = override.model ?? base.model;
  const providerConfig = doc?.providers?.[provider];
  if (!PROVIDERS.has(provider) || typeof model !== 'string' || !TOKEN.test(model) || !providerConfig) throw new Error('MODEL_ROUTING_INVALID');
  const executable = providerConfig.executable;
  const permissionMode = providerConfig.permissionMode;
  if (typeof executable !== 'string' || !executable.startsWith('/') || typeof permissionMode !== 'string' || !permissionMode) throw new Error('MODEL_ROUTING_INVALID');
  return { provider, model, executable, permissionMode };
}
