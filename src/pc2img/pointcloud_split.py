# TODO: Make angle units more flexible
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import chain
from joblib import Parallel, delayed
import json
import math
from pathlib import Path
from typing import Iterable#, Self
# from typing_extensions import Self
from timeit import default_timer as timer

import numpy as np
# from scipy.interpolate import griddata as scipy_gd
import imageio.v3 as iio
# from imageio.plugins.tifffile_v3 import TifffilePlugin as iio_tiff
import tifffile

import pchandler as pch
from pchandler.fov import FoV, FoVTree
from pchandler.geometry import PointCloudData
# from pc2img.image_processing import ImageGenerator
# from pc2img import image_processing
# from pc2img.image_processing import knn_griddata as knn_griddata
# from pc2img.image_processing import barycentric_interpolation

EPS32 = np.finfo(np.float32).eps


def split_pc_with_fov_tree(self, pcd: PointCloudData, fov_tree: FoVTree, remove_empty: bool = True, n_jobs: int = -1) \
        -> list[tuple[str, FoV, PointCloudData]]:
    """

    """
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


class PointCloudSplitter:
    @property
    def aspect_ratio(self):
        return self.image_resolution[0] / self.image_resolution[1]

    def __init__(self, image_resolution: tuple[int, int], minimum_nb_points: int):

        self.image_resolution = image_resolution # Height x Width [px]
        self.minimum_nb_points = minimum_nb_points

    # def split_pointcloud_distance_distribution(self, pcd: PointCloudData, fov_borders: FoV) \
    #         -> list[tuple[PointCloudData, FoV], ...]:
    #     """
    #
    #     Args:
    #         pcd:
    #         fov_borders:
    #
    #     Returns:
    #
    #     """
    #     # print(fov_borders)
    #     # print(pcd)
    #     if pcd.nbPoints <= self.minimum_nb_points:
    #         return [(pcd, fov_borders,)]
    #     distances_percentiles = np.percentile(pcd.spherical_coordinates[:, 0], (90, 10))
    #     fov_optimal = self._calculate_optimal_FoV_from_distance(distances_percentiles[0])
    #
    #     if fov_borders.extent("gon")[0] < 4 * fov_optimal[0] or \
    #             fov_borders.extent("gon")[1] < 4 * fov_optimal[1] or \
    #             np.divide(*distances_percentiles) < self.percentile_ratio:
    #         tiles = self.tile(pcd, fov_borders, fov_optimal)  # TODO: Check if angular resolution necessary
    #         # return tuple([(tile[0], angular_resolution, tile[1]) for tile in tiles])
    #         return tiles
    #     # fov_borders = np.array(fov_borders)
    #     # fov_quadrants = [(fov_borders[0], fov_borders[1], fov_borders[[0, 2]].mean(), fov_borders[[1, 3]].mean()),
    #     #                  (fov_borders[[0, 2]].mean(), fov_borders[1], fov_borders[2], fov_borders[[1, 3]].mean()),
    #     #                  (fov_borders[0], fov_borders[[1, 3]].mean(), fov_borders[[0, 2]].mean(), fov_borders[3]),
    #     #                  (fov_borders[[0, 2]].mean(), fov_borders[[1, 3]].mean(), fov_borders[2], fov_borders[3])]
    #
    #     fov_quadrants = fov_borders.quadrants()
    #
    #     splits = []
    #     for fq in fov_quadrants:
    #         pcd_extract = pcd.extract_angles(**fq.as_dict())
    #         if pcd_extract.nbPoints:
    #             splits.append((pcd_extract, fq))
    #     # splits.append((pcd.extract_angles(**fov_quadrants[0].as_dict()), fov_quadrants[0]))
    #     # splits.append((pcd.extract_angles(**fov_quadrants[1].as_dict()), fov_quadrants[1]))
    #     # splits.append((pcd.extract_angles(**fov_quadrants[2].as_dict()), fov_quadrants[2]))
    #     # splits.append((pcd, fov_quadrants[3]))
    #
    #     pcd_fov_splits = Parallel(n_jobs=-1, prefer="processes", verbose=50, timeout=10 * 60)(delayed(
    #         self.split_pointcloud_distance_distribution)(*pcd_split) for pcd_split in splits)
    #
    #     # pcd_fov_splits = [self.split_pointcloud_distance_distribution(*pcd_split) for pcd_split in splits]
    #
    #     # pcd_fov_flattened = []
    #     # for pcd_fov in pcd_fov_splits:
    #     #     if pcd_fov is not None:
    #     #         pcd_fov_flattened.extend(pcd_fov)
    #     pcd_fov_flattened = list(chain.from_iterable(pcd_fov_splits))
    #     return pcd_fov_flattened

    # def _calculate_optimal_FoV_from_distance(self, distance: float):
    #     """ Calculate optimal FoV and angular resolution based on distance.
    #
    #     This function calculates the angular resolution between pixel to achieve the point spacing defined in
    #     `self.point_distance_pixel` (with the lower limit set by `self.minimum_angular_resolution_gon`). Based on the
    #     calculated angular resolution and the defined image size in pixels, the FoV is calculated.
    #
    #     Args:
    #         distance (float): Distance [m] to the majority of pixels
    #
    #     Returns:
    #         tuple[float, float]: FoV angles [gon] width and height
    #     """
    #     angular_resolution = max(2 * math.asin((self.ground_sampling_distance / 2) / distance) * 200 / math.pi,
    #                              self.minimum_angular_resolution_gon)
    #     # angular_resolution_rounded = np.floor(angular_resolution * 1000) / 1000   # round to 1e-3
    #     FoV = tuple([angular_resolution * pixel_count for pixel_count in self.image_resolution])
    #
    #     return FoV

    # def tile(self, pcd: pch.geometry.PointCloudData, fov: FoV,
    #          fov_per_image: tuple[float, float]) -> list[tuple[pch.geometry.PointCloudData, FoV]]:
    #     """Tile pcd into equally sized tiles along FoV.
    #
    #     TODO: Check if tiling can be parallelized; Alternatively check if too many tiles and return to splitting
    #
    #
    #     Args:
    #         fov:
    #         fov_per_image:
    #
    #     Returns:
    #
    #     """
    #
    #     sampling_angle_gon = \
    #         max(min((fov.extent("gon")[0] / np.ceil(fov.extent("gon")[0] / fov_per_image[0])) /
    #                 self.image_resolution[0],
    #                 (fov.extent("gon")[1] / np.ceil(fov.extent("gon")[1] / fov_per_image[1])) /
    #                 self.image_resolution[1]), self.minimum_angular_resolution_gon)
    #
    #     new_fov_per_image = tuple(sampling_angle_gon * np.array(self.image_resolution))
    #
    #     horizontal_fov_edges = np.arange(start=fov.horizontal_min_gon,
    #                                      stop=fov.horizontal_max_gon + new_fov_per_image[0],
    #                                      step=new_fov_per_image[0])
    #     elevation_fov_edges = np.arange(start=fov.elevation_min_gon,
    #                                     stop=fov.elevation_max_gon + new_fov_per_image[1],
    #                                     step=new_fov_per_image[1])
    #
    #     fov_tiles = []
    #     # nbTiles = (horizontal_fov_edges.shape[0] - 1) * (elevation_fov_edges.shape[0] - 1)
    #     # print(f"Number of tiles: {nbTiles:d}")
    #     for i in range(horizontal_fov_edges.shape[0] - 1):
    #         for j in range(elevation_fov_edges.shape[0] - 1):
    #             fov_tiles.append(FoV(horizontal_fov_edges[i], elevation_fov_edges[j], horizontal_fov_edges[i + 1],
    #                                  elevation_fov_edges[j + 1], unit="gon"))
    #             # print(f"{i}, {j}")
    #     pcd_fov_tiles = [(pcd.extract_angles(**fov_tile.as_dict("rad")), fov_tile) for fov_tile in fov_tiles]
    #     return pcd_fov_tiles
    #
    # def split_on_fovs(self, pcd: pch.geometry.PointCloudData, fovs: Iterable[FoV]):
    #     pcd_fov = [(pcd.extract_angles(**fov.as_dict("rad")), fov) for fov in fovs]
    #     # pcd_fov = []
    #     # for i, fov in enumerate(fovs):
    #     #     pcd_fov.append((pcd.extract_angles(**fov.as_dict("rad")), fov, ))
    #     #     print(i)
    #     return pcd_fov


