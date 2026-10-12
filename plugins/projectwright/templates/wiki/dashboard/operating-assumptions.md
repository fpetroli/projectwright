---
title: Operating assumptions (pre-code gate)
type: dashboard
status: informational
area: PRJ
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: "derived view of the open questions"
related:
  - "[[project-status]]"
---

# Operating assumptions (pre-code gate)

Read this before writing code. The gate is computed from the **question files** (project level and components): the assumption and the precaution of each question live in the question itself, never in hand-kept lists here.

For Claude and outside Obsidian: `wiki-query.py questions --lifecycle open` (in the `scripts/` folder of the plugin).

## How to use the gate

- 🔴 **Stop** — the code that touches the topic is not implemented until there is a decision. Report to the user; restart only on an explicit decision.
- 🟠 **Proceed with the assumption** — implement with the declared assumption and the prescribed precaution (typically: isolate the unstable choice behind an interface or a single configuration point). Declare the assumption to the user before implementing.
- 🟡 **Decide when needed** — a detail decided in the task, declaring the choice to the user.

<!-- Project-specific guidance on the gate, if any. -->

## 🔴 Stop

<!-- Bases view: open questions with gate red, with what they block. -->

## 🟠 Proceed with the assumption

<!-- Bases view: open questions with gate orange, with assumption and precaution. -->

## 🟡 Decide when needed

<!-- Bases view: open questions with gate yellow. -->
