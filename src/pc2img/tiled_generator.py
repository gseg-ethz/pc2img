from collections import namedtuple
from pathlib import Path
from typing import Optional, NamedTuple, Sequence, overload, TypeVar, Type, Mapping, Any
from joblib import Parallel, delayed, parallel_config
import logging
from functools import wraps

from pydantic import validate_call, ConfigDict

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pchandler.geometry import PointCloudData
from pchandler.geometry.fov import FoV

from pc2img import PointCloudImageGenerator
from pc2img.image_cache import DiskBackedImageData
from pc2img.strategies import INTERPOLATIONS, InterpolationStrategy, InterpolationName, InterpolationStrategyClass
from pc2img.strategies import PROJECTIONS, ProjectionStrategy, ProjectionName, ProjectionStrategyClass


#
# class PointCloudTile(NamedTuple):
#     identifier: str
#     pcd: PointCloudData
#     fov: FoV
#
PointCloudTile = namedtuple("PointCloudTile", ["tile_id", "pcd", "fov"])

ImageKey = namedtuple("ImageKey", ["tile_id", "feature"])

ProjClassT = TypeVar(
    "ProjClassT",
    ProjectionName,
    Type[ProjectionStrategy],
)
InterpClassT = TypeVar(
    "InterpClassT",
    InterpolationName,
    Type[InterpolationStrategy],
)

class TiledPointCloudImageGenerator:
    @overload
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile],
            proj_cls: ProjClassT,
            interp_cls: InterpClassT,
            *,
            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,

            lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None: ...


    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile],
            proj_cls: ProjectionStrategyClass,
            interp_cls: InterpolationStrategyClass,
            *,

            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,
            lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ):
        self.pcd_tiles = pcd_tiles
        self.proj_cls = proj_cls
        self.interp_cls = interp_cls
        self._proj_kwargs = proj_kwargs or {}
        self._interp_kwargs = interp_kwargs or {}
        self._lazy_disk_cache_config = lazy_disk_cache_config


    def generate(
            self,
            features: list[str],
            image_res: tuple[int,int],
            n_jobs: int = 1,
    ):

        tasks = self.pcd_tiles

        with parallel_config(backend="loky", n_jobs=n_jobs, verbose=50, prefer="processes"):
            results = Parallel()(
                delayed(self._process_tile)(
                    task.tile_id, task.pcd, task.fov,
                    features, image_res
                )
                for task in tasks
            )

        result_dict: dict[ImageKey, DiskBackedImageData] = {}
        for tile_dict in results:
            result_dict.update(tile_dict)

        return result_dict

    def _process_tile(
            self,
            tile_id: str,
            tile: PointCloudData,
            fov: FoV,
            features: list[str],
            image_res: tuple[int,int],
    ):
        image_gen = PointCloudImageGenerator(
            pcd=tile,
            proj=self.proj_cls(field_of_view=fov, **self._proj_kwargs),
            interp=self.interp_cls(**self._interp_kwargs),
            lazy_disk_cache_config=self._lazy_disk_cache_config,
        )
        tile_images = image_gen.generate(features, image_res)
        return {
            ImageKey(tile_id, feature): image
            for feature, image in tile_images.items()
        }

