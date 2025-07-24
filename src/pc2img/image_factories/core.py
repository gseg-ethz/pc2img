from abc import ABC, abstractmethod
import re

import numpy as np

class ImageFactory(ABC):

    REGEX_GRADIENT_PATTERN = re.compile(r"gradient_(?P<axis>[x|y])_(?P<feature>.+)")
    REGEX_HILLSHADE_PATTERN = re.compile(r"hillshade(?:_(?P<azimuth>\d*)_(?P<altitude>\d*)_"
                                         r"(?P<z_factor>\d+(?:\.\d+)?)?)?")

    def __init__(self, image_resolution: tuple[int, int], rasterization_method: str):
        if len(image_resolution) != 2:
            raise ValueError(f"``image_resolution`` needs to have two values!")
        if any(res < 1 for res in image_resolution):
            raise ValueError(f"The image resolution components need to all be above zero!")

        self.image_resolution = image_resolution
        self.rasterization_method = rasterization_method

        self._pixel_raster = self._generate_pixel_raster()

        self._interpolation = None

    @property
    @abstractmethod
    def identifier(self):
        pass

    @property
    def aspect_ratio(self):
        return self.image_resolution[1] / self.image_resolution[0]

    @staticmethod
    def calculate_triangulation(
            points: np.ndarray | tuple[np.ndarray, np.ndarray],
            xi: np.ndarray | tuple[np.ndarray, np.ndarray],
            method: str,
            batch_size: int = 5_000_000
    ) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray, np.ndarray]:

        logging.debug(f"Starting calculation of triangulation with method: {method}.")

        if isinstance(points, tuple):
            points = np.stack(points, axis=-1)

        if isinstance(xi, tuple):
            xi = np.stack(xi, axis=-1)

        if xi.ndim == 3:
            original_shape = xi.shape[:-1]
            xi = np.reshape(xi, newshape=(-1, 2))

        match method:
            case 'knn':
                knn = NearestNeighbors(n_neighbors=3)
                knn.fit(points)

                nb_pixels = xi.shape[0]
                if not batch_size or nb_pixels <= batch_size:
                    distances, indices = knn.kneighbors(xi)
                else:
                    distances = np.empty((nb_pixels, 3), dtype=np.float32)
                    indices = np.empty((nb_pixels, 3), dtype=np.int32)

                    for start in tqdm(range(0, nb_pixels, batch_size),
                                      disable=not (logger.getEffectiveLevel() <= logging.INFO),
                                      desc="KNN triangulation batches"):
                        end = min(start + batch_size, nb_pixels)
                        dists_chunck, indices_chunck = knn.kneighbors(xi[start:end])
                        distances[start:end] = distances[start:end]
                        indices[start:end] = indices_chunck

                simplices = points[indices[:, 0]], points[indices[:, 1]], points[indices[:, 2]]

            case 'delaunay':
                tri = Delaunay(points)
                simplex_index = tri.find_simplex(xi)
                indices = tri.simplices[simplex_index]
                simplices = (tri.points[indices[:, 0]], tri.points[indices[:, 1]], tri.points[indices[:, 2]])

                XA = tri.points[indices].reshape(-1, 2).astype(np.float32)
                XB = np.repeat(xi, repeats=3, axis=0)
                distances = np.linalg.norm(XA - XB, axis=1).reshape(-1, 3)
                distances[simplex_index == -1] = np.inf

            case 'delaunay_block':
                Nx, Ny = 8, 8  # number of blocks in x and y
                margin = 0.01  # fraction of block‐size to overlap
                # global bounds and block sizes
                simplices, indices, distances = delaunay_query_threads(
                    points, xi,
                    Nx=Nx, Ny=Ny, margin=0.01,
                    n_workers=12
                )

            case 'test_gpu_delaunay':

                # import cupy as cp
                # from cupyx.scipy.spatial import Delaunay
                Nx, Ny = 8, 8  # number of blocks in x and y
                margin = 0.01  # fraction of block‐size to overlap
                dtype = np.float32  # choose float32 for less GPU memory

                # 1) global bounds and block sizes
                xmin, ymin = points.min(axis=0)
                xmax, ymax = points.max(axis=0)
                bx = (xmax - xmin) / Nx
                by = (ymax - ymin) / Ny

                m = xi.shape[0]
                # prepare output arrays
                indices = -np.ones((m, 3), dtype=int)
                distances = np.full((m, 3), np.inf, dtype=float)

                # 2) loop over blocks
                for i, j in tqdm(product(range(Nx), range(Ny)), total=Nx * Ny, desc="GPU blocks"):
                    # core block
                    x0c = xmin + i * bx;
                    x1c = x0c + bx
                    y0c = ymin + j * by;
                    y1c = y0c + by
                    # extended block for triangulation
                    x0e = x0c - margin * bx;
                    x1e = x1c + margin * bx
                    y0e = y0c - margin * by;
                    y1e = y1c + margin * by

                    # 2a) pick the points in the extended block
                    mask_ext = (
                            (points[:, 0] >= x0e) & (points[:, 0] <= x1e)
                            & (points[:, 1] >= y0e) & (points[:, 1] <= y1e)
                    )
                    idxs_ext = np.nonzero(mask_ext)[0]
                    if idxs_ext.size < 3:
                        continue

                    # 2b) GPU‐Delaunay the block
                    pts_block = cp.asarray(points[idxs_ext], dtype=dtype)
                    tri_block = Delaunay(pts_block)
                    verts = tri_block.simplices  # shape (n_tri, 3)

                    # 2c) pick only the xi in *this block’s core* region
                    mask_xi_core = (
                            (xi[:, 0] >= x0c) & (xi[:, 0] <= x1c)
                            & (xi[:, 1] >= y0c) & (xi[:, 1] <= y1c)
                    )
                    idxs_xi_core = np.nonzero(mask_xi_core)[0]
                    if idxs_xi_core.size == 0:
                        continue

                    # 2d) locate those xi
                    xi_gpu = cp.asarray(xi[idxs_xi_core], dtype=cp.float64)
                    local_simp = tri_block.find_simplex(xi_gpu).get()  # (-1 if outside)

                    # 2e) vectorized mapping & distance‐compute
                    #   local_simp:  (n_core,)  int array on CPU after .get()
                    #   idxs_xi_core: (n_core,) global-xi indices

                    valid = local_simp >= 0
                    if valid.any():
                        # which query points are actually in some simplex
                        qi_core = idxs_xi_core[valid]  # shape (v,)

                        # get the GPU‐simplices for those valid ones, move to CPU
                        # verts is GPU array of shape (n_tri,3)
                        local_tris = verts[local_simp[valid]].get()  # shape (v,3)

                        # map block‐local verts → global point indices
                        global_tris = idxs_ext[local_tris]  # shape (v,3)
                        indices[qi_core] = global_tris  # fill your m×3 output

                        # and distances: shape (v,3,2) minus (v,1,2) → norm→ (v,3)
                        P = points[global_tris]  # (v,3,2)
                        Q = xi[qi_core][:, None, :]  # (v,1,2)
                        distances[qi_core] = np.linalg.norm(P - Q, axis=2)

                # 3) assemble the same “simplices” tuple as before
                simplices = (
                    points[indices[:, 0]],
                    points[indices[:, 1]],
                    points[indices[:, 2]],
                )

            case _:
                raise ValueError(f"{method} is not a correct method")


        return simplices, indices, distances

    def _generate_pixel_raster(self) -> tuple[np.ndarray, np.ndarray]:
        row_index = np.arange(start=0, stop=self.image_resolution[0], dtype=np.float32)
        column_index = np.arange(start=0, stop=self.image_resolution[1], dtype=np.float32)
        ii, jj = np.meshgrid(row_index, column_index, indexing="ij")
        return ii, jj


    @staticmethod
    def barycentric_interpolation(
            # points: np.ndarray | tuple[np.ndarray, np.ndarray],
            values: np.ndarray | tuple[np.ndarray, ...],
            # triangulation: tuple[np.ndarray, np.ndarray, np.ndarray],
            simplices: tuple[np.ndarray, np.ndarray, np.ndarray],
            indices: np.ndarray,
            distances: np.ndarray,
            xi: np.ndarray | tuple[np.ndarray, np.ndarray], # Todo: the handling of xi and simplices etc is not consistent
            filter_distance: float = 0.0,
            fill_value: float = np.nan) -> list[np.ndarray]:
        """
            Interpolate unstructured 2D data using barycentric interpolation.

            Parameters
            ----------
            points : 2-D ndarray of floats with shape (n, 2), or length 2 tuple of 1-D ndarrays with shape (n,).
                Data point coordinates.
            values : tuple of ndarray of float, shape (n,)
                Data values.
            xi : 2-D ndarray of floats with shape (m, 2), or length 2 tuple of ndarrays broadcastable to the same shape.
                Points at which to interpolate data.
            filter_distance : float, optional
                Maximum distance to closest point of simplex before replacing interpolation result with ``fill_value``.
                If not provided, defaults to ``0.0``, which is interpreted as no filter.
            fill_value : float, optional
                Value used to fill in for requested points outside of the
                convex hull of the input points. If not provided, then the
                default is ``nan``. This option has no effect for the
                'nearest' method.

            Returns
            -------
            ndarray
                Array of interpolated values.

            Todo
            ----
                -

            See Also
            --------
            scipy.spatial.Delaunay
        """
        logging.debug(f"Starting barycentric interpolation.")


        if not isinstance(values, tuple):
            values = tuple(values)

        if isinstance(xi, tuple):
            xi = np.stack(xi, axis=-1)

        if xi.ndim == 3:
            original_shape = xi.shape[:-1]
            xi = np.reshape(xi, newshape=(-1, 2))
        # delaunay = Delaunay(points)
        # simplex_index = delaunay.find_simplex(xi)
        # indices = delaunay.simplices[simplex_index]
        #
        # v0, v1, v2 = (delaunay.points[indices[:, 0]], delaunay.points[indices[:, 1]],
        #               delaunay.points[indices[:, 2]])

        v0, v1, v2 = simplices

        detT = (v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1])

        alpha = np.full_like(detT, fill_value=np.nan)
        beta = np.full_like(detT, fill_value=np.nan)

        np.divide(
            ((v1[:, 1] - v2[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (xi[:, 1] - v2[:, 1])),
            detT,
            out=alpha,
            where = (detT != 0)
        )
        np.divide(
            ((v2[:, 1] - v0[:, 1]) * (xi[:, 0] - v2[:, 0]) + (v0[:, 0] - v2[:, 0]) * (xi[:, 1] - v2[:, 1])),
            detT,
            out=beta,
            where = (detT != 0)
        )

        gamma = 1 - alpha - beta
        barycentric_weights = np.stack((alpha, beta, gamma), axis=1)




        if filter_distance:
            filter_indices = np.nanmin(distances, axis=1) > filter_distance
        else:
            filter_indices = np.isinf(distances).any(axis=1)

        interpolation_results = []
        for v in values:
            interpolation_values = np.sum(v[indices] * barycentric_weights, axis=1)
            interpolation_values[filter_indices] = fill_value
            interpolation_values[np.isnan(gamma)] = fill_value

            if "original_shape" in locals():
                interpolation_values = np.reshape(interpolation_values, newshape=original_shape)

            interpolation_results.append(interpolation_values)
        return interpolation_results

    def map_to_nearest_pixel(self, points: np.ndarray, values: np.ndarray | tuple[np.ndarray, ...]) -> list[NDArray]:
        # Todo: Think about splitting the two tasks
        if isinstance(values, np.ndarray):
            values = (values,)

        elevation_pixel_int = np.floor(points[0]).astype(int)
        horizontal_pixel_int = np.floor(points[1]).astype(int)
        rasterized_blank = np.full(self.image_resolution, np.nan)

        rasterized_data = list()
        for v in values:
            rasterized_values = rasterized_blank.copy().astype(v.dtype) if v.dtype.kind == "f" else rasterized_blank.copy()
            rasterized_values[elevation_pixel_int, horizontal_pixel_int] = v
            rasterized_data.append(rasterized_values)

        return rasterized_data

    def map_to_nearest_pixel_with_nanconv(self, points: np.ndarray, values: np.ndarray | tuple[np.ndarray, ...],
                                          kernel: NDArray) -> NDArray:
        rasterized_data = self.map_to_nearest_pixel(points, values)

        rasterized_data_with_nanconv = list()
        for rd in rasterized_data:
            rasterized_data_with_nanconv.append(nanconv(rd, kernel))

        return rasterized_data_with_nanconv
