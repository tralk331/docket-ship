---
id: T-0003
type: ticket
title: Warn when an accepted decision is edited
status: open
summary: Use git to flag changes to the body of a decision that was already accepted at HEAD.
specs: [checks]
decisions: []
blocked_by: []
---

## Done when

- `docket-ship check` asks git (when it's available) whether an accepted decision
  changed since HEAD, apart from `status` and `superseded_by`, and warns if so.
- Without git, it skips this check silently.
