"""Sensors for ``features/derivative_features.py`` (BUG-05, TEST-04).

Two distinct kinds of test live here, per the Phase-5 disposition of the four
04-FINDINGS items that touch this module:

* **Genuine defects (DSN-03 + M-12).** ``NormalizedFeature`` mutates the raster it
  fetches in place (DSN-03, :78-79) and has its percentile-bounds validation
  commented out (M-12, :68) — both on the same ``compute``. These ship
  *test-first*: the proving tests below are authored ``xfail`` and flip to passing
  asserts once the one-edit fix lands (D-12).
* **Kept-behavior (M-10 + M-11).** ``GradientFeature``'s ``1/100`` gradient spacing
  and ``HillshadeFeature``'s non-north-up aspect handedness are DELIBERATE,
  downstream-validated design (Pitfall 5). They are pinned by *characterization*
  tests that are green from the start and stay green: the only source change is an
  opt-in ``pixel_size`` param whose default reproduces today's output byte-for-byte
  (M-10/D-07), and a docstring note for the aspect convention (M-11/D-08). We assert
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


# --------------------------------------------------------------------------- #
# DSN-03 + M-12 — genuine defects, authored xfail (flip to passing in the fix) #
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(
    strict=False,
    reason="Phase 5 (BUG-05): NormalizedFeature bounds validation (M-12) not yet re-enabled",
)
def test_normalized_feature_rejects_inverted_percentiles() -> None:
    # low > high is nonsense; ClipPercentileFeature already rejects it, and the
    # commented-out check here (:68) enforced ``0 <= low < high <= 100``.
    with pytest.raises(ValueError):
        NormalizedFeature(base_feature="range", low="90", high="10")


@pytest.mark.xfail(
    strict=False,
    reason="Phase 5 (BUG-05): NormalizedFeature out-of-[0,100] validation (M-12) not yet re-enabled",
)
def test_normalized_feature_rejects_out_of_range_percentiles() -> None:
    with pytest.raises(ValueError):
        NormalizedFeature(base_feature="range", low="10", high="120")


@pytest.mark.xfail(
    strict=False,
    reason="Phase 5 (BUG-05): NormalizedFeature copy-before-mutate (DSN-03) not yet applied",
)
def test_normalized_feature_does_not_mutate_fetched_array(fetch_stub) -> None:
    # DSN-03: compute() must not write into the array it receives from ``fetch``.
    raster = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64)
    original = raster.copy()
    fetch = fetch_stub({"range": raster})

    NormalizedFeature(base_feature="range").compute(None, fetch)

    np.testing.assert_array_equal(raster, original)


# --------------------------------------------------------------------------- #
# M-10 — GradientFeature 1/100 spacing is KEPT behavior (characterization)     #
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


# --------------------------------------------------------------------------- #
# M-11 — Hillshade aspect handedness is KEPT behavior (self-consistency only)  #
# --------------------------------------------------------------------------- #
def test_hillshade_azimuth_sweep_is_self_consistent(fetch_stub) -> None:
    # An east-rising ramp: value increases along the column axis. We assert only
    # that illuminating it from one azimuth is consistently brighter than from the
    # opposite azimuth — an *internal* invariant, NOT ESRI-compass truth (D-08).
    ramp = np.tile(np.linspace(0.0, 10.0, 10, dtype=np.float64), (10, 1))
    fetch_bright = fetch_stub({"range": ramp})
    fetch_dark = fetch_stub({"range": ramp})

    bright = HillshadeFeature(base_feature="range", azimuth="0").compute(None, fetch_bright)
    dark = HillshadeFeature(base_feature="range", azimuth="180").compute(None, fetch_dark)

    assert np.nanmean(bright) > np.nanmean(dark)
