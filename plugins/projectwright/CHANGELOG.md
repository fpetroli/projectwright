# Changelog

All notable changes to the projectwright framework are recorded here. Versions follow [semantic versioning](https://semver.org/): a **major** version changes the data schema (folders, fields, IDs) in an incompatible way, a **minor** version adds compatible features, a **patch** fixes errors. Every entry that touches the method ends with its **upgrade notes**: what `/projectwright:upgrade` cannot do by merging files — new configuration, changes to the notes translated into the project language, data.

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
