from pathlib import Path
from typing import Optional, TypeVar, Any, overload, Mapping, NamedTuple, TypeAlias

from pydantic import ConfigDict, validate_call
import numpy as np

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pchandler import PointCloudData

from pc2img.strategies.projection import ProjectionStrategy, ProjectionName
from pc2img.strategies.interpolation import InterpolationStrategy, InterpolationName
from pc2img.features.manager import FeatureManager
from pc2img.image_cache.disk_backed_image_data import DiskBackedImageData

ProjArg: TypeAlias = (
    ProjectionStrategy
    | ProjectionName
    | tuple[ProjectionName, Mapping[str, Any]]
)
InterpArg: TypeAlias = (
    InterpolationStrategy
    | InterpolationName
    | tuple[InterpolationName, Mapping[str, Any]]
)

# ImgRes: TypeAlias = tuple[int, int]
class ImgRes(NamedTuple):
    width: int
    height: int

    def __repr__(self) -> str:
        return f"ImgRes(width={self.width}, height={self.height})"


class PointCloudImageGenerator:

    @overload
    def __init__(
        self,
        pcd: PointCloudData,
        img_res: ImgRes,
        proj: ProjArg,
        interp: InterpArg,
        lazy_disk_cache_config: Mapping[str,Any] | LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None: ...

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
        self,
        pcd: PointCloudData,
        img_res: ImgRes,
        proj: ProjectionStrategy,
        interp: InterpolationStrategy,
        lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None:
        self._pcd = pcd
        self._img_res = img_res
        self._proj = proj
        self._interp = interp
        self.feature_mgr = FeatureManager(self._pcd, lazy_disk_cache_config=lazy_disk_cache_config)
        self.projection_results = {}


    def generate(
            self,
            features: list[str],
    ) -> dict[str,DiskBackedImageData]:

        self.feature_mgr.request(features)
        base_features_1D = self.feature_mgr.get_base_features()

        if base_features_1D:
            resolution = self._img_res
            if not self.projection_results:
                self.projection_results["pts2d"], self.projection_results["mask"] = self._proj.project(self._pcd, resolution)

            pts2d = self.projection_results["pts2d"]
            mask = self.projection_results["mask"]

            w, h = resolution
            gx = np.arange(w)
            gy = np.arange(h)
            grid_x, grid_y = np.meshgrid(gx, gy)

            for bf_name, bf_1D in base_features_1D.items():
                bf_raster = self._interp.interpolate(bf_1D[mask], pts2d, grid_x, grid_y)
                self.feature_mgr.submit(bf_name, bf_raster)

        results = self.feature_mgr.get_targets()
        return results

    @property
    def projection(self) -> ProjectionStrategy:
        return self._proj