---
name: audit-code
description: Consistency audit between the code in repositories/ and the wiki — checks that the implementation respects the decisions (ADRs), the development standards and the component notes, and finds implementation choices never recorded. Total read-only: reports, does not correct. Use periodically, or when the user asks to check that the code is aligned with the wiki.
---

# Audit code ↔ wiki

User input: $ARGUMENTS

## 0. Input

- **What to audit**: a component (by name or code), a repository in `repositories/`, or all of them (from `$ARGUMENTS`, or ask the user). Repositories and their components are listed in `components` of `project.yaml`.
- If the repository does not exist or contains no code, say so and stop: this skill makes sense only when there is an implementation to check.

## 1. Access perimeter — BINDING ⛔

1. **TOTAL READ-ONLY**: you do not write, modify or delete anything — not in the code, not in the wiki, nowhere. You find and **report**; corrections are separate activities that the user decides.
2. Read **only**: the code to audit, `wiki/`, `project.yaml`, and the references of the development skills listed in `dev_skills`. No external knowledge.

## 2. Build the reference picture (from the wiki)

For every component to audit, collect **what must be true**:

1. the applicable **ADRs**: those of the component (`components/<repo>/decisions/`) and the cross-cutting ones (`decisions/`, especially the areas `ARCH` and `STD`), excluding the `superseded` ones;
2. the **component folder** (`components/<repo>/`): entry note, scope, choices, feature notes;
3. the **standards**: the references of the development skills that cover the component (`dev_skills`), and the bridge note of the standards;
4. the relevant cross-cutting notes (`architecture/`, `domain/` when the modules are active).

When the wiki says nothing about a component, say so in the report: **consistency cannot be checked against a truth that is not written** — and that is already a finding: the component is growing without recorded knowledge.

## 3. Check the code

Compare the implementation with the reference picture, rule by rule: structure and naming, prescribed and forbidden patterns, configuration, boundaries between components, contracts. Also check that the code **never points to the wiki** (no `ADR-*`, `Q-*`, `T-*` IDs, no names of people or companies in comments, documentation or configuration). Check what is **observable in the code** — do not speculate on what you cannot see (for example runtime behaviour): when a point cannot be verified statically, declare it as such.

## 4. Classify each divergence — three outcomes, and the user decides

| Outcome | Meaning | Follow-up (to report, not to run) |
|---|---|---|
| **(a) Non-conforming code** | The wiki is right: the implementation breaks a decision or a standard still valid | Development work: fix the code (cite file and line, and the rule broken, with the wikilink to the ADR or note) |
| **(b) Unrecorded choice** | The wiki is **silent**: the code contains an implementation choice that contradicts nothing but is written nowhere | Material for `/projectwright:record-decisions`: the knowledge must be recorded (propose the wording) |
| **(c) Wiki behind** | The code is right: the decision **changed in practice** and the wiki was not updated | Material for `/projectwright:record-decisions`: update ADRs (a superseded decision is superseded, not deleted) and notes — and, in cascade, the official documents behind will be reported |

**Arbitration rule — no source wins automatically, not even here**: when the code **contradicts a recorded rule**, you cannot know whether it is (a) or (c). **STOP and ask the user explicitly: "here, is the wiki or the code right?"** — one conflict at a time, presenting the **observable evidence** (what the ADR or note says and since when; what the code does and since when — commit dates are a legitimate clue) and, if useful, your hypothesis. The (a) or (c) classification is assigned **only by the user's answer**; the label "to arbitrate" is allowed in the report only when the user postpones the decision. Only (b) can be assigned by you, because there is no contradiction — and even there, in doubt between (b) and (c), ask.

## 5. Report

Fixed structure:

1. **Verdict on top**: `✅ Code aligned with the wiki` or `❌ N divergences` (plus any components that cannot be checked because the wiki says nothing about them);
2. **By component**: the divergences found, each with outcome (a)/(b)/(c) — or "to arbitrate" when waiting for the user — file and line, reference rule with wikilink;
3. **Final numbered list** ordered by severity: first violations of architectural decisions, then standards, then style;
4. **Suggested follow-ups**: what to fix in the code (a), what to record as new (b) and what to update in the wiki because superseded by the code (c) — without running anything.
