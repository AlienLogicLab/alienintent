"""The shared model-routing reader and the provider command builder (one copy for Python).

`resolve_route` reads `~/.config/alienintent/model-routing.json` (or `ALIENINTENT_MODEL_ROUTING`) on every call, with
no cache and no default; `provider_command` is the provider command line the Factory Director host and the registry
worker launch both use. Standard library only: the Director host installs this file as its standalone
`model_routing.py` and runs it with plain `python3`.
"""
from __future__ import annotations
import json, os, re
from pathlib import Path

_TOKEN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._:/-]*$')
_PROVIDERS = {'codex', 'claude'}
_PERMISSIONS = {'codex': {'read-only', 'workspace-write', 'danger-full-access'}, 'claude': {'manual', 'bypassPermissions'}}

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
    if not isinstance(executable, str) or not executable.startswith('/') or permission not in _PERMISSIONS[provider]:
        raise ValueError('MODEL_ROUTING_INVALID')
    return {'provider': provider, 'model': model, 'executable': executable, 'permissionMode': permission}

def provider_command(route: dict[str, str], workdir: Path | str) -> list[str]:
    """The provider's own command line for `route`; the prompt goes on standard input (codex `-`, claude none)."""
    if route["provider"] == "claude":
        return [route["executable"], "-p", "--no-session-persistence", "--output-format", "json",
                "--permission-mode", route["permissionMode"], "--model", route["model"]]
    return [route["executable"], "exec", "--ephemeral", "--json", "--sandbox", route["permissionMode"],
            "-C", str(workdir), "--model", route["model"], "-"]
