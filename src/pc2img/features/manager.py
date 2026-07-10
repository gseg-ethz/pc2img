
import numpy as np
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from numpy.typing import NDArray
from pchandler import PointCloudData

from pc2img.image_cache import DiskBackedImageData, DiskBackedImageStore

from .core import BaseFeatureStrategy
from .registry import FEATURES, FeatureRegistry, FeatureSpec


class FeatureManager:
    def __init__(
            self,
            pcd: PointCloudData,
            *,
            lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ):
        self.registry: FeatureRegistry = FEATURES
        self.pcd: PointCloudData = pcd
        self._raster_cache = DiskBackedImageStore(config=lazy_disk_cache_config)
        self._base_features: list[FeatureSpec] = []
        self._targets: list[FeatureSpec] = []

    def request(self, targets: str | list[str]) -> None:
        # Analyze which base features need to be rasterized for targets

        self._targets = []
        if isinstance(targets, str):
            targets = [targets]

        def visit(spec: FeatureSpec):
            if spec.name in self._raster_cache:
                return
            if issubclass(spec.cls, BaseFeatureStrategy):
                self._base_features.append(spec)
            for dep in spec.dependencies:
                dep_spec = self.registry.match(dep)
                visit(dep_spec)

        for t in targets:
            target_spec = self.registry.match(t)
            self._targets.append(target_spec)
            visit(target_spec)

    def available_features(self) -> list[str]:
        return list(self._raster_cache.keys())

    def get_base_features(self) -> dict[str, NDArray]:
        '''Returns base features needed for request which are not yet `self._raster_cache`'''
        base_features = {}
        for base_spec in self._base_features:
            inst = base_spec.cls(**base_spec.params)
            base_features[base_spec.name] = inst.compute(self.pcd, self._get)

        return base_features


    def submit(self, name: str, array: NDArray) -> None:
        self._raster_cache.add_image_to_store(name, array)

    def _get(self, name: str) -> DiskBackedImageData:
        if name in self._raster_cache:
            return self._raster_cache[name]
        self._compute(name)
        return self._raster_cache[name]

    def _compute(self, name: str) -> None:
        spec = self.registry.match(name)
        cls = spec.cls
        inst = cls(**spec.params)
        result = inst.compute(self.pcd, lambda n: np.asarray(self._get(n)))

        self.submit(name, result)


    def get_targets(self) -> dict[str, DiskBackedImageData]:
        results = {}
        for t in self._targets:
            results[t.name] = self._get(t.name)
        return results


    @property
    def cache_store(self) -> DiskBackedImageStore:
        return self._raster_cache
