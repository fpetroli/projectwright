#!/usr/bin/env python3
"""wiki-query — queries the frontmatter of the wiki on the fly. Read-only.

Usage (from the project root, or with --root):
    python3 wiki-query.py dashboard [--format md]
    python3 wiki-query.py questions [--lifecycle open] [--gate red] [--component FE] [--level project]
    python3 wiki-query.py decisions [--area ARCH] [--status decided] [--component FE]
    python3 wiki-query.py tasks     [--progress in-progress] [--phase sprint-1] [--component FE]
    python3 wiki-query.py sources   [--integrated no]
    python3 wiki-query.py deviations          (framework files changed in the project, and the
                                               ADRs marked framework_deviation that motivate them)

Common options:
    --component <code or name>   only records of that component
    --level project|component    only cross-cutting records, or only component records
    --area <code>                only records with that area code
    --status <status>            only records with that epistemic status
    --format table|json|md       output format (default: table)
    --hook                       for the SessionStart hook: never fails, prints nothing
                                 outside a projectwright project

Lists are computed from the files every time: nothing is generated or stored.
"""
import argparse
import csv
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

RECENT_DECISIONS = 8


def records(root, project):
    """Every wiki file with a valid frontmatter, as a dict with some extra keys."""
    comps = {c.get("name"): c for c in (pwlib.get(project, "components") or []) if isinstance(c, dict)}
    out = []
    for p in pwlib.wiki_files(root):
        if p.name == "README.md":
            continue
        fm, err, _text = pwlib.read_frontmatter(p)
        if fm is None:
            continue
        rp = pwlib.rel(root, p)
        parts = Path(rp).parts
        component = None
        if len(parts) > 3 and parts[0] == "wiki" and parts[1] == "components":
            comp = comps.get(parts[2])
            component = (comp or {}).get("code") or parts[2]
        r = {k: (v.isoformat() if isinstance(v, datetime.date) else v) for k, v in fm.items()}
        r["_path"] = rp
        r["_name"] = p.stem
        r["_component"] = component
        out.append(r)
    return out


def match_component(r, wanted, project):
    if not wanted:
        return True
    codes = {wanted}
    for c in pwlib.get(project, "components") or []:
        if isinstance(c, dict) and wanted in (c.get("name"), c.get("code")):
            codes = {c.get("code"), c.get("name")}
    return r["_component"] in codes


def select(recs, project, rtype, args):
    out = []
    for r in recs:
        if r.get("type") != rtype:
            continue
        if not match_component(r, getattr(args, "component", None), project):
            continue
        level = getattr(args, "level", None)
        if level == "project" and r["_component"]:
            continue
        if level == "component" and not r["_component"]:
            continue
        ok = True
        for field in ("area", "status", "lifecycle", "gate", "progress", "phase"):
            wanted = getattr(args, field, None)
            if wanted and str(r.get(field)) != wanted:
                ok = False
        if ok:
            out.append(r)
    return out


def read_log(root):
    path = Path(root) / "wiki-sources" / "ingestion-log.csv"
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def link(r):
    return "[[%s]]" % r["_name"]


def render(rows, columns, fmt, title=None):
    """rows: list of dicts; columns: list of (header, key or function)."""
    def cell(r, getter):
        v = getter(r) if callable(getter) else r.get(getter)
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join(map(str, v))
        return str(v)

    if fmt == "json":
        return json.dumps([{h: cell(r, g) for h, g in columns} for r in rows], ensure_ascii=False, indent=2)
    lines = []
    if fmt == "md":
        if title:
            lines.append("### %s\n" % title)
        if not rows:
            lines.append("_none_\n")
            return "\n".join(lines)
        lines.append("| " + " | ".join(h for h, _ in columns) + " |")
        lines.append("|" + "---|" * len(columns))
        for r in rows:
            lines.append("| " + " | ".join(cell(r, g).replace("|", "\\|").replace("\n", " ") for _, g in columns) + " |")
        return "\n".join(lines) + "\n"
    # plain table
    if title:
        lines.append("== %s" % title)
    if not rows:
        lines.append("(none)")
        return "\n".join(lines)
    table = [[h for h, _ in columns]] + [[cell(r, g).replace("\n", " ") for _, g in columns] for r in rows]
    widths = [min(max(len(row[i]) for row in table), 60) for i in range(len(columns))]
    for row in table:
        lines.append("  ".join(c[:60].ljust(w) for c, w in zip(row, widths)).rstrip())
    return "\n".join(lines)


Q_COLS = [("question", link), ("gate", "gate"), ("status", "status"), ("assumption", "assumption"),
          ("precaution", "precaution"), ("owner", "decision_owner")]
D_COLS = [("decision", link), ("status", "status"), ("area", "area"), ("updated", "updated")]
T_COLS = [("task", link), ("progress", "progress"), ("priority", "priority"), ("phase", "phase"),
          ("assignee", "assignee")]
S_COLS = [("document", "document"), ("card", "card"), ("ingested_on", "ingested_on"),
          ("result", "result"), ("integrated", "integrated")]

GATE_RANK = {"red": 0, "orange": 1, "yellow": 2}


def cmd_questions(root, project, args):
    rows = select(records(root, project), project, "question", args)
    rows.sort(key=lambda r: (GATE_RANK.get(r.get("gate"), 9), r["_name"]))
    return render(rows, Q_COLS, args.format)


def cmd_decisions(root, project, args):
    rows = select(records(root, project), project, "decision", args)
    rows.sort(key=lambda r: r["_name"])
    return render(rows, D_COLS, args.format)


def cmd_tasks(root, project, args):
    rows = select(records(root, project), project, "task", args)
    rows.sort(key=lambda r: r["_name"])
    return render(rows, T_COLS, args.format)


def cmd_sources(root, project, args):
    rows = [r for r in read_log(root) if not args.integrated or r.get("integrated") == args.integrated]
    return render(rows, S_COLS, args.format)


def load_framework_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("framework_mod", pwlib.SCRIPTS_DIR / "framework.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def deviations(root, project):
    """(changed files or None without lock, deviation ADRs, files not cited by any deviation ADR)."""
    ch = load_framework_module().changes(root)
    adrs = [r for r in records(root, project) if r.get("type") == "decision" and r.get("framework_deviation") is True]
    if ch is None:
        return None, adrs, []
    files = [("modified", f) for f in ch[0]] + [("added", f) for f in ch[1]] + [("removed", f) for f in ch[2]]
    texts = {}
    for r in adrs:
        try:
            texts[r["_name"]] = (Path(root) / r["_path"]).read_text(encoding="utf-8")
        except OSError:
            texts[r["_name"]] = ""
    def cited(f, text):  # full path, or path inside the plugin (e.g. skills/x/SKILL.md)
        prefix = pwlib.PLUGIN_IN_PROJECT + "/"
        short = f[len(prefix):] if f.startswith(prefix) else f
        return f in text or short in text

    uncovered = [f for _k, f in files if not any(cited(f, t) for t in texts.values())]
    return files, adrs, uncovered


def cmd_deviations(root, project, args):
    files, adrs, uncovered = deviations(root, project)
    out = []
    if files is None:
        out.append("No lock file (.claude/projectwright.lock.json): changes to the framework files cannot be detected.")
    else:
        rows = [{"_name": f, "change": k, "adr": "" if f in uncovered else "yes"} for k, f in files]
        out.append(render(rows, [("file", "_name"), ("change", "change"), ("covered by an ADR", "adr")],
                          args.format, "Framework files changed in this project"))
    out.append(render(sorted(adrs, key=lambda r: r["_name"]),
                      [("decision", link), ("status", "status"), ("upstream", "upstream"), ("updated", "updated")],
                      args.format, "Deviations recorded (ADR with framework_deviation: true)"))
    if uncovered:
        out.append("%d changed file(s) without an ADR: run /projectwright:record-decisions." % len(uncovered))
    return "\n\n".join(out)


def cmd_dashboard(root, project, args):
    fmt = "md" if args.format == "md" else "table"
    recs = records(root, project)
    name = pwlib.get(project, "project.name") or Path(root).name
    out = []
    if fmt == "md":
        out.append("## projectwright dashboard — %s\n" % name)
        out.append("Computed from the wiki now (framework %s). Rules: `wiki/README.md`; "
                   "reasoned status: `wiki/dashboard/project-status.md`.\n" % (pwlib.get(project, "framework.version") or "?"))
    else:
        out.append("projectwright dashboard — %s" % name)

    class A:  # filters for select()
        component = None
        level = None
        area = status = progress = phase = None
        lifecycle = "open"
        gate = None

    open_q = select(recs, project, "question", A)
    blocking = sorted((r for r in open_q if r.get("gate") in ("red", "orange")),
                      key=lambda r: (GATE_RANK.get(r.get("gate"), 9), r["_name"]))
    out.append(render(blocking, Q_COLS, fmt, "Open questions 🔴/🟠 — the pre-code gate"))
    others = len(open_q) - len(blocking)
    if others:
        out.append(("%d more open question(s) 🟡: `wiki-query.py questions --lifecycle open`\n" if fmt == "md"
                    else "%d more open question(s) (yellow)") % others)

    decisions = [r for r in recs if r.get("type") == "decision" and r.get("status") != "superseded"]
    decisions.sort(key=lambda r: (str(r.get("updated") or ""), str(r.get("created") or ""), r["_name"]), reverse=True)
    out.append(render(decisions[:RECENT_DECISIONS], D_COLS, fmt, "Recent decisions"))

    comps = []
    notes = {r["_name"]: r for r in recs if r.get("type") == "component"}
    for c in pwlib.get(project, "components") or []:
        if isinstance(c, dict):
            n = notes.get(c.get("name"), {})
            comps.append({"_name": c.get("name"), "code": c.get("code"),
                          "component_status": n.get("component_status", "(entry note missing)")})
    out.append(render(comps, [("component", link), ("code", "code"), ("status", "component_status")],
                      fmt, "Components"))

    if pwlib.get(project, "tasks.mode") == "wiki":
        tasks = [r for r in recs if r.get("type") == "task" and r.get("progress") in ("in-progress", "blocked")]
        out.append(render(sorted(tasks, key=lambda r: r["_name"]), T_COLS, fmt, "Tasks in progress or blocked"))

    pending = [r for r in read_log(root) if r.get("integrated") == "no"]
    out.append(render(pending, S_COLS, fmt, "Cards not yet integrated"))

    try:
        files, adrs, uncovered = deviations(root, project)
    except Exception:
        files, adrs, uncovered = None, [], []
    if files:
        to_propose = [r for r in adrs if not r.get("upstream")]
        msg = "Framework files changed in this project: %d (%d without an ADR); deviations not yet proposed: %d" % (
            len(files), len(uncovered), len(to_propose))
        out.append(("**%s** — `wiki-query.py deviations`, `/projectwright:propose-improvement`.\n" if fmt == "md"
                    else "%s — wiki-query.py deviations") % msg)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("wiki_lint", pwlib.SCRIPTS_DIR / "wiki-lint.py")
        lint_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint_mod)
        n = len(lint_mod.lint(root, project, pwlib.load_schema()))
    except Exception:
        n = None
    if n:
        out.append(("**Wiki lint: %d violation(s)** — run `wiki-lint.py` and fix them.\n" if fmt == "md"
                    else "Wiki lint: %d violation(s) — run wiki-lint.py") % n)
    sep = "\n" if fmt == "md" else "\n\n"
    return sep.join(out)


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["dashboard", "questions", "decisions", "tasks", "sources", "deviations"])
    ap.add_argument("--component")
    ap.add_argument("--level", choices=["project", "component"])
    ap.add_argument("--area")
    ap.add_argument("--status")
    ap.add_argument("--lifecycle")
    ap.add_argument("--gate")
    ap.add_argument("--progress")
    ap.add_argument("--phase")
    ap.add_argument("--integrated")
    ap.add_argument("--format", choices=["table", "json", "md"], default="table")
    ap.add_argument("--root")
    ap.add_argument("--hook", action="store_true")
    args = ap.parse_args()

    if args.hook:
        pwlib.setup_output()
        root = pwlib.find_root(args.root, hook=True)
        if root is None:
            return 0
        err = pwlib.check_python()
        if err:
            print("projectwright: %s. Install Python 3.11+ so that the dashboard and the wiki checks work." % err)
            return 0
        try:
            project = pwlib.load_project(root)
            print(cmd_dashboard(root, project, args))
        except Exception as e:  # the start of a session must never fail
            print("projectwright: dashboard not available (%s). Run wiki-query.py dashboard." % e)
        return 0

    root, project, _schema = pwlib.start(args.root)
    handler = {"dashboard": cmd_dashboard, "questions": cmd_questions, "decisions": cmd_decisions,
               "tasks": cmd_tasks, "sources": cmd_sources, "deviations": cmd_deviations}[args.command]
    print(handler(root, project, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
