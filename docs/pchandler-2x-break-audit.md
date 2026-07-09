# pchandler 2.x Break Audit (DEP-01 / DEP-02)

**Audited:** 2026-07-09
**Phase:** 02 — Dependency Adaptation & Reproducible Environment
**Scope:** `src/pc2img/` call sites against the pchandler / GSEGUtils v2.x migration
break lists.
**Verdict:** All three named pchandler 2.x semantic breaks have **zero call sites**
in `src/pc2img/`. DEP-01/DEP-02 are satisfied by an audit attestation (the breaks
are *not broken* because they are *not called*), plus a runtime smoke that proves
the surface the library actually exercises.

This is the honest, proportionate DEP-01/DEP-02 deliverable per D-11 ("audit the
call sites, fix if broken") — the finding is simply "not broken because not
called." No `src/pc2img/` source was edited to satisfy these breaks, and (per D-13)
no `pchandler` / `GSEGUtils` sibling source was edited.

## How this was verified (reproducible evidence)

The audit is a grep of the library source for the identifiers introduced/changed by
the three named breaks. Re-run exactly this command — it is byte-for-byte identical
to the command in Plan 02-03 Task 2's automated `<verify>`:

```bash
grep -rEn "FoVTree|to_py4dgeo|\bCsv\b|\bLas\b|load_csv|load_las" src/pc2img/
```

**Result:** no matches (exit status 1). Zero call sites for any of the named-break
identifiers in the library. Anyone can re-run the command above to confirm the
attestation still holds.

## Named pchandler 2.x breaks — attestation

| Break ID | What changed in pchandler 2.x | Call sites in `src/pc2img/` | Verdict |
|----------|-------------------------------|-----------------------------|---------|
| **BC-PCH-008** | `FoVTree` now emits collision-free 2D `"<r>-<c>"` identifiers; `build_from_tiles` / `__getitem__` / `.identifier` changed accordingly | **NONE** — `grep FoVTree src/pc2img/` returns nothing. `FoVTree` appears only in the example driver `scripts/v2.0/03_tiled_image_gen.py`, not in library code. `tiled_generator.py` consumes **pre-built** `PointCloudTile`s; it never builds a `FoVTree`. | Not affected — audit-only |
| **BC-PCH-007** | `PointCloudData.to_py4dgeo` now returns world-frame (not shift-frame) coords and preserves normals/scalar fields | **NONE** — `grep to_py4dgeo src/pc2img/` returns nothing. | Not affected — audit-only |
| **BC-PCH-006 / BC-PCH-012** | `Las.load` caller-wins `numerical_optimization_shift`; `Csv.load` strict-by-name field selection raising `ValueError` on missing fields | **NONE** — no `Csv`/`Las`/`load_csv`/`load_las` in `src/pc2img/`. The only loaders anywhere are `load_ply`/`load_e57`/`Ply.load` in example `scripts/`, and the only `.load(` in `src/pc2img/` is pc2img's own image-store pickle offload. | Not affected — audit-only |

## Accuracy corrections (carried from RESEARCH — do not drop)

1. **The library exercises pchandler's `FoV`, NOT `FoVTree`.** CONTEXT/D-11 framed
   the spherical projection as exercising "`FoV`/`FoVTree`", but pc2img's spherical
   projection (`src/pc2img/strategies/projection.py`) only touches `FoV` (via
   `pcd.fov`), `FoVFilter`/`BoxFilter`, `rhv2xyz`, and `PointCloudData` properties
   (`pcd.spher`, `pcd.fov`, `pcd.r`, `pcd.nbPoints`, `pcd.scalar_fields`). `FoV` is a
   distinct symbol from `FoVTree`, and BC-PCH-008 did **not** change `FoV`. So the
   SC1 smoke **runtime-proves the exercised `FoV`/spherical surface**; BC-PCH-008
   gets this documented negative audit (it cannot be runtime-proven because the
   library never calls `FoVTree`).

2. **All three named breaks are absent from the library, so no source edits were
   made — and none to `pchandler`/`GSEGUtils` were needed** (D-13 respected). The
   deliverable is an attestation, not a code fix.

## GSEGUtils reality (DEP-02 / SC2)

- **Casing gotcha:** the distribution name is `gsegutils` (what pip/uv installs);
  the importable package is `GSEGUtils` (capitalized). pc2img imports use the
  capitalized form correctly, and the `pyproject.toml` requirement keeps `GSEGUtils`
  capitalized (D-02). pip normalizes case for *resolution* regardless.
- **No GSEGUtils BC required a pc2img source change.** BC-GSEG-001 (on-disk format
  moved from pickle to `.npy` + `.meta.json`, refusing legacy `.pkl`) does not affect
  pc2img: the library creates *fresh* `DiskBackedStore` caches at runtime (e.g. the
  Delaunay triangulation cache), which materialize in the new format — there is no
  legacy `.pkl` to migrate. BC-GSEG-002/003/005 are additive or behaviour-preserving
  and are not on any pc2img call path. The DiskBackedStore/LazyDiskCache surface is
  runtime-exercised by the Delaunay step in the SC1 smoke.

## Runtime proof (what IS exercised)

The exercised surface is proven by `scripts/smoke_pipeline.py` (SC1): a deterministic
synthetic cloud runs the single-cloud spherical → Delaunay → `range` pipeline
end-to-end against the locked pchandler 2.x + GSEGUtils env, exiting 0 with finite
output. Importing the smoke pulls the full `pc2img` module graph (core → strategies →
features → image_cache → tiled_generator), so every `pchandler.*` / `GSEGUtils.*`
import resolves, and Delaunay exercises the GSEGUtils `DiskBackedStore` cache path
(SC2).

## Known follow-ups (out of scope for Phase 2)

- **Uncoerced `None`-default cache config.** `PointCloudImageGenerator`'s
  `lazy_disk_cache_config=None` default is not coerced by pydantic `@validate_call`
  (default-value validation is skipped), so a config-less caller hits a
  `ValidationError`. The Phase-2 workaround is to pass an explicit
  `LazyDiskCacheConfig` (as the smoke does). The default-path fix is deferred to
  Phase 4/5 and tracked as a pending todo
  (`.planning/todos/pending/2026-07-09-coerce-null-lazy-disk-cache-config.md`,
  `resolves_phase: 4`).
