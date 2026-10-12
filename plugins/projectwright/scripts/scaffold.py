#!/usr/bin/env python3
"""scaffold — creates the structure of a projectwright project from the templates.

Never overwrites an existing file: it only creates what is missing, so it can be
run again at any time (for example after changing the optional modules).

Usage:
    python3 scaffold.py project [--name <name>] [--language <code>] [--git] [--root <folder>]
        Creates project.yaml (from the template, if missing), docs/ (when it is the
        documentation folder), utils/, repositories/,
        the ingestion log, and the framework files: CLAUDE.md, the constitution, wiki-sources/README.md, the dashboard notes,
        team-and-roles.md, roadmap.md; writes the lock file of the framework files
        (.claude/projectwright.lock.json) and their original copy when missing.
        The project folder is NOT versioned by default (code repositories have their own git).
        With --git, or when the folder is already a git repository, it also writes .gitignore,
        .gitattributes and .githooks/pre-commit, initialises git and activates the hooks.
        No empty folders: the folders of the wiki are born with their first file; it removes
        .gitkeep files next to real content and folders that hold only a .gitkeep.

    python3 scaffold.py component <name> --code <CODE> [--repository <folder>]
                                  [--status planned|active] [--root <folder>]
        Creates wiki/components/<name>/ with its entry note and roadmap; decisions/,
        questions/ and tasks/ are born with their first record. The component must already
        be registered in project.yaml.

The root defaults to the current directory for `project`, to the project found
automatically for `component`.
"""
import argparse
import datetime
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

T = pwlib.TEMPLATES_DIR
TODAY = datetime.date.today().isoformat()

FILES = [  # template (relative to templates/) -> destination (relative to the root)
    ("CLAUDE.md", "CLAUDE.md"),
    ("wiki/README.md", "wiki/README.md"),
    ("wiki-sources/README.md", "wiki-sources/README.md"),
    ("wiki/dashboard/project-status.md", "wiki/dashboard/project-status.md"),
    ("wiki/dashboard/operating-assumptions.md", "wiki/dashboard/operating-assumptions.md"),
    ("wiki/dashboard/knowledge-map.md", "wiki/dashboard/knowledge-map.md"),
    ("wiki/dashboard/glossary.md", "wiki/dashboard/glossary.md"),
    ("wiki/project/team-and-roles.md", "wiki/project/team-and-roles.md"),
    ("wiki/roadmap.md", "wiki/roadmap.md"),
]
GIT_FILES = [  # only when the project folder is versioned with git (on request)
    ("gitignore", ".gitignore"),
    ("gitattributes", ".gitattributes"),
    ("githooks/pre-commit", ".githooks/pre-commit"),
]
LOG_HEADER = "document,source_path,hash,ingested_on,result,card,integrated,note\n"


def plugin_version():
    with open(pwlib.PLUGIN_DIR / ".claude-plugin" / "plugin.json", encoding="utf-8") as f:
        return json.load(f).get("version", "0.0.0")


def fill(text, values):
    for k, v in values.items():
        text = text.replace(k, v)
    return text


class Result:
    def __init__(self):
        self.created, self.kept, self.removed = [], [], []

    def write(self, root, rel, text, executable=False):
        dest = Path(root) / rel
        if dest.exists():
            self.kept.append(rel)
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if executable:
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.created.append(rel)

    def folder(self, root, rel):
        d = Path(root) / rel
        if not d.exists():
            d.mkdir(parents=True)
            self.created.append(rel + "/")

    def report(self):
        for rel in self.created:
            print("created  %s" % rel)
        for rel in self.removed:
            print("tidied   %s" % rel)
        if self.kept:
            print("kept     %d existing file(s), not overwritten" % len(self.kept))


def tidy(root, res, tops):
    """Removes .gitkeep files next to real content, and folders holding only a .gitkeep
    (except the top folders themselves): folders are born with their first file."""
    for top in tops:
        base = Path(root) / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in sorted(os.walk(base, topdown=False), key=lambda x: -len(x[0])):
            d = Path(dirpath)
            entries = [e for e in d.iterdir() if e.name != ".gitkeep"]
            keep = d / ".gitkeep"
            if entries and keep.exists():
                keep.unlink()
                res.removed.append(pwlib.rel(root, keep))
            elif not entries and d != base:
                if keep.exists():
                    keep.unlink()
                d.rmdir()
                res.removed.append(pwlib.rel(root, d) + "/")


def keep_empty_folders(root, folders):
    for rel in folders:
        d = Path(root) / rel
        if d.is_dir() and not any(d.iterdir()):
            (d / ".gitkeep").touch()


def cmd_project(args):
    root = Path(args.root or os.getcwd()).resolve()
    res = Result()
    values = {"YYYY-MM-DD": TODAY}
    if not (root / "project.yaml").exists():
        text = (T / "project.yaml").read_text(encoding="utf-8")
        text = fill(text, {"{{framework_version}}": plugin_version(),
                           "{{project_name}}": args.name or root.name,
                           "{{language}}": args.language or "en"})
        res.write(root, "project.yaml", text)
    try:
        project = pwlib.load_project(root)
    except pwlib.ConfigError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 3

    # Folders are born with their first file; only utils/ (the place for the files
    # the user asks for), repositories/ (ignored by git) and the documentation folder
    # when it is inside the project (docs/: its structure is the user's) exist from the start.
    utils = str(pwlib.get(project, "paths.utils") or "utils")
    keep = [utils]
    docs = pwlib.get(project, "paths.official_docs")
    if docs and not Path(str(docs)).is_absolute() and not str(docs).startswith(".."):
        keep.append(str(docs))
    for rel in keep + [str(pwlib.get(project, "paths.repositories") or "repositories")]:
        res.folder(root, rel)

    versioned = args.git or (root / ".git").exists()
    for src, dest in FILES + (GIT_FILES if versioned else []):
        text = (T / src).read_text(encoding="utf-8")
        if dest.endswith(".md") and text.startswith("---"):  # notes only: framework READMEs stay identical
            text = fill(text, values)
        res.write(root, dest, text, executable=dest.startswith(".githooks/"))
    res.write(root, "wiki-sources/ingestion-log.csv", LOG_HEADER)
    keep_empty_folders(root, keep)
    tidy(root, res, ["wiki", "wiki-sources"] + keep)

    if versioned:  # the project folder is versioned only when the user asks for it
        if not (root / ".git").exists():
            subprocess.run(["git", "init", "-q"], cwd=root, check=False)
            print("git      initialised a repository for the project folder")
        r = subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=root, check=False)
        if r.returncode == 0:
            print("git      hooks active (core.hooksPath = .githooks)")
    framework = [sys.executable, str(pwlib.SCRIPTS_DIR / "framework.py"), "lock", "--root", str(root)]
    # the lock is written whether the plugin is installed or copied into the project
    if not (root / pwlib.LOCK_REL).exists():
        subprocess.run(framework, check=False)
    else:  # framework files created now (e.g. the git hook) join the existing lock
        new = [d for _s, d in GIT_FILES if d in res.created and d == ".githooks/pre-commit"]
        if new:
            subprocess.run(framework + ["--add", *new], check=False)
    res.report()
    errors = pwlib.validate_project(project, pwlib.load_schema())
    if errors:
        print("\nproject.yaml still to complete:")
        for e in errors:
            print("  - " + e)
    return 0


def cmd_component(args):
    root = pwlib.find_root(args.root)
    if root is None:
        print("ERROR: project.yaml not found", file=sys.stderr)
        return 3
    project = pwlib.load_project(root)
    registered = {c.get("name"): c for c in (pwlib.get(project, "components") or []) if isinstance(c, dict)}
    if args.name not in registered:
        print("ERROR: register the component %s in project.yaml first" % args.name, file=sys.stderr)
        return 2
    comp = registered[args.name]
    code = args.code or comp.get("code")
    repo = args.repository or comp.get("repository") or args.name
    res = Result()
    base = "wiki/components/%s" % args.name
    values = {"YYYY-MM-DD": TODAY, "<repo>": args.name, "<CODE>": code}
    note = fill((T / "records" / "component.md").read_text(encoding="utf-8"), values)
    note = note.replace("component_status: planned", "component_status: %s" % args.status)
    note = note.replace("repository: %s" % args.name, "repository: %s" % repo)
    note = re.sub(r"source:\n  - \"\[\[<card-or-note>\]\]\"\n", 'source: "working session %s"\n' % TODAY, note)
    res.write(root, base + "/%s.md" % args.name, note)
    res.write(root, base + "/%s-roadmap.md" % args.name,
              fill((T / "records" / "component-roadmap.md").read_text(encoding="utf-8"), values))
    res.report()
    return 0


def main():
    pwlib.ensure_python()
    pwlib.setup_output()
    err = pwlib.check_python()
    if err:
        print("ERROR: " + err, file=sys.stderr)
        return 3
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("project")
    p.add_argument("--name")
    p.add_argument("--language")
    p.add_argument("--git", action="store_true", help="version the project folder with git (on the user's request)")
    p.add_argument("--root")
    c = sub.add_parser("component")
    c.add_argument("name")
    c.add_argument("--code")
    c.add_argument("--repository")
    c.add_argument("--status", choices=["planned", "active"], default="active")
    c.add_argument("--root")
    args = ap.parse_args()
    return cmd_project(args) if args.command == "project" else cmd_component(args)


if __name__ == "__main__":
    sys.exit(main())
