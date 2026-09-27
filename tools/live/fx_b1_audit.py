"""FX-B1 read audit: run one module as __main__ and record every path the process touches.

Usage: python3 -B tools/live/fx_b1_audit.py <audit log> -m <module> [arguments...]

The audit hook is installed before the module is imported. Every path named by an `open`,
`sqlite3.connect`, directory listing or file-system write event (see EVENTS) is appended to the
audit log, one JSON string per line, even when the module exits with an error. The log itself
is opened before the hook is installed and is not recorded. `install` is the same hook for a
process that audits itself.
"""
import json
import os
import runpy
import sys

EVENTS = frozenset({"open", "sqlite3.connect", "os.listdir", "os.scandir", "os.mkdir", "os.rename", "os.remove",
                    "os.rmdir", "os.chmod", "os.truncate", "os.link", "os.symlink", "shutil.rmtree", "shutil.copyfile"})


def install(log_path):
    log = open(log_path, "a", buffering=1)

    def hook(event, arguments):
        if event in EVENTS and arguments and arguments[0] is not None and not isinstance(arguments[0], int):
            try:
                log.write(json.dumps(os.path.abspath(os.fsdecode(arguments[0]))) + "\n")
            except (TypeError, ValueError):
                log.write(json.dumps(repr(arguments[0])) + "\n")

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
