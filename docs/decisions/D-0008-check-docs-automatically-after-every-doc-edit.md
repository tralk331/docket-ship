---
id: D-0008
type: decision
title: Check docs automatically after every doc edit
status: accepted
date: 2026-11-12
summary: A hook runs check --fix after Edit or Write on docs/*.md and tells the model only when something is wrong.
affects: [plugin]
supersedes: []
superseded_by:
---

## Context

The conventions rely on `check` being run, and agents forget to run it. On
taskwyre-web a full check takes about 0.35 s.

## Decision

A hooks module runs `docket_ship.py --from <file> check --fix` after every
successful `Edit` or `Write` to a markdown file under a `docs/` folder, except
`INDEX.md`. `--fix` regenerates the index first, because a stale index after an
edit is expected, not an error. The report reaches the model as context on that
tool result, and only when there are errors or warnings. Outside a docket-ship
project (exit code 3), or with no Python 3, the hook does nothing.

## Consequences

- Problems surface at the edit that caused them, not at the end of a task.
- A clean edit costs no tokens.
- The hook needs Claude Code's function-hooks engine (hooks modules). Other
  agents still run `check` themselves, as CONVENTIONS.md says.
