# CLAUDE.md

> **Start check**: sessions must start in the directory that contains this file (the project root). If your working directory is a different one (for example a repository inside `repositories/`), the workspace instructions and the `projectwright` plugin are NOT loaded: do nothing else, and tell the user to restart Claude Code from the project root.

> This file is provided by the `projectwright` framework. It holds no project values: they come from `project.yaml`, imported below. It can be changed for this project, but every change is a deviation from the framework and is recorded with an `ADR-MET` marked `framework_deviation: true`.

## Project configuration

@project.yaml

## Map of the project

- This folder is the **brain** of the project: `CLAUDE.md`, `project.yaml`, `wiki/` (the AI's memory), `wiki-sources/` (ingestion cards), `.claude/` (project settings, the development skills and, when it is copied into the project, the `projectwright` plugin). It is internal to the team and is never delivered. It is **not versioned by default**: it becomes a git repository only if the user asks (`scaffold.py project --git`), for example to share it with the team.
- `utils/` (`paths.utils`) holds the **files the user asks you to create** that are neither code of a repository nor knowledge of the wiki: lists, tables, CSV, exports, drafts, support scripts, reports. Versioned with the brain repository.
- `board.html` is a **generated, read-only view** of the tasks of the wiki (a board in columns and a table, with the detail of each task), to open in a browser. It is regenerated automatically by the hooks; never edit it and never version it. To regenerate it by hand: `python3 "<plugin>/scripts/board.py"`.
- `repositories/` (`paths.repositories`) holds the **product**: code repositories, each with its own git, never part of the brain (if the brain is versioned, `repositories/` is in its `.gitignore`). They contain **only code**: never notes for the AI, skills, `CLAUDE.md` files, nor references to the wiki.
- `docs/` (`paths.official_docs`) holds the **official documentation** — specifications, analyses, minutes — when it lives in the project; otherwise `paths.official_docs` points to the team's shared folder. **Its structure is the user's**: never reorganise, rename or change its documents; write there only new documents the user asks for (for example minutes), where they say. When `paths.official_docs` is not set, ask the user for the path.
- The rules for writing in the wiki are in its constitution, `wiki/README.md`: read it before writing in `wiki/` or `wiki-sources/`.

## Hierarchy of truth

**1. human documentation → 2. wiki → 3. code → 4. chat.**

- A discrepancy is resolved upwards: the lower level adapts, or the divergence is reported;
- **but no source wins automatically**: in front of a conflict between two sources — document vs document, wiki vs code, session vs wiki — stop and let the user arbitrate;
- what the user says in chat becomes truth **only when it is recorded in the wiki**.

## Rules that always apply

1. **Start of session**: the dashboard reaches you through the start-of-session hook of the plugin. If it did not arrive, run `python3 "<plugin>/scripts/wiki-query.py" dashboard` and read `wiki/dashboard/project-status.md`. `<plugin>` is the folder of the `projectwright` plugin: the start-of-session hook gives it ("projectwright plugin …") and writes it in `.claude/.projectwright-plugin`; when the plugin is copied into the project it is `.claude/skills/projectwright`.
2. **Before writing code**: run the pre-code gate (`wiki/dashboard/operating-assumptions.md`, the component folder in `wiki/components/`, the open questions). A task that falls on a 🔴 point is **not implemented**: stop and report to the user. On 🟠 points proceed with the declared assumption and the prescribed precaution.
3. **Development goes through the development skills** of the project, when it has them (listed in `dev_skills`): they carry the pre-code gate and the tracked closing.
4. **Tracking is not optional**: every session that decides, discovers or changes something **closes by recording in the wiki** with `/projectwright:record-decisions` — automatically, without asking for consent.
5. **After every write in the wiki** the lint runs by itself through the hook: fix the violations it reports immediately.
6. **Development standards are binding** and live in the references of the development skills: no silent deviation, in any direction — a conflict between a standard and the wiki is exposed to the user.
7. **Files provided by the framework** (this file except its last section, the constitution, `wiki-sources/README.md`, `.githooks/` and, when it is copied into the project, the plugin in `.claude/skills/projectwright/`) can be changed, but every change is a deviation to motivate: `/projectwright:record-decisions` records it, and `/projectwright:propose-improvement` prepares a proposal to bring it back to the framework. The files of an **installed** plugin are not changed: to adapt them, first copy the plugin into the project with `python3 "<plugin>/scripts/framework.py" vendor`, on the user's request. The framework is upgraded only with `/projectwright:upgrade`, which keeps these changes.
8. **Commits, pushes and merge requests are always run by the user**: for every versioned repository changed — the code repositories, and the project folder if it is versioned — prepare ready-to-paste git commands following `git.convention` and, when it exists, the team's development workflow (`wiki/project/development-workflow.md`: branch names, commits, merge requests, review); when a change is ready for review, prepare the text of the merge request the same way. Branch names, commit messages and merge requests never carry IDs of the wiki nor names of people (constitution, rule 11). Never run `git commit` or `git push`, never open or merge a merge request.
9. **Tracker**: when `tasks.mode` is `tracker`, writing to the tracker follows `tracker.write_mode`; with `propose`, prepare the content and let the user confirm.
10. **Files on request**: when the user asks you to create a file that is not code of a repository nor knowledge of the wiki, save it in `paths.utils` (default `utils/`), unless the user says otherwise; group files in subfolders by topic when they grow. A fact or a decision never lives only there: it goes in the wiki.
11. **Language**: in chat, the user's language; content written in the wiki in `project.language`.
12. **Python**: the scripts need Python ≥ 3.11 and nothing else. The commands in this file and in the skills use `python3`; on Windows use `python`.
13. **Working profile of the user**: the start-of-session hook gives you the user's working preferences, from their personal profile (outside the project, shared by all their projects): follow them. When the user shows a **stable** preference about how they want to work — how to present analyses, how many questions at a time, how much autonomy, level of detail, tone — record it with `python3 "<plugin>/scripts/profile.py" add "<preference>"`, in the user's language; when one stops holding, remove it (`profile.py remove`). Only ways of working: never project facts (they go in the wiki), never names or confidential data. Say in one line what you recorded.

## Project-specific instructions

<!-- This section belongs to the project: instructions of this project only, in any language. Changes here are not deviations from the framework. -->
