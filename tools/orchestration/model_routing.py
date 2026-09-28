from __future__ import annotations
import json, os, re
from pathlib import Path

_TOKEN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._:/-]*$')
_PROVIDERS = {'codex', 'claude'}

def routing_path() -> Path:
    return Path(os.environ.get('ALIENINTENT_MODEL_ROUTING', Path.home() / '.config/alienintent/model-routing.json'))

def resolve_route(role: str, path: Path | str | None = None) -> dict[str, str]:
    doc = json.loads(Path(path or routing_path()).read_text())
    base = doc.get('default')
    override = (doc.get('roles') or {}).get(role, {})
    if doc.get('schemaVersion') != 1 or not isinstance(base, dict) or not isinstance(override, dict):
        raise ValueError('MODEL_ROUTING_INVALID')
    provider = override.get('provider', base.get('provider'))
    model = override.get('model', base.get('model'))
    cfg = (doc.get('providers') or {}).get(provider)
    if provider not in _PROVIDERS or not isinstance(model, str) or not _TOKEN.fullmatch(model) or not isinstance(cfg, dict):
        raise ValueError('MODEL_ROUTING_INVALID')
    executable, permission = cfg.get('executable'), cfg.get('permissionMode')
    if not isinstance(executable, str) or not executable.startswith('/') or not isinstance(permission, str) or not permission:
        raise ValueError('MODEL_ROUTING_INVALID')
    return {'provider': provider, 'model': model, 'executable': executable, 'permissionMode': permission}
