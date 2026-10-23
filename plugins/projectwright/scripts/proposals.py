#!/usr/bin/env python3
"""proposals — the changes to the tasks that Claude proposes and the user decides.

Tasks are decided with the user (constitution, principle 13): Claude proposes a
task to create, move, close, split, edit or cancel — or a reminder to add
(reminders.py) — and writes it only after the user's yes. The proposals wait here, outside the wiki, in
.claude/.projectwright-proposals.json of the project: a proposal is not yet a
fact of the project, and a rejected one leaves nothing in the wiki. The file is
personal and never versioned; the board beside the chat (projectwright-board)
shows the open proposals and answers them.

A proposal (JSON, `add` reads it from --json or stdin):
    kind      create | move | close | cancel | split | edit | remind
    task      the task it changes (file name, without .md); absent for `create`
    summary   the change in one line ("To do -> Blocked, by the test on Windows")
    why       why Claude proposes it
    items     for create and split: the tasks, each {"title", "priority", "progress", "phase", "goal"};
              for remind: the reminders, each {"title", "due"} (due: an ISO date, optional)
    changes   for move and edit: {field: new value}
    consolidation  for close: what of the log moves to which note
The script adds `id` (P-0001, never reused), `status`, `created`, `updated`. The id is
for the tools — the board and Claude answer a proposal by it —, never shown to the
user nor written in the wiki: in chat the proposals are numbered 1, 2, 3.

Status: open -> accepted (Claude applied it) | rejected (the user said no) |
revising (the user commented, Claude is proposing again) -> revised (replaced
by the proposal that names it in `replaces`). Rejected proposals stay, so that
Claude does not propose the same thing again.

Usage (from the project root, or with --root):
    python3 proposals.py add [--json '<proposal>'] [--replaces P-0003]   prints the new id
    python3 proposals.py list [--status open|all|open,revising|...] [--format table|json]
    python3 proposals.py set <id> --status accepted|rejected|revising [--comment "<text>"]
Exit code: 0; 1 for a proposal that is not valid or not found.
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

FILE = Path(".claude") / ".projectwright-proposals.json"
KINDS = ["create", "move", "close", "cancel", "split", "edit", "remind"]
STATUSES = ["open", "accepted", "rejected", "revising", "revised"]
FIELDS = ["kind", "task", "summary", "why", "items", "changes", "consolidation"]


class Invalid(Exception):
    """A proposal that cannot be written, or an id not found."""


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def load(root):
    p = Path(root) / FILE
    if not p.is_file():
        return {"proposals": []}
    data = json.loads(p.read_text(encoding="utf-8") or "{}")
    data.setdefault("proposals", [])
    return data


def save(root, data):
    p = Path(root) / FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, p)  # a reader never sees half a file


def find(data, pid):
    for p in data["proposals"]:
        if p.get("id") == pid:
            return p
    raise Invalid("proposal not found: %s" % pid)


def check(proposal):
    kind = proposal.get("kind")
    if kind not in KINDS:
        raise Invalid("kind must be one of %s" % ", ".join(KINDS))
    if kind not in ("create", "remind") and not proposal.get("task"):
        raise Invalid("a %s proposal names the task it changes (task)" % kind)
    if not str(proposal.get("summary") or "").strip():
        raise Invalid("a proposal needs a summary")
    if kind in ("create", "split", "remind") and not proposal.get("items"):
        raise Invalid("a %s proposal lists its %s (items)" % (kind, "reminders" if kind == "remind" else "tasks"))
    if kind in ("move", "edit") and not proposal.get("changes"):
        raise Invalid("a %s proposal lists its changes (changes)" % kind)


def add(root, proposal, replaces=None):
    check(proposal)
    data = load(root)
    if replaces:
        old = find(data, replaces)
        old["status"], old["updated"] = "revised", now()
    numbers = [int(p["id"][2:]) for p in data["proposals"] if str(p.get("id", "")).startswith("P-")]
    stamp = now()
    new = {"id": "P-%04d" % (max(numbers, default=0) + 1)}
    new.update({k: proposal[k] for k in FIELDS if proposal.get(k) not in (None, "", [], {})})
    if replaces:
        new["replaces"] = replaces
    new.update(status="open", created=stamp, updated=stamp)
    data["proposals"].append(new)
    save(root, data)
    return new["id"]


def set_status(root, pid, status, comment=None):
    if status not in STATUSES:
        raise Invalid("status must be one of %s" % ", ".join(STATUSES))
    data = load(root)
    p = find(data, pid)
    p["status"], p["updated"] = status, now()
    if comment:
        p["comment"] = comment
    save(root, data)


def listed(root, status):
    rows = load(root)["proposals"]
    wanted = status.split(",")
    return rows if "all" in wanted else [p for p in rows if p.get("status") in wanted]


def table(rows):
    if not rows:
        return "(no proposals)"
    return "\n".join("%s  %-8s %-9s %s%s" % (p["id"], p.get("status", ""), p.get("kind", ""),
                                             p.get("summary", ""), "  [%s]" % p["task"] if p.get("task") else "")
                     for p in rows)


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
    a.add_argument("--json")
    a.add_argument("--replaces")
    ls = sub.add_parser("list", parents=[common])
    ls.add_argument("--status", default="open")
    ls.add_argument("--format", choices=["table", "json"], default="table")
    s = sub.add_parser("set", parents=[common])
    s.add_argument("id")
    s.add_argument("--status", required=True)
    s.add_argument("--comment")
    args = ap.parse_args()
    root, _project, _schema = pwlib.start(args.root)
    try:
        if args.cmd == "add":
            text = args.json if args.json is not None else sys.stdin.read()
            try:
                proposal = json.loads(text)
            except json.JSONDecodeError as e:
                raise Invalid("the proposal is not valid JSON: %s" % e)
            if not isinstance(proposal, dict):
                raise Invalid("a proposal is a JSON object")
            print(add(root, proposal, args.replaces))
        elif args.cmd == "list":
            rows = listed(root, args.status)
            print(json.dumps(rows, ensure_ascii=False, indent=2) if args.format == "json" else table(rows))
        else:
            set_status(root, args.id, args.status, args.comment)
            print("%s: %s" % (args.id, args.status))
    except Invalid as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
