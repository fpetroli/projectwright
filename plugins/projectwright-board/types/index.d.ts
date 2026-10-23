// One task as `wiki-query.py tasks --format json` prints it.
export type Task = {
  task: string
  progress: string
  priority: string
  phase: string
  assignee: string
  title?: string
  id?: string
  updated?: string
  closed_on?: string
  blocked_by?: string
}

// What a board shows, as projectwright's assets/board-model.json defines it
// for board.html and the pane alike.
export type Model = {
  columns: { progress: string; label: string; color: string }[]
  hide_when_empty: string[]
  history: { columns: string[]; shown: number; newest_first: boolean }
  priorities: { value: string; label: string; color: string }[]
  card: string[]
  table: string[]
  detail: string[]
  fields: Record<string, string>
}

// A change to the tasks Claude proposes, as `proposals.py list --format json` prints it.
export type Proposal = {
  id: string
  kind: string
  task?: string
  summary: string
  why?: string
  items?: { title?: string; priority?: string; progress?: string; phase?: string; goal?: string }[]
  changes?: Record<string, unknown>
  consolidation?: string
  status: string
  comment?: string
  replaces?: string
}

// A reminder of the person, as `reminders.py list --format json` prints it.
export type Reminder = { id: string; text: string; due?: string; created?: string; done_on?: string }

// What the pane draws: the tasks, the model, the open proposals and the reminders, or why there are none to show.
export type Board = {
  tasks: Task[]; model?: Model; proposals?: Proposal[]; reminders?: Reminder[]; error?: string; updated?: string
}

// The new-reminder form, kept while the person fills it in.
export type ReminderDraft = { isOpen: boolean; text: string; due: string }

// Proposals accepted from the pane and not yet applied by Claude.
export type Accepting = { id: string; sentAt: string; sentMs: number; isStale?: boolean }

// The comment being written on a proposal.
export type Commenting = { id?: string; text: string }

// How the pane shows the columns: the view chosen by hand (otherwise the one the
// width allows), the groups of the list opened or closed against their default,
// and the history columns shown in full.
export type View = { mode?: 'board' | 'list'; toggled: string[]; expanded: string[] }

// The new-task form, kept while the person fills it in.
export type Draft = { isOpen: boolean; title: string; priority: string; notes: string }

// A request sent to Claude and not yet seen in the wiki: `sentMs` when it
// left, `isStale` once a turn of Claude ended without it in the wiki.
export type Pending = { title: string; sentAt: string; sentMs: number; known: string[]; isStale?: boolean }

// One task in full, as `wiki-query.py task <name> --format json` prints it.
export type TaskDetail = {
  name: string
  path: string
  body: string
  links: string[]
  component: string | null
  [field: string]: unknown
}

// The task open in the pane: none, loading, loaded, or why it could not load.
export type Selected = { name?: string; data?: TaskDetail; error?: string }

// The fields of a task the edit form changes.
export type Fields = { title: string; progress: string; priority: string; phase: string; assignee: string }

// The edit form of the open task: the values in the wiki, the ones typed, and
// the change to its body said in words.
export type Edit = { name?: string; original?: Fields; values?: Fields; bodyChange: string }

// Changes sent to Claude and not yet seen in the wiki: `before` is the task as
// it was read when they were sent.
export type Applying = { name?: string; sentAt?: string; sentMs?: number; before?: string; isStale?: boolean }

declare module 'claude-code' {
  interface PluginState {
    'projectwright-board': {
      board: Board; draft: Draft; pending: Pending[]; selected: Selected; edit: Edit; applying: Applying; view: View
      accepting: Accepting[]; commenting: Commenting; reminderDraft: ReminderDraft
    }
  }
}
