#!/usr/bin/env python3
"""ingestion-diff — compares the official documentation folder with the ingestion log.

READ-ONLY on the documentation folder. Reports what is new, modified, removed,
unchanged, and which files are attachments of a document.

Usage (from the project root, or with --root):
    python3 ingestion-diff.py [<documentation folder>] [--format diff|log]
    python3 ingestion-diff.py --record <source path> [--card <name>] [<documentation folder>]
    python3 ingestion-diff.py --record <source path> --ignore "<reason>" [<documentation folder>]
    python3 ingestion-diff.py --mark-integrated <card> [<card> ...]
    python3 ingestion-diff.py --remote
    python3 ingestion-diff.py --record-url <url> --version <version> [--title <t>] [--card <name>]
    python3 ingestion-diff.py --record-url <url> --ignore "<reason>"

    <documentation folder>  defaults to paths.official_docs of project.yaml
                            (relative paths are relative to the project root). It can also be
                            a folder inside the project, typically the documentation of a code
                            repository (repositories/<repo>/docs): its rows keep paths relative
                            to the project root, so the sources never mix in the log.
    --format diff (default) one line per file, tab-separated:
                              NEW         <path>  <hash>  card: <suggested card path>
                              MODIFIED    <path>  <logged hash> -> <current hash>  card: <card>
                              ATTACHMENT  <path>  <hash>  of: <document that cites it>
                              REMOVED     <path>  (in the log, missing from the folder)
                            plus a summary.
    --format log            the rows ready for wiki-sources/ingestion-log.csv (CSV):
                            NEW and ATTACHMENT rows to append, MODIFIED rows that replace
                            the existing row of the same source_path (integrated back to no).
                            Card names are suggestions: the skill may change them.
    --record                writes into the log the row of one document (added, or replacing
                            the row of the same source_path), as ingested with integrated = no
                            and the given card name (default: the suggested one), plus the rows
                            of its new or modified attachments. With --ignore it records the
                            file as ignored, with the reason in the note column.
    --mark-integrated       sets integrated = yes on the log rows of the given cards.
    --remote                lists the online sources already in the log (rows whose source_path
                            is a link: Confluence pages, wiki pages, issues…) with the version
                            recorded, so that they can be checked again.
    --record-url            writes the log row of an online source: the link as source_path and
                            the version given by the source system (page version, last update)
                            in the hash column, as "version:<version>"; or records it as ignored.
    --record and --mark-integrated are the only writes of this script, and only on the log.

Paths matching sources.exclude (glob patterns, relative to the documentation folder)
are never considered. ATTACHMENT: a non-Markdown file that a Markdown document in the
same folder (or in a parent folder) embeds or cites by name — typically the screenshots
shared in a call. It gets a log row with result "ignored", no card.
Exit code: 0 (informative), 2 on usage errors, 3 on configuration errors.
"""
import argparse
import csv
import datetime
import fnmatch
import hashlib
import io
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pwlib  # noqa: E402

LOG_REL = "wiki-sources/ingestion-log.csv"
COLUMNS = ["document", "source_path", "hash", "ingested_on", "result", "card", "integrated", "note"]

IGNORED_FILES = {".gitkeep", "thumbs.db", "desktop.ini", ".ds_store"}
IGNORED_PREFIXES = ("~$", ".")     # Office temporary files, hidden files
IGNORED_SUFFIXES = (".tmp", ".lnk")
RE_EMBED = re.compile(r"!\[[^\]]*\]\((?:<([^>]+)>|([^)\s]+))\)")


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()[:16]


def nfc(s):
    return unicodedata.normalize("NFC", s)


def kebab(s):
    s = nfc(s).lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "document"


def excluded(rel, patterns):
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(rel, pat) or (pat.endswith("/**") and rel.startswith(pat[:-3] + "/")):
            return True
    return False


def scan(folder, patterns):
    """Relative path -> current hash, for every relevant file of the folder."""
    current = {}
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            low = name.lower()
            if low in IGNORED_FILES or low.startswith(IGNORED_PREFIXES) or low.endswith(IGNORED_SUFFIXES):
                continue
            path = os.path.join(dirpath, name)
            rel = nfc(os.path.relpath(path, folder).replace(os.sep, "/"))
            if excluded(rel, patterns):
                continue
            current[rel] = (file_hash(path), path)
    return current


def find_attachments(folder, current):
    """Relative path of an attachment -> relative path of the Markdown document citing it."""
    attachments = {}
    candidates = [r for r in current if not r.lower().endswith(".md")]
    for doc in sorted(r for r in current if r.lower().endswith(".md")):
        try:
            text = io.open(current[doc][1], encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        doc_dir = os.path.dirname(doc)
        cited = set()
        for m in RE_EMBED.finditer(text):
            target = (m.group(1) or m.group(2) or "").strip()
            if target and "://" not in target:
                cited.add(nfc(os.path.normpath(os.path.join(doc_dir, target)).replace(os.sep, "/")))
        for r in candidates:
            if r in attachments:
                continue
            in_scope = (not doc_dir) or r.startswith(doc_dir + "/")
            if r in cited or (in_scope and os.path.basename(r) in text):
                attachments[r] = doc
    return attachments


def read_log(path):
    """List of row dicts of the ingestion log (empty if the log is missing)."""
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_log(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in COLUMNS})


def suggested_card(rel, categories, prefix=""):
    """Suggested path of the card (relative to wiki-sources/) for a document."""
    if prefix:  # documentation inside a code repository: technical docs of that component
        repo = prefix.strip("/").split("/")
        repo = repo[1] if len(repo) > 1 else repo[0]
        parts = rel[len(prefix):].split("/")
        stem = os.path.splitext(parts[-1])[0]
        return "/".join(["technical-docs", kebab(repo), *[kebab(x) for x in parts[:-1]],
                         "%s-%s" % (kebab(repo), kebab(stem))])
    # The structure of the documentation folder is the user's: a first-level folder named
    # like a category gives the category; otherwise "?" — the category comes from the
    # content of the document — and the card mirrors the whole path of the document.
    parts = rel.split("/")
    stem = os.path.splitext(parts[-1])[0]
    first = kebab(parts[0]) if len(parts) > 1 else ""
    if first in categories:
        return "/".join([first, *[kebab(p) for p in parts[1:-1]], kebab(stem)])
    return "/".join(["?", *[kebab(p) for p in parts[:-1]], kebab(stem)])


def is_url(path):
    return path.startswith("http://") or path.startswith("https://")


def list_remote(rows):
    remote = [r for r in rows if is_url(r.get("source_path", ""))]
    for r in remote:
        print("REMOTE\t%s\t%s\tcard: %s\tintegrated: %s" % (
            r["source_path"], r.get("hash", ""), r.get("card", "") or "-", r.get("integrated", "")))
    print("---")
    print("Summary: %d online source(s) in the log" % len(remote))
    return 0


def record_url(log_path, rows, url, version, title, card, ignore):
    if not is_url(url):
        print("ERROR: not a link: %s" % url, file=sys.stderr)
        return 2
    if not ignore and not version:
        print("ERROR: --version is required (the version or last-update date given by the source system)",
              file=sys.stderr)
        return 2
    old = next((r for r in rows if r.get("source_path") == url), {})
    today = datetime.date.today().isoformat()
    slug = kebab(title or url.rstrip("/").split("/")[-1])
    if ignore:
        row = {"document": title or old.get("document") or slug, "source_path": url,
               "hash": ("version:%s" % version) if version else old.get("hash", ""), "ingested_on": today,
               "result": "ignored", "card": "", "integrated": "n/a", "note": ignore}
    else:
        row = {"document": title or old.get("document") or slug, "source_path": url,
               "hash": "version:%s" % version, "ingested_on": today, "result": "ingested",
               "card": card or old.get("card") or slug, "integrated": "no", "note": ""}
    out = [row if r.get("source_path") == url else r for r in rows]
    if not old:
        out.append(row)
    write_log(log_path, out)
    print("recorded: %s -> %s (%s, %s)" % (url, row["card"] or "-", row["result"], row["hash"] or "-"))
    return 0


def mark_integrated(log_path, cards):
    rows = read_log(log_path)
    found = set()
    for row in rows:
        if row.get("card") in cards:
            row["integrated"] = "yes"
            found.add(row["card"])
    missing = [c for c in cards if c not in found]
    if missing:
        print("ERROR: no log row for card(s): %s" % ", ".join(missing), file=sys.stderr)
        return 2
    write_log(log_path, rows)
    print("integrated = yes: %s" % ", ".join(sorted(found)))
    return 0


def record(log_path, rows, current, attachment_of, logged, categories, path, card, ignore, prefix=""):
    """Writes the log row of one document (and of its attachments)."""
    if path not in current:
        print("ERROR: %s is not in the documentation folder (or it is excluded)" % path, file=sys.stderr)
        return 2
    today = datetime.date.today().isoformat()
    by_path = {nfc(r.get("source_path", "")): r for r in rows}
    stem = os.path.splitext(os.path.basename(path))[0]
    if ignore:
        row = {"document": stem, "source_path": path, "hash": current[path][0], "ingested_on": today,
               "result": "ignored", "card": "", "integrated": "n/a", "note": ignore}
    else:
        old = logged.get(path) or {}
        card = card or old.get("card") or suggested_card(path, categories, prefix).split("/")[-1]
        row = {"document": old.get("document") or stem, "source_path": path, "hash": current[path][0],
               "ingested_on": today, "result": "ingested", "card": card, "integrated": "no", "note": ""}
    written = [row]
    if not ignore:
        for att, doc in sorted(attachment_of.items()):
            if doc != path:
                continue
            if att in logged and logged[att].get("hash") == current[att][0]:
                continue
            written.append({"document": os.path.basename(att), "source_path": att, "hash": current[att][0],
                            "ingested_on": today, "result": "ignored", "card": "", "integrated": "n/a",
                            "note": "attachment of %s" % row["card"]})
    for w in written:
        by_path[w["source_path"]] = w
    order = [nfc(r.get("source_path", "")) for r in rows]
    out = [by_path[p] for p in order] + [w for w in written if w["source_path"] not in order]
    write_log(log_path, out)
    for w in written:
        print("recorded: %s -> %s (%s)" % (w["source_path"], w["card"] or "-", w["result"]))
    return 0


def main():
    pwlib.ensure_python()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", help="documentation folder (default: paths.official_docs)")
    ap.add_argument("--format", choices=["diff", "log"], default="diff")
    ap.add_argument("--record", metavar="SOURCE_PATH", help="record one document in the log")
    ap.add_argument("--card", help="card name for --record (default: the suggested one)")
    ap.add_argument("--ignore", metavar="REASON", help="with --record: record the file as ignored")
    ap.add_argument("--mark-integrated", nargs="+", metavar="CARD")
    ap.add_argument("--remote", action="store_true", help="list the online sources in the log")
    ap.add_argument("--record-url", metavar="URL", help="record an online source in the log")
    ap.add_argument("--version", help="with --record-url: version or last-update date from the source system")
    ap.add_argument("--title", help="with --record-url: readable name of the source")
    ap.add_argument("--root", help="project root (default: found automatically)")
    args = ap.parse_args()

    root, project, _schema = pwlib.start(args.root)
    log_path = Path(root) / LOG_REL

    if args.mark_integrated:
        return mark_integrated(log_path, set(args.mark_integrated))
    if args.remote:
        return list_remote(read_log(log_path))
    if args.record_url:
        return record_url(log_path, read_log(log_path), args.record_url, args.version, args.title,
                          args.card, args.ignore)

    folder = args.folder or pwlib.get(project, "paths.official_docs")
    if not folder:
        print("ERROR: no documentation folder: pass it, or set paths.official_docs in project.yaml", file=sys.stderr)
        return 2
    folder = Path(folder)
    if not folder.is_absolute():
        folder = (Path(root) / folder).resolve() if not args.folder else folder.resolve()
    if not folder.is_dir():
        print("ERROR: folder not found: %s" % folder, file=sys.stderr)
        return 2

    categories = [kebab(c) for c in (pwlib.get(project, "sources.categories") or [])]
    patterns = pwlib.get(project, "sources.exclude") or []
    repos_prefix = str(pwlib.get(project, "paths.repositories") or "repositories").strip("/") + "/"

    # Several sources share one log. The official documentation keeps paths relative to
    # its folder; a folder inside the project (e.g. the docs of a code repository) keeps
    # paths relative to the project root, so that its rows never mix with the others.
    official = pwlib.get(project, "paths.official_docs")
    official = (Path(root) / official).resolve() if official else None
    root_path = Path(root).resolve()
    if official is None or folder == official:
        prefix = ""
    elif root_path in folder.parents:
        prefix = Path(os.path.relpath(folder, root_path)).as_posix() + "/"
    else:
        print("ERROR: %s is neither paths.official_docs nor a folder inside the project" % folder, file=sys.stderr)
        return 2

    rows = read_log(log_path)
    if prefix:
        in_scope = lambda sp: sp.startswith(prefix)  # noqa: E731
    else:  # official documentation: neither the docs of the repositories nor the online sources
        in_scope = lambda sp: not sp.startswith(repos_prefix) and not is_url(sp)  # noqa: E731
    logged = {nfc(r["source_path"]): r for r in rows if r.get("source_path") and in_scope(nfc(r["source_path"]))}
    scanned = scan(folder, patterns)
    attachment_of = {prefix + a: prefix + d for a, d in find_attachments(folder, scanned).items()}
    current = {prefix + k: v for k, v in scanned.items()}

    new = sorted(r for r in current if r not in logged and r not in attachment_of)
    removed = sorted(r for r in logged if r not in current)
    modified = sorted(r for r in current if r in logged and r not in attachment_of
                      and current[r][0] != logged[r].get("hash"))
    attachments = sorted(r for r in attachment_of
                         if r not in logged or current[r][0] != logged[r].get("hash"))
    unchanged = len(current) - len(new) - len(modified) - len(attachments)

    if args.record:
        target = nfc(args.record.replace("\\", "/"))
        if prefix and not target.startswith(prefix):
            target = prefix + target
        return record(log_path, rows, current, attachment_of, logged, categories,
                      target, args.card, args.ignore, prefix)

    if args.format == "log":
        today = datetime.date.today().isoformat()
        out = csv.writer(sys.stdout, lineterminator="\n")
        if new:
            print("# NEW — rows to append")
            for r in new:
                card = suggested_card(r, categories, prefix).split("/")[-1]
                out.writerow([os.path.splitext(os.path.basename(r))[0], r, current[r][0], today,
                              "ingested", card, "no", ""])
        if modified:
            print("# MODIFIED — rows that replace the existing row of the same source_path")
            for r in modified:
                old = logged[r]
                out.writerow([old.get("document") or os.path.splitext(os.path.basename(r))[0], r,
                              current[r][0], today, "ingested", old.get("card", ""), "no", old.get("note", "")])
        if attachments:
            print("# ATTACHMENTS — rows to append (or to replace): no card")
            for r in attachments:
                doc = attachment_of[r]
                doc_card = (logged.get(doc) or {}).get("card") or suggested_card(doc, categories, prefix).split("/")[-1]
                out.writerow([os.path.basename(r), r, current[r][0], today, "ignored", "", "n/a",
                              "attachment of %s" % doc_card])
        if removed:
            print("# REMOVED — do not delete anything: ask the user")
            for r in removed:
                print("# %s" % r)
    else:
        for r in new:
            print("NEW\t%s\t%s\tcard: %s" % (r, current[r][0], suggested_card(r, categories, prefix)))
        for r in modified:
            print("MODIFIED\t%s\t%s -> %s\tcard: %s" % (r, logged[r].get("hash"), current[r][0],
                                                         logged[r].get("card", "")))
        for r in attachments:
            print("ATTACHMENT\t%s\t%s\tof: %s" % (r, current[r][0], attachment_of[r]))
        for r in removed:
            print("REMOVED\t%s\t(in the log, missing from the folder)" % r)

    prefix = "# " if args.format == "log" else ""
    print(prefix + "---")
    print(prefix + "Summary: %d new, %d modified, %d attachments, %d removed, %d unchanged (of %d files)"
          % (len(new), len(modified), len(attachments), len(removed), unchanged, len(current)))
    if any(c.startswith("?") for c in (suggested_card(r, categories, prefix) for r in new)):
        print(prefix + "Note: a card path starting with '?/' means the folder does not say the category: "
              "choose it from the content of the document (ask only when unclear).")
    if not (new or modified or attachments or removed):
        print(prefix + "NOTHING NEW")
    return 0


if __name__ == "__main__":
    sys.exit(main())
