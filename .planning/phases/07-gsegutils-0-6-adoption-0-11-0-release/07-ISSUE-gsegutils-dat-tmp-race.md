# Unpickling one DiskBackedStore in several processes at once races on a fixed `<key>.dat.tmp` name (0.6.0)

## Summary

Unpickling the same `DiskBackedStore` in several processes at the same time fails on 0.6.0. Every process rebuilds each entry's `<key>.dat` through one fixed temporary name, `<key>.dat.tmp`, so concurrent rebuilds of the same entry delete or replace each other's temporary file. The losing processes raise `FileNotFoundError` on `<key>.dat.tmp`, and in some runs a process is killed outright by `SIGBUS`. On 0.5.3, where the memmap was written in place, the same scenario never fails.

## Versions

- GSEGUtils 0.6.0 (from PyPI)
- Python 3.12.13, numpy 2.2.6
- Linux (WSL2, x86_64)

## Minimal reproduction

No dependency other than GSEGUtils and numpy. A store with three entries is pickled, then four spawned processes unpickle it at the same instant; this is repeated for twelve rounds.

```python
import multiprocessing as mp
import os
import pickle
import tempfile
import time
from pathlib import Path

import numpy as np


def child(blob_path, go_path, q):
    while not os.path.exists(go_path):  # crude start barrier
        pass
    try:
        pickle.loads(Path(blob_path).read_bytes())
        q.put("ok")
    except BaseException as e:
        q.put(f"{type(e).__name__}: {str(e)[:90]}")


if __name__ == "__main__":
    from GSEGUtils.lazy_disk_cache import (
        DiskBackedNDArray,
        DiskBackedStore,
        LazyDiskCacheConfig,
    )

    rounds, procs = 12, 4
    ctx = mp.get_context("spawn")
    bad = 0
    for _ in range(rounds):
        with tempfile.TemporaryDirectory() as td:
            cfg = LazyDiskCacheConfig(
                enable_caching=True, cache_path=Path(td), purge_disk_on_gc=False
            )
            s = DiskBackedStore[DiskBackedNDArray](
                config=cfg, factory=DiskBackedNDArray, value_type=DiskBackedNDArray
            )
            for k in ("a", "b", "c"):
                s.add_data_to_store(k, np.ones((400, 400), np.float32))
            blob = Path(td) / "state.pkl"
            blob.write_bytes(pickle.dumps(s))  # __getstate__ offloads to the codec pair
            go = Path(td) / "go"
            q = ctx.Queue()
            ps = [
                ctx.Process(target=child, args=(str(blob), str(go), q))
                for _ in range(procs)
            ]
            for p in ps:
                p.start()
            time.sleep(1.5)  # let the children import GSEGUtils, then release them together
            go.touch()
            for p in ps:
                p.join(timeout=60)
            res = []
            for p in ps:
                try:
                    res.append(q.get(timeout=1))
                except Exception:
                    res.append(f"child died without result (exitcode={p.exitcode})")
            bad += any(m != "ok" for m in res)
            for m in res:
                if m != "ok":
                    print("  ", m)
    print(f"rounds with at least one failing child: {bad}/{rounds}")
```

## Observed

- GSEGUtils 0.6.0: `rounds with at least one failing child: 12/12` (an earlier run of the same script gave 11/12). The failing children print, for example:

  ```
  FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmp9wiet09c/a.dat.tmp'
  ```

- The traceback in a failing child:

  ```
  DiskBackedStore.__setstate__            (disk_backed_store.py, self._store[key] = self._load_entry(key))
  DiskBackedStore._load_entry             (disk_backed_store.py, cls(arr, **reconstruct_kwargs))
  LazyDiskCache.__init__ -> _init_from_config -> _convert_to_memmap
  os.chmod(tmp_path, destination_mode)    (lazy_disk_cache.py, line 615)
  FileNotFoundError: ... '<key>.dat.tmp'
  ```

- In some runs a child never reports back. Earlier measurements on the same script showed children killed by `SIGBUS` (exit code -7); in the latest run one child exited without a result.
- GSEGUtils 0.5.3, same script, same machine: `rounds with at least one failing child: 0/12`.

## Root cause

`LazyDiskCache._convert_to_memmap` (0.6.0) writes the array to `get_memmap_tmp_path(cache_dir, key)`, which is always `<cache_dir>/<key>.dat.tmp`, then calls `os.chmod` on that temporary (when the destination already exists) and finally `os.replace(tmp, final)`.

When N processes unpickle one store, each runs this for every entry, against the same cache directory and therefore the same temporary name. One process's `os.replace` moves the shared temporary away while another is still about to `chmod` it (`FileNotFoundError`), or while another still has it memory-mapped and is writing into it (`SIGBUS`). The atomic-rename step is correct for one writer, but the name it renames from is shared by all writers.

## How it reaches a consumer

This is not exotic: any program that sends a store (or an object holding one) to several worker processes hits it. In pc2img, `TiledPointCloudImageGenerator.generate()` hands a bound method to joblib/loky, so every worker unpickles the whole generator, including every tile's store. In the runs measured here the first `generate()` succeeded and the second or third failed: once the stores hold `<key>.dat` files, every worker rebuilds them while unpickling, and the workers race. The visible symptom there is `BrokenProcessPool` ("A task has failed to un-serialize"). A downstream tracking issue will be linked in a comment.

## Suggested fix direction

Give every rebuild its own temporary name, for example `<key>.dat.<pid>-<random>.tmp`, built and containment-checked the same way as today, and keep `os.replace` as the atomic step (the last writer wins with identical content). Alternatives: serialise the rebuild of one entry with a lock file, or skip the rebuild when a valid `<key>.dat` of the right size already exists. A per-process unique name also keeps the crash-leftover story of the temporary intact, provided the removal verb knows the new naming pattern.
