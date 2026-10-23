// A write that changes what the pane shows: a task note or the project settings.
// Paths are compared with forward slashes, and without case on Windows ("C:\\…").
export const touchesWiki = (path: string, root: string) => {
  const slash = (p: string) => p.replace(/\\/g, '/')
  const isWindows = /^[a-zA-Z]:\//.test(slash(root))
  const fold = (p: string) => (isWindows ? slash(p).toLowerCase() : slash(p))
  const base = fold(root).replace(/\/+$/, '')
  const full = fold(path)
  const rel = full.startsWith(base + '/') ? full.slice(base.length + 1) : full
  return rel.startsWith('wiki/') || rel === 'project.yaml'
}
