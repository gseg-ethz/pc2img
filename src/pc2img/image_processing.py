import sys
import warnings

from enum import Enum
from joblib import Parallel, delayed
import json
from pathlib import Path
import re
from timeit import default_timer as timer
from typing import Optional, Iterable, Tuple, List, Any
if sys.version[0] == 3 and sys.version_info[1] >= 11:
    from typing import Self
else:
    from typing_extensions import Self

import cv2
import cupy as cp
import numpy as np
from cuml.neighbors import NearestNeighbors
from numpy import ndarray, dtype
from scipy.spatial import Delaunay
from scipy.interpolate import griddata as sp_griddata
import imageio.v3 as iio
import tifffile

import pchandler as pch
from pchandler.fov import FoV

# from pc2img.core import FoV


EPS32 = np.finfo(np.float32).eps


# def barycentric_interpolation(xi, v0, v1, v2, return_within_check: bool = False):
def barycentric_interpolation(points: np.ndarray | tuple[np.ndarray, np.ndarray],
                              values: np.ndarray | tuple[np.ndarray, ...],
                              xi: np.ndarray | tuple[np.ndarray, np.ndarray],
                              filter_distance: float = 0.0, fill_value: float = np.nan) -> list[np.ndarray]:
    """
        Interpolate unstructured 2D data using barycentric interpolation.

        Parameters
        ----------
        points : 2-D ndarray of floats with shape (n, 2), or length 2 tuple of 1-D ndarrays with shape (n,).
            Data point coordinates.
        values : tuple of ndarray of float, shape (n,)
            Data values.
        xi : 2-D ndarray of floats with shape (m, 2), or length 2 tuple of ndarrays broadcastable to the same shape.
            Points at which to interpolate data.
        filter_distance : float, optional
            Maximum distance to closest point of simplex before replacing interpolation result with ``fill_value``.
            If not provided, defaults to ``0.0``, which is interpreted as no filter.
        fill_value : float, optional
            Value used to fill in for requested points outside of the
            convex hull of the input points. If not provided, then the
            default is ``nan``. This option has no effect for the
            'nearest' method.

        Returns
        -------
        ndarray
            Array of interpolated values.

        Todo
        ----
            - 

        See Also
        --------
        scipy.spatial.Delaunay
    """

    if isinstance(points, tuple):
        points = np.stack(points, axis=-1)

    if isinstance(xi, tuple):
        xi = np.stack(xi, axis=-1)

    if xi.ndim == 3:
        original_shape = xi.shape[:-1]
        xi = np.reshape(xi, newshape=(-1, 2))

    delaunay = Delaunay(points)
    simplex_index = delaunay.find_simplex(xi)
    indices = delaunay.simplices[simplex_index]

    v0, v1, v2 = (delaunay.points[indices[:, 0]], delaunay.points[indices[:, 1]],
                  delaunay.points[indices[:, 2]])

    detT = (v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1])

    alpha = ((v1[:, 1] - v2[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
    beta = ((v2[:, 1] - v0[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v0[:, 0] - v2[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
    gamma = 1 - alpha - beta
    weights = np.stack((alpha, beta, gamma), axis=1)

    if filter_distance:
        XA = delaunay.points[indices].reshape(-1, 2).astype(np.float32)
        XB = np.repeat(xi, repeats=3, axis=0)
        distances = np.linalg.norm(XA - XB, axis=1).reshape(-1, 3)

        filter_indices = np.logical_or(np.min(distances, axis=1) > filter_distance, simplex_index == -1)
    else:
        filter_indices = simplex_index == -1

    interpolation_results = []
    for v in values:
        interpolation_values = np.sum(v[indices] * weights, axis=1)
        interpolation_values[filter_indices] = fill_value

        if "original_shape" in locals():
            interpolation_values = np.reshape(interpolation_values, newshape=original_shape)

        interpolation_results.append(interpolation_values)
    return list(interpolation_results)


def knn_griddata(points, values, xi, method='linear', filter_distance=0.0, fill_value=cp.nan) -> list[np.ndarray]:
    """
    Interpolate values on a grid using CuPy and cuML's k-nearest neighbor implementation.

    Parameters:
    - points: (N, D) array-like
        Data points for interpolation.
    - values: (N,) array-like or tuple[(N,)] array-like
        Values associated with the data points.
    - xi: (M, D) array-like
        The grid points at which to interpolate.
    - method: str, optional
        Interpolation method, 'linear' or 'nearest'.
    - fill_value: float, optional
        Value used to fill in for points outside of the convex hull of points.

    Returns:
    - result: (M,) array-like
        Interpolated values at the grid points.
    """

    if not isinstance(values, tuple):
        values = tuple(values)

    if isinstance(xi, tuple):
        # TODO: How to deal with image_resolution
        image_resolution = xi[0].shape
        xi = np.vstack((np.ndarray.flatten(xi[0]), np.ndarray.flatten(xi[1]))).T

    points, values, xi = (cp.array(points, dtype=cp.float32), cp.array(values, dtype=cp.float32),
                          cp.array(xi, dtype=cp.float32))

    if method == 'barycentric':
        knn = NearestNeighbors(n_neighbors=3)
        knn.fit(points)
        distances, indices = knn.kneighbors(xi)

        # Calculate barycentric coordinates
        v0, v1, v2 = points[indices[:, 0]], points[indices[:, 1]], points[indices[:, 2]]
        detT = (v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1])
        alpha = ((v1[:, 1] - v2[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
        beta = ((v2[:, 1] - v0[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v0[:, 0] - v2[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
        gamma = 1 - alpha - beta
        weights = cp.stack((alpha, beta, gamma), axis=1)

    elif method == 'linear':
        # Linear interpolation using cuML k-NN
        knn = NearestNeighbors(n_neighbors=5)
        knn.fit(points)
        distances, indices = knn.kneighbors(xi)
        weights = 1.0 / (distances + EPS32)
        weights /= cp.sum(weights, axis=1, keepdims=True)
    elif method == 'nearest':
        # Nearest-neighbor interpolation using cuML k-NN
        knn = NearestNeighbors(n_neighbors=1)
        knn.fit(points)
        distances, indices = knn.kneighbors(xi)
        weights = cp.ones_like(indices)
    else:
        raise ValueError("Invalid interpolation method. Use 'linear' or 'nearest'.")

    # result = cp.sum(values[indices] * weights, axis=1)
    results = []
    for v in values:
        result = cp.sum(v[indices] * weights, axis=1)
        if filter_distance:
            result[cp.min(distances, axis=1) > filter_distance] = fill_value
            # if method == 'barycentric':
            #     result[not ((0 <= alpha <= 1) and (0 <= beta <= 1) and (0 <= gamma <= 1))] = fill_value
        results.append(cp.reshape(result, image_resolution).get())

    return list(results)


def normalization(values: np.ndarray, return_bounds: bool = False) -> np.ndarray | tuple[np.ndarray, tuple[float, float]]:
    values_flat = np.ndarray.flatten(values)
    lower, upper = np.nanpercentile(values_flat[~np.isnan(values_flat)], [1, 99])
    normalized_values = (values - lower) / (upper - lower + EPS32)

    np.nan_to_num(normalized_values, copy=False, nan=1.0)
    np.clip(normalized_values, 0, 1, out=normalized_values)

    if return_bounds:
        return normalized_values, (lower, upper)

    return normalized_values


def calculate_hillshade(values: np.ndarray, azimuth: float = 315,
                         altitude: float = 45,
                         z_factor: float = 1.0) -> np.ndarray:

    x, y = np.gradient(values * z_factor)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)
    azimuth_rad = azimuth * np.pi / 180.0
    altitude_rad = altitude * np.pi / 180.0

    shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(slope) * np.cos(azimuth_rad - aspect)

    return shaded


class ImageGenerator:

    REGEX_GRADIENT_PATTERN = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
    REGEX_HILLSHADE_PATTERN = re.compile(r"hillshade(?:_(?P<azimuth>\d*)_(?P<altitude>\d*)_"
                                         r"(?P<z_factor>\d+(?:\.\d+)?)?)?")

    class NormalizationFlag(Enum):
        ORIGINAL = 0
        NORMALIZATION = 1
        BOTH = 2

    @property
    def aspect_ratio(self):
        return self.image_resolution[1] / self.image_resolution[0]

    def __init__(self, image_resolution: tuple[int, int], minimum_nb_points: int, rasterization_method: str,
                 results_folder: Path
                 ):
        # TODO: Add value checks
        if any(res < 1 for res in image_resolution):
            raise ValueError(f"The image resolution components need to all be above zero!")
        if rasterization_method not in ["raw", "delaunay"]:
            raise ValueError(f"Unknown rasterization method: {rasterization_method}!")
        if minimum_nb_points < 0:
            raise ValueError(f"Minimum number of points must be positive or zero!")

        self.image_resolution = image_resolution  # Height x Width [px]
        self.minimum_nb_points = minimum_nb_points
        self.rasterization_method = rasterization_method
        self.results_folder = results_folder

    def map_spherical_coordinates_to_pixels(self, fov, pcd) \
            -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        row_index = np.arange(start=0, stop=self.image_resolution[0], dtype=np.float32)
        column_index = np.arange(start=0, stop=self.image_resolution[1], dtype=np.float32)

        ii, jj = np.meshgrid(row_index, column_index, indexing="ij")

        elevation_pixel = (
                (self.image_resolution[0] - 1) * (pcd.spherical_coordinates[:, 1] - fov.elevation_min)
                / fov.height("rad")).astype(np.float32)
        horizontal_pixel = (
                (self.image_resolution[1] - 1) * (pcd.spherical_coordinates[:, 2] - fov.horizontal_min)
                / fov.width("rad")).astype(np.float32)

        return (ii, jj), (elevation_pixel, horizontal_pixel)

    def project_and_rasterize_2d(self, fov: FoV, pcd: pch.geometry.PointCloudData,
                                 downsample_pcd: Optional[bool | float | int] = None,
                                 field_labels: str | Iterable[str] = ("scalar_Intensity", "range")) \
            -> tuple[dict[str, dict[str, np.ndarray, tuple[np.ndarray, tuple[float, float]]]], FoV]:

        # Clean up different parameter types
        if isinstance(field_labels, str):
            field_labels = (field_labels,)

        if isinstance(downsample_pcd, bool) and downsample_pcd is True:
            pcd.random_subsample(np.prod(self.image_resolution, dtype=int) * 4)
        elif isinstance(downsample_pcd, (float, int)) and not isinstance(downsample_pcd, bool):
            pcd.random_subsample(downsample_pcd)

        # Match the fov ratio to the image ratio
        fov_extended = fov.extend_to_ratio(self.aspect_ratio)

        pixel_raster, mapped_coordinates = self.map_spherical_coordinates_to_pixels(fov_extended, pcd)
        # Create image-pixel-space and Map spherical coordinates to this space

        # Gather fields to rasterize
        values = list()
        available_fields = list()
        for fl in field_labels:
            if fl.lower() == "range":
                values.append(pcd.spherical_coordinates[:, 0])
                available_fields.append(fl)
            elif "gradient" in fl.lower():
                # pattern = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
                match = ImageGenerator.REGEX_GRADIENT_PATTERN.match(fl)
                if not match:
                    warnings.warn(f"!{fl} does not match the gradient feature definitions")
                    continue
                feature = match.groupdict()["feature"]
                if "range" in feature.lower() and "range" not in field_labels and "range" not in available_fields:
                    values.append(pcd.spherical_coordinates[:, 0])
                    available_fields.append("range")
                elif feature in pcd.scalar_fields.keys() and feature not in field_labels and feature not in available_fields:
                    values.append(pcd.scalar_fields[fl])
                    available_fields.append(fl)

            elif "hillshade" in fl.lower():
                if "range" not in field_labels and "range" not in available_fields:
                    values.append(pcd.spherical_coordinates[:, 0])
                    available_fields.append("range")
            elif fl in pcd.scalar_fields.keys():
                values.append(pcd.scalar_fields[fl])
                available_fields.append(fl)
            else:
                warnings.warn(f"!{fl} does not match a scalar field")
                continue

        values = tuple(values)

        match self.rasterization_method:
            case "delaunay":
                rasterized_data = barycentric_interpolation(
                    points=np.stack(mapped_coordinates, axis=-1),
                    values=values, xi=pixel_raster, filter_distance=5.0)
            case "raw":
                elevation_pixel_int = np.floor(mapped_coordinates[0]).astype(int)
                horizontal_pixel_int = np.floor(mapped_coordinates[1]).astype(int)
                rasterized_blank = np.full(self.image_resolution, np.nan)

                rasterized_data = list()
                for v in values:
                    rasterized_values = rasterized_blank.copy()
                    rasterized_values[elevation_pixel_int, horizontal_pixel_int] = v
                    rasterized_data.append(rasterized_values)

        rasterization_results = dict(zip(available_fields, rasterized_data))

        results = dict()
        for fl in field_labels:
            if fl in rasterization_results:
                rd = rasterization_results[fl]
            elif "gradient" in fl.lower():
                match = ImageGenerator.REGEX_GRADIENT_PATTERN.match(fl)
                if not match:
                    continue
                axis, feature = match.groups()

                x, y = np.gradient(rasterization_results[feature])
                rd = x if axis.lower() == "x" else y

            elif "hillshade" in fl.lower():
                # extract (optional) hillshade parameters
                match = ImageGenerator.REGEX_HILLSHADE_PATTERN.match(fl)
                hillshade_parameters = match.groupdict()
                hillshade_parameters = {k: float(v) for k, v in hillshade_parameters.items() if v is not None}

                rd = calculate_hillshade(rasterization_results["range"], **hillshade_parameters)

            results[fl] = {"original_values": rd, "normalized_values": normalization(rd, return_bounds=True)}

        return results, fov_extended

    def generate_and_save_image(self, fov: FoV, pcd: pch.geometry.PointCloudData, identifier: str,
                                features: Iterable[tuple[str, 'ImageGenerator.NormalizationFlag']],
                                downsample_pcd: Optional[bool | float | int] = None) \
            -> tuple[dict[str, dict[str, np.ndarray, tuple[np.ndarray, tuple[float, float]]]], FoV]:

        field_labels = [f[0] for f in features]

        pcd2d = self.project_and_rasterize_2d(fov, pcd, downsample_pcd, field_labels)

        for feature in features:
            match feature[1]:
                case ImageGenerator.NormalizationFlag.ORIGINAL:
                    iio.imwrite(self.results_folder / f"{identifier}_{feature[0]}.png",
                                (np.nan_to_num(pcd2d[0][feature[0]]["original_values"],
                                               copy=True, nan=1.0) * 255).astype(np.uint8))

                case ImageGenerator.NormalizationFlag.NORMALIZATION:
                    iio.imwrite(self.results_folder / f"{identifier}_{feature[0]}_normalized.png",
                                (pcd2d[0][feature[0]]["normalized_values"][0] * 255).astype(np.uint8))

                case ImageGenerator.NormalizationFlag.BOTH:
                    iio.imwrite(self.results_folder / f"{identifier}_{feature[0]}.png",
                                (np.nan_to_num(pcd2d[0][feature[0]]["original_values"],
                                               copy=True, nan=1.0) * 255).astype(np.uint8))
                    iio.imwrite(self.results_folder / f"{identifier}_{feature[0]}_normalized.png",
                                (pcd2d[0][feature[0]]["normalized_values"][0] * 255).astype(np.uint8))

        return pcd2d




    # def generate_images(self, pcds_with_fov: list[tuple[str, FoV, pch.geometry.PointCloudData]], n_jobs: int = -1):
    #     Parallel(n_jobs=n_jobs, prefer="processes", verbose=20)(delayed(self.fov2images)(*pcd) for pcd in pcds_with_fov)

    # def fov2images(self, identifier: str, fov: FoV, pcd: pch.geometry.PointCloudData, downsample_pcd: bool = False):
    #     # TODO: Rework: different options such as normalization etc; File name handling
    #
    #     if pcd.nbPoints < self.minimum_nb_points:
    #         return
    #
    #     if downsample_pcd and pcd.nbPoints / (self.image_resolution[0] * self.image_resolution[1]) > 10:
    #         pcd.random_subsample(np.prod(self.image_resolution, dtype=int) * 4)
    #
    #     raw_file = (self.image_folder / "00_raw" / identifier).with_suffix(".png")
    #     intensity_file = (self.image_folder / "01_intensity" / identifier).with_suffix(".png")
    #     scaled_file = (self.image_folder / "02_intensity_scaled" / identifier).with_suffix(".png")
    #     range_file = (self.image_folder / "03_range" / identifier).with_suffix(".tif")
    #     meta_file = (self.image_folder / "99_meta" / identifier).with_suffix(".json")
    #
    #     raw_file.parent.mkdir(parents=True, exist_ok=True)
    #     intensity_file.parent.mkdir(parents=True, exist_ok=True)
    #     scaled_file.parent.mkdir(parents=True, exist_ok=True)
    #     range_file.parent.mkdir(parents=True, exist_ok=True)
    #     meta_file.parent.mkdir(parents=True, exist_ok=True)
    #
    #     extended_fov = fov.extend_to_ratio(self.aspect_ratio)
    #
    #     row_index = np.arange(start=0, stop=self.image_resolution[0], dtype=np.float32)
    #     column_index = np.arange(start=0, stop=self.image_resolution[1], dtype=np.float32)
    #
    #     ii, jj = np.meshgrid(row_index, column_index, indexing="ij")
    #
    #     elevation_pixel = (
    #                 (self.image_resolution[0] - 1) * (pcd.spherical_coordinates[:, 1] - extended_fov.elevation_min)
    #                 / extended_fov.height("rad")).astype(np.float32)
    #     horizontal_pixel = (
    #                 (self.image_resolution[1] - 1) * (pcd.spherical_coordinates[:, 2] - extended_fov.horizontal_min)
    #                 / extended_fov.width("rad")).astype(np.float32)
    #
    #     # horizontal_bin_edges = np.linspace(extended_fov.horizontal_min,
    #     #                                    extended_fov.horizontal_max,
    #     #                                    num=self.image_resolution[0],
    #     #                                    endpoint=True)
    #     #
    #     # elevation_bin_edges = np.linspace(extended_fov.elevation_min,
    #     #                                   extended_fov.elevation_max,
    #     #                                   num=self.image_resolution[1],
    #     #                                   endpoint=True)
    #     #
    #     # horizontal_grid, elevation_grid = np.meshgrid(horizontal_bin_edges, elevation_bin_edges)
    #
    #     try:
    #         time_start = timer()
    #         # knn_data = knn_griddata(points=np.stack((elevation_pixel, horizontal_pixel), axis=1),
    #         #                         values=(pcd.scalar_fields["scalar_Intensity"], pcd.spherical_coordinates[:, 0]),
    #         #                         xi=(ii, jj), method='barycentric',
    #         #                         filter_distance=5.0)
    #         # time_mid = timer()
    #         # scipy_intensity = scipy_gd(points=np.stack((elevation_pixel, horizontal_pixel), axis=1),
    #         #                            values=pcd.scalar_fields["scalar_Intensity"],
    #         #                            xi=(ii, jj), method='linear', fill_value=1.0)
    #         delaunay_data = barycentric_interpolation(points=np.stack((elevation_pixel, horizontal_pixel), axis=-1),
    #                                                   values=(pcd.scalar_fields["scalar_Intensity"],
    #                                                           pcd.spherical_coordinates[:, 0]),
    #                                                   xi=(ii, jj), filter_distance=5.0)
    #         time_end = timer()
    #
    #         # print(f"Timings: {time_mid - time_start:.2f} for knn; {time_end - time_mid:.2f} for delaunay")
    #         print(f"Timings: {time_end - time_start:.2f} for delaunay")
    #
    #         # Save numpy arrays
    #         np.save(intensity_file.with_name(intensity_file.stem + "_delaunay.npy"), delaunay_data[0])
    #         np.save(range_file.with_name(range_file.stem + "_delaunay.npy"), delaunay_data[1])
    #
    #         # np.save(range_file.with_stem(range_file.stem + "_delaunay").with_suffix(".npy"), delaunay_data[1])
    #
    #         # sp_data = sp_griddata(points=np.stack((elevation_pixel, horizontal_pixel), axis=1),
    #         #                       values=pcd.scalar_fields["scalar_Intensity"],
    #         #                       xi=(ii, jj), method='linear', fill_value=1.0)
    #         #
    #         # iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_scipy"),
    #         #             ((2 ** 8 - 1) * sp_data).astype(np.uint8))
    #
    #         # Generate and save `raw` image
    #
    #         elevation_pixel_int = np.floor(elevation_pixel - EPS32).astype(int)
    #         horizontal_pixel_int = np.floor(horizontal_pixel - EPS32).astype(int)
    #
    #         raw_image = np.ones(self.image_resolution)
    #
    #         elevation_pixel_int[elevation_pixel_int == raw_image.shape[0]] = raw_image.shape[0] - 1
    #         horizontal_pixel_int[horizontal_pixel_int == raw_image.shape[1]] = raw_image.shape[1] - 1
    #
    #         raw_image[elevation_pixel_int, horizontal_pixel_int] = np.clip(pcd.scalar_fields["scalar_Intensity"], 0, 1)
    #
    #         iio.imwrite(raw_file, ((2 ** 8 - 1) * raw_image).astype(np.uint8))
    #
    #         # intensity_data_non = knn_data[0]
    #         # intensity_data_non[np.isnan(intensity_data_non)] = 1.0
    #
    #         # Generate intensity image
    #         delaunay_intensity = delaunay_data[0]
    #         delaunay_intensity[np.isnan(delaunay_data[0])] = 1.0
    #         iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_delaunay"),
    #                     ((2 ** 8 - 1) * delaunay_intensity).astype(np.uint8))
    #
    #         # Generate range image
    #         delaunay_range = normalization(delaunay_data[1])
    #         tifffile.imwrite(range_file.with_stem(range_file.stem + "_delaunay"),
    #                          ((2 ** 32 - 1) * delaunay_range).astype(np.uint32), photometric='minisblack')
    #
    #         delaunay_range_plasma = cv2.applyColorMap(((2 ** 8 - 1) * delaunay_range.T).astype(np.uint8),
    #                                                   cv2.COLORMAP_PLASMA)
    #         iio.imwrite(range_file.with_stem(range_file.stem + "_delaunay_plasma").with_suffix(".png"),
    #                     delaunay_range_plasma.transpose(1, 0, 2)[:, :, ::-1])
    #
    #         # im_color = cv2.applyColorMap(((2 ** 8 - 1) * delaunay_intensity.T).astype(np.uint8), cv2.COLORMAP_VIRIDIS)
    #
    #         # iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_knn"),
    #         #             ((2 ** 8 - 1) * intensity_data_non).astype(np.uint8))
    #
    #         # iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_delaunay_viridis"),
    #         #             im_color.transpose(1, 0, 2)[:, :, ::-1])
    #
    #         # intensity_data, range_data = [normalization(d) for d in knn_data]
    #
    #         # delaunay_intensity_normalized, delaunay_range = [normalization(d) for d in delaunay_data]
    #
    #         # iio.imwrite(scaled_file.with_stem(scaled_file.stem + "_knn"),
    #         #             ((2 ** 8 - 1) * delaunay_intensity_normalized).astype(np.uint8))
    #
    #         # iio.imwrite(scaled_file.with_stem(scaled_file.stem + "_delaunay"),
    #         #             ((2 ** 8 - 1) * intensity_data).astype(np.uint8))
    #
    #         #
    #
    #         # tifffile.imwrite(range_file.with_stem(range_file.stem + "_knn"),
    #         #                  ((2 ** 32 - 1) * range_data).astype(np.uint32), photometric='minisblack')
    #
    #         # np.save(range_file.with_stem(range_file.stem + "_knn").with_suffix(".npy"), knn_data[1])
    #
    #         # iio.imwrite(intensity_file, ((2 ** 8 - 1) * intensity_data).astype(np.uint8))
    #         #
    #         # iio.imwrite(scaled_file, ((2 ** 32 - 1) * intensity_data).astype(np.uint32),
    #         #             photometric='minisblack')
    #         #
    #         # iio.imwrite(range_file, ((2 ** 32 - 1) * range_data).astype(np.uint32),
    #         #             photometric='minisblack')
    #
    #         # iio.imwrite(intensity_file, (255.0 * intensity_data).astype(np.uint8))
    #         # iio.imwrite(scaled_file, (255.0 * intensity_data_scaled).astype(np.uint8))
    #         # iio.imwrite(range_file, (255.0 * range_data_scaled).astype(np.uint8))
    #
    #         '''
    #             GENERATE DERIVATIVES -- Delete after testing
    #         '''
    #
    #         intensity_data_y = np.gradient(delaunay_intensity, axis=0)
    #         intensity_data_x = np.gradient(delaunay_intensity, axis=1)
    #         range_data_y = np.gradient(delaunay_range, axis=0)
    #         range_data_x = np.gradient(delaunay_range, axis=1)
    #
    #         iio.imwrite(intensity_file.with_stem(intensity_file.stem + "deriv_y_delaunay"),
    #                     ((2 ** 8 - 1) * normalization(intensity_data_y)).astype(np.uint8))
    #         iio.imwrite(intensity_file.with_stem(intensity_file.stem + "deriv_x_delaunay"),
    #                     ((2 ** 8 - 1) * normalization(intensity_data_x)).astype(np.uint8))
    #         iio.imwrite(range_file.with_name(range_file.stem + "deriv_y_delaunay.png"),
    #                     ((2 ** 8 - 1) * normalization(range_data_y)).astype(np.uint8))
    #         iio.imwrite(range_file.with_name(range_file.stem + "deriv_x_delaunay.png"),
    #                     ((2 ** 8 - 1) * normalization(range_data_x)).astype(np.uint8))
    #
    #         # TODO: Add additional Info on spherical origin etc
    #         image_info = {
    #             'fov_data': fov.extent(unit='gon'),
    #             'image_resolution': self.image_resolution,
    #             'image_fov': extended_fov.as_dict('gon'),
    #             # 'filter_mask_size': filter_ds_ratio,
    #             'range_info': {'min': pcd.spherical_coordinates[:, 0].min(),
    #                            'max': pcd.spherical_coordinates[:, 0].max()},
    #         }
    #
    #         with open(meta_file, 'w') as f:
    #             json.dump(image_info, f, indent=2)
    #
    #     except:
    #         print(pcd.nbPoints)
    #         raise
    #     else:
    #         pass

