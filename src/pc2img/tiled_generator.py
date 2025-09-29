from collections import namedtuple
from pathlib import Path
from typing import Optional, NamedTuple, Sequence, overload, TypeVar, Type, Mapping, Any, TypeAlias, cast, Self
from joblib import Parallel, delayed, parallel_config
import logging
from functools import wraps
import copy
from dataclasses import dataclass, field, replace, fields

from pydantic import validate_call, ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pchandler import PointCloudData

from pc2img import PointCloudImageGenerator
from pc2img.core import ImgRes
from pc2img.image_cache import DiskBackedImageData
from pc2img.strategies import INTERPOLATIONS, InterpolationStrategy, InterpolationName, InterpolationStrategyClass
from pc2img.strategies import PROJECTIONS, ProjectionStrategy, ProjectionName, ProjectionStrategyClass

logger = logging.getLogger(__name__)

class PointCloudTile(NamedTuple):
    tile_id: str
    tile_pcd: PointCloudData
    tile_kwargs: Mapping[str, Any]

# PointCloudTile = namedtuple("PointCloudTile", ["tile_id", "tile_pcd", "tile_kwargs"])

ImageKey = namedtuple("ImageKey", ["tile_id", "feature"])

# ProjClassT = TypeAlias(
#     "ProjClassT",
#     ProjectionName,
#     Type[ProjectionStrategy],
# )
# InterpClassT = TypeAlias(
#     "InterpClassT",
#     InterpolationName,
#     Type[InterpolationStrategy],
# )
ProjectionLike: TypeAlias = ProjectionName | type[ProjectionStrategy]
InterpolationLike: TypeAlias = InterpolationName | type[InterpolationStrategy]

@pydantic_dataclass(frozen=True)
class TIGSettings:
    img_res: ImgRes
    proj_cls: ProjectionLike
    interp_cls: InterpolationLike

    proj_kwargs: dict[str, Any] = field(default_factory=dict)
    interp_kwargs: dict[str, Any] = field(default_factory=dict)
    lazy_disk_cache_config: Optional[LazyDiskCacheConfig] = None

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def extend_cache_paths(self, new_folder: str) -> Self:
        updates = {}
        if "lazy_disk_cache_config" in self.interp_kwargs and isinstance(self.interp_kwargs["lazy_disk_cache_config"], LazyDiskCacheConfig):
            updates["interp_kwargs"] = dict(self.interp_kwargs).update({
                "lazy_disk_cache_config": self.interp_kwargs["lazy_disk_cache_config"].extend_cache_path(new_folder)
                })
        if self.lazy_disk_cache_config is not None:
            updates["lazy_disk_cache_config"] = self.lazy_disk_cache_config.extend_cache_path(new_folder)

        return replace(self, **updates)
    
    def as_kwargs(self) -> dict[str, Any]:
        """Return a plain dict of fields, excluding those whose value is None."""
        out: dict[str, Any] = {}
        for f in fields(self):
            val = getattr(self, f.name)
            if val is None:
                continue
            out[f.name] = val
        return out



class TiledPointCloudImageGenerator:
    @overload
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile] | Sequence[tuple[str, PointCloudData, Mapping[str, Any]]],
            img_res: tuple[int, int],
            proj_cls: ProjectionLike,
            interp_cls: InterpolationLike,
            *,
            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,

            lazy_disk_cache_config: Mapping[str,Any] | LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None: ...


    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile],
            img_res: ImgRes,
            proj_cls: ProjectionStrategyClass,
            interp_cls: InterpolationStrategyClass,
            *,

            proj_kwargs: Optional[Mapping[str, Any]] = None,
            interp_kwargs: Optional[Mapping[str, Any]] = None,
            lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ):
        self.pcd_tiles = pcd_tiles
        self._img_res = img_res
        self.proj_cls: type[ProjectionStrategy] = cast(type[ProjectionStrategy], proj_cls)
        self.interp_cls: type[InterpolationStrategy] = cast(type[InterpolationStrategy], interp_cls)
        self._proj_kwargs = proj_kwargs or {}
        self._interp_kwargs = interp_kwargs or {}
        self._lazy_disk_cache_config = lazy_disk_cache_config
        self.image_generators: dict[str, PointCloudImageGenerator] = {}


    def generate(
            self,
            features: list[str],
            n_jobs: int = -1,
    ) -> dict[ImageKey, DiskBackedImageData]:

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
        
        interp_kwargs: dict[str, Any] = dict(self._interp_kwargs)
        proj_kwargs: dict[str, Any] = dict(self._proj_kwargs)

        if "lazy_disk_cache_config" in interp_kwargs:
            interp_kwargs["lazy_disk_cache_config"] = interp_kwargs["lazy_disk_cache_config"].extend_cache_path(tile_id)

        image_gen = self.image_generators[tile_id] if tile_id in self.image_generators else PointCloudImageGenerator(
            pcd=tile_pcd,
            proj=self.proj_cls(**tile_kwargs, **proj_kwargs),
            interp=self.interp_cls(**interp_kwargs),
            lazy_disk_cache_config=self._lazy_disk_cache_config.extend_cache_path(tile_id),
            img_res=self._img_res,
        )
        # image_gen = self.image_generators[tile_id]
        tile_images = image_gen.generate(features)
        return tile_id, image_gen, tile_images
