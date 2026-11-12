---
id: T-0006
type: ticket
title: Check references from code into docs
status: open
summary: Code comments name doc paths, section numbers and decision ids that check never sees.
specs: [checks]
decisions: []
blocked_by: []
---

## Done when

- `check` scans the code roots for `docs/...md` paths and `D-NNNN` / `T-NNNN`
  ids, and reports any that don't exist as errors.
- It also warns on a citation of a superseded decision in code.

Seen in the taskwyre-web pilot: 15 code comments pointed at old doc paths or at
section numbers like "seller-onboarding §10.1", and had to be found by hand.
Citing decision ids in code (`decision D-0014`) is what `check` can verify,
because ids are stable and section numbers are not.
