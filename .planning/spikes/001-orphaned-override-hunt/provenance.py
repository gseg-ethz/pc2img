"""Import-provenance gate for spikes 001 / 004 (target: the PyPI GSEGUtils 0.6.0 wheel).

Spike 000 gated on the phase-14 dev worktree. Phase 7 targets what users install:
the **released wheel**. The experiment is invalid if the GSEGUtils under test is a
cached 0.5.x (the lock hides it) or an editable / VCS / workspace checkout, so
``assert_wheel_060_under_test`` refuses to let any assertion run until six
independent checks pass. Every script prints the facts first.
"""

from __future__ import annotations

import importlib.metadata as md
import subprocess
import sys
from pathlib import Path

REPO = Path("/scratch/31_pc2img").resolve()


def assert_wheel_060_under_test(*, require_pc2img_tree: bool = True) -> dict[str, str]:
    import GSEGUtils

    facts: dict[str, str] = {}

    # 1. version, from the module AND from installed-distribution metadata
    facts["GSEGUtils.__version__"] = str(GSEGUtils.__version__)
    facts["metadata GSEGUtils"] = md.version("GSEGUtils")
    if not (GSEGUtils.__version__ == "0.6.0" and md.version("GSEGUtils") == "0.6.0"):
        raise SystemExit(f"PROVENANCE FAIL: GSEGUtils is {GSEGUtils.__version__}, expected 0.6.0")

    # 2. an installed wheel: under site-packages, not inside this repo / a workspace checkout
    gseg_file = Path(GSEGUtils.__file__).resolve()
    facts["GSEGUtils.__file__"] = str(gseg_file)
    if "site-packages" not in gseg_file.parts or gseg_file.is_relative_to(REPO):
        raise SystemExit(f"PROVENANCE FAIL: GSEGUtils not an installed wheel: {gseg_file}")

    # 3. not an editable / VCS / local-directory install (PEP 610 direct_url.json absent)
    direct = md.distribution("GSEGUtils").read_text("direct_url.json")
    facts["direct_url.json"] = "absent (index install)" if direct is None else direct
    if direct is not None:
        raise SystemExit(f"PROVENANCE FAIL: GSEGUtils has direct_url.json: {direct}")

    # 4. behavioural fingerprint: the base store no longer calls self._get_npy_path
    from GSEGUtils.lazy_disk_cache import DiskBackedStore  # noqa: F401

    store_mod = Path(sys.modules["GSEGUtils.lazy_disk_cache.disk_backed_store"].__file__).resolve()
    hits = subprocess.run(
        ["grep", "-c", r"self\._get_npy_path", str(store_mod)], capture_output=True, text=True
    ).stdout.strip()
    facts["grep -c 'self._get_npy_path'"] = hits
    if hits != "0":
        raise SystemExit(f"PROVENANCE FAIL: fingerprint {hits} != 0 (0.5.x routes through the override)")
    facts["DiskBackedStore has _get_npy_path"] = str(hasattr(DiskBackedStore, "_get_npy_path"))
    if hasattr(DiskBackedStore, "_get_npy_path"):
        raise SystemExit("PROVENANCE FAIL: DiskBackedStore still defines _get_npy_path")

    # 5. pchandler is the PyPI 2.1.1 release
    facts["pchandler (metadata)"] = md.version("pchandler")
    if md.version("pchandler") != "2.1.1":
        raise SystemExit(f"PROVENANCE FAIL: pchandler {md.version('pchandler')}, expected 2.1.1")

    # 6. pc2img is the working tree (the code under test), not an installed copy
    if require_pc2img_tree:
        import pc2img

        facts["pc2img.__file__"] = str(Path(pc2img.__file__).resolve())
        if not Path(pc2img.__file__).resolve().is_relative_to(REPO / "src"):
            raise SystemExit(f"PROVENANCE FAIL: pc2img is {pc2img.__file__}, expected {REPO}/src")
    return facts


def print_provenance(**kw) -> None:
    facts = assert_wheel_060_under_test(**kw)
    print("=" * 72)
    print("IMPORT PROVENANCE — verified before any assertion runs")
    print("=" * 72)
    for k, v in facts.items():
        print(f"  {k:36s} = {v}")
    print()


if __name__ == "__main__":
    print_provenance()
