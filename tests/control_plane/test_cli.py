"""Subprocess proof for the public operator CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def test_cli_status_reports_real_execution_when_upstream_is_unavailable(tmp_path: Path) -> None:
    """Removing the CLI adapter or leaking an upstream secret breaks this proof."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile

class Work:
    def import_ready_snapshot(self):
        raise RuntimeError('token=SENTINEL-CLI-SECRET unavailable')
class Worker:
    def cancel(self, *_): return 'cancelled'
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    environment = os.environ | {"PYTHONPATH": f"src:{tmp_path}"}
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "status", "--json"],
        text=True, capture_output=True, env=environment, check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["execution"]["status"] == "known"
    assert payload["upstream"]["status"] == "unavailable"
    assert "SENTINEL-CLI-SECRET" not in result.stdout + result.stderr


def test_cli_returns_json_error_without_traceback_when_factory_leaks_secret(tmp_path: Path) -> None:
    """Removing the top-level sanitization must fail rather than expose diagnostics."""
    factory = tmp_path / "broken_factory.py"
    factory.write_text("def make(): raise RuntimeError('secret=SENTINEL-LEAK')")
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]
    assert "SENTINEL-LEAK" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr


def test_cli_sanitizes_invalid_arguments(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "status", "--bad=secret=SENTINEL-ARG"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-ARG" not in result.stdout + result.stderr


def test_cli_redacts_bearer_and_provider_diagnostics(tmp_path: Path) -> None:
    factory = tmp_path / "broken_factory.py"
    factory.write_text("def make(): raise RuntimeError('Authorization: Bearer SENTINEL-BEARER provider stderr: ghp_SENTINEL-PAT')")
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-BEARER" not in result.stdout + result.stderr
    assert "SENTINEL-PAT" not in result.stdout + result.stderr
    assert "provider stderr" not in result.stdout.lower() + result.stderr.lower()


def test_cli_sanitizes_subcommand_parse_errors() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "decisions", "secret=SENTINEL-SUBPARSER"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-SUBPARSER" not in result.stdout + result.stderr
