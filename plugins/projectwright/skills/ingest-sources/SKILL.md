---
name: ingest-sources
description: Ingests the official project documentation into the wiki — reads the documents from the official documentation folder and writes one ingestion card per document in wiki-sources/, with the ingestion log. Works autonomously and involves the user only for conflicts between documents, removed documents or choices it cannot make alone. Use when the user asks to update the wiki from the documentation or reports new documents to ingest.
---

# Ingest the official documentation

User input: $ARGUMENTS

The writing rules of the wiki are in the constitution (`wiki/README.md`) and those of the cards in `wiki-sources/README.md`: follow them, this skill does not repeat them.

## 0. Input

- The **folder of the official documentation**. Order: `$ARGUMENTS`; otherwise `paths.official_docs` in `project.yaml`, checking that it exists; otherwise ask the user ("Tell me the folder with the project documentation to ingest"). Never invent it.
- It can also be the **documentation inside a code repository** (for example `repositories/<repo>/docs`): it stays in the repository, and its cards go in `wiki-sources/technical-docs/<repo>/`. The script keeps its rows apart from those of the official documentation (their `source_path` is relative to the project root).
- **Its structure is the user's** — the framework neither creates nor requires subfolders. When a first-level folder is named like a category of `sources.categories` (minutes, technical documents, functional documents), it gives the category of the cards; otherwise the category comes from the content of the document. It may be synchronised from a shared drive: hidden files and system files are ignored by the script.
- A document can have **attachments**: non-Markdown files (typically screenshots shared in a call) that the document itself cites or embeds, usually in a folder next to it. They are not documents to ingest: their content is already reported in the document that cites them (§3).

## 1. Way of working: autonomous

When things are smooth and clear, **proceed without asking for confirmation step by step**: read, extract, write the card, update the log, move to the next document. Stop and involve the user **only** when:

- the folder is unknown or does not exist;
- the diff reports **REMOVED** documents;
- two documents (or a document and a card already ingested) **contradict each other** and an arbitration is needed (§5);
- a file **cannot be classified** (document or not, destination folder not deducible);
- the name of a card **collides** with an existing file in `wiki/` or `wiki-sources/`.

Ask **grouped** questions (one structured question per document, with all the divergences found), quoting the versions being compared and always offering the option "still open". If the user asks to **see the steps** (for example the first time), show the preview of each card and wait for approval until they let you proceed alone. Always close with a summary (§8).

## 2. Access perimeter — BINDING ⛔

1. **The documentation folder is strictly READ-ONLY**: never write, modify, rename, move or delete anything inside it — not even temporary files. If something there must change, the user does it: you report it.
2. **Write ONLY in `wiki-sources/`** (cards and `ingestion-log.csv`). Do not write anywhere else in the wiki or the project.
3. **Read ONLY**: the documentation folder, `wiki-sources/` (the existing cards are your only memory of the project), the constitution `wiki/README.md`, `project.yaml` and the plugin scripts. Do not read the other folders of the wiki or other project files, and **do not bring in external knowledge**: everything you write in a card derives from the documents in the folder.

Operating notes:
- read long documents in blocks (for example 20 KB at a time from the shell): the output of a single command is truncated beyond about 30 KB;
- write the cards with the file-writing tool, not with shell heredocs;
- the rows of the log are produced **by the script** (§3), never typed by hand: names with non-ASCII characters would not match otherwise.

## 3. Diff: what there is to ingest

Run the diff script from the project root (read-only):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ingestion-diff.py" ["<documentation folder>"]
```

Without the folder it uses `paths.official_docs`; files matching `sources.exclude` are never considered. For every NEW file the output suggests the path of the card in `wiki-sources/`; a path starting with `?/` means that the folder does not say the category: choose it from the content of the document — a record of a meeting is `minutes`, a description of how the system is built is `technical-docs`, of what it must do is `functional-docs` — and ask only when it is unclear. `--format log` previews the log rows without writing them.

The script classifies **ATTACHMENTS** by itself: a non-Markdown file that a Markdown document in the same folder (or a subfolder) **embeds or cites by name** — it is the document that says which files are its attachments, not a naming convention of the folder. For these files: **no card** and no reading (the document that cites them already transcribed their content), only the log row that `--record` writes together with the document (§7). If an attachment is **modified**, or a new one appears for an already ingested document, update only its row: the card is revised only when the document itself is MODIFIED. An image that **no document cites** stays NEW and is treated as a file that cannot be classified (ask). If an ATTACHMENT classification looks wrong (for example an autonomous document that happens to be named in another one), report it to the user instead of following it.

- **NOTHING NEW** → if there are no online sources to check either (§3b), report that there is nothing to ingest and stop.
- **REMOVED** → delete nothing: report the missing documents and ask how to proceed.
- **NEW / MODIFIED** → your work list.
- **Files that are not documents** (placeholders of a naming convention, empty templates, operational notes of a folder): no card; record them with `--record … --ignore "<reason>"`, so that they do not show up as NEW again. When unsure whether a file is a document, ask. Whole folders that are never documentation are better excluded in `sources.exclude` of `project.yaml` (ask the user).

## 3b. Online sources (links)

Official documentation can also live online: Confluence pages, pages of another wiki, online documents, and the issues of a tracker that carry **knowledge** (an epic with its requirements, a story with acceptance criteria and decisions). They are ingested like files: one card each, with the link instead of the path.

- **What to ingest**: the links the user gives in `$ARGUMENTS` or in the conversation. A parent page (or a space) means its child pages too: list them and confirm the list with the user before ingesting. Issues only when they carry knowledge: managing tasks is not ingestion.
- **How to read them**: through the **MCP server of the source system** configured in the project (for Confluence and Jira, the official Atlassian one), with the user's own account. If no server is available, say so and propose the fallback: export the page (Markdown or PDF) into the official documentation folder, and ingest it as a file. Never ask for credentials and never write them anywhere.
- **New or changed?** Every link already ingested is in the log:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ingestion-diff.py" --remote
  ```
  For each of them (and for each new link) read the **version** that the source system gives — the page version number, otherwise the date of the last update. Not in the log → NEW; a different version → MODIFIED (revise the card, as for a file); the page no longer exists or is no longer readable → REMOVED (ask the user, delete nothing).
- **The card**: same template and rules as for files; `source` is the link; `source_kind` is `reference` (or `event` for pages that record a meeting); the category folder is chosen from the content (functional, technical, minutes) — ask when unclear. The content of a page is often edited by many people: extract only what the page states, as for any document.
- **Record it**, after writing the card:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ingestion-diff.py" --record-url "<link>" --version "<version>" --title "<page title>" --card <card name>
  ```
  A link that turns out not to be documentation: `--record-url "<link>" --ignore "<reason>"`.

## 4. Order of work

1. minutes, in increasing date order;
2. technical documents;
3. functional documents.

This is only a **reading order** (events first give the context), **not** a hierarchy of truth: no kind of document "wins" over another.

## 5. For each document, one at a time

1. **Read it entirely.**
2. **Extract the knowledge** with this granularity:
   - **knowledge**: one claim = **one atomic fact**, as the document states it, with its reference date when the fact is a state ("on 26/08 the environments do not exist"); no inferences;
   - **decisions**: only what the document declares decided; **do not repeat them among the claims**;
   - **open points**: as the document declares them, grouped by topic;
   - **terms**: definitions and words of the domain or the project, with the meaning the document gives them (they feed the glossary during integration).
3. **Annotations added after the event.** Minutes can contain notes added after the call (comparisons with standards or skills, 🔴🟠🟡 callouts, "how it ended up in…"): report them under a separate **Editor's notes** item and **never as content of the call**. If the document marks uncertain terms (⚠️), report them in the Flags.
4. **Consistency check** with the cards already in `wiki-sources/` (especially their Decisions and Flags sections) and with the other documents just read. Tell four cases apart:
   - **declared evolution**: a later document explicitly says it changes or supersedes an earlier decision (for example in a "what changes" section) → not a conflict: record it in the Flags as an evolution, citing the superseded card;
   - **refinement**: it adds compatible detail → record it;
   - **contradiction**: two documents state as true things that are incompatible → **STOP**: show the two versions citing the documents, ask which one holds (or "still open"), **never decide alone**. If a document turns out to be behind, say it with the fixed marker `⚠️ Document to update: <relative path> — <what>` (`/projectwright:propose-docs` and `/projectwright:record-decisions` look for that text). Record divergence and arbitration in the Flags;
   - **divergence from a development standard** reported by the document itself: not a conflict between documents and not yours to arbitrate; report it in the Flags with the marker `⚠️ Divergence from the standard: <topic>`, so that integration turns it into a question.
5. **Write the card and update the log**, then move to the next document. The preview with approval happens only when the user asked for step by step (§1).

## 6. The card

**Path**: mirrors the one of the document. The card goes in the folder of its category in `wiki-sources/` (`minutes/`, `technical-docs/`, `functional-docs/`): the first-level folder of the document when it has a category's name, otherwise the category chosen from the content (§3); **below it, the folders of the document are mirrored**, in kebab-case (lower case, spaces → `-`); create a subfolder when it does not exist yet. For non-Markdown documents the card is still a `.md` file. The name of the card is **unique across `wiki/` and `wiki-sources/`**: on a collision, report it to the user instead of overwriting. Names with accented letters are written in composed form (NFC).

**Structure**: the template `${CLAUDE_PLUGIN_ROOT}/templates/records/source-card.md`, written in `project.language` with the headings of the existing cards (constitution, "Language of the content"). In its frontmatter: `area` is the area code of the topic (usually `PRJ`, `DOM`, `ARCH` or `STD`); `source` is the path of the document relative to the documentation folder; `hash` comes from the diff; `source_kind` is `event` for minutes and `reference` for technical and functional documents.

Cards do not contain wikilinks to wiki notes, which may not exist: cards cite documents, and the notes will cite the cards.

**Reserved data**: a document may contain names of people, amounts or opinions — for example minutes in which the user chose to keep them. The card does not carry them into the wiki: people by organisation and role (`wiki/project/team-and-roles.md`; constitution, "Names of people"), and nothing of what `drafting.forbidden` in `project.yaml` excludes.

## 7. The log

`wiki-sources/ingestion-log.csv` (columns and values: `wiki-sources/README.md`). **Never edit it by hand**: the script writes the rows.

- After writing the card of a document, record it:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ingestion-diff.py" --record "<source path>" --card <card name>
  ```
  The row gets `result` `ingested` and `integrated` `no`; the rows of the document's new or modified attachments are written with it (`ignored`, `n/a`, `attachment of <card>`).
- A file that is not a document: `--record "<source path>" --ignore "<reason>"`.
- A **modified** document: revise the card (explaining in its Flags what changes compared with the previous version) and record it again with `--record`: hash and date are updated and `integrated` goes back to `no`, so the new version is integrated again.
- The `integrated` column belongs to `/projectwright:integrate-wiki`.

## 8. Closing

1. The lint runs by itself after every write; if it reports violations in the cards you wrote, fix them.
2. Summary for the user:
   - documents **ingested**, **updated** and **ignored** in this round;
   - divergences arbitrated and evolutions recorded;
   - ⚠️ **official documents to update** (explicit list, collected from the marker in the Flags: it is the most important reminder, the wiki cannot correct them);
   - divergences from the development standards to carry into integration;
   - any REMOVED documents waiting for instructions;
   - the next step: `/projectwright:integrate-wiki`;
   - if the project folder is versioned, the ready-to-paste git commands (commits and pushes are run by the user).
