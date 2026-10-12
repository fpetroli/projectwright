---
name: adopt-framework
description: Brings an existing project into projectwright — a folder with its own notes, decision logs, open points, documents, rules for AI assistants and code repositories. Takes an inventory of the old folder, proposes where each thing goes in the framework's model, and after the user's approval creates the new project folder next to the old one, which stays untouched. Use when the user wants to adopt the framework on a project that already exists, instead of starting from an empty folder.
---

# Adopt an existing project

User input: $ARGUMENTS (the path of the existing project folder)

An adoption does not invent a project: it **moves what the old project already knows into the framework's model, without losing it and without changing its meaning**. The new project folder is created **next to the old one** (for example `~/work/shop/` → `~/work/shop-project/`); the old folder is **never modified** — the only exception is moving its code repositories, with the user's yes (§5). When the user is satisfied, they delete the old folder themselves.

## 0. Where you are

- The session must run in the **new project folder**, empty, with the `projectwright` plugin loaded. If it was started inside the old project, **stop**: propose to create `<name>-project/` next to it, to install the plugin there and to run this skill from there.
- If `project.yaml` already exists, the project is already set up: stop.
- The old folder is outside the project: if reading it is denied, ask the user to grant access (`/add-dir <old folder>`).

## 1. Inventory — read only

Read the old folder **completely** (in blocks when it is large; never stop at the first level) and classify what you find:

| What | Typical forms | Where it goes |
|---|---|---|
| **Code repositories** | folders with their own git and source code | `repositories/`, one component each (§5) |
| **Official documents** — written for people | specifications, analyses, minutes, manuals; `.docx`, `.pdf`, `.md` | copied into the new project's `docs/` with the structure they have (default, so that the old folder can be deleted), or left in a shared folder: they become the official documentation (`paths.official_docs`) and are **ingested** (§6) — never copied into the wiki |
| **Knowledge for the AI** — written for the assistant or as working memory | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, notes, memory files, an existing wiki, decision logs, ADRs, lists of open points, TODO lists | **converted into records** of the wiki (§4) |
| **Rules of work** | how to write code, conventions, git and review procedures, standards | development workflow note, the project-specific section of `CLAUDE.md`, or the references of a future development skill (§4) |
| **Claude Code configuration** | `.claude/skills/`, `.claude/commands/`, `.claude/agents/`, `.claude/settings.json`, hooks | the project's own skills go to `.claude/skills/` of the new project and into `dev_skills`; settings are merged only on the user's yes |
| **Other files** | exports, tables, drafts, support scripts | `utils/` |
| **Not carried** | generated indexes, caches, build output, duplicates, files the user calls obsolete | listed in the report, left in the old folder |

Also note: the **language** of the content, the names of **people** and **organisations** that appear, the **dates** of decisions and events, and the links between files.

## 2. The proposal — the user approves before anything is written

Show the user, in one message:

1. **The project**: proposed name (default: the old folder's name), language of the wiki (default: the language of the old content), components (one per repository, with code), official documentation folder.
2. **The map**: one row per item or group — old path → destination → how (*converted into records*, *ingested as a source*, *repository moved*, *copied to utils/*, *not carried*), with counts where a group is large ("23 entries of the decision log → 23 ADRs").
3. **The skeleton of the wiki**: the decisions, questions, tasks and notes that will be created, one line each with title and area or component. Same principle as the first run of `/projectwright:integrate-wiki`: the user approves the skeleton, not every file.
4. **The doubts**, as a numbered list: items you cannot classify, content that contradicts other content, decisions you cannot tell whether they were taken or only discussed, names of people.

Ask once, grouped; accept "default" and partial corrections. Do not write anything before the yes.

## 3. Create the project

Run the setup with the choices of §2, as `/projectwright:setup-project` §2–§3 does (`scaffold.py project --name … --language …`, then `project.yaml`, translations of the notes created from the templates, and — if the user allows it, asked with the proposal — `framework.py permissions`). Do not record its `ADR-MET-0001` yet: §7 records the adoption.

## 4. Convert the knowledge for the AI

Read the constitution (`wiki/README.md`) first: every record follows it. Then, item by item of the approved skeleton:

- **Decisions → ADRs** (template `${CLAUDE_PLUGIN_ROOT}/templates/records/decision.md`), one per decision, in the area or component it concerns, with safe IDs. `created` is the **date of the decision** when the old content gives it, otherwise the adoption date. `status: decided` only when the old content says it was decided; when it was only proposed or discussed, `assumed`, or a question instead. A decision later replaced in the old log becomes two ADRs, the first `superseded` by the second.
- **Open points → questions** (template `question.md`), one per decision topic, with the gate of the pre-code gate (🔴/🟠/🟡) from what the old content says about its urgency; when it does not say, ask.
- **Tasks → tasks** when `tasks.mode` is `wiki` (template `task.md`), with their progress; with an external tracker, they stay in the tracker: note the link in the report.
- **Knowledge → thematic notes**, following the placement rule of the constitution; one fact, one place; links by name.
- **Rules for the assistant**: what is about how the team develops goes to `wiki/project/development-workflow.md` (template of the plugin) or, for coding standards, to the report as material for a future development skill; what is specific to working on this project goes to the project-specific section of the root `CLAUDE.md`; what the framework already says is not copied.
- **People**: names go only into `wiki/project/team-and-roles.md`, and only those the user authorises one by one; everywhere else, roles and organisations (constitution, "Names of people").
- **Provenance**: in every record, `source` says where it came from — `"adopted from <path in the old folder>"`. Keep the meaning; rewrite the form to the framework's (headings of the templates, in the project language). Content in another language is translated into the project language.
- **Never resolve a contradiction alone**: two old notes that disagree, or a note that contradicts an official document, become a question with both versions quoted (hierarchy of truth).

The lint runs after every write: fix what it reports.

## 5. Code repositories

For each repository, the flow of `/projectwright:add-repository`: register the component, then — after showing its state and with the user's explicit yes — **move** it into `repositories/<name>` (history, branches and uncommitted changes are kept), or **clone** it from its remote if the user prefers to leave the old folder whole. Report the files for AI assistants found inside the repository and propose to remove them (the user commits it). Create the component folder with `scaffold.py component`.

## 6. Official documents

With the user's yes, copy the documents into the project's `docs/`, keeping their folders and names (default: `paths.official_docs` is already `docs`); or set `paths.official_docs` to the shared folder where they stay. Then tell the user that the next step is `/projectwright:ingest-sources` and `/projectwright:integrate-wiki`: the cards will be compared with the records just converted, and any disagreement will come to the user as a conflict. Do not ingest within this skill: it is a separate, long activity.

## 7. Close

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-lint.py"` and fix every violation.
2. Fill the dashboard where you can: "Where we are" in `wiki/dashboard/project-status.md`, the components, the reading paths of `knowledge-map.md`.
3. Record **`ADR-MET-0001`**: "Project adopted into projectwright <version>", with the choices of §2, the map in short (what became what, with counts), what was **not** carried and why, and the doubts still open.
4. Summary for the user: what was created, what still has to be done (ingestion of the documents, questions opened, files for AI assistants to remove from the repositories), and that **the old folder is untouched** — apart from the repositories moved — and can be deleted when they are satisfied. If the project folder is to be versioned, `scaffold.py project --git` on request; the git commands are run by the user.
