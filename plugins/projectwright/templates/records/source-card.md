---
title: <document name> — ingestion
type: source-card
status: informational
area: <CODE>
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: "<path of the document, relative to the official documentation folder>"
hash: <hash reported by ingestion-diff.py>
ingested_on: YYYY-MM-DD
source_kind: event               # event for minutes | reference for technical and functional documents
---

# <document name> — ingestion

<One or two lines: what document it is, its date, who attended or what it is for.>

**Attachments:** <N files cited by the document, their content already reported in it; omit the line when there are none>

**Extracted knowledge** (one claim per line, one atomic fact each):
- <fact, as the document states it>

**Decisions stated in the document:**
- <decision> (if none: "none")

**Open points stated in the document:**
- <open point> (if none: "none")

**Terms:**
- **<term>**: <meaning in the document> (if none: "none")

**Editor's notes:** (only when the document contains annotations added after the event; otherwise omit)
- <annotation, reported as the editor's knowledge>

**Flags:**
- <declared evolutions and refinements compared with previous cards; divergences and arbitrations; `⚠️ Document to update: …`; `⚠️ Divergence from the standard: …`; uncertain terms marked by the document; or "none">
