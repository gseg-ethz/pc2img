import logging
from collections import namedtuple
from collections.abc import Mapping, Sequence
from dataclasses import field, fields, replace
from typing import (
    Any,
    NamedTuple,
    Self,
    cast,
    overload,
)

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from joblib import Parallel, delayed, parallel_config
from pchandler import PointCloudData
from pydantic import ConfigDict, validate_call
from pydantic.dataclasses import dataclass as pydantic_dataclass

from pc2img.core import ImgRes, PointCloudImageGenerator
from pc2img.image_cache import DiskBackedImageData
from pc2img.strategies import (
    InterpolationName,
    InterpolationStrategy,
    InterpolationStrategyClass,
    ProjectionName,
    ProjectionStrategy,
    ProjectionStrategyClass,
)

logger = logging.getLogger(__name__)


class PointCloudTile(NamedTuple):
    """One tile of a tiled run: its id, its point cloud and its per-tile kwargs.

    ``tile_id`` becomes a cache sub-directory name, so it must be a legal store
    key as defined upstream by GSEGUtils (``is_valid_store_key``). An illegal id
    (a path separator, a backslash, a colon, a trailing dot or space, an empty,
    ``.`` or ``..`` name, or a Windows device name) raises ``StoreKeyError`` (a
    ``ValueError``) from ``extend_cache_path``, unwrapped, also when raised
    inside a worker process. Ids must be unique within a run; a repeated id raises
    ``ValueError`` from the ``TiledPointCloudImageGenerator`` constructor.
    """

    tile_id: str
    tile_pcd: PointCloudData
    tile_kwargs: Mapping[str, Any]


ImageKey = namedtuple("ImageKey", ["tile_id", "feature"])

#     "ProjClassT",
#     ProjectionName,
#     "InterpClassT",
#     InterpolationName,
type ProjectionLike = ProjectionName | type[ProjectionStrategy]
type InterpolationLike = InterpolationName | type[InterpolationStrategy]


@pydantic_dataclass(frozen=True)
class TIGSettings:
    img_res: ImgRes
    proj_cls: ProjectionLike
    interp_cls: InterpolationLike

    proj_kwargs: dict[str, Any] = field(default_factory=dict)
    interp_kwargs: dict[str, Any] = field(default_factory=dict)
    lazy_disk_cache_config: LazyDiskCacheConfig | None = None

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def extend_cache_paths(self, new_folder: str) -> Self:
        """Return a copy whose cache paths are extended by the sub-directory ``new_folder``.

        ``new_folder`` is validated upstream by GSEGUtils (``is_valid_store_key``):
        an illegal segment raises ``StoreKeyError`` (a ``ValueError``) unwrapped.
        """
        updates = {}
        if "lazy_disk_cache_config" in self.interp_kwargs and isinstance(
            self.interp_kwargs["lazy_disk_cache_config"], LazyDiskCacheConfig
        ):
            # Build the extended dict first, then assign it. Assigning
            # ``dict.update()`` (which returns None) would null every per-tile
            # interpolation kwarg — the opposite of the intended path extension.
            extended_interp_kwargs = dict(self.interp_kwargs)
            extended_interp_kwargs["lazy_disk_cache_config"] = self.interp_kwargs[
                "lazy_disk_cache_config"
            ].extend_cache_path(new_folder)
            updates["interp_kwargs"] = extended_interp_kwargs
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
    """Run the projection, interpolation and feature pipeline over many tiles in parallel.

    Every ``generate()`` call makes one ``_process_tile`` call per tile - joblib may batch
    several calls into one worker task, but each tile's generator is still unpickled once per
    call. A call carries only that tile's generator (built in the worker on the first call,
    reused from ``image_generators`` afterwards) and picklable inputs, never the tiled generator
    itself, so repeated ``generate()`` calls on one instance are supported whenever the work
    runs in a worker pool (any ``n_jobs`` other than 1, including the default ``-1``). Tile ids
    are unique (a repeated id raises ``ValueError`` at construction). GSEGUtils 0.6.0
    rebuilds each ``.dat`` memmap through one fixed ``<key>.dat.tmp`` name, which still races
    when one store is unpickled by several processes at once
    (https://github.com/gseg-ethz/GSEGUtils/issues/82); this dispatch no longer does that.

    **Disk persistence after a pooled run.** Entries returned by a pooled ``generate()`` (any
    ``n_jobs`` other than 1, including the default ``-1``) and the entries of the stores kept in
    ``image_generators`` have purge-on-garbage-collection disabled, so releasing one call's
    results never deletes a ``.dat`` memmap that a later call's results read. The price: released
    results and dropped generators no longer delete their cache files at all. Every
    ``<tile_id>/<key>.dat`` (and the codec pair the pickling writes) persists until ``purge()`` is
    called or the cache directory is removed. That includes the default temporary directory a
    store creates with ``tempfile.mkdtemp`` when no ``cache_path`` is configured, which nothing
    cleans up afterwards. Routes: configure ``cache_path`` and remove that directory when the run
    is done; or keep the stores owned by this process by using ``n_jobs=1`` for every call and
    purge from it. ``n_jobs=1`` keeps the single-object behaviour.

    With ``n_jobs >= 2`` every tile's ``DiskBackedImageStore`` is constructed inside a worker
    and records that worker's process id as its owner. GSEGUtils refuses ``purge`` from any other
    process with ``StorePurgeRefusedError`` (a ``RuntimeError``), and ``add_image_to_store`` over
    an existing key purges first, so after ``generate()`` returns the parent process can neither
    purge nor overwrite those stores, and a later ``generate()`` that has to overwrite a key in a
    different worker can fail the same way. Ways around it:

    * run with ``n_jobs=1`` when the instance will be purged from or overwritten;
    * build a fresh ``TiledPointCloudImageGenerator`` for each ``generate()`` call;
    * drop the tile's generator and remove its cache sub-directory ``<cache_path>/<tile_id>``
      (for example with ``shutil.rmtree``).
    """

    @overload
    def __init__(
        self,
        pcd_tiles: Sequence[PointCloudTile] | Sequence[tuple[str, PointCloudData, Mapping[str, Any]]],
        img_res: tuple[int, int],
        proj_cls: ProjectionLike,
        interp_cls: InterpolationLike,
        *,
        proj_kwargs: Mapping[str, Any] | None = None,
        interp_kwargs: Mapping[str, Any] | None = None,
        lazy_disk_cache_config: Mapping[str, Any] | LazyDiskCacheConfig | None = None,
    ) -> None: ...

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
    def __init__(
        self,
        pcd_tiles: Sequence[PointCloudTile],
        img_res: ImgRes,
        proj_cls: ProjectionStrategyClass,
        interp_cls: InterpolationStrategyClass,
        *,
        proj_kwargs: Mapping[str, Any] | None = None,
        interp_kwargs: Mapping[str, Any] | None = None,
        lazy_disk_cache_config: LazyDiskCacheConfig | None = None,
    ):
        tile_ids = [tile.tile_id for tile in pcd_tiles]
        if len(tile_ids) != len(set(tile_ids)):
            duplicated = sorted({tile_id for tile_id in tile_ids if tile_ids.count(tile_id) > 1})
            raise ValueError(f"tile ids must be unique; duplicated: {duplicated}")
        self.pcd_tiles = pcd_tiles
        self._img_res = img_res
        self.proj_cls: type[ProjectionStrategy] = cast(type[ProjectionStrategy], proj_cls)
        self.interp_cls: type[InterpolationStrategy] = cast(type[InterpolationStrategy], interp_cls)
        self._proj_kwargs = proj_kwargs or {}
        self._interp_kwargs = interp_kwargs or {}
        # None-sentinel default (no shared mutable LazyDiskCacheConfig()),
        # consistent with core.py / manager.py / interpolation.py:141.
        self._lazy_disk_cache_config = lazy_disk_cache_config or LazyDiskCacheConfig()
        self.image_generators: dict[str, PointCloudImageGenerator] = {}

    def generate(
        self,
        features: list[str],
        n_jobs: int = -1,
    ) -> dict[ImageKey, DiskBackedImageData]:
        """Generate ``features`` for every tile, one ``_process_tile`` call per tile.

        Each call is the module-level ``_process_tile`` with that tile's own generator
        (``None`` on the first call) and picklable inputs; the tiled generator itself is never
        part of a task.

        Entries returned by a pooled call (any ``n_jobs`` other than 1), and the entries of the
        stores kept in ``image_generators``, no longer delete their ``.dat`` memmap on garbage
        collection: each pickle round-trip gives the parent another entry object on the same
        file, so one released call's results would otherwise unlink the files a later call's
        results read. The tile directory keeps those files until ``purge`` is called or the
        directory is removed. With ``n_jobs=1`` the results are the stores' own entries and
        behave as before.
        """

        tasks = self.pcd_tiles

        with parallel_config(backend="loky", n_jobs=n_jobs, verbose=50, prefer="processes"):
            results = Parallel()(
                delayed(_process_tile)(
                    self.image_generators.get(task.tile_id),
                    task.tile_id,
                    task.tile_pcd,
                    task.tile_kwargs,
                    features,
                    self.proj_cls,
                    self.interp_cls,
                    dict(self._proj_kwargs),
                    dict(self._interp_kwargs),
                    self._lazy_disk_cache_config,
                    self._img_res,
                )
                for task in tasks
            )

        result_dict: dict[ImageKey, DiskBackedImageData] = {}
        for tile_result in results:
            self.image_generators[tile_result[0]] = tile_result[1]
            tile_dict = {
                ImageKey(tile_result[0], feature_id): feature_data
                for feature_id, feature_data in tile_result[2].items()
            }
            result_dict.update(tile_dict)

        if n_jobs != 1:
            _release_gc_ownership(result_dict, self.image_generators)

        return result_dict


def _release_gc_ownership(
    result_dict: Mapping[ImageKey, DiskBackedImageData],
    image_generators: Mapping[str, PointCloudImageGenerator],
) -> None:
    """Disable purge-on-garbage-collection on every pooled result and live store entry.

    A pooled run returns parent-side copies of entries that share one ``<tile>/<key>.dat`` path
    with the copies every other call returns. Each copy carries its own garbage-collection
    finalizer, so whichever is collected first would unlink the file the others read. Only the
    public ``disable_purge()`` is used.
    """
    for entry in result_dict.values():
        entry.disable_purge()
    for image_gen in image_generators.values():
        for entry in image_gen.feature_mgr.cache_store.store.values():
            if entry is not None:
                entry.disable_purge()


def _process_tile(
    image_gen: PointCloudImageGenerator | None,
    tile_id: str,
    tile_pcd: PointCloudData,
    tile_kwargs: Mapping[str, Any],
    features: list[str],
    proj_cls: type[ProjectionStrategy],
    interp_cls: type[InterpolationStrategy],
    proj_kwargs: dict[str, Any],
    interp_kwargs: dict[str, Any],
    lazy_disk_cache_config: LazyDiskCacheConfig,
    img_res: ImgRes,
) -> tuple[str, PointCloudImageGenerator, dict[str, DiskBackedImageData]]:
    """Generate ``features`` for one tile; the unit of work of a worker task.

    Module-level so that a task serialises this function by reference and carries only the
    arguments below - the tile's own generator (``None`` when it has to be built here) and
    plain inputs - never the tiled generator or any other tile's state.
    """

    if image_gen is None:
        if "lazy_disk_cache_config" in interp_kwargs:
            interp_kwargs = dict(interp_kwargs)
            interp_kwargs["lazy_disk_cache_config"] = interp_kwargs["lazy_disk_cache_config"].extend_cache_path(tile_id)

        image_gen = PointCloudImageGenerator(
            pcd=tile_pcd,
            proj=proj_cls(**tile_kwargs, **proj_kwargs),
            interp=interp_cls(**interp_kwargs),
            lazy_disk_cache_config=lazy_disk_cache_config.extend_cache_path(tile_id),
            img_res=img_res,
        )
    tile_images = image_gen.generate(features)
    return tile_id, image_gen, tile_images
