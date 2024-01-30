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
# from pc2img.image_processing import ImageGenerator
# from pc2img import image_processing
# from pc2img.image_processing import knn_griddata as knn_griddata
# from pc2img.image_processing import barycentric_interpolation

EPS32 = np.finfo(np.float32).eps


@dataclass(init=False, frozen=True)
class FoV:
    # TODO: Rework quadrants as special case of generalized split on shape tuple.
    horizontal_min: float
    elevation_min: float
    horizontal_max: float
    elevation_max: float
    _defined_units: tuple[str, ...] = ("rad", "gon", "deg")

    def __init__(self, *, horizontal_min: float, elevation_min: float, horizontal_max: float, elevation_max: float,
                 unit: str = "rad"):
        assert unit in self._defined_units
        assert horizontal_max > horizontal_min  # TODO: Rethink in the context describing shortest path
        assert elevation_max > elevation_min

        match unit:
            case "gon":
                horizontal_min = horizontal_min / 200 * math.pi
                horizontal_max = horizontal_max / 200 * math.pi
                elevation_min = elevation_min / 200 * math.pi
                elevation_max = elevation_max / 200 * math.pi
            case "deg":
                horizontal_min = horizontal_min / 180 * math.pi
                horizontal_max = horizontal_max / 180 * math.pi
                elevation_min = elevation_min / 180 * math.pi
                elevation_max = elevation_max / 180 * math.pi
        object.__setattr__(self, "horizontal_min", horizontal_min)
        object.__setattr__(self, "horizontal_max", horizontal_max)
        object.__setattr__(self, "elevation_min", elevation_min)
        object.__setattr__(self, "elevation_max", elevation_max)

    @property
    def horizontal_min_gon(self):
        return self.horizontal_min * 200 / math.pi

    @property
    def horizontal_max_gon(self):
        return self.horizontal_max * 200 / math.pi

    @property
    def elevation_min_gon(self):
        return self.elevation_min * 200 / math.pi

    @property
    def elevation_max_gon(self):
        return self.elevation_max * 200 / math.pi

    @property
    def horizontal_min_deg(self):
        return self.horizontal_min * 180 / math.pi

    @property
    def horizontal_max_deg(self):
        return self.horizontal_max * 180 / math.pi

    @property
    def elevation_min_deg(self):
        return self.elevation_min * 180 / math.pi

    @property
    def elevation_max_deg(self):
        return self.elevation_max * 180 / math.pi

    def as_tuple(self, unit: str = "rad"):
        assert unit in self._defined_units
        match unit:
            case "rad":
                return self.horizontal_min, self.elevation_min, self.horizontal_max, self.elevation_max
            case "gon":
                return self.horizontal_min_gon, self.elevation_min_gon, self.horizontal_max_gon, self.elevation_max_gon
            case "deg":
                return self.horizontal_min_deg, self.elevation_min_deg, self.horizontal_max_deg, self.elevation_max_deg

    def as_dict(self, unit: str = "rad"):
        assert unit in self._defined_units
        match unit:
            case "rad":
                return {"horizontal_min": self.horizontal_min,
                        "elevation_min": self.elevation_min,
                        "horizontal_max": self.horizontal_max,
                        "elevation_max": self.elevation_max}
            case "gon":
                return {"horizontal_min": self.horizontal_min_gon,
                        "elevation_min": self.elevation_min_gon,
                        "horizontal_max": self.horizontal_max_gon,
                        "elevation_max": self.elevation_max_gon}
            case "rad":
                return {"horizontal_min": self.horizontal_min_deg,
                        "elevation_min": self.elevation_min_deg,
                        "horizontal_max": self.horizontal_max_deg,
                        "elevation_max": self.elevation_max_deg}

    def width(self, unit: str = "rad"):
        assert unit in self._defined_units
        values = self.as_dict(unit)
        return values["horizontal_max"] - values["horizontal_min"]

    def height(self, unit: str = "rad"):
        assert unit in self._defined_units
        values = self.as_dict(unit)
        return values["elevation_max"] - values["elevation_min"]

    def extent(self, unit: str = "rad"):
        assert unit in self._defined_units
        values = self.as_tuple(unit)

        return values[2] - values[0], values[3] - values[1]

    def union(self, fov2: FoV):
        return FoV(horizontal_min=min(self.horizontal_min, fov2.horizontal_min),
                   elevation_min=min(self.elevation_min, fov2.elevation_min),
                   horizontal_max=max(self.horizontal_max, fov2.horizontal_max),
                   elevation_max=max(self.elevation_max, fov2.elevation_max))

    def ratio(self):
        return self.extent()[0] / self.extent()[1]

    def __repr__(self):
        return f"({self.horizontal_min_gon:0.4f}, {self.elevation_min_gon:0.4f}, " \
               f"{self.horizontal_max_gon:0.4f}, {self.elevation_max_gon:0.4f})"

    def extend_to_ratio(self, ratio: float):
        if self.ratio() > ratio:
            target_vertical_extent = self.extent()[0] / ratio
            new_fov = FoV(horizontal_min=self.horizontal_min,
                          elevation_min=self.elevation_min,
                          horizontal_max=self.horizontal_max,
                          elevation_max=self.elevation_min + target_vertical_extent)
        elif self.ratio() < ratio:
            target_horizontal_extent = self.extent()[1] * ratio
            new_fov = FoV(horizontal_min=self.horizontal_min,
                          elevation_min=self.elevation_min,
                          horizontal_max=self.horizontal_min + target_horizontal_extent,
                          elevation_max=self.elevation_max)
        else:
            new_fov = self

        return new_fov

    def split(self, shape: tuple[int, int]) -> list[FoV]:
        assert shape[0] > 0 and shape[1] > 0
        if shape[0] == shape[1] == 1:
            return [self]

        horizontal_borders = np.linspace(start=self.horizontal_min,
                                         stop=self.horizontal_max,
                                         num=shape[0] + 1,
                                         endpoint=True,
                                         retstep=False)
        elevation_borders = np.linspace(start=self.elevation_min,
                                        stop=self.elevation_max,
                                        num=shape[1] + 1,
                                        endpoint=True,
                                        retstep=False)

        fov_splits = [FoV(horizontal_min=hor_min,
                          elevation_min=elev_min,
                          horizontal_max=hor_max,
                          elevation_max=elev_max)
                      for hor_min, hor_max in zip(horizontal_borders[:-1], horizontal_borders[1:])
                      for elev_min, elev_max in zip(elevation_borders[:-1], elevation_borders[1:])]

        return fov_splits

    def equal_tiles(self, target_extent: tuple[tuple[float, float], str], ) -> list[FoV]:
        assert target_extent[0][0] > 0 and target_extent[0][1]
        # assert any(target < own for target, own in zip(target_extent[0], self.extent(target_extent[1])))

        return self.split(shape=(np.ceil(self.extent(target_extent[1])[0] / target_extent[0][0]).astype(int),
                                 np.ceil(self.extent(target_extent[1])[1] / target_extent[0][1]).astype(int)))

    def tile(self, target_extent: tuple[tuple[float, float], str], ) -> list[list[FoV], ...]:
        #TODO: Update to take a FoV
        assert target_extent[0][0] > 0 and target_extent[0][1] > 0
        # assert all(target < own for target, own in zip(target_extent[0], self.extent(target_extent[1])))

        assert target_extent[1] == "rad"

        horizontal_steps = np.append(np.arange(self.horizontal_min, self.horizontal_max, target_extent[0][0]),
                                     self.horizontal_max)

        elevation_steps = np.append(np.arange(self.elevation_min, self.elevation_max, target_extent[0][1]),
                                    self.elevation_max)

        horizontal_bins = list(zip(horizontal_steps[:-1], horizontal_steps[1:]))
        elevation_bins = list(zip(elevation_steps[:-1], elevation_steps[1:]))

        tiles = []
        for hor_bin in horizontal_bins:
            horizontal_tiles = []
            for elev_bin in elevation_bins:
                horizontal_tiles.append(FoV(horizontal_min=hor_bin[0],
                                            elevation_min=elev_bin[0],
                                            horizontal_max=hor_bin[1],
                                            elevation_max=elev_bin[1]))
            tiles.append(horizontal_tiles)
        return tiles

    def quadrants(self):
        # Keep for legacy
        return tuple(self.split(shape=(2, 2)))


@dataclass(init=True, frozen=True)
class FoVTree:
    identifier: str
    node: FoV
    children: dict[str, FoVTree] = field(default_factory=dict)

    @staticmethod
    def add_identifier(fovs: list[FoV], shape: tuple[int, int]):
        identifier_length = np.ceil(math.log(shape[0] * shape[1], 16)).astype(int)
        return tuple([(((identifier_length - len(hex_str := f"{i:x}")) * "0" + hex_str), fov)
                      for i, fov in enumerate(fovs)])

    def depth(self) -> int:
        if not self.children:
            return 1
        return max([c.depth() for c in self.children.values()]) + 1

    @classmethod
    def build_by_splitting(cls, fov: FoV, target_ratio: float, target_fov_extent: tuple[tuple[float, float], str],
                           max_denominator: int, identifier: str = "") -> FoVTree:
        # TODO: Rework stopping criteria
        assert target_fov_extent[1] in ("rad", "gon", "deg")

        target_extent = target_fov_extent[0]
        angle_unit = target_fov_extent[1]

        shape = cls.calculate_optimal_shape(fov, target_ratio, target_fov_extent, max_denominator)

        if (fov.extent(unit=angle_unit)[0] < target_extent[0] * shape[0] or
                fov.extent(unit=angle_unit)[1] < target_extent[1] * shape[1]):
            fov_tiles = fov.equal_tiles(target_fov_extent)
            shape = (len(fov_tiles), 1)
            fov_children = {child_identifier: cls(identifier + child_identifier, child, {})
                            for child_identifier, child in cls.add_identifier(fov_tiles, shape)}
        else:
            fov_splits = fov.split(shape)
            fov_children = {child_identifier: cls.build_by_splitting(child, target_ratio, target_fov_extent,
                                                                     max_denominator * 2, identifier + child_identifier)
                            for child_identifier, child in cls.add_identifier(fov_splits, shape)}

        return cls(identifier, fov, fov_children)

    @classmethod
    def build_by_tiling(cls, fov: FoV, target_fov_extent: tuple[tuple[float, float], str],
                        identifier: str = "") -> FoVTree:
        fov_tiles = fov.equal_tiles(target_fov_extent)

        identifier_length = np.ceil(math.log(len(fov_tiles), 16)).astype(int)
        fov_with_identifier = tuple([(((identifier_length - len(hex_str := f"{i:x}")) * "0" + hex_str), fov)
                                     for i, fov in enumerate(fov_tiles)])

        fov_children = {child_identifier: cls(identifier + child_identifier, child, {})
                        for child_identifier, child in fov_with_identifier}

        return cls(identifier, fov, fov_children)

    # @classmethod
    # def build(cls, fov: FoV, target_fov_extent: FoV):
    #     tiles = fov.tile((target_fov_extent.extent("rad"), "rad"))
    #     pass

    @classmethod
    def build_from_tiles(cls, tiles: list[list[FoV]], min_children: int = 4, identifier: str = ""):
        assert min_children > 1
        if not tiles or not tiles[0]:
            return None

        fov = FoV(horizontal_min=tiles[0][0].horizontal_min,
                  elevation_min=tiles[0][0].elevation_min,
                  horizontal_max=tiles[-1][-1].horizontal_max,
                  elevation_max=tiles[-1][-1].elevation_max)

        if len(tiles) * len(tiles[0]) <= min_children:
            flat_tiles = [tile for row in tiles for tile in row]
            fov_children = {str(i): cls(identifier+str(i), tile, {})
                            for i, tile in enumerate(flat_tiles)}
            return cls(identifier, fov, fov_children) #TODO: BUG! Rebuild identifier function to work 2D

        q0 = tiles[:len(tiles) // 2]
        q1 = tiles[len(tiles) // 2:]
        q00 = [row[:len(row) // 2] for row in q0]
        q01 = [row[len(row) // 2:] for row in q0]
        q10 = [row[:len(row) // 2] for row in q1]
        q11 = [row[len(row) // 2:] for row in q1]

        fov_children = {"0": cls.build_from_tiles(q00, min_children, identifier=(identifier + "0")),
                        "1": cls.build_from_tiles(q01, min_children, identifier=(identifier + "1")),
                        "2": cls.build_from_tiles(q10, min_children, identifier=(identifier + "2")),
                        "3": cls.build_from_tiles(q11, min_children, identifier=(identifier + "3")),
                        }

        fov_children = {k: v for k, v in fov_children.items() if v is not None}

        return cls(identifier, fov, fov_children)

    @staticmethod
    def quadrant_split(tiles: list[list[FoV]]):
        # q1 = tiles[:len(tiles) // 2]
        # q2 = tiles[len(tiles) // 2:]
        # q11 = [row[:len(row)//2] for row in q1]
        # q12 = [row[len(row)//2:] for row in q1]
        # q21 = [row[:len(row) // 2] for row in q2]
        # q22 = [row[len(row) // 2:] for row in q2]
        # quadrant_FoV = FoV(horizontal_min=q11[0][0].horizontal_min,
        #                    elevation_min=q11[0][0].elevation_min,
        #                    horizontal_max=q22[-1][-1].horizontal_max,
        #                    elevation_max=q22[-1][-1].elevation_max)

        FoVTree.quadrant_split(q11)
        FoVTree.quadrant_split(q12)
        FoVTree.quadrant_split(q21)
        FoVTree.quadrant_split(q22)

        pass

    def __getitem__(self, identifier: str):
        # TODO: extend to complete for full string
        child_identifier_length = np.ceil(math.log(len(self.children), 16)).astype(int)
        if len(identifier) > child_identifier_length:
            return self.children[identifier[:child_identifier_length]][identifier[child_identifier_length:]]

        return self.children[identifier]

    def is_leaf(self):
        return not self.children

    @staticmethod
    def calculate_optimal_shape(fov: FoV, target_ratio: float,
                                target_extent: tuple[tuple[float, float], str],
                                max_denominator: float) -> tuple[int, int]:

        shape = Fraction(fov.ratio() / target_ratio).limit_denominator(np.round(max_denominator).astype(int))
        shape = (shape.numerator, shape.denominator,)
        if shape[0] == shape[1] == 1:
            shape = (2, 2)

        return shape


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

    def generate_images(self, pcds_with_fov: list[tuple[str, FoV, pch.geometry.PointCloudData]], n_jobs: int = -1):
        Parallel(n_jobs=n_jobs, prefer="processes", verbose=20)(delayed(self.fov2images)
                                                                (*pcd) for pcd in pcds_with_fov)

    # def fov2images(self, identifier: str, fov: FoV, pcd: pch.geometry.PointCloudData, downsample_pcd: bool = False):
    #     # TODO: Rework: different options such as normalization etc; File name handling
    #
    #     if pcd.nbPoints < self.minimum_nb_points:
    #         return
    #
    #     if downsample_pcd and pcd.nbPoints/(self.image_resolution[0] * self.image_resolution[1]) > 10:
    #         pcd.random_subsample(int(self.image_resolution[0] * self.image_resolution[1] * 4))
    #
    #     raw_file = (self.image_folder / "00_raw" / identifier).with_suffix(".png")
    #     intensity_file = (self.image_folder / "01_intensity" / identifier).with_suffix(".png")
    #     scaled_file = (self.image_folder / "02_intensity_scaled" / identifier).with_suffix(".png")
    #     range_file = (self.image_folder / "03_range" / identifier).with_suffix(".tif")
    #     meta_file = (self.image_folder / "99_meta" / identifier).with_suffix(".json")
    #
    #     raw_file.parent.mkdir(parents=True, exist_ok=True)
    #     intensity_file.parent.mkdir(parents=True, exist_ok=True)
    #     scaled_file.parent.mkdir(parents=True, exist_ok=True)
    #     range_file.parent.mkdir(parents=True, exist_ok=True)
    #     meta_file.parent.mkdir(parents=True, exist_ok=True)
    #
    #     # Calculate pixels that
    #     extended_fov = fov.extend_to_ratio(self.aspect_ratio)
    #
    #     column_index = np.arange(start=0, stop=self.image_resolution[0], dtype=np.float32)
    #     row_index = np.arange(start=0, stop=self.image_resolution[1], dtype=np.float32)
    #
    #     ii, jj = np.meshgrid(row_index, column_index)
    #
    #     elevation_pixel = (self.image_resolution[1] * (pcd.spherical_coordinates[:, 1] - extended_fov.elevation_min)
    #                        / extended_fov.extent("rad")[1]).astype(np.float32)
    #     horizontal_pixel = (self.image_resolution[0] * (pcd.spherical_coordinates[:, 2] - extended_fov.horizontal_min)
    #                         / extended_fov.extent("rad")[0]).astype(np.float32)
    #
    #     # horizontal_bin_edges = np.linspace(extended_fov.horizontal_min,
    #     #                                    extended_fov.horizontal_max,
    #     #                                    num=self.image_resolution[0],
    #     #                                    endpoint=True)
    #     #
    #     # elevation_bin_edges = np.linspace(extended_fov.elevation_min,
    #     #                                   extended_fov.elevation_max,
    #     #                                   num=self.image_resolution[1],
    #     #                                   endpoint=True)
    #     #
    #     # horizontal_grid, elevation_grid = np.meshgrid(horizontal_bin_edges, elevation_bin_edges)
    #
    #     try:
    #         time_start = timer()
    #         knn_data = knn_griddata(points=np.stack((elevation_pixel, horizontal_pixel), axis=1),
    #                             values=(pcd.scalar_fields["scalar_Intensity"], pcd.spherical_coordinates[:, 0]),
    #                             xi=(ii, jj), method='barycentric',
    #                             filter_distance=5.0)
    #         time_mid = timer()
    #         # scipy_intensity = scipy_gd(points=np.stack((elevation_pixel, horizontal_pixel), axis=1),
    #         #                            values=pcd.scalar_fields["scalar_Intensity"],
    #         #                            xi=(ii, jj), method='linear', fill_value=1.0)
    #         delaunay_data = barycentric_interpolation(points=np.stack((elevation_pixel, horizontal_pixel), axis=-1),
    #                                                values=(pcd.scalar_fields["scalar_Intensity"],
    #                                                        pcd.spherical_coordinates[:, 0]),
    #                                                xi=(ii, jj), filter_distance=5.0)
    #         time_end = timer()
    #
    #         print(f"Timings: {time_mid - time_start:.2f} for knn; {time_end - time_mid:.2f} for delaunay")
    #
    #         elevation_pixel_int = np.floor(elevation_pixel-EPS32).astype(int)
    #         horizontal_pixel_int = np.floor(horizontal_pixel-EPS32).astype(int)
    #
    #         raw_image = np.ones(self.image_resolution[::-1])
    #
    #         elevation_pixel_int[elevation_pixel_int == raw_image.shape[0]] = raw_image.shape[0] - 1
    #         horizontal_pixel_int[horizontal_pixel_int == raw_image.shape[1]] = raw_image.shape[1] - 1
    #
    #         raw_image[elevation_pixel_int, horizontal_pixel_int] = pcd.scalar_fields["scalar_Intensity"]
    #
    #         intensity_data_non = knn_data[0]
    #         intensity_data_non[np.isnan(intensity_data_non)] = 1.0
    #
    #         delaunay_intensity = delaunay_data[0]
    #         delaunay_intensity[np.isnan(delaunay_data[0])] = 1.0
    #
    #
    #         iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_knn"),
    #                     ((2 ** 8 - 1) * intensity_data_non.T).astype(np.uint8))
    #
    #         iio.imwrite(intensity_file.with_stem(intensity_file.stem + "_delaunay"),
    #                     ((2 ** 8 - 1) * delaunay_intensity.T).astype(np.uint8))
    #
    #         intensity_data, range_data = [image_processing.normalization(d) for d in knn_data]
    #
    #
    #         scipy_intensity_normalized, scipy_range = [image_processing.normalization(d) for d in delaunay_data]
    #
    #         iio.imwrite(raw_file, ((2 ** 8 - 1) * raw_image).astype(np.uint8))
    #
    #
    #         iio.imwrite(scaled_file.with_stem(scaled_file.stem + "_knn"),
    #                     ((2 ** 8 - 1) * scipy_intensity_normalized.T).astype(np.uint8))
    #
    #         iio.imwrite(scaled_file.with_stem(scaled_file.stem + "_delaunay"),
    #                     ((2 ** 8 - 1) * intensity_data.T).astype(np.uint8))
    #
    #         tifffile.imwrite(range_file.with_stem(range_file.stem + "_delaunay"),
    #                          ((2 ** 32 - 1) * scipy_range.T).astype(np.uint32), photometric='minisblack')
    #
    #         tifffile.imwrite(range_file.with_stem(range_file.stem + "_knn"),
    #                          ((2 ** 32 - 1) * range_data.T).astype(np.uint32), photometric='minisblack')
    #
    #
    #
    #         # iio.imwrite(intensity_file, ((2 ** 8 - 1) * intensity_data).astype(np.uint8))
    #         #
    #         # iio.imwrite(scaled_file, ((2 ** 32 - 1) * intensity_data).astype(np.uint32),
    #         #             photometric='minisblack')
    #         #
    #         # iio.imwrite(range_file, ((2 ** 32 - 1) * range_data).astype(np.uint32),
    #         #             photometric='minisblack')
    #
    #         # iio.imwrite(intensity_file, (255.0 * intensity_data).astype(np.uint8))
    #         # iio.imwrite(scaled_file, (255.0 * intensity_data_scaled).astype(np.uint8))
    #         # iio.imwrite(range_file, (255.0 * range_data_scaled).astype(np.uint8))
    #
    #         image_info = {
    #             'fov_data': fov.extent(unit='gon'),
    #             'image_resolution': self.image_resolution,
    #             'image_fov': extended_fov.as_dict('gon'),
    #             # 'filter_mask_size': filter_ds_ratio,
    #             'range_info': {'min': pcd.spherical_coordinates[:, 0].min(),
    #                            'max': pcd.spherical_coordinates[:, 0].max()},
    #         }
    #
    #         with open(meta_file, 'w') as f:
    #             json.dump(image_info, f, indent=2)
    #
    #     except:
    #         print(pcd.nbPoints)
    #         raise
    #     else:
    #         pass

    # def fov2images(self, identifier: str, fov: FoV, pcd: pch.geometry.PointCloudData):
    #     # TODO: Rework: different options such as normalization etc; File name handling
    #
    #     if pcd.nbPoints < self.minimum_nb_points:
    #         return
    #
    #     intensity_file = (self.image_folder / "01_intensity" / identifier).with_suffix(".png")
    #     scaled_file = (self.image_folder / "02_intensity_scaled" / identifier).with_suffix(".tif")
    #     range_file = (self.image_folder / "03_range" / identifier).with_suffix(".tif")
    #     meta_file = (self.image_folder / "00_meta" / identifier).with_suffix(".json")
    #
    #     intensity_file.parent.mkdir(parents=True, exist_ok=True)
    #     scaled_file.parent.mkdir(parents=True, exist_ok=True)
    #     range_file.parent.mkdir(parents=True, exist_ok=True)
    #     meta_file.parent.mkdir(parents=True, exist_ok=True)
    #
    #     # Calculate pixels that
    #     extended_fov = fov.extend_to_ratio(self.aspect_ratio)
    #
    #     horizontal_bin_edges = np.linspace(extended_fov.horizontal_min,
    #                                        extended_fov.horizontal_max,
    #                                        num=self.image_resolution[0],
    #                                        endpoint=True)
    #
    #     elevation_bin_edges = np.linspace(extended_fov.elevation_min,
    #                                       extended_fov.elevation_max,
    #                                       num=self.image_resolution[1],
    #                                       endpoint=True)
    #
    #     horizontal_grid, elevation_grid = np.meshgrid(horizontal_bin_edges, elevation_bin_edges)
    #
    #     try:
    #         data = griddata(points=pcd.spherical_coordinates[:, 1:],
    #                         values=(pcd.scalar_fields["scalar_Intensity"], pcd.spherical_coordinates[:, 0]),
    #                         xi=(elevation_grid, horizontal_grid), method='linear',
    #                         filter_distance=(elevation_grid[1, 0] - elevation_grid[0, 0]) * 25.0)
    #
    #         intensity_data, range_data = [image_processing.normalization(d) for d in data]
    #
    #         iio.imwrite(intensity_file, ((2**8 - 1) * intensity_data).astype(np.uint8))
    #
    #         iio.imwrite(scaled_file, ((2**32 - 1) * intensity_data).astype(np.uint32),
    #                     photometric='minisblack')
    #
    #         iio.imwrite(range_file, ((2**32 - 1) * range_data).astype(np.uint32),
    #                     photometric='minisblack')
    #
    #         # iio.imwrite(intensity_file, (255.0 * intensity_data).astype(np.uint8))
    #         # iio.imwrite(scaled_file, (255.0 * intensity_data_scaled).astype(np.uint8))
    #         # iio.imwrite(range_file, (255.0 * range_data_scaled).astype(np.uint8))
    #
    #         image_info = {'fov_data': fov.extent(unit='gon'),
    #                       'fov_borders_data': fov.as_dict(unit='gon'),
    #                       'image_resolution': self.image_resolution,
    #                       'image_fov': extended_fov.as_dict('gon'),
    #                       # 'filter_mask_size': filter_ds_ratio,
    #                       # 'range_info': {'min': min_range, 'max': max_range}
    #         }
    #
    #         with open(meta_file, 'w') as f:
    #             json.dump(image_info, f, indent=2)
    #
    #     except:
    #         print(pcd.nbPoints)
    #         raise
    #     else:
    #         pass

    # def fov2images(self, identifier: str, fov: FoV, pcd: pch.geometry.PointCloudData,
    #                filter_ds_ratio: int = 10):
    #     # TODO: Rework: different options such as normalization etc; File name handling
    #     if pcd.nbPoints < self.minimum_nb_points:
    #         return
    #
    #     # if isinstance(filter_downsample_ratios, int):
    #     #     filter_downsample_ratios = [filter_downsample_ratios]
    #
    #     # is_divisor = lambda x, y: x % y == 0
    #
    #     assert all(map(lambda x: x % filter_ds_ratio == 0, self.image_resolution))  # TODO: Replace with error
    #
    #     intensity_file = (self.image_folder / "01_intensity" / identifier).with_suffix(".png")
    #     scaled_file = (self.image_folder / "02_intensity_scaled" / identifier).with_suffix(".png")
    #     range_file = (self.image_folder / "03_range" / identifier).with_suffix(".png")
    #     meta_file = (self.image_folder / "00_meta" / identifier).with_suffix(".json")
    #
    #     intensity_file.parent.mkdir(parents=True, exist_ok=True)
    #     scaled_file.parent.mkdir(parents=True, exist_ok=True)
    #     range_file.parent.mkdir(parents=True, exist_ok=True)
    #     meta_file.parent.mkdir(parents=True, exist_ok=True)
    #
    #     # Calculate pixels that
    #     extended_fov = fov.extend_to_ratio(self.aspect_ratio)
    #
    #     horizontal_bin_edges = np.linspace(extended_fov.horizontal_min,
    #                                        extended_fov.horizontal_max,
    #                                        num=self.image_resolution[0],
    #                                        endpoint=True)
    #
    #     elevation_bin_edges = np.linspace(extended_fov.elevation_min,
    #                                       extended_fov.elevation_max,
    #                                       num=self.image_resolution[1],
    #                                       endpoint=True)
    #
    #     image_resolution_ds = tuple(map(lambda x: int(x / filter_ds_ratio), self.image_resolution))
    #
    #     horizontal_grid, elevation_grid = np.meshgrid(horizontal_bin_edges, elevation_bin_edges)
    #
    #     # TODO: Rethink the indexing
    #
    #     horizontal_index_ds = np.floor((pcd.spherical_coordinates[:, 2] - extended_fov.horizontal_min) /
    #                                    extended_fov.extent()[0] * image_resolution_ds[0]).astype(int)
    #     elevation_index_ds = np.floor((pcd.spherical_coordinates[:, 1] - extended_fov.elevation_min) /
    #                                   extended_fov.extent()[1] * image_resolution_ds[1]).astype(int)
    #
    #     horizontal_index_ds[horizontal_index_ds == image_resolution_ds[0]] = image_resolution_ds[0] - 1
    #
    #     elevation_index_ds[elevation_index_ds == image_resolution_ds[1]] = image_resolution_ds[1] - 1
    #
    #     #ToDo: Check if image indexing consistent (here (elev,hor)!)
    #     filter_mask_scaled = np.empty(image_resolution_ds[::-1])
    #     filter_mask_scaled[:] = np.nan
    #     filter_mask_scaled[elevation_index_ds, horizontal_index_ds] = 1
    #
    #     filter_mask = np.kron(filter_mask_scaled, np.ones((filter_ds_ratio, filter_ds_ratio)))
    #
    #     # if pcd.nbPoints / np.nansum(filter_mask) > 4:  # TODO: Make Ratio a parameter
    #     #     pcd.random_subsample(4 * np.nansum(filter_mask).astype(int), in_place=True)
    #
    #     try:
    #         max_range = pcd.spherical_coordinates[:, 0].max()
    #         min_range = pcd.spherical_coordinates[:, 0].min()
    #         intensity_data = griddata(pcd.spherical_coordinates[:, 1:], pcd.scalar_fields["scalar_Intensity"],
    #                                   (elevation_grid, horizontal_grid), method='linear',
    #                                   filter_distance=(elevation_grid[1, 0] - elevation_grid[0, 0])*5.0,
    #                                   fill_value=1.0)
    #
    #         range_data_scaled = griddata(pcd.spherical_coordinates[:, 1:],
    #                                      (pcd.spherical_coordinates[:, 0] - min_range) / (max_range - min_range),
    #                                      (elevation_grid, horizontal_grid), method='linear', fill_value=1.0)
    #
    #         # intensity_data = filter_mask * intensity_data
    #         # range_data_scaled = filter_mask * range_data_scaled
    #         #
    #         # intensity_data_scaled = ((intensity_data - np.nanmin(intensity_data)) /
    #         #                          (np.nanmax(intensity_data) - np.nanmin(intensity_data)))
    #
    #         #Intensity scaling
    #         flattend_intensity_data = np.ndarray.flatten(intensity_data)
    #         intensity_percentiles = np.nanpercentile(flattend_intensity_data[flattend_intensity_data != 1.0], [1, 99])
    #         intensity_data_scaled = (intensity_data - intensity_percentiles[0])/(intensity_percentiles[1]
    #                                                                              - intensity_percentiles[0])
    #         intensity_data_scaled[intensity_data_scaled > 1] = 1.0
    #         intensity_data_scaled[intensity_data_scaled < 0] = 0.0
    #
    #         np.nan_to_num(intensity_data, copy=False, nan=1.0)
    #         np.nan_to_num(intensity_data_scaled, copy=False, nan=1.0)
    #         np.nan_to_num(range_data_scaled, copy=False, nan=1.0)
    #
    #         iio.imwrite(intensity_file, (255.0 * intensity_data).astype(np.uint8))
    #         iio.imwrite(scaled_file, (255.0 * intensity_data_scaled).astype(np.uint8))
    #         iio.imwrite(range_file, (255.0 * range_data_scaled).astype(np.uint8))
    #
    #         image_info = {'fov_data': fov.extent(unit='gon'),
    #                       'fov_borders_data': fov.as_dict(unit='gon'),
    #                       'image_resolution': self.image_resolution,
    #                       'image_fov': extended_fov.as_dict('gon'),
    #                       'filter_mask_size': filter_ds_ratio,
    #                       'range_info': {'min': min_range, 'max': max_range}}
    #
    #         with open(meta_file, 'w') as f:
    #             json.dump(image_info, f, indent=2)
    #
    #     except:
    #         print(pcd.nbPoints)
    #         raise
    #     else:
    #         pass
