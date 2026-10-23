import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Applying, Board, Draft, Edit, Fields, Model, Pending, Selected, Task, TaskDetail, View } from '../types'

import { touchesWiki } from './paths'

// The pane reads the tasks from the projectwright scripts: the logic stays in
// Python, the mod only draws what wiki-query.py answers.
const PANE = 'projectwright-board'
const board = atom({ plugin: 'projectwright-board', key: 'board' } as const, { tasks: [] })
const EMPTY: Draft = { isOpen: false, title: '', priority: 'medium', notes: '' }
const draft = atom({ plugin: 'projectwright-board', key: 'draft' } as const, EMPTY)
const pending = atom({ plugin: 'projectwright-board', key: 'pending' } as const, [])
const selected = atom({ plugin: 'projectwright-board', key: 'selected' } as const, {} as Selected)
const NO_EDIT: Edit = { bodyChange: '' }
const edit = atom({ plugin: 'projectwright-board', key: 'edit' } as const, NO_EDIT)
const applying = atom({ plugin: 'projectwright-board', key: 'applying' } as const, {} as Applying)
const NO_VIEW: View = { expanded: [] }
const view = atom({ plugin: 'projectwright-board', key: 'view' } as const, NO_VIEW)

// What a board shows — columns, labels, colors, the fields of a card — is
// defined once in projectwright (assets/board-model.json), for board.html and
// this pane alike. The pane turns its color names into theme keys, so they
// follow the person's light or dark theme.
const MODEL = 'assets/board-model.json'
const COLOR: Record<string, string> = { blue: 'suggestion', red: 'error', gray: 'inactive', green: 'success', yellow: 'warning' }
const colorOf = (name?: string) => COLOR[name ?? ''] ?? 'text'
const columnOf = (model: Model, progress: string) =>
  model.columns.find(c => c.progress === progress) ?? { progress, label: progress, color: '' }
const priorityOf = (model: Model, value: string) => model.priorities.find(p => p.value === value)
// "a, b" as the list JSON prints a list field; the detail keeps it a list of links.
const namesIn = (v: unknown) => (Array.isArray(v) ? v.map(String) : String(v ?? '').split(','))
  .map(s => s.trim().replace(/^\[\[|\]\]$/g, '').replace(/\|.*$/, '')).filter(Boolean)
const idOf = (n: string) => /^(T-[A-Z0-9]+-\d+)/.exec(n)?.[1] ?? n

const now = () => new Date().toTimeString().slice(0, 5)

// The project root: the session's folder or the nearest one above it holding
// project.yaml, so the pane still finds the project when the session's working
// directory moves into a subfolder.
const findRoot = async ($: EngineInterface): Promise<string | undefined> => {
  let dir = await $.session.cwd()
  while (dir !== '') {
    if (await $.fs.exists(`${dir}/project.yaml`)) return dir
    const parent = dir.replace(/[\\/][^\\/]*$/, '')
    if (parent === dir) break
    dir = parent
  }
  return undefined
}

// The version a plugin's manifest declares, or undefined when it cannot be read.
const versionOf = async ($: EngineInterface, dir: string) => {
  try {
    const manifest = JSON.parse(await $.fs.read(`${dir}/.claude-plugin/plugin.json`)) as { version?: unknown }
    return typeof manifest.version === 'string' ? manifest.version : undefined
  } catch {
    return undefined
  }
}

// The projectwright plugin this board reads through. Its start-of-session hook
// writes where it is in .claude/.projectwright-plugin; the two plugins are
// released together, so the board works only with its own version.
const projectwright = async ($: EngineInterface, root: string): Promise<{ dir?: string; error?: string }> => {
  const marker = `${root}/.claude/.projectwright-plugin`
  if (!(await $.fs.exists(marker))) {
    return { error: 'The projectwright plugin is not running here: install it, or start a new session.' }
  }
  const dir = (await $.fs.read(marker)).trim()
  const wanted = await versionOf($, $.plugin.root)
  const found = await versionOf($, dir)
  if (wanted !== undefined && found !== wanted) {
    return { error: `projectwright-board ${wanted} needs projectwright ${wanted}; found ${found ?? 'an unknown version'}. ` +
      'Update the two plugins together.' }
  }
  return { dir }
}

// Runs a projectwright script. "python3" is the usual name; Windows often has
// only "python", and answers 9009 when "python3" is the Store's placeholder.
const runScript = async ($: EngineInterface, root: string, dir: string, script: string, args: string[]) => {
  let failure: unknown
  for (const python of ['python3', 'python']) {
    try {
      const ran = await $.process.run([python, `${dir}/scripts/${script}`, ...args, '--root', root], { cwd: root })
      if (ran.exitCode !== 9009) return ran
    } catch (err) {
      failure = err
    }
  }
  throw new Error(`Python not found (python3 or python): ${String(failure ?? 'no interpreter answered')}`)
}

const load = async ($: EngineInterface): Promise<Board> => {
  const root = await findRoot($)
  if (root === undefined) {
    return { tasks: [], error: 'Not a projectwright project.' }
  }
  try {
    const { dir, error } = await projectwright($, root)
    if (dir === undefined) return { tasks: [], error }
    let model: Model
    try {
      model = JSON.parse(await $.fs.read(`${dir}/${MODEL}`)) as Model
    } catch {
      return { tasks: [], error: `projectwright has no ${MODEL}: update the two plugins together.` }
    }
    const ran = await runScript($, root, dir, 'wiki-query.py', ['tasks', '--format', 'json'])
    if (ran.exitCode !== 0) return { tasks: [], error: ran.stderr.trim() || 'wiki-query failed.' }
    const tasks = JSON.parse(ran.stdout) as Task[]
    return { tasks, model, updated: now() }
  } catch (err) {
    return { tasks: [], error: String(err) }
  }
}

const name = (t: Task) => t.task.replace(/^\[\[|\]\]$/g, '')

// What a refresh compares: the tasks or the error, not the time it was read.
const sameBoard = (a: Board, b: Board) => a.error === b.error && JSON.stringify(a.tasks) === JSON.stringify(b.tasks) &&
  JSON.stringify(a.model) === JSON.stringify(b.model)

const refresh = async ($: EngineInterface) => {
  const next = await load($)
  // Unchanged, the pane keeps what it draws: a periodic check redraws nothing.
  if (!sameBoard(await read($, board), next)) await update($, board, () => next)
  // A request is done once a task it did not know about is in the wiki.
  const names = next.tasks.map(name)
  await update($, pending, list => (list ?? []).filter(p => names.every(n => p.known.includes(n))))
  // The task open in the pane follows the wiki too.
  const open = (await read($, selected)).name
  if (open) await openTask($, open)
}

// One task in full: its fields, body and links, as wiki-query.py answers them.
const loadDetail = async ($: EngineInterface, task: string): Promise<Selected> => {
  const root = await findRoot($)
  if (root === undefined) return { name: task, error: 'Not a projectwright project.' }
  try {
    const { dir, error } = await projectwright($, root)
    if (dir === undefined) return { name: task, error }
    const ran = await runScript($, root, dir, 'wiki-query.py', ['task', task, '--format', 'json'])
    if (ran.exitCode !== 0) return { name: task, error: ran.stderr.trim() || 'wiki-query failed.' }
    return { name: task, data: JSON.parse(ran.stdout) as TaskDetail }
  } catch (err) {
    return { name: task, error: String(err) }
  }
}

const openTask = async ($: EngineInterface, task: string) => {
  const shown = await loadDetail($, task)
  const before = await read($, selected)
  if (JSON.stringify(before) !== JSON.stringify(shown)) await update($, selected, () => shown)
  // Changes sent to Claude are applied once the task reads differently.
  const sent = await read($, applying)
  if (sent.name === task && shown.data && JSON.stringify(shown.data) !== sent.before) {
    await update($, applying, () => ({}))
  }
}

const closeTask = async ($: EngineInterface) => {
  await update($, edit, () => NO_EDIT)
  await update($, selected, () => ({}))
}

const FIELDS: (keyof Fields)[] = ['title', 'progress', 'priority', 'phase', 'assignee']

const fieldsOf = (d: TaskDetail): Fields => {
  const text = (key: string) => (typeof d[key] === 'string' ? (d[key] as string) : '')
  return { title: text('title'), progress: text('progress'), priority: text('priority'),
    phase: text('phase'), assignee: text('assignee') }
}

const changesOf = (form: Edit) =>
  FIELDS.filter(f => form.original && form.values && form.original[f] !== form.values[f].trim())

// The edit form gathers the changes; Claude applies them. The mod writes nothing.
const applyEdit = async ($: EngineInterface, form: Edit) => {
  const shown = await read($, selected)
  const changed = changesOf(form)
  const bodyChange = form.bodyChange.trim()
  if (!form.name || !form.original || !form.values || !shown.data) return
  if (changed.length === 0 && bodyChange === '') {
    $.ui.toast('board: nothing to change')
    return
  }
  const { id } = split({ task: `[[${form.name}]]`, progress: '', priority: '', phase: '', assignee: '' })
  const lines = changed.map(f => `- ${f}: "${form.original?.[f]}" → "${form.values?.[f].trim()}"`)
  await update($, applying, () => ({ name: form.name, sentAt: now(), sentMs: Date.now(), before: JSON.stringify(shown.data) }))
  await update($, edit, () => NO_EDIT)
  await askClaude($, `Update task ${id} (${form.name}) with /projectwright:manage-tasks.` +
    (lines.length > 0 ? `\nChange these fields:\n${lines.join('\n')}` : '') +
    (bodyChange ? `\nChange its body (goal, acceptance criteria, notes) as I describe: ${bodyChange}` : '') +
    '\nApply only these changes, following the wiki rules (updated, closed_on when it closes; ' +
    'if it becomes blocked and I did not say by what, ask me). Never rename the file.')
  $.ui.toast(`board: changes to ${id} sent to Claude`)
}

// "T-WEB-0004-checkout-page" → id "T-WEB-0004", and its title: the one in the
// wiki, or, for a link to a task not in the list, words from the file name.
const split = (t: Task) => {
  const m = /^(T-[A-Z0-9]+-\d+)-?(.*)$/.exec(name(t))
  const words = (m?.[2] ?? '').replace(/-/g, ' ')
  const fallback = words.charAt(0).toUpperCase() + words.slice(1)
  return { id: m?.[1] ?? name(t), title: t.title || fallback }
}

// One bar for the whole board: a segment per column, as long as its share.
const bar = (model: Model, tasks: Task[], width: number) =>
  model.columns.map(c => {
    const n = tasks.filter(t => t.progress === c.progress).length
    return { color: c.color, cells: n === 0 ? 0 : Math.max(1, Math.round((n / tasks.length) * width)) }
  }).filter(s => s.cells > 0)

// The columns shown: all of them, save those the model hides while empty.
const columnsShown = (model: Model, tasks: Task[]) => model.columns.filter(c =>
  !model.hide_when_empty.includes(c.progress) || tasks.some(t => t.progress === c.progress))

// The tasks of a column in the model's order: by ID, the history newest first
// and, unless expanded, only the latest few.
const columnTasks = (model: Model, tasks: Task[], progress: string, isExpanded: boolean) => {
  const items = tasks.filter(t => t.progress === progress)
  const isHistory = model.history.columns.includes(progress)
  const ordered = isHistory && model.history.newest_first ? [...items].reverse() : items
  const shown = isHistory && !isExpanded ? ordered.slice(0, model.history.shown) : ordered
  return { items: ordered, shown }
}

// The pane never writes the wiki. Whatever the person does in it becomes a
// request to Claude, which changes the wiki through the projectwright skills,
// with their rules and the lint; the pane then redraws from the new files.
const askClaude = async ($: EngineInterface, text: string) => {
  await $.prompt.submit({ text, asUser: true })
}

const createTask = async ($: EngineInterface, form: Draft) => {
  const title = form.title.trim()
  if (title === '') {
    $.ui.toast('board: the task needs a title')
    return
  }
  const notes = form.notes.trim()
  const known = (await read($, board)).tasks.map(name)
  await update($, pending, list => [...(list ?? []), { title, sentAt: now(), sentMs: Date.now(), known }])
  await update($, draft, () => EMPTY)
  await askClaude($, `Create a task in the wiki with /projectwright:manage-tasks: "${title}". ` +
    `Priority: ${form.priority}. ` +
    (notes ? `My notes on it: ${notes} ` : '') +
    'Infer goal, acceptance criteria and placement from the project; ask me only what you cannot infer.')
  $.ui.toast(`board: sent to Claude — "${title}"`)
}

// The person wants Claude to take up a task: to start it, review it, check one
// detail, or recall what was done on a closed one. Claude reads the wiki itself
// and reads the intent from what the person says next; it changes nothing alone.
const injectTask = async ($: EngineInterface, t: Task) => {
  const { id } = split(t)
  await askClaude($, `Bring task ${id} (${name(t)}) into context. ` +
    'Read its note in the wiki and what it links: decisions, questions, blocking tasks, the component notes; ' +
    'if it touches code, run the pre-code gate. ' +
    `Then tell me briefly what it is about and where it stands (progress: ${t.progress}). ` +
    'I may want to start it, review it, check one detail, or recall what was done on it: understand my intent from what I say. ' +
    'Do not change the wiki; if a change of its progress fits my intent, propose it and wait for my yes.')
  $.ui.toast(`board: ${id} sent to Claude`)
}

// How often the pane looks at the wiki by itself, for the changes made outside
// Claude (by hand, in an editor): the scripts run only when the pane is shown.
const POLL_MS = 30_000

const poll = async ($: EngineInterface) => {
  const panes = await $.ui.panes()
  if (panes.some(p => p.id === PANE && p.isShown)) await refresh($)
}

// A turn of Claude has ended: the requests the pane sent before it began and
// that are still not in the wiki get flagged, since Claude may be waiting for
// an answer, or may have stopped. The person can dismiss them.
let turnStartedMs = 0

const flagStale = async ($: EngineInterface) => {
  await update($, pending, list => (list ?? []).map(p => (p.sentMs <= turnStartedMs ? { ...p, isStale: true } : p)))
  await update($, applying, a => (a?.name && (a.sentMs ?? 0) <= turnStartedMs ? { ...a, isStale: true } : a ?? {}))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'board',
      description: 'Show the projectwright board beside the chat',
    })
    // The rest of the start first: projectwright's own hook says where it runs.
    const started = await next(e)
    await refresh($)
    void $.ui.open({ id: PANE, title: 'Board' })
    try {
      $.clock.every(POLL_MS, () => void poll($).catch(() => undefined))
    } catch {
      // no timers here (a host without them): the pane still refreshes on writes and on /board
    }

    return started
  })

  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) turnStartedMs = Date.now()
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (e.agentId === undefined) {
      await refresh($)
      await flagStale($)
    }
    return done
  }).catch(($, e, next) => next(e)) // the answer is never held up by the pane

  on('command.run', { command: 'board' }, async $ => {
    await refresh($)
    const opened = await $.ui.open({ id: PANE, title: 'Board' })
    const { tasks, model, error } = await read($, board)
    const surfaces = (await $.session.surfaces()).join(', ') || 'none'
    const pane = opened.isPlaced ? 'pane opened' : `pane not drawn (${opened.reason})`

    // The same list as text: the command's output reaches every surface,
    // the remote ones that draw no pane included.
    const lines = error || !model
      ? [error ?? 'The board has not read the wiki yet.']
      : model.columns.flatMap(c => {
          const group = tasks.filter(t => t.progress === c.progress)
          return group.length === 0
            ? []
            : [`● ${c.label} (${group.length})`,
                ...group.map(t => `   ${split(t).id} ${split(t).title}`.trimEnd())]
        })

    return { text: [`Board — ${pane}; surfaces: ${surfaces}`, ...lines].join('\n') }
  })

  on('tool.call', { tool: ['Write', 'Edit'] }, async ($, e, next) => {
    const ran = await next(e)
    const root = await findRoot($)
    if (root !== undefined && touchesWiki(e.file_path, root)) await refresh($)

    return ran
  }).catch(($, e, next) => next(e)) // a failed refresh never blocks the write

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const elements = $.ui.resolve(e)
    const { Box, Text, Button } = elements
    const { tasks, model, error, updated } = await read($, board)
    const form = await read($, draft)
    const sent = (await read($, pending)) ?? []
    const width = Math.max(10, e.props.bodyColumns - 2)

    if (error) return <Text color="error">{error}</Text>
    if (!model) return <Text dimColor>Reading the wiki…</Text>

    // A value of the model as a chip: its label on its color, in either theme.
    const chip = (label: string, color: string, key: string) => (
      <Text key={key} color={colorOf(color)} inverse> {label} </Text>
    )
    const priorityOptions = model.priorities.map(p => ({ value: p.value, label: p.label }))

    // The new-task form: closed, one button; open, title, priority, notes.
    // The mobile app has no text field or select: there the button is all.
    const Input = 'Input' in elements ? elements.Input : undefined
    const Select = 'Select' in elements ? elements.Select : undefined
    const setDraft = (change: Partial<Draft>) => void update($, draft, d => ({ ...(d ?? EMPTY), ...change }))
    const creator = !Input || !Select ? undefined : !form.isOpen ? (
      <Box marginBottom={1}>
        <Button key="open-form" hotkey="n" variant="primary"
          onPress={() => setDraft({ isOpen: true })}>+ New task</Button>
      </Box>
    ) : (
      <Box key="form" flexDirection="column" borderStyle="round" borderColor="claude"
        paddingX={1} marginBottom={1}>
        <Text bold color="claude">New task</Text>
        <Input key="title" label="Title" placeholder="what has to be done" value={form.title} autoFocus
          onInput={title => setDraft({ title })}
          onSubmit={title => void createTask($, { ...form, title })} />
        <Select key="priority" label="Priority" value={form.priority} options={priorityOptions}
          onSelect={priority => setDraft({ priority })} />
        <Input key="notes" label="Notes" placeholder="optional: context for Claude" rows={2}
          value={form.notes} onInput={notes => setDraft({ notes })}
          onSubmit={notes => void createTask($, { ...form, notes })} />
        <Box flexDirection="row" gap={1}>
          <Button key="create" variant="primary" onPress={() => void createTask($, form)}>
            Ask Claude to create it
          </Button>
          <Button key="cancel" role="dismiss" onPress={() => void update($, draft, () => EMPTY)}>
            Cancel
          </Button>
        </Box>
        <Text dimColor wrap="wrap">Claude writes the task with /projectwright:manage-tasks.</Text>
      </Box>
    )

    // Requests on their way: shown until the task is in the wiki, flagged when
    // a turn of Claude ended without it, dismissed with ✕.
    const waiting = sent.length > 0 && (
      <Box flexDirection="column" marginBottom={1}>
        {sent.map((p, i) => (
          <Box key={`pending-${p.sentMs}-${i}`} flexDirection="row" justifyContent="space-between" gap={1}>
            <Box flexShrink={1}>
              {p.isStale
                ? <Text color="warning" wrap="truncate-end">◌ “{p.title}” is not in the wiki yet: Claude may be waiting for you · {p.sentAt}</Text>
                : <Text color="claude" wrap="truncate-end">◌ Claude is adding “{p.title}” · {p.sentAt}</Text>}
            </Box>
            <Button key={`dismiss-pending-${p.sentMs}-${i}`} dimColor
              onPress={() => void update($, pending, list => (list ?? []).filter(x => x.sentMs !== p.sentMs))}>
              ✕
            </Button>
          </Box>
        ))}
      </Box>
    )

    const done = tasks.filter(t => t.progress === 'done').length
    const open = tasks.filter(t => t.progress !== 'done' && t.progress !== 'cancelled').length
    const blocked = tasks.filter(t => t.progress === 'blocked').length

    // Every task, open or closed, can be brought into Claude's context.
    const inject = (t: Task) => (
      <Button key={`inject-${name(t)}`} dimColor onPress={() => void injectTask($, t)}>⇢</Button>
    )

    // The detail of a task, in place of the list: fields, body, links.
    const shown = await read($, selected)
    if (shown.name) {
      const t = tasks.find(x => name(x) === shown.name) ??
        { task: `[[${shown.name}]]`, progress: '', priority: '', phase: '', assignee: '' }
      const d = shown.data
      const { id } = split(t)
      const field = (key: string) => (d && typeof d[key] === 'string' ? (d[key] as string) : '')
      // One property of the model, as board.html draws it beside the task.
      const property = (f: string) => {
        const progress = field('progress') || t.progress
        const priority = priorityOf(model, field('priority') || t.priority)
        const blockers = namesIn(d?.blocked_by ?? t.blocked_by)
        const value = f === 'progress' ? (progress && chip(columnOf(model, progress).label, columnOf(model, progress).color, 'v'))
          : f === 'priority' ? (priority && chip(priority.label, priority.color, 'v'))
          : f === 'blocked_by' ? (blockers.length > 0 && <Text key="v" color="error">{blockers.map(idOf).join(', ')}</Text>)
          : (field(f) && <Text key="v" wrap="wrap">{field(f)}</Text>)
        if (!value) return undefined
        return (
          <Box key={`prop-${f}`} flexDirection="row" gap={1}>
            <Box width={12} flexShrink={0}><Text color="subtle">{model.fields[f] ?? f}</Text></Box>
            <Box flexShrink={1}>{value}</Box>
          </Box>
        )
      }
      const Markdown = 'Markdown' in elements ? elements.Markdown : undefined
      // The note's own heading repeats the title drawn above; wikilinks read as names.
      const body = (d?.body ?? '').replace(/^# .*\n+/, '').replace(/\[\[([^\]|]+)(\|[^\]]*)?\]\]/g, '$1')
      const tasksLinked = (d?.links ?? []).filter(l => /^T-[A-Z0-9]+-\d+/.test(l))
      const otherLinks = (d?.links ?? []).filter(l => !tasksLinked.includes(l))

      // The edit form, in place of the detail; the mobile app has no field to type in.
      const Input = 'Input' in elements ? elements.Input : undefined
      const Select = 'Select' in elements ? elements.Select : undefined
      const form = await read($, edit)
      const sent = await read($, applying)
      const canEdit = Boolean(Input && Select && d)
      if (Input && Select && d && form.name === shown.name && form.values) {
        const values = form.values
        const set = (change: Partial<Fields>) =>
          void update($, edit, f => ({ ...(f ?? NO_EDIT), values: { ...values, ...(f?.values ?? {}), ...change } }))
        const changed = changesOf(form)
        const summary = [...changed, ...(form.bodyChange.trim() ? ['body'] : [])]
        const text = (key: keyof Fields, label: string) => (
          <Input key={`edit-${key}`} label={label} value={values[key]} onInput={v => set({ [key]: v })}
            onSubmit={v => void applyEdit($, { ...form, values: { ...values, [key]: v } })} />
        )
        return (
          <Box flexDirection="column">
            <Box flexDirection="row" justifyContent="space-between" marginBottom={1}>
              <Button key="back" hotkey="b" onPress={() => void closeTask($)}>← Back</Button>
              {inject(t)}
            </Box>
            <Box flexDirection="column" borderStyle="round" borderColor="claude" paddingX={1}>
              <Text bold color="claude">✎ Editing {id}</Text>
              {text('title', 'Title')}
              <Select key="edit-progress" label="Progress" value={values.progress}
                options={model.columns.map(c => ({ value: c.progress, label: c.label }))}
                onSelect={progress => set({ progress })} />
              <Select key="edit-priority" label="Priority" value={values.priority} options={priorityOptions}
                onSelect={priority => set({ priority })} />
              {text('phase', 'Phase')}
              {text('assignee', 'Assignee (a role)')}
              <Input key="edit-body" label="Body" rows={3} value={form.bodyChange}
                placeholder="what to change in goal, criteria, notes (optional)"
                onInput={bodyChange => void update($, edit, f => ({ ...(f ?? NO_EDIT), bodyChange }))}
                onSubmit={bodyChange => void applyEdit($, { ...form, bodyChange })} />
              <Text color={summary.length > 0 ? 'warning' : 'subtle'}>
                {summary.length === 0 ? 'No changes yet' : `${summary.length} change(s): ${summary.join(', ')}`}
              </Text>
              <Box flexDirection="row" gap={1}>
                <Button key="apply" variant="primary" onPress={() => void applyEdit($, form)}>
                  Ask Claude to apply
                </Button>
                <Button key="cancel-edit" role="dismiss" onPress={() => void update($, edit, () => NO_EDIT)}>
                  Cancel
                </Button>
              </Box>
              <Text dimColor wrap="wrap">Claude applies the changes with /projectwright:manage-tasks.</Text>
            </Box>
          </Box>
        )
      }

      return (
        <Box flexDirection="column">
          <Box flexDirection="row" justifyContent="space-between" marginBottom={1}>
            <Button key="back" hotkey="b" onPress={() => void closeTask($)}>← Back</Button>
            <Box flexDirection="row" gap={1}>
              {canEdit && d && (
                <Button key="edit" hotkey="e" onPress={() => void update($, edit, () =>
                  ({ name: shown.name, original: fieldsOf(d), values: fieldsOf(d), bodyChange: '' }))}>
                  ✎ Edit
                </Button>
              )}
              {inject(t)}
            </Box>
          </Box>
          {sent.name === shown.name && (
            <Box flexDirection="row" justifyContent="space-between" gap={1}>
              <Box flexShrink={1}>
                {sent.isStale
                  ? <Text color="warning" wrap="truncate-end">◌ Your changes are not in the wiki yet: Claude may be waiting for you · {sent.sentAt}</Text>
                  : <Text color="claude" wrap="truncate-end">◌ Claude is applying your changes · {sent.sentAt}</Text>}
              </Box>
              <Button key="dismiss-applying" dimColor onPress={() => void update($, applying, () => ({}))}>✕</Button>
            </Box>
          )}
          <Text dimColor>{id}</Text>
          <Text bold wrap="wrap">{field('title') || split(t).title}</Text>
          <Box flexDirection="column" marginTop={1}>
            {model.detail.map(property)}
          </Box>
          <Text dimColor>{'─'.repeat(width)}</Text>
          {shown.error && <Text color="error" wrap="wrap">{shown.error}</Text>}
          {!d && !shown.error && <Text dimColor>Loading…</Text>}
          {d && (Markdown ? <Markdown key="body" text={body} /> : <Text wrap="wrap">{body}</Text>)}
          {tasksLinked.length > 0 && (
            <Box flexDirection="column" marginTop={1}>
              <Text bold>Linked tasks</Text>
              {tasksLinked.map(l => (
                <Button key={`link-${l}`} plain onPress={() => void openTask($, l)}>
                  → <Text bold>{split({ ...t, task: `[[${l}]]` }).id}</Text> {split({ ...t, task: `[[${l}]]` }).title}
                </Button>
              ))}
            </Box>
          )}
          {otherLinks.length > 0 && (
            <Text color="subtle" wrap="wrap">See also: {otherLinks.join(' · ')}</Text>
          )}
          {d && <Text dimColor>{d.path}</Text>}
        </Box>
      )
    }

    // Pressing a task's title opens its detail.
    const opener = (t: Task, children: unknown) => (
      <Button key={`open-${name(t)}`} plain onPress={() => void openTask($, name(t))}>
        {children as string}
      </Button>
    )

    // One field of a card, as the model lists them and board.html draws them.
    const cardField = (t: Task, f: string) => {
      const priority = priorityOf(model, t.priority)
      const blockers = namesIn(t.blocked_by)
      if (f === 'id') return <Text key={f} dimColor>{split(t).id}</Text>
      if (f === 'priority') return priority && chip(priority.label, priority.color, f)
      if (f === 'assignee') return t.assignee && <Text key={f} color="subtle">@{t.assignee}</Text>
      if (f === 'blocked_by') return blockers.length > 0 && chip(`Blocked by ${blockers.map(idOf).join(', ')}`, 'red', f)
      const value = t[f as keyof Task]
      return value && <Text key={f} color="subtle">{String(value)}</Text>
    }

    // A task: its title, then the other fields of the card, in its column's frame.
    const card = (t: Task, color: string) => (
      <Box key={name(t)} flexDirection="column" borderStyle="round" borderColor={colorOf(color)} paddingX={1}>
        <Box flexDirection="row" justifyContent="space-between" gap={1}>
          <Box flexShrink={1}>
            {opener(t, <Text bold strikethrough={t.progress === 'cancelled'} wrap="wrap">{split(t).title}</Text>)}
          </Box>
          {inject(t)}
        </Box>
        <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
          {model.card.filter(f => f !== 'title').map(f => cardField(t, f))}
        </Box>
      </Box>
    )

    // One column at a time: the columns as tabs with their count, a digit for each.
    const columns = columnsShown(model, tasks)
    const shownView = await read($, view)
    const current = columns.find(c => c.progress === shownView.column) ??
      columns.find(c => tasks.some(t => t.progress === c.progress)) ?? columns[0]
    const tabs = (
      <Box flexDirection="row" flexWrap="wrap" columnGap={2} marginBottom={1}>
        {columns.map((c, i) => {
          const n = tasks.filter(t => t.progress === c.progress).length
          return (
            <Button key={`column-${c.progress}`} plain hotkey={i < 9 ? String(i + 1) : undefined}
              onPress={() => void update($, view, v => ({ ...(v ?? NO_VIEW), column: c.progress }))}>
              {c.progress === current?.progress
                ? <Text color={colorOf(c.color)} inverse bold> ● {c.label} {n} </Text>
                : <Text color={colorOf(c.color)}>{c.label} <Text dimColor>{n}</Text></Text>}
            </Button>
          )
        })}
      </Box>
    )
    const isExpanded = current !== undefined && shownView.expanded.includes(current.progress)
    const group = current ? columnTasks(model, tasks, current.progress, isExpanded) : { items: [], shown: [] }

    return (
      <Box flexDirection="column">
        {creator}
        {waiting}
        {tasks.length === 0 ? <Text dimColor>No tasks in the wiki.</Text> : (
          <Box flexDirection="column">
            <Box flexDirection="row" justifyContent="space-between">
              <Text>
                <Text bold>{open}</Text> open
                {blocked > 0 && <Text color="error"> · {blocked} blocked</Text>}
              </Text>
              <Text color="success">{done}/{tasks.length} done</Text>
            </Box>
            <Box flexDirection="row" marginBottom={1}>
              {bar(model, tasks, width).map(s => (
                <Text color={colorOf(s.color)}>{'━'.repeat(s.cells)}</Text>
              ))}
            </Box>
            {tabs}
            {group.items.length === 0 && <Text dimColor>No tasks in {current?.label ?? 'this column'}.</Text>}
            {group.shown.map(t => card(t, current?.color ?? ''))}
            {group.shown.length < group.items.length && (
              <Button key="more" dimColor plain
                onPress={() => void update($, view, v => ({ ...(v ?? NO_VIEW), expanded: [...(v?.expanded ?? []), current?.progress ?? ''] }))}>
                + {group.items.length - group.shown.length} more
              </Button>
            )}
          </Box>
        )}
        <Text dimColor>{updated ? `updated ${updated} · ` : ''}1–{Math.min(columns.length, 9)} column · n new task · /board refresh</Text>
      </Box>
    )
  })
}
