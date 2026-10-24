---
name: upgrade
description: Guided upgrade of the projectwright framework in this project — gets the new version, shows what changes, replaces the framework files the project did not change, merges the ones it changed (three-way), lets the user decide every conflict, applies the upgrade notes of the CHANGELOG (configuration, translated notes, data), then closes with the lock, an ADR-MET and the git commands. Use when the user asks to upgrade the framework, or when the start-of-session check says the plugin is newer than the project.
---

# Upgrade the framework

User input: $ARGUMENTS (optional: the target version, or the folder of the new version of the plugin)

The project records the version it was set up or last upgraded with in the lock file `.claude/projectwright.lock.json` (`version`, and `plugin`: `installed` or `in-project`). Every step that is mechanical is done by `framework.py`; you explain, ask and record. **Never upgrade without the user's yes on the plan** (§3), and **never decide a conflict alone** (§5).

## 1. Where the project stands

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/framework.py" check
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki-query.py" deviations
```

The first gives the running plugin and its version; the lock gives the project's version. The second lists the framework files changed in this project, with the ADRs that motivate them: they are what the upgrade must preserve. If there are changes without an ADR, record them first (as `/projectwright:record-decisions` §6 does), so that their reason is not lost in the merge.

## 2. Get the new version

**Plugin installed** (`plugin: installed`):

- If the running plugin is already newer than the project (the start-of-session check said so), the new version is the running plugin: go to §3 without `--from`.
- Otherwise, update it — with the user's yes — and restart: `claude plugin marketplace update projectwright`, then `claude plugin update projectwright@projectwright --scope project` — and, when the project also has the optional board installed (`projectwright-board@projectwright` in `claude plugin list`), `claude plugin update projectwright-board@projectwright --scope project` too: the two plugins are released together, with the same version. Tell the user to **restart Claude Code** and run `/projectwright:upgrade` again: the skills and hooks of the new version must be the ones running. Stop here.

**Plugin copied into the project** (`plugin: in-project`): the new version is a folder with the new plugin, given with `--from`:

- the folder the user names (for example a local clone of the framework repository: `<clone>/plugins/projectwright`);
- otherwise the framework repository — its URL is `repository` in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`: list the versions with `git ls-remote --tags <url>`, propose the latest `vX.Y.Z` (or the one in `$ARGUMENTS`), and clone it **outside the project**, in a temporary folder: `git clone --depth 1 --branch vX.Y.Z <url> <temporary folder>`; the plugin is `<temporary folder>/plugins/projectwright`.

A version lower than or equal to the project's is not an upgrade: say so and stop.

**Which `framework.py` to run.** From here on, `<new>` is the folder of the new version: the running plugin (`${CLAUDE_PLUGIN_ROOT}`) when it is installed, the `--from` folder when the plugin is copied. Always run **`python3 "<new>/scripts/framework.py"`**: the copy in the project is the old version until the upgrade is over, and one of its own files may be in conflict.

**Follow the new version's own skill.** As soon as `<new>` is there, read `<new>/skills/upgrade/SKILL.md`: when it differs from this one, follow it from here on — it knows the upgrade notes, the files and the questions of the version you are going to. This skill is the one of the version the project has, which may be older.

**Original copy.** The three-way merge needs the framework files as they were at the current version, saved in `.claude/.projectwright-original/` when the framework was applied. It is not versioned: on another computer it may be missing. If it is, get the current version as above (tag of the project's version) and pass it with `--base-plugin <folder>`.

## 3. What changes — the plan

1. **The CHANGELOG** of the new version (`CHANGELOG.md` in its plugin folder): read the entries after the project's version up to the new one, and tell the user in a few lines what each brings. Point out the entries that touch files this project changed (§1). When the project's version is a development version (`0.2.0-dev`), the entry of the version it goes to (`0.2.0`) also lists what the project already has: say so, and tell the user what really changes from the plan (2), which compares the files.
2. **The plan**, which changes nothing:
   ```
   python3 "<new>/scripts/framework.py" upgrade [--from <folder>] [--base-plugin <folder>]
   ```
   For every framework file: `REPLACE` (not changed in the project: takes the new version), `ADD` / `REMOVE` (new or removed in the new version), `KEEP` (changed by the project, untouched by the new version: the project's version stays), `MERGE` (changed by both in different places: merged automatically), `CONFLICT` (changed by both in the same places, or a case that needs a choice).
3. **The upgrade notes in the plan**: read now the upgrade notes of every version crossed (§6) and put in the plan what they will do — the configuration questions to ask, the translated notes to adapt, the lines to add (for example to `.gitignore`), and the data to convert with its own plan (for example `python3 "<new>/scripts/framework.py" renumber-tasks --plan`, which writes nothing: show its table old → new).
4. **The board**, when the project copies it in `.claude/skills/projectwright-board/`: the plan ends with a `Board:` line. `TRACKED` means its files are in the plan like those of the plugin, against the board released beside the new version (`<new>/../projectwright-board`): what the project changed in the board is kept and merged, and a conflict is decided like any other. `REPLACE` (or `SAME`) means a copy made before the board was tracked: it is replaced whole, once, and tracked from then on — say it, and say that a change the project made to that copy would be lost (check `framework.py diff` first if the user may have changed it). `KEEP` means the new version has no board beside it (for example a folder holding only `projectwright`): the board stays at its version, and it works only with a `projectwright` of the same version.
5. Show the user the whole plan in short — how many files per action, every `MERGE` and `CONFLICT` by name with its reason, and the upgrade notes with their effects — and ask **one yes** for all of it. After that yes, ask again only where the user has something to decide: each conflict (§5), the answers to the configuration questions (§6), a change to a task that the lint reveals (proposed, as the constitution wants for tasks), and the board beside the chat (§7). Everything else — files, lines, data already shown in the plan, the closing — goes on without asking.

## 4. Apply

```
python3 "<new>/scripts/framework.py" upgrade [--from <folder>] [--base-plugin <folder>] --apply
```

Files replaced, added, removed and merged are written into the project; **without conflicts the upgrade closes by itself** (it rewrites the lock with the originals of the new version). For the root `CLAUDE.md` only the framework part is touched: its "Project-specific instructions" section is kept as it is. Conflicts are **not** written into the project: they are set aside in `.claude/.projectwright-upgrade/<file>` (the merge with the markers `<<<<<<< this project` / `=======` / `>>>>>>> new version`, or the project's version when no merge was possible) with `<file>.new` beside it (the new version).

## 5. Conflicts — the user decides

For each conflict, one at a time:

1. Read the set-aside file and its `.new`, and the ADR that motivates the project's change (§1).
2. Show the user, briefly and concretely, **what the project changed and why**, **what the new version changes**, and propose a resolution — usually the new version with the project's change applied on top, when the change still makes sense; say it when the new version already covers the need (then the deviation can end, and its ADR is superseded).
3. Write the version the user chooses **into the project file** (for `CLAUDE.md`, only the part before "Project-specific instructions"), without conflict markers, then:
   ```
   python3 "<new>/scripts/framework.py" resolved <file>
   ```

## 6. Upgrade notes — what is not a framework file

Some changes cannot be merged as files, because they live in the project's own content. Apply the **upgrade notes** of every version between the project's and the new one, as the plan (§3) showed them:

- **configuration**: new keys of `project.yaml` — ask the user the questions they need, propose the default, write the answers keeping the comments;
- **notes created from templates and translated** (dashboard, `team-and-roles.md`, roadmaps, `development-workflow.md`): bring the change into them **in the project language**, without touching their content;
- **data**: a change of the wiki's schema — convert the records as the notes say (the conversion the plan showed), then let the lint confirm. A change the lint then asks for on a task (for example a task left in `todo` with an open blocker) is proposed to the user, never made alone.

## 7. Close

1. In `project.yaml`, set `framework.version` to the new version (keep the comment).
2. If there were conflicts, close the upgrade now — it refuses while some are open:
   ```
   python3 "<new>/scripts/framework.py" lock --from "<new>"
   ```
   (`--from`: the originals are the files of the new version, not the project's copy with its changes).
3. **The board beside the chat**, at the upgrade that brings it — the project comes from a version before 0.2.0 —, when `tasks.mode` is `wiki` and the board is neither installed (`projectwright-board@projectwright` in `claude plugin list`) nor copied (`.claude/skills/projectwright-board/`): tell the user in two lines that the optional plugin `projectwright-board` shows the tasks, the proposals of Claude and their reminders in a pane beside the chat — the same as `board.html`, but where they can answer — and that it is built on an early-access API of Claude Code, then **ask** whether to install it, and wait for the answer before the `ADR-MET`, which records it. On a yes, give the command (`claude plugin install projectwright-board@projectwright --scope project`, then a new session; it works with a copied `projectwright` too) — or, when the user prefers to copy it like `projectwright`, copy `<new>/../projectwright-board` into `.claude/skills/projectwright-board/` and add it to the lock with `python3 "<new>/scripts/framework.py" lock --add .claude/skills/projectwright-board`, so that its changes are tracked. The later upgrades do not propose it again.
4. Run `python3 "<new>/scripts/wiki-lint.py"` and fix any violation.
5. Record an **`ADR-MET`**: "Framework upgraded to <version>", with the versions crossed, the conflicts and how they were resolved, the upgrade notes applied, and the deviations that stay. When the new version includes a change this project had proposed, set `upstream: accepted` in its deviation ADR; when a deviation ended because the new version covers it, supersede its ADR with this one.
6. Summary for the user: what changed in practice, the deviations that stay, and — if the project folder is versioned — the ready-to-paste git commands (commits and pushes are run by the user). With the plugin copied into the project, remind them to run `/reload-plugins`, or to restart Claude Code, so that the new skills and hooks are loaded. Delete the temporary folder of §2, if you made one; when the deletion is refused (for example by the permissions of Claude Code), give the user the ready-to-paste command to delete it, with its absolute path.
