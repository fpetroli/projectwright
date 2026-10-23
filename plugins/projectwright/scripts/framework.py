#!/usr/bin/env python3
"""framework — the files provided by the framework in a project, and their changes.

The lock file .claude/projectwright.lock.json records the framework version and a
checksum of every file provided by the framework, as it was when the framework was
applied: the framework part of the root CLAUDE.md (everything before "## Project-specific
instructions"), the wiki constitution, wiki-sources/README.md, the git hooks and, when they
are copied into the project, the whole plugin (.claude/skills/projectwright/) and the whole
board (.claude/skills/projectwright-board/, without the types Claude Code writes in it).

The plugin is either installed for the project from the marketplace (the usual way: its
files live in the plugin cache of Claude Code and cannot be changed per project) or
copied into the project, where its files can be changed and every change is tracked.

Usage (from the project root, or with --root):
    python3 framework.py lock            writes the lock file from the current plugin and
                                         the plugin templates (run when the framework is
                                         applied or upgraded; never otherwise)
    python3 framework.py lock --from <plugin folder>
                                         after an upgrade: the originals are the files of that
                                         version, not the project's copy with its changes
    python3 framework.py lock --add <file> ...
                                         adds framework files created later (e.g. the git hook
                                         when the project folder becomes versioned) to the lock,
                                         from the plugin templates, without touching the rest
    python3 framework.py changes [--format table|json]
                                         files modified, added or removed since the lock
    python3 framework.py diff [<file> ...]
                                         the changes as a unified diff, against the original
                                         copy saved by `lock` in .claude/.projectwright-original/
                                         (works with or without git)
    python3 framework.py vendor          copies the running (installed) plugin into the project,
                                         to change its files: removes the installed plugin from
                                         .claude/settings.json and rewrites the lock
    python3 framework.py upgrade [--from <plugin folder>] [--base-plugin <plugin folder>] [--apply]
                                         upgrade of the framework files to the version in --from
                                         (default: the running plugin): without --apply it prints the
                                         plan; with --apply it replaces the files not changed in the
                                         project, merges the changed ones (three-way, git merge-file)
                                         and sets the conflicts aside in .claude/.projectwright-upgrade/
                                         for the user; without conflicts it closes the upgrade (lock),
                                         otherwise `lock --from` closes it once they are resolved;
                                         a board copied into the project (.claude/skills/projectwright-board)
                                         follows the plan like the plugin, against the one beside the new
                                         version; a copy not yet tracked is replaced whole, and tracked
    python3 framework.py lock --add .claude/skills/projectwright-board
                                         after copying the board into the project: tracks its files
    python3 framework.py resolved <file> ...
                                         marks the conflicts of an upgrade as resolved
    python3 framework.py permissions [--remove]
                                         lets Claude run the plugin's scripts and read its files without
                                         asking: allow rules for those only, in .claude/settings.local.json
                                         (personal, never versioned); the start-of-session check keeps
                                         them up to date when the plugin moves (a new version)
    python3 framework.py renumber-tasks [--plan | --apply]
                                         tasks numbered once for the whole project: the tasks still
                                         named T-<CODE>-NNNN become TASK-NNNN (in order of creation),
                                         with their file names, every mention in wiki/ and in the
                                         proposals and reminders; --plan (the default) only prints
                                         the plan and writes nothing, --apply applies it
    python3 framework.py check [--hook]  start-of-session check: the plugin that runs is the one the
                                         project expects (version, copy in the project); records the
                                         plugin path for the git hook (.claude/.projectwright-plugin)
Exit code: 0; 1 when an upgrade leaves conflicts; 2 when the lock file is missing or a
command cannot run; 3 on configuration errors.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

LOCK_REL = pwlib.LOCK_REL
ORIGINAL_REL = ".claude/.projectwright-original"  # pristine copy of the framework files, never edited
PLUGIN_REL = pwlib.PLUGIN_IN_PROJECT
POINTER_REL = ".claude/.projectwright-plugin"     # path of the running plugin, read by the git hook
STAGE_REL = ".claude/.projectwright-upgrade"       # conflicts of an upgrade, waiting for the user
BOARD_REL = ".claude/skills/projectwright-board"   # the optional board, when the project copies it
PLUGIN_ID = "projectwright@projectwright"          # the plugin installed from the projectwright marketplace
PROJECT_SECTION = "## Project-specific instructions"
# project file -> template that provides it
TEMPLATED = {
    "CLAUDE.md": "CLAUDE.md",
    "wiki/README.md": "wiki/README.md",
    "wiki-sources/README.md": "wiki-sources/README.md",
    ".githooks/pre-commit": "githooks/pre-commit",
}
SKIP_DIRS = {"__pycache__", ".git"}


def framework_part(rel, data):
    """The bytes of a file that belong to the framework (CLAUDE.md: up to the project section)."""
    if rel == "CLAUDE.md":
        text = data.decode("utf-8", errors="replace")
        i = text.find(PROJECT_SECTION)
        if i >= 0:
            text = text[:i]
        return text.rstrip().encode("utf-8")
    return data


def digest(rel, data):
    return "sha256:" + hashlib.sha256(framework_part(rel, data)).hexdigest()


def tree_files(base):
    """Paths relative to `base` of the files of a copied plugin: no caches, and for the board not the
    types that Claude Code writes in .claude-plugin/types/ at every load."""
    base = Path(base)
    out = []
    if not base.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = pwlib.rel(base, Path(dirpath))
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS
                             and not (rel_dir == ".claude-plugin" and d == "types"))
        for name in sorted(filenames):
            if not name.endswith(".pyc"):
                out.append(pwlib.rel(base, Path(dirpath) / name))
    return out


def plugin_files(root):
    """The files of the copy of the plugin in the project (none when the plugin is installed)."""
    return [PLUGIN_REL + "/" + r for r in tree_files(Path(root) / PLUGIN_REL)]


def board_tracked(root):
    """Whether the copy of the board is in the lock: copies made before it was tracked are not."""
    return any(r.startswith(BOARD_REL + "/") for r in ((read_lock(root) or {}).get("files") or {}))


def board_files(root):
    """The files of the copy of the board in the project, once it is tracked (or when no lock exists yet)."""
    if read_lock(root) is not None and not board_tracked(root):
        return []
    return [BOARD_REL + "/" + r for r in tree_files(Path(root) / BOARD_REL)]


def board_source(plugin_dir):
    """The board released beside a version of projectwright (`<plugin>/../projectwright-board`), or None."""
    src = Path(plugin_dir).parent / "projectwright-board"
    return src if (src / ".claude-plugin" / "plugin.json").is_file() else None


def current(root):
    """Relative path -> checksum, for the framework files present now."""
    files = {}
    for rel in plugin_files(root) + board_files(root) + [r for r in TEMPLATED if (Path(root) / r).is_file()]:
        files[rel] = digest(rel, (Path(root) / rel).read_bytes())
    return files


def templates_dir(root):
    """Templates of the copy in the project, or of the running plugin when it is installed."""
    copy = Path(root) / PLUGIN_REL / "templates"
    return copy if copy.is_dir() else pwlib.TEMPLATES_DIR


def plugin_version(root):
    """Version of the copy in the project, or of the running plugin when it is installed."""
    copy = Path(root) / PLUGIN_REL
    return pwlib.plugin_version(copy if copy.is_dir() else pwlib.PLUGIN_DIR)


def pending_conflicts(root):
    base = Path(root) / STAGE_REL
    if not base.is_dir():
        return []
    return sorted(pwlib.rel(base, p) for p in base.rglob("*") if p.is_file() and not p.name.endswith(".new"))


def originals(root, source=None):
    """Relative path -> bytes of every framework file as the framework provides it.

    source: the folder of the plugin version being applied (after an upgrade of a copy, the
    new version); by default the copy in the project, or the running plugin for the templates.
    """
    root = Path(root)
    out = {}
    if (root / PLUGIN_REL).is_dir():
        src = Path(source) if source else root / PLUGIN_REL
        for r in tree_files(src):
            out[PLUGIN_REL + "/" + r] = (src / r).read_bytes()
    if (root / BOARD_REL).is_dir():
        # the board copied into the project is tracked like the copy of the plugin. Its originals are
        # the board released beside the version applied; when that version has none, the originals
        # saved before (so that the project's changes stay changes), or the copy itself
        saved = root / ORIGINAL_REL / BOARD_REL
        src = (board_source(source) if source else root / BOARD_REL) or \
              (saved if saved.is_dir() else root / BOARD_REL)
        for r in tree_files(src):
            out[BOARD_REL + "/" + r] = (src / r).read_bytes()
    tdir = Path(source) / "templates" if source else templates_dir(root)
    for rel, template in TEMPLATED.items():
        # only for the files the project has (the git hook exists only when the folder is versioned)
        if (tdir / template).is_file() and (root / rel).is_file():
            out[rel] = (tdir / template).read_bytes()
    return out


def board_state(root):
    """How the project has the board: copied into it, installed for it, or not at all."""
    if (Path(root) / BOARD_REL).is_dir():
        return "in-project"
    try:
        enabled = read_settings(root)[1].get("enabledPlugins") or {}
    except ValueError:
        enabled = {}
    return "installed" if enabled.get("projectwright-board@projectwright") else "absent"


def cmd_lock(root, source=None):
    pending = pending_conflicts(root)
    if pending:
        print("unresolved conflicts of the upgrade (%s): %s — resolve them and run `framework.py resolved "
              "<file>` first" % (STAGE_REL, ", ".join(pending)), file=sys.stderr)
        return 2
    orig = originals(root, source)
    files = {rel: digest(rel, data) for rel, data in orig.items()}
    save_originals(root, orig)
    version = pwlib.plugin_version(source) if source else plugin_version(root)
    lock = {"framework": "projectwright", "version": version,
            "plugin": "in-project" if (Path(root) / PLUGIN_REL).is_dir() else "installed",
            "board": board_state(root),
            "locked_on": datetime.date.today().isoformat(), "files": dict(sorted(files.items()))}
    path = Path(root) / LOCK_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print("lock written: %s (%d files, version %s, plugin %s)" % (LOCK_REL, len(files), lock["version"], lock["plugin"]))
    return 0


def save_originals(root, orig):
    """Writes the pristine copy of the framework files, the base of `diff` and of the next upgrade."""
    import shutil
    base = Path(root) / ORIGINAL_REL
    if base.exists():
        shutil.rmtree(base)
    for rel, data in orig.items():
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(framework_part(rel, data) + b"\n" if rel == "CLAUDE.md" else data)


def cmd_lock_add(root, files):
    lock = read_lock(root)
    if lock is None:
        return cmd_lock(root)
    base = Path(root) / ORIGINAL_REL
    for rel in files:
        rel = rel.replace(os.sep, "/").rstrip("/")
        if rel == BOARD_REL:  # the board just copied into the project: its files are the originals
            for r in tree_files(Path(root) / BOARD_REL):
                data = (Path(root) / BOARD_REL / r).read_bytes()
                lock["files"][BOARD_REL + "/" + r] = digest(BOARD_REL + "/" + r, data)
                dest = base / BOARD_REL / r
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            lock["board"] = "in-project"
            continue
        template = TEMPLATED.get(rel)
        if not template or not (templates_dir(root) / template).is_file():
            print("not a templated framework file: %s" % rel, file=sys.stderr)
            return 2
        data = (templates_dir(root) / template).read_bytes()
        lock["files"][rel] = digest(rel, data)
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(framework_part(rel, data) + b"\n")
    lock["files"] = dict(sorted(lock["files"].items()))
    (Path(root) / LOCK_REL).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print("lock updated: %s" % ", ".join(files))
    return 0


def read_lock(root):
    path = Path(root) / LOCK_REL
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def changes(root):
    """(modified, added, removed) relative paths, or None when there is no lock file."""
    lock = read_lock(root)
    if lock is None:
        return None
    locked, now = lock.get("files", {}), current(root)
    modified = sorted(r for r in now if r in locked and now[r] != locked[r])
    added = sorted(r for r in now if r not in locked)
    # the board is optional: taking its copy away (to install it, or to drop it) is no change of the framework
    board_gone = not (Path(root) / BOARD_REL).is_dir()
    removed = sorted(r for r in locked if r not in now and not (board_gone and r.startswith(BOARD_REL + "/")))
    return modified, added, removed


def cmd_changes(root, fmt):
    ch = changes(root)
    if ch is None:
        print("no lock file (%s): run `framework.py lock` when the framework is applied" % LOCK_REL, file=sys.stderr)
        return 2
    modified, added, removed = ch
    if fmt == "json":
        print(json.dumps({"modified": modified, "added": added, "removed": removed}, indent=2))
        return 0
    for label, items in (("MODIFIED", modified), ("ADDED", added), ("REMOVED", removed)):
        for r in items:
            print("%s\t%s" % (label, r))
    print("---")
    print("Summary: %d modified, %d added, %d removed" % (len(modified), len(added), len(removed)))
    if not (modified or added or removed):
        print("the framework files are as applied")
    return 0


def cmd_diff(root, files):
    import difflib
    ch = changes(root)
    if ch is None:
        print("no lock file (%s)" % LOCK_REL, file=sys.stderr)
        return 2
    modified, added, removed = ch

    def normalise(f):  # accept paths inside the plugin, e.g. skills/x/SKILL.md
        f = f.replace(os.sep, "/")
        if not (Path(root) / f).exists() and (Path(root) / PLUGIN_REL / f).exists():
            return PLUGIN_REL + "/" + f
        return f

    targets = [normalise(f) for f in files] or (modified + added + removed)
    if not targets:
        print("no changes to the framework files")
        return 0
    base = Path(root) / ORIGINAL_REL
    if not base.is_dir():
        print("no original copy (%s): run `framework.py lock` when the framework is applied" % ORIGINAL_REL,
              file=sys.stderr)
        return 2

    def lines(path, rel):
        if not path.is_file():
            return []
        data = path.read_bytes()
        if path.parent == Path(root) and rel == "CLAUDE.md":
            data = framework_part(rel, data) + b"\n"
        return data.decode("utf-8", errors="replace").splitlines(keepends=True)

    printed = False
    for rel in targets:
        old, new = lines(base / rel, rel), lines(Path(root) / rel, rel)
        diff = list(difflib.unified_diff(old, new, "a/" + rel, "b/" + rel))
        if diff:
            printed = True
            sys.stdout.writelines(d if d.endswith("\n") else d + "\n" for d in diff)
    if not printed:
        print("no difference for: %s" % ", ".join(targets), file=sys.stderr)
    return 0


# ---------------------------------------------------------------- upgrade

def merge3(ours, base, theirs):
    """Three-way merge with git merge-file: (text, conflicts) or None when git is missing."""
    import shutil
    import subprocess
    import tempfile
    if not shutil.which("git"):
        return None
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, data in (("project", ours), ("original", base), ("new", theirs)):
            path = Path(d) / name
            path.write_bytes(data)
            paths.append(str(path))
        r = subprocess.run(["git", "merge-file", "-p", "-L", "this project", "-L", "original", "-L", "new version"]
                           + paths, capture_output=True)
        if r.returncode < 0:
            return None
        return r.stdout, r.returncode


def fw(rel, data):
    """The part of a file that the upgrade merges: for CLAUDE.md the framework part, else all of it."""
    return framework_part(rel, data) + b"\n" if rel == "CLAUDE.md" else data


def project_section(data):
    text = data.decode("utf-8", errors="replace")
    i = text.find(PROJECT_SECTION)
    return text[i:].encode("utf-8") if i >= 0 else b""


def full_text(rel, framework_bytes, project_bytes):
    """A file written back to the project: for CLAUDE.md, the framework part plus the project's own section."""
    if rel != "CLAUDE.md":
        return framework_bytes
    section = project_section(project_bytes or b"")
    return framework_bytes.rstrip() + b"\n\n" + section if section else framework_bytes


def upgrade_sources(root, new_dir, base_plugin):
    """Relative path -> (new file or None, base file or None) for every framework file concerned."""
    root, new_dir = Path(root), Path(new_dir)
    originals = Path(root) / ORIGINAL_REL
    lock = read_lock(root) or {}
    out = {}
    for rel, template in TEMPLATED.items():
        if not (root / rel).is_file() and rel not in lock.get("files", {}):
            continue  # the project never had it (e.g. the git hook of a folder that is not versioned)
        new = new_dir / "templates" / template
        base = originals / rel
        if not base.is_file() and base_plugin:
            base = Path(base_plugin) / "templates" / template
        out[rel] = (new if new.is_file() else None, base if base.is_file() else None)
    trees = []
    if (root / PLUGIN_REL).is_dir():
        trees.append((PLUGIN_REL, new_dir, Path(base_plugin) if base_plugin else None))
    new_board = board_source(new_dir)
    if (root / BOARD_REL).is_dir() and board_tracked(root) and new_board:
        # a tracked copy of the board follows the plan like the plugin; without a board beside the
        # new version it stays as it is
        trees.append((BOARD_REL, new_board, board_source(base_plugin) if base_plugin else None))
    for prefix, new_tree, base_tree in trees:
        rels = {r for r in lock.get("files", {}) if r.startswith(prefix + "/")}
        rels |= {prefix + "/" + r for r in tree_files(root / prefix)}
        rels |= {prefix + "/" + r for r in tree_files(new_tree)}
        for rel in sorted(rels):
            inner = rel[len(prefix) + 1:]
            new = new_tree / inner
            base = originals / rel
            if not base.is_file() and base_tree:
                base = base_tree / inner
            out[rel] = (new if new.is_file() else None, base if base.is_file() else None)
    return out


def upgrade_plan(root, new_dir, base_plugin):
    """List of (rel, action, detail). Actions: same, replace, add, remove, keep, merge, conflict."""
    locked = (read_lock(root) or {}).get("files", {})
    plan = []
    for rel, (new, base) in sorted(upgrade_sources(root, new_dir, base_plugin).items()):
        proj = Path(root) / rel
        p = proj.read_bytes() if proj.is_file() else None
        n = new.read_bytes() if new else None
        lk = locked.get(rel)
        n_digest = digest(rel, n) if n is not None else None
        changed_here = (p is not None and lk is None) or (p is None and lk is not None) or \
                       (p is not None and digest(rel, p) != lk)
        if p is None and lk is None:
            plan.append((rel, "add" if n is not None else "same", "new in this version"))
        elif not changed_here:
            if n is None:
                plan.append((rel, "remove", "removed in the new version"))
            elif n_digest == lk:
                plan.append((rel, "same", ""))
            else:
                plan.append((rel, "replace", "not changed in the project"))
        elif lk is None:  # added by the project
            plan.append((rel, "keep" if n is None else "conflict",
                         "added by the project" if n is None else "added by the project and by the new version"))
        elif p is None:  # deleted by the project
            plan.append((rel, "keep" if n is None or n_digest == lk else "conflict",
                         "deleted by the project" + ("" if n is None or n_digest == lk
                                                     else ", changed by the new version")))
        elif n is None:
            plan.append((rel, "conflict", "changed by the project, removed by the new version"))
        elif n_digest == lk:
            plan.append((rel, "keep", "changed by the project, unchanged by the new version"))
        elif base is None:
            plan.append((rel, "conflict", "changed by both; no original to merge from"))
        else:
            res = merge3(fw(rel, p), fw(rel, base.read_bytes()),
                         fw(rel, n))
            if res is None:
                plan.append((rel, "conflict", "changed by both; git not found to merge"))
            elif res[1] == 0:
                plan.append((rel, "merge", "changed by both, in different places"))
            else:
                plan.append((rel, "conflict", "changed by both, in the same places (%d)" % res[1]))
    return plan


def board_plan(root, new_dir):
    """The board copied into the project. A tracked copy (in the lock) follows the plan file by
    file, like the copy of the plugin: what the project changed in it is kept and merged. A copy
    made before the board was tracked is replaced whole, once, with the board released beside the
    new version, and is tracked from then on.
    Returns (action, detail, source): "tracked", "replace", "same", "keep", or None (no copy)."""
    copy = Path(root) / BOARD_REL
    if not copy.is_dir():
        return None, "", None
    src = board_source(new_dir)
    if src is None:
        return "keep", "the new version has no projectwright-board beside it: the copy stays as it is", None
    old_v, new_v = pwlib.plugin_version(copy), pwlib.plugin_version(src)
    note = "" if new_v == pwlib.plugin_version(new_dir) else " (its version differs from the framework's)"
    if board_tracked(root):
        return "tracked", "board %s -> %s%s: its files are in the plan above" % (old_v, new_v, note), src
    files = lambda base: {r: (base / r).read_bytes() for r in tree_files(base)}
    if files(copy) == files(src):
        return "same", "already the board of %s; tracked from now on" % new_v, src
    return "replace", "board %s -> %s%s; not tracked yet: replaced whole, tracked from now on" % (old_v, new_v, note), src


def apply_board(root, src):
    import shutil
    copy = Path(root) / BOARD_REL
    types = copy / ".claude-plugin" / "types"   # written by Claude Code at every load: kept
    keep = None
    if types.is_dir():
        keep = Path(root) / STAGE_REL / "board-types"
        if keep.exists():
            shutil.rmtree(keep)
        keep.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(types), str(keep))
    shutil.rmtree(copy)
    shutil.copytree(src, copy, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    if keep is not None:
        shutil.move(str(keep), str(types))
        stage = Path(root) / STAGE_REL
        if stage.is_dir() and not any(stage.iterdir()):
            stage.rmdir()


def cmd_upgrade(root, new_dir, base_plugin, apply, fmt):
    lock = read_lock(root)
    if lock is None:
        print("no lock file (%s): the upgrade needs it" % LOCK_REL, file=sys.stderr)
        return 2
    new_dir = Path(new_dir or pwlib.PLUGIN_DIR).resolve()
    if not (new_dir / ".claude-plugin" / "plugin.json").is_file():
        print("not a projectwright plugin folder: %s" % new_dir, file=sys.stderr)
        return 2
    copy = (Path(root) / PLUGIN_REL).resolve()
    if new_dir == copy:
        print("--from is the copy of the plugin in this project: give the folder of the new version", file=sys.stderr)
        return 2
    old, new = lock.get("version", "?"), pwlib.plugin_version(new_dir)
    if pending_conflicts(root):
        print("an upgrade is already in progress: resolve the conflicts in %s first" % STAGE_REL, file=sys.stderr)
        return 2
    plan = upgrade_plan(root, new_dir, base_plugin)
    board_action, board_detail, board_src = board_plan(root, new_dir)
    if fmt == "json":
        print(json.dumps({"from_version": old, "to_version": new, "source": str(new_dir),
                          "plan": [{"file": r, "action": a, "detail": d} for r, a, d in plan],
                          "board": None if board_action is None else
                          {"folder": BOARD_REL, "action": board_action, "detail": board_detail}}, indent=2))
    else:
        print("upgrade of the framework files: %s -> %s (from %s)" % (old, new, new_dir))
        for r, a, d in plan:
            if a != "same":
                print("%s\t%s%s" % (a.upper(), r, "\t" + d if d else ""))
        counts = {}
        for _r, a, _d in plan:
            counts[a] = counts.get(a, 0) + 1
        print("---")
        print("Summary: " + ", ".join("%d %s" % (counts.get(k, 0), k) for k in
                                      ("replace", "add", "remove", "merge", "keep", "conflict", "same")))
        if board_action is not None:
            print("Board: %s\t%s\t%s" % (board_action.upper(), BOARD_REL, board_detail))
    if not apply:
        return 0

    stage = Path(root) / STAGE_REL
    sources = upgrade_sources(root, new_dir, base_plugin)
    conflicts = []
    for rel, action, _d in plan:
        proj = Path(root) / rel
        new, base = sources[rel]
        p = proj.read_bytes() if proj.is_file() else None
        n = new.read_bytes() if new else None
        if action in ("replace", "add"):
            proj.parent.mkdir(parents=True, exist_ok=True)
            proj.write_bytes(full_text(rel, fw(rel, n), p))
        elif action == "remove":
            proj.unlink()
        elif action == "merge":
            merged, _c = merge3(fw(rel, p), fw(rel, base.read_bytes()),
                                fw(rel, n))
            proj.write_bytes(full_text(rel, merged, p))
        elif action == "conflict":
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            res = merge3(fw(rel, p), fw(rel, base.read_bytes()),
                         fw(rel, n)) if (p is not None and n is not None and base) else None
            # the file with the conflict markers, or the project's version; the new version beside it
            target.write_bytes(res[0] if res else (p if p is not None else b""))
            Path(str(target) + ".new").write_bytes(n if n is not None else b"")
            conflicts.append(rel)
    if board_action == "replace":
        apply_board(root, board_src)
        print("board replaced: %s (%s)" % (BOARD_REL, board_detail))
    print("applied: %d file(s) replaced or added, %d removed, %d merged" % (
        sum(1 for _r, a, _d in plan if a in ("replace", "add")),
        sum(1 for _r, a, _d in plan if a == "remove"),
        sum(1 for _r, a, _d in plan if a == "merge")))
    if conflicts:
        print("CONFLICTS (%d), set aside in %s: for each, <file> holds the merge with the markers (or the "
              "project's version) and <file>.new the new version. Write the resolution into the project file, "
              "then run `framework.py resolved <file>`; at the end `framework.py lock --from %s`."
              % (len(conflicts), STAGE_REL, new_dir))
        for rel in conflicts:
            print("  " + rel)
        return 1
    print("no conflicts: closing the upgrade")
    return cmd_lock(root, str(new_dir))


def cmd_resolved(root, files):
    import shutil
    stage = Path(root) / STAGE_REL
    for f in files:
        f = f.replace(os.sep, "/")
        for candidate in (stage / f, Path(str(stage / f) + ".new")):
            if candidate.exists():
                candidate.unlink()
    if stage.is_dir() and not any(p.is_file() for p in stage.rglob("*")):
        shutil.rmtree(stage)
    left = pending_conflicts(root)
    print("conflicts left: %s" % (", ".join(left) if left else "none — run `framework.py lock --from <new version>`"))
    return 0


def read_settings(root):
    path = Path(root) / ".claude" / "settings.json"
    if not path.is_file():
        return path, {}
    return path, json.loads(path.read_text(encoding="utf-8") or "{}")


def cmd_vendor(root):
    import shutil
    dest = Path(root) / PLUGIN_REL
    if dest.exists():
        print("the plugin is already copied into the project: %s" % PLUGIN_REL, file=sys.stderr)
        return 2
    src = pwlib.PLUGIN_DIR
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    # an installed plugin with the same name takes the name even when it is set to false, and the
    # copy is not loaded: the entry is removed (the marketplace may stay declared)
    try:
        path, settings = read_settings(root)
    except ValueError as e:
        print("plugin copied, but .claude/settings.json is not valid JSON (%s): remove \"%s\" "
              "from enabledPlugins by hand" % (e, PLUGIN_ID), file=sys.stderr)
        settings = None
    if settings is not None and PLUGIN_ID in (settings.get("enabledPlugins") or {}):
        del settings["enabledPlugins"][PLUGIN_ID]
        if not settings["enabledPlugins"]:
            del settings["enabledPlugins"]
        path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    cmd_lock(root)  # changes made earlier to CLAUDE.md, constitution… stay visible: their originals are the templates
    print("plugin %s copied from %s into %s" % (plugin_version(root), src, PLUGIN_REL))
    print('the installed plugin is no longer enabled for this project ("%s" removed from .claude/settings.json)' % PLUGIN_ID)
    print("run /reload-plugins (or restart Claude Code): the skills now come from the copy in the project")
    return 0


LOCAL_SETTINGS_REL = ".claude/settings.local.json"


def permission_rules():
    """Allow rules for the scripts of the running plugin, and only those.

    For a plugin installed from the marketplace the folder of the version
    (cache/<marketplace>/<plugin>/<version>) becomes *, so the rules survive upgrades.
    """
    base = pwlib.PLUGIN_DIR
    if base.parent.parent.parent.name == "cache":
        base = base.parent / "*"
    base = base.as_posix()
    rules = []
    for py in ("python3", "python"):
        for sub in ("scripts", "skills"):
            rules.append('Bash(%s "%s/%s/*)' % (py, base, sub))
            rules.append("Bash(%s %s/%s/*)" % (py, base, sub))
    # the skills read the templates and the schema of the plugin, which may live outside the project
    rules.append("Read(/%s/**)" % base if base.startswith("/") else "Read(//%s/**)" % base)
    return rules


def is_projectwright_rule(rule):
    if rule.startswith("Read(/") and rule.rstrip(")").endswith("/projectwright/**") or "/projectwright/*/**" in rule:
        return True
    return rule.startswith("Bash(python") and ("/projectwright/scripts/" in rule or "/projectwright/skills/" in rule
                                               or "/projectwright/*/scripts/" in rule or "/projectwright/*/skills/" in rule)


def write_permissions(root, remove=False):
    """Rewrites the projectwright rules in the local settings. Returns True when the file changed."""
    path = Path(root) / LOCAL_SETTINGS_REL
    settings = json.loads(path.read_text(encoding="utf-8") or "{}") if path.is_file() else {}
    perms = settings.setdefault("permissions", {})
    allow = perms.get("allow", [])
    kept = [r for r in allow if not is_projectwright_rule(r)]
    new = kept if remove else kept + permission_rules()
    if new == allow:
        return False
    perms["allow"] = new
    if not perms["allow"]:
        del perms["allow"]
    if not perms:
        del settings["permissions"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return True


def cmd_permissions(root, remove):
    try:
        changed = write_permissions(root, remove)
    except ValueError as e:
        print("%s is not valid JSON (%s): fix it first" % (LOCAL_SETTINGS_REL, e), file=sys.stderr)
        return 2
    if remove:
        print("projectwright rules %s %s" % ("removed from" if changed else "were not in", LOCAL_SETTINGS_REL))
    else:
        print("%s: Claude runs the scripts of the plugin without asking (%s)" % (
            LOCAL_SETTINGS_REL, "rules written" if changed else "rules already up to date"))
        for r in permission_rules()[:2]:
            print("  " + r)
    return 0


def session_warnings(root):
    """Problems of the plugin setup, for the start of a session."""
    out = []
    copy = Path(root) / PLUGIN_REL
    if copy.is_dir() and not pwlib.plugin_in_project(root):
        out.append("projectwright: the plugin running is NOT the copy in this project (%s) but the installed "
                   "%s, which takes precedence over it. Remove \"%s\" from enabledPlugins in the settings that "
                   "name it — even set to false it keeps the copy from loading: .claude/settings.json, "
                   ".claude/settings.local.json, or for an install on the whole machine `claude plugin uninstall "
                   "%s --scope user` — then /reload-plugins." % (PLUGIN_REL, pwlib.PLUGIN_DIR, PLUGIN_ID, PLUGIN_ID))
    lock = read_lock(root)
    running = pwlib.plugin_version()
    if lock and lock.get("version") not in (None, "?") and running != "?" and lock["version"] != running:
        out.append("projectwright: the plugin is at version %s, but the project was set up or last upgraded "
                   "with %s: run /projectwright:upgrade to bring the project to %s (or ask the user, to stay on %s)."
                   % (running, lock["version"], running, lock["version"]))
    return out


def cmd_check(root, hook):
    try:
        pointer = Path(root) / POINTER_REL
        pointer.parent.mkdir(parents=True, exist_ok=True)
        current_text = pointer.read_text(encoding="utf-8").strip() if pointer.is_file() else ""
        if current_text != str(pwlib.PLUGIN_DIR):
            pointer.write_text(str(pwlib.PLUGIN_DIR) + "\n", encoding="utf-8")
    except OSError:
        pass
    # the permission rules follow the plugin when it moves, only if the user turned them on
    try:
        local = Path(root) / LOCAL_SETTINGS_REL
        if local.is_file() and any(is_projectwright_rule(r) for r in
                                   json.loads(local.read_text(encoding="utf-8") or "{}")
                                   .get("permissions", {}).get("allow", [])):
            write_permissions(root)
    except (OSError, ValueError):
        pass
    # Claude needs the path to run the scripts outside the skills (CLAUDE.md, "<plugin>")
    print("projectwright plugin %s: %s (%s; scripts in its scripts/ folder, path also in %s)" % (
        pwlib.plugin_version(), pwlib.PLUGIN_DIR,
        "copy in the project" if pwlib.plugin_in_project(root) else "installed", POINTER_REL))
    for w in session_warnings(root):
        print(w)
    return 0


OLD_TASK_ID = re.compile(r"\bT-([A-Z]{2,8})-([0-9]{4})\b")
NEW_TASK_ID = re.compile(r"^TASK-([0-9]{4})$")
OWN_FILES = [Path(".claude") / ".projectwright-proposals.json", Path(".claude") / ".projectwright-reminders.json"]


def task_renumbering(root):
    """{old id: new id} for the tasks still numbered per code, in order of creation, after the existing TASK ids."""
    old, highest = [], 0
    for p in pwlib.wiki_files(root):
        fm, _err, _text = pwlib.read_frontmatter(p)
        if not fm or fm.get("type") != "task":
            continue
        rid = str(fm.get("id") or "")
        m = NEW_TASK_ID.match(rid)
        if m:
            highest = max(highest, int(m.group(1)))
            continue
        m = OLD_TASK_ID.fullmatch(rid)
        if m:
            old.append((str(fm.get("created") or ""), m.group(1), int(m.group(2)), rid))
    old.sort()
    return {rid: "TASK-%04d" % (highest + i) for i, (_c, _code, _n, rid) in enumerate(old, start=1)}


def cmd_renumber_tasks(root, apply):
    mapping = task_renumbering(root)
    if not mapping:
        print("no task to renumber: every task is already TASK-NNNN")
        return 0
    for old, new in mapping.items():
        print("%s -> %s" % (old, new))
    if not apply:
        print("---\n%d task(s) to renumber: run again with --apply" % len(mapping))
        return 0
    swap = lambda text: OLD_TASK_ID.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)
    changed, untouched = 0, []
    for p in pwlib.wiki_files(root):
        text = p.read_text(encoding="utf-8")
        new_text = swap(text)
        if new_text == text:
            continue
        if pwlib.rel(root, p).startswith("wiki-sources/"):
            untouched.append(pwlib.rel(root, p))  # the cards are immutable: reported, not changed
            continue
        p.write_text(new_text, encoding="utf-8", newline="\n")
        changed += 1
    for own in OWN_FILES:
        p = Path(root) / own
        if p.is_file():
            p.write_text(swap(p.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    renamed = 0
    for p in pwlib.wiki_files(root):
        m = OLD_TASK_ID.match(p.stem)
        if m and m.group(0) in mapping and pwlib.rel(root, p).startswith("wiki/"):
            p.rename(p.with_name(mapping[m.group(0)] + p.name[len(m.group(0)):]))
            renamed += 1
    print("---\n%d task file(s) renamed, %d file(s) of the wiki rewritten; proposals and reminders updated"
          % (renamed, changed))
    for rp in untouched:
        print("not changed (ingestion card, immutable): %s cites an old task id" % rp)
    print("run wiki-lint.py to confirm, and board.py to redraw the board")
    return 0


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["lock", "changes", "diff", "vendor", "check", "upgrade", "resolved",
                                        "permissions", "renumber-tasks"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--format", choices=["table", "json"], default="table")
    ap.add_argument("--add", action="store_true", help="with lock: add only the given files")
    ap.add_argument("--hook", action="store_true", help="with check: run as the SessionStart hook")
    ap.add_argument("--from", dest="source", help="with upgrade and lock: folder of the new version of the plugin")
    ap.add_argument("--base-plugin", help="with upgrade: folder of the current version, when the original copy is missing")
    ap.add_argument("--apply", action="store_true", help="with upgrade and renumber-tasks: apply the plan")
    ap.add_argument("--plan", action="store_true", help="with renumber-tasks: only print the plan, write nothing (the default)")
    ap.add_argument("--remove", action="store_true", help="with permissions: remove the rules")
    ap.add_argument("--root")
    args = ap.parse_args()
    if args.hook and args.command == "check":  # the start of a session must never fail
        pwlib.setup_output()
        root = pwlib.find_root(args.root, hook=True)
        if root is None or pwlib.check_python():
            return 0
        try:
            return cmd_check(root, True)
        except Exception:
            return 0
    root, _project, _schema = pwlib.start(args.root)
    if args.command == "lock":
        return cmd_lock_add(root, args.files) if args.add else cmd_lock(root, args.source)
    if args.command == "changes":
        return cmd_changes(root, args.format)
    if args.command == "vendor":
        return cmd_vendor(root)
    if args.command == "check":
        return cmd_check(root, False)
    if args.command == "upgrade":
        fmt = "json" if args.format == "json" else "table"
        return cmd_upgrade(root, args.source, args.base_plugin, args.apply, fmt)
    if args.command == "resolved":
        return cmd_resolved(root, args.files)
    if args.command == "permissions":
        return cmd_permissions(root, args.remove)
    if args.command == "renumber-tasks":
        return cmd_renumber_tasks(root, args.apply)
    return cmd_diff(root, args.files)


if __name__ == "__main__":
    sys.exit(main())
