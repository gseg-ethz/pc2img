from abc import ABC, abstractmethod
from typing import Optional, Literal, Any, Generator, Callable, Self

import numpy as np
from numpy.typing import NDArray

from pchandler.geometry import PointCloudData
from pchandler.filters import FoVFilter, BoxFilter
from pchandler.geometry.fov import FoV

from .registry import PROJECTIONS, _StrategyClass, StrategyFactory


ProjectionName = Literal["spherical", "orthographic"]

class ProjectionStrategy(ABC):

    # @classmethod
    # def __get_validators__(cls) -> Generator[Callable, None, None]:
    #     yield cls.validate
    #
    # @classmethod
    # def validate(cls, value: Any) -> Self:
    #     if isinstance(value, cls):
    #         return value
    #     if isinstance(value, str):
    #         try:
    #             return PROJECTIONS.

    @abstractmethod
    def project_raw(
        self,
        pcd: PointCloudData,
    ) -> tuple[NDArray, NDArray]:
        """
        Compute raw 2D coordinates in model space and a mask of valid points.
        Returns:
          - coords_raw: shape (N, 2) raw coordinates (e.g., angles or xy)
          - mask: boolean array of length N indicating which points to keep
        """
        ...

    def project(
        self,
        pcd: PointCloudData,
        resolution: tuple[int, int]
    ) -> tuple[NDArray, NDArray]:
        """
        Normalize raw coords into [0,1]×[0,1] based on data extents,
        map to pixel indices at the given resolution, and apply the mask.

        Returns:
          - pts2d: array of pixel coordinates shape (M, 2)
          - mask: original boolean mask shape (N,)
        """
        coords_raw, mask, mins, maxs = self.project_raw(pcd)
        w, h = resolution
        # normalize per-dimension
        # mins = coords_raw.min(axis=0)
        # maxs = coords_raw.max(axis=0)
        span = maxs - mins
        # avoid division by zero
        span[span == 0] = 1
        norm = (coords_raw - mins) / span
        u, v = norm[:, 0], norm[:, 1]
        # map to pixel indices
        x_px = u * (w - 1)
        y_px = v * (h - 1)
        pts2d = np.vstack((x_px, y_px)).T
        return pts2d, mask


class ProjectionStrategyClass(_StrategyClass, StrategyFactory[Any, ProjectionStrategy]):
    registry = PROJECTIONS
    base_type = ProjectionStrategy


@PROJECTIONS.register("spherical")
class SphericalProjection(ProjectionStrategy):
    def __init__(
            self,
            *,
            field_of_view: Optional[FoV] = None,
            **_: Any
    ) -> None:
        self._field_of_view = field_of_view

    def project_raw(self, pcd: PointCloudData) -> tuple[NDArray, NDArray]:
        mask = FoVFilter(fov=self._field_of_view).mask(pcd) if self._field_of_view is not None \
            else np.ones((pcd.nbPoints,), dtype=bool)

        fov = self._field_of_view if self._field_of_view is not None else pcd.fov
        mins = np.array([fov.left, fov.top]).squeeze()
        maxs = np.array([fov.right, fov.bottom]).squeeze()


        return pcd.spher[mask, 1:], mask, mins, maxs


@PROJECTIONS.register("orthographic")
class OrthographicProjection(ProjectionStrategy):
    def __init__(
            self,
            *,
            plane: Literal["xy", "yz", "xz"],
            roi_box: Optional[tuple[float, float, float, float]] = None,
            **_: Any
    ) -> None:
        match plane:
            case 'xy':
                self._xyz_column_selection = [0,1]
            case 'yz':
                self._xyz_column_selection = [1,2]
            case 'xz':
                self._xyz_column_selection = [0,2]
            # case _:  # Not needed if the configuration is guaranteed via a Pydantic Model or similar
            #     raise ValueError(f"plane must be 'xy' or 'yz' or 'xz'")
        self.plane = plane
        self._roi_box = roi_box

    def project_raw(self, pcd: PointCloudData) -> NDArray:
        if self._roi_box is not None:
            min_corner = np.array(3 * (-np.inf,))
            max_corner = np.array(3 * (np.inf,))

            min_corner[self._xyz_column_selection] = self._roi_box[:2]
            max_corner[self._xyz_column_selection] = self._roi_box[2:]

            mask = BoxFilter(min_corner, max_corner).mask(pcd)
        else:
            mask = np.ones((pcd.nbPoints,), dtype=bool)

        return pcd.xyz[mask, self._xyz_column_selection], mask
