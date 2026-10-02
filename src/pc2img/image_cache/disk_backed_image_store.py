from collections.abc import Mapping
from pathlib import Path

from GSEGUtils.lazy_disk_cache import (
    DiskBackedStore,
    LazyDiskCacheConfig,
    StorePurgeRefusedError,
    get_meta_path,
    get_npy_path,
)
from GSEGUtils.lazy_disk_cache.paths import get_memmap_path
from numpy.typing import NDArray
from pydantic import ConfigDict, validate_call

from .disk_backed_image_data import DiskBackedImageData, _assert_image_shape


def _adoptable_artefact_exists(cache_dir: Path, key: str) -> bool:
    """Return whether ``<key>.npy`` is on disk, the one file a fresh store adopts.

    The base store's startup scan globs ``*.npy``, so a lone ``.npy`` is adopted
    as a tracked key (a read of it is a cache miss) and the codec pair is served;
    a lone ``.meta.json`` or ``.dat`` is not adopted. Only this file can make a
    store serve a stale raster. Built through the upstream builder, so an invalid
    or escaping key raises the upstream ``StoreKeyError`` here exactly as it does
    for the first statement of :meth:`DiskBackedImageStore.add_image_to_store`.
    """
    return get_npy_path(cache_dir, key).exists()


def _leftover_artefact_exists(cache_dir: Path, key: str) -> bool:
    """Return whether a ``<key>.meta.json`` or ``<key>.dat`` is on disk.

    Neither is served by a fresh store, but a ``.dat`` can still be the recorded
    path of a dropped entry whose cleanup hook is armed in this process, and only
    :meth:`DiskBackedStore.purge` detaches that hook.
    """
    return get_meta_path(cache_dir, key).exists() or get_memmap_path(cache_dir, key).exists()


class DiskBackedImageStore(DiskBackedStore[DiskBackedImageData]):
    """Named raster store backed by GSEGUtils' hardened ``DiskBackedStore``.

    Thin WRAPPER over :class:`GSEGUtils.lazy_disk_cache.DiskBackedStore` bound to
    :class:`DiskBackedImageData`: it supplies the factory / value-type and
    re-aliases the legacy method names the :class:`FeatureManager` depends on so
    the public barrel and call sites stay stable.

    The on-disk format is the base store's ``<key>.npy`` + ``<key>.meta.json``
    (``allow_pickle=False``) codec pair. There is no arbitrary-object
    deserialization path here, and a stale legacy cache file degrades to a cache
    miss via the base loader's explicit refusal.

    **Key validation and containment are GSEGUtils'.** Every on-disk path the
    store derives from a key is built by the upstream public builders
    (``get_npy_path`` / ``get_meta_path``, with ``is_valid_store_key`` as the
    lexical check), and the mapping setter refuses an invalid or escaping key at
    set time. An invalid key, or an invalid ``extend_cache_path`` segment, raises
    the upstream ``StoreKeyError`` (a :class:`ValueError`) unwrapped; this class
    adds no pre-validation of its own. The guarantee is construction-time and
    non-adversarial: concurrent writers and racing symlinks or hardlinks are out
    of scope upstream and were never covered here. Two limits are documented
    rather than guarded. A planted ``<key>.npy.tmp`` or ``<key>.meta.json.tmp``
    symlink is followed on write. An entry inserted through the mapping setter
    (``store[key] = value``) carries whatever ``cache_path`` its caller supplied
    and, with the default ``pickle_container=False``, :meth:`offload` writes
    through that entry-owned path even when it lies outside the cache directory;
    only :meth:`add_image_to_store` derives its entry's ``cache_path`` from the
    validated builders. The same entry is also refused by :meth:`purge` and by
    the overwrite in :meth:`add_image_to_store` (a ``StorePurgeForeignArtefactError``),
    so a setter-inserted entry whose ``cache_path`` lies outside the cache
    directory can no longer be replaced through that method. Pickling a store
    de-links cache-internal symlinks (upstream behaviour).

    **Threat model, stated once.** Scalar-field names come from PLY/E57 property
    names read off point-cloud files, which are untrusted metadata, and the
    feature registry's unanchored default fallback turns any unmatched name into
    a scalar-field feature whose name is passed verbatim as the store key. A name
    such as ``../victim`` therefore reaches :meth:`add_image_to_store` through
    ``generate()`` and is refused there; this store is also exported from the
    public barrel, so any caller may pass any key directly.

    **Removal.** ``del store[key]``, ``pop`` and ``clear`` drop tracking only and
    leave every file in place (an offloaded key is re-adopted on the next read).
    :meth:`purge` is the delete verb: it drops tracking and removes the memmap and
    the codec pair. The overwrite in :meth:`add_image_to_store` removes those files
    whether or not the key is still tracked.
    """

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        *,
        config: LazyDiskCacheConfig | None = None,
    ) -> None:
        # None-sentinel default, not a shared mutable LazyDiskCacheConfig()
        # instance, matching the same pattern used at the generator/manager
        # sites. No behaviour change — an omitted or explicit-None config
        # yields the identical default instance; an explicit config passes
        # through unchanged.
        if config is None:
            config = LazyDiskCacheConfig()
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
        re-submits the same feature name. An existing key is therefore purged
        first, so the prior overwrite semantics are preserved.

        **Ordering.** Four steps, in this order:

        1. the upstream ``get_npy_path`` builder validates the key and its
           containment and raises the upstream ``StoreKeyError`` (a
           :class:`ValueError`) before anything else is touched;
        2. :func:`_assert_image_shape` raises :class:`AssertionError` for a bad
           raster shape;
        3. an entry that is tracked, or whose key still has any of its six derived
           files on disk (a key dropped with ``del`` / ``pop`` / ``clear`` and
           left offloaded), is removed with :meth:`purge`. It validates before it
           mutates, detaches every cleanup hook registered for the key (including
           the one on an entry a caller dropped but still holds), and removes the
           memmap and the codec pair, so a retained reference to the old entry
           cannot delete the replacement's files when it is collected. A key that
           is neither tracked nor on disk is never handed to :meth:`purge`, so a
           worker process that did not construct the store can still add new keys;
        4. the replacement is built via :meth:`add_data_to_store`.

        Because the key check runs first, a key that both escapes the cache
        directory and carries a bad-shape raster raises ``StoreKeyError``, never
        :class:`AssertionError`. Both input-driven checks run before the existing
        entry is purged, so a rejected overwrite leaves the old entry and its
        on-disk files untouched.

        **Overwrite failures.** The ``purge`` an overwrite performs can raise
        upstream's refusal family, each a ``StorePurgeRefusedError`` (a
        :class:`RuntimeError`), under three independent conditions:

        - the calling process is not the one that constructed the store. Every
          tile store a ``TiledPointCloudImageGenerator`` builds with
          ``n_jobs >= 2`` is owned by a worker process, so after such a run the
          parent's overwrite of an existing key is refused (use ``n_jobs=1``, a
          fresh generator, or remove the tile sub-directory; see that class's
          docstring);
        - ``StorePurgeForeignArtefactError``, when a built artefact, or a live
          entry's own ``cache_path``, resolves outside the cache directory. This
          includes an entry inserted through the mapping setter with an outside
          ``cache_path``: such an entry can no longer be overwritten through this
          method (it could in earlier releases); re-point it, or give it an
          in-cache ``cache_path``, first;
        - ``StorePurgeAliasedArtefactError``, when a built artefact is a link to
          another key's artefact inside the cache directory.

        ``StorePurgeIncompleteError`` (an :class:`OSError`, outside that family)
        is raised when a file could not be unlinked. All of these surface
        unwrapped. Two failures after the purge still lose the old entry: a
        wrong-type cache override, which fails validation inside
        :meth:`add_data_to_store`, and an :class:`OSError` while the replacement's
        memmap is being created (for example a full disk). Recovering the latter
        would need a build-then-adopt primitive in the cache layer that owns the
        ``<key>.dat`` derivation. This is not a claim that every input-driven
        failure is caught before the purge.

        ``del`` / ``pop`` / ``clear`` drop tracking only; they are not part of an
        overwrite. Only :meth:`purge` removes files.
        """
        get_npy_path(self.cache_dir, img_name)
        _assert_image_shape(img_data)
        if img_name in self or _adoptable_artefact_exists(self.cache_dir, img_name):
            self.purge(img_name)
        elif _leftover_artefact_exists(self.cache_dir, img_name):
            try:
                self.purge(img_name)
            except StorePurgeRefusedError as exc:
                if type(exc) is not StorePurgeRefusedError:
                    raise
        self.add_data_to_store(
            img_name,
            img_data,
            enable_caching_override=enable_caching_override,
            automatic_offloading_override=automatic_offloading_override,
            purge_disk_on_gc_override=purge_disk_on_gc_override,
        )

    @property
    def image_data(self) -> Mapping[str, DiskBackedImageData | None]:
        """Legacy alias for the inherited read-only :attr:`DiskBackedStore.store` mapping."""
        return self.store

    def offload(
        self,
        features: str | list[str] | None = None,
        pickle_container: bool = False,
    ) -> None:
        """Offload selected entries; ``features`` is the legacy alias for ``keys``.

        ``pickle_container=False`` (the default) delegates to each entry's own
        :meth:`LazyDiskCache.offload`, which writes through the entry's own
        ``cache_path`` (the ``<key>.dat`` memmap) directly — for an entry whose
        ``cache_path`` was supplied by the caller rather than derived by
        :meth:`add_image_to_store` that path can lie outside the cache directory
        (see the class docstring). ``pickle_container=True`` writes the
        ``<key>.npy`` + ``<key>.meta.json`` codec pair through the upstream
        validated path builders.
        """
        super().offload(keys=features, pickle_container=pickle_container)

    def offload_image_data_to_disk(self, features: str | list[str] | None = None) -> None:
        """Legacy alias: offload the wrapping container via the base codec pair."""
        self.offload(features, pickle_container=True)
