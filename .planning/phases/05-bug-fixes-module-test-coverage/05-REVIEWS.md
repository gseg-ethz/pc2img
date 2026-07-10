---
phase: 5
reviewers: [codex]
reviewed_at: 2026-07-10T21:02:35Z
plans_reviewed: [05-01-PLAN.md, 05-02-PLAN.md, 05-03-PLAN.md, 05-04-PLAN.md, 05-05-PLAN.md, 05-06-PLAN.md, 05-07-PLAN.md, 05-08-PLAN.md, 05-09-PLAN.md, 05-10-PLAN.md, 05-11-PLAN.md, 05-12-PLAN.md]
model: codex-cli 0.142.2
---

# Cross-AI Plan Review — Phase 5

## Codex Review

## Summary

The plan set is strong overall: it is source-file grouped, mostly dependency-aware, and it correctly identifies the major bugs in the current codebase. The highest-risk areas are the GSEGUtils cross-repo hook, the perspective-projection API shape, registry dependency extraction, and the image-cache test migration. A few plans currently describe the right destination but not enough executable detail to get there safely.

## Strengths

- The orthographic bug is correctly targeted. `ProjectionStrategy.project()` unpacks four values at [src/pc2img/strategies/projection.py:79](/scratch/31_pc2img/src/pc2img/strategies/projection.py:79), while `OrthographicProjection.project_raw()` returns only two and uses problematic indexing at [src/pc2img/strategies/projection.py:176](/scratch/31_pc2img/src/pc2img/strategies/projection.py:176) and [src/pc2img/strategies/projection.py:189](/scratch/31_pc2img/src/pc2img/strategies/projection.py:189).

- The GSEGUtils store blocker is real and correctly surfaced. `DiskBackedStore` has a closed reload registry containing only `DiskBackedNDArray` at [/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py:61](/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py:61), and reload resolves through it at [/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py:455](/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py:455).

- The image-cache migration is directionally sound. Current `DiskBackedImageData.__array_ufunc__` raises the singleton instead of an exception at [src/pc2img/image_cache/disk_backed_image_data.py:55](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py:55), while GSEGUtils has a working unwrap/delegate implementation at [/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_ndarray.py:98](/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_ndarray.py:98).

- The security fix is well motivated. Current image store loads arbitrary pickle data at [src/pc2img/image_cache/disk_backed_image_store.py:48](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:48) and [src/pc2img/image_cache/disk_backed_image_store.py:167](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:167). Moving to GSEGUtils’ `.npy` + JSON codec addresses a real deserialization sink.

- The kept-behavior decisions are appropriately guarded by characterization tests, especially Delaunay culling at [src/pc2img/strategies/interpolation.py:217](/scratch/31_pc2img/src/pc2img/strategies/interpolation.py:217) and hillshade aspect at [src/pc2img/features/derivative_features.py:135](/scratch/31_pc2img/src/pc2img/features/derivative_features.py:135).

## Concerns

- **HIGH:** Plan 05-02 does not define the new perspective API needed for M-03. `PerspectiveProjection.__init__` currently accepts only `projection_matrix` and `rotation_matrix` at [src/pc2img/strategies/projection.py:200](/scratch/31_pc2img/src/pc2img/strategies/projection.py:200), and `project()` uses `(projection_matrix @ rotation_matrix) @ pcd` at [src/pc2img/strategies/projection.py:216](/scratch/31_pc2img/src/pc2img/strategies/projection.py:216). The plan says “add camera-translation term” but does not say whether that is a new `translation` constructor arg, a required 4x4 extrinsic, or a changed meaning of `rotation_matrix`.

- **HIGH:** Plan 05-08 changes GSEGUtils but does not mention how pc2img CI will get that changed dependency. pc2img imports `GSEGUtils.lazy_disk_cache` from the installed dependency, and GSEGUtils currently does not export the hook at [/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/__init__.py:23](/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/__init__.py:23). If CI installs the locked released package, 05-09 will fail unless `pyproject.toml`/`uv.lock` or the dependency release/version route is updated.

- **MEDIUM:** Plan 05-09 misclassifies existing xfails in `tests/test_disk_backed_image_data.py` as arithmetic xfails. They cover disabled-offload logging, getstate/pickle/finalizer/purge behavior at [tests/test_disk_backed_image_data.py:50](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:50), [tests/test_disk_backed_image_data.py:115](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:115), [tests/test_disk_backed_image_data.py:175](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:175), and [tests/test_disk_backed_image_data.py:241](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:241). Reparenting to GSEGUtils changes private state from `_image_data` to `_data`, so these tests need deliberate rewrite or retirement, not simple xfail removal.

- **MEDIUM:** Registry `dependencies_for` needs a more concrete design. `FeatureRegistry.match()` currently instantiates the class only to read dependencies at [src/pc2img/features/registry.py:52](/scratch/31_pc2img/src/pc2img/features/registry.py:52). A generic base implementation cannot infer split-list dependencies for `AverageFeature`, `SumFeature`, and `NormFeature`, whose group names differ at [src/pc2img/features/derivative_features.py:148](/scratch/31_pc2img/src/pc2img/features/derivative_features.py:148), [src/pc2img/features/derivative_features.py:170](/scratch/31_pc2img/src/pc2img/features/derivative_features.py:170), and [src/pc2img/features/derivative_features.py:218](/scratch/31_pc2img/src/pc2img/features/derivative_features.py:218). The plan should require per-class overrides or an explicit param-name mapping.

- **LOW:** The RRIM docstring plan is correct but tiny relative to its process overhead. `from __future__ import annotations` precedes the module string at [src/pc2img/features/rrim.py:1](/scratch/31_pc2img/src/pc2img/features/rrim.py:1), so `__doc__` is not populated. This can be handled mechanically.

## Suggestions

- Specify the `PerspectiveProjection` public contract before implementation: either `extrinsic_matrix`, `translation_vector`, or full `K @ [R|t]` matrix. Add the BC note if constructor parameters change.

- Add an explicit dependency step after 05-08: update pc2img’s dependency source/version or lockfile so CI imports the GSEGUtils hook. Otherwise 05-09 is only locally valid.

- In 05-09, replace “flip existing xfails” with “rewrite existing private-state tests to the inherited `DiskBackedNDArray` contract.” Keep arithmetic tests separate from pickle/finalizer behavior tests.

- For 05-07, define `dependencies_for` as an overridable classmethod on each feature class that has nontrivial dependency grammar. Do not rely on one generic base implementation.

- For 05-12, make “no residual xfail for fixed findings” concrete by grepping `xfail` reasons for fixed IDs. Current suite already has multiple xfails in [tests/test_disk_backed_image_data.py](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:50) and [tests/test_point_cloud_image_generator.py](/scratch/31_pc2img/tests/test_point_cloud_image_generator.py:35).

## Risk Assessment

**Overall risk: MEDIUM.** The phase goals are achievable and the wave decomposition is mostly sound. Risk is concentrated in cross-repo dependency availability, public API ambiguity for perspective projection, and tests that currently assert private internals that the planned reparenting intentionally removes. Fixing those plan details before execution should keep the implementation from stalling mid-wave.

---

## Consensus Summary

Only one reviewer (Codex) was invoked, so this section reflects Codex's grounded findings rather than multi-reviewer agreement. Codex verified claims against the actual source tree (pc2img + sibling GSEGUtils checkout) and cited `file:line` evidence throughout.

### Agreed Strengths

- Plans are source-file grouped and dependency-aware; the major bugs are correctly targeted with verified evidence (orthographic `project_raw` arity mismatch, GSEGUtils closed reload registry, `__array_ufunc__` raising the `NotImplemented` singleton, arbitrary-pickle deserialization sink).
- Kept-behavior decisions (Delaunay culling, hillshade aspect) are appropriately guarded by characterization tests.

### Agreed Concerns (highest priority)

1. **HIGH — 05-02 perspective API undefined (M-03).** The plan says "add camera-translation term" but does not pin the public contract: new `translation` arg vs. required 4×4 extrinsic vs. changed `rotation_matrix` meaning. Decide the `PerspectiveProjection` signature before execution and add a BC note if constructor params change.
2. **HIGH — 05-08 → 05-09 cross-repo dependency delivery.** GSEGUtils does not currently export the reload-registration hook. If CI installs the locked released package, 05-09 fails. Add an explicit step to update pc2img's dependency source/version/lockfile after the GSEGUtils edit.
3. **MEDIUM — 05-09 mis-scopes existing xfails.** The `test_disk_backed_image_data.py` xfails cover offload-logging / getstate / pickle / finalizer / purge behavior, not arithmetic. Reparenting to `DiskBackedNDArray` renames private state `_image_data`→`_data`, so these need deliberate rewrite/retirement, not blanket xfail removal.
4. **MEDIUM — 05-07 `dependencies_for` design too thin.** A generic base cannot infer split-list dependencies for `AverageFeature`/`SumFeature`/`NormFeature`. Require per-class overridable classmethods or an explicit param-name mapping.
5. **LOW — 05-x RRIM docstring.** `from __future__ import annotations` precedes the module string, so `__doc__` is unpopulated; handle mechanically.

### Divergent Views

N/A — single reviewer.
