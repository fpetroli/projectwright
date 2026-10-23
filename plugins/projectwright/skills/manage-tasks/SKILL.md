---
name: manage-tasks
description: Manages the tasks of the project when the wiki is the tracker (tasks.mode = wiki) — creates tasks, moves them between todo, in progress, blocked, done and cancelled, assigns them, sets priority and phase (sprint), links them to decisions, questions and blocking tasks, and lists them. The board (board.html) shows the result. Use when the user asks to create, update, move, assign, close or list tasks, or to plan a sprint.
---

# Manage the tasks

User input: $ARGUMENTS

When `tasks.mode` is `wiki`, the wiki is the project's tracker: **one file per task**, `T-<CODE>-NNNN-<slug>.md`, in `wiki/tasks/` (cross-cutting tasks) or `wiki/components/<repo>/tasks/` (tasks of a component). The rules — fields, values, IDs, language of the content — are in the constitution (`wiki/README.md`) and in the method schema; this skill applies them. Tasks are written in `project.language`, with the headings of the existing tasks. The board `board.html` shows the tasks in columns and is regenerated automatically after every write.

If `tasks.mode` is `tracker`, the tasks live in the external tracker: say so, and stop.

## What the user can ask, and what you do

Requests come in plain words ("create a task to…", "move the cart to in progress", "assign the payment step to the backend developer", "close T-WEB-0004", "what is blocked?", "plan sprint 3"), in chat or sent from a board. Interpret them, act, and confirm in one line per task changed.

**Tasks are decided with the user** (constitution, principle 13). A request is the user's yes for what it asks — and only for that. What the request does not cover is **proposed**, never done: another task to create, a task that looks finished, a block discovered on the way, a priority that seems wrong. Write it as a proposal — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/proposals.py" add --json '<proposal>'`, after checking with `proposals.py list --status all --format json` that it is not already open or rejected — list it after the confirmation, numbered 1, 2, 3 — never with the proposal ids, which are for the tools — and write it in the wiki only after the user's yes. When the request itself leaves a choice open that changes the task (which component, which phase, what blocks it), ask; infer only the details (goal, acceptance criteria, placement), and say what you inferred.

| Request | Action |
|---|---|
| **Create** | New file from the template `${CLAUDE_PLUGIN_ROOT}/templates/records/task.md`: title, **goal** and **acceptance criteria** in the body, `progress: todo` unless said otherwise, `priority` (default `medium`), `phase`, `assignee` **by role** (never a person's name), links in `decisions`, `questions`, `blocked_by`. Place it in the component it belongs to (placement rule of the constitution) or in `wiki/tasks/`. **Safe ID**: the highest number for that code among the task files, plus one (constitution, IDs). |
| **Move** | Change `progress` (`todo`, `in-progress`, `blocked`, `done`, `cancelled`) and `updated`. Moving to `blocked`: ask what blocks it if not said, and record it in `blocked_by` (a task) or in the body (anything else). Moving to `done`: **consolidate** it (below), set `closed_on`; if commits closed it, add their hashes to `commits` (ask for them only if the user wants them recorded). |
| **Assign / prioritise / plan** | Change `assignee`, `priority`, `phase` (the phase or sprint, matching the roadmap). |
| **Link** | Add the wikilinks in `decisions`, `questions`, `blocked_by`. |
| **List** | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" tasks [--progress …] [--phase …] [--component …]`, and point to `board.html` for the visual board. |

**Proposals** (`proposals.py`, outside the wiki; the board beside the chat shows them):
- **"Apply the proposal “…” … [ref P-0003]"** — the user accepted it (the board names the proposal by its summary and ends the message with its id): read it (`proposals.py list --status all --format json`), apply it as if the user had asked for it (a `close` with its consolidation, a `split` as the new tasks plus the old one cancelled or narrowed, as the proposal says), then `proposals.py set P-0003 --status accepted`.
- **"Revise the proposal “…” on my comment: … [ref P-0003]"** — read the proposal and the comment (its `comment` field), and propose again: one corrected proposal, several, or none if the comment discards it. Write each with `proposals.py add --replaces P-0003 --json '<proposal>'` (the old one becomes `revised`), or, when nothing is left to propose, `proposals.py set P-0003 --status rejected`. Say in one line what you proposed and why.
- A proposal the user rejects in chat: `proposals.py set <id> --status rejected`.
- A `remind` proposal accepted: add its reminders (below), then mark it `accepted`.

**Reminders** (`reminders.py`, outside the wiki; the board beside the chat shows them): things to keep in mind that are not tasks — "send the e-mail", "update X" — with an optional date.
- **"Remind me to… (by Monday)"**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/reminders.py" add "<text>" --due <YYYY-MM-DD>`, turning the day the user said into a date; without a day, no `--due`. Confirm in one line.
- **Ticked, removed**: `reminders.py done <id>` / `remove <id>` (the board does it by itself); `reminders.py list` shows them.
- **"Propose a task from my reminder “…” [ref R-0002]"** (from the board): propose the task (`kind: create`); once it is accepted, `reminders.py remove R-0002`.
- A reminder that grows into real work becomes a task through a proposal (`kind: create`), and is removed once the task is accepted.
- You never add a reminder on your own: you propose it (`kind: remind`).

Rules:
- **Never delete a task** and never reuse an ID: a task that is no longer needed becomes `cancelled`.
- **Never rename a task file**: the title can change, the file name stays.
- Tasks say **what** to do; the **why** lives in ADRs and questions: link them instead of copying them.
- **The log of an open task** (constitution, principle 14): add one dated line to its **Log** for what the work found, tried, ruled out, and where it stands — without asking, it changes nothing on the board. A decision or a question found on the way goes at once to its ADR or question file (through `/projectwright:record-decisions`), and the log links it.
- **Consolidate when a task closes**: propose, together with the closing, what of its log has lasting value and which note it goes to — the component's notes, or the project level by the placement rule — and what is only history. After the yes: write it into those notes (linking the task), replace the log with an **Outcome** (what was done, in a few lines, with links to those notes), and close the task. A task cancelled keeps in its outcome why, and what it found that still holds.
- When a 🔴 question blocks a task, say so and suggest `blocked`.
- Delivery repositories never cite task IDs (constitution): commits do not mention `T-*`; the task records the commit hashes instead.

## Closing

The lint runs after every write: fix what it reports. Summarise the tasks created or changed, remind the user that `board.html` is up to date (open it in the browser), and, if the project folder is versioned, give the ready-to-paste git commands for it (commits and pushes are run by the user).
