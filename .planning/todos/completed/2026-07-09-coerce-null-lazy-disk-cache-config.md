---
created: 2026-07-09T14:14:00.000Z
title: Coerce the None-default lazy_disk_cache_config on PointCloudImageGenerator
area: general
resolves_phase: 4
files:
  - src/pc2img/core.py
source: .planning/phases/02-dependency-adaptation-reproducible-environment/02-RESEARCH.md (Blocker / Open Question 1)
---

## Problem

`PointCloudImageGenerator.__init__` declares
`lazy_disk_cache_config: LazyDiskCacheConfigLike = None`, where the runtime type is
`Annotated[LazyDiskCacheConfig, BeforeValidator(coerce_lazy_cfg)]`. But pydantic's
`@validate_call` **does not validate default argument values**, so the `None` default
bypasses `coerce_lazy_cfg` and reaches `FeatureManager` →
`DiskBackedImageStore(config=None)`, raising:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for DiskBackedImageStore.__init__
config  Input should be a dictionary or an instance of LazyDiskCacheConfig [input_value=None]
```

This is a **latent public-API bug on the default path**: any caller that constructs a
`PointCloudImageGenerator` without an explicit `lazy_disk_cache_config` hits it —
including `scripts/v2.0/01_manual_test_PointCloudImageGenerator.py`, which passes no
config.

Surfaced during Phase 2 RESEARCH (§Blocker / Open Question 1). Phase 2 was a
packaging/reproducibility phase; the owner resolved to **defer** the source fix and
have the SC1 smoke pass an explicit `LazyDiskCacheConfig(cache_path=<tmpdir>)` as the
correct Phase-2 workaround (no source change needed for SC1). This todo carries the
default-path fix forward so it is not lost.

## Solution

When worked in Phase 4 (quality/bugs), make the config-less default path resolve to a
sane default instead of raising. Options (TBD — pick during Phase 4):

- Add `validate_default=True` to the `@validate_call` on
  `PointCloudImageGenerator.__init__` so `coerce_lazy_cfg(None)` actually runs on the
  default.
- Handle `None` explicitly in `coerce_lazy_cfg` / `FeatureManager` /
  `DiskBackedImageStore` (coerce `None` → a default `LazyDiskCacheConfig`).
- Change the default from `None` to a sentinel and construct a default config inside
  the body.

Add a small regression check (config-less construction succeeds) when the fix lands —
promotable alongside the Phase-3 smoke/pytest work.

## Resolved (verified 2026-09-28)

Fixed in commit `0658181` ("coerce omitted config"); `PointCloudImageGenerator.__init__` now runs `coerce_lazy_cfg` on an omitted config. Closed during Phase 6 discuss.
