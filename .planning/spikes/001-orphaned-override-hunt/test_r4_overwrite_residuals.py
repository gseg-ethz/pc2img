import sys, tempfile, numpy as np, pickle
from pathlib import Path
sys.path.insert(0, "/scratch/31_pc2img/.planning/spikes/001-orphaned-override-hunt")
import GSEGUtils; print("GSEGUtils", GSEGUtils.__version__)
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from target_store import TargetImageStore
def lst(d): return sorted(p.name for p in d.iterdir())
for label, bad, kw in (("empty (0,0)", np.empty((0, 0), np.float32), {}), ("V0 dtype", np.empty((3, 3), dtype="V0"), {}), ("wrong-type override enable_caching=2", np.ones((3, 3), np.float32), {"enable_caching_override": 2})):
    with tempfile.TemporaryDirectory() as td:
        cache = Path(td)
        st = TargetImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=cache))
        st.add_image_to_store("range", np.ones((4, 4), np.float32)); st.offload_image_data_to_disk("range")
        try:
            st.add_image_to_store("range", bad, **kw); res = "accepted"
        except BaseException as e:
            res = f"{type(e).__name__}: {str(e)[:70]}"
        extra = ""
        try: extra = f" shape={np.asarray(st['range']).shape}"
        except BaseException as e: extra = f" read: {type(e).__name__}"
        print(f"{label:38s} -> {res}; tracked={'range' in st}; files={lst(cache)};{extra}")
# de-link on pickle after a read
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td); shared = tmp/"shared"; cache = tmp/"cache"; shared.mkdir(); cache.mkdir()
    cfg_s = LazyDiskCacheConfig(enable_caching=True, cache_path=shared, purge_disk_on_gc=False)
    ss = TargetImageStore(config=cfg_s); ss.add_image_to_store("range", np.ones((4,4), np.float32)); ss.offload_image_data_to_disk("range")
    (cache/"range.npy").symlink_to(shared/"range.npy"); (cache/"range.meta.json").symlink_to(shared/"range.meta.json")
    st = TargetImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=cache, purge_disk_on_gc=False))
    np.asarray(st["range"]); b = (cache/"range.npy").is_symlink(); pickle.dumps(st)
    print(f"de-link on pickle after a read: is_symlink before={b} after={(cache/'range.npy').is_symlink()}")
