from collections import namedtuple
from pathlib import Path
from typing import Optional, NamedTuple, Sequence, overload, TypeVar, Type
from joblib import Parallel, delayed, parallel_config
import logging
from functools import wraps

from pydantic import validate_call, ConfigDict

from pchandler.geometry import PointCloudData
from pchandler.geometry.fov import FoV

from pc2img import PointCloudImageGenerator
from pc2img.image_cache import DiskBackedImageData
from pc2img.strategies import INTERPOLATIONS, InterpolationStrategy, InterpolationName, InterpolationStrategyClass
from pc2img.strategies import PROJECTIONS, ProjectionStrategy, ProjectionName, ProjectionStrategyClass


def silence_logs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("pchandler.geometry.coordinates")            # root logger
        previous = logger.level
        logger.setLevel(logging.ERROR)          # silence below ERROR
        try:
            return func(*args, **kwargs)
        finally:
            logger.setLevel(previous)          # restore original level
    return wrapper
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
            enable_caching: bool = False,
            cache_dir: Optional[Path] = None,
            automatic_offloading: bool = False,
            purge_disk_on_gc: bool = True,
    ) -> None: ...


    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
            self,
            pcd_tiles: Sequence[PointCloudTile],
            proj_cls: ProjectionStrategyClass,
            interp_cls: InterpolationStrategyClass,
            enable_caching: bool = False,
            cache_dir: Optional[Path] = None,
            automatic_offloading: bool = False,
            purge_disk_on_gc: bool = True,
    ):
        self.pcd_tiles = pcd_tiles
        self.proj_cls = proj_cls
        self.interp_cls = interp_cls
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir
        self.automatic_offloading = automatic_offloading
        self.purge_disk_on_gc = purge_disk_on_gc


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

    @silence_logs
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
            proj=self.proj_cls(field_of_view=fov),
            interp=self.interp_cls(),
            enable_caching=self.enable_caching,
            cache_dir=self.cache_dir,
            automatic_offloading=self.automatic_offloading,
            purge_disk_on_gc=self.purge_disk_on_gc,
        )
        tile_images = image_gen.generate(features, image_res)
        return {
            ImageKey(tile_id, feature): image
            for feature, image in tile_images.items()
        }

