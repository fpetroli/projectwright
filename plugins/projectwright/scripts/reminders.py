#!/usr/bin/env python3
"""reminders — the user's reminders: things to keep in mind that are not tasks.

"Send the e-mail", "update the specification": short points with an optional
date, that the user ticks off. They are personal and never part of the wiki
(constitution, principle 13): they live in .claude/.projectwright-reminders.json
of the project, never versioned. Claude adds one when the user asks ("remind me
to…") and proposes others through proposals.py (kind `remind`); the board beside
the chat (projectwright-board) shows them, to tick, add and remove.

A reminder: `id` (R-0001, never reused, for the tools only), `text`, `due` (an
ISO date, or absent), `created`, and `done_on` once ticked. A ticked reminder is
listed until the end of the day it was ticked, then only with --all.

Usage (from the project root, or with --root):
    python3 reminders.py add "<text>" [--due <date>]   prints the new id; <date>: 2026-10-27, 27/10 or 27/10/2026
    python3 reminders.py list [--all] [--format table|json]
    python3 reminders.py done <id> | undo <id> | remove <id>
Exit code: 0; 1 for a reminder that is not valid or not found.
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

FILE = Path(".claude") / ".projectwright-reminders.json"


class Invalid(Exception):
    """A reminder that cannot be written, or an id not found."""


def today():
    return datetime.date.today()


def parse_due(text, base=None):
    """An ISO date from 2026-10-27, 27/10 or 27/10/2026 (27-10, 27.10 too); None for an empty text."""
    text = (text or "").strip()
    if not text:
        return None
    base = base or today()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.date.fromisoformat(text).isoformat()
        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2}|\d{4}))?", text)
        if m:
            day, month = int(m.group(1)), int(m.group(2))
            year = int(m.group(3)) if m.group(3) else base.year
            if year < 100:
                year += 2000
            due = datetime.date(year, month, day)
            if not m.group(3) and due < base - datetime.timedelta(days=180):
                due = due.replace(year=year + 1)  # "05/01" written in October is next January
            return due.isoformat()
    except ValueError:
        pass
    raise Invalid("not a date: %s (write 2026-10-27, 27/10 or 27/10/2026)" % text)


def load(root):
    p = Path(root) / FILE
    if not p.is_file():
        return {"reminders": []}
    data = json.loads(p.read_text(encoding="utf-8") or "{}")
    data.setdefault("reminders", [])
    return data


def save(root, data):
    p = Path(root) / FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, p)  # a reader never sees half a file
    redraw_board(root)


def redraw_board(root):
    """board.html shows the reminders too: write it again, as the hooks do after a change to the wiki."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("board_mod", Path(__file__).with_name("board.py"))
        board = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(board)
        board.write(root, pwlib.load_project(root))
    except Exception:
        pass  # the board must never stop a reminder


def find(data, rid):
    for r in data["reminders"]:
        if r.get("id") == rid:
            return r
    raise Invalid("reminder not found: %s" % rid)


def add(root, text, due=None):
    text = (text or "").strip()
    if not text:
        raise Invalid("a reminder needs a text")
    data = load(root)
    numbers = [int(r["id"][2:]) for r in data["reminders"] if str(r.get("id", "")).startswith("R-")]
    new = {"id": "R-%04d" % (max(numbers, default=0) + 1), "text": text}
    if parse_due(due):
        new["due"] = parse_due(due)
    new["created"] = today().isoformat()
    data["reminders"].append(new)
    save(root, data)
    return new["id"]


def change(root, rid, action):
    data = load(root)
    r = find(data, rid)
    if action == "done":
        r["done_on"] = today().isoformat()
    elif action == "undo":
        r.pop("done_on", None)
    else:
        data["reminders"].remove(r)
    save(root, data)


def listed(root, everything=False):
    """The open reminders by date (undated last), then those ticked today."""
    rows = load(root)["reminders"]
    shown = rows if everything else [r for r in rows if not r.get("done_on") or r["done_on"] >= today().isoformat()]
    return sorted(shown, key=lambda r: (bool(r.get("done_on")), r.get("due") or "9999-99-99", r.get("id", "")))


def table(rows):
    if not rows:
        return "(no reminders)"
    return "\n".join("%s  %s %-10s %s" % (r["id"], "[x]" if r.get("done_on") else "[ ]", r.get("due", ""), r["text"])
                     for r in rows)


def main():
    pwlib.ensure_python()
    pwlib.setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    # --root also after the command, where the board and the other scripts put it
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", parents=[common])
    a.add_argument("text")
    a.add_argument("--due")
    ls = sub.add_parser("list", parents=[common])
    ls.add_argument("--all", action="store_true")
    ls.add_argument("--format", choices=["table", "json"], default="table")
    for action in ("done", "undo", "remove"):
        sub.add_parser(action, parents=[common]).add_argument("id")
    args = ap.parse_args()
    root, _project, _schema = pwlib.start(args.root)
    try:
        if args.cmd == "add":
            print(add(root, args.text, args.due))
        elif args.cmd == "list":
            rows = listed(root, args.all)
            print(json.dumps(rows, ensure_ascii=False, indent=2) if args.format == "json" else table(rows))
        else:
            change(root, args.id, args.cmd)
            print("%s: %s" % (args.id, args.cmd))
    except Invalid as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
