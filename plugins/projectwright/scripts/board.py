#!/usr/bin/env python3
"""board — writes board.html, a read-only view of the tasks of the wiki.

Reads the tasks of the wiki (frontmatter and body) and project.yaml, and writes
them into the layout assets/board.html of the plugin, with the definition of
what a board shows (assets/board-model.json, shared with projectwright-board).
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
MODEL = pwlib.PLUGIN_DIR / "assets" / "board-model.json"
OUTPUT = "board.html"
PLACEHOLDER = "/*__BOARD_DATA__*/"


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, pwlib.SCRIPTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def collect(root, project):
    """The tasks of the wiki, in full, as `wiki-query.py task --format json` gives them to the pane."""
    query = load_script("wiki_query_mod", "wiki-query.py")
    tasks = [query.task_detail(root, r) for r in query.records(root, project) if r.get("type") == "task"]
    tasks.sort(key=lambda t: t["name"])
    return {
        "project": {"name": pwlib.get(project, "project.name") or Path(root).name,
                    "version": pwlib.get(project, "framework.version") or "?",
                    "tasks_mode": pwlib.get(project, "tasks.mode") or "wiki",
                    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")},
        "model": json.loads(MODEL.read_text(encoding="utf-8")),
        "tasks": tasks,
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
