"""Spike 000, extension — DIFFERENTIAL probe beyond the Phase 5 corpus.

The corpus run showed all 12 inputs refused at the LEXICAL layer
(``validate_store_key``, which rejects any key containing a path separator).
That means the corpus never reaches ``paths._assert_contained`` — the resolved
layer is untested by it.

pc2img's override was a *resolved* check (``path.resolve().is_relative_to(...)``).
So the interesting question is not "does phase-14 catch the corpus" (it does)
but: **is there a key that escapes WITHOUT a path separator?** Such a key would
sail through the lexical rule and can only be caught by the resolved layer. If
one exists and phase-14 lets it through, that is a phase-14 requirement gap that
pc2img's override did catch — the single most valuable possible result.

The canonical instance: a SYMLINK inside the cache directory whose name is a
legal store key and whose target is outside. ``cache_dir / "evil.npy"`` is
lexically contained; ``.resolve()`` is not.

Each probe is run twice — once with pc2img's guard live (the real
``DiskBackedImageStore``), once with it removed — so any divergence is visible.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from provenance import print_provenance  # noqa: E402

print_provenance()

import numpy as np  # noqa: E402
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig  # noqa: E402
from GSEGUtils.lazy_disk_cache.paths import (  # noqa: E402
    StoreContainmentError,
    StoreKeyError,
)

from pc2img.image_cache import DiskBackedImageStore  # noqa: E402
from test_absorption import NoGuardImageStore, _GuardReached, _gray  # noqa: E402

_SENTINEL = b"differential sentinel -- must not be touched"


def _classify(exc: BaseException | None) -> str:
    if exc is None:
        return "ALLOWED"
    if isinstance(exc, _GuardReached):
        return "pc2img guard (tripwire)"
    if isinstance(exc, StoreContainmentError):
        return "StoreContainmentError"
    if isinstance(exc, StoreKeyError):
        return "StoreKeyError"
    if isinstance(exc, ValueError):
        return f"ValueError ({str(exc)[:40]})"
    return f"{type(exc).__name__}"


def probe_symlink(store_cls, follow_name: str = "evil") -> tuple[str, bool, str]:
    """Plant a symlink in the cache dir pointing at an outside sentinel.

    Returns (refused_by, sentinel_intact, note).
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        sentinel = tmp / "victim.npy"
        sentinel.write_bytes(_SENTINEL)

        # The store key is `evil` -> the store builds cache_dir/'evil.npy',
        # which we make a symlink to the outside sentinel. No path separator
        # appears in the key, so the lexical rule has nothing to reject.
        (cache_dir / f"{follow_name}.npy").symlink_to(sentinel)

        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        store = store_cls(config=cfg)
        exc: BaseException | None = None
        try:
            store.add_image_to_store(follow_name, _gray((4, 4)))
            store.offload_image_data_to_disk(follow_name)
        except BaseException as e:  # noqa: BLE001
            exc = e

        intact = sentinel.exists() and sentinel.read_bytes() == _SENTINEL
        note = ""
        if not intact:
            note = (
                "sentinel GONE"
                if not sentinel.exists()
                else f"sentinel OVERWRITTEN -> {sentinel.read_bytes()[:16]!r}"
            )
        return _classify(exc), intact, note


def probe_symlink_delete(store_cls, follow_name: str = "evil") -> tuple[str, bool, str]:
    """Same symlink layout, but exercise the unlink route."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        sentinel = tmp / "victim.npy"
        sentinel.write_bytes(_SENTINEL)
        (cache_dir / f"{follow_name}.npy").symlink_to(sentinel)

        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        store = store_cls(config=cfg)
        exc: BaseException | None = None
        try:
            store[follow_name] = __import__(
                "pc2img.image_cache", fromlist=["DiskBackedImageData"]
            ).DiskBackedImageData(_gray((4, 4)))
            del store[follow_name]
        except BaseException as e:  # noqa: BLE001
            exc = e

        intact = sentinel.exists() and sentinel.read_bytes() == _SENTINEL
        note = "" if intact else ("sentinel GONE" if not sentinel.exists() else "overwritten")
        return _classify(exc), intact, note


# Separator-free keys that are lexically innocent but semantically odd.
ODD_KEYS = ["", ".", "..", "...", "~", "evil.npy", "a" * 200, "with space", "a\\b"]


def probe_key(store_cls, key: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache_dir = tmp / "cache"
        cache_dir.mkdir()
        cfg = LazyDiskCacheConfig(
            enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
        )
        store = store_cls(config=cfg)
        try:
            store.add_image_to_store(key, _gray((3, 3)))
            store.offload_image_data_to_disk(key)
        except BaseException as e:  # noqa: BLE001
            return _classify(e)
        written = sorted(p.name for p in cache_dir.rglob("*") if p.is_file())
        outside = sorted(p.name for p in tmp.iterdir() if p.is_file())
        return f"ALLOWED (in-cache: {written}, outside: {outside})"


if __name__ == "__main__":
    print("=" * 78)
    print("DIFFERENTIAL PROBE — separator-free escapes (lexical layer cannot see these)")
    print("=" * 78)
    print()
    print("Probe A: symlink in cache dir, OFFLOAD WRITE route")
    for label, cls in (("pc2img guard LIVE", DiskBackedImageStore), ("guard REMOVED", NoGuardImageStore)):
        by, intact, note = probe_symlink(cls)
        flag = "ok" if intact else "!! SENTINEL DAMAGED"
        print(f"  {label:20s} -> refused by: {by:28s} sentinel: {flag} {note}")

    print()
    print("Probe B: symlink in cache dir, DELETE route")
    for label, cls in (("pc2img guard LIVE", DiskBackedImageStore), ("guard REMOVED", NoGuardImageStore)):
        by, intact, note = probe_symlink_delete(cls)
        flag = "ok" if intact else "!! SENTINEL DAMAGED"
        print(f"  {label:20s} -> refused by: {by:28s} sentinel: {flag} {note}")

    print()
    print("Probe C: separator-free odd keys (guard REMOVED = phase-14 behaviour alone)")
    for k in ODD_KEYS:
        print(f"  {k!r:24s} -> {probe_key(NoGuardImageStore, k)}")

    print()
    print("Probe C': same keys with pc2img's guard LIVE (divergence = guard adds coverage)")
    for k in ODD_KEYS:
        print(f"  {k!r:24s} -> {probe_key(DiskBackedImageStore, k)}")
