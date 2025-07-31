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


class PointCloudTile(NamedTuple):
    tile_id: str
    tile_pcd: PointCloudData
    tile_kwargs: Mapping[str, Any]

# PointCloudTile = namedtuple("PointCloudTile", ["tile_id", "tile_pcd", "tile_kwargs"])

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
            pcd_tiles: Sequence[PointCloudTile] | Sequence[tuple[str, PointCloudData, Mapping[str, Any]]],
            img_res: tuple[int, int],
            proj_cls: ProjClassT,
            interp_cls: InterpClassT,
            *,
            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,

            lazy_disk_cache_config: Mapping[str,Any] | LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None: ...


    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile],
            img_res: tuple[int, int],
            proj_cls: ProjectionStrategyClass,
            interp_cls: InterpolationStrategyClass,
            *,

            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,
            lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ):
        self.pcd_tiles = pcd_tiles
        self._img_res = img_res
        self.proj_cls = proj_cls
        self.interp_cls = interp_cls
        self._proj_kwargs = proj_kwargs or {}
        self._interp_kwargs = interp_kwargs or {}
        self._lazy_disk_cache_config = lazy_disk_cache_config
        self.image_generators: dict[str, PointCloudImageGenerator] = {}


    def generate(
            self,
            features: list[str],
            n_jobs: int = 1,
    ) -> dict:

        tasks = self.pcd_tiles

        with parallel_config(backend="loky", n_jobs=n_jobs, verbose=50, prefer="processes"):
            results = Parallel()(
                delayed(self._process_tile)(
                    task.tile_id, task.tile_pcd, task.tile_kwargs,
                    features
                )
                for task in tasks
            )

        result_dict: dict[ImageKey, DiskBackedImageData] = {}
        for tile_result in results:
            self.image_generators[tile_result[0]] = tile_result[1]
            tile_dict = {ImageKey(tile_result[0], feature_id): feature_data for feature_id, feature_data in tile_result[2].items()}
            result_dict.update(tile_dict)

        return result_dict

    def _process_tile(
            self,
            tile_id: str,
            tile_pcd: PointCloudData,
            tile_kwargs: Mapping[str, Any],
            features: list[str],
    ) -> tuple[str, PointCloudImageGenerator, dict[str, DiskBackedImageData]]:
        image_gen = self.image_generators[tile_id] if tile_id in self.image_generators else PointCloudImageGenerator(
            pcd=tile_pcd,
            proj=self.proj_cls(**tile_kwargs, **self._proj_kwargs),
            interp=self.interp_cls(**self._interp_kwargs),
            lazy_disk_cache_config=self._lazy_disk_cache_config.extend_cache_path(tile_id),
            img_res=self._img_res,
        )
        # image_gen = self.image_generators[tile_id]
        tile_images = image_gen.generate(features)
        return tile_id, image_gen, tile_images
