#!/usr/bin/env python3
"""Mechanical check of a minutes document: names, references, currency, attachments.

Usage:
    python3 check-minutes.py <transcript.txt|.docx> <minutes.md> [--roles-note <note.md>]
                             [--names "Name1,Name2"] [--ignore "tok1,tok2"] [--attachments <folder>]
                             [--allow names,economics]

What it checks — only what is mechanical and the same in every language:
  R2  no names of people: speaker names are derived from the transcript itself
      (formats "First Last  mm:ss", "Name: text", start/stop transcription
      headers) and searched in the minutes, as full names and as single tokens
      (first name, last name). --roles-note adds the names saved in the People
      table of the team-and-roles note, so that people mentioned in the call but
      not speaking are found too; --names adds further names.
  R5  no anonymous speaker labels (SPEAKER_01), no path, link or file name.
      Exception: the attachments of the call (screenshots in the folder with the
      same name as the minutes) — allowed as relative embeds
      `![...](<./folder/file.png>)` and as file names in backticks. With
      --attachments <folder> the script also checks that every file of the
      folder is cited in the minutes and that every embedded image exists.
  R3  no currency sign or currency code.
--allow skips R2 (names) and/or R3 (economics) when the user chose to keep that
data in this minutes document.

What depends on the language — references to the transcript or the recording,
economic estimates in words, opinions (R1), people management (R4) — is left to
the semantic rereading of the skill.
Exit code 1 when there are violations, 0 when there are only warnings or nothing.
Standard library only.
"""
import argparse
import os
import re
import sys
from collections import Counter

# name particles that are not searched as single tokens
PARTICLES = {"di", "de", "del", "della", "dei", "degli", "da", "lo", "la", "le", "li",
             "van", "von", "der", "den", "mc", "mac", "san", "santa", "du", "des"}

# patterns to extract the speakers from the transcript
RE_TEAMS = re.compile(r"^(?P<n>[^\d\n|:]{2,60}?)\s{2,}\d{1,2}:\d{2}(?::\d{2})?\s*$")
RE_COLON = re.compile(r"^(?P<n>[A-ZÀ-Ý][^\d:\n|]{1,40}?):\s")
RE_HEADER = re.compile(r"^(?P<n>.{2,60}?)\s+(trascrizione (avviata|arrestata)|(started|stopped) transcription)\s*$", re.I)

# R5: anonymous speaker labels and external references (language-independent)
R5_PATTERNS = [
    (r"\[?speaker[ _-]?\d+\]?", "anonymous speaker label"),
    (r"[A-Za-z]:\\", "Windows path"),
    (r"(?<![\w/])/(?:c|home|Users|tmp|mnt)/", "POSIX path"),
    (r"https?://|www\.", "link"),
    (r"\.(?:md|docx|txt|pdf|xlsx|pptx|vtt|srt|png|jpe?g|gif|webp|svg)\b", "file name"),
]

# allowed references to the attachments of the call: relative embed in the folder with
# the same name, or image file name in backticks (table "Material shared in the call")
RE_EMBED = re.compile(r"!\[[^\]]*\]\(<\./([^>]+\.(?:png|jpe?g|gif|webp|svg))>\)", re.I)
RE_ATTACHMENT_TICK = re.compile(r"`([^`/\\]+\.(?:png|jpe?g|gif|webp|svg))`", re.I)
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

# R3: currency signs and ISO codes (language-independent)
R3_ERRORS = [
    (r"[€$£¥₹]", "currency sign"),
    (r"\b(?:EUR|USD|GBP|CHF|JPY)\b", "currency code"),
]

# first header cell of the People table in the team-and-roles note
PEOPLE_HEADER = {"name", "nome"}


def is_attachment_line(line):
    return bool(RE_EMBED.search(line) or RE_ATTACHMENT_TICK.search(line))


def check_attachments(minutes_path, minutes_lines, folder):
    """Checks the consistency between the attachments folder and the references in the minutes."""
    errors, warnings = [], []
    if not os.path.isdir(folder):
        errors.append(("ATT", 0, f"attachments folder not found: {folder}"))
        return errors, warnings
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT))
    if not files:
        warnings.append(("ATT", 0, "the attachments folder contains no images"))
    text = "\n".join(minutes_lines)
    for f in files:
        if f not in text:
            errors.append(("ATT", 0, f"attachment not cited in the minutes: {f}"))
    base = os.path.dirname(os.path.abspath(minutes_path))
    for ln, line in enumerate(minutes_lines, 1):
        for m in RE_EMBED.finditer(line):
            rel = m.group(1)
            if not os.path.isfile(os.path.join(base, rel)):
                errors.append(("ATT", ln, f"embed of a missing file: {rel}"))
    return errors, warnings


def read_transcript(path):
    if path.lower().endswith(".docx"):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from docx2txt import extract, to_text  # noqa: E402
        body, comments = extract(path)
        return to_text(body, comments)
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_names(text):
    """Speaker names as they appear in the transcript."""
    teams, colon, header = Counter(), Counter(), Counter()
    for line in text.splitlines():
        line = line.rstrip()
        m = RE_TEAMS.match(line)
        if m:
            teams[m.group("n").strip()] += 1
            continue
        m = RE_HEADER.match(line)
        if m:
            header[m.group("n").strip()] += 1
            continue
        m = RE_COLON.match(line)
        if m:
            colon[m.group("n").strip()] += 1
    names = set(teams) | set(header) | {n for n, c in colon.items() if c >= 3}
    # drop anonymous labels: the R5 check already catches them
    return {n for n in names if not re.match(r"^\[?speaker", n, re.I)}


def names_from_roles_note(path):
    """Names in the first column of the People table of the team-and-roles note.

    The table is the one after the marker comment "<!-- people-table … -->", which is
    the same in every language; without the marker, a table whose first header is
    "Name" or "Nome" is used.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    names = set()
    marker = any("people-table" in line for line in lines)
    armed = not marker  # without the marker, rely on the header
    in_table = header_seen = False
    for line in lines:
        s = line.strip()
        if marker and "people-table" in s:
            armed, in_table, header_seen = True, False, False
            continue
        if not s.startswith("|"):
            if in_table:
                if marker:
                    break
                in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        first = cells[0] if cells else ""
        if not in_table:
            if armed and (marker or first.lower() in PEOPLE_HEADER):
                in_table, header_seen = True, True
            continue
        if set(first) <= set("-: "):
            continue
        if first and not first.startswith("<"):  # skip template placeholders
            names.add(first)
    return names


def tokens(names):
    """Full name plus the significant single tokens (first name, last name)."""
    out = set()
    for n in names:
        out.add(n)
        for t in re.split(r"[\s\-']+", n):
            if len(t) >= 3 and t.lower() not in PARTICLES:
                out.add(t)
    return out


def search(minutes_lines, pattern, flags=re.I):
    rx = re.compile(pattern, flags)
    for i, line in enumerate(minutes_lines, 1):
        for m in rx.finditer(line):
            a, b = max(0, m.start() - 40), min(len(line), m.end() + 40)
            yield i, line[a:b].strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("minutes")
    ap.add_argument("--roles-note", default="", help="team-and-roles note: the names in its People table are searched too")
    ap.add_argument("--names", default="", help="further names to search, comma-separated")
    ap.add_argument("--ignore", default="", help="tokens not to consider (e.g. surnames equal to common words)")
    ap.add_argument("--attachments", default="", help="folder of the screenshots of the call (usually named as the minutes, without .md)")
    ap.add_argument("--allow", default="", help="reserved data kept in this document, comma-separated: names, economics")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    transcript = read_transcript(args.transcript)
    with open(args.minutes, encoding="utf-8") as f:
        # split on "\n", not splitlines(): line numbers must match those of the editor
        minutes_lines = f.read().replace("\r\n", "\n").split("\n")

    allow = {a.strip().lower() for a in args.allow.split(",") if a.strip()}
    unknown = allow - {"names", "economics"}
    if unknown:
        print("ERROR: --allow accepts names, economics (got: %s)" % ", ".join(sorted(unknown)), file=sys.stderr)
        return 2

    names = extract_names(transcript)
    if args.roles_note:
        names |= names_from_roles_note(args.roles_note)
    names |= {n.strip() for n in args.names.split(",") if n.strip()}
    ignore = {t.strip().lower() for t in args.ignore.split(",") if t.strip()}
    toks = sorted(t for t in tokens(names) if t.lower() not in ignore)

    errors, warnings = [], []

    if "names" in allow:
        print("Names: kept in this document (--allow names), not searched")
        toks = []
    else:
        print(f"Speakers/names collected ({len(names)}): " + (", ".join(sorted(names)) or "none"))
        if not names:
            warnings.append(("R2", 0, "no name collected: check the transcript format, or pass --roles-note / --names"))
    for t in toks:
        for ln, ctx in search(minutes_lines, r"(?<![\w])" + re.escape(t) + r"(?![\w])"):
            errors.append(("R2", ln, f"name «{t}»: …{ctx}…"))

    for pat, desc in R5_PATTERNS:
        for ln, ctx in search(minutes_lines, pat, re.I | re.M):
            if desc == "file name" and is_attachment_line(minutes_lines[ln - 1]):
                continue  # allowed reference to an attachment of the call
            errors.append(("R5", ln, f"{desc}: …{ctx}…"))

    if args.attachments:
        e, w = check_attachments(args.minutes, minutes_lines, args.attachments)
        errors += e
        warnings += w
    elif any(is_attachment_line(line) for line in minutes_lines):
        warnings.append(("ATT", 0, "the minutes cite attachments: run again with --attachments <folder> to check them"))

    for pat, desc in ([] if "economics" in allow else R3_ERRORS):
        for ln, ctx in search(minutes_lines, pat):
            errors.append(("R3", ln, f"{desc}: …{ctx}…"))
    print()
    if errors:
        print(f"VIOLATIONS ({len(errors)}):")
        for rule, ln, msg in errors:
            print(f"  [{rule}] line {ln}: {msg}")
    else:
        print("VIOLATIONS: none")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}), to assess by hand:")
        for rule, ln, msg in warnings:
            print(f"  [{rule}] line {ln}: {msg}")
    print("\nReferences to the recording, estimates in words, opinions (R1) and people management (R4)"
          " are checked by the semantic rereading, not by this script.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
