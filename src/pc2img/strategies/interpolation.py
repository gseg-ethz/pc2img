import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import Any, Literal

import numpy as np
from GSEGUtils.config import CacheDefaults, get_defaults
from GSEGUtils.lazy_disk_cache import (
    DiskBackedNDArray,
    DiskBackedStore,
    LazyDiskCacheConfig,
)
from numpy.typing import NDArray
from scipy.interpolate import (
    CloughTocher2DInterpolator,
    LinearNDInterpolator,
    NearestNDInterpolator,
)
from scipy.spatial import Delaunay

from .registry import INTERPOLATIONS, _StrategyClass
from .utils import thin_points_by_pixel_density

logger = logging.getLogger(__name__)

DEFAULT: CacheDefaults = get_defaults()

InterpolationName = Literal["linear", "nearest_neighbor", "cubic", "delaunay"]


class InterpolationStrategy(ABC):
    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[..., "InterpolationStrategy"], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, _) -> "InterpolationStrategy":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return INTERPOLATIONS.create(value)
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], dict):
            key, kwargs = value
            return INTERPOLATIONS.create(key, **kwargs)

        raise TypeError(f"Cannot interpret {value!r} as a {cls.__name__} strategy")

    @abstractmethod
    def interpolate(self, values: NDArray, points2d: NDArray, grid_x: NDArray, grid_y: NDArray) -> NDArray:
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
    """
    Interpolate via barycentric weights using a Delaunay triangulation.

    Parameters
    ----------
    lazy_disk_cache_config:
        Optional cache configuration for storing intermediate barycentric data.
    enable_density_thinning:
        When true, limit the number of input points per output pixel before
        building the triangulation to guard against OOMs on dense tiles.
    max_points_per_pixel:
        Cap for ``enable_density_thinning``. The first N points encountered per
        pixel are kept, the remainder dropped.
    density_ratio_trigger:
        Optional global guard controlling when thinning activates based on the
        overall point/pixel ratio.
    """

    def __init__(
        self,
        /,
        lazy_disk_cache_config: LazyDiskCacheConfig | None = None,
        *,
        enable_density_thinning: bool = False,
        max_points_per_pixel: int = 4,
        density_ratio_trigger: float | None = 4.0,
    ) -> None:
        self._lazy_disk_cache_config = lazy_disk_cache_config or LazyDiskCacheConfig()
        self._triangulation_precalc: dict[str, DiskBackedStore[DiskBackedNDArray]] = {}
        self._density_thinning_enabled = enable_density_thinning
        self._max_points_per_pixel = max_points_per_pixel
        self._density_ratio_trigger = density_ratio_trigger
        if self._density_thinning_enabled:
            if self._max_points_per_pixel < 1:
                raise ValueError("max_points_per_pixel must be >= 1 when density thinning is enabled")
            if self._density_ratio_trigger is not None and self._density_ratio_trigger <= 0:
                raise ValueError("density_ratio_trigger must be positive when provided")

    @staticmethod
    def _hash_settings(points2d: NDArray, grid_x: NDArray, grid_y: NDArray) -> str:
        m = hashlib.sha256()
        m.update(points2d.tobytes())
        m.update(grid_x.tobytes())
        m.update(grid_y.tobytes())
        return m.hexdigest()

    def interpolate(
        self,
        values: NDArray,
        points2d: NDArray,
        grid_x: NDArray,
        grid_y: NDArray,
        fill_value: float = np.nan,
    ) -> NDArray:

        if self._density_thinning_enabled and points2d.size:
            height, width = grid_x.shape
            thinned_points, keep_mask = thin_points_by_pixel_density(
                points2d,
                img_width=width,
                img_height=height,
                max_points_per_pixel=self._max_points_per_pixel,
                ratio_trigger=self._density_ratio_trigger,
            )
            if keep_mask.size and not np.all(keep_mask):
                if values.shape[0] != keep_mask.shape[0]:
                    raise ValueError("Values array length must match points2d when applying density thinning.")
                values = values[keep_mask]
                points2d = thinned_points
                logger.debug(
                    "Density thinning reduced projected points from %d to %d (max %d per pixel)",
                    keep_mask.shape[0],
                    points2d.shape[0],
                    self._max_points_per_pixel,
                )

        hash_str = self._hash_settings(points2d, grid_x, grid_y)
        if hash_str not in self._triangulation_precalc:
            self._triangulation_precalc[hash_str] = DiskBackedStore[DiskBackedNDArray](
                config=self._lazy_disk_cache_config.extend_cache_path(hash_str),
                factory=DiskBackedNDArray,
                value_type=DiskBackedNDArray,
            )

        if "bary" not in self._triangulation_precalc[hash_str]:
            logger.debug(f"Starting interpolation with hash {hash_str}")
            simplices, verts, bary, triangles = self._calculate_triangulation(points2d, grid_x, grid_y)
            self._triangulation_precalc[hash_str].add_data_to_store("triangles", triangles)
            self._triangulation_precalc[hash_str].add_data_to_store("simplices", simplices)
            self._triangulation_precalc[hash_str].add_data_to_store("verts", verts)
            self._triangulation_precalc[hash_str].add_data_to_store("bary", bary)
        else:
            simplices = np.asarray(self._triangulation_precalc[hash_str]["simplices"])
            verts = np.asarray(self._triangulation_precalc[hash_str]["verts"])
            bary = np.asarray(self._triangulation_precalc[hash_str]["bary"])
            triangles = np.asarray(self._triangulation_precalc[hash_str]["triangles"])
        self._triangulation_precalc[hash_str].offload(pickle_container=True)

        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T

        nQ = grid.shape[0]
        result = np.full(nQ, fill_value, dtype=float)
        mask = simplices >= 0

        # Compute triangle metrics once
        tri_vertices = points2d[triangles]  # shape (M, 3, 2)

        def compute_metrics(tri_pts):
            a = tri_pts[:, 1] - tri_pts[:, 0]
            b = tri_pts[:, 2] - tri_pts[:, 1]
            c = tri_pts[:, 0] - tri_pts[:, 2]
            edges = np.stack(
                [
                    np.linalg.norm(a, axis=1),
                    np.linalg.norm(b, axis=1),
                    np.linalg.norm(c, axis=1),
                ],
                axis=1,
            )
            # Hero's formula
            s = edges.sum(axis=1) / 2
            radicand = np.clip(
                s * (s - edges[:, 0]) * (s - edges[:, 1]) * (s - edges[:, 2]), 0, None
            )  # Guard against numeric instability
            area = np.sqrt(radicand)

            max_edge = edges.max(axis=1)
            min_edge = edges.min(axis=1)
            aspect_ratio = max_edge / np.maximum(min_edge, np.finfo(float).eps)
            return area, max_edge, aspect_ratio

        area, max_edge, aspect_ratio = compute_metrics(tri_vertices)

        area_thresh = np.median(area) * 10
        max_edge_thresh = None
        median_ratio = np.median(aspect_ratio)
        mad_ratio = np.median(np.abs(aspect_ratio - median_ratio))
        aspect_ratio_thresh = median_ratio + 6 * mad_ratio if mad_ratio > 0 else median_ratio * 10

        # Find bad triangles
        tri_is_good = np.ones_like(area, dtype=bool)
        if area_thresh is not None:
            tri_is_good &= area < area_thresh
        if max_edge_thresh is not None:
            tri_is_good &= max_edge < max_edge_thresh
        tri_is_good &= aspect_ratio <= aspect_ratio_thresh

        # Mask out query points whose triangle is bad
        mask &= tri_is_good[simplices]

        logger.debug(f"Valid query point percentage: {mask.sum() / len(mask):.1%}")

        # only compute where inside hull
        result[mask] = np.einsum(
            "qi,qi->q",
            values[verts[mask]],  # pick only valid rows
            bary[mask],
        )
        return result.reshape(grid_x.shape)

    def _calculate_triangulation(
        self, points2d: NDArray, grid_x: NDArray, grid_y: NDArray
    ) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        logger.debug(f"Starting computation of Delaunay triangles for {len(points2d)} candidate points.")
        # 1) Build once
        tri = Delaunay(points2d)
        ndim = points2d.shape[1]

        logger.debug(f"Assigning triangles for {len(grid_x) * len(grid_y.T)} query points.")
        # 2) Precompute geometry for your grid
        grid = np.vstack((grid_x.ravel(), grid_y.ravel())).T
        simplices = tri.find_simplex(grid)  # (n_query,) holds -1 for “outside”
        trans = tri.transform[simplices.clip(0)]  # avoid negative indices
        deltas = grid - trans[:, ndim]
        bary_partial = np.einsum("qij,qj->qi", trans[:, :ndim, :], deltas)
        bary = np.empty((grid.shape[0], ndim + 1))
        bary[:, :-1] = bary_partial
        bary[:, -1] = 1 - bary_partial.sum(axis=1)
        verts = tri.simplices[simplices.clip(0)]  # for outside, we’ll ignore these rows

        return simplices, verts, bary, tri.simplices
