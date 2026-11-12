---
id: distribution
type: spec
title: How docket-ship is packaged and installed
status: active
summary: One Python file plus CONVENTIONS.md; projects keep a copy of the conventions and a docket-ship.cfg.
---

# Packaging and installation

## The tool [D-0003] [D-0006]

`docket_ship.py` and `CONVENTIONS.md` sit side by side in this repo. The script reads
the conventions from its own folder, so the two always travel together. Run it
as `python docket_ship.py`, `python3` or `py -3`.

## In a project [D-0002] [D-0005]

`docket-ship init` sets up:

| Path | What |
| ---- | ---- |
| `docket-ship.cfg` | `docs` folder, `code` roots, `extensions`, `symbols`, `history_phrases` (same header syntax) |
| `docs/CONVENTIONS.md` | Copy of the rules, refreshed by `docket-ship init --update` |
| `docs/INDEX.md` | Generated |
| `docs/spec/`, `docs/decisions/`, `docs/work/` | The three kinds of doc |

The project's `AGENTS.md` or `CLAUDE.md` gets a short section pointing at
`docs/CONVENTIONS.md` and `docs/INDEX.md`. `init` prints that section.

## As a Claude Code plugin [D-0007]

```
/plugin install docket-ship --marketplace tralk331/docket-ship
```

See [plugin](./plugin.md) for what it adds.
