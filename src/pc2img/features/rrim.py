from __future__ import annotations

"""
RRIM utilities and feature registrations.

The implementation is intentionally image-space and NumPy-only so it fits the
existing raster derivative pipeline. Openness uses NaN-padded directional
shifts, which keeps border handling explicit and avoids wrap-around artefacts.
That shift kernel is also a clean target for future CuPy/CUDA acceleration if
RRIM becomes a benchmarking bottleneck.
"""

import re
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Callable, Literal

import numpy as np
from numpy.typing import NDArray

from .core import DerivativeFeatureStrategy
from .registry import FEATURES

RRIMComponent = Literal["slope", "positive", "negative", "structure"]

DEFAULT_BASE_FEATURE = "range"
DEFAULT_NUM_DIRECTIONS = 8
DEFAULT_MAX_DISTANCE = 16
DEFAULT_SLOPE_CLIP = (2.0, 98.0)
DEFAULT_STRUCTURE_CLIP = (2.0, 98.0)
DEFAULT_PIXEL_SIZE = (1.0, 1.0)
DEFAULT_Z_FACTOR = 1.0
DEFAULT_RED_STRENGTH = 1.0

_COMPONENT_TO_CHANNEL = {"positive": 0, "negative": 1, "structure": 2}

_MAX_DISTANCE_RE = re.compile(r"^r(?P<value>\d+)$")
_DIRECTIONS_RE = re.compile(r"^d(?P<value>\d+)$")
_SLOPE_CLIP_RE = re.compile(r"^sclip(?P<low>\d+(?:\.\d+)?)-(?P<high>\d+(?:\.\d+)?)$")
_STRUCTURE_CLIP_RE = re.compile(r"^oclip(?P<low>\d+(?:\.\d+)?)-(?P<high>\d+(?:\.\d+)?)$")
_Z_FACTOR_RE = re.compile(r"^z(?P<value>[+-]?\d+(?:\.\d+)?)$")
_RED_STRENGTH_RE = re.compile(r"^red(?P<value>[+-]?\d+(?:\.\d+)?)$")


@dataclass(frozen=True)
class RRIMConfig:
    """
    RRIM is implemented in image space for generic 2D rasters.

    This matches the existing derivative pipeline and keeps RRIM compatible with
    orthographic height rasters and scanner-centred range images. For spherical
    range images the result is an approximation because pixel spacing is angular
    rather than Euclidean.
    """

    base_feature: str = DEFAULT_BASE_FEATURE
    num_directions: int = DEFAULT_NUM_DIRECTIONS
    max_distance: int = DEFAULT_MAX_DISTANCE
    slope_clip: tuple[float, float] = DEFAULT_SLOPE_CLIP
    structure_clip: tuple[float, float] = DEFAULT_STRUCTURE_CLIP
    pixel_size: tuple[float, float] = DEFAULT_PIXEL_SIZE
    z_factor: float = DEFAULT_Z_FACTOR
    red_strength: float = DEFAULT_RED_STRENGTH

    def pack_feature_name(self) -> str:
        return (
            f"rrim_pack_({self.base_feature},"
            f"r{self.max_distance},d{self.num_directions},z{_format_number(self.z_factor)})"
        )


@dataclass(frozen=True)
class RRIMResult:
    slope: NDArray[np.float32]
    positive_openness: NDArray[np.float32]
    negative_openness: NDArray[np.float32]
    structure: NDArray[np.float32]
    rgb: NDArray[np.float32]


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return format(value, "g")


def _validate_clip(name: str, clip: tuple[float, float]) -> tuple[float, float]:
    low, high = clip
    if not (0.0 <= low <= 100.0 and 0.0 <= high <= 100.0):
        raise ValueError(f"{name} clip percentiles must lie within [0, 100], got {clip}.")
    if low > high:
        raise ValueError(f"{name} clip low percentile must not exceed high percentile, got {clip}.")
    return float(low), float(high)


def _validate_config(config: RRIMConfig) -> RRIMConfig:
    if config.num_directions < 1:
        raise ValueError("RRIM requires at least one direction.")
    if config.max_distance < 1:
        raise ValueError("RRIM max_distance must be >= 1.")
    if config.pixel_size[0] <= 0 or config.pixel_size[1] <= 0:
        raise ValueError(f"pixel_size values must be > 0, got {config.pixel_size}.")
    if config.z_factor <= 0:
        raise ValueError(f"z_factor must be > 0, got {config.z_factor}.")
    if config.red_strength < 0:
        raise ValueError(f"red_strength must be >= 0, got {config.red_strength}.")

    return replace(
        config,
        slope_clip=_validate_clip("slope", config.slope_clip),
        structure_clip=_validate_clip("structure", config.structure_clip),
    )


def _shift_with_fill(
    array: NDArray,
    dy: int,
    dx: int,
    *,
    fill_value: float | bool,
) -> NDArray:
    shifted = np.full(array.shape, fill_value, dtype=array.dtype)

    src_y_start = max(0, -dy)
    src_y_stop = array.shape[0] - max(0, dy)
    src_x_start = max(0, -dx)
    src_x_stop = array.shape[1] - max(0, dx)

    if src_y_start >= src_y_stop or src_x_start >= src_x_stop:
        return shifted

    dst_y_start = max(0, dy)
    dst_y_stop = array.shape[0] - max(0, -dy)
    dst_x_start = max(0, dx)
    dst_x_stop = array.shape[1] - max(0, -dx)

    shifted[dst_y_start:dst_y_stop, dst_x_start:dst_x_stop] = array[src_y_start:src_y_stop, src_x_start:src_x_stop]
    return shifted


def _safe_gradient(values: NDArray[np.float32], pixel_size: tuple[float, float]) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    grad_y = np.zeros_like(values, dtype=np.float32)
    grad_x = np.zeros_like(values, dtype=np.float32)

    if values.shape[0] > 1:
        grad_y = np.gradient(values, pixel_size[1], axis=0, edge_order=1).astype(np.float32, copy=False)
    if values.shape[1] > 1:
        grad_x = np.gradient(values, pixel_size[0], axis=1, edge_order=1).astype(np.float32, copy=False)

    return grad_y, grad_x


def _invalidate_adjacent_to_nans(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    invalid = mask.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        invalid |= _shift_with_fill(mask, dy, dx, fill_value=False)
    return invalid


def _normalize_robust(
    values: NDArray[np.float32],
    clip: tuple[float, float],
    *,
    fill_value: float,
) -> NDArray[np.float32]:
    normalized = np.full(values.shape, np.nan, dtype=np.float32)
    finite = np.isfinite(values)
    if not finite.any():
        return normalized

    low, high = np.nanpercentile(values[finite], clip)
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        normalized[finite] = fill_value
        return normalized

    normalized[finite] = np.clip((values[finite] - low) / (high - low), 0.0, 1.0).astype(np.float32, copy=False)
    return normalized


@lru_cache(maxsize=32)
def _build_ray_offsets(
    num_directions: int,
    max_distance: int,
    pixel_size: tuple[float, float],
) -> tuple[tuple[tuple[int, int, float], ...], ...]:
    directions: list[tuple[tuple[int, int, float], ...]] = []
    angles = np.linspace(0.0, 2.0 * np.pi, num_directions, endpoint=False, dtype=np.float64)

    for angle in angles:
        offsets: list[tuple[int, int, float]] = []
        seen: set[tuple[int, int]] = set()
        for step in range(1, max_distance + 1):
            dx = int(np.rint(np.cos(angle) * step))
            dy = int(np.rint(np.sin(angle) * step))
            offset = (dy, dx)
            if offset == (0, 0) or offset in seen:
                continue
            seen.add(offset)
            distance = float(np.hypot(dx * pixel_size[0], dy * pixel_size[1]))
            if distance > 0:
                offsets.append((dy, dx, distance))
        directions.append(tuple(offsets))

    return tuple(directions)


def compute_slope(
    values: NDArray,
    *,
    pixel_size: tuple[float, float] = DEFAULT_PIXEL_SIZE,
    z_factor: float = DEFAULT_Z_FACTOR,
) -> NDArray[np.float32]:
    raster = np.asarray(values, dtype=np.float32)
    finite = np.isfinite(raster)
    filled = np.where(finite, raster * z_factor, 0.0).astype(np.float32, copy=False)
    grad_y, grad_x = _safe_gradient(filled, pixel_size)
    slope = np.hypot(grad_x, grad_y).astype(np.float32, copy=False)
    slope[_invalidate_adjacent_to_nans(~finite)] = np.nan
    return slope


def compute_openness(
    values: NDArray,
    *,
    pixel_size: tuple[float, float] = DEFAULT_PIXEL_SIZE,
    num_directions: int = DEFAULT_NUM_DIRECTIONS,
    max_distance: int = DEFAULT_MAX_DISTANCE,
    z_factor: float = DEFAULT_Z_FACTOR,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    raster = np.asarray(values, dtype=np.float32)
    scaled = (raster * z_factor).astype(np.float32, copy=False)
    finite_center = np.isfinite(scaled)
    rays = _build_ray_offsets(num_directions, max_distance, pixel_size)

    positive_dirs: list[NDArray[np.float32]] = []
    negative_dirs: list[NDArray[np.float32]] = []

    for ray in rays:
        if not ray:
            continue

        max_upward = np.full(scaled.shape, -np.inf, dtype=np.float32)
        max_downward = np.full(scaled.shape, -np.inf, dtype=np.float32)
        has_sample = np.zeros(scaled.shape, dtype=bool)

        for dy, dx, distance in ray:
            shifted = _shift_with_fill(scaled, dy, dx, fill_value=np.nan)
            valid = finite_center & np.isfinite(shifted)
            if not np.any(valid):
                continue

            delta = shifted - scaled
            upward = np.degrees(np.arctan2(delta, distance)).astype(np.float32, copy=False)
            downward = np.degrees(np.arctan2(-delta, distance)).astype(np.float32, copy=False)

            max_upward = np.where(valid, np.maximum(max_upward, upward), max_upward)
            max_downward = np.where(valid, np.maximum(max_downward, downward), max_downward)
            has_sample |= valid

        positive = np.full(scaled.shape, np.nan, dtype=np.float32)
        negative = np.full(scaled.shape, np.nan, dtype=np.float32)
        positive[has_sample] = 90.0 - max_upward[has_sample]
        negative[has_sample] = 90.0 - max_downward[has_sample]
        positive_dirs.append(positive)
        negative_dirs.append(negative)

    if not positive_dirs:
        nan_result = np.full(scaled.shape, np.nan, dtype=np.float32)
        return nan_result, nan_result.copy()

    positive_stack = np.stack(positive_dirs, axis=-1)
    negative_stack = np.stack(negative_dirs, axis=-1)

    positive_counts = np.sum(np.isfinite(positive_stack), axis=-1)
    negative_counts = np.sum(np.isfinite(negative_stack), axis=-1)

    positive_openness = np.divide(
        np.nansum(positive_stack, axis=-1, dtype=np.float32),
        positive_counts,
        out=np.full(scaled.shape, np.nan, dtype=np.float32),
        where=positive_counts > 0,
    ).astype(np.float32, copy=False)
    negative_openness = np.divide(
        np.nansum(negative_stack, axis=-1, dtype=np.float32),
        negative_counts,
        out=np.full(scaled.shape, np.nan, dtype=np.float32),
        where=negative_counts > 0,
    ).astype(np.float32, copy=False)

    positive_openness[~finite_center] = np.nan
    negative_openness[~finite_center] = np.nan
    return positive_openness, negative_openness


def compose_rrim_rgb(
    slope: NDArray,
    structure: NDArray,
    *,
    slope_clip: tuple[float, float] = DEFAULT_SLOPE_CLIP,
    structure_clip: tuple[float, float] = DEFAULT_STRUCTURE_CLIP,
    red_strength: float = DEFAULT_RED_STRENGTH,
) -> NDArray[np.float32]:
    base = _normalize_robust(np.asarray(structure, dtype=np.float32), structure_clip, fill_value=0.5)
    slope_norm = _normalize_robust(np.asarray(slope, dtype=np.float32), slope_clip, fill_value=0.0)

    base_safe = np.nan_to_num(base, nan=0.0)
    slope_safe = np.nan_to_num(slope_norm, nan=0.0)
    red = np.clip(base_safe + red_strength * slope_safe * (1.0 - base_safe), 0.0, 1.0).astype(np.float32, copy=False)

    rgb = np.stack((red, base_safe, base_safe), axis=-1).astype(np.float32, copy=False)
    invalid = ~np.isfinite(base)
    rgb[invalid] = np.nan
    return rgb


def compute_rrim(
    values: NDArray,
    *,
    pixel_size: tuple[float, float] = DEFAULT_PIXEL_SIZE,
    num_directions: int = DEFAULT_NUM_DIRECTIONS,
    max_distance: int = DEFAULT_MAX_DISTANCE,
    slope_clip: tuple[float, float] = DEFAULT_SLOPE_CLIP,
    structure_clip: tuple[float, float] = DEFAULT_STRUCTURE_CLIP,
    z_factor: float = DEFAULT_Z_FACTOR,
    red_strength: float = DEFAULT_RED_STRENGTH,
) -> RRIMResult:
    """
    Compute RRIM-style terrain visualization products from a 2D raster.

    The computation is image-space and assumes pixel-sized spacing by default.
    This is appropriate for DEM-like rasters and a pragmatic approximation for
    scanner-centred range images.

    Opt-in registration
    --------------------
    RRIM is NOT part of the default feature barrel: importing `pc2img.features`
    does not register it. A caller MUST run `import pc2img.features.rrim` first,
    which executes the module-level `@FEATURES.register` decorators, before
    `generate(["rrim", ...])` will resolve the name. Installing the `rrim` pip
    extra alone does NOT register the feature — the extra only signposts optional
    deps; the explicit module import is what registers.

    Example
    -------
    `import pc2img.features.rrim  # opt-in: runs @FEATURES.register`
    `images = generator.generate(["rrim", "rrim_component_(structure,range,r24,d16)"])`
    `rrim_uint8 = images["rrim"].to_uint8()`
    """
    config = _validate_config(
        RRIMConfig(
            pixel_size=pixel_size,
            num_directions=num_directions,
            max_distance=max_distance,
            slope_clip=slope_clip,
            structure_clip=structure_clip,
            z_factor=z_factor,
            red_strength=red_strength,
        )
    )

    raster = np.asarray(values, dtype=np.float32)
    if raster.ndim != 2:
        raise ValueError(f"RRIM expects a 2D raster input, got shape {raster.shape}.")

    slope = compute_slope(raster, pixel_size=config.pixel_size, z_factor=config.z_factor)
    positive, negative = compute_openness(
        raster,
        pixel_size=config.pixel_size,
        num_directions=config.num_directions,
        max_distance=config.max_distance,
        z_factor=config.z_factor,
    )
    structure = (0.5 * (positive - negative)).astype(np.float32, copy=False)
    rgb = compose_rrim_rgb(
        slope,
        structure,
        slope_clip=config.slope_clip,
        structure_clip=config.structure_clip,
        red_strength=config.red_strength,
    )

    return RRIMResult(
        slope=slope,
        positive_openness=positive,
        negative_openness=negative,
        structure=structure,
        rgb=rgb,
    )


def _parse_option_token(config: RRIMConfig, token: str) -> RRIMConfig:
    match = _MAX_DISTANCE_RE.fullmatch(token)
    if match:
        return replace(config, max_distance=int(match.group("value")))

    match = _DIRECTIONS_RE.fullmatch(token)
    if match:
        return replace(config, num_directions=int(match.group("value")))

    match = _SLOPE_CLIP_RE.fullmatch(token)
    if match:
        return replace(config, slope_clip=(float(match.group("low")), float(match.group("high"))))

    match = _STRUCTURE_CLIP_RE.fullmatch(token)
    if match:
        return replace(config, structure_clip=(float(match.group("low")), float(match.group("high"))))

    match = _Z_FACTOR_RE.fullmatch(token)
    if match:
        return replace(config, z_factor=float(match.group("value")))

    match = _RED_STRENGTH_RE.fullmatch(token)
    if match:
        return replace(config, red_strength=float(match.group("value")))

    raise ValueError(
        f"Unknown RRIM option '{token}'. "
        "Supported tokens are rN, dN, sclipA-B, oclipA-B, zF and redF."
    )


def _looks_like_option_token(token: str) -> bool:
    return any(
        regex.fullmatch(token)
        for regex in (
            _MAX_DISTANCE_RE,
            _DIRECTIONS_RE,
            _SLOPE_CLIP_RE,
            _STRUCTURE_CLIP_RE,
            _Z_FACTOR_RE,
            _RED_STRENGTH_RE,
        )
    )


def _parse_rrim_config(args: str | None) -> RRIMConfig:
    tokens = [] if args is None else [token for token in DerivativeFeatureStrategy._split_top_level(args) if token]
    config = RRIMConfig()

    if tokens and not _looks_like_option_token(tokens[0]):
        config = replace(config, base_feature=tokens.pop(0))

    for token in tokens:
        config = _parse_option_token(config, token)

    return _validate_config(config)


def _parse_rrim_component(args: str) -> tuple[RRIMComponent, RRIMConfig]:
    tokens = [token for token in DerivativeFeatureStrategy._split_top_level(args) if token]
    if not tokens:
        raise ValueError("rrim_component requires at least a component name.")

    component = tokens.pop(0).lower()
    if component not in {"slope", "positive", "negative", "structure"}:
        raise ValueError(
            f"Unsupported RRIM component '{component}'. "
            "Expected one of: slope, positive, negative, structure."
        )

    config = RRIMConfig()
    if tokens and not _looks_like_option_token(tokens[0]):
        config = replace(config, base_feature=tokens.pop(0))
    for token in tokens:
        config = _parse_option_token(config, token)

    return component, _validate_config(config)


@FEATURES.register
class RRIMPackFeature(DerivativeFeatureStrategy):
    """
    Packs the (positive, negative, structure) openness components of RRIM.

    Opt-in: this feature is only registered after `import pc2img.features.rrim`
    runs the module-level `@FEATURES.register` side-effect. It is NOT in the
    default `pc2img.features` barrel, and enabling the `rrim` pip extra alone does
    not register it — the module import is what registers.
    """

    regex_pattern = re.compile(r"^rrim_pack_\((?P<args>.+)\)$")

    def __init__(self, args: str) -> None:
        self.config = _parse_rrim_config(args)
        self.dependencies = [self.config.base_feature]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray[np.float32]:
        values = np.asarray(fetch(self.config.base_feature), dtype=np.float32)
        positive, negative = compute_openness(
            values,
            pixel_size=self.config.pixel_size,
            num_directions=self.config.num_directions,
            max_distance=self.config.max_distance,
            z_factor=self.config.z_factor,
        )
        structure = (0.5 * (positive - negative)).astype(np.float32, copy=False)
        return np.stack((positive, negative, structure), axis=-1).astype(np.float32, copy=False)


@FEATURES.register
class RRIMFeature(DerivativeFeatureStrategy):
    """
    The `rrim` feature: a flat 2-D RGB red-relief raster (slope-red + openness).

    Opt-in registration contract: RRIM is deliberately kept OUT of the default
    `pc2img.features` barrel. `generate(["rrim", ...])` resolves only after the
    caller runs `import pc2img.features.rrim`, which triggers the import-time
    `@FEATURES.register` side-effect on this class. Installing the `rrim` pip
    extra does NOT import this module and does NOT register the feature; the extra
    only signposts optional runtime deps. The explicit module import is the sole
    thing that registers `rrim`.
    """

    regex_pattern = re.compile(r"^rrim(?:_\((?P<args>.+)\))?$")

    def __init__(self, args: str | None = None) -> None:
        self.config = _parse_rrim_config(args)
        self._pack_name = self.config.pack_feature_name()
        self.dependencies = [self.config.base_feature, self._pack_name]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray[np.float32]:
        values = np.asarray(fetch(self.config.base_feature), dtype=np.float32)
        pack = np.asarray(fetch(self._pack_name), dtype=np.float32)
        slope = compute_slope(values, pixel_size=self.config.pixel_size, z_factor=self.config.z_factor)
        structure = pack[..., _COMPONENT_TO_CHANNEL["structure"]]
        return compose_rrim_rgb(
            slope,
            structure,
            slope_clip=self.config.slope_clip,
            structure_clip=self.config.structure_clip,
            red_strength=self.config.red_strength,
        )


@FEATURES.register
class RRIMComponentFeature(DerivativeFeatureStrategy):
    """
    Exposes a single RRIM component (slope/positive/negative/structure) as a raster.

    Opt-in: like the other RRIM features, it is only registered after
    `import pc2img.features.rrim` runs the `@FEATURES.register` side-effect. It is
    NOT in the default barrel, and the `rrim` pip extra alone does not register it.
    """

    regex_pattern = re.compile(r"^rrim_component_\((?P<args>.+)\)$")

    def __init__(self, args: str) -> None:
        self.component, self.config = _parse_rrim_component(args)
        self._pack_name = self.config.pack_feature_name()
        self.dependencies = [self.config.base_feature] if self.component == "slope" else [self._pack_name]

    def compute(self, _, fetch: Callable[[str], NDArray]) -> NDArray[np.float32]:
        if self.component == "slope":
            values = np.asarray(fetch(self.config.base_feature), dtype=np.float32)
            return compute_slope(values, pixel_size=self.config.pixel_size, z_factor=self.config.z_factor)

        pack = np.asarray(fetch(self._pack_name), dtype=np.float32)
        return pack[..., _COMPONENT_TO_CHANNEL[self.component]].astype(np.float32, copy=False)
