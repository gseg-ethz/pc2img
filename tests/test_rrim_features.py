from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from pc2img.core import PointCloudImageGenerator
from pc2img.features import registry as registry_module
from pc2img.features import rrim as rrim_module
from pc2img.features.registry import FEATURES

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RRIM_SRC = "src/pc2img/features/rrim.py"

# The default RRIMConfig pack name (base_feature=range, r16, d8, z1) — the exact
# string RRIMFeature.__init__ derives, so match() must schedule the same dep.
_DEFAULT_PACK_NAME = "rrim_pack_(range,r16,d8,z1)"


def test_rrim_module_docstring_is_populated() -> None:
    """BUG-04: the module docstring is the first statement, so __doc__ populates."""
    assert isinstance(rrim_module.__doc__, str)
    assert rrim_module.__doc__.strip()


def test_rrim_module_docstring_clears_e402() -> None:
    """BUG-04 proving test: reordering the header so the docstring leads clears the E402 findings."""
    ruff = Path(sys.executable).with_name("ruff")
    ruff_cmd = str(ruff) if ruff.exists() else shutil.which("ruff")
    if ruff_cmd is None:
        pytest.skip("ruff not found on PATH or next to the interpreter")

    check = subprocess.run(
        [ruff_cmd, "check", "--select", "E402", _RRIM_SRC],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check.returncode == 0, f"ruff E402 reported findings:\n{check.stdout}"


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


# --------------------------------------------------------------------------- #
# G1 (BUG-05, blocker): RRIM dependency resolution via dependencies_for        #
#                                                                              #
# FeatureRegistry.match derives deps via cls.dependencies_for(params) WITHOUT  #
# constructing the class (DSN-05). The three RRIM classes use a regex group    #
# named ``args`` (not ``base_feature``), so without a dependencies_for         #
# override the inherited base returns [] and the base raster is never          #
# scheduled — reproducing "Scalar field 'rrim' not found" end-to-end. These    #
# tests derive deps without construction AND drive the full generate() path.   #
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(reason="Phase 5 (BUG-05/G1): RRIM classes lack a dependencies_for override; deps resolve to [] so the base raster is never scheduled", strict=False)
def test_rrim_dependencies_for_derives_deps_without_construction() -> None:
    """match() derives each RRIM name's deps via dependencies_for, no __init__."""
    assert FEATURES.match("rrim").dependencies == ["range", _DEFAULT_PACK_NAME]
    assert FEATURES.match("rrim_pack_(range)").dependencies == ["range"]
    # slope component depends on the base feature directly ...
    assert FEATURES.match("rrim_component_(slope,range)").dependencies == ["range"]
    # ... while a non-slope component depends on the pack raster.
    assert FEATURES.match("rrim_component_(structure,range)").dependencies == [_DEFAULT_PACK_NAME]


@pytest.mark.xfail(reason="Phase 5 (BUG-05/G1): RRIM classes lack a dependencies_for override; deps resolve to [] so the base raster is never scheduled", strict=False)
def test_rrim_dependencies_for_does_not_construct_the_class(monkeypatch) -> None:
    """dependencies_for must read params['args'], never run __init__."""

    def _boom(self, *args, **kwargs):
        raise AssertionError("dependencies_for must not construct the RRIM feature")

    monkeypatch.setattr(rrim_module.RRIMFeature, "__init__", _boom)
    assert rrim_module.RRIMFeature.dependencies_for({"args": None}) == ["range", _DEFAULT_PACK_NAME]


def _rrim_generator(synthetic_pcd) -> PointCloudImageGenerator:
    pcd = synthetic_pcd(n=300)
    return PointCloudImageGenerator(pcd, (16, 16), ("orthographic", {"plane": "xy"}), "nearest_neighbor")


@pytest.mark.xfail(reason="Phase 5 (BUG-05/G1): RRIM classes lack a dependencies_for override; deps resolve to [] so the base raster is never scheduled", strict=False)
def test_generate_rrim_end_to_end_returns_finite_rgb(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim"])
    raster = np.asarray(images["rrim"])
    assert raster.shape == (16, 16, 3)
    assert np.isfinite(raster).all()


@pytest.mark.xfail(reason="Phase 5 (BUG-05/G1): RRIM classes lack a dependencies_for override; deps resolve to [] so the base raster is never scheduled", strict=False)
def test_generate_rrim_pack_end_to_end_returns_finite_pack(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim_pack_(range)"])
    raster = np.asarray(images["rrim_pack_(range)"])
    assert raster.shape == (16, 16, 3)
    assert np.isfinite(raster).all()


@pytest.mark.xfail(reason="Phase 5 (BUG-05/G1): RRIM classes lack a dependencies_for override; deps resolve to [] so the base raster is never scheduled", strict=False)
def test_generate_rrim_component_slope_end_to_end_returns_finite_raster(synthetic_pcd) -> None:
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim_component_(slope,range)"])
    raster = np.asarray(images["rrim_component_(slope,range)"])
    assert raster.shape == (16, 16)
    assert np.isfinite(raster).all()
