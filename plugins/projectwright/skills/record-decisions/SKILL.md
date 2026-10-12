---
name: record-decisions
description: Closes a working session by recording in the wiki everything the session changed — decisions → ADRs, new knowledge → notes, questions opened and closed, tasks, dashboard — plus the deviations from the framework, the tracker update to propose and the git commands to run. Applies directly what derives from the session; asks the user only on inconsistencies. Use at the end of every working session, or when the user asks to record decisions in the wiki.
---

# Record the decisions and the knowledge of the session

User input: $ARGUMENTS

The writing rules of the wiki — structure, placement, frontmatter, IDs, statuses, superseded decisions, write-ownership — are in the constitution (`wiki/README.md`): follow it, this skill does not repeat it. Records are written in `project.language`, reusing the headings of the existing records of the same type.

## 0. Input

What to record comes from `$ARGUMENTS` or from the **current working session**: what was decided, discovered or changed while working. If there is nothing to record, say so and stop — but still run §6 (deviations) and §9 (git commands) when the session changed files, and §8 (working profile) always.

## 1. Access perimeter — BINDING ⛔

1. **Write ONLY inside `wiki/`** — and there update **the whole wiki** as needed: thematic notes, component notes, decisions, questions, tasks (when `tasks.mode` is `wiki`), the hand-written parts of the dashboard. **Absolute exception: `wiki-sources/` is READ-ONLY** — cards and log belong to the ingestion skills.
2. **Do not modify anything outside `wiki/`** (official documents, code, the plugin, `project.yaml`, the tracker): if something there turns out to be out of date, **report it** in the summary — do not fix it. Only exception: the user's working profile, through `profile.py` (§8).

## 2. Rule of application

- **What derives from the session is applied directly**, without asking for confirmation item by item: the user was present when it was decided.
- **Stop and ask the user** only in front of:
  - an **inconsistency**: the novelty contradicts an existing note, an ADR or a claim of a card in `wiki-sources/`;
  - an **ambiguity**: from the session it is not clear whether something was *decided* or only *supposed*;
  - an **existing ADR** that already covers (fully or partly) the decision: updating it, superseding it or creating a new one is the user's choice.

## 3. Census of the session

Go through the session and classify the novelties:

1. **Decisions taken** → one ADR each (§4);
2. **New or corrected knowledge** → thematic notes, following the placement rule of the constitution. Existing note → update it; new knowledge → new file (in components: the component folder, a feature note prefixed with the component name);
3. **Questions**: those **closed** by the session are closed in their file (`lifecycle: closed`, `closed_on`, `closure_reason`, `decision`, `status: decided`); those **opened** by the session become new question files with a safe ID (template `templates/records/question.md` of the plugin), with `gate`, `assumption`, `precaution` and `decision_owner` where they apply;
4. **Epistemic statuses**: update the `status` of the notes touched (for example from `undecided` or `conflicting` to `decided`);
5. **Tasks**, when `tasks.mode` is `wiki`: update `progress` and `commits` of the tasks worked on, create the tasks agreed in the session (template `templates/records/task.md`), close the finished ones (`progress: done`, `closed_on`);
6. **Dashboard**: update the hand-written parts touched (synthesis of `project-status`, glossary, reading paths) — they stay **derived**: every fact in them must have its home elsewhere.

## 4. The ADRs

- ID `ADR-<CODE>-NNNN` with a **safe ID** (constitution, IDs): the highest number for that code, plus one — including `origin/<git.main_branch>` after a `git fetch` when the project folder is versioned and shared. Never reuse an ID.
- Template: `templates/records/decision.md` of the plugin; `source: "working session YYYY-MM-DD"`.
- A decision that supersedes an earlier one follows the constitution: the old ADR becomes `superseded` with `superseded_by`; the new ADR explains why.
- The **thematic note** of the decided topic is always updated and **links the ADR**: the decision lives in the ADR (immutable record), the current knowledge in the note.

## 5. Impact on the official documents

Compare the novelties with the **claims of the cards** in `wiki-sources/` (read-only): if a decision or a correction **supersedes** a claim of a card with `source_kind: reference`, the document named in the card's `source` is **behind** → put it in the list "official documents to update" of the summary, and in the dashboard section of the same name. You cannot touch it: the user must.

## 6. Deviations from the framework

The files provided by the framework are the plugin when it is copied into the project (`.claude/skills/projectwright/`; an installed plugin is never changed per project), the framework part of the root `CLAUDE.md` (everything before its "Project-specific instructions" section), the constitution `wiki/README.md`, `wiki-sources/README.md` and `.githooks/`. Check them mechanically:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" deviations
```

For every changed file **without an ADR**:

1. record an `ADR-MET-NNNN` with `framework_deviation: true` that names the files changed and says why (one ADR per coherent change; ask the user when the reason is not clear from the session);
2. add to the summary: *this change to the method could be useful to the framework itself: when you want, prepare a proposal with `/projectwright:propose-improvement`*.

When the framework was upgraded in this session and an upgrade includes a change that this project had proposed, set `upstream: accepted` in its deviation ADR. The project-specific section of `CLAUDE.md`, `project.yaml` and the development skills of the project are **not** deviations.

## 7. Tracker

When `tasks.mode` is `tracker` and the session worked on an issue (its key is known from the session):

- prepare for the issue a **content comment** — decisions taken and constraints, in your own words, following the drafting rules of the code: no wiki IDs (`ADR-*`, `Q-*`, `T-*`), no names of people or companies, by role;
- propose the **status change** of the issue, after reading its current status from the tracker;
- for every 🔴 question opened, propose a linked issue or a note on the affected issue, rephrased for whoever can read the tracker;
- record the issue key in the `tracker` field of the ADRs and notes concerned (one-way link: wiki → tracker).

With `tracker.write_mode: propose` show everything to the user and write to the tracker only after confirmation; `auto` is allowed only when `tracker.client_visible` is false.

## 8. Working profile of the user

The user's working preferences live in their personal profile, outside the project (`profile.py`, root `CLAUDE.md` rule 13). Look back at the session: did the user show a **stable** way of wanting to work — a correction ("explain it better", "aren't we overcomplicating this?"), a choice made again and again, a format they asked for? Record each new one, in the user's language, in one short sentence that says what to do:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/profile.py" add "<preference>"
```

and remove one that the session contradicted (`profile.py remove "<text>"`). Not every remark is a preference: a request about this task only is not. Never project facts, names or confidential data. No consent is asked — the profile is the user's and they can edit it — but the summary says what was recorded.

## 9. Closing

1. The lint runs by itself after every write: if it reports violations introduced by you, fix them.
2. Summary for the user:
   - ADRs created or updated, notes created or updated, questions opened and closed, tasks updated;
   - inconsistencies submitted to the user and how they were resolved;
   - ⚠️ **official documents to update** (explicit reminder — the wiki cannot correct them);
   - deviations from the framework recorded, with the upstream signal;
   - the tracker update to confirm, if any;
   - the preferences recorded in the working profile, if any, in one line;
   - when the session showed a friction with the framework itself (a skill or a rule that got in the way, something expected that did not happen), one line proposing to note it with `/projectwright:framework-feedback`;
   - **always**, the ready-to-paste git commands for every versioned repository changed in the session (any code repository, and the project folder if it is versioned), following `git.convention` and, when it exists, `wiki/project/development-workflow.md` (branch names, commit messages); when a change is ready for review, also the text of the merge request as the note prescribes (title, description, checklist, reviewers by role). Commits, pushes and merge requests are run by the user.
   - when the session decided how the team works with branches or merge requests: an ADR in the `STD` area and the update of `wiki/project/development-workflow.md` (§4).
