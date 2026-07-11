---
phase: 05-bug-fixes-module-test-coverage
plan: 08
subsystem: infra
tags: [GSEGUtils, lazy_disk_cache, disk_backed_store, setuptools_scm, uv, tool.uv.sources, cross-repo, D-05]

# Dependency graph
requires:
  - phase: 04-review-hygiene
    provides: "DSN-09 pickle-sink + BUG-02 __array_ufunc__ findings that motivate reparenting DiskBackedImageData onto GSEGUtils' DiskBackedStore, which needs the store's reload allow-list to accept a pc2img subclass"
provides:
  - "GSEGUtils public `register_lazy_disk_cache_class(cls)` hook (function + decorator form) turning the closed `_LAZY_DISK_CACHE_CLASS_REGISTRY` reload allow-list into a PUBLIC extension point (D-05 Option A)"
  - "GSEGUtils branch `gsd/register-lazy-disk-cache-class` pushed to origin at SHA 2cf80835aa724f64a83853c8e35c91cb7640a919 — the git-rev bridge target 05-09 pins"
  - "Owner-approved delivery route: pc2img consumes the hook via a [tool.uv.sources] git-rev bridge (no version tag), preserving the existing `GSEGUtils ~= 0.5` specifier"
affects: [05-09, 05-12, phase-6-BC-01, phase-6-D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Public extension point over a closed allow-list: explicit registration API (function + decorator), NO importlib fallback — the D-02 tampering-mitigation posture is preserved (crafted meta.json still cannot coerce an unregistered class)"
    - "Cross-repo dependency delivery via [tool.uv.sources] git-rev bridge pinned to a pushed SHA (not a hand-rolled tag), because pc2img/CI resolves GSEGUtils from PyPI and [tool.uv.sources] forbids local/third_party paths (D-12)"

key-files:
  created: []
  modified:
    - "/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py (GSEGUtils repo — public hook added)"
    - "/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/__init__.py (GSEGUtils repo — hook re-exported in __all__)"
    - "/scratch/30_GSEGUtils/tests/test_lazy_disk_cache.py (GSEGUtils repo — 4 hook tests incl. decorator form)"

key-decisions:
  - "Delivery route changed from version tag/pin to a git-rev bridge (owner decision at the checkpoint): the hand-rolled v0.6.0 tag was REMOVED to avoid colliding with release-please's own v0.6.0 (an open release-please PR already proposes 0.5.3); the git build reports 0.5.2.post4 via setuptools_scm, satisfying the existing `GSEGUtils ~= 0.5` specifier"
  - "Landed on GSEGUtils branch `gsd/register-lazy-disk-cache-class` off `main` (which carries v0.5.2 that pc2img resolves against), NOT develop/gsd (37 commits of diverged CI/docs/test-infra)"
  - "Added a 4th test (decorator-form usage) post-checkout per owner request, to lock the advertised `@register_lazy_disk_cache_class` contract"
  - "PR-to-main intentionally DEFERRED to Phase 6 — the hook is proven across Phase 5 on the git-rev bridge first; Phase 6 merges to main so release-please cuts the real 0.6.0 to PyPI, then pc2img bumps `GSEGUtils ~= 0.6` and drops the git bridge (D-17 / BC-01)"

patterns-established:
  - "GSEGUtils LazyDiskCache subclasses register into the store reload allow-list via a public API instead of editing the module-private dict"
  - "pc2img rides a temporary git-rev GSEGUtils dependency during a multi-plan feature, converting to a PyPI minor pin at milestone hardening"

requirements-completed: []  # BUG-05 is multi-plan (05-02..05-07, 05-09, 05-10, 05-11); this plan CONTRIBUTES only — final closure at phase verification

coverage:
  - id: D1
    description: "GSEGUtils exposes a public `register_lazy_disk_cache_class(cls)` hook (function + decorator) that registers a LazyDiskCache subclass into the store reload allow-list; idempotent; rejects non-LazyDiskCache (TypeError) and name collisions with a different class (ValueError); no importlib fallback (D-02 posture preserved)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "GSEGUtils tests/test_lazy_disk_cache.py — registered-subclass offload→reload round-trip, non-subclass rejection, name-collision rejection, decorator-form usage (4 hook tests; full file 24 passed)"
        status: pass
    human_judgment: true
    rationale: "Cross-repo dependency edit under the project's human-approval constraint; owner reviewed and APPROVED the GSEGUtils diff at the blocking dependency-approval checkpoint, and separately approved the git-rev delivery route. Contributes to (does not close) multi-plan BUG-05."
  - id: D2
    description: "Owner-approved git-rev delivery route validated in the pc2img venv: hook imports, register→offload→reload round-trip returns the correct array, pc2img imports"
    requirement: "BUG-05"
    verification:
      - kind: integration
        ref: "pc2img venv bridge validation (performed in 05-09): [tool.uv.sources] git-rev @ 2cf8083 + re-locked uv.lock — hook import + round-trip + pc2img import"
        status: pass
    human_judgment: true
    rationale: "Bridge route was an owner decision made at the checkpoint; the pc2img-side consumption + re-lock is executed and proven in 05-09. Recorded here for the D-17/BC-01 running note."

# Metrics
duration: 20min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 08: GSEGUtils Public Class-Registration Hook (D-05 Option A) Summary

**GSEGUtils gains a public `register_lazy_disk_cache_class` hook (function + decorator) that turns the closed reload allow-list into an extension point — owner-approved, landed on branch `gsd/register-lazy-disk-cache-class` (SHA `2cf8083`, pushed to origin), delivered to pc2img via a `[tool.uv.sources]` git-rev bridge rather than a version tag.**

## Performance

- **Duration:** ~20 min (across Task 1 + blocking owner-approval checkpoint + owner-directed delivery-route change)
- **Started:** 2026-07-11
- **Completed:** 2026-07-11
- **Tasks:** 1 auto (GSEGUtils hook) + 1 blocking human-verify checkpoint (owner-approved)
- **Files modified:** 3 (all in the sibling GSEGUtils repo, none in pc2img source)

## Accomplishments

- **Public hook landed in GSEGUtils:** `register_lazy_disk_cache_class(cls)` added to `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py` and re-exported from that package `__init__` (`__all__`). It registers a `LazyDiskCache` subclass into `_LAZY_DISK_CACHE_CLASS_REGISTRY` under `cls.__name__`, turning the previously closed reload allow-list into a PUBLIC extension point. This unblocks 05-09's `DiskBackedImageData` reparent onto `DiskBackedStore` (offload→reload previously raised `ValueError: Unknown lazy_disk_cache_class 'DiskBackedImageData'`).
- **D-02 security posture preserved:** explicit allow-list, NO importlib fallback; the hook is idempotent, rejects non-`LazyDiskCache` inputs with `TypeError`, and rejects name collisions against a *different* class with `ValueError`. A crafted `.meta.json` still cannot coerce an unregistered class.
- **Tests (GSEGUtils `tests/test_lazy_disk_cache.py`):** 4 hook tests — (1) registered-subclass offload→reload round-trip, (2) non-subclass rejection, (3) name-collision rejection, and (4) decorator-form usage (added post-checkout per owner request to lock the advertised `@register_lazy_disk_cache_class` contract). Full file: **24 passed**.
- **Owner-approved at the blocking dependency-approval checkpoint** (cross-repo edit under the project's human-approval constraint), with an owner-directed change to the DELIVERY ROUTE from a version tag/pin to a git-rev bridge.
- **Landed + pushed:** branch `gsd/register-lazy-disk-cache-class` off `main` (main carries v0.5.2 that pc2img resolves against), pushed to origin (`github.com:gseg-ethz/GSEGUtils`). Commits `aad300c` (hook) + `2cf8083` (decorator test). **Bridge SHA for 05-09 to pin: `2cf80835aa724f64a83853c8e35c91cb7640a919`.**

## Task Commits

This plan's code commits live in the **GSEGUtils repo** (`/scratch/30_GSEGUtils`), NOT pc2img, per the plan's cross-repo scope:

1. **Task 1 (hook):** `aad300c` — `feat(lazy_disk_cache): public register_lazy_disk_cache_class hook` (GSEGUtils)
2. **Task 1 (decorator test, post-checkout per owner request):** `2cf8083` — `test(lazy_disk_cache): cover register hook decorator-form usage` (GSEGUtils)

Branch `gsd/register-lazy-disk-cache-class` HEAD = `2cf80835aa724f64a83853c8e35c91cb7640a919`, pushed to origin.

**Plan metadata (this pc2img repo):** committed with this SUMMARY + STATE/ROADMAP/REQUIREMENTS updates (`docs(deps): ...`).

## Files Created/Modified

All in the sibling GSEGUtils repo (`/scratch/30_GSEGUtils`), none in pc2img source:

- `src/GSEGUtils/lazy_disk_cache/disk_backed_store.py` — added the public `register_lazy_disk_cache_class(cls)` hook (function + decorator form) writing into the same `_LAZY_DISK_CACHE_CLASS_REGISTRY` that `_resolve_lazy_disk_cache_class` reads on reload.
- `src/GSEGUtils/lazy_disk_cache/__init__.py` — re-exported the hook in `__all__`.
- `tests/test_lazy_disk_cache.py` — 4 hook tests (round-trip, non-subclass rejection, name-collision rejection, decorator form); full file 24 passed.

## Decisions Made

- **Delivery route: git-rev bridge, not a version tag (owner decision at the checkpoint).** The hand-rolled `v0.6.0` tag was REMOVED. GSEGUtils versions via release-please, and a manual `v0.6.0` would collide with release-please's own future `v0.6.0`; there is already an open release-please PR proposing `0.5.3`. With no tag, the git build reports `0.5.2.post4` via setuptools_scm, which satisfies pc2img's existing `GSEGUtils ~= 0.5` specifier. pc2img therefore consumes the hook via a `[tool.uv.sources]` git-rev entry pinned to the pushed SHA + a re-locked `uv.lock` (executed in 05-09), because pc2img/CI resolves GSEGUtils from PyPI (the copied `0.5.2`, which lacks the hook) and `[tool.uv.sources]` forbids local/`third_party` paths (D-12). The bridge was VALIDATED in the pc2img venv: hook imports, register→offload→reload round-trip returns the correct array, and `import pc2img` succeeds.
- **Branch base = `main`, not `develop/gsd`.** `main` carries `v0.5.2` (what pc2img resolves against); `develop/gsd` is 37 commits of diverged CI/docs/test-infra. Basing on `main` keeps the bridge diff minimal and the eventual PR clean.
- **4th (decorator) test added post-checkout** per owner request, to lock the publicly advertised `@register_lazy_disk_cache_class` decorator contract in addition to the plain function-call form.
- **BUG-05 contribution only — not closure.** 05-08 unblocks the store consolidation but does not by itself resolve BUG-05 (a multi-plan, review-surfaced-bugs requirement also fed by 05-02..05-07, 05-09, 05-10, 05-11). Final BUG-05 closure is left to phase verification.

## Deviations from Plan

The plan as written targeted a GSEGUtils **release/tag** (`0.6.0`) that 05-09 would pin against. At the blocking owner-approval checkpoint the owner **approved the diff** but **redirected the delivery mechanism** to a git-rev bridge (tag removed) for the reasons above. This is a checkpoint-directed change of route, not an autonomous deviation — the code artifact (the hook + tests) is exactly what the plan specified; only the *delivery vehicle* changed from tag-pin to `[tool.uv.sources]` git-rev @ SHA.

**Total deviations:** 0 autonomous. 1 owner-directed delivery-route change at the approved checkpoint (version tag → git-rev bridge; `v0.6.0` tag removed).
**Impact on plan:** The hook, its security posture, and its tests are unchanged from plan intent. Only how 05-09 consumes it changed (git-rev bridge instead of a `~=0.6` PyPI pin). The `~=0.6` PyPI conversion is deferred to Phase 6.

## Issues Encountered

- A hand-rolled `v0.6.0` tag would have collided with release-please's own versioning (open PR proposes `0.5.3`). Resolved by removing the tag and using setuptools_scm's `0.5.2.post4` git build over a `[tool.uv.sources]` git-rev bridge — no tag, no collision, existing `~= 0.5` specifier still satisfied.

## User Setup Required

None — the cross-repo GSEGUtils edit was owner-reviewed and APPROVED at the blocking dependency-approval checkpoint. No further external configuration is required for Phase 5. (Phase 6 will require merging the GSEGUtils branch to `main` via PR — see Next Phase Readiness.)

## Next Phase Readiness

- **05-09 is unblocked:** it pins `[tool.uv.sources]` to GSEGUtils git-rev `2cf80835aa724f64a83853c8e35c91cb7640a919`, re-locks `uv.lock`, and reparents `DiskBackedImageData` onto `DiskBackedStore` using the now-public reload allow-list. (This SUMMARY records that the bridge was already validated in the pc2img venv during 05-09.)
- **D-17 / BC-01 (Phase-6 material) — running note:** GSEGUtils gains a public class-registration API (`register_lazy_disk_cache_class`); pc2img is temporarily on a git-rev dependency bridge. **PHASE-6 CONVERSION (tracked, must happen at Phase 6 / consolidated in 05-12):** merge the GSEGUtils branch to `main` via PR so release-please cuts the REAL `0.6.0` to PyPI (absorbing the pending `0.5.3` docs/chore notes), then in pc2img bump `GSEGUtils ~= 0.6`, DROP the `[tool.uv.sources]` git entry, and re-lock. The PR-to-main is intentionally DEFERRED until the hook is proven across Phase 5.
- **No blockers** for downstream Phase-5 plans.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-08-SUMMARY.md
- FOUND GSEGUtils commit aad300c (Task 1 — hook)
- FOUND GSEGUtils commit 2cf8083 (Task 1 — decorator test; branch HEAD 2cf80835aa724f64a83853c8e35c91cb7640a919, pushed to origin)
- No pc2img source edits (docs-only plan capturing the owner-approved cross-repo GSEGUtils change)
