"""Tiled-orchestration sensors.

Covers the ``tiled_generator`` findings:

* **extend_cache_paths dict-assignment** — ``TIGSettings.extend_cache_paths`` must *preserve* the
  per-tile ``interp_kwargs`` when it rewrites the nested cache path. The original
  code assigned the return value of ``dict.update()`` (always ``None``), so the
  extended settings silently dropped every interpolation kwarg — the exact
  opposite of intent. Because ``TIGSettings`` is a frozen pydantic dataclass,
  the ``None`` re-triggers validation and surfaces as loss (a ``ValidationError``
  today), so the proving test simply asserts the post-fix contract.
* **Import-order safety** — ``pc2img.tiled_generator`` imports ``PointCloudImageGenerator``
  from the defining module (``pc2img.core``) rather than the package barrel, so
  importing the submodule *first* in a fresh interpreter cannot trip a
  partially-initialized-module ``ImportError``.

The tests build a real ``PointCloudData`` only where needed; the settings-level
checks are pure-object, keeping them deterministic and CI-safe. The fan-out tests are:
the regression test that repeats ``generate()`` on one instance at ``n_jobs=1`` and
``n_jobs=2``, rebinds the result and reads every raster and store entry (the pooled case
spawns real loky processes); the mixed-sequence sensor, which changes ``n_jobs`` between calls
(``1`` then ``2``, ``1`` then ``-1``, ``2`` then ``1`` then ``2``), reads every raster after each
call and every store entry after ``store.offload()``; the flag test that pins
purge-on-garbage-collection off for returned entries and store entries at both ``n_jobs=1`` and
``n_jobs=2``; the failing-tile tests, which check that a pooled call that raises drops the tile
generators so the retry succeeds, and that a sequential failure drops nothing; the duplicate-id
test; the shape test, which replaces the pool with a recorder and runs inline; and the pin test
for worker-owned stores, which also spawns real loky processes; and the sensor for the refusal
trigger and the ``n_jobs=1`` workaround, which runs a pooled call first and then a sequential one.
"""

from __future__ import annotations

import gc
import pickle
import subprocess
import sys

import numpy as np
import pytest
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, StorePurgeRefusedError, get_npy_path
from GSEGUtils.lazy_disk_cache.paths import get_memmap_path, get_memmap_tmp_path

import pc2img.tiled_generator as tiled_module
from pc2img.core import ImgRes, PointCloudImageGenerator
from pc2img.tiled_generator import PointCloudTile, TIGSettings, TiledPointCloudImageGenerator


def _settings_with_nested_cache_cfg() -> TIGSettings:
    """A ``TIGSettings`` whose ``interp_kwargs`` carries a nested cache config."""
    return TIGSettings(
        img_res=ImgRes(4, 4),
        proj_cls="spherical",
        interp_cls="linear",
        interp_kwargs={"lazy_disk_cache_config": LazyDiskCacheConfig()},
    )


def test_extend_cache_paths_preserves_interp_kwargs() -> None:
    """Extending the cache path must keep ``interp_kwargs`` a live dict.

    The extended settings must still expose ``interp_kwargs`` as a dict whose
    nested ``lazy_disk_cache_config`` is a (path-extended) ``LazyDiskCacheConfig``
    — never ``None`` and never silently dropped.
    """
    settings = _settings_with_nested_cache_cfg()

    extended = settings.extend_cache_paths("tile-0")

    assert isinstance(extended.interp_kwargs, dict)
    nested = extended.interp_kwargs.get("lazy_disk_cache_config")
    assert isinstance(nested, LazyDiskCacheConfig)


def test_tiled_generator_imports_first_in_fresh_interpreter() -> None:
    """Importing the submodule first must not raise on a barrel cycle.

    Runs in a clean subprocess so ``pc2img.tiled_generator`` is genuinely the
    first ``pc2img`` submodule imported — the ordering that would expose a
    partially-initialized-module ``ImportError`` if the module reached back
    through the package barrel for ``PointCloudImageGenerator``.
    """
    proc = subprocess.run(
        [sys.executable, "-c", "import pc2img.tiled_generator"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"fresh import failed:\n{proc.stderr}"


def test_extend_cache_paths_refuses_a_traversing_folder_name() -> None:
    """A folder name that climbs out of the cache directory is refused.

    The upstream ``StoreKeyError`` (a ``ValueError``) from the nested config's
    ``extend_cache_path`` must surface unwrapped at the settings surface.
    """
    settings = _settings_with_nested_cache_cfg()

    with pytest.raises(ValueError):
        settings.extend_cache_paths("../x")


_FEATURES = ["range", "gradient_x_range", "hillshade_range_315_45"]
_TILE_IDS = ("tile_00", "tile_01")


def _read_every_raster(result) -> None:
    """Read every returned raster; an unlinked ``.dat`` raises ``FileNotFoundError`` here."""
    for key in result:
        arr = np.asarray(result[key])
        assert arr.shape == (8, 8), f"{key}: unexpected shape {arr.shape}"


@pytest.mark.parametrize("n_jobs", [1, 2], ids=["n_jobs=1", "n_jobs=2"])
def test_tiled_regenerate_on_one_instance_with_two_workers(tmp_path, synthetic_pcd, n_jobs) -> None:
    """Repeated ``generate()`` on one instance returns rasters that can be read.

    Each task carries only its own tile's generator, so a worker never unpickles another
    tile's disk-backed store. The earlier failure mode - every worker unpickling every tile's
    store at once and racing the single temporary name ``<key>.dat.tmp`` GSEGUtils 0.6.0 uses
    to rebuild a ``.dat`` memmap, surfacing as a loky ``BrokenProcessPool`` or a worker
    ``FileNotFoundError`` - is what the fan-out shape test guards. GSEGUtils#82
    (https://github.com/gseg-ethz/GSEGUtils/issues/82) remains the upstream defect for any
    program that unpickles one store in several processes at once;
    https://github.com/gseg-ethz/pc2img/issues/24 tracks it here.

    The result is rebound on every call and collected, then every raster is *read*: a pooled
    call hands the parent another entry object on each ``<tile>/<key>.dat``, and a released
    call's garbage-collection finalizers must not unlink the files a later call's entries
    read. A test that only checks the returned keys cannot see that, so every array is read
    with ``np.asarray`` and every store entry is read at the end.
    """
    tiles = [
        PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
        PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
    ]
    gen = TiledPointCloudImageGenerator(
        tiles,
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path),
    )

    result = gen.generate(["range"], n_jobs=n_jobs)
    result = gen.generate(_FEATURES, n_jobs=n_jobs)
    gc.collect()
    _read_every_raster(result)

    result = gen.generate(["range"], n_jobs=n_jobs)
    gc.collect()
    _read_every_raster(result)

    for tile_id in _TILE_IDS:
        assert (tile_id, "range") in result, f"no range raster for {tile_id}: {list(result)}"
        store = gen.image_generators[tile_id].feature_mgr.cache_store
        for name in _FEATURES:
            assert np.asarray(store[name]).shape == (8, 8), f"{tile_id}/{name}"
        assert get_memmap_path(store.cache_dir, "range").exists()


def test_tiled_results_never_own_gc_deletion(tmp_path, synthetic_pcd) -> None:
    """Entries a ``generate()`` call returns never delete shared memmaps when collected, at any ``n_jobs``.

    A pooled run returns parent-side copies of entries that share one ``.dat`` path with the
    copies every other call returns. An entry armed at ``n_jobs=1`` is still alive when a later
    pooled call rebuilds the same ``.dat`` under another object, and its finalizer would unlink
    the file that call's results and the stores read. So no entry owns garbage-collection
    deletion, whatever ``n_jobs``.
    """

    def _tiles() -> list[PointCloudTile]:
        return [
            PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
            PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
        ]

    def _purge_flags(gen, result) -> list[bool]:
        flags = [entry.purge_disk_on_gc for entry in result.values()]
        for image_gen in gen.image_generators.values():
            flags.extend(
                entry.purge_disk_on_gc
                for entry in image_gen.feature_mgr.cache_store.store.values()
                if entry is not None
            )
        return flags

    for label, n_jobs in (("pooled", 2), ("seq", 1)):
        gen = TiledPointCloudImageGenerator(
            _tiles(),
            (8, 8),
            "spherical",
            "linear",
            lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / label),
        )
        flags = _purge_flags(gen, gen.generate(["range"], n_jobs=n_jobs))
        assert flags, f"{label}: no entries were inspected"
        assert all(flag is False for flag in flags), (
            f"{label} (n_jobs={n_jobs}): expected purge_disk_on_gc is False everywhere: {flags}"
        )


_MIXED_SEQUENCES = {
    "1-then-2": [(1, ["range"]), (2, ["range"])],
    "1-then-neg1": [(1, ["range"]), (-1, ["range"])],
    "2-then-1-adding-then-2": [(2, ["range"]), (1, _FEATURES), (2, _FEATURES)],
}


@pytest.mark.parametrize("sequence", list(_MIXED_SEQUENCES.values()), ids=list(_MIXED_SEQUENCES))
def test_mixed_n_jobs_sequences_keep_every_raster_readable(tmp_path, synthetic_pcd, sequence) -> None:
    """Mixing ``n_jobs`` values on one instance never leaves an unreadable raster or store entry.

    An entry created at ``n_jobs=1`` must not delete, when released, a ``.dat`` that a later
    pooled call rebuilt under another object. After every call the previous result is released
    and collected, every returned raster is read, and at the end every store entry is read after
    an entry-level ``store.offload()``; an unlinked ``.dat`` raises ``FileNotFoundError`` there.
    """
    tiles = [
        PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
        PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
    ]
    gen = TiledPointCloudImageGenerator(
        tiles,
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path),
    )

    result = None
    for n_jobs, features in sequence:
        result = gen.generate(features, n_jobs=n_jobs)
        gc.collect()
        _read_every_raster(result)

    for tile_id in _TILE_IDS:
        store = gen.image_generators[tile_id].feature_mgr.cache_store
        store.offload()
        for name in list(store.keys()):
            assert np.asarray(store[name]).shape == (8, 8), f"{tile_id}/{name}"
        assert get_memmap_path(store.cache_dir, "range").exists()


def test_retry_after_a_pooled_call_with_one_failing_tile_succeeds(tmp_path, synthetic_pcd) -> None:
    """A pooled call in which one tile fails must not poison the retry for the tiles that finished.

    The tiles that finished wrote their codec pairs into their directories before another tile
    failed, and ``Parallel`` raises without their results. The parent's pre-call store copies do
    not track those keys, so the next call would reach the hard gate (``StorePurgeRefusedError``)
    in a non-owner process. Dropping the generators makes the next call rebuild each store in a
    worker, whose construction scan adopts the codec pairs as tracked keys. At ``n_jobs=1`` the
    stores are updated in place and nothing is dropped.

    The failing tile lacks the ``intensity`` scalar field; the exception type belongs to the
    point cloud and is not pinned.
    """

    def _tiles() -> list[PointCloudTile]:
        fields = {"intensity": None}
        return [
            PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1, with_scalar_fields=fields), {}),
            PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2, with_scalar_fields=fields), {}),
            PointCloudTile("tile_02", synthetic_pcd(n=64, seed=3, with_scalar_fields=fields), {}),
            PointCloudTile("tile_03", synthetic_pcd(n=64, seed=4), {}),
        ]

    for label, retry_n_jobs in (("seq-retry", 1), ("pooled-retry", 2)):
        gen = TiledPointCloudImageGenerator(
            _tiles(),
            (8, 8),
            "spherical",
            "linear",
            lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / label),
        )
        gen.generate(["range"], n_jobs=2)
        with pytest.raises(Exception):  # noqa: B017 - the type belongs to the point cloud, deliberately not pinned
            gen.generate(["gradient_x_range", "scalar_field_intensity"], n_jobs=2)
        assert gen.image_generators == {}, f"{label}: the parent kept stale tile generators"

        result = gen.generate(["gradient_x_range"], n_jobs=retry_n_jobs)
        gc.collect()
        assert len(result) == 4
        for key in result:
            assert np.asarray(result[key]).shape == (8, 8), f"{label}: {key}"
        assert len(gen.image_generators) == 4


def test_a_failing_sequential_call_keeps_the_tile_generators(tmp_path, synthetic_pcd) -> None:
    """At ``n_jobs=1`` the stores were updated in place, so a failure drops nothing.

    The parent's generators stay the owners; dropping them would only lose ownership.
    """
    fields = {"intensity": None}
    tiles = [
        PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1, with_scalar_fields=fields), {}),
        PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
    ]
    gen = TiledPointCloudImageGenerator(
        tiles,
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path),
    )
    gen.generate(["range"], n_jobs=1)
    before = dict(gen.image_generators)
    assert set(before) == set(_TILE_IDS)

    with pytest.raises(Exception):  # noqa: B017 - the type belongs to the point cloud, deliberately not pinned
        gen.generate(["scalar_field_intensity"], n_jobs=1)

    assert gen.image_generators == before
    assert all(gen.image_generators[tid] is before[tid] for tid in before)


def test_duplicate_tile_ids_are_rejected_at_construction(synthetic_pcd) -> None:
    """A repeated tile id raises ``ValueError`` at construction and names the id.

    With a repeated id, later calls hand both tasks one generator, so one tile is computed
    from the other's points, one tile is missing from the results, and with a pool the
    one-store-in-two-processes race returns.
    """
    args = ((4, 4), "spherical", "linear")

    with pytest.raises(ValueError, match="dup"):
        TiledPointCloudImageGenerator(
            [
                PointCloudTile("dup", synthetic_pcd(n=8, seed=1), {}),
                PointCloudTile("dup", synthetic_pcd(n=8, seed=2), {}),
            ],
            *args,
        )

    with pytest.raises(ValueError, match="'a'"):
        TiledPointCloudImageGenerator(
            [PointCloudTile(tid, synthetic_pcd(n=8, seed=i), {}) for i, tid in enumerate(("a", "b", "a"))],
            *args,
        )

    TiledPointCloudImageGenerator(
        [PointCloudTile(tid, synthetic_pcd(n=8, seed=i), {}) for i, tid in enumerate(("a", "b"))],
        *args,
    )


def test_generate_dispatches_one_tile_per_task_without_pickling_the_generator(
    tmp_path, synthetic_pcd, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each task handed to the worker pool carries one tile, never the whole generator.

    ``Parallel`` is replaced by a recorder that captures the ``(func, args, kwargs)``
    triples ``generate()`` builds with ``delayed`` and runs them inline, so the fan-out
    shape is checked deterministically and without spawning processes. A bound method of
    the tiled generator as the dispatched callable would pickle every tile's generator,
    store and point cloud into every task - the shape that makes each worker unpickle every
    tile's store at once.
    """
    recorded: list[list[tuple]] = []

    class _RecordingParallel:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __call__(self, iterable):
            triples = list(iterable)
            recorded.append(triples)
            return [func(*args, **kwargs) for func, args, kwargs in triples]

    monkeypatch.setattr(tiled_module, "Parallel", _RecordingParallel)

    tile_ids = ("tile_00", "tile_01")
    tiles = [
        PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
        PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
    ]
    gen = TiledPointCloudImageGenerator(
        tiles,
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path),
    )

    gen.generate(["range"], n_jobs=2)
    gen.generate(["range"], n_jobs=2)

    assert len(recorded) == 2
    for call_index, triples in enumerate(recorded):
        assert len(triples) == len(tile_ids), "expected exactly one task per tile"
        for func, args, kwargs in triples:
            values = [*args, *kwargs.values()]
            assert getattr(func, "__self__", None) is None, f"bound method dispatched: {func!r}"
            assert func is tiled_module._process_tile
            assert not any(value is gen for value in values), "the tiled generator itself is in a task payload"

            own = [tile_id for tile_id in tile_ids if any(isinstance(v, str) and v == tile_id for v in values)]
            assert len(own) == 1, f"a task must name exactly one tile id, got {own}"
            (tile_id,) = own
            other = next(t for t in tile_ids if t != tile_id)

            generators = [value for value in values if isinstance(value, PointCloudImageGenerator)]
            assert len(generators) <= 1, "a task carries at most one tile generator"
            if call_index == 1:
                assert len(generators) == 1, "second call must hand the tile its existing generator"
                assert generators[0] is gen.image_generators[tile_id], "second call must reuse the tile's own generator"

            payload = pickle.dumps((func, args, kwargs))
            assert other.encode() not in payload, f"{tile_id}'s task payload contains {other}'s state"


def test_tile_stores_built_by_workers_refuse_purge_from_the_parent(tmp_path, synthetic_pcd) -> None:
    """Stores built inside a worker belong to that worker; the parent cannot purge them.

    Pins the ownership limit documented on ``TiledPointCloudImageGenerator`` so the docstring
    cannot silently go stale: with ``n_jobs=2`` the tile stores record the worker's process id
    as owner and GSEGUtils refuses ``purge`` from the parent, leaving the key and its files
    untouched; with ``n_jobs=1`` the parent owns the stores and purges them. When the limit is
    lifted this test is rewritten, not deleted.
    """

    def _tiles() -> list[PointCloudTile]:
        return [
            PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
            PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
        ]

    pooled = TiledPointCloudImageGenerator(
        _tiles(),
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / "pooled"),
    )
    pooled.generate(["range"], n_jobs=2)
    store = pooled.image_generators["tile_00"].feature_mgr.cache_store

    with pytest.raises(StorePurgeRefusedError):
        store.purge("range")
    assert "range" in store
    assert get_npy_path(store.cache_dir, "range").exists()

    sequential = TiledPointCloudImageGenerator(
        _tiles(),
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / "seq"),
    )
    sequential.generate(["range"], n_jobs=1)
    own_store = sequential.image_generators["tile_00"].feature_mgr.cache_store

    own_store.purge("range")
    assert "range" not in own_store


def test_regenerate_at_n_jobs_1_after_a_pooled_run_tolerates_a_leftover_temporary_but_refuses_a_dropped_codec_pair(
    tmp_path, synthetic_pcd
) -> None:
    """Pins the two sentences of the class docstring that describe the remaining ownership limit.

    After a pooled run every tile store belongs to the worker that built it, for good, so the
    parent process is not the owner either and ``n_jobs=1`` does not help:

    * a leftover temporary file for a requested feature (a killed worker, a failed rename) does
      not trigger the refusal - the later call succeeds and every raster reads;
    * a requested feature that is untracked but still has its codec pair in the tile directory
      (dropped with ``del`` while offloaded) does: ``StorePurgeRefusedError``, deterministically
      at ``n_jobs=1``.

    The trigger sits in ``tile_00``, the first tile: at ``n_jobs=1`` with ``verbose=50`` joblib
    masks an exception raised after the first tile as an ``AttributeError``.
    """

    def _tiles() -> list[PointCloudTile]:
        return [
            PointCloudTile("tile_00", synthetic_pcd(n=64, seed=1), {}),
            PointCloudTile("tile_01", synthetic_pcd(n=64, seed=2), {}),
        ]

    tolerant = TiledPointCloudImageGenerator(
        _tiles(),
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / "tolerant"),
    )
    tolerant.generate(["range"], n_jobs=2)
    tolerant_store = tolerant.image_generators["tile_00"].feature_mgr.cache_store
    leftover = get_memmap_tmp_path(tolerant_store.cache_dir, "gradient_x_range")
    leftover.write_bytes(b"\0" * 64)

    result = tolerant.generate(["gradient_x_range"], n_jobs=1)
    gc.collect()
    _read_every_raster(result)
    assert ("tile_00", "gradient_x_range") in result and ("tile_01", "gradient_x_range") in result

    refused = TiledPointCloudImageGenerator(
        _tiles(),
        (8, 8),
        "spherical",
        "linear",
        lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path / "refused"),
    )
    refused.generate(["range"], n_jobs=2)
    refused_store = refused.image_generators["tile_00"].feature_mgr.cache_store
    del refused_store["range"]
    assert "range" not in refused_store
    assert get_npy_path(refused_store.cache_dir, "range").exists(), "the codec pair must stay on disk"

    with pytest.raises(StorePurgeRefusedError):
        refused.generate(["range"], n_jobs=1)
