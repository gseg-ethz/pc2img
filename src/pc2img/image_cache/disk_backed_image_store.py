from pathlib import Path

from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig
from numpy.typing import NDArray
from pydantic import ConfigDict, validate_call

from .disk_backed_image_data import DiskBackedImageData


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

    **Containment invariant (WR-02, narrowed round 4 — review-r2-3f625b03fb03):**
    every on-disk path this store builds FROM A KEY resolves *inside* the
    configured cache directory. A key whose path escapes it is refused with
    :class:`ValueError` at the first path build, so no key can make a write, a
    read or an unlink touch a file outside that directory. Nesting *under* the
    cache directory is still allowed — only escaping is refused. This guard
    does NOT extend to an entry's own ``cache_path``: an entry inserted
    through the mapping setter (``store[key] = value``) carries whatever
    ``cache_path`` its caller supplied, and :meth:`offload` with the default
    ``pickle_container=False`` writes through that entry-owned path directly
    (the ``.dat`` memmap write is a GSEGUtils carry-out — see
    :meth:`offload`). Only :meth:`add_image_to_store` derives its entry's
    ``cache_path`` from the guarded route.
    """

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        *,
        config: LazyDiskCacheConfig | None = None,
    ) -> None:
        # IN-03 (review-r1-8ff7171c6ca4): None-sentinel default, not a shared
        # mutable LazyDiskCacheConfig() instance (DSN-07 pattern, matching the
        # 05-10/05-11 sweep at the generator/manager sites). No behaviour
        # change — an omitted or explicit-None config yields the identical
        # default instance; an explicit config passes through unchanged.
        if config is None:
            config = LazyDiskCacheConfig()
        super().__init__(
            config=config,
            factory=DiskBackedImageData,
            value_type=DiskBackedImageData,
        )

    # --- containment: one authority over every on-disk path (WR-02) ----------

    def _assert_within_cache_dir(self, path: Path) -> Path:
        """Return ``path`` unchanged, or raise if it escapes the cache directory.

        This is the single containment authority for the on-disk paths this
        store builds FROM A KEY, because every one of them routes through
        :meth:`_get_npy_path` / :meth:`_get_meta_path`:

        1. **insertion** — ``DiskBackedStore.add_data_to_store`` (so the refusal
           lands *before* any file outside the cache directory is created);
           the ``cache_path`` derived here is what the inserted entry's own
           memmap write (``LazyDiskCache._convert_to_memmap``) later writes
           through as ``<key>.dat`` — ``LazyDiskCache._init_from_config``
           re-suffixes the handed-in ``.npy`` path internally,
        2. **offload write** — ``DiskBackedStore._store_entry``, which also
           builds the ``<key>.meta.json.tmp`` atomic-write sidecar directly
           from the cache directory,
        3. **load** — ``DiskBackedStore._load_entry``,
        4. **delete** — this class's :meth:`__delitem__` unlink.

        Threat posture, measured 2026-09-24 (BUG-05, review-r2-1a435f413f18):
        ``FeatureRegistry.match`` (:mod:`pc2img.features.registry`) has an
        UNANCHORED default fallback — any name that matches no registered
        pattern becomes a ``ScalarFieldFeature`` pseudo-spec with
        ``params={'feature': name}``, and ``FeatureManager.submit`` passes
        that name verbatim as the store key. ``ScalarFieldFeature``'s own
        pattern (``^scalar_field_(?P<feature>.+)$``) has an unconstrained
        suffix that accepts an embedded traversal too. Scalar-field names
        come from PLY/E57 property names read off point-cloud files —
        untrusted metadata, not a value pc2img constructs. Reproduced
        end-to-end: a ``PointCloudData`` carrying a scalar field named
        ``../victim`` reaches this guard via ``generate(["../victim"])`` and
        is refused with ``ValueError``; without the guard it would write
        outside the cache directory. On the installed GSEGUtils 0.5.x this
        containment guard is **LOAD-BEARING**, not defence-in-depth — it
        becomes redundant only at the Phase-6 GSEGUtils 0.6 adoption, where
        upstream absorbs the equivalent check
        (``.planning/spikes/000-absorption-test/README.md``, verdict
        VALIDATED). This store is also exported from the public barrel
        ``pc2img.image_cache.__all__``, so any caller may pass any key
        directly — the guard is not solely defending the registry route.

        The original ``path`` is returned (not the resolved one) so the base
        store's behaviour stays byte-identical — only the *check* resolves. The
        cache directory is resolved per call rather than cached on the instance:
        the base store pickles its ``__dict__`` wholesale for the joblib/loky
        tiled path, so a cached resolved path is state that can go stale across
        processes, and the measured cost of not caching is ~40 µs per path build
        (per raster, not per pixel).
        """
        cache_dir = self._cache_dir.resolve()
        candidate = path.parent.resolve() / path.name
        if not candidate.is_relative_to(cache_dir):
            raise ValueError(
                f"Refusing raster key path {str(path)!r}: it resolves to "
                f"{str(candidate)!r}, outside the configured cache directory "
                f"{str(cache_dir)!r}. Raster keys must not escape the cache directory."
            )
        return path

    def _get_npy_path(self, feature: str) -> Path:
        """Return the base store's ``.npy`` path, refused if it escapes the cache dir."""
        return self._assert_within_cache_dir(super()._get_npy_path(feature))

    def _get_meta_path(self, feature: str) -> Path:
        """Return the base store's JSON sidecar path, refused if it escapes the cache dir."""
        return self._assert_within_cache_dir(super()._get_meta_path(feature))

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

        Three-stage contract, in order (round 4, review-r2-70fb459066a6):

        1. **Containment first** — both codec paths are built via
           :meth:`_get_npy_path` / :meth:`_get_meta_path` before anything else
           runs. If ``key`` escapes the cache directory this raises
           ``ValueError`` here, before the in-memory entry is touched: a
           refused delete is a no-op in memory as well as on disk.
        2. **Membership second** — only then does the base store's
           ``__delitem__`` run: its entire body is an in-memory ``del``, so it
           raises ``KeyError`` for an untracked key with no side effect on
           disk (G10). Ordering matters here — building the paths AFTER the
           base delegation made a refused delete (either a containment
           ``ValueError`` or, historically, a reversed ``KeyError`` ordering)
           irreversibly destructive.
        3. **Unlink last** — the two ``.npy`` / ``.meta.json`` paths, already
           bound to local variables in stage 1, are purged only once stage 2
           has confirmed the key was genuinely tracked.

        No membership pre-check (``key in self``) is added ahead of the
        delegation in stage 2 — the base store stays the single membership
        authority, and the ``KeyError`` path stays a disk no-op because no
        unlink runs until ``super().__delitem__`` has returned.

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
        npy_path = self._get_npy_path(key)
        meta_path = self._get_meta_path(key)
        super().__delitem__(key)
        npy_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

    @property
    def image_data(self) -> dict[str, DiskBackedImageData | None]:
        """Legacy alias for the inherited :attr:`DiskBackedStore.store` mapping."""
        return self.store

    def offload(
        self,
        features: str | list[str] | None = None,
        pickle_container: bool = False,
    ) -> None:
        """Offload selected entries; ``features`` is the legacy alias for ``keys``.

        ``pickle_container=False`` (the default) delegates to each entry's own
        :meth:`LazyDiskCache.offload`, which writes through the entry's own
        ``cache_path`` (the ``<key>.dat`` memmap) directly — this bypasses the
        store's containment guard for an entry whose ``cache_path`` was
        supplied by the caller rather than derived by
        :meth:`add_image_to_store` (see the class docstring's containment
        invariant, review-r2-3f625b03fb03). ``pickle_container=True`` routes
        through the guarded ``_get_npy_path`` / ``_get_meta_path`` builders.
        """
        super().offload(keys=features, pickle_container=pickle_container)

    def offload_image_data_to_disk(self, features: str | list[str] | None = None) -> None:
        """Legacy alias: offload the wrapping container via the base codec pair."""
        self.offload(features, pickle_container=True)
