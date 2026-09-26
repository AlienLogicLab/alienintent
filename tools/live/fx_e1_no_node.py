#!/usr/bin/env python3
"""FX-E1 no-Node instrumentation: observe, rather than assume, that no Node runs.

Two independent observers are applied to every process the FX-E1 run launches:

1. **Shims.** A per-run directory placed first on `PATH` holds `node`, `nodejs`,
   `npm`, `npx` and `corepack` stand-ins. Each appends one line to an audit log
   whose absolute path is written into the shim itself, then exits 97. A process
   that resolves Node by name is therefore recorded, even when the control plane
   states its worker environment instead of inheriting it, because the stated
   environment still carries `PATH`.
2. **A /proc sampler.** Every sample walks the whole process table and keeps each
   process that descends from a watched root or whose environment carries the
   per-run shim directory on `PATH`. Every distinct executable is retained; one
   whose resolved executable is a Node binary, or which maps `libnode`, is a
   Node observation. This catches a process that bypasses the shims by
   absolute path.

`self_test` demonstrates that the pair discriminates: intact (no Node) reads
clean, a shimmed Node invocation and an absolute-path Node invocation are each
detected, and the restored intact probe reads clean again.

    python3 tools/live/fx_e1_no_node.py --self-test --json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

NODE_NAMES = ("node", "nodejs", "npm", "npx", "corepack")
SHIM_EXIT = 97
NODE_EXECUTABLE_NAMES = frozenset({"node", "nodejs"})


def real_node_binaries() -> list[str]:
    """Every Node executable resolvable on the unshimmed PATH, resolved to its file."""
    found = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        for name in NODE_EXECUTABLE_NAMES:
            candidate = Path(directory or ".") / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                found.add(str(candidate.resolve()))
    return sorted(found)


class NodeShims:
    """A per-run PATH directory whose Node names record their use and fail."""

    def __init__(self, root: Path) -> None:
        self.directory = root / "no-node-shims"
        self.audit = root / "no-node-audit.log"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.audit.touch()
        for name in NODE_NAMES:
            shim = self.directory / name
            shim.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\t%s\\t%s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \"$$\" \"{name} $*\" >> '{self.audit}'\n"
                f"exit {SHIM_EXIT}\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)

    def environment(self, base: dict[str, str] | None = None) -> dict[str, str]:
        environment = dict(os.environ if base is None else base)
        environment["PATH"] = f"{self.directory}{os.pathsep}{environment.get('PATH', '')}"
        return environment

    def invocations(self) -> list[str]:
        return [line for line in self.audit.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _parent(pid: int) -> int | None:
    stat = _read(Path(f"/proc/{pid}/stat")).decode(errors="replace")
    closing = stat.rfind(")")
    if closing < 0:
        return None
    fields = stat[closing + 2:].split()
    return int(fields[1]) if len(fields) > 1 else None


def _executable(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/exe").removesuffix(" (deleted)")
    except OSError:
        return ""


def _maps_libnode(pid: int) -> bool:
    return b"libnode" in _read(Path(f"/proc/{pid}/maps"))


class ProcessSampler:
    """Sample every process the run owns, by ancestry or by the per-run PATH marker."""

    def __init__(self, marker: str, node_binaries: list[str], interval: float = 0.05) -> None:
        self.marker = marker.encode()
        self.node_binaries = frozenset(node_binaries)
        self.interval = interval
        self.roots: set[int] = set()
        self.seen: dict[tuple[int, str], dict] = {}
        self.samples = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def watch(self, pid: int) -> None:
        self.roots.add(pid)

    def _owned(self, pid: int, parents: dict[int, int | None]) -> bool:
        if b"PATH=" in (environ := _read(Path(f"/proc/{pid}/environ"))) and self.marker in environ:
            return True
        cursor, hops = pid, 0
        while cursor and hops < 64:
            if cursor in self.roots:
                return True
            cursor, hops = parents.get(cursor) or 0, hops + 1
        return False

    def sample(self) -> None:
        pids = [int(name) for name in os.listdir("/proc") if name.isdigit()]
        parents = {pid: _parent(pid) for pid in pids}
        for pid in pids:
            if pid == os.getpid() or not self._owned(pid, parents):
                continue
            executable = _executable(pid)
            key = (pid, executable)
            if key in self.seen:
                continue
            argv = _read(Path(f"/proc/{pid}/cmdline")).split(b"\0")
            resolved = str(Path(executable).resolve()) if executable else ""
            node = (
                Path(resolved).name in NODE_EXECUTABLE_NAMES
                or resolved in self.node_binaries
                or _maps_libnode(pid)
            )
            self.seen[key] = {
                "pid": pid, "executable": resolved, "argv0": argv[0].decode(errors="replace") if argv else "",
                "node": node,
            }
        self.samples += 1

    def start(self) -> "ProcessSampler":
        def loop() -> None:
            while not self._stop.is_set():
                self.sample()
                self._stop.wait(self.interval)
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        self.sample()

    def report(self) -> dict:
        processes = list(self.seen.values())
        return {
            "samples": self.samples,
            "processes_observed": len(processes),
            "executables": sorted({entry["executable"] for entry in processes if entry["executable"]}),
            "node_observations": [entry for entry in processes if entry["node"]],
        }


class NoNodeInstrument:
    """The shims and the sampler, applied together for one run."""

    def __init__(self, root: Path) -> None:
        self.shims = NodeShims(root)
        self.node_binaries = real_node_binaries()
        self.sampler = ProcessSampler(str(self.shims.directory), self.node_binaries)

    def environment(self, base: dict[str, str] | None = None) -> dict[str, str]:
        return self.shims.environment(base)

    def __enter__(self) -> "NoNodeInstrument":
        self.sampler.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.sampler.stop()

    def report(self) -> dict:
        sampled = self.sampler.report()
        shimmed = self.shims.invocations()
        return {
            "shim_directory_names": list(NODE_NAMES),
            "shim_invocations": shimmed,
            "known_node_binaries": self.node_binaries,
            **sampled,
            "node_observed": bool(shimmed) or bool(sampled["node_observations"]),
        }


# --- intact / fault / restored ----------------------------------------------------

PROBES = {
    "intact": [sys.executable, "-c", "print('python only')"],
    "fault-shimmed-node-by-name": [
        sys.executable, "-c", "import subprocess; subprocess.run(['node', '-e', '1'])",
    ],
    "fault-absolute-node-bypassing-shims": None,  # filled from the resolved binary
    "fault-stated-environment-detached": None,
    "restored": [sys.executable, "-c", "print('python only')"],
}


def _probe(name: str, argv: list[str], root: Path, detached_environment: bool = False) -> dict:
    instrument = NoNodeInstrument(root / name)
    with instrument:
        environment = instrument.environment()
        if detached_environment:
            environment = {"PATH": environment["PATH"], "HOME": os.environ.get("HOME", "/")}
        launched = subprocess.Popen(argv, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    start_new_session=detached_environment)
        if not detached_environment:
            instrument.sampler.watch(launched.pid)
        launched.wait(timeout=60)
        time.sleep(0.3)
    report = instrument.report()
    return {"probe": name, "argv": argv, "exit_status": launched.returncode, "node_observed": report["node_observed"],
            "shim_invocations": len(report["shim_invocations"]), "node_process_observations": len(report["node_observations"]),
            "processes_observed": report["processes_observed"], "samples": report["samples"]}


def self_test() -> dict:
    binaries = real_node_binaries()
    probes = dict(PROBES)
    if binaries:
        hold = "setTimeout(()=>{},1500)"
        probes["fault-absolute-node-bypassing-shims"] = [
            sys.executable, "-c", f"import subprocess; subprocess.run([{binaries[0]!r}, '-e', {hold!r}])",
        ]
        probes["fault-stated-environment-detached"] = [binaries[0], "-e", hold]
    results = []
    with tempfile.TemporaryDirectory(prefix="fx-e1-no-node-") as scratch:
        for name, argv in probes.items():
            if argv is None:
                results.append({"probe": name, "applied": False, "detail": "no Node binary on PATH to exercise"})
                continue
            results.append({"applied": True, **_probe(name, argv, Path(scratch), detached_environment=name.endswith("detached"))})
    expected = {name: name.startswith("fault") for name in probes}
    for result in results:
        result["expected_node_observed"] = expected[result["probe"]]
        result["discriminates"] = result.get("applied", False) and result["node_observed"] == expected[result["probe"]]
    return {"known_node_binaries": binaries, "probes": results,
            "ok": all(result["discriminates"] for result in results)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", required=True)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)
    result = self_test()
    if arguments.json:
        print(json.dumps(result, indent=1))
    else:
        for probe in result["probes"]:
            print(f"{'ok ' if probe['discriminates'] else 'BAD'} {probe['probe']}: node_observed={probe.get('node_observed')}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
