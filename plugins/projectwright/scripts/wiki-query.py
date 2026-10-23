#!/usr/bin/env python3
"""wiki-query — queries the frontmatter of the wiki on the fly. Read-only.

Usage (from the project root, or with --root):
    python3 wiki-query.py dashboard [--format md]
    python3 wiki-query.py questions [--lifecycle open] [--gate red] [--component FE] [--level project]
    python3 wiki-query.py decisions [--area ARCH] [--status decided] [--component FE]
    python3 wiki-query.py tasks     [--progress in-progress] [--phase sprint-1] [--component FE]
    python3 wiki-query.py task <file name or ID>   (one task in full: fields, body, linked notes)
    python3 wiki-query.py sources   [--integrated no]
    python3 wiki-query.py deviations          (framework files changed in the project, and the
                                               ADRs marked framework_deviation that motivate them)

Common options:
    --component <code or name>   only records of that component
    --level project|component    only cross-cutting records, or only component records
    --area <code>                only records with that area code
    --status <status>            only records with that epistemic status
    --format table|json|md       output format (default: table); dashboard in JSON is one object
                                 with its sections
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


class NotFound(Exception):
    """The record asked for is not in the wiki."""


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


def cell(r, getter):
    v = getter(r) if callable(getter) else r.get(getter)
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(map(str, v))
    return str(v)


def plain_rows(rows, columns):
    """The rows as the JSON of every command prints them: one object per row, strings only."""
    return [{h: cell(r, g) for h, g in columns} for r in rows]


def render(rows, columns, fmt, title=None):
    """rows: list of dicts; columns: list of (header, key or function)."""
    if fmt == "json":
        return json.dumps(plain_rows(rows, columns), ensure_ascii=False, indent=2)
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
# JSON is read by programs (the boards): the title and the fields of a card too
T_JSON_COLS = T_COLS + [("title", "title"), ("id", "id"), ("updated", "updated"), ("closed_on", "closed_on"),
                        ("blocked_by", lambda r: ", ".join(pwlib.links_in(r.get("blocked_by"))))]
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
    return render(rows, T_JSON_COLS if args.format == "json" else T_COLS, args.format)


def task_detail(root, r):
    """A task record in full, as `task --format json` prints it and board.html reads it."""
    _fm, _err, text = pwlib.read_frontmatter(Path(root) / r["_path"])
    body = pwlib.body_of(text)
    links = []
    for value in [v for k, v in r.items() if not k.startswith("_")] + [body]:
        links += [n for n in pwlib.links_in(value) if n not in links and n != r["_name"]]
    fields = {k: pwlib.plain(v) for k, v in r.items() if not k.startswith("_")}
    return dict(fields, name=r["_name"], path=r["_path"], component=r["_component"], body=body, links=links)


def cmd_task(root, project, args):
    """One task in full: every frontmatter field, its body and the notes it links."""
    wanted = (args.name or "").strip().removeprefix("[[").removesuffix("]]")
    if not wanted:
        raise NotFound("task: name the task, by file name or ID (TASK-0004)")
    found = [r for r in records(root, project)
             if r.get("type") == "task" and wanted in (r["_name"], str(r.get("id")))]
    if not found:
        raise NotFound("task not found: %s" % wanted)
    r = found[0]
    detail = task_detail(root, r)
    if args.format == "json":
        return json.dumps(detail, ensure_ascii=False, indent=2)
    body = detail["body"]
    fields = {k: pwlib.plain(v) for k, v in r.items() if not k.startswith("_")}
    head = ["%s: %s" % (k, ", ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else v))
            for k, v in fields.items()]
    if args.format == "md":
        return "### %s\n\n`%s`\n\n%s\n\n%s" % (link(r), r["_path"], "\n".join("- " + h for h in head), body)
    return "== %s (%s)\n%s\n\n%s" % (link(r), r["_path"], "\n".join("  " + h for h in head), body)


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


C_COLS = [("component", link), ("code", "code"), ("status", "component_status")]


def dashboard_sections(root, project):
    """What the dashboard shows, as records: one place for the text and for the JSON."""
    recs = records(root, project)

    class A:  # filters for select()
        component = None
        level = None
        area = status = progress = phase = None
        lifecycle = "open"
        gate = None

    open_q = select(recs, project, "question", A)
    blocking = sorted((r for r in open_q if r.get("gate") in ("red", "orange")),
                      key=lambda r: (GATE_RANK.get(r.get("gate"), 9), r["_name"]))
    decisions = [r for r in recs if r.get("type") == "decision" and r.get("status") != "superseded"]
    decisions.sort(key=lambda r: (str(r.get("updated") or ""), str(r.get("created") or ""), r["_name"]), reverse=True)
    notes = {r["_name"]: r for r in recs if r.get("type") == "component"}
    comps = [{"_name": c.get("name"), "code": c.get("code"),
              "component_status": notes.get(c.get("name"), {}).get("component_status", "(entry note missing)")}
             for c in pwlib.get(project, "components") or [] if isinstance(c, dict)]
    tasks = None
    if pwlib.get(project, "tasks.mode") == "wiki":
        tasks = sorted((r for r in recs if r.get("type") == "task" and r.get("progress") in ("in-progress", "blocked")),
                       key=lambda r: r["_name"])
    try:
        files, adrs, uncovered = deviations(root, project)
        devs = {"files": len(files), "without_adr": len(uncovered),
                "not_proposed": len([r for r in adrs if not r.get("upstream")])} if files else None
    except Exception:
        devs = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("wiki_lint", pwlib.SCRIPTS_DIR / "wiki-lint.py")
        lint_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint_mod)
        lint = len(lint_mod.lint(root, project, pwlib.load_schema()))
    except Exception:
        lint = None
    return {"name": pwlib.get(project, "project.name") or Path(root).name,
            "blocking": blocking, "others": len(open_q) - len(blocking),
            "decisions": decisions[:RECENT_DECISIONS], "components": comps, "tasks": tasks,
            "pending": [r for r in read_log(root) if r.get("integrated") == "no"],
            "deviations": devs, "lint": lint}


def dashboard_data(root, project):
    """The dashboard as data: the same sections the text shows, with the fields of the JSON
    of the commands they come from (questions, decisions, tasks, sources)."""
    d = dashboard_sections(root, project)
    return {
        "project": d["name"],
        "framework_version": pwlib.get(project, "framework.version"),
        "blocking_questions": plain_rows(d["blocking"], Q_COLS),
        "other_open_questions": d["others"],
        "recent_decisions": plain_rows(d["decisions"], D_COLS),
        "components": plain_rows(d["components"], C_COLS),
        "tasks_in_progress_or_blocked": None if d["tasks"] is None else plain_rows(d["tasks"], T_JSON_COLS),
        "pending_cards": plain_rows(d["pending"], S_COLS),
        "deviations": d["deviations"],
        "lint_violations": d["lint"],
    }


def cmd_dashboard(root, project, args):
    if args.format == "json":
        return json.dumps(dashboard_data(root, project), ensure_ascii=False, indent=2)
    fmt = "md" if args.format == "md" else "table"
    d = dashboard_sections(root, project)
    out = []
    if fmt == "md":
        out.append("## projectwright dashboard — %s\n" % d["name"])
        out.append("Computed from the wiki now (framework %s). Rules: `wiki/README.md`; "
                   "reasoned status: `wiki/dashboard/project-status.md`.\n" % (pwlib.get(project, "framework.version") or "?"))
    else:
        out.append("projectwright dashboard — %s" % d["name"])
    out.append(render(d["blocking"], Q_COLS, fmt, "Open questions 🔴/🟠 — the pre-code gate"))
    if d["others"]:
        out.append(("%d more open question(s) 🟡: `wiki-query.py questions --lifecycle open`\n" if fmt == "md"
                    else "%d more open question(s) (yellow)") % d["others"])
    out.append(render(d["decisions"], D_COLS, fmt, "Recent decisions"))
    out.append(render(d["components"], C_COLS, fmt, "Components"))
    if d["tasks"] is not None:
        out.append(render(d["tasks"], T_COLS, fmt, "Tasks in progress or blocked"))
    out.append(render(d["pending"], S_COLS, fmt, "Cards not yet integrated"))
    devs = d["deviations"]
    if devs:
        msg = "Framework files changed in this project: %d (%d without an ADR); deviations not yet proposed: %d" % (
            devs["files"], devs["without_adr"], devs["not_proposed"])
        out.append(("**%s** — `wiki-query.py deviations`, `/projectwright:propose-improvement`.\n" if fmt == "md"
                    else "%s — wiki-query.py deviations") % msg)
    if d["lint"]:
        out.append(("**Wiki lint: %d violation(s)** — run `wiki-lint.py` and fix them.\n" if fmt == "md"
                    else "Wiki lint: %d violation(s) — run wiki-lint.py") % d["lint"])
    sep = "\n" if fmt == "md" else "\n\n"
    return sep.join(out)


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["dashboard", "questions", "decisions", "tasks", "task", "sources",
                                        "deviations"])
    ap.add_argument("name", nargs="?", help="task: the task's file name or ID")
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
               "tasks": cmd_tasks, "task": cmd_task, "sources": cmd_sources,
               "deviations": cmd_deviations}[args.command]
    try:
        print(handler(root, project, args))
    except NotFound as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
