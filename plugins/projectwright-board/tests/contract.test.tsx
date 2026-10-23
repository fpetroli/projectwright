import { expect, test } from 'claude-code/testing'

import { DETAILS, MODEL, TASKS } from './contract/contract'

// The board on the real output of the projectwright scripts and on the real
// board model (contract/contract.ts, written by contract/make_contract.py). When
// the scripts or the model change, these tests say whether the board still reads them.

const PANE = {
  plugin: 'projectwright-board',
  component: 'Pane',
  requestId: 'projectwright-board',
  props: {
    title: 'Board',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

const names = TASKS.map(t => String(t.task).replace(/^\[\[|\]\]$/g, ''))

// Nothing sits beneath the plugin: these hooks stand for the engine, and the
// scripts answer with what they really printed on the sample project.
const engine = (on: any) => {
  const sent: string[] = []
  on('command.register', () => ({ value: { command: 'board' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.start', (_: unknown, e: any) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/project' }))
  on('fs.exists', () => ({ value: true }))
  on('fs.read', (_: unknown, e: any) => ({
    value: e.path.endsWith('/.projectwright-plugin') ? '/plugin\n'
      : e.path === '/plugin/assets/board-model.json' ? JSON.stringify(MODEL) : JSON.stringify({ version: '0.2.0' }),
  }))
  on('process.run', (_: unknown, e: any) => {
    const argv = [...e.argv] as string[]
    const detail = argv[2] === 'task' ? DETAILS[argv[3] ?? ''] : undefined
    if (argv[2] === 'task' && !detail) {
      return { value: { exitCode: 1, stdout: '', stderr: `ERROR: task not found: ${argv[3]}` } }
    }
    return { value: { exitCode: 0, stdout: JSON.stringify(detail ?? TASKS), stderr: '' } }
  })
  on('prompt.submit', (_: unknown, e: any) => { sent.push(e.text); return { text: e.text } })
  return { sent }
}

test('the list output has the fields the board reads', () => {
  expect(TASKS.length).toBeGreaterThan(0)
  for (const t of TASKS) {
    for (const field of ['task', 'progress', 'priority', 'phase', 'assignee', 'title']) {
      expect(typeof t[field]).toBe('string')
    }
    expect(String(t.task)).toMatch(/^\[\[T-[A-Z0-9]+-\d+-.+\]\]$/)
    // the fields of a card
    for (const field of ['id', 'updated', 'closed_on', 'blocked_by']) expect(typeof t[field]).toBe('string')
  }
  const blocked = TASKS.find(t => t.progress === 'blocked')
  expect(blocked?.blocked_by).toBe('T-WEB-0002-payment-step')
})

test('the model has a column for every progress and the fields the board draws', () => {
  const columns = MODEL.columns as { progress: string; label: string; color: string }[]
  for (const t of TASKS) expect(columns.map(c => c.progress)).toContain(String(t.progress))
  for (const c of columns) for (const key of ['progress', 'label', 'color'] as const) expect(typeof c[key]).toBe('string')
  for (const p of MODEL.priorities as { value: string; label: string; color: string }[]) expect(typeof p.label).toBe('string')
  const fields = MODEL.fields as Record<string, string>
  for (const list of ['card', 'table', 'detail']) {
    for (const f of MODEL[list] as string[]) expect(typeof fields[f]).toBe('string')
  }
  const history = MODEL.history as { columns: string[]; shown: number }
  expect(history.shown).toBeGreaterThan(0)
})

test('the detail output has the fields the board reads', () => {
  for (const name of names) {
    const d = DETAILS[name]
    expect(d?.name).toBe(name)
    for (const field of ['path', 'body', 'title', 'progress']) expect(typeof d?.[field]).toBe('string')
    expect(Array.isArray(d?.links)).toBe(true)
    expect(d?.component === null || typeof d?.component === 'string').toBe(true)
  }
})

// The pane shows one column at a time: a task is drawn once its column is chosen.
const showColumnOf = async (ui: any, name: string) => {
  const t = TASKS.find(x => x.task === `[[${name}]]`)
  await ui.press({ key: `column-${String(t?.progress)}` })
}

test('every task of the sample project is drawn, in a column of the model', async ($, on) => {
  engine(on)
  await $.session.start({ cwd: '/project', surface: 'terminal', isInteractive: true })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  for (const c of MODEL.columns as { progress: string; label: string }[]) {
    expect(await ui.find({ key: `column-${c.progress}` })).toBeDefined()
  }
  for (const name of names) {
    const t = TASKS.find(x => x.task === `[[${name}]]`)
    await showColumnOf(ui, name)
    expect((await ui.find({ key: `open-${name}` }))?.text).toContain(String(t?.title))
  }
  await ui.unmount()
})

test('every task opens its detail from the real output, with its title and linked tasks', async ($, on) => {
  engine(on)
  await $.session.start({ cwd: '/project', surface: 'terminal', isInteractive: true })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  for (const name of names) {
    const d = DETAILS[name] ?? {}
    await showColumnOf(ui, name)
    await ui.press({ key: `open-${name}` })
    expect(await ui.find({ type: 'Text', text: String(d.title) })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /not found|failed/ })).toBeUndefined()
    for (const link of (d.links as string[]).filter(l => names.includes(l))) {
      expect(await ui.find({ key: `link-${link}` })).toBeDefined()
    }
    await ui.press({ key: 'back' })
  }
  await ui.unmount()
})

test('an edit starts from the values in the wiki', async ($, on) => {
  const { sent } = engine(on)
  await $.session.start({ cwd: '/project', surface: 'terminal', isInteractive: true })

  const name = 'T-WEB-0003-order-history'
  const d = DETAILS[name] ?? {}
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await showColumnOf(ui, name)
  await ui.press({ key: `open-${name}` })
  await ui.press({ key: 'edit' })
  await ui.select({ key: 'edit-progress', value: 'todo' })
  await ui.press({ key: 'apply' })
  expect(sent.length).toBe(1)
  expect(sent[0]).toContain(`- progress: "${String(d.progress)}" → "todo"`)
  // the empty assignee of the wiki is not taken for a change
  expect(sent[0]).not.toContain('assignee:')
  await ui.unmount()
})
