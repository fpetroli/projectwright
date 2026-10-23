# Changelog

All notable changes to the projectwright framework are recorded here. Versions follow [semantic versioning](https://semver.org/): a **major** version changes the data schema (folders, fields, IDs) in an incompatible way, a **minor** version adds compatible features, a **patch** fixes errors. Every entry that touches the method ends with its **upgrade notes**: what `/projectwright:upgrade` cannot do by merging files — new configuration, changes to the notes translated into the project language, data.

## [Unreleased] — 0.2.0 in development

The plugins of the marketplace carry the version `0.2.0-dev` until the release: what follows can still change.

### Added

- **The `projectwright-board` plugin** (optional, in development): the tasks of the wiki in a pane beside the Claude Code chat, kept up to date as the wiki changes, with the detail of a task, a form to create one, an edit form and a button that brings a task into Claude's context. Every change made from the pane goes through Claude, with `/projectwright:manage-tasks` and the lint; the pane never writes the wiki. It is a Claude Code hooks module (mod), an early-access API; it is released together with `projectwright`, with the same version, and checks at every refresh that `projectwright` is there with that version. See `plugins/projectwright-board/README.md`.
- **`wiki-query.py task <file name or ID>`**: one task in full — every frontmatter field, its body and the notes it links — as JSON (`--format json`), Markdown or a table.
- **The title of each task** in the JSON of `wiki-query.py tasks` (the table and Markdown outputs, and the dashboard, are unchanged).
- **The dashboard in JSON**: `wiki-query.py dashboard --format json` prints one object with the sections of the dashboard (blocking questions, other open questions, recent decisions, components, tasks in progress or blocked, cards to integrate, deviations, lint violations); before, it printed the text. The text and Markdown outputs are unchanged.
- **One definition for the two boards**: `assets/board-model.json` says what a board shows — the columns and their colors, the priorities, the fields of a card, of the table and of the detail, and their names. `board.html` and the pane of `projectwright-board` both read it, so they show the same thing; a project that changes it changes both.
- **The fields of a card** in the JSON of `wiki-query.py tasks`: `id`, `updated`, `closed_on`, `blocked_by` (the table and Markdown outputs are unchanged).
- **`/projectwright:upgrade` and the board**: a board copied into the project (`.claude/skills/projectwright-board/`) is replaced with the board released beside the new version; with the plugins installed, the upgrade updates the board too.

### Changed

- **`board.html` shows the tasks only**, laid out like a database: a Board view (the pipeline in columns) and a Table view (rows grouped by progress), with the detail of a task in a panel beside them, and a search. The overview, the questions, the decisions, the components and the sources are no longer in it: the dashboard at the start of each session and the wiki itself keep them.
- **The pane of `projectwright-board` shows one column at a time**: the columns are tabs with their count, a digit chooses one; every task is a full card (title, ID, priority, assignee, what blocks it), and the done tasks show the newest few, the rest on request. The detail lists the same properties as `board.html`.

### Upgrade notes

- `projectwright`: nothing to configure, no data to change. A project that changed `assets/board.html` merges it with the new layout, which is a different page: keep the new one and apply the change again if it is still needed.
- `projectwright-board` is optional and is not installed by the upgrade. To use it: `claude plugin install projectwright-board@projectwright --scope project`, then a new session. It does not install `projectwright`: a project that copies `projectwright` into `.claude/skills/projectwright/` keeps its copy and installs only the board.

## [0.1.0] — 2026-10-12

First public release.

### Added

- **The `projectwright` plugin**, distributed by this repository as a Claude Code plugin marketplace. It can be installed for a project (`claude plugin install projectwright@projectwright --scope project`) or copied into it (`framework.py vendor`) to adapt the method, with every change tracked.
- **The project structure**: `CLAUDE.md` (the rules, importing `project.yaml`), `project.yaml` (the choices of the project, validated against `schema.yaml`), `wiki/` (the AI's memory, with its constitution), `wiki-sources/` (ingestion cards and log), `docs/` (official documents, structured by the user), `repositories/` (the code, one git repository each), `utils/` (files created on request), `board.html` (a generated view of the project).
- **The wiki**: decisions (ADRs), questions with the traffic light of the pre-code gate (🔴/🟠/🟡), tasks, thematic notes, components with their roadmap, a dashboard; IDs by area and component; one fact, one place; names of people only where allowed.
- **Skills**:
  - setup: `setup-project`, `add-repository`, `change-setting`, `adopt-framework`;
  - knowledge cycle: `ingest-sources`, `integrate-wiki`, `record-decisions`;
  - documents: `draft-minutes`, `propose-docs`;
  - tasks: `manage-tasks`;
  - checks: `wiki-check`, `audit-code`;
  - the framework itself: `propose-improvement`, `upgrade`, `framework-feedback`.
- **Hooks**: at the start of the session, the plugin check, the user's working profile, the dashboard and the board; after every write in the wiki, the lint and the board; before every commit of a versioned project folder, the full lint.
- **Scripts**, plain Python ≥ 3.11 with no dependencies to install: `wiki-lint.py`, `wiki-query.py`, `board.py`, `ingestion-diff.py`, `scaffold.py`, `framework.py` (fingerprint of the framework files, deviations, `vendor`, `check`, guided `upgrade` with three-way merge, `permissions`), `profile.py`.
- **The personal working profile** (`~/.claude/projectwright/profile.md`): how the user likes to work, learned by Claude and shared by all their projects.
- **The development workflow note** (`wiki/project/development-workflow.md`): branches, commits, merge requests and review of the team; commits, pushes and merge requests are always run by people.
