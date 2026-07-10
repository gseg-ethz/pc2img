from __future__ import annotations

import numpy as np

from pc2img.features import registry as registry_module
from pc2img.features import rrim as rrim_module


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
    pack_name = next(
        dep for dep in rrim_feature.dependencies if dep.startswith("rrim_pack_(")
    )

    pack_spec = features.match(pack_name)
    pack_feature = pack_spec.cls(**pack_spec.params)
    pack = pack_feature.compute(None, lambda name: raster)

    rrim_rgb = rrim_feature.compute(
        None, lambda name: raster if name == "range" else pack
    )
    assert rrim_rgb.shape == raster.shape + (3,)

    component_spec = features.match("rrim_component_(structure,range,r16,d8)")
    component_feature = component_spec.cls(**component_spec.params)
    structure = component_feature.compute(None, lambda name: pack)

    assert structure.shape == raster.shape
    assert np.allclose(structure, pack[..., 2], equal_nan=True)
