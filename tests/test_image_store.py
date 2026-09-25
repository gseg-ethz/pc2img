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
import tempfile
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


def test_legacy_pkl_degrades_to_cache_miss(tmp_path: Path):
    """A legacy pre-Phase-2 `.pkl` degrades to a cache miss (KeyError), never loaded.

    Renamed (round 4, out-of-band from a name collision with the
    review-r2-af50d770d73d mutation check's `-k "escaping or refused"`
    filter): this test's KeyError comes from the legacy-.pkl refusal path,
    not the containment guard, so it must stay guard-INsensitive and out of
    that selection. No behaviour change.
    """
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


def test_delete_tracked_key_without_on_disk_pair_succeeds(tmp_path: Path):
    # A TRACKED key that was never offloaded (no on-disk codec pair) must delete
    # cleanly: unlink(missing_ok=True) carries the safety, not a
    # cache_dir-is-None guard. (review-r1-c2b69f0885e7: renamed from the prior
    # test name, which misdescribed this body — the key IS tracked here, just
    # never offloaded; the genuinely absent-key contract is pinned separately
    # by test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op below.)
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6)))
    del store["range"]  # in memory only — no .npy on disk
    assert "range" not in store


def test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op(tmp_path: Path):
    """A key that was NEVER added must raise KeyError and leave the cache dir untouched (G10).

    A codec pair for "never-added" sits on disk (planted by a peer store,
    constructed AFTER this store so it is never adopted), which is what makes
    the sensor decide something: under an unlink-first delete ordering the
    KeyError still fires, but the codec pair is destroyed first. Distinguishes
    from test_failed_delete_preserves_codec_pair_and_both_stores below: this
    one pins the minimal statement (an absent key, a pair on disk, a single
    non-owning store, no re-materialisation); the two-store sensor pins the
    live-data-loss consequence across two owning stores.
    """
    store = DiskBackedImageStore(config=_two_store_config(tmp_path))

    # Planted by a peer store constructed AFTER `store`, so `store` never
    # adopts "never-added" -- the key is genuinely absent from `store`.
    peer = DiskBackedImageStore(config=_two_store_config(tmp_path))
    peer.add_image_to_store("never-added", _gray((4, 4)))
    peer.offload_image_data_to_disk("never-added")
    assert peer._get_npy_path("never-added").exists()
    assert peer._get_meta_path("never-added").exists()
    assert "never-added" not in store

    before = sorted(p.name for p in tmp_path.iterdir())

    with pytest.raises(KeyError):
        del store["never-added"]

    after = sorted(p.name for p in tmp_path.iterdir())
    assert after == before
    assert peer._get_npy_path("never-added").exists()
    assert peer._get_meta_path("never-added").exists()


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
# `del store["../victim"]` then DELETED it. Reachability corrected round 4:   #
# see the store docstring's threat-posture paragraph and                      #
# `FeatureRegistry.match`'s unanchored default fallback (review-r2-1a435f-    #
# 413f18) — the guard is load-bearing, not defence-in-depth, on the           #
# installed GSEGUtils 0.5.x.                                                  #
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


@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
def test_escaping_key_delete_refuses_and_leaves_outside_file_intact(tmp_path: Path, spelling: str):
    """`del store[escaping_key]` must refuse, and the outside file must survive.

    The key is made tracked through the mapping setter (`store[key] = value`),
    which bypasses `add_data_to_store` entirely — that is the route that makes
    the unlink reachable even once insertion is guarded, so it is the route the
    proving test has to use.

    Carries the union of two contracts: the entry survives a refused delete
    byte-identical to what was inserted (ValueError, membership, array
    equality, sentinel existence + bytes), AND an untracked *ordinary* key
    still raises `KeyError` with no disk side effect (the 05-14 G10 contract).
    Parametrised over the same three escape spellings as the add proving test.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)

    key = _escaping_keys(tmp_path)[spelling]
    original = _gray((4, 4))
    store[key] = DiskBackedImageData(original)
    assert key in store

    with pytest.raises(ValueError):
        del store[key]

    assert key in store, "a refused delete dropped the key from the store"
    np.testing.assert_array_equal(np.asarray(store[key]), original)
    assert sentinel.exists(), "escaping delete removed a file outside the cache directory"
    assert sentinel.read_bytes() == _SENTINEL_BYTES

    # 05-14 G10 contract, unchanged: an untracked ordinary key still raises KeyError.
    with pytest.raises(KeyError):
        del store["never-added"]


@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
def test_escaping_key_add_refuses_before_writing_outside_cache_dir(tmp_path: Path, spelling: str):
    """`add_image_to_store` must refuse before any outside file is created or truncated.

    ``offload_image_data_to_disk`` runs INSIDE the ``pytest.raises`` block,
    directly after ``add_image_to_store`` (review-r2-af50d770d73d): with the
    guard live, ``add_image_to_store`` raises first and the offload call is
    never reached. With the guard disabled (mutation check), insertion alone
    never writes — only reaching ``offload_image_data_to_disk`` and having IT
    raise (or fail to) makes this test guard-sensitive; without the guard the
    offload succeeds, nothing is raised, and ``pytest.raises`` itself fails
    the test with "DID NOT RAISE".
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    key = _escaping_keys(tmp_path)[spelling]

    with pytest.raises(ValueError):
        store.add_image_to_store(key, _gray((4, 4)))
        store.offload_image_data_to_disk(key)

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
    The sentinel outside the cache directory is asserted intact after the
    round trip too (review-r2-e3a76c7d3fd0), so this test bounds both
    false-positive refusals AND stray writes.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    arr = _gray((5, 5))

    store.add_image_to_store(feature_name, arr)
    store.offload_image_data_to_disk(feature_name)

    np.testing.assert_array_equal(np.asarray(store[feature_name]), arr)
    assert sentinel.exists()
    assert sentinel.read_bytes() == _SENTINEL_BYTES


# --------------------------------------------------------------------------- #
# A refused delete must be a full no-op, in memory as well as on disk, on the #
# OVERWRITE route too                                                        #
#                                                                              #
# The delete-side sensor for this contract lives in                          #
# test_escaping_key_delete_refuses_and_leaves_outside_file_intact above (it   #
# now carries the union of both predecessors' assertions). This block covers #
# the remaining half: add_image_to_store's overwrite path must not drop the  #
# existing entry before the replacement is validated.                        #
# --------------------------------------------------------------------------- #


def test_refused_overwrite_leaves_existing_entry_intact(tmp_path: Path):
    """A refused overwrite (`add_image_to_store` on an escaping key) must not drop the old entry."""
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    key = _escaping_keys(tmp_path)["parent_segment"]
    original = _gray((4, 4))
    replacement = (original + 10.0).astype(np.float32)
    store[key] = DiskBackedImageData(original)

    with pytest.raises(ValueError):
        store.add_image_to_store(key, replacement)

    assert key in store, "a refused overwrite dropped the existing entry"
    np.testing.assert_array_equal(np.asarray(store[key]), original)
    assert sentinel.exists(), "refused overwrite removed a file outside the cache directory"
    assert sentinel.read_bytes() == _SENTINEL_BYTES


# --------------------------------------------------------------------------- #
# WR-07 (round 5) — a failed overwrite must leave the existing entry and its   #
# codec pair fully intact, in memory and on disk                              #
#                                                                              #
# `add_image_to_store` used to drop the existing key (`del self[img_name]`)   #
# before the replacement's raster shape was validated, so a bad-shape         #
# overwrite destroyed the entry it was meant to replace. The safe fix is      #
# validate (containment, then shape) -> delete -> build: building the         #
# replacement on the shared `<key>.dat` path BEFORE the old entry is dropped  #
# was also measured and rejected — it clobbers the old entry's live buffer at #
# construction, and the old entry's path-bound finalizer later unlinks the    #
# just-built replacement's `.dat` when the old object is collected.          #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("offloaded", [False, True], ids=["in_memory", "codec_offloaded"])
def test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact(tmp_path: Path, offloaded: bool):
    """A failed overwrite (bad raster shape) is a full no-op on the existing entry.

    The exception type is pinned deliberately: a bad raster shape raises
    `AssertionError` (the rule lives in `DiskBackedImageData.__init__`), and
    this test locks that type — changing it would be a breaking-change event
    this gap round does not open.
    """
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    original = _gray((4, 4))
    store.add_image_to_store("range", original)
    if offloaded:
        store.offload_image_data_to_disk("range")
        assert store._get_npy_path("range").exists()
        assert store._get_meta_path("range").exists()

    with pytest.raises(AssertionError):
        store.add_image_to_store("range", np.ones(4, dtype=np.float32))

    assert "range" in store
    np.testing.assert_array_equal(np.asarray(store["range"]), original)
    if offloaded:
        assert store._get_npy_path("range").exists()
        assert store._get_meta_path("range").exists()


def test_successful_overwrite_serves_the_replacement_after_offload_and_reload(tmp_path: Path):
    """Characterization: a successful overwrite still round-trips after the reorder.

    The replacement must be served after offload and reload from the SAME
    store, and from a FRESH store re-scanning the same cache directory.
    """
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store1 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store1.add_image_to_store("range", a)
    store1.offload_image_data_to_disk("range")

    store1.add_image_to_store("range", b)
    store1.offload_image_data_to_disk("range")

    np.testing.assert_array_equal(np.asarray(store1["range"]), b)
    assert store1._get_npy_path("range").exists()
    assert store1._get_meta_path("range").exists()

    store2 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    np.testing.assert_array_equal(np.asarray(store2["range"]), b)


# --------------------------------------------------------------------------- #
# review-r2-9998f2b36d4c (round 4) — a legitimate symlinked cache entry must   #
# be served, not refused, while every escaping key stays refused              #
#                                                                              #
# `_assert_within_cache_dir` resolves the FULL path, which follows the final  #
# component's own symlink. A cache directory holding `<key>.npy` +            #
# `<key>.meta.json` as symlinks to a real codec pair elsewhere is adopted by  #
# `__init__` (the adoption scan uses `Path.is_file()`, which follows          #
# symlinks) but then refused on read, delete and store-unpickling, because    #
# the resolved candidate lands outside the cache directory even though the   #
# LINK itself sits inside it. Reproduced 2026-09-24.                          #
# --------------------------------------------------------------------------- #
def _symlinked_entry_layout(tmp_path: Path) -> tuple[Path, Path, np.ndarray]:
    """Real codec pair in ``shared/``; ``cache/`` holds only symlinks to it."""
    shared = tmp_path / "shared"
    shared.mkdir()
    cache = tmp_path / "cache"
    cache.mkdir()

    arr = _gray((4, 4))
    shared_store = DiskBackedImageStore(
        config=LazyDiskCacheConfig(enable_caching=True, cache_path=shared, purge_disk_on_gc=False)
    )
    shared_store.add_image_to_store("range", arr)
    shared_store.offload_image_data_to_disk("range")

    (cache / "range.npy").symlink_to(shared / "range.npy")
    (cache / "range.meta.json").symlink_to(shared / "range.meta.json")
    return shared, cache, arr


def test_symlinked_cache_entry_is_served_and_unpickles(tmp_path: Path):
    """A cache-directory-internal symlink to a real codec pair must be served, not refused."""
    shared, cache, arr = _symlinked_entry_layout(tmp_path)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False)
    store = DiskBackedImageStore(config=cfg)

    assert "range" in store, "the adoption scan must still adopt a symlinked codec pair"
    np.testing.assert_array_equal(np.asarray(store["range"]), arr)

    restored = pickle.loads(pickle.dumps(store))
    np.testing.assert_array_equal(np.asarray(restored["range"]), arr)

    # A fresh store for the delete assertion: reading/pickling above may have
    # offloaded the in-memory entry again, and delete must only remove the LINK.
    store2 = DiskBackedImageStore(config=cfg)
    del store2["range"]
    assert not (cache / "range.npy").exists(), "delete must remove the link inside the cache dir"
    assert not (cache / "range.meta.json").exists()
    assert (shared / "range.npy").exists(), "delete of a symlinked entry must not remove its target"
    assert (shared / "range.meta.json").exists()

    # The three escape spellings must still be refused under the rewritten predicate.
    # A fresh subdirectory avoids colliding with the "cache" / "shared" dirs above.
    escape_root = tmp_path / "escape_root"
    escape_root.mkdir()
    sentinel, escape_cfg = _escape_layout(escape_root)
    escape_store = DiskBackedImageStore(config=escape_cfg)
    for key in _escaping_keys(escape_root).values():
        with pytest.raises(ValueError):
            escape_store._get_npy_path(key)
    assert sentinel.exists()
    assert sentinel.read_bytes() == _SENTINEL_BYTES

    # Nesting under the cache directory must still resolve inside.
    nested = escape_store._get_npy_path("sub/nested")
    assert nested.is_relative_to(escape_store.cache_dir.resolve())


# --------------------------------------------------------------------------- #
# review-r2-3f625b03fb03 (round 4) — the containment invariant is about       #
# key-derived paths, not entry-supplied ones                                  #
#                                                                              #
# An entry inserted through the mapping setter (`store[key] = value`) carries #
# its own `cache_path`, chosen by the caller and never routed through the     #
# guarded `_get_npy_path` / `_get_meta_path` builders. `offload()` with the   #
# default `pickle_container=False` writes through the ENTRY's own            #
# `_cache_path`. Reproduced 2026-09-24 via a STORE-INSERTED entry (not a      #
# directly constructed one, whose offload is a no-op): a file outside the     #
# cache directory was overwritten with raster bytes. This is NOT extended     #
# into enforcement (owner decision, D-R4-01 #5) — the docstring is narrowed   #
# to what the key builders actually enforce, and this test pins the enforced  #
# half: an entry inserted through `add_image_to_store` always carries a       #
# `cache_path` under the cache directory (because that route derives it from  #
# the guarded `_get_npy_path`).                                               #
# --------------------------------------------------------------------------- #
def test_store_inserted_entries_carry_a_cache_path_under_the_cache_dir(tmp_path: Path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((4, 4)))

    entry = store.store["range"]
    assert entry is not None
    # LazyDiskCache re-suffixes the handed-in `.npy` path to `.dat`, so only
    # parent + stem are stable across that internal rewrite.
    assert entry.cache_path.parent == store.cache_dir
    assert entry.cache_path.stem == "range"


# --------------------------------------------------------------------------- #
# review-r1-8ff7171c6ca4 (IN-03, round 4) — constructor default is a          #
# None-sentinel, not a shared mutable LazyDiskCacheConfig() instance (DSN-07  #
# pattern, matching the 05-10/05-11 sweep at other generator/manager sites)   #
# --------------------------------------------------------------------------- #
def test_default_config_is_coerced_from_none_sentinel(tmp_path: Path, monkeypatch):
    """`DiskBackedImageStore()` and `DiskBackedImageStore(config=None)` behave identically.

    A `tmp_path`-backed config cannot be used here — that would route through
    the explicit-`cache_path` branch and skip the None-sentinel path entirely.
    Instead `tempfile.tempdir` is redirected to `tmp_path` BEFORE either store
    is constructed, so `tempfile.mkdtemp(dir=None)` (the base store's
    None-`cache_path` branch) lands inside pytest's own tree rather than the
    system temp directory, and `cache_dir.parent == tmp_path` proves the
    mkdtemp route was actually taken, not bypassed.
    """
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    default_cfg = LazyDiskCacheConfig()

    store = DiskBackedImageStore()
    assert isinstance(store.cache_dir, Path)
    assert store._enable_caching == default_cfg.enable_caching
    assert store.cache_dir.parent == tmp_path

    store2 = DiskBackedImageStore(config=None)
    assert isinstance(store2.cache_dir, Path)
    assert store2._enable_caching == default_cfg.enable_caching
    assert store2.cache_dir.parent == tmp_path
