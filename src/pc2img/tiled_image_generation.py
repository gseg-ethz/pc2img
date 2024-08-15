from collections import defaultdict
from pathlib import Path
from typing import Optional, Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import imageio.v3 as iio  # TODO: Remove after meeting

import pchandler as pch
from pchandler.fov import FoV, FoVTree
from pchandler.geometry import PointCloudData, split_pc_with_fov_tree

from pc2img.image_processing import ImageGenerator


def generate_overview_image(pcd: PointCloudData, fov_roi: FoV, image_path: Path, image_width: int = 12000,
                            return_fov: bool = False) \
        -> [None | FoV]:
    image_resolution = (int(image_width / fov_roi.ratio()), image_width)
    image_gen = ImageGenerator(image_resolution=image_resolution, minimum_nb_points=0, rasterization_method="raw",
                               results_folder=image_path.parent)
    image_data = image_gen.project_and_rasterize_2d(fov=fov_roi, pcd=pcd, downsample_pcd=False,
                                                    field_labels="scalar_Intensity")
    image = np.nan_to_num(image_data[0]["scalar_Intensity"]["original_values"], copy=True, nan=1.0)
    iio.imwrite(image_path, (image * 255).astype(np.uint8))
    return image_data[1] if return_fov else None


def annotate_overview_image(overview_path: Path, overview_fov: FoV, fov_tree: FoVTree) -> None:
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

    fov_list = fov_tree.to_list()
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


def generate_tiled_images_from_pcd_folder(
        pcd_folder: Path,
        image_resolution: tuple[int, int],
        angular_resolution_gon: float,
        fov_roi: Optional[FoV] = None,
        scanner_center: Optional[np.ndarray] = None,
        features: Optional[Iterable[tuple[str, ImageGenerator.NormalizationFlag]]] = None,
        results_folder: Optional[Path] = None
) -> dict[int, dict[str, tuple[dict[str, dict[str, np.ndarray, tuple[np.ndarray, tuple[float, float]]]], FoV]]]:

    pcd_path_list = pch.data_io.find_pcd_in_directory(pcd_folder, pcd_file_types=['.ply'],
                                                      include_subdirectories=False)

    pcds: [PointCloudData] = [pch.data_io.load_ply(pcd_path, spherical_coordinates_origin=scanner_center).
                              extract_range(low=25) for pcd_path in pcd_path_list]

    # Find combined FoV if not defined
    if fov_roi is None:
        pcds_downsampled = [pcd.random_subsample(1./100., in_place=False) for pcd in pcds]
        pcd_merged = PointCloudData.merge_pcd(pcds_downsampled)
        fov_roi = pcd_merged.fov

    if features is None:
        features = [("scalar_Intensity", ImageGenerator.NormalizationFlag.BOTH),
                    ("range", ImageGenerator.NormalizationFlag.NORMALIZATION)]

    # Build common FoVTree to split the pointclouds
    fov_patch_size = FoV(elevation_min=0, elevation_max=image_resolution[0] * angular_resolution_gon,
                         horizontal_min=0, horizontal_max=image_resolution[1] * angular_resolution_gon, unit="gon")

    fov_patches = fov_roi.tile(fov_patch_size)
    fov_tree = FoVTree.build_from_tiles(fov_patches)

    if results_folder is not None:
        generate_overview_image(pcds[0].copy(), fov_roi, results_folder / "_overview.png", return_fov=True)
        annotate_overview_image(results_folder / "_overview.png", fov_roi, fov_tree)

    pcds_tree = [split_pc_with_fov_tree(pcd, fov_tree, True, -5) for pcd in pcds]

    rasterization_results = defaultdict(dict)
    for i, pcd in enumerate(pcds_tree):
        image_gen = ImageGenerator(image_resolution=image_resolution, minimum_nb_points=1000,
                                   rasterization_method="delaunay", results_folder=results_folder)
        for cfk in pcd.keys():
            try:
                if results_folder is not None:
                    pcd2d = image_gen.generate_and_save_image(fov_tree[cfk].node, pcd[cfk], f"{i:02d}_{cfk}",
                                                              features, False)
                else:
                    pcd2d = image_gen.project_and_rasterize_2d(pcd[cfk], fov_tree[cfk].node, False,
                                                               [feature[0] for feature in features])
                if pcd2d is None:
                    print(f"Point cloud {i:d}, patch {cfk} had too few points to generate sensible image.")
                    continue
                rasterization_results[i][cfk] = pcd2d
                print(f"Point cloud {i:d}, patch {cfk} done and saved")
            except Exception as e:
                print(f"!Point cloud {i:d}, patch {cfk} failed due to {e}")
    return rasterization_results


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
