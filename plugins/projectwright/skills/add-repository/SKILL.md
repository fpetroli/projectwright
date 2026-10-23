---
name: add-repository
description: Adds a component to the project — clones (or registers) its code repository in repositories/, registers it in project.yaml with a unique code, and creates its twin folder in wiki/components/ with the entry note and roadmap. Use when the user wants to add a repository or a component to the project.
---

# Add a repository (component)

User input: $ARGUMENTS

## 1. What you need

From `$ARGUMENTS` or by asking, in one grouped question:

- **name** of the component: the folder name in `repositories/` (lower case, hyphens). It is **permanent** — the wiki folder and the entry note take it, and file names are never renamed;
- **URL** of the git repository, if it exists (it can be added later: a component can be planned before its repository exists);
- **code**: 2–8 capital letters, unique among the area codes and the other components (propose one from the name, for example `web-portal` → `WP`); it prefixes the ADRs and questions of the component, and is the `area` of its tasks (whose IDs, `TASK-NNNN`, are numbered for the whole project);
- one line on **what the component is**.

Check in `project.yaml` that name, code and repository are not already used.

## 2. The repository

Code repositories live **only** in `repositories/` (`paths.repositories`): never a path outside the project, never a link to another folder.

- **Only online** (or everything is pushed): `git clone <url> repositories/<name>` (cloning is allowed; commits and pushes stay with the user).
- **Already in `repositories/`**: just register it.
- **On this computer, in another folder** (for example `~/code/web-shop`): it is **moved** into `repositories/<name>` — a moved git repository keeps its history, branches and uncommitted changes. Claude Code may have no access to folders outside the project: if reading the folder is denied, ask the user either to grant access (`/add-dir <folder>`) or to move it themselves with the command below and run this skill again. First show the user its state (`git -C <folder> status --short`, current branch, `git -C <folder> remote get-url origin` for the `url`); warn that editors and terminals open on the old path must be reopened on the new one; then, **only after the user's explicit yes**, move it:
  ```
  python3 -c "import shutil; shutil.move(r'<folder>', r'repositories/<name>')"
  ```
- **No repository yet**: the component is `planned`; the folder comes later.

Code repositories are never part of the project folder's own versioning (if it is versioned, `repositories/` is in its `.gitignore`), and never write notes, skills or `CLAUDE.md` files inside a code repository.

## 2b. What the repository already contains

Look at an existing repository before going on, and report to the user:

- **Documentation** — `README*`, `docs/`, ADRs or design notes written in the repository: it stays there (it is part of the product), but its knowledge belongs in the wiki. Propose to ingest it: `/projectwright:ingest-sources repositories/<name>/docs` (or the folder that holds it), then `/projectwright:integrate-wiki`.
- **How the team contributes** — `CONTRIBUTING*`, merge request or pull request templates (`.github/pull_request_template.md`, `.gitlab/merge_request_templates/`), a description of branches and reviews in the README: the team's development workflow. Propose to ingest them with the documentation; integration writes them into `wiki/project/development-workflow.md` (created from the plugin template when missing). If the repository works differently from the others, the note says so in its section "Differences between repositories".
- **Files for AI assistants** — `CLAUDE.md`, `CLAUDE.local.md`, `.claude/`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md` and similar: Claude would load some of them when working in the repository, with rules that may contradict those of the project, and a delivered repository should not contain them (root `CLAUDE.md`, map of the project). Propose to move their content into the wiki or into a development skill and to remove them from the repository; **the user decides**, and removing them is a change of the code repository that the user commits.

## 3. Register and create

1. Add the component to `components` in `project.yaml`:
   ```yaml
     - name: <name>
       code: <CODE>
       repository: <name>
       url: <url or null>
       tracker_component: null
   ```
2. Create its wiki folder:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" component <name> --code <CODE> --status <active|planned>
   ```
   It creates `wiki/components/<name>/` with the entry note `<name>.md` and `<name>-roadmap.md`; `decisions/`, `questions/` and `tasks/` are born with their first record.
3. Fill the entry note: the one line on what the component is (title of the body), and what is already known about its scope. Leave the placeholders that nobody can fill yet. If `project.language` is not English, translate the entry note and the roadmap into it, reusing the headings of the other components if there are any (constitution, "Language of the content").
4. Add one line for the component in the "Components" section of `wiki/dashboard/project-status.md`.
5. **If this is the second component** (the project goes from one repository to several): tell the user that from now on what touches both components goes to the project level (constitution, "Placement rule"); propose activating the modules `architecture` and `domain` in `wiki.optional_modules` if they are not active, recording the choice in an `ADR-MET`; and point out the thematic notes of the first component that look cross-cutting, which can be moved to the project level (links are by name). The records of the first component — decisions, questions, tasks — stay where they are: IDs never change.

## 4. Check and close

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-lint.py"` and fix any violation. If the project folder is versioned, give the user the ready-to-paste git commands for it (commits and pushes are run by the user).
