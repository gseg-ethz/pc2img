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


# --------------------------------------------------------------------------- #
# G10 — a KeyError-raising delete must be a genuine no-op (round 2)            #
#                                                                              #
# The G3 fix above unlinked the codec pair BEFORE super() validated key        #
# membership, inverting the base store's no-side-effect-on-KeyError contract   #
# (its whole body is `del self._store[key]`). With two stores over one cache   #
# directory, `del A["range"]` raises KeyError AND destroys the raster store B  #
# owns — B cleared its in-memory reference on offload, so B itself can no      #
# longer serve the key. That is live data loss, not a stale-cache concern.     #
# --------------------------------------------------------------------------- #
def _two_store_config(tmp_path: Path) -> LazyDiskCacheConfig:
    """Shared cache dir; purge_disk_on_gc=False keeps on-disk state deterministic."""
    return LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path, purge_disk_on_gc=False)


def test_failed_delete_preserves_codec_pair_and_both_stores(tmp_path: Path):
    arr = _gray((6, 6))

    store_a = DiskBackedImageStore(config=_two_store_config(tmp_path))
    store_b = DiskBackedImageStore(config=_two_store_config(tmp_path))

    # Only the pickle-container offload writes the `.npy` + `.meta.json` pair;
    # a plain offload() writes `<key>.dat` and does NOT set up the precondition.
    store_b.add_image_to_store("range", arr)
    store_b.offload_image_data_to_disk("range")
    assert store_b._get_npy_path("range").exists()
    assert store_b._get_meta_path("range").exists()

    with pytest.raises(KeyError):
        del store_a["range"]  # A never tracked the key

    # The failed delete must not have touched the shared cache directory.
    assert store_b._get_npy_path("range").exists(), "failed delete destroyed the .npy"
    assert store_b._get_meta_path("range").exists(), "failed delete destroyed the .meta.json"

    # A fresh store re-scanning the cache dir still recovers the raster ...
    store_c = DiskBackedImageStore(config=_two_store_config(tmp_path))
    np.testing.assert_array_equal(np.asarray(store_c["range"]), arr)

    # ... and so does the OWNING store, which re-materializes it from disk.
    np.testing.assert_array_equal(np.asarray(store_b["range"]), arr)


def test_adopted_key_delete_purges_shared_pair(tmp_path: Path):
    """A SUCCESSFUL delete purges the shared pair even via the adoption route.

    Companion sensor to the test above, pinning the other construction order.
    The test above builds store_a BEFORE the offload, so store_a never tracks
    the key and the delete takes the KeyError branch. Built AFTER the offload,
    `__init__` re-scans `*.npy` and store_a ADOPTS the key — the delete then
    succeeds and does purge the pair, leaving the offloaded peer unable to
    serve it. That is intended G3 behaviour (a surviving pair would let a store
    re-adopt and serve a stale raster), not the G10 defect, and it is the
    property the docstring now claims. Without this test, swapping two lines of
    setup above would silently reduce the suite to the weaker assertion.
    """
    arr = _gray((6, 6))

    store_b = DiskBackedImageStore(config=_two_store_config(tmp_path))
    store_b.add_image_to_store("range", arr)
    store_b.offload_image_data_to_disk("range")

    store_a = DiskBackedImageStore(config=_two_store_config(tmp_path))
    assert "range" in store_a, "store built after the offload must adopt the key from disk"

    del store_a["range"]  # succeeds — the key is genuinely store_a's to delete

    assert not store_b._get_npy_path("range").exists()
    assert not store_b._get_meta_path("range").exists()
    with pytest.raises(KeyError):
        _ = store_b["range"]  # documented consequence of sharing one cache_path


# --------------------------------------------------------------------------- #
# WR-02 — a store key must never build a path outside the cache directory      #
# (round 3)                                                                    #
#                                                                              #
# `_get_npy_path` / `_get_meta_path` join the raw key onto the cache dir with  #
# no containment check, and 05-14 turned `__delitem__` into an unconditional   #
# `unlink`. Reproduced 2026-07-28 on HEAD with a sentinel one level above the  #
# cache directory: `add_image_to_store("../victim", arr)` +                    #
# `offload_image_data_to_disk` OVERWROTE the sentinel with an NPY header, and  #
# `del store["../victim"]` then DELETED it. Not reachable from the             #
# feature-name DSL (every registered `regex_pattern` anchors on a literal      #
# prefix), but the store is exported from the public barrel.                   #
# --------------------------------------------------------------------------- #
_SENTINEL_BYTES = b"pc2img round-3 containment sentinel -- must not be touched"


def _escape_layout(tmp_path: Path) -> tuple[Path, LazyDiskCacheConfig]:
    """Build a cache subdirectory plus a sentinel file one level ABOVE it.

    The cache directory must be a *subdirectory* of ``tmp_path`` — pointing the
    config straight at ``tmp_path`` would leave an escaping key nowhere to
    escape to and make the reproduction impossible.
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    sentinel = tmp_path / "victim.npy"
    sentinel.write_bytes(_SENTINEL_BYTES)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False)
    return sentinel, cfg


def _escaping_keys(tmp_path: Path) -> dict[str, str]:
    """Three spellings of the same escape, all resolving to ``tmp_path/victim.npy``."""
    return {
        "parent_segment": "../victim",
        "absolute": str(tmp_path / "victim"),
        "embedded_traversal": "a/../../victim",
    }


def test_escaping_key_delete_refuses_and_leaves_outside_file_intact(tmp_path: Path):
    """`del store[escaping_key]` must refuse, and the outside file must survive.

    The key is made tracked through the mapping setter (`store[key] = value`),
    which bypasses `add_data_to_store` entirely — that is the route that makes
    the unlink reachable even once insertion is guarded, so it is the route the
    proving test has to use.

    The 05-14 G10 contract is pinned in the same test: an untracked *ordinary*
    key still raises `KeyError` with no disk side effect.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)

    key = "../victim"
    store[key] = DiskBackedImageData(_gray((4, 4)))
    assert key in store

    with pytest.raises(ValueError):
        del store[key]

    assert sentinel.exists(), "escaping delete removed a file outside the cache directory"
    assert sentinel.read_bytes() == _SENTINEL_BYTES

    # 05-14 G10 contract, unchanged: an untracked ordinary key still raises KeyError.
    with pytest.raises(KeyError):
        del store["never-added"]


@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
def test_escaping_key_add_refuses_before_writing_outside_cache_dir(tmp_path: Path, spelling: str):
    """`add_image_to_store` must refuse before any outside file is created or truncated."""
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    key = _escaping_keys(tmp_path)[spelling]

    with pytest.raises(ValueError):
        store.add_image_to_store(key, _gray((4, 4)))

    assert sentinel.exists(), "escaping insert removed a file outside the cache directory"
    assert sentinel.read_bytes() == _SENTINEL_BYTES, "escaping insert overwrote a file outside the cache directory"


@pytest.mark.parametrize(
    "feature_name",
    [
        "range",
        "rrim_pack_(range,r16,d8,z1.2345678)",
        "hillshade_range_315_45",
        "norm_(range,2,98)",
        "scalar_field_intensity",
        "grad_range_px0.5",
    ],
)
def test_containment_guard_accepts_realistic_feature_names(tmp_path: Path, feature_name: str):
    """Characterization guard: the containment check refuses nothing legitimate.

    Carries NO marker deliberately — it must pass both before and after the
    guard lands, which is what bounds the false-positive risk of adding it.
    """
    _sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    arr = _gray((5, 5))

    store.add_image_to_store(feature_name, arr)
    store.offload_image_data_to_disk(feature_name)

    np.testing.assert_array_equal(np.asarray(store[feature_name]), arr)
