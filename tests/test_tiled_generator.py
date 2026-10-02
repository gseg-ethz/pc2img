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
checks are pure-object, keeping them deterministic and CI-safe. One regression
test deliberately drives the real loky fan-out with two workers to pin a known
limitation (an ``xfail``), so it is the only test here that spawns processes.
"""

from __future__ import annotations

import pickle
import subprocess
import sys

import pytest
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

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
    """Repeated ``generate()`` on one instance with two workers must keep working.

    Pins a known limitation: on GSEGUtils 0.6.0 every worker unpickles every tile's
    disk-backed store and rebuilds each ``.dat`` through the single temporary name
    ``<key>.dat.tmp``, so the second or third call fails. Two exception families are
    known manifestations of the one race - a loky pool error
    (``BrokenProcessPool``/``TerminatedWorkerError``, ``RuntimeError``) and the
    worker's own ``FileNotFoundError`` (``OSError``) - and the marker names exactly
    these two, never a third. The pc2img-level reproduction on the migrated tree saw
    OBSERVED_TYPES: joblib.externals.loky.process_executor.BrokenProcessPool
    (``RuntimeError``) in every round; the ``OSError`` family was not seen at this level.

    ``strict=False`` because the failure is a race (upstream it fired in 12 of 12 rounds
    in one measurement and 11 of 12 in another). An XPASS is the signal to drop the
    marker and bump the GSEGUtils pin.
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

            own = [tile_id for tile_id in tile_ids if tile_id in values]
            assert len(own) == 1, f"a task must name exactly one tile id, got {own}"
            (tile_id,) = own
            other = next(t for t in tile_ids if t != tile_id)

            generators = [value for value in values if isinstance(value, PointCloudImageGenerator)]
            assert len(generators) <= 1, "a task carries at most one tile generator"
            if call_index == 1:
                assert generators == [gen.image_generators[tile_id]], "second call must reuse the tile's own generator"

            payload = pickle.dumps((func, args, kwargs))
            assert other.encode() not in payload, f"{tile_id}'s task payload contains {other}'s state"
