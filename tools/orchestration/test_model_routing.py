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
