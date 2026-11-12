---
id: D-0001
type: decision
title: Split docs into specs, decisions and tickets
status: accepted
date: 2026-11-12
summary: Each kind of information gets one home, linked by ids a script can check.
affects: [checks]
supersedes: []
superseded_by:
---

## Context

AI-written project docs mix four things in one file: the current design, the
decisions behind it, build status ("not built yet") and history ("previously").
Status and history go stale as soon as work moves on, and when a decision
changes, nothing points at the other places that stated the old fact. Each
project also ends up with a different format.

## Decision

Three kinds of doc, each with one job: specs (the current design), decisions
(frozen records, replaced instead of edited) and tickets (all unfinished work).
They link by id: specs cite decisions inline, and tickets list their specs.
Every doc has a fixed header.

## Consequences

- When a decision is superseded, its citations show which spec paragraphs to
  update, mechanically.
- Agents read a generated one-line-per-doc index and open only what they need.
- More files than before. `docket new` hands out ids so agents don't collide.
