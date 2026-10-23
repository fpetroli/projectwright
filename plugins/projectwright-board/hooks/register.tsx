import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Applying, Board, Draft, Edit, Fields, Pending, Selected, Task, TaskDetail } from '../types'

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

// Columns of the pane, in the order a task moves through them. Colors are
// theme keys, so they follow the person's light or dark theme.
const COLUMNS = ['in-progress', 'blocked', 'todo', 'done', 'cancelled']
const STATE: Record<string, { label: string; mark: string; color: string }> = {
  'in-progress': { label: 'In progress', mark: '▶', color: 'suggestion' },
  blocked: { label: 'Blocked', mark: '■', color: 'error' },
  todo: { label: 'To do', mark: '○', color: 'text' },
  done: { label: 'Done', mark: '✓', color: 'success' },
  cancelled: { label: 'Cancelled', mark: '✗', color: 'inactive' },
}
const MARK = (progress: string) => STATE[progress]?.mark ?? '·'
const PRIORITY: Record<string, { mark: string; color: string }> = {
  high: { mark: '▲ high', color: 'error' },
  medium: { mark: '● medium', color: 'warning' },
  low: { mark: '▽ low', color: 'subtle' },
}
// Tasks being worked on get a card; the others a single row.
const FOCUS = ['in-progress', 'blocked']
// Done and cancelled tasks are history: the pane shows only the latest few.
const HISTORY = 3

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
    const ran = await runScript($, root, dir, 'wiki-query.py', ['tasks', '--format', 'json'])
    if (ran.exitCode !== 0) return { tasks: [], error: ran.stderr.trim() || 'wiki-query failed.' }
    const tasks = JSON.parse(ran.stdout) as Task[]
    return { tasks, updated: now() }
  } catch (err) {
    return { tasks: [], error: String(err) }
  }
}

const name = (t: Task) => t.task.replace(/^\[\[|\]\]$/g, '')

// What a refresh compares: the tasks or the error, not the time it was read.
const sameBoard = (a: Board, b: Board) => a.error === b.error && JSON.stringify(a.tasks) === JSON.stringify(b.tasks)

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

// One bar for the whole board: a segment per state, as long as its share.
const bar = (tasks: Task[], width: number) =>
  COLUMNS.map(progress => {
    const n = tasks.filter(t => t.progress === progress).length
    return { progress, cells: n === 0 ? 0 : Math.max(1, Math.round((n / tasks.length) * width)) }
  }).filter(s => s.cells > 0)

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
    const { tasks, error } = await read($, board)
    const surfaces = (await $.session.surfaces()).join(', ') || 'none'
    const pane = opened.isPlaced ? 'pane opened' : `pane not drawn (${opened.reason})`

    // The same list as text: the command's output reaches every surface,
    // the remote ones that draw no pane included.
    const lines = error
      ? [error]
      : COLUMNS.flatMap(progress => {
          const group = tasks.filter(t => t.progress === progress)
          return group.length === 0
            ? []
            : [`${MARK(progress)} ${progress} (${group.length})`,
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
    const { tasks, error, updated } = await read($, board)
    const form = await read($, draft)
    const sent = (await read($, pending)) ?? []
    const width = Math.max(10, e.props.bodyColumns - 2)

    if (error) return <Text color="error">{error}</Text>

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
        <Select key="priority" label="Priority" value={form.priority}
          options={[{ value: 'high', label: '▲ high' }, { value: 'medium', label: '● medium' },
            { value: 'low', label: '▽ low' }]}
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
      const state = STATE[String(d?.progress ?? t.progress)]
      const priority = PRIORITY[String(d?.priority ?? t.priority)]
      const { id } = split(t)
      const field = (key: string) => (d && typeof d[key] === 'string' ? (d[key] as string) : '')
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
                options={COLUMNS.map(p => ({ value: p, label: `${MARK(p)} ${p}` }))}
                onSelect={progress => set({ progress })} />
              <Select key="edit-priority" label="Priority" value={values.priority}
                options={Object.entries(PRIORITY).map(([value, p]) => ({ value, label: p.mark }))}
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
          <Text bold color={state?.color ?? 'text'}>
            {state?.mark ?? '·'} {id}  <Text dimColor>{field('progress') || t.progress}</Text>
            {priority && <Text color={priority.color}>  {priority.mark}</Text>}
          </Text>
          <Text bold wrap="wrap">{field('title') || split(t).title}</Text>
          <Text color="subtle" wrap="wrap">
            {[field('assignee') && `@${field('assignee')}`, field('phase'),
              field('updated') && `updated ${field('updated')}`, field('closed_on') && `closed ${field('closed_on')}`]
              .filter(Boolean).join(' · ')}
          </Text>
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

    // Pressing a task's id or title opens its detail.
    const opener = (t: Task, children: unknown, isHistory = false) => (
      <Button key={`open-${name(t)}`} plain dimColor={isHistory} onPress={() => void openTask($, name(t))}>
        {children as string}
      </Button>
    )

    // A task being worked on: id and priority, title, assignee, in its state's frame.
    const card = (t: Task, color: string) => {
      const { id, title } = split(t)
      const priority = PRIORITY[t.priority]
      return (
        <Box key={name(t)} flexDirection="column" borderStyle="round" borderColor={color} paddingX={1}>
          <Box flexDirection="row" justifyContent="space-between">
            <Text bold color={color}>{id}{t.assignee && <Text color="subtle"> @{t.assignee}</Text>}</Text>
            <Box flexDirection="row" gap={1}>
              {priority && <Text color={priority.color}>{priority.mark}</Text>}
              {inject(t)}
            </Box>
          </Box>
          {opener(t, title)}
        </Box>
      )
    }

    // Any other task: one row, the priority as a mark before the title.
    const row = (t: Task, isHistory: boolean) => {
      const { id, title } = split(t)
      const priority = PRIORITY[t.priority]
      const room = Math.max(4, width - id.length - 12)
      const short = title.length > room ? `${title.slice(0, room - 1)}…` : title
      return (
        <Box key={name(t)} flexDirection="row" justifyContent="space-between" gap={1}>
          <Text>
            {'  '}<Text color={isHistory ? 'inactive' : priority?.color ?? 'text'}>{priority?.mark.charAt(0) ?? '·'}</Text>
          </Text>
          <Box flexGrow={1} flexShrink={1}>
            {opener(t, [<Text bold={!isHistory}>{id}</Text>, ' ',
              <Text strikethrough={t.progress === 'cancelled'}>{short}</Text>], isHistory)}
          </Box>
          {inject(t)}
        </Box>
      )
    }

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
              {bar(tasks, width).map(s => (
                <Text color={STATE[s.progress]?.color ?? 'text'}>{'━'.repeat(s.cells)}</Text>
              ))}
            </Box>
            {COLUMNS.map(progress => {
              const group = tasks.filter(t => t.progress === progress)
              if (group.length === 0) return undefined
              const state = STATE[progress] ?? { label: progress, mark: '·', color: 'text' }
              const isHistory = progress === 'done' || progress === 'cancelled'
              const shown = isHistory ? group.slice(-HISTORY) : group
              return (
                <Box key={progress} flexDirection="column" marginBottom={1}>
                  <Text bold color={state.color}>
                    {state.mark} {state.label.toUpperCase()} <Text dimColor>{group.length}</Text>
                  </Text>
                  {shown.map(t => (FOCUS.includes(progress) ? card(t, state.color) : row(t, isHistory)))}
                  {shown.length < group.length && (
                    <Text dimColor>  … {group.length - shown.length} more</Text>
                  )}
                </Box>
              )
            })}
          </Box>
        )}
        <Text dimColor>{updated ? `updated ${updated} · ` : ''}n new task · /board refresh</Text>
      </Box>
    )
  })
}
