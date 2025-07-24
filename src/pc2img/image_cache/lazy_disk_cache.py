from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
import threading
from typing import Optional, Any
import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

class LazyDiskCache(ABC):
    _MEMMAP_SUFFIX = ".dat"

    def __init__(self,
                 cache_path: Optional[Path] = None,
                 automatic_offloading: bool = False) -> None:
        self._cache_path = cache_path.with_suffix(self._MEMMAP_SUFFIX) if cache_path else None
        self._automatic_offloading = automatic_offloading and (cache_path is not None)
        self._lock = threading.RLock()
        # track in-memory state
        self._in_memory = True
        if automatic_offloading:
            self.offload()

    @staticmethod
    def ensure_loaded(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            was_offloaded = self.offloaded
            if was_offloaded:
                self.load()
            result = func(self, *args, **kwargs)
            if self.automatic_offloading and was_offloaded:
                self.offload()
            return result
        return wrapper

    @property
    def offloaded(self) -> bool:
        return not self._in_memory

    @property
    def automatic_offloading(self) -> bool:
        return self._automatic_offloading

    @automatic_offloading.setter
    def automatic_offloading(self, value: bool):
        assert isinstance(value, bool)
        self._automatic_offloading = value

    @property
    def cache_path(self) -> Optional[Path]:
        return self._cache_path

    def offload(self) -> None:
        """Write in-memory buffer to disk and drop it from RAM."""
        with self._lock:
            if not self._cache_path:
                logger.warning("No cache_path: offload() ignored")
                return
            if self.offloaded:
                return

            shape, dtype, array = self._describe_buffer()
            # ensure directory
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            memmap = np.memmap(self._cache_path, dtype=dtype, mode="w+", shape=shape)
            memmap[:] = array
            memmap.flush()
            self._drop_buffer()
            self._in_memory = False
            # hook for pruning or cleaning resources
            try:
                self.on_offload()
            except Exception:
                logger.exception("Error in on_offload hook")
            logger.debug(f"Offloaded buffer to {self._cache_path}")

    def load(self, mode: str = "r+") -> None:
        """Load (or reload) the buffer from disk into memory."""
        with self._lock:
            if self.offloaded and self._cache_path:
                shape, dtype = self._describe_shape_dtype()
                buf = np.memmap(self._cache_path, dtype=dtype, mode=mode, shape=shape)
                self._set_buffer(buf)
                self._in_memory = True
                # hook for cleanup after load
                try:
                    self.on_load()
                except Exception:
                    logger.exception("Error in on_load hook")
                logger.debug(f"Loaded buffer from {self._cache_path}")

    def __getstate__(self):
        if self.cache_path:
            self.offload()
        state = self.__dict__.copy()
        state.pop("_lock", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.RLock()


    @abstractmethod
    def _describe_buffer(self) -> tuple[tuple[int, ...], Any, np.ndarray]:
        """Return (shape, dtype, in-memory array)"""
        ...

    @abstractmethod
    def _drop_buffer(self) -> None:
        """Drop the in-memory array (e.g. set to None or similar)"""
        ...

    @abstractmethod
    def _describe_shape_dtype(self) -> tuple[tuple[int, ...], Any]:
        """Return (shape, dtype) without accessing the full array"""
        ...

    @abstractmethod
    def _set_buffer(self, buf: np.ndarray) -> None:
        """Given a memmap, restore it into your object"""
        ...

    # Optional hooks subclasses can override
    def on_offload(self) -> None:
        """Hook called after offloading to disk. Use to prune resources."""
        pass

    def on_load(self) -> None:
        """Hook called after loading into memory. Use to cleanup or reinitialize."""
        pass