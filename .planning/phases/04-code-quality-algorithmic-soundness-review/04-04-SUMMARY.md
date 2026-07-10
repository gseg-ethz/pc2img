---
phase: 04-code-quality-algorithmic-soundness-review
plan: 04
subsystem: tooling / code-hygiene
tags: [ruff, hygiene, dead-code, formatting, pep695, QUAL-01]
requires:
  - "04-02 ([tool.ruff] config + per-file-ignores + metadata cleanup)"
  - "04-03 (manual source edits: dup convert_to_image removed, barrel __all__ synced)"
provides:
  - "ruff-clean (hygiene subset) + ruff-format-clean (120-col) src/ + tests/ tree"
  - "stable post-format line numbers as FINDINGS anchors for 04-05/06/07"
  - "activated tests/test_hygiene.py ruff-clean gate (no longer xfail)"
affects:
  - "04-05 / 04-06 / 04-07 design+math review (records file:line into 04-FINDINGS)"
  - "Phase 5 (BUG-05 fixes): 18 residual ruff findings are the deferred breadcrumbs"
tech-stack:
  added: []
  patterns:
    - "ruff line-length 120 (matches sibling PCHandler/GSEGUtils; reverses D-11)"
    - "PEP 695 type-parameter syntax (type X = ...; class X[T])"
key-files:
  created: []
  modified:
    - "pyproject.toml (line-length 88 -> 120)"
    - "src/pc2img/** (unused-import removal, dead-code deletion, format, PEP695, E741/B904)"
    - "tests/test_hygiene.py (ruff-clean gate activated; keywords/viz markers flipped)"
    - "tests/test_disk_backed_image_data.py, tests/test_rrim_features.py (ruff format only)"
decisions:
  - "Owner reversed D-11: ruff line-length 88 -> 120 (dense numerical code; cleared all 25 E501 with zero code edits)"
  - "PEP 695 modernization (UP040/UP046) applied now via --unsafe-fixes"
  - "Option A: keep [tool.ruff] config STRICT; retarget the gate test to the hygiene-fixable subset rather than suppressing E402/C901/B008 globally"
  - "18 residual findings (E402x9, C901x5, B008x4) deferred to Phase 5 per D-02; kept visible in bare `ruff check` as breadcrumbs"
metrics:
  duration: 24min
  completed: 2026-07-10
status: complete
---

# Phase 04 Plan 04: Ruff Hygiene Sweep Summary

Ran the QUAL-01 ruff hygiene sweep (D-09) as legible per-mutation commits: unused-import
removal, deliberate ERA001 dead-code deletion, a one-time `ruff format`, an owner-approved
line-length bump to 120, PEP 695 modernization, and the two safe-mechanical fixes (E741/B904)
— leaving the tree ruff-clean over the hygiene-fixable rule subset and ruff-format-clean, with
the 18 D-02-deferred structural findings intentionally left visible as Phase-5 breadcrumbs.

## What was built

- **Unused-import + dead-local removal** (`ruff check --fix --ignore ERA001 src/`): 45 F401
  unused imports stripped and import blocks sorted (I); 2 F841 dead locals (`finite`, `ch_axis`
  in `util.replace_nan`) removed manually (ruff marked them unsafe-to-autofix). `--ignore ERA001`
  kept commented-code deletion out of this pass. Barrel re-exports preserved via the 04-02
  per-file-ignores; strategy/feature registration verified through the public lookup APIs
  (`PROJECTIONS.get_strategy`, `INTERPOLATIONS.get_strategy`, `FEATURES.match`).
- **Deliberate ERA001 dead-code deletion**: ERA001 has no ruff autofix, which enforced the
  "review then delete" requirement. Enumerated 96 flagged lines across 9 files, confirmed every
  one is genuine commented-out code (old `replace_nan` reimplementation, commented
  `TriangulationData` dataclass + `BarycentricInterpolation` class, dead `__array_ufunc__` body,
  unreachable post-`return` cache-store calls, stale threshold experiments, dead one-liners), and
  removed exactly those lines bottom-up. Explanatory comments (`# normalize per-dimension`,
  `# Compute triangle metrics once`) were correctly not flagged and are preserved.
- **`ruff format`** on `src/` + `tests/` (one-time; the tree was not previously black-clean).
- **Line-length 88 -> 120** (owner-approved, reverses D-11): re-ran `ruff format` at 120, which
  unwraps lines previously wrapped to fit 88 and clears all 25 residual E501 with no manual edits.
- **PEP 695 modernization** (`UP040`/`UP046`, `--unsafe-fixes`): 4 `X: TypeAlias = ...` -> `type X = ...`
  and 2 `class X(Generic[T])` -> `class X[T]`; removed 3 orphaned typing imports.
- **Safe-mechanical fixes**: E741 (`gaussian_kernel(l=...)` -> `side_length`, no callers) and
  B904 (`raise KeyError(key) from None` for the mapping-miss in the image store;
  `raise ValueError(...) from err` in the strategy registry to preserve the KeyError cause).
- **Gate activation** (`tests/test_hygiene.py`): `test_ruff_check_src_is_clean` dropped its xfail
  and now asserts `ruff check src/ --ignore E402,C901,B008` clean plus `ruff format --check`;
  the two 04-02 metadata markers (`keywords`, `viz`), which were xpassing, flipped to normal
  passing tests.

## Deviations from Plan

### Owner-directed scope decision (checkpoint resolved)

The plan's Task 2 literal acceptance ("`ruff check src/` clean") was unachievable within the
phase scope: the 04-02 config selects E/F/W/I/B/C90/UP/NPY, and after the sweep 52 findings
remained (E501×25, E402×9, C901×5, B008×4, B904×2, E741×1) — several explicitly Phase-5 LOG
items per D-02. Surfaced as a `checkpoint:decision`; owner chose **Option A** plus two config
choices. Resolution applied:

1. **[Owner-approved, reverses D-11] Line-length 88 -> 120.** Rationale: dense numerical
   expressions read better unwrapped; clears all 25 E501 with zero code edits. Matches the
   sibling PCHandler/GSEGUtils template.
2. **[Owner-approved] PEP 695 modernization** applied now (6 UP040/UP046 fixes).
3. **[Rule 3 - blocking] Orphaned imports** left by the PEP 695 conversion (`TypeAlias`,
   `Generic`) removed in the same commit so the modernization does not regress F401.
4. **Config kept STRICT.** Did NOT add global `ignore` for the deferred families — they remain
   visible in a bare `ruff check` as Phase-5 breadcrumbs. Instead the gate test scopes to the
   hygiene-fixable subset (`--ignore E402,C901,B008`).

### Auto-fixed issues

- **[Rule 1] Dead locals** `finite` / `ch_axis` in `util.replace_nan` removed manually (F841,
  ruff-unsafe). No behavior change — both were unused assignments.

## Residual findings (deferred to Phase 5 per D-02) — FINDINGS breadcrumbs

18 findings remain in a bare `ruff check src/`, intentionally not fixed here (behavioral /
correctness / refactor territory → each needs a proving test in Phase 5). Feeds 04-05/04-07 synthesis:

| Rule | Count | Locations | Phase-5 mapping |
|------|-------|-----------|-----------------|
| E402 | 9 | `features/rrim.py:13-23` | BUG-04 — `from __future__ import annotations` precedes the module docstring, so imports are not "at top"; fixing ties to the inert-docstring bug |
| C901 | 5 | `features/derivative_features.py:294,376,471,578` + `util.replace_nan:227` | complexity refactor (mccabe > 10) |
| B008 | 4 | `features/manager.py:17`, `image_cache/disk_backed_image_store.py:22`, `tiled_generator.py:96,109` | design seed E — `LazyDiskCacheConfig()` mutable constructed default; prefer None-sentinel + `coerce_lazy_cfg` |

## Verification

- `ruff check src/ --ignore E402,C901,B008` — clean.
- `ruff format --check src/ tests/` — clean (25 files formatted).
- `ruff check --select F401,F811,F841 src/` — clean (F811 confirms 04-03 removed the duplicate
  `convert_to_image`).
- Import + registration smoke: `PROJECTIONS`/`INTERPOLATIONS`/`FEATURES` all resolve.
- Full suite: **19 passed, 11 xfailed, 0 xpassed** (was 15 passed / 11 xfailed pre-phase; the
  ruff-clean gate flipped xfail->pass and the two 04-02 metadata tests flipped xpass->pass;
  no live xfail flipped to unexpected pass).

## Commits

- `b478a34` refactor(hygiene): remove unused imports and dead locals via ruff --fix
- `18cf7e7` refactor(hygiene): delete commented-out dead code (ERA001)
- `f25b999` style(format): one-time ruff-format pass (88-col, black-equivalent)
- `8451b83` style(format): set ruff line-length to 120 and reflow
- `e3fb09b` refactor(typing): adopt PEP 695 type-parameter syntax (UP040/UP046)
- `b59eb4d` style(hygiene): resolve E741 ambiguous name and B904 exception chaining
- `29c64d1` test(hygiene): activate ruff-clean gate and flip metadata markers

## Scope fence honored (D-10)

Ran ruff LOCALLY to apply fixes and format the tree. No blocking ruff lint gate was wired into
any CI workflow — CI enforcement stays deferred to Phase 6.
## Self-Check: PASSED
