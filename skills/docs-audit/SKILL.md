---
name: docs-audit
description: Audit a docket-ship project's specs against the code and report drift the checker cannot see - behaviour, rules, routes or states a spec describes differently from what the code does. Use when the user asks whether docs are current, before a release, or after a large change.
---

# Audit specs against the code

**Running docket-ship:** the script is `docket_ship.py`, two folders above this
skill's base directory. Run it with `python3`, or `python` / `py -3` on Windows,
from the project root. Below, `ds` means that command.

The checker already verifies ids, links, paths and code names. This audit
checks **meaning**: does the code do what the spec says?

1. Run `ds check` and fix its errors first, so the audit starts from clean
   links.
2. Choose the scope: the specs named in the arguments, or every `active` spec
   in `docs/INDEX.md`. Do one spec at a time.
3. For each spec, list its concrete claims, such as:
   - fields, states and transitions
   - endpoints and their errors
   - access rules
   - routes and UI behaviour

   Find the code for each claim and compare. Skip a claim only if you can't
   find its code in a reasonable search, and list it as unverified.
4. Remember that a spec describes the accepted design. Code that doesn't exist
   yet isn't drift if an open ticket covers it: check `ds refs <spec>` for the
   spec's open tickets.

**Report** each finding with the spec line, the code location, what each says,
and the kind of fix:

| Kind | Fix |
| ---- | --- |
| Spec is wrong; the code reflects a deliberate change | A decision (`decide` skill), then the spec |
| Spec is wrong; it was just stale or incomplete | Edit the spec |
| Code is wrong | A ticket (`ticket` skill) |
| Can't tell | Ask the user |

Don't change code during an audit. Apply spec fixes only after the user agrees
to them. End with counts: claims checked, findings by kind, and claims left
unverified.
