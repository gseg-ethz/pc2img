import re
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import binary_dilation, gaussian_filter, sobel

from .core import DerivativeFeatureStrategy
from .registry import FEATURES


def _validate_percentile_bounds(low: float, high: float, *, strict: bool) -> None:
    """Validate a (low, high) percentile pair — the single source of the rule (G8).

    Enforces ``0 <= low <= 100`` and ``0 <= high <= 100``, then the ordering:
    ``low < high`` when ``strict`` else ``low <= high``. Raises ``ValueError`` on
    a violation; returns ``None`` on success.

    The ``strict`` flag is a DELIBERATE contract, not drift. ``NormalizedFeature``
    passes ``strict=True`` because a zero-width percentile range (``low == high``)
    divides by zero during normalization, so an equal pair is genuinely invalid
    there. ``ClipPercentileFeature`` and the RRIM clip validation pass
    ``strict=False`` because clipping to a single percentile is a well-defined
    (degenerate) operation. Centralizing the rule keeps the two contracts from
    silently diverging between call sites while preserving each site's outcome.
    """
    if not (0.0 <= low <= 100.0 and 0.0 <= high <= 100.0):
        raise ValueError(f"percentiles must lie within [0, 100], got low={low}, high={high}.")
    if strict:
        if not (low < high):
            raise ValueError(f"percentiles must satisfy low < high, got low={low}, high={high}.")
    elif low > high:
        raise ValueError(f"percentile low must not exceed high, got low={low}, high={high}.")


@FEATURES.register
class GradientFeature(DerivativeFeatureStrategy):
    """
    Computes the gradient of a base feature image along x or y.
    Dependencies: the base feature (will be treated as grid-level).

    Name syntax:
        gradient_<axis>_<base_feature>[_px<pixel_size>]   (axis ∈ {x, y})

    ``pixel_size`` is the ``np.gradient`` sample spacing; the reported gradient is
    scaled by ``1/pixel_size``. It defaults to ``100`` (KEPT-BEHAVIOR, D-07): every
    pre-existing ``gradient_..`` name that omits the ``_px`` suffix reproduces the
    historical ``1/100``-scaled output byte-for-byte. Supply ``_px<value>`` (or the
    ``pixel_size=`` constructor kwarg) to opt into a different spacing.

    Examples:
        gradient_x_range          → ∂/∂x with spacing 100 (historical default)
        gradient_x_range_px1      → ∂/∂x with unit spacing (opt-in)
    """

    regex_pattern = re.compile(
        r"^gradient_(?P<axis>[xy])_(?P<base_feature>.+?)"
        r"(?:_px(?P<pixel_size>\d+(?:\.\d+)?))?$"
    )

    def __init__(self, base_feature: str, axis: str, pixel_size: str | float | None = None) -> None:
        self.base_feature = base_feature
        self.axis = axis
        # Default 100 reproduces today's 1/100-scaled output byte-for-byte (D-07).
        self.pixel_size = 100.0 if pixel_size is None else float(pixel_size)
        if self.pixel_size <= 0:
            raise ValueError(f"pixel_size must be > 0, got {self.pixel_size}.")
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        ax = 1 if self.axis == "x" else 0
        grad = np.gradient(img, self.pixel_size, axis=ax)
        return grad


@FEATURES.register
class SobelFeature(DerivativeFeatureStrategy):
    """
    Computes the Sobel filter of a base feature image along x or y.
    Dependencies: the base feature (will be treated as grid-level).
    """

    regex_pattern = re.compile(r"^sobel_(?P<axis>[xy])_(?P<base_feature>.+)$")

    def __init__(self, base_feature: str, axis: str) -> None:
        self.base_feature = base_feature
        self.axis = axis
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:

        img = fetch(self.base_feature)
        ax = 1 if self.axis == "x" else 0
        sobel_img = sobel(img, axis=ax, mode="constant", cval=np.nan)
        return sobel_img


@FEATURES.register
class NormalizedFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(
        r"^normalized_(?P<base_feature>.+?)"
        r"(?:_(?P<low>\d+(?:\.\d+)?)_(?P<high>\d+(?:\.\d+)?))?$"
    )

    def __init__(self, base_feature: str, low: str | None = None, high: str | None = None) -> None:
        if low is None:
            low = "0"
        if high is None:
            high = "100"

        self.base_feature = base_feature
        self.dependencies = [base_feature]
        self.low = float(low)
        self.high = float(high)
        # M-12/G8: strict percentile bounds (a zero-width range divides by zero),
        # validated through the shared single-source helper.
        _validate_percentile_bounds(self.low, self.high, strict=True)

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        # DSN-03: copy-before-mutate so the fetched raster is never written in place.
        img = np.array(fetch(self.base_feature), copy=True)
        low_bound, high_bound = np.nanpercentile(img, [self.low, self.high])

        if high_bound - low_bound != 0:
            np.divide(img - low_bound, high_bound - low_bound, out=img)
        np.clip(img, 0, 1.0, out=img)
        return img


@FEATURES.register
class LogFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^log_(?P<base_feature>.+?)$")

    def __init__(self, base_feature: str) -> None:

        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.log10(img)


@FEATURES.register
class HillshadeFeature(DerivativeFeatureStrategy):
    """
    Hillshade of a base raster (Lambertian illumination).

    Name syntax:
        hillshade[_<base_feature>][_<azimuth>][_<altitude>][_<z_factor>]

    Convention note (M-11 / D-08, KEPT-BEHAVIOR): the illumination *magnitude*
    formula is algebraically equivalent to the ESRI hillshade, but the aspect axis
    here (``aspect = arctan2(-x, y)`` with ``x = ∂/∂row``, ``y = ∂/∂col``) is NOT
    north-up ESRI-compass aligned — it is rotated ≈90° relative to that convention.
    This is deliberate and downstream-validated; results are self-consistent under
    an azimuth sweep. Do not "correct" the aspect handedness without re-validating
    downstream consumers (a principled align-north option is a deferred improvement).
    """

    regex_pattern = re.compile(
        r"^hillshade"
        r"(?:_(?P<base_feature>.+?))?"
        r"(?:_(?P<azimuth>\d+(?:\.\d+)?))?"
        r"(?:_(?P<altitude>\d+(?:\.\d+)?))?"
        r"(?:_(?P<z_factor>\d+(?:\.\d+)?))?"
        r"$"
    )

    def __init__(
        self,
        base_feature: str | None = None,
        azimuth: str | None = None,
        altitude: str | None = None,
        z_factor: str | None = None,
    ) -> None:
        if base_feature is None:
            base_feature = "range"
        if azimuth is None:
            azimuth: float = 315.0
        if altitude is None:
            altitude: float = 45.0
        if z_factor is None:
            z_factor: float = 1.0

        self.base_feature = base_feature
        self.azimuth = float(azimuth)
        self.altitude = float(altitude)
        self.z_factor = float(z_factor)
        self.dependencies = [base_feature]

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        # Mirror __init__: the base_feature group is OPTIONAL and defaults to
        # "range" when absent (bare ``hillshade``). Preserve that so match() and
        # construction agree (DSN-05).
        base_feature = params.get("base_feature")
        return [base_feature if base_feature is not None else "range"]

    def compute(self, _, fetch) -> NDArray:
        values = fetch(self.base_feature)

        x, y = np.gradient(values * self.z_factor)
        slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
        aspect = np.arctan2(-x, y)
        azimuth_rad = self.azimuth * np.pi / 180.0
        altitude_rad = self.altitude * np.pi / 180.0

        shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(slope) * np.cos(
            azimuth_rad - aspect
        )

        return shaded


@FEATURES.register
class AverageFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^average_[(](?P<average_features>[^,]+(?:,[^,]+)+)[)]$")

    def __init__(self, average_features: str) -> None:
        self.average_features = type(self)._split_top_level(average_features)
        self.dependencies = self.average_features

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        # Mirror __init__: split this feature's own regex group (DSN-05).
        return cls._split_top_level(params["average_features"] or "")

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        values: list[NDArray] = [fetch(v) for v in self.average_features]
        need_3dim = any(v.ndim == 3 for v in values)

        if need_3dim:
            new_values = []
            for v in values:
                new_values.append(v if v.ndim == 3 else np.repeat(v[:, :, np.newaxis], 3, axis=-1))
            values = new_values

        stacked = np.stack(values, axis=-1)
        return np.average(stacked, axis=-1)


@FEATURES.register
class SumFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^sum_[(](?P<sum_features>[^,]+(?:,[^,]+)+)[)]$")

    def __init__(self, sum_features: str) -> None:
        self.sum_features = type(self)._split_top_level(sum_features)
        self.dependencies = self.sum_features

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        # Mirror __init__: split this feature's own regex group (DSN-05).
        return cls._split_top_level(params["sum_features"] or "")

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        values: list[NDArray] = [fetch(v) for v in self.sum_features]
        need_3dim = any(v.ndim == 3 for v in values)

        if need_3dim:
            new_values = []
            for v in values:
                new_values.append(v if v.ndim == 3 else np.repeat(v[:, :, np.newaxis], 3, axis=-1))
            values = new_values

        stacked = np.stack(values, axis=-1)
        return np.sum(stacked, axis=-1)


@FEATURES.register
class SquareFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^square_(?P<base_feature>.+?)$")

    def __init__(self, base_feature: str) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.square(img)


@FEATURES.register
class RootFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^sqrt_(?P<base_feature>.+?)$")

    def __init__(self, base_feature: str) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        img = fetch(self.base_feature)
        return np.sqrt(img)


@FEATURES.register
class NormFeature(DerivativeFeatureStrategy):
    regex_pattern = re.compile(r"^norm_[(](?P<norm_features>[^,]+(?:,[^,]+)+)[)]$")

    def __init__(self, norm_features: str) -> None:
        self.norm_features = type(self)._split_top_level(norm_features)
        self.dependencies = self.norm_features

    @classmethod
    def dependencies_for(cls, params: dict[str, str | None]) -> list[str]:
        # Mirror __init__: split this feature's own regex group (DSN-05).
        return cls._split_top_level(params["norm_features"] or "")

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        values: list[NDArray] = [fetch(v) for v in self.norm_features]
        need_3dim = any(v.ndim == 3 for v in values)

        if need_3dim:
            new_values = []
            for v in values:
                new_values.append(v if v.ndim == 3 else np.repeat(v[:, :, np.newaxis], 3, axis=-1))
            values = new_values

        stacked = np.stack(values, axis=-1)
        squared_sum = np.sum(stacked * stacked, axis=-1)
        return np.sqrt(squared_sum)


@FEATURES.register
class ClipPercentileFeature(DerivativeFeatureStrategy):
    """
    Clips a base raster between low/high percentiles.
    Example: clip_range_5_95
    """

    regex_pattern = re.compile(r"^clip_(?P<base_feature>.+?)_(?P<low>\d+(?:\.\d+)?)_(?P<high>\d+(?:\.\d+)?)$")

    def __init__(self, base_feature: str, low: str, high: str) -> None:
        self.low = float(low)
        self.high = float(high)
        # G8: non-strict bounds (clipping to a single percentile is well-defined),
        # validated through the shared single-source helper.
        _validate_percentile_bounds(self.low, self.high, strict=False)
        self.base_feature = base_feature
        self.dependencies = [base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        values = np.array(fetch(self.base_feature), dtype=np.float32, copy=True)
        if not np.isfinite(values).any():
            return values

        low_bound, high_bound = np.nanpercentile(values, [self.low, self.high])
        if low_bound == high_bound:
            # Avoid in-place operation to maintain original array when degenerate
            return np.clip(values, low_bound, high_bound)
        np.clip(values, low_bound, high_bound, out=values)
        return values


@FEATURES.register
class MultiScaleGradientFeature(DerivativeFeatureStrategy):
    """
    Computes scale-normalised gradients of a base raster at multiple Gaussian scales.
    Name syntax:
        multigrad_<base_feature>_<sigma1>-<sigma2>-...<sigmaN>[_<fuse>][_<norm|raw>]
        multigrad_<axis>_<base_feature>_<sigma1>-...   → axis-specific output (axis∈{x,y})
    Examples:
        multigrad_range_1-2-4              → max |∇| across σ∈{1,2,4} (default fuse)
        multigrad_range_1-2-4_mean         → mean |∇| across scales
        multigrad_x_range_1-2_mean         → mean ∂/∂x response across σ∈{1,2}
    """

    regex_pattern = re.compile(
        r"^multigrad_(?:(?P<axis>[xy])_)?(?P<base_feature>.+?)_"
        r"(?P<sigmas>\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)*)"
        r"(?:_(?P<options>[A-Za-z0-9_-]+))?$"
    )

    _FUSE_CHOICES = {"max", "sum", "mean"}

    def __init__(
        self,
        base_feature: str,
        sigmas: str,
        options: str | None = None,
        axis: str | None = None,
    ) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]
        self.axis = axis.lower() if axis is not None else None

        self.sigmas = [float(s) for s in sigmas.split("-")]
        if not self.sigmas:
            raise ValueError("At least one sigma must be provided for multigrad feature.")
        if any(sigma <= 0 for sigma in self.sigmas):
            raise ValueError(f"All sigmas must be > 0, got {self.sigmas}.")
        if self.axis is not None and self.axis not in {"x", "y"}:
            raise ValueError(f"Axis must be 'x' or 'y', got '{axis}'.")

        # Default behaviour
        self.fuse_mode = "max"
        self.scale_normalize = True
        self.include_components = True

        if options:
            for token in options.split("_"):
                token_lower = token.lower()
                if token_lower in self._FUSE_CHOICES:
                    self.fuse_mode = token_lower
                elif token_lower in {"raw", "nonorm"}:
                    self.scale_normalize = False
                elif token_lower in {"norm", "scale"}:
                    self.scale_normalize = True
                elif token_lower == "mag":
                    if self.axis is not None:
                        raise ValueError("Option 'mag' is incompatible with axis-specific multigrad outputs.")
                    self.include_components = False
                elif token_lower == "components":
                    if self.axis is not None:
                        raise ValueError("Option 'components' is incompatible with axis-specific multigrad outputs.")
                    self.include_components = True
                else:
                    raise ValueError(
                        f"Unknown option '{token}' for multigrad feature. "
                        f"Valid fuse modes: {sorted(self._FUSE_CHOICES)}; "
                        "options: 'norm', 'raw', 'mag', 'components'."
                    )

        if self.axis is not None:
            self.include_components = False
        elif self.fuse_mode != "stack" and self.include_components:
            # Fuse modes operate on magnitudes; components would break shape.
            self.include_components = False

        self._weight_eps = 1e-5
        self._gaussian_mode = "reflect"

    @staticmethod
    def _smooth_with_nan(
        image: NDArray[np.float32], sigma: float, mode: str, eps: float
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        mask = np.isfinite(image)
        if mask.all():
            smoothed = gaussian_filter(image, sigma=sigma, mode=mode)
            weights = np.ones_like(image, dtype=np.float32)
            return smoothed.astype(np.float32, copy=False), weights

        filled = np.where(mask, image, 0.0).astype(np.float32, copy=False)
        smoothed = gaussian_filter(filled, sigma=sigma, mode=mode)
        weights = gaussian_filter(mask.astype(np.float32), sigma=sigma, mode=mode)

        with np.errstate(invalid="ignore", divide="ignore"):
            smoothed = np.divide(
                smoothed,
                weights,
                out=np.zeros_like(smoothed, dtype=np.float32),
                where=weights > eps,
            )
        smoothed = smoothed.astype(np.float32, copy=False)
        smoothed[weights <= eps] = np.nan
        return smoothed, weights.astype(np.float32, copy=False)

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        base = fetch(self.base_feature)
        img = np.array(base, dtype=np.float32, copy=True)

        if img.ndim != 2:
            raise ValueError(f"multigrad expects a 2D raster input; '{self.base_feature}' has shape {img.shape}")

        stacked_channels: list[NDArray[np.float32]] = []
        fuse_layers: list[NDArray[np.float32]] = []

        for sigma in self.sigmas:
            smoothed, weights = self._smooth_with_nan(img, sigma, self._gaussian_mode, self._weight_eps)
            # Fill NaNs temporarily for gradient calculation.
            smoothed_finite = np.nan_to_num(smoothed, nan=0.0)
            grad_y, grad_x = np.gradient(smoothed_finite, edge_order=1)
            grad_x = grad_x.astype(np.float32, copy=False)
            grad_y = grad_y.astype(np.float32, copy=False)

            if self.scale_normalize:
                grad_x *= sigma
                grad_y *= sigma

            valid = weights > self._weight_eps
            invalid = ~valid
            grad_x[invalid] = np.nan
            grad_y[invalid] = np.nan

            if self.axis is not None:
                component = grad_x if self.axis == "x" else grad_y
                if self.fuse_mode == "stack":
                    stacked_channels.append(component)
                else:
                    fuse_layers.append(component)
            else:
                grad_mag = np.hypot(grad_x, grad_y).astype(np.float32, copy=False)
                if self.fuse_mode == "stack":
                    if self.include_components:
                        stacked_channels.extend((grad_x, grad_y, grad_mag))
                    else:
                        stacked_channels.append(grad_mag)
                else:
                    fuse_layers.append(grad_mag)

        if self.fuse_mode == "stack":
            if not stacked_channels:
                raise RuntimeError("No channels computed for stacking; check configuration.")
            stacked = np.stack(stacked_channels, axis=-1)
            return stacked.astype(np.float32, copy=False)

        if not fuse_layers:
            raise RuntimeError("No layers computed for fusion; check configuration.")

        mags = np.stack(fuse_layers, axis=-1)
        if self.fuse_mode == "max":
            with np.errstate(invalid="ignore"):
                fused = np.nanmax(mags, axis=-1)
        elif self.fuse_mode == "mean":
            with np.errstate(invalid="ignore"):
                fused = np.nanmean(mags, axis=-1)
        elif self.fuse_mode == "sum":
            with np.errstate(invalid="ignore"):
                fused = np.nansum(mags, axis=-1)
        else:
            raise ValueError(f"Unsupported fuse mode '{self.fuse_mode}'")

        return fused.astype(np.float32, copy=False)


@FEATURES.register
class OcclusionAwareMultiScaleGradientFeature(DerivativeFeatureStrategy):
    """
    Multi-scale gradient with occlusion-aware smoothing and gating.
    Name syntax:
        multigradocc_<base_feature>_<sigma1>-...[_<options>]
        multigradocc_<axis>_<base_feature>_<sigma1>-...[_<options>]

    Options (underscore separated, all optional):
        - max | mean | sum     → choose fusion across scales (default=max).
        - raw | nonorm         → disable scale normalisation.
        - norm | scale         → force-enable scale normalisation.
        - threshX.Y            → gradient threshold for occlusion mask (default 1.0).
        - sigmaeZ.Z            → Gaussian sigma for edge strength smoothing (default 0.0).
        - dilateN              → binary dilation iterations on occlusion mask (default 1).
        - soft or softQ.Q      → retain occlusion pixels with weight (default 0.3 if 'soft').
        - mask                 → append occlusion mask as extra channel.
    """

    regex_pattern = re.compile(
        r"^multigradocc_(?:(?P<axis>[xy])_)?(?P<base_feature>.+?)_"
        r"(?P<sigmas>\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)*)"
        r"(?:_(?P<options>[A-Za-z0-9._-]+))?$"
    )

    _FUSE_CHOICES = {"max", "sum", "mean"}

    def __init__(
        self,
        base_feature: str,
        sigmas: str,
        options: str | None = None,
        axis: str | None = None,
    ) -> None:
        self.base_feature = base_feature
        self.dependencies = [base_feature]
        self.axis = axis.lower() if axis is not None else None

        self.sigmas = [float(s) for s in sigmas.split("-")]
        if not self.sigmas:
            raise ValueError("At least one sigma must be provided for multigradocc feature.")
        if any(sigma <= 0 for sigma in self.sigmas):
            raise ValueError(f"All sigmas must be > 0, got {self.sigmas}.")
        if self.axis is not None and self.axis not in {"x", "y"}:
            raise ValueError(f"Axis must be 'x' or 'y', got '{axis}'.")

        self.fuse_mode = "max"
        self.scale_normalize = True
        self.include_components = False  # not exposed for occlusion variant

        # Occlusion specific defaults
        self.edge_threshold = 1.0
        self.edge_sigma = 0.0
        self.edge_dilate = 1
        self.soft_weight = None  # None → hard mask
        self.return_mask = False

        if options:
            for token in options.split("_"):
                token_lower = token.lower()
                if token_lower in self._FUSE_CHOICES:
                    self.fuse_mode = token_lower
                elif token_lower in {"raw", "nonorm"}:
                    self.scale_normalize = False
                elif token_lower in {"norm", "scale"}:
                    self.scale_normalize = True
                elif token_lower.startswith("thresh"):
                    try:
                        self.edge_threshold = float(token_lower.removeprefix("thresh"))
                    except ValueError as exc:
                        raise ValueError(f"Invalid thresh token '{token}'.") from exc
                elif token_lower.startswith("sigmae"):
                    try:
                        self.edge_sigma = float(token_lower.removeprefix("sigmae"))
                    except ValueError as exc:
                        raise ValueError(f"Invalid sigmae token '{token}'.") from exc
                elif token_lower.startswith("dilate"):
                    try:
                        dil = int(float(token_lower.removeprefix("dilate")))
                    except ValueError as exc:
                        raise ValueError(f"Invalid dilate token '{token}'.") from exc
                    if dil < 0:
                        raise ValueError("dilate iterations must be >= 0.")
                    self.edge_dilate = dil
                elif token_lower == "soft":
                    self.soft_weight = 0.3
                elif token_lower.startswith("soft"):
                    try:
                        self.soft_weight = float(token_lower.removeprefix("soft"))
                    except ValueError as exc:
                        raise ValueError(f"Invalid soft token '{token}'.") from exc
                    if not (0.0 <= self.soft_weight <= 1.0):
                        raise ValueError("soft weight must be between 0 and 1.")
                elif token_lower == "mask":
                    self.return_mask = True
                else:
                    valid_modes = ", ".join(sorted(self._FUSE_CHOICES))
                    raise ValueError(
                        f"Unknown option '{token}' for multigradocc feature. "
                        f"Valid fuse modes: {valid_modes}; "
                        "options: 'raw', 'norm', 'threshX', 'sigmaeX', 'dilateN', 'soft[W]', 'mask'."
                    )

        if self.axis is not None and self.return_mask:
            # including mask still ok, but ensure soft gating respects axis
            pass

        if self.edge_threshold < 0:
            raise ValueError("thresh value must be >= 0.")
        if self.edge_sigma < 0:
            raise ValueError("sigmae value must be >= 0.")
        if self.soft_weight is not None and not (0.0 <= self.soft_weight <= 1.0):
            raise ValueError("soft weight must be within [0, 1].")

        self._weight_eps = 1e-5
        self._gaussian_mode = "reflect"

    @staticmethod
    def _safe_nan_to_num(arr: NDArray[np.float32]) -> NDArray[np.float32]:
        return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    def _estimate_occlusion_mask(self, img: NDArray[np.float32]) -> NDArray[np.bool_]:
        finite = self._safe_nan_to_num(img.astype(np.float32, copy=True))
        grad_y, grad_x = np.gradient(finite, edge_order=1)
        edge_strength = np.hypot(grad_x, grad_y).astype(np.float32, copy=False)
        if self.edge_sigma > 0:
            edge_strength = gaussian_filter(edge_strength, sigma=self.edge_sigma, mode=self._gaussian_mode)
        mask = edge_strength >= self.edge_threshold
        if self.edge_dilate > 0:
            structure = np.ones((3, 3), dtype=bool)
            mask = binary_dilation(mask, structure=structure, iterations=self.edge_dilate)
        mask |= ~np.isfinite(img)
        return mask

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray:
        base = fetch(self.base_feature)
        img = np.array(base, dtype=np.float32, copy=True)
        if img.ndim != 2:
            raise ValueError(f"multigradocc expects a 2D raster input; '{self.base_feature}' has shape {img.shape}")

        occlusion_mask = self._estimate_occlusion_mask(img)

        stacked_channels: list[NDArray[np.float32]] = []

        for sigma in self.sigmas:
            masked_input = img.copy()
            masked_input[occlusion_mask] = np.nan
            smoothed, weights = MultiScaleGradientFeature._smooth_with_nan(
                masked_input, sigma, self._gaussian_mode, self._weight_eps
            )
            smoothed_finite = self._safe_nan_to_num(smoothed)
            grad_y, grad_x = np.gradient(smoothed_finite, edge_order=1)
            grad_x = grad_x.astype(np.float32, copy=False)
            grad_y = grad_y.astype(np.float32, copy=False)

            if self.scale_normalize:
                grad_x *= sigma
                grad_y *= sigma

            valid = weights > self._weight_eps
            invalid = ~valid
            grad_x[invalid] = np.nan
            grad_y[invalid] = np.nan

            if self.soft_weight is None:
                grad_x[occlusion_mask] = np.nan
                grad_y[occlusion_mask] = np.nan
            else:
                grad_x[occlusion_mask] *= self.soft_weight
                grad_y[occlusion_mask] *= self.soft_weight

            if self.axis is not None:
                component = grad_x if self.axis == "x" else grad_y
                stacked_channels.append(component)
            else:
                grad_mag = np.hypot(grad_x, grad_y).astype(np.float32, copy=False)
                stacked_channels.append(grad_mag)

        if not stacked_channels:
            raise RuntimeError("No channels computed for occlusion-aware multigrad.")

        stack = np.stack(stacked_channels, axis=-1)

        if self.fuse_mode == "max":
            with np.errstate(invalid="ignore"):
                fused = np.nanmax(stack, axis=-1)
        elif self.fuse_mode == "mean":
            with np.errstate(invalid="ignore"):
                fused = np.nanmean(stack, axis=-1)
        elif self.fuse_mode == "sum":
            with np.errstate(invalid="ignore"):
                fused = np.nansum(stack, axis=-1)
        else:
            raise ValueError(f"Unsupported fuse mode '{self.fuse_mode}'")

        fused = fused.astype(np.float32, copy=False)

        if self.return_mask:
            mask_out = occlusion_mask.astype(np.float32)
            return np.stack((fused, mask_out), axis=-1)

        return fused
