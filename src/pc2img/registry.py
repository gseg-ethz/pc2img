# The former ``make_generator`` factory was removed in Phase 04 (QUAL-01): it called
# ``PointCloudImageGenerator(pcd, proj, interp)`` with three positional arguments, which
# — against the real 5-parameter constructor ``(pcd, img_res, proj, interp,
# lazy_disk_cache_config)`` — landed ``proj`` in ``img_res`` and ``interp`` in ``proj``.
# No caller existed anywhere in ``src/``, ``tests/``, or ``scripts/``, so the broken
# factory was deleted rather than repaired. Construct a generator directly via
# ``pc2img.PointCloudImageGenerator`` instead.
