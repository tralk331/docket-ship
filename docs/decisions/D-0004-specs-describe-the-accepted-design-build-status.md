---
id: D-0004
type: decision
title: Specs describe the accepted design; build status lives in tickets
status: accepted
date: 2026-11-12
summary: A spec says what the code should do; whether it does yet is an open ticket.
affects: [checks]
supersedes: []
superseded_by:
---

## Context

The workflow writes docs first and implements from them, so a spec often
describes code that doesn't exist yet. If specs had to match the code, they
would fill up with "not built yet" notes, which go stale.

## Decision

A spec is the accepted design. Unbuilt parts are open tickets that list the spec
in `specs:`. The index shows each spec's open tickets, worked out from the
files.

## Consequences

- Phrases such as "not yet" in a spec are a warning.
- A path or symbol a spec names but the code lacks is a warning, not an error.
  For a spec with open tickets, the message says it may be planned work.
