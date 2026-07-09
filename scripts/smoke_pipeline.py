"""SC1 smoke: single-cloud spherical -> Delaunay -> ``range`` pipeline.

Runs the full ``PointCloudImageGenerator`` pipeline end-to-end against
pchandler 2.x + GSEGUtils on a deterministic, in-code synthetic point cloud
(no external file, D-10) and asserts the ``range`` raster is finite and sane.
This is the durable SC1 evidence for Phase 2 (D-09); it is intended to be
promoted to a pytest smoke test in Phase 3.

Run with::

    uv run python scripts/smoke_pipeline.py

Exit 0 (and a printed ``OK`` line) means the pipeline works against the locked
pchandler/GSEGUtils env.
"""

import logging
import tempfile
from pathlib import Path

import numpy as np
from pchandler import PointCloudData
from pchandler.geometry.coordinates import rhv2xyz

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pc2img.core import PointCloudImageGenerator
from pc2img.strategies import SphericalProjection, DelaunayInterpolation

logger = logging.getLogger(__name__.split(".")[0])


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
        # NOTE: this explicit config does NOT govern both caches. DelaunayInterpolation()
        # keeps its own default cache config (src/pc2img/strategies/interpolation.py),
        # so the Delaunay step exercises the GSEGUtils DiskBackedStore surface through
        # its own default cache while the generator's raster store uses the explicit
        # config here. Both still exercise the GSEGUtils disk-cache path (SC2), just
        # through two independent configs.
        cfg = LazyDiskCacheConfig(cache_path=Path(td))
        gen = PointCloudImageGenerator(
            pcd,
            (200, 200),
            SphericalProjection(field_of_view=pcd.fov),
            DelaunayInterpolation(),
            lazy_disk_cache_config=cfg,
        )
        out = gen.generate(features=["range"])

        img = np.asarray(out["range"])
        finite_fraction = float(np.isfinite(img).mean())

        assert img.shape == (200, 200), f"unexpected shape {img.shape}"
        assert finite_fraction > 0.5, f"too few finite pixels: {finite_fraction}"
        assert np.nanmin(img) > 0, "range must be a positive distance"

        # Print the diagnostic (finite fraction + shape/min/max) so CI logs carry it,
        # not just the pass/fail from the asserts.
        print(
            "OK",
            f"shape={img.shape}",
            f"finite_fraction={finite_fraction:.3f}",
            f"min={float(np.nanmin(img)):.3f}",
            f"max={float(np.nanmax(img)):.3f}",
        )


if __name__ == "__main__":
    main()
