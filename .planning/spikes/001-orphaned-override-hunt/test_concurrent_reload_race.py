"""Spike 001, part C — SURPRISE: concurrent store reload races on the fixed ``<key>.dat.tmp`` name.

Found while running the tiled generator against the 0.6.0 wheel: a *second or later*
``TiledPointCloudImageGenerator.generate()`` (>= 2 tiles, n_jobs >= 2) fails in the loky workers
with ``BrokenProcessPool`` / ``TerminatedWorkerError``. The worker-side traceback is
``DiskBackedStore.__setstate__ -> _load_entry -> LazyDiskCache._convert_to_memmap ->
os.chmod(<key>.dat.tmp): FileNotFoundError``: every worker unpickles the *whole* generator
(``self._process_tile`` is a bound method, and ``self.image_generators`` holds every tile's
store) and re-creates each entry's ``.dat`` through ONE shared ``<key>.dat.tmp`` name that
0.6.0 introduced for atomic writes. Two processes reloading the same entry race that name.

This script reproduces it with GSEGUtils alone (no pc2img): N processes unpickle the same
store simultaneously.  Expectation on 0.6.0: some rounds fail with FileNotFoundError.

Run:  <venv>/bin/python test_concurrent_reload_race.py [rounds] [procs]
"""

from __future__ import annotations

import multiprocessing as mp
import os
import pickle
import sys
import tempfile
import time
from pathlib import Path

import numpy as np


def _child(blob_path: str, go_path: str, q) -> None:
    while not os.path.exists(go_path):  # crude start barrier
        pass
    try:
        pickle.loads(Path(blob_path).read_bytes())
        q.put("ok")
    except BaseException as e:  # noqa: BLE001
        q.put(f"{type(e).__name__}: {str(e)[:90]}")


if __name__ == "__main__":
    import GSEGUtils
    from GSEGUtils.lazy_disk_cache import DiskBackedNDArray, DiskBackedStore, LazyDiskCacheConfig

    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    print(f"GSEGUtils {GSEGUtils.__version__} ({Path(GSEGUtils.__file__).parent})")
    ctx = mp.get_context("spawn")
    bad = 0
    msgs: dict[str, int] = {}
    for r in range(rounds):
        with tempfile.TemporaryDirectory() as td:
            cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=Path(td), purge_disk_on_gc=False)
            s = DiskBackedStore[DiskBackedNDArray](config=cfg, factory=DiskBackedNDArray, value_type=DiskBackedNDArray)
            for k in ("a", "b", "c"):
                s.add_data_to_store(k, np.ones((400, 400), np.float32))
            blob = Path(td) / "state.pkl"
            blob.write_bytes(pickle.dumps(s))  # __getstate__ force-offloads to the codec pair
            go = Path(td) / "go"
            q = ctx.Queue()
            ps = [ctx.Process(target=_child, args=(str(blob), str(go), q)) for _ in range(procs)]
            for p in ps:
                p.start()
            time.sleep(1.5)  # let the children import GSEGUtils, then release them together
            go.touch()
            res = []
            for p in ps:
                p.join(timeout=60)
            for p in ps:
                try:
                    res.append(q.get(timeout=1))
                except Exception:  # noqa: BLE001 - a child that died without reporting
                    res.append(f"CHILD DIED without result (exitcode={p.exitcode})")
            for m in res:
                if m != "ok":
                    msgs[m] = msgs.get(m, 0) + 1
            bad += any(m != "ok" for m in res)
    print(f"rounds with at least one failing child: {bad}/{rounds}")
    for m, n in msgs.items():
        print(f"  x{n}  {m}")
