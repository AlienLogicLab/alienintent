"""Executable control-plane CLI proofs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from alienintent.control_plane.application.operator import OperatorControlPlane
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore


class _Profile:
    name = "offline"

    def __init__(self, path: Path) -> None:
        self.store = SQLiteOperationalStore(path)
        self.coordinator = None

    def cancel(self, target, **command):
        return {"target": target, "operation": "cancelled", "actor": command["actor"]}


def test_cli_version_and_unavailable_profile_are_machine_readable(tmp_path: Path) -> None:
    environment = {**os.environ, "PYTHONPATH": f"{Path.cwd() / 'src'}:{Path.cwd()}"}
    version = subprocess.run([sys.executable, "-m", "alienintent", "--json", "version"], capture_output=True, text=True, env=environment)
    assert version.returncode == 0
    assert json.loads(version.stdout)["version"] == "0.0.0"

    unavailable = subprocess.run([sys.executable, "-m", "alienintent", "--json", "status"], capture_output=True, text=True, env=environment)
    assert unavailable.returncode != 0
    assert json.loads(unavailable.stdout)["error"] == "profile is required"


def test_status_labels_execution_separately_when_upstream_is_unavailable(tmp_path: Path) -> None:
    control = OperatorControlPlane(_Profile(tmp_path / "operational.sqlite"))

    status = control.status()

    assert status["upstream"]["availability"] == "unavailable"
    assert status["execution"]["availability"] == "known"
    assert status["projection"]["availability"] == "unavailable"


def test_mutation_is_delegated_to_a_profile_application_service(tmp_path: Path) -> None:
    control = OperatorControlPlane(_Profile(tmp_path / "operational.sqlite"))

    result = control.invoke("cancel", "PY-08", actor="morty", authority="SWF-21", expected_version=0, reason="bounded test", idempotency_key="cancel-1")

    assert result == {"target": "PY-08", "operation": "cancelled", "actor": "morty"}
