"""The post-migration ``DiskBackedImageStore`` — SIMULATED, never written to src/.

Spike rule (MANIFEST): investigation only. Override removal is simulated by this local
subclass of the *upstream* ``DiskBackedStore``, which reproduces the real class's
surviving surface (``__init__``, ``add_image_to_store``, ``image_data``, ``offload``,
``offload_image_data_to_disk``) with the three overrides deleted
(``_assert_within_cache_dir`` / ``_get_npy_path`` / ``_get_meta_path`` / ``__delitem__``)
and the overwrite path switched from ``del self[k]`` to ``self.purge(k)`` (D-08).

``add_image_to_store`` keeps ONE containment-first statement — the public free function
``get_npy_path(cache_dir, key)`` in place of the old ``self._get_npy_path(key)`` — so that
key refusal still precedes the shape check and every mutation (the Phase-5 ordering).
"""

from __future__ import annotations

from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig, get_npy_path
from numpy.typing import NDArray

from pc2img.image_cache import DiskBackedImageData
from pc2img.image_cache.disk_backed_image_data import _assert_image_shape


class TargetImageStore(DiskBackedStore[DiskBackedImageData]):
    def __init__(self, *, config: LazyDiskCacheConfig | None = None) -> None:
        if config is None:
            config = LazyDiskCacheConfig()
        super().__init__(config=config, factory=DiskBackedImageData, value_type=DiskBackedImageData)

    def add_image_to_store(
        self,
        img_name: str,
        img_data: NDArray,
        *,
        enable_caching_override: bool | None = None,
        automatic_offloading_override: bool | None = None,
        purge_disk_on_gc_override: bool | None = None,
    ) -> None:
        get_npy_path(self.cache_dir, img_name)  # key / containment refusal FIRST
        _assert_image_shape(img_data)  # then shape (AssertionError, pinned)
        if img_name in self:
            self.purge(img_name)  # D-08: upstream verb, validates before mutating
        self.add_data_to_store(
            img_name,
            img_data,
            enable_caching_override=enable_caching_override,
            automatic_offloading_override=automatic_offloading_override,
            purge_disk_on_gc_override=purge_disk_on_gc_override,
        )

    @property
    def image_data(self):
        return self.store

    def offload(self, features=None, pickle_container: bool = False) -> None:
        super().offload(keys=features, pickle_container=pickle_container)

    def offload_image_data_to_disk(self, features=None) -> None:
        self.offload(features, pickle_container=True)


def assert_target_state() -> None:
    """The simulated class must really have none of the removed names."""
    for n in ("_get_npy_path", "_get_meta_path", "_assert_within_cache_dir"):
        assert not hasattr(TargetImageStore, n), n
    assert TargetImageStore.__delitem__ is DiskBackedStore.__delitem__
    assert TargetImageStore.purge is DiskBackedStore.purge
