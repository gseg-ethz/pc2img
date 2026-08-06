"""Import-provenance gate for spike 000.

The whole absorption experiment is invalid if the GSEGUtils under test is the
installed 0.5.3 wheel: 0.5.3 still routes every disk-touching route through
``self._get_npy_path``, so pc2img's override would be LIVE and every escaping
key would be refused for the wrong reason — a false green.

This module refuses to let the experiment proceed unless the imported
GSEGUtils is the phase-14 workspace tree, verified three independent ways.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXPECTED_ROOT = Path("~/gsd-workspaces/pchandler/30_GSEGUtils").expanduser().resolve()


def assert_phase14_under_test() -> dict[str, str]:
    """Return provenance facts, or raise SystemExit with the reason it is wrong."""
    import GSEGUtils

    facts: dict[str, str] = {}

    # --- 1. the imported package resolves under the phase-14 workspace ------
    gseg_file = Path(GSEGUtils.__file__).resolve()
    facts["GSEGUtils.__file__"] = str(gseg_file)
    facts["GSEGUtils.__version__"] = str(GSEGUtils.__version__)
    if not gseg_file.is_relative_to(EXPECTED_ROOT):
        raise SystemExit(
            f"PROVENANCE FAIL: GSEGUtils imported from {gseg_file}, "
            f"expected a path under {EXPECTED_ROOT}. "
            "Refusing to run — this would be a false green."
        )

    # --- 2. the concrete store module, not just the package __init__ -------
    from GSEGUtils.lazy_disk_cache import DiskBackedStore  # noqa: F401

    store_mod = Path(
        sys.modules["GSEGUtils.lazy_disk_cache.disk_backed_store"].__file__
    ).resolve()
    facts["disk_backed_store.py"] = str(store_mod)
    if not store_mod.is_relative_to(EXPECTED_ROOT):
        raise SystemExit(f"PROVENANCE FAIL: store module is {store_mod}")

    # --- 3. the behavioural fingerprint of the version under test ----------
    # phase-14 routes paths through the shared builders, so the base store no
    # longer calls self._get_npy_path anywhere. 0.5.3 calls it 4 times.
    hits = subprocess.run(
        ["grep", "-c", r"self\._get_npy_path", str(store_mod)],
        capture_output=True,
        text=True,
    ).stdout.strip()
    facts["grep -c 'self._get_npy_path'"] = hits
    if hits != "0":
        raise SystemExit(
            f"PROVENANCE FAIL: base store calls self._get_npy_path {hits}x — "
            "that is the 0.5.x fingerprint, pc2img's override would still be live."
        )

    # --- 4. pc2img itself is the working tree ------------------------------
    import pc2img

    facts["pc2img.__file__"] = str(Path(pc2img.__file__).resolve())

    return facts


def print_provenance() -> None:
    facts = assert_phase14_under_test()
    print("=" * 72)
    print("IMPORT PROVENANCE — verified before any assertion runs")
    print("=" * 72)
    for k, v in facts.items():
        print(f"  {k:32s} = {v}")
    print(
        "  fingerprint                      = phase-14 "
        "(base store calls self._get_npy_path 0 times)"
    )
    print()


if __name__ == "__main__":
    print_provenance()
