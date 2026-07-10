---
phase: 04-code-quality-algorithmic-soundness-review
plan: 05
subsystem: review / software-design audit (QUAL-02)
tags: [review, findings, design-audit, refute, QUAL-02, wave-3]
requires:
  - "04-03 (make_generator deleted; _TransformArray guarded; barrel __all__ synced)"
  - "04-04 (ruff hygiene sweep; stable post-format line numbers; 18 residual breadcrumbs)"
provides:
  - "04-FINDINGS-design.md (refuted, deduped design findings in the D-06 schema)"
  - "04-FINDINGS-design-candidates.md (retained raw FIND-pass output; D-05 evidence)"
  - "design half of the FINDINGS input for 04-07 synthesis -> Phase 5 BUG-05"
affects:
  - "04-07 (synthesis consumes the design + math FINDINGS halves)"
  - "Phase 5 (BUG-05 fixes: DSN-01..DSN-11 are the specified, proving-test-ready inputs)"
tech-stack:
  added: []
  patterns:
    - "two-file FIND/REFUTE split as retained adversarial-pass evidence (D-05)"
    - "stable DSN-* finding ids (no per-finding BUG-05.x IDs, per D-07)"
key-files:
  created:
    - ".planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS-design-candidates.md"
    - ".planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS-design.md"
  modified: []
decisions:
  - "BUG-02 redefined: 04-04 ruff --fix (F901, b478a34) already changed `raise NotImplemented`->`raise NotImplementedError`, so the exception-type half is fixed; the live defect is that __array_ufunc__ still unconditionally raises (NDArrayOperatorsMixin arithmetic dead). Phase-5 proving test must assert NotImplementedError, NOT TypeError"
  - "Anchor #4 (dependency-cycle guard) downgraded to LOW/latent: no currently-registered feature graph can form a cycle (regex-derived deps strictly shrink the name), so no live RecursionError; the missing visited-set is a real but unreachable structural gap"
  - "Pickle-load (seed J / T-04-J) logged as DSN-09 surfaced-and-logged, not fixed (D-02); trust boundary recorded = process-local tempfile.mkdtemp cache dirs"
metrics:
  duration: 10min
  completed: 2026-07-10
status: complete
---

# Phase 04 Plan 05: Design-track Review (QUAL-02) Summary

Ran the QUAL-02 design half of the single orchestrated review (D-03) as a fan-out FIND pass across
four module sets (D1 registries+factory, D2 orchestration, D3 image cache, D4 cross-cutting
hygiene) followed by an independent-refuter REFUTE pass, emitting eleven live `DSN-*` findings in
the D-06 schema (plus the FIXED make_generator anchor and hygiene breadcrumbs) — every `file:line`
re-grepped against the post-04-04 tree, with the two-file FIND/REFUTE split retained on disk as the
adversarial-pass evidence.

## What was built

- **`04-FINDINGS-design-candidates.md`** — the retained raw FIND-pass output, grouped by module set
  D1-D4. This is the D-05 evidence that a real find→refute pass ran; it stays distinct from the
  refuted file.
- **`04-FINDINGS-design.md`** — the refuted, deduped design findings, most-severe first, each with
  the full D-06 schema (id / file:line / defect / why-wrong / minimal repro / severity /
  pillar=design / Fix-or-Log disposition / proving-test sketch) **and** the independent refuter's
  concrete verdict (survived / downgraded / FIXED).

### The four required anchors (all present-or-fixed)

| Anchor | Finding | Disposition |
|--------|---------|-------------|
| #1 broken `make_generator` | DSN-F1 | **FIXED** in 04-03 (deleted, zero callers) — recorded, not re-logged |
| #2 divergent registries | DSN-05 | LOG (KeyError vs RuntimeError contracts; + side-effectful `match()` instantiation) |
| #3 in-place raster mutation | DSN-03 | LOG (masked today by `__array__` copy; Normalized/Clip inconsistency) |
| #4 missing dependency-cycle guard | DSN-08 | LOG, **LOW/latent** (no current feature graph can cycle) |

### Beyond-seed / broad-audit findings (D-04)

- **DSN-01 (HIGH, BUG-03):** `extend_cache_paths` nulls `interp_kwargs` — `dict(x).update(y)`
  returns `None` (`tiled_generator.py:66-68`). Source-only cross-ref (no xfail encodes it).
- **DSN-02 (HIGH, BUG-02 redefined):** `__array_ufunc__` unconditionally raises → the whole
  `NDArrayOperatorsMixin` arithmetic surface is dead (`disk_backed_image_data.py:63-64`).
- **DSN-04 (MED):** `FeatureManager._base_features` never reset in `request()` — accumulates across
  calls (`manager.py:22/28/36`).
- **DSN-06 (MED):** omitted `lazy_disk_cache_config` not coerced (explicit `None` is) — the live
  xfail `test_point_cloud_image_generator.py:35` encodes exactly this.
- **DSN-07 (MED, B008×4):** mutable constructed `LazyDiskCacheConfig()` default (seed E).
- **DSN-09 (security, T-04-J):** pickle-load of arbitrary cache files — surfaced-and-logged.
- **DSN-10/11 (LOW):** circular-import sensitivity; `_default_cls` typed non-optional but `None`.

## Deviations from Plan

### Auto-fixed / corrections applied during review (Rule 1 — correctness of the finding record)

- **[Rule 1 — Pitfall 1/4 correction] BUG-02 exception type is stale in the research.** Re-grepping
  the post-04-04 tree found `raise NotImplementedError` at `disk_backed_image_data.py:64`, not the
  `raise NotImplemented` singleton the 04-RESEARCH/CONTEXT anchor tables documented. `git show`
  confirmed commit `b478a34` (04-04 `ruff check --fix`, rule **F901**) rewrote it. I corrected
  DSN-02 to state the *observed* `NotImplementedError` and flagged that the Phase-5 proving test
  must assert `NotImplementedError` (not `TypeError`) — otherwise Phase 5 would assert the wrong
  exception (Pitfall 4). Verified empirically this session (`PROBE-F`).
- **[Rule 1 — honest refutation] Anchor #4 downgraded to LOW/latent.** The refuter's counter-check
  showed no currently-registered feature can form a dependency cycle (regex-derived deps strictly
  shrink the name), so no live `RecursionError` reproduces. Rather than log it as a confirmed HIGH
  bug, it is retained at LOW ("empirical confirmation pending in Phase 5") with the missing
  visited-set noted — this is the D-05 vote-threshold behavior working as designed.

No architectural changes (Rule 4) were needed — this is a review/analysis plan that writes markdown
findings only, no source edits.

## Verification

- Task 1: `test -s 04-FINDINGS-design-candidates.md` — pass (8966 bytes).
- Task 2: `test -s 04-FINDINGS-design.md && grep -qi make_generator && grep -qi pickle` — pass
  (20373 bytes; both anchors present).
- Two-file FIND/REFUTE split confirmed on disk (D-05 evidence retention).
- Refuter probes (cheap, D-05), verified this session:
  - `PROBE-G`: `dict({"a":1}).update({"b":2})` → `None` (confirms DSN-01/BUG-03).
  - `PROBE-F`: `raise NotImplementedError` → `NotImplementedError`; `raise NotImplemented` →
    `TypeError` (confirms DSN-02 redefinition + Pitfall-4 correction).
- Every `file:line` re-grepped against the post-04-04 tree (Pitfall 1); drifts corrected
  (DSN-01 `:66-68`, DSN-02 `:63-64`, DSN-03 `:76-81`).

## Threat surface

T-04-J (pickle.load of arbitrary `*.pkl`, Tampering/RCE, high, disposition=mitigate/log) is recorded
as DSN-09 with its current mitigation (process-local `tempfile.mkdtemp` cache dirs) and the
trust-boundary recommendation — satisfying the ASVS L1 `block_on:high` gate by surfacing-and-logging
per D-02. No new security surface introduced by this review (markdown-only outputs).

## Commits

- `111009f` docs(review): FIND-pass design candidates (D1-D4) for QUAL-02
- `c37e222` docs(review): refuted design FINDINGS (QUAL-02) for Phase 4

## Notes for 04-07 synthesis

This is the **design half** only. The math half (QUAL-03, `04-FINDINGS-math.md`) is a sibling plan;
04-07 merges both into the canonical `04-FINDINGS.md`. DSN ids are stable and can be carried
forward verbatim. BUG-01/03/04 remain source-only cross-references (no pytest xfail encodes them);
only the coerce-null finding (DSN-06) and the two DiskBackedImageData lifecycle cases have live
xfails today.

## Self-Check: PASSED

- Created files verified on disk: `04-FINDINGS-design-candidates.md`, `04-FINDINGS-design.md`,
  `04-05-SUMMARY.md`.
- Commits verified in git log: `111009f`, `c37e222`.
