"""The model-routing reader and provider command builder, re-exported from its one copy.

The code lives in `src/alienintent/composition/model_routing.py` (standard library only). It is loaded here by file
path, never by importing the `alienintent` package, so the tools and their tests work with plain `python3`. The
installed Director host gets that file itself as its `model_routing.py` (install_factory_director_host.sh).
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[2] / "src" / "alienintent" / "composition" / "model_routing.py"
_SPEC = importlib.util.spec_from_file_location("_alienintent_composition_model_routing", _SOURCE)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

routing_path, resolve_route, provider_command = _MODULE.routing_path, _MODULE.resolve_route, _MODULE.provider_command
