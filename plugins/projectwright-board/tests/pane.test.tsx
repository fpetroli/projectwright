import { expect, mock, test } from 'claude-code/testing'

import { touchesWiki } from '../hooks/paths'

import { MODEL } from './contract/contract'

const PANE = {
  plugin: 'projectwright-board',
  component: 'Pane',
  requestId: 'projectwright-board',
  props: {
    title: 'Board',
    isFocused: false,
    bodyColumns: 50,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const TASKS = [
  { task: '[[T-WEB-0001-checkout-page]]', progress: 'in-progress', priority: 'high', phase: 'sprint-1',
    assignee: 'frontend developer', title: 'Checkout page' },
  { task: '[[T-WEB-0002-payment-step]]', progress: 'todo', priority: '', phase: '', assignee: '',
    title: 'Payment step' },
]

const DETAIL = {
  name: 'T-WEB-0001-checkout-page', path: 'wiki/components/web/tasks/T-WEB-0001-checkout-page.md',
  component: 'WEB', title: "The customer's checkout page", progress: 'in-progress', priority: 'high',
  phase: 'sprint-1', assignee: 'frontend developer',
  body: '# T-WEB-0001 — Checkout page\n\n**Goal** — A checkout page that leads to [[T-WEB-0002-payment-step]].\n',
  links: ['T-WEB-0002-payment-step', 'ADR-WEB-0003-one-page-checkout'],
}

type Engine = {
  cwd?: string
  root?: string | null
  version?: string | null
  tasks?: unknown[] | (() => unknown[])
  pythons?: string[]
  model?: string | null
}

// Nothing sits beneath the plugin: these hooks stand for the engine, with a
// project at `root` whose projectwright plugin is in /plugin.
const engine = (on: any, opts: Engine = {}) => {
  const root = opts.root === undefined ? '/project' : opts.root
  const version = opts.version === undefined ? '0.2.0' : opts.version
  const pythons = opts.pythons ?? ['python3', 'python']
  const sent: string[] = []
  const written: string[] = []
  const ran: string[][] = []
  const clock = mock.clock(on)
  on('turn.start', (_: unknown, e: any) => ({ turnId: e.turnId }))
  on('turn.complete', (_: unknown, e: any) => ({ text: e.answer ?? '' }))
  on('command.register', () => ({ value: { command: 'board' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.start', (_: unknown, e: any) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: opts.cwd ?? '/project' }))
  on('fs.exists', (_: unknown, e: any) => ({
    value: root !== null && (e.path === `${root}/project.yaml` ||
      (version !== null && e.path === `${root}/.claude/.projectwright-plugin`)),
  }))
  on('fs.read', (_: unknown, e: any) => {
    if (e.path.endsWith('/.projectwright-plugin')) return { value: '/plugin\n' }
    if (e.path === '/plugin/.claude-plugin/plugin.json') return { value: JSON.stringify({ version }) }
    if (e.path.endsWith('/.claude-plugin/plugin.json')) return { value: JSON.stringify({ version: '0.2.0' }) }
    if (e.path === '/plugin/assets/board-model.json') {
      if (opts.model === null) throw new Error('ENOENT: no such file')
      return { value: opts.model ?? JSON.stringify(MODEL) }
    }
    return { value: '' }
  })
  on('fs.write', (_: unknown, e: any) => { written.push(e.path); return { value: undefined } })
  on('process.run', (_: unknown, e: any) => {
    const argv = [...e.argv] as string[]
    if (!pythons.includes(argv[0] ?? '')) throw new Error(`${argv[0]}: not found`)
    ran.push(argv)
    const tasks = typeof opts.tasks === 'function' ? opts.tasks() : opts.tasks ?? TASKS
    const stdout = argv[2] === 'task' ? JSON.stringify(DETAIL) : JSON.stringify(tasks)
    return { value: { exitCode: 0, stdout, stderr: '' } }
  })
  on('prompt.submit', (_: unknown, e: any) => { sent.push(e.text); return { text: e.text } })
  return { sent, written, ran, clock }
}

const start = ($: any, cwd = '/project') => $.session.start({ cwd, surface: 'terminal', isInteractive: true })

test('the pane groups the tasks wiki-query answers, with their titles, on every surface', async ($, on) => {
  const { ran } = engine(on)
  await start($)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    // the first column with tasks is shown, the others are tabs; the choice outlives the mount
    if (surface === 'terminal') expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeDefined()
    else await ui.press({ key: 'column-in-progress' })
    expect((await ui.find({ key: 'column-in-progress' }))?.text).toContain('In progress 1')
    expect((await ui.find({ key: 'open-T-WEB-0001-checkout-page' }))?.text).toContain('Checkout page')
    expect(await ui.find({ key: 'open-T-WEB-0002-payment-step' })).toBeUndefined()
    await ui.press({ key: 'column-todo' })
    expect((await ui.find({ key: 'open-T-WEB-0002-payment-step' }))?.text).toContain('Payment step')
    expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeUndefined()
    await ui.unmount()
  }
  expect(ran[0]).toEqual(['python3', '/plugin/scripts/wiki-query.py', 'tasks', '--format', 'json', '--root', '/project'])
})

test('a card shows the fields of the model: priority, assignee, what blocks it', async ($, on) => {
  const tasks = [{ ...TASKS[0], id: 'T-WEB-0001', blocked_by: 'T-WEB-0002-payment-step' }, TASKS[1]]
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /^ High $/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /@frontend developer/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Blocked by T-WEB-0002/ })).toBeDefined()
  await ui.unmount()
})

test('done tasks show the newest few first, and the rest on request', async ($, on) => {
  const tasks = [1, 2, 3, 4, 5].map(n => ({ task: `[[T-WEB-000${n}-step-${n}]]`, progress: 'done', priority: 'low',
    phase: '', assignee: '', title: `Step ${n}` }))
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'open-T-WEB-0005-step-5' })).toBeDefined()
  expect(await ui.find({ key: 'open-T-WEB-0003-step-3' })).toBeDefined()
  expect(await ui.find({ key: 'open-T-WEB-0002-step-2' })).toBeUndefined()
  await ui.press({ key: 'more' })
  expect(await ui.find({ key: 'open-T-WEB-0001-step-1' })).toBeDefined()
  await ui.unmount()
})

test('without the board model of projectwright the pane says what to do', async ($, on) => {
  engine(on, { model: null })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /projectwright has no assets\/board-model\.json/ })).toBeDefined()
  await ui.unmount()
})

test('outside a projectwright project the pane says so', async ($, on) => {
  engine(on, { root: null, cwd: '/elsewhere' })
  await start($, '/elsewhere')

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Not a projectwright project/ })).toBeDefined()
  await ui.unmount()
})

test('without the projectwright plugin, or with another version of it, the pane says what to do', async ($, on) => {
  engine(on, { version: '0.1.0' })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /needs projectwright 0\.2\.0; found 0\.1\.0/ })).toBeDefined()
  await ui.unmount()
})

test('a project where projectwright has not run yet', async ($, on) => {
  engine(on, { version: null })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /projectwright plugin is not running here/ })).toBeDefined()
  await ui.unmount()
})

test('where only "python" answers, the scripts run with it', async ($, on) => {
  const { ran } = engine(on, { pythons: ['python'] })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeDefined()
  expect(ran[0]?.[0]).toBe('python')
  await ui.unmount()
})

test('from a subfolder of the project the pane still finds the tasks', async ($, on) => {
  const { ran } = engine(on, { cwd: '/project/repositories/web' })
  await start($, '/project/repositories/web')

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeDefined()
  expect(ran[0]).toContain('/project')
  await ui.unmount()
})

test('a task typed in the pane goes to Claude, never to the wiki', async ($, on) => {
  const { sent, written } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-form' })
  await ui.input({ key: 'title', text: 'Order history', kind: 'change' })
  await ui.select({ key: 'priority', value: 'high' })
  await ui.press({ key: 'create' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('/projectwright:manage-tasks: "Order history"')
  expect(sent[0]).toContain('Priority: high.')
  expect(written.length).toBe(0)
  // until the task is in the wiki, the pane says Claude is on it
  expect(await ui.find({ type: 'Text', text: /Claude is adding “Order history”/ })).toBeDefined()
  await ui.unmount()
})

test('the inject button hands the task to Claude, on open and closed tasks alike', async ($, on) => {
  const tasks = [...TASKS, { task: '[[T-WEB-0003-cart]]', progress: 'done', priority: 'low', phase: '',
    assignee: '', title: 'Cart' }]
  const { sent, written } = engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'inject-T-WEB-0001-checkout-page' })
  await ui.press({ key: 'column-done' })
  await ui.press({ key: 'inject-T-WEB-0003-cart' })
  expect(sent.length).toBe(2)
  expect(sent[0]).toContain('Bring task T-WEB-0001 (T-WEB-0001-checkout-page) into context.')
  expect(sent[1]).toContain('(progress: done)')
  expect(sent[1]).toContain('Do not change the wiki')
  expect(written.length).toBe(0)
  await ui.unmount()
})

test('pressing a task opens its detail in place of the list, and Back returns', async ($, on) => {
  const { ran, written } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-T-WEB-0001-checkout-page' })
  expect(ran.at(-1)).toEqual(['python3', '/plugin/scripts/wiki-query.py', 'task', 'T-WEB-0001-checkout-page',
    '--format', 'json', '--root', '/project'])
  // the title from the frontmatter, the linked task as a button, the inject button
  expect(await ui.find({ type: 'Text', text: /The customer's checkout page/ })).toBeDefined()
  expect(await ui.find({ key: 'link-T-WEB-0002-payment-step' })).toBeDefined()
  expect(await ui.find({ key: 'inject-T-WEB-0001-checkout-page' })).toBeDefined()
  // its properties, named and drawn as the model says
  expect(await ui.find({ type: 'Text', text: /^Status$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^ In progress $/ })).toBeDefined()
  expect(await ui.find({ key: 'column-todo' })).toBeUndefined()
  await ui.press({ key: 'back' })
  expect(await ui.find({ key: 'column-todo' })).toBeDefined()
  expect(written.length).toBe(0)
  await ui.unmount()
})

test('the edit form sends only the changed fields to Claude, and writes nothing', async ($, on) => {
  const { sent, written } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-T-WEB-0001-checkout-page' })
  await ui.press({ key: 'edit' })
  // nothing changed yet: nothing is sent
  await ui.press({ key: 'apply' })
  expect(sent.length).toBe(0)
  await ui.select({ key: 'edit-progress', value: 'done' })
  await ui.input({ key: 'edit-body', text: 'add a criterion on the tests', kind: 'change' })
  expect(await ui.find({ type: 'Text', text: /2 change\(s\): progress, body/ })).toBeDefined()
  await ui.press({ key: 'apply' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('Update task T-WEB-0001 (T-WEB-0001-checkout-page) with /projectwright:manage-tasks.')
  expect(sent[0]).toContain('- progress: "in-progress" → "done"')
  expect(sent[0]).not.toContain('priority:')
  expect(sent[0]).toContain('add a criterion on the tests')
  expect(written.length).toBe(0)
  // back on the detail, the pane says Claude is on it
  expect(await ui.find({ type: 'Text', text: /Claude is applying your changes/ })).toBeDefined()
  await ui.unmount()
})

test('a write tells the wiki apart from the code, on Windows paths too', () => {
  expect(touchesWiki('/project/wiki/tasks/T-WEB-0009-new.md', '/project')).toBe(true)
  expect(touchesWiki('/project/project.yaml', '/project')).toBe(true)
  expect(touchesWiki('/project/repositories/web/app.ts', '/project')).toBe(false)
  expect(touchesWiki('/projects/other/wiki/x.md', '/project')).toBe(false)
  // Windows: back slashes, a drive letter, and a case that does not matter
  expect(touchesWiki('C:\\Work\\Shop\\wiki\\tasks\\T-WEB-0009-new.md', 'C:\\Work\\Shop')).toBe(true)
  expect(touchesWiki('c:\\work\\shop\\wiki\\x.md', 'C:\\Work\\Shop\\')).toBe(true)
  expect(touchesWiki('C:/Work/Shop/project.yaml', 'C:\\Work\\Shop')).toBe(true)
  expect(touchesWiki('C:\\Work\\Shop\\repositories\\web\\app.ts', 'C:\\Work\\Shop')).toBe(false)
  expect(touchesWiki('C:\\Work\\Shopping\\wiki\\x.md', 'C:\\Work\\Shop')).toBe(false)
})

test('a write of Claude in the wiki refreshes the pane, a write in the code does not', async ($, on) => {
  const { ran } = engine(on)
  on('tool.call', () => ({ result: {} }))
  await start($)

  const before = ran.length
  await $.tool.call({ tool: 'Write', file_path: '/project/wiki/tasks/T-WEB-0009-new.md', content: 'x' })
  expect(ran.length).toBe(before + 1)
  await $.tool.call({ tool: 'Write', file_path: '/project/repositories/web/app.ts', content: 'x' })
  expect(ran.length).toBe(before + 1)
})

test('a request Claude did not carry out is flagged when its turn ends, and can be dismissed', async ($, on) => {
  const { sent } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-form' })
  await ui.input({ key: 'title', text: 'Order history', kind: 'change' })
  await ui.press({ key: 'create' })
  expect(sent.length).toBe(1)
  expect(await ui.find({ type: 'Text', text: /Claude is adding “Order history”/ })).toBeDefined()

  // Claude's turn on the request ends, and the task is not in the wiki
  await $.turn.start({ text: sent[0] ?? '', turnId: 't1' })
  await $.turn.complete({ turnId: 't1', reason: 'answer', answer: 'Which component?', durationMs: 900, isAborted: false })
  expect(await ui.find({ type: 'Text', text: /“Order history” is not in the wiki yet: Claude may be waiting for you/ }))
    .toBeDefined()

  const row = await ui.find({ type: 'Text', text: /Order history/ })
  expect(row).toBeDefined()
  const dismiss = (await ui.find({ type: 'Button', text: /✕/ }))
  expect(dismiss).toBeDefined()
  await ui.press({ key: String((dismiss as any).key) })
  expect(await ui.find({ type: 'Text', text: /Order history/ })).toBeUndefined()
  await ui.unmount()
})

test('while the pane is shown it looks at the wiki every 30 seconds, for changes made by hand', async ($, on) => {
  let tasks: unknown[] = TASKS
  on('ui.panes', () => ({ value: [{ id: 'projectwright-board', title: 'Board', isShown: true, isFocused: false }] }))
  const { clock } = engine(on, { tasks: () => tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'column-done' })
  expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeUndefined()
  // someone closes a task in an editor
  tasks = TASKS.map(t => (t.task === '[[T-WEB-0001-checkout-page]]' ? { ...t, progress: 'done' } : t))
  await clock.advance(30_000)
  expect(await ui.find({ key: 'open-T-WEB-0001-checkout-page' })).toBeDefined()
  await ui.unmount()
})

test('while the pane is not shown, the periodic look runs no script', async ($, on) => {
  on('ui.panes', () => ({ value: [] }))
  const { ran, clock } = engine(on)
  await start($)

  const before = ran.length
  await clock.advance(90_000)
  expect(ran.length).toBe(before)
})

