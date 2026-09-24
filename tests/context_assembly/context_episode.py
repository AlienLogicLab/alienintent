"""FX-C2 predecessor process: commit one durable event, pin, reconstruct, then exit.

Labelled LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE: EpisodeControl is C3, so an OS process
boundary with no shared object and no transcript stands in for ending an episode.
"""
import argparse
from pathlib import Path

from alienintent.composition.context_reconstruction import main as runner
from tests.context_assembly.test_context_reconstruction import attention_identity, build


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    profile = build(arguments.root, invocation=arguments.invocation)
    item = profile.attention.show(attention_identity(profile))
    profile.attention.seen(item.identity, "director", item.version)
    pointer = profile.context.pin()
    return runner(["reconstruct", "--root", str(arguments.root), "--project", "project", "--profile", "fixture",
                   "--manifest", pointer, "--invocation", arguments.invocation, "--observer", "context-predecessor"])


if __name__ == "__main__":
    raise SystemExit(main())
