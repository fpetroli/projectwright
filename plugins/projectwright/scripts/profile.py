#!/usr/bin/env python3
"""profile — the personal working profile of the user, shared by all their projects.

How this person likes to work with Claude: how to present analyses, how many
questions at a time, how much autonomy, level of detail, tone. Claude writes it
from what it observes, never with project facts or confidential data; the
start-of-session hook gives it to Claude in every projectwright project.

It lives outside the projects, in the user's Claude Code folder
(~/.claude/projectwright/profile.md, or $CLAUDE_CONFIG_DIR/projectwright/profile.md;
$PROJECTWRIGHT_PROFILE sets another file): it is personal, never in the wiki and
never versioned with a project.

Usage:
    python3 profile.py show [--hook]       prints the profile (the hook prints nothing when it is empty)
    python3 profile.py path                prints the path of the profile
    python3 profile.py add "<preference>"  adds a preference, dated
    python3 profile.py remove "<text>"     removes the preferences that contain <text>
                                           (when a preference no longer holds)
Exit code: 0, or 2 when nothing matches `remove`.
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

HEADER = """# Working profile

How I like to work with Claude, observed by Claude in my projectwright projects.
Personal: it lives outside the projects and is never shared. Edit or delete freely.

## Preferences
"""


def profile_path():
    if os.environ.get("PROJECTWRIGHT_PROFILE"):
        return Path(os.environ["PROJECTWRIGHT_PROFILE"]).expanduser()
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return Path(base) / "projectwright" / "profile.md"


def entries(text):
    return [line for line in text.splitlines() if line.startswith("- ")]


def read():
    p = profile_path()
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def write(text):
    p = profile_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def cmd_show(hook):
    text = read()
    if hook:
        if not entries(text):
            return 0
        print("projectwright — working profile of the user (%s). Follow these preferences; when you observe a "
              "new stable one, or one stops holding, update it with profile.py add / remove:\n" % profile_path())
        print("\n".join(entries(text)))
        return 0
    print(text if text else "no profile yet: %s" % profile_path())
    return 0


def cmd_add(preference):
    preference = " ".join(preference.split())
    if not preference:
        print("empty preference", file=sys.stderr)
        return 2
    text = read() or HEADER
    if any(preference.lower() in e.lower() for e in entries(text)):
        print("already in the profile: %s" % preference)
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += "- %s (%s)\n" % (preference, datetime.date.today().isoformat())
    write(text)
    print("added to the profile (%s): %s" % (profile_path(), preference))
    return 0


def cmd_remove(fragment):
    text = read()
    lines = text.splitlines(keepends=True)
    kept = [l for l in lines if not (l.startswith("- ") and fragment.lower() in l.lower())]
    if len(kept) == len(lines):
        print("no preference contains: %s" % fragment, file=sys.stderr)
        return 2
    write("".join(kept))
    print("removed %d preference(s) containing: %s" % (len(lines) - len(kept), fragment))
    return 0


def main():
    pwlib.ensure_python()
    pwlib.setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["show", "path", "add", "remove"])
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--hook", action="store_true", help="with show: run as the SessionStart hook")
    args = ap.parse_args()
    if args.hook:  # only in projectwright projects; the start of a session must never fail
        try:
            if pwlib.find_root(None, hook=True) is None or pwlib.check_python():
                return 0
            return cmd_show(True)
        except Exception:
            return 0
    if args.command == "show":
        return cmd_show(False)
    if args.command == "path":
        print(profile_path())
        return 0
    if args.command == "add":
        return cmd_add(args.text)
    return cmd_remove(args.text)


if __name__ == "__main__":
    sys.exit(main())
