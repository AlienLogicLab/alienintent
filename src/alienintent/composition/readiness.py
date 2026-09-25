"""Readiness producer binding and adapter, resolved at the composition boundary from the configured executable.

product_version comes from installed-distribution metadata found beside the configured executable or MCP server
command, via the distribution that declares that console script, so it is bound to the launched identity. Nothing
here imports or reads Agent Ready modules, and no probe or invocation runs: an unresolvable identity is UNKNOWN,
which blocks admission (C#/contracts/4/provenance_contract version_source). The CLI or MCP producer adapter is
constructed from that binding, so the executable launched is exactly the one whose identity was resolved.
"""
from importlib import metadata
import json
import os
from pathlib import Path
from typing import Mapping

from alienintent.execution_coordination.adapters.agent_ready_producer import (
    AgentReadyCliAssessment, AgentReadyMcpAssessment)
from alienintent.execution_coordination.domain.readiness import UNKNOWN, ProducerBinding
from alienintent.execution_coordination.ports.readiness import ReadinessAssessment

PRODUCERS = {"cli": AgentReadyCliAssessment, "mcp": AgentReadyMcpAssessment}
# Provider credentials Agent Ready reads from its own isolated provider configuration; an inherited API key would
# override that configuration (the same filter as tools/orchestration/readiness_assessment.py).
FILTERED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


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


def assessment_environment() -> dict[str, str]:
    return {name: value for name, value in os.environ.items() if name not in FILTERED_ENV}


def compose_producer(binding: ProducerBinding | None, provider: str | None,
                     environment: Mapping[str, str] | None = None,
                     timeout_s: float = 900) -> ReadinessAssessment | None:
    """The public-interface adapter for the bound executable, or None when nothing is bound or no provider is set.

    Construction is not admission: ReadinessAdmission still refuses an unestablished binding before any launch.
    """
    if binding is None or provider is None:
        return None
    if binding.transport not in PRODUCERS:
        raise ValueError(f"unsupported readiness transport {binding.transport!r}")
    return PRODUCERS[binding.transport](binding, provider,
                                        assessment_environment() if environment is None else environment, timeout_s)
