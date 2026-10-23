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
- **Proposals of Claude, outside the wiki**: `scripts/proposals.py` keeps the changes to the tasks that Claude proposes — create, move, close, split, edit, cancel — in `.claude/.projectwright-proposals.json`, personal and never versioned, until the user decides; a rejected proposal stays there so that it is not proposed again. `record-decisions` and `manage-tasks` write their proposals there, and apply or revise them on request. The pane of `projectwright-board` shows them above the columns, to **accept**, **reject** (without a turn of Claude) or **comment** (Claude proposes again).
- **Reminders**: `scripts/reminders.py` keeps the user's reminders — things to keep in mind that are not tasks, with an optional date — in `.claude/.projectwright-reminders.json`, personal and never versioned. The user adds them ("remind me to…", or from the pane); Claude proposes them (proposals of kind `remind`) and never adds one on its own. The pane shows them as a checklist below the proposals — tick, add and remove without a turn of Claude, turn one into a task through a proposal — and `board.html` shows the same checklist, written again at every change of a reminder.
- **A blocked task says so, and says why**: a task that an open task blocks is `blocked`, and the lint now reports one left in `todo` or `in-progress`; `manage-tasks` moves a task to `blocked` when it gets an open blocker and, when a task closes, proposes to free the tasks it blocked. The boards show "Blocked by" only for the blockers still open; the detail marks the closed ones.
- **The ids of the proposals are for the tools**: the pane never shows them, Claude numbers the proposals 1, 2, 3 in chat, and the wiki never cites them.
- **`/projectwright:upgrade` and the board**: a board copied into the project (`.claude/skills/projectwright-board/`) is replaced with the board released beside the new version; with the plugins installed, the upgrade updates the board too.

### Changed

- **Tasks are numbered once for the whole project: `TASK-NNNN`** (`TASK-0012`), the board's numbering, as in a tracker, instead of one number per code (`T-WEB-0012`). The component of a task is its folder and its `area`, as before; decisions and questions keep `ADR-<CODE>-NNNN` and `Q-<CODE>-NNNN`. Schema (`id_scope: project`), lint, constitution, task template, skills and boards follow; the boards still read the old ids until a project is renumbered.
- **A task holds the work in progress; closing it consolidates it.** While a task is open, its new **Log** section keeps what the work finds, tries and rules out; decisions and questions still go at once to their ADR or question. When the task closes, what has lasting value moves to the notes of its component and the log gives way to an **Outcome**, proposed with the closing. New principle 14 of the constitution; `manage-tasks` and `record-decisions` follow it; the task template has the two new sections.
- **Tasks are decided with the user**: no skill creates, moves, closes, cancels, assigns or re-prioritises a task on its own any more. Claude proposes — `/projectwright:record-decisions` ends with a list of tasks to confirm, `/projectwright:manage-tasks` does what was asked and proposes the rest — and writes after the user's yes; a request of the user, in chat or from the board, is already the yes. Only the `commits` of a task are written without asking. New principle 13 of the constitution, rule 9 of `CLAUDE.md`.
- **`board.html` shows the tasks only**, laid out like a database: a Board view (the pipeline in columns) and a Table view (rows grouped by progress), with the detail of a task in a panel beside them, and a search. The overview, the questions, the decisions, the components and the sources are no longer in it: the dashboard at the start of each session and the wiki itself keep them.
- **The pane of `projectwright-board` has two views**, as `board.html` has Board and Table: **Board**, the columns side by side, with the empty ones reduced to their heading; **List**, the columns one under the other, as groups that open and close. It opens in the one the width allows, and `v` swaps them. Every task is a full card (title, ID, priority, assignee, what blocks it), and the done tasks show the newest few, the rest on request. The detail lists the same properties as `board.html`.

### Upgrade notes

- `projectwright`: nothing to configure. **Data: renumber the tasks** — `python3 "<plugin>/scripts/framework.py" renumber-tasks` shows the plan (old id → new id, in order of creation), `--apply` renames the task files and rewrites every mention in `wiki/` and in the proposals and reminders; then the lint must pass. Ingestion cards are not changed: the command names any that cites an old task id. When the project folder is versioned, add `.claude/.projectwright-proposals.json` and `.claude/.projectwright-reminders.json` to its `.gitignore` (proposals and reminders are personal). Existing tasks need no change: the **Log** and **Outcome** sections appear in the tasks written from now on; in a project whose language is not English, the first task that uses them translates their headings, and the next ones reuse them (constitution, "Same headings everywhere"). A project that changed `assets/board.html` merges it with the new layout, which is a different page: keep the new one and apply the change again if it is still needed.
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
