import tempfile
from collections.abc import MutableMapping
import logging
from pathlib import Path
import pickle
from typing import Dict, Iterator, Optional, Union, Any, Unpack, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import validate_call, ConfigDict

from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

from .disk_backed_image_data import DiskBackedImageData


logger = logging.getLogger(__name__.split(".")[0])

class DiskBackedImageStore(MutableMapping[str, DiskBackedImageData]):

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
            self,
            *,
            config: LazyDiskCacheConfig = LazyDiskCacheConfig(),
    ) -> None:

        self._data: Dict[str, Optional[DiskBackedImageData]] = {}
        self._enable_caching = config.enable_caching
        if config.cache_path is None or config.cache_path.is_file():
            self._cache_dir = Path(tempfile.mkdtemp())
        else:
            self._cache_dir = config.cache_path
        self._automatic_offloading = config.automatic_offloading and config.cache_path is not None
        self._purge_disk_on_gc = config.purge_disk_on_gc

        if self._cache_dir is not None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            # Scan for existing pkl files
            available_files = [f for f in self._cache_dir.glob("*.pkl") if f.is_file()]
            for f in available_files:
                self._data[f.stem] = None


    def __getitem__(self, key: str) -> DiskBackedImageData:
        obj = self._data.get(key, None)
        if obj is not None:
            return obj

        try:
            with open(self._get_pickle_path(key), "rb") as f:
                loaded_obj = cast(DiskBackedImageData, pickle.load(f))
        except FileNotFoundError:
            raise KeyError(key)

        self._data[key] = loaded_obj
        return loaded_obj


    def __setitem__(self, key: str, value: DiskBackedImageData) -> None:
        if not isinstance(value, DiskBackedImageData):
            raise TypeError(f"Value must be an ImageData, got {type(value)}.")
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"ImageStack({list(self._data.keys())})"

    def _get_pickle_path(self, feature: str) -> Path:
        return self._cache_dir / f"{feature}.pkl"

    def add_image_to_store(
            self,
            img_name: str,
            img_data: NDArray,
            *,
            enable_caching_override: Optional[bool] = None,
            automatic_offloading_override: Optional[bool] = None,
            purge_disk_on_gc_override: Optional[bool] = None,
    ) -> None:

        self._data[img_name] = DiskBackedImageData(
            img_data,
            enable_caching=enable_caching_override if enable_caching_override is not None else self._enable_caching,
            cache_path=self._cache_dir / f"{img_name}.pkl" if self._cache_dir else None,
            automatic_offloading=automatic_offloading_override if automatic_offloading_override is not None else self._automatic_offloading,
            purge_disk_on_gc=purge_disk_on_gc_override if purge_disk_on_gc_override is not None else self._purge_disk_on_gc
        )

    # def fetch_image(self, feature: str) -> None:
    #     image_data_cache_path = self._get_pickle_path(feature) if self._cache_dir else None
    #     if image_data_cache_path and image_data_cache_path.is_file():
    #         with open(image_data_cache_path, "rb") as f:
    #             self._data[feature] = pickle.load(f)
    #         logger.debug(f"Loaded ImageData for {feature=} from {image_data_cache_path}")
    #         return
    #
    #     if isinstance(self._image_generator, ImageGeneratorFromPCD):
    #         self._create_image_from_pcd(feature, image_data_cache_path)
    #     else:
    #         logger.error("Not implemented")
    #         raise NotImplementedError
    #
    # def _create_image_from_pcd(self, feature: str, image_data_path: Optional[Path]) -> None:
    #     image_generator: ImageGeneratorFromPCD = self._image_generator
    #     image_data: dict[str, NDArray[np.generic]] = image_generator.project_and_rasterize(feature)
    #     if image_data is None:
    #         logger.warning(f"PointCloudData has no scalar feature {feature} available.")
    #         return
    #     self._data[feature] = DiskBackedImageData(image_data[feature], image_data_path, self._automatic_offloading)

    @property
    def image_data(self) -> dict[str, Optional[DiskBackedImageData]]:
        return self._data

    @property
    def cache_dir(self) -> Optional[Path]:
        return self._cache_dir


    # @property
    # def identifier(self) -> str:
    #     return self._image_generator.identifier
    #
    # def __repr__(self):
    #     return f"Factory for {self.identifier} with available images for {list(self._data.keys())}"

    def keys(self) -> list[str]:
        """
        Returns a list of all available image keys.
        """
        return list(self._data.keys())

    def values(self) -> Iterator[DiskBackedImageData]:
        return iter(self._data.values())

    def items(self) -> Iterator[tuple[str, DiskBackedImageData]]:
        return iter(self._data.items())

    def offload(self, features: Optional[str | list[str]] = None) -> None:
        if self._cache_dir is None:
            logger.warning(f"Without cache_dir, the offload function is ignored!")
            return

        if features is None:
            features = self.keys()
        if isinstance(features, str):
            features = [features]

        for feature in features:
            obj = self._data[feature]
            if obj is None:
                continue
            obj.offload()

    def offload_image_data_to_disk(self, features: Optional[str | list[str]] = None) -> None:
        if self._cache_dir is None:
            logger.warning(f"Without cache_dir, the pickle_image_data function is ignored!")
            return

        if features is None:
            features = self.keys()
        if isinstance(features, str):
            features = [features]

        for feature in features:
            if self._data[feature] is None:
                continue
            with open(self._get_pickle_path(feature), "wb") as f:
                pickle.dump(self._data[feature], f)
            logger.debug(f"Pickled ImageData for {feature=} to {self._get_pickle_path(feature)}")
            self._data[feature] = None

    def __getstate__(self) -> dict[str, Any]:
        if self._enable_caching:
            self.offload_image_data_to_disk()
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        if self._enable_caching:
            for feature in self.keys():
                if self._data[feature] is not None:
                    continue
                with open(self._get_pickle_path(feature), "rb") as f:
                    self._data[feature] = pickle.load(f)
