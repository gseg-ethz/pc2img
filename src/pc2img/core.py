from pathlib import Path
from typing import Optional, TypeVar, Any, overload, Mapping

from pydantic import ConfigDict, validate_call
import numpy as np

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pchandler.geometry import PointCloudData

from pc2img.strategies.projection import ProjectionStrategy, ProjectionName
from pc2img.strategies.interpolation import InterpolationStrategy, InterpolationName
from pc2img.features.manager import FeatureManager
from pc2img.image_cache.disk_backed_image_data import DiskBackedImageData

ProjArg = (
    ProjectionStrategy
    | ProjectionName
    | tuple[ProjectionName, Mapping[str, Any]]
)
InterpArg = (
    InterpolationStrategy
    | InterpolationName
    | tuple[InterpolationName, Mapping[str, Any]]
)

class PointCloudImageGenerator:

    @overload
    def __init__(
        self,
        pcd: PointCloudData,
        proj: ProjArg,
        interp: InterpArg,
        lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None: ...

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
        self,
        pcd: PointCloudData,
        proj: ProjectionStrategy,
        interp: InterpolationStrategy,
        lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None:
        self._pcd = pcd
        self._proj = proj
        self._interp = interp
        self.feature_mgr = FeatureManager(self._pcd, lazy_disk_cache_config=lazy_disk_cache_config)


    def generate(
            self,
            features: list[str],
            resolution: tuple[int,int],
    ) -> dict[str,DiskBackedImageData]:
        pts2d, mask = self._proj.project(self._pcd, resolution)

        w, h = resolution
        gx = np.arange(w)
        gy = np.arange(h)
        grid_x, grid_y = np.meshgrid(gx, gy)

        self.feature_mgr.request(features)
        base_features_1D = self.feature_mgr.get_base_features()
        for bf_name, bf_1D in base_features_1D.items():
            bf_raster = self._interp.interpolate(bf_1D[mask], pts2d, grid_x, grid_y)
            self.feature_mgr.submit(bf_name, bf_raster)
        results = self.feature_mgr.get_targets()
        return results