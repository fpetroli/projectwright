#!/usr/bin/env python3
"""wiki-lint — mechanical integrity checks of the wiki (wiki/ and wiki-sources/).

Checks, without ever correcting:
  config       project.yaml is valid (keys, values, codes, tracker rules)
  encoding     files are UTF-8 without BOM
  frontmatter  present (except README.md), valid YAML, conforming to schema.yaml:
               known type, required and forbidden fields, allowed values, dates,
               wikilink fields written as "[[name]]", known area code
  names        file names are unique across wiki/ and wiki-sources/
  links        every [[wikilink]] (body and frontmatter) points to an existing file;
               placeholders like [[<name>]] are ignored
  ids          ADR/Q/T records: id well formed, matching type, file name and area,
               known code, not duplicated, in a folder named as the type requires
  superseded   a superseded decision has superseded_by
  components   every component of project.yaml has wiki/components/<name>/<name>.md
               of type component with the same code; no unregistered component folder
  cards        every file in wiki-sources/ (except README.md) is a source-card
  versioning   only when the project folder is a git repository: repositories/ is ignored
               and nothing under it (files or nested repositories) is tracked

Usage:
    python3 wiki-lint.py [--root <project root>]
    python3 wiki-lint.py --hook        (Claude Code PostToolUse hook: reads the event
                                        from stdin, checks only when the written file is
                                        in wiki/ or wiki-sources/, reports only what
                                        concerns that file, on stderr, exit code 2)
Exit code: 0 = sound, 1 = violations, 2 = violations in --hook mode, 3 = configuration error.
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`[^`]*`")


def is_date(value):
    if isinstance(value, datetime.date):
        return True
    return isinstance(value, str) and bool(pwlib.DATE.match(value))


def is_placeholder(target):
    """Template placeholders such as [[<repo>]], [[web-<feature>]] or [[ADR-FE-NNNN-…]]."""
    return any(mark in target for mark in ("<", ">", "…", "{{"))


def body_links(text):
    """(line number, target) of the wikilinks outside code blocks and code spans."""
    out = []
    in_fence = False
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":  # skip the frontmatter: checked separately
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    for n, line in enumerate(lines[start:], start + 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in pwlib.WIKILINK.finditer(CODE_SPAN.sub("", line).replace("\\|", "|")):
            out.append((n, m.group(1).strip()))
    return out


def lint(root, project, schema):
    """List of violations: (check, file relative path or "", message)."""
    v = []
    root = Path(root)

    for msg in pwlib.validate_project(project, schema):
        v.append(("config", "project.yaml", msg))

    files = pwlib.wiki_files(root)
    by_name = {}
    for p in files:
        if p.name != "README.md":
            by_name.setdefault(p.stem, []).append(p)
    for name, paths in sorted(by_name.items()):
        if len(paths) > 1:
            for p in paths:
                v.append(("names", pwlib.rel(root, p), "file name '%s.md' not unique: %s" % (
                    name, ", ".join(pwlib.rel(root, q) for q in paths))))
    names = set(by_name)

    values = schema.get("values", {})
    types = schema.get("types", {})
    date_fields = set(schema.get("dates", []))
    link_fields = set(schema.get("wikilinks", []))
    id_rx = re.compile(schema.get("ids", {}).get("id", r"^(?P<prefix>[A-Z]+)-(?P<code>[A-Z]{2,8})-(?P<number>[0-9]{4})$"))
    codes = pwlib.known_codes(project)
    ids_seen = {}
    entry_notes = {}

    for p in files:
        rp = pwlib.rel(root, p)
        if pwlib.has_bom(p):
            v.append(("encoding", rp, "UTF-8 with BOM: save it without BOM"))
        fm, err, text = pwlib.read_frontmatter(p)

        for n, target in body_links(text):
            if not is_placeholder(target) and target not in names:
                v.append(("links", rp, "line %d: broken link [[%s]]" % (n, target)))

        if p.name == "README.md":
            continue
        if fm is None:
            v.append(("frontmatter", rp, err))
            continue

        ftype = fm.get("type")
        if ftype not in types:
            v.append(("frontmatter", rp, "type %r not allowed (allowed: %s)" % (ftype, ", ".join(types))))
            continue
        rules = types[ftype]
        for field in rules.get("required", []):
            if pwlib.empty(fm.get(field)):
                v.append(("frontmatter", rp, "required field missing or empty: %s" % field))
        for field in rules.get("forbidden", []):
            if field in fm:
                v.append(("frontmatter", rp, "field not allowed for type %s: %s" % (ftype, field)))
        for field, value in fm.items():
            allowed = (rules.get("values") or {}).get(field) or values.get(field)
            if allowed and not pwlib.empty(value):
                for item in value if isinstance(value, list) else [value]:
                    if item not in allowed:
                        v.append(("frontmatter", rp, "%s: value %r not allowed (allowed: %s)"
                                  % (field, item, ", ".join(map(str, allowed)))))
            if field in date_fields and not pwlib.empty(value) and not is_date(value):
                v.append(("frontmatter", rp, "%s: %r is not a date YYYY-MM-DD" % (field, value)))
            if field in link_fields and not pwlib.empty(value):
                for item in value if isinstance(value, list) else [value]:
                    if not (isinstance(item, str) and pwlib.WIKILINK.fullmatch(item.strip())):
                        v.append(("frontmatter", rp, "%s: %r must be a wikilink \"[[name]]\"" % (field, item)))
        for field, value in fm.items():
            for target in pwlib.links_in(value):
                if not is_placeholder(target) and target not in names:
                    v.append(("links", rp, "frontmatter %s: broken link [[%s]]" % (field, target)))

        area = fm.get("area")
        if not pwlib.empty(area) and str(area) not in codes:
            v.append(("frontmatter", rp, "area %r is neither an area code of project.yaml nor a component code" % area))

        prefix = rules.get("id_prefix")
        if prefix:
            rid = fm.get("id")
            m = id_rx.match(str(rid or ""))
            if not m:
                v.append(("ids", rp, "id %r not well formed (expected %s-<CODE>-NNNN)" % (rid, prefix)))
            else:
                if m.group("prefix") != prefix:
                    v.append(("ids", rp, "id %s: a %s needs the prefix %s" % (rid, ftype, prefix)))
                if m.group("code") not in codes:
                    v.append(("ids", rp, "id %s: code %s unknown" % (rid, m.group("code"))))
                if not pwlib.empty(area) and str(area) != m.group("code"):
                    v.append(("ids", rp, "id %s: area is %s but the code of the id is %s" % (rid, area, m.group("code"))))
                if p.stem == rid:
                    v.append(("ids", rp, "file name needs a short title after the id: %s-<short-title>.md" % rid))
                elif not p.stem.startswith(rid + "-"):
                    v.append(("ids", rp, "file name must start with the id %s" % rid))
                ids_seen.setdefault(rid, []).append(rp)
            folder = rules.get("folder")
            if folder and p.parent.name != folder:
                v.append(("ids", rp, "a %s lives in a folder named %s/" % (ftype, folder)))

        if fm.get("status") == "superseded" and pwlib.empty(fm.get("superseded_by")):
            v.append(("superseded", rp, "status superseded without superseded_by"))

        top = Path(rp).parts[0]
        if top == "wiki-sources" and ftype != "source-card":
            v.append(("cards", rp, "files in wiki-sources/ are ingestion cards (type source-card)"))
        if ftype == "component":
            entry_notes[p.stem] = (rp, fm, p)

    for rid, paths in sorted(ids_seen.items()):
        if len(paths) > 1:
            for rp in paths:
                v.append(("ids", rp, "id %s duplicated: %s" % (rid, ", ".join(paths))))

    comp_dir = root / "wiki" / "components"
    registered = {c.get("name"): c for c in (pwlib.get(project, "components") or []) if isinstance(c, dict)}
    for name, comp in registered.items():
        note = comp_dir / str(name) / ("%s.md" % name)
        if not note.is_file():
            v.append(("components", "project.yaml", "component %s: entry note wiki/components/%s/%s.md missing"
                      % (name, name, name)))
            continue
        rp, fm, _p = entry_notes.get(name, (pwlib.rel(root, note), None, None))
        if fm is None:
            v.append(("components", rp, "the entry note of a component has type: component"))
            continue
        if str(fm.get("code")) != str(comp.get("code")):
            v.append(("components", rp, "code %r differs from project.yaml (%r)" % (fm.get("code"), comp.get("code"))))
        if fm.get("repository") != comp.get("repository"):
            v.append(("components", rp, "repository %r differs from project.yaml (%r)"
                      % (fm.get("repository"), comp.get("repository"))))
    if comp_dir.is_dir():
        for d in sorted(x for x in comp_dir.iterdir() if x.is_dir()):
            if d.name not in registered:
                v.append(("components", pwlib.rel(root, d), "component folder not registered in project.yaml"))
    for name, (rp, _fm, p) in entry_notes.items():
        if p.parent.parent != comp_dir or p.parent.name != name:
            v.append(("components", rp, "an entry note lives in wiki/components/<name>/<name>.md"))
    v += versioning(root, project)
    return v


def versioning(root, project):
    """When the project folder is versioned, the code repositories must stay out of it."""
    import subprocess
    if not (Path(root) / ".git").exists():
        return []
    repos = str(pwlib.get(project, "paths.repositories") or "repositories").strip("/")
    out = []
    try:
        tracked = subprocess.run(["git", "ls-files", "-s", "--", repos], cwd=root, capture_output=True,
                                 text=True, encoding="utf-8").stdout.splitlines()
        ignored = subprocess.run(["git", "check-ignore", "-q", repos + "/"], cwd=root).returncode == 0
    except OSError:  # git not available
        return []
    if tracked:
        nested = [l.split("\t", 1)[-1] for l in tracked if l.startswith("160000")]
        what = ("nested repositories: %s" % ", ".join(nested[:3])) if nested else ("%d file(s), e.g. %s" % (
            len(tracked), tracked[0].split("\t", 1)[-1]))
        out.append(("versioning", repos + "/", "code of the product is tracked by the project repository (%s): "
                    "remove it with `git rm -r --cached %s`" % (what, repos)))
    if not ignored:
        out.append(("versioning", ".gitignore", "%s/ is not ignored: add it to .gitignore" % repos))
    return out


ORDER = ["config", "versioning", "encoding", "frontmatter", "names", "links", "ids", "superseded", "components", "cards"]


def report(violations, stream):
    current = None
    rank = {c: i for i, c in enumerate(ORDER)}
    for check, rp, msg in sorted(violations, key=lambda x: (rank.get(x[0], 99), x[1])):
        if check != current:
            print("[%s]" % check, file=stream)
            current = check
        print("  - %s — %s" % (rp, msg) if rp else "  - " + msg, file=stream)


def hook_mode(args):
    pwlib.setup_output()
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".md"):
        return 0
    root = pwlib.find_root(args.root, hook=True)
    if root is None:
        return 0
    try:
        rp = pwlib.rel(root, Path(path).resolve())
    except ValueError:
        return 0
    if not (rp.startswith("wiki/") or rp.startswith("wiki-sources/")):
        return 0
    if pwlib.check_python():
        return 0
    try:
        project, schema = pwlib.load_project(root), pwlib.load_schema()
    except pwlib.ConfigError as e:
        print("wiki-lint: %s" % e, file=sys.stderr)
        return 2
    mine = [x for x in lint(root, project, schema) if x[1] == rp]
    if not mine:
        return 0
    print("wiki-lint: %d violation(s) in %s — fix them now (rules: wiki/README.md):" % (len(mine), rp),
          file=sys.stderr)
    report(mine, sys.stderr)
    return 2


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="project root (default: found automatically)")
    ap.add_argument("--hook", action="store_true", help="run as a Claude Code PostToolUse hook")
    args = ap.parse_args()
    if args.hook:
        return hook_mode(args)
    root, project, schema = pwlib.start(args.root)
    violations = lint(root, project, schema)
    n = len(pwlib.wiki_files(root))
    print("wiki-lint on %s (%d files)" % (root, n))
    if not violations:
        print("OK — no violation.")
        return 0
    print("VIOLATIONS: %d\n" % len(violations))
    report(violations, sys.stdout)
    return 1


if __name__ == "__main__":
    sys.exit(main())
