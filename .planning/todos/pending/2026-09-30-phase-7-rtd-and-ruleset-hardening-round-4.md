---
created: 2026-09-30T15:50:00Z
title: Phase 7 — RTD tag-fetch hardening (release precondition) and ruleset-comparator follow-ups from Phase-6 review round 4
area: ci
severity: minor
resolves_phase: 7
files:
  - .readthedocs.yaml
  - .github/scripts/ruleset_lib.py
  - .github/scripts/test_ruleset_lib.py
  - RULESETS.md
source: 06-REVIEW.md round 4 (commit 2a094ed; review of fix diffs fb44899 + e9a3a98), consolidated into 06-UAT.md as review-r4-* (owner dispositions 2026-09-30)
---

## Why

Phase 6's round-4 review of its two late fixes found no breaking defect but eight
hardening items. The owner deferred all eight to Phase 7 and made the three
Read the Docs items a **precondition of the 0.11.0 promotion**: the release is the
moment `release-please.yml` moves the floating `v0`/`v0.10` tags, which is exactly
when WR-02 bites.

## Before the 0.11.0 promotion (release gate)

- [ ] **WR-02** — `.readthedocs.yaml`: `git fetch --tags` → `git fetch --tags --force`.
      Reproduced failure: `! [rejected] v0 -> v0 (would clobber existing tag)`, build exits 1.
- [ ] **WR-03** — unshallow only when `git rev-parse --is-shallow-repository` is true,
      without `|| true`. Reproduced failure: skipped unshallow on develop-gsd gives a
      silently wrong `0.10.4.post344` (true value post473) on a green build.
- [ ] **WR-04** — add a `post_install` job asserting the installed version does not start
      with `0.0.` and the clone is not shallow (the CI docs job already has the `0.0.` guard;
      RTD build 34851945 rendered `0.0.post41` and went green).

## Anytime in Phase 7

- [ ] **WR-01** — owner policy: keep normalising the read-filled keys; add one line to
      RULESETS.md naming the five fields the apply does not govern
      (`allowed_merge_methods`, `dismissal_restriction`, `required_reviewers`,
      `require_extra_approval_for_unattributed_changes`, `do_not_enforce_on_create`).
- [ ] **IN-01** — update the live fixture to measured shapes (`dismissal_restriction`
      `{"enabled": false, "allowed_actors": []}`, no `integration_id` after an apply); keep one
      UI-created case with `integration_id: 15368`.
- [ ] **IN-02** — reword the rule (c) docstring/record: live omits `integration_id` after an apply.
- [ ] **IN-03** — parametrise the "read-filled key survives when committed sets it" test over
      both read-filled tuples.
- [ ] **IN-04** — name the rule (d) keys (or the two tuples) in the `normalize` contract docstring.

## Procedure reminder

Each fix reaches `main` only through a promotion PR, and every promotion needs the
back-merge in RELEASE.md "Releasing" step 2 (skipping it broke ancestry once in Phase 6,
issue #21). The fixes get their own review before the promotion (global review rule).
