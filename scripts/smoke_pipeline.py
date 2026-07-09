"""SC1 smoke: single-cloud spherical -> Delaunay -> ``range`` pipeline.

Runs the full ``PointCloudImageGenerator`` pipeline end-to-end against
pchandler 2.x + GSEGUtils on a deterministic, in-code synthetic point cloud
(no external file, D-10) and asserts the ``range`` raster is finite and sane.
This is the durable SC1 evidence for Phase 2 (D-09); it is intended to be
promoted to a pytest smoke test in Phase 3.

Run with::

    uv run python scripts/smoke_pipeline.py

Exit 0 (and a printed ``OK`` line) means the pipeline works against the locked
pchandler/GSEGUtils env. The checks below are written to be sensitive: they
raise ``RuntimeError`` (not bare ``assert``, so they survive ``python -O``),
use a non-square resolution so a transposed-axes projection bug fails the shape
check, bound the ``range`` raster to its physical band (rejecting a constant /
pixel-coordinate / wrong-scalar raster that a ``> 0`` check would pass), and
assert an on-disk cache artifact is actually written so the GSEGUtils
disk-offload codec is genuinely exercised rather than silently skipped.
"""

import tempfile
from pathlib import Path

import numpy as np
from pchandler import PointCloudData
from pchandler.geometry.coordinates import rhv2xyz

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pc2img.core import PointCloudImageGenerator
from pc2img.strategies import SphericalProjection, DelaunayInterpolation


def _check(condition: bool, message: str) -> None:
    """Fail the smoke with a clear error. Unlike ``assert`` this is NOT stripped
    under ``python -O``, so a broken pipeline can never print ``OK`` and exit 0."""
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    # Deterministic synthetic cloud (D-10). Synthesize from spherical angles via
    # rhv2xyz over a real (h, v) range, NOT a flat xy plane: a planar wall gives a
    # near-degenerate horizontal FoV span and collapses the raster (RESEARCH Pitfall 2).
    rng = np.random.default_rng(42)
    n = 8000
    h = rng.uniform(-0.30, 0.30, n)  # horizontal angle (rad)
    v = rng.uniform(1.20, 1.80, n)  # vertical/polar angle (rad)
    r = 10.0 + 0.5 * np.sin(4 * h) + 0.3 * rng.standard_normal(n)  # gentle structured range
    xyz = rhv2xyz(np.column_stack([r, h, v])).astype(np.float64)
    pcd = PointCloudData(xyz=xyz)  # r / spher / fov / nbPoints all derive from xyz

    with tempfile.TemporaryDirectory() as td:
        # The explicit LazyDiskCacheConfig is load-bearing: PointCloudImageGenerator's
        # lazy_disk_cache_config=None default is NOT coerced by pydantic @validate_call
        # (it skips default-value validation), so the None default reaches
        # DiskBackedImageStore and raises a ValidationError. Passing an explicit config
        # is the correct Phase-2 workaround (RESEARCH Blocker / Pitfall 1) -- the
        # uncoerced None-default public-API bug is a known follow-up deferred to
        # Phase 4/5 (RESEARCH Open Question 1); this is a workaround, not a fix.
        #
        # enable_caching=True is required for the offload path to run: LazyDiskCacheConfig
        # defaults enable_caching=False, and DiskBackedImageData.offload() no-ops when
        # caching is disabled -- so cache_path alone writes nothing to disk. With caching
        # enabled, the generator's raster store materializes the ``range`` raster as an
        # on-disk artifact (range.dat), which is what runtime-exercises the GSEGUtils
        # LazyDiskCache offload codec (SC2 / BC-GSEG-001). This explicit config governs the
        # generator's raster store only; DelaunayInterpolation() keeps its own default
        # cache config (caching off), so the Delaunay step does not itself write to disk.
        cfg = LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True)
        gen = PointCloudImageGenerator(
            pcd,
            (200, 260),  # non-square (width, height): shape check now catches a transposed projection
            SphericalProjection(field_of_view=pcd.fov),
            DelaunayInterpolation(),
            lazy_disk_cache_config=cfg,
        )
        out = gen.generate(features=["range"])

        img = np.asarray(out["range"])
        finite_fraction = float(np.isfinite(img).mean())
        raster_min = float(np.nanmin(img))
        raster_max = float(np.nanmax(img))

        # On-disk artifacts prove the GSEGUtils offload codec actually ran (see comment
        # above). With enable_caching=False this list is empty and the pipeline would
        # otherwise "pass" without exercising the disk format at all (SC2 gap).
        artifacts = sorted(p.name for p in Path(td).rglob("*") if p.is_file())

        # Shape: ImgRes is (width, height) -> numpy (rows=height, cols=width). A projection
        # that swapped axes would yield (200, 260) and fail here.
        _check(img.shape == (260, 200), f"unexpected shape {img.shape} (expected (260, 200))")
        # Coverage: observed ~0.96; a regression that NaN-ed a large fraction of the hull
        # interior must fail. 0.90 leaves headroom for interpolation jitter without being lax.
        _check(finite_fraction > 0.90, f"too few finite pixels: {finite_fraction:.4f}")
        # Physical band: the synthetic range is ~[8.7, 11.3]. These bounds reject a constant
        # raster, a pixel-coordinate raster (~0..260), or a wrong scalar field -- all of which
        # a bare ``nanmin > 0`` check would wave through. Observed: min=8.80, max=11.27.
        _check(8.0 < raster_min < 9.5, f"range min out of band: {raster_min:.3f} (expected ~8.8)")
        _check(10.5 < raster_max < 12.0, f"range max out of band: {raster_max:.3f} (expected ~11.3)")
        # Offload proof: at least one cache artifact must have been written to disk.
        _check(
            len(artifacts) >= 1,
            f"no on-disk cache artifact under {td} -- GSEGUtils offload codec was not exercised "
            f"(is enable_caching=True?)",
        )

        # Print the diagnostic (finite fraction + shape/min/max + artifacts) so CI logs carry
        # it, not just the pass/fail from the checks.
        print(
            "OK",
            f"shape={img.shape}",
            f"finite_fraction={finite_fraction:.3f}",
            f"min={raster_min:.3f}",
            f"max={raster_max:.3f}",
            f"artifacts={artifacts}",
        )


if __name__ == "__main__":
    main()
