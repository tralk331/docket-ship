---
id: D-0003
type: decision
title: Write the tool as one stdlib-only Python file
status: accepted
date: 2026-11-12
summary: docket.py runs on Python 3.8+ with no dependencies, so it works in non-Node projects such as Godot.
affects: [distribution]
supersedes: []
superseded_by:
---

## Context

The projects span Next.js and Godot, so a Node tool would be wrong for some of
them. A Go or Rust binary needs a build per OS. Shell scripts get fragile when
parsing headers.

## Decision

A single `docket.py` that uses only the standard library and supports Python
3.8+. Headers are a strict YAML subset parsed in-house, so no YAML library is
needed.

## Consequences

- Runs anywhere Python is installed. On Windows the command may be `python` or
  `py -3` rather than `python3`.
- Headers can't nest or span lines. That limit is deliberate: it keeps them
  easy to grep.
