"""TEST-03 interpolation sensors for ``strategies/interpolation.py`` (Phase 5, BUG-05).

M-06 is **KEPT-BEHAVIOR** (D-06): the Delaunay interior-culling heuristic is a
*deliberate* choice — it measurably reduced artifact noise in a downstream
optical-flow task — so these tests **pin** it (Pitfall 5), they do not "fix" it.

The held-out oracle is ``scipy.interpolate.LinearNDInterpolator``: a query point is
NaN **iff** it falls outside the convex hull (``Delaunay.find_simplex == -1``). With
interior culling inactive, ``DelaunayInterpolation`` must reproduce that NaN
placement exactly. The barycentric weights are **CONFIRMED-CORRECT** (04-FINDINGS)
and are pinned here — a linear field is reproduced to ~1e-13 — not re-opened.

All fixtures are pure numpy arrays (no ``PointCloudData``): the interpolation layer
operates on scattered ``(values, points2d)`` and a ``(grid_x, grid_y)`` mesh, so a
seeded/deterministic grid is the whole contract.

Grid geometry
-------------
* ``_uniform_points`` — a regular unit grid. Every Delaunay triangle is congruent,
  so ``area``/``aspect_ratio`` have zero spread and the culling thresholds admit
  **all** triangles ("culling inactive"). Here Delaunay == the scipy oracle.
* ``_holed_points`` — the same grid with a central block removed. Delaunay bridges
  the hole with large, elongated triangles whose area exceeds ``median * 10`` and
  whose aspect ratio exceeds the MAD threshold, so culling **fires** and stamps the
  hole interior NaN even though it lies inside the convex hull. This is exactly the
  M-06 kept-behavior we pin.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import LinearNDInterpolator

from pc2img.strategies.interpolation import DelaunayInterpolation

# Linear scalar field f(x, y) = 2x + 3y + 1 — reproduced exactly by barycentric
# interpolation over any triangulation, so it is the natural weight oracle.
_A, _B, _C = 2.0, 3.0, 1.0


def _linear_field(pts: NDArray) -> NDArray:
    """The reference linear field evaluated at ``(N, 2)`` points."""
    return _A * pts[:, 0] + _B * pts[:, 1] + _C


def _uniform_points(n: int = 11, step: float = 1.0) -> NDArray:
    """A regular ``n x n`` unit grid — all Delaunay triangles congruent (culling inactive)."""
    axis = np.arange(n, dtype=float) * step
    gx, gy = np.meshgrid(axis, axis)
    return np.column_stack([gx.ravel(), gy.ravel()])


def _holed_points(n: int = 11, lo: float = 3.0, hi: float = 7.0) -> NDArray:
    """The uniform grid with the interior block ``[lo, hi]^2`` removed (triggers culling)."""
    pts = _uniform_points(n)
    inside_hole = (pts[:, 0] >= lo) & (pts[:, 0] <= hi) & (pts[:, 1] >= lo) & (pts[:, 1] <= hi)
    return pts[~inside_hole]


def _query_mesh(lo: float = 0.5, hi: float = 9.5, n: int = 40) -> tuple[NDArray, NDArray]:
    """A dense interior query mesh, kept clear of the hull edge to isolate culling effects."""
    axis = np.linspace(lo, hi, n)
    return np.meshgrid(axis, axis)


def _scipy_oracle(values: NDArray, points2d: NDArray, grid_x: NDArray, grid_y: NDArray) -> NDArray:
    """The held-out oracle: NaN iff outside the convex hull, otherwise the linear value."""
    return LinearNDInterpolator(points2d, values)(grid_x, grid_y)


# --------------------------------------------------------------------------- #
# Barycentric weights — CONFIRMED-CORRECT, pinned                             #
# --------------------------------------------------------------------------- #
def test_barycentric_reproduces_linear_field_within_tolerance():
    """A linear field is recovered to ~1e-13 wherever the interpolant is defined."""
    pts = _uniform_points()
    values = _linear_field(pts)
    grid_x, grid_y = _query_mesh()

    out = DelaunayInterpolation().interpolate(values, pts, grid_x, grid_y)
    expected = _A * grid_x + _B * grid_y + _C

    defined = ~np.isnan(out)
    assert defined.any(), "interpolant produced only NaN — grid/points misconfigured"
    np.testing.assert_allclose(out[defined], expected[defined], atol=1e-13, rtol=0)


# --------------------------------------------------------------------------- #
# Oracle — culling inactive on the uniform grid                              #
# --------------------------------------------------------------------------- #
def test_uniform_grid_matches_scipy_oracle_nan_placement():
    """On a congruent grid, culling admits every triangle, so NaN placement == scipy."""
    pts = _uniform_points()
    values = _linear_field(pts)
    grid_x, grid_y = _query_mesh()

    out = DelaunayInterpolation().interpolate(values, pts, grid_x, grid_y)
    oracle = _scipy_oracle(values, pts, grid_x, grid_y)

    # Same NaN mask (NaN iff outside hull) — no interior triangle was culled.
    np.testing.assert_array_equal(np.isnan(out), np.isnan(oracle))
    both = ~np.isnan(out) & ~np.isnan(oracle)
    np.testing.assert_allclose(out[both], oracle[both], atol=1e-12, rtol=0)


# --------------------------------------------------------------------------- #
# M-06 characterization — interior culling is DELIBERATE, pin it              #
# --------------------------------------------------------------------------- #
def test_interior_culling_stamps_extra_nans_inside_hull():
    """M-06 kept-behavior: over a hole, default culling adds NaNs the scipy oracle does not.

    The removed interior block lies *inside* the convex hull, so ``LinearNDInterpolator``
    fills it. ``DelaunayInterpolation`` culls the large bridging triangles and leaves the
    hole NaN — the intentional, downstream-validated behavior we are pinning here.
    """
    pts = _holed_points()
    values = _linear_field(pts)
    grid_x, grid_y = _query_mesh()

    out = DelaunayInterpolation().interpolate(values, pts, grid_x, grid_y)
    oracle = _scipy_oracle(values, pts, grid_x, grid_y)

    delaunay_nan = int(np.isnan(out).sum())
    oracle_nan = int(np.isnan(oracle).sum())

    # Culling fires: strictly more NaNs than the fill-the-hull oracle.
    assert delaunay_nan > oracle_nan, (
        f"expected interior culling to add NaNs over the hole (delaunay={delaunay_nan}, oracle={oracle_nan})"
    )
    # And every oracle-NaN (outside the hull) is also NaN in the culled output:
    # culling only ever *adds* NaNs, never removes hull-exterior NaNs.
    assert np.all(np.isnan(out)[np.isnan(oracle)])
