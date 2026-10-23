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
  { task: '[[TASK-0001-checkout-page]]', progress: 'in-progress', priority: 'high', phase: 'sprint-1',
    assignee: 'frontend developer', title: 'Checkout page' },
  { task: '[[TASK-0002-payment-step]]', progress: 'todo', priority: '', phase: '', assignee: '',
    title: 'Payment step' },
]

const DETAIL = {
  name: 'TASK-0001-checkout-page', path: 'wiki/components/web/tasks/TASK-0001-checkout-page.md',
  component: 'WEB', title: "The customer's checkout page", progress: 'in-progress', priority: 'high',
  phase: 'sprint-1', assignee: 'frontend developer',
  body: '# TASK-0001 — Checkout page\n\n**Goal** — A checkout page that leads to [[TASK-0002-payment-step]].\n',
  links: ['TASK-0002-payment-step', 'ADR-WEB-0003-one-page-checkout'],
}

type Engine = {
  cwd?: string
  root?: string | null
  version?: string | null
  tasks?: unknown[] | (() => unknown[])
  pythons?: string[]
  model?: string | null
  proposals?: Record<string, unknown>[]
  reminders?: Record<string, unknown>[]
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
    // proposals.py: the proposals of the test, answered and changed in memory
    if (String(argv[1]).endsWith('/proposals.py')) {
      const store = opts.proposals ?? []
      if (argv[2] === 'set') {
        const p = store.find(x => x.id === argv[3])
        if (p) Object.assign(p, { status: argv[5] }, argv[6] === '--comment' ? { comment: argv[7] } : {})
        return { value: { exitCode: 0, stdout: '', stderr: '' } }
      }
      const open = store.filter(p => p.status === 'open' || p.status === 'revising')
      return { value: { exitCode: 0, stdout: JSON.stringify(open), stderr: '' } }
    }
    // reminders.py: the reminders of the test, in memory too
    if (String(argv[1]).endsWith('/reminders.py')) {
      const store = opts.reminders ?? []
      if (argv[2] === 'add') {
        if (argv[4] === '--due' && !/^\d{4}-\d{2}-\d{2}$|^\d{1,2}\/\d{1,2}$/.test(argv[5] ?? '')) {
          return { value: { exitCode: 1, stdout: '', stderr: `ERROR: not a date: ${argv[5]}` } }
        }
        store.push({ id: `R-${store.length + 1}`, text: argv[3], ...(argv[4] === '--due' ? { due: argv[5] } : {}) })
      } else if (argv[2] !== 'list') {
        const r = store.find(x => x.id === argv[3])
        if (argv[2] === 'done' && r) r.done_on = '2026-10-23'
        if (argv[2] === 'undo' && r) delete r.done_on
        if (argv[2] === 'remove' && r) store.splice(store.indexOf(r), 1)
      }
      return { value: { exitCode: 0, stdout: argv[2] === 'list' ? JSON.stringify(store) : '', stderr: '' } }
    }
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
    // a narrow pane lists the columns one under the other, each a group that opens and closes
    expect((await ui.find({ key: 'group-in-progress' }))?.text).toContain('In progress 1')
    expect((await ui.find({ key: 'open-TASK-0001-checkout-page' }))?.text).toContain('Checkout page')
    expect((await ui.find({ key: 'open-TASK-0002-payment-step' }))?.text).toContain('Payment step')
    await ui.press({ key: 'group-todo' })
    expect(await ui.find({ key: 'open-TASK-0002-payment-step' })).toBeUndefined()
    await ui.press({ key: 'group-todo' })
    expect(await ui.find({ key: 'open-TASK-0002-payment-step' })).toBeDefined()
    await ui.unmount()
  }
  expect(ran[0]).toEqual(['python3', '/plugin/scripts/wiki-query.py', 'tasks', '--format', 'json', '--root', '/project'])
})

const PROPOSED = () => [
  { id: 'P-0001', kind: 'create', summary: 'Address book', why: 'Asked at every checkout.', status: 'open',
    items: [{ title: 'Address book', priority: 'medium' }] },
  { id: 'P-0002', kind: 'move', task: 'TASK-0001-checkout-page', summary: 'In progress -> Done', status: 'open',
    changes: { progress: 'done' } },
]

test('the proposals of Claude are drawn above the columns, and only when there are some', async ($, on) => {
  engine(on, { proposals: PROPOSED() })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Proposed by Claude 2/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'Address book' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^Why: Asked at every checkout\.$/ })).toBeDefined()
  for (const key of ['accept-P-0001', 'reject-P-0001', 'comment-open-P-0001', 'accept-P-0002']) {
    expect(await ui.find({ key })).toBeDefined()
  }
  await ui.unmount()
})

test('without proposals there is no section for them', async ($, on) => {
  engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Proposed by Claude/ })).toBeUndefined()
  await ui.unmount()
})

test('accepting a proposal asks Claude to apply it, and says so until Claude has', async ($, on) => {
  const { sent, written } = engine(on, { proposals: PROPOSED() })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'accept-P-0002' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('Apply the proposal “In progress -> Done” on TASK-0001 with /projectwright:manage-tasks.')
  // the id is for Claude: only at the end, as a reference
  expect(sent[0]).toMatch(/\[ref P-0002\]$/)
  expect(written.length).toBe(0)
  expect(await ui.find({ type: 'Text', text: /Claude is applying it/ })).toBeDefined()
  // Claude's turn ends and the proposal is still open
  await $.turn.start({ text: sent[0] ?? '', turnId: 't1' })
  await $.turn.complete({ turnId: 't1', reason: 'answer', answer: 'Which commit?', durationMs: 900, isAborted: false })
  expect(await ui.find({ type: 'Text', text: /Not applied yet: Claude may be waiting for you/ })).toBeDefined()
  await ui.unmount()
})

test('rejecting a proposal needs no turn of Claude: the pane marks it', async ($, on) => {
  const proposals = PROPOSED()
  const { sent, ran } = engine(on, { proposals })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'reject-P-0001' })
  expect(sent.length).toBe(0)
  expect(ran.some(a => a.includes('/plugin/scripts/proposals.py') && a.includes('rejected'))).toBe(true)
  expect(proposals[0]?.status).toBe('rejected')
  expect(await ui.find({ type: 'Text', text: 'Address book' })).toBeUndefined()
  await ui.unmount()
})

test('a comment goes to Claude, which proposes again; the card says it is being revised', async ($, on) => {
  const proposals = PROPOSED()
  const { sent } = engine(on, { proposals })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'comment-open-P-0001' })
  // nothing written yet: nothing is sent
  await ui.press({ key: 'send-P-0001' })
  expect(sent.length).toBe(0)
  await ui.input({ key: 'comment-P-0001', text: 'make it part of the checkout task', kind: 'change' })
  await ui.press({ key: 'send-P-0001' })
  expect(proposals[0]).toMatchObject({ status: 'revising', comment: 'make it part of the checkout task' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('Revise the proposal “Address book” with /projectwright:manage-tasks on my comment: make it part of the checkout task [ref P-0001]')
  expect(await ui.find({ type: 'Text', text: /Claude is revising it on your comment/ })).toBeDefined()
  expect(await ui.find({ key: 'accept-P-0001' })).toBeUndefined()
  await ui.unmount()
})

test('the cards of the proposals never show their ids', async ($, on) => {
  engine(on, { proposals: PROPOSED() })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /P-000/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /TASK-0001/ })).toBeDefined()
  await ui.unmount()
})

test('a proposed reminder, accepted, joins the reminders without a turn of Claude', async ($, on) => {
  const proposals = [{ id: 'P-0003', kind: 'remind', summary: 'Ask for the Windows logs', status: 'open',
    items: [{ title: 'Ask for the Windows logs', due: '2026-10-31' }] }]
  const reminders: Record<string, unknown>[] = []
  const { sent } = engine(on, { proposals, reminders })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /REMINDER/ })).toBeDefined()
  await ui.press({ key: 'accept-P-0003' })
  expect(sent.length).toBe(0)
  expect(reminders).toEqual([{ id: 'R-1', text: 'Ask for the Windows logs', due: '2026-10-31' }])
  expect(proposals[0]?.status).toBe('accepted')
  expect(await ui.find({ type: 'Text', text: /Reminders 1/ })).toBeDefined()
  await ui.unmount()
})

const REMINDED = () => [
  { id: 'R-0001', text: 'Send the e-mail on the test', due: '2020-01-02' },
  { id: 'R-0002', text: 'Renew the login' },
  { id: 'R-0003', text: 'Commit the project folder', done_on: '2026-10-23' },
]

test('the reminders are a checklist: the open ones counted, the late ones red, the ticked ones struck through', async ($, on) => {
  engine(on, { reminders: REMINDED() })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Reminders 2/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /1 overdue/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: '02/01' })).toBeDefined()
  expect((await ui.find({ key: 'tick-R-0001' }))?.text).toContain('☐')
  expect((await ui.find({ key: 'tick-R-0003' }))?.text).toContain('☑')
  // a ticked reminder cannot become a task
  expect(await ui.find({ key: 'totask-R-0003' })).toBeUndefined()
  await ui.unmount()
})

test('without reminders there is no section, only the button to add one', async ($, on) => {
  engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Reminders/ })).toBeUndefined()
  expect(await ui.find({ key: 'open-reminder' })).toBeDefined()
  await ui.unmount()
})

test('ticking, adding and removing a reminder need no turn of Claude', async ($, on) => {
  const reminders = REMINDED()
  const { sent } = engine(on, { reminders })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'tick-R-0002' })
  expect(reminders[1]?.done_on).toBe('2026-10-23')
  await ui.press({ key: 'remove-R-0003' })
  expect(reminders.map(r => r.id)).not.toContain('R-0003')
  await ui.press({ key: 'open-reminder' })
  await ui.input({ key: 'reminder-text', text: 'Update the specification', kind: 'change' })
  await ui.input({ key: 'reminder-due', text: '31/10', kind: 'change' })
  await ui.press({ key: 'reminder-add' })
  expect(reminders.at(-1)).toMatchObject({ text: 'Update the specification', due: '31/10' })
  expect(sent.length).toBe(0)
  await ui.unmount()
})

test('a date the script refuses keeps the form open, and says why', async ($, on) => {
  const reminders: Record<string, unknown>[] = []
  engine(on, { reminders })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-reminder' })
  await ui.input({ key: 'reminder-text', text: 'Call back', kind: 'change' })
  await ui.input({ key: 'reminder-due', text: 'someday', kind: 'change' })
  await ui.press({ key: 'reminder-add' })
  expect(reminders.length).toBe(0)
  expect(await ui.find({ key: 'reminder-text' })).toBeDefined()
  await ui.unmount()
})

test('a reminder becomes a task through Claude, as a proposal', async ($, on) => {
  const { sent } = engine(on, { reminders: REMINDED() })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'totask-R-0001' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('Propose a task from my reminder “Send the e-mail on the test” (due 2020-01-02)')
  expect(sent[0]).toMatch(/\[ref R-0001\]$/)
  await ui.unmount()
})

test('a project not yet renumbered still shows its task ids', async ($, on) => {
  engine(on, { tasks: [{ task: '[[T-WEB-0007-old-cart]]', progress: 'todo', priority: 'low', phase: '', assignee: '', title: 'Old cart' }] })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: 'T-WEB-0007' })).toBeDefined()
  expect((await ui.find({ key: 'open-T-WEB-0007-old-cart' }))?.text).toContain('Old cart')
  await ui.unmount()
})

test('a closed task blocks no more: the card does not show it', async ($, on) => {
  const tasks = [{ ...TASKS[0], blocked_by: 'TASK-0002-payment-step' }, { ...TASKS[1], progress: 'done' }]
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /Blocked by/ })).toBeUndefined()
  await ui.unmount()
})

test('a card shows the fields of the model: priority, assignee, what blocks it', async ($, on) => {
  const tasks = [{ ...TASKS[0], id: 'TASK-0001', blocked_by: 'TASK-0002-payment-step' }, TASKS[1]]
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /^ High $/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /@frontend developer/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Blocked by TASK-0002/ })).toBeDefined()
  await ui.unmount()
})

test('done tasks start closed in the list, then show the newest few first, and the rest on request', async ($, on) => {
  const tasks = [1, 2, 3, 4, 5].map(n => ({ task: `[[TASK-000${n}-step-${n}]]`, progress: 'done', priority: 'low',
    phase: '', assignee: '', title: `Step ${n}` }))
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  // one column with tasks fits the board even in a narrow pane: v shows the list
  expect(await ui.find({ key: 'group-done' })).toBeUndefined()
  await ui.press({ key: 'view' })
  expect(await ui.find({ key: 'open-TASK-0005-step-5' })).toBeUndefined()
  await ui.press({ key: 'group-done' })
  expect(await ui.find({ key: 'open-TASK-0005-step-5' })).toBeDefined()
  expect(await ui.find({ key: 'open-TASK-0003-step-3' })).toBeDefined()
  expect(await ui.find({ key: 'open-TASK-0002-step-2' })).toBeUndefined()
  await ui.press({ key: 'more-done' })
  expect(await ui.find({ key: 'open-TASK-0001-step-1' })).toBeDefined()
  await ui.unmount()
})

test('a wide pane shows the columns side by side, and v swaps to the list', async ($, on) => {
  const tasks = [...TASKS, { task: '[[TASK-0003-cart]]', progress: 'done', priority: 'low', phase: '',
    assignee: '', title: 'Cart' }]
  engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal', props: { ...PANE.props, bodyColumns: 140 } })
  // the board: every column at once, the done ones too, and no group to open; an empty one is its heading
  expect(await ui.find({ key: 'open-TASK-0003-cart' })).toBeDefined()
  expect(await ui.find({ key: 'group-done' })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: / Blocked 0 / })).toBeDefined()
  await ui.press({ key: 'view' })
  expect(await ui.find({ key: 'group-done' })).toBeDefined()
  expect(await ui.find({ key: 'open-TASK-0003-cart' })).toBeUndefined()
  await ui.press({ key: 'view' })
  expect(await ui.find({ key: 'open-TASK-0003-cart' })).toBeDefined()
  await ui.unmount()
})

test('the state an earlier pane left in the session still draws', async ($, on) => {
  // the view as the one-column-at-a-time pane kept it, without the fields of the views
  on('state.get', { plugin: 'projectwright-board', key: 'view' },
    () => ({ value: { value: { column: 'todo', expanded: [] }, version: 1 } }))
  engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'open-TASK-0001-checkout-page' })).toBeDefined()
  expect(await ui.find({ key: 'view' })).toBeDefined()
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
  expect(await ui.find({ key: 'open-TASK-0001-checkout-page' })).toBeDefined()
  expect(ran[0]?.[0]).toBe('python')
  await ui.unmount()
})

test('from a subfolder of the project the pane still finds the tasks', async ($, on) => {
  const { ran } = engine(on, { cwd: '/project/repositories/web' })
  await start($, '/project/repositories/web')

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'open-TASK-0001-checkout-page' })).toBeDefined()
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
  const tasks = [...TASKS, { task: '[[TASK-0003-cart]]', progress: 'done', priority: 'low', phase: '',
    assignee: '', title: 'Cart' }]
  const { sent, written } = engine(on, { tasks })
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'inject-TASK-0001-checkout-page' })
  await ui.press({ key: 'group-done' })
  await ui.press({ key: 'inject-TASK-0003-cart' })
  expect(sent.length).toBe(2)
  expect(sent[0]).toContain('Bring task TASK-0001 (TASK-0001-checkout-page) into context.')
  expect(sent[1]).toContain('(progress: done)')
  expect(sent[1]).toContain('Do not change the wiki')
  expect(written.length).toBe(0)
  await ui.unmount()
})

test('pressing a task opens its detail in place of the list, and Back returns', async ($, on) => {
  const { ran, written } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-TASK-0001-checkout-page' })
  expect(ran.at(-1)).toEqual(['python3', '/plugin/scripts/wiki-query.py', 'task', 'TASK-0001-checkout-page',
    '--format', 'json', '--root', '/project'])
  // the title from the frontmatter, the linked task as a button, the inject button
  expect(await ui.find({ type: 'Text', text: /The customer's checkout page/ })).toBeDefined()
  expect(await ui.find({ key: 'link-TASK-0002-payment-step' })).toBeDefined()
  expect(await ui.find({ key: 'inject-TASK-0001-checkout-page' })).toBeDefined()
  // its properties, named and drawn as the model says
  expect(await ui.find({ type: 'Text', text: /^Status$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^ In progress $/ })).toBeDefined()
  expect(await ui.find({ key: 'group-todo' })).toBeUndefined()
  await ui.press({ key: 'back' })
  expect(await ui.find({ key: 'group-todo' })).toBeDefined()
  expect(written.length).toBe(0)
  await ui.unmount()
})

test('the edit form sends only the changed fields to Claude, and writes nothing', async ($, on) => {
  const { sent, written } = engine(on)
  await start($)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-TASK-0001-checkout-page' })
  await ui.press({ key: 'edit' })
  // nothing changed yet: nothing is sent
  await ui.press({ key: 'apply' })
  expect(sent.length).toBe(0)
  await ui.select({ key: 'edit-progress', value: 'done' })
  await ui.input({ key: 'edit-body', text: 'add a criterion on the tests', kind: 'change' })
  expect(await ui.find({ type: 'Text', text: /2 change\(s\): progress, body/ })).toBeDefined()
  await ui.press({ key: 'apply' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain('Update task TASK-0001 (TASK-0001-checkout-page) with /projectwright:manage-tasks.')
  expect(sent[0]).toContain('- progress: "in-progress" → "done"')
  expect(sent[0]).not.toContain('priority:')
  expect(sent[0]).toContain('add a criterion on the tests')
  expect(written.length).toBe(0)
  // back on the detail, the pane says Claude is on it
  expect(await ui.find({ type: 'Text', text: /Claude is applying your changes/ })).toBeDefined()
  await ui.unmount()
})

test('a write tells the wiki apart from the code, on Windows paths too', () => {
  expect(touchesWiki('/project/wiki/tasks/TASK-0009-new.md', '/project')).toBe(true)
  expect(touchesWiki('/project/project.yaml', '/project')).toBe(true)
  expect(touchesWiki('/project/repositories/web/app.ts', '/project')).toBe(false)
  expect(touchesWiki('/projects/other/wiki/x.md', '/project')).toBe(false)
  // Windows: back slashes, a drive letter, and a case that does not matter
  expect(touchesWiki('C:\\Work\\Shop\\wiki\\tasks\\TASK-0009-new.md', 'C:\\Work\\Shop')).toBe(true)
  expect(touchesWiki('c:\\work\\shop\\wiki\\x.md', 'C:\\Work\\Shop\\')).toBe(true)
  expect(touchesWiki('C:/Work/Shop/project.yaml', 'C:\\Work\\Shop')).toBe(true)
  expect(touchesWiki('C:\\Work\\Shop\\repositories\\web\\app.ts', 'C:\\Work\\Shop')).toBe(false)
  expect(touchesWiki('C:\\Work\\Shopping\\wiki\\x.md', 'C:\\Work\\Shop')).toBe(false)
})

test('a write of Claude in the wiki refreshes the pane, a write in the code does not', async ($, on) => {
  const { ran } = engine(on)
  on('tool.call', () => ({ result: {} }))
  await start($)

  // a refresh reads the tasks, the proposals and the reminders
  const before = ran.length
  await $.tool.call({ tool: 'Write', file_path: '/project/wiki/tasks/TASK-0009-new.md', content: 'x' })
  expect(ran.length).toBe(before + 3)
  await $.tool.call({ tool: 'Write', file_path: '/project/repositories/web/app.ts', content: 'x' })
  expect(ran.length).toBe(before + 3)
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
  await ui.press({ key: 'group-done' })
  expect(await ui.find({ key: 'open-TASK-0001-checkout-page' })).toBeDefined()
  expect((await ui.find({ key: 'group-done' }))?.text).toContain('Done 0')
  // someone closes a task in an editor
  tasks = TASKS.map(t => (t.task === '[[TASK-0001-checkout-page]]' ? { ...t, progress: 'done' } : t))
  await clock.advance(30_000)
  expect((await ui.find({ key: 'group-done' }))?.text).toContain('Done 1')
  expect((await ui.find({ key: 'group-in-progress' }))?.text).toContain('In progress 0')
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

