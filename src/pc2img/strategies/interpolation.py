from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from numpy.typing import DTypeLike, NDArray
from numpy.lib.mixins import NDArrayOperatorsMixin
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator
from scipy.spatial import Delaunay

from GSEGUtils.config import get_defaults, CacheDefaults

from pc2img.image_cache.lazy_disk_cache import LazyDiskCache
from .registry import INTERPOLATIONS

DEFAULT: CacheDefaults = get_defaults()


class InterpolationStrategy(ABC):
    @abstractmethod
    def interpolate(
        self,
        values: NDArray,
        points2d: NDArray,
        grid_x: NDArray,
        grid_y: NDArray
    ) -> NDArray:
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

class _DiskBackedNDArray(LazyDiskCache, NDArrayOperatorsMixin):

    def __init__(
            self,
            array_data: NDArray,
            enable_caching: bool = True,
            cache_path: Optional[Path] = None,
            automatic_offloading: bool = DEFAULT.preset_automatic_offloading,
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


    @LazyDiskCache.ensure_loaded
    def __getitem__(self, key):
        return self._data[key]


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

    @dataclass(frozen=True)
    class TriangulationData:
        bary: _DiskBackedNDArray
        verts: _DiskBackedNDArray
        simplices: _DiskBackedNDArray


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
        if hash_id not in self._triangulation_precalc:
            self._precalc_traingulation(points2d, grid_x, grid_y, hash_id)

        triangulation_data = self._triangulation_precalc[hash_id]

        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T
        simplices = triangulation_data.simplices
        verts = triangulation_data.verts
        bary = triangulation_data.bary


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


    def _precalc_traingulation(
            self,
            points2d: NDArray,
            grid_x: NDArray,
            grid_y: NDArray,
            hash_id: int
    ) -> None:
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


        self._triangulation_precalc[
            hash_id
        ] = DelaunayInterpolation.TriangulationData(
            _DiskBackedNDArray(bary),
            _DiskBackedNDArray(verts),
            _DiskBackedNDArray(simplices)
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