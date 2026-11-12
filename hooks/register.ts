import type { ProcessRunInit, ProcessRunResult, Register } from 'claude-code'

// A doc docket-ship governs: any markdown under a docs/ folder. INDEX.md is
// generated, so editing it is not a change worth checking.
const DOC = /[\\/]docs[\\/](?:.+[\\/])?[^\\/]+\.md$/i
const GENERATED = /[\\/]INDEX\.md$/i

// Tried in order. On Windows `python3` is often the Store alias, which exits
// non-zero without running anything, so each candidate is probed for real.
const PYTHONS: readonly (readonly string[])[] = [['python3'], ['python'], ['py', '-3']]

/** The script's exit code for "no docket-ship.cfg here or above". */
const NOT_A_PROJECT = 3

type Run = (argv: readonly string[], init?: ProcessRunInit) => Promise<ProcessRunResult>

export const register: Register = on => {
  // undefined: not probed yet; null: no Python 3 found, so the hook stays out.
  let python: readonly string[] | null | undefined

  const findPython = async (run: Run): Promise<readonly string[] | null> => {
    if (python !== undefined) return python
    python = null
    for (const candidate of PYTHONS) {
      try {
        const probe = await run([...candidate, '--version'], { timeoutMs: 5000 })
        if (probe.exitCode === 0 && /Python 3\./.test(probe.stdout + probe.stderr)) {
          python = candidate
          break
        }
      } catch {
        // Not installed under this name; try the next.
      }
    }
    return python
  }

  /** The check's report for the model, or undefined when there is nothing to say. */
  const checkAfterEdit = async (run: Run, root: string, file: string) => {
    const interpreter = await findPython(run)
    if (!interpreter) return undefined
    const checked = await run(
      [...interpreter, `${root}/docket_ship.py`, '--from', file, 'check', '--fix'],
      { timeoutMs: 20000 },
    )
    // Clean, or not a docket-ship project: say nothing, spend no tokens.
    if (checked.exitCode === NOT_A_PROJECT) return undefined
    if (checked.exitCode === 0 && /\b0 errors, 0 warnings\b/.test(checked.stdout)) return undefined
    const stderr = checked.stderr.trim()
    return (
      `docket-ship check after editing ${file} (INDEX.md was regenerated):\n` +
      checked.stdout.trim() +
      (stderr ? `\n${stderr}` : '') +
      '\nFix the errors before finishing; warnings need a fix or a reason.'
    )
  }

  /**
   * The context to add to an edit's result: the check's report after any doc
   * edit with problems, else nothing. The edit already happened, so a failed
   * check must never hide its result.
   */
  const contextAfter = async (
    existing: readonly string[] | undefined,
    file: string,
    run: Run,
    root: string,
    log: (line: string) => void,
  ): Promise<readonly string[] | undefined> => {
    if (!DOC.test(file) || GENERATED.test(file)) return undefined
    try {
      const report = await checkAfterEdit(run, root, file)
      return report ? [...(existing ?? []), report] : undefined
    } catch (error) {
      log(`docket-ship: check did not run: ${String(error)}`)
      return undefined
    }
  }

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || ran.isError) return ran
    const context = await contextAfter(
      ran.context,
      e.file_path,
      (argv, init) => $.process.run(argv, init),
      $.plugin.root,
      line => $.ui.log(line, { to: 'debug' }),
    )
    return context ? { ...ran, context } : ran
  })

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || ran.isError) return ran
    const context = await contextAfter(
      ran.context,
      e.file_path,
      (argv, init) => $.process.run(argv, init),
      $.plugin.root,
      line => $.ui.log(line, { to: 'debug' }),
    )
    return context ? { ...ran, context } : ran
  })
}
