# projectwright-board — the board beside the chat

An optional plugin of the projectwright framework: the tasks of the project wiki in a pane beside the Claude Code chat, kept up to date as the wiki changes. It adds to `board.html` and to the hooks of the `projectwright` plugin; it replaces neither.

It is a Claude Code **mod**: a TypeScript hooks module that runs inside Claude Code. The logic stays in the `projectwright` scripts: the board only draws what `wiki-query.py` answers.

## Install

The board needs the **`projectwright` plugin of the same version**, from the same marketplace. In a project that already uses projectwright:

```
claude plugin install projectwright-board@projectwright --scope project
```

or, at the prompt of a session, `/plugin install projectwright-board@projectwright`. Then start a new session in the project folder.

Installing the board does not install `projectwright`: install it first, or keep the copy the project has in `.claude/skills/projectwright/`. This is on purpose: a project that copies projectwright to adapt it must keep running its own copy, and an installed `projectwright` would take its place.

A project that copies projectwright can copy the board too, into `.claude/skills/projectwright-board/`, add it to the lock (`python3 "<projectwright>/scripts/framework.py" lock --add .claude/skills/projectwright-board`) and run `/reload-plugins`: Claude Code loads it from there. The copy is tracked like the copied `projectwright`: a change the project makes to it is a deviation, kept and merged by `/projectwright:upgrade` with the board of the new version, and can be proposed back with `/projectwright:propose-improvement`. Colors, columns and the fields of the cards are in `board-model.json` of projectwright, for both boards.

Requirements: a version of Claude Code with hooks modules (mods); Python ≥ 3.11, as for `projectwright` (`python3`, or `python` where only that name exists).

## Use

The pane opens by itself beside the chat when the terminal is wide enough; otherwise, and to open it again, type **`/board`**. The command also answers with the list of tasks as text, which reaches every surface.

- **Two views of the columns** — in progress, blocked, to do, done (and cancelled, when there is one) — as `board.html` has Board and Table. **Board**: the columns side by side; an empty one is only its heading, on a line above the others, so the columns with tasks share the whole width. **List**: the columns one under the other, each a group that opens and closes when its heading is pressed; done and cancelled start closed. The pane opens in Board when the columns with tasks fit side by side, in List otherwise; **`v`** swaps them. Above them, a summary and a bar coloured by progress.
- **The cards**: every task is a card with its title, ID, priority, assignee and what blocks it, in both views; done and cancelled show the newest few, and **+ N more** the rest.
- **New task** (`n` when the pane has the keyboard): title, priority and notes; Claude creates the task.
- **The detail**: press a task's title to see its properties, its body and the tasks it links, in place of the list; **← Back** (`b`) returns.
- **Edit** (`e`, in the detail): the fields of the task, and in words what to change in its body; Claude applies only what changed.
- **⇢** on every task, open or closed: Claude reads the task and its context, tells where it stands and asks what you want to do with it.
- **Proposed by Claude**: above the columns, the changes to the tasks Claude proposes — a task to create, move, close, split, edit or cancel — each with what it changes and why. **✓ Accept** asks Claude to apply it; **✕ Reject** marks it rejected, without a turn of Claude, and Claude does not propose it again; **💬 Comment** sends your comment to Claude, which proposes again (one proposal, several, or none). Without proposals the section is not drawn. The cards never show the ids of the proposals: they are for the tools, and close the message the pane sends to Claude as a reference.
- **Reminders**: below the proposals, a checklist of things to keep in mind that are not tasks, with an optional date (red once it has passed). **+ Reminder** (`r`) adds one; **☐** ticks it and **✕** removes it, without a turn of Claude; **→** asks Claude to propose a task from it. A ticked reminder stays, struck through, until the end of the day. A reminder Claude proposes arrives among the proposals: accepted, the pane adds it by itself. `board.html` shows the same checklist.

**Every change goes through Claude**, and Claude never changes the board on its own: it proposes tasks and changes, and writes after your yes. The board never writes the wiki: what you do in it becomes a request to Claude, sent as yours and visible in the conversation, which Claude applies with `/projectwright:manage-tasks`, its rules and the lint. Viewing (the list, the detail) changes nothing and asks nothing.

The board refreshes at the start of the session, after every write of Claude in `wiki/` or `project.yaml`, at the end of every turn of Claude, and with `/board`. While the pane is shown it also looks at the wiki every 30 seconds, so a change made by hand, in an editor, shows within half a minute.

A request sent from the board shows in the pane until its task is in the wiki. When a turn of Claude ends without it — Claude may be asking you something, or may have stopped — the line says so; **✕** dismisses it.

## Limits

- Hooks modules are an **early-access** API of Claude Code and may change between releases: if the board stops working, the `projectwright` plugin is not affected.
- The pane is drawn in the terminal and in the apps that host panes; a session followed through **Remote Control** does not show it: use `/board` or `board.html`.
- The mobile app has no text fields or selects: there the board shows tasks but cannot create or edit them.
- Every change from the board costs one turn of Claude.

## How it relies on projectwright

The two plugins are released together, with the same version. The board relies on:

- `wiki-query.py tasks --format json` and `wiki-query.py task <name> --format json`;
- `proposals.py list --format json` and `proposals.py set`, for the proposals of Claude;
- `reminders.py list --format json`, `add`, `done`, `undo` and `remove`, for the reminders;
- `assets/board-model.json`, which says what a board shows — columns, colors, priorities, the fields of a card and of the detail — for this pane and for `board.html` alike, so the two show the same thing;
- the skill `/projectwright:manage-tasks`, named in the requests it sends to Claude;
- `.claude/.projectwright-plugin`, written by the start-of-session hook of `projectwright`, which says where that plugin runs.

At every refresh the board checks that projectwright is there and has the same version, and says what to do when it is not.

## Tests

From the root of the repository:

```
python3 plugins/projectwright-board/tests/contract/make_contract.py --check
claude plugin test plugins/projectwright-board
```

The first command checks that `tests/contract/contract.ts` holds the current output of the `projectwright` scripts (tasks, proposals and reminders) and the current board model: it builds a sample project with the real `scaffold.py`, checks it with `wiki-lint.py` and runs the real queries. When it fails, a change to the scripts changed their output: run it again without `--check` to write the file, then run the tests, which say whether the board still reads it. Run both before every release, and after every change to `wiki-query.py` or to `assets/board-model.json`.

## Contents

| Path | Content |
|---|---|
| `hooks/hooks.json` | Names the hooks module |
| `hooks/register.tsx` | The board: the command, the refresh after writes in the wiki, the pane |
| `types/index.d.ts` | The values the pane keeps in the session's state |
| `tests/pane.test.tsx` | What the board does, on simulated answers of the engine |
| `tests/contract.test.tsx` | The board on the real output of the scripts |
| `tests/contract/` | `make_contract.py`, which writes that output into `contract.ts` |
