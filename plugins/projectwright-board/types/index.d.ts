// One task as `wiki-query.py tasks --format json` prints it.
export type Task = {
  task: string
  progress: string
  priority: string
  phase: string
  assignee: string
  title?: string
}

// What the pane draws: the tasks, or why there are none to show.
export type Board = { tasks: Task[]; error?: string; updated?: string }

// The new-task form, kept while the person fills it in.
export type Draft = { isOpen: boolean; title: string; priority: string; notes: string }

// A request sent to Claude and not yet seen in the wiki.
export type Pending = { title: string; sentAt: string; known: string[] }

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
export type Applying = { name?: string; sentAt?: string; before?: string }

declare module 'claude-code' {
  interface PluginState {
    'projectwright-board': {
      board: Board; draft: Draft; pending: Pending[]; selected: Selected; edit: Edit; applying: Applying
    }
  }
}
