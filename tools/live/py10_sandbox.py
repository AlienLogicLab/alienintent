#!/usr/bin/env python3
"""Shared live-sandbox plumbing for the PY-10 tools.

Everything here is tooling around the shipped package: credential minting for
Git, the redaction boundary the retained evidence is produced through, and the
seeded backlog's own definition. No tool in this directory is part of the
product, and nothing here is imported by `alienintent`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from alienintent.composition.sandbox_profile import (  # noqa: E402
    compose_identity,
    compose_profile,
    compose_secrets,
    load_profile_document,
)
from alienintent.composition.sandbox_run_profile import contract_from_document  # noqa: E402
from alienintent.installation.adapters.app_jwt import app_assertion  # noqa: E402
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport  # noqa: E402
from alienintent.installation.application.installation_credentials import InstallationCredentials  # noqa: E402

DEFAULT_PROFILE = Path.home() / ".config/alienintent-sandbox/profile.json"
DEFAULT_STATE = Path.home() / ".local/state/alienintent-sandbox/run"


def profile_path() -> Path:
    return Path(os.environ.get("ALIENINTENT_SANDBOX_PROFILE", str(DEFAULT_PROFILE))).expanduser()


def state_root() -> Path:
    return Path(os.environ.get("ALIENINTENT_SANDBOX_STATE", str(DEFAULT_STATE))).expanduser()


def document() -> dict:
    return dict(load_profile_document(profile_path()))


def credentials(record: dict) -> InstallationCredentials:
    return InstallationCredentials(
        compose_identity(record), compose_secrets(record), UrllibGitHubTransport(), time.time, app_assertion,
    )


class Redactor:
    """Replace every private installation detail with a stable placeholder.

    Retained evidence is produced *through* this boundary rather than cleaned
    afterwards, so AC 17 holds by construction. The sandbox identity still
    shows: the repository and Project this run used are named, only the App,
    installation, key path, ingress hostname and tunnel are not.
    """

    def __init__(self, record: dict) -> None:
        application = record.get("githubApp") or {}
        webhook = record.get("webhook") or {}
        self._rules = [
            (str(application.get("applicationId") or ""), "<app-id redacted>"),
            (str(application.get("installationId") or ""), "<installation-id redacted>"),
            (str(application.get("privateKeyPath") or ""), "<private-key-path redacted>"),
            (str(webhook.get("public_url") or "").rstrip("/"), "<ingress-hostname redacted>"),
            (str(webhook.get("tunnel_id") or ""), "<tunnel-id redacted>"),
        ]
        # The tunnel's *name* and its unit file are deliberately not redacted.
        # They are substrings of the sandbox repository name, and replacing
        # them would corrupt the repository identity, the candidate locators
        # and the installation scope — destroying the isolation proof the
        # redaction exists to protect. The tunnel identifier, which is the
        # private installation detail, is redacted.
        for location in (record.get("secret_references") or {}).values():
            self._rules.append((str(location), "<secret-reference-path redacted>"))
        self._rules.append((str(Path.home()), "<home redacted>"))

    def __call__(self, value: object) -> object:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, dict):
            return {self.text(str(name)): self(item) for name, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self(item) for item in value]
        return value

    def text(self, value: str) -> str:
        redacted = str(value)
        for secret, placeholder in self._rules:
            if secret:
                redacted = redacted.replace(secret, placeholder)
        return redacted


def credentialed_git_environment(record: dict, token: str) -> dict[str, str]:
    """Let Git reach the private sandbox repository by its published URL.

    Candidate custody compares a published revision against a *fresh* clone,
    and the locator it records must not carry credentials. The control plane
    therefore clones and pushes by the plain URL and rewrites it to the
    credentialed one here, in its own process environment only. The worker is
    launched with a stated environment that excludes these variables, so the
    credential that publishes a candidate never reaches the process that
    produced it.
    """
    repository = str(record["repository"])
    return dict(os.environ) | {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"url.https://x-access-token:{token}@github.com/{repository}.insteadOf",
        "GIT_CONFIG_VALUE_0": f"https://github.com/{repository}",
    }


def git(*arguments: str, cwd: Path | None = None, environment: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=cwd, env=environment, capture_output=True, text=True, check=check,
    )


# --- the seeded backlog -------------------------------------------------------
#
# Deliberately minimal but sufficient to exercise the factory (binding rule 4):
# four priorities, one equal-priority pair whose ordering can only come from
# READY-entry time, one dependency whose dependent outranks its blocker, and one
# BIU that requires a capability the profile does not hold.

WORKER_RUN = """#!/bin/bash
# The factory's worker entry point. The control plane launches exactly this
# file; the instruction for the specific BIU comes from the repository, and the
# provider CLI does the work.
set -euo pipefail

invocation="${ALIENINTENT_INVOCATION_ID:?the worker was not told which invocation it is}"
biu="${invocation#launch:}"
biu="${biu%:*}"
contract="biu/${biu}.json"
test -f "$contract" || { echo "no contract document for ${biu}" >&2; exit 4; }

# The control plane's publication credential must never reach a worker.
if [ -n "${GIT_CONFIG_COUNT:-}" ]; then
  echo "worker inherited a publication credential" >&2
  exit 5
fi

note="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["task"]["note"])' "$contract")"
instruction="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["task"]["instruction"])' "$contract")"

mkdir -p "$(dirname "$note")"
claude -p --permission-mode bypassPermissions --no-session-persistence \
  "You are the AlienIntent factory worker for BIU ${biu}, invocation ${invocation}. \
Task: ${instruction} \
Write only the file ${note}. Do not run git. Do not touch any other path. Reply with one short line when done." \
  >worker-provider.log 2>&1 || { echo "provider invocation failed" >&2; tail -5 worker-provider.log >&2; exit 6; }
rm -f worker-provider.log

test -s "$note" || { echo "the provider produced no ${note}" >&2; exit 7; }
git add -A
git commit -qm "${biu}: factory candidate for ${invocation}"
"""

WORKER_PROTOCOL = """# Sandbox worker protocol

The AlienIntent control plane allocates a Git worktree of this repository, then
runs `worker/run.sh` inside it with `ALIENINTENT_INVOCATION_ID` set to the
correlation the coordinator dispatched under (`launch:<BIU>:<version>`).

`run.sh` resolves the BIU from that identity, reads its task from
`biu/<BIU>.json`, asks the provider CLI to produce the named note, and makes one
commit. It never pushes: publication and independent read-back are the control
plane's, and the worker is not given a credential that could publish.

This repository is PY-10 test infrastructure. Nothing here is a product.
"""


def seed_contract(identity: str, priority: str, *, dependencies: tuple[str, ...] = (), capabilities: tuple[str, ...] = ("python",), purpose: str = "") -> dict:
    note = f"docs/{identity}.md"
    return {
        "identity": identity,
        "version": "1",
        "intent": f"{identity}: {purpose}",
        "satisfied_requirement_ids": ["SF-REQ-001", "SF-REQ-010"],
        "fixed_decisions": ["FD-03"],
        "authorized_scope": [note],
        "excluded_scope": ["every path outside the named note"],
        "dependencies": list(dependencies),
        "required_capabilities": list(capabilities),
        "budget_policy": {
            "hard_required_dimensions": ["attempts", "retries"],
            "maximum_attempts": 2,
            "hard_wall_clock_seconds": 600,
            "retry_limit": 1,
            "concurrency_limit": 1,
            "cancellation_limit": 1,
        },
        "retry_policy": "one bounded retry, then report failure",
        "completion_criteria": [f"{note} records the invocation that produced it"],
        "verification_obligations": ["the published candidate is read back from a fresh, independent clone"],
        "required_evidence": ["artifact-verified"],
        "non_goals": ["any change outside the named note", "pushing, merging or deploying"],
        "candidate_custody_requirements": ["a published source revision, independently read back before VERIFY"],
        "release_policy": "automatic-on",
        "authority_issuer": "PY-10 live proof (SWF-11)",
        "authority_references": ["SWF-08", "SWF-11", "AlienLogicLab/alienintent#58"],
        "target_repositories": ["AlienLogicLab/alienintent-sandbox"],
        "baselines": ["main"],
        "required_closure_actions": ["candidate-published"],
        "stop_escalation_conditions": ["authority the profile does not hold"],
        "task": {
            "note": note,
            "priority": priority,
            "instruction": (
                f"Create {note} containing a markdown heading '# {identity}' and exactly one bullet line "
                f"recording that the AlienIntent factory executed {identity} under the invocation named above."
            ),
        },
    }


SEEDS: tuple[dict, ...] = (
    seed_contract("SB-01", "P0", purpose="highest priority work, dispatched first"),
    seed_contract("SB-06", "P0", capabilities=("python", "network-egress"), purpose="requires a capability this profile does not hold, so release admission must escalate"),
    seed_contract("SB-02", "P1", purpose="first of an equal-priority pair, made READY earlier"),
    seed_contract("SB-03", "P1", purpose="second of an equal-priority pair, made READY later"),
    seed_contract("SB-04", "P2", dependencies=("SB-05",), purpose="outranks its blocker and must still wait for it"),
    seed_contract("SB-05", "P3", purpose="lowest priority, and the blocker SB-04 depends on"),
)


def seed_body(contract_document: dict) -> str:
    digest = contract_from_document(contract_document).content_digest
    identity = contract_document["identity"]
    return "\n".join([
        f"biu: {identity}",
        f"contract: biu/{identity}.json",
        f"readiness_digest: {digest}",
        f"depends_on: {', '.join(contract_document['dependencies'])}",
        "",
        contract_document["intent"],
    ])


def seed_title(contract_document: dict) -> str:
    return f"{contract_document['identity']} — {contract_document['task']['note']}"


class SeedWriter:
    """Set Project field values while seeding, without widening the product adapter.

    The shipped `GitHubProjectsV2Directory` writes exactly one thing — the
    lifecycle Status projection — and nothing in the product ever sets
    Priority. Seeding does, so it is done here, in tooling, and still routes
    every answer through `ProjectAddress.resolve` so no other Project can be
    addressed by accident.
    """

    _SCHEMA = """query($project:ID!){ node(id:$project){ ... on ProjectV2 { id number
      fields(first:50){ nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }"""
    _WRITE = """mutation($project:ID!,$item:ID!,$field:ID!,$option:String!){
      updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:{singleSelectOptionId:$option}}){
        projectV2Item { id project { id number } } } }"""

    def __init__(self, address, transport, authorization) -> None:
        self._address, self._transport, self._authorization = address, transport, authorization
        self.addressed: list[str] = []

    def _graphql(self, query: str, variables: dict) -> dict:
        body = json.dumps({"query": query, "variables": variables}).encode()
        response = self._transport.request(
            "POST", "https://api.github.com/graphql",
            dict(self._authorization()) | {"Content-Type": "application/json"}, body,
        )
        answer = json.loads(response.body or b"{}")
        if response.status != 200 or answer.get("errors"):
            raise RuntimeError(f"Projects v2 refused a seeding call: HTTP {response.status}")
        return answer.get("data") or {}

    def options(self, field: str) -> dict[str, str]:
        node = self._graphql(self._SCHEMA, {"project": self._address.project_id})["node"]
        self._address.resolve(node.get("id"), node.get("number"))
        self.addressed.append(str(node.get("id")))
        for candidate in node["fields"]["nodes"]:
            if candidate and candidate.get("name") == field:
                return {option["name"]: option["id"] for option in candidate["options"]}
        raise RuntimeError(f"the configured Project exposes no {field} field")

    def set_field(self, item: str, field: str, option_name: str) -> None:
        option = self.options(field)[option_name]
        written = self._graphql(self._WRITE, {
            "project": self._address.project_id, "item": item,
            "field": self._address.field_for(field), "option": option,
        })["updateProjectV2ItemFieldValue"]["projectV2Item"]
        self._address.resolve(written["project"].get("id"), written["project"].get("number"))
        self.addressed.append(str(written["project"].get("id")))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
