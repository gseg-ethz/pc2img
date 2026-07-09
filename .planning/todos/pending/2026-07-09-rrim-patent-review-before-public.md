---
created: 2026-07-09T00:00:00.000Z
title: BLOCKING — investigate RRIM patent/IP situation before rrim.py goes public
area: legal-ip
severity: blocking
blocks: publication
resolves_phase: 6
files:
  - src/pc2img/features/rrim.py
source: .planning/phases/03-test-ci-foundation/03-02-SUMMARY.md (owner-raised during Phase 3 execution)
---

## Problem

`src/pc2img/features/rrim.py` was brought under version control during Phase 3
(Plan 03-02, commit `019e9ed`) so that its filesystem-loaded test
(`tests/test_rrim_features.py`) can run on a fresh CI checkout. The module was
committed **unchanged** — no behavior change — but committing it means the code
now lives in this repo's git history on the `gsd/phase-03-test-ci-foundation`
branch, and will squash onto `main` at milestone ship.

**The owner has flagged a reported patent / IP situation around the RRIM (Red
Relief Image Map) technique.** RRIM is associated with prior-art patents held by
a third party (reported: Asia Air Survey Co., Ltd. — needs confirmation). This
has NOT been legally investigated. Until it is, `rrim.py` must not be pushed to
any public remote or merged onto a public `main`.

### Risk boundary (important)

- Committing to this **private phase branch** is version control, not
  publication — acceptable for now.
- The exposure is the **public push**: `main` is only exposed at milestone ship
  (Phase 6 — Publication Hardening + branch protection). Even if `rrim.py` is
  later removed from the `main` tree, git *history* on any pushed branch would
  still carry it. So resolution must happen **before the first public push**,
  and if removal is required it must be a history-level decision, not just a
  working-tree delete.

## Required before publication (Phase 6 gate)

1. Investigate the RRIM patent situation (identify the specific patent(s),
   jurisdictions, claims, and whether this implementation infringes or is
   covered by an exception / expiry / license).
2. Decide one of:
   - **Keep + license/attribute** — if clear to publish (e.g. patent expired,
     licensed, or non-infringing), document the basis in CONTRIBUTING/NOTICE.
   - **Gate/optional-extra** — ship behind an explicit opt-in with a legal note.
   - **Remove before public** — strip `rrim.py` (and its test) from the public
     `main` AND from the history of any branch that gets pushed publicly
     (filter/rewrite, not just a delete commit). Note this also removes the
     `rrim` feature from the public feature set — coordinate downstream.
3. Do NOT let Phase 6 publication CI/CD or branch-protection setup proceed to a
   public push until this is resolved.

## Notes

- This is separate from the code-quality review of `rrim.py` (Phase 4) — that is
  a correctness/hygiene concern; this is an IP/publication concern.
- `rrim.py` is not currently wired into any tracked `src/**/__init__.py`, so it
  is loaded only by its test via filesystem path — worth confirming its intended
  public API status as part of the same review.
