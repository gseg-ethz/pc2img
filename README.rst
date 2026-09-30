======
pc2img
======

``pc2img`` is a scientific Python library from the ETH Zurich Geosensors and
Engineering Geodesy (GSEG) group that converts 3D point clouds into 2D raster
images. It projects points into image space (spherical, orthographic, or
perspective), interpolates the scattered values onto a pixel grid, and
computes named "features" (range, scalar fields, gradients, hillshade, RRIM,
multiscale gradient, and more) as rasters, held in a lazy disk-backed cache.
A tiled orchestrator fans the same pipeline across many point-cloud tiles in
parallel.

Installation
============

Install the latest release from PyPI::

    pip install pc2img

This installs ``pc2img`` together with its two core dependencies,
`pchandler <https://pypi.org/project/pchandler/>`_ (point-cloud data and
geometry) and `GSEGUtils <https://pypi.org/project/gsegutils/>`_ (the
lazy disk-cache layer), both pulled from PyPI. ``pc2img`` requires Python
3.12.

Optional extras
----------------

- ``pc2img[viz]`` installs matplotlib, used only for colormap support in
  ``convert_to_image``. Without it, colormap conversion raises a clear
  error; everything else works unaffected.
- ``pc2img[cuda12]`` / ``pc2img[cuda11]`` pull the GPU-accelerated RAPIDS
  stack through ``pchandler``. The two extras are mutually exclusive — pick
  the one that matches your NVIDIA driver. Run ``nvidia-smi`` and read the
  "CUDA Version" in the top-right corner: driver support for CUDA >= 12.0
  means ``pc2img[cuda12]`` (preferred), an older driver capped at CUDA 11.x
  means ``pc2img[cuda11]``. Both extras need the NVIDIA package index::

      pip install pc2img[cuda12] --extra-index-url=https://pypi.nvidia.com

- ``pc2img[rrim]`` is a signposting-only extra: it installs no additional
  packages. See the RRIM notice below for what actually enables the
  feature.

Quickstart
==========

The example below builds a synthetic point cloud, runs it through the
spherical projection + Delaunay interpolation pipeline, and computes the
``range`` raster:

.. code-block:: python

    import numpy as np
    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
    from pchandler import PointCloudData

    from pc2img.core import PointCloudImageGenerator
    from pc2img.strategies import DelaunayInterpolation, SphericalProjection
    from pc2img.util import convert_to_image

    # An (N, 3) array of xyz points; r / spherical coords / field of view
    # are all derived from xyz.
    xyz = np.random.default_rng(0).normal(size=(5000, 3)) + [0, 0, 10]
    pcd = PointCloudData(xyz=xyz)

    cache_config = LazyDiskCacheConfig(cache_path="./cache", enable_caching=True)

    generator = PointCloudImageGenerator(
        pcd,
        img_res=(512, 512),
        proj=SphericalProjection(field_of_view=pcd.fov),
        interp=DelaunayInterpolation(),
        lazy_disk_cache_config=cache_config,
    )
    rasters = generator.generate(features=["range"])

    range_raster = rasters["range"]           # a raw float raster
    range_uint8 = convert_to_image(range_raster, normalize=True)  # uint8 export

``PointCloudImageGenerator`` takes the point cloud, the target image
resolution, a projection strategy, an interpolation strategy, and an
optional cache configuration; ``generate()`` accepts a list of feature
names and returns a dict mapping each name to its raster.

Feature overview
=================

Feature rasters are requested by name; the name itself is a small DSL that
also parameterizes the computation. A selection of the registered feature
families:

- ``range`` — the per-point range (distance from sensor), interpolated onto
  the grid.
- ``scalar_field_<name>`` — any scalar field carried on the point cloud,
  interpolated onto the grid.
- ``gradient_<axis>_<base_feature>[_px<pixel_size>]`` — the gradient of a
  base feature raster along ``x`` or ``y``, e.g. ``gradient_x_range``.
- ``hillshade[_<base_feature>][_<azimuth>][_<altitude>][_<z_factor>]`` —
  Lambertian hillshade illumination of a base raster.
- ``normalized_<base_feature>[_<low>_<high>]`` and
  ``clip_<base_feature>_<low>_<high>`` — percentile normalization/clipping
  of a base raster.
- ``multigrad_<base_feature>_<sigma1>-<sigma2>-...`` — scale-normalized
  gradients at multiple Gaussian scales.
- ``rrim``, ``rrim_pack_(...)``, ``rrim_component_(...)`` — the RRIM
  (Red Relief Image Map style) feature family; see the notice below.

Each feature strategy documents its full name grammar in its class
docstring — see ``src/pc2img/features/base_features.py``,
``derivative_features.py``, and ``rrim.py``.

RRIM notice
===========

The RRIM feature is an independent, image-space implementation of the
red-relief-image visualization technique, built on the patent-expiry basis
recorded in ``NOTICE``: the core patent family covering the technique has
expired in every jurisdiction in which it was granted. The technique is
credited to Tatsuro Chiba and Asia Air Survey Co., Ltd., with the openness
brightness component credited to the independent academic method of
Yokoyama, Shirasawa, and Pike (2002). "RRIM" and "Red Relief Image Map" may
be trademarks of Asia Air Survey Co., Ltd.; pc2img is not affiliated with
or endorsed by Asia Air Survey Co., Ltd.

The RRIM feature is opt-in: it registers only after an explicit
``import pc2img.features.rrim`` — it is not part of the default
``pc2img.features`` barrel, and installing the ``pc2img[rrim]`` extra alone
does not register it. See ``NOTICE`` and ``docs/ip/`` for the full
intellectual-property basis.

Documentation and contributing
===============================

Full documentation is hosted at
https://pc2img.readthedocs.io/en/latest/. Development setup, environment
bootstrap, and test-running instructions are in
`CONTRIBUTING.md <https://github.com/gseg-ethz/pc2img/blob/main/CONTRIBUTING.md>`_.
See the
`changelog <https://github.com/gseg-ethz/pc2img/blob/main/CHANGELOG.md>`_
for release history.

``pc2img`` is licensed under the BSD 3-Clause License.
