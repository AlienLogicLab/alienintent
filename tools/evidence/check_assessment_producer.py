#!/usr/bin/env python3
"""Readiness-assessment producer-identity checker.

Founder invariant (2026-09-22, Architecture Authority amendment (b)):

    A compatible output shape is not evidence that the authoritative capability produced the
    result.

Wave 1's readiness assessments were produced by a surrogate — coordinator-run Codex/Claude
prompts shaped to Agent Ready's contract — and their `provider_evidence` copied the words Agent
Ready generates host-side (`compatibility`, `capability_probe`). The release gate read only
`disposition`. Nothing asked who produced the artifact.

This checker makes producer identity a declared, checked fact. A provenance manifest
(`docs/evidence/wave1-readiness-assessment-provenance.json`) declares a producer for every
retained assessment; each declaration is tested against what a native Agent Ready result
actually looks like:

- an MCP envelope (`content` / `structuredContent` / `isError`), or
- a CLI object with exactly the twelve contract fields, plus at most Agent Ready's own
  `provider_evidence`, and a disposition from `READY / CLARIFY / SPLIT / HOLD`.

Agent Ready's `provider_evidence` is host-measured and provider-generic (ARP-01). It has exactly
the keys `provider`, `version`, `compatibility`, `capability_probe`; `provider` is one Agent Ready
supports, declared once in `AGENT_READY_PROVIDER_VERSION_FORMATS` together with the version
format Agent Ready accepts from that provider's CLI; `version` matches *that* provider's format;
and (`compatibility`, `capability_probe`) is `SUPPORTED`/`REVIEWED_VERSION` or
`COMPATIBLE_UNVERIFIED`/`PASSED`. No provider is special-cased.

Anything carrying `invocation`, `adapter`, `model`, `provider_failover`, `permission_denials`
or similar, provider evidence Agent Ready does not emit, or a bootstrap-assessor disposition, was
not produced by Agent Ready, whatever it asserts about itself. The historical files are never
modified; the manifest sits beside them.

An entry may declare `partial_record: true` (PG-00's receipt excerpt; PG-18's incomplete retained
copy). A partial record cannot show the full shape, so it is held to native *provenance* only:
an Agent Ready disposition, Agent Ready's own `provider_evidence` under the same rule, and no
runner-asserted fields. The declaration must cite the documentation its producer claim rests on.

Usage: python3 tools/evidence/check_assessment_producer.py [manifest.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONTRACT_FIELDS = frozenset((
    "disposition", "governing_intent", "summary", "owner_clarifications",
    "implementation_unknowns", "independent_decision_centers",
    "semantic_split_recommendation", "verification_assessment", "expected_rework_locality",
    "material_risks", "next_action", "rationale"))
NATIVE_PROVIDER_EVIDENCE_KEYS = frozenset(("provider", "version", "compatibility",
                                           "capability_probe"))
AGENT_READY_DISPOSITIONS = ("READY", "CLARIFY", "SPLIT", "HOLD")
# The one declared source of Agent Ready's supported providers, each with the version format
# Agent Ready's adapter accepts from that provider's CLI (agent_ready/providers.py). The
# readiness adapter's PROVIDERS must name the same set; a test holds them together.
_SEMVER = r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?"
AGENT_READY_PROVIDER_VERSION_FORMATS = {
    "codex": re.compile(rf"codex-cli {_SEMVER}"),
    "claude": re.compile(rf"{_SEMVER} \(Claude Code\)"),
}
# (compatibility, capability_probe) pairs Agent Ready records for a provider it ran.
AGENT_READY_COMPATIBILITY_PAIRS = frozenset((("SUPPORTED", "REVIEWED_VERSION"),
                                             ("COMPATIBLE_UNVERIFIED", "PASSED")))

CHECKS = ("producer_declared", "declared_native_must_look_native",
          "declared_surrogate_must_not_look_native", "every_assessment_covered")

NATIVE_PRODUCERS = ("agent-ready-cli", "agent-ready-mcp")


def is_native_provider_evidence(pe) -> bool:
    """True when `pe` is exactly the provider evidence Agent Ready emits, for any provider it
    supports: the four keys, a declared provider, a version in that provider's own format, and a
    compatibility/probe pair Agent Ready records."""
    if not isinstance(pe, dict) or set(pe) != NATIVE_PROVIDER_EVIDENCE_KEYS:
        return False
    provider, version = pe.get("provider"), pe.get("version")
    version_format = AGENT_READY_PROVIDER_VERSION_FORMATS.get(provider) \
        if isinstance(provider, str) else None
    if version_format is None or not isinstance(version, str) \
            or not version_format.fullmatch(version):
        return False
    return (pe.get("compatibility"), pe.get("capability_probe")) in AGENT_READY_COMPATIBILITY_PAIRS


def looks_native_agent_ready(artifact: dict) -> bool:
    """True when the artifact has the shape only the Agent Ready product produces."""
    if not isinstance(artifact, dict):
        return False
    if {"content", "structuredContent", "isError"} <= set(artifact):
        inner = artifact.get("structuredContent")
        return artifact.get("isError") is False and looks_native_agent_ready(inner)
    keys = set(artifact) - {"record_kind"}  # PG-00's receipt carries one bookkeeping key
    extra = keys - CONTRACT_FIELDS
    if not CONTRACT_FIELDS <= keys:
        return False
    if extra and extra != {"provider_evidence"}:
        return False
    if artifact.get("disposition") not in AGENT_READY_DISPOSITIONS:
        return False
    pe = artifact.get("provider_evidence")
    if pe is not None and not is_native_provider_evidence(pe):
        return False
    return True


def native_provenance_only(artifact: dict) -> bool:
    """For a declared partial record (an excerpt): the part that remains must still be Agent
    Ready's — its own 4-key provider_evidence, an Agent Ready disposition, and no
    runner-asserted fields. The full contract shape is not required, because it is absent by
    declaration, not by substitution."""
    if not isinstance(artifact, dict):
        return False
    inner = artifact.get("structuredContent", artifact)
    if inner.get("disposition") not in AGENT_READY_DISPOSITIONS:
        return False
    if not is_native_provider_evidence(inner.get("provider_evidence")):
        return False
    return not (set(inner) - CONTRACT_FIELDS - {"provider_evidence", "record_kind"})


def check_manifest(manifest: dict, expected_paths=None) -> tuple[bool, list[str]]:
    failures: list[str] = []
    entries = manifest.get("entries", [])

    for e in entries:
        path = e.get("path", "<no path>")
        producer = e.get("producer")
        if not producer:
            failures.append(f"producer_declared: {path} declares no producer")
            continue
        artifact = e.get("artifact")
        if artifact is None:
            continue  # coverage-only entry; shape cannot be tested without the artifact
        native_shape = looks_native_agent_ready(artifact)
        if e.get("partial_record") is True:
            native_shape = native_provenance_only(artifact)
        # Any producer label that names Agent Ready is a native claim, whatever the flag says.
        declared_native = e.get("native_agent_ready") is True or producer in NATIVE_PRODUCERS \
            or str(producer).lower().startswith("agent-ready")
        if declared_native and not native_shape:
            failures.append(
                f"declared_native_must_look_native: {path} is declared produced by Agent Ready "
                f"({producer}) but does not have Agent Ready's shape — asserted provenance, "
                "foreign fields, provider evidence Agent Ready does not emit or a "
                "bootstrap-assessor disposition. A compatible output shape is not evidence; an "
                "incompatible one is disproof")
        if not declared_native and native_shape and producer != "UNKNOWN":
            failures.append(
                f"declared_surrogate_must_not_look_native: {path} is declared {producer!r} yet "
                "has exactly Agent Ready's native shape; either the declaration is wrong or a "
                "real Agent Ready execution is being hidden")

    if expected_paths is not None:
        covered = {e.get("path") for e in entries}
        for p in expected_paths:
            if p not in covered:
                failures.append(
                    f"every_assessment_covered: {p} is a retained assessment with no producer "
                    "declaration; an undeclared surrogate can sit beside declared ones")

    return (not failures), failures


def _discover(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.glob("docs/work-units/**/*.assessment*.json")) + \
        sorted(str(p.relative_to(root)) for p in root.glob("docs/work-units/**/*.receipt.json"))


def main(argv: list[str]) -> int:
    root = Path(".")
    path = Path(argv[0] if argv else "docs/evidence/wave1-readiness-assessment-provenance.json")
    manifest = json.loads(path.read_text())
    for e in manifest.get("entries", []):
        p = root / e["path"]
        if p.exists() and "artifact" not in e:
            e["artifact"] = json.loads(p.read_text())
    ok, failures = check_manifest(manifest, expected_paths=_discover(root))
    entries = manifest.get("entries", [])
    print(f"manifest  : {path}")
    print(f"entries   : {len(entries)} "
          f"({sum(1 for e in entries if e.get('native_agent_ready'))} native, "
          f"{sum(1 for e in entries if e.get('producer') == 'UNKNOWN')} unknown)")
    print(f"checks    : {', '.join(CHECKS)}")
    print(f"result    : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
