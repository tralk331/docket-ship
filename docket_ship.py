#!/usr/bin/env python3
"""docket-ship - keeps a project's specs, decisions and tickets consistent.

One file, standard library only, Python 3.8+. The format it checks is defined
in CONVENTIONS.md next to this script; `docket-ship init` copies that file into a
project so any agent can read the rules without the tool installed.
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

VERSION = "0.1.0"
TOOL_DIR = Path(__file__).resolve().parent
CONVENTIONS = "CONVENTIONS.md"
CONFIG = "docket-ship.cfg"
INDEX = "INDEX.md"

# type -> folder under docs/
FOLDERS = {"spec": "spec", "decision": "decisions", "ticket": "work"}
STATUSES = {
    "spec": ("draft", "active", "retired"),
    "decision": ("proposed", "accepted", "rejected", "superseded"),
    "ticket": ("open", "doing", "done", "dropped"),
}
OPEN_TICKET = ("open", "doing")
REQUIRED = {
    "spec": ("id", "type", "title", "status", "summary"),
    "decision": ("id", "type", "title", "status", "date", "summary"),
    "ticket": ("id", "type", "title", "status", "summary"),
}
KNOWN = {
    "spec": set(REQUIRED["spec"]),
    "decision": set(REQUIRED["decision"]) | {"affects", "supersedes", "superseded_by", "tickets"},
    "ticket": set(REQUIRED["ticket"]) | {"specs", "decisions", "blocked_by"},
}
LIST_KEYS = {"affects", "supersedes", "tickets", "specs", "decisions", "blocked_by"}
PREFIX = {"decision": "D", "ticket": "T"}

ID_PATTERN = {
    "spec": re.compile(r"^[a-z0-9][a-z0-9-]*$"),
    "decision": re.compile(r"^D-\d{4}$"),
    "ticket": re.compile(r"^T-\d{4}$"),
}
CITE = re.compile(r"\b([DT]-\d{4})\b")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADER_LINE = re.compile(r"^([a-z_]+):(?:\s+(.*))?$")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
PATH_LIKE = re.compile(r"^[\w.@/\[\]()-]+\.[A-Za-z0-9]{1,6}$")
DOTTED = re.compile(r"^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*(?:\(\))?$")
IDENT = re.compile(r"[A-Za-z_$][\w$]*")
IGNORE_MARK = "docket-ship:ignore"

DEFAULT_CONFIG = {
    "docs": "docs",
    "code": [],
    "extensions": ["ts", "tsx", "js", "jsx", "mjs", "py", "gd", "cs", "go", "rs",
                   "java", "kt", "swift", "rb", "php", "c", "h", "cpp", "hpp", "tscn", "json"],
    "symbols": "true",
    # "used to" alone also matches "used to add emphasis", so only the past-tense form counts.
    "history_phrases": ["not yet", "not built", "previously", "used to be", "we decided",
                        "for now", "todo", "tbd", "later stage", "first draft"],
}
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "out", "__pycache__",
             ".godot", ".import", "venv", ".venv", "target", "vendor", ".turbo", "coverage"}
MAX_CODE_FILE = 1_000_000


# --------------------------------------------------------------------------
# Header parsing: a strict YAML subset, so it never needs a dependency.
# --------------------------------------------------------------------------

def parse_value(raw: str):
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        return raw[1:end] if end > 0 else raw[1:]
    raw = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    return raw


def parse_header(lines: List[str]) -> Tuple[Optional[dict], int, List[Tuple[int, str]]]:
    """Returns (meta, index of first body line, problems as (line, message))."""
    if not lines or lines[0].strip() != "---":
        return None, 0, [(1, "missing frontmatter: the file must start with a '---' header")]
    meta: dict = {}
    problems: List[Tuple[int, str]] = []
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            return meta, i + 1, problems
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = HEADER_LINE.match(line.rstrip())
        if not m:
            problems.append((i + 1, "cannot parse header line %r (use 'key: value' or 'key: [a, b]')"
                             % line.strip()))
            continue
        if m.group(1) in meta:
            problems.append((i + 1, "duplicate header key '%s'" % m.group(1)))
        meta[m.group(1)] = parse_value(m.group(2) or "")
    return None, 0, [(1, "header is not closed with '---'")]


def set_header_value(path: Path, key: str, value: str) -> None:
    """Rewrites one header line in place, adding it if it is missing."""
    lines = path.read_text(encoding="utf-8").split("\n")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    for i in range(1, end):
        if HEADER_LINE.match(lines[i].rstrip()) and lines[i].startswith(key + ":"):
            lines[i] = ("%s: %s" % (key, value)).rstrip()
            break
    else:
        lines.insert(end, ("%s: %s" % (key, value)).rstrip())
    path.write_text("\n".join(lines), encoding="utf-8")


def format_list(items: List[str]) -> str:
    return "[" + ", ".join(items) + "]"


# --------------------------------------------------------------------------
# Project model
# --------------------------------------------------------------------------

class Issue:
    def __init__(self, path: Path, line: int, level: str, message: str):
        self.path, self.line, self.level, self.message = path, line, level, message


class Doc:
    def __init__(self, path: Path, kind: str):
        self.path = path
        self.kind = kind  # from the folder it sits in
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.meta, self.body_start, self.header_problems = parse_header(self.lines)
        self.meta = self.meta or {}

    @property
    def id(self) -> str:
        value = self.meta.get("id")
        return value if isinstance(value, str) and value else self.path.stem

    @property
    def status(self) -> str:
        value = self.meta.get("status")
        return value if isinstance(value, str) else ""

    def text(self, key: str) -> str:
        value = self.meta.get(key)
        return value if isinstance(value, str) else ""

    def list(self, key: str) -> List[str]:
        value = self.meta.get(key)
        return value if isinstance(value, list) else []

    def body(self) -> Iterator[Tuple[int, str]]:
        """Body lines outside fenced code blocks, as (1-based line number, text)."""
        fence = None
        for i in range(self.body_start, len(self.lines)):
            line = self.lines[i]
            stripped = line.lstrip()
            if fence:
                if stripped.startswith(fence):
                    fence = None
                continue
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                continue
            yield i + 1, line


class Project:
    def __init__(self, root: Path):
        self.root = root
        self.config_problems: List[str] = []
        self.config = self._read_config()
        self.docs_dir = root / str(self.config["docs"])
        self.docs: List[Doc] = []
        for kind, folder in FOLDERS.items():
            directory = self.docs_dir / folder
            if directory.is_dir():
                self.docs.extend(Doc(p, kind) for p in sorted(directory.glob("*.md")))
        self.by_id: Dict[str, Doc] = {}
        for doc in self.docs:
            self.by_id.setdefault(doc.id, doc)
        self._code: Optional[Tuple[Set[str], List[str]]] = None

    def _read_config(self) -> dict:
        config = dict(DEFAULT_CONFIG)
        path = self.root / CONFIG
        if not path.exists():
            return config
        lines = ["---"] + path.read_text(encoding="utf-8").splitlines() + ["---"]
        meta, _, problems = parse_header(lines)
        self.config_problems = ["%s line %d: %s" % (CONFIG, n - 1, msg) for n, msg in problems]
        for key, value in (meta or {}).items():
            if key not in DEFAULT_CONFIG:
                self.config_problems.append("%s: unknown key '%s'" % (CONFIG, key))
            config[key] = value
        return config

    def of(self, kind: str) -> List[Doc]:
        return [d for d in self.docs if d.kind == kind]

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def open_tickets_for(self, spec_id: str) -> List[str]:
        return [t.id for t in self.of("ticket")
                if t.status in OPEN_TICKET and spec_id in t.list("specs")]

    def code_index(self) -> Tuple[Set[str], List[str]]:
        """Every identifier in the code roots, and every code file's path."""
        if self._code is None:
            identifiers: Set[str] = set()
            files: List[str] = []
            extensions = {"." + e.lstrip(".") for e in as_list(self.config["extensions"])}
            for code_root in as_list(self.config["code"]):
                base = self.root / code_root
                if not base.exists():
                    continue
                for path in walk(base):
                    if path.suffix not in extensions or path.stat().st_size > MAX_CODE_FILE:
                        continue
                    files.append(self.rel(path))
                    try:
                        identifiers.update(IDENT.findall(path.read_text(encoding="utf-8",
                                                                        errors="ignore")))
                    except OSError:
                        pass
            self._code = (identifiers, files)
        return self._code


def as_list(value) -> List[str]:
    if isinstance(value, list):
        return value
    return [value] if value else []


def walk(base: Path) -> Iterator[Path]:
    for entry in base.iterdir():
        if entry.is_dir():
            if entry.name not in SKIP_DIRS and not entry.name.startswith("."):
                yield from walk(entry)
        elif entry.is_file():
            yield entry


def find_root(start: Path) -> Optional[Path]:
    for candidate in [start, *start.parents]:
        if (candidate / CONFIG).exists():
            return candidate
    return None


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def check(project: Project) -> List[Issue]:
    issues: List[Issue] = []

    def add(doc_or_path, line: int, level: str, message: str) -> None:
        path = doc_or_path.path if isinstance(doc_or_path, Doc) else doc_or_path
        issues.append(Issue(path, line, level, message))

    for problem in project.config_problems:
        add(project.root / CONFIG, 1, "error", problem)

    seen: Dict[str, Doc] = {}
    for doc in project.docs:
        for line, message in doc.header_problems:
            add(doc, line, "error", message)
        if doc.header_problems and not doc.meta:
            continue
        check_header(project, doc, seen, add)

    check_relations(project, add)
    for doc in project.docs:
        if doc.meta:
            check_body(project, doc, add)

    check_index(project, add)
    check_conventions(project, add)
    issues.sort(key=lambda i: (project.rel(i.path), i.line))
    return issues


def check_header(project: Project, doc: Doc, seen: Dict[str, Doc], add) -> None:
    kind, meta = doc.kind, doc.meta
    for key in REQUIRED[kind]:
        if key not in meta or meta[key] in ("", []):
            add(doc, 1, "error", "missing required header '%s'" % key)
    declared = meta.get("type")
    if declared and declared != kind:
        add(doc, 1, "error", "type is '%s' but the file is in the %s folder (%s)"
            % (declared, kind, FOLDERS[kind]))
    for key in meta:
        if key not in KNOWN[kind]:
            add(doc, 1, "warning", "unknown header '%s' for a %s" % (key, kind))
        if key in LIST_KEYS and meta[key] != "" and not isinstance(meta[key], list):
            add(doc, 1, "error", "'%s' must be a list like [a, b]" % key)

    doc_id = meta.get("id")
    if isinstance(doc_id, str) and doc_id:
        if not ID_PATTERN[kind].match(doc_id):
            add(doc, 1, "error", "id '%s' is not a valid %s id" % (doc_id, kind))
        stem = doc.path.stem
        if kind == "spec" and stem != doc_id:
            add(doc, 1, "error", "spec id '%s' must equal its filename '%s'" % (doc_id, stem))
        if kind != "spec" and not (stem == doc_id or stem.startswith(doc_id + "-")):
            add(doc, 1, "error", "filename must start with its id '%s'" % doc_id)
        if doc_id in seen:
            add(doc, 1, "error", "duplicate id '%s' (also %s)"
                % (doc_id, project.rel(seen[doc_id].path)))
        else:
            seen[doc_id] = doc

    if doc.status and doc.status not in STATUSES[kind]:
        add(doc, 1, "error", "status '%s' is not one of %s"
            % (doc.status, ", ".join(STATUSES[kind])))
    if kind == "decision" and doc.text("date") and not DATE.match(doc.text("date")):
        add(doc, 1, "error", "date must be YYYY-MM-DD")


def check_relations(project: Project, add) -> None:
    by_id = project.by_id

    def expect(doc: Doc, key: str, kind: str) -> None:
        for ref in doc.list(key):
            target = by_id.get(ref)
            if target is None or target.kind != kind:
                add(doc, 1, "error", "'%s' lists %s, which is not a known %s" % (key, ref, kind))

    for d in project.of("decision"):
        expect(d, "affects", "spec")
        expect(d, "supersedes", "decision")
        expect(d, "tickets", "ticket")
        successor = d.text("superseded_by")
        if d.status == "superseded":
            if not successor:
                add(d, 1, "error", "status is superseded but superseded_by is empty")
            elif successor not in by_id or by_id[successor].kind != "decision":
                add(d, 1, "error", "superseded_by %s is not a known decision" % successor)
            elif d.id not in by_id[successor].list("supersedes"):
                add(d, 1, "error", "superseded_by %s, but %s does not list %s in supersedes"
                    % (successor, successor, d.id))
        elif successor:
            add(d, 1, "error", "superseded_by is set but status is '%s'" % d.status)
        if d.status == "accepted":
            for old_id in d.list("supersedes"):
                old = by_id.get(old_id)
                if old and old.kind == "decision" and (
                        old.status != "superseded" or old.text("superseded_by") != d.id):
                    add(d, 1, "error", "supersedes %s, but %s is not marked superseded by %s "
                        "(run: docket-ship supersede %s %s)" % (old_id, old_id, d.id, old_id, d.id))

    for t in project.of("ticket"):
        expect(t, "specs", "spec")
        expect(t, "decisions", "decision")
        expect(t, "blocked_by", "ticket")

    for s in project.of("spec"):
        if s.status == "retired":
            for ticket_id in project.open_tickets_for(s.id):
                add(by_id[ticket_id], 1, "warning", "open ticket implements retired spec '%s'" % s.id)

    # An accepted decision should be visible where it applies.
    for d in project.of("decision"):
        if d.status != "accepted":
            continue
        for spec_id in d.list("affects"):
            spec = by_id.get(spec_id)
            if spec and spec.kind == "spec" and not any(
                    d.id in CITE.findall(line) for _, line in spec.body()):
                add(spec, 1, "warning", "%s affects this spec but is not cited in it" % d.id)


def check_body(project: Project, doc: Doc, add) -> None:
    by_id = project.by_id
    is_spec = doc.kind == "spec"
    phrases = [p.lower() for p in as_list(project.config["history_phrases"])]
    symbols_on = str(project.config["symbols"]).lower() == "true" and as_list(project.config["code"])
    planned = " (this spec has open tickets, so it may describe planned work)" \
        if is_spec and project.open_tickets_for(doc.id) else ""

    for number, line in doc.body():
        ignored = IGNORE_MARK in line
        # An id in backticks is an example (`D-0014` in another project), not a citation.
        for cited in set(CITE.findall(INLINE_CODE.sub("", line))):
            target = by_id.get(cited)
            if target is None:
                add(doc, number, "error", "cites %s, which does not exist" % cited)
            elif is_spec and target.kind == "ticket":
                add(doc, number, "warning", "specs should not cite tickets (%s); tickets point at "
                    "specs instead" % cited)
            elif is_spec and target.status in ("superseded", "rejected"):
                successor = target.text("superseded_by")
                add(doc, number, "error", "cites %s %s%s - update this paragraph" % (
                    target.status, cited, " (superseded by %s)" % successor if successor else ""))
            elif is_spec and target.status == "proposed":
                add(doc, number, "warning", "cites %s, which is still proposed" % cited)

        for target in LINK.findall(line):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            local = target.split("#", 1)[0].split("?", 1)[0].replace("%20", " ")
            if local and not (doc.path.parent / local).exists():
                add(doc, number, "error", "broken link: %s" % target)

        if not is_spec or ignored:
            continue
        lowered = line.lower()
        for phrase in phrases:
            if re.search(r"\b%s\b" % re.escape(phrase), lowered):
                add(doc, number, "warning", "'%s' reads as status or history; move it to a ticket "
                    "or decision, or mark the line %s" % (phrase, IGNORE_MARK))
                break
        for code in INLINE_CODE.findall(line):
            check_code_ref(project, doc, number, code.strip(), bool(symbols_on), planned, add)


def check_code_ref(project: Project, doc: Doc, number: int, code: str, symbols_on: bool,
                   planned: str, add) -> None:
    if PATH_LIKE.match(code) and "/" in code:
        if (project.root / code).exists() or (doc.path.parent / code).exists():
            return
        _, files = project.code_index()
        if not any(f == code or f.endswith("/" + code) for f in files):
            add(doc, number, "warning", "names path %s, which does not exist%s" % (code, planned))
        return
    if not symbols_on or not DOTTED.match(code):
        return
    identifiers, _ = project.code_index()
    for part in code.rstrip("()").split("."):
        if is_distinctive(part) and part not in identifiers:
            add(doc, number, "warning", "names %s, which is not found in the code%s" % (part, planned))


def is_distinctive(name: str) -> bool:
    """Only names that look like code (camelCase, PascalCase words, snake_case) are checked;
    plain words such as `draft` would match prose and code alike."""
    if len(name) < 4:
        return False
    return ("_" in name.strip("_") or bool(re.search(r"[a-z][A-Z]", name))
            or bool(re.match(r"^[A-Z][a-z]+[A-Z]", name)))


def check_index(project: Project, add) -> None:
    path = project.docs_dir / INDEX
    if not path.exists():
        add(path, 1, "error", "missing; run: docket-ship index")
    elif normalize(path.read_text(encoding="utf-8")) != normalize(render_index(project)):
        add(path, 1, "error", "out of date; run: docket-ship index")


def check_conventions(project: Project, add) -> None:
    bundled = TOOL_DIR / CONVENTIONS
    local = project.docs_dir / CONVENTIONS
    if not local.exists():
        add(local, 1, "warning", "missing; run: docket-ship init --update")
    elif bundled.exists() and normalize(local.read_text(encoding="utf-8")) != normalize(
            bundled.read_text(encoding="utf-8")):
        add(local, 1, "warning", "differs from this docket-ship's version; run: docket-ship init --update")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


# --------------------------------------------------------------------------
# index
# --------------------------------------------------------------------------

def render_index(project: Project) -> str:
    def link(doc: Doc) -> str:
        return "[%s](%s)" % (doc.id, doc.path.relative_to(project.docs_dir).as_posix())

    out = ["# Docs index", "",
           "<!-- Generated by `docket-ship index`. Do not edit. Rules: CONVENTIONS.md -->", ""]

    out += ["## Specs", ""]
    specs = sorted(project.of("spec"), key=lambda d: (d.status == "retired", d.id))
    for s in specs:
        line = "- %s · %s · %s — %s" % (link(s), s.status, s.text("title"), s.text("summary"))
        open_ids = project.open_tickets_for(s.id)
        out.append(line + (" · open: %s" % ", ".join(open_ids) if open_ids else ""))
    if not specs:
        out.append("_None._")
    out.append("")

    decisions = project.of("decision")
    live = [d for d in decisions if d.status in ("proposed", "accepted")]
    gone = [d for d in decisions if d.status not in ("proposed", "accepted")]
    out += ["## Decisions", ""]
    for d in live:
        affects = d.list("affects")
        out.append("- %s · %s · %s — %s%s" % (link(d), d.status, d.text("date"), d.text("title"),
                                             " · affects: %s" % ", ".join(affects) if affects else ""))
    if not live:
        out.append("_None._")
    if gone:
        out += ["", "Superseded or rejected: " + ", ".join(
            "%s%s" % (link(d), " → %s" % d.text("superseded_by") if d.text("superseded_by")
                      else " (rejected)") for d in gone)]
    out.append("")

    tickets = project.of("ticket")
    active = [t for t in tickets if t.status in OPEN_TICKET]
    out += ["## Open tickets", ""]
    for t in sorted(active, key=lambda t: (t.status != "doing", t.id)):
        extra = []
        if t.list("specs"):
            extra.append("specs: " + ", ".join(t.list("specs")))
        if t.list("blocked_by"):
            extra.append("blocked by: " + ", ".join(t.list("blocked_by")))
        out.append("- %s · %s · %s%s" % (link(t), t.status, t.text("title"),
                                          "".join(" · " + e for e in extra)))
    if not active:
        out.append("_None._")
    closed = len(tickets) - len(active)
    if closed:
        out += ["", "%d closed (`docket-ship list tickets --status done`)." % closed]
    out.append("")
    return "\n".join(out)


def write_index(project: Project) -> Path:
    path = project.docs_dir / INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_index(project), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# new, list, refs, supersede, init
# --------------------------------------------------------------------------

TEMPLATES = {
    "decision": """---
id: {id}
type: decision
title: {title}
status: proposed
date: {date}
summary: {title}.
affects: {affects}
supersedes: {supersedes}
superseded_by:
---

## Context

What forces this choice, in a few lines.

## Decision

What we do.

## Consequences

What follows, good and bad. Which specs change.
""",
    "ticket": """---
id: {id}
type: ticket
title: {title}
status: open
summary: {title}.
specs: {specs}
decisions: {decisions}
blocked_by: []
---

## Done when

-
""",
    "spec": """---
id: {id}
type: spec
title: {title}
status: draft
summary: {title}.
---

# {title}

""",
}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(slug) > 50:
        # Cut at a word boundary so the filename stays readable.
        slug = slug[:51].rsplit("-", 1)[0] if "-" in slug[:51] else slug[:50]
    return slug or "untitled"


def next_id(project: Project, kind: str) -> str:
    folder = project.docs_dir / FOLDERS[kind]
    pattern = re.compile(r"^%s-(\d{4})" % PREFIX[kind])
    numbers = [int(m.group(1)) for p in folder.glob("*.md") for m in [pattern.match(p.name)] if m]
    return "%s-%04d" % (PREFIX[kind], max(numbers, default=0) + 1)


def split_ids(value: Optional[str]) -> List[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def cmd_new(project: Project, args) -> int:
    kind = args.kind
    folder = project.docs_dir / FOLDERS[kind]
    folder.mkdir(parents=True, exist_ok=True)
    if kind == "spec":
        if not ID_PATTERN["spec"].match(args.name):
            return fail("spec slug must be lowercase letters, digits and hyphens")
        doc_id, title, filename = args.name, args.title or args.name, args.name + ".md"
    else:
        doc_id, title = next_id(project, kind), args.name
        filename = "%s-%s.md" % (doc_id, slugify(title))
    path = folder / filename
    if path.exists():
        return fail("%s already exists" % project.rel(path))
    path.write_text(TEMPLATES[kind].format(
        id=doc_id, title=title, date=datetime.date.today().isoformat(),
        affects=format_list(split_ids(args.affects)),
        supersedes=format_list(split_ids(args.supersedes)),
        specs=format_list(split_ids(args.specs)),
        decisions=format_list(split_ids(args.decisions)),
    ), encoding="utf-8")
    write_index(Project(project.root))
    print("created %s (%s); index updated" % (project.rel(path), doc_id))
    return 0


def cmd_list(project: Project, args) -> int:
    kinds = {"specs": "spec", "decisions": "decision", "tickets": "ticket"}
    wanted = [kinds[args.kind]] if args.kind else list(FOLDERS)
    for kind in wanted:
        for doc in project.of(kind):
            if args.status and doc.status != args.status:
                continue
            if args.open and doc.status in ("retired", "rejected", "superseded", "done", "dropped"):
                continue
            extra = ""
            if kind == "ticket" and doc.list("specs"):
                extra = "  [%s]" % ", ".join(doc.list("specs"))
            if kind == "decision" and doc.list("affects"):
                extra = "  [%s]" % ", ".join(doc.list("affects"))
            print("%-12s %-10s %s%s" % (doc.id, doc.status, doc.text("title"), extra))
    return 0


def cmd_refs(project: Project, args) -> int:
    target = args.id
    target_doc = project.by_id.get(target)
    found = 0
    for doc in project.docs:
        for key in sorted(LIST_KEYS | {"superseded_by"}):
            if target in doc.list(key) or doc.text(key) == target:
                print("%s:1: %s: %s" % (project.rel(doc.path), key, target))
                found += 1
        if doc is target_doc:
            continue
        for number, line in doc.body():
            hit = target in CITE.findall(line)
            if not hit and target_doc is not None and target_doc.kind == "spec":
                hit = any(Path(l.split("#")[0]).name == target_doc.path.name
                          for l in LINK.findall(line))
            if hit:
                print("%s:%d: %s" % (project.rel(doc.path), number, line.strip()))
                found += 1
    if not found:
        print("no references to %s" % target)
    return 0


def cmd_supersede(project: Project, args) -> int:
    old, new = project.by_id.get(args.old), project.by_id.get(args.new)
    for given, doc in ((args.old, old), (args.new, new)):
        if doc is None or doc.kind != "decision":
            return fail("%s is not a known decision" % given)
    set_header_value(old.path, "status", "superseded")
    set_header_value(old.path, "superseded_by", new.id)
    if old.id not in new.list("supersedes"):
        set_header_value(new.path, "supersedes", format_list(new.list("supersedes") + [old.id]))
    refreshed = Project(project.root)
    write_index(refreshed)
    print("%s is now superseded by %s; index updated" % (old.id, new.id))
    if new.status != "accepted":
        print("note: %s is still '%s' - set it to accepted once agreed" % (new.id, new.status))
    stale = [(s, n, line) for s in refreshed.of("spec") for n, line in s.body()
             if old.id in CITE.findall(line)]
    affected = sorted(set(old.list("affects")) | set(new.list("affects")))
    if stale:
        print("\nSpec paragraphs that cite %s and need updating:" % old.id)
        for s, n, line in stale:
            print("  %s:%d: %s" % (refreshed.rel(s.path), n, line.strip()))
    if affected:
        print("\nSpecs either decision affects: %s" % ", ".join(affected))
    return 0


AGENTS_SNIPPET = """## Docs

Docs follow `docs/CONVENTIONS.md` (docket-ship): specs hold the current design,
decisions are frozen records, tickets hold all unfinished work. Start at
`docs/INDEX.md`. After changing docs, run `docket-ship check`."""


def cmd_init(root: Path, args) -> int:
    bundled = TOOL_DIR / CONVENTIONS
    if not bundled.exists():
        return fail("%s is missing next to docket_ship.py" % CONVENTIONS)
    config_path = root / CONFIG
    if not config_path.exists():
        code = [d for d in ("src", "app", "lib", "scripts", "addons") if (root / d).is_dir()]
        config_path.write_text(
            "# docket-ship configuration - see docs/CONVENTIONS.md\n"
            "docs: docs\n"
            "code: %s              # folders to look in for named paths and symbols\n"
            "symbols: true\n" % format_list(code), encoding="utf-8")
        print("created %s" % CONFIG)
    project = Project(root)
    for folder in FOLDERS.values():
        (project.docs_dir / folder).mkdir(parents=True, exist_ok=True)
    local = project.docs_dir / CONVENTIONS
    if not local.exists() or args.update:
        shutil.copyfile(bundled, local)
        print("wrote %s" % project.rel(local))
    write_index(Project(root))
    print("wrote %s" % project.rel(project.docs_dir / INDEX))
    if not args.update:
        print("\nAdd this to the project's AGENTS.md or CLAUDE.md:\n\n" + AGENTS_SNIPPET)
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def fail(message: str) -> int:
    print("docket-ship: %s" % message, file=sys.stderr)
    return 2


def cmd_check(project: Project, args) -> int:
    issues = check(project)
    for issue in issues:
        print("%s:%d: %s: %s" % (project.rel(issue.path), issue.line, issue.level, issue.message))
    errors = sum(1 for i in issues if i.level == "error")
    warnings = len(issues) - errors
    print("docket-ship: %d error%s, %d warning%s in %d docs" % (
        errors, "" if errors == 1 else "s", warnings, "" if warnings == 1 else "s",
        len(project.docs)))
    return 1 if errors or (args.strict and warnings) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docket-ship", description=__doc__.split("\n")[0])
    parser.add_argument("--root", help="project root (default: nearest folder with docket-ship.cfg)")
    parser.add_argument("--version", action="version", version="docket-ship " + VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="validate docs")
    p.add_argument("--strict", action="store_true", help="fail on warnings too")
    sub.add_parser("index", help="regenerate docs/INDEX.md")

    p = sub.add_parser("new", help="create a decision, ticket or spec")
    p.add_argument("kind", choices=["decision", "ticket", "spec"])
    p.add_argument("name", help="title (decision, ticket) or slug (spec)")
    p.add_argument("title", nargs="?", help="spec title")
    p.add_argument("--affects")
    p.add_argument("--supersedes")
    p.add_argument("--specs")
    p.add_argument("--decisions")

    p = sub.add_parser("list", help="one line per doc")
    p.add_argument("kind", nargs="?", choices=["specs", "decisions", "tickets"])
    p.add_argument("--status")
    p.add_argument("--open", action="store_true", help="leave out closed and retired docs")

    p = sub.add_parser("refs", help="every place an id is referenced")
    p.add_argument("id")

    p = sub.add_parser("supersede", help="mark OLD superseded by NEW")
    p.add_argument("old")
    p.add_argument("new")

    p = sub.add_parser("init", help="set up docket-ship in a project")
    p.add_argument("--update", action="store_true", help="refresh docs/CONVENTIONS.md")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)

    if args.command == "init":
        return cmd_init(Path(args.root or ".").resolve(), args)
    root = Path(args.root).resolve() if args.root else find_root(Path.cwd())
    if root is None or not (root / CONFIG).exists():
        return fail("no %s found here or above; run: docket-ship init" % CONFIG)
    project = Project(root)
    if args.command == "index":
        print("wrote %s" % project.rel(write_index(project)))
        return 0
    return {"check": cmd_check, "new": cmd_new, "list": cmd_list, "refs": cmd_refs,
            "supersede": cmd_supersede}[args.command](project, args)


if __name__ == "__main__":
    sys.exit(main())
