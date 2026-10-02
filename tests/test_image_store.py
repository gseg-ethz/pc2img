"""Proving sensors for the image_cache reparent onto GSEGUtils.

Authored test-first: every sensor here is RED until
`image_cache/` is reparented onto the GSEGUtils primitives
(`DiskBackedNDArray` + `DiskBackedStore`). Tests are pure (no PointCloudData).

- Arithmetic: `DiskBackedImageData` arithmetic must dispatch through the
  inherited `__array_ufunc__` and return a plain `np.ndarray`.
- Security: the store must not carry an arbitrary-object
  deserialization sink; reload goes through the `allow_pickle=False` codec and
  a legacy `.pkl` degrades to a cache miss.
- Blocker sensor: an offload -> reload round-trip through the store
  must return the correct array (fails if the reload class registration is
  unresolved).
"""

import gc
import hashlib
import os
import pickle
import re
import tempfile
import types
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from GSEGUtils.lazy_disk_cache import (
    LazyDiskCacheConfig,
    StoreKeyError,
    StorePurgeRefusedError,
    get_meta_path,
    get_npy_path,
    is_valid_store_key,
)
from GSEGUtils.lazy_disk_cache.paths import get_memmap_path

from pc2img.image_cache import DiskBackedImageData, DiskBackedImageStore

_rng = np.random.default_rng(20260711)


def _gray(shape=(10, 10), dtype=np.float32):
    return _rng.random(shape).astype(dtype)


def test_arithmetic_returns_plain_ndarray():
    """dbid + dbid == arr + arr and the result is a plain ndarray."""
    arr = _gray()
    a = DiskBackedImageData(arr)
    b = DiskBackedImageData(arr)

    result = a + b

    np.testing.assert_array_equal(result, arr + arr)
    assert type(result) is np.ndarray


def test_store_source_has_no_arbitrary_deserialization_sink():
    """Security: the store SOURCE must not call the arbitrary-object load sink.

    We negative-grep the store module source. The forbidden token is assembled
    from a pattern with the ``re.MULTILINE`` flag passed as a ``re.compile``
    argument rather than as a bare literal, since an inline mid-pattern flag
    group (``(?m)``) is rejected by Python's ``re`` module when it does not
    appear at the very start of the pattern.
    """
    import pc2img.image_cache.disk_backed_image_store as store_mod

    src = Path(store_mod.__file__).read_text(encoding="utf-8")
    sink = re.compile(r"pickle\s*\.\s*loads?\s*\(", re.MULTILINE)

    assert sink.search(src) is None, "store source still holds an arbitrary-object load sink"


def test_legacy_pkl_degrades_to_cache_miss(tmp_path: Path):
    """A legacy pickle cache file from before the codec change degrades to a
    cache miss (KeyError), never loaded.

    Renamed (out-of-band from a name collision with a
    mutation check's `-k "escaping or refused"`
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
# Overwrite / purge must remove the on-disk codec pair                        #
#                                                                              #
# `del store[key]` (and `pop` / `popitem` / `clear`) drop only the in-memory   #
# entry, so the `<key>.npy` + `<key>.meta.json` pair stays and a fresh store   #
# re-scans `*.npy` on construction -- it would re-adopt and serve the stale    #
# pre-overwrite raster. The overwrite path therefore calls `purge`, the        #
# upstream delete verb that removes the memmap and the codec pair, whenever    #
# the key is tracked OR any of its derived files is on disk.                   #
# --------------------------------------------------------------------------- #
def test_overwrite_does_not_leave_stale_on_disk_raster(tmp_path: Path):
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store1 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store1.add_image_to_store("range", a)
    store1.offload_image_data_to_disk("range")
    assert get_npy_path(store1.cache_dir, "range").exists()

    # Overwrite the key in the SAME store -- the overwrite purges the old entry's files.
    store1.add_image_to_store("range", b)

    # A fresh store over the same cache_dir must NOT serve the stale pre-overwrite A.
    store2 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    try:
        served = np.asarray(store2["range"])
    except KeyError:
        served = None  # cache miss: A purged, B never offloaded — acceptable
    if served is not None:
        assert not np.array_equal(served, a), "fresh store served the stale pre-overwrite raster"


@pytest.mark.parametrize("route", ["del", "pop", "popitem", "clear"])
def test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store(tmp_path: Path, route: str):
    """Every drop route leaves the codec pair on disk and untracks the key; the
    overwrite must still remove that pair, otherwise a fresh store adopts it and
    serves the pre-overwrite raster as a cache hit."""
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", a)
    store.offload_image_data_to_disk("range")
    assert get_npy_path(store.cache_dir, "range").exists()

    if route == "del":
        del store["range"]
    elif route == "pop":
        store.pop("range")
    elif route == "popitem":
        popped_key, _ = store.popitem()
        assert popped_key == "range"
    else:
        store.clear()
    assert "range" not in store  # tracking dropped, files still on disk
    assert get_npy_path(store.cache_dir, "range").exists()

    store.add_image_to_store("range", b)

    assert not get_npy_path(store.cache_dir, "range").exists(), "stale .npy survived the overwrite"
    assert not get_meta_path(store.cache_dir, "range").exists(), "stale .meta.json survived the overwrite"
    np.testing.assert_array_equal(np.asarray(store["range"]), b)

    fresh = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    if "range" in fresh:
        served = np.asarray(fresh["range"])
        assert not np.array_equal(served, a), "fresh store served the stale pre-overwrite raster"


def test_retained_reference_to_a_dropped_entry_does_not_delete_the_replacement_memmap_on_gc(tmp_path: Path):
    """The dropped entry's cleanup hook must have been detached by the overwrite's
    purge; otherwise it unlinks whatever now occupies its recorded path when the
    caller's retained reference is collected."""
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", a)
    old = store.store["range"]  # strong reference to the entry object
    assert old is not None
    del store["range"]

    store.add_image_to_store("range", b)
    dat = get_memmap_path(store.cache_dir, "range")
    assert dat.exists()

    del old
    gc.collect()

    assert dat.exists(), "collecting the dropped entry deleted the replacement's memmap"
    np.testing.assert_array_equal(np.asarray(store["range"]), b)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork-based process-identity pin")
def test_adding_a_new_key_from_another_process_is_not_refused(tmp_path: Path):
    """The tiled workers add new keys into stores they did not construct on every
    later ``generate()``, so the overwrite route must only ever reach ``purge``
    for a key that is tracked or has files on disk. An EXISTING key from another
    process is still refused: upstream's owner-process rule on ``purge``."""
    a = _gray((6, 6))
    b = (a + 10.0).astype(np.float32)

    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", a)

    def _run_in_child(key: str) -> int:
        pid = os.fork()
        if pid == 0:  # pragma: no cover - runs in the forked child
            try:
                store.add_image_to_store(key, b)
                os._exit(0)
            except StorePurgeRefusedError:
                os._exit(3)
            except BaseException:
                os._exit(4)
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status)

    assert _run_in_child("fresh_key") == 0, "a brand-new key was refused in a non-owner process"
    assert _run_in_child("range") == 3, "an existing key was not refused in a non-owner process"


def test_purge_removes_the_codec_pair_and_the_memmap(tmp_path: Path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6)))
    store.offload_image_data_to_disk("range")
    assert get_npy_path(store.cache_dir, "range").exists()
    assert get_meta_path(store.cache_dir, "range").exists()

    store.purge("range")

    # ``_tmp`` is the test session's tempfile redirect, not part of the cache directory.
    assert sorted(p.name for p in tmp_path.iterdir() if p.name != "_tmp") == []
    assert "range" not in store


def test_delete_tracked_key_without_on_disk_pair_succeeds(tmp_path: Path):
    # A TRACKED key that was never offloaded (no on-disk codec pair) must delete
    # cleanly: upstream `__delitem__` drops tracking only and touches no file, so
    # an absent pair is irrelevant. (The key IS tracked here, just never
    # offloaded; the absent-key contract is pinned by
    # test_failed_delete_preserves_codec_pair_and_both_stores below.)
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6)))
    del store["range"]  # in memory only — no .npy on disk
    assert "range" not in store


# --------------------------------------------------------------------------- #
# A KeyError-raising delete must be a genuine no-op                           #
#                                                                              #
# Upstream's `__delitem__` has no side effect on a KeyError: it drops tracking #
# only and never unlinks. With two stores over one cache directory,            #
# `del A["range"]` raises KeyError and must leave the raster store B owns      #
# untouched -- B cleared its in-memory reference on offload, so if the delete  #
# destroyed the codec pair B itself could no longer serve the key. That would  #
# be live data loss, not a stale-cache concern.                                #
# --------------------------------------------------------------------------- #
def _two_store_config(tmp_path: Path) -> LazyDiskCacheConfig:
    """Shared cache dir; purge_disk_on_gc=False keeps on-disk state deterministic."""
    return LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path, purge_disk_on_gc=False)


def test_failed_delete_preserves_codec_pair_and_both_stores(tmp_path: Path):
    """Pins upstream's no-side-effect-on-KeyError contract; the single absent-key sensor."""
    arr = _gray((6, 6))

    store_a = DiskBackedImageStore(config=_two_store_config(tmp_path))
    store_b = DiskBackedImageStore(config=_two_store_config(tmp_path))

    # Only the pickle-container offload writes the `.npy` + `.meta.json` pair;
    # a plain offload() writes `<key>.dat` and does NOT set up the precondition.
    store_b.add_image_to_store("range", arr)
    store_b.offload_image_data_to_disk("range")
    assert get_npy_path(store_b.cache_dir, "range").exists()
    assert get_meta_path(store_b.cache_dir, "range").exists()

    with pytest.raises(KeyError):
        del store_a["range"]  # A never tracked the key

    # The failed delete must not have touched the shared cache directory.
    assert get_npy_path(store_b.cache_dir, "range").exists(), "failed delete destroyed the .npy"
    assert get_meta_path(store_b.cache_dir, "range").exists(), "failed delete destroyed the .meta.json"

    # A fresh store re-scanning the cache dir still recovers the raster ...
    store_c = DiskBackedImageStore(config=_two_store_config(tmp_path))
    np.testing.assert_array_equal(np.asarray(store_c["range"]), arr)

    # ... and so does the OWNING store, which re-materializes it from disk.
    np.testing.assert_array_equal(np.asarray(store_b["range"]), arr)


def test_adopted_key_purge_removes_shared_pair(tmp_path: Path):
    """A SUCCESSFUL purge removes the shared pair even via the adoption route.

    Companion sensor to the test above, pinning the other construction order.
    The test above builds store_a BEFORE the offload, so store_a never tracks
    the key and the delete takes the KeyError branch. Built AFTER the offload,
    `__init__` re-scans `*.npy` and store_a ADOPTS the key -- `purge` then
    succeeds and removes the pair, leaving the offloaded peer unable to serve
    it. That is the intended purge semantics (a surviving pair would let a
    store re-adopt and serve a stale raster) and a reason two stores must not
    share one `cache_path` unless the caller wants exactly that aliasing.
    Without this test, swapping two lines of setup above would silently reduce
    the suite to the weaker assertion.
    """
    arr = _gray((6, 6))

    store_b = DiskBackedImageStore(config=_two_store_config(tmp_path))
    store_b.add_image_to_store("range", arr)
    store_b.offload_image_data_to_disk("range")

    store_a = DiskBackedImageStore(config=_two_store_config(tmp_path))
    assert "range" in store_a, "store built after the offload must adopt the key from disk"

    store_a.purge("range")  # succeeds -- the key is genuinely store_a's to purge

    assert not get_npy_path(store_b.cache_dir, "range").exists()
    assert not get_meta_path(store_b.cache_dir, "range").exists()
    with pytest.raises(KeyError):
        _ = store_b["range"]  # documented consequence of sharing one cache_path


# --------------------------------------------------------------------------- #
# A store key must never build a path outside the cache directory             #
#                                                                              #
# The key-derived path builders upstream validates the key and verifies        #
# containment, and the mapping setter refuses an escaping key at set time.     #
# Reproduced on the previous GSEGUtils release with a sentinel one level above #
# the cache directory: `add_image_to_store("../victim", arr)` +                #
# `offload_image_data_to_disk` OVERWROTE the sentinel with an NPY header.      #
# Scalar-field names come from point-cloud file metadata and reach the store   #
# verbatim through `FeatureRegistry.match`'s unanchored default fallback, so   #
# the refusal is load-bearing, not defence-in-depth.                           #
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
    # An embedded-traversal key (``a/../../victim``) can only resolve past the
    # cache directory when its first segment exists, so create it.
    (cache_dir / "a").mkdir()
    sentinel = tmp_path / "victim.npy"
    sentinel.write_bytes(_SENTINEL_BYTES)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False)
    return sentinel, cfg


def _escaping_keys(tmp_path: Path) -> dict[str, str]:
    """Spellings a store key must never be allowed to take.

    The first three resolve to ``tmp_path/victim.npy``, above the cache
    directory. ``empty``, ``dot`` and ``dotdot`` resolve onto the cache
    directory itself. ``nested`` stays inside the cache directory but carries a
    path separator, and a legal store key is a single path segment.
    """
    return {
        "parent_segment": "../victim",
        "absolute": str(tmp_path / "victim"),
        "embedded_traversal": "a/../../victim",
        "nested": "sub/nested",
        "empty": "",
        "dot": ".",
        "dotdot": "..",
    }


def _tree(root: Path) -> dict[str, object]:
    """Snapshot every path under ``root`` without following any link.

    A symlink is recorded by its target (``os.readlink``) and never opened, so a
    dangling or escaping link cannot make the snapshot itself raise. Anything
    under a top-level ``_tmp`` directory is skipped: that is where the test
    session's ``tempfile`` default is redirected, and it is not part of the
    cache directory or its surroundings.
    """
    snapshot: dict[str, object] = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if rel.parts[0] == "_tmp":
            continue
        key = rel.as_posix()
        if path.is_symlink():
            snapshot[key] = ("symlink", os.readlink(path))
        elif path.is_dir():
            snapshot[key] = None
        else:
            snapshot[key] = path.read_bytes()
    return snapshot


def test_tree_snapshot_records_links_by_target_and_survives_a_dangling_one(tmp_path: Path):
    (tmp_path / "file.bin").write_bytes(b"abc")
    (tmp_path / "dir").mkdir()
    (tmp_path / "dangling").symlink_to(tmp_path / "does-not-exist")
    (tmp_path / "_tmp").mkdir(exist_ok=True)  # the session's tempfile redirect target
    (tmp_path / "_tmp" / "litter").write_bytes(b"ignored")

    assert _tree(tmp_path) == {
        "file.bin": b"abc",
        "dir": None,
        "dangling": ("symlink", str(tmp_path / "does-not-exist")),
    }


@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
def test_escaping_key_setter_refuses_and_key_is_never_tracked(tmp_path: Path, spelling: str):
    """`store[escaping_key] = value` must refuse at set time, and the outside file must survive.

    The mapping setter bypasses `add_data_to_store`, so it is its own insertion
    route. Upstream validates the key there: the refusal is a `ValueError`, the
    key is never tracked (so no later delete or offload can reach the outside
    path), and the sentinel one level above the cache directory is untouched.
    An untracked *ordinary* key still raises `KeyError` on delete with no disk
    side effect.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)

    key = _escaping_keys(tmp_path)[spelling]
    with pytest.raises(ValueError):
        store[key] = DiskBackedImageData(_gray((4, 4)))

    assert key not in store, "a refused setter insertion still tracked the key"
    assert sentinel.exists(), "escaping insertion removed a file outside the cache directory"
    assert sentinel.read_bytes() == _SENTINEL_BYTES

    # Unchanged contract: an untracked ordinary key still raises KeyError.
    with pytest.raises(KeyError):
        del store["never-added"]


@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
def test_escaping_key_add_refuses_before_writing_outside_cache_dir(tmp_path: Path, spelling: str):
    """`add_image_to_store` must refuse before any outside file is created or truncated.

    ``offload_image_data_to_disk`` runs INSIDE the ``pytest.raises`` block,
    directly after ``add_image_to_store``: with the
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


# The six ways a key reaches the disk. Each runs with a store built on the
# escape layout, so a stray write anywhere under ``tmp_path`` shows up in the
# snapshot taken before the call.
def _route_add(store: DiskBackedImageStore, key: str) -> None:
    store.add_image_to_store(key, _gray((4, 4)))


def _route_setitem(store: DiskBackedImageStore, key: str) -> None:
    store[key] = DiskBackedImageData(_gray((4, 4)))


def _route_add_then_offload(store: DiskBackedImageStore, key: str) -> None:
    store.add_image_to_store(key, _gray((4, 4)))
    store.offload_image_data_to_disk(key)


def _route_purge(store: DiskBackedImageStore, key: str) -> None:
    store.purge(key)


def _route_getitem(store: DiskBackedImageStore, key: str) -> None:
    _ = store[key]


def _route_add_data(store: DiskBackedImageStore, key: str) -> None:
    store.add_data_to_store(key, _gray((4, 4)))


_ROUTES: dict[str, Callable[[DiskBackedImageStore, str], None]] = {
    "add": _route_add,
    "setitem": _route_setitem,
    "add_then_offload": _route_add_then_offload,
    "purge": _route_purge,
    "getitem": _route_getitem,
    "add_data": _route_add_data,
}


@pytest.mark.parametrize("route", list(_ROUTES))
@pytest.mark.parametrize("spelling", list(_escaping_keys(Path("/unused"))))
def test_escaping_key_refused_on_every_route_and_nothing_written_anywhere(tmp_path: Path, spelling: str, route: str):
    """Every refused spelling leaves the WHOLE temp tree bit-identical, on every route.

    The snapshot covers the cache directory, the sentinel above it and anything
    else under ``tmp_path``, so a stray file anywhere (not only the one path a
    known exploit targeted) fails the comparison. The ``nested`` spelling pins
    that nesting under the cache directory is no longer an accepted key.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    key = _escaping_keys(tmp_path)[spelling]
    before = _tree(tmp_path)

    with pytest.raises(ValueError):
        _ROUTES[route](store, key)

    assert _tree(tmp_path) == before, "a refused key changed the temp tree"
    assert key not in store, "a refused key was tracked"
    assert sentinel.read_bytes() == _SENTINEL_BYTES


def test_escaping_key_with_bad_shape_is_refused_by_containment_not_shape(tmp_path: Path):
    """An escaping key with a bad-shape raster raises the key error, not ``AssertionError``.

    The key check precedes the shape check in ``add_image_to_store``. This is the
    one test that pins the upstream subtype; everywhere else the asserted public
    contract is ``ValueError``.
    """
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)

    with pytest.raises(ValueError) as excinfo:
        store.add_image_to_store("../victim", np.ones(4, dtype=np.float32))

    assert isinstance(excinfo.value, StoreKeyError)
    assert sentinel.read_bytes() == _SENTINEL_BYTES


def test_del_drops_tracking_only_and_an_offloaded_key_is_readopted(tmp_path: Path):
    arr = _gray((6, 6))
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", arr)
    store.offload_image_data_to_disk("range")

    del store["range"]

    assert get_npy_path(store.cache_dir, "range").exists()
    assert get_meta_path(store.cache_dir, "range").exists()
    np.testing.assert_array_equal(np.asarray(store["range"]), arr)  # re-adopted on read

    fresh = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    assert "range" in fresh


def test_store_mapping_is_read_only(tmp_path: Path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((4, 4)))

    with pytest.raises(TypeError):
        store.store["x"] = DiskBackedImageData(_gray((2, 2)))  # type: ignore[index]
    with pytest.raises(TypeError):
        del store.store["range"]  # type: ignore[attr-defined]

    assert isinstance(store.image_data, types.MappingProxyType)
    assert "x" not in store
    assert "range" in store


# --------------------------------------------------------------------------- #
# The key rule is upstream's; these characterize it over the names pc2img     #
# produces. No pc2img code checks any of this.                                 #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name",
    [
        "range",
        "aspect",
        "slope_deg",
        "hillshade_range_315_45",
        "grad_range_px0.5",
        "norm_(range,2,98)",
        "rrim_pack_(range,r16,d8,z1.2345678)",
        "rrim_pack_(range,r16,d8,z1e-05)",
        "rrim_component_(structure,range,r16,d8)",
        "scalar_field_intensity",
        "scalar_field_Scalar field",
        "tile_03",
        "tile-3",
        "0_0",
        "x_-1_-1",
        "0",
        "1.5",
        "tile 03",
        hashlib.sha256(b"tile").hexdigest(),
        "triangles",
        "simplices",
        "verts",
        "bary",
    ],
)
def test_realistic_keys_and_segments_are_legal_upstream(name: str):
    assert is_valid_store_key(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "CON",
        "tile_03/range",
        "tile_03.",
        "scalar_field_a/b",
        "scalar_field_a\\b",
        "scalar_field_GPS:time",
        "scalar_field_x.",
    ],
)
def test_hostile_keys_and_segments_are_refused_upstream(name: str):
    assert not is_valid_store_key(name)


def test_empty_raster_overwrite_is_accepted(tmp_path: Path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((4, 4)))

    store.add_image_to_store("range", np.empty((0, 0), dtype=np.float32))

    assert np.asarray(store["range"]).shape == (0, 0)


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
    round trip too, so this test bounds both
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
# Validate-before-purge overwrite: a failed overwrite must leave the          #
# existing entry and its codec pair fully intact, in memory and on disk       #
#                                                                              #
# `add_image_to_store` validates the key (containment) and then the raster    #
# shape BEFORE it purges the existing entry, so a rejected overwrite destroys  #
# nothing. The replacement is only built after the purge: building it on the  #
# shared `<key>.dat` path while the old entry is still tracked would clobber   #
# the old entry's live buffer at construction.                                 #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("offloaded", [False, True], ids=["in_memory", "codec_offloaded"])
def test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact(tmp_path: Path, offloaded: bool):
    """A failed overwrite (bad raster shape) is a full no-op on the existing entry.

    The exception type is pinned deliberately: a bad raster shape raises
    `AssertionError` (the rule is enforced by `_assert_image_shape`, called
    both from the store's `add_image_to_store` and from
    `DiskBackedImageData.__init__`), and this test locks that type — changing
    it would be a breaking-change event that is not opened here.
    """
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    original = _gray((4, 4))
    store.add_image_to_store("range", original)
    if offloaded:
        store.offload_image_data_to_disk("range")
        assert get_npy_path(store.cache_dir, "range").exists()
        assert get_meta_path(store.cache_dir, "range").exists()

    with pytest.raises(AssertionError):
        store.add_image_to_store("range", np.ones(4, dtype=np.float32))

    assert "range" in store
    np.testing.assert_array_equal(np.asarray(store["range"]), original)
    if offloaded:
        assert get_npy_path(store.cache_dir, "range").exists()
        assert get_meta_path(store.cache_dir, "range").exists()


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
    assert get_npy_path(store1.cache_dir, "range").exists()
    assert get_meta_path(store1.cache_dir, "range").exists()

    store2 = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    np.testing.assert_array_equal(np.asarray(store2["range"]), b)


# --------------------------------------------------------------------------- #
# A legitimate symlinked cache entry must be served, not refused, while       #
# every escaping key stays refused                                            #
#                                                                              #
# A cache directory holding `<key>.npy` + `<key>.meta.json` as symlinks to a  #
# real codec pair elsewhere is adopted by `__init__` (the adoption scan uses   #
# `Path.is_file()`, which follows symlinks) and must be served and unpickled.  #
# `purge` follows each link to its resolved target: it refuses an outside      #
# target (a foreign artefact it may not touch) and, for a target inside the    #
# cache directory, removes the link and the payload it points at.              #
# --------------------------------------------------------------------------- #
def _symlinked_entry_layout(tmp_path: Path, *, shared_inside_cache: bool = False) -> tuple[Path, Path, np.ndarray]:
    """Real codec pair in ``shared/``; ``cache/`` holds only symlinks to it.

    ``shared/`` sits next to ``cache/`` by default (an OUTSIDE target) or, with
    ``shared_inside_cache``, below it (an INSIDE target).
    """
    cache = tmp_path / "cache"
    cache.mkdir()
    shared = cache / "shared" if shared_inside_cache else tmp_path / "shared"
    shared.mkdir()

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

    # Every escape spelling is refused by the upstream key-derived path builder.
    # A fresh subdirectory avoids colliding with the "cache" / "shared" dirs above.
    escape_root = tmp_path / "escape_root"
    escape_root.mkdir()
    sentinel, escape_cfg = _escape_layout(escape_root)
    escape_store = DiskBackedImageStore(config=escape_cfg)
    for key in _escaping_keys(escape_root).values():
        with pytest.raises(ValueError):
            get_npy_path(escape_store.cache_dir, key)
    assert sentinel.exists()
    assert sentinel.read_bytes() == _SENTINEL_BYTES

    # Nesting is refused too: a legal store key is a single path segment.
    with pytest.raises(ValueError):
        get_npy_path(escape_store.cache_dir, "sub/nested")


def test_symlinked_entry_with_outside_target_purge_is_refused(tmp_path: Path):
    """`purge` must not follow a cache-internal link to a target outside the cache directory."""
    shared, cache, arr = _symlinked_entry_layout(tmp_path)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False)
    store = DiskBackedImageStore(config=cfg)
    assert "range" in store

    with pytest.raises(StorePurgeRefusedError):
        store.purge("range")

    # A refused purge touches nothing: both links, both payload files, and the entry survive.
    assert (cache / "range.npy").is_symlink()
    assert (cache / "range.meta.json").is_symlink()
    assert (shared / "range.npy").exists(), "a refused purge removed the outside target"
    assert (shared / "range.meta.json").exists(), "a refused purge removed the outside target"
    np.testing.assert_array_equal(np.asarray(store["range"]), arr)


def test_symlinked_entry_with_inside_target_purge_removes_link_and_payload(tmp_path: Path):
    """`purge` of a link whose target is inside the cache directory removes the link AND its payload."""
    shared, cache, _ = _symlinked_entry_layout(tmp_path, shared_inside_cache=True)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False)
    store = DiskBackedImageStore(config=cfg)
    assert "range" in store

    store.purge("range")

    assert not (cache / "range.npy").exists()
    assert not (cache / "range.npy").is_symlink(), "purge left the link behind"
    assert not (cache / "range.meta.json").is_symlink(), "purge left the link behind"
    assert not (shared / "range.npy").exists(), "purge left the payload the link pointed at"
    assert not (shared / "range.meta.json").exists(), "purge left the payload the link pointed at"
    assert "range" not in store


# --------------------------------------------------------------------------- #
# The key-derived path builders and entry-supplied paths are different things  #
#                                                                              #
# An entry inserted through the mapping setter (`store[key] = value`) carries #
# its own `cache_path`, chosen by the caller and never routed through the     #
# validated key-derived path builders. `offload()` with the default           #
# `pickle_container=False` writes through the ENTRY's own `_cache_path`. A     #
# file outside the cache directory was overwritten with raster bytes through   #
# such a store-inserted entry. Enforcing containment on an entry's own path    #
# is upstream's concern and is not extended here -- the class docstring states #
# the limit, including that `purge` and the overwrite in `add_image_to_store`  #
# refuse such an entry -- so this test pins the enforced half: an entry        #
# inserted through `add_image_to_store` always carries a `cache_path` under    #
# the cache directory (because that route derives it from the validated path   #
# builder).                                                                    #
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
# Constructor default is a None-sentinel, not a shared mutable                #
# LazyDiskCacheConfig() instance, matching the same pattern used at other     #
# generator/manager sites                                                     #
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
