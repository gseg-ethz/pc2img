---
phase: 2
reviewers: [codex]
reviewed_at: 2026-07-09T13:18:11Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md]
---

# Cross-AI Plan Review — Phase 2

## Codex Review

## 02-01-PLAN.md

**Summary**  
The plan is well-scoped and matches the actual dependency state. `pyproject.toml:18-32` has the sibling deps commented out, `pyproject.toml:52-68` currently keeps dev/doc as extras and has bare RAPIDS cuda extras, and `/scratch/41_pchandler/pyproject.toml:24-38` plus `:119-122` supports the planned pins and cuda wiring. Overall this is a strong declaration-layer plan.

**Strengths**
- Correctly targets the real gap: `pchandler` and `GSEGUtils` are only commented in `pyproject.toml:19-21`.
- Keeps `numpy ~= 2.0` aligned with the user decision; pchandler provides the effective `<2.4` cap at `/scratch/41_pchandler/pyproject.toml:28`.
- Rewiring cuda extras through `pchandler[cuda11/12]` is justified by pchandler’s maintained cuda extras at `/scratch/41_pchandler/pyproject.toml:119-122`.
- Avoids Phase 4 cleanup creep such as placeholder metadata at `pyproject.toml:9` and `:46`.

**Concerns**
- **MEDIUM:** The `[tool.uv.sources]` RAPIDS pinning is acknowledged as an assumption, but Plan 01 verification only checks TOML shape, not resolver behavior. That is acceptable if Plan 02 is treated as the real gate, but Plan 01’s “fully lockable” language is slightly stronger than proven.
- **LOW:** The verification checks `src['cudf-cu12']` and `src['cudf-cu11']` only. It should also assert every RAPIDS name listed in the action is present, because pchandler pulls five package names per cuda extra.

**Suggestions**
- Add a structural verification loop over all ten expected RAPIDS package names.
- Add a negative check that no `[tool.uv.sources]` value contains `/scratch`, `third_party`, `path`, or `editable`.

**Risk Assessment: LOW-MEDIUM**  
Low implementation risk for the `pyproject.toml` edits; medium residual risk only because the transitive uv source behavior is not proven until locking.

## 02-02-PLAN.md

**Summary**  
The plan addresses the right reproducibility goals, but its clean-room proof is weaker than its wording. It runs in the same checkout with `third_party/` still present, and the command would not catch an accidental local-path source if one were committed. The lock/sync sequencing is otherwise sound, and `uv sync --help` confirms `--no-editable`, `--frozen`, dependency groups, and extras are valid command concepts.

**Strengths**
- Correctly depends on Plan 01 before locking.
- Uses `uv lock --check` and `uv run python -c "import pc2img"` as direct gates in `02-02-PLAN.md:71-78`.
- The fallback behavior for `pypi.nvidia.com` failure in `02-02-PLAN.md:66-69` is explicit and avoids silently weakening D-06.
- `setup.py:1-4` is minimal, so keeping the build backend unchanged is reasonable.

**Concerns**
- **MEDIUM:** The “no `third_party` symlinks” proof is not actually symlink-free. `third_party/` exists in the checkout and is ignored (`git status --ignored` shows `!! third_party/`), while the verification in `02-02-PLAN.md:96` runs from the same project root. If `[tool.uv.sources]` accidentally pointed to `third_party/pchandler`, this check could still pass.
- **MEDIUM:** The version verification is too shallow. `02-02-PLAN.md:72` greps for package names but does not assert actual versions or absence of local/editable sources in `uv.lock`.
- **LOW:** The clean-room command falls back from `uv sync --frozen --no-editable` to plain `uv sync --frozen`; if the first failure is meaningful, the fallback could mask why non-editable install failed.

**Suggestions**
- Add `grep -E '/scratch|third_party|editable = true|source = .*path' uv.lock` as a failing check, adjusted for actual uv lock syntax.
- Print exact versions using `importlib.metadata.version("pchandler")`, `version("gsegutils")`, and `version("numpy")`.
- Prefer a real isolated proof: copy/export the repo to a temp dir excluding `third_party/`, then run `UV_PROJECT_ENVIRONMENT=... uv sync --frozen`.
- If keeping the fallback, log the first `--no-editable` failure instead of suppressing it.

**Risk Assessment: MEDIUM**  
The main goal is achievable, but the current verification can give a false sense of clean-install independence.

## 02-03-PLAN.md

**Summary**  
This is the strongest plan conceptually. It corrects the earlier FoVTree misconception and proves the actual used surface: `SphericalProjection` imports and uses `FoV`, `FoVFilter`, `rhv2xyz`, and `PointCloudData` at `src/pc2img/strategies/projection.py:8-13` and `:108-116`, while `rg` found no `FoVTree`, `to_py4dgeo`, `Csv`, or `Las` call sites in `src/pc2img`. The explicit cache config is also justified by `PointCloudImageGenerator.__init__` passing the default through to `FeatureManager` at `src/pc2img/core.py:66-82`.

**Strengths**
- The smoke path is realistic and narrow: `RangeFeature` is exactly `^range$` and returns `pcd.r` at `src/pc2img/features/base_features.py:13-18`.
- Correctly avoids the config-less example call in `scripts/v2.0/01_manual_test_PointCloudImageGenerator.py:63-68`; the default can flow as `None` into `FeatureManager`, then `DiskBackedImageStore`, at `src/pc2img/features/manager.py:24-28` and `src/pc2img/image_cache/disk_backed_image_store.py:21-30`.
- The break-audit scope is honest: example scripts use `FoVTree` at `scripts/v2.0/03_tiled_image_gen.py:19` and `:57-62`, but library source does not.
- Fixing the `scripts/` ignore trap is necessary: `.gitignore:118` currently ignores `[Ss]cripts`, and `git check-ignore` confirms `scripts/smoke_pipeline.py` is ignored.

**Concerns**
- **LOW:** The `.gitignore` fix should probably include both `!/scripts/` and `!/scripts/**`. The plan’s verification will catch failure, but adding both avoids gitignore reinclusion edge cases.
- **LOW:** The optional pending todo in `02-03-PLAN.md:101` is not listed in `files_modified`. Either make it mandatory and list it, or remove it from the action to avoid artifact drift.
- **LOW:** The smoke passes `LazyDiskCacheConfig` to `PointCloudImageGenerator`, but `DelaunayInterpolation()` still uses its own default cache config at `src/pc2img/strategies/interpolation.py:103-113`. That still exercises GSEGUtils, but the plan should avoid implying the one explicit config controls both caches.

**Suggestions**
- Add a direct assertion in the smoke that the finite fraction is printed, not just asserted, so CI logs carry useful diagnostics.
- Make the audit grep command in the doc exactly match the verification command in `02-03-PLAN.md:104`.
- Use `!/scripts/` plus `!/scripts/**` in `.gitignore`.

**Risk Assessment: LOW**  
The plan is well-supported by code evidence and has executable verification. Remaining issues are polish and precision, not blockers.

## Overall Assessment

The phase plan set is mostly complete and aligned with the phase goals. The biggest improvement needed is strengthening Plan 02’s clean-room and lockfile verification so it proves “PyPI + lock, no local symlink source” rather than merely “import works from this checkout.” No HIGH-severity blockers found. Overall risk: **MEDIUM**, driven by uv/GPU lock resolution and clean-room proof fidelity, not by the pc2img source adaptation itself.

---

## Consensus Summary

Only one external reviewer (Codex) was invoked for this phase, so there is no
cross-reviewer consensus to synthesize. The findings below are Codex's, grounded
in `file:line` evidence against the working tree.

### Agreed Strengths

- **Plan 01** correctly targets the real gap — `pchandler`/`GSEGUtils` are only
  commented out in `pyproject.toml:19-21`; the numpy pin stays aligned with the
  user decision (pchandler supplies the effective `<2.4` cap); cuda rewiring
  through `pchandler[cuda11/12]` is justified by pchandler's maintained extras.
- **Plan 03** is the strongest plan: it corrects the FoVTree misconception and
  proves the actually-used pchandler surface (`FoV`, `FoVFilter`, `rhv2xyz`,
  `PointCloudData` in `src/pc2img/strategies/projection.py`), and its
  `.gitignore` scripts-trap fix is necessary and verified.

### Agreed Concerns (highest priority)

- **[MEDIUM] Plan 02 clean-room proof is weaker than its wording.** The
  verification runs in the same checkout with `third_party/` still present
  (`02-02-PLAN.md:96`), so an accidental local-path `[tool.uv.sources]` entry
  could still pass. Recommend a genuinely isolated proof (export repo to a temp
  dir excluding `third_party/`, then `uv sync --frozen`) plus a failing grep for
  `/scratch|third_party|editable = true|path` sources in `uv.lock`.
- **[MEDIUM] Plan 02 version verification is too shallow** (`02-02-PLAN.md:72`
  greps package names, not actual versions). Assert exact versions via
  `importlib.metadata.version(...)` for pchandler / gsegutils / numpy.
- **[MEDIUM] Plan 01 RAPIDS source pinning is asserted but not proven** until
  locking; Plan 01's "fully lockable" language is slightly stronger than what its
  TOML-shape-only verification demonstrates. Treat Plan 02 as the real gate.

### Lower-priority polish

- Plan 01: verification only checks `cudf-cu12`/`cudf-cu11`; loop over all ten
  expected RAPIDS package names and add a negative check for `/scratch`,
  `third_party`, `path`, `editable` in source values.
- Plan 03: use both `!/scripts/` and `!/scripts/**` in `.gitignore`; align the
  audit grep in the doc with the verification command (`02-03-PLAN.md:104`); note
  that `DelaunayInterpolation` keeps its own default cache config
  (`strategies/interpolation.py:103-113`), so the one explicit `LazyDiskCacheConfig`
  does not control both caches.

### Divergent Views

None — single reviewer.

### Overall

No HIGH-severity blockers. Codex's overall risk: **MEDIUM**, driven by uv/GPU
lock resolution and clean-room proof fidelity (Plan 02), not by the pc2img
source adaptation itself (Plan 03 is LOW risk).
