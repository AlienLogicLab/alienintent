import json
import pytest
from model_routing import resolve_route


def doc(model):
    return {
        "schemaVersion": 1,
        "default": {"provider": "codex", "model": model},
        "providers": {
            "codex": {"executable": "/bin/codex", "permissionMode": "danger-full-access"},
            "claude": {"executable": "/bin/claude", "permissionMode": "bypassPermissions"},
        },
        "roles": {},
    }


def test_model_routing_is_reread_on_every_resolution(tmp_path):
    path = tmp_path / "routing.json"
    path.write_text(json.dumps(doc("model-a")))
    assert resolve_route("DIRECTOR", path)["model"] == "model-a"
    path.write_text(json.dumps(doc("model-b")))
    assert resolve_route("DIRECTOR", path)["model"] == "model-b"


def test_invalid_routing_fails_closed(tmp_path):
    path = tmp_path / "routing.json"
    bad = doc("")
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="MODEL_ROUTING_INVALID"):
        resolve_route("DIRECTOR", path)


def test_routing_enforces_provider_scoped_permission_modes(tmp_path):
    path = tmp_path / "routing.json"
    value = doc("model-a")
    value["providers"]["codex"]["permissionMode"] = "bypassPermissions"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="MODEL_ROUTING_INVALID"):
        resolve_route("DIRECTOR", path)


# --- unit 6c-2: one reader and one provider command builder, in src/alienintent/composition ---------------------------

import os  # noqa: E402
from pathlib import Path  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MOVED = ROOT / "src" / "alienintent" / "composition" / "model_routing.py"
ROUTES = {"claude": {"provider": "claude", "executable": "/bin/claude", "model": "m-1", "permissionMode": "bypassPermissions"},
          "codex": {"provider": "codex", "executable": "/bin/codex", "model": "m-2", "permissionMode": "workspace-write"}}


def test_the_tools_reader_is_the_moved_module_loaded_by_file_path_without_the_package():
    from model_routing import provider_command
    assert resolve_route.__code__.co_filename == provider_command.__code__.co_filename == str(MOVED)
    probe = subprocess.run([sys.executable, "-c", "import sys, model_routing; print('alienintent' in sys.modules)"],
                           cwd=HERE, env={"PATH": os.environ["PATH"]}, capture_output=True, text=True, check=True)
    assert probe.stdout.strip() == "False"


def test_the_director_command_is_the_moved_provider_command(tmp_path):
    from factory_director_host import ProcessDirectorLauncher
    from model_routing import provider_command
    for route in ROUTES.values():
        launcher = ProcessDirectorLauncher(tmp_path, tmp_path / "p", output_dir=tmp_path / "e", route_resolver=lambda _r: route)
        assert launcher.command() == provider_command(route, tmp_path)


def test_the_installed_director_host_imports_and_builds_its_command_with_plain_python3(tmp_path):
    """Check 9: install into a temporary HOME (systemctl stubbed), then import and build the command from the
    installed folder with plain python3 and no PYTHONPATH."""
    stub = tmp_path / "stub-bin"
    stub.mkdir()
    (stub / "systemctl").write_text("#!/bin/sh\nexit 0\n")
    (stub / "systemctl").chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    environment = {"HOME": str(home), "PATH": f"{stub}:/usr/bin:/bin"}
    subprocess.run(["bash", str(HERE / "install_factory_director_host.sh")], env=environment, check=True,
                   capture_output=True)
    target = home / ".local/share/alienintent-bootstrap/factory-director-host"
    assert (target / "model_routing.py").read_bytes() == MOVED.read_bytes()
    code = ("import json, sys\nfrom factory_director_host import ProcessDirectorLauncher\n"
            "routes = json.loads(sys.argv[1])\n"
            "print(json.dumps([ProcessDirectorLauncher('/work', '/p', output_dir='/tmp/e', route_resolver=lambda _r, r=r: r)"
            ".command() for r in routes]))")
    built = subprocess.run(["python3", "-c", code, json.dumps(list(ROUTES.values()))], cwd=target, env=environment,
                           capture_output=True, text=True, check=True)
    assert json.loads(built.stdout) == [
        ["/bin/claude", "-p", "--no-session-persistence", "--output-format", "json", "--permission-mode",
         "bypassPermissions", "--model", "m-1"],
        ["/bin/codex", "exec", "--ephemeral", "--json", "--sandbox", "workspace-write", "-C", "/work", "--model", "m-2", "-"]]
