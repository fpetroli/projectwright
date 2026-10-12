---
title: Project status
type: dashboard
status: informational
area: PRJ
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: "derived view of the notes, the questions and the ingestion log"
related:
  - "[[knowledge-map]]"
  - "[[operating-assumptions]]"
---

# Project status

Derived picture of the project. **No fact lives only here**: every line points to the note that owns it. The hand-written parts are kept up to date by `/projectwright:integrate-wiki` and `/projectwright:record-decisions`; the lists are computed views.

For Claude, the same picture comes from `wiki-query.py dashboard` (in the `scripts/` folder of the plugin), which the start-of-session hook runs automatically.

## Where we are

- <phase of the project, with a link to the note that describes it>
- <state of each hot topic, with links to ADRs and notes>

## What blocks what

- <reasoned synthesis: which open question or external dependency stops which work, with links>

<!-- Bases view: open questions with gate red (project and components). -->

## Components

One line per component, pointing to its entry note.

- [[<repo>]] — <one line: state of the component>

## In progress

<!-- Bases view: tasks in progress (tasks.mode = wiki), or a pointer to the tracker (tasks.mode = tracker). -->

## Official documents to update

- <official documents found behind later decisions: which, on what, which ADR supersedes them>

## Knowledge queue

<!-- Bases view: ingestion cards not yet integrated. -->
