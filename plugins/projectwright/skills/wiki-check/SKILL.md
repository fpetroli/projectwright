---
name: wiki-check
description: Guardrail of the wiki — full integrity check, mechanical and semantic, of wiki/ and wiki-sources/. Corrects nothing, reports. Use periodically, at the end of a large intervention on the wiki, or when the user asks.
---

# Wiki check

User input: $ARGUMENTS (no input required: the check is **always complete**, there are no reduced modes).

The rules being checked are those of the constitution (`wiki/README.md`) and of `wiki-sources/README.md`.

## 1. Perimeter — BINDING ⛔

- **TOTAL READ-ONLY**: this skill does not write, modify or delete anything, in any folder. It finds and **reports**; the corrections are decided by the user (or made by the skill that introduced the violation).
- Read only `wiki/`, `wiki-sources/`, `project.yaml` and the plugin (to run the script of §2 and compare the development skills with the ADRs). No other project file, no external knowledge.

## 2. Mechanical layer (script)

From the project root run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-lint.py"
```

and collect its full output. It covers what a script can judge: links, unique names, valid frontmatter and allowed values, IDs, superseded decisions, component entry notes, direction of links, consistency with `project.yaml` and `repositories/`, immutability of the cards, encoding.

## 3. Semantic layer (your work)

Reading the wiki, check what a script cannot judge:

1. **Divergences between cards and notes**: for every card marked `integrated` = `yes` in the log, do its claims find a match in the wiki notes? When a note has evolved in **contradiction** with a card, report the pair (card, note) quoting the passages — material for an arbitration by the user or for `/projectwright:propose-docs`.
2. **Contradictions between notes**: two notes that state incompatible facts (dates, rules, scopes, responsibilities). Quote both.
3. **Forbidden content**: names of people outside `project/team-and-roles.md`; economic content (amounts, estimates with values, negotiations). Recognising them takes judgement: do not stop at patterns.
4. **Facts that live only in the dashboard**: substantial statements in `dashboard/` that have no home in another note (the dashboard owns no facts).
5. **One fact, one place**: the same substantial fact repeated in several notes instead of written in one and linked from the others; pairs of notes on very close topics that may overlap.
6. **Ageing assumptions**: notes and questions with status `assumed` whose `updated` date is old — a debt to bring to the user.
7. **Development standards vs decisions**: rules in the references of the development skills (`dev_skills` in `project.yaml`) that contradict an ADR still `decided`.
8. **Tasks not consolidated** (constitution, principle 14): tasks `done` or `cancelled` that still have a **Log** and no **Outcome**, or whose log holds knowledge of lasting value that no note of their component carries.
9. **Decisions hidden in a task**: lines of the log of an open task that state a decision or an open question with no ADR or question file — they do not wait for the task to close.
10. **Ids that are not the wiki's**: ids of the proposals (`P-…`) or of the reminders (`R-…`) cited in the wiki — they are for the tools, and their files are personal and never versioned.

## 4. Report

Fixed structure:

1. **Verdict on top**: `✅ Wiki sound` or `❌ N violations`.
2. **Mechanical section**: the output of the script, as is.
3. **Semantic section**: for each check (1–7), the violations found with **file (and line where possible)** and a one-line explanation; when a check is clean, say so explicitly.
4. **Final numbered list** of all violations, ordered by severity (first what corrupts the truth: contradictions and divergences; then structure; then style), so that the user can say what to correct by number.

Do not propose bulk automatic corrections: at most, for each violation, say **where** it should be corrected according to the constitution. Correcting is a separate activity that starts only on the user's request.
