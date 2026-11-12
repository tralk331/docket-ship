---
id: D-0007
type: decision
title: Ship the Claude Code plugin from the tool's own repo
status: accepted
date: 2026-11-12
summary: The repo root is both the plugin and its marketplace, so the script and conventions ship inside it unchanged.
affects: [plugin, distribution]
supersedes: []
superseded_by:
---

## Context

The plugin needs `docket_ship.py` and `CONVENTIONS.md`. A separate plugin repo
would have to copy them, and the copies would drift: the problem the tool
exists to solve.

## Decision

The repo root holds `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` (one entry, `source: "./"`), with the skills
and hooks beside the script.

## Consequences

- Install with `/plugin install docket-ship --marketplace tralk331/docket-ship`.
- Skills find the script relative to their own folder, so they work with no
  configuration.
- Every commit to `main` is a release; the plugin version in `plugin.json`
  should move with the script's `VERSION`.
