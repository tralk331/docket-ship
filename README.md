# docket-ship

Keeps a project's docs consistent across projects and over time. Docs are split
into **specs** (the current design), **decisions** (frozen records, replaced
instead of edited) and **tickets** (all unfinished work), linked by ids that a
checker verifies.

- **The format and rules:** [CONVENTIONS.md](CONVENTIONS.md). This is the file
  agents read, and `init` copies it into each project.
- **This tool's own docs**, written in that format: [docs/INDEX.md](docs/INDEX.md)

## Install in Claude Code

```
/plugin install docket-ship --marketplace tralk331/docket-ship
```

Answer `y` to add the marketplace, then pick a scope (user scope makes it
available in every project). This adds four skills (`/decide`, `/ticket`,
`/docs-audit`, `/docs-migrate`) and a hook that runs `check` after every edit to
a doc, telling Claude only when something is wrong. See
[docs/spec/plugin.md](docs/spec/plugin.md).

## Requirements

Python 3.8 or newer. Nothing else.

## Use

```sh
python path/to/docket_ship.py init            # in a project: creates docket-ship.cfg and docs/
python path/to/docket_ship.py new decision "Use Postgres" --affects storage
python path/to/docket_ship.py check           # exit 1 on errors; --strict fails on warnings too
```

Every command is listed in [CONVENTIONS.md](CONVENTIONS.md#commands). On
Windows, use `python` or `py -3` if `python3` isn't available.

## Develop

```sh
python -m unittest discover -s tests
python docket_ship.py check                   # docket-ship's own docs
claude plugin validate .                      # the plugin manifest and hook
```
