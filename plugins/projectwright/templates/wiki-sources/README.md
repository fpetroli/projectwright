# Ingestion cards — `wiki-sources/`

This folder holds the **ingestion cards**: one card per official document ingested into the wiki, plus the **ingestion log**. It sits next to `wiki/` and not inside it because its rules are the opposite of the wiki's: cards are **immutable** and only ingestion writes them, while the wiki keeps evolving.

> This file is provided by the `projectwright` framework. The general writing rules (frontmatter, names, links, IDs) are in the constitution, `wiki/README.md`; this file only adds what is specific to the cards.

**A card is not the official document.** It is an extract produced by the AI from the document: claims of one line each, with provenance and hash. The official documentation stays in its folder (`paths.official_docs` in `project.yaml`: `docs/` in the project, or a shared folder) and is never copied here.

## Structure

```
wiki-sources/
├── README.md                     ← this file
├── ingestion-log.csv             ← the DATA SOURCE of ingestion (see below)
├── minutes/                      ← one card per minutes document (source_kind: event)
├── technical-docs/<subfolder>/   ← cards of the technical reference documents
└── functional-docs/<subfolder>/  ← cards of the functional reference documents
```

The categories are those in `sources.categories` of `project.yaml` — kinds of documents, not folders the documentation must have: the structure of the documentation folder is the user's. A card goes in the category of its document — given by the first-level folder when it has the category's name, otherwise by the content — and mirrors the folders of the document, in *kebab-case* (lower case, spaces → `-`). Category folders are created with the first card.

## The ingestion log

`ingestion-log.csv` is **data, not a catalogue**: it holds what exists nowhere else — hash, result, integration state — and cannot live in the cards because they are immutable.

```csv
document,source_path,hash,ingested_on,result,card,integrated,note
```

| Column | Content |
|---|---|
| `document` | Readable name of the document |
| `source_path` | Path relative to the official documentation folder; for documentation inside a code repository, relative to the project root (`repositories/<repo>/docs/…`); for an **online source** (Confluence page, issue…), its link |
| `hash` | Hash of the file at ingestion time; for an online source, `version:<version>` as given by the source system (page version or last update) |
| `ingested_on` | Date of the ingestion (`YYYY-MM-DD`) |
| `result` | `ingested` or `ignored` |
| `card` | Name of the card (empty when `ignored`) |
| `integrated` | `yes`, `no` or `n/a` (`n/a` for ignored files) |
| `note` | Free text: the reason of an `ignored`, e.g. `attachment of <card>` |

- Rows are written only by the script `ingestion-diff.py` (`--record`, `--mark-integrated`), run by `/projectwright:ingest-sources` and `/projectwright:integrate-wiki`; never typed by hand.
- Only `/projectwright:integrate-wiki` changes the `integrated` column.
- Paths of the documentation folder that are never documentation can be excluded with `sources.exclude` in `project.yaml`.
- Online sources are recorded with `ingestion-diff.py --record-url`; the log itself is the list of the online sources to check again (`--remote`).
- A **modified** document gets its row updated (new hash and date) and `integrated` back to `no`.

## Rules of the cards

- **Immutable**: once written, a card is never edited. A new version of the document produces a revised card through `/projectwright:ingest-sources`, which explains in its flags what changed.
- **Only from the document**: everything in a card derives from the document it describes; no external or previous knowledge.
- **No links to wiki notes**: cards cite documents; it is the wiki notes that cite the cards (`source: "[[card-name]]"`).
- **Unique names**: the name of a card is unique across `wiki/` and `wiki-sources/`; on a collision the user is asked, nothing is overwritten.
- The structure of a card is in `templates/records/source-card.md` of the plugin.
