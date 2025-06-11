from abc import ABC, abstractmethod
from typing import Literal, Optional
from pathlib import Path

import numpy as np
from numpy._typing import DTypeLike
from numpy.typing import NDArray
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator
from scipy.spatial import Delaunay

from .registry import INTERPOLATIONS
from .triangulation import TriangulationStrategy, DelaunayTriangulation
from ..image_cache.lazy_disk_cache import LazyDiskCache

class InterpolationStrategy(ABC):
    @abstractmethod
    def interpolate(
        self,
        values: np.ndarray,
        points2d: np.ndarray,
        grid_x: np.ndarray,
        grid_y: np.ndarray
    ) -> np.ndarray:
        """Interpolate point-values onto a grid."""

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

class _DiskBackedNDArray(LazyDiskCache):

    def __init__(
            self,
            array_data: NDArray,
            enable_caching: bool = True,
            cache_path: Optional[Path] = None,
            automatic_offloading: bool = True,
            purge_disk_on_gc: bool = True

    ) -> None:
        self._data = array_data
        self._shape = array_data.shape
        self._dtype = array_data.dtype
        super().__init__(enable_caching, cache_path, automatic_offloading, purge_disk_on_gc)

    @LazyDiskCache.ensure_loaded
    def __array__(self, dtype=None, *, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported. A copy is always created.")

        arr = self._data
        return arr.astype(dtype, copy=True) if dtype else arr.copy()

    def _describe_buffer(self) -> tuple[tuple[int, ...], DTypeLike, np.ndarray]:
        return self._shape, self._dtype, self._data

    def _drop_buffer(self) -> None:
        self._data = None

    def _describe_shape_dtype(self) -> tuple[tuple[int, ...], DTypeLike]:
        return self._shape, self._dtype

    def _set_buffer(self, buf: NDArray) -> None:
        self._data = buf


@INTERPOLATIONS.register("delaunay")
class DelaunayInterpolation(InterpolationStrategy):
    grid_x: Optional[_DiskBackedNDArray] = None
    grid_y: Optional[_DiskBackedNDArray] = None
    points2d: Optional[_DiskBackedNDArray] = None

    bary: Optional[_DiskBackedNDArray] = None
    verts: Optional[_DiskBackedNDArray] = None
    simplices: Optional[_DiskBackedNDArray] = None



    def __init__(self):
        self._triangulation_precalc: Optional[dict[Literal["grid_x", "grid_y", "points2d", "bary", "verts", "simplices"], NDArray]] = None


    def interpolate(self, values, points2d, grid_x, grid_y, fill_value: float = np.nan) -> NDArray:
        if (self._triangulation_precalc is None  #Todo: Rework
                or not np.allclose(points2d, self.points2d)
                or not np.allclose(grid_x, self._triangulation_precalc["grid_x"])
                or not np.allclose(grid_y, self._triangulation_precalc["grid_y"])
        ):
            self._precalc_traingulation(points2d, grid_x, grid_y)

        fill_value = np.nan
        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T
        simplices = self._triangulation_precalc["simplices"]
        verts = self._triangulation_precalc["verts"]
        bary = self._triangulation_precalc["bary"]


        nQ = grid.shape[0]
        result = np.full(nQ, fill_value, dtype=float)
        mask = (simplices >= 0)
        # only compute where inside hull
        result[mask] = np.einsum(
            'qi,qi->q',
            values[verts[mask]],  # pick only valid rows
            bary[mask]
        )
        return result.reshape(grid_x.shape)


    def _precalc_traingulation(self, points2d, grid_x, grid_y):
        # 1) Build once
        tri = Delaunay(points2d)
        ndim = points2d.shape[1]

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

        self._triangulation_precalc = {
            "grid_x": grid_x,
            "grid_y": grid_y,
            "points2d": points2d,
            "bary": bary,
            "verts": verts,
            "simplices": simplices,
        }



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