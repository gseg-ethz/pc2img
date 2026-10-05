import tempfile, numpy as np, GSEGUtils
from pathlib import Path
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from pc2img.image_cache import DiskBackedImageStore
print("GSEGUtils", GSEGUtils.__version__)
for key in ("scalar_field_a/b", "scalar_field_GPS:time", "scalar_field_x."):
    with tempfile.TemporaryDirectory() as td:
        cfg = LazyDiskCacheConfig(enable_caching=True, cache_path=Path(td), purge_disk_on_gc=False)
        s = DiskBackedImageStore(config=cfg)
        try:
            s.add_image_to_store(key, np.ones((3,3), np.float32)); s.offload_image_data_to_disk(key)
            ok = np.array_equal(np.asarray(s[key]), np.ones((3,3)))
            s2 = DiskBackedImageStore(config=cfg)
            print(f"{key!r}: add+offload+read ok={ok}; fresh store tracks it: {key in s2}; files={sorted(str(p.relative_to(td)) for p in Path(td).rglob('*') if p.is_file())}")
        except BaseException as e:
            print(f"{key!r}: {type(e).__name__}: {str(e)[:100]}")
