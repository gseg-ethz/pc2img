# TODO: Make angle units more flexible
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cached_property
from itertools import chain
import logging

from PIL.ImageColor import colormap
from joblib import Parallel, delayed
import warnings

import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union#, Self
# from typing_extensions import Self

import numpy as np
from numpy.typing import NDArray
# from scipy.interpolate import griddata as scipy_gd
import imageio.v3 as iio
# from imageio.plugins.tifffile_v3 import TifffilePlugin as iio_tiff
import tifffile

import pchandler as pch
from pchandler.geometry import PointCloudData
from pchandler.geometry.fov import FoV


from .image_generation import ImageGenerator, ImageGeneratorFromPCD
from .util import convert_to_image, replace_nan


EPS32 = np.finfo(np.float32).eps

logger = logging.getLogger(__name__.split(".")[0])

@dataclass
class PC2IMGRunSettings:
    pcd_directory: Path
    image_results_directory: Path
    image_resolution: tuple[int, int]
    angular_resolution_gon: float
    rasterization_features: Optional[Iterable[tuple[str, ImageGenerator.NormalizationFlag]]] = None





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
                       normilization_percentiles: tuple[int, int] = (0, 100), replace_nan_with: Optional[str] = None,
                       return_normalization_borders: bool = False) -> NDArray[np.floating | np.integer]:

        if not stack_identifier in self.image_stacks.keys():
            raise KeyError(f"{stack_identifier} not in {self.available_stacks}")
        return self.image_stacks[stack_identifier].get_image_data(feature, normalize, normilization_percentiles, replace_nan_with)
        # return self.image_stacks[stack_identifier][feature]

    def save_stack_as_images(self, save_dir: Path, stack_identifier: str,
                             features: Optional[Union[str,Iterable[str]]] = None, normalize: bool = True,
                             normalization_percentiles: tuple[int, int] = (0, 100), replace_nan_with: str = "max",
                             colormap: Optional[str] = None, create_subdirs: bool = False) -> list[Path]:
        # logging.debug(f"Starting savcalculation of triangulation with method: {method}.")
        return self.image_stacks[stack_identifier].save_images(save_dir, features, normalize, normalization_percentiles,
                                                               replace_nan_with, colormap, create_subdirs)

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

    def __post_init__(self):
        if self.cache_folder is not None and not self.cache_folder.exists():
            self.cache_folder.mkdir(parents=True)
        self.images = {}

    @property
    def identifier(self) -> int:
        return self.image_generator.identifier # Todo: Should be changed to camera parameters at a later point


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
                       normilization_percentiles: tuple[int, int] = (0, 100), replace_nan_with: Optional[str] = None,
                       return_normalization_borders: bool = False) -> Union[NDArray, tuple[NDArray, tuple[float, float]]]:
        if return_normalization_borders and not normalize:
            warnings.warn(f"return_normalization_borders is set but normalize is set to False. return_normalization_borders will be ignored")
            return_normalization_borders = False
        if feature not in self.images:
            self.add_images(features=[feature])

        image_data = self.images[feature].data if not normalize else self.images[feature].normalized(normilization_percentiles)
        if replace_nan_with:
            image_data = replace_nan(image_data, replace_nan_with)
        return image_data

    def save_images(self, save_dir: Path, features: Optional[Union[str,Iterable[str]]] = None, normalilze: bool = True,
                    normalization_percentiles: tuple[int, int] = (0, 100), replace_nan_with: str = "max",
                    colormap: Optional[str] = None, create_subdirs: bool = False) -> list[Path]:
        image_paths = []
        if isinstance(features, str):
            features = [features]
        if features is None:
            features = list(self.images.keys())
        for feature in features:
            if feature not in self.images:
                self.add_images(features=[feature])
            if feature in self.images:
                save_path = save_dir / f"{feature}.png" if create_subdirs else save_dir.with_stem(save_dir.stem + f"_{feature}.png")
                image_paths.append(self.images[feature].save_image(save_path, normalilze, normalization_percentiles,
                                                                   replace_nan_with, colormap))
            else:
                warnings.warn(f"Feature: {feature} not available!")
        return image_paths



    def __getitem__(self, feature: str):  # Todo: Rethink if this sensible
        return self.get_image_data(feature)


@dataclass
class ImageData:
    data: NDArray[np.floating] = None
    cache_path: Optional[Path] = None
    _normalized_cache: Dict[Tuple[int, int], NDArray[np.floating]] = field(default_factory=dict, init=False)

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

    def normalized(self, percentile_region: tuple[int, int] = (0, 100)) -> NDArray[np.floating]:
        if len(percentile_region) != 2 or not (0 <= percentile_region[0] < percentile_region[1] <= 100):
            raise ValueError(
                "`percentile_region` needs values between 0 and 100, and the second value has to be larger than the first!"
            )

        if percentile_region in self._normalized_cache:
            return self._normalized_cache[percentile_region]


        # values_flat = np.ndarray.flatten(self.data)
        lower, upper = np.nanpercentile(self.data, list(percentile_region))
        clipped_data = np.clip(self.data, lower, upper)
        normalized_data = (clipped_data - lower) / (upper - lower + EPS32)

        #
        # np.nan_to_num(normalized_values, copy=False, nan=1.0)
        # np.clip(normalized_values, 0, 1, out=normalized_values)

        if self.cache_path:
            norm_path = self.cache_path.with_suffix(self.NORMALIZED_SUFFIX_TEMPLATE.format(*percentile_region))
            np.save(norm_path, normalized_data)
            normalized_memmap = np.load(norm_path, mmap_mode="r+")
            self._normalized_cache[percentile_region] = normalized_memmap

            np.savez(self.cache_dict_path, **{str(k): str(v.filename) for k, v in self._normalized_cache.items()})
            return normalized_memmap
        else:
            self._normalized_cache[percentile_region] = normalized_data
            return normalized_data

    def save_image(self, image_path: Path, normalize: bool = True,
                   normalization_percentiles: Optional[tuple[int, int]] = None,
                   replace_nan_with: str = "max", colormap: Optional[str] = None, override_path_changes: bool = False) -> Path:
        if not image_path.parent.exists():
            image_path.parent.mkdir(parents=True)

        if normalization_percentiles is None:
            normalization_percentiles = (0, 100)

        if normalize and not override_path_changes:
            image_path = image_path.with_stem(image_path.stem +
                                              f"_norm_{normalization_percentiles[0]}_{normalization_percentiles[1]}")
        if colormap and not override_path_changes:
            image_path = image_path.with_stem(image_path.stem + f"_{colormap}")

        data = self.normalized(percentile_region=normalization_percentiles) if normalize else self.data

        data = convert_to_image(data, replace_nan_with, normalize, colormap)

        iio.imwrite(image_path, data)
        logger.info(f"Saved image to {image_path}")
        return image_path
