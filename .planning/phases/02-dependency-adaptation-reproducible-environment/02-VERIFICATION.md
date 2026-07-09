---
phase: 02-dependency-adaptation-reproducible-environment
verified: 2026-07-09T14:23:58Z
status: passed
score: 4/4 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 2: Dependency Adaptation & Reproducible Environment Verification Report

**Phase Goal:** pc2img imports and runs correctly against PCHandler 2.x + the current GSEGUtils release, with a correctly pinned, reproducible `uv` environment.
**Verified:** 2026-07-09T14:23:58Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Every success criterion was confirmed by running the load-bearing command myself (not by trusting SUMMARY claims): `uv lock --check`, a frozen import of all three packages, the SC1 smoke, and a genuinely isolated clean-room `uv sync --frozen`. SC1 and SC3 are runtime/behavior-dependent — both were behaviorally exercised, not merely presence-checked.

### Observable Truths (ROADMAP Success Criteria)

| #   | Truth   | Status     | Evidence       |
| --- | ------- | ---------- | -------------- |
| 1   | Importing pc2img + single-cloud pipeline succeeds against pchandler 2.x with semantic/runtime breaks resolved (FoVTree 2D `"<r>-<c>"`, world-frame `to_py4dgeo`, Csv/Las load) | ✓ VERIFIED | `uv run --frozen python scripts/smoke_pipeline.py` → `OK shape=(200, 200) finite_fraction=0.959 min=8.748 max=11.262`, exit 0 (ran myself). Break-audit grep `grep -rEn "FoVTree\|to_py4dgeo\|\bCsv\b\|\bLas\b\|load_csv\|load_las" src/pc2img/` → zero hits (re-ran; attestation valid). `docs/pchandler-2x-break-audit.md` documents each named break as zero-call-site. |
| 2   | pc2img uses current GSEGUtils correctly (`lazy_disk_cache`, `config`, `base_types`), respecting `gsegutils`/`GSEGUtils` casing | ✓ VERIFIED | `src/pc2img/` imports all three surfaces: `from GSEGUtils.base_types`, `from GSEGUtils.config`, `from GSEGUtils.lazy_disk_cache`. Frozen `import GSEGUtils` succeeds; `version("gsegutils")` == `0.5.2` (casing gotcha honored). Delaunay step exercises `DiskBackedStore` at runtime (smoke ran green). |
| 3   | pyproject.toml declares+pins pchandler + GSEGUtils, resolves numpy 2.x pin; clean install imports without `third_party/` symlinks | ✓ VERIFIED | `pyproject.toml`: `pchandler ~= 2.1`, `GSEGUtils ~= 0.5`, `numpy ~= 2.0` (uncommented). Ran isolated clean-room myself (rsync excluding `third_party/`+`.venv`, `test ! -e third_party` passed): `uv sync --frozen --no-editable` OK, `import pc2img, pchandler, GSEGUtils` OK, versions 2.1.0/0.5.2/2.0.2 from PyPI registry. Lock records pchandler/gsegutils as `source = { registry = "https://pypi.org/simple" }`; only self-ref is `source = { editable = "." }`. |
| 4   | Documented `uv` workflow reproduces dev env from a committed lockfile | ✓ VERIFIED | `uv.lock` committed (git-tracked, 2525 lines, 181 pkgs); `uv lock --check` → "Resolved 181 packages", exit 0 (ran myself). `CONTRIBUTING.md` documents `uv sync`, `uv sync --group doc`, `uv run` (smoke + pytest), `uv lock` / `uv lock --check` after dep edits, plus casing + `third_party/` role. |

**Score:** 4/4 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pyproject.toml` | Real sibling pins, cuda extras via pchandler, PEP 735 groups, nvidia index + 10 RAPIDS sources | ✓ VERIFIED | All present and parseable; `[tool.uv] conflicts` added (Plan 02 owner-approved deviation). |
| `uv.lock` | Committed universal hash-pinned lock | ✓ VERIFIED | Git-tracked; `uv lock --check` up to date; no local-path source leaks. |
| `CONTRIBUTING.md` | uv bootstrap workflow doc | ✓ VERIFIED | Git-tracked; all required commands + gotchas documented. |
| `scripts/smoke_pipeline.py` | Runnable SC1 smoke | ✓ VERIFIED | Substantive (89 lines, real pipeline); runs green; git-tracked; not gitignored. |
| `docs/pchandler-2x-break-audit.md` | Negative-audit attestation | ✓ VERIFIED | Names BC-PCH-008/007/006/012 + casing + reproducible grep; accuracy corrections carried. |
| `.gitignore` | `!/scripts/` + `!/scripts/**` negations | ✓ VERIFIED | Both negations present; `git check-ignore scripts/smoke_pipeline.py` → not ignored. |
| `.planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md` | Deferred-bug todo, `resolves_phase: 4` | ✓ VERIFIED | Exists with `resolves_phase: 4`. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| clean-room `uv sync --frozen` | `uv.lock` | registry-resolved pchandler/gsegutils, no editable siblings | ✓ WIRED | Ran in isolated temp copy with `third_party/` physically absent; imports succeed from PyPI. |
| `scripts/smoke_pipeline.py` | pchandler `FoV`/spherical + GSEGUtils `DiskBackedStore` | `PointCloudData(rhv2xyz)` → `SphericalProjection(field_of_view=pcd.fov)` → `DelaunayInterpolation` → `range` | ✓ WIRED | Full module graph resolves; pipeline produces finite raster (0.959 finite). |
| cuda11/cuda12 extras | pchandler[cudaXX] | `[project.optional-dependencies]` + `[tool.uv] conflicts` | ✓ WIRED | Lock forks each GPU stack; both hash-pinned. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Lock up to date | `uv lock --check` | Resolved 181 packages, exit 0 | ✓ PASS |
| Frozen tri-import | `uv run --frozen python -c "import pc2img, pchandler, GSEGUtils"` | pchandler 2.1.0 / gsegutils 0.5.2 / numpy 2.0.2 | ✓ PASS |
| SC1 smoke | `uv run --frozen python scripts/smoke_pipeline.py` | `OK shape=(200, 200) finite_fraction=0.959 …`, exit 0 | ✓ PASS |
| SC3 clean-room | isolated rsync (no `third_party`) + `uv sync --frozen --no-editable` + import | sync OK, import OK, PyPI versions | ✓ PASS |
| Break-audit grep | `grep -rEn "FoVTree\|to_py4dgeo\|\bCsv\b\|\bLas\b\|load_csv\|load_las" src/pc2img/` | zero hits (exit 1) | ✓ PASS |
| Lock negative-source | grep `/scratch`/`third_party` + non-self local source in `uv.lock` | none found | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DEP-01 | 02-03 | Run against PCHandler 2.x, breaks resolved | ✓ SATISFIED | Smoke runs green + zero-call-site audit (SC1). |
| DEP-02 | 02-03 | Run against current GSEGUtils, casing gotcha | ✓ SATISFIED | All 3 GSEGUtils surfaces imported; casing honored; DiskBackedStore exercised (SC2). |
| DEP-03 | 02-01, 02-02 | pyproject re-enables+pins siblings, numpy resolved, clean install | ✓ SATISFIED | Pins present; clean-room import proven (SC3). |
| DEP-04 | 02-01, 02-02 | Reproducible uv env, documented, lockfile committed | ✓ SATISFIED | uv.lock committed + up-to-date; CONTRIBUTING documents workflow (SC4). |

All four requirement IDs declared in PLAN frontmatter map to Phase 2 in REQUIREMENTS.md (all marked Complete). No orphaned requirements — REQUIREMENTS.md maps exactly DEP-01..04 to Phase 2, all claimed by plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No TBD/FIXME/XXX in any phase-modified file | — | — |

Note: `pyproject.toml` retains placeholder metadata (`keywords = ["one","two"]`, `documentation = "https://google.com"`, duplicate joblib `~= 1.5`/`~= 1.3` pins). These were **explicitly scoped out** of Phase 2 (QUAL-01 / Phase 4) by both plans and are not a Phase 2 gap.

### Human Verification Required

None. All behavior-dependent criteria (SC1 pipeline runtime, SC3 clean-room install) were exercised directly by the verifier and passed.

### Gaps Summary

No gaps. Every success criterion, plan must-have truth, artifact, and key link was verified against the actual codebase with reproduced behavioral evidence. The phase goal — pc2img imports and runs correctly against PCHandler 2.x + current GSEGUtils with a correctly pinned, reproducible uv environment — is achieved.

---

_Verified: 2026-07-09T14:23:58Z_
_Verifier: Claude (gsd-verifier)_
