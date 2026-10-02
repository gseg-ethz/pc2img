---
created: 2026-10-02T14:00:00.000Z
title: Pooled tiled runs leave cache files on disk (delete-on-GC disarmed); restore cleanup once GSEGUtils finalizers delete only their own file
area: tiled
files:
  - src/pc2img/tiled_generator.py
source: Phase 7 gap round 2 (07-16, G1-CR-01 fix); owner accepted + documented 2026-10-02
---

## Problem

To stop released results deleting `.dat` files newer results read (G1-CR-01), pc2img 0.11.0 calls
`disable_purge()` on every entry returned from a pooled `generate()` (any `n_jobs` other than 1).
Consequence (plan-checker measured): after a pooled run and dropping the generator, every `.dat`
plus the codec pair stays in each tile directory (18 files vs the pair before). With no
`cache_path`, the store's `mkdtemp` directory is never cleaned, so the files persist in the temp dir.

## Next

Upstream (GSEGUtils, backlog with #82): make the purge-on-GC finalizer delete only a file its own
entry created (or a per-entry `.dat` name). Then drop the pc2img disarm and re-enable cleanup;
meanwhile consider the tiled generator removing its own default temp directory on GC.
