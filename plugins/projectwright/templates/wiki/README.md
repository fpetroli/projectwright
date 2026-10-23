# Constitution of the wiki

This folder is the **operating memory of the AI** on the project: a wiki of Markdown files linked to each other. It holds the whole epistemic picture of the project: what is decided, what is assumed, what is in conflict, and *why* things were chosen.

This file is the **only place where the writing rules of the wiki live**. Skills and people refer to it; they do not repeat its rules. The exact lists of allowed values are in the method schema (`schema.yaml` of the `projectwright` plugin); everything that varies from project to project (paths, areas, components, languages, conventions) is in `project.yaml`. Neither is copied here.

> This file is provided by the `projectwright` framework. It can be changed for this project, but every change is a deviation from the framework and is recorded with an `ADR-MET` marked `framework_deviation: true`.

---

## The structure

```
wiki/
├── README.md                 ← this file: the constitution
├── dashboard/                ── DASHBOARD: derived views only, no facts of its own
│   ├── project-status.md            where we are, what blocks what, one line per component
│   ├── operating-assumptions.md     the pre-code gate (🔴 stop / 🟠 assume / 🟡 decide)
│   ├── knowledge-map.md             reading paths + views of notes, decisions, questions
│   └── glossary.md                  domain terms and recurring ambiguities
├── project/                  ── stable context: goals, actors, scope, plan, method, team and roles
│   ├── team-and-roles.md            organisations, anonymous roles, people, transcription fixes
│   └── development-workflow.md      branches, commits, merge requests, review (when known)
├── decisions/                ── cross-cutting ADRs, one file each
├── questions/                ── cross-cutting questions, one file each
├── roadmap.md                ── phases, goals and dependencies of the project
├── tasks/                    ── ONLY when tasks.mode = wiki: one file per task
├── components/               ── mirrors repositories/: one folder per component
│   └── <repo>/
│       ├── <repo>.md                entry note of the component (type: component)
│       ├── <repo>-<feature>.md      one note per feature, prefixed with the component name
│       ├── <repo>-roadmap.md        phases and goals of the component
│       ├── decisions/               ADRs internal to the component
│       ├── questions/               questions internal to the component
│       └── tasks/                   ONLY when tasks.mode = wiki
├── domain/                   ── OPTIONAL module: functional model of the platform
└── architecture/             ── OPTIONAL module: cross-cutting technical views, standards, contracts
```

`board.html`, in the project root, is a generated, read-only view of the tasks for people (a board in columns and a table): it reads these files, so it is never out of date and never versioned.

Files created on request (exports, drafts, support scripts…) live in `utils/` (`paths.utils`), outside the wiki: they are not knowledge, and a fact written only there is invisible to the dashboard and to the pre-code gate.

The ingestion cards live **outside** the wiki, in the sibling folder `wiki-sources/` (its own `README.md` has the rules), because their rules are the opposite of the wiki's: they are immutable and only ingestion writes them.

**Folders are born with their first file**: a new project has only the folders that hold something, and `questions/`, `tasks/`, the optional modules, the folders inside a component and those of `wiki-sources/` appear when the first record is written there. Never create empty folders or `.gitkeep` files in the wiki. The optional modules active in this project are listed in `wiki.optional_modules` of `project.yaml`. There are no numeric prefixes on folders: the reading order is given by `dashboard/knowledge-map.md`.

---

## The principles

1. **The wiki is derived memory.** The official documents (minutes, technical and functional documents) hold the cardinal points; the wiki holds the whole epistemic picture for the AI. **Thinning rule**: the more a topic settles, the thinner its note gets (at the limit, a bridge to the ingestion card); the hotter it is, the richer the note.
2. **No copies of the official documents.** The wiki does not replicate them: it **ingests** them. `wiki-sources/` holds **ingestion cards**, not copies: extracted claims of one line each, with provenance and hash.
3. **No source wins automatically.** When two sources contradict each other (document vs document, card vs note, code vs wiki, session vs wiki), the divergence goes to the user, who arbitrates. Skills never modify the official documents: if one is behind, the user is asked to update it.
4. **Names, not paths.** Links are always wikilinks `[[file-name]]`, also in the frontmatter, never Markdown links with a path. Therefore **file names are globally unique** across `wiki/` and `wiki-sources/`, and **a file is never renamed**. Aliases `[[file-name|text]]` are allowed (escape the pipe in tables: `[[file-name\|text]]`). Outside Obsidian the links stay readable as text.
5. **One fact, one place.** Every piece of knowledge has one home; the other places **link** it. Split by fact, not by source document: a long document becomes twenty notes, not five long notes that mirror its chapters. When two sources say the same thing, the note is one and both sources go in `source`.
6. **New = new file.** One file per decision, question, task, card, feature. Questions and tasks are files, never rows of an index. Nothing in the wiki is a generated index or catalogue: lists are computed when needed (`wiki-query.py`, Bases views).
7. **The dashboard owns no facts.** Everything in `dashboard/` is derived; a fact that lives only there is in the wrong place.
8. **Placement rule.** What lives **entirely inside the boundaries of one repository** goes in its component folder; what **touches two or more components** goes to the project level (`decisions/`, `questions/`, `architecture/`, `domain/`). Test: a flow that crosses three services → project level; how one service implements its own dashboard → component. The project level also holds what is about **the project itself** rather than the product: scope, plan, method, organisation, agreements with the client or other teams (areas `PRJ`, `MET`, `INT`).
   - **With a single repository** the line is *project or product*: everything about the product — architecture, domain, standards included — goes in the component; the project level keeps only what is about the project itself. The technical areas of the project (`ARCH`, `DOM`, `STD`) and the modules `architecture/` and `domain/` are needed only when there are two or more components.
   - **When a second repository arrives**, the structure is already there: the records of the first component stay where they are (IDs never change); from then on, what touches both components goes to the project level, and the modules `architecture/` and `domain/` can be activated. A thematic note of the first component that turns out to be cross-cutting can be moved to the project level: links are by name, so nothing breaks.
9. **Fractal wiki.** Every component is an autonomous unit that repeats, in small, the structure of the project level. It respects the cross-cutting ADRs and uses the common glossary and domain.
10. **IDs are never reused.** A retired number stays a hole. The same holds for file names.
11. **Delivery repositories never point to the wiki.** The wiki cites code and its normative documents (as text: constraint IDs, file paths); the code cites nothing from here — no ADR, question or task IDs, no names of people or companies. Whoever receives the delivery does not have this folder. Test for where content goes: *if a rule loses its why, is it still applicable?* If yes, the rule lives in the repository and the why lives here; if not, the why is part of the rule and is written in the repository.
12. **Skills work autonomously**: they proceed without asking step by step and involve the user only for conflicts between sources, decisions they cannot take alone (arbitrations, permanent names when the wiki is born, IDs that cannot be made safe) and official documents to correct.

---

## Epistemic statuses

The `status` field says how much a note can be relied on. Use it for real: a wiki where everything is `decided` no longer tells what is verified from what is supposed.

| Status | Meaning | When to assign it |
|---|---|---|
| `decided` | The fact is verified, or the decision is taken and holds until revoked | A measure, an observed behaviour, an official document or a recorded decision (ADR) exists |
| `assumed` | An answer was chosen to proceed, without confirmation from the competent source | Someone can confirm it and has not yet done so: an open question tracks it |
| `hypothesis` | A plausible reconstruction that nobody has chosen as the answer | It comes from a clue (a name, an analogy, a piece of code), not from a source |
| `conflicting` | Two sources that matter say incompatible things and the contradiction is unresolved | The body describes the contradiction with both positions, who decides and what is needed to close it |
| `undecided` | An open point recognised as such, with not even an assumption | Questions without an assumption; notes that expose an alternative without choosing |
| `informational` | Content that asserts nothing to verify | Dashboard notes, ingestion cards, purely descriptive notes |
| `superseded` | Decisions only: the ADR was replaced by a later decision and stays as history | `superseded_by` points to the ADR that replaces it; the new ADR explains why |

Rules of use: an assumption that falls is not deleted — the note is updated with the true answer and its status becomes `decided` (the history of what was assumed explains why the code is the way it is); `conflicting` is a working state, not an archive; `updated` changes at every substantial change of the body, and an old note still `assumed` is a debt that the date makes visible.

---

## Language of the content

The wiki is written in the language of the project (`project.language`); the framework — this constitution, the skills, the templates, the board — is in English.

- **Names stay in English**: folders, file-name prefixes (`ADR-`, `Q-`, `T-`), frontmatter fields and their allowed values (`status: decided`, `gate: red`). Scripts read them.
- **Everything else is in the project language**: titles, text, and the **headings** of the records, translated from the English templates of the plugin.
- **Same headings everywhere**: before writing a record (decision, question, task, card, component entry note), look at an existing record of the same type and **reuse its headings exactly**; translate the template only for the first record of a type. This keeps every record of a type readable in the same way.
- Notes created from the templates of the plugin (dashboard, `team-and-roles.md`, `development-workflow.md`, roadmaps) are translated into the project language when they are created.

## Frontmatter

Every note (except `README.md` files) opens with a **valid YAML** frontmatter. Wikilinks in the frontmatter go **between quotes**; several values are a **YAML list**; all fields are *snake_case*; dates of an event end in `_on`.

```yaml
---
title: <readable title>
type: <see schema.yaml>                 # note, decision, question, task, source-card, dashboard, component
status: <see schema.yaml>               # the epistemic status (not for tasks)
area: <area code or component code>     # e.g. ARCH, PRJ, FE — always the code
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: <provenance: "[[card-name]]", a document, "working session YYYY-MM-DD">
related:
  - "[[note-1]]"
  - "[[note-2]]"
tracker: KEY-123                        # only when tasks.mode = tracker: linked key (one-way link)
---
```

`source` is always filled where content derives from something: a note without provenance is an opinion. When content comes from several cards, `source` is a list of all of them.

Additional fields by type (the required ones and the allowed values are in `schema.yaml`):

| `type` | Additional fields |
|---|---|
| `decision` | `id`; `superseded_by: "[[ADR-…]]"` when `superseded`; `framework_deviation: true` when the decision motivates a change to a file provided by the framework, with `upstream: proposed \| accepted \| rejected` once it has been proposed to the framework |
| `question` | `id`; `lifecycle: open \| closed`; `gate: red \| orange \| yellow`; `assumption` (the answer adopted to proceed, for 🟠); `precaution` (how to isolate the unstable choice); `decision_owner` (by role); `closed_on`; `closure_reason`; `decision` (the ADR that closes it, if any). While open, `status` is `undecided`, `assumed` or `conflicting`; when closed, `decided` |
| `task` | `id`; **`progress` instead of `status`**; `priority`; `phase`; `assignee` (by role); `closed_on`; `decisions`; `questions`; `blocked_by`; `commits` |
| `source-card` | `hash`; `ingested_on`; `source_kind: event \| reference` (minutes are events; reference documents describe the current truth and get updated) |
| `component` | `code`; `component_status: planned \| active \| retired`; `repository` (name in `repositories/`) |

---

## IDs

Uniform format: **`<TYPE>-<CODE>-NNNN`**, a four-digit number **per code**, never reused.

| Element | Format | Example |
|---|---|---|
| Decision | `ADR-<CODE>-NNNN` | `ADR-ARCH-0012`, `ADR-FE-0003` |
| Question | `Q-<CODE>-NNNN` | `Q-ARCH-0004`, `Q-FE-0001` |
| Task (tasks.mode = wiki) | `T-<CODE>-NNNN` | `T-FE-0012` |

- **`<CODE>`** is the code of a project area (`wiki.areas` in `project.yaml`) for cross-cutting elements, or the code of a component (`components[].code`) for elements internal to it. The `area` field holds the same code.
- File name = ID + slug: `Q-FE-0001-http-timeout-to-backend.md`. The `id` field matches the prefix of the file name.
- **Safe ID**: whoever assigns an ID takes the highest number for that code among the files of the wiki, plus one. When the project folder is versioned with git and shared, first run `git fetch` and consider also the files on `origin/<git.main_branch>`.
- **Collision between branches** (only when the project folder is versioned and shared): if two people assign the same ID in parallel, the lint reports the duplicate after the merge; the more recent element is renumbered. It is the only case in which an ID changes.

---

## Decisions (ADR)

One file per decision, in `decisions/` (cross-cutting) or `components/<repo>/decisions/` (internal). An ADR is an **immutable record**: the current knowledge lives in the thematic note, which links the ADR.

A **superseded** decision is never rewritten: the old ADR takes `status: superseded` and `superseded_by: "[[ADR-…]]"`; the new ADR explains why. This is the only rule on superseded decisions; skills refer to it.

Body of an ADR (template: `templates/records/decision.md` in the plugin; headings in the project language, see "Language of the content"):

```markdown
# ADR-<CODE>-NNNN — <title>

**Context** — the situation or problem that required the decision
**Decision** — what was decided, in a verifiable statement
**Rationale** — why this path
**Alternatives considered** — what was discarded and why
**Consequences** — impacts: notes updated, questions closed/opened, constraints
```

---

## Questions and the pre-code gate

One file per question, in `questions/` (cross-cutting) or `components/<repo>/questions/` (internal). **One question = one decision topic**, not a bullet: open points from different sources are merged by topic. Closed questions **stay in their folder** with `lifecycle: closed`, `closed_on` and `closure_reason`; the ID stays forever.

The `gate` drives the **pre-code gate**, which every development skill runs before writing code:

- 🔴 **`red`** — stop: code that touches the topic is not implemented until there is a decision; report to the user;
- 🟠 **`orange`** — proceed with the declared `assumption` and the prescribed `precaution` (typically: isolate the unstable choice behind an interface or a single configuration point);
- 🟡 **`yellow`** — a detail decided in the task when it comes up, declaring it.

The gate is computed from the question files (project level and component), never from hand-kept lists.

---

## Components

Every repository in `repositories/` has a twin folder `components/<repo>/`. Its **entry note** `<repo>.md` has `type: component` and the fields `code`, `component_status`, `repository`; it says what the component is, its boundaries, and "before touching X read Y".

**Direction of links**: notes of a component link the project level freely. The project level and other components reach the **thematic notes** of a component only through its entry note (`[[<repo>]]`), so the internal structure of a component can change without breaking the rest. **Exception**: ADRs, questions and tasks of a component can be linked from anywhere, because they are permanent records.

A retired repository keeps its component folder intact, with `component_status: retired`. If a repository changes name, the `repository` field changes, never the folder or the note name.

---

## Write-ownership

| Zone | Who writes |
|---|---|
| Cards in `wiki-sources/` | Only `/projectwright:ingest-sources` (immutable after writing) |
| `wiki-sources/ingestion-log.csv` | `/projectwright:ingest-sources` (rows) + `/projectwright:integrate-wiki` (only the `integrated` column) |
| `decisions/`, `questions/` (project and components) | `/projectwright:integrate-wiki`, `/projectwright:record-decisions`, people |
| `tasks/` (tasks.mode = wiki) | People, `/projectwright:manage-tasks`, `/projectwright:record-decisions`, development skills (only `progress` and `commits`) |
| Thematic notes, roadmaps | `/projectwright:integrate-wiki`, `/projectwright:record-decisions`, people |
| Entry note of a component | Created by `/projectwright:add-repository`; then `/projectwright:integrate-wiki`, `/projectwright:record-decisions`, people |
| `project/team-and-roles.md` | `/projectwright:draft-minutes` (only entries the user authorises), `/projectwright:integrate-wiki`, `/projectwright:record-decisions`, people |
| `dashboard/`: hand-written parts (synthesis of `project-status`, introduction of `operating-assumptions`, reading paths, glossary) | `/projectwright:integrate-wiki`, `/projectwright:record-decisions`, people |
| `dashboard/`: Bases views | Written once at setup; then only people |
| `upstream` field of deviation ADRs | `/projectwright:propose-improvement` (`proposed`), `/projectwright:record-decisions` and people (`accepted`, `rejected`) |
| Read-only | `/projectwright:wiki-check`, `/projectwright:audit-code`, `/projectwright:reconcile-tracker`, development skills (except `progress` and `commits` of tasks) |
| Everything | Watched by `wiki-lint.py` (hook) and `/projectwright:wiki-check` |

---

## Changes to the framework

The files provided by the framework — the framework part of the root `CLAUDE.md`, this constitution, `wiki-sources/README.md`, `.githooks/` and, when it is copied into the project, the plugin in `.claude/skills/projectwright/` — can be changed for this project. The plugin **installed** from the marketplace is shared by every project on the machine and is never changed: to adapt its skills or scripts, the project first copies it with `framework.py vendor`, which also stops enabling the installed one for this project. The state of these files when the framework was applied is recorded in the lock file `.claude/projectwright.lock.json`, with an original copy in `.claude/.projectwright-original/`, so every change is detected (`wiki-query.py deviations`) and shown (`framework.py diff`). Every change is a **deviation**, motivated by an `ADR-MET` with `framework_deviation: true`. A deviation that can be useful to other projects is proposed to the framework with `/projectwright:propose-improvement`; the `upstream` field of its ADR records the outcome.

## Names of people

`project/team-and-roles.md` is the **only note where names of people are allowed**: it maps people to anonymous roles, and every name enters it only with the user's explicit consent. Everywhere else — notes, ADRs, questions, cards, minutes, code, tracker — people are referred to by **role** and **organisation**.

---

## Operating rules for whoever writes (human or AI)

1. **Before writing code**: run the pre-code gate (`dashboard/operating-assumptions.md`, the component folder, the open questions); stop on 🔴.
2. **New knowledge** = a new file in the right folder (placement rule), with a conforming frontmatter and wikilinks to the related notes.
3. **Existing knowledge to correct** = correct it immediately in its note; do not record the correction elsewhere.
4. **Never**: rename files, reuse IDs, duplicate a fact, write a generated list, touch the cards in `wiki-sources/` (immutable) or write there outside the ingestion flows.
5. **Code and its normative documents are cited as text** (constraint IDs, paths), never with relative links: they live in another repository.
6. The lint runs by itself after every write (hook) and, when the project folder is versioned, before every commit (git hook): fix the violations it reports immediately. Periodically, run the full check `/projectwright:wiki-check`.
