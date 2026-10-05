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

    **Disk persistence.** Entries returned by any ``generate()`` call (``n_jobs=1`` included) and
    the entries of the stores kept in ``image_generators`` have purge-on-garbage-collection
    disabled, so releasing one call's results never deletes a ``.dat`` memmap that a later call's
    results read. The price: released results and dropped generators no longer delete their cache
    files at all, whatever ``n_jobs``. With the default ``enable_caching=False`` nothing is written
    and only each store's empty temporary directory remains (as before this change). When caching
    is enabled without a ``cache_path``, each tile store writes into its own temporary directory
    (created with ``tempfile.mkdtemp``): ``<store dir>/<key>.dat``, plus the codec pair
    (``<key>.npy`` and ``<key>.meta.json``) that pickling in a pooled run writes, and nothing
    cleans that directory up. With a ``cache_path`` the files are
    ``<cache_path>/<tile_id>/<key>.dat`` and the codec pair. All of them persist until ``purge()``
    is called or the directory is removed. Routes: configure ``cache_path`` and remove that
    directory when the run is done; or ``purge()`` keys from the owning process (the calling
    process owns a tile's store if that store was built by an ``n_jobs=1`` call: a pooled call
    builds it in a worker, and after a pooled failure an ``n_jobs=1`` retry rebuilds it in the
    calling process).

    The disarm may be recorded on disk. After tiled runs, a key's ``.meta.json`` sidecar may
    record ``purge_disk_on_gc=False``, and any store or generator opened later over the same
    directory, tiled or not, inherits that value for the key whatever its own configuration asks.
    A durable-cache or warm-restart configuration that asks for ``purge_disk_on_gc=True`` may
    therefore be overridden for some keys; check the value on the loaded entries if it matters.

    Whenever the work runs in a worker pool, every tile's ``DiskBackedImageStore`` is constructed
    inside a worker and records that worker's process id as its owner, for good. GSEGUtils refuses
    ``purge`` from any other process with ``StorePurgeRefusedError`` (a ``RuntimeError``), and
    ``add_image_to_store`` purges first when the key is tracked or its ``<key>.npy`` codec file is
    on disk. After a pooled run the parent process can therefore neither purge nor overwrite those
    stores. A later ``generate()`` that requests a feature which is untracked but still has its
    codec pair in the tile directory (dropped with ``del``, ``pop``, ``popitem`` or ``clear`` while
    offloaded) raises ``StorePurgeRefusedError`` when that tile's ``_process_tile`` runs in a process
    other than the owner. In a pool that depends on which worker gets the tile; after a pooled run
    it always happens at ``n_jobs=1``, because the parent is not the owner either. Leftover
    temporary files, a lone ``.meta.json`` or a lone ``.dat`` (a killed worker, or a session with
    ``purge_disk_on_gc=False``) do not trigger it. Ways around it:

    * use ``n_jobs=1`` for every call on an instance that will be purged from or overwritten; an
      instance that has run in a pool once is owned by its workers for good;
    * build a fresh ``TiledPointCloudImageGenerator`` for each ``generate()`` call;
    * drop the tile's generator and remove its cache sub-directory ``<cache_path>/<tile_id>``
      (for example with ``shutil.rmtree``).

    If any tile fails in a pooled call, the parent drops the tile generators that existed before
    the call and re-raises: the tiles that finished have already written codec pairs the parent's
    copies do not track. A failing first call has nothing to drop. With a ``cache_path`` the next
    call rebuilds each tile's generator (in a worker, or in the calling process at ``n_jobs=1``)
    and the construction scan adopts the codec pairs the finished tiles wrote, so the retry is
    not refused on ownership grounds (for the retry's own hazard see Known limitations below).
    Without a ``cache_path`` the next call rebuilds every tile store in a new temporary
    directory, recomputes every feature and leaves the previous directories and their files
    behind. With the default ``enable_caching=False`` nothing is on disk, so the reset protects
    nothing there and only discards the in-memory rasters. A failing ``n_jobs=1`` call keeps the
    generators that existed before it, whose stores were updated in place; a generator it built
    for the first time is not kept, so a failing first call leaves ``image_generators`` empty.
    The entries a failed call added to the kept stores keep their delete-on-collection hook (see
    Known limitations below).

    **Known limitations after a failed call (upstream-rooted).** The cause is in GSEGUtils: a
    released entry's purge-on-garbage-collection deletes a ``<key>.dat`` that another live copy of
    the entry uses (https://github.com/gseg-ethz/GSEGUtils/issues/83). Behaviour fixes are
    planned for pc2img 0.11.1. Until then, treat the following as a hazard of every failed
    ``generate()`` call with caching enabled, whatever ``n_jobs``, ``cache_path`` or call history:

    * The disarm described above runs only after a ``generate()`` call returns successfully. The
      entries a failed call added to kept stores stay armed, and so may the entries of generators
      a failing first call built and did not keep.
    * After a ``generate()`` call raises, the files of a later retry may be deleted when the
      failed call's objects are garbage-collected: the retry may rewrite the same
      ``<tile_id>/<key>.dat`` files, the failed call's old entries may unlink them when they are
      collected, and a later read of a retried raster may then raise ``FileNotFoundError``. Do
      not retry inside the ``except`` block, and do not rely on ``gc.collect()`` there: it
      collects nothing while the exception is still referenced. Let the exception go out of
      scope, call ``gc.collect()``, then retry; or retry with a fresh
      ``TiledPointCloudImageGenerator`` over a fresh ``cache_path``.
    * Do not hold entries taken from the tile stores (``image_generators[...].feature_mgr.
      cache_store``) across a regenerate: a held entry may delete the replacement's ``.dat`` when
      it is released.

    With the default ``enable_caching=False`` nothing is written to disk.

    **Link check (pc2img's own, to be revisited in 0.11.1).** Independent of the upstream cause
    above, ``DiskBackedImageStore`` refuses a symlink at any of a key's write paths before every
    write: ``StorePurgeAliasedArtefactError`` when the link resolves inside the cache directory,
    ``StorePurgeForeignArtefactError`` when it resolves outside. The classification is by where
    the link resolves, so a ``<key>.dat`` link to a payload that upstream treats as a legitimate
    adopted entry is refused as well, and so is a dangling link. A symlink loop at a write path
    raises a bare ``RuntimeError`` from ``Path.resolve``, not a member of the
    ``StorePurgeRefusedError`` family.
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
        part of a task. If a pooled call (any ``n_jobs`` other than 1) raises, the tile generators
        that existed before the call are dropped before the exception propagates and the next call
        rebuilds them; a call that raises at ``n_jobs=1`` keeps the generators that existed before
        it (a first call has none to keep). Without a ``cache_path`` the rebuild writes every tile
        store into a new temporary directory and leaves the previous ones behind.

        Entries returned by any call (``n_jobs=1`` included), and the entries of the stores kept
        in ``image_generators``, never delete their ``.dat`` memmap on garbage collection: each
        pickle round-trip gives the parent another entry object on the same file, and an entry
        created at ``n_jobs=1`` is still alive when a later pooled call rebuilds that file under
        another object, so one released call's results would otherwise unlink the files a later
        call's results read. The tile directory keeps those files until ``purge`` is called or
        the directory is removed. The disarm runs only after a call returns successfully: the
        entries a call that raised added to kept stores stay armed, which may make a retry of
        that call lose files (see the class docstring, Known limitations, for the recommended route).
        """

        tasks = self.pcd_tiles

        try:
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
        except BaseException:
            if n_jobs != 1:
                # ``Parallel`` raises without the partial results, so the parent cannot know which
                # tiles finished. Those that did have written codec pairs the parent's pre-call
                # store copies do not track; the retry would hit the hard gate in a non-owner
                # process. Dropping every generator makes the next call rebuild each store in a
                # worker (or here, at ``n_jobs=1``), whose construction scan adopts what is on
                # disk and recomputes the rest. Only the generators that existed before the call
                # are dropped. A call that raises at ``n_jobs=1`` keeps the generators that
                # existed before it, because their stores were updated in place; the entries it
                # added to them stay armed, since the disarm below runs only after a successful
                # return.
                self.image_generators.clear()
            raise

        result_dict: dict[ImageKey, DiskBackedImageData] = {}
        for tile_result in results:
            self.image_generators[tile_result[0]] = tile_result[1]
            tile_dict = {
                ImageKey(tile_result[0], feature_id): feature_data
                for feature_id, feature_data in tile_result[2].items()
            }
            result_dict.update(tile_dict)

        _release_gc_ownership(result_dict, self.image_generators)

        return result_dict


def _release_gc_ownership(
    result_dict: Mapping[ImageKey, DiskBackedImageData],
    image_generators: Mapping[str, PointCloudImageGenerator],
) -> None:
    """Disable purge-on-garbage-collection on every returned result and live store entry.

    Called after every successful ``generate()``, whatever ``n_jobs``; a call that raises
    leaves what it added armed. A pooled run hands back parent-side
    copies of entries that share one ``<tile>/<key>.dat`` path with the copies every other call
    hands back, and an entry created at ``n_jobs=1`` is still alive (and armed) when a later pooled
    call rebuilds the same file under another object. Each copy carries its own garbage-collection
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
