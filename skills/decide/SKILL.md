---
name: decide
description: Record a decision in a docket-ship project and update every spec it affects in the same change. Use when the user makes or changes a design, architecture or product decision ("let's use X", "we decided", "change of plan"), or asks to record one.
---

# Record a decision

**Running docket-ship:** the script is `docket_ship.py`, two folders above this
skill's base directory. Run it with `python3`, or `python` / `py -3` on Windows,
from the project root. Below, `ds` means that command. If the project has no
`docket-ship.cfg`, offer `ds init` and stop until the user agrees.

Read `docs/CONVENTIONS.md` and `docs/INDEX.md` first if they aren't in context.
The decision to record is in the arguments or the conversation. If it is
unclear what was decided, ask in one question.

1. **Find what it touches.** Using the index, pick the specs it affects. Check
   whether it replaces an earlier decision: `ds list decisions --open`, then
   `ds refs <id>` for any candidate.
2. **Create it:** `ds new decision "<title>" --affects <spec,spec> [--supersedes D-NNNN]`.
   The title states the choice ("Orders take no payment in v1"), not the topic.
3. **Write the body** in under 40 lines:
   - **Context:** what forces the choice.
   - **Decision:** what we do.
   - **Consequences:** what follows, good and bad.

   Set `status: accepted` if the user has made the call; leave it `proposed` if
   they're still weighing it, and say so.
4. **If it replaces a decision**, once accepted run `ds supersede <OLD> <NEW>`.
   It lists the spec paragraphs that cite the old decision. Every one must be
   rewritten.
5. **Update the specs now**, in the same change. Rewrite the affected
   paragraphs to describe the new design and cite the decision inline:
   `... [D-NNNN]`. A spec states the current design only, with no "previously"
   and no "we decided". If an area has no spec yet, create one:
   `ds new spec <slug> "<Title>"`.
6. **If it creates work**, open tickets (`ds new ticket "<title>" --specs ... --decisions D-NNNN`)
   and list them in the decision's `tickets:`.
7. **Run `ds check`** until it reports 0 errors. Treat "affects this spec but
   is not cited" as a missed paragraph, not noise.

Report the decision id, the specs changed and the tickets opened, in three
lines.
