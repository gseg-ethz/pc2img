from pathlib import Path
from typing import Optional, Iterable

import numpy as np

import imageio.v3 as iio  # TODO: Remove after meeting

import pchandler as pch
from pchandler.fov import FoV, FoVTree
from pchandler.geometry import PointCloudData, merge_pcd, split_pc_with_fov_tree

from pc2img.image_processing import ImageGenerator


def generate_and_save_images(pcd_directory: Path, results_directory: Path, image_resolution: tuple[int, int],
              angular_resolution_gon: float, fov_roi: Optional[FoV] = None, scanner_center: Optional[np.ndarray] = None,
              features: Optional[Iterable[tuple[str, int]]] = None) -> int:
    # features: The int can be 0, 1 or 2; 0 means save original, 1 normalized, 2 both

    pcd_path_list = pch.data_io.find_pcd_in_directory(pcd_directory, pcd_file_types=['.ply'],
                                                      include_subdirectories=False)

    pcds: [PointCloudData] = [pch.data_io.load_ply(pcd_path, spherical_coordinates_origin=scanner_center).
                              extract_range(low=25) for pcd_path in pcd_path_list]

    # Find combined FoV if not defined
    if fov_roi is None:
        pcds_downsampled = [pcd.random_subsample(1./100., in_place=False) for pcd in pcds]
        pcd_merged = merge_pcd(pcds_downsampled)
        fov_roi = pcd_merged.fov

    if features is None:
        features = [("scalar_Intensity", 2), ("range", 1)]

    field_labels = [f[0] for f in features]

    # Build common FoVTree to split the pointclouds
    fov_patch_size = FoV(elevation_min=0, elevation_max=image_resolution[0] * angular_resolution_gon,
                         horizontal_min=0, horizontal_max=image_resolution[1] * angular_resolution_gon, unit="gon")

    fov_patches = fov_roi.tile(fov_patch_size)
    fov_tree = FoVTree.build_from_tiles(fov_patches)

    pcds_tree = [split_pc_with_fov_tree(pcd, fov_tree, True, -5) for pcd in pcds]

    for i, pcd in enumerate(pcds_tree):
        image_gen = ImageGenerator(image_resolution=image_resolution, minimum_nb_points=0,
                                       image_folder=results_directory)
        for cfk in pcd.keys():
            try:
                pcd_2d = image_gen.project_and_rasterize_2d(
                    fov_tree[cfk].node, pcd[cfk], False, field_labels=field_labels,
                    rasterization_method="delaunay"
                )

                for feature in features:
                    match feature[1]:
                        case 0:
                            iio.imwrite(results_directory / f"{i:02d}_{cfk}_{feature[0]}.png",
                                        (np.nan_to_num(pcd_2d[0][feature[0]]["original_values"],
                                                       copy=True, nan=1.0) * 255).astype(np.uint8))
                        case 1:
                            iio.imwrite(results_directory / f"{i:02d}_{cfk}_{feature[0]}_normalized.png",
                                        (pcd_2d[0][feature[0]]["normalized_values"][0] * 255).astype(np.uint8))
                        case 2:
                            iio.imwrite(results_directory / f"{i:02d}_{cfk}_{feature[0]}.png",
                                        (np.nan_to_num(pcd_2d[0][feature[0]]["original_values"],
                                                       copy=True, nan=1.0) * 255).astype(np.uint8))
                            iio.imwrite(results_directory / f"{i:02d}_{cfk}_{feature[0]}_normalized.png",
                                        (pcd_2d[0][feature[0]]["normalized_values"][0] * 255).astype(np.uint8))

                print(f"Patch {cfk} done and saved")
            except:
                print(f"!Patch {cfk} failed")
    return 0


if __name__ == "__main__":
    PCD_DIR = Path(r"/scratch/31_PCProjectionImage/_data/01_scans/Axpo_May24")
    RESULTS_FOLDER = Path(r"/scratch/31_PCProjectionImage/_data/02_results/42_Axpo_May24/"
                          r"09_MinAR_6mgon_FoV_1920x4000")

    FEATURES = [("scalar_Intensity", 2), ("range", 1), ("hillshade", 1), ("hillshade_0_0_1.0", 1),
                ("hillshade_0_45_1.0", 1), ("hillshade_0_90_1.0", 1), ("hillshade_0_135_1.0", 1),
                ("hillshade_0_180_1.0", 1), ("hillshade_90_0_1.0", 1), ("hillshade_90_45_1.0", 1),
                ("hillshade_90_90_1.0", 1), ("hillshade_90_135_1.0", 1),
                ("hillshade_90_180_1.0", 1), ]
    SCANNER_CENTER = None
    FOV_ROI = None

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    IMAGE_RESOLUTION = (1920, 4000) # height x width
    ANGULAR_RESOLUTION_GON = 6e-3

    generate_and_save_images(PCD_DIR, RESULTS_FOLDER, IMAGE_RESOLUTION, ANGULAR_RESOLUTION_GON,
                         scanner_center=SCANNER_CENTER, fov_roi=FOV_ROI, features=FEATURES)
