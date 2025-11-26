from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]
BoolArray = NDArray[np.bool_]


def thin_points_by_pixel_density(
    points2d: FloatArray,
    *,
    img_width: int,
    img_height: int,
    max_points_per_pixel: int,
    ratio_trigger: float | None = None,
) -> tuple[FloatArray, BoolArray]:
    """
    Limit the number of projected points that fall into each image pixel.

    Parameters
    ----------
    points2d:
        Array of projected coordinates shaped (N, 2) with x/y pixel space values.
    img_width / img_height:
        Image resolution used to clamp coordinates into valid bins.
    max_points_per_pixel:
        Upper bound on the number of points retained per pixel.
    ratio_trigger:
        Optional global guard. If provided, thinning is skipped unless
        len(points2d) > ratio_trigger * (img_width * img_height).

    Returns
    -------
    filtered_points, mask
        The subset of points after thinning and the boolean mask applied along
        the first dimension of ``points2d``. The mask is always length N.
    """
    if max_points_per_pixel < 1:
        raise ValueError("max_points_per_pixel must be >= 1")

    n_points = points2d.shape[0]
    if n_points == 0:
        return points2d, np.zeros(0, dtype=bool)

    n_pixels = img_width * img_height
    if ratio_trigger is not None and ratio_trigger > 0 and n_pixels > 0:
        if n_points <= ratio_trigger * n_pixels:
            return points2d, np.ones(n_points, dtype=bool)

    # Clamp projected coordinates to the target pixel grid.
    ix = np.floor(points2d[:, 0]).astype(np.int64)
    iy = np.floor(points2d[:, 1]).astype(np.int64)
    np.clip(ix, 0, img_width - 1, out=ix)
    np.clip(iy, 0, img_height - 1, out=iy)

    lin_idx = iy * img_width + ix
    counts = np.bincount(lin_idx, minlength=n_pixels)
    if counts.size == 0 or counts.max() <= max_points_per_pixel:
        return points2d, np.ones(n_points, dtype=bool)

    keep_mask = np.zeros(n_points, dtype=bool)
    slot_counts = np.zeros_like(counts, dtype=np.int32)

    for i, bucket in enumerate(lin_idx):
        taken = slot_counts[bucket]
        if taken < max_points_per_pixel:
            keep_mask[i] = True
            slot_counts[bucket] = taken + 1

    return points2d[keep_mask], keep_mask

