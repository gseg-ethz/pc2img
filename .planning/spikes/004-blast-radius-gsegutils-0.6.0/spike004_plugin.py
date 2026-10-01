"""Spike 004 pytest plugin — the FULL pc2img suite against GSEGUtils 0.6.0 with the overrides removed.

Load with ``-p spike004_plugin`` (PYTHONPATH must contain this directory). The tracked tree is NOT
edited: the removal is simulated in-process by mutating the already-imported
``DiskBackedImageStore`` class at ``pytest_configure`` time, i.e. before any test module runs.

Arms (env SPIKE004_ARM):
  A  removal only. ``_assert_within_cache_dir``, ``_get_npy_path``, ``_get_meta_path`` and
     ``__delitem__`` are deleted from the class; ``add_image_to_store`` is rebound to the migrated body
     (containment-first ``get_npy_path(...)``, shape check, ``purge`` on overwrite).
  B  arm A plus a TEST-ONLY shim re-adding ``_get_npy_path`` / ``_get_meta_path`` as thin wrappers over
     the public free functions — separates failures that are mere renames from real semantic changes.

Provenance is asserted INSIDE this process (pytest_configure), and every run prints it.
"""

from __future__ import annotations

import importlib.metadata as md
import os
import subprocess
import sys
from pathlib import Path

import pytest

ARM = os.environ.get("SPIKE004_ARM", "A").upper()
STATE = {"purge_calls": 0, "purge_from_add": 0}


def pytest_configure(config):
    import GSEGUtils
    from GSEGUtils.lazy_disk_cache import DiskBackedStore, get_meta_path, get_npy_path

    # ---- provenance (inside the test process) ---------------------------------------------------
    gfile = Path(GSEGUtils.__file__).resolve()
    store_mod = Path(sys.modules["GSEGUtils.lazy_disk_cache.disk_backed_store"].__file__).resolve()
    hits = subprocess.run(["grep", "-c", r"self\._get_npy_path", str(store_mod)], capture_output=True, text=True).stdout.strip()
    direct = md.distribution("GSEGUtils").read_text("direct_url.json")
    facts = {
        "GSEGUtils.__version__": GSEGUtils.__version__,
        "metadata GSEGUtils / pchandler": f"{md.version('GSEGUtils')} / {md.version('pchandler')}",
        "GSEGUtils.__file__": str(gfile),
        "direct_url.json": "absent" if direct is None else direct,
        "grep -c 'self._get_npy_path'": hits,
        "DiskBackedStore._get_npy_path": str(hasattr(DiskBackedStore, "_get_npy_path")),
    }
    ok = (
        GSEGUtils.__version__ == "0.6.0" and md.version("GSEGUtils") == "0.6.0" and md.version("pchandler") == "2.1.1"
        and "site-packages" in gfile.parts and direct is None and hits == "0"
        and not hasattr(DiskBackedStore, "_get_npy_path")
    )
    import pc2img

    pc = Path(pc2img.__file__).resolve()
    facts["pc2img.__file__"] = str(pc)
    ok = ok and pc.is_relative_to(Path("/scratch/31_pc2img/src"))
    print("\n=== SPIKE 004 PROVENANCE (asserted in the test process) ===")
    for k, v in facts.items():
        print(f"  {k:34s} = {v}")
    if not ok:
        raise pytest.UsageError("SPIKE 004 PROVENANCE FAIL — refusing to run (would be a false green)")

    # ---- simulate the removal --------------------------------------------------------------------
    from pc2img.image_cache import DiskBackedImageStore
    from pc2img.image_cache.disk_backed_image_data import _assert_image_shape

    for name in ("_assert_within_cache_dir", "_get_npy_path", "_get_meta_path", "__delitem__"):
        assert name in DiskBackedImageStore.__dict__, f"{name} not an override on the real class"
        delattr(DiskBackedImageStore, name)

    def add_image_to_store(self, img_name, img_data, *, enable_caching_override=None,
                           automatic_offloading_override=None, purge_disk_on_gc_override=None):
        get_npy_path(self.cache_dir, img_name)
        _assert_image_shape(img_data)
        if img_name in self:
            STATE["purge_from_add"] += 1
            self.purge(img_name)
        self.add_data_to_store(
            img_name, img_data,
            enable_caching_override=enable_caching_override,
            automatic_offloading_override=automatic_offloading_override,
            purge_disk_on_gc_override=purge_disk_on_gc_override,
        )

    DiskBackedImageStore.add_image_to_store = add_image_to_store
    real_purge = DiskBackedStore.purge

    def counting_purge(self, key):
        STATE["purge_calls"] += 1
        return real_purge(self, key)

    DiskBackedStore.purge = counting_purge

    if ARM == "B":
        DiskBackedImageStore._get_npy_path = lambda self, k: get_npy_path(self.cache_dir, k)
        DiskBackedImageStore._get_meta_path = lambda self, k: get_meta_path(self.cache_dir, k)

    # ---- static proof that the removal took ------------------------------------------------------
    assert DiskBackedImageStore.__delitem__ is DiskBackedStore.__delitem__
    assert hasattr(DiskBackedImageStore, "_get_npy_path") == (ARM == "B")
    assert not hasattr(DiskBackedImageStore, "_assert_within_cache_dir")
    print(f"  ARM {ARM}: overrides removed (in-process); add_image_to_store -> migrated body; "
          f"_get_*_path shim {'PRESENT' if ARM == 'B' else 'absent'}\n")


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(
        f"SPIKE004 ARM {ARM}: purge() calls during the suite = {STATE['purge_calls']} "
        f"(of which triggered by add_image_to_store overwrite = {STATE['purge_from_add']})"
    )
