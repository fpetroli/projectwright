---
name: draft-minutes
description: Writes the minutes of a project call from its transcript and from the screenshots shared in the call, applying the drafting rules of the project (by default no names of people, no economics, no opinions, self-contained document) and asking, for each minutes document, which reserved data to keep. Learns from one minutes document to the next — roles, people, transcription fixes — saving only what the user authorises. Use when the user asks to write the minutes of a call or provides a transcript to turn into minutes.
---

# Write minutes from a transcript

User input: $ARGUMENTS

## 0. Input

- The user must provide **the transcript of the call**: a path to a file or the pasted text. If `$ARGUMENTS` is empty and no transcript was given in the conversation, **ask for it** before proceeding ("Give me the path of the transcript or paste it here").
- **Accepted formats**: text (`.txt`, `.md`), subtitles (`.vtt`, `.srt`) or `.docx` (the usual export of video-conferencing tools). For a `.docx`, extract the text with `python3 "${CLAUDE_PLUGIN_ROOT}/skills/draft-minutes/scripts/docx2txt.py" <file.docx> <output.txt>` (standard library only, also extracts the comments of the document) and work on the extracted text, saved in a temporary folder, not next to the original.
- Read the transcript **entirely** before writing anything. If it is long, read it in blocks up to the last line: a partial reading produces partial minutes.
- **Drafting rules** of the project: the `drafting` section of `project.yaml` — common rules (`forbidden`, `self_contained`) and those of the minutes (`drafting.minutes`: file name format, allowed participant labels). The rules of §3 are the defaults of the framework; when `project.yaml` relaxes or adds something, `project.yaml` wins.
- **What the project already knows**: read `wiki/project/team-and-roles.md` — organisations and anonymous roles, people already associated with a role, transcription fixes. It is the **only** project file you may read besides the transcript, and you use it **only** to choose roles and correct words, never as a source of content.
- **Call metadata**: exports often have a header with title, date/time and duration; the file name may contain a timestamp. Header times may be in **UTC**: convert them to the team's local time and compare with the timestamp of the file name; if they do not match, ask the user which one to use. Without a header, ask for **date and time** and a **thematic title**.
- **Checkpoint before writing.** Once the reading is done, find the unknowns that run through the whole document and ask about them **now**, in a single list: (a) speakers whose **organisation or role** cannot be deduced from the content and are not in `team-and-roles.md`; (b) unrecognised terms that **could be names of people**; (c) **which reserved data to keep in this document**. Clarifying them later costs a full rewrite.
- **Reserved data, chosen for each minutes document.** For every kind of reserved data that the project's rules exclude (`drafting.forbidden`: `person-names`, `economics`, `opinions`) **and that actually appears in the call**, ask whether to keep it **in this document**, stating the project default — for example: *"Five people are named in the call and an estimate of 20 days is given. The project rules leave out names and amounts: for these minutes do I keep the names? And the amounts?"*. Do not ask about kinds of data the call does not contain. The answer holds for this document only; when the user says it should always hold, propose to change `drafting.forbidden` in `project.yaml` and record the reason in an `ADR-MET`. People management (R4) and the self-contained form (R5) are not optional. Everything else (doubtful technical terms, interpretations) does not block: it stays marked ⚠️ in the text and goes into the final list of doubts.
- **Attachments of the call (optional)**: the user may provide **screenshots of the screen shared** during the call (diagrams, templates, demos). They live in a **folder with the same name as the minutes, without `.md`**, next to the file; their names end with the time of the shot (`… Screenshot YYYY-MM-DD HHMMSS.png`). Before writing: check whether the folder exists (even if the user does not say so), **read every image** and compute for each the **minute of the call** = time of the shot − start time of the call, so as to tie each figure to what was being said at that moment (§4, step 6).
- ⛔ **Only allowed inputs: the transcript, its attachments and `team-and-roles.md`** (plus date, title and save location asked to the user). Attachments are content of the call itself (what participants were seeing), not external knowledge. **Do not read other project files** — previous minutes, other wiki notes, documentation, code — and **do not bring in external or previous knowledge**: every content of the minutes derives from the transcript. What the transcript does not say stays an **open point** or an **uncertain term ⚠️** — it is not resolved by consulting documentation nor completed "from memory".

## 1. What to produce

A Markdown file, saved **where the user says**: minutes are official documents, so if not said, propose the place where the documentation folder (`paths.official_docs`, by default `docs/`) already keeps minutes — its structure is the user's — or ask, with the name built from `drafting.minutes.filename` (default `{date} - {title} - {participants}`):

- **title**: describes the **topic**, never the people (for example "Technical onboarding pt2 (prototype, data model)", "Deep dive on the authentication service"). Names of organisations are allowed, names of people are not;
- **participants**: the organisations or teams present, joined by a hyphen (for example `TeamA-TeamB`, `TeamA-Client`); for internal calls, one of the labels in `drafting.minutes.allowed_participants` (default `Internal`);
- the date in `YYYY-MM-DD` format.

The title **inside** the document (`# Minutes – <Title>`) repeats the topic; the word "Minutes" does not go in the file name. The document is written in `project.language`, headings included.

The minutes are a **very complete record**: they go into the details, trace all the technical knowledge, the decisions taken and the open points. Not a short summary: whoever reads them must be able to reconstruct the whole call.

## 2. Structure of the document

```markdown
# Minutes – <Title>

| | |
|---|---|
| **Date** | <weekday> <date>, <time> |
| **Duration** | ~<duration> |
| **Type** | <nature of the session: onboarding / technical alignment / planning / …> |
| **Written on** | <today's date> |

## Participants

| Role | Organisation | Contribution in the call |
|---|---|---|
| <anonymous role> | <organisation> | <what they brought to the call> |

**Actors mentioned:** <roles/organisations mentioned but not present>.

> ⚠️ **Note on attribution.** [ONLY IF NEEDED] The attribution of some passages is uncertain and was reconstructed from the content.
>
> **Reading note.** Points whose interpretation remains uncertain are marked ⚠️ and collected in §<last N>.
>
> **Drafting note.** Only project content is reported: facts, decisions, technical topics and open points. Personal assessments of people or organisations expressed in the call are omitted. Economic and management content is not in scope of the minutes; references to people are given by organisation and role.   ← drop the sentences about the data this document keeps (§0)

## Material shared in the call          ← ONLY IF THERE ARE ATTACHMENTS (announced by the Reading note)

| Figure | Minute of the call | Content | File (attached folder) |
|---|---|---|---|
| **Fig. 1** | ~00:02 (§1) | <title/content of the screen> | `<file name>.png` |

---

## 0. Executive summary

<The 2–4 load-bearing decisions or novelties of the call, in dense prose. What changes compared with before.>

---

## 1..N. <Thematic area>          ← one section per topic discussed

**Discussion**

![Fig. N – <title>](<./<attachments folder>/<file name>.png>)      ← ONLY IF the figure concerns this topic

*Fig. N – <caption: what it shows and who shared it (organisation)>.*

- <detailed and faithful reconstruction: facts, reasoning, concrete examples, verbatim quotes in «» when significant; references to figures as "Fig. N" or "step 11 of Fig. 1">

**Decisions**
- ✅ <decision taken>

**Open points**
- ❓ <what remains to be clarified/decided>

---

## N+1. Action items

| # | Action | Owner | Status |
|---|---|---|---|
| 1 | <action> | <ORGANISATION, never people> | Open / In progress / Agreed / Planned |

---

## N+2. Points to verify / uncertain terms

| ⚠️ | Term heard in the call | Interpretation | To confirm |
|---|---|---|---|
| <category> | "<term as heard>" | <interpretation> | <what remains to confirm, or —> |

---

## N+3. Synthesis: <load-bearing technical decisions / glossary>   ← optional, when the call deserves it
```

Further format conventions: priorities 🔴 (blocking) / 🟠 (soon) / 🟡 (to clarify) where useful; bold on key concepts; tables for comparable lists.

## 3. Drafting rules — BINDING

These are the defaults of the framework; `drafting` in `project.yaml` may change them for the project. Within the project the only exception is the reserved data the user chose to keep **in this document** at the checkpoint of §0: `person-names` lifts R2 (names may be used where the rule would put a role, and the participants table may carry them), `economics` lifts R3, `opinions` lifts R1. R4 and R5 always apply.

### R1 — Never personal opinions on people or organisations
Personal assessments expressed in the call (on colleagues, other organisations or teams, suppliers, the client) **do not appear**. The **facts** stay, even uncomfortable ones, in neutral form: "the documentation has not arrived", "the supplier is late without a delivery date", "the stream started without prior alignment". **Technical criticism** (of a design, a naming, a choice) is legitimate content and is reported as such. Avoid evaluative words about the subject ("sloppy", "for show", "keep an eye on them"): rephrase on the fact ("incomplete information", "formal without supporting structure", "monitor the progress").

### R2 — Never names of people: only organisations and anonymous roles
- Attribute to the **organisation** (or team) wherever possible.
- Where you need to tell people apart inside an organisation, use **anonymous roles**: those of `team-and-roles.md` first. Typical forms: "the architecture lead", "the application lead", "the delivery lead", "the functional analyst", "the <team> lead", "the client's owner", "the client's functional contact".
- For a new person: coin an anonymous role consistent with the others ("the <function> lead of <organisation>"), never use the name; if organisation or role cannot be deduced from the content, **ask the user before writing** (checkpoint of §0), without guessing.
- The correspondence **names → roles never goes into the minutes**. It lives only in `team-and-roles.md`, and only for the people the user has authorised (§5).
- It holds **everywhere**: title, text, quotes, table of uncertain terms, owners of action items (always organisations). Names irrelevant to the project (interruptions, people of other projects): omit them entirely.
- An unrecognised term that **could be the proper name of a person** (surname, nickname, a team name that matches a surname) **does not enter the document**, not even the table of uncertain terms: describe it by function ("the structure that triggers the procedures") and ask the user what it is.
- Mind the grammar of the substitutions.

### R3 — Never economic content
Forbidden: amounts, estimates with values (days, currency), negotiations and economic splits, budgets, negotiating tactics, margins and buffers. Allowed: "the impact on estimates and plan was not quantified" (without values), contractual scope facts without amounts ("frontend tests are not in the contract"), and **functional amounts of the domain** (for example "a refund of 3,000 as a use case" — it is application content, not project economics).

### R4 — Never people-management content
No indications on how much autonomy to give someone, assessments of experience, management of individuals. The substance of method is kept in impersonal form ("strong direction and close supervision on the standards").

### R5 — Self-contained document: no references
- **No "Source" row** in the header, no paths to files or folders, no file names, no links.
- **Never mention** transcript, diarisation, recording, audio, speaker labels, timestamps of the recording. The minutes talk about the **call**, not about its file: "emerged in the call", "the term was not caught", "that part is not traced".
- **No references to other files**, not even in the same folder: no "see minutes X §Y", no external tracker IDs, no links to other documents. Other sessions are cited **as events** ("in the previous session", "in the overview call of the same day"), never as documents.
- **Divergences from project artefacts or guidelines** are annotated **inline and self-explanatory** — `> 🔴 **Divergence from <artefact cited in the call>.** <what the artefact prescribes, as reported in the call>: «…». <why it is a problem / what must be decided>` — but **only if the divergence emerged in the call itself**: do not compare the minutes with other artefacts to find new ones (that would be external knowledge).
- Allowed: internal references within the same document ("see §8") and the **names of project artefacts** mentioned in the call, provided that the relevant content was said in the call and is reported inline.
- **Only exception: the attachments of the call** (§0). Screenshots shared in the call are embedded with a path **relative** to the folder with the same name (`![Fig. N – …](<./<folder>/<file>.png>)`, angle brackets because names contain spaces) and listed in the table "Material shared in the call" with the file name in backticks. They are content of the call, not external references: the minutes stay self-contained because the folder travels with them. The content of every figure is still **reported inline in the text** (tables, numbered steps, exact names): whoever reads without the images must lose nothing.

## 4. Working the transcript

1. **Identify the speakers and map them to roles.** Speakers may appear as **anonymous labels** (for example `SPEAKER_01`) or with **first and last name** (video-conferencing exports); in both cases the document contains **only roles and organisations** (R2).
   - With anonymous labels: map them to roles from what they say **in this call** (who presents the database and the standards → an architecture lead; who presents the frontend → an application or frontend lead; and so on). If the diarisation mixes speakers in the same block, reconstruct from the content and declare the uncertainty.
   - With names: use `team-and-roles.md` when the person is there; for the others deduce organisation and role from the content and, if impossible, **ask at the checkpoint of §0**. People mentioned but not present follow the same rule.
   - If an identification remains doubtful after the checkpoint, declare it in the "Note on attribution" and add it to the final list of doubts.
2. **Normalise the terms mangled** by automatic transcription. Apply the **transcription fixes** of `team-and-roles.md` and the obvious general ones (technical terms rendered as similar-sounding common words). Apply a normalisation **only if the context of the transcript confirms it**; the terms that remain doubtful are **marked ⚠️ in the text** and collected in the table of uncertain terms with the proposed interpretation, without resolving them with external knowledge. Exception: terms that could be **names of people** go neither in the text nor in the table (R2), only in the questions to the user.
3. **Organise by thematic area**, not chronologically: group the discussion by topic; for each topic separate discussion / decisions / open points.
4. **Omit** (leaving no trace of the content; at most "a non-relevant segment was omitted"): personal digressions, opinions on people or organisations, economic and people-management content (R1–R4).
5. **Quote verbatim in «»** the sentences that fix a concept or a decision (after normalisation and without names).
6. **Integrate the attachments** (if any, §0). For every screenshot: (a) compute the minute of the call and find the corresponding passage of the transcript, to tie **what was said to what was seen**; (b) assign a progressive "Fig. N" in chronological order and fill the table "Material shared in the call"; (c) embed the figure in the relevant thematic section with a caption; (d) **transcribe in the text the content of the image** (diagrams → table of levels/components and numbered steps of the legend; templates → field/description table with the **exact names**; demos → what was seen), weaving it with what was said aloud; (e) use the images to **resolve ⚠️ terms** they clarify (for example the mangled name of a field that is readable on the screen) and remove the resolved rows from the table of uncertain terms; (f) if the image **contradicts** or refines what was said aloud, flag it ⚠️ in the text and in the table of uncertain terms, without deciding who is right. Names of people visible in the screenshots (user names, signatures, chats) **are not transcribed** (R2); if an image is full of them, describe it without embedding it and tell the user.

## 5. Closing

1. **Mechanical check**:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/draft-minutes/scripts/check-minutes.py" <transcript> <minutes.md> --roles-note wiki/project/team-and-roles.md [--names "Name1,Name2"] [--attachments <folder>] [--allow names,economics]
   ```
   Pass `--allow` with the reserved data the user chose to keep in this document (§0): `names` skips the search for names (R2), `economics` the one for currency (R3).
   The script does only the mechanical checks, the same in every language: it derives the speakers' names from the transcript, adds the names saved in `team-and-roles.md` (so it also finds people mentioned but not present) and those passed with `--names`, and looks for all of them in the minutes (full name and single first/last name); then it looks for anonymous speaker labels, paths, links, file names, currency signs and codes (R2, R5, R3). With `--attachments` it accepts the references to the images and checks that **every file of the folder is cited** in the minutes and that **every embedded image exists**. Fix every violation and run the script again until there are zero violations; warnings are assessed by hand.
2. **Semantic reread**, in the language of the minutes, for everything that depends on the language or on judgement:
   - R5: mentions of the transcript, the recording, the audio or its timestamps ("as the transcript shows", "in the recording…"), cross-references to other documents ("see the minutes of…"), a "Source" row in the header;
   - only for the rules that still apply to this document (§0):
   - R3: economic content in words or without figures (estimates in days, budgets, margins, negotiations, splits) — distinguishing it from functional amounts of the domain;
   - R1 (opinions on people or organisations) and R4 (people management);
   - owners of action items at organisation level, grammar of the name → role substitutions.
3. If the user has not said yet **where to save** the minutes, propose the place where the documentation folder (`paths.official_docs`) keeps minutes, and save the file there once confirmed.
4. In the final message to the user (NOT inside the minutes): summarise the topics covered and, if there are attachments, the **mapping figure → minute of the call**; then — if there are doubts of interpretation, identification of roles or drafting choices — present them as a **numbered list** of questions. Names of people may appear in this message to the user, never in the minutes.
5. **What was learned — saved only with consent.** List what this minutes document taught that `team-and-roles.md` does not contain yet, as numbered entries, marking those that contain a name:
   > 1. Person: <First Last> → <role> of <organisation> *(contains a name)*
   > 2. New role: <the technical lead of the supplier>
   > 3. Transcription fix: "<as transcribed>" → <correct term>

   Ask the user **which entries to save**, one by one (for example "save 2 and 3, not 1"), and add **only the authorised ones** to the right section of `wiki/project/team-and-roles.md`, updating its `updated` date. Nothing is saved without an explicit yes. Do not save anything in this skill's own files: they belong to the framework.
6. Remind the user, in one line, that **the wiki is updated separately**: when the minutes are in the official documentation folder, `/projectwright:ingest-sources` ingests them (do not do it automatically: it is outside the perimeter of this skill). The wiki stays anonymous even when the minutes keep names or amounts: the card reports people by role and leaves out what the project's rules exclude.

## 6. Tools of the skill

In the `scripts/` folder of the skill, both using only the Python standard library:

| Script | Use |
|---|---|
| `docx2txt.py <file.docx> [<output.txt>]` | Extracts the text (and the comments) of a `.docx` transcript; without output it prints to stdout |
| `check-minutes.py <transcript> <minutes.md> [--roles-note <note>] [--names "…"] [--ignore "…"] [--attachments <folder>] [--allow names,economics]` | Language-independent mechanical check of R2/R5/R3 (names, speaker labels, paths, links, file names, currency signs and codes); accepts the transcript as `.txt` or `.docx`; `--roles-note` adds the names saved in the People table of the note; `--ignore` excludes tokens that coincide with common words; `--attachments` allows the references to the screenshots of the call and checks that all the files of the folder are cited and that the embeds point to existing files; `--allow` skips the checks of the reserved data kept in this document; exit code 1 when there are violations |
