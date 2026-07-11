from collections.abc import Callable
from functools import partial
from typing import Any, Unpack

import numpy as np
from GSEGUtils.lazy_disk_cache import (
    DiskBackedNDArray,
    LazyDiskCache,
    LazyDiskCacheKw,
)
from numpy.typing import NDArray

from pc2img.util import convert_to_image


class DiskBackedImageData(DiskBackedNDArray):
    """Disk-backed raster: a thin ``DiskBackedNDArray`` with an image-shape guard.

    Reparented onto :class:`GSEGUtils.lazy_disk_cache.DiskBackedNDArray` (D-04):
    the working ``__array_ufunc__`` (unwrap -> delegate -> plain ndarray), the
    ``__array__`` / ``__getitem__`` / ``data`` accessors and the offload/load
    buffer hooks are all inherited. This class only adds the ``ndim in (2, 3)``
    (single- or 3-channel) shape assertion and the :meth:`to_uint8` conversion.
    """

    def __init__(
        self,
        image_data: np.ndarray,
        **lazy_disk_cache_settings: Unpack[LazyDiskCacheKw],
    ):
        assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3)
        super().__init__(image_data, **lazy_disk_cache_settings)

    @LazyDiskCache.ensure_loaded
    def to_uint8(
        self,
        pre_processing_func: Callable[[NDArray[np.floating[Any]]], NDArray[np.uint8]] | None = None,
    ) -> NDArray[np.uint8]:

        if pre_processing_func is None:
            pre_processing_func = partial(convert_to_image, replace_nan_with="max", normalize=False)
        return pre_processing_func(self._data)
