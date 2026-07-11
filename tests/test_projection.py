"""TEST-03 projection sensors for ``strategies/projection.py`` (Phase 5, BUG-05).

Proving tests for the five ``projection.py`` correctness findings, authored
test-first (D-12): each genuine fix gets an ``xfail`` proving test in Task 1 that
flips to a passing assert once the source is fixed (Tasks 2 & 3).

Findings covered
----------------
* **M-01 / BUG-01** — ``OrthographicProjection.project_raw`` must return the
  4-tuple ``(coords, mask, mins, maxs)`` the base ``project()`` unpacks, and must
  select columns rows-then-columns (``xyz[mask][:, cols]``) rather than the
  broadcasting fancy-index that produces a silent diagonal.
* **M-02** — ``PerspectiveProjection`` must cull behind-camera points
  (camera-space depth ``Z_c <= 0``) so a mirrored phantom cannot land in-bounds.
* **M-03** — ``PerspectiveProjection`` must honor a camera ``translation`` so the
  model is the full pinhole ``K.(R.X + t)``, not the origin-only ``t = 0`` case.
* **M-03b** (``<perspective_api_contract>``) — a 4x4 ``rotation_matrix`` raises
  ``TypeError``; a non-orthonormal 3x3 raises ``ValueError`` (fail-fast in
  ``__init__``).
* **M-04** — ``PerspectiveProjection.project`` works against the documented
  pchandler ``_TransformArray.__matmul__(pcd)`` contract.
* **M-05 / D-15** — a wrapping FoV (``left > right``, ``crosses_pi=True``) raises
  ``NotImplementedError`` in *both* ``project_raw`` and ``inverse_projection``.

The ``@ pcd`` matmul contract used by the perspective path is
``pchandler.geometry.transforms._TransformArray.__matmul__``: when the right
operand is a ``FixedLengthArray`` with ``ndim > 1`` (a ``PointCloudData``), it
dispatches to ``pcd.__rmatmul__(self)``. A 4x4 affine extrinsic yields the
camera-frame coordinates ``R.X + t`` as a fresh ``PointCloudData`` whose ``.xyz``
is the transformed ``(N, 3)`` array (verified against pchandler 2.1.0).
"""

from __future__ import annotations

import numpy as np
import pytest
from pchandler import PointCloudData
from pchandler.geometry.spherical import FoV

from pc2img.strategies.projection import (
    OrthographicProjection,
    PerspectiveProjection,
    SphericalProjection,
)
from pc2img.strategies.registry import PROJECTIONS

# Column selection per orthographic plane — mirrors OrthographicProjection.__init__.
_PLANE_COLS = {"xy": [0, 1], "yz": [1, 2], "xz": [0, 2]}


def _intrinsics(f: float = 100.0, cx: float = 50.0, cy: float = 50.0) -> np.ndarray:
    """A minimal pinhole intrinsic matrix K (focal ``f``, principal point ``(cx, cy)``)."""
    return np.array([[f, 0.0, cx], [0.0, f, cy], [0.0, 0.0, 1.0]], dtype=np.float32)


def _wrapping_fov() -> FoV:
    """A wrapping FoV (``left > right`` → ``crosses_pi=True``) built past the bounds check."""
    return FoV.construct_without_bounds_check(left=2.0, right=-2.0, top=0.5, bottom=-0.5)


# --------------------------------------------------------------------------- #
# M-01 / BUG-01 — Orthographic arity + column indexing                         #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("plane", ["xy", "yz", "xz"])
def test_orthographic_project_columns_and_arity(synthetic_pcd, plane):
    pcd = synthetic_pcd(n=16)
    w, h = 64, 32
    pts2d, mask = OrthographicProjection(plane=plane).project(pcd, (w, h))

    assert mask.shape == (pcd.nbPoints,)
    assert mask.all()

    cols = _PLANE_COLS[plane]
    xyz = np.asarray(pcd.xyz)
    coords = xyz[mask][:, cols]
    assert pts2d.shape == (coords.shape[0], 2)

    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    span = maxs - mins
    span[span == 0] = 1
    norm = (coords - mins) / span
    expected = np.vstack((norm[:, 0] * (w - 1), norm[:, 1] * (h - 1))).T
    np.testing.assert_allclose(pts2d, expected, rtol=1e-6, atol=1e-6)

    # Guard against the silent-diagonal result the broadcasting fancy-index produces:
    # the two output columns must be genuinely distinct projections, not equal.
    assert not np.allclose(pts2d[:, 0], pts2d[:, 1])


def test_orthographic_project_raw_returns_4_tuple(synthetic_pcd):
    pcd = synthetic_pcd(n=8)
    out = OrthographicProjection(plane="xy").project_raw(pcd)
    assert len(out) == 4
    coords, mask, mins, maxs = out
    assert coords.shape == (int(mask.sum()), 2)
    assert mins.shape == (2,)
    assert maxs.shape == (2,)


def test_orthographic_roi_box_masks_and_normalizes(synthetic_pcd):
    pcd = synthetic_pcd(n=32)
    # ROI covering only part of the xy plane — keeps a strict subset of points.
    roi = (0.25, 0.25, 0.75, 0.75)
    pts2d, mask = OrthographicProjection(plane="xy", roi_box=roi).project(pcd, (50, 50))
    assert mask.shape == (pcd.nbPoints,)
    assert 0 < int(mask.sum()) < pcd.nbPoints
    assert pts2d.shape == (int(mask.sum()), 2)
    # Kept points fall inside the ROI on both selected columns.
    kept = np.asarray(pcd.xyz)[mask][:, _PLANE_COLS["xy"]]
    assert (kept[:, 0] >= roi[0]).all() and (kept[:, 0] <= roi[2]).all()
    assert (kept[:, 1] >= roi[1]).all() and (kept[:, 1] <= roi[3]).all()


# --------------------------------------------------------------------------- #
# Orthographic + Spherical happy-path breadth (TEST-03)                        #
# --------------------------------------------------------------------------- #
def test_spherical_project_happy_path(synthetic_pcd):
    # field_of_view=None → resolves pcd.fov; random cloud → non-wrapping FoV.
    pcd = synthetic_pcd(n=12)
    pts2d, mask = SphericalProjection().project(pcd, (32, 16))
    assert mask.shape == (pcd.nbPoints,)
    assert mask.all()
    assert pts2d.shape == (int(mask.sum()), 2)


def test_spherical_inverse_roundtrip_shapes():
    # A non-wrapping FoV inverse-projects a range image to xyz without raising.
    fov = FoV(left=-1.0, right=1.0, top=0.5, bottom=1.5)
    proj = SphericalProjection(field_of_view=fov)
    range_img = np.ones((4, 6), dtype=np.float32)
    xyz, mask = proj.inverse_projection(range_img)
    assert mask.shape == (range_img.size,)
    assert xyz.shape[1] == 3


# --------------------------------------------------------------------------- #
# M-05 / D-15 — Spherical wrapping-FoV seam guard                              #
# --------------------------------------------------------------------------- #
def test_spherical_project_raw_rejects_wrapping_fov(synthetic_pcd):
    pcd = synthetic_pcd(n=8)
    proj = SphericalProjection(field_of_view=_wrapping_fov())
    with pytest.raises(NotImplementedError):
        proj.project_raw(pcd)


def test_spherical_inverse_rejects_wrapping_fov():
    proj = SphericalProjection(field_of_view=_wrapping_fov())
    with pytest.raises(NotImplementedError):
        proj.inverse_projection(np.zeros((4, 4), dtype=np.float32))


# --------------------------------------------------------------------------- #
# M-02 / M-03 / M-04 — Perspective cluster                                     #
# --------------------------------------------------------------------------- #
def test_perspective_masks_behind_camera():
    k = _intrinsics()
    r = np.eye(3, dtype=np.float32)
    # Front point at Xc=[0,0,5] and its behind-camera mirror at [0,0,-5]. Both
    # divide to the principal point (cx,cy); only the front point is legitimate.
    xyz = np.array([[0.0, 0.0, 5.0], [0.0, 0.0, -5.0]], dtype=np.float32)
    pcd = PointCloudData(xyz)
    pts2d, mask = PerspectiveProjection(k, r).project(pcd, (100, 100))
    assert mask.tolist() == [True, False]
    assert pts2d.shape == (1, 2)


def test_perspective_applies_translation():
    k = _intrinsics()
    r = np.eye(3, dtype=np.float32)
    t = np.array([1.0, -2.0, 10.0], dtype=np.float32)
    x = np.array([[0.5, 0.5, 5.0]], dtype=np.float32)
    pcd = PointCloudData(x)

    pts2d, mask = PerspectiveProjection(k, r, translation=t).project(pcd, (200, 200))
    assert bool(mask[0])
    # K.(R.X + t) with R = I.
    uv = k @ (x[0] + t)
    expected = uv[:2] / uv[2]
    np.testing.assert_allclose(pts2d[0], expected, rtol=1e-5, atol=1e-5)

    # The t=0 camera must land the same world point on a different pixel — proving
    # translation is actually applied, not silently dropped.
    pts0, mask0 = PerspectiveProjection(k, r).project(pcd, (200, 200))
    assert bool(mask0[0])
    assert not np.allclose(pts2d[0], pts0[0])


def test_perspective_rejects_4x4_rotation():
    with pytest.raises(TypeError):
        PerspectiveProjection(_intrinsics(), np.eye(4, dtype=np.float32))


def test_perspective_rejects_non_orthonormal_rotation():
    # A scale matrix is 3x3 but not a proper rotation (det != 1, R.R^T != I).
    bad = np.diag([2.0, 1.0, 1.0]).astype(np.float32)
    with pytest.raises(ValueError):
        PerspectiveProjection(_intrinsics(), bad)


def test_perspective_translation_survives_registry_coercion():
    # translation= must survive the (name, kwargs)-tuple → PROJECTIONS.create path,
    # not just direct __init__ (registry coercion path, <perspective_api_contract>).
    k = _intrinsics()
    r = np.eye(3, dtype=np.float32)
    t = np.array([1.0, -2.0, 10.0], dtype=np.float32)
    x = np.array([[0.5, 0.5, 5.0]], dtype=np.float32)
    pcd = PointCloudData(x)

    proj = PROJECTIONS.create("perspective", projection_matrix=k, rotation_matrix=r, translation=t)
    pts2d, mask = proj.project(pcd, (200, 200))
    assert bool(mask[0])
    uv = k @ (x[0] + t)
    np.testing.assert_allclose(pts2d[0], uv[:2] / uv[2], rtol=1e-5, atol=1e-5)


def test_perspective_project_raw_is_documented_refusal():
    # M-04: project_raw is a documented NotImplementedError (the class projects in
    # one shot via project()), not a silent/undocumented dead override.
    proj = PerspectiveProjection(_intrinsics(), np.eye(3, dtype=np.float32))
    with pytest.raises(NotImplementedError):
        proj.project_raw(PointCloudData(np.zeros((1, 3), dtype=np.float32)))


# --------------------------------------------------------------------------- #
# G2 — PerspectiveProjection K (intrinsics) validation                         #
#                                                                              #
# The rotation is validated (3x3, orthonormal, det+1) but K is stored          #
# unchecked. A wrong-shape K yields an opaque matmul crash at project() time;  #
# a non-pinhole K (bottom row != [0,0,1]) makes the perspective divisor        #
# uv_h[:,2] diverge in sign from depth, defeating the M-02 behind-camera cull. #
# Validate K at construction with the same fail-fast posture as the rotation.  #
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(reason="Phase 5 (G2): K is stored unchecked; a non-3x3 K is not refused at construction", strict=False)
def test_perspective_rejects_wrong_shape_intrinsics():
    r = np.eye(3, dtype=np.float32)
    bad_k = np.eye(2, dtype=np.float32)
    with pytest.raises((ValueError, TypeError)):
        PerspectiveProjection(bad_k, r)


@pytest.mark.xfail(reason="Phase 5 (G2): a non-pinhole K (bottom row != [0,0,1]) is not refused at construction", strict=False)
@pytest.mark.parametrize("bottom_row", [[0.0, 0.0, 2.0], [1.0, 0.0, 1.0]])
def test_perspective_rejects_non_pinhole_intrinsics(bottom_row):
    r = np.eye(3, dtype=np.float32)
    k = _intrinsics()
    k[2] = np.array(bottom_row, dtype=np.float32)
    with pytest.raises(ValueError):
        PerspectiveProjection(k, r)


def test_perspective_accepts_valid_pinhole_intrinsics():
    # A well-formed pinhole K (bottom row [0,0,1]) constructs successfully.
    proj = PerspectiveProjection(_intrinsics(), np.eye(3, dtype=np.float32))
    assert np.allclose(np.asarray(proj._intrinsics)[2], [0.0, 0.0, 1.0])


# --------------------------------------------------------------------------- #
# G4 — orthonormality/det check accepts a double-precision rotation            #
#                                                                              #
# Characterization: a legitimate float64 proper rotation must be accepted. The #
# fix moves the orthonormality/det math to float64 so the float32 round-trip   #
# can never false-reject a valid double-precision rotation at the atol=1e-6    #
# boundary. (Random scipy rotations already pass under float32 at atol=1e-6,   #
# so this pins the accept side rather than flipping a RED failure.)            #
# --------------------------------------------------------------------------- #
def _float64_proper_rotation() -> np.ndarray:
    """A proper rotation in genuine float64 (scipy if available, else axis-angle)."""
    try:
        from scipy.spatial.transform import Rotation

        return np.asarray(Rotation.random(random_state=9).as_matrix(), dtype=np.float64)
    except Exception:  # pragma: no cover - scipy is a hard dep, fallback for safety
        theta = 0.7
        axis = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        axis /= np.linalg.norm(axis)
        x, y, z = axis
        c, s = np.cos(theta), np.sin(theta)
        return np.array(
            [
                [c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)],
            ],
            dtype=np.float64,
        )


def test_perspective_accepts_float64_proper_rotation():
    r64 = _float64_proper_rotation()
    assert r64.dtype == np.float64
    # Must construct without a false ValueError from the orthonormality/det check.
    PerspectiveProjection(_intrinsics(), r64)


# --------------------------------------------------------------------------- #
# G7 — OrthographicProjection single-pass np.ix_ gather (behavior-identical)   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("plane", ["xy", "yz", "xz"])
def test_orthographic_project_raw_ix_equivalence(synthetic_pcd, plane):
    pcd = synthetic_pcd(n=24)
    coords, mask, _mins, _maxs = OrthographicProjection(plane=plane).project_raw(pcd)
    cols = _PLANE_COLS[plane]
    xyz = np.asarray(pcd.xyz)
    # The single-pass np.ix_ gather must be byte-identical to the prior two-step index.
    np.testing.assert_array_equal(coords, xyz[np.ix_(mask, cols)])
    np.testing.assert_array_equal(coords, xyz[mask][:, cols])


def test_spherical_inverse_projection_without_fov_raises_valueerror():
    # WR-01 (05-REVIEW): a default-constructed SphericalProjection (field_of_view
    # is None) cannot invert — inverse_projection has no point cloud to source a
    # FoV from — so it must fail fast with a clear ValueError, not dereference
    # None into a bare AttributeError.
    proj = SphericalProjection()
    range_img = np.ones((16, 32), dtype=np.float32)
    with pytest.raises(ValueError, match="explicit field_of_view"):
        proj.inverse_projection(range_img)
