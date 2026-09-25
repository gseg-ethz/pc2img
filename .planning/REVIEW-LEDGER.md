# Review Ledger

<!-- schema_version: 1
     A CACHE of review events, NOT a source of truth. Gating truth lives in each phase's
     UAT.md + VERIFICATION.md — the files GSD actually reads. This file records only what
     those cannot: which reviewer ran, over which range, and when.
     A missing or corrupt ledger degrades coverage reporting to UNKNOWN, never to "covered".
     Last updated: 2026-09-25T07:41:26Z -->

```json
[
  {
    "phase": "05",
    "reviewer": "gsd-code-reviewer-deep",
    "base": "e6e5bcc87",
    "head": "9631ad3",
    "ran": "2026-07-28T09:53:00Z",
    "findings": 10,
    "consolidated": true,
    "round": 1
  },
  {
    "phase": "05",
    "reviewer": "gsd-code-reviewer-deep",
    "base": "e6e5bcc87",
    "head": "3897237",
    "ran": "2026-07-28T14:09:45Z",
    "findings": 11,
    "consolidated": true,
    "round": 2
  },
  {
    "phase": "05",
    "reviewer": "gsd-code-reviewer-deep",
    "base": "443d390",
    "head": "c93e045",
    "ran": "2026-09-25T07:41:26Z",
    "findings": 14,
    "consolidated": true,
    "round": 3
  }
]
```
