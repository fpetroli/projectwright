# projectwright-board — the board beside the chat

An optional plugin of the projectwright framework: the tasks of the project wiki in a pane beside the Claude Code chat, kept up to date as the wiki changes. It adds to `board.html` and to the hooks of the `projectwright` plugin; it replaces neither.

> **In development** — this is the `0.2.0-dev` version, not a release yet: what it shows and how it looks can still change.

It is a Claude Code **mod**: a TypeScript hooks module that runs inside Claude Code. The logic stays in the `projectwright` scripts: the board only draws what `wiki-query.py` answers.

## Install

The board needs the **`projectwright` plugin of the same version**, from the same marketplace. In a project that already uses projectwright:

```
claude plugin install projectwright-board@projectwright --scope project
```

or, at the prompt of a session, `/plugin install projectwright-board@projectwright`. Then start a new session in the project folder.

Installing the board does not install `projectwright`: install it first, or keep the copy the project has in `.claude/skills/projectwright/`. This is on purpose: a project that copies projectwright to adapt it must keep running its own copy, and an installed `projectwright` would take its place.

A project that copies projectwright can copy the board too, into `.claude/skills/projectwright-board/`: Claude Code loads it from there, and `/projectwright:upgrade` replaces it with the board of the new version. The copy is not meant to be changed: to adapt the board, change it in this repository.

Requirements: a version of Claude Code with hooks modules (mods); Python ≥ 3.11, as for `projectwright` (`python3`, or `python` where only that name exists).

## Use

The pane opens by itself beside the chat when the terminal is wide enough; otherwise, and to open it again, type **`/board`**. The command also answers with the list of tasks as text, which reaches every surface.

- **The columns**: in progress, blocked, to do, done (and cancelled, when there is one), shown one at a time: the columns are tabs with their count, and a digit (`1`, `2`, …) chooses one when the pane has the keyboard. Above them, a summary and a bar coloured by progress.
- **The cards**: each task of the column is a card with its title, ID, priority, assignee and what blocks it; done and cancelled show the newest few, and **+ N more** the rest.
- **New task** (`n` when the pane has the keyboard): title, priority and notes; Claude creates the task.
- **The detail**: press a task's title to see its properties, its body and the tasks it links, in place of the list; **← Back** (`b`) returns.
- **Edit** (`e`, in the detail): the fields of the task, and in words what to change in its body; Claude applies only what changed.
- **⇢** on every task, open or closed: Claude reads the task and its context, tells where it stands and asks what you want to do with it.

**Every change goes through Claude.** The board never writes the wiki: what you do in it becomes a request to Claude, sent as yours and visible in the conversation, which Claude applies with `/projectwright:manage-tasks`, its rules and the lint. Viewing (the list, the detail) changes nothing and asks nothing.

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

The first command checks that `tests/contract/contract.ts` holds the current output of the `projectwright` scripts and the current board model: it builds a sample project with the real `scaffold.py`, checks it with `wiki-lint.py` and runs the real queries. When it fails, a change to the scripts changed their output: run it again without `--check` to write the file, then run the tests, which say whether the board still reads it. Run both before every release, and after every change to `wiki-query.py` or to `assets/board-model.json`.

## Contents

| Path | Content |
|---|---|
| `hooks/hooks.json` | Names the hooks module |
| `hooks/register.tsx` | The board: the command, the refresh after writes in the wiki, the pane |
| `types/index.d.ts` | The values the pane keeps in the session's state |
| `tests/pane.test.tsx` | What the board does, on simulated answers of the engine |
| `tests/contract.test.tsx` | The board on the real output of the scripts |
| `tests/contract/` | `make_contract.py`, which writes that output into `contract.ts` |
