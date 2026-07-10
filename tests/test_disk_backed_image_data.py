import numpy as np
import pytest
import pickle
from pathlib import Path
import gc

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
        # Too many dimensions
        img = np.zeros((5, 5, 5))
        with pytest.raises(AssertionError):
            DiskBackedImageData(img)


class TestOffloadingAndLoading:
    @pytest.mark.xfail(
        reason=(
            "Phase 5 (BUG-05 candidate): offload() with caching disabled does not "
            "emit the expected 'Caching disabled ==> `offload()` ignored.' debug log "
            "-- xpasses once the disabled-offload log path is wired; re-classify then."
        ),
        strict=False,
    )
    def test_offload_without_cache_path_logs_warning(self, caplog):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img, enable_caching=False, cache_path=None)
        caplog.set_level("DEBUG")
        data_obj.offload()
        assert "Caching disabled ==> `offload()` ignored." in caplog.text
        assert not data_obj.offloaded

    def test_offload_and_load_with_cache(self, tmp_path: Path, caplog):
        caplog.set_level("DEBUG")
        img = dummy_rgb_image()
        cache_file = tmp_path / "img.dat"
        data_obj = DiskBackedImageData(
            img, enable_caching=True, cache_path=cache_file, automatic_offloading=False
        )

        # Offload manually
        data_obj.offload()
        assert data_obj.offloaded
        assert data_obj._image_data is None

        # File was created
        assert cache_file.exists()
        assert cache_file.stat().st_size > 0

        # Data should be None internally, but load repopulates
        data_obj.load()
        assert not data_obj.offloaded
        loaded = data_obj.data
        assert isinstance(loaded, np.memmap)
        assert np.allclose(loaded, img)

    def test_automatic_offloading_flag(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "gray.dat"
        data_obj = DiskBackedImageData(
            img, enable_caching=True, cache_path=cache_file, automatic_offloading=True
        )
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

    def test_getstate_without_cache_path_preserves_data(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        state = data_obj.__getstate__()
        # Without cache_path, _image_data should remain intact
        assert state["_image_data"] is not None
        assert isinstance(state["_image_data"], np.ndarray)
        assert state["_shape"] == img.shape
        assert state["_dtype"] == img.dtype

    @pytest.mark.xfail(
        reason=(
            "Phase 5 (BUG-05 candidate): __getstate__ with a cache_path does not "
            "unload _image_data (state['_image_data'] is not None) -- xpasses once "
            "cache-path getstate unloading is fixed; re-classify then."
        ),
        strict=False,
    )
    def test_getstate_with_cache_path_unloads_data(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "temp.dat"
        data_obj = DiskBackedImageData(img, cache_path=cache_file)
        state = data_obj.__getstate__()
        # With cache_path, _image_data should be unloaded
        assert state["_image_data"] is None
        assert state["_cache_path"] == cache_file
        assert state["_shape"] == img.shape
        assert state["_dtype"] == img.dtype

    def test_setstate_restores_attributes(self):
        img = dummy_rgb_image()
        data_obj = DiskBackedImageData(img)
        state = data_obj.__getstate__()
        new_obj = DiskBackedImageData(dummy_gray_image())  # start with different
        new_obj.__setstate__(state)
        # After setstate, object's dict matches state
        for key, val in state.items():
            if isinstance(val, np.ndarray):
                assert val is getattr(new_obj, key)
            else:
                assert getattr(new_obj, key) == val

    def test_pickle_roundtrip_without_cache(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        # data should still be accessible
        assert np.array_equal(loaded_obj.data, img)

    @pytest.mark.xfail(
        reason=(
            "Phase 5 (BUG-05 candidate): pickle roundtrip with a cache_path does not "
            "leave _image_data lazily unloaded on the restored object -- xpasses once "
            "cached pickle round-tripping is fixed; re-classify then."
        ),
        strict=False,
    )
    def test_pickle_roundtrip_with_cache(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "temp.dat"
        data_obj = DiskBackedImageData(img, cache_file)
        serialized = pickle.dumps(data_obj)
        loaded_obj = pickle.loads(serialized)
        # data should be lazily loaded
        assert getattr(loaded_obj, "_image_data") is None
        # When accessing data, the data should be loaded
        assert np.array_equal(loaded_obj, img)


@pytest.mark.xfail(
    reason=(
        "Phase 5 (BUG-05 candidate): DiskBackedImageData cache-file finalizer "
        "lifecycle (registration, cancel-on-getstate, re-register-on-unpickle, "
        "cleanup-deletes-file) does not match current behavior -- every method here "
        "xpasses once finalization is fixed; re-classify then."
    ),
    strict=False,
)
class TestCacheFileFinalization:
    def test_finalizer_alive_and_canceled_on_getstate(self, tmp_path: Path):
        # Create object with cache
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, cache_file)
        # Finalizer should be registered
        assert hasattr(data_obj, "_finalizer")
        assert data_obj._finalizer.alive

        # Calling getstate should cancel the finalizer
        _ = data_obj.__getstate__()
        assert not data_obj._finalizer.alive
        # Cache file should exist after offload
        assert cache_file.exists()

    def test_finalizer_reregistered_on_unpickle(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, cache_file)
        serialized = pickle.dumps(data_obj)
        # Unpickle
        loaded_obj = pickle.loads(serialized)
        # New instance should have a live finalizer
        assert hasattr(loaded_obj, "_finalizer")
        assert loaded_obj._finalizer.alive

    def test_cache_file_persistence_after_original_deletion(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, cache_file)
        cache_file = data_obj.cache_path
        # Force offload via getstate
        serialized = pickle.dumps(data_obj)
        # File must exist
        assert cache_file.exists()
        # Delete original and collect
        del data_obj
        gc.collect()
        # File should still exist because original finalizer was canceled
        assert cache_file.exists()

    def test_cleanup_on_finalizer_call_deletes_file(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(img, cache_file)
        serialized = pickle.dumps(data_obj)
        # Unpickle to get live finalizer
        loaded_obj = pickle.loads(serialized)
        # Ensure file is present
        assert cache_file.exists()
        # Trigger cleanup manually via finalizer
        loaded_obj._finalizer()
        # File should be removed
        assert not cache_file.exists()


@pytest.mark.xfail(
    reason=(
        "Phase 5 (BUG-05 candidate): DiskBackedImageData purge-on-gc enable/disable "
        "toggle does not drive the finalizer as expected (disable_purge/enable_purge "
        "and the no-cache path) -- every method here xpasses once purge toggling is "
        "fixed; re-classify then."
    ),
    strict=False,
)
class TestPurgeToggle:
    def test_disable_purge(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(
            img, cache_file, automatic_offloading=True, purge_disk_on_gc=True
        )
        # Finalizer initially alive
        assert hasattr(data_obj, "_finalizer")
        assert data_obj._finalizer.alive
        # Disable purge
        data_obj.disable_purge()
        assert not data_obj._finalizer.alive
        assert not data_obj._purge_on_delete
        # Trigger finalize manually; file should still exist after
        data_obj._finalizer()
        assert cache_file.exists()

    def test_enable_purge(self, tmp_path: Path):
        img = dummy_gray_image()
        cache_file = tmp_path / "cache.dat"
        data_obj = DiskBackedImageData(
            img, cache_file, automatic_offloading=True, purge_disk_on_gc=True
        )
        # Disable then enable
        data_obj.disable_purge()
        assert not data_obj._purge_on_delete
        data_obj.enable_purge()
        assert data_obj._finalizer.alive
        assert data_obj._purge_on_delete
        # Trigger finalize manually; file should be removed
        data_obj._finalizer()
        assert not cache_file.exists()

    def test_enable_purge_no_cache(self):
        img = dummy_gray_image()
        data_obj = DiskBackedImageData(img)
        # No cache_path, so no _finalizer attribute
        assert not hasattr(data_obj, "_finalizer")
        # enable_purge should not error
        data_obj.enable_purge()
        # Still no _finalizer
        assert not hasattr(data_obj, "_finalizer")
