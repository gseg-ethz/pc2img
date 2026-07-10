from collections.abc import Mapping
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple, TypeAlias, cast

import numpy as np
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from pchandler import PointCloudData
from pydantic import BeforeValidator, ConfigDict, validate_call

from pc2img.features.manager import FeatureManager
from pc2img.image_cache.disk_backed_image_data import DiskBackedImageData
from pc2img.strategies.interpolation import InterpolationName, InterpolationStrategy
from pc2img.strategies.projection import ProjectionName, ProjectionStrategy


# ImgRes: TypeAlias = tuple[int, int]
class ImgRes(NamedTuple):
    width: int
    height: int

    def __repr__(self) -> str:
        return f"ImgRes(width={self.width}, height={self.height})"

# --- Converters (single source of truth for coercion) ---

def coerce_img_res(x: ImgRes | tuple[int, int]) -> ImgRes:
    if isinstance(x, ImgRes):
        return x
    if (isinstance(x, tuple) and len(x) == 2
            and all(isinstance(v, int) for v in x)):
        return ImgRes(*x)
    raise TypeError("img_res must be ImgRes or (width:int, height:int)")

def coerce_lazy_cfg(x: LazyDiskCacheConfig | Mapping[str, Any] | None) -> LazyDiskCacheConfig:
    if x is None:
        return LazyDiskCacheConfig()
    if isinstance(x, LazyDiskCacheConfig):
        return x
    if isinstance(x, Mapping):
        return LazyDiskCacheConfig(**x)
    raise TypeError("lazy_disk_cache_config must be a mapping or LazyDiskCacheConfig")

# --- Typing trick: show loose types to type-checkers, use converters at runtime ---

if TYPE_CHECKING:
    ProjectionStrategyLike: TypeAlias = (
        ProjectionStrategy
        | ProjectionName
        | tuple[ProjectionName, Mapping[str, Any]]
    )
    InterpolationStrategyLike: TypeAlias = (
        InterpolationStrategy
        | InterpolationName
        | tuple[InterpolationName, Mapping[str, Any]]
    )
    ImgResLike = ImgRes | tuple[int, int]
    LazyDiskCacheConfigLike = LazyDiskCacheConfig | Mapping[str, Any] | None
else:
    ProjectionStrategyLike = ProjectionStrategy
    InterpolationStrategyLike = InterpolationStrategy
    ImgResLike = Annotated[ImgRes, BeforeValidator(coerce_img_res)]
    LazyDiskCacheConfigLike = Annotated[LazyDiskCacheConfig, BeforeValidator(coerce_lazy_cfg)]

class PointCloudImageGenerator:

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
        self,
        pcd: PointCloudData,
        img_res: ImgResLike,
        proj: ProjectionStrategyLike,
        interp: InterpolationStrategyLike,
        lazy_disk_cache_config: LazyDiskCacheConfigLike = None,  # default handled by coerce_lazy_cfg
    ) -> None:
        self._pcd = pcd
        self._img_res = cast(ImgRes, img_res)
        self._proj = cast(ProjectionStrategy, proj)
        self._interp = cast(InterpolationStrategy, interp)
        self.feature_mgr = FeatureManager(
            self._pcd,
            lazy_disk_cache_config=cast(LazyDiskCacheConfig, lazy_disk_cache_config)
        )
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
