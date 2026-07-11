from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

import numpy as np
from GSEGUtils.base_types import (
    Array_Nx2_Float_T,
    Vector_Bool_T,
)
from numpy.typing import NDArray
from pchandler import PointCloudData
from pchandler.filters import BoxFilter, FoVFilter
from pchandler.geometry.coordinates import rhv2xyz
from pchandler.geometry.spherical import FoV
from pchandler.geometry.transforms import Transform

if TYPE_CHECKING:
    # Private pchandler symbol used only in a static annotation on
    # PerspectiveProjection.__init__ (see below). Guarding it under TYPE_CHECKING
    # keeps `import pc2img.strategies.projection` — which also ships
    # SphericalProjection / OrthographicProjection — working even if a future
    # pchandler drops or renames the private symbol (T-04-D1).
    from pchandler.geometry.transforms import _TransformArray

from .registry import PROJECTIONS, _StrategyClass

ProjectionName = Literal["spherical", "orthographic", "perspective"]


def _reject_wrapping_fov(fov: FoV) -> None:
    """Refuse a horizontally wrapping FoV (``left > right``, ``crosses_pi=True``).

    A wrapping FoV would make the ``left`` extent numerically greater than the
    ``right`` extent, so span normalization silently reverses the horizontal
    pixel axis (the M-05/D-15 silent-reversal bug). Rather than emit reversed
    columns we refuse, mirroring pchandler's own ``FoV.tile()`` split-first
    refusal. Callers must split the FoV at the ``+/- pi`` boundary first.

    Shared by both ``SphericalProjection.project_raw`` and
    ``SphericalProjection.inverse_projection`` so the forward and inverse paths
    stay in sync behind a single message source.
    """
    if fov.crosses_pi:
        raise NotImplementedError(
            "SphericalProjection does not support wrapping FoVs "
            "(left > right, i.e. crosses_pi=True). "
            "Split the FoV at the wrap-around boundary before projecting."
        )


class ProjectionStrategy(ABC):
    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[..., ProjectionStrategy], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, _) -> ProjectionStrategy:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return PROJECTIONS.create(value)
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], dict):
            key, kwargs = value
            return PROJECTIONS.create(key, **kwargs)

        raise TypeError(f"Cannot interpret {value!r} as a {cls.__name__} strategy")

    @abstractmethod
    def project_raw(
        self,
        pcd: PointCloudData,
    ) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        """
        Compute raw 2D coordinates in model space and a mask of valid points.
        Returns:
          - coords_raw: shape (N, 2) raw coordinates (e.g., angles or xy)
          - mask: boolean array of length N indicating which points to keep
        """
        ...

    @abstractmethod
    def inverse_projection(self): ...

    def project(self, pcd: PointCloudData, resolution: tuple[int, int]) -> tuple[NDArray, NDArray]:
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


class ProjectionStrategyClass(_StrategyClass[ProjectionStrategy]):
    registry = PROJECTIONS
    base_type = ProjectionStrategy


@PROJECTIONS.register("spherical")
class SphericalProjection(ProjectionStrategy):
    def __init__(
        self,
        *,
        field_of_view: FoV | None = None,
    ) -> None:
        self._field_of_view = field_of_view

    @property
    def fov(self) -> FoV | None:
        return self._field_of_view

    def project_raw(self, pcd: PointCloudData) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        mask = (
            FoVFilter(fov=self._field_of_view).mask(pcd)
            if self._field_of_view is not None
            else np.ones((pcd.nbPoints,), dtype=bool)
        )

        fov = self._field_of_view if self._field_of_view is not None else pcd.fov
        # Guard both the user-supplied FoV and pcd.fov: a wrapping FoV would
        # reverse the horizontal axis under span normalization (M-05/D-15).
        _reject_wrapping_fov(fov)
        mins = np.array([fov.left, fov.top]).squeeze()
        maxs = np.array([fov.right, fov.bottom]).squeeze()

        return pcd.spher[mask, 1:], mask, mins, maxs

    def inverse_projection(
        self, range_img: NDArray, spherical_origin: NDArray | None = None
    ) -> tuple[NDArray, NDArray]:
        if self._field_of_view is None:
            # inverse_projection rebuilds angles from the raster's pixel grid, which
            # needs the angular extents. Unlike the forward path there is no point
            # cloud here to source a FoV from, so require an explicit one rather
            # than dereferencing None below (AttributeError).
            raise ValueError(
                "SphericalProjection.inverse_projection requires the projection to "
                "have been constructed with an explicit field_of_view; the range "
                "image alone does not carry angular extents."
            )
        # Same seam guard as the forward path: a wrapping FoV would make the
        # linspace below run left→right through the +/- pi discontinuity.
        _reject_wrapping_fov(self._field_of_view)

        px_vertical, px_horizontal = range_img.shape
        horizontal_range = np.linspace(
            self._field_of_view.left,
            self._field_of_view.right,
            num=px_horizontal,
            endpoint=True,
            dtype=np.float32,
        )
        vertical_range = np.linspace(
            self._field_of_view.top,
            self._field_of_view.bottom,
            num=px_vertical,
            endpoint=True,
            dtype=np.float32,
        )

        vertical_mesh, horizontal_mesh = np.meshgrid(vertical_range, horizontal_range, indexing="ij")

        range_data = range_img.flatten()
        vertical_angles = vertical_mesh.flatten()
        horizontal_angles = horizontal_mesh.flatten()

        spherical_coordinates = np.vstack((range_data, horizontal_angles, vertical_angles)).T
        mask = np.ones_like(range_data, dtype=bool)
        mask[np.isnan(range_data)] = False

        xyz = rhv2xyz(spherical_coordinates[mask], spherical_origin)
        return xyz, mask


@PROJECTIONS.register("orthographic")
class OrthographicProjection(ProjectionStrategy):
    def __init__(
        self,
        *,
        plane: Literal["xy", "yz", "xz"],
        roi_box: tuple[float, float, float, float] | None = None,
    ) -> None:
        match plane:
            case "xy":
                self._xyz_column_selection = [0, 1]
            case "yz":
                self._xyz_column_selection = [1, 2]
            case "xz":
                self._xyz_column_selection = [0, 2]
        self.plane = plane
        self._roi_box = roi_box

    def project_raw(self, pcd: PointCloudData) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        cols = self._xyz_column_selection
        if self._roi_box is not None:
            min_corner = np.array(3 * (-np.inf,))
            max_corner = np.array(3 * (np.inf,))

            min_corner[cols] = self._roi_box[:2]
            max_corner[cols] = self._roi_box[2:]

            mask = BoxFilter(min_corner, max_corner).mask(pcd)
        else:
            mask = np.ones((pcd.nbPoints,), dtype=bool)

        # Select the two plane columns rows-then-columns: pcd.xyz[mask][:, cols]
        # yields (M, 2). The prior pcd.xyz[mask, cols] fancy-index broadcast the
        # boolean row mask against the 2-element column list and produced a
        # silent diagonal (M-01/BUG-01).
        coords = pcd.xyz[mask][:, cols]

        # Provide the (mins, maxs) the base project() needs for span normalization.
        # Prefer the ROI box extent when supplied (so identical clouds normalize to
        # the same frame); otherwise fall back to the kept-point extent.
        if self._roi_box is not None:
            mins = np.asarray(self._roi_box[:2], dtype=coords.dtype)
            maxs = np.asarray(self._roi_box[2:], dtype=coords.dtype)
        elif coords.shape[0]:
            mins = coords.min(axis=0)
            maxs = coords.max(axis=0)
        else:
            mins = np.zeros(2, dtype=coords.dtype)
            maxs = np.ones(2, dtype=coords.dtype)

        return coords, mask, mins, maxs

    def inverse_projection(self):
        # Orthographic projection discards the out-of-plane axis, so a raster
        # cannot be inverted back to 3D without that missing depth. This method
        # exists to satisfy the ProjectionStrategy ABC (its absence previously
        # left OrthographicProjection abstract and impossible to instantiate);
        # it is a documented refusal, not a silent stub.
        raise NotImplementedError(
            "OrthographicProjection has no inverse: the projection drops the "
            "out-of-plane coordinate, so the raster cannot be lifted back to 3D."
        )


@PROJECTIONS.register("perspective")
class PerspectiveProjection(ProjectionStrategy):
    """Full pinhole camera projection ``x ∝ K·(R·X + t)``.

    Parameters
    ----------
    projection_matrix : NDArray | _TransformArray
        The 3x3 camera intrinsic matrix ``K``. Applied linearly; the perspective
        divide by camera depth is performed manually.
    rotation_matrix : NDArray | _TransformArray
        The 3x3 **proper rotation** ``R`` of the extrinsic. Must be orthonormal
        with ``det ≈ +1``. A non-3x3 matrix (notably a 4x4) raises ``TypeError`` —
        pass the camera translation via ``translation=`` instead of baking it into
        a 4x4 extrinsic.
    translation : NDArray | None, keyword-only
        The length-3 camera-frame translation ``t``. ``None`` → ``zeros(3)``,
        reproducing an origin camera. Convention is camera-frame: a caller holding
        a camera *center* ``C`` (world coordinates) passes ``t = −R·C`` — matching
        pchandler ``Transform.generate(rotation, translation)`` which builds
        ``x0 = (R·s + t) @ x1``. Do NOT use an ``R·(X − C)`` convention.

    Notes
    -----
    Breaking change (D-17): a 4x4 ``rotation_matrix`` was previously accepted and
    silently treated as an affine extrinsic; it now raises ``TypeError``. The 4x4
    path had zero reachable callers, so this is batched into the release with no
    runtime ``DeprecationWarning`` — version pinning is the migration deferral.

    The extrinsic is applied FIRST via pchandler's transform matmul contract
    (``Transform @ pcd`` → ``pcd.__rmatmul__``): ``K`` (3x3) cannot be pre-composed
    with a 4x4 affine because ``pcd.__rmatmul__`` accepts a 4x4 only if it is a
    pure affine and ``_TransformArray.__matmul__`` composes only same-shaped
    matrices — so we never write ``(K @ extrinsic) @ pcd``.
    """

    def __init__(
        self,
        projection_matrix: NDArray | _TransformArray,
        rotation_matrix: NDArray | _TransformArray,
        *,
        translation: NDArray | None = None,
    ):
        rot = np.asarray(getattr(rotation_matrix, "arr", rotation_matrix), dtype=np.float32)
        # Fail fast on a non-3x3 rotation. A 4x4 is the notable case: the caller
        # meant to supply an extrinsic — steer them to translation= (D-01).
        if rot.shape != (3, 3):
            raise TypeError(
                f"PerspectiveProjection expected a 3×3 rotation matrix; got shape {rot.shape}. "
                "Pass the camera translation via the translation= argument."
            )
        # A proper rotation is orthonormal with det ≈ +1. A scale/shear baked into
        # a 3x3 is silent wrong-geometry; refuse it rather than honor it.
        identity = np.eye(3, dtype=np.float32)
        if not (np.allclose(rot @ rot.T, identity, atol=1e-6) and np.isclose(np.linalg.det(rot), 1.0, atol=1e-6)):
            raise ValueError(
                "PerspectiveProjection rotation_matrix must be a proper rotation "
                "(orthonormal, det ≈ +1); got a matrix with scale/shear or reflection."
            )

        if translation is None:
            trans = np.zeros(3, dtype=np.float32)
        else:
            trans = np.asarray(translation, dtype=np.float32)
            if trans.shape != (3,):
                raise ValueError(
                    f"PerspectiveProjection translation must be a length-3 vector; got shape {trans.shape}."
                )

        self.projection_matrix = projection_matrix
        self.rotation_matrix = rotation_matrix
        self._rotation = rot
        self._translation = trans
        self._intrinsics = np.asarray(getattr(projection_matrix, "arr", projection_matrix), dtype=np.float32)

    def project_raw(self, pcd: PointCloudData) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        # PerspectiveProjection computes the full projection in one shot in
        # project() (K·(R·X + t) + manual perspective divide), so the two-phase
        # project_raw/normalize contract of the base class does not apply. This
        # documented refusal satisfies the ABC; it is never reached by project().
        raise NotImplementedError(
            "PerspectiveProjection computes pixel coordinates in one shot via project(); "
            "it does not implement the two-phase project_raw()/normalize contract."
        )

    def inverse_projection(self):
        raise NotImplementedError("PerspectiveProjection has no inverse: the perspective divide discards depth.")

    def project(self, pcd: PointCloudData, resolution: tuple[int, int]) -> tuple[Array_Nx2_Float_T, Vector_Bool_T]:
        """Project points to pixel coordinates via the full pinhole model.

        Applies the extrinsic ``[R|t]`` first (camera-frame coordinates), culls
        behind-camera points (depth ``Z_c ≤ 0``), then applies ``K`` and the
        manual perspective divide.

        Returns
        -------
        pts2d : Array_Nx2_Float_T
            Pixel coordinates of the in-bounds, in-front points, shape ``(M, 2)``.
        mask : Vector_Bool_T
            Boolean mask over all ``N`` input points, shape ``(N,)``.
        """
        # 1) extrinsic-first: build the 4x4 affine [R|t] and apply it via the
        #    documented pchandler `Transform @ pcd` contract (dispatches to
        #    pcd.__rmatmul__), yielding camera-frame coordinates Xc = R·X + t.
        extrinsic = Transform.generate(rotation=self._rotation, translation=self._translation)
        camera_frame = extrinsic @ pcd
        camera_xyz = np.asarray(camera_frame.xyz)
        depth = camera_xyz[:, 2]

        # 2) apply K, then the manual perspective divide by the homogeneous depth.
        uv_h = camera_xyz @ self._intrinsics.T  # (N, 3), row = K · Xc
        with np.errstate(invalid="ignore", divide="ignore"):
            uv = uv_h[:, :2] / uv_h[:, 2].reshape(-1, 1)

        # 3) M-02 behind-camera cull: drop points at/behind the camera plane
        #    (Z_c ≤ 0) so a double-sign-flip phantom cannot land in-bounds.
        in_front = depth > 0
        in_bounds = np.logical_and(
            np.logical_and(uv[:, 0] >= 0, uv[:, 0] < resolution[0]),
            np.logical_and(uv[:, 1] >= 0, uv[:, 1] < resolution[1]),
        )
        mask = np.logical_and(in_front, in_bounds)

        return uv[mask, :], mask
