import re
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
from numpy.typing import NDArray
from pchandler.geometry import PointCloudData
from .strategies.projection import ProjectionStrategy
from .strategies.interpolation import InterpolationStrategy

from .features.core import BaseFeatureStrategy, DerivativeFeatureStrategy
from .features.manager import FeatureManager
from .features.registry import FEATURES

from .image_cache.disk_backed_image_data import DiskBackedImageData


# REGEX_GRADIENT_PATTERN = re.compile(r"^gradient_(?P<axis>[xy])_(?P<feature>.+)$")

class PointCloudImageGenerator:
    def __init__(
        self,
        pcd: PointCloudData,
        proj: ProjectionStrategy,
        interp: InterpolationStrategy,
        enable_caching: bool = False,
        cache_dir: Optional[Path] = None,
        automatic_offloading: bool = False,
        purge_disk_on_gc: bool = True,
    ):
        self._pcd = pcd
        self._proj = proj
        self._interp = interp
        self._cache_dir = cache_dir
        self._automatic_offloading = automatic_offloading
        self._purge_disk_on_gc = purge_disk_on_gc
        # self._cache = dict[str, NDArray]
        self.feature_mgr = FeatureManager(self._pcd, enable_caching, cache_dir, automatic_offloading, purge_disk_on_gc)


    def generate(
            self,
            features: list[str],
            resolution: tuple[int,int],
    ) -> dict[str,DiskBackedImageData]:
        pts2d, mask = self._proj.project(self._pcd, resolution)

        w, h = resolution
        gx = np.arange(w)
        gy = np.arange(h)
        grid_x, grid_y = np.meshgrid(gx, gy)

        self.feature_mgr.request(features)
        base_features_1D = self.feature_mgr.get_base_features()
        for bf_name, bf_1D in base_features_1D.items():
            bf_raster = self._interp.interpolate(bf_1D[mask], pts2d, grid_x, grid_y)
            self.feature_mgr.submit(bf_name, bf_raster)
        results = self.feature_mgr.get_targets()
        return results