#!/usr/bin/env python3
"""FX-E1 resident: the shipped sandbox run profile, held resident until told to stop.

This is the same zero-argument factory `alienintent --profile-factory` loads, so the
ingress it serves is the production composition, the durable store is the run's
own `state.sqlite`, and its notifications append to the run's notification log.
It makes no Project write and dispatches nothing: it only answers deliveries.

    python3 tools/live/fx_e1_resident.py <stop-marker>
"""
from __future__ import annotations

from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from alienintent.composition.sandbox_run_profile import profile  # noqa: E402


def main(argv: list[str]) -> int:
    stop = Path(argv[0])
    run = profile()
    print(f"resident {run.ingress_route}", flush=True)
    while not stop.exists():
        time.sleep(0.25)
    run.release_residency()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
