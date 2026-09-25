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


def _assert_image_shape(image_data: np.ndarray) -> None:
    """Assert ``image_data`` is a single-channel 2-D or 3-channel (H, W, 3) raster.

    The single source of the raster-shape rule: both :meth:`DiskBackedImageData.__init__`
    and the store's overwrite path (:class:`pc2img.image_cache.disk_backed_image_store.DiskBackedImageStore`)
    call this helper rather than duplicating the condition, so the rule cannot
    drift between the two call sites. The exception type is deliberately
    ``AssertionError`` — an internal-invariant signal, not user-input
    validation — and stays pinned: changing it would be a breaking-change
    event this helper's extraction does not open.
    """
    assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3), (
        f"image_data must be 2-D or (H, W, 3); got shape {image_data.shape}"
    )


class DiskBackedImageData(DiskBackedNDArray):
    """Disk-backed raster: a thin ``DiskBackedNDArray`` with an image-shape guard.

    Reparented onto :class:`GSEGUtils.lazy_disk_cache.DiskBackedNDArray` (D-04):
    the working ``__array_ufunc__`` (unwrap -> delegate -> plain ndarray), the
    ``__array__`` / ``__getitem__`` / ``data`` accessors and the offload/load
    buffer hooks are all inherited. This class only adds the single- or
    3-channel raster-shape assertion (via the module-level
    :func:`_assert_image_shape` helper) and the :meth:`to_uint8` conversion.
    """

    def __init__(
        self,
        image_data: np.ndarray,
        **lazy_disk_cache_settings: Unpack[LazyDiskCacheKw],
    ):
        _assert_image_shape(image_data)
        super().__init__(image_data, **lazy_disk_cache_settings)

    @LazyDiskCache.ensure_loaded
    def to_uint8(
        self,
        pre_processing_func: Callable[[NDArray[np.floating[Any]]], NDArray[np.uint8]] | None = None,
    ) -> NDArray[np.uint8]:

        if pre_processing_func is None:
            pre_processing_func = partial(convert_to_image, replace_nan_with="max", normalize=False)
        return pre_processing_func(self._data)
