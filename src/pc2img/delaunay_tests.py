from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from itertools import product
import numpy as np
from scipy.spatial import Delaunay
from tqdm import tqdm

def process_block(args):
    """
    Triangulate one (i,j) block and compute, for any xi in its core,
    the containing simplex global indices and distances to its vertices.
    Returns:
      qi_core      : (v,) indices into the global xi array
      global_tris  : (v,3) global point-indices of each triangle
      dist_core    : (v,3) distances from each xi to its triangle’s vertices
    """
    points, xi, i, j, Nx, Ny, margin = args

    # 1) compute global bounds and block sizes
    xmin, ymin = points.min(axis=0)
    xmax, ymax = points.max(axis=0)
    bx = (xmax - xmin) / Nx
    by = (ymax - ymin) / Ny

    # 2) core bounds
    x0c = xmin + i * bx
    x1c = x0c + bx
    y0c = ymin + j * by
    y1c = y0c + by

    # 3) extended bounds
    x0e = x0c - margin * bx
    x1e = x1c + margin * bx
    y0e = y0c - margin * by
    y1e = y1c + margin * by

    # 4) mask site-points in the extended block
    mask_ext = (
        (points[:, 0] >= x0e) & (points[:, 0] <= x1e) &
        (points[:, 1] >= y0e) & (points[:, 1] <= y1e)
    )
    idxs_ext = np.nonzero(mask_ext)[0]
    if idxs_ext.size < 3:
        # nothing to triangulate
        return np.array([], dtype=int), np.zeros((0,3), dtype=int), np.zeros((0,3), dtype=float)

    # 5) Delaunay on the extended block
    pts_block = points[idxs_ext]
    tri_block = Delaunay(pts_block)

    # 6) select query points within the core region
    mask_xi_core = (
        (xi[:, 0] >= x0c) & (xi[:, 0] <= x1c) &
        (xi[:, 1] >= y0c) & (xi[:, 1] <= y1c)
    )
    idxs_xi_core = np.nonzero(mask_xi_core)[0]
    if idxs_xi_core.size == 0:
        return np.array([], dtype=int), np.zeros((0,3), dtype=int), np.zeros((0,3), dtype=float)

    xi_core = xi[idxs_xi_core]
    # 7) find which simplex each core-query falls into
    simplices_local = tri_block.find_simplex(xi_core)
    valid = simplices_local >= 0
    if not valid.any():
        return np.array([], dtype=int), np.zeros((0,3), dtype=int), np.zeros((0,3), dtype=float)

    # 8) map to global indices
    qi_core      = idxs_xi_core[valid]                             # (v,)
    local_tris   = tri_block.simplices[simplices_local[valid]]     # (v,3)
    global_tris  = idxs_ext[local_tris]                            # (v,3)

    # 9) compute distances
    P = points[global_tris]                # (v,3,2)
    Q = xi[qi_core][:, None, :]            # (v,1,2)
    dist_core = np.linalg.norm(P - Q, axis=2)  # (v,3)

    return qi_core, global_tris, dist_core


def delaunay_query_parallel(points, xi,
                            Nx=8, Ny=8, margin=0.01,
                            n_workers=8):
    """
    Partition the domain into Nx×Ny blocks, run process_block in parallel,
    and assemble the global simplices, indices, and distances arrays.
    """
    m = xi.shape[0]
    # preallocate outputs
    indices   = -np.ones((m, 3), dtype=int)
    distances = np.full((m, 3), np.inf, dtype=float)

    # build argument list for each block (i, j)
    tasks = [
        (points, xi, i, j, Nx, Ny, margin)
        for i, j in product(range(Nx), range(Ny))
    ]

    # launch a process‐pool and collect results as they complete
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(process_block, t) for t in tasks]
        for fut in tqdm(as_completed(futures),
                        total=len(futures),
                        desc="blocks"):
            qi_core, global_tris, dist_core = fut.result()
            if qi_core.size == 0:
                continue
            indices[qi_core]   = global_tris
            distances[qi_core] = dist_core

    # assemble the same `simplices` tuple as your original code
    simplices = (
        points[indices[:, 0]],
        points[indices[:, 1]],
        points[indices[:, 2]],
    )
    return simplices, indices, distances


def process_block_thread(i, j, points, xi, Nx, Ny, margin):
    """
    Triangulate the (i,j) tile on the CPU and for any xi in its core
    return the indices of the containing triangle's vertices and distances.
    """
    # 1) compute global bounds & tile size
    xmin, ymin = points.min(axis=0)
    xmax, ymax = points.max(axis=0)
    bx = (xmax - xmin) / Nx
    by = (ymax - ymin) / Ny

    # 2) core bounds
    x0c, x1c = xmin + i * bx, xmin + (i + 1) * bx
    y0c, y1c = ymin + j * by, ymin + (j + 1) * by

    # 3) extended bounds
    x0e = x0c - margin * bx
    x1e = x1c + margin * bx
    y0e = y0c - margin * by
    y1e = y1c + margin * by

    # 4) select points in extended block
    mask_ext = (
        (points[:, 0] >= x0e) & (points[:, 0] <= x1e) &
        (points[:, 1] >= y0e) & (points[:, 1] <= y1e)
    )
    idxs_ext = np.nonzero(mask_ext)[0]
    if idxs_ext.size < 3:
        # nothing to triangulate here
        return np.array([], dtype=int), np.zeros((0, 3), dtype=int), np.zeros((0, 3), dtype=float)

    # 5) local Delaunay
    pts_block = points[idxs_ext]
    tri_block = Delaunay(pts_block)

    # 6) select queries in core region
    mask_xi_core = (
        (xi[:, 0] >= x0c) & (xi[:, 0] <= x1c) &
        (xi[:, 1] >= y0c) & (xi[:, 1] <= y1c)
    )
    idxs_xi_core = np.nonzero(mask_xi_core)[0]
    if idxs_xi_core.size == 0:
        return np.array([], dtype=int), np.zeros((0, 3), dtype=int), np.zeros((0, 3), dtype=float)

    xi_core = xi[idxs_xi_core]

    # 7) find containing simplex for each core-query
    simplices_local = tri_block.find_simplex(xi_core)
    valid = simplices_local >= 0
    if not valid.any():
        return np.array([], dtype=int), np.zeros((0, 3), dtype=int), np.zeros((0, 3), dtype=float)

    # 8) map local simplex -> global point-indices
    qi_core    = idxs_xi_core[valid]                            # (v,)
    local_tris = tri_block.simplices[simplices_local[valid]]    # (v,3)
    global_tris = idxs_ext[local_tris]                          # (v,3)

    # 9) compute distances
    P = points[global_tris]                 # (v,3,2)
    Q = xi[qi_core][:, None, :]             # (v,1,2)
    dist_core = np.linalg.norm(P - Q, axis=2)  # (v,3)

    return qi_core, global_tris, dist_core




def delaunay_query_threads(points, xi,
                           Nx=8, Ny=8, margin=0.01,
                           n_workers=8):
    m = len(xi)
    indices   = -np.ones((m,3), dtype=int)
    distances = np.full((m,3), np.inf, dtype=float)

    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = [
            pool.submit(process_block_thread, i, j, points, xi, Nx, Ny, margin)
            for i,j in product(range(Nx), range(Ny))
        ]
        for fut in tqdm(as_completed(futures),
                        total=Nx*Ny, desc="blocks"):
            qi_core, global_tris, dist_core = fut.result()
            if qi_core.size:
                indices[qi_core]   = global_tris
                distances[qi_core] = dist_core

    simplices = (
      points[indices[:, 0]],
      points[indices[:, 1]],
      points[indices[:, 2]],
    )
    return simplices, indices, distances