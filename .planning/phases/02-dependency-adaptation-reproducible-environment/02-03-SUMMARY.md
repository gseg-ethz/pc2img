---
phase: 02-dependency-adaptation-reproducible-environment
plan: 03
subsystem: smoke-and-audit
tags: [smoke, pchandler-2x, gsegutils, audit, gitignore, dep-01, dep-02]
requires:
  - "committed universal uv.lock + uv sync installing pc2img editable (Plan 02)"
  - "pchandler ~= 2.1 / GSEGUtils ~= 0.5 pins resolvable from PyPI (Plan 01)"
provides:
  - "scripts/smoke_pipeline.py — durable SC1 synthetic single-cloud smoke (spherical -> Delaunay -> range)"
  - "docs/pchandler-2x-break-audit.md — DEP-01/DEP-02 negative-audit attestation (zero call sites for all three named breaks)"
  - "corrected .gitignore that no longer un-commits new scripts/ files"
  - "pending todo tracking the deferred uncoerced None-default cache-config bug (resolves_phase: 4)"
affects:
  - .gitignore
  - scripts/smoke_pipeline.py
  - docs/pchandler-2x-break-audit.md
  - .planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md
tech-stack:
  added: []
  patterns:
    - "synthetic in-code point cloud via rhv2xyz(seed 42) -> PointCloudData (no external file, D-10)"
    - "explicit LazyDiskCacheConfig(cache_path=tmpdir) workaround for the uncoerced None default"
    - "grep-attest negative audit for off-path/absent semantic breaks (D-11 proportionate verification)"
key-files:
  created:
    - scripts/smoke_pipeline.py
    - docs/pchandler-2x-break-audit.md
    - .planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md
  modified:
    - .gitignore
decisions:
  - "DEP-01/DEP-02 delivered as an audit attestation + runtime smoke, not code fixes — all three named pchandler 2.x breaks have zero call sites in src/pc2img/ (RESEARCH finding, D-11 'not broken because not called')"
  - "Smoke passes an explicit LazyDiskCacheConfig; the uncoerced None-default cache-config bug is deferred to Phase 4/5 (pending todo, not folded into Phase 2)"
metrics:
  duration: 5min
  completed: 2026-07-09
status: complete
---

# Phase 2 Plan 3: SC1 Smoke + pchandler 2.x Break-Audit Summary

Delivered the durable SC1 proof and the honest DEP-01/DEP-02 deliverable: a
committed synthetic smoke that runs the single-cloud spherical → Delaunay → `range`
pipeline end-to-end against the locked pchandler 2.x + GSEGUtils env, plus a
grep-attested negative audit showing all three named pchandler 2.x semantic breaks
have zero call sites in `src/pc2img/`. Also fixed a `.gitignore` trap that would have
silently un-committed the new `scripts/` file.

## What Was Built

- **Task 1 — SC1 smoke + gitignore fix.** First corrected the `.gitignore` trap: the
  virtualenv-template `[Ss]cripts` rule (line 118) matched the tracked top-level
  `scripts/` source dir, so a new `scripts/smoke_pipeline.py` was silently
  un-committable (`git check-ignore` confirmed it). Added both root-anchored
  negations `!/scripts/` and `!/scripts/**` (with an explanatory comment) so the dir
  and its contents re-include while the generic rule still catches nested venv
  `Scripts/` bin dirs. Then created `scripts/smoke_pipeline.py`: a deterministic
  synthetic cloud (`default_rng(42)` over spherical `(h, v)` angle ranges →
  `rhv2xyz` → Nx3 float64 → `PointCloudData`), run inside a `TemporaryDirectory`
  through `PointCloudImageGenerator((200,200), SphericalProjection(field_of_view=pcd.fov),
  DelaunayInterpolation(), lazy_disk_cache_config=LazyDiskCacheConfig(cache_path=...))`,
  computing `generate(["range"])` and asserting shape `(200,200)`, finite-fraction
  > 0.5, and min > 0. It **prints** the finite fraction + shape/min/max so CI logs
  carry the diagnostic. Load-bearing details are commented inline: the explicit
  `LazyDiskCacheConfig` is required (the `None` default is uncoerced and raises), it
  does **not** govern both caches (`DelaunayInterpolation` keeps its own default
  cache config), and the None-default bug is a deferred Phase-4/5 follow-up.
- **Task 2 — pchandler 2.x break-audit attestation.** Created
  `docs/pchandler-2x-break-audit.md` recording the DEP-01/DEP-02 finding: **BC-PCH-008**
  (FoVTree 2D identifiers), **BC-PCH-007** (world-frame `to_py4dgeo`), and
  **BC-PCH-006/012** (Csv/Las load behavior) each have zero call sites in
  `src/pc2img/`, so the deliverable is an attestation, not a code fix. The doc records
  the exact reproducible grep command (byte-for-byte identical to Task 2's `<verify>`)
  + its empty result as evidence, carries the two RESEARCH accuracy corrections
  (library exercises `FoV` not `FoVTree`; breaks absent → no source edits, no sibling
  edits per D-13), attests the GSEGUtils casing gotcha (dist `gsegutils` / import
  `GSEGUtils`) and that no GSEGUtils BC required a source change, and adds a "Known
  follow-ups" section for the deferred None-config bug. Also filed the mandatory
  pending todo `.planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md`
  (`resolves_phase: 4`) mirroring the existing todo front-matter format.

## Verification

- Task 1: `git check-ignore scripts/smoke_pipeline.py` returns non-zero (not
  ignored); `uv run python scripts/smoke_pipeline.py` exits 0 and prints
  `OK shape=(200, 200) finite_fraction=0.959 min=8.748 max=11.262` — matching the
  RESEARCH runtime-verified output exactly — **passed**.
- Task 2: `docs/pchandler-2x-break-audit.md` exists and names BC-PCH-008/007/006/012,
  contains the `grep -rEn` command and the `casing` note; the pending todo exists with
  `resolves_phase: 4`; the audit grep of `src/pc2img/` returns zero hits (attestation
  valid) — full compound `<verify>` — **passed**.

## Deviations from Plan

None — plan executed exactly as written. Both tasks are `type="auto"`; no deviation
rules (1–4) triggered, no auth gates, no checkpoints. No pchandler/GSEGUtils source
was edited (D-13 respected); no `src/pc2img/` source was edited (the breaks are
absent, so there was nothing to fix).

## Notes

- **SC1 is durably proven** by the committed, CI-friendly smoke running the real
  single-cloud pipeline against pchandler 2.x + GSEGUtils. **SC2** (GSEGUtils
  `DiskBackedStore` path) is exercised as a side effect of the Delaunay step.
- **DEP-01/DEP-02** are satisfied honestly: the exercised `FoV`/spherical surface is
  runtime-proven; the three named breaks are attested non-applicable (zero call
  sites). This closes the Phase 2 requirement set (DEP-01..04 across the three plans).
- The smoke is intended to be promoted to a pytest smoke test in Phase 3.

## Commits

- ad7fcf4: feat(scripts): add SC1 synthetic smoke pipeline; fix scripts gitignore trap
- 1721c78: docs(audit): attest zero call sites for the three pchandler 2.x breaks

## Self-Check: PASSED

- FOUND: scripts/smoke_pipeline.py
- FOUND: docs/pchandler-2x-break-audit.md
- FOUND: .gitignore
- FOUND: .planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md
- FOUND: commit ad7fcf4
- FOUND: commit 1721c78
