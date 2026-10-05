# A released entry's purge-on-gc deletes `<key>.dat` that another live store copy still uses (0.6.0)

## Summary

With `purge_disk_on_gc=True` (the default), every `DiskBackedNDArray` entry deletes its `<key>.dat` memmap when it is garbage-collected. When a store has been pickled and unpickled, the copy's entry uses the same `<cache_dir>/<key>.dat` path as the original's. If the original is read again after pickling and is then released, its entry deletes the file the copy still relies on, and the copy fails with `FileNotFoundError` the next time it reads from disk. This happens in a single process, with no concurrency involved; it is independent of #82.

## Versions

- GSEGUtils 0.6.0 (from PyPI)
- Python 3.12.13, numpy 2.2.6
- Linux (WSL2, x86_64)

## Minimal reproduction

```python
import gc
import pickle
import tempfile
from pathlib import Path

import numpy as np

from GSEGUtils.lazy_disk_cache import DiskBackedNDArray, DiskBackedStore, LazyDiskCacheConfig

td = Path(tempfile.mkdtemp())
cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=td)  # purge_disk_on_gc defaults to True
a = DiskBackedStore[DiskBackedNDArray](config=cfg, factory=DiskBackedNDArray, value_type=DiskBackedNDArray)
a.add_data_to_store("k", np.ones((50, 50), np.float32))

b = pickle.loads(pickle.dumps(a))  # a second store whose entry uses the same k.dat
np.asarray(a["k"])  # the original is used again after pickling

del a
gc.collect()  # the original's entry deletes k.dat

b.offload()
np.asarray(b["k"])  # FileNotFoundError: .../k.dat
```

## Observed

- `FileNotFoundError` on `<cache_dir>/k.dat` in 3 of 3 runs; `k.dat` no longer exists after `gc.collect()`.
- Before `b.offload()`, `b["k"]` still reads correctly from memory, so the loss only shows on the next read from disk.
- Without the read of `a["k"]` after pickling, `k.dat` survives and the copy reads fine (pickling the original alone does not trigger it).

## Expected

Releasing one store must not delete a file that another live entry still maps. Either the copy owns its own file, or the file is removed only when no live entry uses it.

## Root cause

The finalizer registered for an entry deletes the path derived from the key, `<cache_dir>/<key>.dat`, unconditionally. Unpickling rebuilds an entry on that same derived path, so two live entries share one file while each believes it alone owns it.

## Suggested fix direction

Make the finalizer delete only a file its own entry created: for example a per-entry file name (`<key>.<token>.dat`) recorded in the entry, or an ownership token checked before unlinking. A per-entry name would also remove the shared temporary name behind #82.

---

Filed: https://github.com/gseg-ethz/GSEGUtils/issues/83 (owner-approved text, 2026-10-05; read-back identical).
