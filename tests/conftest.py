"""Shared synthetic test-fixture factory for the pc2img test suite.

Deterministic, fast, and free of committed binary fixtures: every point cloud is
built at runtime from a seeded ``numpy`` generator, so the tests are reproducible
without shipping ``.ply`` / ``.e57`` blobs. ``pchandler`` 2.1.0 constructs a
``PointCloudData`` directly from a raw ``Nx3`` float array and attaches named
scalar fields via the ``scalar_fields=`` kwarg, so no loader round-trip is needed.

Three consumers are served here:

* ``synthetic_pcd`` — a *factory* fixture that returns a callable building a real
  ``PointCloudData``. Only the projection and orchestration tests need a
  real PCD; the other tests are pure-array/stub and use the lighter helpers below.
* ``fetch_stub`` — a factory returning a dict-backed ``Callable[[str], NDArray]``
  for the ``compute(_, fetch)`` derivative/DSL call sites (which ignore the pcd).
* ``fake_projection`` — a duck-typed ``ProjectionStrategy`` returning the full
  ``project_raw`` 4-tuple, for tests where constructing a full PCD is heavy.

The ``DummyProjection`` / ``DummyInterpolation`` duck stubs and ``make_point_cloud``
helper are lifted here from ``test_point_cloud_image_generator.py`` so the old and
new tests can share one source.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from pchandler import PointCloudData

from pc2img.strategies.interpolation import InterpolationStrategy
from pc2img.strategies.projection import ProjectionStrategy

# A fixed seed keeps every synthesized cloud byte-identical across runs.
_DEFAULT_SEED = 0


# --------------------------------------------------------------------------- #
# Duck-typed strategy stubs (lifted from test_point_cloud_image_generator.py)  #
# --------------------------------------------------------------------------- #
class DummyProjection(ProjectionStrategy):
    """A projection that keeps no points — the minimal valid ``project_raw``.

    Returns the full 4-tuple contract ``(coords (M, 2), mask (N,), mins (2,),
    maxs (2,))`` with an empty coordinate array and an all-False mask, so it can
    stand in wherever a projection is needed but its output is irrelevant.
    """

    def project_raw(self, pcd: PointCloudData):
        return (
            np.empty((0, 2), dtype=np.float32),
            np.zeros((pcd.nbPoints,), dtype=bool),
            np.zeros(2, dtype=np.float32),
            np.ones(2, dtype=np.float32),
        )

    def inverse_projection(self):
        return None


class DummyInterpolation(InterpolationStrategy):
    """An interpolation that returns a zero grid regardless of inputs."""

    def interpolate(self, values, points2d, grid_x, grid_y):
        return np.zeros_like(grid_x, dtype=np.float32)


class FakeProjection(ProjectionStrategy):
    """A duck-typed projection with a *usable* ``project_raw`` output.

    Unlike :class:`DummyProjection` (which masks everything out), this keeps all
    points and derives 2-D coordinates from the first two columns of ``pcd.xyz``.
    Useful where a projection test needs a well-formed 4-tuple over real points
    but constructing a full projection strategy would be heavy.
    """

    def project_raw(self, pcd: PointCloudData):
        xyz = np.asarray(pcd.xyz, dtype=np.float32)
        coords = xyz[:, :2].copy()
        mask = np.ones((pcd.nbPoints,), dtype=bool)
        if coords.size:
            mins = coords.min(axis=0).astype(np.float32)
            maxs = coords.max(axis=0).astype(np.float32)
        else:
            mins = np.zeros(2, dtype=np.float32)
            maxs = np.ones(2, dtype=np.float32)
        return coords, mask, mins, maxs

    def inverse_projection(self):
        return None


def make_point_cloud() -> PointCloudData:
    """Return an empty (0-point) ``PointCloudData`` — the lightest valid PCD."""
    return PointCloudData(np.empty((0, 3), dtype=np.float32))


def make_synthetic_pcd(
    n: int = 16,
    *,
    with_scalar_fields: Mapping[str, NDArray] | None = None,
    seed: int = _DEFAULT_SEED,
) -> PointCloudData:
    """Build a deterministic synthetic ``PointCloudData`` with ``n`` points.

    Parameters
    ----------
    n:
        Number of points. ``xyz`` is drawn from a seeded generator so the cloud
        is reproducible run-to-run.
    with_scalar_fields:
        Optional mapping of field-name -> per-point array. Length-``n`` arrays
        are attached verbatim; a mapping to ``None`` requests seeded synthetic
        fields (one deterministic ``float32`` array per name).
    seed:
        Seed for the ``numpy`` generator backing both ``xyz`` and any synthesized
        scalar fields.

    Notes
    -----
    Only the ``xyz`` positions and explicitly supplied scalar fields are set;
    derived quantities (``.spher``, ``.fov``) are left to ``pchandler`` to compute
    so this factory never fabricates values the real PCD owns.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    rng = np.random.default_rng(seed)
    xyz = rng.random((n, 3), dtype=np.float32)

    scalar_fields: dict[str, NDArray] | None = None
    if with_scalar_fields is not None:
        scalar_fields = {}
        for name, values in with_scalar_fields.items():
            if values is None:
                values = rng.random((n,), dtype=np.float32)
            arr = np.asarray(values)
            if arr.shape[0] != n:
                raise ValueError(f"scalar field {name!r} has length {arr.shape[0]}, expected {n}")
            scalar_fields[name] = arr

    if scalar_fields is None:
        return PointCloudData(xyz)
    return PointCloudData(xyz, scalar_fields=scalar_fields)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _isolate_tempdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect ``tempfile``'s default directory under the test's ``tmp_path``.

    Several modules call ``tempfile.mkdtemp`` / ``TemporaryDirectory`` without a
    ``dir=`` (the default cache location of a store, for one), which leaked
    about eighteen ``tmp*`` entries per full run into the system temp
    directory. Pointing the module-level default at ``tmp_path / "_tmp"`` keeps
    them under pytest's own tree, which pytest prunes. A subdirectory rather
    than ``tmp_path`` itself, so a test that snapshots ``tmp_path`` can exclude
    it. A test that sets ``tempfile.tempdir`` itself runs after this fixture and
    wins.
    """
    tmp = tmp_path / "_tmp"
    tmp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp))


@pytest.fixture
def synthetic_pcd() -> Callable[..., PointCloudData]:
    """Factory fixture: call it to build a deterministic ``PointCloudData``.

    Example
    -------
    >>> def test_x(synthetic_pcd):
    ...     pcd = synthetic_pcd(n=8, with_scalar_fields={"intensity": None})
    ...     assert pcd.nbPoints == 8
    """
    return make_synthetic_pcd


@pytest.fixture
def fetch_stub() -> Callable[[Mapping[str, NDArray]], Callable[[str], NDArray]]:
    """Factory fixture: turn a name->array mapping into a ``fetch`` callable.

    The returned callable mirrors the ``fetch`` argument passed to derivative /
    DSL ``compute(_, fetch)`` call sites, which resolve dependency rasters by
    name and ignore the ``pcd`` positional.

    Example
    -------
    >>> def test_x(fetch_stub):
    ...     fetch = fetch_stub({"range": np.zeros((4, 4))})
    ...     assert fetch("range").shape == (4, 4)
    """

    def _make_fetch(arrays: Mapping[str, NDArray]) -> Callable[[str], NDArray]:
        table = dict(arrays)

        def fetch(name: str) -> NDArray:
            try:
                return table[name]
            except KeyError as e:
                raise KeyError(f"fetch_stub has no array for {name!r}; available: {sorted(table)}") from e

        return fetch

    return _make_fetch


@pytest.fixture
def fake_projection() -> FakeProjection:
    """A duck-typed projection returning a well-formed ``project_raw`` 4-tuple."""
    return FakeProjection()
