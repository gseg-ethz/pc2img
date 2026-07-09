from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np


FEATURES_DIR = Path(__file__).resolve().parents[1] / "src" / "pc2img" / "features"
TEST_ROOT_PACKAGE = "rrim_testpkg"
TEST_FEATURES_PACKAGE = f"{TEST_ROOT_PACKAGE}.features"


def _load_module(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name!r} from {path}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_rrim_modules():
    # Only install a minimal `pchandler` stub when no real pchandler is
    # importable. A real installation (dev + CI, where `uv sync --frozen`
    # provides it) is left untouched and imported normally by the exec'd rrim
    # modules below. Unconditionally inserting the stub would permanently shadow
    # a real pchandler in sys.modules, which — under any non-alphabetical
    # collection order — flips unrelated tests red (they'd bind the fake
    # PointCloudData). Gating on find_spec removes that order dependency: when a
    # real module exists there is nothing to shadow, and when none exists there
    # is no other test that could be affected.
    if "pchandler" not in sys.modules and importlib.util.find_spec("pchandler") is None:
        pchandler = types.ModuleType("pchandler")

        class PointCloudData:  # pragma: no cover - import stub only
            pass

        pchandler.PointCloudData = PointCloudData
        sys.modules["pchandler"] = pchandler

    if TEST_ROOT_PACKAGE not in sys.modules:
        pkg = types.ModuleType(TEST_ROOT_PACKAGE)
        pkg.__path__ = [str(FEATURES_DIR.parent)]
        sys.modules[TEST_ROOT_PACKAGE] = pkg

    if TEST_FEATURES_PACKAGE not in sys.modules:
        pkg = types.ModuleType(TEST_FEATURES_PACKAGE)
        pkg.__path__ = [str(FEATURES_DIR)]
        sys.modules[TEST_FEATURES_PACKAGE] = pkg

    core = _load_module(f"{TEST_FEATURES_PACKAGE}.core", FEATURES_DIR / "core.py")
    registry = _load_module(f"{TEST_FEATURES_PACKAGE}.registry", FEATURES_DIR / "registry.py")
    rrim = _load_module(f"{TEST_FEATURES_PACKAGE}.rrim", FEATURES_DIR / "rrim.py")
    return core, registry, rrim


_, registry_module, rrim_module = _load_rrim_modules()


def test_compute_rrim_flat_plane_returns_neutral_gray() -> None:
    raster = np.zeros((9, 9), dtype=np.float32)
    result = rrim_module.compute_rrim(raster, max_distance=4, num_directions=8)

    assert np.nanmax(np.abs(result.slope)) == 0.0
    assert np.nanmax(np.abs(result.structure)) < 1e-6
    assert np.allclose(result.rgb[4, 4], np.array([0.5, 0.5, 0.5], dtype=np.float32))


def test_compute_rrim_distinguishes_ridge_from_valley() -> None:
    ridge_profile = np.array([0.0, 1.0, 2.5, 1.0, 0.0], dtype=np.float32)
    ridge = np.tile(ridge_profile, (5, 1))
    valley = -ridge

    ridge_result = rrim_module.compute_rrim(ridge, max_distance=3, num_directions=8)
    valley_result = rrim_module.compute_rrim(valley, max_distance=3, num_directions=8)

    assert ridge_result.structure[2, 2] > 0.0
    assert valley_result.structure[2, 2] < 0.0
    assert ridge_result.structure[2, 2] > valley_result.structure[2, 2]


def test_compute_rrim_steeper_surface_increases_red_channel() -> None:
    x = np.arange(21, dtype=np.float32)
    profile = np.where(x < 10, x * 0.2, 2.0 + (x - 10) * 1.0)
    raster = np.tile(profile, (11, 1))

    result = rrim_module.compute_rrim(raster, max_distance=4, num_directions=8)

    assert result.rgb[5, 16, 0] > result.rgb[5, 4, 0]
    assert np.allclose(result.rgb[..., 1], result.rgb[..., 2], equal_nan=True)


def test_compute_rrim_nan_and_edge_handling_do_not_wrap() -> None:
    raster = np.zeros((5, 5), dtype=np.float32)
    raster[:, -1] = 10.0
    raster[2, 2] = np.nan

    result = rrim_module.compute_rrim(raster, max_distance=1, num_directions=4)

    assert np.isnan(result.structure[2, 2])
    assert np.nanmax(np.abs(result.structure[:, 0])) < 1e-6


def test_rrim_feature_registry_outputs_rgb_and_components() -> None:
    features = registry_module.FEATURES
    raster = np.tile(np.linspace(0.0, 2.0, 9, dtype=np.float32), (9, 1))

    rrim_spec = features.match("rrim")
    rrim_feature = rrim_spec.cls(**rrim_spec.params)
    pack_name = next(dep for dep in rrim_feature.dependencies if dep.startswith("rrim_pack_("))

    pack_spec = features.match(pack_name)
    pack_feature = pack_spec.cls(**pack_spec.params)
    pack = pack_feature.compute(None, lambda name: raster)

    rrim_rgb = rrim_feature.compute(None, lambda name: raster if name == "range" else pack)
    assert rrim_rgb.shape == raster.shape + (3,)

    component_spec = features.match("rrim_component_(structure,range,r16,d8)")
    component_feature = component_spec.cls(**component_spec.params)
    structure = component_feature.compute(None, lambda name: pack)

    assert structure.shape == raster.shape
    assert np.allclose(structure, pack[..., 2], equal_nan=True)
