# Review Ledger

<!-- schema_version: 1
     A CACHE of review events, NOT a source of truth. Gating truth lives in each phase's
     UAT.md + VERIFICATION.md — the files GSD actually reads. This file records only what
     those cannot: which reviewer ran, over which range, and when.
     A missing or corrupt ledger degrades coverage reporting to UNKNOWN, never to "covered".
     Last updated: 2026-10-05T10:51:40Z -->

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
  },
  {
    "phase": "05",
    "reviewer": "gsd-code-reviewer-deep",
    "base": "c93e045",
    "head": "dc7783d",
    "ran": "2026-09-25T11:45:54Z",
    "findings": 10,
    "consolidated": true,
    "round": 4
  },
  {
    "phase": "06",
    "reviewer": "gsd-code-review-deep",
    "base": "e9eb3c4",
    "head": "2ec34fc",
    "ran": "2026-09-29T06:58:35Z",
    "findings": 24,
    "consolidated": true,
    "round": 1
  },
  {
    "phase": "06",
    "reviewer": "gsd-code-review-deep",
    "base": "2ec34fc",
    "head": "5eae12c",
    "ran": "2026-09-29T12:08:42Z",
    "findings": 11,
    "consolidated": true,
    "round": 2
  },
  {
    "phase": "06",
    "reviewer": "gsd-code-review-deep",
    "base": "29039d5",
    "head": "f5d9037",
    "ran": "2026-09-29T16:42:42Z",
    "findings": 15,
    "consolidated": true,
    "round": 3
  },
  {
    "phase": "06",
    "reviewer": "gsd-code-review-deep",
    "base": "4da8c6c",
    "head": "2a094ed",
    "ran": "2026-09-30T15:42:34Z",
    "findings": 8,
    "consolidated": true,
    "round": 4
  },
  {
    "phase": "07",
    "reviewer": "gsd-code-review-deep+code-review-high",
    "base": "9bb6b51",
    "head": "5ee3c80",
    "ran": "2026-10-02T11:45:57Z",
    "findings": 12,
    "consolidated": true,
    "round": 1
  },
  {
    "phase": "07",
    "reviewer": "gsd-code-review-deep+code-review-high",
    "base": "271b208",
    "head": "d689b6a",
    "ran": "2026-10-02T13:15:11Z",
    "findings": 10,
    "consolidated": true,
    "round": 2
  },
  {
    "phase": "07",
    "reviewer": "gsd-code-review-deep+code-review-high",
    "base": "7094dde",
    "head": "5382353",
    "ran": "2026-10-05T08:33:49Z",
    "findings": 8,
    "consolidated": true,
    "round": 3
  },
  {
    "phase": "07",
    "reviewer": "gsd-code-review-deep+code-review-high",
    "base": "c1b813d",
    "head": "08c8445",
    "ran": "2026-10-05T09:56:11Z",
    "findings": 8,
    "consolidated": true,
    "round": 4
  },
  {
    "phase": "07",
    "reviewer": "gsd-code-review-standard+code-review-high",
    "base": "cb85baa",
    "head": "f3e2787",
    "ran": "2026-10-05T10:51:40Z",
    "findings": 7,
    "consolidated": true,
    "round": 5
  }
]
```
