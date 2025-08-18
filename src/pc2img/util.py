from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.signal import convolve2d

ALL_CMAPS = Literal[
    'magma', 'inferno', 'plasma', 'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'berlin',
    'managua', 'vanimo', 'Blues', 'BrBG', 'BuGn', 'BuPu', 'CMRmap', 'GnBu', 'Greens', 'Greys', 'OrRd',
    'Oranges', 'PRGn', 'PiYG', 'PuBu', 'PuBuGn', 'PuOr', 'PuRd', 'Purples', 'RdBu', 'RdGy', 'RdPu', 'RdYlBu',
    'RdYlGn', 'Reds', 'Spectral', 'Wistia', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd', 'afmhot', 'autumn', 'binary',
    'bone', 'brg', 'bwr', 'cool', 'coolwarm', 'copper', 'cubehelix', 'flag', 'gist_earth', 'gist_gray',
    'gist_heat', 'gist_ncar', 'gist_rainbow', 'gist_stern', 'gist_yarg', 'gnuplot', 'gnuplot2', 'gray',
    'hot', 'hsv', 'jet', 'nipy_spectral', 'ocean', 'pink', 'prism', 'rainbow', 'seismic', 'spring', 'summer',
    'terrain', 'winter', 'Accent', 'Dark2', 'Paired', 'Pastel1', 'Pastel2', 'Set1', 'Set2', 'Set3', 'tab10',
    'tab20', 'tab20b', 'tab20c', 'grey', 'gist_grey', 'gist_yerg', 'Grays', 'magma_r', 'inferno_r', 'plasma_r',
    'viridis_r', 'cividis_r', 'twilight_r', 'twilight_shifted_r', 'turbo_r', 'berlin_r', 'managua_r', 'vanimo_r',
    'Blues_r', 'BrBG_r', 'BuGn_r', 'BuPu_r', 'CMRmap_r', 'GnBu_r', 'Greens_r', 'Greys_r', 'OrRd_r', 'Oranges_r',
    'PRGn_r', 'PiYG_r', 'PuBu_r', 'PuBuGn_r', 'PuOr_r', 'PuRd_r', 'Purples_r', 'RdBu_r', 'RdGy_r', 'RdPu_r',
    'RdYlBu_r', 'RdYlGn_r', 'Reds_r', 'Spectral_r', 'Wistia_r', 'YlGn_r', 'YlGnBu_r', 'YlOrBr_r', 'YlOrRd_r',
    'afmhot_r', 'autumn_r', 'binary_r', 'bone_r', 'brg_r', 'bwr_r', 'cool_r', 'coolwarm_r', 'copper_r',
    'cubehelix_r', 'flag_r', 'gist_earth_r', 'gist_gray_r', 'gist_heat_r', 'gist_ncar_r', 'gist_rainbow_r',
    'gist_stern_r', 'gist_yarg_r', 'gnuplot_r', 'gnuplot2_r', 'gray_r', 'hot_r', 'hsv_r', 'jet_r',
    'nipy_spectral_r', 'ocean_r', 'pink_r', 'prism_r', 'rainbow_r', 'seismic_r', 'spring_r', 'summer_r',
    'terrain_r', 'winter_r', 'Accent_r', 'Dark2_r', 'Paired_r', 'Pastel1_r', 'Pastel2_r', 'Set1_r', 'Set2_r',
    'Set3_r', 'tab10_r', 'tab20_r', 'tab20b_r', 'tab20c_r', 'grey_r', 'gist_grey_r', 'gist_yerg_r', 'Grays_r'
]

NAN_REPLACEMENT_STR = Literal["max", "min", "random"]


def nanconv(a: NDArray, k: NDArray, replace_nan: Optional[float] = None) -> NDArray:
    on = np.ones(a.shape, dtype=a.dtype)

    n = np.isnan(a)
    a[n] = 0
    on[n] = 0

    flat = convolve2d(on, k, mode="same").astype(np.float16)

    c = np.full(flat.shape, np.nan, dtype=np.float16)
    np.divide(convolve2d(a, k, mode="same").astype(np.float16), flat, out=c, where=(flat != 0))
    if replace_nan is not None:
        np.nan_to_num(c, copy=False, nan=replace_nan)
    return c


def gaussian_kernel(l=5, sig=1.):
    """
    creates gaussian kernel with side length `l` and a sigma of `sig`
    """
    ax = np.linspace(-(l - 1) / 2., (l - 1) / 2., l)
    gauss = np.exp(-0.5 * np.square(ax) / np.square(sig))
    kernel = np.outer(gauss, gauss)
    return kernel / np.sum(kernel)

def convert_to_image(image_data: NDArray[np.floating], replace_nan_with: NAN_REPLACEMENT_STR = "max", normalize: bool = False,
                     colormap: Optional[ALL_CMAPS] = None) -> NDArray[np.uint8]:
    if replace_nan_with not in ["max", "min", "random"]:
        raise ValueError("replace_nan must be one of 'max', 'min', 'random'")

    if image_data.ndim != 2 and colormap:
        raise ValueError("Can't use colormap with more than 1 channel'")

    nan_positions = np.isnan(image_data)
    image_data = replace_nan(image_data, replace_nan_with)

    image_min = np.min(image_data)
    image_max = np.max(image_data)
    if normalize or np.min(image_data) < 0.0 or np.max(image_data) > 1.0:
        image_data = (image_data - image_min) / (image_max - image_min)

    if colormap is not None:
        # Extract cmap from matplotlib; cmap returns an RGBA image in float [0, 1]; drop the alpha channel
        cmap = plt.get_cmap(colormap)
        colored_image_data = cmap(image_data)[..., :3]

        # Replace original nan_positions with non-colormap data (grey random)
        image_data = np.dstack(3*(image_data,))
        image_data[~nan_positions,:] = colored_image_data[~nan_positions,:]

    return (255.0 * image_data).astype(np.uint8)

def replace_nan(image_data: NDArray[np.floating], replace_nan_with: str = "max") -> NDArray[np.floating]:
    if replace_nan_with not in ["max", "min", "random"]:
        raise ValueError("replace_nan_with must be one of 'max', 'min', 'random'")

    image_data = image_data.copy()
    image_min = np.nanmin(image_data)
    image_max = np.nanmax(image_data)
    nan_positions = np.isnan(image_data)
    if nan_positions.ndim > 2:
        nan_positions = np.any(nan_positions, axis=2)
    match replace_nan_with:
        case "max":
            np.nan_to_num(image_data, copy=False, nan=image_max)
        case "min":
            np.nan_to_num(image_data, copy=False, nan=image_min)
        case "random":
            rng = np.random.default_rng()
            random = rng.uniform(image_min, image_max, size=image_data.shape[:2])
            if image_data.ndim == 3:
                random = np.stack(image_data.shape[-1] * (random,), axis=-1)
                nan_positions = np.stack(image_data.shape[-1] * (nan_positions,), axis=-1)
            image_data[nan_positions] = random[nan_positions]

    return image_data




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
    # dip_directions[dip_directions < 0] += 360  # Ensure directions are between 0 and 360 degrees

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
        colorwheel[col:col + YG, 0] = 255 - np.floor(255 * np.arange(0, YG) / YG)
        colorwheel[col:col + YG, 1] = 255
        col = col + YG
        # GC
        colorwheel[col:col + GC, 1] = 255
        colorwheel[col:col + GC, 2] = np.floor(255 * np.arange(0, GC) / GC)
        col = col + GC
        # CB
        colorwheel[col:col + CB, 1] = 255 - np.floor(255 * np.arange(CB) / CB)
        colorwheel[col:col + CB, 2] = 255
        col = col + CB
        # BM
        colorwheel[col:col + BM, 2] = 255
        colorwheel[col:col + BM, 0] = np.floor(255 * np.arange(0, BM) / BM)
        col = col + BM
        # MR
        colorwheel[col:col + MR, 2] = 255 - np.floor(255 * np.arange(MR) / MR)
        colorwheel[col:col + MR, 0] = 255
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
            idx = (rad <= 1)
            col[idx] = 1 - rad[idx] * (1 - col[idx])
            col[~idx] = col[~idx] * 0.75  # out of range
            # Note the 2-i => BGR instead of RGB
            ch_idx = 2 - i if convert_to_bgr else i
            flow_image[:, :, ch_idx] = np.floor(255 * col)
        return flow_image

    def flow_to_image(self, flow_uv, clip_flow=None, convert_to_bgr=False, max_quantile: Optional[float] = None):
        """
        Expects a two dimensional flow image of shape.

        Args:
            flow_uv (np.ndarray): Flow UV image of shape [H,W,2]
            clip_flow (float, optional): Clip maximum of flow values. Defaults to None.
            convert_to_bgr (bool, optional): Convert output image to BGR. Defaults to False.

        Returns:
            np.ndarray: Flow visualization image of shape [H,W,3]
        """
        assert flow_uv.ndim == 3, 'input flow must have three dimensions'
        assert flow_uv.shape[2] == 2, 'input flow must have shape [H,W,2]'
        epsilon = 1e-5

        if clip_flow is not None:
            flow_uv = np.clip(flow_uv, 0, clip_flow)
        # u = flow_uv[:,:,0]
        # v = flow_uv[:,:,1]
        rad = np.linalg.norm(flow_uv, axis=2, keepdims=True)
        uv_unit = flow_uv / (rad + epsilon)

        rad_max = np.max(rad) if max_quantile is None else np.quantile(rad, max_quantile)
        # rad_max = np.max(rad)
        rad_norm_to_max = rad / rad_max
        rad_norm_to_max[rad_norm_to_max > 1.0] = 1.0

        u = uv_unit[:, :, 0] * rad_norm_to_max[..., 0]
        v = uv_unit[:, :, 1] * rad_norm_to_max[..., 0]

        return self.flow_uv_to_colors(u, v, convert_to_bgr)
