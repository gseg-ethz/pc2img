from pathlib import Path
from typing import Optional

from pchandler.data_io import load_ply

from pc2img.tiled_image_generation import TiledImageGenerationSettings, TiledImageGeneration


def main(pcd_path: Path, config: TiledImageGenerationSettings, range_filter: Optional[dict[str,float]] = None):

    assert set(range_filter.keys()).issubset(["low", "high"])

    pcd = load_ply(pcd_path)
    if not range_filter is None:
        pcd = pcd.extract_range(**range_filter)


    tiled_image_generator = TiledImageGeneration([pcd], config)
    tiled_image_generator.generate_overview_image(pcd=pcd,
                                                  image_path=tiled_image_generator.image_results_directory / "_overview.png")

    tiled_image_generator.annotate_overview_image(overview_fov=tiled_image_generator.fov_roi,
                                                  overview_path=tiled_image_generator.image_results_directory / "_overview.png")

    pcds_rasterized_data = tiled_image_generator.generate_tiled_images()


if __name__ == "__main__":
    PCD_PATH = Path(r"/scratch/00_data/BAFU/scan01.ply")
    IMAGES_DIR = Path(r"/scratch/00_data/BAFU/images")

    IMAGE_RESOLUTION = (480, 1000)  # height x width
    ANGULAR_RESOLUTION_GON = 3e-3
    FEATURES = [
        ("scalar_Intensity", 2),
        ("range", 1),
        ("hillshade", 1),
        ("hillshade_0_45_1.0", 1),
        # ("hillshade_0_90_1.0", 1),
        # ("hillshade_90_0_1.0", 1),
        # ("hillshade_90_45_1.0", 1),
        # ("hillshade_90_90_1.0", 1),
        # ("gradient_x_range", 1),
        # ("gradient_y_range", 1),
    ]
    FOV_ROI = None

    config = TiledImageGenerationSettings(image_results_directory=IMAGES_DIR,
                                          image_resolution=IMAGE_RESOLUTION,
                                          angular_resolution_gon=ANGULAR_RESOLUTION_GON,
                                          rasterization_features=FEATURES,
                                          fov_roi=FOV_ROI)

    main(pcd_path=PCD_PATH)
