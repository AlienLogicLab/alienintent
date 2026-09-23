"""Read inert, size-bounded Git blobs from an explicit manifest, never crawl."""
from pathlib import Path, PurePosixPath
import json
import re
import subprocess

from alienintent.context_assembly.domain.inventory import (Manifest, SourceSpec, SourceRecord, DefinitionSpan,
                                                          Provenance, InventoryHold)
from alienintent.context_assembly.ports.requirement_source import RequirementSource


class GitRequirementSource(RequirementSource):
    def __init__(self, root: Path, max_bytes: int = 2_000_000) -> None:
        self.root, self.max_bytes = root.resolve(), max_bytes

    def read(self, manifest: Manifest) -> tuple[SourceRecord, ...]:
        records = []
        for spec in manifest.entries:
            path = PurePosixPath(spec.path)
            if (path.is_absolute() or ".." in path.parts or "\\" in spec.path or path.as_posix() != spec.path
                    or not re.fullmatch(r"[0-9a-f]{40}", spec.revision)):
                records.append(SourceRecord(spec, None, "SOURCE_REJECTED"))
                continue
            obj = spec.revision+":"+spec.path
            try:
                size = subprocess.run(["git", "cat-file", "-s", obj], cwd=self.root, capture_output=True, timeout=10, check=True)
                if int(size.stdout) > self.max_bytes:
                    records.append(SourceRecord(spec, None, "SOURCE_OVERSIZED"))
                    continue
                blob = subprocess.run(["git", "cat-file", "blob", obj], cwd=self.root, capture_output=True, timeout=10, check=True)
                text = blob.stdout.decode("utf-8")
                records.append(SourceRecord(spec, text))
            except (OSError, ValueError, subprocess.SubprocessError):
                records.append(SourceRecord(spec, None, "SOURCE_UNAVAILABLE"))
        return tuple(records)


def historical_manifest(contract_path: Path) -> Manifest:
    """Translate the historical regression manifest without inventing source authority.

    Source line lengths/spans are derived from the pinned blob. IDs in definition_slots
    are deliberately not consumed: the parser must discover them independently.
    """
    data = json.loads(contract_path.read_text())["contracts"][0]["identifier_contract"]["historical_fixture_manifest"]
    root = contract_path.resolve().parents[2]
    entries = []
    for entry in data["entries"]:
        result = subprocess.run(["git", "show", data["revision"]+":"+entry["path"]], cwd=root,
                                capture_output=True, timeout=10, check=True)
        lines = result.stdout.decode().splitlines()
        spans = []
        for slot in entry["definition_slots"]:
            start = slot["line"]
            following = next((n for n in range(start+1, len(lines)+1) if re.match(r"^#{1,6}\s", lines[n-1])), len(lines)+1)
            end = following-1 if slot["form"] == "factory_plan_heading" else len(lines)
            spans.append(DefinitionSpan(start, end, slot["form"]))
        provenance = Provenance("git", entry["path"], data["revision"], "git:"+data["revision"]+":"+entry["path"],
                                "2026-09-23T00:00:00Z", "historical-observation", "no-projection; regression-only")
        entries.append(SourceSpec(entry["path"], data["revision"], entry["sha256"], tuple(spans),
                                  ((1, len(lines)),), ("SF",), provenance, data["revision"], "Observation"))
    if len(entries) != 17:
        raise InventoryHold("HISTORICAL_MANIFEST_SHAPE")
    return Manifest("AlienLogicLab/alienintent", tuple(entries), data["name"])
