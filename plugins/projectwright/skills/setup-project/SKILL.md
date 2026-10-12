---
name: setup-project
description: Sets up a project with projectwright — a short interview, then project.yaml, the wiki, wiki-sources/, the dashboard, the root CLAUDE.md, the git hooks and the first ADR-MET with the initial choices. Use right after the projectwright plugin has been installed for the project (or copied into it), or when the user asks to set up the project.
---

# Set up the project

User input: $ARGUMENTS

The plugin is already loaded — installed for this project from the projectwright marketplace (`claude plugin install projectwright@projectwright --scope project`), or copied into `.claude/skills/projectwright/` — and the session was started from the project root. The mechanical part is done by `scaffold.py`, which never overwrites existing files; this skill runs the interview and writes the choices.

## 0. Check where you are

- If `project.yaml` already exists **and** `wiki/README.md` exists, the project is already set up: say so and stop. To add a component use `/projectwright:add-repository`; to change a choice, `/projectwright:change-setting`.
- **If the folder already holds a project** — notes, decision logs, documents, rules for AI assistants, beyond code — **stop** and propose `/projectwright:adopt-framework`: it brings that project into the framework from a new folder next to it, leaving this one untouched.
- **If the folder is itself a code repository** (a git repository with source code and history, not an empty folder just initialised): **stop**. The brain repository must never live inside a delivered repository (principle 1). Propose to create the project **next to it** — for example `<folder>-project/` — and to move the code repository into its `repositories/` with `/projectwright:add-repository`; the user decides, then restarts Claude Code in the new folder.
- If the folder contains other files (documents, notes…), list them, **move or delete nothing**, and ask the user to confirm before proceeding. Code repositories belong in `repositories/`: suggest moving them there with `/projectwright:add-repository`, but only the user decides.

## 1. Interview

Ask in **two or three grouped questions**, always proposing the default, and accept "default" as an answer:

1. **Project**: name (default: the folder name); language of the wiki content (default: the language of this conversation).
2. **Sources**: where the official documentation lives (minutes, technical and functional documents) — in the project's `docs/` (default; its structure is the user's), or in a shared folder outside the project (`paths.official_docs`); and whether part of the documentation lives **online** (Confluence, another wiki, a tracker): if so, which system — its pages are ingested through its MCP server, which each person connects with their own account (`claude mcp add --scope project …`, following the documentation of the server; credentials never in the repository).
3. **Wiki**: optional modules — default **none** with zero or one known repository (with a single repository architecture and domain live in the component, constitution "Placement rule"), `domain` and `architecture` with two or more; area codes (default: `PRJ`, `MET`, `DOM`, `ARCH`, `STD`, `INT`).
4. **Tasks**: `wiki` (tasks as files in the wiki — default) or `tracker` (an external tracker: type, project key, whether the client can read it).
5. **Drafting rules** for minutes and documents: show the defaults (no names of people, no economics, no opinions, self-contained documents) and ask whether to keep them.
6. **Git**: commit convention for the code repositories (default Conventional Commits); and, only if the user knows it already, how the team works with **branches and merge requests** (branch names, what a merge request must contain, reviewers by role, merge method) — otherwise it is filled later, from a repository's contributing guide or from a decision. The project folder itself is **not** versioned unless the user asks; if they want it versioned (for example to share it with the team), main branch (default `main`).
7. **Components**: the code repositories already known (name, URL), if any.
8. **Permissions**: Claude runs the framework's scripts often (lint, dashboard, ingestion): allow them without asking? (default yes) — only those scripts, a personal setting of this computer, never versioned.

Do not ask about what has a sensible default and does not matter now.

## 2. Create the structure

From the project root:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" project --name "<name>" --language <code>
```

It creates `project.yaml` from the template, the framework files (`CLAUDE.md`, the constitution `wiki/README.md`, `wiki-sources/README.md`, the dashboard notes, `team-and-roles.md`, `roadmap.md`), `utils/` (for the files the user asks to create), the empty ingestion log, and the lock file of the framework files with their original copy. It does **not** version the project folder. Only if the user asks to version it, add `--git`: it also writes `.gitignore`, `.gitattributes` and the git hook `.githooks/pre-commit`, initialises git and activates the hook.

## 3. Write the choices

1. Edit `project.yaml` with the answers of the interview (keep its comments). Do not register components here: §5 does it.
2. Run the scaffold again — it only adds what the new choices need (for example the folders of the optional modules, or `wiki/tasks/`):
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" project
   ```
3. **Language**: if `project.language` is not English, translate into it the notes just created from the templates — `wiki/dashboard/*.md`, `wiki/project/team-and-roles.md`, `wiki/roadmap.md` — keeping file names, frontmatter fields and values, wikilinks, commands and all HTML comments (views, markers) unchanged (constitution, "Language of the content").
4. If the interview gave the team's development workflow, create `wiki/project/development-workflow.md` from the plugin template `${CLAUDE_PLUGIN_ROOT}/templates/wiki/project/development-workflow.md`, in the project language, with what was said (the rest stays as placeholders).
5. Fill the dashboard notes where you can: in `wiki/dashboard/project-status.md` the "Where we are" section (the project is being set up), in `wiki/dashboard/knowledge-map.md` the reading paths that already make sense. Leave the other placeholders: the knowledge cycle will fill them.
6. If the user allowed it (interview, point 8), let Claude run the framework's scripts without asking:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/framework.py" permissions
   ```
   It writes allow rules for the plugin's scripts only in `.claude/settings.local.json` (personal, never versioned); the start-of-session check keeps them up to date when the plugin moves. `--remove` takes them away.
7. Record **`ADR-MET-0001`** in `wiki/decisions/` (template `${CLAUDE_PLUGIN_ROOT}/templates/records/decision.md`): "Project set up with projectwright <version>", with the choices of the interview in the Decision section and their reasons in the Rationale section, headings in the project language.

## 4. Check

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-lint.py"
```

Fix any violation. Then show the dashboard: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" dashboard`.

## 5. Next steps

1. For each known component: `/projectwright:add-repository`.
2. When there is official documentation: `/projectwright:ingest-sources`, then `/projectwright:integrate-wiki`.
3. If the project folder is versioned, give the user the ready-to-paste git commands for the first commit (commits and pushes are run by the user), with a message following `git.convention`; otherwise remind them that the project folder is not versioned (back it up, or ask to version it to share it with the team).
4. Remind the user that from the next session the dashboard reaches Claude automatically, and that every session closes with `/projectwright:record-decisions`.
