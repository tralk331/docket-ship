---
id: T-0001
type: ticket
title: Claude Code plugin with docs skills
status: doing
summary: Package docket-ship as a user-level Claude Code plugin with skills that apply the workflow.
specs: [distribution]
decisions: []
blocked_by: [T-0002]
---

## Done when

- The plugin bundles `docket_ship.py` and `CONVENTIONS.md`.
- It has these skills:
  - `/decide`: write a decision, find the affected specs, propose the spec edits in the same change.
  - `/ticket`: open, update or close a ticket. Closing requires the spec to be up to date.
  - `/docs-audit`: an agent compares specs with the code to find drift the checker can't see.
  - `/docs-migrate`: convert a project's existing docs into this layout.
- Installed at user level, it works in any project.
