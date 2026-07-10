---
phase: 04-code-quality-algorithmic-soundness-review
verified: 2026-07-10T00:00:00Z
status: passed
score: 4/4 success criteria verified
behavior_unverified: 0
overrides_applied: 0
resolution: >
  The single SC1 gap below was closed post-verification (owner chose "sweep now").
  Commit 4192da5 deleted the ~37 residual commented-out dead-code fragments across
  all listed files (99 lines removed, including the pyproject DeSpAn leftovers);
  commit 85be3ff corrected the 04-04 SUMMARY overclaim forward-only. Re-checked:
  fragments confirmed absent, all touched modules import, ruff format --check clean,
  hygiene gate (ruff check src/ --ignore E402,C901,B008) clean, pytest 19 passed /
  11 xfailed / 0 xpassed (no regression). QUAL-01 now fully met.
gaps:
  - truth: "SC1 — Dead/commented code is removed (QUAL-01)"
    status: resolved
    reason: >
      The joblib collapse, metadata de-placeholder, duplicate convert_to_image
      removal, and matplotlib->viz extra are all fully done. But the
      "dead/commented code is removed" sub-item is only partially met: the ruff
      ERA001 sweep (commit 18cf7e7) deleted only the 96 lines ERA001's heuristic
      flagged (lines that parse as complete statements). Orphaned comment
      fragments and intact commented blocks remain because ERA001 does not flag
      incomplete fragments (`# def foo(`, `# class Bar:`, `# @decorator`). The
      04-04 SUMMARY (and the 18cf7e7 commit message) claim the `TriangulationData`
      dataclass and `BarycentricInterpolation` class were removed — their header
      comments are still in the source. ~37 lines of commented-out code remain
      across 6 files. Not covered by the Phase-5 deferred ruff breadcrumbs
      (E402/C901/B008), so not auto-deferred. Low severity, non-blocking.
    artifacts:
      - path: "src/pc2img/strategies/interpolation.py"
        issue: "Lines 122-123 (# @dataclass / # class TriangulationData:), 270-286 (commented _triangulation_precalc cache block), 287-309 (commented BarycentricInterpolation class + BarycentricFactory) still present"
      - path: "src/pc2img/image_cache/disk_backed_image_store.py"
        issue: "Lines 98-119: commented fetch_image / _create_image_from_pcd / identifier / __repr__ method fragments remain"
      - path: "src/pc2img/image_cache/disk_backed_image_data.py"
        issue: "Lines 54-80: commented _derive_cache_path / wrap method fragments remain"
      - path: "src/pc2img/util.py"
        issue: "Lines 219-224: old replace_nan reimplementation signature + branch comments remain"
      - path: "src/pc2img/strategies/registry.py"
        issue: "Line 28: # class StrategyRegistry(Generic[T]): fragment remains"
      - path: "pyproject.toml"
        issue: "Lines 60-61: stale commented #repository=...DeSpAn / #[project.scripts] DeSpAn leftovers from a foreign template"
    missing:
      - "Delete the residual commented-out code fragments (orphaned class/def/decorator headers left by the ERA001-only sweep), OR record an explicit owner override accepting them as intentionally-retained. Cheap; could fold into the Phase-5 deferred-ruff cleanup."
      - "Correct the 04-04 SUMMARY narrative: the TriangulationData dataclass and BarycentricInterpolation class comments were NOT fully removed."
---

# Phase 4: Code Quality & Algorithmic Soundness Review — Verification Report

**Phase Goal:** Code hygiene, software-design flaws, and mathematical/algorithmic
soundness reviewed; fixes applied or findings logged, feeding concrete bug items
into Phase 5.
**Verified:** 2026-07-10
**Status:** gaps_found (one low-severity, non-blocking hygiene gap)
**Re-verification:** No — initial verification

## Verdict Summary

| Requirement | Verdict | One-line |
| ----------- | ------- | -------- |
| QUAL-01 (hygiene / tooling) | **PASS** | all sub-items clean + gate enforced; SC1 dead-code gap closed post-verification (4192da5), SUMMARY corrected (85be3ff) |
| QUAL-02 (design review) | **PASS** | 4 anchors present-or-fixed, pickle security logged, schema-consistent, FIND→REFUTE evidence retained |
| QUAL-03 (math review) | **PASS** | projection/culling/NaN-smoothing/feature math reviewed with numeric probes; BUG-01 captured via extent-normalization math |
| **Overall** | **PASS** | Primary deliverable (findings log) is excellent; the one SC1 hygiene gap was swept post-verification and re-checked green |

The phase goal is **substantially achieved**. The core deliverable — a rigorous,
adversarially-refuted, schema-consistent 04-FINDINGS.md feeding Phase 5 (BUG-05) —
is high quality. The only gap is residual commented-out code that SC1 says should
be gone and that the 04-04 SUMMARY inaccurately claims was removed. It does not
block Phase 5.

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| SC1 | Dead/commented code removed, joblib pin collapsed, placeholder metadata replaced, dup `convert_to_image` removed, matplotlib -> optional extra | ✗ PARTIAL | joblib single pin (pyproject:36); keywords are the real LiDAR/DEM/RRIM domain set + enriched classifiers + BSD license + real ETH/GitHub URLs (owner-confirmed, no google.com); `convert_to_image` defined exactly once (util.py:345); matplotlib is `viz` extra (pyproject:83). **BUT** ~37 lines of commented-out code remain across 6 files — see Gaps. |
| SC2 | Software-design review complete; 4 named findings + pickle addressed or logged | ✓ VERIFIED | 04-FINDINGS-design.md + candidates fragment exist. Anchor #1 make_generator FIXED in 04-03 (registry.py factory deleted, no dangling refs); #2 divergent registries -> DSN-05; #3 in-place raster mutation -> DSN-03; #4 dependency-cycle guard -> DSN-08; pickle security (seed J) -> DSN-09. |
| SC3 | Math/algorithmic soundness review of projection geometry, Delaunay culling, NaN-aware smoothing, feature math complete | ✓ VERIFIED | 04-FINDINGS-math.md + candidates with numeric probes (numpy 2.0.2/scipy). Coverage: spherical (M-05), orthographic (M-01), perspective per D-08 (M-02/M-03/M-04), Delaunay culling (M-06), NaN-aware smoothing (M-07), feature math (hillshade M-11, multiscale gradient). Adversarial NON-FINDING entries prove genuine refutation (barycentric weights err 7.1e-15; hillshade magnitude formula algebraically correct -> not logged). |
| SC4 | Correctness issues captured as concrete testable BUG-05 inputs for Phase 5 | ✓ VERIFIED | Canonical 04-FINDINGS.md: 24 findings, 585 lines, most-severe-first, 100% schema coverage (all 8 D-06 labels on every entry). BUG-01 captured via extent-normalization math (M-01), not just arity. D-07 honored: no BUG-05.x sub-ids minted, no GSD todos. |

**Score:** 3/4 success criteria verified (SC1 partial).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/test_hygiene.py` | Real hygiene gate, not a stub | ✓ VERIFIED | 4 live tests; `test_ruff_check_src_is_clean` genuinely shells `ruff check src/ --ignore E402,C901,B008` + `ruff format --check` via subprocess and asserts returncode 0. Import-smoke test imports all 6 submodules to keep registration firing. |
| `pyproject.toml` [tool.ruff] + viz + metadata | ruff config, viz extra, real metadata | ✓ VERIFIED | [tool.ruff] line-length 120 (owner-approved reversal of D-11), select E/F/W/I/B/C90/UP/NPY + extend-select ERA001, barrel per-file-ignores present; viz extra (line 83); metadata de-placeholdered. |
| `src/pc2img/registry.py` | make_generator repaired or removed | ✓ VERIFIED | Broken 3-arg factory deleted; file documents why; zero dangling `make_generator` refs in src/. |
| `src/pc2img/strategies/projection.py` | `_TransformArray` under TYPE_CHECKING | ✓ VERIFIED | `from __future__ import annotations` (line 1) + `_TransformArray` imported under `if TYPE_CHECKING:` (line 28); module imports clean at runtime. |
| `src/pc2img/features/__init__.py` | `__all__` synced to registered non-rrim features | ✓ VERIFIED | `__all__` lists the 18 base+derivative features; RRIM deliberately excluded (opt-in), documented inline. |
| `04-FINDINGS.md` | Canonical, schema-valid, most-severe-first | ✓ VERIFIED | 24 findings, all 8 labels, HIGH->LOW buckets. |
| `04-FINDINGS-design.md` / `-math.md` + candidates | FIND->REFUTE evidence | ✓ VERIFIED | All 4 fragment files present alongside canonical. |

### Behavioral Spot-Checks (live state)

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Suite green | `.venv/bin/python -m pytest -q` | 19 passed, 11 xfailed, 0 xpassed | ✓ PASS |
| Hygiene gate (fixable subset) | `ruff check src/ --ignore E402,C901,B008` | All checks passed! (exit 0) | ✓ PASS |
| Format clean | `ruff format --check src/ tests/` | 25 files already formatted | ✓ PASS |
| Deferred breadcrumbs visible | `ruff check src/` | 18 errors (E402x9, C901x5, B008x4) | ✓ PASS (intentional Phase-5 breadcrumbs) |
| ERA001 clean (gate hole) | `ruff check src/ --select ERA001` | All checks passed! | ⚠️ MISLEADING — passes despite ~37 residual commented-code lines (heuristic limit) |

### Findings-Log Anchor Spot-Checks (vs live source)

| Finding | Claimed anchor | Live source | Match |
| ------- | -------------- | ----------- | ----- |
| M-01 (BUG-01) | projection.py:79 unpacks 4-tuple; :188 Todo; :189 returns 2-tuple | Exact: `coords_raw, mask, mins, maxs = self.project_raw(pcd)` / `# Todo: Update to pass min and max back!` / `return pcd.xyz[mask, self._xyz_column_selection], mask` | ✓ |
| DSN-01 (BUG-03) | tiled_generator.py:66-68 `dict(...).update(...)` -> None | Exact: `updates["interp_kwargs"] = dict(self.interp_kwargs).update({...})` | ✓ |
| DSN-02 (BUG-02) | disk_backed_image_data.py:63-64 raises; exception-type history TypeError->NotImplementedError | Exact: `def __array_ufunc__(...): raise NotImplementedError` (F901 fix confirmed live) | ✓ |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| interpolation.py | 122-123, 270-309 | Commented-out class/dataclass/method fragments | ⚠️ Warning | SC1 not fully met; SUMMARY claims removal |
| disk_backed_image_store.py | 98-119 | Commented-out method fragments | ⚠️ Warning | SC1 residual |
| disk_backed_image_data.py | 54-80 | Commented-out method fragments | ⚠️ Warning | SC1 residual |
| util.py | 219-224 | Old `replace_nan` reimplementation comment | ⚠️ Warning | SC1 residual |
| pyproject.toml | 60-61 | Stale `#repository=...DeSpAn` foreign-template leftover | ℹ️ Info | Cosmetic |

No `TBD`/`FIXME`/`XXX` debt markers found in phase-modified files. (A `# Todo:` at projection.py:188 is the documented BUG-01 acknowledgement, captured as M-01.)

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
| ----------- | ----------- | ------ | -------- |
| QUAL-01 | 04-01/02/03/04 | ⚠ PARTIAL | Gate enforced, 4/5 hygiene sub-items clean; residual commented code |
| QUAL-02 | 04-03/05/07 | ✓ SATISFIED | Design findings + anchors logged |
| QUAL-03 | 04-06/07 | ✓ SATISFIED | Math findings with numeric probes |

### Gaps Summary

One gap, low severity, non-blocking:

**SC1 dead-code removal is incomplete and over-reported.** The ERA001-only deletion
pass (commit 18cf7e7) removed exactly the lines ERA001 flags — lines that parse as
complete Python statements. It left behind orphaned comment fragments (class/def/
decorator headers that do not parse standalone) and some intact commented blocks.
Result: ~37 lines of genuine commented-out code remain across 6 source files,
including the `# class TriangulationData:` and `# class BarycentricInterpolation`
headers that the 04-04 SUMMARY explicitly claims were removed. Because ERA001 does
not flag these, the hygiene gate test passes green over them — the gate cannot see
this gap.

This does not compromise the phase's primary deliverable (the findings log) or block
Phase 5. Recommended resolution: either sweep the residual fragments now (trivial),
fold them into Phase 5's deferred-ruff cleanup, or record an owner override in this
file's frontmatter accepting them as intentionally retained. In all cases the 04-04
SUMMARY narrative should be corrected.

**If this is deemed acceptable as-is**, add to this file's frontmatter:

```yaml
overrides:
  - must_have: "SC1 dead/commented code is removed"
    reason: "Residual comment fragments retained deliberately; ERA001-fixable subset swept, remainder folds into Phase-5 cleanup"
    accepted_by: "{name}"
    accepted_at: "{ISO timestamp}"
```

---

_Verified: 2026-07-10_
_Verifier: Claude (gsd-verifier)_
