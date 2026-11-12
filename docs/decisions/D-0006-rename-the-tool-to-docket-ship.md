---
id: D-0006
type: decision
title: Rename the tool to docket-ship
status: accepted
date: 2026-11-12
summary: "docket" is already the name of several existing tools; the project is docket-ship.
affects: [distribution]
supersedes: []
superseded_by:
---

## Context

"docket" is already used by several existing projects, which makes the tool
hard to search for and risks clashing command names.

## Decision

The project, repo and command are `docket-ship`. The script is `docket_ship.py`
(an underscore, so it stays importable), the config is `docket-ship.cfg`, and
the ignore marker is `docket-ship:ignore`.

## Consequences

- Decisions D-0001 to D-0005 still say "docket": they are frozen records and
  were true when they were written.
- Projects set up before the rename rename `docket.cfg` and run
  `docket-ship init --update`.
