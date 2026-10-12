"""Common library of the projectwright scripts.

Finds the project root, loads project.yaml and the method schema, validates the
configuration and reads the frontmatter of the wiki files. Standard library
plus the PyYAML copy shipped in _vendor/ (no installation needed).
"""
import os
import re
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)

SCRIPTS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = SCRIPTS_DIR.parent
SCHEMA_PATH = PLUGIN_DIR / "schema.yaml"
TEMPLATES_DIR = PLUGIN_DIR / "templates"

sys.path.insert(0, str(SCRIPTS_DIR / "_vendor"))
import yaml  # noqa: E402  (vendored PyYAML)

WIKILINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ConfigError(Exception):
    """project.yaml or schema.yaml cannot be read."""


def setup_output():
    """UTF-8 on stdout/stderr, also on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def ensure_python():
    """When the interpreter is too old, re-runs the script with a newer one if found.

    Hooks call a generic "python3", which on some systems is older than 3.11
    while a newer interpreter is installed beside it. Must run before stdin is read.
    """
    if sys.version_info >= MIN_PYTHON or os.environ.get("PROJECTWRIGHT_REEXEC"):
        return
    import shutil
    for name in ("python3.14", "python3.13", "python3.12", "python3.11"):
        exe = shutil.which(name)
        if exe:
            os.environ["PROJECTWRIGHT_REEXEC"] = "1"
            os.execv(exe, [exe] + sys.argv)


def check_python():
    """Returns an error message when the interpreter is too old, else None."""
    if sys.version_info < MIN_PYTHON:
        return "projectwright needs Python %d.%d or later (this is %d.%d)" % (
            MIN_PYTHON + sys.version_info[:2])
    return None


PLUGIN_IN_PROJECT = ".claude/skills/projectwright"   # where a copy of the plugin lives in a project
LOCK_REL = ".claude/projectwright.lock.json"


def find_root(explicit=None, hook=False):
    """The project root: the folder that holds project.yaml.

    Order: an explicit path; the project that contains this plugin, when the plugin
    is copied into it (<root>/.claude/skills/projectwright/scripts); the project
    directory Claude Code gives to hooks (CLAUDE_PROJECT_DIR); the current directory
    and its parents. With hook=True the folder must also hold the lock file of the
    framework, so that an installed plugin never acts on an unrelated folder that
    happens to have a project.yaml. Returns a Path or None.
    """
    def ok(p):
        return (p / "project.yaml").is_file() and (not hook or (p / LOCK_REL).is_file())

    if explicit:
        p = Path(explicit).resolve()
        return p if (p / "project.yaml").is_file() else None
    candidate = PLUGIN_DIR.parent.parent.parent
    if PLUGIN_DIR.parent.name == "skills" and ok(candidate):
        return candidate
    starts = []
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        starts.append(Path(os.environ["CLAUDE_PROJECT_DIR"]).resolve())
    starts.append(Path.cwd().resolve())
    for here in starts:
        for p in [here, *here.parents]:
            if ok(p):
                return p
    return None


def plugin_in_project(root):
    """True when the running plugin is the copy inside the project, not an installed one."""
    try:
        return PLUGIN_DIR == (Path(root) / PLUGIN_IN_PROJECT).resolve()
    except OSError:
        return False


def plugin_version(plugin_dir=PLUGIN_DIR):
    import json
    try:
        with open(Path(plugin_dir) / ".claude-plugin" / "plugin.json", encoding="utf-8") as f:
            return json.load(f).get("version", "?")
    except (OSError, ValueError):
        return "?"


def load_yaml_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise ConfigError("file not found: %s" % path)
    except yaml.YAMLError as e:
        raise ConfigError("invalid YAML in %s: %s" % (path, e))


def load_schema():
    return load_yaml_file(SCHEMA_PATH)


def load_project(root):
    return load_yaml_file(Path(root) / "project.yaml")


def get(data, dotted, default=None):
    """Value of a dotted key ("tracker.write_mode") in nested dicts."""
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def empty(value):
    return value is None or value == "" or value == [] or value == {}


def known_codes(project):
    """Code -> ("area" | "component", label or component name)."""
    codes = {}
    for code, label in (get(project, "wiki.areas") or {}).items():
        codes[str(code)] = ("area", label)
    for comp in get(project, "components") or []:
        if isinstance(comp, dict) and comp.get("code"):
            codes[str(comp["code"])] = ("component", comp.get("name"))
    return codes


def validate_project(project, schema):
    """List of error messages about project.yaml (empty when valid)."""
    errors = []
    rules = schema.get("project", {})
    for key in rules.get("required", []):
        if empty(get(project, key)):
            errors.append("missing or empty key: %s" % key)
    for key, allowed in (rules.get("values") or {}).items():
        value = get(project, key)
        if empty(value):
            continue
        for item in value if isinstance(value, list) else [value]:
            if item not in allowed:
                errors.append("%s: value %r not allowed (allowed: %s)" % (key, item, ", ".join(map(str, allowed))))

    code_rx = re.compile(schema.get("ids", {}).get("code", r"^[A-Z]{2,8}$"))
    areas = get(project, "wiki.areas") or {}
    if not isinstance(areas, dict):
        errors.append("wiki.areas must be a mapping code -> label")
        areas = {}
    for code in areas:
        if not code_rx.match(str(code)):
            errors.append("wiki.areas: code %r not valid (2-8 capital letters)" % code)

    seen_codes, seen_names, seen_repos = set(areas), set(), set()
    components = get(project, "components") or []
    if not isinstance(components, list):
        errors.append("components must be a list")
        components = []
    for i, comp in enumerate(components):
        where = "components[%d]" % i
        if not isinstance(comp, dict):
            errors.append("%s must be a mapping" % where)
            continue
        for key in ("name", "code", "repository"):
            if empty(comp.get(key)):
                errors.append("%s: missing %s" % (where, key))
        code, name, repo = comp.get("code"), comp.get("name"), comp.get("repository")
        if code is not None:
            if not code_rx.match(str(code)):
                errors.append("%s: code %r not valid (2-8 capital letters)" % (where, code))
            elif code in seen_codes:
                errors.append("%s: code %r already used by an area or another component" % (where, code))
            seen_codes.add(code)
        if name:
            if name in seen_names:
                errors.append("%s: name %r duplicated" % (where, name))
            seen_names.add(name)
        if repo:
            if repo in seen_repos:
                errors.append("%s: repository %r duplicated" % (where, repo))
            seen_repos.add(repo)

    if get(project, "tasks.mode") == "tracker":
        for key in ("tracker.type", "tracker.project"):
            if empty(get(project, key)):
                errors.append("tasks.mode is tracker but %s is empty" % key)
    if get(project, "tracker.write_mode") == "auto" and get(project, "tracker.client_visible") is not False:
        errors.append("tracker.write_mode: auto is forbidden when tracker.client_visible is true")
    return errors


def read_frontmatter(path):
    """Reads a Markdown file.

    Returns (frontmatter, error, text): frontmatter is a dict or None; error is
    None or a message (missing frontmatter, invalid YAML, not a mapping).
    """
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]
    if not text.startswith("---"):
        return None, "frontmatter missing", text
    end = text.find("\n---", 3)
    if end < 0:
        return None, "frontmatter not closed", text
    block = text[3:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        msg = str(e).replace("\n", " ")
        return None, "frontmatter is not valid YAML: %s" % msg, text
    except ValueError as e:  # e.g. an impossible date such as 2026-13-01
        return None, "frontmatter has an invalid value: %s" % e, text
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping", text
    return data, None, text


def has_bom(path):
    with open(path, "rb") as f:
        return f.read(3) == b"\xef\xbb\xbf"


def wiki_files(root):
    """All .md files of wiki/ and wiki-sources/, as Paths."""
    out = []
    for top in ("wiki", "wiki-sources"):
        base = Path(root) / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in sorted(filenames):
                if name.endswith(".md"):
                    out.append(Path(dirpath) / name)
    return out


def links_in(value):
    """Wikilink targets contained in a frontmatter value (string or list)."""
    items = value if isinstance(value, list) else [value]
    out = []
    for item in items:
        if isinstance(item, str):
            out += [m.group(1).strip() for m in WIKILINK.finditer(item)]
    return out


def rel(root, path):
    return Path(os.path.relpath(path, root)).as_posix()


def start(argv_root=None, need_project=True):
    """Common start of a script: output, Python check, root, project, schema.

    Returns (root, project, schema). Exits with a message on fatal errors.
    """
    ensure_python()
    setup_output()
    err = check_python()
    if err:
        print("ERROR: " + err, file=sys.stderr)
        sys.exit(3)
    root = find_root(argv_root)
    if root is None and need_project:
        print("ERROR: project.yaml not found (run from the project root or pass --root)", file=sys.stderr)
        sys.exit(3)
    try:
        schema = load_schema()
        project = load_project(root) if root else {}
    except ConfigError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        sys.exit(3)
    return root, project, schema
