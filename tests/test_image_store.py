"""Proving sensors for the image_cache reparent (BUG-02 / DSN-02 + DSN-09).

Authored test-first (Phase 5, D-12): every sensor here is RED until
`image_cache/` is reparented onto the GSEGUtils primitives
(`DiskBackedNDArray` + `DiskBackedStore`). Tests are pure (no PointCloudData).

- BUG-02 / DSN-02: `DiskBackedImageData` arithmetic must dispatch through the
  inherited `__array_ufunc__` and return a plain `np.ndarray`.
- DSN-09 (security): the store must not carry an arbitrary-object
  deserialization sink; reload goes through the `allow_pickle=False` codec and
  a legacy `.pkl` degrades to a cache miss.
- Blocker sensor (Pitfall 1): an offload -> reload round-trip through the store
  must return the correct array (fails if the reload class registration is
  unresolved).
"""

import pickle
import re
from pathlib import Path

import numpy as np
import pytest
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pc2img.image_cache import DiskBackedImageData, DiskBackedImageStore

_rng = np.random.default_rng(20260711)


def _gray(shape=(10, 10), dtype=np.float32):
    return _rng.random(shape).astype(dtype)


def test_arithmetic_returns_plain_ndarray():
    """BUG-02 / DSN-02: dbid + dbid == arr + arr and the result is a plain ndarray."""
    arr = _gray()
    a = DiskBackedImageData(arr)
    b = DiskBackedImageData(arr)

    result = a + b

    np.testing.assert_array_equal(result, arr + arr)
    assert type(result) is np.ndarray


def test_store_source_has_no_arbitrary_deserialization_sink():
    """DSN-09: the store SOURCE must not call the arbitrary-object load sink.

    We negative-grep the store module source. The forbidden token is assembled
    from a hoisted, MULTILINE-flagged pattern (Pitfall 6: no mid-pattern inline
    flags under Python >= 3.11) rather than a bare literal.
    """
    import pc2img.image_cache.disk_backed_image_store as store_mod

    src = Path(store_mod.__file__).read_text(encoding="utf-8")
    sink = re.compile(r"pickle\s*\.\s*loads?\s*\(", re.MULTILINE)

    assert sink.search(src) is None, "store source still holds an arbitrary-object load sink"


def test_legacy_pkl_refused_as_cache_miss(tmp_path: Path):
    """A legacy pre-Phase-2 `.pkl` must be refused (cache miss), never loaded."""
    legacy = tmp_path / "ghost.pkl"
    with open(legacy, "wb") as f:
        pickle.dump({"unexpected": "payload"}, f)

    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))

    with pytest.raises(KeyError):
        _ = store["ghost"]


def test_offload_reload_round_trip(tmp_path: Path):
    """Blocker sensor: add -> offload -> re-fetch returns the correct array."""
    arr = _gray((6, 6))
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", arr)

    store.offload_image_data_to_disk("range")

    reloaded = np.asarray(store["range"])
    np.testing.assert_array_equal(reloaded, arr)


# --------------------------------------------------------------------------- #
# G3 — overwrite / delete must purge the on-disk codec pair                    #
#                                                                              #
# add_image_to_store's overwrite path does `del self[key]`, but the base       #
# __delitem__ drops only the in-memory entry. The stale `<key>.npy` +          #
# `<key>.meta.json` remain, and a fresh store re-scans `*.npy` on construction #
# — so it re-adopts and serves the stale pre-overwrite raster.                 #
# --------------------------------------------------------------------------- #
def test_overwrite_does_not_leave_stale_on_disk_raster(tmp_path: Path):
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store1 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store1.add_image_to_store("range", a)
    store1.offload_image_data_to_disk("range")
    assert store1._get_npy_path("range").exists()

    # Overwrite the key in the SAME store — routes through `del self["range"]`.
    store1.add_image_to_store("range", b)

    # A fresh store over the same cache_dir must NOT serve the stale pre-overwrite A.
    store2 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    try:
        served = np.asarray(store2["range"])
    except KeyError:
        served = None  # cache miss: A purged, B never offloaded — acceptable
    if served is not None:
        assert not np.array_equal(served, a), "fresh store served the stale pre-overwrite raster"


def test_delete_purges_on_disk_codec_pair(tmp_path: Path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6)))
    store.offload_image_data_to_disk("range")
    assert store._get_npy_path("range").exists()
    assert store._get_meta_path("range").exists()

    del store["range"]

    assert not store._get_npy_path("range").exists()
    assert not store._get_meta_path("range").exists()


def test_delete_absent_key_does_not_raise(tmp_path: Path):
    # A key that was never offloaded (no on-disk codec pair) must delete cleanly:
    # unlink(missing_ok=True) carries the safety, not a cache_dir-is-None guard.
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6)))
    del store["range"]  # in memory only — no .npy on disk
    assert "range" not in store
