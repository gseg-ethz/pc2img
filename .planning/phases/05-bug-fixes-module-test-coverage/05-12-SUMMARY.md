---
phase: 05-bug-fixes-module-test-coverage
plan: 12
subsystem: infra
tags: [coverage, ci, ratchet, BC-01, D-17, D-10, D-03, requirements, phase-close]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: "All 11 prior Phase-5 plans (05-01..05-11): every fix + coverage plan landed, full suite green at 109 passed / 0 xfailed; each plan recorded its D-17 BC delta"
provides:
  - "Ratcheted CI --cov-fail-under floor 35 -> 55 (measured whole-package branch coverage 57.17%, Phase-3 ~2pt margin convention)"
  - "CONTRIBUTING.md coverage baseline updated to 57% measured 2026-07-11, floor 55"
  - "05-BC-NOTES.md — consolidated BC-01 running note (11 changes) collated from every Phase-5 SUMMARY, GSD-consumable by Phase-6 BC-01 without git-diff reconstruction"
  - "REQUIREMENTS.md traceability: PERF-02 + PERF-03 mapped to Phase 5 (D-03 pull-forward), BUG-05 closed"
affects: [phase-6-BC-01, phase-6-CICD-02, phase-6-D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Coverage floor as a regression ratchet on the CI CLI only (never addopts/TOML), ratcheted to measured-baseline-minus-margin at phase close (Phase-3 D-05/D-10 convention)"
    - "Consolidated per-phase BC running note collated from plan SUMMARYs at phase close, so the downstream-migration requirement consumes one artifact instead of reconstructing from diffs (D-17)"

key-files:
  created:
    - ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md"
  modified:
    - ".github/workflows/ci.yml — --cov-fail-under 35 -> 55 + comment"
    - "CONTRIBUTING.md — Coverage baseline section (57% / floor 55 / 2026-07-11)"
    - ".planning/REQUIREMENTS.md — PERF-02/PERF-03 traced to Phase 5, v2 Performance annotated, BUG-05 closed"

key-decisions:
  - "New floor = 55 = measured baseline 57 minus the Phase-3 2-point margin; the margin is retained as ratchet headroom even though the suite now carries 0 xfails (no more xfail-volatility to absorb)"
  - "Did NOT overshoot the measured baseline — floor 55 < 57.17% measured, so the ratchet keeps CI green (verified exit 0)"
  - "Kept the gate on the CI CLI only, not addopts/TOML (Phase-3 D-05), so local subset runs stay fast"
  - "BUG-05 closed: multi-plan requirement, all contributing fixes (05-02..05-07, 05-09..05-11) + the 05-08 hook landed with proving tests"
  - "PERF-02/PERF-03 pull-forward recorded forward-only: v2 Performance entries annotated as pulled-forward rather than deleted (D-03), with new Traceability rows"

patterns-established:
  - "Phase-close plan re-measures coverage, ratchets the floor, and collates the BC running note as the completion gate"

requirements-completed: [BUG-05, TEST-03, TEST-04, TEST-05, TEST-06]

coverage:
  - id: D1
    description: "Full suite green and coverage re-measured; CI --cov-fail-under ratcheted to a regression floor at/below achieved coverage (D-10)"
    requirement: "TEST-03"
    verification:
      - kind: integration
        ref: "uv run --frozen pytest tests/ --cov=pc2img --cov-branch --cov-fail-under=55 -> 109 passed, Total coverage 57.17%, exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "No residual xfail cites a finding fixed this phase (BUG-01..05, DSN-02/06/08/09/10/11, M-02/03/04/05/08); suite carries 0 xfails"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "grep -rEn -A6 'pytest.mark.xfail' tests/ | grep -E 'BUG-0[1-5]|DSN-(02|06|08|09|10|11)|M-0[23458]' -> empty (SWEEP CLEAN); no xfail markers exist at all"
        status: pass
    human_judgment: false
  - id: D3
    description: "05-BC-NOTES.md consolidates every Phase-5 BC/behavior/format/error-type/param change for direct Phase-6 BC-01 consumption, incl. the GSEGUtils git-rev bridge + Phase-6 conversion action"
    requirement: "BC-01"
    verification:
      - kind: unit
        ref: "test -s 05-BC-NOTES.md && grep -qi npy 05-BC-NOTES.md -> bc-notes-ok (11 change classes + summary table + Phase-6 conversion block)"
        status: pass
    human_judgment: false
  - id: D4
    description: "REQUIREMENTS.md traceability maps PERF-02 and PERF-03 to Phase 5 (D-03 pull-forward), forward-only annotation of the v2 Performance entries"
    requirement: "BC-01"
    verification:
      - kind: unit
        ref: "grep -Eq 'PERF-02.*Phase 5' && grep -Eq 'PERF-03.*Phase 5' .planning/REQUIREMENTS.md -> both present"
        status: pass
    human_judgment: false

# Metrics
duration: 12min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 12: Phase Close — Coverage Ratchet + Consolidated BC-01 Notes Summary

**Closed Phase 5: re-measured whole-package branch coverage at 57.17% (109 passed / 0 xfailed), ratcheted the CI `--cov-fail-under` floor 35 → 55 without overshooting the baseline, consolidated all eleven Phase-5 breaking-change deltas into `05-BC-NOTES.md` for Phase-6 BC-01 (incl. the GSEGUtils git-rev bridge conversion), and finalized REQUIREMENTS traceability (PERF-02/PERF-03 → Phase 5, BUG-05 closed).**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-11
- **Completed:** 2026-07-11
- **Tasks:** 2 auto
- **Files created:** 1 (`05-BC-NOTES.md`)
- **Files modified:** 3 (`ci.yml`, `CONTRIBUTING.md`, `REQUIREMENTS.md`)

## Accomplishments

- **Coverage re-measured (D-10):** `uv run --frozen pytest tests/ --cov=pc2img --cov-branch` → **109 passed, 0 xfailed, total coverage 57.17%** (whole-package branch). Confirmed green with every Phase-5 proving/characterization test passing.
- **xfail residual sweep CLEAN:** grepping `pytest.mark.xfail` reasons for any finding fixed this phase (BUG-01..05, DSN-02/06/08/09/10/11, M-02/03/04/05/08) returns nothing — the suite in fact carries **no xfail markers at all**. The only permitted deferral (M-13 near-axis ray sampling, D-16) is not present as an xfail; kept-behavior findings (M-06/M-10/M-11) are passing characterization tests, not xfails.
- **CI floor ratcheted 35 → 55:** raised `--cov-fail-under` in `ci.yml` to `55` = measured 57% minus the Phase-3 ~2-point margin convention; verified the suite still passes at the new floor (`--cov-fail-under=55` → `Required test coverage of 55% reached. Total coverage: 57.17%`, exit 0). The gate stays on the CI CLI only (not `addopts`/TOML), per Phase-3 D-05.
- **CONTRIBUTING.md baseline updated:** new measured baseline 57%, floor 55, date 2026-07-11, with the ratchet history (37% → 57%) and margin rationale retained.
- **`05-BC-NOTES.md` consolidated (D-17):** eleven changes collated from every Phase-5 SUMMARY, each with symbol / old→new / migration note, plus a summary table — GSD-consumable so Phase-6 BC-01 does not reconstruct from git diffs. Includes all six change classes the plan named plus the wrapping-FoV raise, the PerspectiveProjection 4×4 TypeError, the `DiskBackedImageData` arithmetic surface, and the DSN-08 dependency-cycle `ValueError`. The **GSEGUtils public `register_lazy_disk_cache_class` hook + the temporary `[tool.uv.sources]` git-rev bridge @ `2cf80835`** is documented with the explicit **Phase-6 conversion action** (merge branch → release-please 0.6.0 → bump `GSEGUtils ~= 0.6` → drop the git entry → re-lock).
- **REQUIREMENTS finalized (D-03):** added Traceability rows mapping PERF-02 → Phase 5 and PERF-03 → Phase 5; forward-only annotation of the v2 `### Performance` PERF-02/PERF-03 lines as "pulled forward into Phase 5 (D-03)"; adjusted the coverage tally note; closed **BUG-05** (multi-plan, all contributing fixes landed).

## Task Commits

1. **Task 1: re-measure coverage + ratchet CI floor** — `d1159a6` (`ci(coverage): ratchet --cov-fail-under floor 35 -> 55`)
2. **Task 2: consolidate BC-01 notes + trace PERF-02/03 + close BUG-05** — `9ac449c` (`docs(bc): consolidate Phase-5 BC-01 notes + trace PERF-02/03 to Phase 5`)

**Plan metadata:** committed with this SUMMARY + STATE/ROADMAP updates (`docs`).

## Files Created/Modified

- `.planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md` (new) — consolidated BC-01 running note.
- `.github/workflows/ci.yml` — `--cov-fail-under` 35 → 55 + updated comment.
- `CONTRIBUTING.md` — Coverage baseline section rewritten (57% / floor 55 / 2026-07-11 + ratchet history).
- `.planning/REQUIREMENTS.md` — PERF-02/PERF-03 traced to Phase 5, v2 Performance entries annotated, BUG-05 closed, coverage tally note updated.

## Decisions Made

- **Floor = 55, not higher.** Applied the Phase-3 2-point margin (baseline 57 − 2). Even though the suite now carries **0 xfails** (so the original xfail-volatility rationale no longer bites), the margin is retained as ratchet headroom against incidental drift and to honor the "do not overshoot the measured baseline" instruction. Floor 55 < measured 57.17%, so CI stays green.
- **Gate stays on the CI CLI** (Phase-3 D-05) — not added to `addopts` or `pyproject.toml`, keeping local subset runs fast and un-gated.
- **BUG-05 closed here.** It is the multi-plan review-surfaced-bugs requirement; with 05-02..05-07, 05-09, 05-10, 05-11 each landing a fix + proving test and 05-08 contributing the unblocking hook, the closure condition is met at phase verification (this plan).
- **PERF-02/PERF-03 recorded forward-only** — annotated in place rather than deleted from the v2 block (D-03), per the project's forward-only-edits directive.

## Deviations from Plan

**None — plan executed exactly as written.** Both tasks' automated verifications passed on the first run. The suite was already green with 0 xfails coming into the plan (a stronger state than the plan's "no residual xfail for a fixed finding" floor), so the residual-xfail sweep is trivially clean.

## Issues Encountered

None.

## User Setup Required

None for Phase 5. **Phase 6 carries one tracked action** (recorded in `05-BC-NOTES.md` §10 and REQUIREMENTS BC-01): merge the GSEGUtils `gsd/register-lazy-disk-cache-class` branch to `main` so release-please ships `0.6.0` to PyPI, then in pc2img bump `GSEGUtils ~= 0.6`, drop the `[tool.uv.sources]` git-rev entry, and re-lock.

## Next Phase Readiness

- **Phase 5 is complete.** ROADMAP SC1..5 satisfied: all findings fixed with proving tests (SC1..4), four module areas covered TEST-03..06 (SC5-coverage), floor ratcheted (D-10).
- **Phase-6 inputs handed off:** `05-BC-NOTES.md` is the single BC-01 intake artifact; the GSEGUtils bridge → PyPI `0.6.0` conversion is the first Phase-6 dependency task; CICD-02 (branch protection + publication hardening) remains Phase-6 Pending.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-12-SUMMARY.md
- FOUND: .github/workflows/ci.yml, CONTRIBUTING.md, .planning/REQUIREMENTS.md
- FOUND commit d1159a6 (Task 1 — coverage ratchet)
- FOUND commit 9ac449c (Task 2 — BC-notes + requirements)
