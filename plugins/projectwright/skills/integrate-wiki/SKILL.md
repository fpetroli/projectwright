---
name: integrate-wiki
description: Propagates into the wiki the knowledge of the ingestion cards not yet integrated (wiki-sources/) — creates and updates thematic notes, decisions, questions, component notes and the dashboard. Works autonomously and involves the user only for conflicts with the existing wiki, to approve the skeleton when the wiki is born, and for decisions it cannot make alone. Use when the user asks to integrate the wiki or after a round of /projectwright:ingest-sources.
---

# Integrate the ingestion cards into the wiki

User input: $ARGUMENTS

The writing rules of the wiki — structure, placement, frontmatter, IDs, statuses, superseded decisions, write-ownership — are in the constitution (`wiki/README.md`): follow it, this skill does not repeat it. Records are written in `project.language`, reusing the headings of the existing records of the same type.

## 0. Input

No mandatory input: the work queue is in the ingestion log. If `$ARGUMENTS` names a specific card, work only on that one.

## 1. Way of working: autonomous

When things are smooth and clear, **proceed without asking for confirmation step by step**. Stop and involve the user **only** when:

- a claim of a card **contradicts an existing note** of the wiki (§6);
- you are in **bootstrap mode** (§4) and must have the **skeleton** approved once, because file names are permanent;
- an ADR, a question or a task needs an **ID** that you cannot make safe (§5);
- the card records a **missing arbitration** or a divergence that only the user can resolve.

Ask grouped questions, quoting the versions being compared and always offering the option "still open". If the user asks to see the steps, show the plan of each card and wait until they let you proceed. Always close with a summary (§7).

## 2. Access perimeter — BINDING ⛔

1. **Work ONLY inside `wiki/` and `wiki-sources/`**, with `project.yaml` and the plugin scripts: do not read or write anything else (no official documents, no code repositories). Your only source of knowledge are **the ingestion cards**: do not bring in external or previous knowledge. The only exception, when the project folder is versioned, is `git fetch` and reading `origin/<git.main_branch>`, needed for safe IDs.
2. **The cards in `wiki-sources/` are IMMUTABLE**: never modify them. In `wiki-sources/` you may touch **only `ingestion-log.csv`, only the `integrated` column**, and only through the script (§7) — never by hand: a broken row breaks the diff.
3. Write in `wiki/` **following the constitution**.

Operating note: write the notes with the file-writing tool, not with shell heredocs.

## 3. The work queue

The rows of `wiki-sources/ingestion-log.csv` with `integrated` = `no` are the queue, in increasing order of `ingested_on` and, for equal dates, by **date of the document** (the one in the name or in the card). Rows with `n/a` (ignored files) are skipped. Empty queue → report "nothing to integrate" and stop.

## 4. Two modes

**Steady state** (few cards in the queue and a wiki already populated): one card at a time, following §5, marking the log after each one.

**Bootstrap** (the wiki is empty, or the queue has five or more cards): working one card at a time would rewrite the same notes several times. Then:

1. read **all** the cards in the queue;
2. design the **skeleton**: the list of notes to create (name, folder, content), the components and their codes, the ADRs with their IDs, the consolidated questions with their IDs, the glossary terms;
3. **propose the skeleton to the user and wait for approval**: it is the only approval needed, because file names are never renamed;
4. write the notes **consolidated** across all the cards that touch them, citing all of them in `source`;
5. mark all the rows of the log and close the round (§7).

## 5. Integration rules

- **Placement** of knowledge (constitution, placement rule): `project/` = project context — and the team's development workflow (branches, commits, merge requests, review) always in `wiki/project/development-workflow.md`, created from the plugin template `templates/wiki/project/development-workflow.md` when missing · `domain/` = functional model of the platform (one concept or process per note, if the module is active) · `architecture/` = cross-cutting technical views and the bridge note of the standards (if the module is active; otherwise the bridge note goes in `project/`) · `components/<repo>/` = inside the boundary of one component. A reference document that lists the components gives rise to their folders and entry notes (`type: component`, template `templates/records/component.md` of the plugin) only for components already registered in `project.yaml`; for a component that is not registered, propose `/projectwright:add-repository` to the user. Feature notes are born when the feature is worked on.
- **One fact, one place.** If the knowledge already exists in a note, **update that note**; if it is new, **new file**; never duplicate. The fact lives in the competent note and the others **link** it.
- **Decisions → ADRs**, one per decision, in `decisions/` or `components/<repo>/decisions/` (template `templates/records/decision.md`), with ID `ADR-<CODE>-NNNN` and a **safe ID** (constitution, IDs). A **decision repeated in several cards is a single ADR** that cites all of them in `source`; the date of the decision is that of the first event. A **superseded** decision follows the constitution (`superseded`, `superseded_by`).
- **Open points → questions**, one file per question, in `questions/` or `components/<repo>/questions/` (template `templates/records/question.md`), with a safe ID `Q-<CODE>-NNNN`. **One question = one decision topic**, not a bullet: open points of the cards are merged by topic. Fill `gate` following the pre-code gate (🔴 the code that touches the topic is not implemented until a decision · 🟠 proceed with a declarable assumption and a precaution · 🟡 detail decided when needed), with `assumption`, `precaution` and `decision_owner` (by role) where they apply. A question answered by later knowledge is **closed in its file** (`lifecycle: closed`, `closed_on`, `closure_reason`, `decision` if an ADR closes it, `status: decided`).
- **Terms → `dashboard/glossary.md`**, each entry with the link to the note that owns the fact.
- **Epistemic status** of what you write: `decided` when the card reports it as decided; `undecided` for open points; `informational` for descriptive facts; `assumed` when a draft or a document takes a position on a point that the events leave open; `conflicting` when the card records a divergence from a development standard or an arbitration that reopens a decision.
- **Divergences from the development standards** (marked `⚠️ Divergence from the standard` in the cards): the note or ADR involved becomes `conflicting`, the divergence becomes a question in the `STD` area, and the bridge note of the standards lists it. **Never arbitrate**: standards are binding, but no source wins alone; the user decides.
- **Provenance and links**: every note cites its cards in `source` (wikilinks to the card names) and its neighbours in `related`; in the body, ADRs and questions are linked by name. Aliases `[[name|alias]]` are allowed, also in tables (escaped pipe).
- **Proposals of change** (a card of a document that proposes changes to the product — for example an improvement proposal written by `/projectwright:propose-improvement` in another project): one **question** per proposal in the component concerned, `gate: yellow`, `decision_owner` the user, with the need, the change and the card in `source`. Accepting or rejecting it is the user's decision; the accepted change is then made in the code like any other work.
- **Tasks**: cards do not create tasks. When `tasks.mode` is `wiki`, actions agreed in minutes can become task files only if the user asks for it.

## 6. Conflicts

If a claim of a card **contradicts an existing note**, **STOP and ask the user** which version holds, citing card and note and offering "still open"; never decide alone. Apply the outcome: update the note, or mark it `conflicting` with the explanation and open the question. Not conflicts: the **declared evolutions** recorded by the cards (apply the most recent version, supersede the old ADR) and the **refinements**.

## 7. Closing the round

1. **Update the hand-written parts of the dashboard** once per round (not at every card): the reasoned synthesis of `dashboard/project-status.md` (where we are, what blocks what, one line per component), the introduction of `dashboard/operating-assumptions.md` if the gate guidance changed, the reading paths of `dashboard/knowledge-map.md` if new areas were born, and the glossary. The lists are computed views: never write them by hand. No fact may live only in the dashboard.
2. **Mark the outcome** in the log, with the script:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ingestion-diff.py" --mark-integrated <card> [<card> …]
   ```
3. The lint runs by itself after every write: if it reports violations in what you wrote, fix them.
4. Summary for the user: cards integrated; notes created and updated; ADRs and questions created, closed or superseded; conflicts arbitrated; notes and ADRs `conflicting`; the 🔴 points that stop the code; if the project folder is versioned, the ready-to-paste git commands (commits and pushes are run by the user).
