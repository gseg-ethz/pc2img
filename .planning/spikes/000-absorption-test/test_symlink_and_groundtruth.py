"""Spike 000, part 3 — settle the symlink divergence + capture ground truth.

Part 1 (differential) found the ONE input class where pc2img's override and
phase-14 diverge: a symlink inside the cache directory whose name is a legal,
separator-free store key. pc2img REFUSES it; phase-14 ALLOWS it — but the
outside sentinel survived anyway.

"Allowed but undamaged" is not a finding until you know WHY. Two candidate
explanations with opposite implications:

  (a) the writer uses atomic replace (tmp + os.replace), which REPLACES the
      symlink inode rather than following it  -> genuinely safe, override adds
      nothing but a stricter error;
  (b) my probe simply aimed at the wrong artefact -> the dangerous one is still
      open and this is a real phase-14 gap.

pc2img writes THREE artefacts per key (observed: ``<key>.dat``,
``<key>.meta.json``, ``<key>.npy``) and they do not all come from the same
writer — ``.dat`` is ``LazyDiskCache``'s own payload, the other two are the
store codec pair. So each is symlinked and measured independently.

Also folds in old spike 002: a real ``PointCloudImageGenerator.generate()`` run
with the cache directory listed verbatim, to settle which writer actually puts
pc2img's artefacts on disk.
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

from pc2img.image_cache import DiskBackedImageStore  # noqa: E402
from test_absorption import NoGuardImageStore, _gray  # noqa: E402

_SENTINEL = b"symlink sentinel -- must not be touched"


def probe_symlinked_artefact(store_cls, suffix: str) -> dict:
    """Symlink ``<key><suffix>`` inside the cache dir at an outside sentinel."""
    key = "evil"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        sentinel = tmp / "victim.bin"
        sentinel.write_bytes(_SENTINEL)
        link = cache_dir / f"{key}{suffix}"
        link.symlink_to(sentinel)

        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        store = store_cls(config=cfg)
        outcome = "ALLOWED"
        try:
            store.add_image_to_store(key, _gray((4, 4)))
            store.offload_image_data_to_disk(key)
        except BaseException as e:  # noqa: BLE001
            outcome = f"refused: {type(e).__name__}"

        intact = sentinel.exists() and sentinel.read_bytes() == _SENTINEL
        still_link = link.is_symlink() if link.exists() or link.is_symlink() else False
        return {
            "suffix": suffix,
            "outcome": outcome,
            "sentinel": "INTACT" if intact else "!! DAMAGED",
            "link_survived": still_link,
            "why": (
                "symlink replaced (atomic write)"
                if (intact and not still_link)
                else "symlink untouched"
                if (intact and still_link)
                else "WRITE FOLLOWED THE SYMLINK"
            ),
        }


def ground_truth_cache_listing() -> None:
    """Old spike 002, folded in: a real generate() run, cache dir listed verbatim."""
    from pchandler import PointCloudData
    from pchandler.geometry.coordinates import rhv2xyz

    from pc2img.core import PointCloudImageGenerator
    from pc2img.strategies import DelaunayInterpolation, SphericalProjection

    rng = np.random.default_rng(42)
    n = 8000
    h = rng.uniform(-0.30, 0.30, n)
    v = rng.uniform(1.20, 1.80, n)
    r = 10.0 + 0.5 * np.sin(4 * h) + 0.3 * rng.standard_normal(n)
    pcd = PointCloudData(xyz=rhv2xyz(np.column_stack([r, h, v])).astype(np.float64))

    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td)
        cfg = LazyDiskCacheConfig(cache_path=cache_dir, enable_caching=True)
        gen = PointCloudImageGenerator(
            pcd,
            (200, 260),
            SphericalProjection(field_of_view=pcd.fov),
            DelaunayInterpolation(),
            lazy_disk_cache_config=cfg,
        )
        out = gen.generate(features=["range", "hillshade_range_315_45"])
        img = np.asarray(out["range"])

        print(f"  generate() -> range raster {img.shape}, "
              f"finite={float(np.isfinite(img).mean()):.3f}, "
              f"min={float(np.nanmin(img)):.2f}, max={float(np.nanmax(img)):.2f}")
        print()
        print("  VERBATIM: sorted(p.name for p in cache_dir.iterdir())")
        print(f"  {sorted(p.name for p in cache_dir.iterdir())}")
        print()
        print("  Recursive (files only), with sizes:")
        for p in sorted(cache_dir.rglob("*")):
            if p.is_file():
                print(f"    {p.relative_to(cache_dir)}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    print("=" * 78)
    print("SYMLINK DIVERGENCE — one probe per artefact, per writer")
    print("=" * 78)
    for label, cls in (
        ("phase-14 alone (guard REMOVED)", NoGuardImageStore),
        ("pc2img guard LIVE", DiskBackedImageStore),
    ):
        print(f"\n  {label}")
        for suffix in (".npy", ".meta.json", ".dat"):
            r = probe_symlinked_artefact(cls, suffix)
            print(
                f"    {r['suffix']:12s} {r['outcome']:22s} sentinel: {r['sentinel']:11s} "
                f"link survived: {str(r['link_survived']):5s}  {r['why']}"
            )

    print()
    print("=" * 78)
    print("GROUND TRUTH (folded spike 002) — real generate() run, cache dir verbatim")
    print("=" * 78)
    ground_truth_cache_listing()
