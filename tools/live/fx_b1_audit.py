"""FX-B1 read audit: run one module as __main__ and record every path the process touches.

Usage: python3 -B tools/live/fx_b1_audit.py <audit log> -m <module> [arguments...]

The audit hook is installed before the module is imported. Every path named by an `open`,
`sqlite3.connect`, directory listing or file-system write event (see EVENTS) is appended to the
audit log, symlinks resolved, one JSON string per line; every child process is recorded with its
argument vector (see EXECUTIONS), even when the module exits with an error. The log itself
is opened before the hook is installed and is not recorded. `install` is the same hook for a
process that audits itself.
"""
import json
import os
import runpy
import sys

EVENTS = frozenset({"open", "sqlite3.connect", "os.listdir", "os.scandir", "os.mkdir", "os.rename", "os.remove",
                    "os.rmdir", "os.chmod", "os.truncate", "os.link", "os.symlink", "shutil.rmtree", "shutil.copyfile"})
# Child processes: (event, index of the argument vector). A child is not itself audited, so its
# whole argument vector is recorded and every absolute path argument is recorded as touched.
EXECUTIONS = {"subprocess.Popen": 1, "os.exec": 1, "os.posix_spawn": 1, "os.spawn": 2, "os.system": 0}


def resolved(path):
    """Symlinks resolved; a path that cannot be decoded is recorded so that it is always forbidden."""
    try:
        return os.path.realpath(os.fsdecode(path))
    except (TypeError, ValueError):
        return "UNDECODABLE:" + repr(path)


def install(log_path):
    log = open(log_path, "a", buffering=1)

    def write(record):
        log.write(json.dumps(record) + "\n")

    def hook(event, arguments):
        if event in EVENTS and arguments and arguments[0] is not None and not isinstance(arguments[0], int):
            write(resolved(arguments[0]))
        elif event in EXECUTIONS and len(arguments) > EXECUTIONS[event]:
            argv = arguments[EXECUTIONS[event]]
            argv = argv.split() if isinstance(argv, (str, bytes)) else list(argv or ())
            argv = [os.fsdecode(a) if isinstance(a, (str, bytes, os.PathLike)) else repr(a) for a in argv]
            write({"exec": argv})
            for argument in argv:
                candidate = argument.split("=", 1)[-1]
                if candidate.startswith(os.sep):
                    write(resolved(candidate))

    sys.addaudithook(hook)


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "-m":
        raise SystemExit("usage: fx_b1_audit.py <audit log> -m <module> [arguments...]")
    log_path, module = sys.argv[1], sys.argv[3]
    install(log_path)
    sys.argv = [module, *sys.argv[4:]]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
