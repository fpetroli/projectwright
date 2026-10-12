#!/usr/bin/env python3
"""board — writes board.html, a read-only view of the whole brain repository.

Reads the wiki (frontmatter and body of every record), the ingestion log and
project.yaml, and writes them into the layout assets/board.html of the plugin.
The result, board.html in the project root, is a single self-contained file
(no network, no external libraries) to open in a browser. It is generated: it is
never edited and never versioned (it is in .gitignore).

Usage (from the project root, or with --root):
    python3 board.py [--open]        writes board.html (and opens it in the browser)
    python3 board.py --hook          for the Claude Code hooks: regenerates silently,
                                     only inside a projectwright project, never fails
"""
import argparse
import datetime
import importlib.util
import json
import os
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

LAYOUT = pwlib.PLUGIN_DIR / "assets" / "board.html"
OUTPUT = "board.html"
PLACEHOLDER = "/*__BOARD_DATA__*/"
LINK_FIELDS = ["related", "decisions", "questions", "blocked_by", "superseded_by", "decision", "source"]
SCALAR_FIELDS = ["title", "type", "id", "status", "area", "lifecycle", "gate", "assumption", "precaution",
                 "decision_owner", "progress", "priority", "phase", "assignee", "created", "updated", "closed_on",
                 "code", "component_status", "repository", "upstream"]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, pwlib.SCRIPTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def body_of(text):
    """The Markdown body of a file, without its frontmatter."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[end + 4:].lstrip("\n")
    return text


def plain(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, list):
        return [plain(x) for x in v]
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def collect(root, project):
    query = load_script("wiki_query_mod", "wiki-query.py")
    records = []
    for r in query.records(root, project):
        text = (Path(root) / r["_path"]).read_text(encoding="utf-8", errors="replace")
        rec = {"name": r["_name"], "path": r["_path"], "component": r["_component"], "body": body_of(text)}
        for f in SCALAR_FIELDS:
            if f in r and r[f] not in (None, ""):
                rec[f] = plain(r[f])
        links = {}
        for f in LINK_FIELDS:
            names = pwlib.links_in(r.get(f))
            if names:
                links[f] = names
        rec["links"] = links
        records.append(rec)

    notes = {r["name"]: r for r in records if r.get("type") == "component"}
    components = [{"name": c.get("name"), "code": c.get("code"),
                   "status": (notes.get(c.get("name")) or {}).get("component_status", "(entry note missing)")}
                  for c in (pwlib.get(project, "components") or []) if isinstance(c, dict)]
    sources = query.read_log(root)

    summary = {"pending_cards": sum(1 for s in sources if s.get("integrated") == "no")}
    try:
        lint = load_script("wiki_lint_mod", "wiki-lint.py")
        summary["lint"] = len(lint.lint(root, project, pwlib.load_schema()))
    except Exception:
        summary["lint"] = None
    try:
        files, adrs, uncovered = query.deviations(root, project)
        if files:
            summary["deviations"] = "%d framework file(s) changed in this project, %d without an ADR; %d deviation(s) not yet proposed." % (
                len(files), len(uncovered), len([a for a in adrs if not a.get("upstream")]))
    except Exception:
        pass

    return {
        "project": {"name": pwlib.get(project, "project.name") or Path(root).name,
                    "language": pwlib.get(project, "project.language"),
                    "version": pwlib.get(project, "framework.version") or "?",
                    "tasks_mode": pwlib.get(project, "tasks.mode") or "wiki",
                    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")},
        "summary": summary,
        "records": records,
        "components": components,
        "sources": sources,
    }


def write(root, project):
    data = json.dumps(collect(root, project), ensure_ascii=False)
    data = data.replace("</", "<\\/")  # never close the <script> element from inside the data
    html = LAYOUT.read_text(encoding="utf-8").replace(PLACEHOLDER, data, 1)
    out = Path(root) / OUTPUT
    out.write_text(html, encoding="utf-8", newline="\n")
    return out


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--open", action="store_true", help="open the board in the browser")
    ap.add_argument("--hook", action="store_true", help="run as a Claude Code hook")
    ap.add_argument("--root")
    args = ap.parse_args()
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}") if not sys.stdin.isatty() else {}
        except Exception:
            event = {}
        root = pwlib.find_root(args.root, hook=True)
        if root is None or pwlib.check_python():
            return 0
        path = ((event or {}).get("tool_input") or {}).get("file_path")
        if path:  # after a write: regenerate only when the wiki changed
            try:
                rp = pwlib.rel(root, Path(path).resolve())
            except ValueError:
                return 0
            if not (rp.startswith("wiki/") or rp.startswith("wiki-sources/") or rp == "project.yaml"):
                return 0
        try:
            write(root, pwlib.load_project(root))
        except Exception:
            pass  # the board must never disturb the session
        return 0
    root, project, _schema = pwlib.start(args.root)
    out = write(root, project)
    print("board written: %s" % out)
    if args.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
