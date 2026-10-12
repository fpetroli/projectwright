---
title: Development workflow
type: note
status: decided
area: STD
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: "<card, ADR or working session the workflow comes from>"
related: []
---

# Development workflow

How the team takes a change from a branch to the main branch: branches, commits, merge requests, review and merge. Claude follows it whenever it prepares git commands or the text of a merge request; **commits, pushes and merge requests are always run by people** (root `CLAUDE.md`). The basic settings — main branch, commit convention, required scope — are in the `git` section of `project.yaml` and are not repeated here.

Branches, commit messages and merge requests belong to the delivered repositories: they **never contain IDs of the wiki** (`ADR-…`, `Q-…`, `T-…`) nor names of people (constitution, rule 11). They may carry the issue key of the external tracker, when there is one; a task of the wiki records its commits, not the other way round.

Created from the plugin template when the team's workflow is first known (setup, a repository's contributing guide, a decision); a change to it is a decision (`ADR` in the `STD` area) and this note is updated. Delete the sections that do not apply; a placeholder nobody can fill yet stays as it is.

## Branches

| Kind of work | Branch name | Created from |
|---|---|---|
| <feature> | <`feature/<issue-key>-<short-description>`, or `feature/<short-description>` without a tracker> | <main branch> |
| <fix> | <`fix/<issue-key>-<short-description>`> | <main branch> |

## Commits

<What the convention of `project.yaml` does not say: for example the issue key of the tracker in the footer (`Refs: <ISSUE-KEY>`), one commit per logical change, language of the messages.>

## Merge requests

- **When**: <for example when the acceptance criteria of the task are met and the tests pass>.
- **Target branch**: <main branch, or a release branch>.
- **Title**: <for example the same form as the commit messages>.
- **Description**: <the sections it must have — what changes, why, how to test, link to the issue of the tracker if there is one>.
- **Checklist before opening**: <tests, lint, documentation, no secrets>.
- **Reviewers**: <by role, never by name — for example "the architecture lead for changes to the data model">.
- **Labels and other fields**: <if the team uses them>.

## Review and merge

- **Approvals needed**: <number and roles>.
- **Merge method**: <merge commit, squash or rebase>; <delete the branch after the merge or not>.
- **After the merge**: <for example move the task to done and record the commit in its `commits` field, update the changelog>.

## Differences between repositories

<Only when a repository works differently from the rest: repository → what changes.>
