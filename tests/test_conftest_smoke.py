"""Collection smoke: every advertised conftest fixture resolves and is usable.

Pure, deterministic, and fixture-only — this proves the shared fixture factory
is wired before any other test depends on it. It does not exercise the
production pipeline.
"""

from __future__ import annotations

import numpy as np
from pchandler import PointCloudData


def test_synthetic_pcd_builds_requested_point_count(synthetic_pcd) -> None:
    pcd = synthetic_pcd(n=8)
    assert isinstance(pcd, PointCloudData)
    assert pcd.nbPoints == 8
    assert pcd.xyz.shape == (8, 3)


def test_synthetic_pcd_is_deterministic(synthetic_pcd) -> None:
    a = synthetic_pcd(n=5)
    b = synthetic_pcd(n=5)
    np.testing.assert_array_equal(a.xyz, b.xyz)


def test_synthetic_pcd_attaches_scalar_fields(synthetic_pcd) -> None:
    intensity = np.arange(4, dtype=np.float32)
    pcd = synthetic_pcd(n=4, with_scalar_fields={"intensity": intensity})
    assert pcd.nbPoints == 4
    assert "intensity" in pcd.scalar_fields
    np.testing.assert_array_equal(pcd.scalar_fields["intensity"], intensity)


def test_synthetic_pcd_synthesizes_none_scalar_fields(synthetic_pcd) -> None:
    pcd = synthetic_pcd(n=6, with_scalar_fields={"range": None})
    assert pcd.scalar_fields["range"].shape == (6,)


def test_fetch_stub_returns_supplied_array_by_name(fetch_stub) -> None:
    grid = np.zeros((4, 4), dtype=np.float32)
    fetch = fetch_stub({"range": grid})
    assert fetch("range") is grid


def test_fake_projection_returns_four_tuple(fake_projection, synthetic_pcd) -> None:
    pcd = synthetic_pcd(n=7)
    result = fake_projection.project_raw(pcd)
    assert isinstance(result, tuple) and len(result) == 4
    coords, mask, mins, maxs = result
    assert coords.shape == (7, 2)
    assert mask.shape == (7,)
    assert mins.shape == (2,)
    assert maxs.shape == (2,)
    assert fake_projection.inverse_projection() is None
