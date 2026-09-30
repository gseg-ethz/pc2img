from __future__ import annotations

import numpy as np
from pchandler import PointCloudData

from pc2img.core import PointCloudImageGenerator
from pc2img.strategies.interpolation import InterpolationStrategy
from pc2img.strategies.projection import ProjectionStrategy


class DummyProjection(ProjectionStrategy):
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
    def interpolate(self, values, points2d, grid_x, grid_y):
        return np.zeros_like(grid_x, dtype=np.float32)


def make_point_cloud() -> PointCloudData:
    return PointCloudData(np.empty((0, 3), dtype=np.float32))


def test_constructor_normalizes_omitted_lazy_disk_cache_config() -> None:
    generator = PointCloudImageGenerator(
        make_point_cloud(),
        (1, 1),
        DummyProjection(),
        DummyInterpolation(),
    )

    assert generator.feature_mgr.cache_store.cache_dir.exists()
    assert generator.feature_mgr.available_features() == []


def test_constructor_normalizes_explicit_none_lazy_disk_cache_config() -> None:
    generator = PointCloudImageGenerator(
        make_point_cloud(),
        (1, 1),
        DummyProjection(),
        DummyInterpolation(),
        lazy_disk_cache_config=None,
    )

    assert generator.feature_mgr.cache_store.cache_dir.exists()
    assert generator.feature_mgr.available_features() == []
