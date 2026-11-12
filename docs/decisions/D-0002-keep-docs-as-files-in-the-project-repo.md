---
id: D-0002
type: decision
title: Keep docs as files in the project repo
status: accepted
date: 2026-11-12
summary: No external tracker; markdown in the repo, with git as the history.
affects: [distribution]
supersedes: []
superseded_by:
---

## Context

A Jira-like service, or GitHub Issues, would need an API or connector,
credentials and network calls in every project, and its history would live apart
from the code.

## Decision

Specs, decisions and tickets are markdown files under `docs/` in each project.

## Consequences

- A decision and the code it caused land in the same commit, and `git log` is
  the audit trail.
- Any agent that can read files can use them, offline and at no cost.
- There's no board view or notifications. That's fine for a solo developer.
