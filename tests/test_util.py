"""Tests for :mod:`pc2img.util`.

Covers three findings on this module plus breadth coverage for the
pure-array helpers:

* ``nanconv`` must not mutate the caller's input array in place.
* ``nanconv`` must accumulate/divide in float32 (float16 overflows to
  ``inf`` on realistic range magnitudes).
* ``convert_to_image`` on all-NaN input with ``normalize=True`` must
  degrade to a valid constant uint8 image rather than raising.

The genuine-fix sensors are authored ``xfail`` first: they
prove the defect is reachable today and flip to passing once ``util.py`` is fixed.
The ``replace_nan`` / ``to_gray`` breadth tests pass from the start (characterization).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import convolve2d

from pc2img.util import convert_to_image, nanconv, replace_nan, to_gray


# --------------------------------------------------------------------------- #
# float64 oracle for the normalized-convolution math                          #
# --------------------------------------------------------------------------- #
def _nanconv_float64_reference(a: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Reference normalized convolution in float64 (no float16 cast, no mutation).

    Mirrors ``nanconv``'s math exactly but accumulates in float64, so it serves as
    the correctness oracle the float32 implementation must track.
    """
    a = np.asarray(a, dtype=np.float64)
    k = np.asarray(k, dtype=np.float64)
    mask = np.isnan(a)
    filled = np.where(mask, 0.0, a)
    on = np.ones(a.shape, dtype=np.float64)
    on[mask] = 0.0
    denom = convolve2d(on, k, mode="same")
    numer = convolve2d(filled, k, mode="same")
    out = np.full(denom.shape, np.nan, dtype=np.float64)
    np.divide(numer, denom, out=out, where=(denom != 0))
    return out


# --------------------------------------------------------------------------- #
# nanconv must not mutate the caller's input                                  #
# --------------------------------------------------------------------------- #
def test_nanconv_does_not_mutate_input_nan_mask() -> None:
    a = np.array([[1.0, np.nan, 3.0], [np.nan, 5.0, 6.0], [7.0, 8.0, np.nan]], dtype=np.float32)
    snapshot = a.copy()
    k = np.ones((3, 3), dtype=np.float32)

    nanconv(a, k)

    # The caller's NaN mask (and finite values) must survive untouched.
    assert np.array_equal(np.isnan(a), np.isnan(snapshot))
    assert np.array_equal(a[~np.isnan(a)], snapshot[~np.isnan(snapshot)])


# --------------------------------------------------------------------------- #
# nanconv must stay finite and float32-accurate on realistic magnitudes       #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("magnitude", [5e3, 1.2e4, 5e4])
@pytest.mark.parametrize("kernel_size", [3, 5, 7])
def test_nanconv_finite_and_within_float32_tolerance(magnitude: float, kernel_size: int) -> None:
    a = np.full((16, 16), magnitude, dtype=np.float32)
    k = np.ones((kernel_size, kernel_size), dtype=np.float32)

    result = nanconv(a, k)
    reference = _nanconv_float64_reference(a, k)

    assert np.all(np.isfinite(result)), "float16 accumulation overflowed to inf/nan"
    np.testing.assert_allclose(result, reference, rtol=1e-4, atol=1e-2)


# --------------------------------------------------------------------------- #
# Reduced-precision opt-in on nanconv                                         #
# --------------------------------------------------------------------------- #
def test_nanconv_default_reproduces_float32_output_byte_for_byte() -> None:
    # The default (compute_dtype=np.float32) must equal the mandatory fixed path.
    a = np.array([[1.0, np.nan, 3.0], [4.0, 5.0, np.nan], [7.0, 8.0, 9.0]], dtype=np.float32)
    k = np.ones((3, 3), dtype=np.float32)

    default_out = nanconv(a, k)
    explicit_f32 = nanconv(a, k, compute_dtype=np.float32)

    assert default_out.dtype == np.float32
    assert np.array_equal(default_out, explicit_f32, equal_nan=True)


def test_nanconv_reduced_precision_engages_only_when_requested() -> None:
    a = np.full((16, 16), 12000.0, dtype=np.float32)
    k = np.ones((7, 7), dtype=np.float32)

    # Explicit opt-in to reduced precision engages float16 (and overflows).
    reduced = nanconv(a, k, compute_dtype=np.float16)
    assert reduced.dtype == np.float16

    # Default keeps the finite float32 correctness path.
    default_out = nanconv(a, k)
    assert default_out.dtype == np.float32
    assert np.all(np.isfinite(default_out))


# --------------------------------------------------------------------------- #
# convert_to_image on all-NaN + normalize=True must not raise                 #
# --------------------------------------------------------------------------- #
def test_convert_to_image_all_nan_normalize_returns_constant_image() -> None:
    x = np.full((4, 4), np.nan, dtype=np.float32)

    img = convert_to_image(x, normalize=True)

    assert img.dtype == np.uint8
    assert img.shape == (4, 4, 1)
    # An all-invalid raster degrades to a constant image.
    assert np.all(img == img.flat[0])


# --------------------------------------------------------------------------- #
# Breadth: replace_nan                                                        #
# --------------------------------------------------------------------------- #
def test_replace_nan_max_policy_fills_with_finite_max() -> None:
    x = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    out = replace_nan(x, "max")
    assert not np.any(np.isnan(out))
    assert out[0, 1] == pytest.approx(4.0)


def test_replace_nan_min_policy_fills_with_finite_min() -> None:
    x = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    out = replace_nan(x, "min")
    assert out[0, 1] == pytest.approx(1.0)


def test_replace_nan_float_literal_fills_with_value() -> None:
    x = np.array([[1.0, np.nan], [np.nan, 4.0]], dtype=np.float32)
    out = replace_nan(x, -7.0)
    assert out[0, 1] == pytest.approx(-7.0)
    assert out[1, 0] == pytest.approx(-7.0)


def test_replace_nan_no_nan_returns_unmodified_copy() -> None:
    x = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    out = replace_nan(x, "max")
    assert np.array_equal(out, x)
    assert out is not x  # must be a copy, not the caller's array


# --------------------------------------------------------------------------- #
# Breadth: to_gray                                                            #
# --------------------------------------------------------------------------- #
def test_to_gray_2d_passthrough_preserves_values() -> None:
    x = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    g = to_gray(x)
    assert g.shape == (2, 2)
    assert g.dtype == np.float32
    assert np.array_equal(g, x)


def test_to_gray_rgb_weights_sum_to_one_on_uniform_input() -> None:
    # Default rgb weights sum to 1.0, so a uniform RGB image maps to that value.
    x = np.full((2, 2, 3), 0.5, dtype=np.float32)
    g = to_gray(x)
    assert g.shape == (2, 2)
    np.testing.assert_allclose(g, 0.5, rtol=0, atol=1e-6)


def test_to_gray_integer_input_normalizes_to_unit_range() -> None:
    x = np.full((2, 2), 255, dtype=np.uint8)
    g = to_gray(x)
    np.testing.assert_allclose(g, 1.0, rtol=0, atol=1e-6)
