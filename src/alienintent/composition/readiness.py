"""Readiness producer binding, resolved at the composition boundary from the configured executable.

product_version comes from installed-distribution metadata found beside the configured executable or MCP server
command, via the distribution that declares that console script, so it is bound to the launched identity. Nothing
here imports or reads Agent Ready modules, and no probe or invocation runs: an unresolvable identity is UNKNOWN,
which blocks admission (C#/contracts/4/provenance_contract version_source).
"""
from importlib import metadata
import json
from pathlib import Path

from alienintent.execution_coordination.domain.readiness import UNKNOWN, ProducerBinding


def resolve_binding(executable: Path | None, transport: str = "cli") -> ProducerBinding | None:
    if executable is None:
        return None
    executable = Path(executable)
    sites = [str(p) for p in sorted((executable.parent.parent / "lib").glob("python*/site-packages"))]
    for distribution in metadata.distributions(path=sites) if sites else ():
        scripts = {e.name for e in distribution.entry_points if e.group in ("console_scripts", "gui_scripts")}
        if executable.name not in scripts:
            continue
        name = (distribution.metadata["Name"] or UNKNOWN).lower().replace("_", "-")
        source = f"importlib.metadata:{getattr(distribution, '_path', 'unknown')}"
        return ProducerBinding(name, distribution.version or UNKNOWN, source, str(executable), transport,
                               _editable_revision(distribution))
    return ProducerBinding(UNKNOWN, UNKNOWN, "no installed distribution declares this executable",
                           str(executable), transport)


def _editable_revision(distribution: metadata.Distribution) -> str | None:
    """The editable checkout location (PEP 610 direct_url.json) when the distribution is an editable install."""
    try:
        info = json.loads(distribution.read_text("direct_url.json") or "{}")
    except ValueError:
        return None
    if not isinstance(info, dict) or not (info.get("dir_info") or {}).get("editable"):
        return None
    commit = (info.get("vcs_info") or {}).get("commit_id")
    return f"{info.get('url')}@{commit}" if commit else str(info.get("url"))
