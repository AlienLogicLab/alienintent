#!/usr/bin/env python3
"""Installation launch-command migration proof (WO-220510, DAG node B7, proof fixture FX-B7).

Enumerates every installation launch surface pinned in
docs/evidence/wave2-proof-fixtures/FX-B7/FX-B7.md, classifies each reference to the canonical
`alienintent` command or its `b-disp` compatibility alias, migrates alias launches only under a
recorded installation authority (with byte-exact rollback), reads back canonical launches on the
live installation, and proves persisted B-DISP markers, lanes, resources and history survive.

Host reads are read-only: systemd-analyze, `systemctl --user list-units/show`, `crontab -l`,
`reg.exe query`, /proc and file reads. The only write path is `migrate --apply`, and only for a
non-empty plan. Alias retirement is never performed or claimed.

Usage:
    python3 tools/live/installation_launch.py run --output <dir> --invocation <id> --authority <decision.md>
    python3 tools/live/installation_launch.py controls --output <controls.json>
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-B7/FX-B7.md"
PREDECESSOR_MANIFEST = "docs/evidence/wo-220501-fx-b0/bootstrap-custody-manifest.json"
SELF_HOSTING = HOME / ".config/alienintent/self-hosting.json"
RUNTIME_UNIT = "alienintent.service"

SURFACES = ("systemd-user-paths", "systemd-system-paths", "systemd-user-loaded", "processes", "cron",
            "shell-startup", "xdg-autostart", "path-executables", "alienintent-config", "bootstrap-root",
            "wsl-boot", "windows-startup", "windows-run-keys", "windows-tasks")
ALIAS_NAMES = {"b-disp", "b-disp.mjs", "b-disp.cmd", "b-disp.ps1"}
CANONICAL_NAMES = {"alienintent", "alienintent.mjs", "alienintent.cmd", "alienintent.ps1"}
REPLACEMENT = {"b-disp": "alienintent", "b-disp.mjs": "alienintent.mjs", "b-disp.cmd": "alienintent.cmd",
               "b-disp.ps1": "alienintent.ps1"}
RETIREMENT_HELD = "HELD"
RETIREMENT_COMPLETE = "COVERAGE_COMPLETE_RETIREMENT_NOT_AUTHORIZED_HERE"
AUTHORITY_TOKEN = "INSTALLATION_MIGRATION_AUTHORITY"
STATE_KEYS = ("resources", "closures", "founderExceptions", "deliveries", "diagnostics", "active")
MARKER_SOURCES = {"src/github/authority.mjs": r"B-DISP", "src/runtime/dispatcher.mjs": r"B-DISP",
                  "src/runtime/worktree-manager.mjs": r"b-disp"}
SPLIT = re.compile(r"""[\s"'`=,;(){}\[\]<>|&]+""")
JSON_LAUNCH_KEY = re.compile(r"(executable|launcher|command|exec|preflight|script|program)", re.I)


class Unknown(Exception):
    """A surface could not be read completely; its coverage is UNKNOWN."""


@dataclass(frozen=True)
class Record:
    location: str
    line: int
    text: str
    launch: bool


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry_point(token: str) -> bool:
    """True when the token can name a launched program: a bare command word, an entry-point file
    name, or an existing regular file. Directory paths and repository slugs are names only."""
    base = re.split(r"[/\\]", token)[-1]
    return token == base or base.endswith((".mjs", ".cmd", ".ps1")) or os.path.isfile(token)


def classify_token(token: str) -> str | None:
    base = re.split(r"[/\\]", token)[-1]
    if base in ALIAS_NAMES:
        return "ALIAS"
    if base in CANONICAL_NAMES:
        return "CANONICAL"
    return None


def references(surface: str, records) -> list[dict]:
    found = []
    for record in records:
        for token in SPLIT.split(record.text):
            kind = classify_token(token)
            if kind:
                found.append({"surface": surface, "location": record.location, "line": record.line,
                              "token": token, "launch": record.launch, "entry_point": entry_point(token),
                              "class": f"{kind}_{'LAUNCH' if record.launch else 'REFERENCE'}",
                              "text": record.text.strip()[:400]})
    return found


def text_of(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    text = data.decode("utf-8", "replace")
    if data.count(b"\x00") > len(data) // 4:  # binary such as .lnk: scan UTF-16LE strings as well
        text += "\n" + data.decode("utf-16-le", "replace").replace("\x00", " ")
    return text


def file_records(path: Path, launch_rule) -> list[Record]:
    records = []
    for number, line in enumerate(text_of(path.read_bytes()).splitlines(), 1):
        records.append(Record(str(path), number, line, launch_rule(line)))
    return records


def walk_files(root: Path, excluded=()):
    """Every file under root. Missing root is an empty surface; unreadable entries raise Unknown."""
    if not root.exists():
        return []
    files, errors = [], []
    for directory, dirs, names in os.walk(root, onerror=errors.append):
        dirs[:] = sorted(d for d in dirs if d not in excluded)
        files += [Path(directory) / n for n in sorted(names)]
    if errors:
        raise Unknown(f"unreadable under {root}: {errors[0]}")
    return files


def exec_line(line: str) -> bool:
    return bool(re.match(r"\s*-?Exec\w*\s*=", line))


def code_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def cron_line(line: str) -> bool:
    return code_line(line) and not re.match(r"\s*[A-Za-z_]+\s*=", line)


def config_records(path: Path) -> list[Record]:
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_text())
        except (ValueError, UnicodeDecodeError):
            return file_records(path, exec_line)
        records = []

        def visit(node, keys):
            if isinstance(node, dict):
                for key, child in node.items():
                    visit(child, keys + [str(key)])
            elif isinstance(node, list):
                for child in node:
                    visit(child, keys)
            elif isinstance(node, str):
                pointer = "/" + "/".join(keys)
                records.append(Record(f"{path}#{pointer}", 0, node, bool(JSON_LAUNCH_KEY.search(pointer))))
        visit(value, [])
        return records
    return file_records(path, lambda line: exec_line(line) or line.lstrip().startswith("exec "))


class Host:
    """Operational host. Every method is read-only."""
    label = "OPERATIONAL"

    def __init__(self):
        self.commands = []
        self.observations = {}

    def run(self, argv, check=True):
        self.commands.append(argv)
        env = dict(os.environ, XDG_RUNTIME_DIR=os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
        result = subprocess.run(argv, capture_output=True, env=env, timeout=120)
        self.observations[" ".join(argv)] = result.stdout + result.stderr
        if check and result.returncode != 0:
            raise Unknown(f"{argv[0]} exited {result.returncode}: {result.stderr.decode(errors='replace')[:200]}")
        return result.stdout.decode(errors="replace")

    # --- surfaces -------------------------------------------------------------------------
    def unit_path_records(self, user):
        argv = ["systemd-analyze"] + (["--user"] if user else []) + ["unit-paths"]
        records = []
        for directory in self.run(argv).split():
            for path in walk_files(Path(directory)):
                if path.is_file():
                    records += file_records(path, exec_line)
        return records

    def loaded_units(self):
        listing = self.run(["systemctl", "--user", "list-units", "--all", "--plain", "--no-legend", "--no-pager"])
        names = [line.split()[0] for line in listing.splitlines() if line.split()]
        shown = self.run(["systemctl", "--user", "show", "-p", "Id,ExecStart,ExecStartPre,ExecStartPost,ExecReload,"
                          "ExecStop,ActiveState,SubState,MainPID", "--", *names])
        units = {}
        for block in shown.split("\n\n"):
            props = dict(p.split("=", 1) for p in block.splitlines() if "=" in p)
            if not props.get("Id"):
                continue
            execs = [re.sub(r"^.*?argv\[\]=(.*?) ; ignore_errors.*$", r"\1", v)
                     for k, v in props.items() if k.startswith("Exec") and v]
            units[props["Id"]] = {"exec": execs, "active": props.get("ActiveState"), "sub": props.get("SubState"),
                                  "main_pid": int(props.get("MainPID") or 0)}
        if set(names) - set(units):
            raise Unknown(f"systemctl show omitted units: {sorted(set(names) - set(units))[:5]}")
        return units

    def loaded_records(self):
        return [Record(f"unit:{name}", 0, e, True)
                for name, unit in self.loaded_units_cache().items() for e in unit["exec"]]

    def cmdline(self, pid):
        try:
            return Path(f"/proc/{pid}/cmdline").read_bytes().rstrip(b"\x00").split(b"\x00")
        except OSError:
            return None

    def process_records(self):
        records, own = [], {os.getpid()}
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit() and int(entry.name) not in own:
                argv = self.cmdline(entry.name)
                if argv:
                    records.append(Record(f"pid:{entry.name}", 0,
                                          " ".join(a.decode(errors="replace") for a in argv), True))
        return records

    def cron_records(self):
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        self.commands.append(["crontab", "-l"])
        if result.returncode != 0 and "no crontab" not in result.stderr:
            raise Unknown(f"crontab -l: {result.stderr.strip()}")
        records = [Record("crontab:user", n, line, cron_line(line)) for n, line in enumerate(result.stdout.splitlines(), 1)]
        for path in [Path("/etc/crontab")] + walk_files(Path("/etc/cron.d")):
            if path.is_file():
                records += file_records(path, cron_line)
        return records

    def listed_file_records(self, paths, rule):
        records = []
        for path in paths:
            for file in ([path] if path.is_file() else walk_files(path)):
                records += file_records(file, rule)
        return records

    def shell_records(self):
        paths = [HOME / n for n in (".profile", ".bash_profile", ".bash_login", ".bashrc", ".bash_aliases",
                                   ".zshrc", ".zprofile")] + [Path("/etc/profile"), Path("/etc/profile.d"),
                                                               Path("/etc/bash.bashrc")]
        return self.listed_file_records([p for p in paths if p.exists()], code_line)

    def autostart_records(self):
        return self.listed_file_records([p for p in (HOME / ".config/autostart", Path("/etc/xdg/autostart"))
                                         if p.exists()], exec_line)

    def path_dirs(self):
        dirs = []
        pid = self.runtime_pid()
        if pid:
            environ = Path(f"/proc/{pid}/environ").read_bytes().split(b"\x00")
            dirs += [d for e in environ if e.startswith(b"PATH=") for d in e[5:].decode().split(":")]
        login = self.run(["env", "-i", f"HOME={HOME}", "bash", "-lc", 'printf %s "$PATH"'])
        dirs += login.split(":")
        node = shutil.which("node", path=":".join(dirs)) or str(HOME / ".local/bin/node")
        prefix = Path(os.path.realpath(node)).parent.parent
        dirs += [str(prefix / "bin"), str(prefix / "lib/node_modules")]
        return list(dict.fromkeys(d for d in dirs if d))

    def path_records(self):
        records = []
        for directory in self.path_dirs():
            path = Path(directory)
            if not path.is_dir():
                continue
            try:
                names = sorted(os.listdir(path))
            except OSError as error:
                raise Unknown(f"unreadable PATH directory {path}: {error}")
            records += [Record(str(path / n), 0, str(path / n) + " -> " + os.path.realpath(path / n), True)
                        for n in names]
        return records

    def config_surface_records(self):
        records = []
        for path in walk_files(HOME / ".config/alienintent", excluded=("secrets",)):
            if path.is_file():
                records += config_records(path)
        return records

    def bootstrap_records(self):
        records = []
        for path in walk_files(HOME / ".local/share/alienintent-bootstrap", excluded=("__pycache__", ".pytest_cache")):
            if path.is_file():
                records += file_records(path, code_line)
        return records

    def wsl_records(self):
        path = Path("/etc/wsl.conf")
        return file_records(path, lambda line: line.strip().startswith("command")) if path.exists() else []

    def windows_startup_records(self):
        users = Path("/mnt/c/Users")
        if not users.exists():
            raise Unknown("/mnt/c is not mounted")
        folders = [Path("/mnt/c/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp")]
        for user in sorted(users.iterdir()):
            if user.is_dir():
                try:
                    candidate = user / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
                    if candidate.exists():
                        folders.append(candidate)
                except PermissionError as error:
                    raise Unknown(f"unreadable Windows profile {user}: {error}")
        return self.listed_file_records(folders, lambda line: True)

    def windows_run_records(self):
        reg = "/mnt/c/Windows/System32/reg.exe"
        if not Path(reg).exists():
            raise Unknown("reg.exe unavailable")
        records = []
        for hive in ("HKCU", "HKLM"):
            for key in ("Run", "RunOnce"):
                name = f"{hive}\\Software\\Microsoft\\Windows\\CurrentVersion\\{key}"
                result = subprocess.run([reg, "query", name], capture_output=True, timeout=60)
                self.commands.append([reg, "query", name])
                out = text_of(result.stdout)
                self.observations[f"reg query {name}"] = result.stdout + result.stderr
                if result.returncode != 0 and b"unable to find" not in (result.stdout + result.stderr).lower():
                    raise Unknown(f"reg query {name} exited {result.returncode}")
                records += [Record(f"registry:{name}", n, line, True) for n, line in enumerate(out.splitlines(), 1)]
        return records

    def windows_task_records(self):
        root = Path("/mnt/c/Windows/System32/Tasks")
        if not root.exists():
            raise Unknown("Task Scheduler store is not readable")
        return self.listed_file_records([root], lambda line: True)

    def surfaces(self):
        return {"systemd-user-paths": lambda: self.unit_path_records(True),
                "systemd-system-paths": lambda: self.unit_path_records(False),
                "systemd-user-loaded": self.loaded_records, "processes": self.process_records,
                "cron": self.cron_records, "shell-startup": self.shell_records,
                "xdg-autostart": self.autostart_records, "path-executables": self.path_records,
                "alienintent-config": self.config_surface_records, "bootstrap-root": self.bootstrap_records,
                "wsl-boot": self.wsl_records, "windows-startup": self.windows_startup_records,
                "windows-run-keys": self.windows_run_records, "windows-tasks": self.windows_task_records}

    # --- runtime -------------------------------------------------------------------------
    def repository_store(self) -> Path:
        return Path(json.loads(SELF_HOSTING.read_text())["paths"]["repositoryStore"])

    def state_path(self) -> Path:
        return Path(json.loads(SELF_HOSTING.read_text())["paths"]["stateFile"])

    def runtime_pid(self):
        try:
            return self.loaded_units_cache().get(RUNTIME_UNIT, {}).get("main_pid")
        except Unknown:
            return None

    def loaded_units_cache(self):
        if not hasattr(self, "_units"):
            self._units = self.loaded_units()
        return self._units


class FixtureHost(Host):
    """Disposable host for LOCAL controls. Layout under root:
    surfaces/<surface-id>/** (files scanned with the surface's launch rule), units.json,
    proc/<pid>/cmdline, store/ (checkout) and state.json."""
    label = "LOCAL"
    RULES = {"systemd-user-paths": exec_line, "systemd-system-paths": exec_line, "cron": cron_line,
             "shell-startup": code_line, "xdg-autostart": exec_line, "bootstrap-root": code_line,
             "wsl-boot": lambda line: line.strip().startswith("command")}

    def __init__(self, root: Path):
        super().__init__()
        self.root = root

    def surface_records(self, surface):
        base = self.root / "surfaces" / surface
        if not base.exists():
            return []
        if not os.access(base, os.R_OK | os.X_OK):
            raise Unknown(f"unreadable surface directory {base}")
        records = []
        for path in walk_files(base):
            if surface == "alienintent-config":
                records += config_records(path)
            elif surface == "path-executables":
                records.append(Record(str(path), 0, str(path), True))
            else:
                records += file_records(path, self.RULES.get(surface, lambda line: True))
        return records

    def loaded_units(self):
        return json.loads((self.root / "units.json").read_text())

    def loaded_units_cache(self):
        return self.loaded_units()

    def cmdline(self, pid):
        path = self.root / "proc" / str(pid) / "cmdline"
        return path.read_bytes().rstrip(b"\x00").split(b"\x00") if path.exists() else None

    def process_records(self):
        records = []
        for entry in sorted((self.root / "proc").iterdir()):
            argv = self.cmdline(entry.name)
            records.append(Record(f"pid:{entry.name}", 0, " ".join(a.decode() for a in argv), True))
        return records

    def surfaces(self):
        own = {"systemd-user-loaded": self.loaded_records, "processes": self.process_records}
        return {s: own.get(s, lambda s=s: self.surface_records(s)) for s in SURFACES}

    def repository_store(self):
        return self.root / "store"

    def state_path(self):
        return self.root / "state.json"


# --- inventory ------------------------------------------------------------------------------
def inventory(host: Host) -> dict:
    surfaces, found = {}, []
    for surface, collect in host.surfaces().items():
        try:
            records = collect()
            locations = sorted({r.location.split("#")[0] for r in records})
            surfaces[surface] = {"status": "SCANNED", "records_scanned": len(records),
                                 "locations_scanned": len(locations),
                                 "locations_sha256": sha("\n".join(locations).encode())}
            found += references(surface, records)
        except Unknown as error:
            surfaces[surface] = {"status": "UNKNOWN", "reason": str(error)}
    counts = {}
    for ref in found:
        counts[ref["class"]] = counts.get(ref["class"], 0) + 1
        if ref["entry_point"]:
            key = ref["class"] + "_ENTRY_POINT"
            counts[key] = counts.get(key, 0) + 1
    unknown = sorted(s for s, v in surfaces.items() if v["status"] == "UNKNOWN")
    alias_launches = [r for r in found if r["class"] == "ALIAS_LAUNCH"]
    return {"label": host.label, "coverage_method": CONTRACT + "#coverage-method-pinned", "surfaces": surfaces,
            "references": found, "counts": counts, "unknown_surfaces": unknown,
            "alias_launch_count": len(alias_launches),
            "alias_retirement": RETIREMENT_HELD if unknown or alias_launches else RETIREMENT_COMPLETE}


def check_inventory(record: dict) -> list[str]:
    failures = []
    if set(record.get("surfaces", {})) != set(SURFACES):
        failures.append("coverage_incomplete")
    unknown = [s for s, v in record.get("surfaces", {}).items() if v.get("status") != "SCANNED"]
    if unknown:
        failures.append("coverage_unknown")
    alias = [r for r in record.get("references", []) if r["class"] == "ALIAS_LAUNCH"]
    if alias:
        failures.append("alias_launch")
    expected = RETIREMENT_HELD if unknown or alias or "coverage_incomplete" in failures else RETIREMENT_COMPLETE
    if record.get("alias_retirement") != expected:
        failures.append("retirement_claim")
    return failures


# --- migration ------------------------------------------------------------------------------
def plan(record: dict) -> list[dict]:
    steps = []
    for ref in record["references"]:
        if ref["class"] != "ALIAS_LAUNCH":
            continue
        path = ref["location"].split("#")[0]
        file_backed = Path(path).is_file() and ref["line"] > 0
        base = re.split(r"[/\\]", ref["token"])[-1]
        steps.append({"surface": ref["surface"], "path": path, "line": ref["line"], "token": ref["token"],
                      "replacement": ref["token"][: len(ref["token"]) - len(base)] + REPLACEMENT[base],
                      "method": "REWRITE_TOKEN" if file_backed else "NOT_FILE_BACKED_HOLD"})
    return steps


def authorized(authority: Path | None) -> bool:
    return bool(authority) and authority.is_file() and AUTHORITY_TOKEN in authority.read_text()


def migrate(steps: list[dict], authority: Path | None, receipt_dir: Path, apply: bool) -> dict:
    receipt = {"authority": str(authority) if authority else None, "applied": False, "steps": [], "holds": []}
    if not steps:
        receipt["result"] = "NO_MIGRATION_REQUIRED"
        return receipt
    if not authorized(authority):
        receipt |= {"result": "REFUSED", "holds": ["authority"]}
        return receipt
    if not apply:
        receipt |= {"result": "PLANNED_NOT_APPLIED", "holds": ["MIGRATION_PENDING"]}
        return receipt
    objects = receipt_dir / "objects"
    objects.mkdir(parents=True, exist_ok=True)
    for step in steps:
        if step["method"] != "REWRITE_TOKEN":
            receipt["holds"].append("NOT_FILE_BACKED:" + step["path"])
            continue
        path = Path(step["path"])
        original = path.read_bytes()
        (objects / sha(original)).write_bytes(original)
        lines = original.decode().splitlines(keepends=True)
        lines[step["line"] - 1] = lines[step["line"] - 1].replace(step["token"], step["replacement"], 1)
        path.write_bytes("".join(lines).encode())
        receipt["steps"].append(step | {"before_sha256": sha(original), "after_sha256": sha(path.read_bytes()),
                                        "backup": f"objects/{sha(original)}"})
    receipt |= {"applied": True, "result": "MIGRATED" if not receipt["holds"] else "PARTIAL_HOLD"}
    return receipt


def rollback(receipt: dict, receipt_dir: Path, skip: int = 0) -> dict:
    restored = []
    for index, step in enumerate(reversed(receipt["steps"])):
        if index < skip:
            continue
        Path(step["path"]).write_bytes((receipt_dir / step["backup"]).read_bytes())
        restored.append(step["path"])
    return {"restored": restored}


def check_rollback(receipt: dict) -> list[str]:
    firsts = {}
    for step in receipt["steps"]:
        firsts.setdefault(step["path"], step["before_sha256"])
    return ["rollback"] if any(sha(Path(p).read_bytes()) != s for p, s in firsts.items()) else []


# --- readback -------------------------------------------------------------------------------
def readback(host: Host) -> dict:
    units = host.loaded_units_cache()
    store = Path(os.path.realpath(host.repository_store()))
    checked = []
    for name, unit in sorted(units.items()):
        # A unit launches the command when its program or script argument (argv[0] or argv[1])
        # is an entry point; a slug or path merely mentioned in a longer command line does not count.
        kinds = {classify_token(t) for e in unit["exec"] for t in SPLIT.split(e)[:2] if entry_point(t)} - {None}
        if not kinds:
            continue
        argv = [a.decode(errors="replace") for a in (host.cmdline(unit["main_pid"]) or [])] if unit["main_pid"] else []
        argv_kinds = [classify_token(a) for a in argv]
        entry = next((a for a, k in zip(argv, argv_kinds) if k == "CANONICAL"), None)
        real = Path(os.path.realpath(entry)) if entry else None
        body = real.read_text() if real and real.is_file() else ""
        observed = {"unit": name, "declared": sorted(kinds), "active": unit["active"], "sub": unit["sub"],
                    "main_pid": unit["main_pid"], "argv": argv, "entry": entry,
                    "entry_realpath": str(real) if real else None,
                    "entry_sha256": sha(body.encode()) if body else None,
                    "entry_in_repository_store": bool(real) and str(real).startswith(str(store) + os.sep),
                    "entry_reexports_alias": "b-disp" in body}
        observed["pass"] = (kinds == {"CANONICAL"} and unit["active"] == "active" and unit["sub"] == "running"
                            and "ALIAS" not in argv_kinds and entry is not None
                            and observed["entry_in_repository_store"] and not observed["entry_reexports_alias"]
                            and bool(body))
        checked.append(observed)
    alias_file = store / "bin/b-disp.mjs"
    return {"repository_store": str(store), "units": checked,
            "alias_entry_point": {"path": str(alias_file), "present": alias_file.is_file(),
                                  "sha256": sha(alias_file.read_bytes()) if alias_file.is_file() else None},
            "failures": [] if checked and all(u["pass"] for u in checked) else ["readback"]}


# --- preservation ---------------------------------------------------------------------------
def snapshot(host: Host) -> dict:
    state = json.loads(host.state_path().read_text())
    store = host.repository_store()
    identities = {k: sorted(state.get(k) or {}) for k in STATE_KEYS}
    markers = {}
    for relative, pattern in MARKER_SOURCES.items():
        path = store / relative
        lines = [line for line in path.read_text().splitlines() if re.search(pattern, line)] if path.exists() else []
        markers[relative] = {"lines": len(lines), "sha256": sha("\n".join(lines).encode())}
    return {"taken_at": dt.datetime.now(dt.timezone.utc).isoformat(), "state_path": str(host.state_path()),
            "identities": identities,
            "identity_digests": {k: {"count": len(v), "sha256": sha("\n".join(v).encode())}
                                 for k, v in identities.items()},
            "markers": markers}


def check_preservation(before: dict, after: dict) -> dict:
    missing = {k: sorted(set(v) - set(after["identities"].get(k, []))) for k, v in before["identities"].items()}
    missing = {k: v for k, v in missing.items() if v}
    # A lane leaves `active` when its invocation ends; that is lifecycle, not loss, if its
    # resource identity and diagnostics lane persist.
    if "active" in missing:
        persisted = set(after["identities"].get("diagnostics", []))
        missing["active"] = [lane for lane in missing["active"] if lane not in persisted]
        if not missing["active"]:
            del missing["active"]
    markers = before["markers"] == after["markers"] and all(m["lines"] for m in before["markers"].values())
    added = {k: len(set(after["identities"].get(k, [])) - set(v)) for k, v in before["identities"].items()}
    return {"missing": missing, "added": added, "markers_identical": markers,
            "failures": ["preservation"] if missing or not markers else []}


# --- controls -------------------------------------------------------------------------------
CANONICAL_UNIT = "[Service]\nExecStart=/usr/bin/node {store}/bin/alienintent.mjs --config /c.json\n"


def build_fixture(root: Path) -> FixtureHost:
    store = root / "store"
    (store / "bin").mkdir(parents=True)
    (store / "bin/alienintent.mjs").write_text("#!/usr/bin/env node\nimport './../src/runtime/dispatcher.mjs';\n")
    (store / "bin/b-disp.mjs").write_text("#!/usr/bin/env node\nimport \"./alienintent.mjs\";\n")
    for relative, text in {"src/github/authority.mjs": 'const M = "<!-- B-DISP: INVOCATION=x RESULT=y -->";\n',
                           "src/runtime/dispatcher.mjs": "// B-DISP marker text\n",
                           "src/runtime/worktree-manager.mjs": "branch: `b-disp/${id}`\n"}.items():
        (store / relative).parent.mkdir(parents=True, exist_ok=True)
        (store / relative).write_text(text)
    surfaces = root / "surfaces"
    for surface in SURFACES:
        (surfaces / surface).mkdir(parents=True)
    (surfaces / "systemd-user-paths/alienintent.service").write_text(CANONICAL_UNIT.format(store=store))
    (surfaces / "systemd-user-paths/other.service").write_text(
        "[Service]\nWorkingDirectory=/w/b-disp-morty\nExecStart=/usr/bin/true\n")
    (surfaces / "cron/crontab").write_text("0 3 * * * /usr/bin/python3 /x/sync.py\n")
    (surfaces / "alienintent-config/self-hosting.json").write_text(json.dumps(
        {"executables": {"node": "/usr/bin/node"}, "workers": {"PRODUCER": {"branchPrefix": "b-disp/"}}}))
    (surfaces / "bootstrap-root/probe.sh").write_text('branch="b-disp/credential-probe"\n')
    (root / "proc/100").mkdir(parents=True)
    (root / "proc/100/cmdline").write_bytes(
        b"\x00".join([b"/usr/bin/node", str(store / "bin/alienintent.mjs").encode(), b"--config", b"/c.json"]))
    (root / "units.json").write_text(json.dumps({"alienintent.service": {
        "exec": [f"/usr/bin/node {store}/bin/alienintent.mjs --config /c.json"],
        "active": "active", "sub": "running", "main_pid": 100}}))
    (root / "state.json").write_text(json.dumps({
        "resources": {"o/r#1:PRODUCER:aaaa": {"branch": "b-disp/aaaa"}}, "closures": {"o/r#1:PRODUCER:aaaa": {}},
        "founderExceptions": {}, "deliveries": {"d-1": {}}, "diagnostics": {"o/r#1:PRODUCER": {}},
        "active": {"o/r#1:PRODUCER": {}}}))
    (root / "authority.md").write_text(f"Founder decision: {AUTHORITY_TOKEN} disposed for this BIU.\n")
    return FixtureHost(root)


def gate(host: FixtureHost, before=None, record=None) -> set[str]:
    record = record if record is not None else inventory(host)
    failures = set(check_inventory(record)) | set(readback(host)["failures"])
    if before is not None:
        failures |= set(check_preservation(before, snapshot(host))["failures"])
    return failures


def run_controls() -> list[dict]:
    results = []

    def control(name, fault_class, expected, fault, restore, evaluate=None):
        with tempfile.TemporaryDirectory(prefix="fx-b7-") as temporary:
            host = build_fixture(Path(temporary))
            evaluate = evaluate or (lambda h, ctx: gate(h))
            context = {}
            intact = evaluate(host, context)
            applications = fault(host, context)
            faulted = evaluate(host, context)
            restore(host, context)
            restored = evaluate(host, context)
            results.append({"control": name, "failure_class": fault_class, "application_count": applications,
                            "intact": sorted(intact), "fault": sorted(faulted), "restored": sorted(restored),
                            "expected": expected,
                            "discriminating": applications == 1 and not intact and not restored
                            and set(expected) <= faulted})

    alias_unit = "[Service]\nExecStart=/usr/bin/node /opt/ai/bin/b-disp.mjs --config /c.json\n"

    def inject_alias(host, ctx):
        (host.root / "surfaces/systemd-user-paths/legacy.service").write_text(alias_unit)
        return 1
    control("alias_launch_injected", "unmigrated alias launch hidden in an installation surface",
            ["alias_launch"], inject_alias,
            lambda h, c: (h.root / "surfaces/systemd-user-paths/legacy.service").unlink(),
            lambda h, c: gate(h) | ({"retirement_not_held"} if inventory(h)["alias_retirement"] != RETIREMENT_HELD
                                    and inventory(h)["alias_launch_count"] else set()))

    def unreadable(host, ctx):
        os.chmod(host.root / "surfaces/cron", 0)
        return 1

    def held(host, ctx):
        record = inventory(host)
        extra = {"retirement_not_held"} if record["unknown_surfaces"] and record["alias_retirement"] != RETIREMENT_HELD else set()
        return gate(host, record=record) | extra
    control("surface_unreadable", "unknown installation coverage must hold alias retirement", ["coverage_unknown"],
            unreadable, lambda h, c: os.chmod(h.root / "surfaces/cron", 0o755), held)

    def drop_surface(host, ctx):
        ctx["drop"] = True
        return 1

    def dropped(host, ctx):
        record = inventory(host)
        if ctx.get("drop"):
            record["surfaces"].pop("windows-tasks")
        return gate(host, record=record)
    control("surface_dropped", "enumeration without a complete coverage method", ["coverage_incomplete"],
            drop_surface, lambda h, c: c.pop("drop"), dropped)

    def alias_process(host, ctx):
        path = host.root / "proc/100/cmdline"
        ctx["cmdline"] = path.read_bytes()
        path.write_bytes(ctx["cmdline"].replace(b"alienintent.mjs", b"b-disp.mjs"))
        return 1
    control("readback_alias_process", "canonical launch not confirmed by actual readback", ["readback"],
            alias_process, lambda h, c: (h.root / "proc/100/cmdline").write_bytes(c["cmdline"]))

    def preserved(host, ctx):
        ctx.setdefault("before", snapshot(host))
        return gate(host, before=ctx["before"])

    def drop_identity(host, ctx):
        path = host.state_path()
        ctx["state"] = path.read_text()
        state = json.loads(ctx["state"])
        state["resources"] = {k.replace("PRODUCER", "producer"): v for k, v in state["resources"].items()}
        path.write_text(json.dumps(state))
        return 1
    control("identity_dropped", "persisted lane/resource identity renamed or dropped", ["preservation"],
            drop_identity, lambda h, c: h.state_path().write_text(c["state"]), preserved)

    def alter_marker(host, ctx):
        path = host.repository_store() / "src/github/authority.mjs"
        ctx["marker"] = path.read_text()
        path.write_text(ctx["marker"].replace("B-DISP", "ALIENINTENT"))
        return 1
    control("marker_altered", "B-DISP protocol marker renamed", ["preservation"], alter_marker,
            lambda h, c: (h.repository_store() / "src/github/authority.mjs").write_text(c["marker"]), preserved)

    def claim(host, ctx):
        ctx["claim"] = True
        return 1

    def claimed(host, ctx):
        record = inventory(host)
        if ctx.get("claim"):
            record["alias_retirement"] = "RETIRED"
        return gate(host, record=record)
    control("retirement_claimed", "alias retirement claimed from a candidate or local result",
            ["retirement_claim"], claim, lambda h, c: c.pop("claim"), claimed)

    def migration_evaluate(host, ctx):
        (host.root / "surfaces/systemd-user-paths/legacy.service").write_text(alias_unit)
        receipts = host.root / f"receipt-{len(ctx.get('runs', []))}"
        authority = None if ctx.get("no_authority") else host.root / "authority.md"
        receipt = migrate(plan(inventory(host)), authority, receipts, apply=True)
        failures = set(receipt["holds"]) | set(check_inventory(inventory(host)))
        if receipt["applied"]:
            rollback(receipt, receipts)
            failures |= set(check_rollback(receipt))
        (host.root / "surfaces/systemd-user-paths/legacy.service").unlink()
        ctx.setdefault("runs", []).append(receipt["result"])
        return failures
    control("migration_without_authority", "migration without installation authority", ["authority"],
            lambda h, c: c.update(no_authority=True) or 1, lambda h, c: c.pop("no_authority"), migration_evaluate)

    def rollback_evaluate(host, ctx):
        unit = host.root / "surfaces/systemd-user-paths/legacy.service"
        unit.write_text(alias_unit)
        receipts = host.root / f"rb-{len(ctx.get('runs', []))}"
        receipt = migrate(plan(inventory(host)), host.root / "authority.md", receipts, apply=True)
        migrated = check_inventory(inventory(host))
        rollback(receipt, receipts, skip=1 if ctx.get("skip") else 0)
        failures = set(check_rollback(receipt)) | set(migrated)
        ctx.setdefault("runs", []).append(receipt["result"])
        unit.unlink()
        return failures
    control("rollback_incomplete", "rollback that does not restore exact original bytes", ["rollback"],
            lambda h, c: c.update(skip=True) or 1, lambda h, c: c.pop("skip"), rollback_evaluate)
    return results


# --- evidence run ---------------------------------------------------------------------------
def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def execute(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    return {"argv": argv, "exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(output: Path, invocation: str, authority: Path, apply: bool) -> int:
    output.mkdir(parents=True, exist_ok=False)
    objects = output / "objects"
    objects.mkdir()

    def retain(data: bytes) -> str:
        digest = sha(data)
        (objects / digest).write_bytes(data)
        return f"objects/{digest}"

    host = Host()
    holds = []
    before = snapshot(host)
    record = inventory(host)
    inventory_failures = check_inventory(record)
    steps = plan(record)
    receipt = migrate(steps, authority, output / "migration", apply)
    holds += receipt["holds"]
    if receipt["applied"]:
        record = inventory(host)
        inventory_failures = check_inventory(record)
    back = readback(host)
    after = snapshot(host)
    preservation = check_preservation(before, after)
    controls = run_controls()
    predecessor = [execute([sys.executable, "-B", "tools/evidence/bootstrap_custody_manifest.py", "check",
                            PREDECESSOR_MANIFEST]),
                   execute([sys.executable, "-B", "tools/evidence/bootstrap_custody_manifest.py", "check",
                            PREDECESSOR_MANIFEST, "--root", str(HOME / ".local/share/alienintent-bootstrap")]),
                   execute([sys.executable, "-m", "pytest", "-q", "tools/evidence/test_bootstrap_custody_manifest.py"])]
    focused = execute([sys.executable, "-m", "pytest", "-q", "tools/live/test_installation_launch.py"])
    holds += [f"INVENTORY:{f}" for f in inventory_failures] + [f"READBACK:{f}" for f in back["failures"]]
    holds += [f"PRESERVATION:{f}" for f in preservation["failures"]]
    holds += [f"CONTROL_NOT_DISCRIMINATING:{c['control']}" for c in controls if not c["discriminating"]]
    if predecessor[0]["exit_status"] or predecessor[2]["exit_status"]:
        holds.append("PREDECESSOR_CHECK_FAILED")
    if focused["exit_status"]:
        holds.append("FOCUSED_TESTS_FAILED")
    dirty = git("status", "--porcelain", "--", "tools/live/installation_launch.py",
                "tools/live/test_installation_launch.py", CONTRACT)
    if dirty:
        holds.append("SOURCE_UNCOMMITTED")
    observations = {name: retain(data) for name, data in sorted(host.observations.items())}
    commands = [{"label": label, "argv": c["argv"], "exit_status": c["exit_status"],
                 "stdout": retain(c["stdout"]), "stderr": retain(c["stderr"])}
                for label, c in zip(("fx-b0-check", "fx-b0-live-rediscovery", "fx-b0-tests", "fx-b7-tests"),
                                    predecessor + [focused])]
    probes = {
        "B7-01 coverage": "PASS" if "coverage_incomplete" not in inventory_failures
                          and "coverage_unknown" not in inventory_failures else "HOLD",
        "B7-02 enumeration": "PASS" if record["references"] is not None else "HOLD",
        "B7-03 migration": "PASS" if receipt["result"] in ("NO_MIGRATION_REQUIRED", "MIGRATED") else "HOLD",
        "B7-04 readback": "PASS" if not back["failures"] else "FAIL",
        "B7-05 preservation": "PASS" if not preservation["failures"] else "FAIL",
        "B7-06 retirement hold": "PASS" if "retirement_claim" not in inventory_failures else "FAIL",
        "B7-07 predecessor": "PASS" if not (predecessor[0]["exit_status"] or predecessor[2]["exit_status"])
                             else "FAIL",
    }
    execution = {"fixture": "FX-B7", "biu": "WO-220510", "issue": 129, "label": "OPERATIONAL",
                 "target": {"host": os.uname().nodename, "unit": RUNTIME_UNIT,
                            "repository_store": str(host.repository_store()),
                            "profile": str(SELF_HOSTING)},
                 "invocation": invocation, "contract": CONTRACT, "authority": str(authority),
                 "source_candidate": {"commit": git("rev-parse", "HEAD"),
                                      "files": {p: sha((ROOT / p).read_bytes()) for p in (
                                          CONTRACT, "tools/live/installation_launch.py",
                                          "tools/live/test_installation_launch.py")}},
                 "installed_checkout_head": subprocess.run(["git", "-C", str(host.repository_store()), "rev-parse",
                                                            "HEAD"], capture_output=True, text=True).stdout.strip(),
                 "host_commands": host.commands, "observations": observations, "commands": commands,
                 "probes": probes, "holds": holds, "alias_retirement": record["alias_retirement"],
                 "exit_status": 1 if holds else 0,
                 "telemetry": {"tokens": "UNKNOWN (not exposed to the producer)", "cost": "UNKNOWN"},
                 "non_claims": ["No alias retirement, release or live operation is authorized or performed.",
                                "LOCAL controls prove discrimination only, not operational acceptance.",
                                "Operational acceptance requires the independent VERIFIER verdict."]}
    for name, value in (("execution-record.json", execution), ("inventory.json", record),
                        ("migration-receipt.json", receipt | {"plan": steps}), ("readback.json", back),
                        ("preservation-before.json", before), ("preservation-after.json", after),
                        ("preservation-check.json", preservation), ("controls.json", controls)):
        write_json(output / name, value)
    manifest = {str(p.relative_to(output)): "sha256:" + sha(p.read_bytes())
                for p in sorted(output.rglob("*")) if p.is_file()}
    write_json(output / "digest-manifest.json", manifest)
    print(json.dumps({"exit_status": execution["exit_status"], "holds": holds, "probes": probes,
                      "alias_retirement": record["alias_retirement"], "counts": record["counts"],
                      "migration": receipt["result"],
                      "controls": {c["control"]: c["discriminating"] for c in controls}}, indent=2))
    return execution["exit_status"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--invocation", required=True)
    run_parser.add_argument("--authority", type=Path, required=True)
    run_parser.add_argument("--apply", action="store_true")
    controls_parser = sub.add_parser("controls")
    controls_parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    if arguments.command == "run":
        return run(arguments.output, arguments.invocation, arguments.authority, arguments.apply)
    results = run_controls()
    write_json(arguments.output, results)
    return 0 if all(c["discriminating"] for c in results) else 1


if __name__ == "__main__":
    sys.exit(main())
