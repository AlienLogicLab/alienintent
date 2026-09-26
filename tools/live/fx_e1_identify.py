#!/usr/bin/env python3
"""FX-E1 step 1: identify the existing Python profile/transport, offline.

WO-220502 requires the existing Python profile and transport revision, custody
and configured scoped resources to be identified *before* any live integration
proof. This tool makes no network call and changes nothing: it reads the
repository, the recorded sandbox profile and tunnel configuration, file modes and
the local process table, and prints the identification record through the same
redaction boundary the PY-10 tools use (no App id, installation id, key path,
secret path, ingress hostname or tunnel id).

    python3 tools/live/fx_e1_identify.py --json > identification.json
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_sandbox import ROOT, Redactor, document, profile_path  # noqa: E402

from alienintent.composition.sandbox_profile import compose_profile  # noqa: E402

NODE_CONFIG = Path.home() / ".config/alienintent/self-hosting.json"
TUNNEL_CONFIG = Path.home() / ".config/alienintent-sandbox/tunnel.yml"

# The production path FX-E1 exercises: the CLI-loadable composition, the
# transport and ingress adapters it binds, the durable store and the factory.
PRODUCTION_PATH_MODULES = (
    "src/alienintent/__main__.py",
    "src/alienintent/control_plane/adapters/cli.py",
    "src/alienintent/composition/sandbox_run_profile.py",
    "src/alienintent/composition/sandbox_profile.py",
    "src/alienintent/composition/role_binding.py",
    "src/alienintent/composition/doctor_probes.py",
    "src/alienintent/execution_coordination/adapters/github_webhook.py",
    "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
    "src/alienintent/execution_coordination/adapters/github_work_management.py",
    "src/alienintent/execution_coordination/adapters/github_repository_api.py",
    "src/alienintent/execution_coordination/adapters/sqlite_store.py",
    "src/alienintent/execution_coordination/application/factory_coordinator.py",
    "src/alienintent/installation/adapters/urllib_github_transport.py",
    "src/alienintent/installation/adapters/app_jwt.py",
    "src/alienintent/installation/application/installation_credentials.py",
    "src/alienintent/invocation_runtime/adapters/cli_worker.py",
    "src/alienintent/invocation_runtime/adapters/git_source_control.py",
    "src/alienintent/invocation_runtime/application/real_worker.py",
)

CUSTODY_RECORDS = (
    ("docs/operations/py10-sandbox.md", "provisioning record of the sandbox repository, Project, App, tunnel, port and profile (SWF-08)"),
    ("docs/decisions/2026-09-21-sandbox-isolation-standard.md", "SWF-34 isolation standard: repository isolation permission-enforced, Project isolation configuration-enforced"),
    ("docs/evidence/PY-09B-live-transport.md", "PY-09B: the transport substrate the profile composes (Wave 1 receipt; identification only, not proof here)"),
    ("docs/evidence/wo-220501-fx-b0/bootstrap-custody-manifest.json", "WO-220501 FX-B0 external bootstrap custody manifest (Node/bootstrap side)"),
    ("docs/work-units/wave2/WO-220502.md", "EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY record (2026-09-26)"),
)


def digest(path: Path) -> str | None:
    return "sha256:" + sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()


def declared_dependencies() -> list[str]:
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8")).get("project") or {}
    return list(project.get("dependencies") or [])


def file_custody(path: Path) -> dict:
    if not path.exists():
        return {"present": False}
    info = path.stat()
    return {"present": True, "mode": oct(stat.S_IMODE(info.st_mode)), "owner_uid_matches_operator": info.st_uid == os.getuid()}


def processes() -> list[dict]:
    listed = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            argv = Path(f"/proc/{name}/cmdline").read_bytes().split(b"\0")
            executable = os.readlink(f"/proc/{name}/exe")
        except OSError:
            continue
        listed.append({"pid": int(name), "executable": executable, "argv": [part.decode(errors="replace") for part in argv if part]})
    return listed


def tunnel_identification(table: list[dict]) -> dict:
    text = TUNNEL_CONFIG.read_text(encoding="utf-8") if TUNNEL_CONFIG.is_file() else ""
    services = [line.split("service:", 1)[1].strip() for line in text.splitlines() if "service:" in line]
    runners = [entry for entry in table if any(str(TUNNEL_CONFIG) == part for part in entry["argv"])]
    return {
        "config_digest": digest(TUNNEL_CONFIG),
        "config_custody": file_custody(TUNNEL_CONFIG),
        "ingress_services": services,
        "connector_processes": [
            {"pid": entry["pid"], "executable_name": Path(entry["executable"]).name,
             "executable_is_node": Path(entry["executable"]).name in {"node", "nodejs"}}
            for entry in runners
        ],
        "definition": "the sandbox's own cloudflared connector routes the provisioned hostname to the Python ingress port; "
                      "a running tunnel alone discharges nothing (WO-220502)",
    }


def node_writer_identification(table: list[dict]) -> dict:
    """The live Node writer, identified so the Python proof provably stays off its work."""
    config = json.loads(NODE_CONFIG.read_text(encoding="utf-8")) if NODE_CONFIG.is_file() else {}
    repository = config.get("repository") or {}
    runtime = [entry for entry in table if any(part.endswith("bin/alienintent.mjs") for part in entry["argv"])]
    return {
        "repository": f"{repository.get('owner')}/{repository.get('name')}" if repository else None,
        "project_number": (config.get("project") or {}).get("number"),
        "listen_port": (config.get("webhook") or {}).get("listenPort"),
        "runtime_processes": [{"pid": entry["pid"], "executable_name": Path(entry["executable"]).name} for entry in runtime],
        "policy": "KEEP_UNTIL_REPLACED: the Node bootstrap is the single approved live writer of its own repository and "
                  "Project; FX-E1 neither starts, stops, reconfigures nor dispatches its work",
    }


def identify() -> dict:
    record = document()
    redact = Redactor(record)
    profile = compose_profile(record)
    application = record.get("githubApp") or {}
    table = processes()
    node_writer = node_writer_identification(table)
    scoped = {
        "repository": profile.repository,
        "project_reference": profile.project_reference,
        "project_number": profile.project_number,
        "ingress_listen": f"{profile.webhook_listen_address}:{profile.webhook_listen_port}",
        "tunnel_name": (record.get("webhook") or {}).get("tunnel"),
        "tunnel_unit": (record.get("webhook") or {}).get("systemd_unit"),
        "app_slug": application.get("applicationSlug"),
        "app_status": application.get("status"),
        "automatic_release": profile.automatic_release,
        "must_not_touch": list((record.get("isolation") or {}).get("must_not_touch") or ()),
    }
    disjoint = {
        "python_repository_differs_from_node_repository": node_writer["repository"] not in (None, profile.repository),
        "python_port_differs_from_node_port": node_writer["listen_port"] != profile.webhook_listen_port,
        "node_repository_is_on_the_python_must_not_touch_list": node_writer["repository"] in scoped["must_not_touch"],
    }
    identification = {
        "record_kind": "FxE1Identification",
        "schema_version": "1",
        "fixture_id": "FX-E1",
        "work_unit": "WO-220502",
        "network_calls": 0,
        "source": {
            "repository": "AlienLogicLab/alienintent",
            "revision": git("rev-parse", "HEAD"),
            "worktree_clean": git("status", "--porcelain", "--", "src") == "",
            "python": platform.python_version(),
            "declared_runtime_dependencies": declared_dependencies(),
            "production_path_modules": {path: digest(ROOT / path) for path in PRODUCTION_PATH_MODULES},
        },
        "profile": {
            "name": profile.profile,
            "location": str(profile_path()),
            "document_digest": digest(profile_path()),
            "custody": file_custody(profile_path()),
            "composition_factory": "alienintent.composition.sandbox_run_profile:profile",
            "secret_references": {
                name: file_custody(Path(str(location))) for name, location in (record.get("secret_references") or {}).items()
            },
            "app_private_key": file_custody(Path(str(application.get("privateKeyPath") or "/nonexistent"))),
        },
        "scoped_resources": scoped,
        "transport": tunnel_identification(table),
        "node_live_writer": node_writer,
        "one_writer_separation": disjoint,
        "custody_records": [{"path": path, "digest": digest(ROOT / path), "role": role} for path, role in CUSTODY_RECORDS],
        "execution_authority": {
            "provisioning": "SWF-08 (Founder, 2026-09-21): test/integration infrastructure only",
            "isolation": "SWF-34 (Founder, 2026-09-21)",
            "live_proof": "EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY, Director inbox founder-live-transport-proof-authority-20260926T070519Z, "
                          "recorded in docs/work-units/wave2/WO-220502.md; release of WO-220502 by SWF-35 on Issue #122",
        },
        "interpretation": (
            "The only configured Python live profile is py10-sandbox. Its production path is the shipped control plane "
            "(`python -m alienintent --profile-factory alienintent.composition.sandbox_run_profile:profile`) bound to the "
            "real GitHub App installation, the real sandbox repository and Project, the provisioned tunnel and the resident "
            "ingress on its recorded port. The AlienIntent repository and Project #1 belong to the live Node writer and are on "
            "this profile's must-not-touch list; exercising them from Python would breach one-writer ownership, so they are "
            "not a target of this proof."
        ),
    }
    return redact(identification)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="FX-E1 offline identification")
    parser.add_argument("--json", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(identify(), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
