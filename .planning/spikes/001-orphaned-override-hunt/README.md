---
spike: 001
name: orphaned-override-hunt
type: standard
validates: "Given every pc2img subclass of a GSEGUtils class and the released GSEGUtils 0.6.0 wheel, when each pc2img-defined name is classified against what upstream still defines and calls, then every override is either absorbed (deletable) or an upstream gap — including the extend_cache_path drift re-derivation"
verdict: VALIDATED
related: [000-absorption-test, 004-blast-radius-gsegutils-0.6.0]
tags: [gsegutils, mro, bc-gseg-006, drift, orphan, purge, 0.6.0]
---

# Spike 001: Orphaned-Override Hunt (target: PyPI GSEGUtils 0.6.0 wheel)

Run during Phase 7 research (decision D-04). Target is the **released wheel** users install
(D-05), not the phase-14 dev tree spike 000 measured. Investigation only: no edit to `src/`,
`tests/`, `pyproject.toml` or `uv.lock`; the override removal is simulated by
`target_store.py` (a local subclass of the upstream `DiskBackedStore`), and one scratch
overlay copy of `src/` (outside the repo) was used for the loky arm.

## Import provenance (asserted in the test process, `provenance.py`)

| check | value |
|---|---|
| `GSEGUtils.__version__` / distribution metadata | `0.6.0` / `0.6.0` |
| `GSEGUtils.__file__` | `<scratch-venv>/lib/python3.12/site-packages/GSEGUtils/__init__.py` (installed wheel) |
| `direct_url.json` | absent (index install, not editable/VCS) |
| `grep -c 'self\._get_npy_path'` on `disk_backed_store.py` | **0** (0.5.x fingerprint: non-zero) |
| `DiskBackedStore` has `_get_npy_path` | `False` |
| `pchandler` (metadata) | `2.1.1` |
| `pc2img.__file__` | `/scratch/31_pc2img/src/pc2img/__init__.py` (the tree under test) |

## How to run

```bash
uv venv --python 3.12 /tmp/s001 && uv pip install --python /tmp/s001/bin/python \
  "GSEGUtils==0.6.0" "pchandler==2.1.1" "joblib~=1.5" "numpy~=2.0" "imageio~=2.31" "Pillow~=10.0" \
  "pydantic~=2.11" "scipy~=1.14" "typing-extensions~=4.9" "tifffile[all]~=2024.1" "opencv-python~=4.0" pytest pyyaml
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/scratch/31_pc2img/src
/tmp/s001/bin/python .planning/spikes/001-orphaned-override-hunt/provenance.py
/tmp/s001/bin/python .planning/spikes/001-orphaned-override-hunt/test_orphan_hunt.py
/tmp/s001/bin/python .planning/spikes/001-orphaned-override-hunt/test_store_semantics.py
/tmp/s001/bin/python .planning/spikes/001-orphaned-override-hunt/test_r4_overwrite_residuals.py
/tmp/s001/bin/python .planning/spikes/001-orphaned-override-hunt/test_concurrent_reload_race.py 12 4
```

## Results

### A. Orphan hunt (static + MRO, `test_orphan_hunt.py`)

Two pc2img classes subclass a GSEGUtils class:
`DiskBackedImageData` (`DiskBackedNDArray` > `LazyDiskCache`) and `DiskBackedImageStore`
(`DiskBackedStore`).

| pc2img name | verdict on 0.6.0 |
|---|---|
| `DiskBackedImageStore._get_npy_path`, `._get_meta_path` | **ORPHAN** — base defines neither; both `super()` calls are **DANGLING** (`AttributeError: 'super' object has no attribute '_get_npy_path'`) |
| `._assert_within_cache_dir` | pc2img-only helper; its only callers are the two orphans above -> orphan by transitivity |
| `.__delitem__` | **LIVE** — upstream `pop` (`disk_backed_store.py:1300,1304`) and `clear` (`:1377`) reach it through `del self[key]` (a dunder dispatch an attribute scan cannot see; the scanner was corrected to look for it). It is the only pc2img override upstream still reaches, which is why keeping it would turn `clear()` into a cache-destroying call. Replaced by upstream `purge` (D-08) |
| `.offload` | LIVE, signature drift noted: pc2img's parameter is `features`, upstream's is `keys`. Upstream only ever calls `self.offload(pickle_container=True)` (`disk_backed_store.py:2305`), so nothing breaks; an external caller passing `keys=` to a pc2img store would get `TypeError` (pre-existing, not a regression) |
| `.add_image_to_store`, `.image_data`, `.offload_image_data_to_disk` | pc2img-only API, no base counterpart |
| `DiskBackedImageData.__init__` | LIVE; `**lazy_disk_cache_settings` still matches `DiskBackedNDArray.__init__(data, **settings)` |
| `DiskBackedImageData.to_uint8` | pc2img-only |
| `LazyDiskCache` buffer hooks | **none overridden by pc2img** — `_describe_buffer`, `_drop_buffer`, `_set_buffer`, `_describe_shape_dtype` are inherited from `DiskBackedNDArray`; reload-class registration (`register_lazy_disk_cache_class`) still works: 2-D f32, 2-D u8 and (H,W,3) f32 round-trip, `.meta.json` records `lazy_disk_cache_class: DiskBackedImageData`, a fresh store re-adopts and reloads them |

All 10 `from GSEGUtils... import X` statements in `src/`, `tests/`, `scripts/` (excluding the
vendored `scripts/v1.0|v2.0` snapshots) resolve on 0.6.0 (`CacheDefaults`, `get_defaults`,
`Array_Nx2_Float_T`, `Vector_Bool_T`, `register_lazy_disk_cache_class`, ...). pc2img also uses
`DiskBackedStore[DiskBackedNDArray]` **directly** (not subclassed) for triangulation precalcs
(`strategies/interpolation.py:202`): keys `triangles`/`simplices`/`verts`/`bary` are legal.

### B. `extend_cache_path` drift (BC-GSEG-006) — all five sites re-derived

Sites (current tree, unchanged since the handoff's ref): `tiled_generator.py:71,74,162,171`,
`strategies/interpolation.py:203`. `test_store_semantics.py` §S3 measured:

* realistic folder names pass: `tile_03`, `0`, `tile-0`, `tile 03`, a 64-hex sha256 digest;
* refused with `StoreKeyError` (a `ValueError`): `../x`, `a/b`, `/tmp/x`, `''`, `.`, `CON`, `t.`;
* a planted directory symlink pointing outside the cache root: `StoreContainmentError`
  (new refusal, `ValueError` subtype);
* a non-`str` tile id (`5`): pydantic `ValidationError` from `@validate_call` (pre-existing type
  check, not a store-key refusal);
* `TIGSettings.extend_cache_paths('../x')` surfaces `StoreKeyError` unwrapped;
* a hostile tile id through the **real loky path** (`TiledPointCloudImageGenerator.generate`,
  `n_jobs=2`) arrives in the parent as `StoreKeyError` (the exception types pickle round-trip);
  nothing was created outside the cache directory.

### C. Store semantics on the simulated end state (`target_store.py`)

See 07-RESEARCH.md for the tables; headline measurements:

* Phase-5 escape corpus (3 spellings) x 9 routes (add_image_to_store, setitem, setitem+del,
  add+offload, purge, getitem, pop, get, add_data_to_store): **every mutating/reading route
  refuses with `StoreKeyError`** (MRO `StoreKeyError > ValueError`), directory tree bit-for-bit
  unchanged, sentinel intact; `get()` returns its default (no exception). **The mapping
  setter refuses at set time** — the Phase-5 tests that seeded an escaping key through
  `store[key] = ...` and then expected `del` to refuse can no longer reach the delete.
* `purge` removes `.dat`, `.npy`, `.meta.json` (the set pc2img's pipeline writes is `.dat`),
  works for in-memory, plain-offloaded and codec-offloaded entries, raises `KeyError` for a key
  that is neither tracked nor on disk, and is refused from a forked child / a loky worker
  holding a parent-constructed store with `StorePurgeRefusedError` (`RuntimeError`).
* `del` / `pop` / `clear` drop tracking only; an offloaded entry is **re-adopted by the very
  next read** and by any fresh store over the directory.
* `.store` / `image_data` is a `mappingproxy`: `st[k]=v` and `del st[k]` raise `TypeError`;
  `.pop/.clear/.update/.setdefault` raise `AttributeError` (the method does not exist).

### D. Delta vs spike 000 (phase-14 dev tree, `0.5.0.post28`)

| spike-000 finding | 0.6.0 wheel |
|---|---|
| escape corpus 12/12 refused, all lexical | same (and 9 routes, 27 cells, all refused) |
| `.dat` symlink planted at a legal key was **followed**, sentinel overwritten | **closed**: `StoreContainmentError`, sentinel intact (`add_image_to_store`); a planted `.dat.tmp` symlink is also refused |
| `.npy` symlink: replaced atomically, sentinel intact | adopted symlink to a target outside the cache: `purge`/overwrite refused with `StorePurgeForeignArtefactError` |
| not measured | planted `.npy.tmp` and `.meta.json.tmp` symlinks are **still followed** — sentinel overwritten (needs write access to the cache dir; the documented non-adversarial residual) |
| not measured | an entry **supplied with its own `cache_path`** outside the cache dir (setter inserts it, key is legal) still offloads there — containment covers key-derived paths only |

### E. Surprise (not an override): concurrent reload races on `<key>.dat.tmp`

A second or later `TiledPointCloudImageGenerator.generate()` (>= 2 tiles, `n_jobs >= 2`)
fails in the loky workers with `BrokenProcessPool` / `TerminatedWorkerError` on 0.6.0 and
succeeds on 0.5.3. Worker traceback: `DiskBackedStore.__setstate__ -> _load_entry ->
LazyDiskCache._convert_to_memmap -> os.chmod('<tile>/range.dat.tmp'): FileNotFoundError`.
Cause: 0.6.0 writes every `.dat` through one fixed `<key>.dat.tmp` name, and every worker
unpickles the whole generator (`self._process_tile` is a bound method; `self.image_generators`
holds every tile's store) and rebuilds each entry's `.dat` — N processes race one temp name.
`test_concurrent_reload_race.py` reproduces it with GSEGUtils alone: 11/12 rounds fail on 0.6.0
(`FileNotFoundError`, and workers killed by SIGBUS, exit code -7), 0/12 on 0.5.3. Latest PyPI
GSEGUtils is 0.6.0 (no fix released). **Not caused by the migration** — the traceback never
touches pc2img's store.

## Verdict

**VALIDATED, with one surfaced upstream defect.** Every pc2img override of a GSEGUtils member is
either orphaned (`_get_npy_path`, `_get_meta_path`, the `_assert_within_cache_dir` helper:
absorbed, deletable) or superseded by an upstream verb (`__delitem__` -> `purge`). No pc2img
override is an upstream *gap*. The concurrent-reload race (§E) is not an override gap but it is
an adoption blocker for the tiled re-generate path and needs an owner decision.
