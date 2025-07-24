from functools import partial
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Optional, Any

import numpy as np
from numpy.typing import NDArray

from .lazy_disk_cache import LazyDiskCache
from ..util import convert_to_image


class DiskBackedImageData(LazyDiskCache):
    def __init__(self,
                 image_data: np.ndarray,
                 cache_path: Optional[Path] = None,
                 automatic_offloading: bool = False):
        assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3)
        self._image_data = image_data
        self._shape = image_data.shape
        self._dtype = image_data.dtype
        super().__init__(cache_path, automatic_offloading)

    @property
    @LazyDiskCache.ensure_loaded
    def data(self):
        if self.offloaded:
            self.load()
        return self._image_data

    @LazyDiskCache.ensure_loaded
    def to_uint8(
            self,
            pre_processing_func: Optional[Callable[
                [NDArray[np.floating[Any]]],
                NDArray[np.uint8]]
            ] = None) -> NDArray[np.uint8]:

        if pre_processing_func is None:
            pre_processing_func = partial(convert_to_image, replace_nan_with="max", normalize=False)
        return pre_processing_func(self._image_data)


    def __array__(self) -> NDArray[np.floating]:
        return self.data

    def _describe_buffer(self):
        return self._shape, self._dtype, self._image_data

    def _drop_buffer(self):
        self._image_data = None

    def _describe_shape_dtype(self):
        return self._shape, self._dtype

    def _set_buffer(self, buf: np.ndarray):
        self._image_data = buf
