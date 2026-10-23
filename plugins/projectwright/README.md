# projectwright — the method

The plugin of the projectwright framework: a project wiki as the AI's memory, the skills of the knowledge cycle, automatic checks, templates and a project board. It is distributed by the projectwright marketplace (the repository that contains this folder) and works in either of two ways:

- **installed for the project** (the usual way): Claude Code keeps it in its plugin cache, and the project's `.claude/settings.json` enables it;
- **copied into the project**, in `.claude/skills/projectwright/`, when the project wants to change the plugin's own files: every change is tracked as a deviation from the framework.

## Set up a project

1. From the project folder: `claude plugin marketplace add fpetroli/projectwright --scope project`, then `claude plugin install projectwright@projectwright --scope project`. (Or copy this folder into the project as `.claude/skills/projectwright/`.)
2. Start Claude Code **in the project folder** and trust it; if the `/projectwright:…` skills are not there yet, run `/reload-plugins`.
3. Run `/projectwright:setup-project`: a short interview, then the wiki, `project.yaml`, the dashboard and the root `CLAUDE.md`.
4. Add the code repositories with `/projectwright:add-repository`.

Requirements: Claude Code, git, Python ≥ 3.11 (nothing to install: PyYAML is included).

## What it contains

| Path | Content |
|---|---|
| `skills/` | The skills, invoked as `/projectwright:<skill>`: `setup-project`, `add-repository`, `ingest-sources`, `integrate-wiki`, `record-decisions`, `draft-minutes`, `propose-docs`, `propose-improvement`, `manage-tasks`, `wiki-check`, `audit-code`, `upgrade`, `adopt-framework`, `change-setting`, `framework-feedback` |
| `hooks/hooks.json` | Lint after every write in the wiki; at the start of every session a check of the plugin setup, the user's working profile and the dashboard; `board.html` kept up to date |
| `scripts/` | `wiki-lint.py`, `wiki-query.py`, `ingestion-diff.py`, `scaffold.py`, `framework.py`, `board.py`, `profile.py`, the common library `pwlib.py`, PyYAML in `_vendor/` |
| `CHANGELOG.md` | Changes by version, with how to apply them to an existing project |
| `assets/board.html` | The layout of the board, the read-only view of the tasks generated into `board.html` |
| `assets/board-model.json` | What a board shows — columns, colors, priorities, the fields of a card, of the table and of the detail — read by `board.py` and by the pane of `projectwright-board` |
| `schema.yaml` | The method schema: record types, allowed values, required fields, rules of `project.yaml` |
| `templates/` | The files written into a project: root `CLAUDE.md`, wiki constitution, dashboard notes, record templates, `project.yaml`, git hook |

## The board

`board.html`, in the project root, is a read-only view of the tasks of the wiki to open in a browser: a Board view in columns and a Table view, with the detail of a task beside them. It is regenerated automatically; with `tasks.mode: wiki` it works as the project's tracker, together with `/projectwright:manage-tasks`. The pane of `projectwright-board` shows the same thing beside the chat: both read `assets/board-model.json`, so a change there changes both.

## Improving the method from your projects

A project can adapt the files of the framework — the plugin's own files only once it is copied into the project (`scripts/framework.py vendor` copies the installed plugin into the project and stops enabling the installed one there). Every change is detected (lock file `.claude/projectwright.lock.json`, `wiki-query.py deviations`) and motivated by an ADR; when a change can help other projects, `/projectwright:propose-improvement` writes an anonymous proposal document to bring to the framework.

The rules of the wiki are in its constitution, `templates/wiki/README.md`, which becomes `wiki/README.md` in the project.
