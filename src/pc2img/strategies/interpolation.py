from abc import ABC, abstractmethod
from typing import Optional, Literal, Any, Generator, Callable, Self
from pathlib import Path
from dataclasses import dataclass
import logging

import numpy as np
from numpy.typing import DTypeLike, NDArray
from numpy.lib.mixins import NDArrayOperatorsMixin
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator
from scipy.spatial import Delaunay

from GSEGUtils.config import get_defaults, CacheDefaults
from GSEGUtils.lazy_disk_cache import DiskBackedNDArray

from .registry import INTERPOLATIONS, _StrategyClass, StrategyFactory

logger = logging.getLogger(__name__)

DEFAULT: CacheDefaults = get_defaults()

InterpolationName = Literal["linear", "nearest_neighbor", "cubic", "delaunay"]

class InterpolationStrategy(ABC):

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Self], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, _) -> Self:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return INTERPOLATIONS.create(value)
        if (
                isinstance(value, tuple)
                and len(value) == 2
                and isinstance(value[0], str)
                and isinstance(value[1], dict)
        ):
            key, kwargs = value
            return INTERPOLATIONS.create(key, **kwargs)

        raise TypeError(f"Cannot interpret {value!r} as a {cls.__name__} strategy")

    @abstractmethod
    def interpolate(
        self,
        values: NDArray,
        points2d: NDArray,
        grid_x: NDArray,
        grid_y: NDArray
    ) -> NDArray:
        """Interpolate point-values onto a grid."""

class InterpolationStrategyClass(_StrategyClass[InterpolationStrategy]):
    registry = INTERPOLATIONS
    base_type = InterpolationStrategy

@INTERPOLATIONS.register("linear")
class LinearInterpolation(InterpolationStrategy):
    def interpolate(self, values, points2d, grid_x, grid_y):
        interp = LinearNDInterpolator(points2d, values)
        return interp(grid_x, grid_y)

@INTERPOLATIONS.register("nearest_neighbor")
class NearestNeighborInterpolation(InterpolationStrategy):
    def interpolate(self, values, points2d, grid_x, grid_y):
        interp = NearestNDInterpolator(points2d, values)
        return interp(grid_x, grid_y)

@INTERPOLATIONS.register("cubic")
class CubicInterpolation(InterpolationStrategy):
    def interpolate(self, values, points2d, grid_x, grid_y):
        interp = CloughTocher2DInterpolator(points2d, values)
        return interp(grid_x, grid_y)



@INTERPOLATIONS.register("delaunay")
class DelaunayInterpolation(InterpolationStrategy):

    @dataclass(frozen=True)
    class TriangulationData:
        bary: DiskBackedNDArray  # shape=(N, 3): Per-query point weights of bary centric interpolation
        verts: DiskBackedNDArray  # shape=(N, 3): Per-query point indices of the three vertices
        simplices: DiskBackedNDArray  # shape=(N,): Per-query point indices of the delaunay triangle
        triangles: DiskBackedNDArray  # shape=(M, 3): Per-triangle indices of the vertices


    def __init__(self):
        self._triangulation_precalc: dict[int, DelaunayInterpolation.TriangulationData] = {}

    @staticmethod
    def _hash_settings(points2d: NDArray, grid_x: NDArray, grid_y:NDArray) -> int:
        return hash((hash(points2d.tobytes()), hash(grid_x.tobytes()), hash(grid_y.tobytes())))


    def interpolate(
            self,
            values: NDArray,
            points2d: NDArray,
            grid_x: NDArray,
            grid_y: NDArray,
            fill_value: float = np.nan
    ) -> NDArray:

        hash_id = self._hash_settings(points2d, grid_x, grid_y)

        logger.debug(f"Starting interpolation with hash {hash_id}")
        if hash_id not in self._triangulation_precalc:
            self._precalc_traingulation(points2d, grid_x, grid_y, hash_id)

        triangulation_data = self._triangulation_precalc[hash_id]

        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T

        simplices = np.asarray(triangulation_data.simplices)
        verts = np.asarray(triangulation_data.verts)
        bary = np.asarray(triangulation_data.bary)
        triangles = np.asarray(triangulation_data.triangles)

        nQ = grid.shape[0]
        result = np.full(nQ, fill_value, dtype=float)
        mask = (simplices >= 0)

        # area_thresh = 6
        # max_edge_thresh = 10

        # if area_thresh is not None or max_edge_thresh is not None:
        # Compute triangle metrics once
        tri_vertices = points2d[triangles]  # shape (M, 3, 2)

        def compute_metrics(tri_pts):
            a = tri_pts[:, 1] - tri_pts[:, 0]
            b = tri_pts[:, 2] - tri_pts[:, 1]
            c = tri_pts[:, 0] - tri_pts[:, 2]
            edges = np.stack([np.linalg.norm(a, axis=1),
                              np.linalg.norm(b, axis=1),
                              np.linalg.norm(c, axis=1)], axis=1)
            s = edges.sum(axis=1) / 2
            area = np.sqrt(s * (s - edges[:, 0]) * (s - edges[:, 1]) * (s - edges[:, 2]))
            max_edge = edges.max(axis=1)
            return area, max_edge

        area, max_edge = compute_metrics(tri_vertices)

        # area_thresh = np.median(area) + 3 * np.median(np.abs(area-np.median(area)))
        # max_edge_thresh = np.median(max_edge) + 3 * np.median(np.abs(max_edge-np.median(max_edge)))
        area_thresh = np.median(area)*3
        max_edge_thresh = np.median(max_edge)*3

        # Find bad triangles
        tri_is_good = np.ones_like(area, dtype=bool)
        if area_thresh is not None:
            tri_is_good &= area < area_thresh
        if max_edge_thresh is not None:
            tri_is_good &= max_edge < max_edge_thresh

        # Mask out query points whose triangle is bad
        mask &= tri_is_good[simplices]

        logger.debug(f"Valid query point percentage: {mask.sum() / len(mask):.1%}")



        # only compute where inside hull
        result[mask] = np.einsum(
            'qi,qi->q',
            values[verts[mask]],  # pick only valid rows
            bary[mask]
        )
        return result.reshape(grid_x.shape)


    def _precalc_traingulation(
            self,
            points2d: NDArray,
            grid_x: NDArray,
            grid_y: NDArray,
            hash_id: int
    ) -> None:
        logger.debug(f"Starting computation of Delaunay triangles for {len(points2d)} candidate points.")
        # 1) Build once
        tri = Delaunay(points2d)
        ndim = points2d.shape[1]

        logger.debug(f"Assigning triangles for {len(grid_x)*len(grid_y.T)} query points.")
        # 2) Precompute geometry for your grid
        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T
        simplices = tri.find_simplex(grid)  # (n_query,) holds -1 for “outside”
        trans = tri.transform[simplices.clip(0)]  # avoid negative indices
        deltas = grid - trans[:, ndim]
        bary_partial = np.einsum('qij,qj->qi', trans[:, :ndim, :], deltas)
        bary = np.empty((grid.shape[0], ndim + 1))
        bary[:, :-1] = bary_partial
        bary[:, -1] = 1 - bary_partial.sum(axis=1)
        verts = tri.simplices[simplices.clip(0)]  # for outside, we’ll ignore these rows


        self._triangulation_precalc[
            hash_id
        ] = DelaunayInterpolation.TriangulationData(
            DiskBackedNDArray(bary),
            DiskBackedNDArray(verts),
            DiskBackedNDArray(simplices),
            DiskBackedNDArray(tri.simplices),
        )



# class BarycentricInterpolation(InterpolationStrategy):
#     def __init__(
#         self,
#         triangulator: TriangulationStrategy = DelaunayTriangulation(),
#     ):
#         self._tri = triangulator
#
#     def interpolate(
#         self,
#         values: np.ndarray,
#         points2d: np.ndarray,
#         grid_x: np.ndarray,
#         grid_y: np.ndarray,
#     ) -> np.ndarray:
#         # 1) Build triangles only once
#         triangles = self._tri.triangulate(points2d)
#
#         # 2) Compute barycentric weights & rasterize
#         #    (pseudo-code; you’d fill in your own math here)
#         coords = np.vstack([grid_x.ravel(), grid_y.ravel()]).T
#         img_flat = np.zeros(coords.shape[0])
#         for tri_idx in triangles:
#             verts = points2d[tri_idx]
#             vals  = values[tri_idx]
#             # compute mask & weights for this triangle
#             w = barycentric_weights(verts, coords)  # shape (M,)
#             img_flat += w * vals[None, :]
#         return img_flat.reshape(grid_x.shape)
#
#
# @INTERPOLATIONS.register("barycentric")
# class BarycentricFactory:
#     def __call__(self, *, use_incremental: bool = False) -> InterpolationStrategy:
#         tri = IncrementalTriangulation() if use_incremental else DelaunayTriangulation()
#         return BarycentricInterpolation(triangulator=tri)