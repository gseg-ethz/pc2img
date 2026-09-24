---
phase: 05-bug-fixes-module-test-coverage
plan: 17
subsystem: features
tags: [rrim, feature-registry, test-strength, gap-closure, bookkeeping, gsegutils]

requires:
  - phase: 05-bug-fixes-module-test-coverage (plan 05-16)
    provides: the round-4 wave-1 image-cache fixes and disposition table this plan's UAT evidence lines and Round-4 closure record cite verbatim
provides:
  - "WR-03 precedence pinned at the public surface (FEATURES.match), not just the private parser, tying the asserted dependency string to the derived store key (review-r2-d1c47843161c)"
  - "z_factor proven observably load-bearing end-to-end: rrim/rrim_pack rasters at two z values are finite and NOT array-equal (review-r1-a8cd7b4707b0)"
  - "z round-trip coverage extended to the upper exponent boundary (1e16..1e22, 4503599627370495.5) at the NAME level only (review-r1-4939108716dd)"
  - "A clip validation error names which clip (slope_clip/structure_clip) failed (review-r1-8fb6b87813d1)"
  - "A Phase-6 todo filing the GSEGUtils 0.6 adoption + containment-override deletion, citing spike-000's VALIDATED absorption verdict"
  - "05-UAT.md reconciled: 17 status: flips (16 resolved, 1 newly deferred), audit-uat now reports only 2 deferred items and zero failed"
  - "05-VERIFICATION.md gains a Round-4 closure record covering both 05-16 and 05-17"
affects: [phase-06-gsegutils-adoption, phase-05-code-review, phase-05-reverification]

actuals:
  tokens: 9431
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Pin a BC-relevant precedence contract at the PUBLIC surface (FEATURES.match) in addition to the private parser it is implemented by — the public surface is what the BC record is actually written about"
    - "Wrap-and-reraise a shared validator's ValueError to add caller-identifying context, chained via `from`, without touching the shared validator's own signature or message"

key-files:
  created:
    - .planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md
  modified:
    - src/pc2img/features/rrim.py
    - tests/test_rrim_features.py
    - .planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md
    - .planning/phases/05-bug-fixes-module-test-coverage/05-VERIFICATION.md

key-decisions:
  - "review-r2-2b9426a42695 and review-r2-6f4507d8c33f: 05-16 folded both into rewrites it made anyway (same commit f1a81cb), so they read resolved with that evidence, not deferred; review-r2-a7c7f4e498a6 had no host rewrite to fold into, so it is the sole entry newly deferred by this plan"
  - "IN-02 (_validate_clip naming its clip) judged NOT a BC-NOTES entry: message-text-only change, same ValueError type, identical accept/reject outcomes, no test asserted the old text — precedent is G8's unified percentile-bounds message strings, recorded as a 05-VERIFICATION.md deviation rather than a BC entry"
  - "review-r1-ab91c4469087's artifact path: corrected in place from src/pc2img/features/rrim.py (which has never had a logger — empty git log -S getLogger) to src/pc2img/image_cache/disk_backed_image_store.py, where 05-16 actually removed the dead logger; issue: text left unchanged"

requirements-completed: [BUG-05, TEST-04]

coverage:
  - id: D1
    description: "The WR-03 base-feature-vs-option precedence is pinned through FEATURES.match (the public surface the BC record is about), not only the private parser, and ties the asserted dependency string to the derived store key (review-r2-d1c47843161c)"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_exponent_token_precedence_is_visible_at_the_registry_surface"
        status: pass
    human_judgment: false
  - id: D2
    description: "z_factor is proven observably load-bearing in the end-to-end generate() path — a computation that silently dropped z would now be caught (review-r1-a8cd7b4707b0)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_generate_rrim_z_factor_changes_the_output"
        status: pass
    human_judgment: false
  - id: D3
    description: "z round-trip coverage extends to the upper exponent boundary at the NAME level, without computing any raster at z >= 1e16 (review-r1-4939108716dd)"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_pack_feature_name_round_trips_z_factor"
        status: pass
      - kind: unit
        ref: "tests/test_rrim_features.py#test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name"
        status: pass
    human_judgment: false
  - id: D4
    description: "A clip validation error names which clip (slope_clip or structure_clip) failed, RED-first then GREEN (review-r1-8fb6b87813d1)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_clip_validation_error_names_the_failing_clip"
        status: pass
      - kind: unit
        ref: "tests/test_rrim_features.py#test_clip_validation_error_reaches_the_registry_surface"
        status: pass
    human_judgment: false
  - id: D5
    description: "The three absorption-superseded containment findings are either folded (resolved, with evidence) or deferred to a new Phase-6 todo that tells the deletion story completely (spike prerequisites, exception-type check, findings list)"
    verification:
      - kind: other
        ref: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md + 05-UAT.md flips"
        status: pass
    human_judgment: false
  - id: D6
    description: "05-UAT.md gap bookkeeping reconciled to reality: only genuinely-deferred items remain open to gsd-tools query audit-uat"
    verification:
      - kind: other
        ref: "gsd-tools query audit-uat -> 05-UAT.md: 2 open items, both deferred, zero failed"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-09-24
status: complete
---

# Phase 05 Plan 17: RRIM residual gap closure, Phase-6 override-deletion todo, round-4 UAT bookkeeping

**Pins the WR-03 precedence at the public FEATURES.match surface (not just the private parser), makes z_factor observably load-bearing end-to-end, extends the z round-trip to the upper exponent boundary, names the failing clip in a validation error, files the Phase-6 GSEGUtils-0.6 override-deletion todo, and closes all 17 remaining round-4 UAT gaps with cited evidence.**

## Performance

- **Duration:** 11 min (approx. — STATE.md `last_updated` 2026-09-24T14:08:22Z at plan hand-off to sandbox clock 2026-09-24T14:18:57Z; the sandbox clock does not track wall-clock tool-call time closely, so this is a lower bound on effort)
- **Started:** 2026-09-24T14:08:22Z (approx.)
- **Completed:** 2026-09-24T14:18:57Z
- **Tasks:** 2
- **Files modified:** 4 (+ 1 created)

## Accomplishments

- `test_exponent_token_precedence_is_visible_at_the_registry_surface` asserts the WR-03 base-feature-vs-option precedence through `FEATURES.match` — the exact surface `dependencies_for` (G1/DSN-05) rewrote — including `spec.cls` identity for all three RRIM classes and tying the second dependency of `rrim_(z1e5)` to `RRIMConfig(z_factor=1e5).pack_feature_name()`, the literal store key BC-NOTES entry 16 is about.
- `test_generate_rrim_z_factor_changes_the_output` drives `generate()` end-to-end at two `z_factor` values and asserts the `rrim`/`rrim_pack` rasters are finite AND not array-equal, closing the gap where a computation silently dropping `z` would have passed every existing G9 proving test (shape + finiteness only).
- `_ROUND_TRIP_Z_VALUES` extended with `1e16, 1e17, 1.2345678e20, 1e22, 4503599627370495.5` (now 14 parametrised round-trip cases); `test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name` pins that three exponent spellings of `1e16` (`z1e16`, `z1E+16`, `z1e+16`) all canonicalise to one identical dependency list, and that the high-precision `1.2345678e20` pack name re-parses to the exact double. NAME-level only — no raster is computed at `z >= 1e16`.
- `_validate_clip` now re-raises the shared `_validate_percentile_bounds` `ValueError` naming `<name>_clip`, chained via `from`, with zero change to the shared helper, its callers, or the `slope`/`structure` names passed at the two call sites. RED confirmed first (3 xfailed: 2 parametrised + 1 registry-surface), then GREEN with markers removed.
- Filed `.planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md` (`resolves_phase: 6`): the Phase-6 vehicle for adopting GSEGUtils 0.6 and deleting `DiskBackedImageStore`'s three-method containment override, citing spike-000's `VALIDATED` absorption verdict, requiring the two still-`PENDING` spikes (001 orphaned-override-hunt, 004 blast-radius-phase14) to run first, and spelling out the exception-type check (`StoreKeyError`/`StoreContainmentError` subclassing `ValueError` or not) before touching any `pytest.raises`.
- Reconciled `05-UAT.md`: 17 `status:` flips (16 to `resolved` with an `evidence:` line citing a commit SHA, test function, or BC-NOTES entry; 1 newly `deferred` with a `deferred_to:` line) — every flip edits the existing `status:` line in place, inside the single `## Gaps` heading. `review-r1-ab91c4469087`'s artifact `path:` corrected from `rrim.py` to the store module.
- Appended `## Round-4 closure record (2026-09-24)` to `05-VERIFICATION.md`, covering both `05-16` and `05-17`, without touching either file's frontmatter.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RRIM residuals): pin precedence, z-sensitivity, upper boundary** — `83e69e4` (test), `01dcff0` (fix)
2. **Task 2 (deferral + bookkeeping): Phase-6 todo, UAT flips, verification record** — `9ff3a11` (docs: todos), `b7b1d94` (docs: uat), `78d0094` (docs: verification)

**Plan metadata:** committed via the final `docs(05-17):` commit below (this SUMMARY + STATE.md + ROADMAP.md + REQUIREMENTS.md).

## Files Created/Modified

- `src/pc2img/features/rrim.py` — `_validate_clip` re-raises with `<name>_clip` in the message, chained via `from`; no other executable line changed
- `tests/test_rrim_features.py` — 4 new tests, 1 extended parametrisation (5 new values), 1 new parametrised pair (2 cases): `test_exponent_token_precedence_is_visible_at_the_registry_surface`, `test_generate_rrim_z_factor_changes_the_output`, `test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name`, `test_clip_validation_error_names_the_failing_clip` (parametrised), `test_clip_validation_error_reaches_the_registry_surface`
- `.planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md` — new, Phase-6 deletion vehicle
- `.planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md` — 17 `status:` flips + 1 artifact `path:` correction, inside `## Gaps`
- `.planning/phases/05-bug-fixes-module-test-coverage/05-VERIFICATION.md` — appended `## Round-4 closure record (2026-09-24)`

## First-Run / RED-GREEN Results

Measured 2026-09-24 on HEAD `d397606` (05-16 completion), before any Task-1 source edit:

- `test_exponent_token_precedence_is_visible_at_the_registry_surface`: **PASSED on first run** (characterization — no source change was needed).
- `test_generate_rrim_z_factor_changes_the_output`: **PASSED on first run**.
- `test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name`: **PASSED on first run**.
- `test_pack_feature_name_round_trips_z_factor` (extended to 14 cases): **PASSED on first run** for all 14.
- Clip-naming tests, RED state (`.venv/bin/pytest tests/test_rrim_features.py -q` before the fix): **48 passed, 3 xfailed** — exactly the 2 parametrised cases + 1 registry-surface case, confirming the target tests failed on the intended assertion, not a collection/fixture error.
- Pre-fix message text (pasted verbatim, measured before any source edit):
  - `slope_clip=(98.0, 2.0)` → `'percentile low must not exceed high, got low=98.0, high=2.0.'`
  - `structure_clip=(98.0, 2.0)` → `'percentile low must not exceed high, got low=98.0, high=2.0.'`
  - Neither message contained `slope_clip` or `structure_clip` — confirming the RED state matched the finding.
- After the `_validate_clip` fix and marker removal: `.venv/bin/pytest tests/test_rrim_features.py -q` → **51 passed, 0 xfailed, 0 xpassed**.

## Fold/Defer Outcome (D-R4-01 #4)

- `review-r2-2b9426a42695` — **FOLDED** by 05-16 into the `_assert_within_cache_dir` predicate rewrite (commit `f1a81cb`; resolved cache directory bound once per call as part of the parent-only-resolution rewrite). Now `status: resolved`.
- `review-r2-6f4507d8c33f` — **FOLDED** by 05-16 into the rewritten route-enumeration paragraph (same commit `f1a81cb`; now names the `.dat` memmap route). Now `status: resolved`.
- `review-r2-a7c7f4e498a6` — no host rewrite to fold into (the `_get_meta_path` guard branch has no direct test, only transitive coverage). **Deferred** to the new todo, `deferred_to:` set, `status: deferred`.

## IN-02 Not-a-BC-Entry Judgement

`_validate_clip` naming its failing clip is a message-text-only change: the exception type (`ValueError`) is unchanged, accept/reject outcomes are unchanged, and no existing test asserted the old message text. Per the owner-delegated planner judgement in `owner_decisions_locked` #3, this is judged NOT a BC-NOTES entry, on the precedent of G8's unified percentile-bounds message strings — recorded in `05-VERIFICATION.md` (Round-3 closure record) as a deviation, not a BC entry. The same treatment is applied here and recorded in the new Round-4 closure record.

## Printed Verification Output

```
resolved=31 deferred=2
open UAT items: 2 | deferred,deferred
196 passed, 17 warnings in 2.15s (full suite, before this SUMMARY commit)
```

Coverage: `.venv/bin/pytest --cov=pc2img --cov-branch --cov-fail-under=55 -q` → "Required test coverage of 55% reached. Total coverage: 62.20%", 196 passed. `tests/test_hygiene.py` — 4 passed.

## Decisions Made

- See `key-decisions` in frontmatter (fold/defer split, IN-02 not-a-BC-entry judgement, IN-01 artifact-path correction).
- `_validate_clip`'s fix is scoped to exactly the two hunks `git diff` shows against the 05-16 completion commit — no forbidden symbol (`_Z_FACTOR_RE`, `_format_number`, `_looks_like_option_token`, `_parse_rrim_config`, `_parse_rrim_component`, `compute_slope`, `compute_openness`, `pack_feature_name`) appears in the diff, confirmed by the plan's own grep gate.

## Deviations from Plan

None — plan executed exactly as written. All `<acceptance_criteria>` and `<verify>` gates in both tasks passed on the commands specified in the plan, without needing a Rule 1-4 deviation.

## Issues Encountered

- `uv run --frozen pyright src/pc2img/features/rrim.py` (plan-level `<verification>` bullet) could not be run: `pyright` is not installed in this environment, consistent with 05-16-SUMMARY.md's "Issues Encountered" note for the same gap. `ruff check` and `ruff format --check` on both changed files are clean. This is flagged, as 05-16 flagged it, for a follow-up in an environment where `pyright` is actually available — the type-relevant surface touched here (`try`/`except ValueError as exc: raise ... from exc`) follows an existing typed pattern in the file and introduces no new dynamic-typing surface.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Both round-4 gap-closure plans (`05-16`, `05-17`) are complete and committed. Per this project's global Review Discipline rule (gap-closure fixes get their own review), the combined round-4 diff needs its OWN review before Phase 5 re-verifies:
  `/gsd-code-review 05 --files src/pc2img/features/rrim.py tests/test_rrim_features.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py`, escalating to `/code-review <base> high` because 05-16 touched a base-class contract (`__delitem__` ordering) and a security predicate (containment).
- After that review (and any findings it produces routed back through `/gsd-consolidate-findings`, per the same global rule), Phase 5 should re-verify. Re-verification owns the `status:`/`gaps_open:` frontmatter of both `05-UAT.md` and `05-VERIFICATION.md` — this plan deliberately left them untouched.
- The Phase-6 todo this plan filed (`2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`) is ready for Phase 6 planning; it depends on the still-`PENDING` spikes 001 and 004 running first.

## Self-Check: PASSED

- `src/pc2img/features/rrim.py` — FOUND
- `tests/test_rrim_features.py` — FOUND
- `.planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md` — FOUND
- `.planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md` — FOUND
- `.planning/phases/05-bug-fixes-module-test-coverage/05-VERIFICATION.md` — FOUND
- Commits `83e69e4`, `01dcff0`, `9ff3a11`, `b7b1d94`, `78d0094` — all FOUND in `git log --oneline --all`

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-09-24*
