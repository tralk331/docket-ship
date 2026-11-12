---
id: checks
type: spec
title: What docket-ship check verifies
status: active
summary: Every rule docket-ship check enforces, with its level; errors fail the run.
---

# What `docket-ship check` verifies

Output is one `path:line: level: message` per issue. The exit code is 1 on
any error, or on any warning with `--strict`. Implemented in `check` in
[docket_ship.py](../../docket_ship.py).

## Headers and ids

| Rule | Level |
| ---- | ----- |
| Header present, closed, and every line parses as `key: value` or `key: [a, b]` | error |
| Required keys per type are present; status and `date` are valid | error |
| `type` matches the folder; ids match the type's pattern; ids are unique | error |
| A spec id equals its filename; a decision or ticket filename starts with its id | error |
| Unknown header keys | warning |

## Links between docs [D-0001]

| Rule | Level |
| ---- | ----- |
| `affects`, `supersedes`, `specs`, `decisions`, `blocked_by` and `tickets` name docs that exist, of the right kind | error |
| `superseded` ⇔ `superseded_by` is set, and both sides agree | error |
| An accepted decision's `supersedes` targets are marked superseded by it | error |
| A spec cites a superseded or rejected decision | error |
| A spec cites a proposed decision | warning |
| An accepted decision is not cited in a spec it `affects` | warning |
| A spec cites a ticket | warning |
| A cited id (outside backticks) doesn't exist; a relative markdown link doesn't resolve | error |
| An open ticket implements a retired spec | warning |

## Spec prose [D-0004]

These run on specs only, skip fenced code, and skip lines marked
`docket-ship:ignore`.

| Rule | Level |
| ---- | ----- |
| A phrase from `history_phrases` in `docket-ship.cfg` (status or history wording) | warning |
| A backticked path (with a `/` and an extension) that isn't in the project or the code roots | warning |
| A backticked camelCase, PascalCase or snake_case name that doesn't appear in any code file | warning |

The code-reference warnings say so when the spec has open tickets, since the
code may simply not be built yet. Symbols are only checked when `code` is set
and `symbols: true`. See `is_distinctive` for which names count.

## Generated and copied files [D-0005]

| Rule | Level |
| ---- | ----- |
| `docs/INDEX.md` matches what `docket-ship index` would write | error |
| `docs/CONVENTIONS.md` is present and matches the tool's copy | warning |
