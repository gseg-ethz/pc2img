"""Spike 000, part 4 — the ``.dat`` survivor, run to ground.

Part 3 produced two results that only make sense together:

  * a real ``generate()`` run wrote ONLY ``['hillshade_range_315_45.dat',
    'range.dat']`` — no ``.npy``, no ``.meta.json``;
  * a symlink planted at ``<key>.dat`` was FOLLOWED by the writer and the
    outside sentinel was overwritten — under phase-14 alone AND with pc2img's
    guard live.

So the containment work on both sides guards the artefact family pc2img's real
pipeline does not write, and leaves unguarded the one it does. This module
establishes that precisely rather than by inference:

  Q1. Which code object writes the ``.dat``, and does its path go through
      ``paths._build`` (and therefore ``_assert_contained``) at all?
  Q2. Does ``generate()`` ever call the store codec pair (``_store_entry``)?
  Q3. Can an escaping name reach the ``.dat`` writer through a route pc2img
      actually uses — or is the store key rule the only door, keeping this
      theoretical?
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from provenance import print_provenance  # noqa: E402

print_provenance()

import numpy as np  # noqa: E402
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig  # noqa: E402
from GSEGUtils.lazy_disk_cache import paths as gseg_paths  # noqa: E402

from pc2img.image_cache import DiskBackedImageData, DiskBackedImageStore  # noqa: E402

_SENTINEL = b"dat-writer sentinel -- must not be touched"


# --------------------------------------------------------------------------- #
# Q1/Q2 — instrument the shared builders and the codec pair, then run the      #
#         real pipeline and see which ones actually fire.                      #
# --------------------------------------------------------------------------- #
def instrumented_generate() -> None:
    from pchandler import PointCloudData
    from pchandler.geometry.coordinates import rhv2xyz

    from pc2img.core import PointCloudImageGenerator
    from pc2img.strategies import DelaunayInterpolation, SphericalProjection

    calls: dict[str, list] = {"paths._build": [], "_assert_contained": [], "_store_entry": []}

    real_build = gseg_paths._build
    real_contained = gseg_paths._assert_contained

    def spy_build(cache_dir, key, suffix):
        calls["paths._build"].append((str(key), str(suffix)))
        return real_build(cache_dir, key, suffix)

    def spy_contained(cache_dir, candidate):
        calls["_assert_contained"].append(str(candidate))
        return real_contained(cache_dir, candidate)

    gseg_paths._build = spy_build
    gseg_paths._assert_contained = spy_contained

    from GSEGUtils.lazy_disk_cache.disk_backed_store import DiskBackedStore

    real_store_entry = DiskBackedStore._store_entry

    def spy_store_entry(self, key, *a, **kw):
        calls["_store_entry"].append(str(key))
        return real_store_entry(self, key, *a, **kw)

    DiskBackedStore._store_entry = spy_store_entry

    try:
        rng = np.random.default_rng(42)
        n = 4000
        h = rng.uniform(-0.30, 0.30, n)
        v = rng.uniform(1.20, 1.80, n)
        r = 10.0 + 0.5 * np.sin(4 * h) + 0.3 * rng.standard_normal(n)
        pcd = PointCloudData(xyz=rhv2xyz(np.column_stack([r, h, v])).astype(np.float64))

        with tempfile.TemporaryDirectory() as td:
            cfg = LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True)
            gen = PointCloudImageGenerator(
                pcd, (120, 160),
                SphericalProjection(field_of_view=pcd.fov),
                DelaunayInterpolation(),
                lazy_disk_cache_config=cfg,
            )
            gen.generate(features=["range"])
            written = sorted(p.name for p in Path(td).rglob("*") if p.is_file())
    finally:
        gseg_paths._build = real_build
        gseg_paths._assert_contained = real_contained
        DiskBackedStore._store_entry = real_store_entry

    print(f"  files written by generate()   : {written}")
    print(f"  paths._build calls            : {len(calls['paths._build'])} {calls['paths._build'][:6]}")
    print(f"  paths._assert_contained calls : {len(calls['_assert_contained'])}")
    print(f"  DiskBackedStore._store_entry  : {len(calls['_store_entry'])} {calls['_store_entry'][:6]}")
    print()
    if not calls["_store_entry"]:
        print("  => generate() NEVER reaches the store codec pair. The .npy/.meta.json")
        print("     path builders — and pc2img's override on them — do not run at all.")
    if not any(s == ".dat" for _, s in calls["paths._build"]):
        print("  => the .dat path is NOT built by paths._build, so it never reaches")
        print("     _assert_contained. It is outside the phase-14 containment seam.")


# --------------------------------------------------------------------------- #
# Q1 cont. — who owns the .dat path, and is it validated?                      #
# --------------------------------------------------------------------------- #
def locate_dat_writer() -> None:
    import inspect

    from GSEGUtils.lazy_disk_cache.lazy_disk_cache import LazyDiskCache

    for name in ("offload", "_get_cache_file_path", "cache_file_path", "_cache_file"):
        obj = getattr(LazyDiskCache, name, None)
        if obj is None:
            continue
        try:
            src_file = inspect.getsourcefile(obj)
            _, lineno = inspect.getsourcelines(obj)
            print(f"  LazyDiskCache.{name:22s} -> {Path(src_file).name}:{lineno}")
        except (TypeError, OSError):
            print(f"  LazyDiskCache.{name:22s} -> <not a function>")

    src = inspect.getsource(LazyDiskCache)
    print(f"  '.dat' literal in LazyDiskCache source : {'.dat' in src}")
    print(f"  LazyDiskCache calls paths._build       : {'paths._build' in src or '_build(' in src}")
    print(f"  LazyDiskCache calls _assert_contained  : {'_assert_contained' in src}")
    print(f"  LazyDiskCache uses os.replace (atomic) : {'os.replace' in src or 'replace(' in src}")


# --------------------------------------------------------------------------- #
# Q3 — can an escaping name reach the .dat writer through a real route?        #
# --------------------------------------------------------------------------- #
def probe_direct_dat(name: str) -> str:
    """DiskBackedImageData constructed directly — the route FeatureManager uses."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        sentinel = tmp / "victim.bin"
        sentinel.write_bytes(_SENTINEL)
        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        try:
            dbid = DiskBackedImageData(
                np.zeros((4, 4), np.float32), lazy_disk_cache_config=cfg
            )
            dbid.name = name  # type: ignore[attr-defined]
            dbid.offload()
        except BaseException as e:  # noqa: BLE001
            return f"refused: {type(e).__name__}: {str(e)[:60]}"
        intact = sentinel.exists() and sentinel.read_bytes() == _SENTINEL
        inside = sorted(p.name for p in cache_dir.rglob("*") if p.is_file())
        outside = sorted(p.name for p in tmp.iterdir() if p.is_file())
        return f"ALLOWED sentinel={'INTACT' if intact else '!! DAMAGED'} in={inside} out={outside}"


def probe_store_key_gate() -> None:
    """Is the store key rule the only door to a .dat filename in pc2img's flow?"""
    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td) / "cache"
        cache_dir.mkdir()
        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        store = DiskBackedImageStore(config=cfg)
        for key in ("../victim", "a/../../victim"):
            try:
                store.add_image_to_store(key, np.zeros((3, 3), np.float32))
                print(f"    {key!r:20s} -> ALLOWED through the store")
            except BaseException as e:  # noqa: BLE001
                print(f"    {key!r:20s} -> refused by {type(e).__name__} (store key rule)")


if __name__ == "__main__":
    print("=" * 78)
    print("Q1/Q2 — instrumented generate(): which writers and seams actually fire")
    print("=" * 78)
    instrumented_generate()

    print()
    print("=" * 78)
    print("Q1 cont. — who owns the .dat path")
    print("=" * 78)
    locate_dat_writer()

    print()
    print("=" * 78)
    print("Q3 — reachability of an escaping name at the .dat writer")
    print("=" * 78)
    print("  direct DiskBackedImageData route (what FeatureManager constructs):")
    for nm in ("range", "../victim", "a/../../victim"):
        print(f"    {nm!r:20s} -> {probe_direct_dat(nm)}")
    print("  via the store (the door pc2img's pipeline actually uses):")
    probe_store_key_gate()
