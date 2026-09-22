# Agent Ready interface documentation audit — CLI and MCP

Date: 2026-09-22. Auditor: AlienIntent resident bootstrap coordinator, as a prospective consumer.
Subject: `/mnt/d/Projects/agent-ready` at `d5b28f9` (branch `feat/v0.1`, package `0.1.0rc1`).
Goal, from the Founder: *a person or agent should understand how to consume Agent Ready through
either CLI or MCP without reading private source code.*

Method: read only public documentation (`README.md`, `PRIVACY.md`, `SECURITY.md`,
`CONTRIBUTING.md`, `docs/verification.md`, `docs/provider-security.md`, `docs/ready-rubric.md`,
`examples/`, `schemas/assessment.schema.json`, `prompts/readiness.md`), then verify each
documented claim against the installed tool (`agent-ready --help`, `agent-ready assess --help`,
`importlib.metadata`) and, where documentation was silent, against source — source reads are
recorded below as the *gap*, not as documentation.

Verdict scale: **documented** · **partially documented** · **missing** · **contradictory** ·
**stale**.

## CLI

| Question | Verdict | Where / evidence |
|---|---|---|
| How to install | documented | README "Install the release candidate": venv, `pip install .`, Python 3.10+, Windows note, "not on PyPI" stated. Verified: `.venv/bin/agent-ready` exists. |
| How to run an assessment | documented | README top: `agent-ready assess ./task.md --provider codex`. Verified: `assess --help` matches. |
| Accepted input forms | documented | One explicit UTF-8 file (≤ 400,000 bytes) or `OWNER/REPO#123` via authenticated `gh`; only title and body retrieved; assessment text ≤ 100,000 characters. Verified against `sources.py` limits. |
| Provider selection | documented | `--provider codex|claude`, required. Exact supported versions and `SUPPORTED / COMPATIBLE_UNVERIFIED / INCOMPATIBLE` semantics in README and `docs/provider-security.md`. |
| JSON output mode | documented | `--json` prints the complete public contract; human output "highlights disposition and next action, then includes every field". |
| Disposition meaning | documented | README bullets + `docs/ready-rubric.md` + four synthetic examples. |
| Exit behaviour | documented | "Successful assessments exit 0 for all four dispositions. Errors exit 1 with no assessment on stdout; command usage errors exit 2." Verified: missing subcommand → argparse exit 2. |
| Error behaviour | partially documented | Exit codes and "no assessment on stdout" are stated; that errors are **sanitized** (no provider log or task text echoed) is in PRIVACY/SECURITY but not in the CLI section; the stderr format `agent-ready: <message>` is undocumented (source: `cli.py`). |
| Schema / version information | **missing** | No `--version` flag exists (verified: `agent-ready --version` is rejected). No schema version identifier exists in the contract. The only version identity is the package version (`0.1.0rc1`, via `pip`/`importlib.metadata`). A consumer retaining assessments has nothing on the CLI surface to record. |
| Examples | documented | `examples/README.md` plus four `.md`/`.json` pairs, explicitly synthetic and curated. |
| Security / privacy implications | documented | PRIVACY.md and SECURITY.md are precise: text goes to the selected provider CLI; no backend; isolated provider subprocess controls; what is and is not protected. |

**CLI verdict: documented, with two gaps.** A fresh user can install, run, choose a provider,
read JSON and interpret every disposition from the README alone. What they cannot do is discover
the tool's version or the contract's version from the CLI, and the stderr error format is
unstated. Neither is contradictory or stale.

## MCP

| Question | Verdict | Where / evidence |
|---|---|---|
| How to launch / configure the local server | documented | README "Local MCP": `agent-ready-mcp` as a host-managed stdio subprocess; absolute-path examples. |
| Transport type | documented | stdio; "no HTTP listener or remote transport". Verified: `mcp_server.py` uses `stdio_server`. |
| Exposed tool name(s) | documented | Exactly `assess_work_unit`; "no resources or prompts" (SECURITY.md). Verified. |
| Input contract | documented (was partially) | `{"text","provider"}`; extra keys rejected; path-like text is only text. The 100,000-character limit was stated only in the CLI section; **corrected in this audit** with one README sentence in the MCP section (verified against `INPUT_SCHEMA.maxLength = MAX_TEXT_CHARS`). |
| Output contract | documented | Same validated JSON in `structuredContent` plus a JSON text block; failures `isError: true` with no assessment. Verified. |
| Provider selection | documented | `provider` enum `codex|claude`; Codex results carry host-measured `provider_evidence`. |
| Capability / security limits | documented | SECURITY.md capability boundary: no paths, shell, env queries, provider config objects, resources or prompts; recursion prevented. |
| What MCP cannot do | documented | README and SECURITY.md: no file loading, GitHub access, repository modification, environment enumeration, execution handoff. |
| Example host configuration | documented | Claude Desktop / `mcpServers`, VS Code `.vscode/mcp.json`, Codex `config.toml`; Windows path note; restart-host note. |
| Version / schema behaviour | **partially documented** | "Existing assessment fields and dispositions are unchanged" and "the public schema accepts the new optional evidence field without making old saved assessments invalid" (provider-security.md) describe compatibility intent. There is no version or schema identifier in the tool result, and no documented way for a host to learn the server version. Same gap as the CLI. |
| Failure behaviour | documented | `isError: true`, generic sanitized message; "Check provider installation, supported version and authentication locally." |

**MCP verdict: documented, with one gap.** A host operator can configure, enumerate and call the
tool from the README alone. The gap is version/schema identity in the result.

## Contradictions and staleness checked

- README "Codex CLI 0.153.4 SUPPORTED; other versions COMPATIBLE_UNVERIFIED after probe" vs
  provider-security.md "0.154.0 passed the probe but is intentionally COMPATIBLE_UNVERIFIED":
  **consistent**, not contradictory.
- Claude pinned to exactly Claude Code 2.1.258 (README, SECURITY, provider-security): consistent
  across all three. Consequence for any consumer: a different installed Claude Code version fails
  closed before content is sent. This is a documented constraint, not a documentation defect.
- `provider_evidence` is emitted for Codex only and its schema rejects `provider: "claude"`:
  documented in README ("Successful Codex results include…") and provider-security.md. A
  consumer needing Claude provenance must record provider/model itself. Documented gap, not a
  contradiction.
- Spec §7 says CLI "may read only the explicitly supplied input file"; README matches. Spec §8
  MCP prohibitions match SECURITY.md. No staleness found between spec, README and code on the
  public surface.

## Corrections made in this audit

One, bounded and authority-preserving: the README MCP section now states the 100,000-character
`text` limit, which the code enforces and the CLI section already documented. No implementation
was changed.

## Follow-up recommendations (owner: Agent Ready maintainers)

1. **Expose version identity on both surfaces** — `agent-ready --version` and a version field in
   the MCP server initialization or tool result; and/or a `schema_version` in
   `assessment.schema.json`. Consumers retaining assessments immutably need it; today they must
   capture the package version out-of-band. *Implementation change; not this task.*
2. **Document the stderr error format** (`agent-ready: <message>`, sanitized) in the README CLI
   section. *Documentation; small.*
3. **State the Claude provenance gap in one place** consumers will read (README MCP or CLI
   section): Claude results carry no `provider_evidence`. Currently inferable, not stated.
