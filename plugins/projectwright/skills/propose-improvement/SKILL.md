---
name: propose-improvement
description: Prepares a proposal to bring the changes this project made to the framework (skills, templates, schema, rules) back to the projectwright framework — collects the deviations, asks which ones to propose, writes an anonymous, self-contained proposal document with the reason and the exact change, and marks the deviations as proposed. Use when the user wants to propose an improvement of the method to the framework.
---

# Propose an improvement to the framework

User input: $ARGUMENTS

A project may change the files provided by the framework (constitution § "the files provided by the framework"); every change is a **deviation**, motivated by an `ADR-MET` marked `framework_deviation: true`. This skill turns one or more deviations into a **proposal document** that the user brings to the framework, where it is decided.

## 1. Collect the deviations

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" deviations
```

It lists the framework files changed since the framework was applied (from the lock file `.claude/projectwright.lock.json`) and the deviation ADRs, with their `upstream` state.

- **Changed files without an ADR**: first record them — ask the user why the change was made and write the `ADR-MET` (as `/projectwright:record-decisions` does). A proposal without a reason is not useful.
- **No lock file**: changes cannot be detected; work only from the deviation ADRs, and tell the user.
- Deviations with `upstream: proposed`, `accepted` or `rejected` are not proposed again, unless the user asks.

If `$ARGUMENTS` names a topic or an ADR, restrict to it. Otherwise show the candidate deviations (one line each: what and why) and **ask which ones to propose**; related deviations can go in the same proposal.

## 2. Make it generic — BINDING ⛔

The framework is public: the proposal must make sense for **any** project and reveal nothing of this one.

- No names of the project, of the client, of organisations or people; no internal details (domain, components, decisions of the project). Describe the need in general terms: "in projects with frequent calls with external suppliers, …".
- If a change mixes something general with something specific to this project, propose only the general part, and say so to the user.
- Show the user the parts you generalised.

## 3. Write the proposal

One document per proposal, in `project.language` (headings included), self-contained (it does not refer to files of this project):

````markdown
# Improvement proposal — <short title>

| | |
|---|---|
| **Framework version** | <version in .claude/projectwright.lock.json> |
| **Date** | <YYYY-MM-DD> |
| **Files of the framework** | <paths inside the plugin or the framework files, e.g. skills/draft-minutes/SKILL.md> |

## The need
<what was missing or wrong, from the experience of a project, in general terms>

## The change
<what changes, in plain words>

## Why this way
<the reasons; alternatives considered>

## The exact change
```diff
<from: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/framework.py" diff <files> — anonymised if needed>
```

## Notes for the framework
<impact on other projects, on the schema, migrations needed — or "none">
````

- The diff comes from `framework.py diff <files>`, which compares with the original copy saved when the framework was applied (`.claude/.projectwright-original/`). If that copy is missing, describe the change precisely instead, and say so.
- File name: `<YYYY-MM-DD> - Improvement proposal - <short title>.md`.
- **Ask the user where to save it** — propose `utils/proposals/` (under `paths.utils`) by default, or the proposals folder of the framework project if they have it locally — and save it there. Nothing is sent anywhere: bringing the proposal to the framework is the user's act.

## 4. Mark the deviations as proposed

In each deviation ADR included in the proposal, set `upstream: proposed` and update `updated`. This is the only change this skill makes to the wiki. Later, when the framework accepts or rejects the proposal, the user (or `/projectwright:record-decisions` after an upgrade of the framework) sets `accepted` or `rejected`.

## 5. Closing

Summary for the user: proposals written and where; deviations included and marked `proposed`; the parts that were generalised or left out; if the project folder is versioned, the ready-to-paste git commands for it (commits and pushes are run by the user).
