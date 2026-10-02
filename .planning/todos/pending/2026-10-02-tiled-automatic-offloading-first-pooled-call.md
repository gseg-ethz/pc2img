---
created: 2026-10-02T13:30:00.000Z
title: Tiled generator with automatic_offloading=True fails on the first pooled generate() (AttributeError '_data')
area: tiled
files:
  - src/pc2img/tiled_generator.py
  - src/pc2img/image_cache/disk_backed_image_store.py
source: Phase 7 gap round 1 review (07-REVIEW-GAP1.md IN-05, UAT G1-IN-05; owner deferred 2026-10-02)
---

## Problem

`TiledPointCloudImageGenerator` configured with `LazyDiskCacheConfig(automatic_offloading=True)`
raises `AttributeError: '_data'` on the FIRST `generate(..., n_jobs>=2)`. Reproduced by the
gap-round-1 reviewer on both the pre-fix tree (271b208) and the fixed tree; it predates Phase 7's
per-tile dispatch. Scratch repro: `gap1/` in the 2026-10-02 session scratchpad (not durable).

## Next

Reproduce on the released 0.11.0, find whether offloaded entries lose `_data` across the worker
pickle round-trip, and add a pooled test with `automatic_offloading=True`.
