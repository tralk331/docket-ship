---
id: T-0005
type: ticket
title: Support decisions migrated without a known date
status: open
summary: Migrated decisions all got the migration date, which hides when they were really made.
specs: [checks]
decisions: []
blocked_by: []
---

## Done when

- A decision can record that its date is the date it was written down, not when
  it was made. One option is an optional `recorded:` field, with `date:`
  allowed to be just a month (`2026-09`) or left empty.
- `check` and the index handle it.

Seen in the taskwyre-web pilot: all 29 decisions are dated 2026-11-12, though
most were made between September and November.
