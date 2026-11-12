---
id: T-0002
type: ticket
title: "Pilot: migrate taskwyre-web docs"
status: done
summary: Convert taskwyre-web's seven docs to specs, decisions and tickets as the first real test.
specs: []
decisions: []
blocked_by: []
---

## Done when

- Each doc's "Decisions", "Resolved questions" and "Accepted limitations"
  sections become decision records.
- Each "Not yet covered" section and each deferred item becomes a ticket.
- What's left becomes specs that cite their decisions.
- `docket check` passes with no errors.
- Whatever the migration showed should change in docket becomes tickets here.

## Outcome

Seven docs became 9 specs, 29 decisions and 13 tickets, and `check` passes with
no errors or warnings. An agent's entry point dropped from about 90k characters
of docs to an 8.5k index plus the specs it needs. The findings are T-0005
(dates), T-0006 (references from code) and T-0007 (coding rules). The
"used to" phrase was narrowed to "used to be" after a false positive. For
T-0001: writing about 40 files was only practical through a generator script,
so `/docs-migrate` should batch-create docs rather than call `new` once per
file.
