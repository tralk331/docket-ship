---
name: docs-migrate
description: Convert a project's existing documentation into docket-ship's specs, decisions and tickets. Use when the user wants to adopt docket-ship in a project that already has design docs, ADRs, a docs/ folder or long README sections.
---

# Migrate existing docs

**Running docket-ship:** the script is `docket_ship.py`, two folders above this
skill's base directory. Run it with `python3`, or `python` / `py -3` on Windows,
from the project root. Below, `ds` means that command. Read the script's
`CONVENTIONS.md` (beside it) before starting.

Work on a branch, and have the user confirm the plan before writing files.

1. **Read every existing doc in full.** Note which other docs, `CLAUDE.md` /
   `AGENTS.md`, the README and the code reference.
2. **Sort the content into the three kinds:**
   - current design → **specs**, one per area. Split out general mechanisms
     (a notifications system, an auth model) that several docs share.
   - why something was chosen: sections such as "Decisions", "Resolved
     questions", "Why not X", "Accepted limitations", and rationale paragraphs
     → **decisions**.
   - anything unfinished: "not yet", "later", "TODO", "not covered", "verified
     on", deferred features, missing tests → **tickets**.
   - history ("previously", "first draft", "rename completed") → drop it, or
     put it in a decision's Context.
3. **Show the plan**: specs by name, decisions by title, tickets by title, and
   anything you can't place. Wait for the user's go-ahead.
4. **Set up:** run `ds init`, then set `code:` in `docket-ship.cfg` to the
   source folders (and message catalogs, if code names live there).
5. **Write decisions in bulk.** With dozens of files, write a short generator
   script in a scratch folder that emits the header format, rather than calling
   `ds new` once per file. Number them `D-0001…` in a sensible order. Their
   real dates are usually unknown: use today's date, and say so in the report.
6. **Write the specs.** Keep facts, drop status and rationale, and cite the
   decision behind each choice: `... [D-NNNN]`. Every spec needs a header and a
   one-line summary.
7. **Write the tickets**, each with concrete "Done when" bullets. A checklist
   that only existed in chat or in a "not covered" section goes into the
   ticket's body.
8. **Retire the old docs** (`git rm`), then fix every reference to them: agent
   files, the README, and code comments (search for the old file names and for
   section references like "§10.1"). Code comments cite decision ids
   ("decision D-0014"), not section numbers.
9. **Add the docs section** that `ds init` printed to `CLAUDE.md` / `AGENTS.md`.
10. **Run `ds check`** until it reports 0 errors. Read every warning: "affects
    this spec but is not cited" usually means a missed paragraph.

Report:
- counts of specs, decisions and tickets;
- references fixed;
- what you dropped as history;
- anything you had to guess, such as decision dates or how something was
  classified.
