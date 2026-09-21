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


def test_cli_accepts_a_distinct_biu_version_for_decisions() -> None:
    from alienintent.control_plane.adapters.cli import _parser

    args = _parser().parse_args([
        "decisions", "decide", "PY-08", "--choice", "authorize", "--biu-version", "0",
        "--actor", "morty", "--authority", "operator", "--intent", "authorize",
        "--expected-version", "1", "--reason", "approved", "--idempotency-key", "decision-1",
    ])
    assert args.biu_version == 0


def test_cli_decision_uses_kernel_biu_version_after_row_revision_advances(tmp_path: Path) -> None:
    """Passing the store row revision to the kernel decision must fail this proof."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
from alienintent.execution_coordination.ports.worker_provider import WorkerOutcome
from tests.execution_coordination.test_factory_coordinator import _item

class Work:
    def __init__(self): self.items = (_item('PY-08', 0, 1),)
    def import_ready_snapshot(self): return self.items
    def propose_release(self, _): pass
    def project_execution_state(self, *_): pass
class Worker:
    def start(self, *_): return WorkerOutcome('authority-block')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    assert profile.coordinator.start().authority_blocked == ('PY-08',)
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "decisions", "decide", "PY-08", "--choice", "authorize", "--biu-version", "0", "--actor", "morty", "--authority", "SWF-21", "--intent", "authorize", "--expected-version", "2", "--reason", "approved", "--idempotency-key", "decision-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["event"]["work_item"] == "PY-08"


def test_cli_returns_a_sanitized_readiness_reason(tmp_path: Path) -> None:
    """Replacing the safe diagnostic vocabulary with an opaque constant must fail."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def start(self, *_): raise AssertionError('readiness gate must prevent start')
def make(): return OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "run", "--actor", "morty", "--authority", "SWF-21", "--intent", "start", "--expected-version", "0", "--reason", "approved", "--idempotency-key", "run-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "readiness-gate-failed"}


def test_cli_rejects_a_stale_mutation_version(tmp_path: Path) -> None:
    """A stale CLI write must be denied before the cancellation protocol runs."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): raise AssertionError('stale command reached cancellation')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "cancel", "PY-08", "--actor", "morty", "--authority", "SWF-21", "--intent", "cancel", "--expected-version", "0", "--reason", "stale", "--idempotency-key", "cancel-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "stale-expected-version"}


def test_cli_stop_rejects_a_stale_profile_fence(tmp_path: Path) -> None:
    """Dropping stop's expected-version fence would let this subprocess cancel work."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): raise AssertionError('stale stop reached cancellation')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "stop", "--actor", "morty", "--authority", "SWF-21", "--intent", "stop", "--expected-version", "0", "--reason", "stale", "--idempotency-key", "stop-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "stale-expected-version"}


def test_cli_sanitizer_labels_domain_conflicts_without_exposing_messages() -> None:
    """Generic ValueError/RuntimeError buckets misdescribe normal domain outcomes."""
    from alienintent.control_plane.adapters.cli import _sanitize
    from alienintent.execution_coordination.application.factory_coordinator import TerminalWork
    from alienintent.execution_coordination.domain.escalation import SupersededDecision
    from alienintent.execution_coordination.ports.operational_store import VersionConflict

    assert _sanitize(TerminalWork("terminal work contains token=SENTINEL")) == "terminal-work"
    assert _sanitize(SupersededDecision("decision token=SENTINEL")) == "superseded-decision"
    assert _sanitize(VersionConflict("revision token=SENTINEL")) == "stale-expected-version"


def test_cli_cancel_cannot_write_through_its_store_view(tmp_path: Path) -> None:
    """Replacing the application-service cancellation with a store write must fail."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): return 'cancelled'
class ReadOnlyStore:
    def __init__(self, store): self._store = store
    def read_state(self, *args): return self._store.read_state(*args)
    def commit(self, *_): raise AssertionError('CLI attempted a direct store write')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    profile.store = ReadOnlyStore(profile.store)
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "cancel", "PY-08", "--actor", "morty", "--authority", "SWF-21", "--intent", "cancel", "--expected-version", "1", "--reason", "operator stop", "--idempotency-key", "cancel-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "cancelled"


def test_cli_sanitizes_realistic_secret_shapes(tmp_path: Path) -> None:
    factory = tmp_path / "broken_factory.py"
    sentinel = "SENTINELSECRET"
    factory.write_text(
        "def make(): raise RuntimeError('AKIAIOSFODNN" + sentinel + " xoxb-1-" + sentinel
        + " postgres://factory:" + sentinel + "@db /home/a/.ssh/config Authorization=Basic " + sentinel + "')"
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )
    assert result.returncode != 0
    assert sentinel not in result.stdout + result.stderr
