"""Sensors for ``features/derivative_features.py``.

Two distinct kinds of test live here, per the disposition of the findings
that touch this module:

* **Genuine defects.** ``NormalizedFeature`` mutated the raster it
  fetches in place and had its percentile-bounds validation
  commented out — both on the same ``compute``. These shipped
  *test-first*: the proving tests below are authored ``xfail`` and flip to passing
  asserts once the one-edit fix lands.
* **Kept behaviour.** ``GradientFeature``'s ``1/100`` gradient spacing
  and ``HillshadeFeature``'s non-north-up aspect handedness are DELIBERATE,
  downstream-validated design. They are pinned by *characterization*
  tests that are green from the start and stay green: the only source change is an
  opt-in ``pixel_size`` param whose default reproduces today's output byte-for-byte,
  and a docstring note for the aspect convention. We assert
  hillshade azimuth-sweep *self-consistency*, never ESRI-compass truth.

The derivative ``compute(_, fetch)`` call sites ignore the ``pcd`` positional and
resolve dependency rasters by name, so every test drives them through the shared
``fetch_stub`` factory fixture (``tests/conftest.py``).
"""

from __future__ import annotations

import numpy as np
import pytest

from pc2img.features.derivative_features import (
    GradientFeature,
    HillshadeFeature,
    NormalizedFeature,
)
from pc2img.features.registry import FEATURES


# --------------------------------------------------------------------------- #
# Genuine defects, now fixed (proving asserts pass)                           #
# --------------------------------------------------------------------------- #
def test_normalized_feature_rejects_inverted_percentiles() -> None:
    # low > high is nonsense; ClipPercentileFeature already rejects it, and the
    # re-enabled check here enforces ``0 <= low < high <= 100``.
    with pytest.raises(ValueError):
        NormalizedFeature(base_feature="range", low="90", high="10")


def test_normalized_feature_rejects_out_of_range_percentiles() -> None:
    with pytest.raises(ValueError):
        NormalizedFeature(base_feature="range", low="10", high="120")


def test_normalized_feature_does_not_mutate_fetched_array(fetch_stub) -> None:
    # compute() must not write into the array it receives from ``fetch``.
    raster = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64)
    original = raster.copy()
    fetch = fetch_stub({"range": raster})

    NormalizedFeature(base_feature="range").compute(None, fetch)

    np.testing.assert_array_equal(raster, original)


# --------------------------------------------------------------------------- #
# GradientFeature 1/100 spacing is KEPT behaviour (characterization)          #
# --------------------------------------------------------------------------- #
def _unit_slope_ramp() -> np.ndarray:
    """An 8x8 raster whose value rises by 1 per column (unit slope along x)."""
    return np.tile(np.arange(8, dtype=np.float64), (8, 1))


def test_gradient_default_matches_hundredth_scaled_reference(fetch_stub) -> None:
    ramp = _unit_slope_ramp()
    fetch = fetch_stub({"range": ramp})

    grad = GradientFeature(base_feature="range", axis="x").compute(None, fetch)

    # Pins today's output byte-for-byte: np.gradient with spacing 100 (∴ 1/100 scale).
    expected = np.gradient(ramp, 100, axis=1)
    np.testing.assert_array_equal(grad, expected)


def test_gradient_pixel_size_default_reproduces_hundred_spacing(fetch_stub) -> None:
    ramp = _unit_slope_ramp()

    default = GradientFeature(base_feature="range", axis="x").compute(None, fetch_stub({"range": ramp}))
    explicit = GradientFeature(base_feature="range", axis="x", pixel_size="100").compute(
        None, fetch_stub({"range": ramp})
    )

    # The opt-in param's default is a no-op: byte-identical to the historical output.
    np.testing.assert_array_equal(default, explicit)


def test_gradient_pixel_size_scales_output(fetch_stub) -> None:
    ramp = _unit_slope_ramp()

    px100 = GradientFeature(base_feature="range", axis="x", pixel_size="100").compute(None, fetch_stub({"range": ramp}))
    px1 = GradientFeature(base_feature="range", axis="x", pixel_size="1").compute(None, fetch_stub({"range": ramp}))

    # Spacing divides the gradient: unit spacing is 100x the spacing-100 result.
    np.testing.assert_allclose(px1, px100 * 100)


def test_gradient_dsl_px_suffix_parses_pixel_size() -> None:
    spec = FEATURES.match("gradient_x_range_px50")
    feature = spec.cls(**spec.params)

    assert feature.base_feature == "range"
    assert feature.pixel_size == 50.0


def test_gradient_dsl_without_suffix_keeps_default_spacing() -> None:
    spec = FEATURES.match("gradient_x_range")
    feature = spec.cls(**spec.params)

    assert feature.base_feature == "range"
    assert feature.pixel_size == 100.0


# --------------------------------------------------------------------------- #
# Hillshade aspect handedness is KEPT behaviour (self-consistency only)       #
# --------------------------------------------------------------------------- #
def test_hillshade_azimuth_sweep_is_self_consistent(fetch_stub) -> None:
    # An east-rising ramp: value increases along the column axis. We assert only
    # that illuminating it from one azimuth is consistently brighter than from the
    # opposite azimuth — an *internal* invariant, NOT ESRI-compass truth.
    ramp = np.tile(np.linspace(0.0, 10.0, 10, dtype=np.float64), (10, 1))
    fetch_bright = fetch_stub({"range": ramp})
    fetch_dark = fetch_stub({"range": ramp})

    bright = HillshadeFeature(base_feature="range", azimuth="0").compute(None, fetch_bright)
    dark = HillshadeFeature(base_feature="range", azimuth="180").compute(None, fetch_dark)

    assert np.nanmean(bright) > np.nanmean(dark)


# --------------------------------------------------------------------------- #
# Percentile-bounds validation centralized (strict/non-strict preserved)      #
#                                                                              #
# NormalizedFeature keeps its strict low < high contract (a zero range divides #
# by zero) while ClipPercentileFeature and rrim keep the non-strict low <= high #
# contract. The rule now lives in one shared _validate_percentile_bounds, but  #
# NO observable validation outcome changes — these characterization tests are  #
# green before and after the refactor.                                         #
# --------------------------------------------------------------------------- #
def test_normalized_rejects_equal_percentiles_strict() -> None:
    with pytest.raises(ValueError):
        NormalizedFeature(base_feature="range", low="50", high="50")


def test_clip_percentile_accepts_equal_percentiles_non_strict() -> None:
    from pc2img.features.derivative_features import ClipPercentileFeature

    # low == high is allowed under the non-strict contract; must not raise.
    ClipPercentileFeature(base_feature="range", low="50", high="50")


def test_rrim_validate_clip_accepts_equal_percentiles_non_strict() -> None:
    from pc2img.features import rrim

    assert rrim._validate_clip("slope", (50.0, 50.0)) == (50.0, 50.0)


def test_shared_percentile_validator_strict_and_non_strict_contract() -> None:
    from pc2img.features.derivative_features import _validate_percentile_bounds

    _validate_percentile_bounds(10.0, 20.0, strict=True)  # ok
    _validate_percentile_bounds(20.0, 20.0, strict=False)  # equal allowed
    with pytest.raises(ValueError):
        _validate_percentile_bounds(20.0, 20.0, strict=True)  # equal rejected (zero range)
    with pytest.raises(ValueError):
        _validate_percentile_bounds(10.0, 120.0, strict=False)  # out of [0, 100]
