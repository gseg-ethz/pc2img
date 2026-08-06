"""Spike 000 — ABSORPTION TEST.

Question: did GSEGUtils phase-14 absorb pc2img's WR-02 containment override?

Method: take the exact escape corpus that pc2img commit 03eb715 was written to
stop, remove pc2img's ``_get_npy_path`` / ``_get_meta_path`` override, and run
the corpus against GSEGUtils phase-14 HEAD. Every input must still be refused —
by ``StoreKeyError`` (lexical layer, ``validate_store_key``) or
``StoreContainmentError`` (resolved layer, ``paths._assert_contained``).

  ALL REFUSED  -> absorption confirmed, the override is redundant and deletable.
  ANY SURVIVOR -> a GSEGUtils phase-14 REQUIREMENT GAP, not a pc2img patch.

The override is removed WITHOUT editing pc2img source: a local subclass rebinds
both path builders back to the base implementations. A tripwire on
``_assert_within_cache_dir`` proves the pc2img guard is genuinely out of the
loop, so a refusal can never be credited to the very code under test.

Run:
    PYTHONPATH=~/gsd-workspaces/pchandler/30_GSEGUtils/src \
        .venv/bin/python .planning/spikes/000-absorption-test/test_absorption.py
"""

from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from provenance import print_provenance  # noqa: E402

print_provenance()

import numpy as np  # noqa: E402
from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig  # noqa: E402
from GSEGUtils.lazy_disk_cache.paths import (  # noqa: E402
    StoreContainmentError,
    StoreKeyError,
)

from pc2img.image_cache import DiskBackedImageData, DiskBackedImageStore  # noqa: E402

_rng = np.random.default_rng(20260711)
_SENTINEL_BYTES = b"pc2img round-3 containment sentinel -- must not be touched"


def _gray(shape=(4, 4), dtype=np.float32):
    return _rng.random(shape).astype(dtype)


# --------------------------------------------------------------------------- #
# The override, removed — without touching pc2img source.                      #
# --------------------------------------------------------------------------- #
class _GuardReached(RuntimeError):
    """Raised if pc2img's containment guard runs. It must not."""


class NoGuardImageStore(DiskBackedImageStore):
    """``DiskBackedImageStore`` as it would be with commit 03eb715 reverted.

    Both path builders are rebound to the base-class implementations, which is
    exactly what deleting the override would leave behind. ``__delitem__``,
    ``add_image_to_store`` and the offload aliases are inherited unchanged —
    only the containment authority is gone.
    """

    _get_npy_path = DiskBackedStore._get_npy_path
    _get_meta_path = DiskBackedStore._get_meta_path

    def _assert_within_cache_dir(self, path: Path) -> Path:  # tripwire
        raise _GuardReached(
            "pc2img's WR-02 guard was reached — the override is NOT removed, "
            "this run would be a false green"
        )


def _verify_override_removed() -> None:
    """Static proof that the guard is out of the loop before any corpus runs."""
    assert NoGuardImageStore._get_npy_path is DiskBackedStore._get_npy_path
    assert NoGuardImageStore._get_meta_path is DiskBackedStore._get_meta_path
    assert DiskBackedImageStore._get_npy_path is not DiskBackedStore._get_npy_path, (
        "pc2img's override is missing from the real class — corpus would be meaningless"
    )
    print("OVERRIDE REMOVED: NoGuardImageStore path builders are the base ones;")
    print("                  pc2img's _assert_within_cache_dir is a tripwire.\n")


# --------------------------------------------------------------------------- #
# The Phase 5 escape corpus, verbatim from commit 03eb715.                     #
# --------------------------------------------------------------------------- #
def _escape_layout(tmp_path: Path) -> tuple[Path, LazyDiskCacheConfig]:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    sentinel = tmp_path / "victim.npy"
    sentinel.write_bytes(_SENTINEL_BYTES)
    cfg = LazyDiskCacheConfig(
        enable_caching=True, cache_path=cache_dir, purge_disk_on_gc=False
    )
    return sentinel, cfg


def _escaping_keys(tmp_path: Path) -> dict[str, str]:
    return {
        "parent_segment": "../victim",
        "absolute": str(tmp_path / "victim"),
        "embedded_traversal": "a/../../victim",
    }


def _classify(exc: BaseException) -> str:
    if isinstance(exc, _GuardReached):
        return "!! GUARD REACHED (invalid run)"
    if isinstance(exc, StoreContainmentError):
        return "StoreContainmentError (resolved layer)"
    if isinstance(exc, StoreKeyError):
        return "StoreKeyError (lexical layer)"
    return f"{type(exc).__name__} (OTHER: {exc})"


# --------------------------------------------------------------------------- #
# Routes. Each is an independent way an escaping key can reach the disk.       #
# --------------------------------------------------------------------------- #
def route_insert(store, key, arr):
    """R1 — insertion via the legacy alias (add_data_to_store underneath)."""
    store.add_image_to_store(key, arr)


def route_setitem(store, key, arr):
    """R2 — the mapping setter, which bypasses add_data_to_store entirely."""
    store[key] = DiskBackedImageData(arr)


def route_setitem_then_delete(store, key, arr):
    """R3 — the unlink route: track via the setter, then delete."""
    try:
        store[key] = DiskBackedImageData(arr)
    except Exception:
        raise  # refused earlier; still a refusal
    del store[key]


def route_insert_then_offload(store, key, arr):
    """R4 — the offload WRITE route (the one that overwrote the sentinel)."""
    store.add_image_to_store(key, arr)
    store.offload_image_data_to_disk(key)


ROUTES = [
    ("R1 insert", route_insert),
    ("R2 setitem", route_setitem),
    ("R3 setitem+delete", route_setitem_then_delete),
    ("R4 insert+offload", route_insert_then_offload),
]


def run_corpus() -> list[dict]:
    results = []
    for spelling in ("parent_segment", "absolute", "embedded_traversal"):
        for route_name, route in ROUTES:
            with tempfile.TemporaryDirectory() as td:
                tmp_path = Path(td)
                sentinel, cfg = _escape_layout(tmp_path)
                key = _escaping_keys(tmp_path)[spelling]
                store = NoGuardImageStore(config=cfg)
                arr = _gray()

                outcome, layer, detail = "SURVIVED", "-", ""
                try:
                    route(store, key, arr)
                except BaseException as exc:  # noqa: BLE001 — classifying, not handling
                    outcome, layer = "refused", _classify(exc)
                    if layer.startswith(("!!", "TypeError", "AttributeError")):
                        detail = traceback.format_exc(limit=3)

                # Independent damage check — a refusal that still touched the
                # sentinel is not a refusal.
                intact = sentinel.exists() and sentinel.read_bytes() == _SENTINEL_BYTES
                if not intact:
                    outcome = "SURVIVED"
                    layer = (
                        "sentinel DELETED"
                        if not sentinel.exists()
                        else "sentinel OVERWRITTEN"
                    )
                    detail = (
                        f"sentinel now: "
                        f"{sentinel.read_bytes()[:32]!r}"
                        if sentinel.exists()
                        else "file gone"
                    )

                results.append(
                    {
                        "spelling": spelling,
                        "key": key if spelling != "absolute" else "<tmp>/victim",
                        "route": route_name,
                        "outcome": outcome,
                        "layer": layer,
                        "detail": detail,
                    }
                )
    return results


# --------------------------------------------------------------------------- #
# False-positive bound: absorption must not over-refuse real feature names.    #
# --------------------------------------------------------------------------- #
REALISTIC = [
    "range",
    "rrim_pack_(range,r16,d8,z1.2345678)",
    "hillshade_range_315_45",
    "norm_(range,2,98)",
    "scalar_field_intensity",
    "grad_range_px0.5",
]


def run_false_positive_bound() -> list[dict]:
    out = []
    for name in REALISTIC:
        with tempfile.TemporaryDirectory() as td:
            _sentinel, cfg = _escape_layout(Path(td))
            store = NoGuardImageStore(config=cfg)
            arr = _gray((5, 5))
            try:
                store.add_image_to_store(name, arr)
                store.offload_image_data_to_disk(name)
                np.testing.assert_array_equal(np.asarray(store[name]), arr)
                out.append({"name": name, "outcome": "round-trips", "detail": ""})
            except BaseException as exc:  # noqa: BLE001
                out.append(
                    {
                        "name": name,
                        "outcome": "!! REFUSED (false positive)",
                        "detail": f"{type(exc).__name__}: {exc}",
                    }
                )
    return out


def _table(rows: list[dict], cols: list[tuple[str, str]]) -> None:
    widths = [
        max(len(h), *(len(str(r[k])) for r in rows)) for h, k in cols
    ]
    print("  " + " | ".join(h.ljust(w) for (h, _), w in zip(cols, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print("  " + " | ".join(str(r[k]).ljust(w) for (_, k), w in zip(cols, widths)))


if __name__ == "__main__":
    _verify_override_removed()

    print("=" * 72)
    print("ESCAPE CORPUS (commit 03eb715) vs phase-14, pc2img override REMOVED")
    print("=" * 72)
    corpus = run_corpus()
    _table(
        corpus,
        [("key", "key"), ("route", "route"), ("outcome", "outcome"), ("refused by", "layer")],
    )
    survivors = [r for r in corpus if r["outcome"] == "SURVIVED"]
    print()
    for r in corpus:
        if r["detail"]:
            print(f"  detail [{r['key']} / {r['route']}]:\n{r['detail']}")

    print("=" * 72)
    print("FALSE-POSITIVE BOUND — realistic feature names must still round-trip")
    print("=" * 72)
    fp = run_false_positive_bound()
    _table(fp, [("feature name", "name"), ("outcome", "outcome"), ("detail", "detail")])
    false_positives = [r for r in fp if r["outcome"].startswith("!!")]

    print()
    print("=" * 72)
    if survivors:
        print(f"VERDICT: {len(survivors)} SURVIVOR(S) — GSEGUtils PHASE-14 REQUIREMENT GAP")
        for r in survivors:
            print(f"  - {r['key']} via {r['route']}: {r['layer']}")
    elif false_positives:
        print(f"VERDICT: absorption refuses too much — {len(false_positives)} false positive(s)")
    else:
        print("VERDICT: ABSORPTION CONFIRMED — every corpus input refused upstream,")
        print("         no realistic feature name refused. Override is redundant.")
    print("=" * 72)
    sys.exit(1 if (survivors or false_positives) else 0)
