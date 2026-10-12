---
name: change-setting
description: Changes a choice of project.yaml made at setup — language of the wiki, optional modules, areas, paths, documentation categories and exclusions, task mode (wiki or tracker), tracker settings, drafting rules, git conventions, retiring a component — and brings the existing content in line with it, so that there are never two truths. Records the change in an ADR-MET and runs the lint. Use when the user wants to change a setting of the project.
---

# Change a setting of the project

User input: $ARGUMENTS (the setting to change and the new value, in plain words)

`project.yaml` holds the choices the framework foresees. Changing one is **not** a deviation from the framework — it is a choice the framework allows — but it must leave the project coherent: **the content follows the new setting** (migration), then `project.yaml` changes, then an `ADR-MET` says why. Components are added with `/projectwright:add-repository`; `framework.version` changes only with `/projectwright:upgrade`.

## 1. Understand the change

1. Identify the key (or keys) of `project.yaml` and the new value. The allowed values are in `${CLAUDE_PLUGIN_ROOT}/schema.yaml` (`values`, `project`); if the new value is not allowed, say so and stop.
2. Find in the table of §2 what the change implies, and **measure it on this project**: how many records, notes, files or rows it touches (search the wiki, `wiki-sources/ingestion-log.csv`, the folders).
3. Ask the user why — the reason goes in the ADR — unless it is already clear from the conversation.

## 2. What each change implies

| Setting | Migration of the content |
|---|---|
| `project.name` | None beyond the titles of the dashboard notes that carry the name. |
| `project.language` | The wiki is written in the new language from now on. Ask: **translate the existing notes** (recommended: one language per wiki — titles, text and headings, keeping file names, frontmatter fields and values, wikilinks, IDs, commands and HTML comments unchanged) or keep the existing ones as they are. Cards in `wiki-sources/` are never translated: they are immutable. |
| `paths.official_docs` | If the documents moved with the same structure, nothing else (`source_path` in the log is relative to this folder). If the structure changed, run `ingestion-diff.py`: documents that look removed and new are the same documents moved — tell the user, and let `/projectwright:ingest-sources` record them. |
| `paths.repositories`, `paths.utils` | Move the folder (with the user's yes; repositories keep their git); when versioned, update `.gitignore`. |
| `wiki.optional_modules` — adding `domain` / `architecture` | Move into the new module the notes it now owns (constitution, placement rule): with several components, the cross-cutting technical views and the functional model; links are by name, so they do not break. Records (ADRs, questions, tasks) never move: their IDs stay. |
| `wiki.optional_modules` — removing a module | Move its notes to the project level or to the component they concern; the folder disappears with its last file. |
| `wiki.areas` | Adding a code: nothing. A code already used by records **cannot be removed or renamed** (IDs never change): only its label can change. |
| `components` — retiring one | Set `component_status: retired` in its entry note and in the dashboard; its folder stays intact; open questions and tasks of the component: ask whether to close them (`closure_reason`) or keep them. Never delete or rename the component. |
| `sources.categories` | Adding: nothing (the folder is born with the first card). Removing a category with cards: cards are immutable, so the category stays as long as it has cards — say so. |
| `sources.exclude` | Run `ingestion-diff.py` before and after: documents already ingested that are now excluded keep their cards and rows; ask whether the knowledge they brought still holds. |
| `tasks.mode`: `wiki` → `tracker` | The open tasks (`progress` not `done`/`cancelled`) become issues of the tracker, field by field (title, goal and acceptance criteria, priority, assignee by role, blocks): through the tracker's MCP server, when connected, writing as `tracker.write_mode` says (`propose`: show each issue and wait for the yes); otherwise prepare an import file in `utils/` for the user. In each task file add the issue key (in the body, "Tracker: KEY-…"), set `progress: cancelled` with the reason "moved to the tracker" — the files stay as history. Fill `tracker.*` first (type, project key, `client_visible`, `write_mode`). |
| `tasks.mode`: `tracker` → `wiki` | The open issues become task files (template `${CLAUDE_PLUGIN_ROOT}/templates/records/task.md`), with safe IDs and the issue key in the body; through the MCP server or from an export the user provides. Closed issues are not imported unless the user asks. |
| `tracker.*` | `client_visible: true` forbids `write_mode: auto` (the lint checks it). Changing tracker type or project: the keys cited in the wiki stay as history; say so. |
| `drafting.*` | No migration: the rules apply to documents written from now on; existing minutes and documents are official documents and are not rewritten. |
| `git.*` | No migration of history. If `wiki/project/development-workflow.md` contradicts the new value, align the note. |
| `dev_skills` | Only names of folders that exist in `.claude/skills/`; the skill itself is created or removed by the user (or by `/projectwright:create-dev-skill`, when available). |

Changes of several keys together (for example `tasks.mode` with `tracker.*`) are one change, with one ADR.

## 3. Propose, then apply

1. Show the user the change and its migration **measured on this project**: "`tasks.mode` wiki → tracker: 7 open tasks become issues of `SHOP` (list), 12 closed tasks stay as history; nothing else changes". Wait for the yes; for language and modules, also the choice of §2.
2. Apply **the migration first, then `project.yaml`** — keeping its comments and order — so that the content is never behind the setting.
3. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" project`: it adds only what the new setting needs and never overwrites.

## 4. Close

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-lint.py"`: it validates `project.yaml` against the schema and the coherence of the wiki with it. Fix every violation.
2. Record an **`ADR-MET`** (template `${CLAUDE_PLUGIN_ROOT}/templates/records/decision.md`): "<setting>: <old> → <new>", with the reason, the migration done (with counts) and what was left as history. It is **not** a framework deviation: no `framework_deviation`.
3. Update the dashboard where the change shows (for example the components, or a note in "Where we are").
4. Summary for the user, with — if the project folder is versioned — the ready-to-paste git commands (commits and pushes are run by the user).
