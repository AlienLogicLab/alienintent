#!/usr/bin/env python3
"""Agent Ready CLI adapter in the shape of the `ReadinessAssessment` port — programme tooling.

Founder (2026-09-22): invoke Agent Ready only through its supported CLI or MCP, behind the
canonical `ReadinessAssessment` port; record producer identity / version / schema provenance
where available and preserve the limitation explicitly where it is not.

This is the post-Wave-1 programme's adapter, not the SF-REQ-015 product port (that is Wave 2
work). It exists so no programme step can produce a contract-shaped surrogate again. It:

- runs `agent-ready assess <file> --provider <p> --json` and nothing else — no prompt, no rubric,
  no schema of its own;
- preserves the raw result verbatim and records what produced it (executable, package version,
  editable checkout commit, invocation, exit code, input fingerprint, timestamp);
- treats every non-zero exit, unparsable output, or result without Agent Ready's shape as an
  EXECUTION_FAILURE that carries no disposition (SF-REQ-015: execution failure is not a
  disposition and never becomes READY);
- states what Agent Ready v0.1 does not expose — product/schema version on the result, the
  analysis model — as a recorded limitation (agent-ready issue #1), never as a guess.

Usage: python3 tools/orchestration/readiness_assessment.py --agent-ready <exe> --provider codex
           --work-unit-id WO-220101 <work-unit-file>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evidence"))
from check_assessment_producer import looks_native_agent_ready  # noqa: E402

AGENT_READY_DISPOSITIONS = ("READY", "CLARIFY", "SPLIT", "HOLD")
PROVIDERS = ("codex", "claude")
FILTERED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
RECORD_DIR = Path("docs/evidence/wave2-readiness-assessments")

# What Agent Ready v0.1 does not put on its results. Recorded, not inferred.
CONTRACT_VERSION_NOTE = ("bound to the package release; Agent Ready v0.1 results carry no schema "
                         "version identifier (sanookdu/agent-ready#1)")
MODEL_NOTE = "not exposed by Agent Ready v0.1 results; provider_evidence carries the CLI version only"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentReadyCliAdapter:
    def __init__(self, executable: str, runner=subprocess.run) -> None:
        self.executable = str(executable)
        self.runner = runner

    # -- provenance discovery ---------------------------------------------------------------

    def _package_identity(self, env) -> tuple[str, str]:
        """(version, editable checkout commit) of the installed package, or UNKNOWN."""
        python = Path(self.executable).with_name("python")
        version, commit = "UNKNOWN", "UNKNOWN"
        try:
            show = self.runner([str(python), "-m", "pip", "show", "agent-ready"], capture_output=True,
                               text=True, env=env, timeout=60)
        except (OSError, subprocess.SubprocessError):
            return version, commit
        if show.returncode != 0:
            return version, commit
        m = re.search(r"^Version:\s*(\S+)", show.stdout, re.M)
        version = m.group(1) if m else "UNKNOWN"
        loc = re.search(r"^Editable project location:\s*(.+)$", show.stdout, re.M)
        if loc:
            try:
                rev = self.runner(["git", "-C", loc.group(1).strip(), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, env=env, timeout=60)
                if rev.returncode == 0 and rev.stdout.strip():
                    commit = rev.stdout.strip()
            except (OSError, subprocess.SubprocessError):
                pass
        return version, commit

    # -- the port operation -----------------------------------------------------------------

    def assess(self, text: str, *, provider: str, work_unit_id: str, timeout_s: int = 900) -> dict:
        if provider not in PROVIDERS:
            raise ValueError(f"unsupported provider {provider!r}; Agent Ready v0.1 offers {PROVIDERS}")
        env = {k: v for k, v in os.environ.items() if k not in FILTERED_ENV}
        version, commit = self._package_identity(env)
        started = _now()
        with TemporaryDirectory(prefix="readiness-assessment-") as d:
            source = Path(d) / f"{work_unit_id}.md"
            source.write_text(text, encoding="utf-8")
            argv = [self.executable, "assess", str(source), "--provider", provider, "--json"]
            try:
                proc = self.runner(argv, capture_output=True, text=True, env=env, timeout=timeout_s)
                exit_code, stdout, stderr = proc.returncode, proc.stdout or "", proc.stderr or ""
            except subprocess.TimeoutExpired:
                exit_code, stdout, stderr = None, "", f"timeout after {timeout_s}s"
            except OSError as exc:
                exit_code, stdout, stderr = None, "", f"launch failed: {exc}"
        provenance = {
            "producer": "agent-ready-cli",
            "native_agent_ready": True,
            "executable": self.executable,
            "agent_ready_version": version,
            "agent_ready_checkout_commit": commit,
            "contract_version": f"{version}; {CONTRACT_VERSION_NOTE}",
            "provider": provider,
            "provider_evidence": None,
            "model": MODEL_NOTE,
            "input_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "input_chars": len(text),
            "invocation": argv,
            "exit_code": exit_code,
            "timeout_s": timeout_s,
            "started_at": started,
            "ended_at": _now(),
        }
        record = {"record_kind": "ReadinessAssessment", "schema_version": "1",
                  "work_unit_id": work_unit_id, "provenance": provenance}

        failure = None
        assessment = None
        if exit_code != 0:
            failure = {"class": "PROVIDER_OR_PRODUCT_FAILURE", "stderr": stderr[-2000:]}
        else:
            try:
                assessment = json.loads(stdout)
            except ValueError:
                failure = {"class": "MALFORMED_OUTPUT", "stderr": stderr[-2000:],
                           "stdout_head": stdout[:500]}
            else:
                if not looks_native_agent_ready(assessment) or \
                        assessment.get("disposition") not in AGENT_READY_DISPOSITIONS:
                    failure = {"class": "NOT_AGENT_READY_SHAPE", "stderr": stderr[-2000:],
                               "keys": sorted(assessment) if isinstance(assessment, dict) else None}
                    assessment = None
        if failure is not None:
            record["outcome"] = "EXECUTION_FAILURE"
            record["failure"] = failure
            return record
        record["outcome"] = "ASSESSED"
        record["disposition"] = assessment["disposition"]
        record["assessment"] = assessment
        provenance["provider_evidence"] = assessment.get("provider_evidence")
        return record

    @staticmethod
    def write_record(record: dict, root: Path | str = ".") -> Path:
        out_dir = Path(root) / RECORD_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = record["provenance"]["started_at"].replace(":", "").replace("+0000", "Z")
        out = out_dir / f"{record['work_unit_id']}.{stamp}.assessment.json"
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", help="work-unit text file handed to Agent Ready verbatim")
    ap.add_argument("--agent-ready", required=True, help="path to the agent-ready executable")
    ap.add_argument("--provider", required=True, choices=PROVIDERS)
    ap.add_argument("--work-unit-id", required=True)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    text = Path(a.source).read_text(encoding="utf-8")
    rec = AgentReadyCliAdapter(a.agent_ready).assess(text, provider=a.provider,
                                                     work_unit_id=a.work_unit_id, timeout_s=a.timeout)
    out = AgentReadyCliAdapter.write_record(rec, root=a.root)
    print(f"record    : {out}")
    print(f"outcome   : {rec['outcome']}" + (f"  disposition {rec['disposition']}" if "disposition" in rec else ""))
    p = rec["provenance"]
    print(f"producer  : {p['producer']} {p['agent_ready_version']} @ {p['agent_ready_checkout_commit']}")
    if rec["outcome"] != "ASSESSED":
        print(f"failure   : {rec['failure']['class']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
