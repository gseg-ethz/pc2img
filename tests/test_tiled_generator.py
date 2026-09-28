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
checks are pure-object and free of any joblib/loky process parallelism, keeping
them deterministic and CI-safe.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from pc2img.core import ImgRes
from pc2img.tiled_generator import TIGSettings


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
