from abc import abstractmethod, ABC
from functools import partial
import logging
import re
from typing import Iterable, Optional
import warnings


import numpy as np
from numpy.typing import NDArray
from scipy.spatial import Delaunay

from pchandler.geometry import PointCloudData
from pchandler.geometry.filters import FoVFilter, BoxFilter, VoxelDownsample
from pchandler.fov import FoV

from .util import nanconv, gaussian_kernel


logger = logging.getLogger(__name__.split(".")[0])


# CPU-01 / CPU-02 / CPU-03: lazy cuml + sklearn fallback for bary_knn rasterization.
# Module-level flag ensures the WARNING fires exactly once per process even though
# `calculate_triangulation` may be called many times across scans. Tests reset this
# flag via monkeypatch (Pitfall 9 in 03-RESEARCH.md).
_cpu_fallback_warned: bool = False


def _warn_bary_knn_cpu_fallback() -> None:
    """Emit a single-fire PERFORMANCE WARNING when cuml is unavailable.

    Called from inside the `'knn'` case of `calculate_triangulation` when the
    `cuml.neighbors` import fails. The warning surfaces via the `pc2img` logger
    (see line above); Plan 06 of Phase 3 will route this warning through the
    tls2dseg CLI logger so it is visible to the end user per the CPU-03 contract.
    """
    global _cpu_fallback_warned
    if not _cpu_fallback_warned:
        logger.warning(
            "PERFORMANCE: cuml.neighbors unavailable — using sklearn NearestNeighbors "
            "for bary_knn rasterization. CPU path is functional but significantly slower. "
            "Install RAPIDS/cuml for GPU acceleration. (This message fires once per process.)"
        )
        _cpu_fallback_warned = True


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
    @abstractmethod
    def identifier(self):
        pass


    @property
    def aspect_ratio(self):
        return self.image_resolution[1] / self.image_resolution[0]

    @staticmethod
    def calculate_triangulation(points: np.ndarray | tuple[np.ndarray, np.ndarray],
                                xi: np.ndarray | tuple[np.ndarray, np.ndarray],
                                method: str) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray, np.ndarray]:
        logging.debug(f"Starting calculation of triangulation with method: {method}.")

        if isinstance(points, tuple):
            points = np.stack(points, axis=-1)

        if isinstance(xi, tuple):
            xi = np.stack(xi, axis=-1)

        if xi.ndim == 3:
            original_shape = xi.shape[:-1]
            xi = np.reshape(xi, newshape=(-1, 2))

        match method:
            case 'knn':
                # CPU-01 / CPU-02: lazy cuml import + sklearn fallback. Keeps the
                # module importable on machines without RAPIDS/cuml installed; the
                # sklearn path is functionally equivalent (slower on large inputs).
                try:
                    from cuml.neighbors import NearestNeighbors
                except ImportError:
                    _warn_bary_knn_cpu_fallback()
                    from sklearn.neighbors import NearestNeighbors
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
        logging.debug(f"Starting barycentric interpolation.")


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
            filter_indices = np.min(distances, axis=1) > filter_distance
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

    def map_to_nearest_pixel(self, points: np.ndarray, values: np.ndarray | tuple[np.ndarray, ...]) -> list[NDArray]:
        # Todo: Think about splitting the two tasks
        if isinstance(values, np.ndarray):
            values = (values,)

        elevation_pixel_int = np.floor(points[0]).astype(int)
        horizontal_pixel_int = np.floor(points[1]).astype(int)
        rasterized_blank = np.full(self.image_resolution, np.nan)

        rasterized_data = list()
        for v in values:
            rasterized_values = rasterized_blank.copy().astype(v.dtype) if v.dtype.kind == "f" else rasterized_blank.copy()
            rasterized_values[elevation_pixel_int, horizontal_pixel_int] = v
            rasterized_data.append(rasterized_values)

        return rasterized_data

    def map_to_nearest_pixel_with_nanconv(self, points: np.ndarray, values: np.ndarray | tuple[np.ndarray, ...],
                                          kernel: NDArray) -> NDArray:
        rasterized_data = self.map_to_nearest_pixel(points, values)

        rasterized_data_with_nanconv = list()
        for rd in rasterized_data:
            rasterized_data_with_nanconv.append(nanconv(rd, kernel))

        return rasterized_data_with_nanconv


class ImageGeneratorFromPCD(ImageGenerator):

    def __init__(self, pcd: PointCloudData, image_resolution: tuple[int, int], rasterization_method: str):
        super().__init__(image_resolution, rasterization_method)
        self.pcd = pcd
        self._coordinates_mapped_to_pixels = None  # Since this is an abstract mehtod this should be set by the inheriting classes


    def project_and_rasterize(self, features: str | Iterable[str], filter_distance: float = 0.0,
                              fill_value: float = np.nan,
                              precomputed_features: Optional[dict[str,np.ndarray]] = None) -> Optional[dict[str, NDArray]]:
        if self.minimum_nb_points and self.pcd.nbPoints < self.minimum_nb_points:
            return None

        if precomputed_features is None:
            precomputed_features = {}

        pcd_data_for_features = self.extract_pcd_data_for_features(features, precomputed_features)

        if len(pcd_data_for_features) == 0:
            return self.extract_features_from_pcd_data(features, {}, precomputed_features)

        if self._interpolation is None:
            logging.debug(f"Starting calculation of interpolation with method: {self.rasterization_method}.")
            match self.rasterization_method:
                case 'bary_delaunay':
                    simplices, indices, distances = self.calculate_triangulation(self._coordinates_mapped_to_pixels,
                                                                                 self._pixel_raster, "delaunay")
                    self._interpolation = partial(self.barycentric_interpolation, simplices = simplices, indices=indices,
                                                  distances=distances, filter_distance=filter_distance, xi=self._pixel_raster,
                                                  fill_value=fill_value)
                case 'bary_knn':
                    simplices, indices, distances = self.calculate_triangulation(self._coordinates_mapped_to_pixels,
                                                                                 self._pixel_raster, "knn")
                    self._interpolation = partial(self.barycentric_interpolation, simplices=simplices, indices=indices,
                                                  distances=distances, filter_distance=filter_distance, xi=self._pixel_raster,
                                                  fill_value=fill_value)
                case 'raw':
                    self._interpolation = partial(self.map_to_nearest_pixel, points=self._coordinates_mapped_to_pixels,)
                case 'nanconv':
                    kernel = gaussian_kernel()
                    self._interpolation = partial(self.map_to_nearest_pixel_with_nanconv,
                                                  points=self._coordinates_mapped_to_pixels, kernel=kernel)



        rasterized_results = self._interpolation(values=tuple(pcd_data_for_features.values()))
        rasterization_results = dict(zip(pcd_data_for_features.keys(), rasterized_results))

        return self.extract_features_from_pcd_data(features, rasterization_results, precomputed_features)



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

    @classmethod
    def extract_primary_features(cls, features: str | Iterable[str]) -> list[str]:
        if isinstance(features, str):
            features = (features,)

        if not features:
            return None
        pcd_features = list()
        for fl in features:
            if "gradient" in fl:
                match = cls.REGEX_GRADIENT_PATTERN.match(fl)
                if not match:
                    warnings.warn(f"!{fl} does not match the gradient feature definitions")
                    continue
                pcd_features.append(match.groupdict()["feature"])
            elif "hillshade" in fl:
                pcd_features.append("range")
            elif "color" in fl:
                pcd_features.append("red")
                pcd_features.append("green")
                pcd_features.append("blue")
            else:
                pcd_features.append(fl)
        pcd_features = list(set(pcd_features))
        return pcd_features


    def extract_pcd_data_for_features(self, features: str | Iterable[str],
                                      precomputed_features: Optional[dict[str,np.ndarray]] = None) -> dict[str, NDArray]:
        # Clean up different parameter types
        if isinstance(features, str):
            features = (features,)

        if precomputed_features is None:
            precomputed_features = {}

        if not features:
            return None  # Todo: Consider raising an error

        primary_features = self.extract_primary_features(features)

        # Remove precomputed features
        remaining_primary_features = [pf for pf in primary_features if pf not in precomputed_features]

        # Extract from data
        pcd_data_for_features = dict()
        for rpf in remaining_primary_features:
            if rpf == "range":
                pcd_data_for_features[rpf] = self.pcd.spherical_coordinates[:, 0]
            elif rpf in ["red", "r"]:
                pcd_data_for_features[rpf] = self.pcd.color[:,0].astype(np.float32) / 255.0
            elif rpf in ["green", "g"]:
                pcd_data_for_features[rpf] = self.pcd.color[:,1].astype(np.float32) / 255.0
            elif rpf in ["blue", "b"]:
                pcd_data_for_features[rpf] = self.pcd.color[:,2].astype(np.float32) / 255.0
            elif rpf in self.pcd.scalar_fields:
                pcd_data_for_features[rpf] = self.pcd.scalar_fields[rpf].data
            else:
                warnings.warn(f"!{rpf} does not match a scalar field")
        return pcd_data_for_features
        #
        #
        # pcd_data_for_features = dict()
        # for fl in features:
        #     if fl.lower() == "range":
        #         # values.append(self.pcd.spherical_coordinates[:, 0])
        #         pcd_data_for_features[fl] = self.pcd.spherical_coordinates[:, 0]
        #     elif "gradient" in fl.lower():
        #         # pattern = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
        #         match = re.compile(r"gradient_(?P<axis>[xy])_(?P<feature>.+)").match(fl)
        #         if not match:
        #             warnings.warn(f"!{fl} does not match the gradient feature definitions")
        #             continue
        #         feature = match.groupdict()["feature"]
        #         if all((feature == "range",
        #                 "range" not in features,
        #                 "range" not in pcd_data_for_features.keys(),
        #                 precomputed_features is not None and "range" not in precomputed_features)):
        #             pcd_data_for_features["range"] = self.pcd.spherical_coordinates[:, 0]
        #         elif all((feature in self.pcd.scalar_fields.keys(), feature not in features,
        #                  feature not in pcd_data_for_features.keys())):
        #             pcd_data_for_features[fl] = self.pcd.scalar_fields[fl]
        #
        #     elif "hillshade" in fl.lower():
        #         if all(("range" not in features, "range" not in pcd_data_for_features.keys())):
        #             pcd_data_for_features["range"] = self.pcd.spherical_coordinates[:, 0]
        #     elif fl in self.pcd.scalar_fields.keys():
        #
        #         pcd_data_for_features[fl] = self.pcd.scalar_fields[fl]
        #     else:
        #         warnings.warn(f"!{fl} does not match a scalar field")
        #         continue
        #
        # return pcd_data_for_features

    def extract_features_from_pcd_data(self, features: str | Iterable[str],
                                       pcd_data_for_features: dict[str, np.ndarray],
                                       precomputed_features: Optional[dict[str,np.ndarray]] = None) -> dict[str, np.ndarray]:
        if isinstance(features, str):
            features = [features]

        if precomputed_features is None:
            precomputed_features = {}

        feature_data = dict()
        for feature in features:
            if feature in pcd_data_for_features.keys():
                rd = pcd_data_for_features[feature]
            elif feature == "color":
                rd = np.dstack((pcd_data_for_features["red"],pcd_data_for_features["green"],pcd_data_for_features["blue"],) )
            elif "gradient" in feature.lower():
                match = ImageGenerator.REGEX_GRADIENT_PATTERN.match(feature)
                if not match:
                    continue
                axis, base_feature = match.groups()
                if base_feature in pcd_data_for_features:
                    x, y = np.gradient(pcd_data_for_features[base_feature])
                elif base_feature in precomputed_features:
                    x, y = np.gradient(precomputed_features[base_feature])
                else:
                    RuntimeError(f"Base feature for '{feature}' not found!")
                rd = x if axis.lower() == "x" else y

            elif "hillshade" in feature.lower():
                # extract (optional) hillshade parameters
                match = ImageGenerator.REGEX_HILLSHADE_PATTERN.match(feature)
                hillshade_parameters = match.groupdict()
                hillshade_parameters = {k: float(v) for k, v in hillshade_parameters.items() if v is not None}
                if "range" in precomputed_features:
                    range = precomputed_features["range"]
                elif "range" in pcd_data_for_features:
                    range = pcd_data_for_features["range"]
                else:
                    RuntimeError(f"Base feature 'range' not found for hillshade!")
                rd = self.calculate_hillshade(range, **hillshade_parameters)
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
        # self.pcd = self.pcd.sample_angles(self.fov)
        self.pcd = FoVFilter(self.fov).sample(self.pcd)

        self._coordinates_mapped_to_pixels = self._map_spherical_coordinates_to_pixel_raster()

    @property
    def identifier(self):
        id = f"Spherical_projection-fov_{self.fov}-resolution_{self.image_resolution[0]}x{self.image_resolution[1]}"
        return "".join(id.split())  # Removes all whitespaces



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


class OrthographicImageGeneratorFromPCD(ImageGeneratorFromPCD):
    def __init__(self, pcd: PointCloudData, image_resolution: tuple[int, int], rasterization_method: str,
                 minimum_nb_points: int, plane: str, roi_box: Optional[tuple[float, float, float, float]] = None,
                 downsample: bool = True):
        super().__init__(pcd, image_resolution, rasterization_method)

        self.minimum_nb_points = minimum_nb_points
        match plane:
            case 'xy':
                self.xyz_column_selection = [0,1]
            case 'yz':
                self.xyz_column_selection = [1,2]
            case 'xz':
                self.xyz_column_selection = [0,2]
            case _:
                raise ValueError(f"plane must be 'xy' or 'yz' or 'xz'")

        self.plane = plane

        if roi_box is None:
            roi_box = np.concatenate((np.min(pcd.xyz[:,self.xyz_column_selection], axis=0),
                                      np.max(pcd.xyz[:,self.xyz_column_selection], axis=0)))


        min_corner = np.array(3 * (-np.inf,))
        max_corner = np.array(3 * (np.inf,))

        min_corner[self.xyz_column_selection] = roi_box[:2]
        max_corner[self.xyz_column_selection] = roi_box[2:]


        self.pcd = BoxFilter(min_corner, max_corner).sample(self.pcd)

        if downsample:
            meter_per_vertical_pixels =  (roi_box[2] - roi_box[0]) / image_resolution[0]
            meter_per_horizontal_pixels = (roi_box[3] - roi_box[1]) / image_resolution[1]
            self.pcd = VoxelDownsample(min(meter_per_vertical_pixels, meter_per_horizontal_pixels) / 2,).sample(self.pcd)

        # Adjust roi_box to fit apect ratio of image_resolution
        roi_width = roi_box[2] - roi_box[0]
        roi_height = roi_box[3] - roi_box[1]
        roi_box_aspect = roi_width / roi_height
        image_resolution_aspect = image_resolution[0] / image_resolution[1]

        if roi_box_aspect > image_resolution_aspect:
            new_height = roi_width / image_resolution_aspect
            cy = (roi_box[1] + roi_box[3]) / 2
            roi_box[1] = cy - new_height / 2
            roi_box[3] = cy + new_height / 2

        elif roi_box_aspect < image_resolution_aspect:
            new_width = roi_height * image_resolution_aspect
            cx = (roi_box[0] + roi_box[2]) / 2
            roi_box[0] = cx - new_width / 2
            roi_box[2] = cx + new_width / 2

        self.roi_box = roi_box

        self._coordinates_mapped_to_pixels = self._map_spherical_coordinates_to_pixel_raster()
        


    def _map_to_pixel_raster(self):
        return self._map_spherical_coordinates_to_pixel_raster()

    def _map_spherical_coordinates_to_pixel_raster(self) -> tuple[np.ndarray, np.ndarray]:
        elevation_pixel = (
                (self.image_resolution[0] - 1) * (self.pcd.xyz[:, self.xyz_column_selection[0]] - self.roi_box[0])
                / (self.roi_box[2] - self.roi_box[0])).astype(np.float32)
        horizontal_pixel = (
                (self.image_resolution[1] - 1) * (self.pcd.xyz[:, self.xyz_column_selection[1]] - self.roi_box[1])
                / (self.roi_box[3] - self.roi_box[1])).astype(np.float32)
        return (elevation_pixel, horizontal_pixel)


    @property
    def identifier(self):
        id = f"Orthographic-plane_{self.plane}-roi_box_{self.roi_box}-resolution_{self.image_resolution[0]}x{self.image_resolution[1]}"
        return "".join(id.split())  # Removes all whitespaces


