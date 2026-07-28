import logging

from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig
from numpy.typing import NDArray
from pydantic import ConfigDict, validate_call

from .disk_backed_image_data import DiskBackedImageData

logger = logging.getLogger(__name__.split(".")[0])


class DiskBackedImageStore(DiskBackedStore[DiskBackedImageData]):
    """Named raster store backed by GSEGUtils' hardened ``DiskBackedStore`` (D-05).

    Thin WRAPPER over :class:`GSEGUtils.lazy_disk_cache.DiskBackedStore` bound to
    :class:`DiskBackedImageData`: it supplies the factory / value-type and
    re-aliases the legacy method names the :class:`FeatureManager` depends on so
    the public barrel and call sites stay stable.

    The on-disk format is the base store's ``<key>.npy`` + ``<key>.meta.json``
    (``allow_pickle=False``) codec pair. The previous arbitrary-object
    deserialization sink (DSN-09) is eliminated by construction — there is no
    load-from-serialized-object path here anymore — and a stale legacy cache
    file degrades to a cache miss via the base loader's explicit refusal.
    """

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        *,
        config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None:
        super().__init__(
            config=config,
            factory=DiskBackedImageData,
            value_type=DiskBackedImageData,
        )

    # --- legacy BC aliases: keep FeatureManager call sites stable ------------

    def add_image_to_store(
        self,
        img_name: str,
        img_data: NDArray,
        *,
        enable_caching_override: bool | None = None,
        automatic_offloading_override: bool | None = None,
        purge_disk_on_gc_override: bool | None = None,
    ) -> None:
        """Wrap ``img_data`` and store it under ``img_name`` (overwrite-preserving).

        The base :meth:`DiskBackedStore.add_data_to_store` raises on an existing
        key, but the legacy store silently replaced it — generator reuse
        re-submits the same feature name. We drop the existing key first so the
        prior overwrite semantics are preserved.
        """
        if img_name in self:
            del self[img_name]
        self.add_data_to_store(
            img_name,
            img_data,
            enable_caching_override=enable_caching_override,
            automatic_offloading_override=automatic_offloading_override,
            purge_disk_on_gc_override=purge_disk_on_gc_override,
        )

    def __delitem__(self, key: str) -> None:
        """Drop ``key`` and purge its on-disk ``.npy`` + ``.meta.json`` codec pair.

        Membership is validated by the base store FIRST: the entire body of
        :meth:`DiskBackedStore.__delitem__` is an in-memory ``del``, so it raises
        ``KeyError`` for an untracked key with no side effect. Delegating before
        touching the disk keeps that contract intact, and buys exactly one
        property: **a delete that raises ``KeyError`` is a no-op on disk** (G10).
        Ordering matters here — the reverse order made a ``KeyError`` delete
        irreversibly destructive.

        That property is narrower than "one store cannot destroy another store's
        raster", and deliberately so. The base ``__init__`` re-scans ``*.npy`` and
        adopts every key it finds, so a store constructed *after* another store
        offloaded ``key`` **tracks** it; the delete then succeeds, does purge the
        shared codec pair, and the offloaded peer can no longer serve it. That is
        the intended G3 semantics — leaving an offloaded pair behind would let a
        store re-adopt and serve a stale raster, so unlinking keeps the ``.npy`` +
        JSON pair the single on-disk source of truth. It is a reason two stores
        must not share one ``cache_path`` unless the caller wants exactly that
        aliasing; ``TiledPointCloudImageGenerator`` sidesteps it by giving each
        tile its own ``extend_cache_path(tile_id)`` subdirectory.

        ``add_image_to_store`` routes its overwrite through this method, so both
        explicit-delete and overwrite are covered by this single override.

        ``unlink(missing_ok=True)`` carries the safety for a key that was tracked
        but never offloaded — an absent file is simply a no-op. No new
        deserialization surface is introduced (the DSN-09 posture is preserved).
        """
        super().__delitem__(key)
        self._get_npy_path(key).unlink(missing_ok=True)
        self._get_meta_path(key).unlink(missing_ok=True)

    @property
    def image_data(self) -> dict[str, DiskBackedImageData | None]:
        """Legacy alias for the inherited :attr:`DiskBackedStore.store` mapping."""
        return self.store

    def offload(
        self,
        features: str | list[str] | None = None,
        pickle_container: bool = False,
    ) -> None:
        """Offload selected entries; ``features`` is the legacy alias for ``keys``."""
        super().offload(keys=features, pickle_container=pickle_container)

    def offload_image_data_to_disk(self, features: str | list[str] | None = None) -> None:
        """Legacy alias: offload the wrapping container via the base codec pair."""
        self.offload(features, pickle_container=True)
