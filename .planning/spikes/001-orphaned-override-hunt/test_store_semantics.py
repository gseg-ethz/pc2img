"""Spike 001, part B — MEASURED behaviour of the post-migration store on the 0.6.0 wheel.

Every claim in 07-RESEARCH.md about exception types, containment, purge, del/pop/clear,
read-only ``.store``, key verdicts and the five ``extend_cache_path`` sites is printed by
this script (reproduce, don't read).  Nothing here touches src/ or tests/: the migrated
store is the local ``TargetImageStore`` (see target_store.py).

Sections:  S1 escape corpus x routes | S2 key verdicts | S3 extend_cache_path sites |
           S4 purge / del / pop / clear semantics | S5 residuals (ABA, .dat symlink,
           mid-build OSError) | S6 .store read-only | S7 DiskBackedImageData hooks.

Run: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/scratch/31_pc2img/src <scratch-venv>/bin/python this.py
"""

from __future__ import annotations

import ast
import gc
import os
import pickle
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from provenance import print_provenance  # noqa: E402

print_provenance()

import numpy as np  # noqa: E402
from GSEGUtils.lazy_disk_cache import (  # noqa: E402
    DiskBackedStore,
    LazyDiskCacheConfig,
    StoreContainmentError,
    StoreKeyError,
    StorePurgeIncompleteError,
    StorePurgeRefusedError,
    get_meta_path,
    get_npy_path,
    is_valid_store_key,
)

from pc2img.image_cache import DiskBackedImageData  # noqa: E402
from target_store import TargetImageStore, assert_target_state  # noqa: E402

assert_target_state()
REPO = Path("/scratch/31_pc2img")
SENT = b"pc2img phase-7 spike sentinel -- must not be touched"
_rng = np.random.default_rng(7)


def gray(shape=(4, 4)):
    return _rng.random(shape).astype(np.float32)


def exc_desc(e: BaseException) -> str:
    chain = [c.__name__ for c in type(e).__mro__ if c not in (object, BaseException)]
    return f"{type(e).__name__} (MRO: {' > '.join(chain)}) ValueError={isinstance(e, ValueError)} KeyError={isinstance(e, KeyError)}"


def listing(d: Path) -> list[str]:
    return sorted(str(p.relative_to(d)) for p in d.rglob("*"))


def hdr(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def layout(tmp: Path):
    cache = tmp / "cache"
    cache.mkdir()
    sentinel = tmp / "victim.npy"
    sentinel.write_bytes(SENT)
    cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False)
    return cache, sentinel, cfg


def mk(tmp: Path, **kw):
    cache = tmp / "cache"
    cache.mkdir(exist_ok=True)
    return cache, LazyDiskCacheConfig(enable_caching=True, cache_path=cache, **kw)


# =========================================================================== S1
hdr("S1  Escape corpus (Phase-5, 3 spellings) x routes, TARGET store (override deleted)")
ROUTES = {
    "R1 add_image_to_store": lambda s, k, a: s.add_image_to_store(k, a),
    "R2 setitem": lambda s, k, a: s.__setitem__(k, DiskBackedImageData(a)),
    "R3 setitem+del": lambda s, k, a: (s.__setitem__(k, DiskBackedImageData(a)), s.__delitem__(k)),
    "R4 add+offload(codec)": lambda s, k, a: (s.add_image_to_store(k, a), s.offload_image_data_to_disk(k)),
    "R5 purge": lambda s, k, a: s.purge(k),
    "R6 getitem": lambda s, k, a: s[k],
    "R7 pop": lambda s, k, a: s.pop(k),
    "R8 get": lambda s, k, a: s.get(k),
    "R9 add_data_to_store": lambda s, k, a: s.add_data_to_store(k, a),
}
survivors = []
for spelling in ("parent_segment", "absolute", "embedded_traversal"):
    for rname, route in ROUTES.items():
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cache, sentinel, cfg = layout(tmp)
            key = {"parent_segment": "../victim", "absolute": str(tmp / "victim"),
                   "embedded_traversal": "a/../../victim"}[spelling]
            store = TargetImageStore(config=cfg)
            before = listing(tmp)
            try:
                route(store, key, gray())
                out = "NO EXCEPTION"
            except BaseException as e:  # noqa: BLE001
                out = exc_desc(e)
            intact = sentinel.exists() and sentinel.read_bytes() == SENT
            same = listing(tmp) == before
            if out == "NO EXCEPTION" and rname not in ("R8 get",) or not intact or not same:
                survivors.append((spelling, rname, out, intact, same))
            print(f"  {spelling:19s} {rname:22s} -> {out}  sentinel_intact={intact} tree_unchanged={same}")
print(f"\n  SURVIVORS / damage cells: {survivors}")

# entry-supplied cache_path: the Phase-5 documented residual (store docstring) --------
hdr("S1b entry-supplied cache_path outside the cache dir (legal key, caller-chosen path)")
for label, mkpath in {
    "outside .npy path": lambda tmp: tmp / "victim.npy",
    "outside via ../ in path": lambda tmp: tmp / "cache" / ".." / "victim.npy",
}.items():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cache, sentinel, cfg = layout(tmp)
        store = TargetImageStore(config=cfg)
        entry = DiskBackedImageData(gray(), enable_caching=True, cache_path=mkpath(tmp), purge_disk_on_gc=False)
        store["legit"] = entry  # setter validates the KEY only
        try:
            store.offload("legit")  # plain offload -> entry's own .dat memmap write
            res = "offload ALLOWED"
        except BaseException as e:  # noqa: BLE001
            res = f"offload refused: {exc_desc(e)}"
        try:
            store.offload_image_data_to_disk("legit")
            res2 = "codec offload ok"
        except BaseException as e:  # noqa: BLE001
            res2 = f"codec offload: {exc_desc(e)}: {e}"
        outside = sorted(p.name for p in tmp.iterdir() if p.is_file())
        print(f"  {label:26s} {res}; {res2}; sentinel_intact={sentinel.read_bytes()==SENT}; outside files={outside}")

# =========================================================================== S2
hdr("S2  is_valid_store_key verdicts on REALISTIC keys (tile ids, folders, hash, feature names)")

def literals_from_tests() -> set[str]:
    out: set[str] = set()
    names = {"generate", "request", "submit", "add_image_to_store", "extend_cache_paths",
             "extend_cache_path", "PointCloudTile", "_get", "match", "compute"}
    for py in sorted((REPO / "tests").glob("*.py")):
        tree = ast.parse(py.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if fn in names:
                    for sub in ast.walk(n):
                        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                            out.add(sub.value)
    return out

corpus = sorted(literals_from_tests() | {
    "range", "aspect", "slope_deg", "hillshade_range_315_45", "grad_range_px0.5",
    "norm_(range,2,98)", "rrim_pack_(range,r16,d8,z1.2345678)", "scalar_field_intensity",
    "scalar_field_Scalar field", "scalar_field_GPS:time", "scalar_field_a/b", "scalar_field_x.",
    "scalar_field_a\\b", "scalar_field_é", "scalar_field_a*b", "scalar_field_a?b", "scalar_field_a<b>",
    "scalar_field_a|b", 'scalar_field_a"b',
    "tile_03", "tile-3", "0_0", "x_-1_-1", "0", "tile 03", "1.5", "ZH/01", "tile_03/range", "tile_03.",
    "CON", "", ".", "..", "a" * 64, "a" * 255, "a" * 256, "a" * 300,
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # sha256 hexdigest shape
    "triangles", "simplices", "verts", "bary",
})
print(f"  corpus size {len(corpus)} (AST-extracted from tests/ + hand-added edge names)")
refused = []
for k in corpus:
    v = is_valid_store_key(k)
    if not v:
        refused.append(k)
    print(f"  {('legal  ' if v else 'REFUSED')}  {k!r}"[:150])
print(f"\n  REFUSED set: {refused}")

# =========================================================================== S3
hdr("S3  extend_cache_path (BC-GSEG-006 drift): the five pc2img sites, realistic + hostile folder names")
with tempfile.TemporaryDirectory() as td:
    base = LazyDiskCacheConfig(enable_caching=True, cache_path=Path(td))
    for label, name in [("tile id", "tile_03"), ("tile id int-like str", "0"), ("hash", "e3b0c442" * 8),
                        ("folder", "tile-0"), ("hostile ../x", "../x"), ("nested a/b", "a/b"),
                        ("absolute", "/tmp/x"), ("empty", ""), ("dot", "."), ("CON", "CON"),
                        ("trailing dot", "t."), ("space", "tile 03")]:
        try:
            r = base.extend_cache_path(name)
            res = f"ok -> {r.cache_path.relative_to(td)}"
        except BaseException as e:  # noqa: BLE001
            res = exc_desc(e)
        print(f"  LazyDiskCacheConfig.extend_cache_path({label:20s} {name!r:>12}) {res}"[:200])
    try:
        base.extend_cache_path(5)  # non-str tile id
    except BaseException as e:  # noqa: BLE001
        print(f"  extend_cache_path(5)  -> {type(e).__name__} (pydantic validate_call type check, not StoreKeyError)")

    # symlink dir that points outside (resolved layer)
    outside = Path(td).parent / "spike001_outside_dir"
    outside.mkdir(exist_ok=True)
    (Path(td) / "linkdir").symlink_to(outside, target_is_directory=True)
    try:
        base.extend_cache_path("linkdir")
        print("  extend_cache_path(planted dir symlink) -> ALLOWED")
    except BaseException as e:  # noqa: BLE001
        print(f"  extend_cache_path(planted dir symlink) -> {exc_desc(e)}")
    outside.rmdir()

    # via TIGSettings (pydantic wrapper) — does a hostile name surface as StoreKeyError or ValidationError?
    from pc2img.core import ImgRes
    from pc2img.tiled_generator import TIGSettings

    st = TIGSettings(img_res=ImgRes(4, 4), proj_cls="spherical", interp_cls="linear",
                     lazy_disk_cache_config=base, interp_kwargs={"lazy_disk_cache_config": base})
    for nm in ("tile-0", "../x"):
        try:
            st.extend_cache_paths(nm)
            print(f"  TIGSettings.extend_cache_paths({nm!r}) -> ok")
        except BaseException as e:  # noqa: BLE001
            print(f"  TIGSettings.extend_cache_paths({nm!r}) -> {exc_desc(e)}")

print("\n  exception picklability (loky workers must be able to ship these back):")
for cls in (StoreKeyError, StoreContainmentError, StorePurgeRefusedError, StorePurgeIncompleteError):
    try:
        e = cls("probe message") if cls is not StorePurgeIncompleteError else cls("probe message")
        e2 = pickle.loads(pickle.dumps(e))
        print(f"    {cls.__name__:28s} pickle round-trip OK -> {type(e2).__name__}")
    except BaseException as ex:  # noqa: BLE001
        print(f"    {cls.__name__:28s} pickle round-trip FAILED: {type(ex).__name__}: {ex}")

print("\n  real TiledPointCloudImageGenerator, hostile tile id: n_jobs=1 for the migrated-store arm (monkeypatch is per-process;\n  the loky/n_jobs=2 arm of the migrated store is exercised via the scratch overlay, see README), n_jobs=2 for the refusal type:")
try:
    from pchandler import PointCloudData
    from pchandler.geometry.coordinates import rhv2xyz

    import pc2img.features.manager as _fm
    from pc2img.tiled_generator import PointCloudTile, TiledPointCloudImageGenerator

    _fm.DiskBackedImageStore = TargetImageStore  # simulated removal: FeatureManager builds the migrated store

    rng = np.random.default_rng(1)
    n = 800
    h = rng.uniform(-0.3, 0.3, n); v = rng.uniform(1.2, 1.8, n)
    r = 10 + 0.5 * np.sin(4 * h)
    pcd = PointCloudData(xyz=rhv2xyz(np.column_stack([r, h, v])).astype(np.float64))
    for tid in ("tile_03", "../evil"):
        with tempfile.TemporaryDirectory() as td:
            cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=Path(td))
            tg = TiledPointCloudImageGenerator(
                [PointCloudTile(tid, pcd, {"field_of_view": pcd.fov}), PointCloudTile("tile_04", pcd, {"field_of_view": pcd.fov})],
                (40, 50), "spherical", "linear", lazy_disk_cache_config=cfg)
            try:
                res = tg.generate(["range"], n_jobs=(2 if tid.startswith("..") else 1))
                print(f"    tile id {tid!r:12} -> ok keys={sorted(map(str, res))[:2]} files={sorted(p.name for p in Path(td).rglob('*') if p.is_file())[:6]}")
            except BaseException as e:  # noqa: BLE001
                print(f"    tile id {tid!r:12} -> {exc_desc(e)}")
            print(f"       directory created outside the cache dir ({Path(td).parent / 'evil'}): {(Path(td).parent / 'evil').exists()}")
except Exception:
    traceback.print_exc()

# =========================================================================== S4
hdr("S4  purge / del / pop / clear semantics on the TARGET store")

def build_variants(tmp: Path):
    cache, cfg = mk(tmp, purge_disk_on_gc=False)
    s = TargetImageStore(config=cfg)
    s.add_image_to_store("mem_only", gray((5, 5)))                       # tracked, .dat only
    s.add_image_to_store("plain_off", gray((5, 5))); s.offload("plain_off")  # entry.offload -> .dat
    s.add_image_to_store("codec_off", gray((5, 5))); s.offload_image_data_to_disk("codec_off")  # .npy+.meta
    return cache, s

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, s = build_variants(tmp)
    print("  cache dir after adds/offloads:", listing(cache))
    for k in ("mem_only", "plain_off", "codec_off"):
        s.purge(k)
        print(f"  purge({k!r}) -> remaining files {listing(cache)}  tracked={k in s}")
    try:
        s.purge("never-added"); print("  purge(absent) -> NO EXCEPTION")
    except BaseException as e:  # noqa: BLE001
        print(f"  purge(absent key) -> {exc_desc(e)}")
    try:
        s["mem_only"]; print("  getitem after purge -> served")
    except BaseException as e:  # noqa: BLE001
        print(f"  getitem after purge -> {exc_desc(e)}")

print("\n  del / pop / clear (D-08 consequence):")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, s = build_variants(tmp)
    before = listing(cache)
    del s["codec_off"]
    print(f"  del store['codec_off'] -> files unchanged={listing(cache)==before}; 'codec_off' in store={'codec_off' in s}")
    try:
        s["codec_off"]; print("  next store['codec_off'] read -> RE-ADOPTED from disk (key tracked again)", "codec_off" in s)
    except BaseException as e:  # noqa: BLE001
        print("  next read ->", exc_desc(e))
    del s["plain_off"]
    print(f"  del store['plain_off'] -> in store={'plain_off' in s}; next read:", end=" ")
    try:
        s["plain_off"]; print("served (re-adopted)")
    except BaseException as e:  # noqa: BLE001
        print(exc_desc(e))
    s2 = TargetImageStore(config=mk(tmp, purge_disk_on_gc=False)[1])
    print(f"  FRESH store over same dir tracks: {sorted(s2.keys())}")
    s2.pop("codec_off"); print(f"  pop -> files unchanged={listing(cache)==before}")
    s2.clear(); print(f"  clear -> len={len(s2)} files unchanged={listing(cache)==before}")

print("\n  default config (what FeatureManager uses when no config is given):")
s = TargetImageStore(); s.add_image_to_store("range", gray())
print(f"    enable_caching={s._enable_caching} cache_dir={s.cache_dir} files={sorted(p.name for p in s.cache_dir.iterdir())}")
s.purge("range"); print(f"    after purge: files={sorted(p.name for p in s.cache_dir.iterdir())} tracked={'range' in s}")
s.add_image_to_store("range", gray()); s.add_image_to_store("range", gray())
print(f"    overwrite (purge path) ok; files={sorted(p.name for p in s.cache_dir.iterdir())}")

print("\n  overwrite semantics through add_image_to_store (target store):")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp)
    s = TargetImageStore(config=cfg)
    a = gray((6, 6)); b = a + 10
    s.add_image_to_store("range", a); s.offload_image_data_to_disk("range")
    print("    after codec offload:", listing(cache))
    held = None
    s.add_image_to_store("range", b)
    print("    after overwrite:", listing(cache), "| served==b:", np.array_equal(np.asarray(s["range"]), b))
    s3 = TargetImageStore(config=cfg)
    try:
        print("    fresh store serves:", "b" if np.array_equal(np.asarray(s3["range"]), b) else "STALE a!")
    except KeyError:
        print("    fresh store: KeyError (stale A purged; B never codec-offloaded) -- acceptable per existing test")
    # failed overwrite (bad shape) must leave the old entry
    try:
        s.add_image_to_store("range", np.ones(4, np.float32))
    except BaseException as e:  # noqa: BLE001
        print(f"    bad-shape overwrite -> {exc_desc(e)}; old entry intact={np.array_equal(np.asarray(s['range']), b)}")
    try:
        s.add_image_to_store("../victim", np.ones((4, 4), np.float32))
    except BaseException as e:  # noqa: BLE001
        print(f"    escaping-key overwrite -> {exc_desc(e)}; old entry intact={'range' in s}")
    try:
        s.add_image_to_store("../victim", np.ones(4, np.float32))
    except BaseException as e:  # noqa: BLE001
        print(f"    escaping key + bad shape (precedence) -> {type(e).__name__}")

print("\n  purge from a forked child / unpickled store in another process:")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp, purge_disk_on_gc=False)
    s = TargetImageStore(config=cfg); s.add_image_to_store("range", gray())
    pid = os.fork()
    if pid == 0:
        try:
            s.purge("range"); code = 10
        except StorePurgeRefusedError:
            code = 11
        except BaseException:
            code = 12
        os._exit(code)
    _, st = os.waitpid(pid, 0)
    print(f"    forked child purge -> exit {os.waitstatus_to_exitcode(st)} (10=purged, 11=StorePurgeRefusedError, 12=other); files={listing(cache)}")

    from joblib import Parallel, delayed

    def worker(store):
        try:
            store.add_image_to_store("range", gray())   # overwrite in a worker => purge
            return "overwrite OK"
        except BaseException as e:  # noqa: BLE001
            return exc_desc(e)

    # the store is pickled to the worker (this is how tiled generation ships generators back and forth)
    print("    overwrite of a tracked key inside a loky worker with a parent-constructed store ->",
          Parallel(n_jobs=2, backend="loky")(delayed(worker)(s) for _ in range(1))[0])
    print("    same overwrite in the constructing process ->", worker(s))

# =========================================================================== S5
hdr("S5  Upstream residuals (D-11 rows): finalizer ABA, .dat symlink-follow, mid-build OSError")
print("  ABA hazard — held reference to the OLD entry, re-add, collect old, purge_disk_on_gc=True:")
for label, remover in (("del  (override-free, old pc2img overwrite shape sans unlink)", lambda s, k: s.__delitem__(k)),
                       ("purge (D-08)", lambda s, k: s.purge(k))):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); cache, cfg = mk(tmp, purge_disk_on_gc=True)
        s = DiskBackedStore[DiskBackedImageData](config=cfg, factory=DiskBackedImageData, value_type=DiskBackedImageData)
        s.add_data_to_store("range", gray((5, 5)))
        old = s["range"]
        remover(s, "range")
        s.add_data_to_store("range", gray((5, 5)) + 1)
        new_present_before = (cache / "range.dat").exists()
        del old; gc.collect()
        print(f"    {label:62s} new .dat present before/after old collected: {new_present_before}/{(cache / 'range.dat').exists()}")

print("\n  .dat / .npy / .meta.json symlink planted at a LEGAL key name pointing OUTSIDE the cache dir:")
for suffix in (".dat", ".npy", ".meta.json"):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); cache, sentinel, cfg = layout(tmp)
        sentinel.write_bytes(SENT)
        (cache / f"victimkey{suffix}").symlink_to(sentinel)
        s = TargetImageStore(config=cfg)
        try:
            s.add_image_to_store("victimkey", gray())
            s.offload("victimkey")
            s.offload_image_data_to_disk("victimkey")
            res = "ALLOWED (no exception)"
        except BaseException as e:  # noqa: BLE001
            res = exc_desc(e)
        print(f"    symlink {suffix:10s} -> {res}; sentinel intact={sentinel.read_bytes()==SENT}")

print("\n  mid-build OSError (disk full) during an overwrite — target store, old entry offloaded then overwritten:")
import GSEGUtils.lazy_disk_cache.lazy_disk_cache as ldc  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp)
    s = TargetImageStore(config=cfg)
    a = gray((6, 6)); s.add_image_to_store("range", a)
    real = np.memmap
    def boom(*a_, **k_):
        raise OSError(28, "No space left on device (simulated)")
    ldc.np.memmap = boom  # monkeypatch inside the scratch harness only
    try:
        try:
            s.add_image_to_store("range", a + 1)
        except OSError as e:
            print(f"    overwrite raised {type(e).__name__}: {e}")
    finally:
        ldc.np.memmap = real
    print(f"    afterwards: 'range' tracked={'range' in s}; files={listing(cache)}  -> old entry LOST (documented residual unchanged)")

# =========================================================================== S6
hdr("S6  .store / image_data read-only (BC-GSEG-007) and clear()")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp)
    s = TargetImageStore(config=cfg); s.add_image_to_store("range", gray())
    st = s.store
    print(f"  type(store.store)={type(st).__name__}  image_data is a read-only view: {type(s.image_data).__name__}")
    def _assign(): st["x"] = None
    def _del(): del st["range"]
    for label, fn in {"st[k] = v": _assign, "del st[k]": _del, ".pop(k)": lambda: st.pop("range"),
                      ".clear()": lambda: st.clear(), ".update({})": lambda: st.update({"y": None}),
                      ".setdefault(k, v)": lambda: st.setdefault("z", None)}.items():
        try:
            fn(); print(f"   .store {label}: NO EXCEPTION")
        except BaseException as e:  # noqa: BLE001
            print(f"   .store {label}: {type(e).__name__}: {str(e)[:70]}")
    print(f"  reads: len={len(st)} 'range' in st={'range' in st} entry type={type(st['range']).__name__}")

# =========================================================================== S7
hdr("S7  DiskBackedImageData / LazyDiskCache hooks on 0.6.0 (reload class registration, shapes, codec)")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp, purge_disk_on_gc=False)
    s = TargetImageStore(config=cfg)
    for name, arr in {"f32_2d": gray((6, 7)), "u8_2d": (gray((6, 7)) * 255).astype(np.uint8), "f32_rgb": gray((6, 7, 3))}.items():
        s.add_image_to_store(name, arr); s.offload_image_data_to_disk(name)
        back = s[name]
        print(f"  {name:8s} round-trip equal={np.array_equal(np.asarray(back), arr)} type={type(back).__name__} dtype={np.asarray(back).dtype} meta_class="
              + str(__import__('json').loads((cache / f'{name}.meta.json').read_text()).get('lazy_disk_cache_class')))
    s2 = TargetImageStore(config=cfg)
    print(f"  fresh store re-adopts: {sorted(s2.keys())}; reload type={type(s2['f32_rgb']).__name__}")
    print(f"  pickle round-trip of store: {sorted(pickle.loads(pickle.dumps(s)).keys())}")
    ss = DiskBackedImageData(gray())
    print(f"  to_uint8 ok: {ss.to_uint8().dtype}; AssertionError on 1-D: ", end="")
    try:
        DiskBackedImageData(np.ones(4, np.float32))
    except AssertionError:
        print("yes (type unchanged)")

hdr("S8  Symlinked adopted entry (Phase-5 test_symlinked_cache_entry_*): purge / overwrite / del on the TARGET store")
for inside in (False, True):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shared = (tmp / "cache" / "shared") if inside else (tmp / "shared")
        cache = tmp / "cache"
        cache.mkdir(exist_ok=True); shared.mkdir(parents=True, exist_ok=True)
        arr = gray()
        shared_store = TargetImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=shared, purge_disk_on_gc=False))
        shared_store.add_image_to_store("range", arr); shared_store.offload_image_data_to_disk("range")
        (cache / "range.npy").symlink_to(shared / "range.npy")
        (cache / "range.meta.json").symlink_to(shared / "range.meta.json")
        cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False)
        label = "link target INSIDE cache dir (cache/shared)" if inside else "link target OUTSIDE cache dir (sibling shared/)"
        st = TargetImageStore(config=cfg)
        print(f"  [{label}] adopted={'range' in st} served={np.array_equal(np.asarray(st['range']), arr)}")
        try:
            st.purge("range"); res = "purge OK"
        except BaseException as e:  # noqa: BLE001
            res = exc_desc(e)
        print(f"     purge -> {res}; link exists={(cache/'range.npy').is_symlink()}; shared target exists={(shared/'range.npy').exists()}")
        st2 = TargetImageStore(config=cfg)
        try:
            st2.add_image_to_store("range", gray()); res = "overwrite OK"
        except BaseException as e:  # noqa: BLE001
            res = exc_desc(e)
        print(f"     add_image_to_store overwrite of the adopted entry -> {res}")
        st3 = TargetImageStore(config=cfg)
        try:
            del st3["range"]
            print(f"     del -> link still on disk={(cache/'range.npy').is_symlink()} (tracking dropped only)")
        except KeyError:
            print("     del -> KeyError (nothing left to adopt: the overwrite above already consumed the entry)")


hdr("S9  Remaining D-11 evidence: planted *.tmp symlinks, de-link on pickle, empty raster, precedence w/o pre-check")
for suffix, route in ((".npy.tmp", "codec"), (".meta.json.tmp", "codec"), (".dat.tmp", "add")):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); cache, sentinel, cfg = layout(tmp)
        (cache / f"tkey{suffix}").symlink_to(sentinel)
        s = TargetImageStore(config=cfg)
        try:
            s.add_image_to_store("tkey", gray())
            if route == "codec":
                s.offload_image_data_to_disk("tkey")
            res = "ALLOWED"
        except BaseException as e:  # noqa: BLE001
            res = exc_desc(e)
        print(f"  planted symlink tkey{suffix:15s} -> {res}; sentinel intact={sentinel.read_bytes()==SENT}")

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    shared = tmp / "shared"; cache = tmp / "cache"; shared.mkdir(); cache.mkdir()
    ss = TargetImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=shared, purge_disk_on_gc=False))
    ss.add_image_to_store("range", gray()); ss.offload_image_data_to_disk("range")
    (cache / "range.npy").symlink_to(shared / "range.npy"); (cache / "range.meta.json").symlink_to(shared / "range.meta.json")
    st = TargetImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False))
    before = (cache / "range.npy").is_symlink()
    pickle.dumps(st)
    print(f"  de-link on pickle: cache/range.npy is_symlink before={before} after pickle.dumps(store)={(cache / 'range.npy').is_symlink()} (upstream __getstate__ force-offload; atomic replace swaps the link)")

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, cfg = mk(tmp)
    st = TargetImageStore(config=cfg)
    st.add_image_to_store("range", gray((4, 4))); st.offload_image_data_to_disk("range")
    for label, bad in (("empty (0,0) raster", np.empty((0, 0), np.float32)),):
        try:
            st.add_image_to_store("range", bad); res = "accepted"
        except BaseException as e:  # noqa: BLE001
            res = f"{type(e).__name__}: {str(e)[:60]}"
        print(f"  overwrite with {label}: {res}; old 'range' still tracked={'range' in st}; files={listing(cache)}")

class NoPreCheck(TargetImageStore):
    """add_image_to_store WITHOUT the get_npy_path pre-check (D-10 literal: no pc2img pre-validation)."""
    def add_image_to_store(self, img_name, img_data, **kw):
        from pc2img.image_cache.disk_backed_image_data import _assert_image_shape
        _assert_image_shape(img_data)
        if img_name in self:
            self.purge(img_name)
        self.add_data_to_store(img_name, img_data, **kw)

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); cache, sentinel, cfg = layout(tmp)
    for cls in (TargetImageStore, NoPreCheck):
        st = cls(config=cfg)
        for label, key, arr in (("escaping key + valid shape", "../victim", gray()), ("escaping key + bad shape", "../victim", np.ones(4, np.float32)),
                                ("legal key + bad shape", "range", np.ones(4, np.float32))):
            try:
                st.add_image_to_store(key, arr); res = "no exception"
            except BaseException as e:  # noqa: BLE001
                res = type(e).__name__
            print(f"  {cls.__name__:15s} {label:28s} -> {res}")
    print(f"  sentinel intact={sentinel.read_bytes()==SENT}")

print("\nDONE")
