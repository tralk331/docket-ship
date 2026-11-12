---
name: ticket
description: Open, start, close, drop or list tickets in a docket-ship project. Use when the user asks to track work, says something is done or abandoned, asks what is left, or when unfinished work, a known bug or a missing test turns up and belongs in a ticket rather than a spec.
---

# Manage tickets

**Running docket-ship:** the script is `docket_ship.py`, two folders above this
skill's base directory. Run it with `python3`, or `python` / `py -3` on Windows,
from the project root. Below, `ds` means that command. If the project has no
`docket-ship.cfg`, offer `ds init` and stop until the user agrees.

Work out the action from the arguments: `open`, `start`, `close`, `drop`, or
nothing (list).

**List.** Run `ds list tickets --open` and show it. Point out any ticket that is
`doing` or blocked.

**Open.**
1. Check it isn't already a ticket: `ds list tickets --open`.
2. Run `ds new ticket "<title>" --specs <spec,spec> [--decisions D-NNNN]`. The
   title says the outcome ("Page the review queue"), not the activity.
3. Under `## Done when`, write concrete, checkable bullets.
4. Set `blocked_by:` if another ticket must land first.

Specs don't mention the ticket; the index links them.

**Start.** Set `status: doing`.

**Close.** Before setting `status: done`:
1. Check each "Done when" bullet against the code. If one isn't met, say which
   and keep the ticket open.
2. Compare the implementation with the specs in `specs:`. If the code
   deliberately differs from the spec, that is a decision: hand it to the
   `decide` skill. If the spec was just incomplete, fix the spec.
3. Add one line under `## Outcome`: what shipped, and anything deferred (which
   becomes a new ticket).

**Drop.** Set `status: dropped` and give the reason under `## Outcome`.

After any change, run `ds check` until it reports 0 errors, then report the
ticket id and its new status.
