---
id: T-0004
type: ticket
title: Install docket-ship for use outside Claude Code
status: open
summary: A one-step install that puts a docket-ship command on PATH, on Windows and Unix.
specs: [distribution]
decisions: []
blocked_by: []
---

## Done when

- `docket-ship` (with `docket.cmd` on Windows) runs the script with whichever
  Python is available.
- The README explains installing it and running it in CI.
