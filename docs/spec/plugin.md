---
id: plugin
type: spec
title: The Claude Code plugin
status: active
summary: Four skills (decide, ticket, docs-audit, docs-migrate) and a hook that checks docs after every edit.
---

# The Claude Code plugin

The repo root is the plugin and its marketplace [D-0007]:

| Path | What |
| ---- | ---- |
| `.claude-plugin/plugin.json` | Manifest, name `docket-ship` |
| `.claude-plugin/marketplace.json` | One entry, `source: "./"` |
| `skills/<name>/SKILL.md` | The four skills |
| `hooks/hooks.json`, `hooks/register.ts` | The check-after-edit hook |

## Skills

Each skill finds the script two folders above its own base directory, and
offers `init` when the project has no `docket-ship.cfg`.

| Skill | Does |
| ----- | ---- |
| `decide` | Writes a decision, supersedes the old one if needed, and updates every affected spec in the same change, citing the new id |
| `ticket` | Opens, starts, closes, drops or lists tickets. Closing checks "Done when" against the code and the spec against the implementation |
| `docs-audit` | Compares each spec's claims with the code and reports drift by kind of fix; changes no code |
| `docs-migrate` | Turns existing docs into specs, decisions and tickets, confirming the plan first, writing decisions in bulk and fixing references from code |

## Hook [D-0008]

`hooks/register.ts` hooks `tool.call` for `Edit` and `Write`:

- It acts after a successful call on a `.md` file under a `docs/` folder,
  except `INDEX.md`.
- It finds Python 3 once per load (`python3`, then `python`, then `py -3`),
  probing each with `--version`.
- It runs `docket_ship.py --from <file> check --fix`.
- It adds the report to the result's `context`, and only when the check isn't
  clean. Exit code 3 (not a docket-ship project), no Python, or a failed run
  adds nothing; a failed run is logged to the debug log.
