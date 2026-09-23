"""Derived requirements inventory; syntax and source observations never grant authority."""
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import re


class InventoryHold(ValueError):
    """Input cannot safely be interpreted as a requirements inventory."""


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value: object) -> str:
    return sha256(canonical(value).encode()).hexdigest()


REQUIREMENT = r"[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-REQ-[0-9]{3,}(?:[A-Z])?"
ACCEPTANCE = REQUIREMENT + r"-AC-[0-9]{2,}"


@dataclass(frozen=True)
class Provenance:
    external_source: str
    external_identity: str
    external_revision: str
    source_link: str
    ingestion_timestamp: str
    authority_status: str
    synchronization: str

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip() for v in asdict(self).values()):
            raise InventoryHold("MISSING_PROVENANCE")


@dataclass(frozen=True)
class DefinitionSpan:
    start: int
    end: int
    form: str


@dataclass(frozen=True)
class SourceSpec:
    path: str
    revision: str
    digest: str
    definitions: tuple[DefinitionSpan, ...]
    references: tuple[tuple[int, int], ...]
    namespaces: tuple[str, ...]
    provenance: Provenance
    authority_revision: str
    role: str
    satisfaction_links: tuple[str, ...] = ()
    access_label: str = "private"
    adapter_version: str = "git-prose-v1"
    contract_version: str = "SF-REQ-011/grammar-2"

    def __post_init__(self) -> None:
        if (not self.path or not self.revision or not re.fullmatch(r"[0-9a-f]{64}", self.digest)
                or not self.authority_revision or not self.role or not self.namespaces
                or self.access_label not in {"public", "private"}
                or self.provenance.external_revision != self.revision):
            raise InventoryHold("INVALID_SOURCE_SPEC")
        for spans in (tuple((s.start, s.end) for s in self.definitions), self.references):
            if any(type(a) is not int or type(b) is not int or a < 1 or b < a for a, b in spans):
                raise InventoryHold("INVALID_SPANS")
        if any(s.form not in {"factory_plan_heading", "canonical_requirement", "recorded_as"} for s in self.definitions):
            raise InventoryHold("UNSUPPORTED_FORM")
        for field in ("definitions", "references", "namespaces", "satisfaction_links"):
            value = getattr(self, field)
            if not isinstance(value, tuple):
                raise InventoryHold("MUTABLE_SOURCE_SPEC")


@dataclass(frozen=True)
class Manifest:
    project: str
    entries: tuple[SourceSpec, ...]
    name: str
    version: int = 1

    def __post_init__(self) -> None:
        if not self.project or not self.name or self.version != 1 or not isinstance(self.entries, tuple):
            raise InventoryHold("INVALID_MANIFEST")
        if len({(e.path, e.revision) for e in self.entries}) != len(self.entries):
            raise InventoryHold("DUPLICATE_SOURCE")


@dataclass(frozen=True)
class SourceRecord:
    spec: SourceSpec
    text: str | None
    issue: str | None = None


@dataclass(frozen=True)
class Token:
    raw_token: str
    kind: str
    operands: tuple[str, ...] = ()
    parent_id: str | None = None
    reason: str | None = None
    path: str = ""
    line: int = 0
    column: int = 0
    grammar_revision: int = 2


@dataclass(frozen=True)
class Issue:
    path: str
    line: int
    raw_token: str
    reason: str
    grammar_revision: int = 2
    status: str = "UNVERIFIED"


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    revision: str
    authority_revision: str
    semantic: str
    role: str
    dependencies: tuple[str, ...]
    satisfaction_links: tuple[str, ...]
    provenance: tuple[Provenance, ...]
    source_paths: tuple[str, ...]
    source_spans: tuple[tuple[str, int, int], ...]
    retired: bool
    eligible: bool


@dataclass(frozen=True)
class Resolution:
    status: str
    definition: Requirement | None = None


@dataclass(frozen=True)
class InventorySnapshot:
    project: str
    source_manifest_digest: str
    current: tuple[Requirement, ...]
    history: tuple[Requirement, ...]
    tokens: tuple[Token, ...]
    identifier_issues: tuple[Issue, ...]
    source_issues: tuple[Issue, ...]
    definition_locators: tuple[tuple[str, int, str, str], ...]
    referenced_ids: tuple[str, ...]
    defined_ids: tuple[str, ...]
    unresolved: tuple[str, ...]
    conflicts: tuple[str, ...]
    retired: tuple[str, ...]
    stale_links: tuple[str, ...]
    prior_snapshot: str | None
    schema_version: int = 1

    @property
    def digest(self) -> str:
        return digest(asdict(self))

    @property
    def status(self) -> str:
        return "UNVERIFIED" if self.source_issues or self.identifier_issues else "CONFLICT" if self.conflicts else "ASSEMBLED"


def classify(raw: str, namespaces: tuple[str, ...]) -> Token:
    kind, operands, parent = "IdentifierShapeConflict", (), None
    if re.fullmatch(ACCEPTANCE, raw):
        kind, parent = "AcceptanceCriterionId", raw.rsplit("-AC-", 1)[0]
    elif re.fullmatch(REQUIREMENT, raw):
        kind, operands = "RequirementIdentifier", (raw,)
    else:
        parts = raw.split("/")
        if len(parts) > 1 and re.fullmatch(REQUIREMENT, parts[0]):
            prefix = parts[0].rsplit("-REQ-", 1)[0] + "-REQ-"
            expanded = tuple(p if "-REQ-" in p else prefix+p for p in parts)
            if all(re.fullmatch(REQUIREMENT, p) for p in expanded):
                kind, operands = "CompoundReference", expanded
        if kind == "IdentifierShapeConflict":
            match = re.fullmatch(r"("+REQUIREMENT+r")(?:\.\.|–|-)("+REQUIREMENT+r"|[0-9]{3,})", raw)
            if match:
                start, end = match.groups()
                prefix, number = start.rsplit("-REQ-", 1)
                end = end if "-REQ-" in end else prefix+"-REQ-"+end
                end_prefix, end_number = end.rsplit("-REQ-", 1)
                if (prefix == end_prefix and number.isascii() and number.isdigit() and end_number.isascii()
                        and end_number.isdigit() and len(number) == len(end_number) and int(number) <= int(end_number)):
                    kind, operands = "CompoundReference", (start, end)
        if kind == "IdentifierShapeConflict":
            match = re.fullmatch(r"("+REQUIREMENT+r")[’']s", raw)
            if match:
                kind, operands = "PossessiveReference", (match[1],)
    reason = "UNRECOGNIZED_REQUIREMENT_ID" if kind == "IdentifierShapeConflict" else None
    ids = operands or ((parent,) if parent else ())
    if any(i.rsplit("-REQ-", 1)[0] not in namespaces for i in ids):
        reason = "UNAUTHORIZED_REQUIREMENT_NAMESPACE"
    return Token(raw, kind, operands, parent, reason)


def _mask_markdown(text: str, preserve_columns: bool = True) -> str:
    return re.sub(r"(?<![A-Za-z0-9])(\*\*|__|`|\*)([\s\S]+?)\1(?![A-Za-z0-9])",
                  lambda m: " "*len(m[1])+m[2]+" "*len(m[1]) if preserve_columns else m[2], text)


def _mask_destinations(line: str) -> str:
    """Mask complete inline destinations, balancing unescaped parentheses."""
    masked = list(line)
    start = 0
    while (start := line.find("](", start)) != -1:
        end, depth = start + 2, 1
        while end < len(line) and depth:
            if line[end] == "\\":
                end += 2  # An escaped parenthesis cannot open or close a destination.
                continue
            if line[end] == "(":
                depth += 1
            elif line[end] == ")":
                depth -= 1
            end += 1
        if depth == 0:
            masked[start+1:end] = " " * (end-start-1)
            start = end
        else:
            start += 2  # Incomplete syntax must not hide the remaining prose.
    return "".join(masked)


def _reference_tokens(line: str, namespaces: tuple[str, ...]) -> tuple[Token, ...]:
    # Hide only Markdown destinations; preserve source columns and complete labels.
    line = _mask_destinations(line)
    line = re.sub(r"(?<![A-Za-z0-9])(\*\*|__|`|\*)(.+?)\1(?![A-Za-z0-9])",
                  lambda m: " "*len(m[1])+m[2]+" "*len(m[1]), line)
    result = []
    for match in re.finditer(r"[^\s\[\]<>\"(){};,!?]+", line):
        raw = match[0].strip(".:|“”")
        if "-REQ-" in raw:
            t = classify(raw, namespaces)
            result.append(Token(t.raw_token, t.kind, t.operands, t.parent_id, t.reason, column=match.start()+1))
    return tuple(result)


def _unmark(text: str) -> str:
    text = text.strip()
    for marker in ("**", "__", "`", "*"):
        if text.startswith(marker) and text.endswith(marker) and len(text) >= 2*len(marker):
            return text[len(marker):-len(marker)].strip()
    return text


def _definition_slot(line: str, form: str) -> str | None:
    if form == "factory_plan_heading":
        match = re.match(r"^#{1,6}[ \t](.*)$", line)
        return _unmark(re.split(r"\s+[—–]\s+", match[1], maxsplit=1)[0]) if match else None
    if form == "canonical_requirement":
        match = re.match(r"^Canonical requirement:\s*(.*?)\s*$", line)
        return _unmark(match[1].rstrip(".")) if match else None
    if form == "recorded_as":
        match = re.match(r"^Recorded as\s+(.*?)(?:\s+[—–]\s+.*|:\s*.*)$", line)
        return _unmark(match[1]+("**" if match[1].startswith("**") and not match[1].endswith("**") and "**:" in line else "")) if match else None
    return None


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"(?m)^#{1,6}\s+", "", _mask_markdown(text, False)).split())


def assemble(project: str, records: tuple[SourceRecord, ...], previous: InventorySnapshot | None = None) -> InventorySnapshot:
    if not project or (previous and previous.project != project):
        raise InventoryHold("PROJECT_MISMATCH")
    specs = tuple(sorted((r.spec for r in records), key=lambda s: (s.path, s.revision)))
    if len({(s.path, s.revision) for s in specs}) != len(specs):
        raise InventoryHold("DUPLICATE_SOURCE")
    tokens, issues, source_issues, definitions, locators = [], [], [], [], []
    for record in sorted(records, key=lambda r: (r.spec.path, r.spec.revision)):
        spec = record.spec
        source_reason = record.issue
        if record.text is None:
            source_reason = source_reason or "SOURCE_UNAVAILABLE"
        elif sha256(record.text.encode()).hexdigest() != spec.digest:
            source_reason = "SOURCE_DIGEST_MISMATCH"
        if source_reason:
            source_issues.append(Issue(spec.path, 0, "", source_reason))
            continue
        lines = record.text.splitlines()
        if any(end > len(lines) for _, end in spec.references) or any(s.end > len(lines) for s in spec.definitions):
            source_issues.append(Issue(spec.path, 0, "", "SOURCE_SPAN_UNAVAILABLE"))
            continue
        source_tokens = []
        numbers = sorted({n for start, end in (*spec.references, *((s.start, s.end) for s in spec.definitions))
                          for n in range(start, end+1)})
        reference_lines = list(lines)
        # Pair presentation markers only inside contiguous manifested spans.
        runs: list[list[int]] = []
        for number in numbers:
            if not runs or number != runs[-1][-1]+1:
                runs.append([])
            runs[-1].append(number)
        for run in runs:
            masked = _mask_markdown("\n".join(lines[n-1] for n in run)).splitlines()
            for number, line in zip(run, masked):
                reference_lines[number-1] = line
        for number in numbers:
            for t in _reference_tokens(reference_lines[number-1], spec.namespaces):
                token = Token(t.raw_token, t.kind, t.operands, t.parent_id, t.reason, spec.path, number, t.column)
                tokens.append(token)
                source_tokens.append(token)
                if token.reason:
                    issues.append(Issue(spec.path, number, token.raw_token, token.reason))
        for span in spec.definitions:
            raw = _definition_slot(lines[span.start-1], span.form)
            if raw is None:
                issues.append(Issue(spec.path, span.start, lines[span.start-1], "DEFINITION_FORM_MISMATCH"))
                continue
            token = classify(raw, spec.namespaces)
            reason = ("MISSING_REQUIREMENT_ID" if not raw else "AMBIGUOUS_REQUIREMENT_ID" if len(raw.split()) > 1
                      else token.reason or ("WRONG_IDENTIFIER_KIND" if token.kind != "RequirementIdentifier" else None))
            if reason:
                issues.append(Issue(spec.path, span.start, raw, reason))
                continue
            locators.append((spec.path, span.start, span.form, raw))
            # The slot's label is presentation. Body and authority carry semantic identity.
            body = "\n".join(lines[span.start:span.end])
            if span.form == "recorded_as" and ":" in lines[span.start-1]:
                body = lines[span.start-1].split(":", 1)[1] + "\n" + body
            semantic = _normalize(body)
            retired = bool(re.search(r"[—–]\s*retired\b", lines[span.start-1], re.I)
                           or re.match(r"(?:Status:\s*)?retired\b", semantic, re.I))
            dependencies = tuple(sorted({operand for t in source_tokens if span.start <= t.line <= span.end and not t.reason
                                         for operand in t.operands if operand != raw}))
            links = tuple(sorted(set(spec.satisfaction_links)))
            fields = (raw, spec.authority_revision, semantic, spec.role, dependencies, links, retired)
            definitions.append(Requirement(raw, digest(fields), spec.authority_revision, semantic, spec.role,
                                           dependencies, links, (spec.provenance,), (spec.path,), ((spec.path, span.start, span.end),), retired,
                                           spec.provenance.authority_status == "approved" and spec.role == "Requirement"))
    merged: dict[tuple[str, str], Requirement] = {}
    for d in definitions:
        key = (d.requirement_id, d.revision)
        if key in merged:
            old = merged[key]
            d = Requirement(d.requirement_id, d.revision, d.authority_revision, d.semantic, d.role, d.dependencies,
                            d.satisfaction_links, tuple(sorted(set(old.provenance+d.provenance), key=canonical_provenance)),
                            tuple(sorted(set(old.source_paths+d.source_paths))), tuple(sorted(set(old.source_spans+d.source_spans))), d.retired, old.eligible and d.eligible)
        merged[key] = d
    current = tuple(merged[k] for k in sorted(merged))
    conflicts = {d.requirement_id for d in current if sum(x.requirement_id == d.requirement_id for x in current) > 1}
    retired = {d.requirement_id for d in current if d.retired} | (set(previous.retired) if previous else set())
    conflicts.update(d.requirement_id for d in current if d.requirement_id in retired and not d.retired)
    history = {(d.requirement_id, d.revision): d for d in (previous.history if previous else ())}
    for key, d in merged.items():
        if key in history:
            old = history[key]
            d = replace(d, provenance=tuple(sorted(set(old.provenance+d.provenance), key=canonical_provenance)),
                        source_paths=tuple(sorted(set(old.source_paths+d.source_paths))),
                        source_spans=tuple(sorted(set(old.source_spans+d.source_spans))))
        history[key] = d
    stale = set(previous.stale_links if previous else ())
    if previous:
        ids = {d.requirement_id for d in previous.current+current}
        changed = {i for i in ids if {d.revision for d in previous.current if d.requirement_id == i}
                   != {d.revision for d in current if d.requirement_id == i}}
        for d in previous.current:
            if d.requirement_id in changed or set(d.dependencies) & changed:
                stale.update(d.satisfaction_links)
    references = tuple(sorted({o for t in tokens if not t.reason for o in t.operands}))
    defined = tuple(sorted({d.requirement_id for d in current}))
    return InventorySnapshot(project, digest([asdict(s) for s in specs]), current,
                             tuple(history[k] for k in sorted(history)), tuple(tokens), tuple(issues), tuple(source_issues),
                             tuple(sorted(locators)), references, defined, tuple(sorted(set(references)-set(defined))),
                             tuple(sorted(conflicts)), tuple(sorted(retired)), tuple(sorted(stale)), previous.digest if previous else None)


def canonical_provenance(value: Provenance) -> str:
    return canonical(asdict(value))


def resolve(snapshot: InventorySnapshot, requirement_id: str) -> Resolution:
    if requirement_id in snapshot.conflicts:
        return Resolution("CONFLICT")
    if requirement_id in snapshot.retired:
        return Resolution("RETIRED")
    definitions = [d for d in snapshot.current if d.requirement_id == requirement_id]
    if not definitions:
        return Resolution("UNRESOLVED")
    d = definitions[0]
    if d.retired:
        return Resolution("RETIRED")
    if not d.eligible or any(i.path == path and (i.line == 0 or start <= i.line <= end)
                             for i in snapshot.identifier_issues+snapshot.source_issues for path, start, end in d.source_spans):
        return Resolution("UNVERIFIED")
    return Resolution("ELIGIBLE_FOR_PREPARATION", d)
