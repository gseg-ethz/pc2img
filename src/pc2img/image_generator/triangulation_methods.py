from enum import Enum, auto
import logging
from typing import Callable

from tqdm import tqdm

try:
    from cuml.neighbors import NearestNeighbors
    GPU_ENABLED_NN = True
except ImportError:
    from sklearn.neighbors import NearestNeighbors
    GPU_ENABLED_NN = False

try:
    import cupy as cp
    from cupyx.scipy.spatial import Delaunay
    GPU_ENABLED_DELAUNAY = True
except ImportError:
    from scipy.spatial import Delaunay
    GPU_ENABLED_DELAUNAY = False



import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__.split(".")[0])

TriangulationResult = tuple[
    tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating]],
    NDArray[np.floating],
    NDArray[np.floating]
]

class TriangulationMethod(Enum):
    KNN              = "knn"
    DELAUNAY         = "delaunay"
    # DELAUNAY_BLOCK   = "delaunay_block"
    # GPU_DELAUNAY     = "test_gpu_delaunay"


def _tri_knn(points, xi, batch_size, **_) -> TriangulationResult:
    logger.debug(f"Running KNN on {'GPU' if GPU_ENABLED_NN else 'CPU'} with k=3 neighbors")
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
    return simplices, indices, distances


def _tri_delaunay(points, xi, **_) -> TriangulationResult:
    tri = Delaunay(points)
    simplex_index = tri.find_simplex(xi)
    indices = tri.simplices[simplex_index]
    simplices = (tri.points[indices[:, 0]], tri.points[indices[:, 1]], tri.points[indices[:, 2]])

    XA = tri.points[indices].reshape(-1, 2).astype(np.float32)
    XB = np.repeat(xi, repeats=3, axis=0)
    distances = np.linalg.norm(XA - XB, axis=1).reshape(-1, 3)
    distances[simplex_index == -1] = np.inf

    return simplices, indices, distances



_TRI_FUNCS: dict[TriangulationMethod, Callable[..., TriangulationResult]] = {
    TriangulationMethod.KNN: _tri_knn,
    TriangulationMethod.DELAUNAY: _tri_delaunay,

}

def calculate_triangulation(
            points: NDArray[np.floating] | tuple[NDArray[np.floating], NDArray[np.floating]],
            xi: NDArray[np.floating] | tuple[NDArray[np.floating], NDArray[np.floating]],
            method: str,
            batch_size: int = 5_000_000
) -> TriangulationResult:

    logging.debug(f"Starting calculation of triangulation with method: {method}.")

    try:
        tri_method = TriangulationMethod(method)
    except ValueError:
        valid = [m.value for m in TriangulationMethod]
        raise ValueError(f"Unknown method {method!r}, valid options are: {valid}")

    if isinstance(points, tuple):
        points = np.stack(points, axis=-1)

    if isinstance(xi, tuple):
        xi = np.stack(xi, axis=-1)

    # original_shape = None
    if xi.ndim == 3:
        # original_shape = xi.shape[:-1]
        xi = np.reshape(xi, newshape=(-1, 2))

    fn = _TRI_FUNCS[tri_method]
    simplices, indices, distances = fn(points=points, xi=xi, batch_size=batch_size)

    return simplices, indices, distances



