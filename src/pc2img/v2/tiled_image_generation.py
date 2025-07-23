from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import partial, reduce
import hashlib
from joblib import Parallel, delayed
import logging
from pathlib import Path
import pickle
from typing import Optional, Iterable, Generator

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import imageio.v3 as iio  # TODO: Remove after meeting

import pchandler as pch
from pchandler.fov import FoV, FoVTree
from pchandler.geometry import PointCloudData
from pchandler.geometry.splitter import FoVTreePointCloudSplitter

# from pc2img.image_processing import ImageGenerator
from .image_generation import SphericalImageGeneratorFromPCD
from .core import PCDImageLink, ImageStack, ImageData
from .util import convert_to_image

logger = logging.getLogger(__name__.split(".")[0])


@dataclass(frozen=True)
class CommonTiledImageGeneratorSettings:
    # pcd_directory: Path
    image_resolution: tuple[int, int]  # width x height
    angular_resolution_gon: float
    rasterization_method: str
    rasterization_method_overview: str = 'raw'
    # rasterization_features: Iterable[str]
    fov_roi: Optional[FoV] = None

    image_base_directory: Optional[Path] = None
    cache_base_directory: Optional[Path] = None

    def __post_init__(self):
        if self.image_base_directory is not None and not self.image_base_directory.exists():
            self.image_base_directory.mkdir(parents=True)
        if self.cache_base_directory is not None and not self.cache_base_directory.exists():
            self.cache_base_directory.mkdir(parents=True)

        logger.debug(f"Created config dict with {self.image_resolution=}; {self.angular_resolution_gon=}; "
                     f"{self.rasterization_method=}; {self.rasterization_method_overview=}; {self.fov_roi=};"
                     f"{self.image_base_directory=}; {self.cache_base_directory=}")




class CommonTiledImageGeneratorFromPCDs:
    def __init__(self, pcds: dict[str, PointCloudData], config: CommonTiledImageGeneratorSettings, cache_key: str):
        self.pcds = pcds
        self.config = config
        # self.image_base_directory = config.image_base_directory
        # self.image_resolution = config.image_resolution
        # self.angular_resolution_gon = config.angular_resolution_gon
        # self.rasterization_method = config.rasterization_method
        # self.rasterization_method_overview = config.rasterization_method_overview
        self.cache_base_directory = config.cache_base_directory / cache_key if config.cache_base_directory else None

        # self.fov_roi = config.fov_roi
        if self.fov_roi is None:
            fovs = [pcd.fov for pcd in self.pcds.values()]
            self.fov_roi = reduce(lambda f1, f2: f1.intersect(f2), fovs)
            logger.info(f"Found {self.fov_roi.as_dict('gon')=}")

        self.fov_structure = None
        self.common_tile_pcd = {}
        self.cache_file = (
                    config.cache_base_directory / f"{cache_key}.pkl") if config.cache_base_directory else None

    @classmethod
    def from_pcds_or_cache(cls, pcd_paths: dict[str, Path], config: CommonTiledImageGeneratorSettings) -> "CommonTiledImageGeneratorFromPCDs":
        cache_key = cls._generate_cache_key(list(pcd_paths.keys()), config)
        cache_file = config.cache_base_directory / f"{cache_key}.pkl" if config.cache_base_directory else None

        if cache_file and cache_file.exists():
            logger.info(f"Loading from cache: {cache_file}")
            with open(cache_file, "rb") as f:
                return pickle.load(f)

        logger.info("No cache found. Loading PCDs and creating new instance.")
        pcds = {name: PointCloudData.load_from_path(path) for name, path in pcd_paths.items()}
        instance = cls(pcds, config, cache_key)
        instance.cache_current_state()
        return instance

    @classmethod
    def is_cached(cls, pcds_paths: list[str], config: CommonTiledImageGeneratorSettings) -> bool:
        if not config.cache_base_directory:
            return False
        cache_key = cls._generate_cache_key(sorted(pcds_paths), config)
        return (config.cache_base_directory / f"{cache_key}.pkl").exists()



    # def __init__(self, pcds: dict[str, PointCloudData], config: CommonTiledImageGeneratorSettings):
    #     # Generate a unique cache key
    #     cache_key = self._generate_cache_key(list(pcds.keys()), config)
    #     logger.debug(f"Generated cache key {cache_key}")
    #     cache_file = (config.cache_base_directory / f"{cache_key}.pkl") if config.cache_base_directory else None
    #
    #     # Try to load from cache if the file exists
    #     if cache_file and cache_file.exists():
    #         logger.info(f"Loading cache file {cache_file}")
    #         with open(cache_file, 'rb') as f:
    #             cached_object = pickle.load(f)
    #         self.__dict__.update(cached_object.__dict__)
    #         return
    #
    #
    #     self.pcds = pcds
    #     # self.config = config
    #     self.image_base_directory = config.image_base_directory
    #     self.image_resolution = config.image_resolution
    #     self.angular_resolution_gon = config.angular_resolution_gon
    #     self.rasterization_method = config.rasterization_method
    #     self.rasterization_method_overview = config.rasterization_method_overview
    #
    #     self.image_base_directory = config.image_base_directory
    #     self.cache_base_directory = config.cache_base_directory / cache_key if config.cache_base_directory else None
    #
    #     # self.rasterization_features = config.rasterization_features
    #     # if self.rasterization_features is None:
    #     #     self.rasterization_features = [
    #     #         ("scalar_Intensity", ImageGenerator.NormalizationFlag.BOTH),
    #     #         ("range", ImageGenerator.NormalizationFlag.NORMALIZATION)
    #     #     ]
    #
    #     self.fov_roi = config.fov_roi
    #     if self.fov_roi is None:
    #         fovs = [pcd.fov for pcd in self.pcds.values()]
    #         self.fov_roi = reduce(lambda fov1, fov2: fov1.intersect(fov2), fovs)
    #         # pcds_downsampled = [pcd.random_subsample(1. / 100., in_place=False) for pcd in self.pcds.values()]
    #         # pcd_merged = PointCloudData.merge_pcd(pcds_downsampled)
    #         # self.fov_roi = pcd_merged.fov
    #         logger.info(f"Found {self.fov_roi.as_dict('gon')=}")
    #
    #     self.fov_structure = None
    #     self.common_tile_pcd = {}
    #     self.cache_file = cache_file
    #
    #     # Save to cache for future use
    #     self.cache_current_state()

    def cache_current_state(self):
        if self.cache_file:
            logger.info(f"Saving state to cached file {self.cache_file}")
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self, f)


    @property
    def available_tiles(self) -> list[str]:
        return sorted(self.common_tile_pcd.keys())

    @property
    def available_pcds(self) -> list[str]:
        return sorted(self.pcds.keys())

    @staticmethod
    def _generate_cache_key(pcds_paths: list[str], config: CommonTiledImageGeneratorSettings) -> str:
        # Convert properties to a string and hash for a unique cache key
        key_data = (
            str(config.image_resolution),
            str(config.angular_resolution_gon),
            config.rasterization_method,
            str(config.fov_roi),
            str(sorted(pcds_paths))
        )
        return hashlib.md5("_".join(key_data).encode()).hexdigest()

    @classmethod
    def check_for_cache(cls, pcds_paths: list[Path], config: CommonTiledImageGeneratorSettings) -> bool:
        if config.cache_base_directory is None:
            return False
        cache_key = cls._generate_cache_key([p.stem for p in pcds_paths], config)
        cache_result = True if (config.cache_base_directory / f"{cache_key}.pkl").exists() else False
        return cache_result


    def split_pcds_on_fov_tree(self, fov_tree: FoVTree = None, overwrite: bool = False, n_jobs: int = -1):
        if not overwrite and self.common_tile_pcd:
            return

        if fov_tree is None:
            # Build common FoVTree to split the pointclouds
            fov_target_patch_size = FoV(elevation_min=0,
                                        elevation_max=self.image_resolution[0] * self.angular_resolution_gon,
                                        horizontal_min=0,
                                        horizontal_max=self.image_resolution[1] * self.angular_resolution_gon,
                                        unit="gon")

            fov_patches = self.fov_roi.tile(fov_target_patch_size)
            self.fov_structure = FoVTree.build_from_tiles(fov_patches)
        else:
            self.fov_structure = fov_tree

        pcd_splitter = FoVTreePointCloudSplitter(self.fov_structure, remove_empty=True, n_jobs=n_jobs, method="iterative")
        pcds_tree = {pcd_id: pcd_splitter.split(pcd.copy()) for pcd_id, pcd in self.pcds.items()}

        # pcds_tree = {pcd_id: split_pc_with_fov_tree(pcd.copy(), self.fov_structure, True, -5) for pcd_id, pcd in self.pcds.items()}
        common_tile_ids = sorted(list(set.intersection(*[set(tiled_pcd.keys()) for tiled_pcd in pcds_tree.values()])))
        logger.info(f"A total of {len(common_tile_ids)} tiles were found")
        pcd_ids = sorted(pcds_tree.keys())
        #
        # image_generator_skeleton = partial(SphericalImageGeneratorFromPCD, image_resolution=self.image_resolution,
        #                                    rasterization_method=self.rasterization_method, minimum_nb_points=0)
        for tile_id in common_tile_ids:
            image_generator_skeleton = partial(SphericalImageGeneratorFromPCD, image_resolution=self.image_resolution,
                                               rasterization_method=self.rasterization_method, minimum_nb_points=0,
                                               fov=self.fov_structure[tile_id].node)
            self.common_tile_pcd[tile_id] = {
                pcd_id: PCDImageLink(pcd=pcds_tree[pcd_id][tile_id],
                                     image_generators_skeletons=[image_generator_skeleton], identifier=tile_id,
                                     cache_folder=self.cache_base_directory / pcd_id / tile_id if self.cache_base_directory else None)
                for pcd_id in pcd_ids
            }

        self.cache_current_state()



    def get_feature(self, tile_id: str, feature: str, normalize: bool = False,
                    normilization_percentiles: tuple[int, int] = (0, 100), replace_nan_with: Optional[str] = None) -> dict[str, np.ndarray | np.memmap]:

        if self.common_tile_pcd is None:
            raise RuntimeError("Cannot call 'get_feature' before splitting the pointclouds!")

        feature_data = {pcd_id: pcd_link.get_image_data(pcd_link.available_stacks[0], feature, normalize, normilization_percentiles, replace_nan_with)
                        for pcd_id, pcd_link in self.common_tile_pcd[tile_id].items()}
        return feature_data

    # def save_all_images(self, feature: str, normalize: bool = True, normilization_percentiles: tuple[int,int] = (0,100)):
    #     for tile_id in self.available_tiles:
    #         for pcd_id, pcd_link in self.common_tile_pcd[tile_id].items():
    #             pcd_link.save_stack_as_images(
    #                 self.image_base_directory / f"{pcd_id}_{tile_id}",
    #                 pcd_link.available_stacks[0], feature, normalize, normilization_percentiles
    #             )

    def save_all_images(self, feature: str, normalize: bool = True,
                        normilization_percentiles: tuple[int, int] = (0, 100), replace_nan: str = 'max',
                        colormap: Optional[str] = None, n_jobs: int = -1) -> None:
        logger.info(f"Saving all images for {feature} to {self.image_resolution}")
        # Define the task to parallelize
        def save_image_task(tile_id, pcd_id, pcd_link):
            pcd_link.save_stack_as_images(
                self.image_base_directory / f"{pcd_id}_{tile_id}",
                pcd_link.available_stacks[0], feature, normalize, normilization_percentiles, replace_nan, colormap,
            )

        # Create a list of tasks
        tasks = [
            (tile_id, pcd_id, pcd_link)
            for tile_id in self.available_tiles
            for pcd_id, pcd_link in self.common_tile_pcd[tile_id].items()
        ]


        # Run the tasks in parallel
        Parallel(n_jobs=n_jobs, verbose=50)(delayed(save_image_task)(tile_id, pcd_id, pcd_link)
                                    for tile_id, pcd_id, pcd_link in tasks)


    def __getitem__(self, tile_id: str) -> dict[str, PCDImageLink]:
        return self.common_tile_pcd[tile_id]

    def generate_overview_image(self, image_path: Optional[Path] = None, feature: str = "intensity", normalize: bool = False,
                                normilization_percentiles: tuple[int,int] = (0,100), replace_nan_with: str = "max",
                                colormap: Optional[str] = None, image_width: int = 12000, fov: Optional[FoV] = None,
                                annotate_fovs: bool = True, pcd_id: Optional[str] = None):

        if pcd_id is None:
            pcd_id = self.available_pcds[0]

        if pcd_id not in self.available_pcds:
            raise ValueError(f"The pcd_id given '{pcd_id}' is not available!")

        if fov is None:
            fov = self.fov_roi

        if image_path is None:
            image_path = self.image_base_directory / "overview.png"

        image_resolution = (int(image_width / fov.ratio()), image_width)

        logger.info(f"Generating overview image of size {image_resolution} for {feature} and saving to {image_path}")

        overview_image_link = PCDImageLink(
            self.pcds[pcd_id],
            [partial(SphericalImageGeneratorFromPCD, image_resolution=image_resolution,
                    rasterization_method="nanconv", minimum_nb_points=0)]
        )
        overview_path =  overview_image_link.save_stack_as_images(image_path, overview_image_link.available_stacks[0],
                                                                  feature, normalize, normilization_percentiles,
                                                                  replace_nan_with, colormap)

        if annotate_fovs:
            self.annotate_overview_image(overview_path[0], fov)


    def annotate_overview_image(self, overview_path: Path, overview_fov: FoV) -> None:
        def calculate_font_size(text, max_width, max_height, font_path, initial_font_size=10):
            # Create a temporary image to draw text
            temp_image = Image.new('RGB', (1, 1), 'white')
            draw = ImageDraw.Draw(temp_image)

            font_size = initial_font_size
            while True:
                font = ImageFont.truetype(font_path, font_size)
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # Check if either dimension exceeds the allowed space
                if text_width > max_width or text_height > max_height:
                    break
                font_size += 1

            return font_size - 1  # Return the last valid size that fit

        # Open the image
        image = Image.open(overview_path)
        overview_px_width, overview_px_height = image.size
        overview_rad_width, overview_rad_height = overview_fov.extent("rad")

        overview_ratio_width = overview_px_width / overview_rad_width
        overview_ratio_height = overview_px_height / overview_rad_height

        overview_rad_width_min, overview_rad_height_min = overview_fov.as_tuple("rad")[0:2]

        image = image.convert("RGB")

        draw = ImageDraw.Draw(image)

        if isinstance(self.fov_structure, FoVTree):
            fov_list = self.fov_structure.to_list()
        for fov_identifier, fov in fov_list:
            fov_rad_width_min, fov_rad_height_min, fov_rad_width_max, fov_rad_height_max = fov.as_tuple("rad")
            x1 = (fov_rad_width_min - overview_rad_width_min) * overview_ratio_width
            y1 = (fov_rad_height_min - overview_rad_height_min) * overview_ratio_height
            x2 = (fov_rad_width_max - overview_rad_width_min) * overview_ratio_width
            y2 = (fov_rad_height_max - overview_rad_height_min) * overview_ratio_height

            # Draw the rectangle
            draw.rectangle((x1, y1, x2, y2), outline="red", width=3)

            # Load a font
            # font = ImageFont.load_default()  # Using the default font
            # To use a specific font file, uncomment the line below and provide the path to your font file
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

            max_text_width = 0.5 * (x2 - x1)
            max_text_height = 0.25 * (y2 - y1)
            font_size = calculate_font_size(fov_identifier, max_text_width, max_text_height, font_path, 1)

            # font_size = calculate_font_size(fov_identifier, int(0.25*(y2-y1)), font_path, 12)
            font = ImageFont.truetype(font_path, font_size)

            # Calculate the text size to center it
            text_width, text_height = draw.textbbox((0, 0), fov_identifier, font=font)[2:4]
            text_x = x1 + (x2 - x1 - text_width) / 2
            text_y = y1 + (y2 - y1 - text_height) / 2

            # Add text to the image
            draw.text((text_x, text_y), fov_identifier, fill="red", font=font)

        image.save(overview_path.with_stem(overview_path.stem + "_annotated"))
        return

