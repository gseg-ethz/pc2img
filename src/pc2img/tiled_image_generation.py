from collections import defaultdict
from dataclasses import dataclass
from functools import partial
import hashlib
from joblib import Parallel, delayed
from pathlib import Path
import pickle
from typing import Optional, Iterable, Generator

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import imageio.v3 as iio  # TODO: Remove after meeting

import pchandler as pch
from markdown_it.rules_inline import image
from pchandler.fov import FoV, FoVTree
from pchandler.geometry import PointCloudData, split_pc_with_fov_tree

# from pc2img.image_processing import ImageGenerator
from pc2img.image_generation import SphericalImageGeneratorFromPCD
from pc2img.core import PCDImageLink, ImageStack, ImageData

# @dataclass
# class TiledImageGenerationSettings:
#     # pcd_directory: Path
#     image_results_directory: Path
#     image_resolution: tuple[int, int]
#     angular_resolution_gon: float
#     rasterization_features: Iterable[tuple[str, ImageGenerator.NormalizationFlag]]
#     fov_roi: Optional[FoV] = None
#
#     def __post_init__(self):
#         self.rasterization_features = [(feature, ImageGenerator.NormalizationFlag(value)) for feature, value in self.rasterization_features]
#
#         if not self.image_results_directory.exists():
#             self.image_results_directory.mkdir(parents=True)
#
#
# class TiledImageGeneration:
#
#
#     def __init__(self, pcds: Iterable[PointCloudData], config: TiledImageGenerationSettings):
#         self.pcds = pcds
#         #self.config = config
#         self.image_results_directory = config.image_results_directory
#         self.image_resolution = config.image_resolution
#         self.angular_resolution_gon = config.angular_resolution_gon
#
#         self.rasterization_features = config.rasterization_features
#         if self.rasterization_features is None:
#             self.rasterization_features = [
#                 ("scalar_Intensity", ImageGenerator.NormalizationFlag.BOTH),
#                 ("range", ImageGenerator.NormalizationFlag.NORMALIZATION)
#             ]
#
#         self.fov_roi = config.fov_roi
#         if self.fov_roi is None:
#             pcds_downsampled = [pcd.random_subsample(1. / 100., in_place=False) for pcd in self.pcds.values()]
#             pcd_merged = PointCloudData.merge_pcd(pcds_downsampled)
#             self.fov_roi = pcd_merged.fov
#
#         # Build common FoVTree to split the pointclouds
#         fov_target_patch_size = FoV(elevation_min=0, elevation_max=self.image_resolution[0] * self.angular_resolution_gon,
#                                     horizontal_min=0, horizontal_max=self.image_resolution[1] * self.angular_resolution_gon,
#                                     unit="gon")
#
#         fov_patches = self.fov_roi.tile(fov_target_patch_size)
#         self.fov_tree = FoVTree.build_from_tiles(fov_patches)
#
#     def generate_tiled_images(self
#                               ) -> dict[
#         str, dict[str, tuple[dict[str, dict[str, np.ndarray, tuple[np.ndarray, tuple[float, float]]]], FoV]]]:
#
#         # if self.image_results_directory is not None:
#         #     first_epoch = sorted(self.pcds.keys())[0]
#         #     self.generate_overview_image(self.pcds[first_epoch].copy(), self.image_results_directory / "_overview.png",
#         #                                  return_fov=False)
#         #     self.annotate_overview_image(overview_fov=self.fov_roi,
#         #                                  overview_path=self.image_results_directory / "_overview.png")
#
#         pcds_tree = {pcd_id: split_pc_with_fov_tree(pcd, self.fov_tree, True, -5) for pcd_id, pcd in self.pcds.items()}
#
#         rasterization_results = defaultdict(dict)
#         for pcd_id, pcd in pcds_tree.items():
#             image_gen = ImageGenerator(image_resolution=self.image_resolution, minimum_nb_points=1000,
#                                        rasterization_method="delaunay", results_folder=self.image_results_directory)
#             for cfk in pcd.keys():
#                 try:
#                     if self.image_results_directory is not None:
#                         pcd2d = image_gen.generate_and_save_image(self.fov_tree[cfk].node, pcd[cfk], f"{pcd_id}_{cfk}",
#                                                                   self.rasterization_features, False)
#                     else:
#                         pcd2d = image_gen.project_and_rasterize_2d(pcd[cfk], fov_tree[cfk].node, False,
#                                                                    [feature[0] for feature in self.rasterization_features])
#                     if pcd2d is None:
#                         print(f"Point cloud {pcd_id}, patch {cfk} had too few points to generate sensible image.")
#                         continue
#                     rasterization_results[pcd_id][cfk] = pcd2d
#                     print(f"Point cloud {pcd_id}, patch {cfk} done and saved")
#                 except Exception as e:
#                     print(f"!Point cloud {pcd_id}, patch {cfk} failed due to {e}")
#         return rasterization_results
#
#     def tiled_images_generator(self) :# -> Generator[tuple[str, str, None | tuple[dict[str, dict[str, np.ndarray, tuple[np.ndarray, tuple[float, float]]]], FoV]]]:
#
#         # if self.image_results_directory is not None:
#         #     first_epoch = sorted(self.pcds.keys())[0]
#         #     self.generate_overview_image(self.pcds[first_epoch].copy(), self.image_results_directory / "_overview.png",
#         #                                  return_fov=False)
#         #     self.annotate_overview_image(overview_fov=self.fov_roi,
#         #                                  overview_path=self.image_results_directory / "_overview.png")
#
#         pcds_tree = {pcd_id: split_pc_with_fov_tree(pcd, self.fov_tree, True, -5) for pcd_id, pcd in self.pcds.items()}
#
#         rasterization_results = defaultdict(dict)
#         for pcd_id, pcd in pcds_tree.items():
#             image_gen = ImageGenerator(image_resolution=self.image_resolution, minimum_nb_points=1000,
#                                        rasterization_method="delaunay", results_folder=self.image_results_directory)
#             for cfk in pcd.keys():
#                 try:
#                     if self.image_results_directory is not None:
#                         pcd2d = image_gen.generate_and_save_image(self.fov_tree[cfk].node, pcd[cfk], f"{pcd_id}_{cfk}",
#                                                                   self.rasterization_features, False)
#                     else:
#                         pcd2d = image_gen.project_and_rasterize_2d(pcd[cfk], fov_tree[cfk].node, False,
#                                                                    [feature[0] for feature in self.rasterization_features])
#                     if pcd2d is None:
#                         print(f"Point cloud {pcd_id}, patch {cfk} had too few points to generate sensible image.")
#                         continue
#                     # rasterization_results[pcd_id][cfk] = pcd2d
#                     print(f"Point cloud {pcd_id}, patch {cfk} done and saved")
#                     yield (pcd_id, cfk, pcd2d)
#                 except Exception as e:
#                     print(f"!Point cloud {pcd_id}, patch {cfk} failed due to {e}")
#         return rasterization_results
#
#
#     def generate_overview_image(self, pcd: PointCloudData, image_path: Path, image_width: int = 12000,
#                                 return_fov: bool = False) -> Optional[FoV]:
#         image_resolution = (int(image_width / self.fov_roi.ratio()), image_width)
#         image_gen = ImageGenerator(image_resolution=image_resolution, minimum_nb_points=0, rasterization_method="raw",
#                                    results_folder=image_path.parent)
#         image_data = image_gen.project_and_rasterize_2d(fov=self.fov_roi, pcd=pcd.copy(), downsample_pcd=True,
#                                                         field_labels="scalar_Intensity")
#
#         image = np.nan_to_num(image_data[0]["scalar_Intensity"]["original_values"], copy=True, nan=1.0)
#         iio.imwrite(image_path, (image * 255).astype(np.uint8))
#         return image_data[1] if return_fov else None
#
#
#     def annotate_overview_image(self, overview_path: Path, overview_fov: FoV) -> None:
#         def calculate_font_size(text, desired_height, font_path, initial_font_size=10):
#             # Create a temporary image to draw text
#             temp_image = Image.new('RGB', (1, 1), 'white')
#             draw = ImageDraw.Draw(temp_image)
#
#             font_size = initial_font_size
#             while True:
#                 font = ImageFont.truetype(font_path, font_size)
#                 text_bbox = draw.textbbox((0, 0), text, font=font)
#                 text_height = text_bbox[3] - text_bbox[1]
#
#                 # Check if the text height is close to the desired height
#                 if text_height >= desired_height:
#                     break
#                 font_size += 1
#
#             return font_size
#
#         # Open the image
#         image = Image.open(overview_path)
#         overview_px_width, overview_px_height = image.size
#         overview_rad_width, overview_rad_height = overview_fov.extent("rad")
#
#         overview_ratio_width = overview_px_width / overview_rad_width
#         overview_ratio_height = overview_px_height / overview_rad_height
#
#         overview_rad_width_min, overview_rad_height_min = overview_fov.as_tuple("rad")[0:2]
#
#         image = image.convert("RGB")
#
#         draw = ImageDraw.Draw(image)
#
#         fov_list = self.fov_tree.to_list()
#         for fov_identifier, fov in fov_list:
#             fov_rad_width_min, fov_rad_height_min, fov_rad_width_max, fov_rad_height_max = fov.as_tuple("rad")
#             x1 = (fov_rad_width_min - overview_rad_width_min) * overview_ratio_width
#             y1 = (fov_rad_height_min - overview_rad_height_min) * overview_ratio_height
#             x2 = (fov_rad_width_max - overview_rad_width_min) * overview_ratio_width
#             y2 = (fov_rad_height_max - overview_rad_height_min) * overview_ratio_height
#
#             # Draw the rectangle
#             draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
#
#             # Load a font
#             # font = ImageFont.load_default()  # Using the default font
#             # To use a specific font file, uncomment the line below and provide the path to your font file
#             font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
#
#             font_size = calculate_font_size(fov_identifier, int(0.25*(y2-y1)), font_path, 12)
#             font = ImageFont.truetype(font_path, font_size)
#
#             # Calculate the text size to center it
#             text_width, text_height = draw.textbbox((0, 0), fov_identifier, font=font)[2:4]
#             text_x = x1 + (x2 - x1 - text_width) / 2
#             text_y = y1 + (y2 - y1 - text_height) / 2
#
#             # Add text to the image
#             draw.text((text_x, text_y), fov_identifier, fill="red", font=font)
#
#         image.save(overview_path.with_stem(overview_path.stem + "_annotated"))
#         return


@dataclass
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

class CommonTiledImageGeneratorFromPCDs:

    def __init__(self, pcds: dict[str, PointCloudData], config: CommonTiledImageGeneratorSettings):
        # Generate a unique cache key
        cache_key = self._generate_cache_key(list(pcds.keys()), config)
        cache_file = (config.cache_base_directory / f"{cache_key}.pkl") if config.cache_base_directory else None

        # Try to load from cache if the file exists
        if cache_file and cache_file.exists():
            with open(cache_file, 'rb') as f:
                cached_object = pickle.load(f)
            self.__dict__.update(cached_object.__dict__)
            return


        self.pcds = pcds
        # self.config = config
        self.image_base_directory = config.image_base_directory
        self.image_resolution = config.image_resolution
        self.angular_resolution_gon = config.angular_resolution_gon
        self.rasterization_method = config.rasterization_method
        self.rasterization_method_overview = config.rasterization_method_overview

        self.image_base_directory = config.image_base_directory
        self.cache_base_directory = config.cache_base_directory / cache_key

        # self.rasterization_features = config.rasterization_features
        # if self.rasterization_features is None:
        #     self.rasterization_features = [
        #         ("scalar_Intensity", ImageGenerator.NormalizationFlag.BOTH),
        #         ("range", ImageGenerator.NormalizationFlag.NORMALIZATION)
        #     ]

        self.fov_roi = config.fov_roi
        if self.fov_roi is None:
            pcds_downsampled = [pcd.random_subsample(1. / 100., in_place=False) for pcd in self.pcds.values()]
            pcd_merged = PointCloudData.merge_pcd(pcds_downsampled)
            self.fov_roi = pcd_merged.fov

        self.fov_structure = None
        self.common_tile_pcd = {}
        self.cache_file = cache_file

        # Save to cache for future use
        self.cache_current_state()

    def cache_current_state(self):
        if self.cache_file:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self, f)


    @property
    def available_tiles(self) -> list[str]:
        return sorted(self.common_tile_pcd.keys())

    @property
    def available_pcds(self) -> list[str]:
        return sorted(self.pcds.keys())

    @classmethod
    def _generate_cache_key(cls, pcds_paths: list[str], config: CommonTiledImageGeneratorSettings) -> str:
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


    def split_pcds_on_fov_tree(self, fov_tree: FoVTree = None):
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

        pcds_tree = {pcd_id: split_pc_with_fov_tree(pcd.copy(), self.fov_structure, True, -5) for pcd_id, pcd in self.pcds.items()}
        common_tile_ids = sorted(list(set.intersection(*[set(tiled_pcd.keys()) for tiled_pcd in pcds_tree.values()])))
        pcd_ids = sorted(pcds_tree.keys())

        image_generator_skeleton = partial(SphericalImageGeneratorFromPCD, image_resolution=self.image_resolution,
                                           rasterization_method=self.rasterization_method, minimum_nb_points=0)
        for tile_id in common_tile_ids:
            self.common_tile_pcd[tile_id] = {
                pcd_id: PCDImageLink(pcd=pcds_tree[pcd_id][tile_id],
                                     image_generators_skeletons=[image_generator_skeleton], identifier=tile_id,
                                     cache_folder=self.cache_base_directory / pcd_id / tile_id)
                for pcd_id in pcd_ids
            }

        self.cache_current_state()



    def get_feature(self, tile_id: str, feature: str) -> dict[str, np.ndarray | np.memmap]:
        if self.common_tile_pcd is None:
            raise RuntimeError("Cannot call 'get_feature' before splitting the pointclouds!")
        feature_data = {pcd_id: pcd_link.get_image_data(pcd_link.available_stacks[0], feature)
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
                        normilization_percentiles: tuple[int, int] = (0, 100), n_jobs: int = -1):
        # Define the task to parallelize
        def save_image_task(tile_id, pcd_id, pcd_link):
            pcd_link.save_stack_as_images(
                self.image_base_directory / f"{pcd_id}_{tile_id}",
                pcd_link.available_stacks[0], feature, normalize, normilization_percentiles
            )

        # Create a list of tasks
        tasks = [
            (tile_id, pcd_id, pcd_link)
            for tile_id in self.available_tiles
            for pcd_id, pcd_link in self.common_tile_pcd[tile_id].items()
        ]


            # Run the tasks in parallel
        Parallel(n_jobs=n_jobs)(delayed(save_image_task)(tile_id, pcd_id, pcd_link)
                                    for tile_id, pcd_id, pcd_link in tasks)


    def __getitem__(self, tile_id: str) -> dict[str, PCDImageLink]:
        return self.common_tile_pcd[tile_id]

    def generate_overview_image(self, image_path: Optional[Path] = None, feature: str = "scalar_Intensity", normalize: bool = False,
                                normilization_percentiles: tuple[int,int] = (0,100), image_width: int = 12000,
                                fov: Optional[FoV] = None, annotate_fovs: bool = True, pcd_id: Optional[str] = None):
        if pcd_id is None:
            pcd_id = self.available_pcds[0]

        if pcd_id not in self.available_pcds:
            raise ValueError(f"The pcd_id given '{pcd_id}' is not available!")

        if fov is None:
            fov = self.fov_roi

        if image_path is None:
            image_path = self.image_base_directory / "overview.png"

        image_resolution = (int(image_width / fov.ratio()), image_width)
        image_generator = SphericalImageGeneratorFromPCD(pcd=self.pcds[pcd_id], image_resolution=image_resolution,
                                                         rasterization_method='raw', minimum_nb_points=0, fov=fov)
        rasterization_results = image_generator.project_and_rasterize(feature)
        image_data = rasterization_results[feature]

        image = np.nan_to_num(image_data, nan=1.0)
        iio.imwrite(image_path, (image * 255).astype(np.uint8))

        if annotate_fovs:
            self.annotate_overview_image(image_path, fov)
        print(1)



#     def generate_overview_image(self, pcd: PointCloudData, image_path: Path, image_width: int = 12000,
#                                 return_fov: bool = False) -> Optional[FoV]:
#         image_resolution = (int(image_width / self.fov_roi.ratio()), image_width)
#         image_gen = ImageGenerator(image_resolution=image_resolution, minimum_nb_points=0, rasterization_method="raw",
#                                    results_folder=image_path.parent)
#         image_data = image_gen.project_and_rasterize_2d(fov=self.fov_roi, pcd=pcd.copy(), downsample_pcd=True,
#                                                         field_labels="scalar_Intensity")
#
#         image = np.nan_to_num(image_data[0]["scalar_Intensity"]["original_values"], copy=True, nan=1.0)
#         iio.imwrite(image_path, (image * 255).astype(np.uint8))
#         return image_data[1] if return_fov else None
#
#
    def annotate_overview_image(self, overview_path: Path, overview_fov: FoV) -> None:
        def calculate_font_size(text, desired_height, font_path, initial_font_size=10):
            # Create a temporary image to draw text
            temp_image = Image.new('RGB', (1, 1), 'white')
            draw = ImageDraw.Draw(temp_image)

            font_size = initial_font_size
            while True:
                font = ImageFont.truetype(font_path, font_size)
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_height = text_bbox[3] - text_bbox[1]

                # Check if the text height is close to the desired height
                if text_height >= desired_height:
                    break
                font_size += 1

            return font_size

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

            font_size = calculate_font_size(fov_identifier, int(0.25*(y2-y1)), font_path, 12)
            font = ImageFont.truetype(font_path, font_size)

            # Calculate the text size to center it
            text_width, text_height = draw.textbbox((0, 0), fov_identifier, font=font)[2:4]
            text_x = x1 + (x2 - x1 - text_width) / 2
            text_y = y1 + (y2 - y1 - text_height) / 2

            # Add text to the image
            draw.text((text_x, text_y), fov_identifier, fill="red", font=font)

        image.save(overview_path.with_stem(overview_path.stem + "_annotated"))
        return


if __name__ == "__main__":
    PCD_DIR = Path(r"/scratch/31_PCProjectionImage/_data/01_scans/Axpo_May24")
    RESULTS_FOLDER = Path(r"/scratch/31_PCProjectionImage/_data/02_results/42_Axpo_May24/"
                          r"12_MinAR_6mgon_FoV_1920x4000")

    FEATURES = [("scalar_Intensity", 2), ("range", 1), ("hillshade", 1), ("hillshade_0_0_1.0", 1),
                ("hillshade_0_45_1.0", 1), ("hillshade_0_90_1.0", 1), ("hillshade_0_135_1.0", 1),
                ("hillshade_0_180_1.0", 1), ("hillshade_90_0_1.0", 1), ("hillshade_90_45_1.0", 1),
                ("hillshade_90_90_1.0", 1), ("hillshade_90_135_1.0", 1), ("hillshade_90_180_1.0", 1),
                ("gradient_x_range", 1), ("gradient_y_range", 1), ("gradient_x_scalar_Intensity", 1),
                ("gradient_y_scalar_Intensity", 1)]

    FEATURES = [(feature, ImageGenerator.NormalizationFlag(value)) for feature, value in FEATURES]

    SCANNER_CENTER = None
    FOV_ROI = None

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    IMAGE_RESOLUTION = (1920, 4000) # height x width
    ANGULAR_RESOLUTION_GON = 6e-3

    pcds_2d = generate_tiled_images_from_pcd_folder(
        PCD_DIR, IMAGE_RESOLUTION, ANGULAR_RESOLUTION_GON, scanner_center=SCANNER_CENTER, fov_roi=FOV_ROI,
        features=FEATURES, results_folder=RESULTS_FOLDER)

    print("Done")
