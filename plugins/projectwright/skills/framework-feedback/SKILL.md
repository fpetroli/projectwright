---
name: framework-feedback
description: Notes a friction with the projectwright framework while working — a skill that asked too much or too little, a rule that got in the way, something expected that did not happen, an idea — in an anonymous feedback file of this project, to bring to the framework later. Use when the user says something like "note for the framework", "this should work differently", or when the session showed a friction with the framework and the user agrees to note it.
---

# Note a feedback for the framework

User input: $ARGUMENTS (what happened, in the user's words)

This is the light way to tell the framework what does not work well, **without changing anything**. When the project actually changed a file of the framework, the right tool is `/projectwright:propose-improvement`, which carries the change and its reason; this skill only collects observations.

## 1. Understand the feedback

From `$ARGUMENTS` and the session, make clear — asking at most one question when something essential is missing:

- **what was being done** (the activity, the skill or rule involved);
- **what happened**;
- **what was expected**, or what would have helped;
- an **idea** for the framework, if the user has one.

## 2. Make it anonymous — BINDING ⛔

The file is brought to a public framework: write it so that it makes sense for **any** project and reveals nothing of this one — no names of the project, client, organisations or people, no domain details, no paths, no content of the wiki. "While ingesting a long technical specification, the skill asked to approve every card" — not "while ingesting the payment spec of <client>".

## 3. Write it

Append the entry to `<paths.utils>/projectwright-feedback.md` (default `utils/projectwright-feedback.md`), creating the file when missing with this head:

```markdown
# Feedback for projectwright

Observations collected while using the framework, to bring to the framework's maintainers. Anonymous: no names, no project details.

| Framework version | <framework.version of project.yaml> |
|---|---|
```

and one entry per feedback, in the user's language:

```markdown
## <date> — <short title>

- **Doing**: <activity, skill or rule involved>
- **Happened**: <what happened>
- **Expected**: <what was expected or would have helped>
- **Idea**: <the user's idea, or "—">
```

If an entry on the same friction already exists, add to it ("happened again: …") instead of writing a new one. Update the framework version in the head when it changed.

## 4. Close

Say in one line what was noted and where. When the file has several entries, remind the user that they can bring it to the framework (for example by opening an issue on the framework's repository, whose URL is `repository` in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, or by sending it to its maintainers). The file is not part of the wiki: it holds no fact or decision of the project.
