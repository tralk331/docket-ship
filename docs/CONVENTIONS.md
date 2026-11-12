<!-- docket-ship-conventions v1 -->
# Docs conventions (docket-ship)

Project docs come in three kinds. Each kind holds one sort of information, and
they link to each other by ID, so the `docket-ship` tool can check that they agree.
Read `docs/INDEX.md` first. It lists every doc in one line each, so you only
need to open what is relevant.

| Kind | Folder | Holds | Changes how |
| ---- | ------ | ----- | ----------- |
| **Spec** | `docs/spec/<slug>.md` | The accepted design of one area: what the code should do | Edited in place, always current |
| **Decision** | `docs/decisions/D-NNNN-<slug>.md` | One choice: its context, what was chosen, and the consequences | Frozen once accepted; replaced by a new decision, never rewritten |
| **Ticket** | `docs/work/T-NNNN-<slug>.md` | Work that is not done: build, fix, test, investigate | Status changes until `done` or `dropped` |

## The rules that keep docs from going stale

1. **A spec states only the current design.** It has no history ("previously",
   "used to"), no status ("not built yet", "verified on …") and no record of
   decisions ("we decided …"). History lives in decisions, and status lives in
   tickets.
2. **A spec cites the decision behind each choice**, inline, like this:
   `Orders take no payment. [D-0014]`. This is what makes a later change
   traceable to its cause.
3. **A decision is never rewritten after it is accepted.** To change course,
   write a new decision with `supersedes: [D-0014]`, run
   `docket-ship supersede D-0014 D-0020`, and then update every spec paragraph that
   cites D-0014. Do this in the same change.
4. **Work that isn't done is a ticket**, never a note in a spec. That includes
   unbuilt features, missing tests, known bugs and open questions. A ticket
   lists the specs it implements in `specs:`. Close it by setting `status: done`
   once the code matches the spec.
5. **Specs don't reference tickets.** Tickets point at specs. The index shows
   each spec's open tickets, worked out from the files, so that list is never
   stale.
6. **Get IDs from `docket-ship new`**, and after editing, run `docket-ship check`. The
   check rebuilds nothing; it reports problems. `docket-ship index` regenerates
   `docs/INDEX.md`, which is never edited by hand.

## Frontmatter

Every doc begins with a header in a strict subset of YAML: one `key: value` per
line, and lists only in the inline form `[a, b]`. Use no nesting, no multi-line
values and no quotes unless the value contains `: `.

**Spec**

```yaml
---
id: orders                # equals the filename without .md
type: spec
title: Orders
status: draft             # draft (being designed) | active | retired
summary: One line, written to be read in the index.
---
```

**Decision**

```yaml
---
id: D-0014
type: decision
title: Order flow v1 takes no payments
status: accepted          # proposed | accepted | rejected | superseded
date: 2026-11-12
summary: One line.
affects: [orders]         # spec ids this decision shapes
supersedes: []            # decisions this replaces
superseded_by:            # set only by `docket-ship supersede`
tickets: []               # optional: the work it creates
---
```

The body has three sections, `## Context`, `## Decision` and `## Consequences`,
and should usually stay under 40 lines.

**Ticket**

```yaml
---
id: T-0031
type: ticket
title: Build order flow v1
status: open              # open | doing | done | dropped
summary: One line.
specs: [orders]           # specs this implements or fixes
decisions: [D-0014]       # optional
blocked_by: []            # optional: ticket ids
---
```

The body says what "done" means. When closing a ticket, add one line under
`## Outcome`.

## Writing style

These docs are read by agents as much as by people, so tokens count.

- Use the short form: tables and lists over paragraphs, one fact in one place.
  Link to a fact rather than repeating it.
- Name code by path and symbol (`src/orders/hooks.ts`, `governOrder`). The
  checker warns when a named path or symbol no longer exists in the code.
- One spec covers one area. Split a spec at roughly 300 lines.
- If a sentence in a spec has to mention status or history (rare), end the line
  with `<!-- docket-ship:ignore -->`.
- An id in backticks (`` `D-0042` ``) is an example, not a citation, and isn't
  checked. Code comments cite decisions by id ("decision D-0014"), never by
  section number.

## Commands

```
docket-ship check [--strict]        validate everything; exit 1 on errors (and on warnings with --strict)
docket-ship index                   regenerate docs/INDEX.md
docket-ship new decision "Title" [--affects a,b] [--supersedes D-0003]
docket-ship new ticket "Title" [--specs a,b] [--decisions D-0001]
docket-ship new spec <slug> "Title"
docket-ship list [specs|decisions|tickets] [--status s] [--open]
docket-ship refs <ID>               every place an id is cited
docket-ship supersede <OLD> <NEW>   mark OLD superseded and list the specs to update
docket-ship init                    set up docs/ and this file in a project
```

Run it as `python <path>/docket_ship.py …`, or `python3` or `py -3`, depending on
the platform.
