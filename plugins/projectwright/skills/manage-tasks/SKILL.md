---
name: manage-tasks
description: Manages the tasks of the project when the wiki is the tracker (tasks.mode = wiki) — creates tasks, moves them between todo, in progress, blocked, done and cancelled, assigns them, sets priority and phase (sprint), links them to decisions, questions and blocking tasks, and lists them. The board (board.html) shows the result. Use when the user asks to create, update, move, assign, close or list tasks, or to plan a sprint.
---

# Manage the tasks

User input: $ARGUMENTS

When `tasks.mode` is `wiki`, the wiki is the project's tracker: **one file per task**, `T-<CODE>-NNNN-<slug>.md`, in `wiki/tasks/` (cross-cutting tasks) or `wiki/components/<repo>/tasks/` (tasks of a component). The rules — fields, values, IDs, language of the content — are in the constitution (`wiki/README.md`) and in the method schema; this skill applies them. Tasks are written in `project.language`, with the headings of the existing tasks. The board `board.html` shows the tasks in columns and is regenerated automatically after every write.

If `tasks.mode` is `tracker`, the tasks live in the external tracker: say so, and stop.

## What the user can ask, and what you do

Requests come in plain words ("create a task to…", "move the cart to in progress", "assign the payment step to the backend developer", "close T-WEB-0004", "what is blocked?", "plan sprint 3"). Interpret them, act, and confirm in one line per task changed.

| Request | Action |
|---|---|
| **Create** | New file from the template `${CLAUDE_PLUGIN_ROOT}/templates/records/task.md`: title, **goal** and **acceptance criteria** in the body, `progress: todo` unless said otherwise, `priority` (default `medium`), `phase`, `assignee` **by role** (never a person's name), links in `decisions`, `questions`, `blocked_by`. Place it in the component it belongs to (placement rule of the constitution) or in `wiki/tasks/`. **Safe ID**: the highest number for that code among the task files, plus one (constitution, IDs). |
| **Move** | Change `progress` (`todo`, `in-progress`, `blocked`, `done`, `cancelled`) and `updated`. Moving to `blocked`: ask what blocks it if not said, and record it in `blocked_by` (a task) or in the body (anything else). Moving to `done`: set `closed_on`; if commits closed it, add their hashes to `commits` (ask for them only if the user wants them recorded). |
| **Assign / prioritise / plan** | Change `assignee`, `priority`, `phase` (the phase or sprint, matching the roadmap). |
| **Link** | Add the wikilinks in `decisions`, `questions`, `blocked_by`. |
| **List** | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" tasks [--progress …] [--phase …] [--component …]`, and point to `board.html` for the visual board. |

Rules:
- **Never delete a task** and never reuse an ID: a task that is no longer needed becomes `cancelled`.
- **Never rename a task file**: the title can change, the file name stays.
- Tasks say **what** to do; the **why** lives in ADRs and questions: link them instead of copying them.
- When a 🔴 question blocks a task, say so and suggest `blocked`.
- Delivery repositories never cite task IDs (constitution): commits do not mention `T-*`; the task records the commit hashes instead.

## Closing

The lint runs after every write: fix what it reports. Summarise the tasks created or changed, remind the user that `board.html` is up to date (open it in the browser), and, if the project folder is versioned, give the ready-to-paste git commands for it (commits and pushes are run by the user).
