---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 15
subsystem: tracking
tags: [github-issues, owner-approval]
requires: [07-12, 07-03]
provides: [pc2img#24 follow-up comment]
affects: [07-11]
key-files:
  created: []
  modified:
    - .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-ISSUE-NOTES-DRAFT.md
key-decisions:
  - "Owner dropped the GSEGUtils#82 note: upstream issues stay about the upstream defect; pc2img status goes in pc2img#24 only"
  - "#24 comment held until the gap rounds settled, then redrafted for what 0.11.0 ships (fix + two documented limitations, GSEGUtils#83 / 0.11.1)"
  - "#24 closes when 0.11.0 is on PyPI (07-11)"
requirements-completed: []
completed: 2026-10-05
---

# Phase 07 Plan 15: Issue notes for the tiled re-generation race Summary

Task 1 (9fd8660) drafted the #82 note and two #24 variants with a recorded Baseline (#82 OPEN/1 comment, #24 OPEN/0).
Task 2 (owner checkpoint): the owner dropped the #82 note (2026-10-02, 27b758e) and held the #24 comment while the
gap-round reviews showed the drafted fix text was not yet true. After gap rounds 07-12..07-24 the orchestrator
redrafted the comment for the shipped behaviour; the owner approved it verbatim on 2026-10-05 and it was posted:
https://github.com/gseg-ethz/pc2img/issues/24#issuecomment-5994949825 . Pre-post state matched the Baseline
(#24 OPEN, 0 comments); after posting OPEN, 1 comment; read-back identical apart from GitHub's trailing newline.
#82 untouched (still 1 comment). Close of #24 deferred to 07-11 (0.11.0 on PyPI).

## Deviations from Plan

- [Owner decision] #82 note dropped; only #24 posted.
- [Owner decision] Posted text is a redraft (v2), not variant A/B from Task 1; the round counts it quotes come from
  07-12 (before) and 07-16/07-19 (after, arrays read) twelve-round measurements.
- Posting done by the orchestrator, not a continuation executor (one approved `gh issue comment` + read-back).

## Self-Check: PASSED
