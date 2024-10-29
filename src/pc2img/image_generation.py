from abc import abstractmethod, ABC
from functools import partial
import re
from typing import Iterable, Optional


from cuml.neighbors import NearestNeighbors
import numpy as np
from scipy.spatial import Delaunay

from pchandler.geometry import PointCloudData
from pchandler.fov import FoV


class ImageGenerator(ABC):

    REGEX_GRADIENT_PATTERN = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
    REGEX_HILLSHADE_PATTERN = re.compile(r"hillshade(?:_(?P<azimuth>\d*)_(?P<altitude>\d*)_"
                                         r"(?P<z_factor>\d+(?:\.\d+)?)?)?")

    def __init__(self, image_resolution: tuple[int, int], rasterization_method: str):
        if len(image_resolution) != 2:
            raise ValueError(f"``image_resolution`` needs to have two values!")
        if any(res < 1 for res in image_resolution):
            raise ValueError(f"The image resolution components need to all be above zero!")

        self.image_resolution = image_resolution
        self.rasterization_method = rasterization_method

        self._pixel_raster = self._generate_pixel_raster()

        self._interpolation = None

    @property
    def aspect_ratio(self):
        return self.image_resolution[1] / self.image_resolution[0]

    @staticmethod
    def calculate_triangulation(points: np.ndarray | tuple[np.ndarray, np.ndarray],
                                xi: np.ndarray | tuple[np.ndarray, np.ndarray],
                                method: str) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray, np.ndarray]:

        if isinstance(points, tuple):
            points = np.stack(points, axis=-1)

        if isinstance(xi, tuple):
            xi = np.stack(xi, axis=-1)

        if xi.ndim == 3:
            original_shape = xi.shape[:-1]
            xi = np.reshape(xi, newshape=(-1, 2))

        match method:
            case 'knn':
                knn = NearestNeighbors(n_neighbors=3)
                knn.fit(points)
                distances, indices = knn.kneighbors(xi)
                simplices = points[indices[:, 0]], points[indices[:, 1]], points[indices[:, 2]]
            case 'delaunay':
                tri = Delaunay(points)
                simplex_index = tri.find_simplex(xi)
                indices = tri.simplices[simplex_index]
                simplices = (tri.points[indices[:, 0]], tri.points[indices[:, 1]], tri.points[indices[:, 2]])

                XA = tri.points[indices].reshape(-1, 2).astype(np.float32)
                XB = np.repeat(xi, repeats=3, axis=0)
                distances = np.linalg.norm(XA - XB, axis=1).reshape(-1, 3)
                distances[simplex_index == -1] = np.inf

            case _:
                raise ValueError(f"{method} is not a correct method")

        return simplices, indices, distances

    def _generate_pixel_raster(self) -> tuple[np.ndarray, np.ndarray]:
        row_index = np.arange(start=0, stop=self.image_resolution[0], dtype=np.float32)
        column_index = np.arange(start=0, stop=self.image_resolution[1], dtype=np.float32)
        ii, jj = np.meshgrid(row_index, column_index, indexing="ij")
        return ii, jj


    @staticmethod
    def barycentric_interpolation(
            # points: np.ndarray | tuple[np.ndarray, np.ndarray],
            values: np.ndarray | tuple[np.ndarray, ...],
            # triangulation: tuple[np.ndarray, np.ndarray, np.ndarray],
            simplices: tuple[np.ndarray, np.ndarray, np.ndarray],
            indices: np.ndarray,
            distances: np.ndarray,
            xi: np.ndarray | tuple[np.ndarray, np.ndarray], # Todo: the handling of xi and simplices etc is not consistent
            filter_distance: float = 0.0,
            fill_value: float = np.nan) -> list[np.ndarray]:
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



        if not isinstance(values, tuple):
            values = tuple(values)

        if isinstance(xi, tuple):
            xi = np.stack(xi, axis=-1)

        if xi.ndim == 3:
            original_shape = xi.shape[:-1]
            xi = np.reshape(xi, newshape=(-1, 2))
        # delaunay = Delaunay(points)
        # simplex_index = delaunay.find_simplex(xi)
        # indices = delaunay.simplices[simplex_index]
        #
        # v0, v1, v2 = (delaunay.points[indices[:, 0]], delaunay.points[indices[:, 1]],
        #               delaunay.points[indices[:, 2]])

        v0, v1, v2 = simplices

        detT = (v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1])

        alpha = ((v1[:, 1] - v2[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
        beta = ((v2[:, 1] - v0[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v0[:, 0] - v2[:, 0]) * (xi[:, 1] - v2[:, 1])) / detT
        gamma = 1 - alpha - beta
        weights = np.stack((alpha, beta, gamma), axis=1)

        if filter_distance:
            filter_indices = np.logical_or(np.min(distances, axis=1) > filter_distance, simplex_index == -1)
        else:
            filter_indices = np.isinf(distances).any(axis=1)

        interpolation_results = []
        for v in values:
            interpolation_values = np.sum(v[indices] * weights, axis=1)
            interpolation_values[filter_indices] = fill_value

            if "original_shape" in locals():
                interpolation_values = np.reshape(interpolation_values, newshape=original_shape)

            interpolation_results.append(interpolation_values)
        return interpolation_results



class ImageGeneratorFromPCD(ImageGenerator):

    def __init__(self, pcd: PointCloudData, image_resolution: tuple[int, int], rasterization_method: str):
        super().__init__(image_resolution, rasterization_method)
        self.pcd = pcd
        self._coordinates_mapped_to_pixels = None  # Since this is an abstract mehtod this should be set by the inheriting classes


    def project_and_rasterize(self, features: str | Iterable[str], filter_distance: float = 0.0,
                              fill_value: float = np.nan):
        if self.minimum_nb_points and pcd.nbPoints < self.minimum_nb_points:
            return None

        pcd_data_for_features = self.extract_pcd_data_for_features(features)

        if self._interpolation is None:
            match self.rasterization_method:
                case 'bary_delaunay':
                    simplices, indices, distances = self.calculate_triangulation(self._coordinates_mapped_to_pixels,
                                                                                 self._pixel_raster, "delaunay")
                    self._interpolation = partial(self.barycentric_interpolation, simplices = simplices, indices=indices,
                                                  distances=distances, filter_distance=filter_distance, xi=self._pixel_raster,
                                                  fill_value=fill_value)

        rasterized_results = self._interpolation(values=tuple(pcd_data_for_features.values()))
        rasterization_results = dict(zip(pcd_data_for_features.keys(), rasterized_results))

        return self.extract_features_from_pcd_data(features, rasterization_results)




    # @staticmethod
    # def _extract_gradient_fields(field_labels: set[str,...]):
    #     regex_gradient_pattern = re.compile(r"gradient_(?P<axis>[xy])_(?P<feature>.+)")
    #
    #     # Subsample and extract information using the regex pattern
    #     filtered_info = {
    #         match.group(0): {
    #             "axis": match.group("axis"),
    #             "feature": match.group("feature")
    #         }
    #         for s in strings
    #         if (match := REGEX_GRADIENT_PATTERN.search(s))
    #     }
    #     return filtered_info

    @abstractmethod
    def _map_to_pixel_raster(self):
        pass


    def extract_pcd_data_for_features(self, features: str | Iterable[str]) -> dict[str, np.ndarray]:
        # Clean up different parameter types
        if isinstance(features, str):
            features = (features,)

        if not features:
            return None  # Todo: Consider raising an error

        pcd_data_for_features = dict()
        for fl in features:
            if fl.lower() == "range":
                # values.append(self.pcd.spherical_coordinates[:, 0])
                pcd_data_for_features[fl] = self.pcd.spherical_coordinates[:, 0]
            elif "gradient" in fl.lower():
                # pattern = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
                match = re.compile(r"gradient_(?P<axis>[xy])_(?P<feature>.+)").match(fl)
                if not match:
                    warnings.warn(f"!{fl} does not match the gradient feature definitions")
                    continue
                feature = match.groupdict()["feature"]
                if all("range" in feature.lower(), "range" not in features, "range" not in pcd_data_for_features.keys()):
                    pcd_data_for_features["range"] = self.pcd.spherical_coordinates[:, 0]
                elif all(feature in self.pcd.scalar_fields.keys(), feature not in features,
                         feature not in pcd_data_for_features.keys()):
                    pcd_data_for_features[fl] = self.pcd.scalar_fields[fl]

            elif "hillshade" in fl.lower():
                if all(("range" not in features, "range" not in pcd_data_for_features.keys())):
                    pcd_data_for_features["range"] = self.pcd.spherical_coordinates[:, 0]
            elif fl in self.pcd.scalar_fields.keys():

                pcd_data_for_features[fl] = self.pcd.scalar_fields[fl]
            else:
                warnings.warn(f"!{fl} does not match a scalar field")
                continue

        return pcd_data_for_features

    def extract_features_from_pcd_data(self, features: str | Iterable[str],
                                       pcd_data_for_features: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        feature_data = dict()
        for feature in features:
            if feature in pcd_data_for_features.keys():
                rd = pcd_data_for_features[feature]
            elif "gradient" in feature.lower():
                match = ImageGenerator.REGEX_GRADIENT_PATTERN.match(feature)
                if not match:
                    continue
                axis, base_feature = match.groups()

                x, y = np.gradient(pcd_data_for_features[base_feature])
                rd = x if axis.lower() == "x" else y

            elif "hillshade" in feature.lower():
                # extract (optional) hillshade parameters
                match = ImageGenerator.REGEX_HILLSHADE_PATTERN.match(feature)
                hillshade_parameters = match.groupdict()
                hillshade_parameters = {k: float(v) for k, v in hillshade_parameters.items() if v is not None}

                rd = self.calculate_hillshade(pcd_data_for_features["range"], **hillshade_parameters)
            feature_data[feature] = rd
        return feature_data

    @staticmethod
    def calculate_hillshade(values: np.ndarray, azimuth: float = 315,
                            altitude: float = 45,
                            z_factor: float = 1.0) -> np.ndarray:

        x, y = np.gradient(values * z_factor)
        slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
        aspect = np.arctan2(-x, y)
        azimuth_rad = azimuth * np.pi / 180.0
        altitude_rad = altitude * np.pi / 180.0

        shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(slope) * np.cos(
            azimuth_rad - aspect)

        return shaded



class SphericalImageGeneratorFromPCD(ImageGeneratorFromPCD):

    def __init__(self, pcd: PointCloudData, image_resolution: tuple[int, int], rasterization_method: str,
                 minimum_nb_points: int, fov: Optional[FoV] = None):


        super().__init__(pcd, image_resolution, rasterization_method)

        self.minimum_nb_points = minimum_nb_points

        if fov is None:
            fov = self.pcd.fov

        # Match the fov ratio to the image ratio and the pcd to fov
        self.fov = fov.extend_to_ratio(self.aspect_ratio)
        self.pcd = self.pcd.extract_angles(self.fov)

        self._coordinates_mapped_to_pixels = self._map_spherical_coordinates_to_pixel_raster()


    def _map_to_pixel_raster(self):
        return self._map_spherical_coordinates_to_pixel_raster()

    def _map_spherical_coordinates_to_pixel_raster(self) -> tuple[np.ndarray, np.ndarray]:
        elevation_pixel = (
                (self.image_resolution[0] - 1) * (self.pcd.spherical_coordinates[:, 1] - self.fov.elevation_min)
                / self.fov.height("rad")).astype(np.float32)
        horizontal_pixel = (
                (self.image_resolution[1] - 1) * (self.pcd.spherical_coordinates[:, 2] - self.fov.horizontal_min)
                / self.fov.width("rad")).astype(np.float32)
        return (elevation_pixel, horizontal_pixel)
