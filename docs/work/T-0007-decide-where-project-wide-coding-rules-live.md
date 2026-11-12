---
id: T-0007
type: ticket
title: Decide where project-wide coding rules live
status: open
summary: Rules such as "no any" or "forms use TanStack Form" fit neither a spec nor a decision.
specs: []
decisions: []
blocked_by: []
---

## Done when

- A decision records the answer. The options:
  - leave the rules in `CLAUDE.md` / `AGENTS.md`, which agents already load;
  - add a `rules` kind of doc;
  - write each rule as a decision with no `affects`, and generate the agent
    file from them.
- CONVENTIONS.md says where the rules go.

Seen in the taskwyre-web pilot: CLAUDE.md's Conventions section holds about a
dozen rules, each with its rationale. They were left where they are.
