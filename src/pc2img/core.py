# TODO: Make angle units more flexible
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cached_property
from itertools import chain
import logging
from joblib import Parallel, delayed
import warnings

# from optparse import Option

import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union#, Self
# from typing_extensions import Self

import numpy as np
# from scipy.interpolate import griddata as scipy_gd
import imageio.v3 as iio
# from imageio.plugins.tifffile_v3 import TifffilePlugin as iio_tiff
import tifffile

import pchandler as pch
from markdown_it.rules_inline import image
from pchandler.geometry import PointCloudData
from pchandler.fov import FoV
from skimage.io import image_stack
from yaml import warnings

# from pc2img.image_processing import ImageGenerator, SphericalImageGeneratorFromPCD
from pc2img.image_generation import ImageGenerator, ImageGeneratorFromPCD


# from pc2img.image_processing import ImageGenerator
# from pc2img import image_processing
# from pc2img.image_processing import knn_griddata as knn_griddata
# from pc2img.image_processing import barycentric_interpolation

EPS32 = np.finfo(np.float32).eps

logger = logging.getLogger(__name__)

@dataclass
class PC2IMGRunSettings:
    pcd_directory: Path
    image_results_directory: Path
    image_resolution: tuple[int, int]
    angular_resolution_gon: float
    rasterization_features: Optional[Iterable[tuple[str, ImageGenerator.NormalizationFlag]]] = None



class PointCloudSplitter:
    @property
    def aspect_ratio(self):
        return self.image_resolution[0] / self.image_resolution[1]

    def __init__(self, image_resolution: tuple[int, int], ground_sampling_distance: float, minimum_nb_points: int,
                 percentile_ratio: float, minimum_angular_resolution_gon: float, image_folder: Path):

        self.image_resolution = image_resolution # Width x Height [px]
        self.ground_sampling_distance = ground_sampling_distance
        self.minimum_nb_points = minimum_nb_points
        self.percentile_ratio = percentile_ratio
        self.minimum_angular_resolution_gon = minimum_angular_resolution_gon
        self.image_folder = image_folder

    def split_pointcloud_distance_distribution(self, pcd: pch.geometry.PointCloudData, fov_borders: FoV) \
            -> list[tuple[pch.geometry.PointCloudData, FoV], ...]:
        """

        Args:
            pcd:
            fov_borders:

        Returns:

        """
        # print(fov_borders)
        # print(pcd)
        if pcd.nbPoints <= self.minimum_nb_points:
            return [(pcd, fov_borders,)]
        distances_percentiles = np.percentile(pcd.spherical_coordinates[:, 0], (90, 10))
        fov_optimal = self._calculate_optimal_FoV_from_distance(distances_percentiles[0])

        if fov_borders.extent("gon")[0] < 4 * fov_optimal[0] or \
                fov_borders.extent("gon")[1] < 4 * fov_optimal[1] or \
                np.divide(*distances_percentiles) < self.percentile_ratio:
            tiles = self.tile(pcd, fov_borders, fov_optimal)  # TODO: Check if angular resolution necessary
            # return tuple([(tile[0], angular_resolution, tile[1]) for tile in tiles])
            return tiles
        # fov_borders = np.array(fov_borders)
        # fov_quadrants = [(fov_borders[0], fov_borders[1], fov_borders[[0, 2]].mean(), fov_borders[[1, 3]].mean()),
        #                  (fov_borders[[0, 2]].mean(), fov_borders[1], fov_borders[2], fov_borders[[1, 3]].mean()),
        #                  (fov_borders[0], fov_borders[[1, 3]].mean(), fov_borders[[0, 2]].mean(), fov_borders[3]),
        #                  (fov_borders[[0, 2]].mean(), fov_borders[[1, 3]].mean(), fov_borders[2], fov_borders[3])]

        fov_quadrants = fov_borders.quadrants()

        splits = []
        for fq in fov_quadrants:
            pcd_extract = pcd.extract_angles(**fq.as_dict())
            if pcd_extract.nbPoints:
                splits.append((pcd_extract, fq))
        # splits.append((pcd.extract_angles(**fov_quadrants[0].as_dict()), fov_quadrants[0]))
        # splits.append((pcd.extract_angles(**fov_quadrants[1].as_dict()), fov_quadrants[1]))
        # splits.append((pcd.extract_angles(**fov_quadrants[2].as_dict()), fov_quadrants[2]))
        # splits.append((pcd, fov_quadrants[3]))

        pcd_fov_splits = Parallel(n_jobs=-1, prefer="processes", verbose=50, timeout=10 * 60)(delayed(
            self.split_pointcloud_distance_distribution)(*pcd_split) for pcd_split in splits)

        # pcd_fov_splits = [self.split_pointcloud_distance_distribution(*pcd_split) for pcd_split in splits]

        # pcd_fov_flattened = []
        # for pcd_fov in pcd_fov_splits:
        #     if pcd_fov is not None:
        #         pcd_fov_flattened.extend(pcd_fov)
        pcd_fov_flattened = list(chain.from_iterable(pcd_fov_splits))
        return pcd_fov_flattened

    def _calculate_optimal_FoV_from_distance(self, distance: float):
        """ Calculate optimal FoV and angular resolution based on distance.

        This function calculates the angular resolution between pixel to achieve the point spacing defined in
        `self.point_distance_pixel` (with the lower limit set by `self.minimum_angular_resolution_gon`). Based on the
        calculated angular resolution and the defined image size in pixels, the FoV is calculated.

        Args:
            distance (float): Distance [m] to the majority of pixels

        Returns:
            tuple[float, float]: FoV angles [gon] width and height
        """
        angular_resolution = max(2 * math.asin((self.ground_sampling_distance / 2) / distance) * 200 / math.pi,
                                 self.minimum_angular_resolution_gon)
        # angular_resolution_rounded = np.floor(angular_resolution * 1000) / 1000   # round to 1e-3
        FoV = tuple([angular_resolution * pixel_count for pixel_count in self.image_resolution])

        return FoV

    def tile(self, pcd: pch.geometry.PointCloudData, fov: FoV,
             fov_per_image: tuple[float, float]) -> list[tuple[pch.geometry.PointCloudData, FoV]]:
        """Tile pcd into equally sized tiles along FoV.

        TODO: Check if tiling can be parallelized; Alternatively check if too many tiles and return to splitting


        Args:
            fov:
            fov_per_image:

        Returns:

        """

        sampling_angle_gon = \
            max(min((fov.extent("gon")[0] / np.ceil(fov.extent("gon")[0] / fov_per_image[0])) /
                    self.image_resolution[0],
                    (fov.extent("gon")[1] / np.ceil(fov.extent("gon")[1] / fov_per_image[1])) /
                    self.image_resolution[1]), self.minimum_angular_resolution_gon)

        new_fov_per_image = tuple(sampling_angle_gon * np.array(self.image_resolution))

        horizontal_fov_edges = np.arange(start=fov.horizontal_min_gon,
                                         stop=fov.horizontal_max_gon + new_fov_per_image[0],
                                         step=new_fov_per_image[0])
        elevation_fov_edges = np.arange(start=fov.elevation_min_gon,
                                        stop=fov.elevation_max_gon + new_fov_per_image[1],
                                        step=new_fov_per_image[1])

        fov_tiles = []
        # nbTiles = (horizontal_fov_edges.shape[0] - 1) * (elevation_fov_edges.shape[0] - 1)
        # print(f"Number of tiles: {nbTiles:d}")
        for i in range(horizontal_fov_edges.shape[0] - 1):
            for j in range(elevation_fov_edges.shape[0] - 1):
                fov_tiles.append(FoV(horizontal_fov_edges[i], elevation_fov_edges[j], horizontal_fov_edges[i + 1],
                                     elevation_fov_edges[j + 1], unit="gon"))
                # print(f"{i}, {j}")
        pcd_fov_tiles = [(pcd.extract_angles(**fov_tile.as_dict("rad")), fov_tile) for fov_tile in fov_tiles]
        return pcd_fov_tiles

    def split_on_fovs(self, pcd: pch.geometry.PointCloudData, fovs: Iterable[FoV]):
        pcd_fov = [(pcd.extract_angles(**fov.as_dict("rad")), fov) for fov in fovs]
        # pcd_fov = []
        # for i, fov in enumerate(fovs):
        #     pcd_fov.append((pcd.extract_angles(**fov.as_dict("rad")), fov, ))
        #     print(i)
        return pcd_fov

    def split_on_fov_tree(self, pcd: pch.geometry.PointCloudData, fov_tree: FoVTree, n_jobs: int = -1,
                          remove_empty: bool = True) -> list[tuple[str, FoV, pch.geometry.PointCloudData]]:
        # if not pcd.nbPoints:
        #     return []

        if fov_tree.is_leaf() or pcd.nbPoints <= self.minimum_nb_points:
            return [(fov_tree.identifier, fov_tree.node, pcd,)]

        split_packages = [(pcd.extract_angles(**child.node.as_dict()), child, n_jobs)
                          for child in fov_tree.children.values()]
        if remove_empty:
            split_packages = [sp for sp in split_packages if sp[0].nbPoints]
        # print(*[FoV(**sp[0].fov, unit="rad") for sp in split_packages], sep='\n')
        split = Parallel(n_jobs=n_jobs, prefer="processes", verbose=50, timeout=10 * 60)(delayed(
            self.split_on_fov_tree)(*split_package) for split_package in split_packages)

        split = list(chain.from_iterable(split))

        return list(split)

@dataclass(init=False)
class PCDImageLink:
    pcd: PointCloudData
    image_stacks: dict[int, ImageStack] = None
    identifier: Optional[str] = None

    cache_folder: Optional[Path] = None


    def __init__(self, pcd: PointCloudData,
                 image_generators_skeletons: Iterable[Callable[[PointCloudData], ImageGeneratorFromPCD]],
                 identifier: str = None, cache_folder: Path = None):
        self.pcd = pcd
        self.cache_folder = cache_folder
        if self.cache_folder is not None and not self.cache_folder.exists():
            self.cache_folder.mkdir(parents=True)
        self.image_stacks = {}
        for igs in image_generators_skeletons:
            ig = igs(pcd=self.pcd)
            stack_cache_folder = cache_folder / ig.identifier if cache_folder is not None else None
            new_stack = ImageStack(image_generator=ig, cache_folder=stack_cache_folder)
            self.image_stacks[ig.identifier] = new_stack


    @property
    def available_stacks(self):
        return sorted(list(self.image_stacks.keys()))

    def get_image_data(self, stack_identifier: str, feature: str, normalize: bool = False,
                       normilization_percentiles: tuple[int, int] = (0, 100)) -> Union[np.ndarray, np.memmap]:

        if not stack_identifier in self.image_stacks.keys():
            raise KeyError(f"{stack_identifier} not in {self.available_stacks}")
        return self.image_stacks[stack_identifier].get_image_data(feature, normalize, normilization_percentiles)
        # return self.image_stacks[stack_identifier][feature]

    def save_stack_as_images(self, save_dir: Path, stack_identifier: str, features: Optional[Union[str,Iterable[str]]] = None,
                             normalize: bool = True, normalization_percentiles: tuple[int, int] = (0, 100), create_subdirs: bool = False):
        # logging.debug(f"Starting savcalculation of triangulation with method: {method}.")
        self.image_stacks[stack_identifier].save_images(save_dir, features, normalize, normalization_percentiles, create_subdirs)

        # if feature in self.image_stacks.images.keys():
        #     return self.image_stacks[stack_identifier].images[feature]
        #
        # else:



@dataclass
class ImageStack:
    # image_parameters: FoV  # Todo: Should be changed to camera parameters at a later point

    image_generator: ImageGenerator

    cache_folder: Optional[Path]

    images: dict[str, ImageData] = None

    # camera_parameters

    @property
    def identifier(self) -> int:
        return self.image_generator.identifier # Todo: Should be changed to camera parameters at a later point


    # def __init__(self):
    #     pass

    def __post_init__(self):
        if self.cache_folder is not None and not self.cache_folder.exists():
            self.cache_folder.mkdir(parents=True)
        self.images = {}

    def add_images(self, **kwargs):
        if isinstance(self.image_generator, ImageGeneratorFromPCD):
            self._add_images_from_pcd(**kwargs)

    def _add_images_from_pcd(self, features: str | Iterable[str]):
        if isinstance(features, str):
            features = [features,]
        # Check if features have been already computed
        features = [feature for feature in features if feature not in self.images]
        if self.cache_folder is not None:
            existing_features = [f for f in features if ImageData.cache_exists(self.cache_folder / f"{f}")]
            for ef in existing_features:
                self.images[ef] = ImageData(cache_path=self.cache_folder / f"{ef}")
            features = list(set(features) - set(existing_features))
        if not features:
            return
        # Check if the necessary primary features have already been computed (such as in the case of `hillshade` or `gradient`)
        primary_features = ImageGeneratorFromPCD.extract_primary_features(features)
        primary_features_data = {pf: self.images[pf] for pf in primary_features if pf in self.images} # Todo: maybe passing .data makes more sense
        primary_features = [pf for pf in primary_features if pf not in self.images]
        if self.cache_folder is not None:
            cached_primary_features = [f for f in primary_features if ImageData.cache_exists(self.cache_folder / f"{f}")]
            for cpf in cached_primary_features:
                self.images[cpf] = ImageData(cache_path=self.cache_folder / f"{cpf}")
                primary_features_data[cpf] = self.images[cpf].data
            primary_features = list(set(primary_features) - set(cached_primary_features))



        projected_data = self.image_generator.project_and_rasterize(features=features, filter_distance=5.0,
                                                                    precomputed_features=primary_features_data)  # Todo: Filter distance might be too hidden
        for feature, projected_feature_data in projected_data.items():
            feature_cache_path = self.cache_folder / f"{feature}" if self.cache_folder is not None else None
            self.images[feature] = ImageData(data=projected_feature_data, cache_path=feature_cache_path,)
        return
        # if self.cache_folder is not None:
        #     existing_features = [f for f in features if ImageData.cache_exists(self.cache_folder / f"{f}")]
        #     for ef in existing_features:
        #         self.images[ef] = ImageData(cache_path=self.cache_folder / f"{ef}")
        #     features = list(set(features) - set(existing_features))
        # if not features:
        #     return
        #
        # projected_data = self.image_generator.project_and_rasterize(features=features, filter_distance=5.0)  # Todo: Filter distance might be too hidden
        # for feature, projected_feature_data in projected_data.items():
        #     feature_cache_path = self.cache_folder / f"{feature}" if self.cache_folder is not None else None
        #     self.images[feature] = ImageData(data=projected_feature_data, cache_path=feature_cache_path,)
        # return

    def get_image_data(self, feature: str, normalize: bool = False,
                       normilization_percentiles: tuple[int, int] = (0, 100)) -> Union[np.ndarray, np.memmap]:
        if feature not in self.images:
            self.add_images(features=[feature])

        image_data = self.images[feature].data if not normalize else self.images[feature].normalized(normilization_percentiles)
        return image_data

    def save_images(self, save_dir: Path, features: Optional[Union[str,Iterable[str]]] = None, normalilze: bool = True,
                    normalization_percentiles: tuple[int, int] = (0, 100), create_subdirs: bool = False):
        if isinstance(features, str):
            features = [features]
        if features is None:
            features = list(self.images.keys())
        for feature in features:
            if feature not in self.images:
                self.add_images(features=[feature])
            if feature in self.images:
                save_path = save_dir / f"{feature}.png" if create_subdirs else save_dir.with_stem(save_dir.stem + f"_{feature}.png")
                self.images[feature].save_image(save_path, normalilze, normalization_percentiles)
            else:
                warnings.warn(f"Feature: {feature} not available!")


    def __getitem__(self, feature: str):  # Todo: Rethink if this sensible
        return self.get_image_data(feature)


@dataclass
class ImageData:
    data: Union[np.ndarray, np.memmap] = None
    cache_path: Optional[Path] = None
    _normalized_cache: Dict[Tuple[int, int], Union[np.ndarray, np.memmap]] = field(default_factory=dict, init=False)

    # derivative_from: Optional[ImageData] = None
    # derivative_images: list[ImageData] = None

    # Class-level constants for suffixes
    DATA_SUFFIX = ".data.npy"
    CACHE_DICT_SUFFIX = ".cache.npz"
    NORMALIZED_SUFFIX_TEMPLATE = ".norm_{}_{}.npy"

    def __post_init__(self):
        if self.cache_path:
            # Define paths for data and normalized cache using class-level suffixes
            self.data_path = self.cache_path.with_suffix(self.DATA_SUFFIX)
            self.cache_dict_path = self.cache_path.with_suffix(self.CACHE_DICT_SUFFIX)

            # Load or initialize data
            if self.data_path.exists():
                # Load existing data as memmap
                self.data = np.load(self.data_path, mmap_mode='r+')
                # self.data = np.memmap(self.data_path, dtype=float, mode='r+', shape=self.pixel_resolution)
            elif self.data is None:
                raise ValueError("Data must be provided if no cache is available")
            else:
                # Convert numpy array to memmap by saving and reloading it
                np.save(self.data_path, self.data)
                self.data = np.load(self.data_path, mmap_mode='r+')
                # self.data = np.memmap(self.data_path, dtype=float, mode='r+', shape=self.pixel_resolution)
        elif isinstance(self.data, np.ndarray):
            # If cache_path is None, work with numpy array as-is
            pass
        else:
            raise ValueError("Data must be provided as a numpy array if cache_path is not specified.")

        # Load or initialize _normalized_cache
        if self.cache_path and self.cache_dict_path.exists():
            cached = np.load(self.cache_dict_path, allow_pickle=True)
            self._normalized_cache = {ast.literal_eval(normalization_key_str): np.load(Path(filename.item()), mmap_mode="r+")
                                      for normalization_key_str, filename in cached.items()}
        else:
            self._normalized_cache = {}

    @classmethod
    def cache_exists(cls, cache_path: Path) -> bool:
        """Check if data cache file exists or if data needs to be generated."""
        data_path = cache_path.with_suffix(cls.DATA_SUFFIX)
        return data_path.exists()

    def normalized(self, percentile_region: tuple[int, int] = (0, 100)) -> Union[np.ndarray, np.memmap]:
        if any((len(percentile_region) != 2, percentile_region[0] >= percentile_region[1],
                percentile_region[0] < 0, percentile_region[1] > 100)):
            raise ValueError(
                "`percentile_region` needs values between 0 and 100, and the second value has to be larger than the first!"
            )

        if percentile_region in self._normalized_cache:
            return self._normalized_cache[percentile_region]

        values_flat = np.ndarray.flatten(self.data)
        lower, upper = np.nanpercentile(values_flat[~np.isnan(values_flat)], list(percentile_region))
        normalized_values = (self.data - lower) / (upper - lower + EPS32)

        np.nan_to_num(normalized_values, copy=False, nan=1.0)
        np.clip(normalized_values, 0, 1, out=normalized_values)

        if self.cache_path:
            norm_path = self.cache_path.with_suffix(self.NORMALIZED_SUFFIX_TEMPLATE.format(*percentile_region))
            np.save(norm_path, normalized_values)
            normalized_memmap = np.load(norm_path, mmap_mode="r+")
            self._normalized_cache[percentile_region] = normalized_memmap

            np.savez(self.cache_dict_path, **{str(k): str(v.filename) for k, v in self._normalized_cache.items()})
            return normalized_memmap
        else:
            self._normalized_cache[percentile_region] = normalized_values
            return normalized_values

    def save_image(self, image_path: Path, normalize: bool = True, normalization_percentiles: tuple[int, int] = (0, 100)):
        if not image_path.parent.exists():
            image_path.parent.mkdir(parents=True)
        if normalize:
            image_path = image_path.with_stem(image_path.stem +
                                              f"_norm_{normalization_percentiles[0]}_{normalization_percentiles[1]}")
        data = self.normalized(percentile_region=normalization_percentiles) if normalize else np.nan_to_num(self.data, copy=True, nan=1.0)
        iio.imwrite(image_path, (data * 255).astype(np.uint8))
        print(f"{image_path} saved")
