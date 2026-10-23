# projectwright

A framework for AI-driven project work with [Claude Code](https://claude.com/claude-code).

When you work with an AI assistant on a real project, every session starts from zero: the assistant does not remember what was decided last week, why the code is the way it is, or which points are still open. Decisions end up scattered across chats, documents and people's heads, and the assistant ends up contradicting choices already made or deciding on its own things that were someone else's call.

**projectwright gives the project a written, ordered and checked memory**: a **wiki** of Markdown files that Claude reads at the start of every session and updates at the end of it, following precise rules. It holds:

- the **decisions**, one file each, with their reasons (ADRs);
- the **open questions**, each with a traffic light: 🔴 no code on this until it is decided, 🟠 proceed with a declared assumption, 🟡 decide when it comes up;
- the **knowledge** of the project, in short linked notes;
- the **tasks**, when you do not use an external tracker;
- a **dashboard** that tells where the project stands.

The method is a Claude Code **plugin**, distributed by this repository as a plugin marketplace: you install it for your project, set the project up with it, and upgrade it when you decide. If you need to change the method itself, you can copy the plugin into your project and adapt it there, with every change tracked.

> **Early version (0.x).** The core works — setup, ingestion of documents, recording of decisions, automatic checks, dashboard, task board. Still to come: integration with external trackers. It has been tested on Linux and macOS; not yet on Windows.

---

## Contents

- [Getting started](#getting-started)
- [How a project is structured](#how-a-project-is-structured)
- [How it works](#how-it-works)
- [The skills](#the-skills)
- [Automation and tools](#automation-and-tools)
- [Configuration](#configuration)
- [Adapting the method and proposing improvements](#adapting-the-method-and-proposing-improvements)
- [Upgrading](#upgrading)
- [This repository](#this-repository)

---

## Getting started

### Requirements

- Claude Code
- git (for your code repositories)
- Python 3.11 or later — nothing else to install: the few libraries needed are bundled in the plugin

### 1. Create the project folder

```bash
mkdir ~/projects/my-shop && cd ~/projects/my-shop
```

If you already have a code repository, do **not** use its folder: create the project folder **next to it**. The repository will be brought in at step 4. If you already have a whole project — notes, decisions, documents for the AI — run **`/projectwright:adopt-framework`** at step 3 instead of `setup-project`: it brings it all in, leaving the old folder untouched.

### 2. Install the plugin for the project

From the project folder:

```bash
claude plugin marketplace add fpetroli/projectwright --scope project
claude plugin install projectwright@projectwright --scope project
```

The first command registers this repository as a plugin marketplace, the second installs the `projectwright` plugin. With `--scope project` both are written in the project's `.claude/settings.json`: the plugin is enabled for this project only, and whoever opens the project folder later — for example a colleague — gets the same plugin.

### 3. Open Claude Code and set up the project

```bash
claude
```

1. Claude Code asks whether you trust the folder: answer yes. If the `/projectwright:…` skills are not there yet, run `/reload-plugins`.
2. Run **`/projectwright:setup-project`**: a short interview — project name, language of the wiki, where the official documentation is, whether you use an external tracker — then it creates the configuration, the wiki, the dashboard, the project's `CLAUDE.md` and the first decision.

### 4. Add your code repositories

For each repository run **`/projectwright:add-repository`**. It clones the repository into `repositories/`, or — if it is already on your computer in another folder — moves it there after asking you (history, branches and uncommitted changes are kept). It creates the component's folder in the wiki, and points out documentation worth ingesting and files for AI assistants that a delivered repository should not contain.

### 5. Feed the wiki with what you already know

If you have documents (minutes, specifications, analyses), put them in the project's **`docs/`** folder, organised as you like — or keep them in a shared folder and set it in `project.yaml` (`paths.official_docs`), or give Claude the links, if they live online (Confluence, another wiki) — and run:

1. **`/projectwright:ingest-sources`** — reads the documents and writes one ingestion card per document;
2. **`/projectwright:integrate-wiki`** — turns the cards into decisions, questions and notes. The first time it shows you the skeleton of the wiki and waits for your approval.

### 6. Version the project folder (optional)

The project folder is **not** versioned by default: your code repositories keep their own git. If you want to share the wiki with your team, or simply keep its history, ask Claude to version it — it runs `scaffold.py project --git`, which initialises git, adds a `.gitignore` that keeps the code repositories out, and a git hook that checks the wiki before every commit. Without versioning, back the folder up.

### A colleague joining a versioned project

1. Clone the project folder, open Claude Code in it and trust it: Claude Code reads `.claude/settings.json`, registers the marketplace and loads the plugin (the first time, run `/reload-plugins` when it says so).
2. Clone the code repositories into `repositories/` (their addresses are in `project.yaml`).
3. Activate the git hook: `git config core.hooksPath .githooks`.

### Without the marketplace

You can also put the plugin straight into the project, without installing anything: clone this repository and copy `plugins/projectwright/` into the project as `.claude/skills/projectwright/` (on Windows, `Copy-Item -Recurse`). Claude Code loads it from there after you trust the folder and run `/reload-plugins` once. This is the "copied" way described in [Adapting the method](#adapting-the-method-and-proposing-improvements).

---

## How a project is structured

```
my-shop/                              ← THE PROJECT FOLDER: the "brain" of the project
│
├── CLAUDE.md                         ← instructions for Claude (from the framework + a final section of yours)
├── project.yaml                      ← YOUR CHOICES: name, language, components, rules, conventions
├── board.html                        ← generated view of the tasks, to open in a browser
│
├── .claude/
│   ├── settings.json                 ← enables the projectwright plugin for this project
│   ├── projectwright.lock.json       ← framework version and fingerprint of its files, to detect your changes
│   ├── .projectwright-original/      ← original copy of the framework files (local)
│   └── skills/projectwright/         ← THE PLUGIN, only if you copied it into the project
│
├── wiki/                             ← THE MEMORY OF THE PROJECT
│   ├── README.md                     ← the constitution: the rules for writing in the wiki
│   ├── dashboard/                    ← where we are, the pre-code gate, reading paths, glossary
│   ├── project/                      ← context, goals, plan, team and roles, development workflow
│   ├── decisions/                    ← decisions about the project as a whole (ADR-PRJ-…, ADR-MET-…)
│   ├── questions/                    ← open questions about the project as a whole
│   ├── tasks/                        ← tasks, when the wiki is the tracker
│   ├── roadmap.md                    ← phases and goals
│   └── components/
│       └── web-shop/                 ← ONE FOLDER PER CODE REPOSITORY
│           ├── web-shop.md               entry note: what it is, boundaries, "before touching X read Y"
│           ├── web-shop-roadmap.md
│           ├── decisions/                decisions internal to the component (ADR-WS-…)
│           ├── questions/                questions internal to the component
│           └── tasks/
│
├── docs/                             ← THE OFFICIAL DOCUMENTS: specifications, analyses, minutes —
│                                         organised as you like (or a shared folder outside the project)
│
├── wiki-sources/                     ← WHAT HAS BEEN READ from the official documentation
│   ├── README.md
│   ├── ingestion-log.csv             ← which document (or link), which version, integrated or not
│   ├── minutes/                      ← one card per minutes document (cards are grouped by kind of document)
│   ├── technical-docs/
│   └── functional-docs/
│
├── utils/                            ← files you ask Claude to create: exports, tables, drafts, scripts
│
└── repositories/                     ← THE PRODUCT: your code repositories, each with its own git
    └── web-shop/                         never contains notes for the AI, nor references to the wiki
```

A few principles shape this layout:

- **The brain and the product are separate.** Everything the AI needs lives in the project folder; the code repositories in `repositories/` contain only code, never notes for the AI, and never refer to the wiki. What you deliver to a client is clean.
- **Folders are born with their first file.** A new project only has what holds something, plus `utils/`; `questions/`, `tasks/` and the others appear when the first record is written there.
- **One folder per repository, ready for many.** With a single repository, the project level keeps what is about the project itself (scope, plan, method, organisation) and the component keeps everything about the product. When a second repository arrives, what touches both moves up to the project level — the structure is already there.
- **Always start Claude Code from the project folder**, never from inside a code repository: from there the plugin is not loaded, and the project's `CLAUDE.md` tells Claude to stop and ask you to restart.

---

## How it works

### The wiki is the memory

- **One fact, one place.** Every piece of knowledge has one home; the other notes link it with `[[wikilinks]]`, by file name. File names are unique and never renamed, so links never break.
- **Epistemic statuses.** Every note says how far it can be trusted: `decided`, `assumed`, `hypothesis`, `conflicting`, `undecided`, `informational`, `superseded`. A wiki where everything is "decided" no longer tells the verified from the supposed.
- **Hierarchy of truth.** Human documentation → wiki → code → chat. No source wins automatically: when two sources disagree, you decide. What is said in chat becomes true only when it is recorded in the wiki.
- **One file per record**, with a YAML frontmatter that works as a small database: decisions `ADR-<CODE>-NNNN`, questions `Q-<CODE>-NNNN`, tasks `TASK-NNNN` (one number for the whole project). The code of decisions and questions is an area of the project (`PRJ`, `MET`, `ARCH`…) or a component (`WS`…); a task tells its component by its folder. IDs are never reused.
- **Nothing generated is kept.** There are no hand-kept indexes that go out of date: lists are computed from the files when needed.
- **The wiki is plain Markdown**, in the language of your project; field names stay in English. Obsidian works on it but is not required.

### The pre-code gate

Before writing code on a component, Claude reads the open questions that concern it. On a 🔴 it stops and tells you why; on a 🟠 it proceeds with the declared assumption and the prescribed precaution (typically: isolate the unstable choice behind an interface); on a 🟡 it decides in the task and tells you.

### The knowledge cycle

```
 official documents ──ingest-sources──▶ ingestion cards ──integrate-wiki──▶ WIKI
 (files or links)                       (wiki-sources/)                     │  ▲
        ▲                                                                   │  │
        └──────────────────────── propose-docs ◀────────────────────────────┘  │
                                                                               │
   call transcript ──draft-minutes──▶ minutes (an official document)           │
                                                                               │
   working session (code, decisions, tasks) ──────────── record-decisions ─────┘
```

1. Official documents — files in a folder, or links to Confluence pages and the like — are **ingested**: one immutable card per document, with the claims it states and its version.
2. Cards are **integrated** into the wiki: notes, decisions, questions, glossary. Contradictions are brought to you, never resolved silently.
3. You **work**: Claude gets the dashboard at the start, runs the pre-code gate, and at the end **records** what the session decided or discovered.
4. When the wiki holds settled knowledge that the documents lack, Claude can **propose** updated documents; the minutes of your calls become new documents.

### Rules that always hold

- **Commits, pushes and merge requests are always yours**: Claude prepares the commands and the text of the merge request following your team's development workflow (a note of the wiki: branches, commits, merge requests, review), never runs them.
- **Every session that decides something closes by recording it** (`/projectwright:record-decisions`), automatically.
- **No silent choices**: conflicts between sources, between standards and decisions, between code and wiki are always put in front of you.

---

## The skills

All skills are invoked as `/projectwright:<name>`. You can also just ask in plain words: Claude picks the right one.

| Skill | What it does |
|---|---|
| **Setup** | |
| `setup-project` | Interview and creation of the whole project: configuration, wiki, dashboard, `CLAUDE.md`, first decision |
| `add-repository` | Adds a code repository: clones it or moves it into `repositories/`, creates its component folder |
| `change-setting` | Changes a choice of the project (language, modules, task mode, tracker…) and brings the existing content in line with it |
| `adopt-framework` | Brings an existing project into the framework: its notes, decisions, open points, documents and repositories, in a new folder next to the old one, which stays untouched |
| **Knowledge cycle** | |
| `ingest-sources` | Reads the official documentation (files or online pages) and writes the ingestion cards |
| `integrate-wiki` | Turns the cards into notes, decisions, questions; on the first run it has the skeleton approved |
| `record-decisions` | Closes every session: decisions → ADRs, knowledge → notes, questions, tasks, changes to the framework, git commands |
| **Documents** | |
| `draft-minutes` | Writes the minutes of a call from its transcript — by default no names of people, no amounts, no opinions, and for each minutes document it asks which of them you want to keep; learns roles and terms only with your consent |
| `propose-docs` | Proposes new or updated official documents from what the wiki holds as decided |
| **Tasks** | |
| `manage-tasks` | Creates, moves, assigns, plans and closes tasks when the wiki is the tracker |
| **Checks** | |
| `wiki-check` | Full check of the wiki: mechanical and semantic (contradictions, misplaced names, ageing assumptions) |
| `audit-code` | Checks that the code respects decisions and standards; on conflicts asks you who is right |
| **The framework itself** | |
| `propose-improvement` | Turns your changes to the method into an anonymous proposal for the framework |
| `upgrade` | Brings the project to a new version of the framework, keeping your changes; you decide every conflict |
| `framework-feedback` | Notes, anonymously, a friction with the framework while you work, to bring to the framework later |

---

## Automation and tools

**Hooks** — installed by the plugin, nothing to configure:

- **after every write in the wiki**, the lint checks the file; violations go straight back to Claude, which fixes them;
- **at the start of every session**, Claude receives your working profile (see below) and the dashboard: blocking questions, recent decisions, components, tasks in progress, cards to integrate, lint problems — and a check of the plugin itself: a warning if its version is not the one the project was set up with, or if an installed copy overrides the one in the project;
- **`board.html` is regenerated** at the start of the session and after every change to the wiki;
- **before every commit** (only if the project folder is versioned), a git hook runs the full lint and blocks the commit on errors.

**The board** — `board.html`, in the project folder, is a read-only view of the tasks of the wiki to open in your browser, laid out like a database: a **Board** view (the pipeline in columns: in progress, blocked, to do, done) and a **Table** view (one row per task, grouped by progress), a search, and the detail of a task beside the list. It works offline, changes nothing and is never versioned. With `/projectwright:manage-tasks` it replaces an external tracker. **The tasks are decided together**: you and Claude both propose them, and Claude never creates, moves, closes or re-prioritises a task on its own — it proposes, and writes after your yes. The proposals wait outside the wiki, and the board beside the chat shows them, to accept, reject or comment. Next to the tasks, both boards keep your **reminders** — "send the e-mail", "update X" — a checklist with an optional date, outside the wiki too: you add them, or Claude proposes them. It shows what the pane beside the chat shows (below), from the same definition.

**The board beside the chat** — `projectwright-board` is an optional second plugin of this marketplace: the tasks of the wiki in a pane beside the Claude Code chat, in a Board or a List view, kept up to date as the wiki changes, with the detail of a task and forms to create and edit one. It shows the same columns, cards and detail as `board.html`. Every change made from the pane goes through Claude, which applies it with `/projectwright:manage-tasks` and the lint: the pane never writes the wiki. It needs `projectwright` of the same version and does not install it; install it with `claude plugin install projectwright-board@projectwright --scope project`, then type `/board`. It is built on an early-access API of Claude Code, and a session followed through Remote Control does not show the pane: use `/board` or `board.html` there. Details in [`plugins/projectwright-board/README.md`](plugins/projectwright-board/README.md).

**When the skills do not appear** — in a folder trusted for the first time, Claude Code may run the hooks of a plugin copied into the project but not list its skills yet (`/projectwright:…` is then an unknown command): run `/reload-plugins`, or start a new session.

**Scripts** — in the `scripts/` folder of the plugin (its path is in `.claude/.projectwright-plugin` after the first session), plain Python with no dependencies to install. Claude and the hooks use them; you can too:

| Script | What it does |
|---|---|
| `wiki-lint.py` | Mechanical checks: links, unique names, valid frontmatter, allowed values, IDs, components, configuration |
| `wiki-query.py` | Queries the wiki: `dashboard`, `questions`, `decisions`, `tasks`, `task` (one task in full), `sources`, `deviations` |
| `board.py` | Writes `board.html` (`--open` opens it) |
| `ingestion-diff.py` | Compares the documentation with the ingestion log: what is new, changed, removed |
| `scaffold.py` | Creates the structure of a project and of a component; `--git` versions the project folder |
| `framework.py` | The framework files: fingerprint, your changes, their exact diff; `vendor` copies the installed plugin into the project; `check` verifies the plugin setup; `upgrade`; `permissions` lets Claude run the plugin's scripts without asking; `renumber-tasks` moves the tasks of an older project to `TASK-NNNN` |
| `profile.py` | Your working profile: `show`, `add`, `remove` |
| `proposals.py` | The changes to the tasks Claude proposes and you decide: `add`, `list`, `set` (outside the wiki, never versioned) |
| `reminders.py` | Your reminders, things to keep in mind that are not tasks: `add` (with an optional date), `list`, `done`, `undo`, `remove` (outside the wiki, never versioned) |

**Your working profile** — Claude learns how *you* like to work: whether you want analyses point by point or prefer to let it proceed, one question at a time or all together, how much detail, which tone. It does not ask: it notices stable preferences — a correction, a choice you make again and again — and records them, one sentence each, in a personal profile that lives **outside your projects** (`~/.claude/projectwright/profile.md`). Every projectwright project reads it at the start of the session, so the experience fits you more and more. It never holds project facts or confidential data, it is never shared with the team, and you can edit or delete it at any time; at the end of a session Claude tells you in one line what it recorded.

---

## Configuration

- **`project.yaml`** — everything that varies from project to project: name and language, paths (official documentation, code repositories, `utils/`), wiki modules and area codes, components, documentation categories and exclusions, task mode (`wiki` or an external tracker), drafting rules for minutes and documents, git conventions. `CLAUDE.md` imports it, so Claude always sees the current values.
- **`schema.yaml`** (in the plugin) — the values of the method, the same for every project: record types, statuses, traffic lights, task progress, required fields, ID formats, the rules of `project.yaml`.
- **The constitution** (`wiki/README.md`) — the only place where the writing rules of the wiki live; the skills refer to it instead of repeating them.

---

## Adapting the method and proposing improvements

Every project can adapt the method to itself: a rule of the constitution, the framework part of `CLAUDE.md`, and — with the plugin copied into the project — a skill, a template or a script.

**Installed or copied.** The plugin installed from the marketplace lives in Claude Code's plugin cache and is shared by the projects that use that version: its files are not meant to be changed. To change them, copy the plugin into the project:

```bash
python3 "<plugin folder>/scripts/framework.py" vendor
```

It copies the running plugin into `.claude/skills/projectwright/`, removes the installed one from the project's `.claude/settings.json` (an installed plugin enabled for the project would take precedence over the copy) and takes a new fingerprint. From then on the project uses its own copy — run `/reload-plugins` so that the session loads it; Claude can do it for you when you ask to change a skill.

The framework keeps track of every change:

1. Every change to a file provided by the framework is **detected** (against the fingerprint taken when the framework was applied) — the final "project-specific" section of `CLAUDE.md` is yours and does not count.
2. `/projectwright:record-decisions` records the change and its reason as a **deviation** (an ADR marked `framework_deviation: true`); `wiki-query.py deviations` lists them, and the dashboard warns about changes without a reason.
3. When a change could help other projects, **`/projectwright:propose-improvement`** writes a proposal — the need, the change, the reasons and the exact diff — with every detail of your project removed. Bring it to the framework, where it is discussed and, if accepted, released in a new version.

---

## Upgrading

Each project records the version of the framework it was set up with (`framework.version` in `project.yaml` and the lock file), and nothing changes until you decide: the plugin pins its version, and a marketplace you add does not update by itself unless you turn auto-update on. When you want a new version, run **`/projectwright:upgrade`**:

1. **It gets the new version.** Installed plugin: it updates it (`claude plugin update`) and asks you to restart Claude Code, so that the new version is the one running. Copied plugin: from a folder you name, or from a tag of this repository.
2. **It shows what changes**: the CHANGELOG entries in between, and a plan file by file — replaced, merged, kept, in conflict.
3. **It keeps your changes.** Framework files you did not change take the new version; those you changed are merged with it, three-way; where both changed the same lines, it shows you the two versions with a proposal, and you decide.
4. **It applies the upgrade notes** of each version — new settings to choose, changes to the notes translated into your language — then records the upgrade in an `ADR-MET`.

The optional board follows: installed, the upgrade updates it together with `projectwright`; copied into the project (`.claude/skills/projectwright-board/`), it is tracked like the copied plugin: what the project changes in it is a deviation, kept and merged by the upgrade, and can be proposed back with `/projectwright:propose-improvement`.

A colleague who installs the plugin later gets the latest version: the start-of-session check tells them when it is ahead of the project, so that the team can decide whether to upgrade.

---

## This repository

| Path | Content |
|---|---|
| `.claude-plugin/marketplace.json` | Makes this repository a Claude Code plugin marketplace, listing the `projectwright` and `projectwright-board` plugins |
| `plugins/projectwright/` | The plugin: skills, hooks, scripts, schema, templates |
| `plugins/projectwright-board/` | The optional board beside the chat (see below) |
| `plugins/projectwright/CHANGELOG.md` | Changes by version, with the upgrade notes for an existing project |

To try a change to the plugin before publishing it, add your local clone as a marketplace (`claude plugin marketplace add ./projectwright --scope project` from a test project): a plugin from a local marketplace is loaded straight from its folder, so your edits apply at the next `/reload-plugins`. `claude plugin validate .` checks the marketplace and the plugin manifests.

## License

[MIT](LICENSE). PyYAML, bundled in the plugin, is MIT too (see `plugins/projectwright/THIRD-PARTY-NOTICES`).
