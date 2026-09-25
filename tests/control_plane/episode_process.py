"""FX-C3 episode process: one OS process per step, sharing only the durable profile store.

Clocks are injected (`--utc`, `--mono`, integer microseconds). Prints one JSON document.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path


def result_for(profile, record, action, effect):
    from alienintent.control_plane.ports.episode import CoordinatorResult
    from tests.context_assembly.test_context_reconstruction import candidate
    view = profile.context.reconstruct(record.manifest_ref)
    version = view.document["lifecycle"][record.objective]["version"]
    return CoordinatorResult(record.objective, record.objective, record.epoch, record.invocation, record.manifest_ref,
                             action, version, effect, candidate() if action == "verify" else None)


def main() -> int:
    from alienintent.control_plane.domain.episode import EpisodeHold
    from alienintent.control_plane.ports.episode import Admitted, CoordinatorResult
    from tests.control_plane.test_episode_control import OBJECTIVE, episode_profile, Clocks, start
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("begin", "renew", "submit", "tick", "load"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--utc", required=True, type=int)
    parser.add_argument("--mono", type=int, default=0)
    parser.add_argument("--action")
    parser.add_argument("--effect")
    parser.add_argument("--result")
    arguments = parser.parse_args()
    profile = episode_profile(arguments.root, Clocks(arguments.utc, arguments.mono), invocation=arguments.invocation)
    output = {}
    try:
        if arguments.command in ("begin", "renew"):
            if arguments.command == "renew":
                current = profile.repository.load(OBJECTIVE)[1]
                profile.episodes.end(OBJECTIVE, epoch=current.epoch, actor="director")
            record = start(profile)
            output["result"] = asdict(result_for(profile, record, arguments.action, arguments.effect))
        elif arguments.command == "submit":
            outcome = profile.episodes.submit(CoordinatorResult(**json.loads(arguments.result)))
            output["outcome"] = "ADMITTED" if isinstance(outcome, Admitted) else "REFUSED"
            output["reason"] = getattr(outcome, "reason", None)
        elif arguments.command == "tick":
            profile.episodes.tick(OBJECTIVE)
        output["status"] = "OK"
    except EpisodeHold as hold:
        output.update(status="HOLD", reason=str(hold.reason), detail=hold.detail)
    record = profile.repository.load(OBJECTIVE)[1]
    output["record"] = None if record is None else record.document()
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
