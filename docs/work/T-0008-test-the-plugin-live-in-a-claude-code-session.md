---
id: T-0008
type: ticket
title: Test the plugin live in a Claude Code session
status: open
summary: Install the plugin and confirm the skills load and the hook reports problems after a doc edit.
specs: [plugin]
decisions: []
blocked_by: []
---

## Done when

- `/plugin install docket-ship --marketplace tralk331/docket-ship` installs it.
- The four skills appear and `decide` resolves the script path from its base
  directory.
- Editing a spec in taskwyre-web to cite a missing id makes the hook's report
  reach the model. A clean edit adds nothing, and an edit outside a docket-ship
  project adds nothing.
