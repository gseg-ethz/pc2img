"""Behaviour tests for the reparented ``DiskBackedImageData``.

After the reparent onto ``GSEGUtils.lazy_disk_cache.DiskBackedNDArray``,
the private buffer is ``self._data`` and the offload/load, pickle, finalizer and
purge machinery is inherited from ``LazyDiskCache``. These tests assert the
inherited contract directly against the renamed private attribute.

Arithmetic lives in ``tests/test_image_store.py``, not here.
"""

import gc
import pickle
from pathlib import Path

import numpy as np
import pytest

from pc2img.image_cache import DiskBackedImageData


def dummy_gray_image(shape=(10, 10), dtype=np.float32):
    """Create a dummy grayscale image array."""
    return np.random.rand(*shape).astype(dtype)


def dummy_rgb_image(shape=(8, 8, 3), dtype=np.float64):
    """Create a dummy RGB image array."""
    return np.random.rand(*shape).astype(dtype)


class TestImageDataInitialization:
    def test_init_with_gray_image(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(
            img,
            enable_caching=False,
            cache_path=None,
            automatic_offloading=False,
            purge_disk_on_gc=False,
        )
        assert np.array_equal(data_obj.data, img)
        assert not data_obj.cache_enabled
        assert not data_obj.offloaded
        assert data_obj.cache_path is not None
        assert not data_obj.automatic_offloading

    def test_init_with_rgb_image(self):
        img = dummy_rgb_image()
        data_obj = DiskBackedImageData(img)
        assert np.array_equal(data_obj.data, img)
        assert data_obj.data.shape == img.shape

    def test_init_invalid_dimensions(self):
        # Too many dimensions / non-3 channel count
        img = np.zeros((5, 5, 5))
        with pytest.raises(AssertionError):
            DiskBackedImageData(img)


class TestToUint8:
    def test_to_uint8_reads_data_buffer(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        out = data_obj.to_uint8()
        assert out.dtype == np.uint8
        assert out.shape[:2] == img.shape[:2]

    def test_to_uint8_after_offload_reloads(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "img.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, automatic_offloading=False)
        data_obj.offload()
        assert data_obj.offloaded
        out = data_obj.to_uint8()
        assert out.dtype == np.uint8


class TestOffloadingAndLoading:
    def test_offload_without_caching_is_ignored_and_logged(self, caplog):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img, enable_caching=False, cache_path=None)
        caplog.set_level("INFO")
        data_obj.offload()
        # Inherited LazyDiskCache.offload() logs a caching-disabled notice and no-ops.
        assert "Caching disabled" in caplog.text
        assert "`offload()` ignored" in caplog.text
        assert not data_obj.offloaded

    def test_offload_and_load_with_cache(self, tmp_path: Path):
        img = dummy_rgb_image()
        cache_file = tmp_path / "img.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, automatic_offloading=False)

        # Offload manually — inherited _drop_buffer() deletes the in-memory buffer.
        data_obj.offload()
        assert data_obj.offloaded
        assert not hasattr(data_obj, "_data")

        # File was created
        assert cache_file.exists()
        assert cache_file.stat().st_size > 0

        # Loading repopulates the buffer from the memmap.
        data_obj.load()
        assert not data_obj.offloaded
        loaded = data_obj.data
        assert isinstance(loaded, np.memmap)
        assert np.allclose(loaded, img)

    def test_automatic_offloading_flag(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "gray.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, automatic_offloading=True)
        # Should have offloaded at init
        assert data_obj.offloaded
        assert data_obj.automatic_offloading


class TestArrayInterfaceAndPickling:
    def test_array_protocol(self):
        img = dummy_rgb_image()
        data_obj = DiskBackedImageData(img)
        arr = np.array(data_obj)
        assert isinstance(arr, np.ndarray)
        assert np.array_equal(arr, img)

    def test_getstate_without_caching_preserves_data(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)  # enable_caching defaults to False
        state = data_obj.__getstate__()
        # Without caching there is no offload, so the buffer is preserved in-state.
        assert state["_data"] is not None
        assert isinstance(state["_data"], np.ndarray)
        assert state["_shape"] == img.shape
        assert state["_dtype"] == img.dtype

    def test_getstate_with_caching_unloads_data(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "temp.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file)
        state = data_obj.__getstate__()
        # With caching enabled, inherited __getstate__ offloads -> buffer dropped.
        assert state.get("_data") is None
        assert state["_shape"] == img.shape
        assert state["_dtype"] == img.dtype

    def test_setstate_restores_attributes(self):
        img = dummy_rgb_image()
        data_obj = DiskBackedImageData(img)
        state = data_obj.__getstate__()
        new_obj = DiskBackedImageData(dummy_gray_image())  # start with different
        new_obj.__setstate__(state)
        # After setstate, restored data matches.
        assert np.array_equal(new_obj.data, img)
        assert new_obj._shape == img.shape
        assert new_obj._dtype == img.dtype

    def test_pickle_roundtrip_without_cache(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        # data should still be accessible
        assert np.array_equal(loaded_obj.data, img)

    def test_pickle_roundtrip_with_cache(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "temp.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        # With caching, the restored object is lazily offloaded until first access.
        assert loaded_obj.offloaded
        # Accessing the data reloads it from the memmap.
        assert np.allclose(np.asarray(loaded_obj), img)


class TestCacheFileFinalization:
    def test_finalizer_alive_and_canceled_on_getstate(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, purge_disk_on_gc=True)
        # Finalizer should be registered and alive
        assert hasattr(data_obj, "_finalizer")
        assert data_obj._finalizer.alive

        # Calling getstate should cancel the finalizer (disable_purge detaches it)
        _ = data_obj.__getstate__()
        assert not data_obj._finalizer.alive
        # Cache file should exist after offload
        assert cache_file.exists()

    def test_finalizer_reregistered_on_unpickle(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, purge_disk_on_gc=True)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        # Restored instance re-registers a live finalizer (the enable_purge path).
        assert hasattr(loaded_obj, "_finalizer")
        assert loaded_obj._finalizer.alive

    def test_cache_file_persistence_after_original_deletion(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, purge_disk_on_gc=True)
        # getstate cancels the original finalizer
        _ = pickle.dumps(data_obj)
        assert cache_file.exists()
        # Delete original and collect
        del data_obj
        gc.collect()
        # File should still exist because the original finalizer was canceled
        assert cache_file.exists()

    def test_cleanup_on_finalizer_call_deletes_file(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, enable_caching=True, cache_path=cache_file, purge_disk_on_gc=True)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        assert cache_file.exists()
        # Trigger cleanup manually via the re-registered finalizer
        loaded_obj._finalizer()
        assert not cache_file.exists()


class TestPurgeToggle:
    def test_disable_purge(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(
            img, enable_caching=True, cache_path=cache_file, automatic_offloading=True, purge_disk_on_gc=True
        )
        assert hasattr(data_obj, "_finalizer")
        assert data_obj._finalizer.alive
        # Disable purge — inherited flag is _purge_disk_on_gc
        data_obj.disable_purge()
        assert not data_obj._finalizer.alive
        assert not data_obj.purge_disk_on_gc
        # Trigger the (detached) finalizer manually; file should still exist
        data_obj._finalizer()
        assert cache_file.exists()

    def test_enable_purge(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(
            img, enable_caching=True, cache_path=cache_file, automatic_offloading=True, purge_disk_on_gc=True
        )
        # Disable then re-enable
        data_obj.disable_purge()
        assert not data_obj.purge_disk_on_gc
        data_obj.enable_purge()
        assert data_obj._finalizer.alive
        assert data_obj.purge_disk_on_gc
        # Trigger finalize manually; file should be removed
        data_obj._finalizer()
        assert not cache_file.exists()

    def test_enable_purge_is_safe_without_explicit_cache_path(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        # A temp cache_path is always assigned by LazyDiskCache, so enable_purge
        # is a safe, idempotent no-error operation.
        data_obj.enable_purge()
        assert data_obj.purge_disk_on_gc
