from typing import Literal

import numpy as np
from numpy.typing import DTypeLike, NDArray
from scipy.signal import convolve2d

ALL_CMAPS = Literal[
    "magma",
    "inferno",
    "plasma",
    "viridis",
    "cividis",
    "twilight",
    "twilight_shifted",
    "turbo",
    "berlin",
    "managua",
    "vanimo",
    "Blues",
    "BrBG",
    "BuGn",
    "BuPu",
    "CMRmap",
    "GnBu",
    "Greens",
    "Greys",
    "OrRd",
    "Oranges",
    "PRGn",
    "PiYG",
    "PuBu",
    "PuBuGn",
    "PuOr",
    "PuRd",
    "Purples",
    "RdBu",
    "RdGy",
    "RdPu",
    "RdYlBu",
    "RdYlGn",
    "Reds",
    "Spectral",
    "Wistia",
    "YlGn",
    "YlGnBu",
    "YlOrBr",
    "YlOrRd",
    "afmhot",
    "autumn",
    "binary",
    "bone",
    "brg",
    "bwr",
    "cool",
    "coolwarm",
    "copper",
    "cubehelix",
    "flag",
    "gist_earth",
    "gist_gray",
    "gist_heat",
    "gist_ncar",
    "gist_rainbow",
    "gist_stern",
    "gist_yarg",
    "gnuplot",
    "gnuplot2",
    "gray",
    "hot",
    "hsv",
    "jet",
    "nipy_spectral",
    "ocean",
    "pink",
    "prism",
    "rainbow",
    "seismic",
    "spring",
    "summer",
    "terrain",
    "winter",
    "Accent",
    "Dark2",
    "Paired",
    "Pastel1",
    "Pastel2",
    "Set1",
    "Set2",
    "Set3",
    "tab10",
    "tab20",
    "tab20b",
    "tab20c",
    "grey",
    "gist_grey",
    "gist_yerg",
    "Grays",
    "magma_r",
    "inferno_r",
    "plasma_r",
    "viridis_r",
    "cividis_r",
    "twilight_r",
    "twilight_shifted_r",
    "turbo_r",
    "berlin_r",
    "managua_r",
    "vanimo_r",
    "Blues_r",
    "BrBG_r",
    "BuGn_r",
    "BuPu_r",
    "CMRmap_r",
    "GnBu_r",
    "Greens_r",
    "Greys_r",
    "OrRd_r",
    "Oranges_r",
    "PRGn_r",
    "PiYG_r",
    "PuBu_r",
    "PuBuGn_r",
    "PuOr_r",
    "PuRd_r",
    "Purples_r",
    "RdBu_r",
    "RdGy_r",
    "RdPu_r",
    "RdYlBu_r",
    "RdYlGn_r",
    "Reds_r",
    "Spectral_r",
    "Wistia_r",
    "YlGn_r",
    "YlGnBu_r",
    "YlOrBr_r",
    "YlOrRd_r",
    "afmhot_r",
    "autumn_r",
    "binary_r",
    "bone_r",
    "brg_r",
    "bwr_r",
    "cool_r",
    "coolwarm_r",
    "copper_r",
    "cubehelix_r",
    "flag_r",
    "gist_earth_r",
    "gist_gray_r",
    "gist_heat_r",
    "gist_ncar_r",
    "gist_rainbow_r",
    "gist_stern_r",
    "gist_yarg_r",
    "gnuplot_r",
    "gnuplot2_r",
    "gray_r",
    "hot_r",
    "hsv_r",
    "jet_r",
    "nipy_spectral_r",
    "ocean_r",
    "pink_r",
    "prism_r",
    "rainbow_r",
    "seismic_r",
    "spring_r",
    "summer_r",
    "terrain_r",
    "winter_r",
    "Accent_r",
    "Dark2_r",
    "Paired_r",
    "Pastel1_r",
    "Pastel2_r",
    "Set1_r",
    "Set2_r",
    "Set3_r",
    "tab10_r",
    "tab20_r",
    "tab20b_r",
    "tab20c_r",
    "grey_r",
    "gist_grey_r",
    "gist_yerg_r",
    "Grays_r",
]

NAN_REPLACEMENT_STR = Literal["max", "min", "random"]


def nanconv(
    a: NDArray,
    k: NDArray,
    replace_nan: float | None = None,
    *,
    compute_dtype: DTypeLike = np.float32,
) -> NDArray:
    """NaN-aware normalized 2D convolution.

    Convolves ``a`` with kernel ``k`` while ignoring NaN entries (normalized
    convolution: the kernel is applied to a zero-filled copy and re-normalized by
    the convolved validity mask), so NaNs neither propagate nor bias the result.

    Parameters
    ----------
    a:
        2D input array; NaNs mark invalid samples.
    k:
        2D convolution kernel.
    replace_nan:
        If given, output NaNs (pixels with no valid support) are replaced with
        this value in place of the accumulator.
    compute_dtype:
        Accumulation/division dtype (PERF-02 reduced-precision opt-in, D-03). The
        default ``np.float32`` is the correctness path: it never overflows on
        realistic range/elevation magnitudes and reproduces the mandatory M-08 fix
        byte-for-byte. Pass a reduced-precision dtype (e.g. ``np.float16``) only
        when the caller explicitly wants to trade accuracy/range for memory.

    Notes
    -----
    The caller's ``a`` is never mutated: NaNs are zeroed on a fresh copy (M-07).
    """
    dtype = np.dtype(compute_dtype)

    n = np.isnan(a)
    # M-07: fill NaNs on a fresh buffer so the caller's array is left untouched.
    a_filled = np.where(n, 0.0, a).astype(dtype, copy=False)
    on = np.ones(a.shape, dtype=dtype)
    on[n] = 0

    # M-08 / D-09: accumulate + divide in ``compute_dtype`` (float32 by default).
    # float16's ~65504 ceiling overflows to inf on ordinary summed range values;
    # float32 buys correctness at no CPU cost. Reduced precision engages only when
    # the caller opts in via ``compute_dtype`` (PERF-02).
    flat = convolve2d(on, k, mode="same").astype(dtype)

    c = np.full(flat.shape, np.nan, dtype=dtype)
    np.divide(convolve2d(a_filled, k, mode="same").astype(dtype), flat, out=c, where=(flat != 0))
    if replace_nan is not None:
        np.nan_to_num(c, copy=False, nan=replace_nan)
    return c


def gaussian_kernel(side_length=5, sig=1.0):
    """
    creates gaussian kernel with side length `side_length` and a sigma of `sig`
    """
    ax = np.linspace(-(side_length - 1) / 2.0, (side_length - 1) / 2.0, side_length)
    gauss = np.exp(-0.5 * np.square(ax) / np.square(sig))
    kernel = np.outer(gauss, gauss)
    return kernel / np.sum(kernel)


def replace_nan(
    image_data: NDArray[np.floating] | NDArray[np.integer],
    replace_nan_with: NAN_REPLACEMENT_STR | float = "max",
    *,
    rng: np.random.Generator | int | None = None,
) -> NDArray[np.floating]:
    """
    Replace NaNs in a 2D/3D array.

    - If `replace_nan_with` is a float, use that literal value.
    - Else use {"max","min","random"} computed over finite values per-channel.
    - For 3D input, replacement is broadcast channel-wise.
    """
    x = np.asarray(image_data)
    out = x.astype(np.float32, copy=True)

    isnan = np.isnan(out)
    if not np.any(isnan):
        return out

    # Build RNG if needed
    if replace_nan_with == "random":
        if isinstance(rng, int):
            rng = np.random.default_rng(rng)
        elif rng is None:
            rng = np.random.default_rng()

    # Per-channel stats for 3D, scalar for 2D
    if out.ndim == 3:
        mins = np.nanmin(out, axis=(0, 1))
        maxs = np.nanmax(out, axis=(0, 1))
        if isinstance(replace_nan_with, float):
            fill = np.full_like(out, replace_nan_with, dtype=np.float32)
        elif replace_nan_with == "max":
            fill = np.broadcast_to(maxs, out.shape).astype(np.float32)
        elif replace_nan_with == "min":
            fill = np.broadcast_to(mins, out.shape).astype(np.float32)
        elif replace_nan_with == "random":
            H, W, C = out.shape
            lows = np.broadcast_to(mins, (H, W, C)).astype(np.float32)
            highs = np.broadcast_to(maxs, (H, W, C)).astype(np.float32)
            fill = rng.uniform(lows, highs).astype(np.float32)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown policy {replace_nan_with!r}")
    else:
        # 2D
        mn = np.nanmin(out)
        mx = np.nanmax(out)
        if isinstance(replace_nan_with, float):
            fill = np.full_like(out, replace_nan_with, dtype=np.float32)
        elif replace_nan_with == "max":
            fill = np.full_like(out, mx, dtype=np.float32)
        elif replace_nan_with == "min":
            fill = np.full_like(out, mn, dtype=np.float32)
        elif replace_nan_with == "random":
            fill = np.random.default_rng(rng).uniform(mn, mx, size=out.shape).astype(np.float32)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown policy {replace_nan_with!r}")

    out[isnan] = fill[isnan]
    return out


def to_gray(
    a: NDArray,
    *,
    channel_axis: int | None = -1,
    normalize_ints: bool = True,
    out_dtype: type[np.floating] = np.float32,
    nan_policy: Literal["keep", "min", "max", "random"] = "keep",
    rgb_weights: tuple[float, float, float] = (0.299, 0.587, 0.114),
) -> NDArray[np.floating]:
    """
    Convert an image to 2D grayscale float array.

    - If `a` is 2D: just cast/normalize and return.
    - If `a` is 3D: assume RGB(A) on `channel_axis`. Alpha is ignored.
    - If integer dtype and normalize_ints=True: scale to [0,1] using dtype max.
    - NaNs: leave as-is ("keep") or fill via your existing strategy.

    Returns a float32 (by default) HxW array.
    """
    x = np.asarray(a)

    # Move channel axis to last for simplicity (only if present)
    if channel_axis is not None:
        if x.ndim < 2:
            raise ValueError(f"Expected 2D/3D array, got shape {x.shape}")
        if channel_axis < 0:
            channel_axis = x.ndim + channel_axis
        if x.ndim == 3 and channel_axis != x.ndim - 1:
            x = np.moveaxis(x, channel_axis, -1)

    # Scale integers to [0,1] if requested
    if np.issubdtype(x.dtype, np.integer) and normalize_ints:
        info = np.iinfo(x.dtype)
        x = x.astype(out_dtype, copy=False) / float(info.max)
    else:
        x = x.astype(out_dtype, copy=False)

    if x.ndim == 2:
        g = x
    elif x.ndim == 3:
        C = x.shape[-1]
        if C < 3:
            raise ValueError(f"Expected >=3 channels for RGB, got {C}")
        r, gch, b = x[..., 0], x[..., 1], x[..., 2]
        wr, wg, wb = rgb_weights
        g = wr * r + wg * gch + wb * b
    else:
        raise ValueError(f"Expected 2D/3D array, got shape {x.shape}")

    if nan_policy != "keep":
        g = replace_nan(g, nan_policy)

    return g


def convert_to_image(
    image_data: NDArray,
    *,
    replace_nan_with: NAN_REPLACEMENT_STR | float = "max",
    normalize: bool = False,
    colormap: ALL_CMAPS | None = None,
    channel_axis: int | None = -1,
    normalize_ints: bool = True,
) -> NDArray[np.uint8]:
    """
    Convert 2D or 3D array to uint8 image.

    - If colormap is provided: expects a 2D array; if 3D, we first gray it via channel average.
    - NaNs are filled using `replace_nan_with` **before** normalization.
    - Integers are scaled to [0,1] if `normalize_ints=True`.
    - If `normalize=True` or data not already in [0,1], min-max normalize on finite values.
    """
    x = np.asarray(image_data)

    # If 3D with colormap: reduce to gray for mapping
    if colormap is not None and x.ndim == 3:
        # quick, dependency-free grayscale for display: mean over channels
        if channel_axis is not None and channel_axis != x.ndim - 1:
            x = np.moveaxis(x, channel_axis, -1)
        x = x.astype(np.float32, copy=False)
        x = x.mean(axis=-1)

    # Handle integer input scaling
    if np.issubdtype(x.dtype, np.integer) and normalize_ints:
        info = np.iinfo(x.dtype)
        x = x.astype(np.float32) / float(info.max)
    else:
        x = x.astype(np.float32, copy=False)

    # Replace NaNs first (works for 2D or 3D)
    x = replace_nan(x, replace_nan_with)

    # Normalize if requested or out of [0,1]
    finite = np.isfinite(x)
    if normalize or (x[finite].min(initial=0.0) < 0.0) or (x[finite].max(initial=1.0) > 1.0):
        # M-09: an all-invalid raster has no finite values to reduce over; degrade
        # to a constant/zero image instead of crashing on the empty min/max.
        if not finite.any():
            x = np.zeros_like(x, dtype=np.float32)  # constant image (no finite data)
        else:
            lo = x[finite].min()
            hi = x[finite].max()
            if hi > lo:
                x = (x - lo) / (hi - lo)
            else:
                x = np.zeros_like(x, dtype=np.float32)  # constant image

    if colormap is not None:
        try:
            import matplotlib.pyplot as plt
        except Exception as e:
            raise RuntimeError("Colormap requires matplotlib") from e

        if x.ndim != 2:
            raise ValueError("colormap requires a 2D array after grayscale conversion.")
        cmap = plt.get_cmap(colormap)
        rgb = cmap(x)[..., :3]  # float in [0,1]
        return (rgb * 255.0 + 0.5).astype(np.uint8)

    # If 2D, expand to 1-channel; if 3D, assume channels last
    if x.ndim == 2:
        x = np.expand_dims(x, axis=-1)  # HxW×1

    return (x * 255.0 + 0.5).astype(np.uint8)


def calculate_dip_direction_and_angle(xyz: np.ndarray) -> np.ndarray:
    # Normalize the vectors
    norms = np.linalg.norm(xyz, axis=1, keepdims=True)
    norm_vectors = xyz / norms

    # Projection on the XY plane (z-component is zero)
    xy_projection = np.concatenate((norm_vectors[:, :2], np.zeros_like(norms)), axis=1)

    # Calculate dip angles
    # Angle between the vector and its projection on the XY plane
    dip_angles = np.arccos(np.sum(norm_vectors * xy_projection, axis=1) / np.linalg.norm(xy_projection, axis=1))

    # Calculate dip directions
    # Azimuth of the projection of the vector onto the XY plane
    dip_directions = np.arctan2(norm_vectors[:, 1], norm_vectors[:, 0])

    return np.column_stack((dip_angles, dip_directions))


class OpticalFlowVisualization:
    @staticmethod
    def make_colorwheel():
        """
        Generates a color wheel for optical flow visualization as presented in:
            Baker et al. "A Database and Evaluation Methodology for Optical Flow" (ICCV, 2007)
            URL: http://vision.middlebury.edu/flow/flowEval-iccv07.pdf

        Code follows the original C++ source code of Daniel Scharstein.
        Code follows the Matlab source code of Deqing Sun.

        Returns:
            np.ndarray: Color wheel
        """

        RY = 15
        YG = 6
        GC = 4
        CB = 11
        BM = 13
        MR = 6

        ncols = RY + YG + GC + CB + BM + MR
        colorwheel = np.zeros((ncols, 3))
        col = 0

        # RY
        colorwheel[0:RY, 0] = 255
        colorwheel[0:RY, 1] = np.floor(255 * np.arange(0, RY) / RY)
        col = col + RY
        # YG
        colorwheel[col : col + YG, 0] = 255 - np.floor(255 * np.arange(0, YG) / YG)
        colorwheel[col : col + YG, 1] = 255
        col = col + YG
        # GC
        colorwheel[col : col + GC, 1] = 255
        colorwheel[col : col + GC, 2] = np.floor(255 * np.arange(0, GC) / GC)
        col = col + GC
        # CB
        colorwheel[col : col + CB, 1] = 255 - np.floor(255 * np.arange(CB) / CB)
        colorwheel[col : col + CB, 2] = 255
        col = col + CB
        # BM
        colorwheel[col : col + BM, 2] = 255
        colorwheel[col : col + BM, 0] = np.floor(255 * np.arange(0, BM) / BM)
        col = col + BM
        # MR
        colorwheel[col : col + MR, 2] = 255 - np.floor(255 * np.arange(MR) / MR)
        colorwheel[col : col + MR, 0] = 255
        return colorwheel

    def flow_uv_to_colors(self, u, v, convert_to_bgr=False):
        """
        Applies the flow color wheel to (possibly clipped) flow components u and v.

        According to the C++ source code of Daniel Scharstein
        According to the Matlab source code of Deqing Sun

        Args:
            u (np.ndarray): Input horizontal flow of shape [H,W]
            v (np.ndarray): Input vertical flow of shape [H,W]
            convert_to_bgr (bool, optional): Convert output image to BGR. Defaults to False.

        Returns:
            np.ndarray: Flow visualization image of shape [H,W,3]
        """
        flow_image = np.zeros((u.shape[0], u.shape[1], 3), np.uint8)
        colorwheel = self.make_colorwheel()  # shape [55x3]
        ncols = colorwheel.shape[0]
        rad = np.sqrt(np.square(u) + np.square(v))
        a = np.arctan2(-v, -u) / np.pi
        fk = (a + 1) / 2 * (ncols - 1)
        k0 = np.floor(fk).astype(np.int32)
        k1 = k0 + 1
        k1[k1 == ncols] = 0
        f = fk - k0
        for i in range(colorwheel.shape[1]):
            tmp = colorwheel[:, i]
            col0 = tmp[k0] / 255.0
            col1 = tmp[k1] / 255.0
            col = (1 - f) * col0 + f * col1
            idx = rad <= 1
            col[idx] = 1 - rad[idx] * (1 - col[idx])
            col[~idx] = col[~idx] * 0.75  # out of range
            # Note the 2-i => BGR instead of RGB
            ch_idx = 2 - i if convert_to_bgr else i
            flow_image[:, :, ch_idx] = np.floor(255 * col)
        return flow_image

    def flow_to_image(
        self,
        flow_uv,
        clip_flow=None,
        convert_to_bgr=False,
        max_quantile: float | None = None,
    ):
        """
        Expects a two dimensional flow image of shape.

        Args:
            flow_uv (np.ndarray): Flow UV image of shape [H,W,2]
            clip_flow (float, optional): Clip maximum of flow values. Defaults to None.
            convert_to_bgr (bool, optional): Convert output image to BGR. Defaults to False.

        Returns:
            np.ndarray: Flow visualization image of shape [H,W,3]
        """
        assert flow_uv.ndim == 3, "input flow must have three dimensions"
        assert flow_uv.shape[2] == 2, "input flow must have shape [H,W,2]"
        epsilon = 1e-5

        if clip_flow is not None:
            flow_uv = np.clip(flow_uv, 0, clip_flow)
        rad = np.linalg.norm(flow_uv, axis=2, keepdims=True)
        uv_unit = flow_uv / (rad + epsilon)

        rad_max = np.max(rad) if max_quantile is None else np.quantile(rad, max_quantile)
        rad_norm_to_max = rad / rad_max
        rad_norm_to_max[rad_norm_to_max > 1.0] = 1.0

        u = uv_unit[:, :, 0] * rad_norm_to_max[..., 0]
        v = uv_unit[:, :, 1] * rad_norm_to_max[..., 0]

        return self.flow_uv_to_colors(u, v, convert_to_bgr)
