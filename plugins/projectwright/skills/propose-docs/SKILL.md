---
name: propose-docs
description: Proposes new official project documentation — or updates to the existing one — from the consolidated knowledge of the wiki, comparing what the wiki holds as decided with what the documents say (through the ingestion cards). Drafts are refined with the user and saved where they say. Use periodically, or when the user asks to align the documentation with the wiki.
---

# Propose documentation from the consolidated knowledge of the wiki

User input: $ARGUMENTS

## 0. Input

No mandatory input: the skill works on the wiki. If `$ARGUMENTS` names a topic or a document, restrict the audit to that.

## 1. Access perimeter — BINDING ⛔

1. **Read ONLY `wiki/`, `wiki-sources/` and `project.yaml`.** Do not open the official documentation folder: your baseline of "what the documents say" is **the cards in `wiki-sources/`**. Do not bring in external knowledge.
2. **Write nothing in the wiki** — not even in the ingestion log: for this skill the wiki is read-only.
3. The only output are the **proposed documents**, saved **where the user says** (ask when saving; propose `utils/docs/` by default). You never touch the existing official documents: you do not even see them.

## 2. The baseline and its limit — always declare it

The cards describe the documents **as of their last ingestion** (`ingested_on`). If a document changed later, you cannot know. Therefore:

- every proposal **declares the date of the baseline** it rests on;
- at the start and in the summary remind the user: *if the documentation changed recently, ingest it again with `/projectwright:ingest-sources` first; then this audit makes sense*.

## 3. The search — two directions, one strict filter

Compare the knowledge of the wiki (thematic notes and ADRs) with the claims of the cards:

1. **Documents behind**: knowledge with status `decided` that **supersedes** the claims of a card with `source_kind: reference` → proposal to **update** that document. Cards and notes with the marker `⚠️ Document to update` are the first candidates;
2. **Clusters without a home**: knowledge with status `decided`, stable and coherent around a topic, that **no reference card covers** → proposal of a **new document**.

**Strict filter**: only knowledge with status `decided` is promoted. Never `hypothesis`, `conflicting`, `undecided`, never open questions — the transitory lives in the wiki and stays there. And **never propose changes to minutes**: they are events, history is not updated.

## 4. Proposal and refinement — together with the user

For each proposal, **one at a time**:

1. **Present what and why**: which `decided` knowledge justifies it (with wikilinks to notes and ADRs), which claims turn out superseded (for updates), the date of the baseline;
2. if the user accepts, **write the complete draft**, following the drafting rules of `project.yaml`:
   - **cardinal points, not snapshots**: no progress states, open points or choices in progress;
   - **human-readable**: written for people, not for the AI;
   - **self-contained** (`drafting.self_contained`): no paths, no references to other files, no mention of the wiki or of its mechanics;
   - **no forbidden content** (`drafting.forbidden`, by default names of people, economics, opinions): organisations and roles stay anonymous;
   - **file name** of technical documents with the suffix of the stream when the project uses them (`drafting.technical_docs.suffixes`);
   - the language of the document is `project.language`;
   - for **updates**: the whole document in the proposed version, plus the bullet list of **what changes** compared with the baseline;
3. **refine the draft with the user**: apply their corrections and iterate until they approve — these are documents of the people, the final form is theirs;
4. **ask where to save it** — propose `utils/docs/` (under `paths.utils`) by default — and save it there. Then move to the next proposal.

## 5. Closing

Summary for the user:

1. documents **created** and **updated**, where they were saved and the knowledge promoted (wikilinks);
2. the **reminder that closes the loop**: put the documents in the shared documentation space and **run `/projectwright:ingest-sources` again** — re-ingestion will update cards and log, and the wiki ↔ documents cycle is aligned again without ping-pong;
3. any clusters **not promoted** because not yet `decided` (useful to know: they are the candidates of the next round).
