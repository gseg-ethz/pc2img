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
checks are pure-object, keeping them deterministic and CI-safe. Three tests concern the
fan-out: repeated generation on one instance with two workers and the worker-owned-store
pin spawn real loky processes, while the fan-out shape test replaces the pool with a
recorder and runs inline.
"""

from __future__ import annotations

import pickle
import subprocess
import sys

import pytest
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, StorePurgeRefusedError, get_npy_path

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


def test_tiled_regenerate_on_one_instance_with_two_workers(tmp_path, synthetic_pcd) -> None:
    """Repeated ``generate()`` on one instance with two workers keeps working.

    Each task carries only its own tile's generator, so a worker never unpickles another
    tile's disk-backed store. The earlier failure mode - every worker unpickling every tile's
    store at once and racing the single temporary name ``<key>.dat.tmp`` GSEGUtils 0.6.0 uses
    to rebuild a ``.dat`` memmap, surfacing as a loky ``BrokenProcessPool`` or a worker
    ``FileNotFoundError`` - is what the fan-out shape test guards. GSEGUtils#82
    (https://github.com/gseg-ethz/GSEGUtils/issues/82) remains the upstream defect for any
    program that unpickles one store in several processes at once;
    https://github.com/gseg-ethz/pc2img/issues/24 tracks it here.
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

    gen.generate(["range"], n_jobs=2)
    gen.generate(["range", "gradient_x_range", "hillshade_range_315_45"], n_jobs=2)
    result = gen.generate(["range"], n_jobs=2)

    for tile_id in ("tile_00", "tile_01"):
        assert (tile_id, "range") in result, f"no range raster for {tile_id}: {list(result)}"


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
