---
id: D-0005
type: decision
title: Copy the conventions into each project and warn on drift
status: accepted
date: 2026-11-12
summary: docs/CONVENTIONS.md is a copy of the tool's file; check warns when they differ.
affects: [distribution, checks]
supersedes: []
superseded_by:
---

## Context

Agents other than Claude Code, and people without docket installed, still need
to read the rules. A copy in each project makes that possible, but copies drift
apart, which is the inconsistency this tool exists to stop.

## Decision

`docket init` copies `CONVENTIONS.md` into `docs/`. `docket check` warns
when the copy differs from the version bundled with the tool, and
`docket init --update` refreshes it.

## Consequences

- Every project can be read without the tool installed.
- Updating the conventions means running one command in each project.
