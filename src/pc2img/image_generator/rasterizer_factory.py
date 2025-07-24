from abc import ABC, abstractmethod
from functools import partial
import numpy as np

from .triangulation_methods import calculate_triangulation
from ..util import nanconv, gaussian_kernel
from .core import ImageGenerator  # base class with interpolation methods

# -- Define the strategy interface --
class RasterizerStrategy(ABC):
    @abstractmethod
    def build_interpolator(self) -> callable:
        """
        Return a callable that accepts ``values`` (tuple of arrays) and returns a list of 2D rasters.
        """
        ...


# -- Concrete strategies --
class BarycentricDelaunayRasterizer(RasterizerStrategy):
    def __init__(
        self,
        coords: tuple[np.ndarray, np.ndarray],
        pixel_raster: tuple[np.ndarray, np.ndarray],
        filter_distance: float = 0.0,
        fill_value: float = np.nan,
    ):
        self.coords = coords
        self.pixel_raster = pixel_raster
        self.filter_distance = filter_distance
        self.fill_value = fill_value

    def build_interpolator(self):
        simplices, indices, distances = calculate_triangulation(
            points=self.coords,
            xi=self.pixel_raster,
            method="delaunay"
        )
        return partial(
            ImageGenerator.barycentric_interpolation,
            simplices=simplices,
            indices=indices,
            distances=distances,
            xi=self.pixel_raster,
            filter_distance=self.filter_distance,
            fill_value=self.fill_value,
        )


class BarycentricKnnRasterizer(RasterizerStrategy):
    def __init__(
        self,
        coords: tuple[np.ndarray, np.ndarray],
        pixel_raster: tuple[np.ndarray, np.ndarray],
        filter_distance: float = 0.0,
        fill_value: float = np.nan,
        batch_size: int = 5_000_000,
    ):
        self.coords = coords
        self.pixel_raster = pixel_raster
        self.filter_distance = filter_distance
        self.fill_value = fill_value
        self.batch_size = batch_size

    def build_interpolator(self):
        simplices, indices, distances = calculate_triangulation(
            points=self.coords,
            xi=self.pixel_raster,
            method="knn",
            batch_size=self.batch_size,
        )
        return partial(
            ImageGenerator.barycentric_interpolation,
            simplices=simplices,
            indices=indices,
            distances=distances,
            xi=self.pixel_raster,
            filter_distance=self.filter_distance,
            fill_value=self.fill_value,
        )


class RawRasterizer(RasterizerStrategy):
    def __init__(
        self,
        coords: tuple[np.ndarray, np.ndarray],
        pixel_raster: tuple[np.ndarray, np.ndarray],
    ):
        self.coords = coords
        self.pixel_raster = pixel_raster

    def build_interpolator(self):
        # direct nearest-pixel mapping, no filtering needed
        return partial(
            ImageGenerator.map_to_nearest_pixel,
            points=self.coords,
        )


class NanConvRasterizer(RasterizerStrategy):
    def __init__(
        self,
        coords: tuple[np.ndarray, np.ndarray],
        pixel_raster: tuple[np.ndarray, np.ndarray],
        kernel: np.ndarray = None,
    ):
        self.coords = coords
        self.pixel_raster = pixel_raster
        self.kernel = kernel or gaussian_kernel()

    def build_interpolator(self):
        return partial(
            ImageGenerator.map_to_nearest_pixel_with_nanconv,
            points=self.coords,
            kernel=self.kernel,
        )


# -- Factory --
class RasterizerFactory:
    """
    Factory for building rasterizer strategies based on method name.
    """
    _strategies: dict[str, type[RasterizerStrategy]] = {
        "bary_delaunay": BarycentricDelaunayRasterizer,
        "bary_knn":     BarycentricKnnRasterizer,
        "raw":          RawRasterizer,
        "nanconv":      NanConvRasterizer,
    }

    @classmethod
    def register(
        cls,
        name: str,
        strategy_cls: type[RasterizerStrategy]
    ) -> None:
        """
        Register a new rasterizer strategy under a custom name.
        """
        cls._strategies[name] = strategy_cls

    @classmethod
    def create(
        cls,
        method: str,
        coords: tuple[np.ndarray, np.ndarray],
        pixel_raster: tuple[np.ndarray, np.ndarray],
        **kwargs,
    ) -> RasterizerStrategy:
        """
        Instantiate the strategy for the given method name.
        Raises ValueError if the method is unknown.

        Parameters
        ----------
        method : str
            Key matching one of the registered strategies.
        coords : (elev_pixels, horz_pixels)
        pixel_raster : (ii, jj) meshgrid of pixel coordinates
        kwargs :
            Additional parameters specific to the strategy
        """
        try:
            strat_cls = cls._strategies[method]
        except KeyError:
            valid = list(cls._strategies)
            raise ValueError(f"Unknown rasterization method {method!r}, valid: {valid}")
        return strat_cls(coords=coords, pixel_raster=pixel_raster, **kwargs)
