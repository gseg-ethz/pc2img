__all__ = ["DiskBackedImageData", "DiskBackedImageStore"]

from GSEGUtils.lazy_disk_cache import register_lazy_disk_cache_class

from .disk_backed_image_data import DiskBackedImageData
from .disk_backed_image_store import DiskBackedImageStore

# Register DiskBackedImageData into the GSEGUtils reload allow-list at import
# time, so rasters offloaded through DiskBackedStore's codec resolve their
# class on reload. Explicit allow-list, no importlib fallback — the
# no-arbitrary-class-loading tampering posture is preserved.
register_lazy_disk_cache_class(DiskBackedImageData)
