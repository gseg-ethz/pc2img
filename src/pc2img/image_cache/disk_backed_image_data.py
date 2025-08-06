from functools import partial
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Optional, Any, Unpack

import numpy as np
from numpy.typing import NDArray
from numpy.lib.mixins import NDArrayOperatorsMixin

from GSEGUtils.lazy_disk_cache import LazyDiskCache, LazyDiskCacheConfig, LazyDiskCacheKw

from pc2img.util import convert_to_image


class DiskBackedImageData(LazyDiskCache, NDArrayOperatorsMixin):
    __array_priority__ = 1000

    def __init__(
            self,
            image_data: np.ndarray,
            **lazy_disk_cache_settings: Unpack[LazyDiskCacheKw],
     ):
        assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3)
        self._image_data = image_data
        self._shape = image_data.shape
        self._dtype = image_data.dtype
        super().__init__(
            **lazy_disk_cache_settings
        )

    @property
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


    @LazyDiskCache.ensure_loaded
    def __array__(self, dtype=None, *, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported. A copy is always created.")

        arr = self._image_data
        return arr.astype(dtype, copy=True) if dtype else arr.copy()

    # def _derive_cache_path(self) -> Optional[Path]:
    #     """
    #     Generate a new cache_path in the same directory,
    #     based on the original filename + a UUID suffix.
    #     Returns None if there was no original cache_path.
    #     """
    #     if not self.cache_path:
    #         return None
    #     base = self.cache_path.with_suffix("").name
    #     new_name = f"{base}_{uuid.uuid4().hex}{self._MEMMAP_SUFFIX}"
    #     return self.cache_path.parent / new_name

    # @LazyDiskCache.ensure_loaded
    # def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    #     # unwrap and handle 'out' exactly as before…
    #     # [your existing unwrapping + out=… code]
    #
    #     # call the ufunc on raw arrays
    #     result = getattr(ufunc, method)(*raw_inputs, **kwargs, **out_kwargs)
    #
    #     # in-place case
    #     if out_kwargs:
    #         return outs if len(outs) > 1 else outs[0]
    #
    #     # copy-on-write: give derivative its own cache file
    #     new_cache = self._derive_cache_path()
    #
    #     def wrap(arr):
    #         return DiskBackedImageData(
    #             arr,
    #             cache_path=new_cache,
    #             automatic_offloading=self.automatic_offloading,
    #             purge_on_delete=True,
    #         )
    #
    #     if isinstance(result, tuple):
    #         return tuple(wrap(r) for r in result)
    #     else:
    #         return wrap(result)

    def _describe_buffer(self):
        return self._shape, self._dtype, self._image_data

    def _drop_buffer(self):
        self._image_data = None

    def _describe_shape_dtype(self):
        return self._shape, self._dtype

    def _set_buffer(self, buf: NDArray):
        self._image_data = buf
