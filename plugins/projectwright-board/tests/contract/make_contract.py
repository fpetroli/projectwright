#!/usr/bin/env python3
"""make_contract — the real output of the projectwright scripts, for the board's tests.

The board relies on the JSON of `wiki-query.py tasks` and `wiki-query.py task`
(see the README of the plugin). This script builds a sample project with the
real `scaffold.py`, adds the tasks below, checks it with the real `wiki-lint.py`,
runs the real queries and writes their output into `contract.ts`, which the
tests of the board import. A change to the scripts that changes their output
shows here first: `--check` fails, the file is written again, and the tests of
the board run on the new output.

Usage (from anywhere; Python >= 3.11, nothing to install):
    python3 make_contract.py            writes contract.ts
    python3 make_contract.py --check    fails when contract.ts is not up to date
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "projectwright" / "scripts"
OUTPUT = HERE / "contract.ts"

TASK = """---
title: {title}
type: task
id: {id}
area: {area}
progress: {progress}
priority: {priority}
phase: {phase}
assignee: {assignee}
created: 2026-01-12
updated: 2026-01-19
closed_on: {closed_on}
decisions: []
questions: []
blocked_by: {blocked_by}
commits: []
---

# {id} — {title}

**Goal** — {goal}

**Acceptance criteria**
- {criterion}

**Notes** — {notes}
"""

# The sample project: one component and a cross-cutting task, every progress,
# a block and links in the body.
TASKS = [
    dict(folder="wiki/components/web/tasks", name="T-WEB-0001-checkout-page", id="T-WEB-0001", area="WEB",
         title="Checkout page", progress="in-progress", priority="high", phase="sprint-1",
         assignee="frontend developer", closed_on="", blocked_by="[]",
         goal="A checkout page that leads to [[T-WEB-0002-payment-step]].",
         criterion="The customer sees the order before paying.", notes="Part of [[web]]."),
    dict(folder="wiki/components/web/tasks", name="T-WEB-0002-payment-step", id="T-WEB-0002", area="WEB",
         title="Payment step", progress="todo", priority="medium", phase="sprint-1",
         assignee="frontend developer", closed_on="", blocked_by="[]",
         goal="The payment step of the checkout.", criterion="A failed payment can be tried again.",
         notes="After [[T-WEB-0001-checkout-page]]."),
    dict(folder="wiki/components/web/tasks", name="T-WEB-0003-order-history", id="T-WEB-0003", area="WEB",
         title="Order history", progress="blocked", priority="low", phase="sprint-2", assignee="",
         closed_on="", blocked_by='\n  - "[[T-WEB-0002-payment-step]]"',
         goal="The customer's past orders.", criterion="Orders are listed newest first.", notes="None."),
    dict(folder="wiki/components/web/tasks", name="T-WEB-0004-old-cart", id="T-WEB-0004", area="WEB",
         title="Old cart", progress="cancelled", priority="low", phase="", assignee="",
         closed_on="2026-01-15", blocked_by="[]",
         goal="The cart of the first version.", criterion="None.", notes="Replaced by the checkout page."),
    dict(folder="wiki/tasks", name="T-PRJ-0001-release-notes", id="T-PRJ-0001", area="PRJ",
         title="Release notes", progress="done", priority="medium", phase="sprint-1", assignee="maintainer",
         closed_on="2026-01-19", blocked_by="[]",
         goal="Notes for the first release.", criterion="Every change is listed.", notes="None."),
]


def run(args, cwd):
    done = subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8")
    if done.returncode != 0:
        sys.exit("make_contract: %s failed:\n%s%s" % (Path(args[0]).name, done.stdout, done.stderr))
    return done.stdout


def build():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run([SCRIPTS / "scaffold.py", "project", "--name", "sample", "--language", "en", "--root", root], root)
        project = root / "project.yaml"
        text = project.read_text(encoding="utf-8")
        entry = "components:\n  - name: web\n    code: WEB\n    repository: web\n"
        project.write_text(text.replace("components: []", entry.rstrip("\n"), 1), encoding="utf-8")
        run([SCRIPTS / "scaffold.py", "component", "web", "--code", "WEB", "--status", "active", "--root", root], root)
        for t in TASKS:
            folder = root / t["folder"]
            folder.mkdir(parents=True, exist_ok=True)
            fields = {k: v for k, v in t.items() if k not in ("folder", "name")}
            (folder / (t["name"] + ".md")).write_text(TASK.format(**fields), encoding="utf-8")
        run([SCRIPTS / "wiki-lint.py", "--root", root], root)
        tasks = json.loads(run([SCRIPTS / "wiki-query.py", "tasks", "--format", "json", "--root", root], root))
        details = {t["name"]: json.loads(run([SCRIPTS / "wiki-query.py", "task", t["name"], "--format", "json",
                                              "--root", root], root)) for t in TASKS}
    return ("// The real output of the projectwright scripts on a sample project.\n"
            "// Written by make_contract.py: do not edit; run it again after changing the scripts.\n\n"
            "export const TASKS: Record<string, unknown>[] = %s\n\n"
            "export const DETAILS: Record<string, Record<string, unknown>> = %s\n"
            % (json.dumps(tasks, ensure_ascii=False, indent=2), json.dumps(details, ensure_ascii=False, indent=2)))


def main():
    sys.path.insert(0, str(SCRIPTS))
    import pwlib  # noqa: E402

    pwlib.ensure_python()  # re-runs this script with a newer Python when "python3" is too old
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail when contract.ts is not up to date")
    args = ap.parse_args()
    text = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != text:
            print("contract.ts is not up to date with the scripts: run make_contract.py, then the tests "
                  "of the board.", file=sys.stderr)
            return 1
        print("contract.ts is up to date.")
        return 0
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print("written: %s" % OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
